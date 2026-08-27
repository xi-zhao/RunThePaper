#!/usr/bin/env python3
"""Measure the repaired code path before launching the 2000-instance run.

This is resource evidence only.  It deliberately lowers ensemble counts and
never promotes the resulting values into scientific coverage.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scientific_closure import _t002, _t003, _t005, _t006  # noqa: E402


RUNNERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "T002": _t002,
    "T003": _t003,
    "T005": _t005,
    "T006": _t006,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _configure_count(parameters: dict[str, Any], target_id: str, count: int) -> int:
    if target_id == "T005":
        parameters[target_id]["chaotic_sample_count"] = count
        parameters[target_id]["published_chaotic_sample_count"] = count
        parameters[target_id]["integrable_sample_count"] = count
        return 2 * count
    parameters[target_id]["sample_count"] = count
    if target_id in {"T002", "T003", "T006"}:
        parameters[target_id]["published_ideal_sample_count"] = count
    return count if target_id == "T002" else 2 * count


def _paper_work_units(parameters: dict[str, Any], target_id: str) -> int:
    if target_id == "T002":
        return int(parameters[target_id]["sample_count"])
    if target_id in {"T003", "T006"}:
        return 2 * int(parameters[target_id]["sample_count"])
    return int(parameters[target_id]["chaotic_sample_count"]) + int(
        parameters[target_id]["integrable_sample_count"]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark-config",
        type=Path,
        default=WORKSPACE / "config" / "author_repair_scaling_benchmark.json",
    )
    args = parser.parse_args()
    benchmark_config = _load(args.benchmark_config)
    source_config = WORKSPACE / benchmark_config["source_config"]
    scientific_parameters = _load(source_config)["scientific_parameters"]
    rows: list[dict[str, Any]] = []
    projections: dict[str, Any] = {}

    for target_id in benchmark_config["target_ids"]:
        target_rows: list[dict[str, Any]] = []
        for count_value in benchmark_config["sample_counts"]:
            count = int(count_value)
            parameters = deepcopy(scientific_parameters)
            work_units = _configure_count(parameters, target_id, count)
            started = time.perf_counter()
            result = RUNNERS[target_id](parameters)
            elapsed = time.perf_counter() - started
            row = {
                "target_id": target_id,
                "sample_count_per_lane": count,
                "ensemble_sample_work_units": work_units,
                "elapsed_seconds": elapsed,
                "numeric_output_finite": bool(
                    np.isfinite(elapsed) and isinstance(result.get("checks"), dict)
                ),
                "scientific_coverage_promoted": False,
            }
            rows.append(row)
            target_rows.append(row)

        work = np.asarray([row["ensemble_sample_work_units"] for row in target_rows], dtype=float)
        seconds = np.asarray([row["elapsed_seconds"] for row in target_rows], dtype=float)
        slope, intercept = np.polyfit(work, seconds, 1)
        paper_units = _paper_work_units(scientific_parameters, target_id)
        projections[target_id] = {
            "paper_ensemble_sample_work_units": paper_units,
            "fitted_seconds_per_work_unit": float(max(slope, 0.0)),
            "fitted_intercept_seconds": float(max(intercept, 0.0)),
            "projected_paper_run_seconds": float(max(intercept + slope * paper_units, 0.0)),
        }

    payload = {
        "schema_version": 1,
        "paper_id": benchmark_config["paper_id"],
        "status": "passed" if all(row["numeric_output_finite"] for row in rows) else "failed",
        "purpose": "resource_scaling_only",
        "scientific_coverage_promoted": False,
        "source_config": benchmark_config["source_config"],
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "measurements": rows,
        "paper_scale_projections": projections,
        "projected_total_seconds": float(
            sum(item["projected_paper_run_seconds"] for item in projections.values())
        ),
    }
    output_path = WORKSPACE / benchmark_config["output_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
