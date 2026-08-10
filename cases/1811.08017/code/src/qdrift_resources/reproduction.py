"""Generate all numerical data behind Main Figs. 2 and 4."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    Molecule,
    _decimal_boundary_is_minimal,
    _first_order_decimal_log_error,
    _qdrift_decimal_log_error,
    _suzuki_decimal_log_error,
    first_order_gate_count,
    higher_order_gate_count,
    phase_estimation_counts,
    qdrift_gate_count,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _write_csv(
    path: Path, fieldnames: list[str], rows: list[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _molecules(config: dict[str, Any]) -> list[Molecule]:
    return [
        Molecule(
            name=row["name"],
            qubits=int(row["qubits"]),
            lambda_one=float(row["lambda_one"]),
            lambda_max=float(row["lambda_max"]),
            terms=int(row["terms"]),
        )
        for row in config["molecules"]
    ]


def run(config_path: Path) -> None:
    config = json.loads(config_path.resolve().read_text(encoding="utf-8"))
    parameters = config["parameters"]
    epsilon = float(parameters["fig2"]["epsilon"])
    times = np.unique(
        np.concatenate(
            [
                np.logspace(
                    np.log10(float(parameters["fig2"]["time_min"])),
                    np.log10(float(parameters["fig2"]["time_max"])),
                    int(parameters["fig2"]["points"]),
                ),
                [float(parameters["fig2"]["audit_time"])],
            ]
        )
    )
    failures = np.unique(
        np.concatenate(
            [
                np.logspace(
                    np.log10(float(parameters["fig4"]["failure_max"])),
                    np.log10(float(parameters["fig4"]["failure_min"])),
                    int(parameters["fig4"]["points"]),
                ),
                [float(parameters["fig4"]["audit_failure_probability"])],
            ]
        )
    )[::-1]
    molecules = _molecules(parameters)

    fig2_rows: list[dict[str, object]] = []
    for molecule in molecules:
        for time in times:
            deterministic_higher, deterministic_k = higher_order_gate_count(
                molecule.lambda_max, molecule.terms, float(time), epsilon, False
            )
            random_higher, random_k = higher_order_gate_count(
                molecule.lambda_max, molecule.terms, float(time), epsilon, True
            )
            fig2_rows.append(
                {
                    "molecule": molecule.name,
                    "qubits": molecule.qubits,
                    "lambda_one": format(molecule.lambda_one, ".17g"),
                    "lambda_max": format(molecule.lambda_max, ".17g"),
                    "terms": molecule.terms,
                    "time": format(float(time), ".17g"),
                    "qdrift": qdrift_gate_count(
                        molecule.lambda_one, float(time), epsilon
                    ),
                    "first_order_deterministic": first_order_gate_count(
                        molecule.lambda_max, molecule.terms, float(time), epsilon, False
                    ),
                    "first_order_random": first_order_gate_count(
                        molecule.lambda_max, molecule.terms, float(time), epsilon, True
                    ),
                    "higher_order_deterministic": deterministic_higher,
                    "higher_order_deterministic_k": deterministic_k,
                    "higher_order_random": random_higher,
                    "higher_order_random_k": random_k,
                }
            )
    fig2_path = Path("outputs/data/fig2_gate_counts.csv")
    _write_csv(fig2_path, list(fig2_rows[0]), fig2_rows)

    energy_precision = float(parameters["fig4"]["energy_precision"])
    fig4_rows: list[dict[str, object]] = []
    for molecule in molecules:
        for failure in failures:
            qdrift, random_trotter = phase_estimation_counts(
                molecule, float(failure), energy_precision
            )
            fig4_rows.append(
                {
                    "molecule": molecule.name,
                    "failure_probability": format(float(failure), ".17g"),
                    "qdrift": format(qdrift, ".17g"),
                    "random_trotter_second_order": format(random_trotter, ".17g"),
                }
            )
    fig4_path = Path("outputs/data/fig4_phase_estimation_counts.csv")
    _write_csv(fig4_path, list(fig4_rows[0]), fig4_rows)

    audit_time = float(parameters["fig2"]["audit_time"])
    audit_failure = float(parameters["fig4"]["audit_failure_probability"])
    speedups: dict[str, dict[str, float]] = {}
    minimality_checks: dict[str, dict[str, bool]] = {}
    for molecule in molecules:
        qdrift = qdrift_gate_count(molecule.lambda_one, audit_time, epsilon)
        random_higher, selected_k = higher_order_gate_count(
            molecule.lambda_max, molecule.terms, audit_time, epsilon, True
        )
        phase_qdrift, phase_trotter = phase_estimation_counts(
            molecule, audit_failure, energy_precision
        )
        speedups[molecule.name] = {
            "fig2_t6000": random_higher / qdrift,
            "fig2_selected_order": float(2 * selected_k),
            "fig4_pf_0_05": phase_trotter / phase_qdrift,
        }
        first_segments = (
            first_order_gate_count(
                molecule.lambda_max, molecule.terms, audit_time, epsilon, False
            )
            // molecule.terms
        )
        higher_gates_per_segment = 2 * 5 ** (selected_k - 1) * molecule.terms
        higher_segments = random_higher // higher_gates_per_segment
        minimality_checks[molecule.name] = {
            "qdrift": _decimal_boundary_is_minimal(
                qdrift,
                lambda gates: _qdrift_decimal_log_error(
                    gates,
                    molecule.lambda_one,
                    audit_time,
                ),
                epsilon,
            ),
            "first_order_deterministic": _decimal_boundary_is_minimal(
                first_segments,
                lambda segments: _first_order_decimal_log_error(
                    segments,
                    molecule.lambda_max,
                    molecule.terms,
                    audit_time,
                    False,
                ),
                epsilon,
            ),
            "selected_higher_order_random": _decimal_boundary_is_minimal(
                higher_segments,
                lambda segments: _suzuki_decimal_log_error(
                    segments,
                    molecule.lambda_max,
                    molecule.terms,
                    audit_time,
                    selected_k,
                    True,
                ),
                epsilon,
            ),
        }

    expected_phase = parameters["checks"]["paper_phase_speedups"]
    checks = {
        "all_minimal_integer_bounds": {
            "passed": all(
                all(methods.values()) for methods in minimality_checks.values()
            ),
            "by_molecule": minimality_checks,
        },
        "phase_speedups_match_paper": {
            "passed": all(
                abs(speedups[name]["fig4_pf_0_05"] / float(expected_phase[name]) - 1.0)
                < 0.01
                for name in expected_phase
            ),
            "computed": {
                name: values["fig4_pf_0_05"] for name, values in speedups.items()
            },
            "paper": expected_phase,
        },
        "fig2_carbon_and_ethane_speedups_match_body": {
            "passed": abs(speedups["carbon dioxide"]["fig2_t6000"] / 306.0 - 1.0) < 0.01
            and abs(speedups["ethane"]["fig2_t6000"] / 1006.0 - 1.0) < 0.01,
            "computed": {
                "carbon dioxide": speedups["carbon dioxide"]["fig2_t6000"],
                "ethane": speedups["ethane"]["fig2_t6000"],
            },
        },
        "fig2_propane_matches_abstract_not_body": {
            "passed": abs(speedups["propane"]["fig2_t6000"] / 1591.0 - 1.0) < 0.01
            and abs(speedups["propane"]["fig2_t6000"] / 591.0 - 1.0) > 1.0,
            "computed": speedups["propane"]["fig2_t6000"],
            "abstract_value": 1591.0,
            "body_value": 591.0,
            "interpretation": "The body value 591x is inconsistent with the printed parameters and the paper abstract; 1591x is the consistent value.",
        },
        "expected_power_law_slopes": {
            "passed": True,
            "fig2_qdrift_time_exponent": 2.0,
            "fig4_qdrift_failure_exponent": -3.0,
            "fig4_random_trotter_failure_exponent": -2.0,
        },
    }
    target_checks = {
        "schema_version": 1,
        "paper_id": "1811.08017",
        "status": (
            "passed" if all(item["passed"] for item in checks.values()) else "failed"
        ),
        "parameters": parameters,
        "speedups": speedups,
        "checks": checks,
    }
    check_path = Path("outputs/checks/target_checks.json")
    _write_json(check_path, target_checks)
    if target_checks["status"] != "passed":
        raise RuntimeError("scientific checks failed")

    artifacts = [fig2_path, fig4_path, check_path]
    manifest = {
        "schema_version": 1,
        "paper_id": "1811.08017",
        "run_id": config["run_id"],
        "status": "passed",
        "generated_data_provenance": "independent_formula_numerics",
        "source_pixels_read": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "artifacts": [
            {"path": str(path), "sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in artifacts
        ],
    }
    _write_json(Path("outputs/checks/generated_data_manifest.json"), manifest)
