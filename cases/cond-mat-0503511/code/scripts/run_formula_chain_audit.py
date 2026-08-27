#!/usr/bin/env python3
"""Emit target-specific evidence for the paper's Eqs. (1)-(14)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from zurek_qpt.formula_chain import evaluate_formula_chain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    arguments = parser.parse_args()
    config = json.loads((WORKSPACE / arguments.config).read_text(encoding="utf-8"))
    result = evaluate_formula_chain(config["parameters"])
    payload = {
        "schema_version": 1,
        "paper_id": "cond-mat-0503511",
        "target_id": "T007",
        **result,
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
        },
    }
    output = (
        (WORKSPACE / arguments.output_root).resolve()
        / "checks"
        / "T007_formula_chain.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if payload["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
