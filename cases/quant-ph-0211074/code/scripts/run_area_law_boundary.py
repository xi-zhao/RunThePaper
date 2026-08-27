#!/usr/bin/env python3
"""Execute or fail closed at the paper's underspecified area-law boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from vidal_entanglement.area_law import evaluate_area_law_dataset  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    parameters = config["parameters"]
    missing = [
        name
        for name, value in parameters["paper_model_contract"].items()
        if value in (None, "", [])
    ]
    datasets = parameters["datasets"]
    analyses = [evaluate_area_law_dataset(dataset) for dataset in datasets]
    if missing or not datasets:
        status = "blocked_publication_underspecified"
    else:
        status = "generated"
    payload = {
        "schema_version": 1,
        "paper_id": "quant-ph-0211074",
        "target_id": "T018",
        "status": status,
        "missing_paper_inputs": missing,
        "analyses": analyses,
        "required_dataset_schema": {
            "data_provenance": "independent_numerics",
            "boundary_measure": "strictly increasing positive array",
            "entropy": "aligned independently generated array",
        },
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "model_or_kappa_guessed": False,
        },
    }
    output = (WORKSPACE / args.output_root).resolve() / "checks" / "T018_area_law_assessment.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
