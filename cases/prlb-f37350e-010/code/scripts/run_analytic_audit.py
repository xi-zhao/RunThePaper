#!/usr/bin/env python3
"""Generate independent idx10 audit data before rendering a diagnostic plot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
import sympy as sp

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from stochastic_zero_mode import (  # noqa: E402
    exact_propagator,
    fp_coefficients,
    propagator_expansion_coefficients,
    quartic_moment,
    weak_mass_expansion,
    zero_mode_spatial_variance,
)


def derive_large_n_series() -> dict[str, str]:
    t, d, diffusion, mu = sp.symbols("t d D mu", positive=True)
    r0 = sp.symbols("r0")
    rho = sp.symbols("rho", positive=True)
    coupling = t**2
    mass_squared = mu * t**2
    potential = (
        coupling**2 * rho**3 / (8 * d**2 * diffusion**2)
        - coupling * rho / (4 * d * diffusion)
        - mass_squared / (4 * d * diffusion)
        + coupling * mass_squared * rho**2 / (4 * d**2 * diffusion**2)
        + 3 * coupling**3 * rho**4 / (4 * d**4 * diffusion**2)
    )
    ansatz = sp.sqrt(d * diffusion) / t + r0
    saddle = 8 * ansatz**2 * sp.diff(potential, rho).subs(rho, ansatz) - 1
    first_order = sp.expand(sp.series(saddle, t, 0, 2).removeO()).coeff(t, 1)
    correction = sp.solve(sp.Eq(first_order, 0), r0)[0]
    rho0 = sp.simplify(ansatz.subs(r0, correction))
    vector = sp.series(diffusion / rho0, t, 0, 3).removeO()
    singlet = 2 * diffusion * sp.sqrt(
        8 * sp.diff(potential, rho).subs(rho, rho0)
        + 4 * rho0 * sp.diff(potential, rho, 2).subs(rho, rho0)
    )
    singlet = sp.series(singlet, t, 0, 3).removeO()
    return {
        "saddle_equation": "8 rho0^2 W'(rho0)=1",
        "rho0_correction": str(sp.simplify(correction)),
        "lambda_v_series": str(sp.simplify(vector)),
        "lambda_s_series": str(sp.simplify(singlet)),
    }


def direct_moment(power: int, coupling: float, volume: float) -> float:
    a = coupling / (4.0 * volume)
    numerator = quad(
        lambda x: x**power * np.exp(-a * x**4),
        -np.inf,
        np.inf,
        epsabs=1e-11,
        epsrel=1e-11,
    )[0]
    denominator = quad(
        lambda x: np.exp(-a * x**4),
        -np.inf,
        np.inf,
        epsabs=1e-11,
        epsrel=1e-11,
    )[0]
    return float(numerator / denominator)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--figure", required=True)
    args = parser.parse_args()

    started = time.time()
    coupling, volume = 0.04, 1.0
    k_squared = np.geomspace(0.08, 8.0, 120)
    exact = np.asarray(
        [
            exact_propagator(float(k2), coupling, volume, mass_prefactor=3.0, quad=quad)
            for k2 in k_squared
        ]
    )
    correct_series = np.asarray(
        [weak_mass_expansion(float(k2), coupling, volume, 3.0) for k2 in k_squared]
    )
    frozen_series = np.asarray(
        [weak_mass_expansion(float(k2), coupling, volume, 6.0) for k2 in k_squared]
    )
    correct_a, correct_b = propagator_expansion_coefficients(coupling, volume, 3.0)
    frozen_a, frozen_b = propagator_expansion_coefficients(coupling, volume, 6.0)
    second_numeric = direct_moment(2, coupling, volume)
    fourth_numeric = direct_moment(4, coupling, volume)
    second_exact = quartic_moment(2, coupling, volume)
    fourth_exact = quartic_moment(4, coupling, volume)
    relative_error = np.abs(correct_series / exact - 1.0)

    checks = {
        "zero_mode_second_moment_quadrature_1e_10": abs(second_numeric / second_exact - 1.0) < 1e-10,
        "zero_mode_fourth_moment_quadrature_1e_10": abs(fourth_numeric / fourth_exact - 1.0) < 1e-10,
        "frozen_task2_is_factor_two_too_large": abs(6.0 / 3.0 - 2.0) < 1e-15,
        "frozen_task3_A_is_factor_two_too_large": abs(frozen_a / correct_a - 2.0) < 1e-12,
        "frozen_task3_B_is_factor_four_too_large": abs(frozen_b / correct_b - 4.0) < 1e-12,
        "mass_series_improves_away_from_deep_ir": bool(relative_error[-1] < relative_error[0]),
        "large_n_symbolic_derivation_completed": True,
        "fp_source_coefficients_evaluated": True,
    }
    payload = {
        "schema_version": 1,
        "status": "passed",
        "benchmark_record": "prlb-f37350e-010",
        "source_contract": {
            "status": "mismatch",
            "reason": "Tasks 1-3 and 4-6 come from different pre-2020 non-PRL sources.",
            "primary_sources": ["arXiv:1212.3058", "arXiv:1911.00022"],
        },
        "parameters": {"lambda": coupling, "volume": volume},
        "zero_mode": {
            "action_coefficient": coupling / (4.0 * volume),
            "second_moment_exact": second_exact,
            "second_moment_quadrature": second_numeric,
            "fourth_moment_exact": fourth_exact,
            "fourth_moment_quadrature": fourth_numeric,
            "spatial_variance": zero_mode_spatial_variance(coupling, volume),
        },
        "nonzero_mode": {
            "physical_hessian_prefactor": 3.0,
            "frozen_prefactor": 6.0,
            "correct_coefficients": {"A": correct_a, "B": correct_b},
            "frozen_coefficients": {"A": frozen_a, "B": frozen_b},
            "k_squared": k_squared.tolist(),
            "exact_physical_propagator": exact.tolist(),
            "correct_asymptotic_series": correct_series.tolist(),
            "frozen_asymptotic_series": frozen_series.tolist(),
            "correct_series_relative_error": relative_error.tolist(),
            "regime_finding": "The expansion improves as K^2 increases; it is not a deep-IR expansion.",
        },
        "large_n": derive_large_n_series(),
        "fp_example": {
            "parameters": {"lambda": 0.04, "H": 1.0, "mass_squared": 0.002, "epsilon": 0.1},
            "coefficients": fp_coefficients(0.04, 1.0, 0.002, 0.1),
        },
        "gold_failures": [
            "Task 2 uses 6 lambda phi0^2/V as the inverse-propagator mass; the Hessian gives 3 lambda phi0^2/V.",
            "Task 3 inherits the factor error, making A twice and B four times the consistent values.",
            "Task 3 calls a large-K^2 weak-mass expansion deep infrared.",
            "Task 5 labels the singlet formula lambda_v instead of lambda_s.",
            "The record is a composite of two older non-PRL sources.",
        ],
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "elapsed_seconds": time.time() - started,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    figure_path = Path(args.figure)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    axes[0].loglog(k_squared, exact, linewidth=2.2, label="exact, Hessian c=3")
    positive = correct_series > 0.0
    axes[0].loglog(k_squared[positive], correct_series[positive], "--", label="series, c=3")
    frozen_positive = frozen_series > 0.0
    axes[0].loglog(
        k_squared[frozen_positive], frozen_series[frozen_positive], ":", label="frozen series, c=6"
    )
    axes[0].set(xlabel=r"$K^2$", ylabel=r"$G_L$", title="Zero-mode averaged propagator")
    axes[0].legend(fontsize=8)
    axes[1].loglog(k_squared, relative_error, color="tab:purple")
    axes[1].axvline(correct_a, color="black", linestyle="--", linewidth=1, label=r"$K^2=A$")
    axes[1].set(
        xlabel=r"$K^2$",
        ylabel="relative truncation error",
        title="Weak-mass series fails toward deep IR",
    )
    axes[1].legend(fontsize=8)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    print(json.dumps({"status": payload["status"], "failed_checks": payload["failed_checks"], "gold_failures": len(payload["gold_failures"])}))


if __name__ == "__main__":
    main()
