#!/usr/bin/env python3
"""Case-local entrypoint for the blind numerical reproduction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from bose_fermi_transport.reproduction import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/feature.json")
    args = parser.parse_args()
    config = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config.parents:
        raise ValueError("config must remain inside workspace")
    result = run(config, WORKSPACE)
    print(
        json.dumps(
            {
                "all_assertions_passed": result["checks"]["all_assertions_passed"],
                "outputs": len(result["manifest"]["outputs"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
