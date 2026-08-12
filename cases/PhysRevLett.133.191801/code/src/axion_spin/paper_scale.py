"""Fail-closed paper-scale input inventory and resumable analysis plan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import qmc

from .axion import finite_volume_kernel
from .campaign import (
    PAPER_ID,
    atomic_json,
    canonical_json,
    sha256_bytes,
    sha256_file,
    write_csv,
)
from .experimental import analyze_segment_bundle, read_calibration_table
from .signals import resonant_free_decay_response


class MissingInputsError(RuntimeError):
    def __init__(self, missing: list[str]):
        super().__init__(f"missing indispensable paper-scale inputs: {missing}")
        self.missing = missing


def load_paper_scale_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("paper_id") != PAPER_ID:
        raise ValueError("paper-scale config schema or paper_id mismatch")
    if config.get("profile") != "paper_scale":
        raise ValueError("paper-scale runner requires profile=paper_scale")
    if not config.get("required_inputs"):
        raise ValueError("paper-scale config must declare required_inputs")
    return config


def input_inventory(config: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    records = []
    missing = []
    for item in config["required_inputs"]:
        relative = Path(str(item["path"]))
        path = workspace / relative
        record = {
            "path": relative.as_posix(),
            "role": str(item["role"]),
            "exists": path.is_file(),
            "sha256": sha256_file(path) if path.is_file() else None,
            "expected_sha256": item.get("sha256"),
        }
        if not path.is_file():
            missing.append(relative.as_posix())
        elif item.get("sha256") and record["sha256"] != item["sha256"]:
            record["hash_matches"] = False
            missing.append(f"{relative.as_posix()}#sha256-mismatch")
        else:
            record["hash_matches"] = True
        records.append(record)
    return {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "status": "ready" if not missing else "blocked_missing_inputs",
        "missing": missing,
        "inputs": records,
    }


def build_plan(config: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    inventory = input_inventory(config, workspace=workspace)
    plan = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": "paper_scale",
        "status": inventory["status"],
        "input_inventory": inventory,
        "stages": [
            {
                "id": "inventory",
                "checkpoint": "outputs/checks/paper_scale/input_inventory.json",
            },
            {
                "id": "calibration",
                "checkpoint": "outputs/checkpoints/paper_scale/calibration.json",
            },
            {
                "id": "segment_filtering",
                "checkpoint": "outputs/checkpoints/paper_scale/segments.jsonl",
            },
            {
                "id": "dataset_aggregation",
                "checkpoint": "outputs/data/paper_scale/dataset_estimates.csv",
            },
            {
                "id": "finite_geometry",
                "checkpoint": "outputs/checkpoints/paper_scale/geometry.jsonl",
            },
            {
                "id": "constraint",
                "checkpoint": "outputs/data/paper_scale/constraint_curve.csv",
            },
            {
                "id": "acceptance",
                "checkpoint": "outputs/checks/paper_scale/target_acceptance.json",
            },
        ],
        "resume": True,
        "source_pixels_allowed": False,
        "author_code_allowed": False,
    }
    check_root = workspace / "outputs" / "checks" / "paper_scale"
    atomic_json(check_root / "input_inventory.json", inventory)
    atomic_json(check_root / "plan.json", plan)
    return plan


def require_inputs(plan: dict[str, Any]) -> None:
    missing = list(plan["input_inventory"]["missing"])
    if missing:
        raise MissingInputsError(missing)


def _safe_input_path(workspace: Path, relative: str) -> Path:
    inputs = (workspace / "inputs").resolve()
    path = (workspace / relative).resolve()
    if inputs not in path.parents:
        raise ValueError(f"paper-scale input escapes inputs: {relative}")
    return path


def _sample_cylinder(
    unit: np.ndarray,
    *,
    center_m: np.ndarray,
    radius_m: float,
    length_m: float,
) -> np.ndarray:
    if unit.ndim != 2 or unit.shape[1] != 3:
        raise ValueError("unit cylinder samples must have shape (N, 3)")
    if radius_m <= 0 or length_m <= 0 or center_m.shape != (3,):
        raise ValueError("cylinder geometry is invalid")
    radial = radius_m * np.sqrt(unit[:, 0])
    angle = 2.0 * np.pi * unit[:, 1]
    axial = length_m * (unit[:, 2] - 0.5)
    local = np.column_stack((radial * np.cos(angle), radial * np.sin(angle), axial))
    return local + center_m


def _geometry_points(geometry: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    sample_count = int(geometry["paired_qmc_samples"])
    if sample_count < 1024 or sample_count & (sample_count - 1):
        raise ValueError("paired_qmc_samples must be a power of two and at least 1024")
    engine = qmc.Sobol(d=6, scramble=True, seed=int(geometry["seed"]))
    unit = engine.random_base2(int(np.log2(sample_count)))
    source_spec = geometry["source_cylinder"]
    sensor_spec = geometry["sensor_cylinder"]
    source = _sample_cylinder(
        unit[:, :3],
        center_m=np.asarray(source_spec["center_m"], dtype=float),
        radius_m=float(source_spec["radius_m"]),
        length_m=float(source_spec["length_m"]),
    )
    sensor = _sample_cylinder(
        unit[:, 3:],
        center_m=np.asarray(sensor_spec["center_m"], dtype=float),
        radius_m=float(sensor_spec["radius_m"]),
        length_m=float(sensor_spec["length_m"]),
    )
    return source, sensor


def _load_segment_manifest(path: Path, *, workspace: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("segment manifest requires a nonempty datasets list")
    seen: set[str] = set()
    for item in datasets:
        dataset_id = str(item["dataset_id"])
        if dataset_id in seen:
            raise ValueError(f"duplicate dataset_id: {dataset_id}")
        seen.add(dataset_id)
        bundle = _safe_input_path(workspace, str(item["path"]))
        if not bundle.is_file() or sha256_file(bundle) != str(item["sha256"]):
            raise ValueError(f"dataset bundle missing or hash mismatch: {dataset_id}")
    return manifest


def execute_paper_scale(
    config: dict[str, Any],
    *,
    workspace: Path,
    resume: bool,
) -> dict[str, Any]:
    """Execute the complete reanalysis when every indispensable input exists."""

    plan = build_plan(config, workspace=workspace)
    require_inputs(plan)
    inputs = {
        str(item["role"]): _safe_input_path(workspace, str(item["path"]))
        for item in config["required_inputs"]
    }
    calibration_rows = []
    for role in ("temperature_calibration", "power_calibration"):
        for row in read_calibration_table(inputs[role]):
            calibration_rows.append({"scan_kind": role, **row})
    write_csv(
        workspace / "outputs" / "data" / "paper_scale" / "calibration_summary.csv",
        ["scan_kind", "scan_value", "polarized_xe", "coherence_s"],
        calibration_rows,
    )

    sensor = config["sensor"]
    source = config["source"]
    dt = float(config["segment_analysis"]["dt_s"])
    template_duration = float(config["segment_analysis"]["template_duration_s"])
    template_time = np.arange(0.0, template_duration + 0.5 * dt, dt)
    template = resonant_free_decay_response(
        template_time,
        amplitude=1.0,
        amplification=float(sensor["amplification"]),
        sensor_coherence_s=float(sensor["coherence_s"]),
        source_coherence_s=float(source["coherence_s"]),
        frequency_hz=float(sensor["resonance_hz"]),
        phase_rad=float(source["phase_rad"]),
    )
    template /= np.max(np.abs(template))
    template_sha = sha256_bytes(
        template.tobytes()
        + canonical_json(
            {
                "sensor": sensor,
                "source": source,
                "segment_analysis": config["segment_analysis"],
            }
        ).encode("utf-8")
    )
    segment_manifest = _load_segment_manifest(
        inputs["segment_manifest"], workspace=workspace
    )
    dataset_records = []
    checkpoint_root = workspace / "outputs" / "checkpoints" / "paper_scale" / "datasets"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    for item in segment_manifest["datasets"]:
        dataset_id = str(item["dataset_id"])
        bundle = _safe_input_path(workspace, str(item["path"]))
        checkpoint = checkpoint_root / f"{dataset_id}.json"
        record: dict[str, Any]
        if resume and checkpoint.is_file():
            candidate = json.loads(checkpoint.read_text(encoding="utf-8"))
            if (
                candidate.get("input_sha256") == item["sha256"]
                and candidate.get("template_manifest_sha256") == template_sha
            ):
                record = candidate
            else:
                record = {}
        else:
            record = {}
        if not record:
            result = analyze_segment_bundle(
                bundle,
                template=template,
                expected_lag=int(config["segment_analysis"]["expected_lag_samples"]),
            )
            record = {
                "dataset_id": dataset_id,
                "input_sha256": item["sha256"],
                "template_manifest_sha256": template_sha,
                "segment_count": result["segment_count"],
                "mean": result["mean"],
                "sample_standard_deviation": result["sample_standard_deviation"],
                "standard_error": result["standard_error"],
            }
            atomic_json(checkpoint, record)
        dataset_records.append(record)
    write_csv(
        workspace / "outputs" / "data" / "paper_scale" / "dataset_estimates.csv",
        [
            "dataset_id",
            "input_sha256",
            "segment_count",
            "mean",
            "sample_standard_deviation",
            "standard_error",
        ],
        dataset_records,
    )

    geometry = json.loads(inputs["finite_cell_geometry"].read_text(encoding="utf-8"))
    source_points, sensor_points = _geometry_points(geometry)
    constraint = config["constraint"]
    masses_microev = np.geomspace(
        float(constraint["mass_min_microeV"]),
        float(constraint["mass_max_microeV"]),
        int(constraint["mass_points"]),
    )
    masses_ev = masses_microev * 1e-6
    kernel = finite_volume_kernel(
        masses_ev,
        source_points,
        sensor_points,
        sensor_spin=geometry.get("sensor_spin", [1.0, 0.0, 0.0]),
        source_spin=geometry.get("source_spin", [1.0, 0.0, 0.0]),
        block_size=int(geometry.get("block_size", 16384)),
    )
    anchor_mass = float(constraint["anchor_mass_microeV"])
    anchor_kernel = float(
        finite_volume_kernel(
            np.array([anchor_mass * 1e-6]),
            source_points,
            sensor_points,
            sensor_spin=geometry.get("sensor_spin", [1.0, 0.0, 0.0]),
            source_spin=geometry.get("source_spin", [1.0, 0.0, 0.0]),
        )[0]
    )
    coupling = (
        float(constraint["anchor_coupling_product_over_four"]) * anchor_kernel / kernel
    )
    write_csv(
        workspace / "outputs" / "data" / "paper_scale" / "constraint_curve.csv",
        ["axion_mass_microeV", "finite_volume_kernel", "g_nps_squared_over_4"],
        (
            {
                "axion_mass_microeV": float(mass),
                "finite_volume_kernel": float(value),
                "g_nps_squared_over_4": float(limit),
            }
            for mass, value, limit in zip(masses_microev, kernel, coupling)
        ),
    )
    segment_count = sum(int(item["segment_count"]) for item in dataset_records)
    acceptance = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "status": (
            "passed"
            if len(dataset_records) == int(config["expected_dataset_count"])
            and segment_count == int(config["expected_segment_count"])
            else "failed"
        ),
        "dataset_count": len(dataset_records),
        "segment_count": segment_count,
        "finite_geometry_samples": int(source_points.shape[0]),
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
    }
    atomic_json(
        workspace / "outputs" / "checks" / "paper_scale" / "target_acceptance.json",
        acceptance,
    )
    return acceptance
