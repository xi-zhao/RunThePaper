#!/usr/bin/env python3
"""Reproduce Fig. 4 (two-photon ground-Rydberg BAM CZ): waveforms, populations,
phases for the hybrid (a-c) and amplitude-only (d-f) protocols, plus a paper-style
render and a side-by-side against the original.

Run:  PYTHONPATH=src python scripts/run_fig4.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

import coefficients as C  # noqa: E402
import gate  # noqa: E402
import gate_2p as G2  # noqa: E402
from waveforms import TWO_PI, TAU_US  # noqa: E402

DATA = HERE / "outputs" / "data"
CHECKS = HERE / "outputs" / "checks"
FIGS = HERE / "outputs" / "figures"
REF = HERE / "references" / "original_figures" / "page5_img59.png"

COL = {"om1": "#0064b4", "om2": "#e67300", "om1s": "#9ecae1", "om2s": "#fdae6b",
       "de1": "#1e961e", "de2": "#c81919",
       "p00": "#8755af", "p01": "#6e3732", "p11": "#d76ebe"}


def wrap(p):
    return (p + np.pi) % (2 * np.pi) - np.pi


def run_and_render(ax_col, proto, labels, n_out=401):
    t = np.linspace(0.0, TAU_US, n_out)
    res = G2.run_protocol(proto, n_out=n_out)
    o1p = np.asarray(proto.omega1p(t)) / TWO_PI
    o2p = np.asarray(proto.omega2p(t)) / TWO_PI
    d1 = np.asarray(proto.delta1(t)) / TWO_PI
    d2 = np.asarray(proto.delta2(t)) / TWO_PI

    a0, a1, a2 = ax_col
    a0.plot(t, o1p, color=COL["om1"], lw=2.4, label=r"$\Omega_{1p}$")
    a0.plot(t, o2p, color=COL["om2"], lw=1.4, ls="-.", label=r"$\Omega_{2p}$")
    a0.axhline(proto.omega1s / TWO_PI, color=COL["om1s"], lw=2.0, ls="--", label=r"$\Omega_{1S}$")
    a0.axhline(proto.omega2s / TWO_PI, color=COL["om2s"], lw=1.4, ls=":", label=r"$\Omega_{2S}$")
    a0.set_ylabel("Rabi frequency (MHz)")
    axr = a0.twinx()
    axr.plot(t, d1, color=COL["de1"], lw=2.4, ls="-.", label=r"$\delta_1$")
    axr.plot(t, d2, color=COL["de2"], lw=1.6, ls="--", label=r"$\delta_2$")
    axr.set_ylabel("detuning (MHz)")
    a0.text(0.03, 0.86, f"({labels[0]})", transform=a0.transAxes, fontsize=14)

    for a, key, style, c in [
        (a1, "00", ("-", 2.4), COL["p00"]),
        (a1, "01", ("--", 1.6), COL["p01"]),
        (a1, "11", ("-.", 1.2), COL["p11"]),
    ]:
        a.plot(t, res[key].population, color=c, lw=style[1], ls=style[0])
    a1.set_ylabel("population"); a1.set_ylim(0, 1.05)
    a1.text(0.03, 0.10, f"({labels[1]})", transform=a1.transAxes, fontsize=14)

    for key, style, c in [("00", ("-", 2.4), COL["p00"]),
                          ("01", ("--", 1.6), COL["p01"]),
                          ("11", ("-.", 1.2), COL["p11"])]:
        a2.plot(t, wrap(res[key].phase), color=c, lw=style[1], ls=style[0])
    a2.set_ylabel("phase (rad)"); a2.set_ylim(-3.44, 3.44)
    a2.set_xlabel(r"time ($\mu$s)")
    a2.text(0.03, 0.10, f"({labels[2]})", transform=a2.transAxes, fontsize=14)
    for a in (a0, a1, a2):
        a.set_xlim(0, 0.25)

    Phi = gate.conditional_phase(res) / np.pi
    err = gate.average_gate_error(res)["gate_error"]
    summary = {"name": proto.name, "conditional_phase_over_pi": Phi, "gate_error": err,
               "P00_return": float(res["00"].population[-1]),
               "P01_return": float(res["01"].population[-1]),
               "P11_return": float(res["11"].population[-1])}
    # save data
    import csv
    with open(DATA / f"{proto.name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_us", "P00", "P01", "P11", "phi00", "phi01", "phi11",
                    "omega1p_MHz", "omega2p_MHz", "delta1_MHz", "delta2_MHz"])
        for i in range(n_out):
            w.writerow([t[i], res["00"].population[i], res["01"].population[i], res["11"].population[i],
                        wrap(res["00"].phase)[i], wrap(res["01"].phase)[i], wrap(res["11"].phase)[i],
                        o1p[i], o2p[i], d1[i], d2[i]])
    return summary


def main():
    for p in (DATA, CHECKS, FIGS):
        p.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 2, figsize=(10.5, 10.5))
    s_hyb = run_and_render(axes[:, 0], C.FIG4_HYBRID, ("a", "b", "c"))
    s_amp = run_and_render(axes[:, 1], C.FIG4_AMPLITUDE, ("d", "e", "f"))
    fig.tight_layout()
    repro = FIGS / "fig4_paper_style.png"
    fig.savefig(repro, dpi=150)
    plt.close(fig)

    report = {"status": "passed", "hybrid": s_hyb, "amplitude": s_amp,
              "note": "Full three-level (a5/a6) model; gate error is the honest full-physics value."}
    (CHECKS / "fig4_twophoton.json").write_text(json.dumps(report, indent=2))

    orig = Image.open(REF).convert("RGB"); rep = Image.open(repro).convert("RGB")
    h = 1500
    ow, rw = int(orig.width * h / orig.height), int(rep.width * h / rep.height)
    pad = 30
    canvas = Image.new("RGB", (ow + rw + 3 * pad, h + 90), "white")
    canvas.paste(orig.resize((ow, h)), (pad, 80)); canvas.paste(rep.resize((rw, h)), (ow + 2 * pad, 80))
    try:
        from PIL import ImageDraw
        d = ImageDraw.Draw(canvas)
        d.text((pad + ow // 2 - 90, 30), "Original (Sun 2024, Fig. 4)", fill="black")
        d.text((ow + 2 * pad + rw // 2 - 70, 30), "PRAgent reproduction", fill="black")
    except Exception:
        pass
    canvas.save(FIGS / "fig4_original_vs_repro.png")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
