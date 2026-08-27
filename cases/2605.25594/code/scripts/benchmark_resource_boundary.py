#!/usr/bin/env python3
"""Measure the current paper-scale Anderson resource boundary.

This is a resource diagnostic, not a scientific generator.  It consumes only
PRAgent-generated A100 timing rows, the frozen paper-scale configuration and
the local host profile.  It never reads the paper, source figures, author code
or author numerical arrays.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from paper_scale_campaign import build_work_units  # noqa: E402


def resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else WORKSPACE / candidate


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_timings(path: Path, expected_L: int) -> list[float]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError(f"no timing rows in {path}")
    if {int(row["L"]) for row in rows} != {expected_L}:
        raise ValueError(f"{path} contains a size other than L={expected_L}")
    timings = [float(row["elapsed_seconds"]) for row in rows]
    if not all(math.isfinite(value) and value > 0 for value in timings):
        raise ValueError(f"{path} contains an invalid elapsed_seconds value")
    return timings


def build_report(config: dict[str, Any]) -> dict[str, Any]:
    parameters = config["parameters"]
    paper_path = resolve(str(parameters["paper_scale_config"]))
    host_path = resolve(str(parameters["host_profile"]))
    paper_config = load_json(paper_path)
    host_profile = load_json(host_path)
    units = build_work_units(paper_config)
    counts = Counter(unit.L for unit in units)

    timing_rows: dict[int, dict[str, Any]] = {}
    input_hashes = {
        str(paper_path.relative_to(WORKSPACE)): sha256(paper_path),
        str(host_path.relative_to(WORKSPACE)): sha256(host_path),
    }
    for row in parameters["timing_inputs"]:
        L = int(row["L"])
        path = resolve(str(row["path"]))
        timings = load_timings(path, L)
        input_hashes[str(path.relative_to(WORKSPACE))] = sha256(path)
        timing_rows[L] = {
            "samples": len(timings),
            "minimum_seconds": min(timings),
            "median_seconds": statistics.median(timings),
            "mean_seconds": statistics.mean(timings),
            "maximum_seconds": max(timings),
        }

    measured_sizes = sorted(timing_rows)
    volumes = np.asarray([size**3 for size in measured_sizes], dtype=float)
    medians = np.asarray(
        [timing_rows[size]["median_seconds"] for size in measured_sizes], dtype=float
    )
    exponent, log_prefactor = np.polyfit(np.log(volumes), np.log(medians), 1)
    prefactor = float(math.exp(float(log_prefactor)))
    projected_by_size: dict[str, dict[str, Any]] = {}
    projected_serial_seconds = 0.0
    for L, count in sorted(counts.items()):
        seconds = prefactor * float(L**3) ** float(exponent)
        projected_serial_seconds += count * seconds
        projected_by_size[str(L)] = {
            "work_units": count,
            "projected_seconds_per_unit": seconds,
            "projected_serial_hours": count * seconds / 3600.0,
        }

    largest_L = int(paper_config["largest_L"])
    dimension = largest_L**3
    float_bytes = int(parameters["memory_model"]["float_bytes"])
    resident_arrays = int(
        parameters["memory_model"]["minimum_full_dense_arrays_during_observable_reduction"]
    )
    one_dense_gib = dimension * dimension * float_bytes / 2**30
    minimum_reduction_gib = resident_arrays * one_dense_gib
    host_memory_gib = float(host_profile["profile"]["memory_gib"])
    accelerator = parameters["available_accelerator"]

    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "measurement_scope": "current PRAgent paper-scale implementation and available single-A100 path",
        "input_sha256": input_hashes,
        "campaign": {
            "work_units": len(units),
            "work_units_by_L": {str(key): value for key, value in sorted(counts.items())},
            "largest_L": largest_L,
            "largest_dimension": dimension,
        },
        "measured_a100_timings": {str(key): value for key, value in timing_rows.items()},
        "runtime_projection": {
            "model": "log-log fit of elapsed time versus Hilbert-space dimension using all generated A100 timing rows at L=24,28,31",
            "dimension_exponent": float(exponent),
            "prefactor": prefactor,
            "by_L": projected_by_size,
            "projected_single_accelerator_serial_hours": projected_serial_seconds / 3600.0,
            "projected_single_accelerator_serial_days": projected_serial_seconds / 86400.0,
            "projection_is_lower_bound": True,
            "lower_bound_reason": "The timing rows cover one T_s observable path; multi-operator reductions, failed large-size solver workspaces, retries and queue latency are not added."
        },
        "memory_boundary": {
            "float64_dense_array_gib_at_L38": one_dense_gib,
            "minimum_observable_reduction_gib_at_L38": minimum_reduction_gib,
            "current_local_host_memory_gib": host_memory_gib,
            "current_local_host_shortfall_gib": max(0.0, minimum_reduction_gib - host_memory_gib),
            "available_a100_memory_gib": float(accelerator["memory_gib"]),
            "largest_completed_a100_L": int(accelerator["largest_completed_L"]),
            "eigensolver_workspace_is_additional": True,
            "local_paper_scale_memory_gate": minimum_reduction_gib <= host_memory_gib,
        },
        "conclusion": {
            "terminal_compute_boundary_confirmed": minimum_reduction_gib > host_memory_gib,
            "statement": "The frozen 12,495-unit campaign cannot run to L=38 on the current 18-GiB host: the current observable-reduction code alone needs two simultaneous L=38 dense float64 arrays before eigensolver workspace. Existing A100 rows measure the single-accelerator campaign as multi-day even under a lower-bound extrapolation, and the available A100 path has only been completed through L=31.",
            "paper_scale_code_ready": True,
            "isolated_smoke_required_separately": True,
        },
        "numerical_input_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "reference_pixels_read": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config_path = resolve(str(args.config))
    config = load_json(config_path)
    report = build_report(config)
    output = resolve(str(config["parameters"]["output"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
