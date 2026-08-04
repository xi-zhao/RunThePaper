#!/usr/bin/env python3
"""Generate deterministic evidence for the record-088 audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from magic_xy_audit import (  # noqa: E402
    asymptotic_shift_coefficient,
    cesaro_error_norm,
    dimerization_norm_factor,
    floquet_error_ratio,
    global_quality_maximum,
    scaled_magic_shift,
)


def main() -> None:
    theta, quality, gap = global_quality_maximum(
        1.0 / 25.0, 1e-3, alpha=1.0, lam=-2.0, closure_as_written=True
    )
    shift_sequences = {
        str(lam): [
            {"s": s, "scaled_shift": scaled_magic_shift(s, lam)}
            for s in (1e-3, 3e-4, 1e-4, 3e-5, 1e-5)
        ]
        for lam in (-100.0, -2.0, 0.0, 100.0)
    }
    ring_norms = [
        {
            "N": size,
            "factor": dimerization_norm_factor(size),
            "odd_m3_cesaro_norm_at_unit_contrast": cesaro_error_norm(size, 3, 1.0, 0.0),
        }
        for size in (4, 6, 8, 10)
    ]
    payload = {
        "schema_version": 1,
        "benchmark_record": "prlb-f37350e-088",
        "source_contract": {
            "status": "mismatch",
            "closest_lineage": "Emperauger et al., Phys. Rev. A 111, 062806 (2025)",
            "arxiv": "2503.15034v3",
            "doi": "10.1103/PhysRevA.111.062806",
            "prl_mapping": "unresolved",
            "absent_from_lineage": ["high-order magic-angle cumulant formula", "periodically permuted XY ring Tasks 4-5"],
        },
        "task_1": {
            "status": "invalid",
            "stated_closure": "Cov(z2/r2,R6)=Az2*Az6*Cov(z2,z6)/r8",
            "required_variance_term": "180*Az2^2*Az6*s^4",
            "frozen_variance_term": "180*Az2*Az6*s^4",
            "quality_remainder_generic": "O(s^2), not O(s^(5/2)), when Var~s^2",
        },
        "task_2": {
            "status": "invalid",
            "frozen_answer": "No",
            "correct_answer": "Yes for every fixed finite lambda",
            "exact_shift_coefficient_radians": asymptotic_shift_coefficient(),
            "exact_shift_coefficient": "563/100",
            "numeric_sequences": shift_sequences,
        },
        "task_3": {
            "status": "valid_at_requested_precision",
            "corrected_theta_degrees": float(np.degrees(theta)),
            "frozen_internal_theta_degrees": 63.8905,
            "four_significant_figures": 63.89,
            "quality": quality,
            "gap_to_next_candidate": gap,
        },
        "task_4": {
            "status": "invalid",
            "exact_formula": "|J0-J1|*f_N/(2m) for odd m, zero for even m",
            "f_N": "1 if N mod 4 = 0; cos(pi/N) if N mod 4 = 2",
            "ring_norms": ring_norms,
            "rubric_factor_conflict": "Rubric says ||H-H'||=|delta|/2 but its displayed final formula requires |delta|.",
        },
        "task_5": {
            "status": "invalid",
            "even_m_counterexample": {
                "N": 6,
                "m": 2,
                "t": 1.0,
                "J0": 1.0,
                "J1": 0.0,
                "ratio": floquet_error_ratio(6, 2, 1.0, 1.0, 0.0),
                "frozen_value": 0.0,
            },
            "N_dependence_counterexample": {
                "N4_even_m2_ratio": floquet_error_ratio(4, 2, 1.0, 1.0, 0.0),
                "N6_even_m2_ratio": floquet_error_ratio(6, 2, 1.0, 1.0, 0.0),
            },
            "m1_small_contrast_limit_N4": 0.5,
            "frozen_m1_value_at_t1": 1.0,
        },
        "verdict": {
            "status": "benchmark_gold_invalid",
            "valid_parts": ["Task 3 at four significant figures"],
            "invalid_parts": ["Task 1", "Task 2", "Task 4", "Task 5"],
        },
    }
    output = WORKSPACE / "outputs" / "data" / "idx88_gold_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["verdict"], indent=2))


if __name__ == "__main__":
    main()
