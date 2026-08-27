#!/usr/bin/env python3
"""Validate or assemble the publication-underspecified DFT displacement target."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from moire_hubbard.dft_displacement import assemble_periodic_displacement_map  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    parameters = config["parameters"]
    required = parameters["paper_input_contract"]
    missing = [name for name, value in required.items() if value in (None, "", [])]
    samples = parameters["independent_qe_samples"]
    map_payload = None
    if not missing and samples:
        map_payload = assemble_periodic_displacement_map(
            samples,
            u_points=int(parameters["displacement_grid"]["u_points"]),
            v_points=int(parameters["displacement_grid"]["v_points"]),
        )
    status = "generated" if map_payload is not None else "blocked_publication_underspecified"
    output_root = (WORKSPACE / args.output_root).resolve()
    plan_path = output_root / "checks" / "d001_dft_campaign_plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan = {
        "schema_version": 1,
        "paper_id": "1804.03151",
        "target_id": "D001",
        "status": status,
        "missing_paper_inputs": missing,
        "required_sample_schema": {
            "data_provenance": "independent_qe_run",
            "u_index": "integer grid index",
            "v_index": "integer grid index",
            "valence_max_ev": "parsed from a clean-room Quantum ESPRESSO run",
        },
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "pseudopotentials_or_coordinates_guessed": False,
        },
    }
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if map_payload is not None:
        map_path = output_root / "data" / "D001_main_fig1c_dft_map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(map_payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
