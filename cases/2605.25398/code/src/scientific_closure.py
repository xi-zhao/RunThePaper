"""Clean-room scientific closure for all seven numerical targets.

The runner consumes only a frozen parameter contract and the independently
derived random-matrix implementation.  It writes compact target-specific data
and falsifiable checks; paper figures and author numerical artifacts are never
inputs.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import wasserstein_distance

from boson_sampling_chaos import (
    CHAOTIC,
    DEFAULT_INPUT,
    INTEGRABLE,
    averaged_conditional_probability_curves,
    collision_free_pairs,
    conditional_two_photon_distribution,
    diagonalize_ensemble,
    ensemble_metrics,
    overlap_count,
    participation_ratio,
    unitary_from_eigendecomposition,
)


TARGET_IDS = ("T001", "T002", "T003", "T004", "T005", "T006", "T007")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _target_pair(dimension: int) -> tuple[int, int]:
    return (2, 5) if dimension >= 6 else (0, 2)


def _paper_ensemble(spec, dimension: int, count: int):
    return diagonalize_ensemble(spec, dimension=dimension, count=count)


def _metrics(spec, dimension: int, count: int, times: np.ndarray) -> list[dict[str, Any]]:
    return ensemble_metrics(
        _paper_ensemble(spec, dimension, count),
        times,
        input_pair=DEFAULT_INPUT,
        target_pair=_target_pair(dimension),
        retain_probabilities=False,
        retain_distribution_rows=False,
    )["metrics"]


def _mixed_time_grid(grid: dict[str, Any]) -> np.ndarray:
    parts: list[np.ndarray] = []
    if "linear_points" in grid:
        parts.append(
            np.linspace(
                float(grid["linear_min"]),
                float(grid["linear_max"]),
                int(grid["linear_points"]),
            )
        )
    if "log_points" in grid:
        parts.append(
            np.geomspace(
                float(grid["log_min"]),
                float(grid["log_max"]),
                int(grid["log_points"]),
            )
        )
    include = np.asarray(grid.get("include_times", []), dtype=float)
    if include.size:
        parts.append(include)
    if not parts:
        raise ValueError("time-grid contract must define linear, log, or included times")
    return np.unique(np.concatenate(parts))


def _select_rows(rows: list[dict[str, Any]], times: np.ndarray) -> list[dict[str, Any]]:
    by_time = {round(float(row["time"]), 12): row for row in rows}
    return [by_time[round(float(time), 12)] for time in times]


def _extrema_time_delta(first: dict[str, float], second: dict[str, float]) -> float:
    return max(
        abs(first[key] - second[key])
        for key in ("time_min_pt", "time_max_entropy", "time_min_sff", "time_max_pr")
    )


def _extrema(rows: list[dict[str, Any]], dimension: int) -> dict[str, float]:
    entropy_row = max(rows, key=lambda row: row["entropy_mean"])
    pt_row = min(rows, key=lambda row: row["pt_wasserstein"])
    sff_row = min(rows, key=lambda row: row["sff4_mean"])
    pr_row = max(rows, key=lambda row: row["participation_ratio_mean"])
    haar_entropy = -1.0 + sum(1.0 / i for i in range(1, math.comb(dimension, 2) + 1))
    return {
        "time_max_entropy": float(entropy_row["time"]),
        "time_min_pt": float(pt_row["time"]),
        "time_min_sff": float(sff_row["time"]),
        "time_max_pr": float(pr_row["time"]),
        "max_entropy": float(entropy_row["entropy_mean"]),
        "min_pt_wasserstein": float(pt_row["pt_wasserstein"]),
        "min_sff4": float(sff_row["sff4_mean"]),
        "max_participation_ratio": float(pr_row["participation_ratio_mean"]),
        "haar_entropy": float(haar_entropy),
        "entropy_gap_percent": float(100.0 * (haar_entropy - entropy_row["entropy_mean"]) / haar_entropy),
    }


def _t001(parameters: dict[str, Any]) -> dict[str, Any]:
    dimension = int(parameters["dimension"])
    cfg = parameters["T001"]
    observations: dict[str, Any] = {}
    for spec in (INTEGRABLE, CHAOTIC):
        samples = _paper_ensemble(spec, dimension, int(cfg["sample_count"]))
        result = ensemble_metrics(
            samples,
            np.asarray([cfg["time"]], dtype=float),
            input_pair=DEFAULT_INPUT,
            target_pair=_target_pair(dimension),
            retain_probabilities=False,
            retain_distribution_rows=False,
        )
        eigenvalues, eigenvectors = samples[0]
        probabilities, pairs = conditional_two_photon_distribution(
            unitary_from_eigendecomposition(eigenvalues, eigenvectors, float(cfg["time"])),
            input_pair=DEFAULT_INPUT,
        )
        observations[spec.label] = {
            "ensemble_mean": result["metrics"][0],
            "representative_probabilities": probabilities.tolist(),
            "output_pairs": [list(pair) for pair in pairs],
            "representative_probability_sum": float(probabilities.sum()),
            "representative_probability_min": float(probabilities.min()),
        }
    chaotic = observations[CHAOTIC.label]["ensemble_mean"]
    integrable = observations[INTEGRABLE.label]["ensemble_mean"]
    checks = {
        "normalized_nonnegative": all(
            abs(row["representative_probability_sum"] - 1.0) < 1e-12
            and row["representative_probability_min"] >= 0.0
            for row in observations.values()
        ),
        "chaotic_pr_exceeds_integrable": (
            chaotic["participation_ratio_mean"]
            >= float(cfg["minimum_pr_ratio"]) * integrable["participation_ratio_mean"]
        ),
        "chaotic_entropy_exceeds_integrable": (
            chaotic["entropy_mean"] - integrable["entropy_mean"]
            >= float(cfg["minimum_entropy_gap"])
        ),
    }
    return {"observations": observations, "checks": checks, "passed": all(checks.values())}


def _t002(parameters: dict[str, Any]) -> dict[str, Any]:
    dimension = int(parameters["dimension"])
    cfg = parameters["T002"]
    coarse_times = _mixed_time_grid(cfg["coarse_extrema_grid"])
    refined_times = _mixed_time_grid(cfg["refined_extrema_grid"])
    late_times = _mixed_time_grid(cfg["late_time_grid"])
    times = np.unique(np.concatenate([coarse_times, refined_times, late_times]))
    rows = _metrics(CHAOTIC, dimension, int(cfg["sample_count"]), times)
    coarse_extrema = _extrema(_select_rows(rows, coarse_times), dimension)
    refined_extrema = _extrema(_select_rows(rows, refined_times), dimension)
    extended_extrema = _extrema(rows, dimension)
    refinement_delta = _extrema_time_delta(coarse_extrema, refined_extrema)
    domain_delta = _extrema_time_delta(refined_extrema, extended_extrema)
    delta = max(
        abs(refined_extrema[key] - float(parameters["paper_t_star"]))
        for key in ("time_min_pt", "time_max_entropy", "time_min_sff")
    )
    late_rows = [row for row in rows if float(row["time"]) >= float(cfg["late_plateau_time_min"])]
    late_pt_mean = float(np.mean([row["pt_wasserstein"] for row in late_rows]))
    late_entropy_mean = float(np.mean([row["entropy_mean"] for row in late_rows]))
    late_sff_mean = float(np.mean([row["sff4_mean"] for row in late_rows]))
    pt_ratio = late_pt_mean / max(refined_extrema["min_pt_wasserstein"], 1e-15)
    sff_ratio = late_sff_mean / max(refined_extrema["min_sff4"], 1e-15)
    checks = {
        "paper_ideal_ensemble_count": int(cfg["sample_count"]) == int(cfg["published_ideal_sample_count"]),
        "finite_probe_triplet": all(
            np.isfinite(row[key])
            for row in rows
            for key in ("pt_wasserstein", "entropy_mean", "sff4_mean")
        ),
        "probe_times_near_t_star": delta <= float(cfg["maximum_t_star_delta"]),
        "extrema_stable_under_grid_refinement": refinement_delta <= float(cfg["maximum_refinement_shift"]),
        "extrema_stable_under_late_domain_extension": domain_delta <= float(cfg["maximum_domain_extension_shift"]),
        "late_plateau_distinct_from_dip": (
            pt_ratio >= float(cfg["minimum_late_pt_to_dip_ratio"])
            and sff_ratio >= float(cfg["minimum_late_sff_to_dip_ratio"])
            and late_entropy_mean < refined_extrema["max_entropy"]
        ),
    }
    return {
        "sample_count": int(cfg["sample_count"]),
        "published_ideal_sample_count": int(cfg["published_ideal_sample_count"]),
        "time_grids": {
            "coarse_extrema": coarse_times.tolist(),
            "refined_extrema": refined_times.tolist(),
            "late_time": late_times.tolist(),
        },
        "metrics": rows,
        "extrema": refined_extrema,
        "convergence": {
            "coarse_extrema": coarse_extrema,
            "refined_extrema": refined_extrema,
            "extended_domain_extrema": extended_extrema,
            "maximum_refinement_shift": refinement_delta,
            "maximum_domain_extension_shift": domain_delta,
        },
        "late_plateau": {
            "time_min": float(cfg["late_plateau_time_min"]),
            "pt_mean": late_pt_mean,
            "entropy_mean": late_entropy_mean,
            "sff4_mean": late_sff_mean,
            "pt_to_dip_ratio": pt_ratio,
            "sff_to_dip_ratio": sff_ratio,
        },
        "max_t_star_delta": delta,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _t003(parameters: dict[str, Any]) -> dict[str, Any]:
    dimension = int(parameters["dimension"])
    cfg = parameters["T003"]
    times = _mixed_time_grid(cfg["time_grid"])
    observations: dict[str, Any] = {}
    for spec in (INTEGRABLE, CHAOTIC):
        result = ensemble_metrics(
            _paper_ensemble(spec, dimension, int(cfg["sample_count"])),
            times,
            input_pair=DEFAULT_INPUT,
            target_pair=_target_pair(dimension),
            retain_probabilities=False,
            retain_distribution_rows=False,
        )
        observations[spec.label] = {
            "metrics": result["metrics"],
            "sector_rows": result["otoc_sector_rows"],
        }
    chaotic_t_star = min(observations[CHAOTIC.label]["metrics"], key=lambda row: abs(row["time"] - float(parameters["paper_t_star"])))
    integrable_t_star = min(observations[INTEGRABLE.label]["metrics"], key=lambda row: abs(row["time"] - float(parameters["paper_t_star"])))
    checks = {
        "paper_ideal_ensemble_count": int(cfg["sample_count"]) == int(cfg["published_ideal_sample_count"]),
        "finite_nonnegative_otocs": all(
            np.isfinite(row["probability_mean"]) and row["probability_mean"] >= 0.0
            for payload in observations.values()
            for row in payload["sector_rows"]
        ),
        "chaotic_pr_exceeds_integrable": (
            chaotic_t_star["participation_ratio_mean"]
            >= float(cfg["minimum_pr_ratio"]) * integrable_t_star["participation_ratio_mean"]
        ),
    }
    return {
        "sample_count": int(cfg["sample_count"]),
        "published_ideal_sample_count": int(cfg["published_ideal_sample_count"]),
        "times": times.tolist(),
        "observations": observations,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _t004(parameters: dict[str, Any]) -> dict[str, Any]:
    cfg = parameters["T004"]
    rng = np.random.default_rng(int(cfg["seed"]))
    n0 = int(cfg["n0"])
    count = int(cfg["draw_count"])
    rows: list[dict[str, Any]] = []
    for conditional_dimension in cfg["conditional_dimensions"]:
        d = int(conditional_dimension)
        draws = rng.exponential(1.0, size=(count, n0))
        values = draws[:, 0] / draws[:, :d].sum(axis=1)
        quantiles = (np.arange(count, dtype=float) + 0.5) / count
        pt_values = -np.log1p(-quantiles) / d
        rows.append({
            "D": d,
            "wasserstein_to_porter_thomas": float(wasserstein_distance(values, pt_values)),
            "mean_probability": float(np.mean(values)),
            "expected_mean": 1.0 / d,
        })
    by_d = {row["D"]: row for row in rows}
    checks = {
        "D28_close_to_porter_thomas": by_d[28]["wasserstein_to_porter_thomas"] <= float(cfg["maximum_D28_w1"]),
        "conditioning_improves_with_dimension": (
            by_d[28]["wasserstein_to_porter_thomas"]
            <= float(cfg["maximum_D28_to_D4_ratio"]) * by_d[4]["wasserstein_to_porter_thomas"]
        ),
    }
    return {"observations": rows, "checks": checks, "passed": all(checks.values())}


def _linear_slope(rows: list[dict[str, Any]], key: str) -> float:
    return float(np.polyfit([row["modes"] for row in rows], [row[key] for row in rows], 1)[0])


def _t005(parameters: dict[str, Any]) -> dict[str, Any]:
    cfg = parameters["T005"]
    chaotic_times = np.asarray(cfg["chaotic_times"], dtype=float)
    integrable_times = np.asarray(cfg["integrable_times"], dtype=float)
    rows: list[dict[str, Any]] = []
    for dimension_value in cfg["mode_counts"]:
        dimension = int(dimension_value)
        for spec, count, times in (
            (CHAOTIC, int(cfg["chaotic_sample_count"]), chaotic_times),
            (INTEGRABLE, int(cfg["integrable_sample_count"]), integrable_times),
        ):
            extrema = _extrema(_metrics(spec, dimension, count, times), dimension)
            rows.append({"modes": dimension, "ensemble": spec.label, "sample_count": count, **extrema})
    chaotic = sorted((row for row in rows if row["ensemble"] == CHAOTIC.label), key=lambda row: row["modes"])
    integrable = sorted((row for row in rows if row["ensemble"] == INTEGRABLE.label), key=lambda row: row["modes"])
    pt_reduction = 1.0 - chaotic[-1]["min_pt_wasserstein"] / chaotic[0]["min_pt_wasserstein"]
    entropy_gap_drop = chaotic[0]["entropy_gap_percent"] - chaotic[-1]["entropy_gap_percent"]
    integrable_spread = max(
        max(row[key] for key in ("time_min_pt", "time_max_entropy", "time_min_sff", "time_max_pr"))
        - min(row[key] for key in ("time_min_pt", "time_max_entropy", "time_min_sff", "time_max_pr"))
        for row in integrable
    )
    checks = {
        "full_even_paper_mode_grid": (
            [row["modes"] for row in chaotic]
            == [int(value) for value in cfg["published_mode_counts"]]
            == list(range(4, 23, 2))
        ),
        "paper_M22_preserved": chaotic[-1]["modes"] == 22 and integrable[-1]["modes"] == 22,
        "paper_entropy_ensemble_count": all(
            row["sample_count"] == int(cfg["published_chaotic_sample_count"])
            for row in chaotic
        ),
        "chaotic_min_pt_improves_with_scale": (
            pt_reduction >= float(cfg["minimum_pt_endpoint_reduction"])
            and _linear_slope(chaotic, "min_pt_wasserstein") < 0.0
        ),
        "chaotic_entropy_gap_shrinks_with_scale": (
            entropy_gap_drop >= float(cfg["minimum_entropy_gap_drop_percent_points"])
            and _linear_slope(chaotic, "entropy_gap_percent") < 0.0
        ),
        "integrable_probe_times_do_not_collapse": integrable_spread >= float(cfg["minimum_integrable_time_spread"]),
    }
    return {
        "observations": rows,
        "pt_endpoint_reduction": pt_reduction,
        "entropy_gap_drop_percent_points": entropy_gap_drop,
        "integrable_max_within_mode_time_spread": integrable_spread,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _t006(parameters: dict[str, Any]) -> dict[str, Any]:
    dimension = int(parameters["dimension"])
    cfg = parameters["T006"]
    times = _mixed_time_grid(cfg["time_grid"])
    pairs = collision_free_pairs(dimension)
    observations: dict[str, Any] = {}
    for spec in (INTEGRABLE, CHAOTIC):
        samples = _paper_ensemble(spec, dimension, int(cfg["sample_count"]))
        curve_values, curve_pairs = averaged_conditional_probability_curves(
            samples,
            times,
            input_pair=DEFAULT_INPUT,
        )
        curves = {
            f"{pair[0]}-{pair[1]}": {
                "overlap": overlap_count(pair, DEFAULT_INPUT),
                "is_initial_configuration": pair == DEFAULT_INPUT,
                "values": curve_values[curve_pairs.index(pair)].tolist(),
            }
            for pair in pairs
        }
        observations[spec.label] = curves
    initial_key = f"{DEFAULT_INPUT[0]}-{DEFAULT_INPUT[1]}"
    checks = {
        "paper_ideal_ensemble_count": int(cfg["sample_count"]) == int(cfg["published_ideal_sample_count"]),
        "all_collision_free_configurations_present": all(
            len(curves) == math.comb(dimension, 2)
            for curves in observations.values()
        ),
        "initial_configuration_present": all(
            initial_key in curves and curves[initial_key]["is_initial_configuration"]
            for curves in observations.values()
        ),
        "conditional_probability_sum_at_every_time": all(
            np.allclose(
                np.sum([curve["values"] for curve in curves.values()], axis=0),
                1.0,
                atol=1e-12,
            )
            for curves in observations.values()
        ),
        "all_curves_finite_nonnegative": all(
            np.all(np.isfinite(curve["values"])) and np.all(np.asarray(curve["values"]) >= 0.0)
            for curves in observations.values()
            for curve in curves.values()
        ),
        "all_overlap_sectors_present": all(
            {curve["overlap"] for curve in curves.values()} == {0, 1, 2}
            for curves in observations.values()
        ),
    }
    return {
        "sample_count": int(cfg["sample_count"]),
        "published_ideal_sample_count": int(cfg["published_ideal_sample_count"]),
        "input_configuration_source_trace": cfg["input_configuration_source_trace"],
        "times": times.tolist(),
        "observations": observations,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _fft_pr_from_series(series: np.ndarray) -> float:
    centered = series / max(float(np.mean(series)), 1e-15) - 1.0
    power = np.abs(np.fft.rfft(centered)) ** 2
    power = power[1:]
    weights = power / max(float(power.sum()), 1e-15)
    return participation_ratio(weights)


def _t007(parameters: dict[str, Any]) -> dict[str, Any]:
    dimension = int(parameters["dimension"])
    cfg = parameters["T007"]
    short_times = np.asarray(cfg["short_times"], dtype=float)
    fft_times = np.linspace(float(cfg["fft_time_min"]), float(cfg["fft_time_max"]), int(cfg["fft_points"]))
    pairs = [pair for pair in collision_free_pairs(dimension) if pair != DEFAULT_INPUT]
    samples_by_spec = {
        spec.label: _paper_ensemble(spec, dimension, int(cfg["sample_count"]))
        for spec in (INTEGRABLE, CHAOTIC)
    }
    short_curves, short_pairs = averaged_conditional_probability_curves(
        samples_by_spec[CHAOTIC.label],
        short_times,
        input_pair=DEFAULT_INPUT,
    )
    slopes: dict[str, float] = {}
    for overlap in (0, 1):
        values = [
            short_curves[short_pairs.index(pair)]
            for pair in pairs
            if overlap_count(pair, DEFAULT_INPUT) == overlap
        ]
        mean_values = np.mean(values, axis=0)
        slopes[str(overlap)] = float(np.polyfit(np.log(short_times), np.log(mean_values), 1)[0])
    fft_curves = {
        label: averaged_conditional_probability_curves(samples, fft_times, input_pair=DEFAULT_INPUT)
        for label, samples in samples_by_spec.items()
    }
    fft_rows = []
    for pair in pairs:
        fft_rows.append({
            "output_pair": list(pair),
            "overlap": overlap_count(pair, DEFAULT_INPUT),
            "chaotic_fft_pr": _fft_pr_from_series(
                fft_curves[CHAOTIC.label][0][fft_curves[CHAOTIC.label][1].index(pair)]
            ),
            "integrable_fft_pr": _fft_pr_from_series(
                fft_curves[INTEGRABLE.label][0][fft_curves[INTEGRABLE.label][1].index(pair)]
            ),
        })
    win_fraction = float(np.mean([row["chaotic_fft_pr"] > row["integrable_fft_pr"] for row in fft_rows]))
    checks = {
        "overlap_one_t_squared": float(cfg["overlap_one_slope_range"][0]) <= slopes["1"] <= float(cfg["overlap_one_slope_range"][1]),
        "overlap_zero_t_fourth": float(cfg["overlap_zero_slope_range"][0]) <= slopes["0"] <= float(cfg["overlap_zero_slope_range"][1]),
        "chaotic_fft_more_delocalized": win_fraction >= float(cfg["minimum_pairwise_fft_win_fraction"]),
    }
    return {"short_time_slopes": slopes, "fft_rows": fft_rows, "pairwise_fft_win_fraction": win_fraction, "checks": checks, "passed": all(checks.values())}


RUNNERS = {
    "T001": _t001,
    "T002": _t002,
    "T003": _t003,
    "T004": _t004,
    "T005": _t005,
    "T006": _t006,
    "T007": _t007,
}


def run_scientific_closure(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["scientific_parameters"]
    if tuple(parameters["target_ids"]) != TARGET_IDS:
        raise ValueError("scientific target denominator must be T001..T007")
    boundary = parameters.get("clean_room_boundary", {})
    forbidden_flags = (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    )
    if any(boundary.get(flag) is not False for flag in forbidden_flags):
        raise ValueError("clean-room boundary must forbid every source-derived numerical input")

    checks: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        result = RUNNERS[target_id](parameters)
        result.update({
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "generated_data_provenance": "independent_numerics",
            "clean_room_boundary": boundary,
        })
        data_path = output_root / "data" / "scientific_closure" / f"{target_id}.json"
        check_path = output_root / "checks" / "scientific_closure" / f"{target_id}.json"
        _write_json(data_path, result)
        check = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "status": "passed" if result["passed"] else "failed",
            "checks": result["checks"],
            "data_ref": f"outputs/data/scientific_closure/{target_id}.json",
        }
        _write_json(check_path, check)
        checks.append(check)

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if all(row["status"] == "passed" for row in checks) else "failed",
        "target_ids": list(TARGET_IDS),
        "clean_room_boundary": boundary,
        "target_checks": checks,
    }
    _write_json(output_root / "checks" / "scientific_closure" / "manifest.json", manifest)
    return manifest
