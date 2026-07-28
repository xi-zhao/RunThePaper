#!/usr/bin/env python3
"""Reproduce Fig. 11: spectral functions of the App. A phenomenological model.

The model (Eqs. A1-A3): an observable couples to N >> 1 slow modes with
uniform weights and Lorentzian-broadened Drude peaks,
|f(omega)|^2 ~ (D0/N) sum_j (1/pi) Gamma_j / (omega^2 + Gamma_j^2),
with relaxation rates Gamma_j drawn from p(Gamma) ~ Gamma^(zeta-2) on
[Gamma_min, Gamma_max].

Source boundary: the paper's printed Eq. (explanation) uses
Gamma^(zeta+1) in the continuum integrand. Multiplying its immediately
preceding p(Gamma) by the Lorentzian numerator gives Gamma^(zeta-1),
which is also the only power consistent with the paper's following
omega^-(2-zeta) claim. This script implements that internally consistent
construction by sampling p(Gamma) and averaging the Lorentzians directly.

Two limiting scenarios (the two panels):
(a) fading ergodicity: Gamma_min ~ Gamma_max - a single Lorentzian whose
    width tracks Gamma (~ 1/Z at the transition);
(b) slowing down of polynomial relaxation: Gamma_max >> Gamma_min - a
    power-law envelope ~ omega^-(2-zeta) emerges between the cutoffs.
    The paper fits b*omega^-a and reports a ~ 0.52 (zeta ~ 1.48).

Gates: the sampled model reproduces the analytic envelope exponent, and
with the paper's zeta the fitted exponent matches a ~ 0.52.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if ROOT.name == "code":
    ROOT = ROOT.parent
FIGURE_PATH = ROOT / "outputs/figures/fig11_phenomenological_model.png"
DATA_PATH = ROOT / "outputs/data/fig11_model_curves.csv"
CHECK_PATH = ROOT / "outputs/checks/fig11_phenomenological_model.json"

PAPER_A = 0.52
ZETA = 2.0 - PAPER_A          # paper's fitted exponent implies zeta ~ 1.48
GAMMA_MIN, GAMMA_MAX = 1e-4, 1.0
N_MODES = 200_000
SEED = 25594


def sample_rates(rng: np.random.Generator) -> np.ndarray:
    """Inverse-CDF sampling of p(Gamma) ~ Gamma^(zeta-2) on [min, max]."""

    exponent = ZETA - 1.0  # CDF ~ Gamma^(zeta-1)
    u = rng.random(N_MODES)
    lo, hi = GAMMA_MIN**exponent, GAMMA_MAX**exponent
    return (lo + u * (hi - lo)) ** (1.0 / exponent)


def spectral_function(omega: np.ndarray, gammas: np.ndarray) -> np.ndarray:
    total = np.zeros_like(omega)
    for chunk in np.array_split(gammas, 40):
        total += np.sum(
            chunk[None, :] / np.pi / (omega[:, None] ** 2 + chunk[None, :] ** 2),
            axis=1,
        )
    return total / len(gammas)


def main() -> int:
    rng = np.random.default_rng(SEED)
    omega = np.logspace(-3.6, 0.0, 160)

    # (b) polynomial-relaxation scenario
    gammas = sample_rates(rng)
    f2_poly = spectral_function(omega, gammas)
    window = (omega >= 1e-3) & (omega <= 1e-1)  # the paper's plotted fit range
    slope, intercept = np.polyfit(np.log(omega[window]), np.log(f2_poly[window]), 1)
    a_fit = -slope

    # (a) fading-ergodicity scenario: single rate, family over Gamma ~ 1/Z
    gamma_family = [3e-3, 1e-2, 3e-2]
    f2_fading = {g: g / np.pi / (omega**2 + g**2) for g in gamma_family}
    halfwidth_ratio = [
        float(omega[np.argmin(np.abs(f2 - f2.max() / 2.0))] / g)
        for g, f2 in f2_fading.items()
    ]

    gate_flags = {
        "power_law_envelope_emerges": bool(abs(a_fit - (2.0 - ZETA)) < 0.06),
        "fit_matches_paper_a": bool(abs(a_fit - PAPER_A) < 0.06),
        "fading_ergodicity_is_lorentzian": bool(
            all(abs(r - 1.0) < 0.15 for r in halfwidth_ratio)
        ),
    }

    with DATA_PATH.open("w") as handle:
        handle.write("omega,f2_polynomial," + ",".join(f"f2_fading_G{g:g}" for g in gamma_family) + "\n")
        for i, w in enumerate(omega):
            handle.write(
                f"{w:.6e},{f2_poly[i]:.6e},"
                + ",".join(f"{f2_fading[g][i]:.6e}" for g in gamma_family)
                + "\n"
            )

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for g in gamma_family:
        axes[0].loglog(omega, f2_fading[g], label=rf"$\Gamma={g:g}$")
    axes[0].set_xlabel(r"$\omega$")
    axes[0].set_ylabel(r"$|f(\omega)|^2$")
    axes[0].set_title("(a) fading ergodicity: single Lorentzian family", fontsize=10)
    axes[0].legend(fontsize=8)
    axes[1].loglog(omega, f2_poly, ".", color="0.4", markersize=4, label="model")
    fit_line = np.exp(intercept) * omega[window] ** slope
    axes[1].loglog(omega[window], fit_line, "-", color="tab:red",
                   label=rf"$b\,\omega^{{-a}}$, $a={a_fit:.2f}$ (paper $\approx${PAPER_A})")
    axes[1].axvline(GAMMA_MIN, color="0.8", ls=":")
    axes[1].axvline(GAMMA_MAX, color="0.8", ls=":")
    axes[1].set_xlabel(r"$\omega$")
    axes[1].set_ylabel(r"$|f(\omega)|^2$")
    axes[1].set_title("(b) polynomial relaxation: power-law envelope", fontsize=10)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=150)
    plt.close(fig)

    checks = {
        "target": "T009",
        "figure": "Fig. 11",
        "status": "physically_consistent" if all(gate_flags.values()) else "partial",
        "model": "App. A LIOM Drude-broadening model, Eqs. (A1)-(A3)",
        "parameters": {
            "zeta": ZETA, "gamma_min": GAMMA_MIN, "gamma_max": GAMMA_MAX,
            "n_modes": N_MODES, "seed": SEED,
        },
        "fitted_exponent_a": round(float(a_fit), 4),
        "paper_exponent_a": PAPER_A,
        "analytic_envelope_exponent": round(2.0 - ZETA, 4),
        "fading_halfwidth_over_gamma": [round(r, 3) for r in halfwidth_ratio],
        "gate_flags": gate_flags,
        "data": "outputs/data/fig11_model_curves.csv",
        "figure_path": "outputs/figures/fig11_phenomenological_model.png",
        "notes": [
            "The paper selected panel-(b) parameters to best match its Fig. 3(b) at V=38^3; our gate is the model's analytic self-consistency plus the paper's reported exponent a~0.52.",
            "The printed Eq. (explanation) has Gamma^(zeta+1), but p(Gamma) times the Lorentzian numerator gives Gamma^(zeta-1), the power required for the stated omega^-(2-zeta) envelope; this script uses the internally consistent construction.",
        ],
    }
    CHECK_PATH.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps({k: checks[k] for k in ["status", "gate_flags", "fitted_exponent_a"]}, indent=2))
    return 0 if checks["status"] == "physically_consistent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
