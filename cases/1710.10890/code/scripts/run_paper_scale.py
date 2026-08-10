#!/usr/bin/env python3
"""Prepare, execute, resume, and finalize the paper-scale theory campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from quantum_droplets.paper_scale import (  # noqa: E402
    aggregate_campaign,
    load_campaign_config,
    make_smoke_config,
    prepare_campaign,
    run_tasks,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the code-ready paper-scale campaign for arXiv:1710.10890."
    )
    parser.add_argument(
        "--config",
        default="config/paper_scale_campaign.json",
        help="Workspace-relative campaign configuration.",
    )
    parser.add_argument(
        "--action",
        choices=["prepare", "run", "finalize", "smoke"],
        default="prepare",
        help="Default prepare validates and expands tasks without allocating a production grid.",
    )
    parser.add_argument(
        "--output-root",
        default="outputs",
        help="Workspace-relative or absolute output directory.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument(
        "--stop-after-real-steps",
        type=int,
        help="Testing/controlled-preemption hook; writes a resumable checkpoint.",
    )
    return parser


def _resolve(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else WORKSPACE / path


def main() -> int:
    args = _parser().parse_args()
    config = load_campaign_config(_resolve(args.config))
    output_root = _resolve(args.output_root)

    if args.action == "prepare":
        payload = prepare_campaign(config, output_root)
    elif args.action == "finalize":
        payload = aggregate_campaign(config, WORKSPACE, output_root)
    elif args.action == "smoke":
        smoke = make_smoke_config(config)
        run_summary = run_tasks(
            smoke,
            WORKSPACE,
            output_root,
            resume=args.resume,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            max_tasks=args.max_tasks,
            stop_after_real_steps=args.stop_after_real_steps,
        )
        payload = {
            "status": "smoke_partial" if run_summary["partial"] else "smoke_completed",
            "run": run_summary,
        }
        if not run_summary["partial"] and args.max_tasks is None and args.shard_count == 1:
            payload["finalize"] = aggregate_campaign(smoke, WORKSPACE, output_root)
    else:
        run_summary = run_tasks(
            config,
            WORKSPACE,
            output_root,
            resume=args.resume,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            max_tasks=args.max_tasks,
            stop_after_real_steps=args.stop_after_real_steps,
        )
        payload = {"status": "run_completed", "run": run_summary}
        if args.finalize:
            payload["finalize"] = aggregate_campaign(config, WORKSPACE, output_root)

    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
