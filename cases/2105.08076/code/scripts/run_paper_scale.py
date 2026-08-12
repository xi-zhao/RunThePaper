#!/usr/bin/env python3
"""Validate, shard, resume, or aggregate the paper-scale campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dark_state_fermions.paper_scale import (  # noqa: E402
    aggregate,
    run_all,
    run_shard,
    write_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_scale.json")
    parser.add_argument(
        "--mode",
        choices=("validate", "run-shard", "aggregate", "run-all"),
        default="validate",
    )
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "torch_cpu", "torch_cuda"),
        default="auto",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside the case workspace")

    if args.mode == "validate":
        path = write_plan(config_path, WORKSPACE)
        result: dict[str, object] = {"plan": path.relative_to(WORKSPACE).as_posix()}
    elif args.mode == "run-shard":
        if args.shard_index is None:
            parser.error("--shard-index is required for run-shard")
        result = run_shard(
            config_path,
            WORKSPACE,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            backend=args.backend,
            resume=args.resume,
        )
    elif args.mode == "aggregate":
        result = aggregate(config_path, WORKSPACE)
    else:
        result = run_all(
            config_path, WORKSPACE, backend=args.backend, resume=args.resume
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
