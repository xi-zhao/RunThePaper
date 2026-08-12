#!/usr/bin/env python3
"""Run the independent 18-target feature campaign."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from lnoi_interference.campaign import (  # noqa: E402
    atomic_json,
    build_manifest,
    canonical_json,
    implementation_digest,
    load_config,
    run_feature,
    sha256_bytes,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/feature.json"))
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    config = load_config(config_path)
    checks = WORKSPACE / "outputs" / "checks" / "feature"
    plan = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "target_ids": config["target_ids"],
        "config_path": config_path.relative_to(WORKSPACE).as_posix(),
        "config_sha256": sha256_bytes(canonical_json(config).encode()),
        "implementation_sha256": implementation_digest(WORKSPACE),
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "raw_directory_read_by_runner": False,
    }
    atomic_json(checks / "plan.json", plan)
    started = time.perf_counter()
    results = run_feature(config, WORKSPACE)
    manifest = build_manifest(WORKSPACE, config)
    summary = dict(results["summary"])
    summary.update(
        {
            "wall_time_seconds": time.perf_counter() - started,
            "figure_count": 0,
            "rendering_lane": "separate_post_freeze_contract",
            "manifest_files": len(manifest["files"]),
        }
    )
    atomic_json(checks / "campaign_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if results["target_checks"]["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
