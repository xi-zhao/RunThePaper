#!/usr/bin/env python3
"""Reproduce Figure 3 of Sun 2024 (single-photon BAM/ORMD CZ gate).

Generates, for both the hybrid (a-c) and amplitude-only (d-f) protocols:
  * structured data  -> outputs/data/fig3_<proto>.csv  (+ summary json)
  * gate checks       -> outputs/checks/fig3_<proto>.json
  * a 3-panel figure  -> outputs/figures/fig3_<proto>.png

Run:  PYTHONPATH=src python scripts/run_fig3.py
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

import coefficients as C  # noqa: E402
import gate  # noqa: E402
from waveforms import TAU_US, TWO_PI  # noqa: E402

DATA = HERE / "outputs" / "data"
CHECKS = HERE / "outputs" / "checks"
FIGS = HERE / "outputs" / "figures"
for d in (DATA, CHECKS, FIGS):
    d.mkdir(parents=True, exist_ok=True)


def waveform_table(proto, t):
    return {
        "omega1_MHz": np.asarray(proto.omega1(t)) / TWO_PI,
        "omega2_MHz": np.asarray(proto.omega2(t)) / TWO_PI,
        "delta1_MHz": np.asarray(proto.delta1(t)) / TWO_PI,
        "delta2_MHz": np.asarray(proto.delta2(t)) / TWO_PI,
    }


def run_one(proto, panel_labels):
    t = np.linspace(0.0, TAU_US, 401)
    wf = waveform_table(proto, t)
    res = gate.run_protocol(proto, n_out=401)
    summary = gate.summarize(res)

    # --- structured data ---
    header = ["t_us", "omega1_MHz", "omega2_MHz", "delta1_MHz", "delta2_MHz",
              "P00", "P01", "P11", "phi00_rad", "phi01_rad", "phi11_rad"]
    cols = [t, wf["omega1_MHz"], wf["omega2_MHz"], wf["delta1_MHz"], wf["delta2_MHz"],
            res["00"].population, res["01"].population, res["11"].population,
            res["00"].phase, res["01"].phase, res["11"].phase]
    arr = np.column_stack(cols)
    csv_path = DATA / f"{proto.name}.csv"
    np.savetxt(csv_path, arr, delimiter=",", header=",".join(header), comments="")

    summary_path = DATA / f"{proto.name}_summary.json"
    summary_path.write_text(json.dumps(
        {"protocol": proto.name, "source": proto.source,
         "B_MHz": proto.B_mhz, "tau_us": TAU_US, **summary}, indent=2))

    # --- gate checks (with pass/fail against paper claims + sanity) ---
    checks = {
        "protocol": proto.name,
        "source": proto.source,
        "claims": {
            "gate_error_below_1e-4": bool(summary["gate_error"] < 1e-4),
            "conditional_phase_is_pi": bool(abs(abs(summary["conditional_phase_over_pi"]) - 1.0) < 5e-3),
            "populations_return": bool(summary["max_leakage"] < 5e-4),
        },
        "sanity": {
            "unitary_norm_drift_below_1e-9": bool(summary["max_norm_drift"] < 1e-9),
            "antisymmetric_dark_below_1e-10": bool(summary["max_dark_population_11"] < 1e-10),
            "waveform_turn_on_zero": bool(abs(wf["omega2_MHz"][0]) < 0.2),
        },
        "values": summary,
    }
    checks["all_pass"] = all(checks["claims"].values()) and all(checks["sanity"].values())
    checks["status"] = "passed" if checks["all_pass"] else "failed"
    (CHECKS / f"{proto.name}.json").write_text(json.dumps(checks, indent=2))

    # --- figure (3 panels stacked, replicating Fig. 3 columns) ---
    fig, ax = plt.subplots(3, 1, figsize=(6.2, 8.4), sharex=True)
    a, b, c = ax
    a.plot(t, wf["omega1_MHz"], color="#1f77b4", lw=2, label=r"$\Omega_1$")
    a.plot(t, wf["omega2_MHz"], color="#17becf", lw=1.5, ls="-", label=r"$\Omega_2$")
    a.set_ylabel("Rabi frequency (MHz)")
    a2 = a.twinx()
    a2.plot(t, wf["delta1_MHz"], color="#ff7f0e", ls="--", lw=1.5, label=r"$\Delta_1$")
    a2.plot(t, wf["delta2_MHz"], color="#2ca02c", ls="-.", lw=1.5, label=r"$\Delta_2$")
    a2.set_ylabel("detuning (MHz)")
    a.set_title(f"({panel_labels[0]}) waveforms  [{proto.name}]")
    lines = a.get_lines() + a2.get_lines()
    a.legend(lines, [l.get_label() for l in lines], fontsize=8, loc="upper right")

    b.plot(t, res["00"].population, color="#6a51a3", lw=2, label=r"$|00\rangle$")
    b.plot(t, res["01"].population, color="#d62728", ls="--", lw=1.5, label=r"$|01\rangle$ or $|10\rangle$")
    b.plot(t, res["11"].population, color="#e377c2", ls=":", lw=1.8, label=r"$|11\rangle$")
    b.set_ylabel("population")
    b.set_title(f"({panel_labels[1]}) return populations")
    b.legend(fontsize=8, loc="lower center")

    def wrap(p):
        return (p + np.pi) % (2 * np.pi) - np.pi
    c.plot(t, wrap(res["00"].phase), color="#6a51a3", lw=2, label=r"$|00\rangle$")
    c.plot(t, wrap(res["01"].phase), color="#d62728", ls="--", lw=1.5, label=r"$|01\rangle$ or $|10\rangle$")
    c.plot(t, wrap(res["11"].phase), color="#e377c2", ls=":", lw=1.8, label=r"$|11\rangle$")
    c.set_ylabel("phase (rad)")
    c.set_xlabel(r"time ($\mu$s)")
    c.set_ylim(-np.pi - 0.2, np.pi + 0.2)
    c.set_title(f"({panel_labels[2]}) phases (wrapped to $(-\\pi,\\pi]$, as in paper)")
    c.legend(fontsize=8, loc="upper left")

    fig.suptitle(
        f"Fig. 3 reproduction ({proto.name}): "
        f"gate error = {summary['gate_error']:.2e}, "
        f"cond. phase = {summary['conditional_phase_over_pi']:+.4f}$\\pi$",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(FIGS / f"{proto.name}.png", dpi=150)
    plt.close(fig)
    return summary, checks


def main():
    out = {}
    out["fig3_hybrid"] = run_one(C.FIG3_HYBRID, ("a", "b", "c"))
    out["fig3_amplitude"] = run_one(C.FIG3_AMPLITUDE, ("d", "e", "f"))
    for name, (summary, checks) in out.items():
        print(f"[{name}] gate_error={summary['gate_error']:.3e}  "
              f"cond_phase={summary['conditional_phase_over_pi']:+.5f}pi  "
              f"all_pass={checks['all_pass']}")


if __name__ == "__main__":
    main()
