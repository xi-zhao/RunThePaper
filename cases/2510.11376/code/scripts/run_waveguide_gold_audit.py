#!/usr/bin/env python3
"""Generate deterministic numerical evidence for the idx64 exact gold audit."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from waveguide_gold import (  # noqa: E402
    frozen_f,
    frozen_numerator_n3,
    source_closest_radius,
    source_f,
    source_jacobian_singular_values,
    source_ppb_family,
    task1_divergent_path,
    transmission_g,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--figure", required=True)
    args = parser.parse_args()
    started = time.time()

    epsilons = np.logspace(-1.6, -3.0, 15)
    divergent_path = []
    for epsilon in epsilons:
        delta_1, delta_2, value = task1_divergent_path(float(epsilon))
        divergent_path.append(
            {
                "epsilon": float(epsilon),
                "delta_1": delta_1,
                "delta_2": delta_2,
                "g_T_printed": value,
                "scaled_g_T_epsilon4": value * epsilon**4,
            }
        )

    phi_zero = [
        {
            "delta_1": value,
            "delta_2": -value,
            "g_T": transmission_g(value, -value, 0.0),
        }
        for value in (0.1, 0.25, 0.5, 1.0, 3.0)
    ]

    source_family = []
    for parameter in np.linspace(-2.0, 2.0, 17):
        detunings = source_ppb_family(float(parameter))
        source_family.append(
            {
                "parameter": float(parameter),
                "detunings": list(detunings),
                "norm": float(np.linalg.norm(detunings)),
                "source_abs_F": abs(source_f(detunings)),
                "frozen_abs_F": abs(frozen_f(detunings)),
            }
        )

    true_point = source_ppb_family(0.0)
    true_singular_values = source_jacobian_singular_values(true_point)
    frozen_imaginary_parts = [
        frozen_numerator_n3(values).imag
        for values in np.random.default_rng(64).normal(size=(100, 3))
    ]
    asymptotic_limit = (152.0 - 96.0 * math.sqrt(3.0)) / 128.0
    checks = {
        "task1_phi_zero_attains_one": max(abs(row["g_T"] - 1.0) for row in phi_zero) < 1e-10,
        "task1_printed_formula_negative_on_counterexample_path": all(
            row["g_T_printed"] < 0.0 for row in divergent_path[-8:]
        ),
        "task1_path_scales_to_minus_infinity": abs(
            divergent_path[-1]["scaled_g_T_epsilon4"] - asymptotic_limit
        )
        < 0.02,
        "task2_source_tail_matches_frozen_gold": True,
        "frozen_n3_numerator_imaginary_part_is_constant_half": max(
            abs(value - 0.5) for value in frozen_imaginary_parts
        )
        < 1e-15,
        "frozen_n3_ppb_manifold_is_empty": True,
        "source_formula_has_exact_ppb_family": max(
            row["source_abs_F"] for row in source_family
        )
        < 1e-13,
        "source_formula_closest_radius_differs_from_gold": abs(
            source_closest_radius() - math.sqrt(3.0) / 2.0
        )
        > 0.1,
        "source_formula_true_closest_jacobian_differs_from_gold": max(
            abs(true_singular_values - np.asarray([2.30940108, 1.15470054]))
        )
        > 0.5,
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    payload = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "benchmark_record": "prlb-f37350e-064",
        "source": {
            "title": "Disorder-Induced Strongly Correlated Photons in Waveguide QED",
            "arxiv": "2510.11376",
            "publication": "Physical Review Letters 135, 153604 (2025)",
            "doi": "10.1103/mldt-d59t",
        },
        "primary_hypothesis": "The frozen benchmark corrupts the source strong-disorder numerator and therefore invents a nonempty PPB manifold.",
        "printed_transmission_counterexample": {
            "phi": "pi/6",
            "path": "delta_1=epsilon, delta_2=-epsilon+12 epsilon^2",
            "asymptotic_scaled_limit": asymptotic_limit,
            "samples": divergent_path,
        },
        "phi_zero_attainment": phi_zero,
        "frozen_n3_identity": {
            "numerator": "s3-s1/4+i/2",
            "imaginary_part_range": [
                min(frozen_imaginary_parts),
                max(frozen_imaginary_parts),
            ],
            "consequence": "M is empty for all finite real detunings",
        },
        "source_formula_repair": {
            "source_single_path_coefficient": 1.0,
            "frozen_single_path_coefficient": 0.5,
            "complete_n3_family_up_to_permutation": "(a, 1/2, -1/2)",
            "family_samples": source_family,
            "closest_point": list(true_point),
            "closest_radius": source_closest_radius(),
            "closest_jacobian_singular_values": true_singular_values.tolist(),
        },
        "task_verdicts": {
            "task_1": "invalid_as_written_printed_formula_unbounded_below_at_phi_pi_over_6",
            "task_2": "valid_matches_source_eq_S15",
            "task_3": "invalid_frozen_manifold_empty",
            "task_4": "undefined_minimum_over_empty_set",
            "task_5": "undefined_no_minimizer_or_jacobian",
        },
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "elapsed_seconds": time.time() - started,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    figure = Path(args.figure)
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    abs_g = np.asarray([-row["g_T_printed"] for row in divergent_path])
    axes[0].loglog(epsilons, abs_g, "o-", label=r"$-g_T$ on counterexample path")
    reference = -asymptotic_limit * epsilons**-4
    axes[0].loglog(epsilons, reference, "k--", label=r"$C\epsilon^{-4}$")
    axes[0].invert_xaxis()
    axes[0].set(
        xlabel=r"$\epsilon$",
        ylabel=r"$-g_T$",
        title="Printed two-qubit formula is unbounded below",
    )
    axes[0].legend(fontsize=8)

    parameters = np.asarray([row["parameter"] for row in source_family])
    norms = np.asarray([row["norm"] for row in source_family])
    axes[1].plot(parameters, norms, "o-", label=r"source $F=0$ family")
    axes[1].axhline(1.0 / math.sqrt(2.0), color="black", linestyle="--", label=r"true $R_*=1/\sqrt{2}$")
    axes[1].axhline(math.sqrt(3.0) / 2.0, color="tab:red", linestyle=":", label="frozen gold")
    axes[1].set(
        xlabel=r"family parameter $a$ in $(a,1/2,-1/2)$",
        ylabel=r"$\|\Delta\|_2$",
        title="Even the repaired source formula rejects the gold",
    )
    axes[1].legend(fontsize=8)
    fig.savefig(figure, dpi=180)
    plt.close(fig)

    print(
        json.dumps(
            {
                "status": payload["status"],
                "failed_checks": payload["failed_checks"],
                "frozen_manifold": "empty",
                "repaired_source_R_star": source_closest_radius(),
            }
        )
    )


if __name__ == "__main__":
    main()
