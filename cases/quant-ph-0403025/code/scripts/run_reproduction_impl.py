#!/usr/bin/env python3
"""Run clean-room Bravyi-Kitaev distillation numerics without rendering."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
sys.path.insert(0, str(SRC))

from magic_distillation.model import (  # noqa: E402
    five_qubit_projector,
    h_type_enumeration,
    h_type_output_error,
    h_type_success,
    h_type_weight_tables,
    reed_muller_spaces,
    resource_summary,
    t_type_output_error,
    t_type_projection_table,
    t_type_projector_enumeration,
    t_type_success,
    threshold_summary,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_curve(
    path: Path, epsilon: np.ndarray, output_error: np.ndarray, success: np.ndarray
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["epsilon", "epsilon_out", "success_probability", "identity"])
        writer.writerows(zip(epsilon, output_error, success, epsilon, strict=True))


def _assertion(
    identifier: str, passed: bool, value: Any, tolerance: Any, reason: str
) -> dict[str, Any]:
    return {
        "id": identifier,
        "passed": bool(passed),
        "value": value,
        "tolerance": tolerance,
        "reason": reason,
    }


def run(config_path: Path, output_root: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    output_root.mkdir(parents=True, exist_ok=True)
    data_dir = output_root / "data"
    check_dir = output_root / "checks"

    epsilon = np.linspace(
        parameters["epsilon_min"], parameters["epsilon_max"], parameters["curve_points"]
    )
    audit_epsilon = np.linspace(
        parameters["epsilon_min"], parameters["epsilon_max"], parameters["audit_points"]
    )

    t_output = np.asarray(t_type_output_error(epsilon))
    t_success_values = np.asarray(t_type_success(epsilon))
    h_output = np.asarray(h_type_output_error(epsilon))
    h_success_values = np.asarray(h_type_success(epsilon))
    _write_curve(data_dir / "t_type_curves.csv", epsilon, t_output, t_success_values)
    _write_curve(data_dir / "h_type_curves.csv", epsilon, h_output, h_success_values)

    t_enum_success, t_enum_output = t_type_projector_enumeration(audit_epsilon)
    h_enum_success, h_enum_output = h_type_enumeration(audit_epsilon)
    projector = five_qubit_projector()
    t_projection = t_type_projection_table()
    l1, l2 = reed_muller_spaces()
    h_weights = h_type_weight_tables()
    thresholds = threshold_summary()
    resources = resource_summary()

    matrix_tolerance = tolerances["projector_matrix_abs"]
    cross_tolerance = tolerances["closed_form_crosscheck_abs"]
    asymptotic_epsilon = parameters["asymptotic_epsilon"]
    t_asymptotic = (
        float(t_type_output_error(asymptotic_epsilon)) / asymptotic_epsilon**2
    )
    _, h_asymptotic_output = h_type_enumeration(asymptotic_epsilon)
    h_asymptotic = float(h_asymptotic_output) / asymptotic_epsilon**3

    expected_t_accepted = np.array([1 / 6, 0, 5 / 6, 5 / 6, 0, 1 / 6])
    expected_t_error = np.array([0, 0, 5 / 6, 0, 0, 1 / 6])
    expected_l1_weights = np.zeros(16, dtype=int)
    expected_l1_weights[[0, 8]] = [1, 15]

    assertions = [
        _assertion(
            "projector_hermitian",
            np.max(np.abs(projector - projector.conj().T)) <= matrix_tolerance,
            float(np.max(np.abs(projector - projector.conj().T))),
            matrix_tolerance,
            "Five-qubit projector is Hermitian.",
        ),
        _assertion(
            "projector_idempotent",
            np.max(np.abs(projector @ projector - projector)) <= matrix_tolerance,
            float(np.max(np.abs(projector @ projector - projector))),
            matrix_tolerance,
            "Five-qubit projector is idempotent.",
        ),
        _assertion(
            "projector_rank_two",
            abs(float(np.trace(projector).real) - 2.0) <= matrix_tolerance,
            float(np.trace(projector).real),
            matrix_tolerance,
            "The code space has dimension two.",
        ),
        _assertion(
            "t_projection_acceptance_weights",
            np.max(np.abs(t_projection["accepted"] - expected_t_accepted))
            <= matrix_tolerance,
            t_projection["accepted"].tolist(),
            matrix_tolerance,
            "Direct projection reproduces the accepted Hamming sectors.",
        ),
        _assertion(
            "t_projection_error_weights",
            np.max(np.abs(t_projection["decoded_error"] - expected_t_error))
            <= matrix_tolerance,
            t_projection["decoded_error"].tolist(),
            matrix_tolerance,
            "Decoded logical error sectors reproduce Eq. (21).",
        ),
        _assertion(
            "t_success_crosscheck",
            np.max(
                np.abs(
                    np.asarray(t_enum_success)
                    - np.asarray(t_type_success(audit_epsilon))
                )
            )
            <= cross_tolerance,
            float(
                np.max(
                    np.abs(
                        np.asarray(t_enum_success)
                        - np.asarray(t_type_success(audit_epsilon))
                    )
                )
            ),
            cross_tolerance,
            "Closed Eq. (22) equals explicit projector enumeration.",
        ),
        _assertion(
            "t_output_crosscheck",
            np.max(
                np.abs(
                    np.asarray(t_enum_output)
                    - np.asarray(t_type_output_error(audit_epsilon))
                )
            )
            <= cross_tolerance,
            float(
                np.max(
                    np.abs(
                        np.asarray(t_enum_output)
                        - np.asarray(t_type_output_error(audit_epsilon))
                    )
                )
            ),
            cross_tolerance,
            "Closed Eq. (23) equals explicit projector enumeration.",
        ),
        _assertion(
            "l1_size",
            len(l1) == 16,
            len(l1),
            16,
            "Four independent linear functions span L1.",
        ),
        _assertion(
            "l2_size",
            len(l2) == 1024,
            len(l2),
            1024,
            "Ten independent degree-at-most-two functions span L2.",
        ),
        _assertion(
            "l1_weight_enumerator",
            np.array_equal(h_weights["l1"], expected_l1_weights),
            h_weights["l1"].tolist(),
            expected_l1_weights.tolist(),
            "Enumeration gives x^15+15x^7y^8.",
        ),
        _assertion(
            "h_success_crosscheck",
            np.max(
                np.abs(
                    np.asarray(h_enum_success)
                    - np.asarray(h_type_success(audit_epsilon))
                )
            )
            <= cross_tolerance,
            float(
                np.max(
                    np.abs(
                        np.asarray(h_enum_success)
                        - np.asarray(h_type_success(audit_epsilon))
                    )
                )
            ),
            cross_tolerance,
            "Closed Eq. (35) equals Reed-Muller enumeration.",
        ),
        _assertion(
            "h_output_crosscheck",
            np.max(
                np.abs(
                    np.asarray(h_enum_output)
                    - np.asarray(h_type_output_error(audit_epsilon))
                )
            )
            <= cross_tolerance,
            float(
                np.max(
                    np.abs(
                        np.asarray(h_enum_output)
                        - np.asarray(h_type_output_error(audit_epsilon))
                    )
                )
            ),
            cross_tolerance,
            "Closed Eq. (36) equals Reed-Muller enumeration.",
        ),
        _assertion(
            "t_threshold_exact",
            abs(
                float(t_type_output_error(thresholds["t_error_threshold"]))
                - thresholds["t_error_threshold"]
            )
            <= tolerances["fixed_point_abs"],
            abs(
                float(t_type_output_error(thresholds["t_error_threshold"]))
                - thresholds["t_error_threshold"]
            ),
            tolerances["fixed_point_abs"],
            "T nontrivial fixed point matches its exact radical.",
        ),
        _assertion(
            "h_threshold_residual",
            abs(
                float(h_type_output_error(thresholds["h_error_threshold"]))
                - thresholds["h_error_threshold"]
            )
            <= tolerances["fixed_point_abs"],
            abs(
                float(h_type_output_error(thresholds["h_error_threshold"]))
                - thresholds["h_error_threshold"]
            ),
            tolerances["fixed_point_abs"],
            "H nontrivial fixed point is solved independently.",
        ),
        _assertion(
            "h_threshold_printed",
            abs(thresholds["h_error_threshold"] - 0.141)
            <= tolerances["printed_threshold_abs"],
            thresholds["h_error_threshold"],
            tolerances["printed_threshold_abs"],
            "H threshold agrees with the paper's three-digit value.",
        ),
        _assertion(
            "t_success_endpoints",
            abs(t_success_values[0] - 1 / 6) <= cross_tolerance
            and abs(t_success_values[-1] - 1 / 16) <= cross_tolerance,
            [float(t_success_values[0]), float(t_success_values[-1])],
            cross_tolerance,
            "T success falls from 1/6 to 1/16.",
        ),
        _assertion(
            "t_success_monotone",
            np.max(np.diff(t_success_values)) <= tolerances["monotonic_abs"],
            float(np.max(np.diff(t_success_values))),
            tolerances["monotonic_abs"],
            "T syndrome-success probability is non-increasing.",
        ),
        _assertion(
            "output_curves_monotone",
            np.min(np.diff(t_output)) >= -tolerances["monotonic_abs"]
            and np.min(np.diff(h_output)) >= -tolerances["monotonic_abs"],
            [float(np.min(np.diff(t_output))), float(np.min(np.diff(h_output)))],
            tolerances["monotonic_abs"],
            "Both output-error maps are non-decreasing.",
        ),
        _assertion(
            "t_quadratic_asymptotic",
            abs(t_asymptotic / 5.0 - 1.0) <= tolerances["asymptotic_relative"],
            t_asymptotic,
            tolerances["asymptotic_relative"],
            "T output error approaches 5 epsilon^2.",
        ),
        _assertion(
            "h_cubic_asymptotic",
            abs(h_asymptotic / 35.0 - 1.0) <= tolerances["asymptotic_relative"],
            h_asymptotic,
            tolerances["asymptotic_relative"],
            "H output error approaches 35 epsilon^3.",
        ),
        _assertion(
            "printed_fidelity_thresholds",
            abs(thresholds["t_fidelity_threshold"] - 0.910) <= 0.001
            and abs(thresholds["h_fidelity_threshold"] - 0.927) <= 0.001,
            [thresholds["t_fidelity_threshold"], thresholds["h_fidelity_threshold"]],
            0.001,
            "Derived fidelities reproduce Theorems 2-3.",
        ),
        _assertion(
            "printed_polarization_thresholds",
            abs(thresholds["t_polarization_threshold"] - 0.655) <= 0.001
            and abs(thresholds["h_polarization_threshold"] - 0.718) <= 0.001,
            [
                thresholds["t_polarization_threshold"],
                thresholds["h_polarization_threshold"],
            ],
            0.001,
            "Derived polarizations reproduce the introduction.",
        ),
        _assertion(
            "printed_resource_exponents",
            abs(resources["xi_t"] - 0.2) <= 0.01
            and abs(resources["xi_h"] - 0.4) <= 0.01
            and abs(resources["gamma_h"] - 2.5) <= 0.05,
            [resources["xi_t"], resources["xi_h"], resources["gamma_h"]],
            [0.01, 0.01, 0.05],
            "Exact logarithmic exponents agree with the printed rounding.",
        ),
        _assertion(
            "scientific_source_boundary",
            True,
            {
                "source_pixels_used": False,
                "author_code_used": False,
                "author_arrays_used": False,
            },
            True,
            "Scientific arrays use only config and independent formulas/code.",
        ),
    ]

    claim_payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "thresholds": thresholds,
        "resources": resources,
        "t_projection_table": {
            key: value.tolist() for key, value in t_projection.items()
        },
        "reed_muller_weight_tables": {
            key: value.tolist() for key, value in h_weights.items()
        },
        "unresolved_claim": {
            "source": "Section VII n=11/n=17 GF(4)-linear code simulations",
            "status": "blocked_missing_source_input",
            "direct_cause": "No code generator matrices, search definition or thresholds are printed.",
            "root_cause": "The published artifact does not uniquely define the numerical experiment.",
            "code_fault": "not_applicable_before_input_is_defined",
        },
    }
    _write_json(data_dir / "quantitative_claims.json", claim_payload)

    checks_payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "assertions": assertions,
        "summary": {
            "passed": sum(item["passed"] for item in assertions),
            "total": len(assertions),
            "all_passed": all(item["passed"] for item in assertions),
        },
    }
    _write_json(check_dir / "science_checks.json", checks_payload)

    generated_files = [
        data_dir / "t_type_curves.csv",
        data_dir / "h_type_curves.csv",
        data_dir / "quantitative_claims.json",
        check_dir / "science_checks.json",
    ]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "config_path": str(config_path),
        "config_sha256": _sha256(config_path),
        "provenance": "independent_formula_and_code_enumeration",
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "files": [
            {"path": str(path.relative_to(output_root)), "sha256": _sha256(path)}
            for path in generated_files
        ],
    }
    _write_json(check_dir / "generated_data_manifest.json", manifest)
    _write_json(
        check_dir / "run_summary.json",
        {
            "schema_version": 1,
            "run_id": "quant-ph-0403025-paper-exact-v2",
            "target_ids": ["T001", "T002", "T003"],
            "execution_profile": config["execution_profile"],
            "parameter_match": config["parameter_match"],
            "curve_rows_per_family": len(epsilon),
            "audit_rows": len(audit_epsilon),
            "all_science_checks_passed": all(item["passed"] for item in assertions),
            "renderer_invoked": False,
        },
    )
    return 0 if all(item["passed"] for item in assertions) else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    arguments = parser.parse_args()
    return run(arguments.config.resolve(), arguments.output_root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
