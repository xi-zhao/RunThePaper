#!/usr/bin/env python3
"""Run or validate a deterministic exact-diagonalization campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from mbl_level_stats.campaign import (  # noqa: E402
    aggregate,
    load_config,
    run_shard,
    validate_plan,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--config", required=True)
    result.add_argument("--output-root", default="outputs")
    result.add_argument("--shard-index", type=int, default=0)
    result.add_argument("--shard-count", type=int)
    result.add_argument("--resume", action="store_true")
    result.add_argument("--validate-only", action="store_true")
    result.add_argument("--aggregate-only", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    output_root = (WORKSPACE / args.output_root).resolve()
    config = load_config(config_path)
    shard_count = args.shard_count or int(config["execution"]["default_shards"])
    if args.validate_only:
        print(json.dumps(validate_plan(config, shard_count=shard_count), indent=2))
        return 0
    if args.aggregate_only:
        summary = aggregate(config, config_path=config_path, output_root=output_root, shard_count=shard_count)
        print(json.dumps(summary, indent=2))
        return 0 if summary["status"] == "passed" else 2
    state = run_shard(
        config,
        config_path=config_path,
        output_root=output_root,
        shard_index=args.shard_index,
        shard_count=shard_count,
        resume=args.resume,
    )
    if shard_count == 1:
        summary = aggregate(config, config_path=config_path, output_root=output_root, shard_count=1)
        print(json.dumps(summary, indent=2))
        return 0 if summary["status"] == "passed" else 2
    print(
        json.dumps(
            {
                "status": state["status"],
                "shard_index": args.shard_index,
                "shard_count": shard_count,
                "next_step": "run every shard, then invoke --aggregate-only",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
