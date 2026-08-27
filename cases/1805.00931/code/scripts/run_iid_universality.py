#!/usr/bin/env python3
"""Execute the clean-room IID-distribution universality target."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from kicked_ising.iid_universality import iid_transfer_spectrum  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    parameters = config["parameters"]
    rows = [
        {
            "distribution": distribution,
            **iid_transfer_spectrum(
                int(time),
                h_mean=float(parameters["h_mean"]),
                standard_deviation=float(parameters["standard_deviation"]),
                distribution=str(distribution),
            ),
        }
        for distribution in parameters["distributions"]
        for time in parameters["times"]
    ]
    checks = {
        "all_unit_multiplicities_match": all(
            row["unit_modulus_count"] == row["expected_unit_modulus_count"]
            for row in rows
        ),
        "all_characteristic_functions_normalized": all(
            float(row["characteristic_at_zero_error"]) <= 1e-14 for row in rows
        ),
        "all_nonprotected_modes_contract": all(
            float(row["maximum_subunit_modulus"])
            < float(config["acceptance"]["maximum_subunit_modulus"])
            for row in rows
        ),
    }
    payload = {
        "schema_version": 1,
        "paper_id": "1805.00931",
        "target_id": "T006",
        "status": "feature_evidence_generated",
        "claim_scope": (
            "The general characteristic-function implementation accepts each "
            "supported IID law; the frozen smoke campaign checks Gaussian, bounded, "
            "discrete, and heavy-tailed representatives at finite transfer times."
        ),
        "checks": checks,
        "rows": rows,
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
        },
    }
    output = (WORKSPACE / args.output_root).resolve() / "checks" / "iid_distribution_universality.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
