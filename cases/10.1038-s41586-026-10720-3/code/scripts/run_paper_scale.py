#!/usr/bin/env python3
"""Execute the sharded formula-only Nature-paper campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from optical_hawking.paper_scale_campaign import (  # noqa: E402
    aggregate,
    build_plan,
    canonical_json,
    implementation_digest,
    run_unit,
    sha256_bytes,
    shard_for,
    smoke_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument("--profile", choices=("paper", "smoke"), default="smoke")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--unit-id")
    parser.add_argument("--device", default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.shard_count <= 0 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("invalid shard index/count")
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = json.loads(config_path.read_text())
    config_digest = sha256_bytes(canonical_json(config))
    code_digest = implementation_digest(WORKSPACE)
    full_plan = build_plan(config, args.profile)
    plan = smoke_plan(full_plan) if args.profile == "smoke" else full_plan
    output_root = WORKSPACE / "outputs" / "data" / "paper_scale" / args.profile
    output_root.mkdir(parents=True, exist_ok=True)
    plan_payload = {
        "schema_version": 1,
        "profile": args.profile,
        "config_sha256": config_digest,
        "implementation_sha256": code_digest,
        "units": plan,
    }
    (output_root / "plan.json").write_text(
        json.dumps(plan_payload, indent=2, ensure_ascii=False) + "\n"
    )

    selected = plan
    if args.unit_id:
        selected = [unit for unit in selected if unit["unit_id"] == args.unit_id]
        if not selected:
            raise SystemExit(f"unknown unit id for profile: {args.unit_id}")
    selected = [
        unit
        for unit in selected
        if shard_for(unit, args.shard_count) == args.shard_index
    ]
    results = []
    if not args.aggregate_only:
        for unit in selected:
            results.append(
                run_unit(
                    WORKSPACE,
                    config,
                    args.profile,
                    unit,
                    output_root,
                    config_digest,
                    code_digest,
                    args.device,
                    args.resume,
                )
            )
    acceptance = aggregate(
        WORKSPACE,
        config,
        args.profile,
        plan,
        output_root,
        config_digest,
        code_digest,
    )
    print(json.dumps({"results": results, "acceptance": acceptance}, indent=2))


if __name__ == "__main__":
    main()
