#!/usr/bin/env python3
"""Run all 17 formula-derived targets without reading paper figures or raw inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from atom_ion_feshbach.reproduction import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/feature.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside the case workspace")
    result = run(config_path, WORKSPACE)
    print(
        json.dumps(
            {
                "all_assertions_passed": result["checks"]["all_assertions_passed"],
                "passed": result["checks"]["summary"]["passed"],
                "targets": result["checks"]["summary"]["targets"],
                "outputs": len(result["manifest"]["outputs"]),
                "paper_error_candidate_emitted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
