"""Strict clean-room input boundary for the two deferred DFT panels.

The publication gives a qualitative QE/Wannier workflow but not the complete
first-principles inputs.  This module therefore validates a frozen input
contract and builds an execution plan without guessing pseudopotentials,
structures, cutoffs, or Wannier windows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TARGET_IDS = ("D001", "D002")
REQUIRED_INPUT_KEYS = (
    "qe_version",
    "exchange_correlation_functional",
    "fully_relativistic_pseudopotentials",
    "relaxed_structure",
    "kinetic_energy_cutoff_ry",
    "charge_density_cutoff_ry",
    "k_point_mesh",
    "occupations_and_smearing",
    "scf_convergence_threshold_ry",
    "spin_orbit_enabled",
    "wannier_projection_windows_ev",
    "wannier_initial_projections",
    "high_symmetry_path",
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_input_contract(
    *,
    schema: dict[str, Any],
    supplied_inputs: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Return missing and invalid fields without consulting external files."""

    if tuple(schema) != REQUIRED_INPUT_KEYS:
        raise ValueError("DFT input schema does not match the frozen denominator")
    if not isinstance(supplied_inputs, dict):
        raise ValueError("supplied_inputs must be an object")
    missing = [key for key in REQUIRED_INPUT_KEYS if key not in supplied_inputs]
    invalid: list[str] = []
    for key, value in supplied_inputs.items():
        if key not in schema:
            invalid.append(f"{key}:undeclared")
            continue
        rule = schema[key]
        if rule.get("hash_required") and not str(value.get("sha256", "")):
            invalid.append(f"{key}:sha256_required")
        if rule.get("type") == "positive_number" and not (
            isinstance(value, (int, float)) and float(value) > 0.0
        ):
            invalid.append(f"{key}:positive_number_required")
        if rule.get("type") == "boolean" and not isinstance(value, bool):
            invalid.append(f"{key}:boolean_required")
    return missing, invalid


def build_execution_plan(target_id: str, displacement: str) -> dict[str, Any]:
    """Return the parameterized QE-to-Wannier pipeline after inputs exist."""

    return {
        "target_id": target_id,
        "displacement": displacement,
        "stages": [
            "validate_hash_bound_inputs",
            "run_fully_relativistic_scf",
            "run_nscf_on_frozen_k_mesh",
            "run_wannier_projection",
            "interpolate_high_symmetry_bands",
            "compute_layer_and_spin_characters",
            "run_cutoff_kmesh_and_window_convergence",
        ],
        "required_checks": [
            "all input hashes match",
            "SCF energy and charge converge",
            "Wannier interpolation matches ab-initio bands in the frozen window",
            "band energies and spin/layer weights are finite on the full path",
            "cutoff, k-mesh, and Wannier-window changes stay below tolerance",
        ],
    }


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    declared = tuple(config.get("attestation_parameters", {}).get("target_ids", ()))
    if declared != TARGET_IDS:
        raise ValueError("campaign target ids do not match D001/D002")
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

    schema = config["dft_input_schema"]
    targets = config["targets"]
    if tuple(targets) != TARGET_IDS:
        raise ValueError("target configuration order is not frozen")

    rows: list[dict[str, Any]] = []
    for target_id in TARGET_IDS:
        spec = targets[target_id]
        missing, invalid = validate_input_contract(
            schema=schema,
            supplied_inputs=spec["supplied_inputs"],
        )
        if invalid:
            raise ValueError(f"{target_id}: invalid supplied inputs: {invalid}")
        result = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "panel": spec["panel"],
            "displacement": spec["displacement"],
            "status": "input_blocked" if missing else "ready_for_external_execution",
            "required_input_schema": schema,
            "supplied_inputs": sorted(spec["supplied_inputs"]),
            "missing_inputs": missing,
            "parameterized_execution_plan": build_execution_plan(
                target_id, spec["displacement"]
            ),
            "acceptance_criteria": config["acceptance_criteria"],
            "scientific_coverage_promoted": False,
        }
        _write_json(output_root / "data" / "dft_input_boundary" / f"{target_id}.json", result)
        _write_json(
            output_root / "checks" / "dft_input_boundary" / f"{target_id}.json",
            {
                "target_id": target_id,
                "status": result["status"],
                "missing_input_count": len(missing),
                "input_schema_complete": tuple(schema) == REQUIRED_INPUT_KEYS,
                "scientific_coverage_promoted": False,
            },
        )
        rows.append(result)

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_scale": config["campaign_scale"],
        "status": "input_blocked",
        "target_ids": list(TARGET_IDS),
        "blocked_targets": [row["target_id"] for row in rows if row["missing_inputs"]],
        "clean_room_boundary": boundary,
        "scientific_coverage_promoted": False,
    }
    _write_json(output_root / "checks" / "dft_input_boundary" / "manifest.json", manifest)
    return manifest
