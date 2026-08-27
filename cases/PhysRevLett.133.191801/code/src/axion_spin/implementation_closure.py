"""Formula-level implementation boundary for mixed theory/experiment panels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .signals import (
    gaussian_modulated_drive,
    linear_chirp_drive,
    resonant_free_decay_response,
)
from .statistics import combine_independent_uncertainties
from .transfer import resonator_response


TARGET_IDS = ("T001", "T002", "T003", "T006")
REQUIRED_INPUTS = {
    "T001": ("measured_decay_traces", "sampling_timebase", "response_normalization"),
    "T002": ("gaussian_waveform_calibration", "measured_gaussian_response"),
    "T003": ("chirp_waveform_calibration", "measured_chirp_response"),
    "T006": ("dataset_estimates", "calibration_covariance", "systematic_decomposition"),
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_required_inputs(
    target_id: str,
    schema: dict[str, Any],
    supplied_inputs: dict[str, Any],
) -> tuple[list[str], list[str]]:
    if target_id not in REQUIRED_INPUTS:
        raise ValueError(f"unsupported target: {target_id}")
    if tuple(schema) != REQUIRED_INPUTS[target_id]:
        raise ValueError(f"{target_id}: schema does not match the frozen denominator")
    if not isinstance(supplied_inputs, dict):
        raise ValueError(f"{target_id}: supplied_inputs must be an object")
    missing = [name for name in schema if name not in supplied_inputs]
    invalid: list[str] = []
    for name, value in supplied_inputs.items():
        if name not in schema:
            invalid.append(f"{name}:undeclared")
        elif schema[name].get("hash_required") and not (
            isinstance(value, dict) and str(value.get("sha256", ""))
        ):
            invalid.append(f"{name}:sha256_required")
    return missing, invalid


def formula_checks(parameters: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Exercise only paper formulas and declared non-paper-exact probe inputs."""

    time = np.linspace(0.0, parameters["duration_s"], parameters["time_points"])
    sensor = parameters["sensor"]
    free = resonant_free_decay_response(
        time,
        amplitude=1.0,
        amplification=sensor["amplification"],
        sensor_coherence_s=sensor["coherence_s"],
        source_coherence_s=parameters["source_coherence_s"],
        frequency_hz=sensor["resonance_hz"],
    )
    gaussian = gaussian_modulated_drive(time, **parameters["gaussian_probe"])
    chirp = linear_chirp_drive(time, **parameters["chirp_probe"])
    gaussian_response = resonator_response(time, gaussian, **sensor)
    chirp_response = resonator_response(time, chirp, **sensor)
    total_uncertainty = combine_independent_uncertainties(
        parameters["uncertainty_components_aT"]
    )
    checks = {
        "T001": {
            "formula_check": "Eq. (4) free-decay response is finite and starts at zero",
            "passed": bool(np.all(np.isfinite(free)) and abs(free[0]) < 1.0e-12),
            "points": int(free.size),
            "peak_abs": float(np.max(np.abs(free))),
        },
        "T002": {
            "formula_check": "Gaussian drive and resonator response are finite",
            "passed": bool(np.all(np.isfinite(gaussian_response))),
            "points": int(gaussian_response.size),
            "peak_abs": float(np.max(np.abs(gaussian_response))),
        },
        "T003": {
            "formula_check": "Linear chirp and resonator response are finite",
            "passed": bool(np.all(np.isfinite(chirp_response))),
            "points": int(chirp_response.size),
            "peak_abs": float(np.max(np.abs(chirp_response))),
        },
        "T006": {
            "formula_check": "Independent uncertainties combine in quadrature",
            "passed": bool(np.isclose(total_uncertainty, np.hypot(140.0, 45.0))),
            "components_aT": parameters["uncertainty_components_aT"],
            "combined_aT": total_uncertainty,
        },
    }
    if not all(row["passed"] for row in checks.values()):
        raise RuntimeError("one or more formula-level checks failed")
    return checks


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if tuple(config["attestation_parameters"]["target_ids"]) != TARGET_IDS:
        raise ValueError("campaign target ids do not match the frozen denominator")
    boundary = config["clean_room_boundary"]
    for field in (
        "paper_pdf_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    ):
        if boundary.get(field) is not False:
            raise ValueError(f"clean-room boundary must set {field}=false")

    checks = formula_checks(config["formula_probe"])
    blocked_targets: list[str] = []
    for target_id in TARGET_IDS:
        spec = config["targets"][target_id]
        missing, invalid = validate_required_inputs(
            target_id, spec["required_input_schema"], spec["supplied_inputs"]
        )
        if invalid:
            raise ValueError(f"{target_id}: invalid supplied inputs: {invalid}")
        status = "input_blocked" if missing else "ready_for_full_reanalysis"
        if missing:
            blocked_targets.append(target_id)
        result = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "status": status,
            "required_input_schema": spec["required_input_schema"],
            "supplied_inputs": sorted(spec["supplied_inputs"]),
            "missing_inputs": missing,
            "formula_check": checks[target_id],
            "next_execution": spec["next_execution"],
            "acceptance_criteria": spec["acceptance_criteria"],
            "scientific_coverage_promoted": False,
        }
        _write_json(
            output_root / "data" / "implementation_closure" / f"{target_id}.json",
            result,
        )
        _write_json(
            output_root / "checks" / "implementation_closure" / f"{target_id}.json",
            {
                "target_id": target_id,
                "status": status,
                "formula_check_passed": checks[target_id]["passed"],
                "missing_input_count": len(missing),
                "scientific_coverage_promoted": False,
            },
        )

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "target_ids": list(TARGET_IDS),
        "status": "input_blocked" if blocked_targets else "ready",
        "blocked_targets": blocked_targets,
        "formula_checks_passed": True,
        "clean_room_boundary": boundary,
        "scientific_coverage_promoted": False,
    }
    _write_json(
        output_root / "checks" / "implementation_closure" / "manifest.json",
        manifest,
    )
    return manifest
