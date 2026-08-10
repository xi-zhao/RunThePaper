#!/usr/bin/env python3
"""Run the paper-scale Figure 2(b,c) finite-MPS campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from scar_tdvp.fig2_tdmrg import load_config, run_campaign, work_units  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/fig2_tdmrg_paper_scale.json")
    parser.add_argument("--lanes", help="comma-separated lane ids")
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--stop-after-checkpoints", type=int, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    config_path = (WORKSPACE / arguments.config).resolve()
    if not config_path.is_relative_to(WORKSPACE.resolve()):
        parser.error("--config must stay within the workspace")
    config, digest = load_config(config_path, smoke=arguments.smoke)
    if arguments.validate_only:
        print(
            json.dumps(
                {
                    "status": "valid",
                    "run_id": config["run_id"],
                    "config_digest": digest,
                    "work_units": list(work_units(config)),
                },
                indent=2,
            )
        )
        return 0
    lanes = arguments.lanes.split(",") if arguments.lanes else None
    result = run_campaign(
        config,
        WORKSPACE,
        digest=digest,
        resume=arguments.resume,
        lanes=lanes,
        shard_index=arguments.shard_index,
        shard_count=arguments.shard_count,
        stop_after_checkpoints=arguments.stop_after_checkpoints,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
