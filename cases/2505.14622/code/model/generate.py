"""Independent Bloch-equation calculation from PRL 135, 140404 Eqs. (8), (A2-9).

No author notebook, reference curves, original images, or comparison output is read.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq
from threadpoolctl import threadpool_limits

ROOT = Path.cwd()


def system(spec, variant):
    c = np.diag(np.asarray(spec["diagonal"], float)).astype(complex)
    c[0, 1] = c[1, 0] = spec["c12"]
    c[0, 2] = 1j * spec["imag_c13"]
    c[2, 0] = c[0, 2].conjugate()
    c[1, 2] = 1j * spec["imag_c23"]
    c[2, 1] = c[1, 2].conjugate()
    h = spec["h3"]
    a, b, d = np.diag(c).real
    m = 2 * np.array([[-b-d, -h+c[0, 1].real, 0],
                      [h+c[0, 1].real, -a-d, 0], [0, 0, -a-b]])
    force = -4 * np.imag([c[1, 2], c[2, 0], c[0, 1]])
    if variant == "stationary_constrained":
        # End Matter explicitly prescribes b=-2 Lambda r*. No reference fitting.
        force = -m @ np.asarray(spec["declared_stationary"], float)
        c[1, 2] = -1j * force[0] / 4
        c[2, 1] = c[1, 2].conjugate()
        c[2, 0] = -1j * force[1] / 4
        c[0, 2] = c[2, 0].conjugate()
    stationary = np.linalg.solve(m, -force)
    return m, force, stationary, c


def trajectory(m, stationary, initial, ts):
    return np.asarray([stationary + expm(m * t) @ (initial-stationary) for t in ts])


def hitting_time(m, stationary, initial, epsilon):
    def distance(t):
        return np.linalg.norm(expm(m*t) @ (initial-stationary)) / 2
    if distance(0) <= epsilon:
        return 0.0
    upper = 1.0
    while distance(upper) > epsilon:
        upper *= 2
        if upper > 1024:
            raise ArithmeticError("stable final dynamics did not reach threshold")
    return float(brentq(lambda t: distance(t)-epsilon, 0, upper, xtol=1e-13))


def main():
    start = time.monotonic()
    config_path = ROOT / "calculation/config.json"
    cfg = json.loads(config_path.read_text())
    ts = np.linspace(0, cfg["time_max"], cfg["time_points"])
    grid = np.linspace(-1, 1, cfg["field_points"])
    gx, gy = np.meshgrid(grid, grid)
    points = np.column_stack((gx.ravel(), gy.ravel(), np.zeros(gx.size)))
    arrays = {"time": ts, "field_x": gx, "field_y": gy,
              "field_mask": gx*gx+gy*gy <= 1}
    summary = {"model": "standard-GKSL Pauli basis; rdot=2 Lambda r+b",
               "independent_generation": "paper parameters only; author notebook not read",
               "parameter_reconstruction": "stationary_constrained uses the explicit r* and b=-2Lambda r*; printed retains all displayed decimals",
               "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
               "variants": {}}
    for variant in cfg["variants"]:
        sets = {}
        for name, group in cfg["sets"].items():
            initial = np.asarray(group["initial"], float)
            mf, bf, rf, cf = system(group["final"], variant)
            ma, ba, ra, ca = system(group["auxiliary"], variant)
            final = trajectory(mf, rf, initial, ts)
            auxiliary = trajectory(ma, ra, initial, ts)
            prefix = f"{variant}_{name}"
            arrays[prefix+"_final"] = final
            arrays[prefix+"_auxiliary"] = auxiliary
            arrays[prefix+"_distance_final"] = np.linalg.norm(final-rf, axis=1)/2
            arrays[prefix+"_distance_auxiliary"] = np.linalg.norm(auxiliary-rf, axis=1)/2
            nominal_rf = np.asarray(group["final"]["declared_stationary"], float)
            arrays[prefix+"_nominal_distance_final"] = np.linalg.norm(final-nominal_rf, axis=1)/2
            for label, m, force in [("final", mf, bf), ("auxiliary", ma, ba)]:
                velocity = points @ m.T + force
                arrays[prefix+"_"+label+"_velocity"] = velocity.reshape(*gx.shape, 3)
            protocols = []
            for switch in group["switches"]:
                intermediate = trajectory(ma, ra, initial, [switch])[0]
                evolved = auxiliary.copy()
                after = ts >= switch
                evolved[after] = trajectory(mf, rf, intermediate, ts[after]-switch)
                key = str(switch).replace(".", "p")
                arrays[prefix+"_protocol_"+key] = evolved
                ds = float(np.linalg.norm(initial-rf)/2)
                di = float(np.linalg.norm(intermediate-rf)/2)
                direct_at_switch = float(np.linalg.norm(expm(mf*switch) @ (initial-rf))/2)
                category = "strong" if di > ds else ("weak_A" if di < direct_at_switch else "weak_B")
                times = []
                for epsilon in cfg["cutoffs"]:
                    direct_time = hitting_time(mf, rf, initial, epsilon)
                    total_time = switch + hitting_time(mf, rf, intermediate, epsilon)
                    times.append({"epsilon": epsilon, "direct_time": direct_time,
                                  "total_two_step_time": total_time,
                                  "speedup": direct_time/total_time})
                protocols.append({"switch": switch, "array_key": prefix+"_protocol_"+key,
                                  "class": category, "initial_distance": ds,
                                  "switch_distance": di, "direct_switch_distance": direct_at_switch,
                                  "relaxation": times})
            sets[name] = {"final_M": mf.tolist(), "auxiliary_M": ma.tolist(),
                          "final_b": bf.tolist(), "auxiliary_b": ba.tolist(),
                          "final_C_real": cf.real.tolist(), "final_C_imag": cf.imag.tolist(),
                          "auxiliary_C_real": ca.real.tolist(), "auxiliary_C_imag": ca.imag.tolist(),
                          "final_stationary": rf.tolist(), "auxiliary_stationary": ra.tolist(),
                          "final_C_eigenvalues": np.linalg.eigvalsh(cf).tolist(),
                          "auxiliary_C_eigenvalues": np.linalg.eigvalsh(ca).tolist(),
                          "nominal_final_stationary_displacement": float(np.linalg.norm(rf-nominal_rf)),
                          "protocols": protocols}
        summary["variants"][variant] = sets
    output = ROOT / "calculation/results"
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output/"generation.npz", **arrays)
    summary["wall_seconds"] = time.monotonic()-start
    summary["numeric_file_sha256"] = hashlib.sha256((output/"generation.npz").read_bytes()).hexdigest()
    (output/"generation.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps({"sets": list(cfg["sets"]), "variants": cfg["variants"],
                      "arrays": len(arrays), "wall_seconds": summary["wall_seconds"]}))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
