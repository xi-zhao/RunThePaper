#!/usr/bin/env python3
"""Validate or execute the fail-closed experimental reanalysis channel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from axion_spin.paper_scale import (
    MissingInputsError,
    build_plan,
    execute_paper_scale,
    load_paper_scale_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = load_paper_scale_config(config_path)
    plan = build_plan(config, workspace=WORKSPACE)
    if args.validate_only:
        print(json.dumps(plan, indent=2))
        return 0
    try:
        acceptance = execute_paper_scale(
            config, workspace=WORKSPACE, resume=args.resume
        )
    except MissingInputsError as error:
        print(
            json.dumps(
                {"status": "blocked_missing_inputs", "missing": error.missing}, indent=2
            )
        )
        return 2
    print(json.dumps(acceptance, indent=2))
    return 0 if acceptance["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
