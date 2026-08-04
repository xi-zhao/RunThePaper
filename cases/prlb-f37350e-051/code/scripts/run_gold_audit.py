#!/usr/bin/env python3
"""Generate the machine-readable independent audit for benchmark record 051."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import mpmath as mp


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from lindhard_kernel import (  # noqa: E402
    asymptotic_coefficient,
    decomposition_coefficients,
    l1,
    response_audit,
    smallest_positive_root,
    yukawa_second_moment,
)


def decimal(value: mp.mpf, digits: int = 60) -> str:
    return mp.nstr(value, digits)


def main() -> None:
    # x^2*l1(x) subtracts O(x^2) terms to expose an O(x^-2) remainder.
    # Keep enough guard digits for the x=1e20 asymptotic probe.
    mp.mp.dps = 180
    root = smallest_positive_root()
    response = response_audit(mp.mpf("0.5"))
    asymptotic_x = mp.mpf("1e20")
    coefficients = decomposition_coefficients()

    payload = {
        "schema_version": 1,
        "benchmark_record": "prlb-f37350e-051",
        "source_contract": {
            "status": "mismatch",
            "recoverable_lineage": "Wang and Teter, Phys. Rev. B 45, 13196 (1992)",
            "doi": "10.1103/PhysRevB.45.13196",
            "prl_mapping": "unresolved",
        },
        "task_1_and_4_sign_audit": {
            key: decimal(value) for key, value in asdict(response).items()
        }
        | {
            "task_1_joint_contract_satisfiable": False,
            "task_4_gold_matches_frozen_response_relation": False,
            "explanation": "Frozen -G>0 makes its stated response positive, while the gold positive Hessian implies a negative response. The 1992 source uses G>0 and delta_rho=-G delta_V.",
        },
        "task_2": {
            "asymptotic_probe_x": decimal(asymptotic_x),
            "x_squared_l1": decimal(asymptotic_coefficient(asymptotic_x)),
            "exact_limit": "-3/35",
            "high_q_tail_determines_second_moment": False,
            "counterexample": {
                "momentum_kernel": "1/(q^2+1)",
                "same_high_q_tail": "q^-2",
                "coordinate_kernel": "exp(-r)/(4*pi*r)",
                "finite_second_radial_moment": decimal(yukawa_second_moment()),
            },
        },
        "task_3_conditional_algebra": {
            key: decimal(value) for key, value in coefficients.items()
        },
        "task_5": {
            "smallest_positive_root": decimal(root, 90),
            "residual": decimal(l1(root), 20),
            "frozen_value": "0.80540452397",
            "absolute_error": decimal(abs(root - mp.mpf("0.80540452397")), 20),
        },
        "verdict": {
            "status": "benchmark_gold_invalid",
            "valid_parts": ["Task 2(a) asymptotic coefficient", "Task 3 conditional algebra", "Task 5 root"],
            "invalid_parts": ["Task 1 sign contract", "Task 2(b) inference from high-q tail", "Task 4 Hessian sign"],
        },
    }
    output = WORKSPACE / "outputs" / "data" / "idx51_gold_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["verdict"], indent=2))


if __name__ == "__main__":
    main()
