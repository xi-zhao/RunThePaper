#!/usr/bin/env python3
"""Validate or run the author-array reanalysis contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from lnoi_interference.campaign import atomic_json  # noqa: E402
from lnoi_interference.experimental import (  # noqa: E402
    inspect_inputs,
    reanalyse_available_inputs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    input_root = WORKSPACE / config["input_root"]
    checks = WORKSPACE / "outputs" / "checks" / "paper_scale"
    inventory = inspect_inputs(input_root)
    atomic_json(checks / "input_inventory.json", inventory)
    plan = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": inventory["status"],
        "target_items": config["target_items"],
        "synthetic_data_allowed": False,
        "source_image_digitization_allowed": False,
    }
    atomic_json(checks / "plan.json", plan)
    if args.validate_only:
        print(json.dumps(plan, indent=2))
        return 0
    result = reanalyse_available_inputs(input_root)
    atomic_json(checks / "reanalysis.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
