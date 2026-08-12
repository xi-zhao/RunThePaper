#!/usr/bin/env python3
"""Run the independent seven-target main-text feature campaign."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from axion_spin.campaign import (
    atomic_json,
    build_manifest,
    config_digest,
    implementation_digest,
    load_config,
    run_feature,
)
from axion_spin.rendering import render_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/feature.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = load_config(config_path)
    checks_root = WORKSPACE / "outputs" / "checks" / str(config["output_slug"])
    plan = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "target_ids": config["target_ids"],
        "config_path": config_path.relative_to(WORKSPACE).as_posix(),
        "config_sha256": config_digest(config),
        "implementation_sha256": implementation_digest(WORKSPACE),
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }
    atomic_json(checks_root / "plan.json", plan)
    started = time.perf_counter()
    results = run_feature(config, workspace=WORKSPACE)
    figures = render_all(results)
    summary = dict(results["summary"])
    summary["wall_time_seconds"] = time.perf_counter() - started
    summary["figure_count"] = len(figures)
    atomic_json(checks_root / "campaign_summary.json", summary)
    manifest = build_manifest(WORKSPACE, slug=str(config["output_slug"]), config=config)
    print(json.dumps({"summary": summary, "manifest": manifest}, indent=2))
    return 0 if results["target_checks"]["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
