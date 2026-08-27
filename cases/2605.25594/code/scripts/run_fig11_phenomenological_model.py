#!/usr/bin/env python3
"""Reproduce Appendix Fig. A00: phenomenological spectral functions.

The model (Eqs. A1-A3): an observable couples to N >> 1 slow modes with
uniform weights and Lorentzian-broadened Drude peaks,
|f(omega)|^2 ~ (D0/N) sum_j (1/pi) Gamma_j / (omega^2 + Gamma_j^2),
with relaxation rates Gamma_j drawn from p(Gamma) ~ Gamma^(zeta-2) on
[Gamma_min, Gamma_max].

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

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/figA00_phenomenology.json"
FIGURE_PATH = ROOT / "outputs/figures/fig11_phenomenological_model.png"
DATA_PATH = ROOT / "outputs/data/fig11_model_curves.csv"
CHECK_PATH = ROOT / "outputs/checks/fig11_phenomenological_model.json"


def load_config(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2605.25594" or config.get("target_id") != "T009":
        raise ValueError("Fig. A00 configuration is bound to the wrong paper or target")
    boundary = config.get("numerical_input_boundary", {})
    if any(boundary.values()):
        raise ValueError(
            "The numerical runner must not read paper or reference artifacts"
        )
    return config


def sample_rates(rng: np.random.Generator, config: dict) -> np.ndarray:
    """Inverse-CDF sampling of p(Gamma) ~ Gamma^(zeta-2) on [min, max]."""

    exponent = float(config["zeta"]) - 1.0  # CDF ~ Gamma^(zeta-1)
    u = rng.random(int(config["n_modes"]))
    lo = float(config["gamma_min"]) ** exponent
    hi = float(config["gamma_max"]) ** exponent
    return (lo + u * (hi - lo)) ** (1.0 / exponent)


def spectral_function(
    omega: np.ndarray, gammas: np.ndarray, spectral_chunks: int
) -> np.ndarray:
    total = np.zeros_like(omega)
    for chunk in np.array_split(gammas, spectral_chunks):
        total += np.sum(
            chunk[None, :] / np.pi / (omega[:, None] ** 2 + chunk[None, :] ** 2),
            axis=1,
        )
    return total / len(gammas)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Freeze numerical CSV/check artifacts without importing plotting libraries.",
    )
    args = parser.parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not args.no_render:
        FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    config_sha256 = hashlib.sha256(config_path.read_bytes()).hexdigest()
    paper_a = float(config["paper_exponent_a"])
    zeta = float(config["zeta"])
    gamma_min = float(config["gamma_min"])
    gamma_max = float(config["gamma_max"])
    rng = np.random.default_rng(int(config["seed"]))
    omega = np.logspace(
        float(config["omega_log10_min"]),
        float(config["omega_log10_max"]),
        int(config["omega_points"]),
    )

    # (b) polynomial-relaxation scenario
    gammas = sample_rates(rng, config)
    f2_poly = spectral_function(omega, gammas, int(config["spectral_chunks"]))
    window = (omega >= float(config["fit_omega_min"])) & (
        omega <= float(config["fit_omega_max"])
    )
    slope, intercept = np.polyfit(np.log(omega[window]), np.log(f2_poly[window]), 1)
    a_fit = -slope

    # (a) fading-ergodicity scenario: single rate, family over Gamma ~ 1/Z
    gamma_family = [float(value) for value in config["gamma_family"]]
    f2_fading = {g: g / np.pi / (omega**2 + g**2) for g in gamma_family}
    halfwidth_ratio = [
        float(omega[np.argmin(np.abs(f2 - f2.max() / 2.0))] / g)
        for g, f2 in f2_fading.items()
    ]

    exponent_tolerance = float(config["acceptance"]["exponent_abs_tolerance"])
    halfwidth_tolerance = float(config["acceptance"]["halfwidth_ratio_abs_tolerance"])
    gate_flags = {
        "power_law_envelope_emerges": bool(
            abs(a_fit - (2.0 - zeta)) < exponent_tolerance
        ),
        "fit_matches_paper_a": bool(abs(a_fit - paper_a) < exponent_tolerance),
        "fading_ergodicity_is_lorentzian": bool(
            all(abs(r - 1.0) < halfwidth_tolerance for r in halfwidth_ratio)
        ),
    }

    with DATA_PATH.open("w") as handle:
        handle.write(
            "omega,f2_polynomial,"
            + ",".join(f"f2_fading_G{g:g}" for g in gamma_family)
            + "\n"
        )
        for i, w in enumerate(omega):
            handle.write(
                f"{w:.6e},{f2_poly[i]:.6e},"
                + ",".join(f"{f2_fading[g][i]:.6e}" for g in gamma_family)
                + "\n"
            )

    if not args.no_render:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
        for g in gamma_family:
            axes[0].loglog(omega, f2_fading[g], label=rf"$\Gamma={g:g}$")
        axes[0].set_xlabel(r"$\omega$")
        axes[0].set_ylabel(r"$|f(\omega)|^2$")
        axes[0].set_title("(a) fading ergodicity: single Lorentzian family", fontsize=10)
        axes[0].legend(fontsize=8)
        axes[1].loglog(omega, f2_poly, ".", color="0.4", markersize=4, label="model")
        fit_line = np.exp(intercept) * omega[window] ** slope
        axes[1].loglog(
            omega[window],
            fit_line,
            "-",
            color="tab:red",
            label=rf"$b\,\omega^{{-a}}$, $a={a_fit:.2f}$ (paper $\approx${paper_a})",
        )
        axes[1].axvline(gamma_min, color="0.8", ls=":")
        axes[1].axvline(gamma_max, color="0.8", ls=":")
        axes[1].set_xlabel(r"$\omega$")
        axes[1].set_ylabel(r"$|f(\omega)|^2$")
        axes[1].set_title("(b) polynomial relaxation: power-law envelope", fontsize=10)
        axes[1].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(FIGURE_PATH, dpi=150)
        plt.close(fig)

    checks = {
        "target": "T009",
        "figure": "Appendix Fig. A00",
        "status": "physically_consistent" if all(gate_flags.values()) else "partial",
        "model": "App. A LIOM Drude-broadening model, Eqs. (A1)-(A3)",
        "config": "config/figA00_phenomenology.json",
        "config_sha256": config_sha256,
        "parameters": {
            "zeta": zeta,
            "gamma_min": gamma_min,
            "gamma_max": gamma_max,
            "n_modes": int(config["n_modes"]),
            "seed": int(config["seed"]),
        },
        "fitted_exponent_a": round(float(a_fit), 4),
        "paper_exponent_a": paper_a,
        "analytic_envelope_exponent": round(2.0 - zeta, 4),
        "fading_halfwidth_over_gamma": [round(r, 3) for r in halfwidth_ratio],
        "gate_flags": gate_flags,
        "data": "outputs/data/fig11_model_curves.csv",
        "figure_path": (
            "outputs/figures/fig11_phenomenological_model.png"
            if not args.no_render
            else None
        ),
        "render_status": "generated" if not args.no_render else "deferred_post_freeze",
        "legacy_filename_note": "The retained fig11_* filenames predate the full-paper audit; their scientific identity is Appendix Fig. A00.",
        "notes": [
            "The paper selected panel-(b) parameters to best match its Fig. 3(b) at V=38^3; our gate is the model's analytic self-consistency plus the paper's reported exponent a~0.52.",
        ],
    }
    CHECK_PATH.write_text(json.dumps(checks, indent=2) + "\n")
    print(
        json.dumps(
            {k: checks[k] for k in ["status", "gate_flags", "fitted_exponent_a"]},
            indent=2,
        )
    )
    return 0 if checks["status"] == "physically_consistent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
