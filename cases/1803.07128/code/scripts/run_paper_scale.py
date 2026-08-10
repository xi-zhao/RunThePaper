#!/usr/bin/env python3
"""Plan, execute, resume, or aggregate the Fig. 8 convergence campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from qml_feature_space.paper_scale import (  # noqa: E402
    aggregate_campaign,
    load_config,
    plan_campaign,
    run_shard,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "aggregate"):
        command = commands.add_parser(name)
        command.add_argument("--config", required=True)
    shard = commands.add_parser("run-shard")
    shard.add_argument("--config", required=True)
    shard.add_argument("--shard-index", type=int, required=True)
    shard.add_argument("--shard-count", type=int, required=True)
    shard.add_argument("--no-resume", action="store_true")
    all_command = commands.add_parser("run-all")
    all_command.add_argument("--config", required=True)
    all_command.add_argument("--no-resume", action="store_true")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    config = load_config(WORKSPACE / arguments.config)
    output_root = WORKSPACE / config["output_root"]
    if arguments.command == "plan":
        result = plan_campaign(config, output_root, write=True)
    elif arguments.command == "run-shard":
        result = run_shard(
            config,
            output_root,
            shard_index=arguments.shard_index,
            shard_count=arguments.shard_count,
            resume=not arguments.no_resume,
        )
    elif arguments.command == "aggregate":
        result = aggregate_campaign(config, output_root)
    else:
        plan_campaign(config, output_root, write=True)
        run = run_shard(
            config,
            output_root,
            shard_index=0,
            shard_count=1,
            resume=not arguments.no_resume,
        )
        result = {"run": run, "aggregate": aggregate_campaign(config, output_root)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
