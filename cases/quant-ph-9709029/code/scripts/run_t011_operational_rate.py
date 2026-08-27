#!/usr/bin/env python3
"""Run the independent pure-state communication-rate certificate."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from wootters.operational_rate import (  # noqa: E402
    check_operational_rate_records,
    optimal_pure_state_communication,
)


def run(config_path: Path, workspace: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    exponent = float(parameters["allowed_infidelity_exponent"])
    records = []
    for probability in parameters["schmidt_probabilities"]:
        for copies in parameters["copy_counts"]:
            records.append(
                optimal_pure_state_communication(
                    float(probability),
                    int(copies),
                    allowed_infidelity=int(copies) ** (-exponent),
                )
            )

    checks = check_operational_rate_records(records)
    checks.update(
        {
            "schema_version": 1,
            "paper_id": "quant-ph-9709029",
            "target_id": "T011",
            "parameter_match": "not_applicable",
            "theorem_contract": {
                "achievability": (
                    "Schmidt compression to the largest 2^q coefficients, "
                    "followed by transmission and decompression."
                ),
                "converse": (
                    "q transmitted qubits create Schmidt rank at most 2^q; "
                    "the Ky Fan bound limits fidelity to the largest-2^q mass."
                ),
                "asymptotic_limit": (
                    "For vanishing infidelity n^-0.4, q_n/n converges to H2(p)."
                ),
            },
            "source_boundary": config["source_boundary"],
        }
    )

    data_path = workspace / "outputs/data/T011_operational_communication_rate.csv"
    check_path = workspace / "outputs/checks/t011_operational_rate_theorem.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(records[0]).keys())
    with data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    check_path.write_text(
        json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not checks["passed"]:
        raise RuntimeError("T011 operational-rate checks failed")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/t011_operational_rate.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside workspace")
    checks = run(config_path, WORKSPACE)
    print(json.dumps({"passed": checks["passed"], "target_id": "T011"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
