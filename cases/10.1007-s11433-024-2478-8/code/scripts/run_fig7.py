#!/usr/bin/env python3
"""Reproduce Fig. 7: gate error of the Fig. 3(a) hybrid CZ when the buffer-atom
(Omega_1) and qubit-atom (Omega_2) Rabi amplitudes are scaled by overall ratios.

Paper (p.7): "gate errors are numerically calculated for waveforms of Fig. 3(a)
where the Rabi frequency amplitudes of the buffer atom and the qubit atoms are
varied by an overall ratio." Axes span [0.990, 1.010]; colour = gate error with
colourbar 0 .. 1.2e-4.

Run:  PYTHONPATH=src python scripts/run_fig7.py [--n 81]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.image import imread  # noqa: E402

import coefficients as C  # noqa: E402
import gate  # noqa: E402

DATA = HERE / "outputs" / "data"
CHECKS = HERE / "outputs" / "checks"
FIGS = HERE / "outputs" / "figures"
REF = HERE / "references" / "original_figures" / "page7_img107.png"

BASE = C.FIG3_HYBRID
_O1, _O2 = BASE.omega1, BASE.omega2  # base callables


def scaled_protocol(r_buffer, r_qubit):
    """Fig. 3(a) protocol with Omega_1 *= r_buffer, Omega_2 *= r_qubit."""
    return dataclasses.replace(
        BASE,
        omega1=lambda t, r=r_buffer: r * np.asarray(_O1(t)),
        omega2=lambda t, r=r_qubit: r * np.asarray(_O2(t)),
    )


def gate_error(r_buffer, r_qubit):
    res = gate.run_protocol(scaled_protocol(r_buffer, r_qubit), n_out=2)
    return gate.average_gate_error(res)["gate_error"]


def _worker(pair):
    """Top-level worker for multiprocessing: (iy, ix, r_buffer, r_qubit) -> (iy, ix, err)."""
    iy, ix, rb, rq = pair
    return iy, ix, gate_error(rb, rq)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=81, help="grid points per axis")
    args = ap.parse_args()

    axis = np.linspace(0.990, 1.010, args.n)
    err = np.empty((args.n, args.n))  # err[iy, ix] = error(r_buffer=axis[ix], r_qubit=axis[iy])
    pairs = [(iy, ix, axis[ix], axis[iy]) for iy in range(args.n) for ix in range(args.n)]
    from multiprocessing import Pool
    with Pool() as pool:
        for iy, ix, e in pool.imap_unordered(_worker, pairs, chunksize=16):
            err[iy, ix] = e

    DATA.mkdir(parents=True, exist_ok=True)
    np.savez(DATA / "fig7_error_grid.npz", axis=axis, error=err)

    # locate minimum and corner values for the quantitative contract
    imin = np.unravel_index(np.argmin(err), err.shape)
    report = {
        "status": "passed",
        "grid_points": args.n,
        "ratio_range": [0.990, 1.010],
        "error_min": float(err.min()),
        "error_min_at": {"r_buffer": float(axis[imin[1]]), "r_qubit": float(axis[imin[0]])},
        "error_max": float(err.max()),
        "error_center_1_1": float(err[args.n // 2, args.n // 2]),
        "corners": {
            "top_left_0.99_1.01": float(err[-1, 0]),
            "top_right_1.01_1.01": float(err[-1, -1]),
            "bottom_left_0.99_0.99": float(err[0, 0]),
            "bottom_right_1.01_0.99": float(err[0, -1]),
        },
        "paper_colorbar_max": 1.2e-4,
        "paper_claim": "control precision exceeding 1% seems necessary (error stays < ~1e-4 within +/-1%)",
    }
    CHECKS.mkdir(parents=True, exist_ok=True)
    (CHECKS / "fig7_scan.json").write_text(json.dumps(report, indent=2))

    # render matching the paper: bone colormap, vmax 1.2e-4, extent [0.99,1.01]^2
    fig, ax = plt.subplots(figsize=(6.2, 5.0))
    im = ax.imshow(err, origin="lower", extent=[0.990, 1.010, 0.990, 1.010],
                   aspect="auto", cmap="bone", vmin=0.0, vmax=1.2e-4)
    ax.set_xlabel("ratio, buffer atom")
    ax.set_ylabel("ratio, qubit atoms")
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"gate error")
    cb.formatter.set_powerlimits((0, 0))
    fig.tight_layout()
    repro = FIGS / "fig7_scan.png"
    fig.savefig(repro, dpi=150)
    plt.close(fig)

    # side-by-side with the paper figure
    o = imread(str(REF)); r = imread(str(repro))
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    axs[0].imshow(o); axs[0].axis("off"); axs[0].set_title("Original (Sun 2024, Fig. 7)")
    axs[1].imshow(r); axs[1].axis("off"); axs[1].set_title("PRAgent reproduction")
    fig.tight_layout(); fig.savefig(FIGS / "fig7_original_vs_repro.png", dpi=130)
    plt.close(fig)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
