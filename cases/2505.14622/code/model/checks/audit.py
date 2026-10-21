"""Read-only numerical audit of PRL 135, 140404 (published source).

The submitted generate.py is never imported or executed. The oracle expands
the 2x2 GKSL action in the matrix-unit basis and propagates that 4x4 operator.
Only audit-* files in this script's directory are written.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
import scipy
from scipy.linalg import expm
from scipy.optimize import brentq
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
P = np.array([[[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]], complex)
I = np.eye(2, dtype=complex)
TOL = {"operator_and_array_abs": 1e-10, "time_abs": 1e-9,
       "density_trace_abs": 1e-12, "positivity_floor": -1e-12,
       "rounding_entry_abs": 0.005 + 1e-14}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rho(r):
    return (I + np.einsum("...a,aij->...ij", np.asarray(r), P))/2


def bloch(rs):
    return np.einsum("aij,...ji->...a", P, rs).real


def direct_action(c, h, r):
    ans = -1j*(h @ r-r @ h)
    for m in range(3):
        for n in range(3):
            product = P[n] @ P[m]
            ans += c[m, n]*(P[m] @ r @ P[n]-(product @ r+r @ product)/2)
    return ans


def operator(c, h):
    basis = np.eye(4).reshape(4, 2, 2)
    return np.column_stack([direct_action(c, h, e).ravel() for e in basis])


def bath(spec, variant):
    c = np.diag(np.array(spec["diagonal"], complex))
    c[0, 1] = c[1, 0] = spec["c12"]
    c[0, 2] = 1j*spec["imag_c13"]
    c[1, 2] = 1j*spec["imag_c23"]
    c[2, 0], c[2, 1] = c[0, 2].conjugate(), c[1, 2].conjugate()
    printed = c.copy()
    h = spec["h3"]*P[2]
    if variant == "stationary_constrained":
        # Obtain the dissipative forcing by two matrix-unit probes rather than
        # using the submitted Bloch coefficient formula.
        rs = rho(spec["declared_stationary"])
        residual = bloch(direct_action(c, h, rs))
        probes = []
        for m, n in [(0, 2), (1, 2)]:
            shift = np.zeros((3, 3), complex)
            shift[m, n], shift[n, m] = 1j, -1j
            probes.append(bloch(direct_action(shift, np.zeros((2, 2)), rs)))
        correction = np.linalg.lstsq(np.array(probes).T, -residual, rcond=None)[0]
        for (m, n), value in zip([(0, 2), (1, 2)], correction):
            c[m, n] += 1j*value
            c[n, m] -= 1j*value
    liouville = operator(c, h)
    constrained = liouville.copy()
    constrained[-1] = [1, 0, 0, 1]
    steady = np.linalg.solve(constrained, np.array([0, 0, 0, 1], complex)).reshape(2, 2)
    force = bloch(direct_action(c, h, I/2))
    matrix = np.column_stack([bloch(direct_action(c, h, p/2)) for p in P])
    return c, h, liouville, steady, matrix, force, printed


def evolution(liouville, initial, times):
    vec = np.asarray(initial).ravel()
    return np.asarray([(expm(liouville*t) @ vec).reshape(2, 2) for t in times])


def distance(rs, target):
    return np.sum(np.abs(np.linalg.eigvalsh(rs-target)), axis=-1)/2


def entry_time(liouville, initial, target, epsilon):
    def f(t):
        r = (expm(liouville*t) @ initial.ravel()).reshape(2, 2)
        return float(distance(r, target))-epsilon
    if f(0) <= 0:
        return 0.
    end = 1.
    while f(end) > 0:
        end *= 2
    return brentq(f, 0, end, xtol=2e-13)


def main():
    start = time.monotonic()
    cfg = json.loads((ROOT/"calculation/config.json").read_text())
    submitted = json.loads((ROOT/"calculation/results/generation.json").read_text())
    arrays = np.load(ROOT/"calculation/results/generation.npz")
    result = {"method": __doc__, "source": "raw/paper-published-harvest.pdf, pp. 2-4, 7-8",
              "python_code_sha256": sha(Path(__file__)), "numpy": np.__version__, "scipy": scipy.__version__,
              "tolerances": TOL, "array_comparisons": {}, "baths": {}, "protocols": {},
              "physical_checks": {}, "source_conditions": cfg,
              "input_integrity": {"config_hash_matches_generation": sha(ROOT/"calculation/config.json") == submitted["config_sha256"],
                                  "npz_hash_matches_generation": sha(ROOT/"calculation/results/generation.npz") == submitted["numeric_file_sha256"]}}
    checked = set()

    def compare(key, value):
        actual = arrays[key]
        assert actual.shape == value.shape, (key, actual.shape, value.shape)
        err = float(np.max(actual != value)) if actual.dtype == bool else float(np.max(np.abs(actual-value)))
        result["array_comparisons"][key] = {"max_abs_error": err,
            "scale": float(np.max(np.abs(value))), "within_1e_10": err <= TOL["operator_and_array_abs"]}
        checked.add(key)

    compare("time", np.linspace(0, cfg["time_max"], cfg["time_points"]))
    grid = np.linspace(-1, 1, cfg["field_points"])
    gx, gy = np.meshgrid(grid, grid)
    compare("field_x", gx); compare("field_y", gy)
    compare("field_mask", gx*gx+gy*gy <= 1)
    field_rho = rho(np.stack([gx, gy, np.zeros_like(gx)], axis=-1))
    times = arrays["time"]

    for variant in cfg["variants"]:
        for name, group in cfg["sets"].items():
            prefix = f"{variant}_{name}"
            initial = rho(group["initial"])
            baths = {label: bath(group[label], variant) for label in ["final", "auxiliary"]}
            outputs = {}
            for label, (c, h, liouville, steady, matrix, force, printed) in baths.items():
                outputs[label] = evolution(liouville, initial, times)
                compare(prefix+"_"+label, bloch(outputs[label]))
                velocities = (field_rho.reshape(-1, 4) @ liouville.T).reshape(*gx.shape, 2, 2)
                compare(prefix+"_"+label+"_velocity", bloch(velocities))
                declared = rho(group[label]["declared_stationary"])
                saved = submitted["variants"][variant][name]
                result["baths"][prefix+"_"+label] = {
                    "C_eigenvalues": np.linalg.eigvalsh(c).tolist(),
                    "C_max_reconstruction_shift": float(np.max(np.abs(c-printed))),
                    "C_shift_within_printed_rounding": bool(np.max(np.abs(c-printed)) <= TOL["rounding_entry_abs"]),
                    "M_eigenvalues_real": np.linalg.eigvals(matrix).real.tolist(),
                    "steady_bloch": bloch(steady).tolist(),
                    "steady_norm": float(np.linalg.norm(bloch(steady))),
                    "declared_steady_trace_distance": float(distance(steady, declared)),
                    "stationarity_residual": float(np.max(np.abs(liouville @ steady.ravel()))),
                    "M_summary_max_abs_error": float(np.max(np.abs(matrix-np.array(saved[label+"_M"])))),
                    "b_summary_max_abs_error": float(np.max(np.abs(force-np.array(saved[label+"_b"])))),
                    "C_summary_max_abs_error": float(np.max(np.abs(c-(np.array(saved[label+"_C_real"])+1j*np.array(saved[label+"_C_imag"]))))),
                    "trace_preservation_residual": float(np.max(np.abs(np.array([1, 0, 0, 1]) @ liouville))),
                    "physical_time_series": {"minimum_density_eigenvalue": float(np.min(np.linalg.eigvalsh(outputs[label]))),
                        "trace_error": float(np.max(np.abs(np.trace(outputs[label], axis1=-2, axis2=-1)-1))),
                        "hermiticity_error": float(np.max(np.abs(outputs[label]-outputs[label].conj().transpose(0, 2, 1))))}}
            lf, target = baths["final"][2:4]
            la = baths["auxiliary"][2]
            compare(prefix+"_distance_final", distance(outputs["final"], target))
            compare(prefix+"_distance_auxiliary", distance(outputs["auxiliary"], target))
            compare(prefix+"_nominal_distance_final", distance(outputs["final"], rho(group["final"]["declared_stationary"])))
            aux_distance = distance(outputs["auxiliary"], target)
            initial_distance = float(distance(initial, target))
            derivative_initial = np.dot(bloch(initial-target), bloch(direct_action(baths["auxiliary"][0], baths["auxiliary"][1], initial)))/(4*initial_distance)
            for switch, saved in zip(group["switches"], submitted["variants"][variant][name]["protocols"]):
                middle = evolution(la, initial, [switch])[0]
                final_state = outputs["auxiliary"].copy()
                after = times >= switch
                final_state[after] = evolution(lf, middle, times[after]-switch)
                key = prefix+"_protocol_"+str(switch).replace(".", "p")
                compare(key, bloch(final_state))
                di = float(distance(middle, target))
                df = float(distance(evolution(lf, initial, [switch])[0], target))
                category = "strong" if di > initial_distance else ("weak_A" if di < df else "weak_B")
                measurements = []
                for epsilon, saved_time in zip(cfg["cutoffs"], saved["relaxation"]):
                    direct = entry_time(lf, initial, target, epsilon)
                    total = switch+entry_time(lf, middle, target, epsilon)
                    measurements.append({"epsilon": epsilon, "direct": direct, "total_two_step": total,
                        "speedup": direct/total, "time_summary_max_abs_error": max(abs(direct-saved_time["direct_time"]), abs(total-saved_time["total_two_step_time"])),
                        "auxiliary_enters_epsilon_before_switch": bool(np.min(aux_distance[times <= switch]) <= epsilon)})
                result["protocols"][key] = {"switch": switch, "class": category,
                    "class_matches_summary": category == saved["class"], "initial_distance": initial_distance,
                    "intermediate_distance": di, "direct_distance_at_switch": df,
                    "auxiliary_initial_distance_derivative": float(derivative_initial),
                    "minimum_density_eigenvalue": float(np.min(np.linalg.eigvalsh(final_state))),
                    "maximum_trace_error": float(np.max(np.abs(np.trace(final_state, axis1=-2, axis2=-1)-1))),
                    "distance_final_segment_max_increase": float(np.max(np.diff(distance(final_state[after], target)))),
                    "measurements": measurements}
    result["checked_arrays"] = sorted(checked)
    result["unchecked_arrays"] = sorted(set(arrays.files)-checked)
    result["aggregate"] = {"array_count": len(checked),
        "array_max_abs_error": max(v["max_abs_error"] for v in result["array_comparisons"].values()),
        "time_max_abs_error": max(z["time_summary_max_abs_error"] for v in result["protocols"].values() for z in v["measurements"]),
        "minimum_C_eigenvalue": min(min(v["C_eigenvalues"]) for v in result["baths"].values()),
        "minimum_density_eigenvalue": min([v["physical_time_series"]["minimum_density_eigenvalue"] for v in result["baths"].values()]+[v["minimum_density_eigenvalue"] for v in result["protocols"].values()])}
    manifest = json.loads((HERE/"audit-input-manifest.json").read_text())
    result["input_integrity"]["all_reviewed_input_hashes_unchanged"] = all(sha(ROOT/p) == meta["sha256"] for p, meta in manifest.items())
    result["wall_seconds"] = time.monotonic()-start
    (HERE/"audit-gksl-results.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"aggregate": result["aggregate"], "unchecked_arrays": result["unchecked_arrays"], "integrity": result["input_integrity"], "wall_seconds": result["wall_seconds"]}, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
