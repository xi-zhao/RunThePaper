"""Executable clean-room boundary for the two unresolved DQC1 claims.

The finite DQC1 model is independently executable, but the publication does
not specify either an asymptotic ensemble/limit protocol or a frozen corpus
for the historical-priority wording.  This module keeps those missing inputs
explicit while exercising the common finite scientific kernel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .claim_boundaries import discord_signature_boundary


TARGET_IDS = ("T008", "T014")
REQUIRED_INPUTS = {
    "T008": (
        "unitary_ensemble_definition",
        "asymptotic_register_sequence",
        "samples_per_register_size",
        "scaling_observable",
        "zero_tolerance",
        "convergence_criterion",
    ),
    "T014": (
        "operational_first_signature_claim",
        "priority_corpus_manifest",
        "asymptotic_protocol",
        "priority_adjudication_rule",
    ),
}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_required_inputs(
    target_id: str,
    schema: dict[str, Any],
    supplied_inputs: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Validate the frozen scientific-input boundary without external reads."""

    if target_id not in REQUIRED_INPUTS:
        raise ValueError(f"unsupported target: {target_id}")
    required = REQUIRED_INPUTS[target_id]
    if tuple(schema) != required:
        raise ValueError(f"{target_id}: schema does not match the frozen denominator")
    if not isinstance(supplied_inputs, dict):
        raise ValueError(f"{target_id}: supplied_inputs must be an object")
    missing = [name for name in required if name not in supplied_inputs]
    invalid: list[str] = []
    for name, value in supplied_inputs.items():
        if name not in schema:
            invalid.append(f"{name}:undeclared")
            continue
        rule = schema[name]
        if rule.get("hash_required") and not (
            isinstance(value, dict) and str(value.get("sha256", ""))
        ):
            invalid.append(f"{name}:sha256_required")
    return missing, invalid


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    """Run the finite kernel and emit fail-closed artifacts for both claims."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    target_ids = tuple(config["attestation_parameters"]["target_ids"])
    if target_ids != TARGET_IDS:
        raise ValueError("campaign target ids do not match the frozen denominator")
    boundary = config["clean_room_boundary"]
    for field in (
        "paper_pdf_read_by_runner",
        "paper_source_read_by_runner",
        "source_pixels_used",
        "author_numeric_arrays_used",
        "author_code_used",
    ):
        if boundary.get(field) is not False:
            raise ValueError(f"clean-room boundary must set {field}=false")

    _, finite = discord_signature_boundary(config["finite_probe_parameters"])
    if not finite["all_rows_support_finite_boundary"]:
        raise RuntimeError("finite DQC1 scientific kernel failed its invariant")

    blocked_targets: list[str] = []
    for target_id in TARGET_IDS:
        spec = config["targets"][target_id]
        missing, invalid = validate_required_inputs(
            target_id,
            spec["required_input_schema"],
            spec["supplied_inputs"],
        )
        if invalid:
            raise ValueError(f"{target_id}: invalid supplied inputs: {invalid}")
        status = "input_blocked" if missing else "ready_for_claim_adjudication"
        if missing:
            blocked_targets.append(target_id)
        data = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "scientific_object": spec["scientific_object"],
            "status": status,
            "required_input_schema": spec["required_input_schema"],
            "supplied_inputs": sorted(spec["supplied_inputs"]),
            "missing_inputs": missing,
            "finite_probe": {
                "alpha_cutoff": finite["alpha_cutoff"],
                "partition_qubits": finite["partition_qubits"],
                "maximum_negativity": finite["maximum_negativity"],
                "maximum_realignment_trace_norm": finite[
                    "maximum_realignment_trace_norm"
                ],
                "all_rows_support_finite_boundary": finite[
                    "all_rows_support_finite_boundary"
                ],
            },
            "next_execution": spec["next_execution"],
            "acceptance_criteria": spec["acceptance_criteria"],
            "scientific_coverage_promoted": False,
        }
        _write_json(
            output_root / "data" / "implementation_closure" / f"{target_id}.json",
            data,
        )
        _write_json(
            output_root / "checks" / "implementation_closure" / f"{target_id}.json",
            {
                "target_id": target_id,
                "status": status,
                "required_inputs_complete": not missing,
                "missing_input_count": len(missing),
                "finite_kernel_passed": True,
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
        "clean_room_boundary": boundary,
        "finite_kernel_passed": True,
        "scientific_coverage_promoted": False,
    }
    _write_json(
        output_root / "checks" / "implementation_closure" / "manifest.json",
        manifest,
    )
    return manifest
