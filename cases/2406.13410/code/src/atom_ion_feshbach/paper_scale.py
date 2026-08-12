"""Hash-bound, resumable paper-scale campaign for all 17 targets."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from .reproduction import run as run_reproduction
from .torch_backend import resolve_backend, simulate_collision_shard


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _write_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _implementation_digest(workspace: Path) -> str:
    files = [
        workspace / "src/atom_ion_feshbach/md.py",
        workspace / "src/atom_ion_feshbach/torch_backend.py",
        workspace / "src/atom_ion_feshbach/paper_scale.py",
        workspace / "src/atom_ion_feshbach/reproduction.py",
        workspace / "src/atom_ion_feshbach/polarization.py",
        workspace / "src/atom_ion_feshbach/recombination.py",
    ]
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(workspace)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _campaign_roots(workspace: Path, campaign: dict[str, Any]) -> tuple[Path, Path]:
    data_root = (workspace / str(campaign["data_root"])).resolve()
    checks_root = (workspace / str(campaign["checks_root"])).resolve()
    for root, expected in (
        (data_root, ("outputs", "data")),
        (checks_root, ("outputs", "checks")),
    ):
        if (
            workspace not in root.parents
            or root.relative_to(workspace).parts[:2] != expected
        ):
            raise ValueError(
                "campaign roots must stay under outputs/data or outputs/checks"
            )
    return data_root, checks_root


def load_campaign(
    config_path: Path, workspace: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2406.13410":
        raise ValueError("config paper_id mismatch")
    campaign = config.get("campaign")
    parameters = config.get("parameters")
    if not isinstance(campaign, dict) or not isinstance(parameters, dict):
        raise ValueError("paper-scale config requires campaign and parameters objects")
    shards = int(campaign["shards"])
    per_shard = int(campaign["trajectories_per_shard"])
    if shards < 1 or per_shard < 128:
        raise ValueError("campaign needs at least one shard and 128 trajectories/shard")
    expected_total = shards * per_shard
    if int(parameters["md"]["trajectories"]) != expected_total:
        raise ValueError("md.trajectories must equal shards*trajectories_per_shard")
    data_root, _ = _campaign_roots(workspace, campaign)
    expected_precomputed = data_root / "aggregated/md_velocity_samples.npz"
    actual_precomputed = (
        workspace / str(parameters["md"]["precomputed_velocity_npz"])
    ).resolve()
    if actual_precomputed != expected_precomputed:
        raise ValueError(
            "precomputed_velocity_npz must name campaign aggregated artifact"
        )
    return config, campaign


def build_plan(config_path: Path, workspace: Path) -> dict[str, Any]:
    config, campaign = load_campaign(config_path, workspace)
    fields = config["parameters"]["md"]["fields_v_m"]
    plan = {
        "schema_version": 1,
        "paper_id": "2406.13410",
        "execution_profile": config["execution_profile"],
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _implementation_digest(workspace),
        "shards": int(campaign["shards"]),
        "trajectories_per_shard": int(campaign["trajectories_per_shard"]),
        "total_trajectories_per_field": int(campaign["shards"])
        * int(campaign["trajectories_per_shard"]),
        "fields": fields,
        "collision_updates": int(campaign["shards"])
        * int(campaign["trajectories_per_shard"])
        * len(fields)
        * int(config["parameters"]["md"]["collisions"]),
        "target_ids": [f"T{index:03d}" for index in range(1, 18)],
        "work_units": [
            {
                "shard_id": shard_id,
                "seeds": [
                    int(config["parameters"]["md"]["seed_base"])
                    + shard_id * int(campaign["shard_seed_stride"])
                    + field_index * int(campaign["field_seed_stride"])
                    for field_index in range(len(fields))
                ],
            }
            for shard_id in range(int(campaign["shards"]))
        ],
        "acceptance": campaign["acceptance"],
    }
    _, checks_root = _campaign_roots(workspace, campaign)
    _write_json(checks_root / "plan.json", plan)
    return plan


def run_shard(
    config_path: Path,
    workspace: Path,
    *,
    shard_id: int,
    backend: str,
    resume: bool,
) -> dict[str, Any]:
    config, campaign = load_campaign(config_path, workspace)
    plan = build_plan(config_path, workspace)
    if not 0 <= shard_id < int(campaign["shards"]):
        raise ValueError("shard_id outside campaign")
    data_root, checks_root = _campaign_roots(workspace, campaign)
    data_path = data_root / "shards" / f"shard_{shard_id:04d}.npz"
    record_path = checks_root / "shards" / f"shard_{shard_id:04d}.json"
    if resume and data_path.is_file() and record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if (
            record.get("config_sha256") == plan["config_sha256"]
            and record.get("implementation_sha256") == plan["implementation_sha256"]
            and record.get("output_sha256") == _sha256(data_path)
        ):
            return {**record, "resumed": True}

    md = config["parameters"]["md"]
    resolved_backend = resolve_backend(backend)
    arrays: dict[str, np.ndarray] = {
        "fields_v_m": np.asarray(md["fields_v_m"], dtype=float),
        "energy_ratios": np.asarray(md["energy_ratios"], dtype=float),
        "config_sha256": np.asarray(plan["config_sha256"]),
        "implementation_sha256": np.asarray(plan["implementation_sha256"]),
        "shard_id": np.asarray(shard_id),
    }
    drifts = []
    for field_index, field in enumerate(md["fields_v_m"]):
        seed = (
            int(md["seed_base"])
            + shard_id * int(campaign["shard_seed_stride"])
            + field_index * int(campaign["field_seed_stride"])
        )
        result = simulate_collision_shard(
            field_v_m=float(field),
            trajectories=int(campaign["trajectories_per_shard"]),
            collisions=int(md["collisions"]),
            seed=seed,
            bath_temperature_k=float(md["bath_temperature_k"]),
            background_temperature_k=float(md["background_temperature_k"]),
            drive_alpha_k_per_v_m2=float(md["drive_alpha_k_per_v_m2"]),
            backend=resolved_backend,
        )
        arrays[f"field_{field_index:02d}_velocities_m_s"] = result.velocities_m_s
        arrays[f"field_{field_index:02d}_stationary_drift"] = np.asarray(
            result.stationary_relative_drift
        )
        drifts.append(result.stationary_relative_drift)
    _write_npz(data_path, arrays)
    record = {
        "schema_version": 1,
        "paper_id": "2406.13410",
        "shard_id": shard_id,
        "backend": resolved_backend,
        "trajectories_per_field": int(campaign["trajectories_per_shard"]),
        "fields": len(md["fields_v_m"]),
        "config_sha256": plan["config_sha256"],
        "implementation_sha256": plan["implementation_sha256"],
        "output": str(data_path.relative_to(workspace)),
        "output_sha256": _sha256(data_path),
        "max_stationary_relative_drift": max(drifts),
        "resumed": False,
    }
    _write_json(record_path, record)
    return record


def aggregate(config_path: Path, workspace: Path) -> dict[str, Any]:
    config, campaign = load_campaign(config_path, workspace)
    plan = build_plan(config_path, workspace)
    data_root, checks_root = _campaign_roots(workspace, campaign)
    md = config["parameters"]["md"]
    per_field: dict[int, list[np.ndarray]] = {
        index: [] for index in range(len(md["fields_v_m"]))
    }
    drifts: dict[int, list[float]] = {index: [] for index in per_field}
    shard_records = []
    for shard_id in range(int(campaign["shards"])):
        path = data_root / "shards" / f"shard_{shard_id:04d}.npz"
        record_path = checks_root / "shards" / f"shard_{shard_id:04d}.json"
        if not path.is_file() or not record_path.is_file():
            raise FileNotFoundError(f"missing completed shard {shard_id}")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if (
            record.get("config_sha256") != plan["config_sha256"]
            or record.get("implementation_sha256") != plan["implementation_sha256"]
            or record.get("output_sha256") != _sha256(path)
        ):
            raise ValueError(f"shard {shard_id} attestation mismatch")
        with np.load(path) as payload:
            if str(payload["config_sha256"]) != plan["config_sha256"]:
                raise ValueError(f"shard {shard_id} embedded config mismatch")
            for field_index in per_field:
                values = np.asarray(
                    payload[f"field_{field_index:02d}_velocities_m_s"], dtype=float
                )
                if values.shape != (
                    int(campaign["trajectories_per_shard"]),
                    3,
                ):
                    raise ValueError(f"shard {shard_id} has wrong velocity shape")
                per_field[field_index].append(values)
                drifts[field_index].append(
                    float(payload[f"field_{field_index:02d}_stationary_drift"])
                )
        shard_records.append(record)

    arrays: dict[str, np.ndarray] = {
        "fields_v_m": np.asarray(md["fields_v_m"], dtype=float),
        "energy_ratios": np.asarray(md["energy_ratios"], dtype=float),
        "config_sha256": np.asarray(plan["config_sha256"]),
        "implementation_sha256": np.asarray(plan["implementation_sha256"]),
    }
    for field_index in per_field:
        arrays[f"field_{field_index:02d}_velocities_m_s"] = np.concatenate(
            per_field[field_index], axis=0
        )
        arrays[f"field_{field_index:02d}_stationary_drift"] = np.asarray(
            max(drifts[field_index])
        )
    aggregate_path = data_root / "aggregated/md_velocity_samples.npz"
    _write_npz(aggregate_path, arrays)
    reproduction_result = run_reproduction(config_path, workspace)
    namespace = str(config["output_namespace"])
    final_checks_root = workspace / "outputs/checks" / namespace
    generated_manifest = final_checks_root / "generated_data_manifest.json"
    target_checks = json.loads(
        (final_checks_root / "target_checks.json").read_text(encoding="utf-8")
    )
    manifest = {
        "schema_version": 1,
        "paper_id": "2406.13410",
        "execution_profile": config["execution_profile"],
        "config_sha256": plan["config_sha256"],
        "implementation_sha256": plan["implementation_sha256"],
        "shards_completed": len(shard_records),
        "shards_expected": int(campaign["shards"]),
        "total_trajectories_per_field": arrays["field_00_velocities_m_s"].shape[0],
        "aggregate": str(aggregate_path.relative_to(workspace)),
        "aggregate_sha256": _sha256(aggregate_path),
        "generated_manifest": str(generated_manifest.relative_to(workspace)),
        "generated_manifest_sha256": _sha256(generated_manifest),
        "all_targets_passed": target_checks["all_assertions_passed"],
        "paper_error_candidate_emitted": False,
        "source_pixels_used_as_numeric_input": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }
    _write_json(checks_root / "campaign_manifest.json", manifest)
    _write_json(
        checks_root / "target_acceptance.json",
        {
            "schema_version": 1,
            "paper_id": "2406.13410",
            "machine_passed": bool(
                manifest["all_targets_passed"]
                and manifest["shards_completed"] == manifest["shards_expected"]
            ),
            "target_checks": str(
                (final_checks_root / "target_checks.json").relative_to(workspace)
            ),
            "acceptance": campaign["acceptance"],
        },
    )
    return {"manifest": manifest, "reproduction": reproduction_result}
