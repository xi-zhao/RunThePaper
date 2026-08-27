"""Clean-room implementation campaign for all four LDSI targets.

Published formulas are exercised at a reduced, frozen scale for T002/T003.
T001/T004 fail closed because their exact finite-chain and nonlinear sampling
inputs are not disclosed.  The campaign never reads paper/source material,
author numerics, or source figures and never promotes scientific coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .ldsi_model import (
    aa_eigensystem,
    continue_self_consistent_branch,
    critical_pump,
    ground_state_response,
    inverse_participation_ratio,
    momentum_distribution,
    scattering_response,
)


TARGET_IDS = ("T001", "T002", "T003", "T004")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
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
        raise ValueError(f"{target_id}: all inputs are supplied; use an executable mode")
    return {
        "target_id": target_id,
        "mode": "input_boundary",
        "status": "input_blocked",
        "required_input_schema": schema,
        "supplied_inputs": supplied,
        "missing_inputs": missing,
        "forbidden_substitutions": [
            "author numerical code",
            "author numerical arrays",
            "digitized paper curves",
            "source-figure pixels",
            "source-calibrated finite-chain phase, boundary, pump, or solver settings",
        ],
        "acceptance_boundary": str(params["acceptance_boundary"]),
        "scientific_coverage_promoted": False,
    }


def _linear_validation(params: dict[str, Any]) -> dict[str, Any]:
    length = int(params["length"])
    gamma = float(params["gamma"])
    gamma_c = float(params["gamma_c"])
    q_values = np.linspace(
        float(params["q_min"]), float(params["q_max"]), int(params["q_points"])
    )
    rows: list[dict[str, Any]] = []
    passed = True
    for chi in params["chi_values"]:
        chi = float(chi)
        energies, vectors = aa_eigensystem(length, chi, gamma=gamma)
        channels, response, _ = scattering_response(energies, vectors, gamma_c)
        threshold = critical_pump(
            response,
            atom_number=float(params["atom_number"]),
            delta_c=float(params["delta_c"]),
            kappa=float(params["kappa"]),
            dispersive_coupling=float(params["dispersive_coupling"]),
            shift_factor=float(params["shift_factor"]),
        )
        momentum = momentum_distribution(vectors[:, 0], q_values)
        ipr = float(inverse_participation_ratio(vectors[:, :1])[0])
        orthogonality_error = float(
            np.max(np.abs(vectors.T @ vectors - np.eye(length)))
        )
        passed = passed and bool(
            np.isfinite(response)
            and response > 0.0
            and np.isfinite(threshold)
            and threshold > 0.0
            and np.all(momentum >= 0.0)
            and abs(float(np.sum(channels)) - response) <= float(params["tolerance"])
            and orthogonality_error <= float(params["orthogonality_tolerance"])
        )
        rows.append(
            {
                "chi_over_J": chi,
                "susceptibility": response,
                "critical_pump_over_J": threshold,
                "ground_ipr": ipr,
                "momentum_min": float(momentum.min()),
                "momentum_max": float(momentum.max()),
                "orthogonality_error": orthogonality_error,
            }
        )
    return {
        "target_id": "T002",
        "mode": "reduced_formula_validation",
        "observations": rows,
        "passed": bool(passed),
        "scientific_coverage_promoted": False,
    }


def _nonlinear_validation(params: dict[str, Any]) -> dict[str, Any]:
    length = int(params["length"])
    gamma = float(params["gamma"])
    gamma_c = float(params["gamma_c"])
    solver = {
        "atom_number": float(params["atom_number"]),
        "delta_c": float(params["delta_c"]),
        "kappa": float(params["kappa"]),
        "dispersive_coupling": float(params["dispersive_coupling"]),
        "shift_factor": float(params["shift_factor"]),
        "mixing": float(params["mixing"]),
        "tolerance": float(params["solver_tolerance"]),
        "max_iterations": int(params["max_iterations"]),
    }
    branch = continue_self_consistent_branch(
        params["eta_descending"],
        length=length,
        chi=float(params["chi"]),
        gamma=gamma,
        gamma_c=gamma_c,
        seed_field=complex(float(params["seed_field_real"]), 0.0),
        **solver,
    )
    branch_rows = [
        {
            "eta_over_J": eta,
            "photon_number": result.photon_number,
            "state_ipr": result.ipr,
            "density_sum": float(np.sum(np.abs(result.state) ** 2)),
            "iterations": result.iterations,
            "converged": result.converged,
        }
        for eta, result in branch
    ]

    landscape: list[dict[str, float]] = []
    for probe_gamma_c in params["landscape_gamma_c"]:
        response, _, _, _ = ground_state_response(
            length,
            float(params["landscape_chi"]),
            gamma=gamma,
            gamma_c=float(probe_gamma_c),
        )
        threshold = critical_pump(
            response,
            atom_number=float(params["atom_number"]),
            delta_c=float(params["delta_c"]),
            kappa=float(params["kappa"]),
            dispersive_coupling=float(params["dispersive_coupling"]),
            shift_factor=float(params["shift_factor"]),
        )
        landscape.append(
            {
                "gamma_c": float(probe_gamma_c),
                "susceptibility": response,
                "critical_pump_over_J": threshold,
            }
        )
    passed = (
        all(row["converged"] for row in branch_rows)
        and all(abs(row["density_sum"] - 1.0) <= float(params["normalization_tolerance"]) for row in branch_rows)
        and all(row["photon_number"] >= 0.0 and np.isfinite(row["photon_number"]) for row in branch_rows)
        and all(np.isfinite(row["critical_pump_over_J"]) and row["critical_pump_over_J"] > 0.0 for row in landscape)
    )
    return {
        "target_id": "T003",
        "mode": "reduced_formula_validation",
        "branch": branch_rows,
        "threshold_landscape": landscape,
        "passed": bool(passed),
        "scientific_coverage_promoted": False,
    }


def _run_target(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    mode = str(params.get("mode") or "")
    if mode == "input_boundary":
        return _input_boundary(target_id, params)
    if target_id == "T002" and mode == "linear_reduced":
        return _linear_validation(params)
    if target_id == "T003" and mode == "nonlinear_reduced":
        return _nonlinear_validation(params)
    raise ValueError(f"{target_id}: unsupported campaign mode {mode!r}")


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if tuple(config.get("attestation_parameters", {}).get("target_ids", ())) != TARGET_IDS:
        raise ValueError("campaign target list does not match the fixed figure denominator")
    boundary = config.get("clean_room_boundary", {})
    for name in (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    ):
        if boundary.get(name) is not False:
            raise ValueError(f"clean-room boundary must set {name}=false")
    targets = config.get("targets", {})
    if tuple(targets) != TARGET_IDS:
        raise ValueError("target configuration must preserve the frozen target order")

    data_dir = output_root / "data" / "implementation_closure"
    check_dir = output_root / "checks" / "implementation_closure"
    checks: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id])
        _write_json(data_dir / f"{target_id}.json", result)
        status = result.get("status") or ("passed" if result.get("passed") else "failed")
        check = {
            "target_id": target_id,
            "status": status,
            "mode": result["mode"],
            "scientific_coverage_promoted": False,
            "acceptance_criteria": targets[target_id]["acceptance_criteria"],
        }
        _write_json(check_dir / f"{target_id}.json", check)
        checks.append(check)

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": "failed" if any(row["status"] == "failed" for row in checks) else "passed_with_input_boundaries",
        "target_ids": list(TARGET_IDS),
        "scientific_coverage_promoted": False,
        "clean_room_boundary": boundary,
        "target_checks": checks,
    }
    _write_json(check_dir / "manifest.json", manifest)
    return manifest
