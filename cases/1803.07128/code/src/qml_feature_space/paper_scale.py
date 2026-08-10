"""Hash-attested, restartable paper-scale campaign for Fig. 8.

Compute can postpone executing this campaign, but every scientific condition is
fully specified and executable.  A completed campaign remains scientifically
inconclusive about exact paper pixels because the paper omits seeds, cutoff,
initialization, optimizer details, and the dataset noise realization.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from .variational_scale import (
    VariationalCondition,
    factorized_dense_crosscheck,
    resolve_device,
    train_condition,
)

TARGET_ID = "T004"


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_npz(path: Path, arrays: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_torch_save(path: Path, payload: dict[str, Any]) -> None:
    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("wb") as handle:
        torch.save(payload, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "paper_id",
        "run_id",
        "output_root",
        "parameters",
        "acceptance",
        "execution",
        "review_policy",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ValueError(f"paper-scale config missing fields: {missing}")
    if config["paper_id"] != "1803.07128":
        raise ValueError("paper-scale config belongs to a different paper")
    parameters = config["parameters"]
    if int(parameters["variational_parameter_count"]) != 8 * int(
        parameters["variational_blocks"]
    ):
        raise ValueError("parameter count must equal eight times the block count")
    if int(parameters["train_samples"]) >= int(parameters["total_samples"]):
        raise ValueError("training split must leave an independent test set")
    return config


def config_sha256(config: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical_json(config))


def implementation_sha256() -> str:
    package = Path(__file__).resolve().parent
    workspace = Path(__file__).resolve().parents[2]
    paths = [
        package / "paper_scale.py",
        package / "variational_scale.py",
        workspace / "scripts" / "run_paper_scale.py",
    ]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def enumerate_conditions(config: dict[str, Any]) -> list[VariationalCondition]:
    parameters = config["parameters"]
    conditions = [
        VariationalCondition(int(cutoff), int(seed))
        for cutoff in parameters["cutoffs"]
        for seed in parameters["seeds"]
    ]
    identifiers = [condition.condition_id for condition in conditions]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("paper-scale condition identifiers are not unique")
    return conditions


def plan_campaign(
    config: dict[str, Any], output_root: Path, *, write: bool = False
) -> dict[str, Any]:
    conditions = enumerate_conditions(config)
    payload = {
        "schema_version": 1,
        "status": "ready",
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "target_ids": [TARGET_ID],
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "conditions_total": len(conditions),
        "conditions": [condition.record() for condition in conditions],
        "recommended_shards": config["execution"]["recommended_shards"],
        "hardware_route": config["execution"]["hardware_route"],
        "full_campaign_executed": False,
    }
    if write:
        _atomic_json(output_root / "plan.json", payload)
    return payload


def _paths(output_root: Path, condition: VariationalCondition) -> dict[str, Path]:
    stem = condition.condition_id
    return {
        "output": output_root / "conditions" / f"{stem}.npz",
        "output_manifest": output_root / "conditions" / f"{stem}.manifest.json",
        "checkpoint": output_root / "checkpoints" / f"{stem}.pt",
        "checkpoint_manifest": output_root / "checkpoints" / f"{stem}.manifest.json",
    }


def _load_torch_checkpoint(path: Path) -> dict[str, Any]:
    import torch

    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def _valid_identity(
    manifest: dict[str, Any],
    config: dict[str, Any],
    condition: VariationalCondition,
) -> bool:
    return (
        manifest.get("paper_id") == config["paper_id"]
        and manifest.get("config_sha256") == config_sha256(config)
        and manifest.get("implementation_sha256") == implementation_sha256()
        and manifest.get("condition") == condition.record()
    )


def run_condition(
    config: dict[str, Any],
    output_root: Path,
    condition: VariationalCondition,
    *,
    resume: bool,
) -> dict[str, Any]:
    paths = _paths(output_root, condition)
    output_exists = paths["output"].exists()
    output_manifest_exists = paths["output_manifest"].exists()
    if output_exists or output_manifest_exists:
        if resume and output_exists and output_manifest_exists:
            manifest = json.loads(paths["output_manifest"].read_text(encoding="utf-8"))
            if (
                manifest.get("status") == "complete"
                and _valid_identity(manifest, config, condition)
                and manifest.get("output_sha256") == _sha256_file(paths["output"])
            ):
                return {
                    "condition_id": condition.condition_id,
                    "status": "resumed_complete",
                }
            raise RuntimeError(
                f"stale or corrupt final output: {condition.condition_id}"
            )
        if resume:
            raise RuntimeError(f"partial final output: {condition.condition_id}")

    checkpoint_exists = paths["checkpoint"].exists()
    checkpoint_manifest_exists = paths["checkpoint_manifest"].exists()
    resume_payload = None
    if checkpoint_exists or checkpoint_manifest_exists:
        if not resume:
            _atomic_json(
                paths["checkpoint_manifest"],
                {
                    "schema_version": 1,
                    "status": "invalidated_for_explicit_restart",
                    "paper_id": config["paper_id"],
                    "condition": condition.record(),
                    "config_sha256": config_sha256(config),
                    "implementation_sha256": implementation_sha256(),
                },
            )
        elif not (checkpoint_exists and checkpoint_manifest_exists):
            raise RuntimeError(f"partial training checkpoint: {condition.condition_id}")
        else:
            checkpoint_manifest = json.loads(
                paths["checkpoint_manifest"].read_text(encoding="utf-8")
            )
            if not (
                checkpoint_manifest.get("status") == "checkpointed"
                and _valid_identity(checkpoint_manifest, config, condition)
                and checkpoint_manifest.get("checkpoint_sha256")
                == _sha256_file(paths["checkpoint"])
            ):
                raise RuntimeError(
                    f"stale or corrupt checkpoint: {condition.condition_id}"
                )
            resume_payload = _load_torch_checkpoint(paths["checkpoint"])
            if int(resume_payload.get("step", -1)) != int(
                checkpoint_manifest.get("completed_steps", -2)
            ):
                raise RuntimeError(
                    f"checkpoint step mismatch: {condition.condition_id}"
                )

    device = resolve_device(str(config["execution"]["device"]))

    def save_checkpoint(payload: dict[str, Any]) -> None:
        _atomic_torch_save(paths["checkpoint"], payload)
        _atomic_json(
            paths["checkpoint_manifest"],
            {
                "schema_version": 1,
                "status": "checkpointed",
                "paper_id": config["paper_id"],
                "condition": condition.record(),
                "completed_steps": int(payload["step"]),
                "actual_device": device,
                "config_sha256": config_sha256(config),
                "implementation_sha256": implementation_sha256(),
                "checkpoint_sha256": _sha256_file(paths["checkpoint"]),
            },
        )

    arrays = train_condition(
        config["parameters"],
        condition,
        device=device,
        resume_payload=resume_payload,
        checkpoint_callback=save_checkpoint,
    )
    _atomic_npz(paths["output"], arrays)
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "target_ids": [TARGET_ID],
        "condition": condition.record(),
        "actual_device": device,
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "output_path": str(paths["output"].relative_to(output_root)),
        "output_sha256": _sha256_file(paths["output"]),
    }
    _atomic_json(paths["output_manifest"], manifest)
    return {
        "condition_id": condition.condition_id,
        "status": "resumed_training" if resume_payload is not None else "computed",
        "actual_device": device,
    }


def run_shard(
    config: dict[str, Any],
    output_root: Path,
    *,
    shard_index: int,
    shard_count: int,
    resume: bool,
) -> dict[str, Any]:
    if shard_count <= 0 or not 0 <= shard_index < shard_count:
        raise ValueError("shard index/count is invalid")
    selected = [
        condition
        for index, condition in enumerate(enumerate_conditions(config))
        if index % shard_count == shard_index
    ]
    results = [
        run_condition(config, output_root, condition, resume=resume)
        for condition in selected
    ]
    status_counts: dict[str, int] = {}
    for result in results:
        key = str(result["status"])
        status_counts[key] = status_counts.get(key, 0) + 1
    summary = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "conditions_selected": len(selected),
        "condition_ids": [condition.condition_id for condition in selected],
        "status_counts": status_counts,
    }
    _atomic_json(
        output_root / "shards" / f"shard-{shard_index:03d}-of-{shard_count:03d}.json",
        summary,
    )
    return summary


def _load_output(
    config: dict[str, Any],
    output_root: Path,
    condition: VariationalCondition,
) -> dict[str, np.ndarray]:
    paths = _paths(output_root, condition)
    if not paths["output"].exists() or not paths["output_manifest"].exists():
        raise RuntimeError(f"condition is incomplete: {condition.condition_id}")
    manifest = json.loads(paths["output_manifest"].read_text(encoding="utf-8"))
    if not (
        manifest.get("status") == "complete"
        and _valid_identity(manifest, config, condition)
        and manifest.get("output_sha256") == _sha256_file(paths["output"])
    ):
        raise RuntimeError(f"condition attestation failed: {condition.condition_id}")
    with np.load(paths["output"], allow_pickle=False) as payload:
        return {key: np.asarray(payload[key]) for key in payload.files}


def aggregate_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    conditions = enumerate_conditions(config)
    records = [
        (condition, _load_output(config, output_root, condition))
        for condition in conditions
    ]
    cutoffs = np.asarray([condition.cutoff for condition, _ in records])
    seeds = np.asarray([condition.seed for condition, _ in records])
    train_accuracy = np.asarray(
        [arrays["train_accuracy"].item() for _, arrays in records]
    )
    test_accuracy = np.asarray(
        [arrays["test_accuracy"].item() for _, arrays in records]
    )
    loss_ratio = np.asarray(
        [arrays["loss_reduction_ratio"].item() for _, arrays in records]
    )
    retained = np.asarray(
        [arrays["input_retained_probability_min"].item() for _, arrays in records]
    )
    probability_maps = np.stack(
        [arrays["class_one_probability"] for _, arrays in records]
    )
    losses = np.stack([arrays["loss"] for _, arrays in records])
    parameters = np.stack([arrays["final_parameters"] for _, arrays in records])
    convergence_rows = []
    for seed in sorted(set(seeds.tolist())):
        indices = np.flatnonzero(seeds == seed)
        indices = indices[np.argsort(cutoffs[indices])]
        for first, second in zip(indices[:-1], indices[1:]):
            convergence_rows.append(
                (
                    seed,
                    int(cutoffs[first]),
                    int(cutoffs[second]),
                    float(
                        np.mean(
                            np.abs(probability_maps[first] - probability_maps[second])
                        )
                    ),
                    float(
                        np.max(
                            np.abs(probability_maps[first] - probability_maps[second])
                        )
                    ),
                )
            )
    convergence = np.asarray(convergence_rows, dtype=float).reshape(-1, 5)
    crosscheck = factorized_dense_crosscheck(
        int(config["acceptance"]["dense_crosscheck_cutoff"])
    )
    maximum_cutoff = max(config["parameters"]["cutoffs"])
    maximum_mask = cutoffs == maximum_cutoff
    final_convergence = convergence[convergence[:, 2] == maximum_cutoff, 3]
    final_convergence_max = (
        float(np.max(final_convergence)) if len(final_convergence) > 0 else None
    )
    acceptance = config["acceptance"]
    method_checks = {
        "factorized_dense_crosscheck": bool(crosscheck["passed"]),
        "maximum_cutoff_retained_probability": bool(
            np.min(retained[maximum_mask])
            >= float(acceptance["maximum_cutoff_retained_probability_min"])
        ),
        "maximum_cutoff_train_accuracy": bool(
            np.min(train_accuracy[maximum_mask])
            >= float(acceptance["maximum_cutoff_train_accuracy_min"])
        ),
        "maximum_cutoff_test_accuracy": bool(
            np.min(test_accuracy[maximum_mask])
            >= float(acceptance["maximum_cutoff_test_accuracy_min"])
        ),
        "maximum_cutoff_loss_reduction": bool(
            np.max(loss_ratio[maximum_mask])
            <= float(acceptance["maximum_cutoff_loss_reduction_ratio_max"])
        ),
        "final_cutoff_probability_convergence": bool(
            len(final_convergence) > 0
            and final_convergence_max is not None
            and final_convergence_max
            <= float(acceptance["final_cutoff_probability_mean_absolute_delta_max"])
        ),
    }
    method_supported = all(method_checks.values())
    aggregate_path = (
        output_root / "aggregates" / "T004_fig8_variational_convergence.npz"
    )
    _atomic_npz(
        aggregate_path,
        {
            "cutoff": cutoffs,
            "seed": seeds,
            "train_accuracy": train_accuracy,
            "test_accuracy": test_accuracy,
            "loss_reduction_ratio": loss_ratio,
            "input_retained_probability_min": retained,
            "probability_maps": probability_maps,
            "loss": losses,
            "final_parameters": parameters,
            "convergence_seed_cutoff_from_cutoff_to_mean_delta_max_delta": convergence,
            "grid_x": np.stack([arrays["grid_x"] for _, arrays in records]),
            "grid_y": np.stack([arrays["grid_y"] for _, arrays in records]),
        },
    )
    aggregate_manifest = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "target_id": TARGET_ID,
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "conditions_total": len(conditions),
        "aggregate_path": str(aggregate_path.relative_to(output_root)),
        "aggregate_sha256": _sha256_file(aggregate_path),
    }
    _atomic_json(output_root / "aggregate_manifest.json", aggregate_manifest)
    _atomic_json(
        output_root / "checks" / "factorized_dense_crosscheck.json",
        {
            "schema_version": 1,
            "status": "passed" if crosscheck["passed"] else "failed",
            **crosscheck,
        },
    )
    assessment = {
        "schema_version": 1,
        "status": "supported" if method_supported else "requires_investigation",
        "paper_id": config["paper_id"],
        "target_id": TARGET_ID,
        "method_checks": method_checks,
        "metrics": {
            "maximum_cutoff": maximum_cutoff,
            "maximum_cutoff_retained_probability_min": float(
                np.min(retained[maximum_mask])
            ),
            "maximum_cutoff_train_accuracy_min": float(
                np.min(train_accuracy[maximum_mask])
            ),
            "maximum_cutoff_test_accuracy_min": float(
                np.min(test_accuracy[maximum_mask])
            ),
            "maximum_cutoff_loss_reduction_ratio_max": float(
                np.max(loss_ratio[maximum_mask])
            ),
            "final_cutoff_probability_mean_absolute_delta_max": final_convergence_max,
        },
        "paper_assessment": "inconclusive",
        "paper_error_candidate": False,
        "reason": (
            "The paper omits dataset seed/noise, Fock cutoff, initialization, "
            "optimizer schedule, and regularization. A converged independent method "
            "test cannot identify exact published arrays without those inputs."
        ),
        "review_boundary": config["review_policy"],
    }
    _atomic_json(output_root / "checks" / "scientific_assessment.json", assessment)
    summary = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "target_ids": [TARGET_ID],
        "conditions_total": len(conditions),
        "method_status": assessment["status"],
        "paper_assessment": "inconclusive",
        "paper_error_candidate": False,
    }
    _atomic_json(output_root / "run_summary.json", summary)
    return summary
