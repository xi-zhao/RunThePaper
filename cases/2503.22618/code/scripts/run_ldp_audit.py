#!/usr/bin/env python3
"""Generate deterministic idx59 LDP evidence before its diagnostic figure."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import gammaln, logsumexp


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from scar_bayes import (  # noqa: E402
    bayesian_path,
    constrained_ring_dimension,
    exact_ldp_rate,
    frozen_regime_flags,
    sector_growth,
)


def exact_event_log_probability(k: int, a: float, b: float, q: float) -> dict[str, float | int]:
    counts = np.arange(k + 1, dtype=float)
    circles = k - counts
    log_a = counts * math.log(a) + circles * math.log(1.0 - a)
    log_b = counts * math.log(b) + circles * math.log(1.0 - b)
    log_baseline = counts * math.log(q) + circles * math.log(1.0 - q)
    growth = np.logaddexp(log_a, log_b) - math.log(2.0) - log_baseline
    accepted = growth >= 0.0
    log_pmf = (
        gammaln(k + 1.0)
        - gammaln(counts + 1.0)
        - gammaln(circles + 1.0)
        + log_baseline
    )
    log_probability = float(logsumexp(log_pmf[accepted]))
    accepted_counts = np.flatnonzero(accepted)
    padded = np.concatenate(([False], accepted, [False])).astype(int)
    changes = np.diff(padded)
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1) - 1
    accepted_ranges = [[int(start), int(end)] for start, end in zip(starts, ends)]
    return {
        "k": k,
        "log_probability": log_probability,
        "rate": -log_probability / k,
        "accepted_min": int(accepted_counts.min()),
        "accepted_max": int(accepted_counts.max()),
        "accepted_ranges": accepted_ranges,
        "naive_samples_for_one_event_log10": -log_probability / math.log(10.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--figure", required=True)
    args = parser.parse_args()

    started = time.time()
    a, b, q = 0.37, 0.81, 0.62
    exact = exact_ldp_rate(a, b, q)
    frozen_flags = frozen_regime_flags(a, b, q)
    k_values = [100, 500, 2_000, 10_000, 50_000, 200_000]
    finite_k = [exact_event_log_probability(k, a, b, q) for k in k_values]

    rng = np.random.default_rng(59)
    path_checks = []
    for length in (10, 50, 200):
        outcomes = (rng.random(length) < q).tolist()
        result = bayesian_path(outcomes, a, b, q)
        result["absolute_telescope_error"] = abs(
            result["accumulated_log_growth"] - result["telescoped_log_growth"]
        )
        path_checks.append(result)

    p = np.linspace(0.0, 1.0, 1001)
    growth_a = np.asarray([sector_growth(float(value), a, q) for value in p])
    growth_b = np.asarray([sector_growth(float(value), b, q) for value in p])

    checks = {
        "frozen_infinite_branch_triggered": bool(frozen_flags["infinite_branch"]),
        "frozen_zero_branch_triggered": bool(frozen_flags["zero_branch"]),
        "frozen_branch_classification_overlaps": bool(
            frozen_flags["infinite_branch"] and frozen_flags["zero_branch"]
        ),
        "correct_rate_is_finite_positive": 0.0 < exact["Gamma"] < math.inf,
        "correct_rate_differs_from_frozen_mc": abs(exact["Gamma"] - 0.013764) > 0.005,
        "full_bayesian_updates_telescope": max(
            item["absolute_telescope_error"] for item in path_checks
        ) < 1e-12,
        "finite_k_rate_approaches_correct_rate": abs(finite_k[-1]["rate"] - exact["Gamma"]) < 1e-4,
        "naive_task4_monte_carlo_is_infeasible": finite_k[-1][
            "naive_samples_for_one_event_log10"
        ] > 1000.0,
        "task5_lucas_dimension_obstruction_valid": all(
            constrained_ring_dimension(length) > length for length in range(6, 102, 2)
        ),
    }
    payload = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "benchmark_record": "prlb-f37350e-059",
        "source": {
            "title": "Enhancing Revivals via Projective Measurements in a Quantum Scarred System",
            "arxiv": "2503.22618",
            "publication": "Physical Review Letters 135, 090402 (2025)",
            "doi": "10.1103/jf2f-wqkx",
        },
        "primary_hypothesis": "The frozen Bayesian LDP classification uses incompatible best-outcome sectors and is internally nonexclusive.",
        "parameters": {"a": a, "b": b, "q": q},
        "source_contract": {
            "status": "benchmark_extension",
            "finding": "The source explicitly says individual scars are not projector eigenstates and contains no Bayesian LDP classification.",
        },
        "frozen_regime_flags": frozen_flags,
        "correct_ldp": exact,
        "finite_k_exact_event": finite_k,
        "full_bayesian_path_checks": path_checks,
        "ring_dimensions": [
            {"N": length, "D_PBC": constrained_ring_dimension(length)}
            for length in range(6, 22, 2)
        ],
        "task_verdicts": {
            "task_1": "conditional_formula_valid_only_after_relaxing_the_projector_contract",
            "task_2": "formula_ambiguous_for_zero_to_zero_power",
            "task_3": "invalid",
            "task_4": "invalid_and_naive_monte_carlo_infeasible",
            "task_5": "valid",
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
    axes[0].plot(p, growth_a, label="fixed sector a")
    axes[0].plot(p, growth_b, label="fixed sector b")
    axes[0].plot(p, np.maximum(growth_a, growth_b), "k--", label="mixture envelope")
    axes[0].axhline(0.0, color="gray", linewidth=1.0)
    axes[0].axvline(q, color="tab:red", linestyle=":", label="typical p=q")
    axes[0].set(xlabel="empirical bullet frequency p", ylabel="asymptotic log growth", title="Bayesian evidence keeps a fixed scar sector")
    axes[0].legend(fontsize=8)
    rates = np.asarray([item["rate"] for item in finite_k])
    axes[1].semilogx(k_values, rates, "o-", label="exact finite-k event")
    axes[1].axhline(exact["Gamma"], color="black", linestyle="--", label="correct LDP rate")
    axes[1].axhline(0.013764, color="tab:red", linestyle=":", label="frozen MC claim")
    axes[1].set(xlabel="k", ylabel=r"$-k^{-1}\log \mathcal{P}_k$", title="Rare-event rate without impossible naive MC")
    axes[1].legend(fontsize=8)
    fig.savefig(figure, dpi=180)
    plt.close(fig)

    print(json.dumps({"status": payload["status"], "failed_checks": payload["failed_checks"], "Gamma": exact["Gamma"], "frozen_overlap": checks["frozen_branch_classification_overlaps"]}))


if __name__ == "__main__":
    main()
