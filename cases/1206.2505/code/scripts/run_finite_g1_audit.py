#!/usr/bin/env python3
"""Run the independent finite-chain audit for the missing finite-g1 claim."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dqpt_tfim.finite_g1 import finite_g1_sector_rates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    parameters = config["parameters"]
    phases = np.linspace(
        float(parameters["phase_min"]),
        float(parameters["phase_max"]),
        int(parameters["phase_points"]),
    )
    rows: list[dict[str, float | int]] = []
    summaries: list[dict[str, float | int]] = []
    for g1 in [float(value) for value in parameters["g1_values"]]:
        result = finite_g1_sector_rates(
            int(parameters["sites"]), g1, phases, periodic=bool(parameters["periodic"])
        )
        error = np.abs(
            result["finite_dominant_rate"] - result["asymptotic_dominant_rate"]
        )
        summaries.append(
            {
                "g1": g1,
                "mean_absolute_correction": float(np.mean(error)),
                "maximum_absolute_correction": float(np.max(error)),
                "maximum_norm_error": float(np.max(np.abs(result["state_norm"] - 1.0))),
            }
        )
        for index, phase in enumerate(phases):
            rows.append(
                {
                    "sites": int(parameters["sites"]),
                    "g1": g1,
                    "phase_g1_t": float(phase),
                    "time": float(result["time"][index]),
                    "finite_diagonal_rate": float(result["finite_diagonal_rate"][index]),
                    "finite_off_diagonal_rate": float(result["finite_off_diagonal_rate"][index]),
                    "finite_dominant_rate": float(result["finite_dominant_rate"][index]),
                    "asymptotic_dominant_rate": float(result["asymptotic_dominant_rate"][index]),
                    "absolute_correction": float(error[index]),
                }
            )

    output_root = (WORKSPACE / args.output_root).resolve()
    data_path = output_root / "data" / "finite_g1_correction_audit.csv"
    check_path = output_root / "checks" / "finite_g1_correction_audit.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    corrections = [float(row["mean_absolute_correction"]) for row in summaries]
    payload = {
        "schema_version": 1,
        "paper_id": "1206.2505",
        "target_id": "T015",
        "status": "exploratory_finite_chain_generated",
        "paper_exact_status": "blocked_publication_withholds_finite_g1_expansion",
        "checks": {
            "norm_preserved": max(float(row["maximum_norm_error"]) for row in summaries)
            <= float(config["acceptance"]["max_norm_error"]),
            "correction_decreases_over_g1_grid": all(
                right < left for left, right in zip(corrections, corrections[1:])
            ),
        },
        "summaries": summaries,
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "unpublished_coefficients_guessed": False,
        },
    }
    check_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
