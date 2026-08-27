#!/usr/bin/env python3
"""Freeze the decidable boundary of the zero-discord DQC1 hardness claim."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from geometric_discord.dqc1_hardness import (  # noqa: E402
    explicit_phase_involution,
    hardness_contract_boundary,
    phase_involution_normalized_trace,
)


def run(config_path: Path, workspace: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    crosscheck_max = int(parameters["explicit_matrix_crosscheck_max_qubits"])
    rows: list[dict[str, object]] = []
    maximum_formula_error = 0.0
    for register_qubits in parameters["register_qubit_counts"]:
        n = int(register_qubits)
        dimension = 1 << n
        offset = int(math.sqrt(dimension))
        positive = min(dimension, dimension // 2 + offset)
        negative = dimension - positive
        for phase in parameters["phases_radians"]:
            record = phase_involution_normalized_trace(
                float(phase), positive, negative
            )
            row = {"register_qubits": n, **asdict(record)}
            if n <= crosscheck_max:
                matrix = explicit_phase_involution(float(phase), positive, negative)
                direct = np.trace(matrix) / dimension
                error = abs(
                    direct
                    - complex(
                        record.normalized_trace_real,
                        record.normalized_trace_imag,
                    )
                )
                maximum_formula_error = max(maximum_formula_error, float(error))
                row["explicit_matrix_formula_error"] = float(error)
            else:
                row["explicit_matrix_formula_error"] = "not_run"
            rows.append(row)

    boundary = hardness_contract_boundary()
    checks = {
        "schema_version": 1,
        "paper_id": "1004.0190",
        "target_id": "T009",
        "passed": maximum_formula_error <= 1.0e-13,
        "parameter_match": "not_applicable",
        "phase_involution_trace_identity_passed": maximum_formula_error <= 1.0e-13,
        "maximum_formula_error": maximum_formula_error,
        "complexity_claim_adjudication": boundary["adjudication"],
        "hardness_contract": boundary,
        "source_boundary": config["source_boundary"],
    }
    data_path = workspace / "outputs/data/T009_phase_involution_trace.csv"
    check_path = workspace / "outputs/checks/t009_dqc1_hardness.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    check_path.write_text(
        json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not checks["passed"]:
        raise RuntimeError("T009 phase-involution formula check failed")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/t009_hardness_boundary.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside workspace")
    checks = run(config_path, WORKSPACE)
    print(
        json.dumps(
            {
                "passed": checks["passed"],
                "target_id": "T009",
                "complexity_claim_adjudication": checks[
                    "complexity_claim_adjudication"
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
