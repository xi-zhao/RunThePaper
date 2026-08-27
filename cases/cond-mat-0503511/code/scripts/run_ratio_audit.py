#!/usr/bin/env python3
"""Generate the claim-specific Eq. (15) arithmetic evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from zurek_qpt.ratio_audit import (  # noqa: E402
    decimal_literal_ratio,
    lzf_kzm_density_ratio,
    ratio_from_preceding_equations,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    parameters = config["parameters"]
    rows = []
    for fidelity in [float(value) for value in parameters["fidelities"]]:
        literal = lzf_kzm_density_ratio(fidelity)
        rederived = ratio_from_preceding_equations(
            fidelity,
            coupling_w=float(parameters["coupling_w"]),
            tau_q=float(parameters["tau_q"]),
            hbar=float(parameters["hbar"]),
        )
        rows.append(
            {
                "fidelity": fidelity,
                "literal_eq15_ratio": literal,
                "rederived_eq10_eq14_ratio": rederived,
                "route_difference": abs(literal - rederived),
            }
        )
    target_fidelity = str(parameters["target_fidelity"])
    literal_target = lzf_kzm_density_ratio(float(target_fidelity))
    decimal_target = float(decimal_literal_ratio(target_fidelity))
    prose_value = float(parameters["paper_prose_value"])
    tolerance = float(config["acceptance"]["independent_route_tolerance"])
    payload = {
        "schema_version": 1,
        "paper_id": "cond-mat-0503511",
        "target_id": "T006",
        "status": "stable_source_discrepancy",
        "checks": {
            "all_algebraic_routes_agree": all(
                float(row["route_difference"]) <= tolerance for row in rows
            ),
            "decimal_route_agrees": abs(literal_target - decimal_target) <= tolerance,
            "paper_prose_value_disagrees": abs(literal_target - prose_value)
            > float(config["acceptance"]["paper_prose_difference_minimum"]),
        },
        "target": {
            "fidelity": float(target_fidelity),
            "literal_eq15_ratio": literal_target,
            "high_precision_ratio": decimal_target,
            "paper_prose_value": prose_value,
            "absolute_discrepancy": abs(literal_target - prose_value),
        },
        "rows": rows,
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
        },
        "adjudication_boundary": (
            "The independent arithmetic stabilizes the discrepancy but does not "
            "promote a paper-error candidate without a fresh-context review."
        ),
    }
    output = (WORKSPACE / args.output_root).resolve() / "checks" / "T006_lzf_kzm_ratio.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if all(payload["checks"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
