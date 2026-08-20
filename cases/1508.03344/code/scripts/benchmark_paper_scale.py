#!/usr/bin/env python3
"""Measure a real L=12 work unit and project the disclosed paper-scale floor."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import platform
import resource
import sys
import time

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from driven_ising.campaign import (  # noqa: E402
    build_work_units,
    execute_unit,
    load_config,
    validate_config,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_scale.json")
    parser.add_argument("--output", default="outputs/checks/performance_profile.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    config = load_config(config_path)
    validation = validate_config(config)
    if validation["status"] != "passed":
        raise RuntimeError(validation["findings"])
    candidate = next(
        unit
        for unit in build_work_units(config)
        if unit.family == "fig2_level" and unit.parameters["system_size"] == 12
    )
    benchmark_unit = replace(
        candidate,
        unit_id=f"{candidate.unit_id}-benchmark-one-sample",
        sample_count=1,
    )
    started = time.perf_counter()
    result = execute_unit(benchmark_unit, backend="numpy")
    duration = time.perf_counter() - started
    total_realizations = int(validation["sample_realizations"])
    serial_floor_seconds = duration * total_realizations
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mib = peak_rss / (1024.0**2 if sys.platform == "darwin" else 1024.0)
    payload = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "1508.03344",
        "benchmark": {
            "family": benchmark_unit.family,
            "system_size": benchmark_unit.parameters["system_size"],
            "sample_count": 1,
            "backend": "numpy",
            "duration_seconds": duration,
            "max_unitary_residual": result["max_unitary_residual"],
            "peak_rss_mib": peak_rss_mib,
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
        "paper_scale": {
            "work_units": int(validation["work_units"]),
            "sample_realizations": total_realizations,
            "serial_cpu_lower_bound_seconds": serial_floor_seconds,
            "serial_cpu_lower_bound_days": serial_floor_seconds / 86400.0,
            "interpretation": "Lower bound only: Fig. 1 eigenvector susceptibility and Fig. 2 spectral units are more expensive than this level-statistics sample.",
            "recommended_execution": "512-way resumable A100 scheduler array followed by fail-closed aggregation",
            "a100_speedup_claim": "not measured; no unsupported speedup is assumed",
        },
    }
    output = (WORKSPACE / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
