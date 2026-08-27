"""Clean-room implementations for the five uncovered analytic claims.

The numerical entry point consumes only a frozen JSON configuration.  It does
not read the paper, source figures, author code, author arrays, or digitized
references.  Passing this campaign proves implementation readiness only; it
does not promote scientific coverage.
"""

from __future__ import annotations

import json
from math import pi
from pathlib import Path
from typing import Any

import numpy as np
from scipy.special import j0


TARGET_IDS = ("T032", "T033", "T034", "T035", "T036")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def crossover_length(
    gamma: np.ndarray,
    *,
    gamma_zero: float,
    prefactor: float,
) -> np.ndarray:
    """Evaluate L_c=A exp(sqrt(gamma_0/gamma)) once inputs are known."""

    values = np.asarray(gamma, dtype=float)
    if np.any(values <= 0.0) or gamma_zero <= 0.0 or prefactor <= 0.0:
        raise ValueError("gamma, gamma_zero, and prefactor must be positive")
    return prefactor * np.exp(np.sqrt(gamma_zero / values))


def qsd_norm_moment_rate(gamma: float, moment: int, centered_mean: float) -> float:
    """Return the Eq. App. 3 rate for a centered QSD measurement operator."""

    if gamma < 0.0 or moment < 1:
        raise ValueError("gamma must be nonnegative and moment must be positive")
    return float(2.0 * gamma * moment * (moment - 1) * centered_mean**2)


def quantum_jump_norm_multiplier(occupation: float) -> float:
    """Exact norm multiplier for (1+M)=n/sqrt(<n>) with n^2=n."""

    probability = float(occupation)
    if not 0.0 < probability <= 1.0:
        raise ValueError("occupation must lie in (0, 1]")
    empty_amplitude = 0.0
    occupied_amplitude = 1.0 / np.sqrt(probability)
    return float(
        (1.0 - probability) * empty_amplitude**2
        + probability * occupied_amplitude**2
    )


def qsdc_norm_moment_rate(
    gamma: float,
    moment: int,
    density_expectation: float,
) -> float:
    """Approximate QSDc growth rate printed below Eq. App. 3."""

    if gamma < 0.0 or moment < 1 or not 0.0 <= density_expectation <= 1.0:
        raise ValueError("invalid QSDc rate parameters")
    return float(
        2.0
        * gamma
        * moment
        * (moment - 1)
        * density_expectation**2
    )


def _input_boundary(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    schema = params.get("required_input_schema")
    supplied = params.get("supplied_inputs", [])
    if not isinstance(schema, dict) or not schema:
        raise ValueError(f"{target_id}: required_input_schema must be non-empty")
    if not isinstance(supplied, list):
        raise ValueError(f"{target_id}: supplied_inputs must be a list")
    missing = [name for name in schema if name not in supplied]
    if not missing:
        raise ValueError(f"{target_id}: all required inputs are present")
    return {
        "target_id": target_id,
        "mode": "input_boundary",
        "status": "input_blocked",
        "required_input_schema": schema,
        "supplied_inputs": supplied,
        "missing_inputs": missing,
        "parameterized_runner": (
            "claim_implementation_campaign.crossover_length"
        ),
        "acceptance_boundary": params["acceptance_boundary"],
        "scientific_coverage_promoted": False,
    }


def _qsd_validation(params: dict[str, Any]) -> dict[str, Any]:
    gamma = float(params["gamma"])
    rows = [
        {
            "moment": int(moment),
            "rate": qsd_norm_moment_rate(gamma, int(moment), 0.0),
        }
        for moment in params["moments"]
    ]
    passed = all(abs(row["rate"]) <= float(params["tolerance"]) for row in rows)
    return {
        "target_id": "T033",
        "mode": "analytic_formula_validation",
        "rows": rows,
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _quantum_jump_validation(params: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, float]] = []
    for occupation in params["occupation_grid"]:
        probability = float(occupation)
        mean_m = np.sqrt(probability) - 1.0
        mean_m2 = 2.0 - 2.0 * np.sqrt(probability)
        rows.append(
            {
                "occupation": probability,
                "direct_projector_multiplier": quantum_jump_norm_multiplier(
                    probability
                ),
                "printed_bracket_as_transcribed": float(
                    mean_m**2 + 4.0 * mean_m * mean_m2 + mean_m2**2
                ),
            }
        )
    tolerance = float(params["tolerance"])
    passed = all(
        abs(row["direct_projector_multiplier"] - 1.0) <= tolerance
        for row in rows
    )
    return {
        "target_id": "T034",
        "mode": "analytic_projector_validation",
        "rows": rows,
        "printed_expansion_note": (
            "The direct n^2=n projector identity proves norm conservation. "
            "The bracket transcribed in Eq. App. 4 is retained separately for "
            "fresh scientific review and is not used to tune the result."
        ),
        "passed": passed,
        "scientific_coverage_promoted": False,
    }


def _qsdc_validation(params: dict[str, Any]) -> dict[str, Any]:
    density = float(params["density_expectation"])
    times = np.asarray(params["times"], dtype=float)
    rows: list[dict[str, Any]] = []
    for gamma in params["gammas"]:
        for moment in params["moments"]:
            rate = qsdc_norm_moment_rate(float(gamma), int(moment), density)
            values = np.exp(rate * times)
            rows.append(
                {
                    "gamma": float(gamma),
                    "moment": int(moment),
                    "predicted_rate": rate,
                    "times": times.tolist(),
                    "normalized_moments": values.tolist(),
                }
            )
    passed = all(
        np.all(np.isfinite(row["normalized_moments"]))
        and np.all(np.diff(row["normalized_moments"]) >= 0.0)
        for row in rows
    )
    return {
        "target_id": "T035",
        "mode": "analytic_formula_validation",
        "rows": rows,
        "passed": bool(passed),
        "scientific_coverage_promoted": False,
    }


def _bessel_validation(params: dict[str, Any]) -> dict[str, Any]:
    tau = np.linspace(
        float(params["tau_min"]),
        float(params["tau_max"]),
        int(params["tau_points"]),
    )
    correlation = j0(tau) ** 2
    orders = np.arange(int(params["asymptotic_order_min"]), int(params["asymptotic_order_max"]) + 1)
    peak_tau = orders * pi + pi / 4.0
    peak_values = j0(peak_tau) ** 2
    slope = float(np.polyfit(np.log(peak_tau), np.log(peak_values), 1)[0])
    scaled_peak_error = float(np.max(np.abs(peak_tau * peak_values - 2.0 / pi)))
    passed = (
        abs(float(correlation[0]) - 1.0) <= float(params["origin_tolerance"])
        and np.all(correlation >= 0.0)
        and abs(slope + 1.0) <= float(params["slope_tolerance"])
        and scaled_peak_error <= float(params["scaled_peak_tolerance"])
    )
    return {
        "target_id": "T036",
        "mode": "analytic_formula_validation",
        "tau": tau.tolist(),
        "correlation": correlation.tolist(),
        "asymptotic_peak_slope": slope,
        "scaled_peak_error_from_2_over_pi": scaled_peak_error,
        "passed": bool(passed),
        "scientific_coverage_promoted": False,
    }


def _run_target(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    if target_id == "T032":
        return _input_boundary(target_id, params)
    runners = {
        "T033": _qsd_validation,
        "T034": _quantum_jump_validation,
        "T035": _qsdc_validation,
        "T036": _bessel_validation,
    }
    return runners[target_id](params)


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    declared = tuple(config.get("attestation_parameters", {}).get("target_ids", ()))
    if declared != TARGET_IDS:
        raise ValueError("campaign target list does not match the fixed denominator")
    boundary = config.get("clean_room_boundary", {})
    forbidden_flags = (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    )
    if any(boundary.get(name) is not False for name in forbidden_flags):
        raise ValueError("clean-room boundary must explicitly reject every source input")
    targets = config.get("targets", {})
    if tuple(targets) != TARGET_IDS:
        raise ValueError("target configuration order is not frozen")

    data_dir = output_root / "data" / "claim_implementation_closure"
    check_dir = output_root / "checks" / "claim_implementation_closure"
    checks: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id])
        _write_json(data_dir / f"{target_id}.json", result)
        status = result.get("status") or ("passed" if result.get("passed") else "failed")
        check = {
            "target_id": target_id,
            "status": status,
            "mode": result["mode"],
            "acceptance_criteria": targets[target_id]["acceptance_criteria"],
            "scientific_coverage_promoted": False,
        }
        _write_json(check_dir / f"{target_id}.json", check)
        checks.append(check)

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": (
            "failed"
            if any(row["status"] == "failed" for row in checks)
            else "passed_with_input_boundaries"
        ),
        "target_ids": list(TARGET_IDS),
        "target_checks": checks,
        "clean_room_boundary": boundary,
        "scientific_coverage_promoted": False,
    }
    _write_json(check_dir / "manifest.json", manifest)
    return manifest
