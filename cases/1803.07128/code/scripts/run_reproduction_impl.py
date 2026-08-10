#!/usr/bin/env python3
"""CLI for the isolated numerical reproduction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from qml_feature_space.reproduction import run_reproduction  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_exact.json")
    arguments = parser.parse_args()
    config = json.loads((WORKSPACE / arguments.config).read_text(encoding="utf-8"))
    result = run_reproduction(config, WORKSPACE)
    print(json.dumps({key: value for key, value in result.items() if key != "target_checks"}, indent=2))
    return 0 if result["formula_checks_passed"] and result["target_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
