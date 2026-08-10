"""Scientific claim assessment for a completed paper-scale campaign.

This module may identify a stable discrepancy, but it deliberately cannot label
the paper wrong.  A paper-error candidate is a later lifecycle state requiring
convergence, independent falsification, and fresh-context review in the Harness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .paper_scale import TARGET_IDS, _atomic_json


def _records(output_root: Path, target_id: str) -> list[dict[str, Any]]:
    aggregate = output_root / "aggregates" / f"{target_id}.npz"
    with np.load(aggregate, allow_pickle=False) as payload:
        detail = json.loads(str(payload["condition_manifest_json"].item()))
        return [
            {
                "condition_id": item["condition_id"],
                "parameters": item["parameters"],
                "trajectories": item["trajectories"],
                "mean": np.asarray(payload[item["mean_key"]], dtype=float),
                "stderr": np.asarray(payload[item["stderr_key"]], dtype=float),
            }
            for item in detail
        ]


def _result(
    target_id: str,
    passed: bool,
    metrics: dict[str, Any],
    tests: list[str],
) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "status": "supported" if passed else "inconclusive",
        "paper_error_candidate": False,
        "metrics": metrics,
        "falsification_tests": tests,
        "next_action": (
            "retain as support with declared unpublished sampling choices"
            if passed
            else "test sampling and finite-size convergence, run an independent method, then request fresh-context review"
        ),
    }


def _assess_transition(
    records: list[dict[str, Any]], parameters: dict[str, Any], threshold: float
) -> dict[str, Any]:
    table = {
        (int(row["parameters"]["L"]), float(row["parameters"]["rate"])): float(row["mean"][0])
        for row in records
    }
    sizes = sorted({key[0] for key in table if key[0] >= 64})
    rates = sorted({key[1] for key in table})
    if len(sizes) < 3:
        return _result("T001", False, {"reason": "fewer than three large sizes"}, ["large-size crossing"])

    def crossing(selected: list[int]) -> float:
        variance = [np.var([table[(length, rate)] for length in selected]) for rate in rates]
        return float(rates[int(np.argmin(variance))])

    estimate = crossing(sizes[-3:])
    two_size = crossing(sizes[-2:])
    paper = float(parameters["critical_rate_main"])
    error = abs(estimate - paper)
    drift = abs(estimate - two_size)
    passed = error <= threshold and drift <= threshold
    return _result(
        "T001",
        passed,
        {
            "estimated_pc_largest_three": estimate,
            "estimated_pc_largest_two": two_size,
            "paper_pc": paper,
            "absolute_error": error,
            "finite_size_drift": drift,
        },
        ["largest-three crossing", "largest-two crossing", "probability bounds"],
    )


def _causal_fraction(record: dict[str, Any]) -> float:
    heatmap = record["mean"]
    duration, length = heatmap.shape
    displacement = np.arange(-length // 2, length // 2)
    time = np.arange(1, duration + 1)
    causal = np.abs(displacement)[None, :] <= time[:, None]
    total = float(heatmap.sum())
    return float(heatmap[causal].sum() / total) if total else 0.0


def _assess_lightcone(
    target_id: str, records: list[dict[str, Any]], threshold: float
) -> dict[str, Any]:
    fractions = {row["condition_id"]: _causal_fraction(row) for row in records}
    passed = bool(fractions) and min(fractions.values()) >= threshold
    return _result(
        target_id,
        passed,
        {"causal_weight_fractions": fractions, "minimum_required": threshold},
        ["one-site-per-layer causal mask", "nonzero purification weight"],
    )


def _assess_partial_record(records: list[dict[str, Any]], tolerance: float) -> dict[str, Any]:
    curves = {
        (float(row["parameters"]["rate"]), row["parameters"]["cutoff"]): row["mean"]
        for row in records
    }
    rates = sorted({key[0] for key in curves})
    order_fractions: dict[str, float] = {}
    bounded = True
    for rate in rates:
        c10, c20, full = curves[(rate, 10)], curves[(rate, 20)], curves[(rate, None)]
        ordered = (c10 + tolerance >= c20) & (c20 + tolerance >= full)
        order_fractions[str(rate)] = float(np.mean(ordered))
        bounded = bounded and all(
            np.all((curve >= -tolerance) & (curve <= 1.0 + tolerance))
            for curve in (c10, c20, full)
        )
    low, high = rates[0], rates[-1]
    phase_order = float(curves[(low, None)][-1]) > float(curves[(high, None)][-1])
    passed = bounded and phase_order and min(order_fractions.values()) >= 0.95
    return _result(
        "T003",
        passed,
        {
            "record_monotonicity_fraction": order_fractions,
            "low_rate_full_final": float(curves[(low, None)][-1]),
            "high_rate_full_final": float(curves[(high, None)][-1]),
            "probability_bounds_passed": bounded,
            "conditioning_model": "exact_mixed_stabilizer_partial_record",
        },
        [
            "data-processing order under larger retained records",
            "full-record volume/area phase order",
            "mixed-stabilizer probability bounds",
        ],
    )


def _fit_surface(records: list[dict[str, Any]], pc: float, gap: float) -> float:
    largest = max(int(row["parameters"]["L"]) for row in records)
    selected = sorted(
        (
            float(row["parameters"]["rate"]),
            float(row["mean"][0]),
        )
        for row in records
        if int(row["parameters"]["L"]) == largest
        and float(row["parameters"]["rate"]) < pc - gap
        and float(row["mean"][0]) > 0.0
    )
    x = np.log([pc - rate for rate, _ in selected])
    y = np.log([value for _, value in selected])
    return float(np.polyfit(x, y, 1)[0])


def _assess_surface(
    records: list[dict[str, Any]], parameters: dict[str, Any], threshold: float
) -> dict[str, Any]:
    pc = float(parameters["critical_rate_correlations"])
    fit_wide = _fit_surface(records, pc, 0.005)
    fit_narrow = _fit_surface(records, pc, 0.010)
    paper = float(parameters["beta_surface"])
    error = abs(fit_wide - paper)
    drift = abs(fit_wide - fit_narrow)
    passed = error <= threshold and drift <= threshold
    return _result(
        "T004",
        passed,
        {
            "beta_fit_gap_0.005": fit_wide,
            "beta_fit_gap_0.010": fit_narrow,
            "paper_beta": paper,
            "absolute_error": error,
            "fit_window_drift": drift,
        },
        ["two fit windows", "largest published size", "probability bounds"],
    )


def _collapse_cv(rows: list[dict[str, Any]], branch: str) -> float:
    selected = [row for row in rows if row["parameters"]["branch"] == branch]
    grid = np.linspace(0.0, 8.0, 129)
    scaled: list[np.ndarray] = []
    for row in selected:
        length = int(row["parameters"]["L"])
        local_time = np.arange(len(row["mean"])) / length
        interpolated = np.interp(grid, local_time, row["mean"])
        scaled.append(interpolated * length ** float(row["parameters"]["exponent"]))
    values = np.asarray(scaled)
    mean = np.mean(values, axis=0)
    mask = (grid >= 1.0) & (np.abs(mean) > 1.0e-8)
    return float(np.mean(np.std(values[:, mask], axis=0) / np.abs(mean[mask])))


def _assess_correlations(
    target_id: str,
    records: list[dict[str, Any]],
    branches: tuple[str, str],
    threshold: float,
) -> dict[str, Any]:
    cvs = {branch: _collapse_cv(records, branch) for branch in branches}
    nonnegative = all(np.all(row["mean"] >= -1.0e-12) for row in records)
    passed = nonnegative and max(cvs.values()) <= threshold
    return _result(
        target_id,
        passed,
        {"relative_collapse_cv": cvs, "nonnegative": nonnegative, "maximum_allowed": threshold},
        ["published exponent collapse", "raw mutual-information positivity"],
    )


def _fit_purification(records: list[dict[str, Any]], references: int, min_size: int) -> float:
    x_values: list[float] = []
    y_values: list[float] = []
    for row in records:
        length = int(row["parameters"]["L"])
        if int(row["parameters"]["references"]) != references or length < min_size:
            continue
        upper = max(4, length // 2)
        time = np.arange(2, upper + 1)
        values = row["mean"][time]
        mask = values > 0.0
        x_values.extend(np.log(time[mask]).tolist())
        y_values.extend(np.log(values[mask]).tolist())
    return float(-2.0 * np.polyfit(x_values, y_values, 1)[0])


def _assess_purification(
    records: list[dict[str, Any]], parameters: dict[str, Any], threshold: float
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    passed = True
    for references, name in ((1, "one"), (4, "four")):
        all_sizes = _fit_purification(records, references, 16)
        large_sizes = _fit_purification(records, references, 64)
        paper = float(parameters[f"supp_eta_{name}"])
        error = abs(large_sizes - paper)
        drift = abs(all_sizes - large_sizes)
        metrics[name] = {
            "fit_all_sizes": all_sizes,
            "fit_L_ge_64": large_sizes,
            "paper_eta": paper,
            "absolute_error": error,
            "finite_size_drift": drift,
        }
        passed = passed and error <= threshold and drift <= threshold
    return _result(
        "T008",
        passed,
        metrics,
        ["all-size fit", "large-size fit", "one/four-reference comparison"],
    )


def assess_campaign(
    output_root: Path,
    config: dict[str, Any],
    acceptance: dict[str, Any],
) -> dict[str, Any]:
    output_root = output_root.resolve()
    rows = {target_id: _records(output_root, target_id) for target_id in TARGET_IDS}
    thresholds = acceptance["thresholds"]
    parameters = config["parameters"]
    results = [
        _assess_transition(rows["T001"], parameters, thresholds["critical_rate_absolute_error"]),
        _assess_lightcone("T002", rows["T002"], thresholds["lightcone_causal_weight_fraction"]),
        _assess_partial_record(rows["T003"], thresholds["probability_tolerance"]),
        _assess_surface(rows["T004"], parameters, thresholds["surface_exponent_absolute_error"]),
        _assess_correlations(
            "T005", rows["T005"], ("surface", "bulk"), thresholds["correlation_collapse_relative_cv"]
        ),
        _assess_correlations(
            "T006", rows["T006"], ("end_to_end", "mixed"), thresholds["correlation_collapse_relative_cv"]
        ),
        _assess_lightcone("T007", rows["T007"], thresholds["lightcone_causal_weight_fraction"]),
        _assess_purification(rows["T008"], parameters, thresholds["purification_exponent_absolute_error"]),
    ]
    supported = all(item["status"] == "supported" for item in results)
    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if supported else "requires_scientific_review",
        "paper_assessment": "supported" if supported else "inconclusive",
        "paper_error_candidate": False,
        "targets": results,
        "review_boundary": {
            "automatic_paper_error_label": False,
            "fresh_context_review_required_for_paper_error_candidate": True,
            "stable_mismatch_must_not_be_fit_away": True,
            "required_candidate_evidence": config["review_policy"]["paper_error_candidate_requires"],
        },
    }
    _atomic_json(output_root / "checks" / "scientific_assessment.json", payload)
    return payload
