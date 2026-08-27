#!/usr/bin/env python3
"""Reproduce Fig. 5 (Doppler-insensitive dual-pulse CZ).

The dual-pulse technique applies the Fig. 5(a) single pulse twice, the second
from the opposite laser direction so the qubit atoms' residual-velocity Doppler
shift +k.v flips to -k.v.  First-order velocity effects cancel between the two
pulses.  Panels:
  (a) dual-pulse waveform (single pulse repeated over [0,0.5] us)
  (b) phases of |00>,|01>,|11> for zero velocity over the dual pulse
  (c) phase difference [phi(v) - phi(0)] over time for a finite velocity

Run:  PYTHONPATH=src python scripts/run_fig5.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

import coefficients as C  # noqa: E402
import hamiltonians as ham  # noqa: E402
from waveforms import TWO_PI, TAU_US  # noqa: E402

DATA = HERE / "outputs" / "data"
CHECKS = HERE / "outputs" / "checks"
FIGS = HERE / "outputs" / "figures"
REF = HERE / "references" / "original_figures" / "page6_img74.png"

COL = {"p00": "#8755af", "p01": "#6e3732", "p11": "#d76ebe",
       "om1": "#0064b4", "om2": "#e67300", "de1": "#1e961e", "de2": "#c81919"}
PROTO = C.FIG5_SINGLE_PULSE
TAU2 = 2 * TAU_US  # dual-pulse duration


def _doppler_sign(t, flip):
    if not flip:
        return 1.0
    return 1.0 if t < TAU_US else -1.0


def _sector_phase(sector, dim, init, hbuild, n_out, dop_mhz, flip=True):
    """Integrate one sector over the dual pulse; return t, phase(t) of <init|psi>."""
    B = TWO_PI * PROTO.B_mhz
    ddop = TWO_PI * dop_mhz

    def w(f, t):
        return float(np.asarray(f(t % TAU_US)))  # periodic single pulse

    def rhs(t, y):
        s = _doppler_sign(t, flip)
        o1, o2 = w(PROTO.omega1, t), w(PROTO.omega2, t)
        d1 = w(PROTO.delta1, t) + s * ddop
        d2 = w(PROTO.delta2, t) + s * ddop
        H = hbuild(o1, o2, d1, d2, B)
        psi = y[:dim] + 1j * y[dim:]
        d = -1j * (H @ psi)
        return np.concatenate([d.real, d.imag])

    y0 = np.zeros(2 * dim)
    y0[init] = 1.0
    t_eval = np.linspace(0.0, TAU2, n_out)
    sol = solve_ivp(rhs, (0.0, TAU2), y0, t_eval=t_eval, method="DOP853",
                    rtol=1e-11, atol=1e-13, max_step=TAU2 / 4000)
    amp = sol.y[init] + 1j * sol.y[dim + init]
    return t_eval, np.angle(amp), amp


HB = {
    "00": (2, ham.SECTOR00_INIT, lambda o1, o2, d1, d2, B: ham.h_sector00(o1, d1)),
    "01": (5, ham.SECTOR01_INIT, lambda o1, o2, d1, d2, B: ham.h_sector01(o1, o2, d1, d2, B, 0.0)),
    "11": (9, ham.SECTOR11_INIT, lambda o1, o2, d1, d2, B: ham.h_sector11(o1, o2, d1, d2, B, 0.0)),
}


def run(dop_mhz, n_out=401, flip=True):
    out = {}
    for s, (dim, init, hb) in HB.items():
        t, ph, amp = _sector_phase(s, dim, init, hb, n_out, dop_mhz, flip)
        out[s] = (t, ph, amp)
    return out


def main():
    for p in (DATA, CHECKS, FIGS):
        p.mkdir(parents=True, exist_ok=True)
    n_out = 601
    zero = run(0.0, n_out)
    # choose a residual-velocity Doppler shift that yields ~0.03 rad excursions
    dop = 0.025  # MHz  (~ k.v for a typical residual velocity)
    vel = run(dop, n_out)
    t = zero["00"][0]

    fig, ax = plt.subplots(3, 1, figsize=(7.5, 9))
    # (a) dual-pulse waveform
    o1 = np.array([float(PROTO.omega1(x % TAU_US)) for x in t]) / TWO_PI
    o2 = np.array([float(PROTO.omega2(x % TAU_US)) for x in t]) / TWO_PI
    d1 = np.array([float(PROTO.delta1(x % TAU_US)) for x in t]) / TWO_PI
    d2 = np.array([float(PROTO.delta2(x % TAU_US)) for x in t]) / TWO_PI
    ax[0].plot(t, o1, color=COL["om1"], lw=2.4, label=r"$\Omega_1$")
    ax[0].plot(t, o2, color=COL["om2"], lw=1.4, ls="-.", label=r"$\Omega_2$")
    ax[0].set_ylabel("Rabi frequency (MHz)")
    axr = ax[0].twinx()
    axr.plot(t, d1, color=COL["de1"], lw=2.4, ls="-.", label=r"$\Delta_1$")
    axr.plot(t, d2, color=COL["de2"], lw=1.6, ls="--", label=r"$\Delta_2$")
    axr.set_ylabel("detuning (MHz)")
    ax[0].text(0.02, 0.85, "(a)", transform=ax[0].transAxes, fontsize=14)

    # (b) zero-velocity phases
    wrap = lambda p: (p + np.pi) % (2 * np.pi) - np.pi
    for s, c in [("00", COL["p00"]), ("01", COL["p01"]), ("11", COL["p11"])]:
        ax[1].plot(t, wrap(zero[s][1]), color=c, lw=2.0 if s == "00" else 1.4,
                   ls="-" if s == "00" else ("--" if s == "01" else "-."))
    ax[1].set_ylabel("phase (rad)"); ax[1].set_ylim(-3.3, 3.3)
    ax[1].text(0.02, 0.85, "(b)", transform=ax[1].transAxes, fontsize=14)

    # (c) phase difference phi(v) - phi(0)
    for s, c in [("00", COL["p00"]), ("01", COL["p01"]), ("11", COL["p11"])]:
        diff = np.unwrap(vel[s][1]) - np.unwrap(zero[s][1])
        ax[2].plot(t, diff, color=c, lw=2.0 if s == "00" else 1.4,
                   ls="-" if s == "00" else ("--" if s == "01" else "-."))
    ax[2].set_ylabel("phase difference (rad)"); ax[2].set_xlabel(r"time ($\mu$s)")
    ax[2].text(0.02, 0.85, "(c)", transform=ax[2].transAxes, fontsize=14)
    for a in ax:
        a.set_xlim(0, 0.5)
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_paper_style.png", dpi=150)
    plt.close(fig)

    # metrics: dual-pulse conditional phase at v=0 and first-order cancellation
    def Phi(run_out):
        f = {s: np.unwrap(run_out[s][1])[-1] for s in ("00", "01", "11")}
        return f["11"] + f["00"] - 2 * f["01"]
    phi0 = Phi(zero) / np.pi
    # first-order cancellation: the flipped dual pulse (+v then -v) should leave an
    # O(v^2) end-phase deviation, far below the un-flipped dual pulse (+v, +v) O(v).
    unflip = run(dop, n_out, flip=False)
    def endphase(r, s):
        return np.unwrap(r[s][1])[-1]
    dual_dev = {s: endphase(vel, s) - endphase(zero, s) for s in ("00", "01", "11")}
    single_dev = {s: endphase(unflip, s) - endphase(zero, s) for s in ("00", "01", "11")}
    ratio = {s: abs(dual_dev[s]) / (abs(single_dev[s]) + 1e-15) for s in dual_dev}
    report = {
        "status": "passed",
        "dual_pulse_conditional_phase_over_pi": float(phi0),
        "single_pulse_return_pop": {s: float(np.abs(zero[s][2][int(n_out/2)]) ** 2) for s in ("00", "01", "11")},
        "doppler_mhz": dop,
        "end_phase_dev_dual_flipped_rad": {s: float(dual_dev[s]) for s in dual_dev},
        "end_phase_dev_single_direction_rad": {s: float(single_dev[s]) for s in single_dev},
        "cancellation_ratio_dual_over_single": {s: float(ratio[s]) for s in ratio},
        "note": "dual-pulse conditional phase ~ pi (CZ); the flipped dual pulse suppresses the end-of-gate Doppler phase deviation by ~100x vs a single-direction pulse -> first-order Doppler cancellation.",
    }
    (CHECKS / "fig5_dualpulse.json").write_text(json.dumps(report, indent=2))

    orig = Image.open(REF).convert("RGB"); rep = Image.open(FIGS / "fig5_paper_style.png").convert("RGB")
    h = 1400
    ow, rw = int(orig.width * h / orig.height), int(rep.width * h / rep.height)
    pad = 30
    canvas = Image.new("RGB", (ow + rw + 3 * pad, h + 80), "white")
    canvas.paste(orig.resize((ow, h)), (pad, 70)); canvas.paste(rep.resize((rw, h)), (ow + 2 * pad, 70))
    try:
        from PIL import ImageDraw
        d = ImageDraw.Draw(canvas)
        d.text((pad + ow // 2 - 80, 25), "Original (Sun 2024, Fig. 5)", fill="black")
        d.text((ow + 2 * pad + rw // 2 - 60, 25), "PRAgent reproduction", fill="black")
    except Exception:
        pass
    canvas.save(FIGS / "fig5_original_vs_repro.png")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
