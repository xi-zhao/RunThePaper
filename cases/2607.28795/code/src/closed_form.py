"""Closed-form targets from Appendices E and I."""

from __future__ import annotations

from typing import Any


def magic_injection_counts(group_order: int, repetition_distance: int) -> dict[str, int]:
    """Evaluate Eq. (E15)."""

    if group_order <= 0 or repetition_distance <= 0:
        raise ValueError("group order and repetition distance must be positive")
    qubits = (2 * repetition_distance**2 + 2 * repetition_distance + 5) * group_order
    checks = (repetition_distance**2 + repetition_distance + 2) * group_order
    return {
        "qubits": qubits,
        "x_checks": checks,
        "z_checks": checks,
        "logical_qubits": qubits - 2 * checks,
    }

def realtime_decoder_metrics(
    stages: list[dict[str, Any]],
    cycle_seconds: float,
) -> dict[str, Any]:
    """Evaluate Eq. (I1) and the mean reaction time from rounded table inputs."""

    if cycle_seconds <= 0:
        raise ValueError("cycle_seconds must be positive")
    rows: list[dict[str, Any]] = []
    mean_latency = 0.0
    for stage in stages:
        fraction = float(stage["fraction"])
        time_seconds = float(stage["time_seconds"])
        contribution = fraction * time_seconds
        mean_latency += contribution
        rows.append(
            {
                "stage": str(stage["stage"]),
                "fraction": fraction,
                "time_seconds": time_seconds,
                "latency_contribution_seconds": contribution,
                "utilization": contribution / cycle_seconds,
            }
        )
    return {
        "stages": rows,
        "mean_latency_seconds": mean_latency,
        "mean_latency_cycles": mean_latency / cycle_seconds,
        "all_mean_stage_utilizations_below_one": all(row["utilization"] < 1 for row in rows),
    }
