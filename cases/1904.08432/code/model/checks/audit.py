"""Read-only audit from the original hopping and jump operators.

No import or execution of generate.py. A Jordan-Wigner full-Fock oracle tests
the fermionic closure and factor of two. Large OBC arrays use adaptive DOP853
integration of the covariance equation, not repeated exponential propagation.
PBC arrays use eigenprojector propagation of independent 2x2 blocks, checked
against generic dense exponentials. Output stays under calculation/checks.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import scipy
from scipy.linalg import expm
from scipy.integrate import solve_ivp
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TOL = {"direct_array_abs": 1e-10, "ode_array_abs": 2e-9,
       "ode_rtol": 2e-11, "ode_atol": 1e-20, "fock_abs": 1e-10,
       "spectrum_abs": 1e-10, "relative_error_reporting_floor": 1e-12}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jumps(length, gl, gg, model):
    loss = np.zeros((length, 2*length), complex)
    gain = loss.copy()
    for cell in range(length):
        loss[cell, 2*cell:2*cell+2] = np.sqrt(gl/2)*np.array([1, -1j])
        gain[cell, 2*cell:2*cell+2] = np.sqrt(gg/2)*np.array([1, (1j if model == 1 else -1j)])
    return loss, gain


def matrices(length, t1, t2, gl, gg, model=1, periodic=False):
    h = np.zeros((2*length, 2*length))
    for cell in range(length):
        a, b = 2*cell, 2*cell+1
        h[a, b] += t1; h[b, a] += t1
        if cell < length-1 or periodic:
            anext = 2*((cell+1) % length)
            h[b, anext] += t2; h[anext, b] += t2
    loss, gain = jumps(length, gl, gg, model)
    ml, mg = loss.conj().T @ loss, gain.conj().T @ gain
    return 1j*h.T-ml.T-mg, mg, h


def annihilators(n):
    out = []
    for site in range(n):
        c = np.zeros((2**n, 2**n), complex)
        for state in range(2**n):
            if state & (1 << site):
                c[state ^ (1 << site), state] = (-1)**((state & ((1 << site)-1)).bit_count())
        out.append(c)
    return out


def fock_operator(length, t1, t2, gl, gg, model, periodic):
    c = annihilators(2*length)
    n = 2**(2*length)
    _, _, h = matrices(length, t1, t2, gl, gg, model, periodic)
    h_many = sum(h[i, j]*c[i].conj().T @ c[j] for i in range(2*length) for j in range(2*length))
    loss, gain = jumps(length, gl, gg, model)
    ls = [sum(d[i]*c[i] for i in range(2*length)) for d in loss]
    ls += [sum(d[i]*c[i].conj().T for i in range(2*length)) for d in gain]
    identity = np.eye(n)
    liouville = -1j*(np.kron(h_many, identity)-np.kron(identity, h_many.T))
    for jump in ls:
        q = jump.conj().T @ jump
        liouville += 2*np.kron(jump, jump.conj())-np.kron(q, identity)-np.kron(identity, q.T)
    observables = np.array([[a.conj().T @ b for b in c] for a in c])
    return liouville, observables


def correlations(rho, observables):
    return np.einsum("ijab,ba->ij", observables, rho)


def pbc_blocks(k, t1, t2, gl, gg):
    # Eq.(2) D vectors and the SSH bonds define the block; no Pauli formula.
    loss = np.sqrt(gl/2)*np.array([1, -1j])
    gain = np.sqrt(gg/2)*np.array([1, 1j])
    ml, mg = np.outer(loss.conj(), loss), np.outer(gain.conj(), gain)
    h = np.zeros((len(k), 2, 2), complex)
    h[:, 0, 1] = t1+t2*np.exp(-1j*k)
    h[:, 1, 0] = h[:, 0, 1].conj()
    return 1j*h-ml.T-mg


def periodic_oracle(length, times, t1, t2, gl, gg):
    k = 2*np.pi*np.arange(length)/length
    x = pbc_blocks(k, t1, t2, gl, gg)
    values, v = np.linalg.eig(x)
    vi = np.linalg.inv(v)
    projectors = np.einsum("kia,kaj->kaij", v, vi)
    gram = np.einsum("kaij,kbij->kab", projectors, projectors.conj())
    result = np.empty(len(times))
    for first in range(0, len(times), 64):
        t = times[first:first+64]
        exponential = np.exp(t[:, None, None]*values[None, :, :])
        norm = np.einsum("tka,tkb,kab->tk", exponential, exponential.conj(), gram).real
        result[first:first+len(t)] = (1-gg/(gl+gg))*np.mean(norm, axis=1)
    indices = np.unique(np.linspace(0, length-1, 11, dtype=int))
    check_times = np.unique(np.quantile(times, [0, .1, .5, 1]))
    oracle_error = 0.
    for idx in indices:
        for t in check_times:
            e = expm(x[idx]*t)
            via_projectors = sum(np.exp(values[idx, a]*t)*projectors[idx, a] for a in range(2))
            oracle_error = max(oracle_error, float(np.max(np.abs(e-via_projectors))))
    return result, {"max_eigenbasis_condition": float(np.max(np.linalg.cond(v))),
                    "generic_expm_crosscheck_max_abs_error": oracle_error}, x


def covariance_ode(length, times, params, model=1, periodic=False):
    x, mg, h = matrices(length, **params, model=model, periodic=periodic)
    if model == 1:
        steady = params["gg"]/(params["gl"]+params["gg"])*np.eye(2*length)
    else:
        # At equal loss/gain, X=ih-gamma/2. Solve in the Hermitian h basis.
        energy, v = np.linalg.eigh(h)
        transformed_gain = v.conj().T @ mg @ v
        gamma = params["gl"]+params["gg"]
        coefficients = 2*transformed_gain/(gamma-1j*(energy[:, None]-energy[None, :]))
        steady = v @ coefficients @ v.conj().T
    initial = np.eye(2*length)-steady
    sx = csr_matrix(x)
    def rhs(_, flat):
        d = flat.reshape(x.shape)
        return (sx @ d+(sx @ d.conj().T).conj().T).ravel()
    sol = solve_ivp(rhs, (times[0], times[-1]), initial.ravel().astype(complex),
                    method="DOP853", t_eval=times, rtol=TOL["ode_rtol"], atol=TOL["ode_atol"])
    assert sol.success, sol.message
    curves = np.empty((len(times), length))
    for j in range(len(times)):
        curves[j] = sol.y[:, j].reshape(x.shape).diagonal().real.reshape(length, 2).sum(axis=1)
    chosen = np.unique(np.linspace(0, len(times)-1, 9, dtype=int))
    direct_error = 0.
    minimum_C_eigenvalue, maximum_C_eigenvalue = 1., 0.
    for j in chosen:
        e = expm(x*times[j])
        cov = e @ initial @ e.conj().T
        direct_error = max(direct_error, float(np.max(np.abs(curves[j]-cov.diagonal().real.reshape(length, 2).sum(axis=1)))))
        physical = steady+cov
        ev = np.linalg.eigvalsh((physical+physical.conj().T)/2)
        minimum_C_eigenvalue = min(minimum_C_eigenvalue, float(ev[0]))
        maximum_C_eigenvalue = max(maximum_C_eigenvalue, float(ev[-1]))
    return curves, {"nfev": sol.nfev, "generic_expm_crosscheck_max_abs_error": direct_error,
                    "stationary_residual": float(np.max(np.abs(x @ steady+steady @ x.conj().T+2*mg))),
                    "steady_eigenvalue_min": float(np.linalg.eigvalsh(steady)[0]),
                    "steady_eigenvalue_max": float(np.linalg.eigvalsh(steady)[-1]),
                    "physical_correlations_eigenvalue_min_selected_times": minimum_C_eigenvalue,
                    "physical_correlations_eigenvalue_max_selected_times": maximum_C_eigenvalue}, steady


def main():
    start = time.monotonic()
    cfg = json.loads((ROOT/"calculation/config.json").read_text())
    submitted = json.loads((ROOT/"calculation/results/generation.json").read_text())
    arrays = np.load(ROOT/"calculation/results/generation.npz")
    result = {"method": __doc__, "source": "raw/paper-arxiv-v2.pdf, pp.1-5,8-9",
              "code_sha256": sha(Path(__file__)), "numpy": np.__version__, "scipy": scipy.__version__,
              "tolerances": TOL, "array_comparisons": {}, "periodic_oracle_diagnostics": {},
              "ode_diagnostics": {}, "spectrum_diagnostics": {}, "fock_oracle": {}, "features": {},
              "input_integrity": {"config_hash_matches_generation": sha(ROOT/"calculation/config.json") == submitted["config_sha256"],
                                  "npz_hash_matches_generation": sha(ROOT/"calculation/results/generation.npz") == submitted["numeric_file_sha256"]}}
    checked = set()
    def compare(key, expected, tolerance=TOL["direct_array_abs"]):
        actual = arrays[key]
        assert actual.shape == expected.shape, (key, actual.shape, expected.shape)
        error = np.abs(actual-expected)
        regular = np.abs(expected) > TOL["relative_error_reporting_floor"]
        result["array_comparisons"][key] = {"max_abs_error": float(np.max(error)),
            "max_relative_error_above_1e_12": float(np.max(error[regular]/np.abs(expected[regular]))) if regular.any() else None,
            "tolerance_abs": tolerance, "within_tolerance": bool(np.max(error) <= tolerance)}
        checked.add(key)

    times = np.geomspace(1, cfg["fig2_time_max"], cfg["fig2_time_points"])
    compare("fig2_time", times)
    for name, spec in cfg["cases"].items():
        params = {"t1": spec["t1"], "t2": spec["t2"], "gl": spec["gamma_l"], "gg": spec["gamma_g"]}
        curve, diagnostics, xk = periodic_oracle(cfg["spectrum_cells"], times, **params)
        result["periodic_oracle_diagnostics"]["fig2a_"+name] = diagnostics
        compare("fig2a_"+name, curve)
        eig = np.linalg.eigvals(xk).ravel()
        actual = arrays["fig2b_"+name+"_pbc"]
        rows, cols = linear_sum_assignment(np.abs(actual[:, None]-eig[None, :]))
        compare("fig2b_"+name+"_pbc", eig[cols[np.argsort(rows)]])
        size = 2*cfg["spectrum_cells"]
        gamma = params["gl"]+params["gg"]
        effective = np.sqrt(params["t1"]**2-gamma**2/4)
        hermitian = np.zeros((size, size))
        for site in range(size-1):
            value = effective if site % 2 == 0 else params["t2"]
            hermitian[site, site+1] = hermitian[site+1, site] = value
        expected = -gamma/2+1j*np.linalg.eigvalsh(hermitian)
        actual = arrays["fig2b_"+name+"_obc"]
        order = np.argsort(actual.imag)
        compare("fig2b_"+name+"_obc", expected[np.argsort(order)])
        # Check the similarity locally to avoid multiplying an enormous gauge.
        ratio = np.sqrt((params["t1"]+gamma/2)/(params["t1"]-gamma/2))
        similarity_error = max(abs((params["t1"]-gamma/2)*ratio-effective),
                               abs((params["t1"]+gamma/2)/ratio-effective))
        short_x = matrices(5, **params)[0]
        short_eig = np.linalg.eigvals(short_x)
        short_h = hermitian[:10, :10]
        short_expected = -gamma/2+1j*np.linalg.eigvalsh(short_h)
        rows, cols = linear_sum_assignment(np.abs(short_eig[:, None]-short_expected[None, :]))
        late = times >= 100
        power = np.polyfit(np.log(times[late]), np.log(curve[late]), 1)[0]
        exponential_rate = -np.polyfit(times[late], np.log(curve[late]), 1)[0]
        result["spectrum_diagnostics"][name] = {"local_similarity_error": float(similarity_error),
            "gauge_condition_number": float(ratio**cfg["spectrum_cells"]),
            "short_chain_direct_eigenvalue_max_error": float(np.max(np.abs(short_eig[rows]-short_expected[cols]))),
            "finite_PBC_gap": float(-2*eig.real.max()), "OBC_gap": gamma,
            "loglog_slope_t100_1000": float(power), "semilog_rate_t100_1000": float(exponential_rate)}

    dynamic = np.linspace(0, cfg["dynamic_time_max"], cfg["dynamic_time_points"])
    control = np.linspace(0, cfg["control_time_max"], cfg["control_time_points"])
    compare("dynamic_time", dynamic); compare("control_time", control)
    p = cfg["dynamics"]
    params = {"t1": p["t1"], "t2": p["t2"], "gl": p["gamma_l"], "gg": p["gamma_g"]}
    for length in cfg["open_lengths"]:
        key = f"open_{length}"
        curve, diag, _ = covariance_ode(length, dynamic, params)
        compare(key, curve, TOL["ode_array_abs"])
        result["ode_diagnostics"][key] = diag
    for length in [60, 150, 4096]:
        key = f"periodic_{length}"
        curve, diag, _ = periodic_oracle(length, dynamic, **params)
        compare(key, curve)
        result["periodic_oracle_diagnostics"][key] = diag
    for boundary in ["periodic", "open"]:
        key = "control_"+boundary
        curve, diag, steady = covariance_ode(60, control, params, model=2, periodic=boundary == "periodic")
        compare(key, curve, TOL["ode_array_abs"])
        result["ode_diagnostics"][key] = diag
        result["features"][key+"_mean_pure_exponential_max_error"] = float(np.max(np.abs(curve.mean(axis=1)-np.exp(-.4*control))))

    # Full 16-state Hilbert space, 256-dimensional superoperator. Independent
    # matrix units catch transpose, gain signs and rate factors in the closure.
    rng = np.random.default_rng(468321)
    for model in [1, 2]:
        for periodic in [False, True]:
            key = f"model{model}_"+("PBC" if periodic else "OBC")
            full, obs = fock_operator(2, **params, model=model, periodic=periodic)
            x, mg, _ = matrices(2, **params, model=model, periodic=periodic)
            random_pure = rng.normal(size=16)+1j*rng.normal(size=16)
            random_pure /= np.linalg.norm(random_pure)
            random_rho = np.outer(random_pure, random_pure.conj())
            delta = correlations(random_rho, obs)
            derivative = (full @ random_rho.ravel()).reshape(16, 16)
            closure_error = np.max(np.abs(correlations(derivative, obs)-(x @ delta+delta @ x.conj().T+2*mg)))
            filled = np.zeros((16, 16), complex); filled[-1, -1] = 1
            if model == 1:
                steady = .5*np.eye(4)
            else:
                gamma = params["gl"]+params["gg"]
                h = matrices(2, **params, model=model, periodic=periodic)[2]
                energy, v = np.linalg.eigh(h)
                steady = v @ (2*(v.T @ mg @ v)/(gamma-1j*(energy[:, None]-energy[None, :]))) @ v.T
            errors, particle_excess = [], []
            for t in [0., .1, 1., 5., 20., 100.]:
                evolved = (expm(full*t) @ filled.ravel()).reshape(16, 16)
                exact_delta = correlations(evolved, obs)
                e = expm(x*t)
                reduced = steady+e @ (np.eye(4)-steady) @ e.conj().T
                errors.append(float(np.max(np.abs(exact_delta-reduced))))
                particle_excess.append({"t": t, "mean_cell_excess": float(np.trace(exact_delta-steady).real/2)})
            result["fock_oracle"][key] = {"random_state_closure_max_abs_error": float(closure_error),
                "filled_state_evolution_max_abs_error": max(errors),
                "trace_preservation_residual": float(np.max(np.abs(np.eye(16).ravel() @ full))),
                "particle_excess": particle_excess}

    # Distinguish the finite-grid dark state from a merely small computed gap.
    dark = np.array([1, 1j])/np.sqrt(2)
    xpi = pbc_blocks(np.array([np.pi]), **params)[0]
    result["features"]["finite_periodic_dark_mode"] = {"Xpi_dark_residual": float(np.linalg.norm(xpi @ dark)),
        "exact_dark_eigenvalue": "0 for t1=t2 at k=pi", "residual_excess_per_cell": {str(l): .5/l for l in [2,60,150,4096]}}
    periodic_values = arrays["periodic_4096"]
    front_results = []
    for ratio_threshold in [.25, .5, .75]:
        crossings = []
        for cell in range(4, 55):
            ratio_curve = arrays["open_60"][:, cell]/periodic_values
            indices = np.where(ratio_curve < ratio_threshold)[0]
            if len(indices) and indices[0] > 0:
                j = indices[0]
                t = np.interp(ratio_threshold, ratio_curve[j-1:j+1][::-1], dynamic[j-1:j+1][::-1])
                crossings.append((cell+1, t))
        slope, intercept = np.polyfit(np.array(crossings)[:,0], np.array(crossings)[:,1], 1)
        front_results.append({"OBC_to_PBC_ratio_threshold": ratio_threshold, "cell_range": [5,55],
            "fitted_front_speed_cells_per_time": float(1/slope), "intercept_time": float(intercept)})
    result["features"]["chiral_front"] = front_results
    result["features"]["PBC_length_60_4096_max_curve_difference_t0_80"] = float(np.max(np.abs(arrays["periodic_60"]-arrays["periodic_4096"])))
    result["features"]["PBC_length_150_4096_max_curve_difference_t0_80"] = float(np.max(np.abs(arrays["periodic_150"]-arrays["periodic_4096"])))
    late = dynamic >= 60
    result["features"]["OBC_L30_semilog_rate_t60_80"] = float(-np.polyfit(dynamic[late], np.log(np.sqrt(np.mean(arrays["open_30"][late]**2, axis=1))), 1)[0])
    result["checked_arrays"] = sorted(checked)
    result["unchecked_arrays"] = sorted(set(arrays.files)-checked)
    manifest = json.loads((HERE/"audit-input-manifest.json").read_text())
    result["input_integrity"]["all_reviewed_input_hashes_unchanged"] = all(sha(ROOT/p) == meta["sha256"] for p, meta in manifest.items())
    result["wall_seconds"] = time.monotonic()-start
    (HERE/"audit-correlations-results.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"array_max_abs_errors": {k:v["max_abs_error"] for k,v in result["array_comparisons"].items()},
                      "unchecked_arrays": result["unchecked_arrays"], "integrity": result["input_integrity"], "wall_seconds": result["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
