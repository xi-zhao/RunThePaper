#!/usr/bin/env python3
"""Reproduce the public-data columns of the paper's two AFHM tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from afhm_exact_diagonalization import (  # noqa: E402
    fixed_magnetization_basis,
    schmidt_probabilities_from_sector_state,
)
from afhm_paper_tables import (  # noqa: E402
    printed_value_tolerance,
    tuned_inverse_square_spectrum,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=WORKSPACE / "config" / "afhm_overlap_table.json")
    args = parser.parse_args()

    config = json.loads(args.config.read_text())
    figure_config_path = WORKSPACE / "config" / "afhm_figure1.json"
    figure_config_sha = hashlib.sha256(figure_config_path.read_bytes()).hexdigest()
    sector_dir = WORKSPACE / "outputs" / "data" / "afhm_figure1_sectors"
    energies_parts: list[np.ndarray] = []
    ranks_parts: list[np.ndarray] = []
    sector_eight = None
    for number_up in range(9):
        path = sector_dir / f"sector_{number_up:02d}.npz"
        saved = np.load(path)
        if str(saved["config_sha256"].item()) != figure_config_sha:
            raise RuntimeError(f"stale exact-diagonalization checkpoint: {path}")
        multiplicity = 1 if number_up == 8 else 2
        energies_parts.append(np.tile(saved["energies"], multiplicity))
        ranks_parts.append(np.tile(np.exp2(saved["s_min"]), multiplicity))
        if number_up == 8:
            if "ground_state" not in saved.files:
                raise RuntimeError("sector 8 checkpoint does not contain the ground state")
            sector_eight = saved

    energies = np.concatenate(energies_parts)
    stable_ranks = np.concatenate(ranks_parts)
    if len(energies) != 2**16 or sector_eight is None:
        raise RuntimeError("exact spectrum does not contain all 65,536 states")
    basis = fixed_magnetization_basis(16, 8)
    schmidt_probabilities = schmidt_probabilities_from_sector_state(
        sector_eight["ground_state"], basis, 16, 8
    )

    significant_figures = int(config["paper_values"]["significant_figures"])
    rows: list[dict] = []
    gates: dict[str, bool] = {
        "state_count": len(energies) == 2**16,
        "ground_state_normalized": abs(float(schmidt_probabilities.sum()) - 1.0) <= 1e-10,
    }
    for bond_dimension, paper_lambda, paper_m in zip(
        config["bond_dimensions"],
        config["paper_values"]["lambda"],
        config["paper_values"]["m"],
    ):
        reproduced_lambda = float(schmidt_probabilities[:bond_dimension].sum())
        tuned = tuned_inverse_square_spectrum(
            energies,
            stable_ranks,
            reproduced_lambda,
        )
        lambda_error = abs(reproduced_lambda - paper_lambda)
        m_error = abs(tuned.compression_bound - paper_m)
        lambda_tolerance = printed_value_tolerance(paper_lambda, significant_figures)
        m_tolerance = printed_value_tolerance(paper_m, significant_figures)
        gates[f"D{bond_dimension}_lambda_printed_value"] = lambda_error <= lambda_tolerance
        gates[f"D{bond_dimension}_stationarity"] = tuned.stationarity_relative_residual <= 1e-12
        rows.append(
            {
                "bond_dimension": bond_dimension,
                "paper_lambda": paper_lambda,
                "reproduced_lambda": reproduced_lambda,
                "lambda_abs_error": lambda_error,
                "lambda_print_tolerance": lambda_tolerance,
                "paper_m": paper_m,
                "reproduced_m": tuned.compression_bound,
                "m_abs_error": m_error,
                "m_print_tolerance": m_tolerance,
                "nu": tuned.nu,
                "ground_probability_residual": abs(tuned.ground_probability - reproduced_lambda),
                "stationarity_relative_residual": tuned.stationarity_relative_residual,
            }
        )

    data_path = WORKSPACE / "outputs" / "data" / "afhm_overlap_table.csv"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    failed_checks = [name for name, passed in gates.items() if not passed]
    m_diagnostic_checks = {
        f"D{row['bond_dimension']}_m_printed_value": row["m_abs_error"] <= row["m_print_tolerance"]
        for row in rows
    }
    m_diagnostic_failed_checks = [
        name for name, passed in m_diagnostic_checks.items() if not passed
    ]
    result = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_id": config["target_id"],
        "paper_asset": config["paper_asset"],
        "status": "passed" if not failed_checks else "failed",
        "artifact_stage": "paper_exact",
        "parameter_match": "partial",
        "parameter_uncertainty": config["known_uncertainty"],
        "method": {
            "ground_state_overlap": "sum of the largest D exact half-chain Schmidt probabilities",
            "tuned_m": "m=B2/B1^2 after bisection on nu to impose p1=Lambda(D)",
        },
        "tuned_m_diagnostic": {
            "status": "matched" if not m_diagnostic_failed_checks else "partial_match",
            "blocker": None if not m_diagnostic_failed_checks else "missing_author_data",
            "reason": "The paper does not release the degenerate-eigenspace basis or numerical arrays used to form every M_i.",
            "checks": m_diagnostic_checks,
            "failed_checks": m_diagnostic_failed_checks,
        },
        "rows": rows,
        "gates": gates,
        "failed_checks": failed_checks,
        "artifacts": {"data_csv": str(data_path.relative_to(WORKSPACE))},
    }
    result_path = WORKSPACE / "outputs" / "checks" / "afhm_overlap_table_result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failed_checks": failed_checks, "result": str(result_path)}, indent=2))
    return 0 if not failed_checks else 2


if __name__ == "__main__":
    raise SystemExit(main())
