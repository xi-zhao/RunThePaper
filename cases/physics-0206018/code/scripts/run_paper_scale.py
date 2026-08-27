#!/usr/bin/env python3
"""Checkpointed paper-scale BEM campaign for Figs. 5--7.

The runner consumes only case-local code and a JSON configuration.  Paper
figures, source pixels, author code, and author numerical arrays are neither
inputs nor fallback data sources.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.bem import (  # noqa: E402
    BoundaryMesh,
    cross_section,
    far_field,
    reconstruct_field,
    resonance_boundary_state,
    resolution_metric,
)
from src.paper_scale import coupled_explicit_rounded_hexagon_mesh  # noqa: E402

STAGES = ("all", "scan", "resonance", "near-field", "far-field", "aggregate")


def _json_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _atomic_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("paper-scale config must be a schema-version-1 object")
    for field in (
        "campaign_id",
        "output_root",
        "parameters",
        "acceptance",
        "machine",
        "observable_contract",
        "parameter_contract",
        "publication_parameter_resolution",
    ):
        if field not in payload:
            raise ValueError(f"paper-scale config is missing {field}")
    return payload


def _balanced_counts(
    total_elements: int, corner_per_corner: int
) -> tuple[list[int], list[int]]:
    """Allocate an exact even total while using the same six-side map per cavity."""
    corner_counts = [int(corner_per_corner)] * 12
    side_total = int(total_elements) - sum(corner_counts)
    if side_total <= 0 or side_total % 2:
        raise ValueError(
            "total boundary elements must leave an even positive side count"
        )
    per_cavity, remainder = divmod(side_total // 2, 6)
    one_cavity = [per_cavity + (index < remainder) for index in range(6)]
    side_counts = one_cavity * 2
    if sum(side_counts) + sum(corner_counts) != total_elements:
        raise AssertionError(
            "balanced element allocation did not preserve the requested total"
        )
    return side_counts, corner_counts


def _smoke_config(payload: dict[str, Any]) -> dict[str, Any]:
    smoke = copy.deepcopy(payload)
    parameters = smoke["parameters"]
    parameters["total_boundary_elements"] = 48
    parameters["side_element_counts"] = [3] * 12
    parameters["corner_element_counts"] = [1] * 12
    parameters["scan"]["segments"] = [{"start": 22.84444, "stop": 23.04444, "count": 3}]
    parameters["scan"]["angular_samples"] = 72
    parameters["resonance"]["convergence_meshes"] = [
        {"total_boundary_elements": 48, "corner_elements_per_corner": 1}
    ]
    parameters["near_field"]["x_count"] = 9
    parameters["near_field"]["y_count"] = 7
    parameters["far_field_angular_samples"] = 72
    smoke["execution_scale"] = "smoke"
    return smoke


def _wave_numbers(parameters: dict[str, Any]) -> np.ndarray:
    rows = []
    for segment in parameters["scan"]["segments"]:
        rows.append(
            np.linspace(
                float(segment["start"]),
                float(segment["stop"]),
                int(segment["count"]),
            )
        )
    return np.unique(np.round(np.concatenate(rows), 12))


def _mesh(parameters: dict[str, Any]) -> BoundaryMesh:
    return coupled_explicit_rounded_hexagon_mesh(
        parameters["side_element_counts"],
        parameters["corner_element_counts"],
        float(parameters["corner_radius_R"]),
        side_length=float(parameters["hexagon_side_R"]),
        center_displacement=parameters["center_displacement_R"],
    )


def _convergence_mesh(parameters: dict[str, Any], row: dict[str, Any]) -> BoundaryMesh:
    total = int(row["total_boundary_elements"])
    if total == int(parameters["total_boundary_elements"]):
        side_counts = parameters["side_element_counts"]
        corner_counts = parameters["corner_element_counts"]
    else:
        side_counts, corner_counts = _balanced_counts(
            total, int(row["corner_elements_per_corner"])
        )
    return coupled_explicit_rounded_hexagon_mesh(
        side_counts,
        corner_counts,
        float(parameters["corner_radius_R"]),
        side_length=float(parameters["hexagon_side_R"]),
        center_displacement=parameters["center_displacement_R"],
    )


def _geometry_metrics(
    mesh: BoundaryMesh, parameters: dict[str, Any]
) -> dict[str, float | int]:
    reported_k = complex(*map(float, parameters["resonance"]["reported_kR"]))
    curved = mesh.length[mesh.curvature > 0]
    wavelength = 2 * np.pi / (float(parameters["n_inside"]) * reported_k.real)
    corner_radius = float(parameters["corner_radius_R"])
    return {
        "boundary_elements": mesh.size,
        "matrix_dimension": 2 * mesh.size,
        "resolution_b": resolution_metric(
            mesh, reported_k, float(parameters["n_inside"])
        ),
        "rho_over_max_corner_element": corner_radius / float(np.max(curved)),
        "rho_over_local_wavelength": corner_radius / wavelength,
    }


def _validate_parameter_contract(
    payload: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Validate the scientific abstraction at which this paper is exact."""

    contract = payload.get("parameter_contract")
    if not isinstance(contract, dict):
        raise ValueError("parameter_contract must be an object")
    if contract.get("kind") != "declared_equivalence_class":
        raise ValueError(
            "paper-scale BEM requires the paper's declared equivalence class"
        )
    if set(contract.get("equivalence_scope", [])) != {
        "corner_rounding",
        "boundary_discretization",
    }:
        raise ValueError("parameter_contract.equivalence_scope is incomplete")
    if not str(contract.get("paper_statement") or "").strip():
        raise ValueError("parameter_contract.paper_statement is required")
    constraints = contract.get("published_constraints")
    if not isinstance(constraints, list) or len(constraints) < 5 or not all(
        isinstance(item, str) and item.strip() for item in constraints
    ):
        raise ValueError(
            "parameter_contract must enumerate every published class constraint"
        )
    if contract.get("author_private_mesh_identity_claimed") is not False:
        raise ValueError("the unpublished author mesh must not be claimed as identical")
    if contract.get("source_pixels_used_to_select_representative") is not False:
        raise ValueError("source pixels must not select the numerical representative")

    representative = contract.get("independent_representative")
    if not isinstance(representative, dict):
        raise ValueError("parameter_contract.independent_representative is required")
    if payload.get("execution_scale") != "smoke":
        exact_fields = (
            "corner_radius_R",
            "total_boundary_elements",
            "side_element_counts",
            "corner_element_counts",
        )
        mismatches = [
            field
            for field in exact_fields
            if representative.get(field) != parameters.get(field)
        ]
        if mismatches:
            raise ValueError(
                "paper-scale parameters differ from the frozen independent "
                f"representative: {mismatches}"
            )
    return contract


def _validate_publication_parameter_resolution(
    payload: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Keep an internal paper contradiction from becoming false paper-exactness."""

    resolution = payload.get("publication_parameter_resolution")
    if not isinstance(resolution, dict):
        raise ValueError("publication_parameter_resolution must be an object")
    if resolution.get("status") != "source_discrepancy":
        raise ValueError("the displacement-sign conflict must remain explicit")
    if resolution.get("parameter") != "parameters.center_displacement_R":
        raise ValueError("publication discrepancy must identify center_displacement_R")
    prose = resolution.get("prose_value_R")
    figure = resolution.get("figure_value_R")
    selected = resolution.get("selected_value_R")
    if prose != [1.8, 0.5] or figure != [1.8, -0.5]:
        raise ValueError("publication displacement values do not match the audited sources")
    if selected != figure or selected != parameters.get("center_displacement_R"):
        raise ValueError("the numerical geometry must use the Figure 4 displacement")
    if not str(resolution.get("selected_basis") or "").strip():
        raise ValueError("publication discrepancy requires a selection basis")
    sources = resolution.get("paper_sources")
    if not isinstance(sources, list) or len(sources) < 2 or not all(
        isinstance(item, str) and item.strip() for item in sources
    ):
        raise ValueError("publication discrepancy requires both paper sources")
    if resolution.get("source_pixels_used_to_fit_parameters") is not False:
        raise ValueError("source pixels must not fit the publication variant")
    if resolution.get("paper_exact_claim_allowed") is not False:
        raise ValueError("the unresolved source conflict forbids paper-exact claims")
    return resolution


def validate_config(payload: dict[str, Any]) -> dict[str, Any]:
    parameters = payload["parameters"]
    parameter_contract = _validate_parameter_contract(payload, parameters)
    publication_resolution = _validate_publication_parameter_resolution(
        payload, parameters
    )
    observable_contract = payload["observable_contract"]
    if not isinstance(observable_contract, dict) or (
        observable_contract.get("T001", {}).get("estimator") != "optical_theorem"
    ):
        raise ValueError("T001 must use the paper's optical-theorem estimator")
    side_counts = [int(value) for value in parameters["side_element_counts"]]
    corner_counts = [int(value) for value in parameters["corner_element_counts"]]
    if len(side_counts) != 12 or len(corner_counts) != 12:
        raise ValueError(
            "the two hexagons require twelve side and twelve corner counts"
        )
    declared_total = int(parameters["total_boundary_elements"])
    if sum(side_counts) + sum(corner_counts) != declared_total:
        raise ValueError("explicit segment counts do not equal total_boundary_elements")
    if declared_total % 2:
        raise ValueError("the two-cavity boundary-element count must be even")
    if any(value < 1 for value in [*side_counts, *corner_counts]):
        raise ValueError("all explicit segment counts must be positive")
    if len(parameters["center_displacement_R"]) != 2:
        raise ValueError("center_displacement_R must contain two coordinates")
    if float(parameters["n_outside"]) != 1.0:
        raise ValueError(
            "the current far-field normalization requires paper n_outside=1"
        )
    if _wave_numbers(parameters).size < 2:
        raise ValueError("scan grid must contain at least two distinct points")
    workers = int(payload.get("sharding", {}).get("in_process_workers", 1))
    if workers < 1:
        raise ValueError("sharding.in_process_workers must be a positive integer")
    output_root = Path(str(payload["output_root"]))
    if (
        output_root.is_absolute()
        or ".." in output_root.parts
        or not output_root.parts
        or output_root.parts[0] != "outputs"
    ):
        raise ValueError("output_root must be workspace-relative below outputs/")
    convergence_totals = [
        int(row["total_boundary_elements"])
        for row in parameters["resonance"]["convergence_meshes"]
    ]
    if convergence_totals != sorted(set(convergence_totals)):
        raise ValueError("resonance convergence meshes must be unique and increasing")
    if not convergence_totals or convergence_totals[-1] != declared_total:
        raise ValueError("resonance convergence must end at total_boundary_elements")
    attestation = payload.get("input_attestation")
    if not isinstance(attestation, dict):
        raise ValueError("input_attestation is required")
    for field in (
        "source_pixels_used_as_numeric_input",
        "source_pixels_used_to_select_representative",
        "author_numerical_arrays_used",
        "author_code_used",
    ):
        if attestation.get(field) is not False:
            raise ValueError(f"input_attestation.{field} must be false")
    if attestation.get("scientific_config_frozen_before_rendering") is not True:
        raise ValueError("scientific config must be frozen before rendering")
    mesh = _mesh(parameters)
    metrics = _geometry_metrics(mesh, parameters)
    return {
        "schema_version": 1,
        "status": "ready",
        "campaign_id": payload["campaign_id"],
        "execution_scale": payload.get("execution_scale", "paper_scale"),
        "config_sha256": _json_hash(payload),
        "scan_points": int(_wave_numbers(parameters).size),
        "near_field_points": int(parameters["near_field"]["x_count"])
        * int(parameters["near_field"]["y_count"]),
        "far_field_angles": int(parameters["far_field_angular_samples"]),
        "in_process_workers": workers,
        "geometry": metrics,
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_arrays_used": False,
        "parameter_contract_kind": parameter_contract["kind"],
        "fig5_observable_estimator": observable_contract["T001"]["estimator"],
        "paper_exact_eligible_after_acceptance": False,
        "publication_variant_eligible_after_acceptance": (
            payload.get("execution_scale") != "smoke"
        ),
        "publication_source_discrepancy": publication_resolution["status"],
        "author_private_mesh_identity_claimed": False,
    }


def _checkpoint_metadata(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with np.load(path, allow_pickle=False) as data:
            return json.loads(str(data["metadata_json"].item()))
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None


def _scan_stage(
    root: Path,
    mesh: BoundaryMesh,
    payload: dict[str, Any],
    digest: str,
    shard_index: int,
    shard_count: int,
) -> None:
    parameters = payload["parameters"]
    wave_numbers = _wave_numbers(parameters)
    checkpoint_dir = root / "checkpoints" / "scan"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for index, wave_number in enumerate(wave_numbers):
        if index % shard_count != shard_index:
            continue
        checkpoint = checkpoint_dir / f"point_{index:05d}.json"
        if checkpoint.is_file():
            try:
                existing = json.loads(checkpoint.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
            if existing.get("config_sha256") == digest and np.isclose(
                existing.get("kR", np.nan), wave_number, atol=1e-13, rtol=0
            ):
                continue
        result = cross_section(
            mesh,
            float(wave_number),
            incidence_angle=np.deg2rad(float(parameters["incidence_angle_degrees"])),
            angular_samples=int(parameters["scan"]["angular_samples"]),
            n_inside=float(parameters["n_inside"]),
            quadrature_order=int(parameters["quadrature_order"]),
        )
        _atomic_json(
            checkpoint,
            {
                "schema_version": 1,
                "config_sha256": digest,
                "index": index,
                "kR": float(wave_number),
                "sigma": float(result["sigma_optical"]),
                "sigma_integrated": float(result["sigma_integrated"]),
                "sigma_optical": float(result["sigma_optical"]),
                "optical_relative_error": float(result["optical_relative_error"]),
                "linear_residual": float(result["relative_residual"]),
            },
        )


def _resonance_stage(root: Path, payload: dict[str, Any], digest: str) -> None:
    parameters = payload["parameters"]
    resonance_k = complex(*map(float, parameters["resonance"]["reported_kR"]))
    checkpoint_dir = root / "checkpoints" / "resonance"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for row in parameters["resonance"]["convergence_meshes"]:
        total = int(row["total_boundary_elements"])
        checkpoint = checkpoint_dir / f"state_N{total:04d}.npz"
        metadata = _checkpoint_metadata(checkpoint)
        if (
            metadata
            and metadata.get("config_sha256") == digest
            and metadata.get("boundary_elements") == total
            and np.isclose(metadata.get("kR_real", np.nan), resonance_k.real)
            and np.isclose(metadata.get("kR_imag", np.nan), resonance_k.imag)
        ):
            continue
        mesh = _convergence_mesh(parameters, row)
        state = resonance_boundary_state(
            mesh,
            resonance_k,
            n_inside=float(parameters["n_inside"]),
            n_outside=float(parameters["n_outside"]),
            quadrature_order=int(parameters["quadrature_order"]),
        )
        metadata = {
            "schema_version": 1,
            "config_sha256": digest,
            "boundary_elements": mesh.size,
            "kR_real": resonance_k.real,
            "kR_imag": resonance_k.imag,
            "smallest_singular": float(state["smallest_singular"]),
            "relative_residual": float(state["relative_residual"]),
            "resolution_b": resolution_metric(
                mesh, resonance_k, float(parameters["n_inside"])
            ),
        }
        _atomic_npz(
            checkpoint,
            metadata_json=np.array(json.dumps(metadata, sort_keys=True)),
            phi=state["phi"],
            psi=state["psi"],
        )


def _final_boundary_state(
    root: Path, payload: dict[str, Any], digest: str
) -> tuple[np.ndarray, np.ndarray]:
    total = int(payload["parameters"]["total_boundary_elements"])
    checkpoint = root / "checkpoints" / "resonance" / f"state_N{total:04d}.npz"
    metadata = _checkpoint_metadata(checkpoint)
    if (
        not metadata
        or metadata.get("config_sha256") != digest
        or metadata.get("boundary_elements") != total
    ):
        raise RuntimeError(
            "final resonance checkpoint is missing or stale; run --stage resonance"
        )
    with np.load(checkpoint, allow_pickle=False) as data:
        return np.array(data["phi"]), np.array(data["psi"])


def _near_field_stage(
    root: Path,
    mesh: BoundaryMesh,
    payload: dict[str, Any],
    digest: str,
    shard_index: int,
    shard_count: int,
) -> None:
    parameters = payload["parameters"]
    phi, psi = _final_boundary_state(root, payload, digest)
    resonance_k = complex(*map(float, parameters["resonance"]["reported_kR"]))
    field = parameters["near_field"]
    x = np.linspace(float(field["x_min"]), float(field["x_max"]), int(field["x_count"]))
    y = np.linspace(float(field["y_min"]), float(field["y_max"]), int(field["y_count"]))
    checkpoint_dir = root / "checkpoints" / "near_field"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for index, y_value in enumerate(y):
        if index % shard_count != shard_index:
            continue
        checkpoint = checkpoint_dir / f"row_{index:05d}.npz"
        metadata = _checkpoint_metadata(checkpoint)
        if (
            metadata
            and metadata.get("config_sha256") == digest
            and metadata.get("row_index") == index
            and np.isclose(metadata.get("y_R", np.nan), y_value)
        ):
            continue
        points = np.column_stack((x, np.full_like(x, y_value)))
        values = reconstruct_field(
            mesh,
            resonance_k,
            phi,
            psi,
            points,
            n_inside=float(parameters["n_inside"]),
            n_outside=float(parameters["n_outside"]),
            quadrature_order=int(parameters["quadrature_order"]),
        )
        metadata = {
            "schema_version": 1,
            "config_sha256": digest,
            "row_index": index,
            "y_R": float(y_value),
        }
        _atomic_npz(
            checkpoint,
            metadata_json=np.array(json.dumps(metadata, sort_keys=True)),
            intensity=np.abs(values) ** 2,
        )


def _far_field_stage(
    root: Path,
    mesh: BoundaryMesh,
    payload: dict[str, Any],
    digest: str,
) -> None:
    parameters = payload["parameters"]
    checkpoint = root / "checkpoints" / "far_field.npz"
    metadata = _checkpoint_metadata(checkpoint)
    if (
        metadata
        and metadata.get("config_sha256") == digest
        and metadata.get("angular_samples")
        == int(parameters["far_field_angular_samples"])
    ):
        return
    phi, psi = _final_boundary_state(root, payload, digest)
    resonance_k = complex(*map(float, parameters["resonance"]["reported_kR"]))
    angles = np.linspace(
        0,
        2 * np.pi,
        int(parameters["far_field_angular_samples"]),
        endpoint=False,
    )
    amplitude = far_field(
        mesh,
        resonance_k,
        phi,
        psi,
        angles,
        quadrature_order=int(parameters["quadrature_order"]),
    )
    metadata = {
        "schema_version": 1,
        "config_sha256": digest,
        "angular_samples": angles.size,
    }
    _atomic_npz(
        checkpoint,
        metadata_json=np.array(json.dumps(metadata, sort_keys=True)),
        angles=angles,
        intensity=np.abs(amplitude) ** 2,
    )


def _read_json_checkpoints(paths: list[Path], digest: str) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"required checkpoint is missing: {path}")
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("config_sha256") != digest:
            raise RuntimeError(f"required checkpoint is stale: {path}")
        rows.append(row)
    return rows


def _acceptance(
    payload: dict[str, Any],
    mesh: BoundaryMesh,
    scan_rows: list[dict[str, Any]],
    convergence: list[dict[str, Any]],
    near_intensity: np.ndarray,
    far_intensity: np.ndarray,
) -> dict[str, Any]:
    parameters = payload["parameters"]
    smoke = payload.get("execution_scale") == "smoke"
    thresholds = payload["acceptance"]
    metrics = _geometry_metrics(mesh, parameters)
    residuals = np.array([row["linear_residual"] for row in scan_rows])
    optical_errors = np.array([row["optical_relative_error"] for row in scan_rows])
    sigma = np.array([row["sigma"] for row in scan_rows])
    far_normalized = far_intensity / max(
        float(np.max(far_intensity)), np.finfo(float).tiny
    )
    half_turn_error = float(
        np.max(
            np.abs(far_normalized - np.roll(far_normalized, far_normalized.size // 2))
        )
    )
    reported_real = float(parameters["resonance"]["reported_kR"][0])
    grid_distance = min(abs(row["kR"] - reported_real) for row in scan_rows)
    wave_numbers = np.array([row["kR"] for row in scan_rows])
    scan_max_spacing = float(np.max(np.diff(wave_numbers)))
    criteria = {
        "checkpoint_coverage_complete": len(scan_rows)
        == _wave_numbers(parameters).size,
        "all_outputs_finite": bool(
            np.all(np.isfinite(sigma))
            and np.all(np.isfinite(near_intensity))
            and np.all(np.isfinite(far_intensity))
        ),
        "cross_section_nonnegative": bool(np.all(sigma >= 0)),
        "linear_residual": float(np.max(residuals))
        <= float(thresholds["linear_residual_max"]),
        "reported_resonance_sampled": grid_distance
        <= float(thresholds["reported_resonance_grid_distance_max"]),
        "fig5_observable_is_optical_theorem": (
            payload["observable_contract"]["T001"]["estimator"]
            == "optical_theorem"
        ),
        "near_field_nonzero": float(np.max(near_intensity)) > 0,
        "far_field_nonzero": float(np.max(far_intensity)) > 0,
    }
    if not smoke:
        rho_delta_target = float(thresholds["rho_over_delta_target"])
        rho_lambda_target = float(thresholds["rho_over_lambda_target"])
        criteria.update(
            {
                "published_boundary_count": mesh.size
                == int(parameters["total_boundary_elements"])
                == 1600,
                "published_matrix_dimension": 2 * mesh.size == 3200,
                "scan_resolution": scan_max_spacing
                <= float(thresholds["scan_max_spacing_max"]),
                "resolution_b": float(metrics["resolution_b"])
                >= float(thresholds["resolution_b_min"]),
                "rounding_rho_over_delta": abs(
                    float(metrics["rho_over_max_corner_element"]) - rho_delta_target
                )
                / rho_delta_target
                <= float(thresholds["rounding_relative_tolerance"]),
                "rounding_rho_over_lambda": abs(
                    float(metrics["rho_over_local_wavelength"]) - rho_lambda_target
                )
                / rho_lambda_target
                <= float(thresholds["rounding_relative_tolerance"]),
                "optical_theorem_median": float(np.median(optical_errors))
                <= float(thresholds["optical_relative_error_median_max"]),
                "resonance_residual": float(convergence[-1]["relative_residual"])
                <= float(thresholds["resonance_relative_residual_max"]),
                "resonance_mesh_trend": float(convergence[-1]["smallest_singular"])
                < float(convergence[0]["smallest_singular"]),
                "far_field_pi_symmetry": half_turn_error
                <= float(thresholds["far_field_pi_symmetry_max"]),
            }
        )
    all_passed = all(criteria.values())
    publication_resolution = payload["publication_parameter_resolution"]
    source_discrepancy = publication_resolution["status"] == "source_discrepancy"
    publication_variant_exact = not smoke and all_passed
    paper_exact = publication_variant_exact and not source_discrepancy
    if not all_passed:
        status = "failed"
    elif smoke:
        status = "passed_smoke"
    elif source_discrepancy:
        status = "passed_with_source_discrepancy"
    else:
        status = "passed"
    failed_criteria = sorted(name for name, passed in criteria.items() if not passed)
    if paper_exact:
        paper_exact_blocker = None
    elif smoke:
        paper_exact_blocker = "smoke run intentionally overrides the paper-scale representative"
    elif publication_variant_exact and source_discrepancy:
        paper_exact_blocker = (
            "publication source conflict: prose gives displacement (1.8R,+0.5R), "
            "while Figure 4 defines (1.8R,-0.5R)"
        )
    else:
        paper_exact_blocker = (
            "published parameter/science contract failed: " + ", ".join(failed_criteria)
        )
    return {
        "schema_version": 1,
        "status": status,
        "execution_scale": "smoke" if smoke else "paper_scale",
        "paper_exact": paper_exact,
        "paper_exact_basis": payload["parameter_contract"]["kind"],
        "discretization_contract_exact": publication_variant_exact,
        "publication_variant_exact": publication_variant_exact,
        "publication_variant_basis": "figure_4_geometry",
        "publication_source_discrepancy": source_discrepancy,
        "publication_parameter_resolution": publication_resolution,
        "author_private_mesh_identity_claimed": False,
        "paper_exact_blocker": paper_exact_blocker,
        "criteria": criteria,
        "metrics": {
            **metrics,
            "linear_residual_max": float(np.max(residuals)),
            "optical_relative_error_median": float(np.median(optical_errors)),
            "optical_relative_error_max": float(np.max(optical_errors)),
            "reported_resonance_grid_distance": float(grid_distance),
            "scan_max_spacing": scan_max_spacing,
            "resonance_smallest_singular_by_mesh": [
                float(row["smallest_singular"]) for row in convergence
            ],
            "resonance_relative_residual": float(convergence[-1]["relative_residual"]),
            "far_field_pi_symmetry_max": half_turn_error,
        },
    }


def _aggregate(
    root: Path,
    mesh: BoundaryMesh,
    payload: dict[str, Any],
    digest: str,
    *,
    render: bool,
    started: float,
) -> dict[str, Any]:
    parameters = payload["parameters"]
    wave_numbers = _wave_numbers(parameters)
    scan_paths = [
        root / "checkpoints" / "scan" / f"point_{index:05d}.json"
        for index in range(wave_numbers.size)
    ]
    scan_rows = _read_json_checkpoints(scan_paths, digest)
    near = parameters["near_field"]
    near_paths = [
        root / "checkpoints" / "near_field" / f"row_{index:05d}.npz"
        for index in range(int(near["y_count"]))
    ]
    near_rows = []
    near_y = np.linspace(
        float(near["y_min"]), float(near["y_max"]), int(near["y_count"])
    )
    for index, path in enumerate(near_paths):
        metadata = _checkpoint_metadata(path)
        if (
            not metadata
            or metadata.get("config_sha256") != digest
            or metadata.get("row_index") != index
            or not np.isclose(metadata.get("y_R", np.nan), near_y[index])
        ):
            raise RuntimeError(
                f"required near-field checkpoint is missing or stale: {path}"
            )
        with np.load(path, allow_pickle=False) as data:
            near_rows.append(np.array(data["intensity"]))
    near_intensity = np.vstack(near_rows)
    far_path = root / "checkpoints" / "far_field.npz"
    metadata = _checkpoint_metadata(far_path)
    if (
        not metadata
        or metadata.get("config_sha256") != digest
        or metadata.get("angular_samples")
        != int(parameters["far_field_angular_samples"])
    ):
        raise RuntimeError("far-field checkpoint is missing or stale")
    with np.load(far_path, allow_pickle=False) as data:
        far_angles = np.array(data["angles"])
        far_intensity = np.array(data["intensity"])
    convergence = []
    for row in parameters["resonance"]["convergence_meshes"]:
        total = int(row["total_boundary_elements"])
        path = root / "checkpoints" / "resonance" / f"state_N{total:04d}.npz"
        row_metadata = _checkpoint_metadata(path)
        if (
            not row_metadata
            or row_metadata.get("config_sha256") != digest
            or row_metadata.get("boundary_elements") != total
        ):
            raise RuntimeError(f"resonance checkpoint is missing or stale: {path}")
        convergence.append(row_metadata)
    phi, psi = _final_boundary_state(root, payload, digest)
    x = np.linspace(float(near["x_min"]), float(near["x_max"]), int(near["x_count"]))
    y = np.linspace(float(near["y_min"]), float(near["y_max"]), int(near["y_count"]))
    near_normalized = near_intensity / max(
        float(np.max(near_intensity)), np.finfo(float).tiny
    )
    far_normalized = far_intensity / max(
        float(np.max(far_intensity)), np.finfo(float).tiny
    )
    data_dir = root / "data"
    checks_dir = root / "checks"
    figures_dir = root / "figures"
    data_path = data_dir / "bem_paper_scale.npz"
    _atomic_npz(
        data_path,
        scan_k=np.array([row["kR"] for row in scan_rows]),
        scan_sigma=np.array([row["sigma"] for row in scan_rows]),
        scan_sigma_integrated=np.array([row["sigma_integrated"] for row in scan_rows]),
        scan_sigma_optical=np.array([row["sigma_optical"] for row in scan_rows]),
        scan_optical_relative_error=np.array(
            [row["optical_relative_error"] for row in scan_rows]
        ),
        scan_linear_residual=np.array([row["linear_residual"] for row in scan_rows]),
        resonance_k=np.asarray(parameters["resonance"]["reported_kR"], dtype=float),
        mesh_start=mesh.start,
        mesh_end=mesh.end,
        mesh_midpoint=mesh.midpoint,
        mesh_normal=mesh.normal,
        mesh_cavity=mesh.cavity,
        boundary_phi=phi,
        boundary_psi=psi,
        near_x=x,
        near_y=y,
        near_intensity=near_normalized,
        far_angle=far_angles,
        far_intensity=far_normalized,
    )
    acceptance = _acceptance(
        payload, mesh, scan_rows, convergence, near_intensity, far_intensity
    )
    summary = {
        "schema_version": 1,
        "paper_id": "physics-0206018",
        "campaign_id": payload["campaign_id"],
        "config_sha256": digest,
        "execution_scale": payload.get("execution_scale", "paper_scale"),
        "parameter_match": (
            "reduced_scale_smoke"
            if payload.get("execution_scale") == "smoke"
            else "paper_exact"
            if acceptance["paper_exact"]
            else "paper_subset"
        ),
        "paper_exact": acceptance["paper_exact"],
        "paper_exact_basis": acceptance["paper_exact_basis"],
        "discretization_contract_exact": acceptance[
            "discretization_contract_exact"
        ],
        "publication_variant_exact": acceptance["publication_variant_exact"],
        "publication_variant_basis": acceptance["publication_variant_basis"],
        "publication_source_discrepancy": acceptance[
            "publication_source_discrepancy"
        ],
        "author_private_mesh_identity_claimed": False,
        "paper_exact_blocker": acceptance["paper_exact_blocker"],
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_arrays_used": False,
        "runtime_seconds": time.monotonic() - started,
        "parameters": parameters,
        "observable_contract": payload["observable_contract"],
        "geometry": _geometry_metrics(mesh, parameters),
        "convergence": convergence,
    }
    _atomic_json(data_dir / "bem_paper_scale_summary.json", summary)
    _atomic_json(checks_dir / "acceptance.json", acceptance)
    if render:
        # Rendering is deliberately imported only in the post-freeze display
        # path.  The isolated numerical contract uses --no-render, so
        # Matplotlib/font discovery never enters the scientific runner.
        from scripts.render_figures import render_figures

        render_figures(data_path, figures_dir)
    code_paths = [
        WORKSPACE / "scripts" / "run_paper_scale.py",
        WORKSPACE / "src" / "bem.py",
        WORKSPACE / "src" / "paper_scale.py",
    ]
    if render:
        code_paths.append(WORKSPACE / "scripts" / "render_figures.py")
    output_paths = [
        data_path,
        data_dir / "bem_paper_scale_summary.json",
        checks_dir / "acceptance.json",
    ]
    if render:
        output_paths.extend(
            figures_dir / name
            for name in (
                "fig5_cross_section.png",
                "fig6_near_field.png",
                "fig7_far_field.png",
            )
        )
    manifest = {
        "schema_version": 1,
        "campaign_id": payload["campaign_id"],
        "config_sha256": digest,
        "code_sha256": {
            str(path.relative_to(WORKSPACE)): _file_hash(path) for path in code_paths
        },
        "outputs_sha256": {
            str(path.relative_to(root)): _file_hash(path) for path in output_paths
        },
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_arrays_used": False,
    }
    _atomic_json(checks_dir / "manifest.json", manifest)
    if acceptance["status"] == "failed":
        campaign_status = "failed"
    elif payload.get("execution_scale") == "smoke":
        campaign_status = "smoke_complete"
    elif acceptance["publication_source_discrepancy"]:
        campaign_status = "paper_scale_complete_source_discrepancy"
    else:
        campaign_status = "paper_scale_complete_paper_contract"
    state = {
        "schema_version": 1,
        "status": campaign_status,
        "execution_scale": payload.get("execution_scale", "paper_scale"),
        "scan_checkpoints": len(scan_rows),
        "near_field_checkpoints": len(near_rows),
        "resonance_checkpoints": len(convergence),
        "acceptance_status": acceptance["status"],
        "paper_exact": acceptance["paper_exact"],
        "paper_exact_basis": acceptance["paper_exact_basis"],
        "discretization_contract_exact": acceptance[
            "discretization_contract_exact"
        ],
        "publication_variant_exact": acceptance["publication_variant_exact"],
        "publication_source_discrepancy": acceptance[
            "publication_source_discrepancy"
        ],
    }
    _atomic_json(checks_dir / "campaign_state.json", state)
    return {"summary": summary, "acceptance": acceptance, "state": state}


def _root(payload: dict[str, Any], override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return (WORKSPACE / str(payload["output_root"])).resolve()


def _run_in_process_shards(
    stage: str,
    root: Path,
    mesh: BoundaryMesh,
    payload: dict[str, Any],
    digest: str,
) -> None:
    """Parallelize independent work without violating the no-child-process runner."""

    workers = int(payload.get("sharding", {}).get("in_process_workers", 1))
    function = _scan_stage if stage == "scan" else _near_field_stage
    if workers == 1:
        function(root, mesh, payload, digest, 0, 1)
        return
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(function, root, mesh, payload, digest, index, workers)
            for index in range(workers)
        ]
        for future in futures:
            future.result()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--stage", choices=STAGES, default="all")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--output-root")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        parser.error("shard-index must be in [0, shard-count)")
    if args.stage == "all" and args.shard_count != 1:
        parser.error(
            "stage=all is serial; shard scan and near-field as separate stages"
        )

    source = Path(args.config)
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve()
    payload = _load_config(source)
    validation = validate_config(payload)
    if args.validate_only:
        print(json.dumps(validation, indent=2, ensure_ascii=False))
        return 0
    if args.smoke:
        payload = _smoke_config(payload)
        validation = validate_config(payload)
    digest = _json_hash(payload)
    root = _root(payload, args.output_root)
    root.mkdir(parents=True, exist_ok=True)
    mesh = _mesh(payload["parameters"])
    started = time.monotonic()

    if args.stage == "all":
        _run_in_process_shards("scan", root, mesh, payload, digest)
    elif args.stage == "scan":
        _scan_stage(root, mesh, payload, digest, args.shard_index, args.shard_count)
    if args.stage in {"all", "resonance"}:
        _resonance_stage(root, payload, digest)
    if args.stage == "all":
        _run_in_process_shards("near-field", root, mesh, payload, digest)
    elif args.stage == "near-field":
        _near_field_stage(
            root, mesh, payload, digest, args.shard_index, args.shard_count
        )
    if args.stage in {"all", "far-field"}:
        _far_field_stage(root, mesh, payload, digest)
    result: dict[str, Any] = {"validation": validation}
    if args.stage in {"all", "aggregate"}:
        result.update(
            _aggregate(
                root,
                mesh,
                payload,
                digest,
                render=not args.no_render,
                started=started,
            )
        )
    else:
        result["stage"] = args.stage
        result["shard_index"] = args.shard_index
        result["shard_count"] = args.shard_count
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
