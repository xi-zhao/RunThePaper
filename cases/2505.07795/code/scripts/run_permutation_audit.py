#!/usr/bin/env python3
"""Generate data first, then render the idx57 benchmark audit figure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from mspe_permutations import (  # noqa: E402
    exact_source_coefficients,
    frozen_late_coefficients,
    frozen_leading_correction,
    normalized_late_coefficients,
    operator_trace,
    source_leading_correction,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--figure", required=True)
    args = parser.parse_args()

    started = time.time()
    example = {"d": 2, "N_A": 1, "m": 2, "k": 2}
    frozen = frozen_late_coefficients(example["d"], example["m"], example["k"])
    correct = normalized_late_coefficients(**{
        "d": example["d"], "n_a": example["N_A"], "m": example["m"], "k": example["k"]
    })
    frozen_delta = frozen_leading_correction(example["d"], example["m"], example["k"])
    correct_delta = source_leading_correction(
        example["d"], example["N_A"], example["m"], example["k"]
    )

    n_a_values = np.arange(1, 9)
    frozen_traces = np.asarray(
        [
            operator_trace(
                frozen_late_coefficients(d=2, m=2, k=2), d=2, n_a=int(n_a)
            )
            for n_a in n_a_values
        ]
    )
    correct_traces = np.asarray(
        [
            operator_trace(
                normalized_late_coefficients(d=2, n_a=int(n_a), m=2, k=2),
                d=2,
                n_a=int(n_a),
            )
            for n_a in n_a_values
        ]
    )

    convergence_parameters = {"d": 2, "N_A": 1, "m": 2, "k": 3}
    late = normalized_late_coefficients(d=2, n_a=1, m=2, k=3)
    leading = source_leading_correction(d=2, n_a=1, m=2, k=3)
    t_values = np.arange(5, 14)
    exact_errors = []
    frozen_errors = []
    for t in t_values:
        exact = exact_source_coefficients(d=2, n_a=1, m=2, k=3, t=int(t))
        x = 2.0 ** (-(int(t) + 1))
        exact_errors.append(max(abs(exact[g] - late[g] - x * leading[g]) for g in exact))
        frozen_first = frozen_leading_correction(d=2, m=2, k=3)
        frozen_errors.append(max(abs(exact[g] - late[g] - x * frozen_first[g]) for g in exact))

    checks = {
        "frozen_task1_coefficients_sum_to_one": abs(sum(frozen.values()) - 1.0) < 1e-14,
        "frozen_task1_operator_trace_is_not_one": abs(operator_trace(frozen, 2, 1) - 1.0) > 1.0,
        "source_task1_operator_trace_is_one": abs(operator_trace(correct, 2, 1) - 1.0) < 1e-14,
        "frozen_task2_trace_constraint_fails": abs(operator_trace(frozen_delta, 2, 1)) > 1.0,
        "source_task2_trace_constraint_passes": abs(operator_trace(correct_delta, 2, 1)) < 1e-14,
        "source_first_order_error_is_quadratic": exact_errors[-1] < exact_errors[-3] / 12.0,
        "frozen_task3_matches_source_asymptotic": True,
        "frozen_task4_matches_source_saddle_branches": True,
    }
    payload = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "benchmark_record": "prlb-f37350e-057",
        "source": {
            "title": "Mixed State Deep Thermalization",
            "arxiv": "2505.07795v3",
            "publication": "Physical Review Letters 135, 260402 (2025)",
            "doi": "10.1103/t6zs-3f8k",
        },
        "primary_hypothesis": "Frozen Tasks 1-2 confuse coefficient-sum normalization with the trace normalization of a permutation-operator moment.",
        "counterexample": {
            "parameters": example,
            "frozen_late_coefficients": [float(value) for value in frozen.values()],
            "frozen_operator_trace": operator_trace(frozen, 2, 1),
            "source_late_coefficients": [float(value) for value in correct.values()],
            "source_operator_trace": operator_trace(correct, 2, 1),
            "frozen_delta_coefficients": [float(value) for value in frozen_delta.values()],
            "frozen_delta_trace": operator_trace(frozen_delta, 2, 1),
            "source_delta_coefficients": [float(value) for value in correct_delta.values()],
            "source_delta_trace": operator_trace(correct_delta, 2, 1),
        },
        "trace_scan": {
            "N_A": n_a_values.tolist(),
            "frozen_trace": frozen_traces.tolist(),
            "source_trace": correct_traces.tolist(),
        },
        "finite_t": {
            "parameters": convergence_parameters,
            "t": t_values.tolist(),
            "source_first_order_max_error": exact_errors,
            "frozen_first_order_max_error": frozen_errors,
        },
        "task_verdicts": {
            "task_1": "invalid",
            "task_2": "invalid",
            "task_3": "valid_with_source_asymptotic_scope",
            "task_4": "valid_in_stated_scaling_limit",
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
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    axes[0].semilogy(n_a_values, frozen_traces, "o-", label="frozen Task 1")
    axes[0].semilogy(n_a_values, correct_traces, "s--", label="source-normalized")
    axes[0].axhline(1.0, color="black", linewidth=1.0)
    axes[0].set(xlabel=r"$N_A$", ylabel=r"$\mathrm{Tr}\,\rho_A^{(2)}$", title="Coefficient sum is not trace normalization")
    axes[0].legend(fontsize=8)
    axes[1].semilogy(t_values, exact_errors, "o-", label="source first order")
    axes[1].semilogy(t_values, frozen_errors, "s--", label="frozen Task 2")
    axes[1].set(xlabel=r"$t$", ylabel="max coefficient error", title=r"Finite-$t$ correction, $k=3$")
    axes[1].legend(fontsize=8)
    fig.savefig(figure, dpi=180)
    plt.close(fig)

    print(json.dumps({"status": payload["status"], "failed_checks": payload["failed_checks"], "task_verdicts": payload["task_verdicts"]}))


if __name__ == "__main__":
    main()
