#!/usr/bin/env python3
"""Enumerate negativity for every control-grouped DQC1 bipartition."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from geometric_discord.dqc1_entanglement import (  # noqa: E402
    control_grouped_bipartition_negativities,
)
from geometric_discord.model import dqc1_state, random_unitary  # noqa: E402


def run(config_path: Path, workspace: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    rng = np.random.default_rng(int(parameters["random_seed"]))
    alpha = float(parameters["alpha"])
    samples = int(parameters["haar_unitaries_per_size"])
    rows: list[dict[str, object]] = []
    summaries: dict[str, object] = {}

    for register_qubits in parameters["register_qubit_counts"]:
        n = int(register_qubits)
        size_rows: list[dict[str, object]] = []
        for sample in range(samples):
            unitary = random_unitary(rng, 1 << n)
            rho = dqc1_state(alpha, unitary)
            partitions = control_grouped_bipartition_negativities(rho, n)
            for item in partitions:
                row = {
                    "register_qubits": n,
                    "unitary_sample": sample,
                    "control_group_registers": ";".join(
                        str(value) for value in item.control_group_registers
                    ),
                    "complement_registers": ";".join(
                        str(value) for value in item.complement_registers
                    ),
                    "control_group_size": len(item.control_group_registers),
                    "negativity": item.negativity,
                    "minimum_partial_transpose_eigenvalue": (
                        item.minimum_partial_transpose_eigenvalue
                    ),
                }
                rows.append(row)
                size_rows.append(row)
        values = np.array([float(row["negativity"]) for row in size_rows])
        control_split_values = np.array(
            [
                float(row["negativity"])
                for row in size_rows
                if int(row["control_group_size"]) == 0
            ]
        )
        summaries[f"n={n}"] = {
            "bipartitions_per_unitary": (1 << n) - 1,
            "unitaries": samples,
            "maximum_negativity": float(np.max(values)),
            "mean_negativity": float(np.mean(values)),
            "control_vs_register_maximum": float(np.max(control_split_values)),
        }

    threshold = float(parameters["diagnostic_small_negativity_threshold"])
    maximum = max(
        float(summary["maximum_negativity"])
        for summary in summaries.values()
    )
    control_maximum = max(
        float(summary["control_vs_register_maximum"])
        for summary in summaries.values()
    )
    checks = {
        "schema_version": 1,
        "paper_id": "1004.0190",
        "target_id": "T010",
        "passed": bool(control_maximum <= 1.0e-12 and maximum <= threshold),
        "parameter_match": "proxy_model",
        "all_declared_bipartitions_enumerated": True,
        "control_vs_register_separable": control_maximum <= 1.0e-12,
        "diagnostic_threshold": threshold,
        "maximum_observed_negativity": maximum,
        "diagnostic_smallness_passed": maximum <= threshold,
        "paper_claim_adjudication": "inconclusive",
        "remaining_scientific_gap": (
            "The publication specifies neither an entanglement measure, a "
            "smallness threshold, a unitary ensemble, nor an asymptotic rate."
        ),
        "summaries": summaries,
        "scientific_boundary": config["scientific_boundary"],
        "source_boundary": config["source_boundary"],
    }

    data_path = workspace / "outputs/data/T010_dqc1_bipartition_negativity.csv"
    check_path = workspace / "outputs/checks/t010_dqc1_bipartition_entanglement.json"
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
        raise RuntimeError("T010 DQC1 bipartition checks failed")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/t010_bipartition_entanglement.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside workspace")
    checks = run(config_path, WORKSPACE)
    print(json.dumps({"passed": checks["passed"], "target_id": "T010"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
