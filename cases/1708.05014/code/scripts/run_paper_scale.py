#!/usr/bin/env python3
"""CLI entrypoint for the resumable 1708.05014 paper-scale campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from boundary_time_crystal.paper_scale import (  # noqa: E402
    FAMILY_TARGETS,
    aggregate_campaign,
    load_paper_scale_config,
    plan_jobs,
    run_campaign,
)


def _family_set(raw: str | None) -> set[str] | None:
    if raw is None:
        return None
    values = {value.strip() for value in raw.split(",") if value.strip()}
    unknown = values - set(FAMILY_TARGETS)
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown families: {sorted(unknown)}")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run, resume, shard, and aggregate paper-scale BTC numerics."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument(
        "--families",
        help="Comma-separated family subset; omit for the complete 24-target plan.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse hash-valid jobs and continue time-block checkpoints.",
    )
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Aggregate after this shard; all configured jobs must already be complete.",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Do not run jobs; require all shards and build frozen target outputs.",
    )
    parser.add_argument(
        "--list-jobs",
        action="store_true",
        help="Validate the config and print the deterministic job plan without writes.",
    )
    arguments = parser.parse_args()

    config_path = arguments.config.resolve()
    families = _family_set(arguments.families)
    if arguments.list_jobs:
        config = load_paper_scale_config(config_path)
        jobs = plan_jobs(config)
        print(
            json.dumps(
                {
                    "paper_id": config["paper_id"],
                    "run_id": config["run_id"],
                    "profile": config["profile"],
                    "jobs": [
                        {
                            "job_id": job.job_id,
                            "family": job.family,
                            "target_ids": list(job.target_ids),
                            "parameters": job.parameters,
                        }
                        for job in jobs
                    ],
                },
                indent=2,
            )
        )
        return

    if arguments.aggregate_only:
        if families is not None:
            parser.error("--families is not valid with --aggregate-only")
        result = aggregate_campaign(config_path)
        print(
            json.dumps(
                {
                    "status": result["acceptance"]["status"],
                    "targets_passed": result["acceptance"]["summary"]["targets_passed"],
                }
            )
        )
        return

    summary = run_campaign(
        config_path,
        shard_index=arguments.shard_index,
        shard_count=arguments.shard_count,
        families=families,
        resume=arguments.resume,
    )
    result: dict[str, object] = {"run": summary}
    if arguments.aggregate:
        result["aggregate"] = aggregate_campaign(config_path)["acceptance"]["summary"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
