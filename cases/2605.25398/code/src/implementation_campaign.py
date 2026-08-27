"""Clean-room implementation attestation for the uncovered numerical targets.

The campaign exercises the existing formula-derived random-matrix model at a
small, frozen scale.  It does not read the paper, source figures, author code,
or author arrays, and a passing result does not promote scientific coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from boson_sampling_chaos import (
    CHAOTIC,
    INTEGRABLE,
    averaged_otoc_series,
    conditional_two_photon_distribution,
    diagonalize_ensemble,
    ensemble_metrics,
    participation_ratio,
    unitary_from_eigendecomposition,
)


TARGET_IDS = ("T001", "T002", "T003", "T006", "T007")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _samples(params: dict[str, Any], *, chaotic: bool):
    spec = CHAOTIC if chaotic else INTEGRABLE
    return diagonalize_ensemble(
        spec,
        dimension=int(params["dimension"]),
        count=int(params["sample_count"]),
    )


def _distribution_validation(params: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for spec in (INTEGRABLE, CHAOTIC):
        samples = diagonalize_ensemble(
            spec,
            dimension=int(params["dimension"]),
            count=int(params["sample_count"]),
        )
        eigenvalues, eigenvectors = samples[0]
        unitary = unitary_from_eigendecomposition(
            eigenvalues, eigenvectors, float(params["time"])
        )
        probabilities, pairs = conditional_two_photon_distribution(unitary)
        rows[spec.label] = {
            "pair_count": len(pairs),
            "probability_sum": float(probabilities.sum()),
            "probability_min": float(probabilities.min()),
            "probability_max": float(probabilities.max()),
            "participation_ratio": participation_ratio(probabilities),
        }
    passed = all(
        abs(row["probability_sum"] - 1.0) <= float(params["tolerance"])
        and row["probability_min"] >= 0.0
        for row in rows.values()
    )
    return {"mode": "reduced_formula_validation", "observations": rows, "passed": passed}


def _probe_validation(params: dict[str, Any]) -> dict[str, Any]:
    times = np.asarray(params["times"], dtype=float)
    result = ensemble_metrics(_samples(params, chaotic=True), times)
    metrics = result["metrics"]
    finite = all(
        np.isfinite(row["pt_wasserstein"])
        and np.isfinite(row["entropy_mean"])
        and np.isfinite(row["sff4_mean"])
        for row in metrics
    )
    return {
        "mode": "reduced_formula_validation",
        "metrics": metrics,
        "passed": bool(finite and len(metrics) == len(times)),
    }


def _otoc_sector_validation(params: dict[str, Any]) -> dict[str, Any]:
    times = np.asarray(params["times"], dtype=float)
    observations: dict[str, Any] = {}
    for chaotic in (False, True):
        spec = CHAOTIC if chaotic else INTEGRABLE
        result = ensemble_metrics(_samples(params, chaotic=chaotic), times)
        sector_rows = result["otoc_sector_rows"]
        observations[spec.label] = {
            "metrics": result["metrics"],
            "sector_rows": sector_rows,
        }
    finite = all(
        np.isfinite(row["probability_mean"])
        and row["probability_mean"] >= 0.0
        for payload in observations.values()
        for row in payload["sector_rows"]
    )
    return {"mode": "reduced_formula_validation", "observations": observations, "passed": bool(finite)}


def _ideal_otoc_validation(params: dict[str, Any]) -> dict[str, Any]:
    times = np.asarray(params["times"], dtype=float)
    pairs = [tuple(int(value) for value in pair) for pair in params["output_pairs"]]
    curves: dict[str, Any] = {}
    for chaotic in (False, True):
        spec = CHAOTIC if chaotic else INTEGRABLE
        samples = _samples(params, chaotic=chaotic)
        curves[spec.label] = {
            f"{pair[0]}-{pair[1]}": averaged_otoc_series(samples, times, pair).tolist()
            for pair in pairs
        }
    finite = all(
        np.all(np.isfinite(values)) and np.all(np.asarray(values) >= 0.0)
        for ensemble in curves.values()
        for values in ensemble.values()
    )
    return {
        "mode": "reduced_formula_validation",
        "times": times.tolist(),
        "curves": curves,
        "passed": bool(finite),
    }


def _short_time_and_fft_validation(params: dict[str, Any]) -> dict[str, Any]:
    samples = _samples(params, chaotic=True)
    short_times = np.asarray(params["short_times"], dtype=float)
    slopes: dict[str, float] = {}
    for label, pair in {
        "overlap_one": tuple(params["overlap_one_pair"]),
        "overlap_zero": tuple(params["overlap_zero_pair"]),
    }.items():
        values = averaged_otoc_series(samples, short_times, pair)
        slopes[label] = float(np.polyfit(np.log(short_times), np.log(values), 1)[0])

    long_times = np.linspace(
        float(params["fft_time_min"]),
        float(params["fft_time_max"]),
        int(params["fft_points"]),
    )
    series = averaged_otoc_series(
        samples, long_times, tuple(params["fft_output_pair"])
    )
    centered = series / max(float(np.mean(series)), 1e-15) - 1.0
    spectrum = np.abs(np.fft.rfft(centered)) ** 2
    positive = spectrum[1:]
    weights = positive / max(float(positive.sum()), 1e-15)
    fft_pr = float(1.0 / np.sum(weights**2))
    expected = params["expected_slope_ranges"]
    passed = (
        expected["overlap_one"][0] <= slopes["overlap_one"] <= expected["overlap_one"][1]
        and expected["overlap_zero"][0] <= slopes["overlap_zero"] <= expected["overlap_zero"][1]
        and np.isfinite(fft_pr)
        and fft_pr > 0.0
    )
    return {
        "mode": "reduced_formula_validation",
        "short_time_slopes": slopes,
        "fft_participation_ratio": fft_pr,
        "passed": bool(passed),
    }


def _run_target(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    modes = {
        "distribution": _distribution_validation,
        "probe_triplet": _probe_validation,
        "otoc_sectors": _otoc_sector_validation,
        "ideal_otoc": _ideal_otoc_validation,
        "short_time_fft": _short_time_and_fft_validation,
    }
    mode = str(params.get("mode") or "")
    if mode not in modes:
        raise ValueError(f"{target_id}: unsupported campaign mode {mode!r}")
    result = modes[mode](params)
    result.update(
        {
            "target_id": target_id,
            "campaign_scale": "reduced",
            "scientific_coverage_promoted": False,
        }
    )
    return result


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if tuple(config.get("attestation_parameters", {}).get("target_ids", ())) != TARGET_IDS:
        raise ValueError("campaign target list does not match the fixed implementation denominator")
    boundary = config.get("clean_room_boundary", {})
    forbidden_flags = (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    )
    if any(boundary.get(name) is not False for name in forbidden_flags):
        raise ValueError("clean-room boundary must explicitly forbid every source-derived input")

    targets = config.get("targets", {})
    if tuple(targets) != TARGET_IDS:
        raise ValueError("target configuration must preserve the frozen target order")
    data_dir = output_root / "data" / "implementation_closure"
    check_dir = output_root / "checks" / "implementation_closure"
    summaries: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id])
        _write_json(data_dir / f"{target_id}.json", result)
        check = {
            "target_id": target_id,
            "status": "passed" if result["passed"] else "failed",
            "mode": result["mode"],
            "scientific_coverage_promoted": False,
            "acceptance_criteria": targets[target_id]["acceptance_criteria"],
        }
        _write_json(check_dir / f"{target_id}.json", check)
        summaries.append(check)

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": "passed" if all(row["status"] == "passed" for row in summaries) else "failed",
        "target_ids": list(TARGET_IDS),
        "scientific_coverage_promoted": False,
        "clean_room_boundary": boundary,
        "target_checks": summaries,
    }
    _write_json(check_dir / "manifest.json", manifest)
    return manifest
