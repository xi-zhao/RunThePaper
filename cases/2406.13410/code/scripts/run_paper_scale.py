#!/usr/bin/env python3
"""Plan, execute, resume, and aggregate the A100-capable campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from atom_ion_feshbach.paper_scale import (  # noqa: E402
    aggregate,
    build_plan,
    run_shard,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_scale.json")
    parser.add_argument(
        "--mode",
        choices=["validate", "run-shard", "aggregate", "run-all"],
        default="validate",
    )
    parser.add_argument("--shard-id", type=int)
    parser.add_argument("--backend", choices=["auto", "numpy", "cuda"], default="auto")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside workspace")
    plan = build_plan(config_path, WORKSPACE)
    result: object = plan
    if args.mode == "run-shard":
        if args.shard_id is None:
            parser.error("--shard-id is required for run-shard")
        result = run_shard(
            config_path,
            WORKSPACE,
            shard_id=args.shard_id,
            backend=args.backend,
            resume=args.resume,
        )
    elif args.mode == "aggregate":
        result = aggregate(config_path, WORKSPACE)["manifest"]
    elif args.mode == "run-all":
        records = [
            run_shard(
                config_path,
                WORKSPACE,
                shard_id=shard_id,
                backend=args.backend,
                resume=args.resume,
            )
            for shard_id in range(int(plan["shards"]))
        ]
        result = {
            "shards": records,
            "campaign": aggregate(config_path, WORKSPACE)["manifest"],
        }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
