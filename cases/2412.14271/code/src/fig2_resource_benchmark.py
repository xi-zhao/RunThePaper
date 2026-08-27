"""Measured feasibility audit for the paper-scale Fig. 2 sparse ED path."""

from __future__ import annotations

import json
import resource
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .dicke import one_photon_steady_state_ed


Solver = Callable[..., dict[str, object]]


def _rss_bytes() -> int:
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return raw if sys.platform == "darwin" else raw * 1024


def fit_power_law(
    cutoffs: list[int], values: list[float]
) -> dict[str, float]:
    if len(cutoffs) < 2 or len(cutoffs) != len(values):
        raise ValueError("at least two matched positive measurements are required")
    x = np.log(np.asarray(cutoffs, dtype=float))
    y = np.log(np.asarray(values, dtype=float))
    if np.any(~np.isfinite(y)) or np.any(np.asarray(values) <= 0):
        raise ValueError("measurements must be finite and positive")
    exponent, log_prefactor = np.polyfit(x, y, 1)
    fitted = log_prefactor + exponent * x
    residual = float(np.sum((y - fitted) ** 2))
    total = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 if total == 0.0 else 1.0 - residual / total
    return {
        "exponent": float(exponent),
        "prefactor": float(np.exp(log_prefactor)),
        "r_squared": r_squared,
    }


def project_power_law(model: dict[str, float], cutoff: int) -> float:
    return float(model["prefactor"] * float(cutoff) ** model["exponent"])


def run_benchmark(
    config: dict[str, Any],
    *,
    solver: Solver = one_photon_steady_state_ed,
) -> dict[str, Any]:
    if config.get("paper_id") != "2412.14271":
        raise ValueError("paper_id must be 2412.14271")
    if config.get("target_id") != "T001":
        raise ValueError("resource benchmark must remain scoped to T001")
    boundary = config.get("clean_room_boundary")
    if not isinstance(boundary, dict) or any(boundary.values()):
        raise ValueError("the numerical benchmark may not read author artifacts")

    params = config["parameters"]
    pilot_cutoffs = [int(value) for value in params["pilot_cutoffs"]]
    paper_cutoffs = [int(value) for value in params["paper_cutoffs"]]
    if pilot_cutoffs != sorted(set(pilot_cutoffs)):
        raise ValueError("pilot_cutoffs must be unique and increasing")
    if not set(pilot_cutoffs).intersection(paper_cutoffs):
        raise ValueError("at least one paper cutoff must be measured directly")

    tolerance = params["acceptance_tolerances"]
    measurements: list[dict[str, Any]] = []
    for cutoff in pilot_cutoffs:
        started = time.monotonic()
        result = solver(
            int(params["system_size"]),
            cutoff,
            float(params["coupling"]),
            omega_c=float(params["omega_c"]),
            omega_a=float(params["omega_a"]),
            kappa1=float(params["kappa1"]),
        )
        elapsed = time.monotonic() - started
        passed = (
            float(result["trace_error"]) <= float(tolerance["trace_error"])
            and float(result["hermiticity_error"])
            <= float(tolerance["hermiticity_error"])
            and float(result["minimum_density_eigenvalue"])
            >= -float(tolerance["positivity"])
            and float(result["liouvillian_residual"])
            <= float(tolerance["liouvillian_residual"])
        )
        measurements.append(
            {
                "cutoff": cutoff,
                "runtime_seconds": elapsed,
                "process_peak_rss_bytes": _rss_bytes(),
                "hilbert_dimension": int(result["hilbert_dimension"]),
                "liouvillian_dimension": int(result["liouvillian_dimension"]),
                "liouvillian_nnz": int(result["liouvillian_nnz"]),
                "liouvillian_residual": float(result["liouvillian_residual"]),
                "trace_error": float(result["trace_error"]),
                "hermiticity_error": float(result["hermiticity_error"]),
                "minimum_density_eigenvalue": float(
                    result["minimum_density_eigenvalue"]
                ),
                "photon_tail": float(result["photon_tail"]),
                "science_invariants_passed": passed,
            }
        )

    memory_model = fit_power_law(
        pilot_cutoffs,
        [float(row["process_peak_rss_bytes"]) for row in measurements],
    )
    runtime_model = fit_power_law(
        pilot_cutoffs,
        [float(row["runtime_seconds"]) for row in measurements],
    )
    safe_memory_bytes = int(
        int(config["host_memory_bytes"])
        * float(config["usable_memory_fraction"])
    )
    observed = {int(row["cutoff"]): row for row in measurements}
    projections = []
    for cutoff in paper_cutoffs:
        projected_memory = project_power_law(memory_model, cutoff)
        projected_runtime = project_power_law(runtime_model, cutoff)
        if cutoff in observed:
            decision = "measured_runnable"
            projected_memory = float(observed[cutoff]["process_peak_rss_bytes"])
            projected_runtime = float(observed[cutoff]["runtime_seconds"])
        elif projected_memory <= safe_memory_bytes:
            decision = "projected_within_safe_envelope"
        else:
            decision = "projected_outside_safe_memory_envelope"
        projections.append(
            {
                "cutoff": cutoff,
                "decision": decision,
                "memory_bytes": projected_memory,
                "runtime_seconds": projected_runtime,
                "memory_fraction_of_physical": projected_memory
                / int(config["host_memory_bytes"]),
            }
        )

    invariants_passed = all(
        bool(row["science_invariants_passed"]) for row in measurements
    )
    blocked_cutoffs = [
        row["cutoff"]
        for row in projections
        if row["decision"] == "projected_outside_safe_memory_envelope"
    ]
    return {
        "schema_version": 1,
        "paper_id": "2412.14271",
        "target_id": "T001",
        "status": "passed" if invariants_passed else "failed",
        "benchmark_kind": "measured_sparse_lu_resource_scaling",
        "host_memory_bytes": int(config["host_memory_bytes"]),
        "usable_memory_fraction": float(config["usable_memory_fraction"]),
        "safe_memory_bytes": safe_memory_bytes,
        "measurements": measurements,
        "models": {"memory": memory_model, "runtime": runtime_model},
        "paper_cutoff_projections": projections,
        "measured_paper_cutoffs": sorted(set(pilot_cutoffs) & set(paper_cutoffs)),
        "blocked_paper_cutoffs": blocked_cutoffs,
        "paper_scale_complete": False,
        "resource_boundary_confirmed": bool(blocked_cutoffs),
        "code_fault_excluded": invariants_passed,
        "clean_room_boundary": boundary,
    }


def write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
