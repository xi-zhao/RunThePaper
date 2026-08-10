#!/usr/bin/env python3
"""Plan, run, resume, aggregate, and assess the paper-scale campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from measurement_criticality.assessment import assess_campaign  # noqa: E402
from measurement_criticality.paper_scale import load_campaign  # noqa: E402


def _path(value: Path) -> Path:
    return value if value.is_absolute() else WORKSPACE / value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "validate-config",
            "plan",
            "run-shard",
            "run-condition",
            "run-all",
            "aggregate-target",
            "aggregate-all",
            "assess",
        ),
    )
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument(
        "--acceptance", type=Path, default=Path("config/paper_scale_acceptance.json")
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--condition")
    parser.add_argument("--target", choices=tuple(f"T{index:03d}" for index in range(1, 9)))
    parser.add_argument("--shard", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    config_path = _path(arguments.config)
    output_root = _path(arguments.output_root) if arguments.output_root else None
    campaign = load_campaign(config_path, output_root=output_root, smoke=arguments.smoke)
    resume = not arguments.no_resume

    if arguments.action == "validate-config":
        result = {
            "status": "passed",
            "paper_id": campaign.config["paper_id"],
            "mode": "smoke" if campaign.smoke else "paper_scale",
            "config_sha256": campaign.config_hash,
            "conditions": len(campaign.conditions),
            "shards": sum(condition.shards for condition in campaign.conditions),
            "targets": sorted({condition.target_id for condition in campaign.conditions}),
        }
    elif arguments.action == "plan":
        result = campaign.plan()
    elif arguments.action == "run-shard":
        if arguments.condition is None or arguments.shard is None:
            raise SystemExit("run-shard requires --condition and --shard")
        result = campaign.run_shard(arguments.condition, arguments.shard, resume=resume)
    elif arguments.action == "run-condition":
        if arguments.condition is None:
            raise SystemExit("run-condition requires --condition")
        result = campaign.run_condition(arguments.condition, resume=resume)
    elif arguments.action == "run-all":
        run = campaign.run_all(resume=resume, workers=arguments.workers)
        aggregate = campaign.aggregate_all()
        result = {"run": run, "aggregate": aggregate}
        if not campaign.smoke:
            acceptance = json.loads(_path(arguments.acceptance).read_text(encoding="utf-8"))
            result["scientific_assessment"] = assess_campaign(
                campaign.output_root, campaign.config, acceptance
            )
    elif arguments.action == "aggregate-target":
        if arguments.target is None:
            raise SystemExit("aggregate-target requires --target")
        result = campaign.aggregate_target(arguments.target)
    elif arguments.action == "aggregate-all":
        result = campaign.aggregate_all()
    else:
        if campaign.smoke:
            raise SystemExit("paper claims cannot be assessed from smoke data")
        acceptance = json.loads(_path(arguments.acceptance).read_text(encoding="utf-8"))
        result = assess_campaign(campaign.output_root, campaign.config, acceptance)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
