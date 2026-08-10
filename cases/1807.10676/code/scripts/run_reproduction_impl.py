#!/usr/bin/env python3
"""Run every executable numerical target from the frozen paper contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from tbg_topology.reproduction import run_reproduction  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_exact.json")
    arguments = parser.parse_args()
    config = json.loads((WORKSPACE / arguments.config).read_text(encoding="utf-8"))
    result = run_reproduction(config, WORKSPACE)
    print(
        json.dumps(
            {
                "elapsed_seconds": result.elapsed_seconds,
                "formula_checks_passed": result.formula_checks["all_passed"],
                "convergence_status": result.convergence["status"],
                "targets_passed": result.target_checks["all_passed"],
            },
            indent=2,
        )
    )
    return 0 if result.target_checks["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
