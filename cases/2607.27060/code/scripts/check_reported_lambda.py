#!/usr/bin/env python3
"""Audit the reported model lambda values without changing panel data."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from local_choi_bound import reconstruct_reported_lambdas  # noqa: E402
from trotter_bounds import write_json  # noqa: E402


def main() -> int:
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    reconstructed = reconstruct_reported_lambdas()
    reported = {"xx_spin_chain": 7.071, "tfim_lattice": 8.0}
    comparisons = {
        "xx_source_snapshot_convention": {
            "reported": reported["xx_spin_chain"],
            "reconstructed": reconstructed[
                "xx_source_snapshot_convention"
            ]["lambda_max"],
        },
        "xx_literal_equation_28_convention": {
            "reported": reported["xx_spin_chain"],
            "reconstructed": reconstructed[
                "xx_literal_equation_28_convention"
            ]["lambda_max"],
        },
        "tfim_literal_equation_31_convention": {
            "reported": reported["tfim_lattice"],
            "reconstructed": reconstructed[
                "tfim_literal_equation_31_convention"
            ]["lambda_max"],
        },
    }
    for comparison in comparisons.values():
        comparison["absolute_difference"] = abs(
            comparison["reported"] - comparison["reconstructed"]
        )
        comparison["matches_reported_at_3_decimals"] = (
            round(comparison["reported"], 3)
            == round(comparison["reconstructed"], 3)
        )

    payload = {
        "schema_version": 1,
        "status": "passed_with_findings",
        "scope": "parameter_method_consistency_only",
        "generated_panel_data_changed": False,
        "reported_lambda": reported,
        "reconstructed": reconstructed,
        "comparisons": comparisons,
        "findings": [
            {
                "severity": "warning",
                "code": "reported_lambda_not_reproduced_by_local_choi_bound",
                "message": (
                    "The local Eq. (32) reconstruction does not reproduce the "
                    "reported lambda values under either the literal equations "
                    "or the frozen source snapshot's dissipator convention. "
                    "The figure targets therefore retain the explicitly reported "
                    "lambda values as paper parameters."
                ),
            },
            {
                "severity": "warning",
                "code": "xx_dissipator_factor_convention_differs",
                "message": (
                    "Eq. (28) is twice the standard dissipator built from the "
                    "jump amplitudes in Eq. (26), while the frozen source-only "
                    "implementation uses the standard dissipator."
                ),
            },
        ],
        "timing": {
            "wall_seconds": time.perf_counter() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu,
        },
    }
    output = (
        WORKSPACE
        / "outputs"
        / "checks"
        / "reported_lambda_consistency.json"
    )
    write_json(output, payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
