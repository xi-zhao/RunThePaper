#!/usr/bin/env python3
"""Generate deterministic evidence for the record-085 gold audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from floquet_ising import (  # noqa: E402
    build_operators,
    floquet_unitary_midpoint,
    hilbert_schmidt_coefficients,
    nested_commutators,
    principal_floquet_from_adaptive,
    principal_floquet_hamiltonian,
    source_frozen_mismatch,
)


def rounded(values: np.ndarray, digits: int = 12) -> list[float]:
    return [round(float(value), digits) for value in values]


def main() -> None:
    operators = build_operators(length=6, j=1.0, h0=2.0)
    cbb, caa = nested_commutators(operators)
    cbb_coefficients, cbb_residual = hilbert_schmidt_coefficients(cbb, operators.basis)
    caa_coefficients, caa_residual = hilbert_schmidt_coefficients(caa, operators.basis)

    asymptotic_points = [source_frozen_mismatch(operators, omega) for omega in (20, 40, 80, 160, 320)]
    exact, _, _ = principal_floquet_from_adaptive(operators, 40.0)
    discretization = []
    for steps in (64, 128, 256):
        unitary = floquet_unitary_midpoint(operators, 40.0, steps)
        hamiltonian = principal_floquet_hamiltonian(unitary, 40.0)
        discretization.append(
            {
                "steps": steps,
                "operator_norm_error_vs_adaptive": float(np.linalg.norm(hamiltonian - exact, 2)),
                "unitarity_error": float(
                    np.linalg.norm(unitary.conj().T @ unitary - operators.identity, 2)
                ),
            }
        )

    leading_mismatch = (
        4.0 * operators.szz
        - 4.0 * operators.syy
        + 8.0 * operators.sx_boundary
        + 16.0 * operators.sx_bulk
        + 16.0 * operators.szxz
    )
    payload = {
        "schema_version": 1,
        "benchmark_record": "prlb-f37350e-085",
        "source_contract": {
            "status": "verified",
            "title": "Temporal Entanglement Transitions in the Periodically Driven Ising Chain",
            "arxiv": "2510.13970v3",
            "publication": "Physical Review Letters 136, 100203 (2026)",
            "doi": "10.1103/cxq7-q9pd",
            "source_equation": "Eq. (3)",
        },
        "tasks_1_to_3": {
            "status": "valid",
            "claims": [
                "P_A rho_A P_A = rho_A",
                "w_plus - w_minus = Tr(rho_A P_A)",
                "a dominant-sector swap forces lambda_0 = lambda_1",
            ],
        },
        "task_4": {
            "status": "invalid",
            "rubric_internal_consistency": False,
            "rubric_stated_formula": "A + [B,[A,B]]/(8 omega^2)",
            "rubric_formula_operator_coefficients": [1.0, -1.0, 0.0, 0.0, 0.0],
            "frozen_answer_operator_coefficients": [-2.0, 2.0, -4.0, -8.0, -8.0],
            "nested_BAB_coefficients": rounded(cbb_coefficients),
            "nested_AAB_coefficients": rounded(caa_coefficients),
            "nested_residuals": {"BAB": cbb_residual, "AAB": caa_residual},
            "phase_independent_van_vleck_coefficients": [2.0, -2.0, 0.0, 0.0, 0.0],
            "principal_log_t0_zero_coefficients": [2.0, -2.0, 4.0, 8.0, 8.0],
            "source_and_frozen_coefficients": [-2.0, 2.0, -4.0, -8.0, -8.0],
        },
        "task_5": {
            "status": "valid",
            "cut_count": "1 at either open boundary, otherwise 2",
            "commutator_norm": "2 J N_cut",
            "integrated_bound": "t_min >= 1/(2 J N_cut)",
        },
        "task_6": {
            "status": "invalid",
            "leading_mismatch_operator_norm": float(np.linalg.norm(leading_mismatch, 2)),
            "asymptotic_behavior": "norm(Delta) = 101.334386275.../omega^2 + O(omega^-3)",
            "claimed_limit_exists": False,
            "claimed_value_approximately_2000": False,
            "observation": "omega^3 norm(Delta) is about 2056 at omega=20 only, then grows linearly.",
            "adaptive_points": asymptotic_points,
            "explicit_midpoint_refinement_at_omega_40": discretization,
        },
        "verdict": {
            "status": "benchmark_gold_invalid",
            "valid_parts": ["Tasks 1-3", "Task 5"],
            "invalid_parts": ["Task 4", "Task 6"],
        },
    }
    output = WORKSPACE / "outputs" / "data" / "idx85_gold_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["verdict"], indent=2))


if __name__ == "__main__":
    main()
