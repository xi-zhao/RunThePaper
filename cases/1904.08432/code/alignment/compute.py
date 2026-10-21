"""Equation-derived controls; no author curves or digitized ordinates are read.

This is a source-aware follow-up, not a fresh blind reproduction. NumPy/SciPy
and the existing model/analytic propagator are reused; the affine steady-state
solve and reference selection are now exercised explicitly.
"""
from pathlib import Path
import json
import warnings
import numpy as np
from scipy.linalg import expm, solve_continuous_lyapunov
from threadpoolctl import threadpool_limits

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]])


def realspace(length, gl=.2, gg=.2, t1=1., t2=1., periodic=True):
    h = np.zeros((2*length, 2*length), complex)
    for cell in range(length):
        a, b = 2*cell, 2*cell+1
        h[a, b] = h[b, a] = t1
        if cell < length-1:
            h[b, b+1] = h[b+1, b] = t2
    if periodic:
        h[0, -1] = h[-1, 0] = t2
    ml = np.kron(np.eye(length), gl/2*(np.eye(2)+SY))
    mg = np.kron(np.eye(length), gg/2*(np.eye(2)-SY))
    return 1j*h.T-ml.T-mg, mg


def filled_deviation(length, times, gl=.2, gg=.2, t1=1., t2=1.):
    """Cell density relative to (gg/gamma) I, evaluated without eigendecomposition."""
    times = np.asarray(times)
    k = 2*np.pi*np.arange(length)/length
    gamma = gl+gg
    b = 1j*((t1+t2*np.cos(k))[:, None, None]*SX
            + (t2*np.sin(k)-1j*gamma/2)[:, None, None]*SY)
    omega = np.sqrt(np.einsum("kij,kji->k", b, b)/2+0j)
    ep = np.exp(times[:, None]*(-gamma/2+omega))
    em = np.exp(times[:, None]*(-gamma/2-omega))
    a = (ep+em)/2
    f = np.empty_like(a)
    regular = abs(omega) > 1e-13
    f[:, regular] = (ep[:, regular]-em[:, regular])/(2*omega[regular])
    f[:, ~regular] = times[:, None]*np.exp(-gamma/2*times[:, None])
    return (1-gg/gamma)*np.mean(
        2*abs(a)**2+abs(f)**2*np.sum(abs(b)**2, axis=(1, 2)), axis=1)


def dark_projector(length):
    # Kernel vector of the real-space X at t1=t2, even L.
    if length % 2:
        return np.zeros((2*length, 2*length), complex)
    v = np.kron((-1.)**np.arange(length), [1, 1j])/np.sqrt(2*length)
    return np.outer(v, v.conj())


def main():
    cfg = json.loads(Path("config.json").read_text())
    t3 = np.arange(0, 80.25, .5)
    t2 = np.arange(0, 2000.25, .5)
    arrays = {"t3": t3, "t2": t2}
    arrays["lengths"] = np.array(cfg["candidate_lengths"])
    arrays["length_base"] = np.array([filled_deviation(l, t3)
                                      for l in cfg["candidate_lengths"]])
    arrays["fig2_A_base"] = filled_deviation(150, t2, .4, .4)
    result = {"solver_controls": [], "initial_state_controls": [],
              "identity": "Delta(0)=I; L counts unit cells (2L orbitals)",
              "reference_family": "C_eta=s(I-P)+eta P, s=gamma_g/gamma",
              "unfitted_offset": "n_eta(t)-n_s(t)=(s-eta)/L for an even critical ring",
              "author_solver_identity": "not established"}
    for length in cfg["solver_lengths"]:
        p = dark_projector(length)
        for gl, gg in cfg["solver_rates"]:
            x, mg = realspace(length, gl, gg)
            s = gg/(gl+gg)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                c = solve_continuous_lyapunov(x, -2*mg)
            expected = s*(np.eye(2*length)-p)
            item = {"length_cells": length, "gamma_l": gl, "gamma_g": gg,
                    "stationary_residual_max": float(np.max(abs(x@c+c@x.conj().T+2*mg))),
                    "distance_to_minimum_norm_max": float(np.max(abs(c-expected))),
                    "dark_occupation": float(np.trace(p@c).real),
                    "density_shift_vs_sI": float(2*s-np.trace(c).real/length),
                    "predicted_shift": s/length if length % 2 == 0 else 0.,
                    "warnings": [str(w.message) for w in caught]}
            result["solver_controls"].append(item)
            if gl == gg and length in (30, 60, 150):
                # Three references applied to the SAME physical evolution.
                ts = t2 if (length, gl) == (150, .4) else t3
                base = filled_deviation(length, ts, gl, gg)
                arrays[f"solver_L{length}_g{gl}"] = base+item["density_shift_vs_sI"]
                # Evaluate original matrix equation directly at selected times.
                physical = []
                for t in [0., 1., 10., 60.]:
                    e = expm(x*t)
                    ct = s*np.eye(2*length)+(1-s)*e@e.conj().T
                    physical.append(float(np.trace(ct-c).real/length))
                item["direct_times"] = [0., 1., 10., 60.]
                item["direct_deviations"] = physical
        if length in (30, 31, 60):
            x, mg = realspace(length)
            for f in cfg["initial_occupations"]:
                limit = .5*np.eye(2*length)+(f-.5)*p
                result["initial_state_controls"].append({
                    "length": length, "uniform_initial_filling": f,
                    "stationary_residual": float(np.max(abs(x@limit+limit@x.conj().T+2*mg))),
                    "initial_cell_density": 2*f,
                    "limit_cell_density": float(np.trace(limit).real/length),
                    "dark_occupation_initial": f if length % 2 == 0 else None})
    # Full rank controls: finite OBC, odd ring, and detuned even ring.
    result["nonsingular_controls"] = []
    for length, periodic, t1 in [(30, False, 1.), (31, True, 1.), (30, True, 1.1)]:
        x, mg = realspace(length, t1=t1, periodic=periodic)
        c = solve_continuous_lyapunov(x, -2*mg)
        result["nonsingular_controls"].append({
            "length": length, "periodic": periodic, "t1": t1,
            "distance_to_half_filled_max": float(np.max(abs(c-.5*np.eye(2*length))))})
    Path("results").mkdir(exist_ok=True)
    np.savez_compressed("results/generated.npz", **arrays)
    Path("results/generated.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"solver_controls": len(result["solver_controls"]),
                      "length_candidates": len(cfg["candidate_lengths"]),
                      "max_stationarity_residual": max(
                          a["stationary_residual_max"] for a in result["solver_controls"])}))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
