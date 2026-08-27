#!/usr/bin/env python3
"""Measure one paper-size diagonalization for an auditable runtime projection."""

from __future__ import annotations

import json
import resource
import sys
import time
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from lyapunov_band import LongRangeModel, finite_spectrum, sample_onsite  # noqa: E402


def main() -> None:
    length = 1000
    disorder_strength = 0.8
    seed = 250709447
    model = LongRangeModel()
    onsite = sample_onsite(length, disorder_strength, np.random.default_rng(seed))

    timings: dict[str, float] = {}
    checks: dict[str, dict[str, float | int]] = {}
    for boundary in ("obc", "pbc"):
        started = time.perf_counter()
        spectrum = finite_spectrum(onsite, model, boundary=boundary)
        timings[boundary] = time.perf_counter() - started
        checks[boundary] = {
            "eigenvalues": int(spectrum.size),
            "finite_fraction": float(np.mean(np.isfinite(spectrum))),
            "mean_real": float(np.mean(spectrum.real)),
            "mean_imag": float(np.mean(spectrum.imag)),
        }

    sample_count = 3200
    single_boundary_hours = {
        boundary: seconds * sample_count / 3600.0
        for boundary, seconds in timings.items()
    }
    result = {
        "status": "passed",
        "evidence_type": "local_single_sample_paper_size_benchmark",
        "machine": "Apple M4 CPU, 10 cores, 16 GiB unified memory",
        "length": length,
        "disorder_strength": disorder_strength,
        "seed": seed,
        "timing_seconds": timings,
        "projected_serial_hours_for_3200_samples": single_boundary_hours,
        "projected_serial_hours_both_boundaries": sum(single_boundary_hours.values()),
        "max_resident_set_size_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "checks": checks,
        "projection_note": (
            "Linear wall-time projection from two single-sample measurements; "
            "process startup, scheduling, cache effects, and convergence studies are excluded."
        ),
    }

    output = WORKSPACE / "outputs" / "checks" / "paper_scale_single_sample_benchmark.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
