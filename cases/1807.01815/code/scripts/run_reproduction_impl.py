#!/usr/bin/env python3
"""Run the isolated numerical generator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from scar_tdvp.reproduction import run_reproduction  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/reduced_scale.json")
    arguments = parser.parse_args()
    config = json.loads((WORKSPACE / arguments.config).read_text(encoding="utf-8"))
    result = run_reproduction(config, WORKSPACE)
    print(json.dumps(result, indent=2))
    return 0 if result["formula_checks_passed"] and result["all_non_discrepant_targets_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
