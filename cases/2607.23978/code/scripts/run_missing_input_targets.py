#!/usr/bin/env python3
"""Run formula-level targets or emit an explicit publication-input blocker."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_workspace = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_workspace))

from src.missing_input_targets import (  # noqa: E402
    load_formula_input,
    reproduce_complete_povm,
    reproduce_nonoptimal_series,
)


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    input_ref = config.get("scientific_input_ref")
    check_path = Path(config["outputs"]["check"])
    if not input_ref:
        _write(
            check_path,
            {
                "schema_version": 1,
                "status": "blocked_on_paper_input",
                "scientific_coverage_awarded": False,
                "missing_input": "public formula definitions for A1, A2, and the complete POVM",
                "required_schema": config["required_scientific_input_schema"],
                "forbidden_substitutes": [
                    "source-image pixels",
                    "digitized curves",
                    "author numerical arrays",
                    "author reproduction code",
                ],
            },
        )
        return 0

    payload = load_formula_input(Path(input_ref))
    parameters = config["parameters"]
    nonoptimal = reproduce_nonoptimal_series(payload, parameters)
    povm = reproduce_complete_povm(payload, parameters)
    data_path = Path(config["outputs"]["data"])
    _write(
        data_path,
        {
            "schema_version": 1,
            "input_sha256": payload["_input_sha256"],
            "nonoptimal_series": nonoptimal,
            "complete_povm": povm,
        },
    )
    _write(
        check_path,
        {
            "schema_version": 1,
            "status": "executed",
            "scientific_coverage_awarded": False,
            "input_sha256": payload["_input_sha256"],
            "physical_povm_passed": povm["physical_povm_passed"],
            "cfi_bound_passed": povm["bound_passed"],
            "note": "Execution alone does not establish paper-exact provenance or independent review.",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
