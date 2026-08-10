#!/usr/bin/env python3
"""Run or inspect the restartable high-resolution moire campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from moire_hubbard.paper_scale import (  # noqa: E402
    aggregate_campaign,
    load_config,
    plan_campaign,
    run_shard,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "aggregate"):
        command = subparsers.add_parser(name)
        command.add_argument("--config", required=True)
    shard = subparsers.add_parser("run-shard")
    shard.add_argument("--config", required=True)
    shard.add_argument("--shard-index", type=int, required=True)
    shard.add_argument("--shard-count", type=int, required=True)
    shard.add_argument("--workers", type=int, default=1)
    shard.add_argument("--no-resume", action="store_true")
    all_command = subparsers.add_parser("run-all")
    all_command.add_argument("--config", required=True)
    all_command.add_argument("--workers", type=int, default=1)
    all_command.add_argument("--no-resume", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    config = load_config(WORKSPACE / args.config)
    output_root = WORKSPACE / config["output_root"]
    if args.command == "plan":
        result = plan_campaign(config, output_root, write=True)
    elif args.command == "run-shard":
        result = run_shard(
            config,
            output_root,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            workers=args.workers,
            resume=not args.no_resume,
        )
    elif args.command == "aggregate":
        result = aggregate_campaign(config, output_root)
    else:
        plan_campaign(config, output_root, write=True)
        shard_result = run_shard(
            config,
            output_root,
            shard_index=0,
            shard_count=1,
            workers=args.workers,
            resume=not args.no_resume,
        )
        result = {
            "run": shard_result,
            "aggregate": aggregate_campaign(config, output_root),
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
