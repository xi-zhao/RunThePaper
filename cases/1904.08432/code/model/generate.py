"""Independent correlation-matrix calculation for arXiv:1904.08432v2.

Spectrum: finite OBC similarity to a Hermitian tridiagonal SSH matrix.
Dynamics: propagate the original damping matrix, never the ill-conditioned gauge.
No reference curves or figure coordinates are read.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from scipy.linalg import expm, eigh_tridiagonal, solve_continuous_lyapunov
from threadpoolctl import threadpool_limits

ROOT = Path.cwd()
SY = np.array([[0, -1j], [1j, 0]])
SX = np.array([[0, 1], [1, 0]], complex)


def realspace(length, t1, t2, gl, gg, periodic=False, model=1):
    size = 2*length
    h = np.diag(np.tile([t1, t2], length)[:size-1], 1)
    h = h+h.T
    if periodic:
        h[0, -1] = h[-1, 0] = t2
    ml = np.kron(np.eye(length), gl/2*(np.eye(2)+SY))
    mg = np.kron(np.eye(length), gg/2*(np.eye(2)+(-1 if model == 1 else 1)*SY))
    x = 1j*h.T-(ml.T+mg)
    return x, mg, h


def bloch(k, t1, t2, gl, gg, model=1):
    gamma = gl+gg
    asymmetry = gamma if model == 1 else gl-gg
    return 1j*((t1+t2*np.cos(k))[..., None, None]*SX
               +(t2*np.sin(k)-1j*asymmetry/2)[..., None, None]*SY)-gamma/2*np.eye(2)


def periodic_curve(length, times, t1, t2, gl, gg):
    k = 2*np.pi*np.arange(length)/length
    x = bloch(k, t1, t2, gl, gg)
    gamma = gl+gg
    b = x+gamma/2*np.eye(2)
    omega = np.sqrt(np.einsum('kij,kji->k', b, b)/2+0j)
    ep = np.exp(times[:, None]*(-gamma/2+omega[None, :]))
    em = np.exp(times[:, None]*(-gamma/2-omega[None, :]))
    a = (ep+em)/2
    factor = np.empty_like(a)
    regular = np.abs(omega) > 1e-13
    factor[:, regular] = (ep[:, regular]-em[:, regular])/(2*omega[regular])
    factor[:, ~regular] = times[:, None]*np.exp(-gamma/2*times[:, None])
    # tr B=0: ||a I+factor B||_F^2=2|a|^2+|factor|^2||B||_F^2.
    # C(0)-C_s=I/2; translational symmetry makes RMS=single-cell deviation.
    norm_b = np.sum(np.abs(b)**2, axis=(1, 2))
    return 0.5*np.mean(2*np.abs(a)**2+np.abs(factor)**2*norm_b, axis=1)


def open_dynamics(length, times, t1, t2, gl, gg, model=1, periodic=False):
    x, mg, _ = realspace(length, t1, t2, gl, gg, periodic, model)
    if model == 1:
        steady = gg/(gl+gg)*np.eye(2*length)
    else:
        steady = solve_continuous_lyapunov(x, -2*mg)
        steady = (steady+steady.conj().T)/2
    initial_difference = np.eye(2*length)-steady
    evals, vectors = np.linalg.eigh(initial_difference)
    if np.min(evals) < -1e-10:
        raise ArithmeticError("nonphysical initial difference to steady state")
    factor = vectors * np.sqrt(np.maximum(evals, 0))[None, :]
    step = expm(x*(times[1]-times[0]))
    result = np.empty((len(times), length))
    for i, _ in enumerate(times):
        diagonal = np.sum(np.abs(factor)**2, axis=1)
        result[i] = diagonal.reshape(length, 2).sum(axis=1)
        if i+1 < len(times):
            factor = step @ factor
    residual = np.linalg.norm(x @ steady+steady @ x.conj().T+2*mg, ord=np.inf)
    return result, {"stationary_residual": float(residual),
                    "stationary_min_eigenvalue": float(np.linalg.eigvalsh(steady)[0]),
                    "stationary_max_eigenvalue": float(np.linalg.eigvalsh(steady)[-1])}


def main():
    start = time.monotonic()
    config_path = ROOT/"calculation/config.json"
    cfg = json.loads(config_path.read_text())
    times = np.geomspace(1, cfg["fig2_time_max"], cfg["fig2_time_points"])
    arrays = {"fig2_time": times}
    summary = {"source": "PRL 123, 170401; arXiv:1904.08432v2 numerical conditions",
               "independent_generation": "Equation-derived process inputs only. Agent read original figure ordinates after v1; v2 adds analytic finite-dark-mode subtraction and declared size candidates. No author code used and no fitted curve ordinates read by this process.",
               "lindblad_convention": "2 L rho Ldagger - {Ldagger L,rho}",
               "spectral_method": "positive-hopping OBC diagonal similarity; Hermitian eigensolver, including isolated edge states",
               "dynamical_method": "matrix exponential of original X, repeated exact uniform semigroup steps; no inverse skin gauge",
               "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
               "cases": {}, "steady_checks": {}}
    size = cfg["spectrum_cells"]
    k = 2*np.pi*np.arange(size)/size
    for name, spec in cfg["cases"].items():
        t1, t2, gl, gg = (spec[q] for q in ["t1", "t2", "gamma_l", "gamma_g"])
        gamma = gl+gg
        arrays["fig2a_"+name] = periodic_curve(size, times, t1, t2, gl, gg)
        # The fully filled finite periodic chain retains its exact k=pi dark mode.
        # Store both the nominated Css reference and the actual filled-state limit.
        if name == 'A':
            arrays['fig2a_A_actual_limit'] = arrays['fig2a_A']-1/(2*size)
            arrays['fig2a_A_minimum_norm'] = arrays['fig2a_A']+1/(2*size)
        arrays["fig2b_"+name+"_pbc"] = np.linalg.eigvals(bloch(k, t1, t2, gl, gg)).ravel()
        effective = np.sqrt(t1*t1-gamma*gamma/4)
        links = np.tile([effective, t2], size)[:2*size-1]
        eigenvalues = eigh_tridiagonal(np.zeros(2*size), links, eigvals_only=True)
        arrays["fig2b_"+name+"_obc"] = -gamma/2+1j*eigenvalues
        summary["cases"][name] = {"pbc_gap_finite_grid": float(-2*np.max(arrays["fig2b_"+name+"_pbc"].real)),
                                  "obc_gap": float(gamma),
                                  "skin_log_amplitude_per_cell": float(np.log((t1+gamma/2)/(t1-gamma/2))/2)}
    dynamic_times = np.linspace(0, cfg["dynamic_time_max"], cfg["dynamic_time_points"])
    arrays["dynamic_time"] = dynamic_times
    params = cfg["dynamics"]
    t1, t2, gl, gg = (params[q] for q in ["t1", "t2", "gamma_l", "gamma_g"])
    for length in cfg["open_lengths"]:
        arrays[f"open_{length}"], diagnostic = open_dynamics(length, dynamic_times, t1, t2, gl, gg)
        summary["steady_checks"][f"modelI_open_{length}"] = diagnostic
    for length in cfg['periodic_lengths']:
        arrays[f"periodic_{length}"] = periodic_curve(length, dynamic_times, t1, t2, gl, gg)
        arrays[f"periodic_actual_{length}"] = arrays[f"periodic_{length}"]-1/(2*length)
        arrays[f"periodic_minimum_norm_{length}"] = arrays[f"periodic_{length}"]+1/(2*length)
    control_times = np.linspace(0, cfg["control_time_max"], cfg["control_time_points"])
    arrays["control_time"] = control_times
    for boundary in ["periodic", "open"]:
        arrays["control_"+boundary], diagnostic = open_dynamics(60, control_times, t1, t2, gl, gg,
                                                               model=2, periodic=boundary == "periodic")
        summary["steady_checks"]["modelII_"+boundary] = diagnostic
    output = ROOT/"calculation/results"
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output/"generation.npz", **arrays)
    summary["wall_seconds"] = time.monotonic()-start
    summary["numeric_file_sha256"] = hashlib.sha256((output/"generation.npz").read_bytes()).hexdigest()
    (output/"generation.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps({"cases": list(cfg["cases"]), "arrays": len(arrays),
                      "wall_seconds": summary["wall_seconds"], "max_spectral_dimension": 2*size}))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
