#!/usr/bin/env python3
"""Run the reduced direct-model feature campaign for all 17 targets."""

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
    condition_step_counts,
    config_digest,
    execute_condition,
    implementation_digest,
    load_condition_results,
    load_config,
    output_layout,
    plan_conditions,
    sha256_file,
)
from tissue_rheology.rendering import render_all_targets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/feature.json"))
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = load_config(config_path)
    if config["profile"] != "feature":
        raise ValueError("run_reproduction.py only accepts the feature profile")
    layout = output_layout(WORKSPACE, config)
    conditions = plan_conditions(config)
    plan = {
        "schema_version": 1,
        "paper_id": "2211.15015",
        "profile": config["profile"],
        "config_path": config_path.relative_to(WORKSPACE).as_posix(),
        "config_sha256": config_digest(config),
        "implementation_sha256": implementation_digest(WORKSPACE),
        "conditions": [
            {
                "condition_id": item.condition_id,
                **item.canonical_payload(),
                "group_ids": list(item.group_ids),
                "target_ids": list(item.target_ids),
                "warmup_steps": condition_step_counts(config, item)[0],
                "sample_steps": condition_step_counts(config, item)[1],
            }
            for item in conditions
        ],
    }
    atomic_json(layout.checks_root / "plan.json", plan)

    started = time.perf_counter()
    records = []
    for index, condition in enumerate(conditions, start=1):
        record = execute_condition(
            config,
            condition,
            workspace=WORKSPACE,
            output_root=layout.state_root,
            resume=args.resume,
        )
        records.append(record)
        print(
            f"[{index}/{len(conditions)}] {condition.condition_id} passed", flush=True
        )
    results = load_condition_results(WORKSPACE, layout.state_root, conditions)
    target_checks = render_all_targets(
        results,
        workspace=WORKSPACE,
        data_root=layout.data_root,
        figures_root=layout.figures_root,
        checks_root=layout.checks_root,
        profile=config["profile"],
        target_selectors=config["target_selectors"],
    )
    summary = campaign_summary(config, conditions, results)
    summary["wall_time_seconds"] = time.perf_counter() - started
    summary["target_check_status"] = target_checks["status"]
    atomic_json(layout.checks_root / "campaign_summary.json", summary)

    artifacts = []
    roots = [layout.data_root, layout.figures_root, layout.checks_root]
    seen: set[Path] = set()
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path in seen:
                continue
            seen.add(path)
            if (
                not path.is_file()
                or "checkpoints" in path.parts
                or "chunks" in path.parts
            ):
                continue
            artifacts.append(
                {
                    "path": path.relative_to(WORKSPACE).as_posix(),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    manifest = {
        "schema_version": 1,
        "paper_id": "2211.15015",
        "profile": config["profile"],
        "config_sha256": config_digest(config),
        "implementation_sha256": implementation_digest(WORKSPACE),
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "artifacts": artifacts,
        "status": "passed",
    }
    atomic_json(layout.checks_root / "generated_data_manifest.json", manifest)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
