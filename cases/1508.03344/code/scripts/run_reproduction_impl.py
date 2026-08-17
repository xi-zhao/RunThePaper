#!/usr/bin/env python3
"""Run, resume, validate or aggregate the clean-room campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from driven_ising.campaign import (  # noqa: E402
    aggregate_units,
    load_config,
    run_units,
    validate_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output_root = (
        args.output_root
        if args.output_root.is_absolute()
        else WORKSPACE / args.output_root
    )
    if args.validate_only:
        result = validate_config(load_config(config_path))
    elif args.aggregate_only:
        result = aggregate_units(WORKSPACE, config_path, output_root)
    else:
        run_result = run_units(
            WORKSPACE,
            config_path,
            output_root,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            resume=args.resume,
        )
        if args.shard_index is None:
            aggregate_result = aggregate_units(WORKSPACE, config_path, output_root)
            result = {"run": run_result, "aggregate": aggregate_result}
        else:
            result = run_result
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if _status(result) == "passed" else 1


def _status(result: dict[str, object]) -> str:
    aggregate = result.get("aggregate")
    if isinstance(aggregate, dict):
        return str(aggregate.get("status", "failed"))
    return str(result.get("status", "failed"))


if __name__ == "__main__":
    raise SystemExit(main())
