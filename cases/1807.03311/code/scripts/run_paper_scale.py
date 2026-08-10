#!/usr/bin/env python3
"""Plan, execute, resume, and aggregate the high-resolution continuum run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from twisted_tmd.paper_scale import (  # noqa: E402
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
    shard.add_argument("--workers", type=int, default=1)
    shard.add_argument("--no-resume", action="store_true")
    run_all = commands.add_parser("run-all")
    run_all.add_argument("--config", required=True)
    run_all.add_argument("--workers", type=int, default=1)
    run_all.add_argument("--no-resume", action="store_true")
    return parser


def main() -> None:
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
            workers=arguments.workers,
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
            workers=arguments.workers,
            resume=not arguments.no_resume,
        )
        result = {"run": run, "aggregate": aggregate_campaign(config, output_root)}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
