#!/usr/bin/env python3
"""Validate, shard, resume, and aggregate the full N=100 campaign."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from tissue_rheology.campaign import (  # noqa: E402
    atomic_json,
    campaign_summary,
    condition_sample_every,
    condition_step_counts,
    config_digest,
    execute_condition,
    implementation_digest,
    load_condition_results,
    load_config,
    output_layout,
    plan_conditions,
    select_shard,
)
from tissue_rheology.rendering import render_all_targets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument(
        "--mode",
        choices=["validate", "run-shard", "run-all", "aggregate"],
        default="validate",
    )
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--confirm-paper-scale", action="store_true")
    return parser.parse_args()


def build_plan(config: dict, conditions: list) -> dict:
    total_steps = 0
    maximum_steps = 0
    rows = []
    for condition in conditions:
        warmup, sample = condition_step_counts(config, condition)
        steps = warmup + sample
        total_steps += steps
        maximum_steps = max(maximum_steps, steps)
        rows.append(
            {
                "condition_id": condition.condition_id,
                **condition.canonical_payload(),
                "group_ids": list(condition.group_ids),
                "target_ids": list(condition.target_ids),
                "warmup_steps": warmup,
                "sample_steps": sample,
                "sample_every_steps": condition_sample_every(config, condition),
            }
        )
    return {
        "schema_version": 1,
        "paper_id": "2211.15015",
        "profile": config["profile"],
        "conditions": rows,
        "condition_count": len(rows),
        "total_vertex_steps": total_steps
        * 2
        * int(config["model"]["nx"])
        * int(config["model"]["ny"]),
        "maximum_condition_steps": maximum_steps,
        "config_sha256": config_digest(config),
        "implementation_sha256": implementation_digest(WORKSPACE),
        "checkpoint_resume": True,
        "source_runner_access": "raw/ and references/ are forbidden by the external isolated run contract",
    }


def main() -> int:
    args = parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = load_config(config_path)
    if config["profile"] not in {"paper_scale", "paper_scale_smoke"}:
        raise ValueError(
            "paper-scale runner requires paper_scale or paper_scale_smoke profile"
        )
    layout = output_layout(WORKSPACE, config)
    conditions = plan_conditions(config)
    plan = build_plan(config, conditions)
    atomic_json(layout.checks_root / "plan.json", plan)
    if args.mode == "validate":
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if (
        config["profile"] == "paper_scale"
        and args.mode in {"run-shard", "run-all"}
        and not args.confirm_paper_scale
    ):
        raise SystemExit(
            "Refusing the multi-node campaign without --confirm-paper-scale"
        )

    if args.mode == "run-shard":
        selected = select_shard(
            conditions,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
        )
    elif args.mode == "run-all":
        selected = conditions
    else:
        selected = []

    started = time.perf_counter()
    records = []
    for index, condition in enumerate(selected, start=1):
        records.append(
            execute_condition(
                config,
                condition,
                workspace=WORKSPACE,
                output_root=layout.state_root,
                resume=args.resume,
            )
        )
        print(f"[{index}/{len(selected)}] {condition.condition_id} passed", flush=True)
    if selected:
        shard_record = {
            "schema_version": 1,
            "paper_id": "2211.15015",
            "profile": config["profile"],
            "shard_index": args.shard_index if args.mode == "run-shard" else 0,
            "shard_count": args.shard_count if args.mode == "run-shard" else 1,
            "condition_ids": [item.condition_id for item in selected],
            "records": len(records),
            "wall_time_seconds": time.perf_counter() - started,
            "status": "passed",
        }
        atomic_json(
            layout.checks_root
            / "shards"
            / f"shard_{shard_record['shard_index']:05d}_of_{shard_record['shard_count']:05d}.json",
            shard_record,
        )

    if args.mode in {"run-all", "aggregate"}:
        results = load_condition_results(
            WORKSPACE,
            layout.state_root,
            conditions,
            load_arrays=False,
        )
        if len(results) != len(conditions) and not args.allow_partial:
            raise SystemExit(
                f"Aggregation fails closed: {len(results)}/{len(conditions)} conditions complete"
            )
        if results:
            render_all_targets(
                results,
                workspace=WORKSPACE,
                data_root=layout.data_root,
                figures_root=layout.figures_root,
                checks_root=layout.checks_root,
                profile=config["profile"],
            )
        summary = campaign_summary(config, conditions, results)
        atomic_json(layout.checks_root / "campaign_summary.json", summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
