#!/usr/bin/env python3
"""Independent pre-execution checks for the paper-derived method."""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.amplitude_estimation import (  # noqa: E402
    PAPER_PERCENTILE,
    amplified_probability,
    assert_resource_reference,
    complexity_rows,
    conventional_qae_error,
    cumulative_mle_amplitudes,
    eis_schedule,
    fisher_information,
    lis_schedule,
    query_count,
)


def main() -> int:
    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, observed: object, expected: object) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "passed" if condition else "failed",
                "observed": observed,
                "expected": expected,
            }
        )

    amplitudes = np.array([1 / 48, 1 / 6, 2 / 3])
    m0 = np.array([float(amplified_probability(float(a), 0)) for a in amplitudes])
    check("probability_m0_identity", np.allclose(m0, amplitudes, atol=1e-14), m0.tolist(), amplitudes.tolist())

    probability_grid = np.array(
        [float(amplified_probability(1 / 7, m)) for m in range(20)]
    )
    check(
        "probability_normalization",
        bool(np.all((0.0 <= probability_grid) & (probability_grid <= 1.0))),
        [float(probability_grid.min()), float(probability_grid.max())],
        "[0, 1]",
    )

    for maximum_m in range(0, 16):
        schedule = lis_schedule(maximum_m)
        direct_query = query_count(schedule, 100)
        closed_query = 100 * (maximum_m + 1) ** 2
        check(
            f"lis_query_sum_M{maximum_m}",
            direct_query == closed_query,
            direct_query,
            closed_query,
        )
        direct_square_sum = int(np.sum((2 * schedule + 1) ** 2))
        closed_square_sum = (maximum_m + 1) * (2 * maximum_m + 1) * (2 * maximum_m + 3) // 3
        check(
            f"lis_fisher_sum_M{maximum_m}",
            direct_square_sum == closed_square_sum,
            direct_square_sum,
            closed_square_sum,
        )

    check(
        "eis_small_schedule",
        eis_schedule(3).tolist() == [0, 1, 2, 4],
        eis_schedule(3).tolist(),
        [0, 1, 2, 4],
    )

    a = 0.37
    counts = np.array([[0], [1], [3], [5], [7], [9], [10]], dtype=np.int64)
    estimates = cumulative_mle_amplitudes(
        counts,
        np.array([0], dtype=np.int64),
        10,
        grid_size=16385,
    )[:, 0]
    expected_mle = counts[:, 0] / 10
    check(
        "m0_binomial_mle",
        bool(np.allclose(estimates, expected_mle, atol=2e-5)),
        estimates.tolist(),
        expected_mle.tolist(),
    )

    fisher_m0 = fisher_information(a, [0], 100)
    expected_fisher_m0 = 100 / (a * (1 - a))
    check(
        "fisher_m0_identity",
        math.isclose(fisher_m0, expected_fisher_m0, rel_tol=1e-14),
        fisher_m0,
        expected_fisher_m0,
    )

    expected_complexities = [
        ("O(epsilon^-2)", "O(epsilon^-2)"),
        ("O(epsilon^-4/3)", "O(epsilon^-5/3)"),
        ("O(epsilon^-1)", "O(epsilon^-1 log(epsilon^-1))"),
    ]
    observed_complexities = [
        (row["query_complexity"], row["postprocessing_complexity"])
        for row in complexity_rows()
    ]
    check(
        "table1_symbolic_rows",
        observed_complexities == expected_complexities,
        observed_complexities,
        expected_complexities,
    )

    try:
        assert_resource_reference()
        resource_ok = True
        resource_observed: object = "all 37 published numeric cells exact"
    except AssertionError as exc:
        resource_ok = False
        resource_observed = str(exc)
    check("table2_exact_rows", resource_ok, resource_observed, "all published cells exact")

    q_query, q_error = conventional_qae_error(1 / 48, 8)
    check(
        "qae_candidate_contract",
        q_query == 255 and 0.0 < q_error < 0.02,
        {"n_query": q_query, "error": q_error},
        {"n_query": 255, "error_range": "(0, 0.02)"},
    )
    check(
        "appendix_percentile",
        math.isclose(PAPER_PERCENTILE, 81.05694691387022, rel_tol=1e-14),
        PAPER_PERCENTILE,
        81.05694691387022,
    )

    status = "passed" if all(item["status"] == "passed" for item in checks) else "failed"
    payload = {
        "schema_version": 1,
        "paper_id": "1904.10246",
        "status": status,
        "purpose": "pre-execution verification of the algorithm and analytic method",
        "summary": {
          "checks_total": len(checks),
          "checks_passed": sum(item["status"] == "passed" for item in checks),
          "checks_failed": sum(item["status"] == "failed" for item in checks)
        },
        "checks": checks,
    }
    output = WORKSPACE / "outputs" / "checks" / "method_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
