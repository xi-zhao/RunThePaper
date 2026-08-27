"""Hash-bound, sharded, checkpointable vertex-model campaign execution."""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .analysis import (
    bimodality_coefficient,
    largest_tension_component_fraction,
    newtonian_viscosity,
    peclet_collapse,
    transition_rates,
)
from .model import VertexTissue
from .target_selection import validate_target_selectors


@dataclass(frozen=True)
class Condition:
    condition_id: str
    p0: float
    activity: float
    shear_rate: float
    seed: int
    group_ids: tuple[str, ...]
    target_ids: tuple[str, ...]

    def canonical_payload(self) -> dict[str, object]:
        return {
            "p0": self.p0,
            "activity": self.activity,
            "shear_rate": self.shear_rate,
            "seed": self.seed,
        }


@dataclass(frozen=True)
class OutputLayout:
    """Keep runtime state, reader data, figures, and checks in canonical roots."""

    state_root: Path
    data_root: Path
    figures_root: Path
    checks_root: Path


def output_layout(workspace: Path, config: dict[str, Any]) -> OutputLayout:
    slug = str(config["output_slug"])
    if not slug or "/" in slug or slug in {".", ".."}:
        raise ValueError("output_slug must be one safe path component")
    state_revision = config_digest(config)[:12]
    return OutputLayout(
        state_root=workspace / "outputs" / "data" / slug / "runtime" / state_revision,
        data_root=workspace / "outputs" / "data" / slug,
        figures_root=workspace / "outputs" / "figures" / slug,
        checks_root=workspace / "outputs" / "checks" / slug,
    )


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def config_digest(config: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(config).encode("utf-8"))


def implementation_digest(workspace: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted((workspace / "src" / "tissue_rheology").glob("*.py"))
    paths.extend(sorted((workspace / "scripts").glob("run_*.py")))
    for path in paths:
        digest.update(path.relative_to(workspace).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("campaign config schema_version must be 1")
    if payload.get("paper_id") != "2211.15015":
        raise ValueError("campaign config paper_id mismatch")
    if (
        not isinstance(payload.get("condition_groups"), list)
        or not payload["condition_groups"]
    ):
        raise ValueError("at least one condition group is required")
    if payload.get("profile") in {"feature", "paper_scale", "paper_scale_smoke"}:
        validate_target_selectors(payload)
    return payload


def _condition_id(payload: dict[str, object]) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))[:16]


def plan_conditions(config: dict[str, Any]) -> list[Condition]:
    merged: dict[tuple[float, float, float, int], dict[str, set[str]]] = {}
    for group in config["condition_groups"]:
        group_id = str(group["group_id"])
        target_ids = {str(value) for value in group["target_ids"]}
        for p0 in group["p0"]:
            for activity in group["activity"]:
                for shear_rate in group["shear_rate"]:
                    for seed in group["seeds"]:
                        key = (float(p0), float(activity), float(shear_rate), int(seed))
                        entry = merged.setdefault(
                            key, {"groups": set(), "targets": set()}
                        )
                        entry["groups"].add(group_id)
                        entry["targets"].update(target_ids)
    output: list[Condition] = []
    for key in sorted(merged):
        p0, activity, shear_rate, seed = key
        payload = {
            "p0": p0,
            "activity": activity,
            "shear_rate": shear_rate,
            "seed": seed,
        }
        output.append(
            Condition(
                condition_id=_condition_id(payload),
                p0=p0,
                activity=activity,
                shear_rate=shear_rate,
                seed=seed,
                group_ids=tuple(sorted(merged[key]["groups"])),
                target_ids=tuple(sorted(merged[key]["targets"])),
            )
        )
    return output


def select_shard(
    conditions: list[Condition],
    *,
    shard_index: int,
    shard_count: int,
) -> list[Condition]:
    if shard_count <= 0 or shard_index < 0 or shard_index >= shard_count:
        raise ValueError("shard index/count are invalid")
    return [
        condition
        for index, condition in enumerate(conditions)
        if index % shard_count == shard_index
    ]


def atomic_json(path: Path, payload: object) -> None:
    def sanitize(value: object) -> object:
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, np.floating):
            converted = float(value)
            return converted if math.isfinite(converted) else None
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, dict):
            return {str(key): sanitize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [sanitize(item) for item in value]
        return value

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(sanitize(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_npz(path: Path, **arrays: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _model_kwargs(config: dict[str, Any], *, p0: float, seed: int) -> dict[str, object]:
    model = config["model"]
    return {
        "nx": int(model["nx"]),
        "ny": int(model["ny"]),
        "p0": p0,
        "seed": seed,
        "kappa_area": float(model["kappa_area"]),
        "kappa_perimeter": float(model["kappa_perimeter"]),
        "zeta": float(model["zeta"]),
        "rotational_diffusion": float(model["rotational_diffusion"]),
        "t1_threshold": float(model["t1_threshold"]),
        "t1_reset_factor": float(model["t1_reset_factor"]),
        "bidispersity": float(model["bidispersity"]),
    }


def prepare_model(config: dict[str, Any], *, p0: float, seed: int) -> VertexTissue:
    model = VertexTissue.initialize(**_model_kwargs(config, p0=p0, seed=seed))
    preparation = config["preparation"]
    dt = float(config["model"]["dt"])
    original_diffusion = model.rotational_diffusion
    model.rotational_diffusion = float(preparation["rotational_diffusion"])
    model.run(
        steps=int(preparation["active_steps"]),
        activity=float(preparation["activity"]),
        shear_rate=0.0,
        dt=dt,
        sample_every=max(1, int(preparation["active_steps"])),
        enable_t1=True,
        max_nonaffine_displacement=preparation.get("max_nonaffine_displacement"),
    )
    model.rotational_diffusion = original_diffusion
    model.run(
        steps=int(preparation["relax_steps"]),
        activity=0.0,
        shear_rate=0.0,
        dt=dt,
        sample_every=max(1, int(preparation["relax_steps"])),
        enable_t1=True,
        max_nonaffine_displacement=preparation.get("max_nonaffine_displacement"),
    )
    model.time = 0.0
    model.strain = 0.0
    model.t1_count = 0
    return model


def condition_step_counts(
    config: dict[str, Any], condition: Condition
) -> tuple[int, int]:
    sampling = config["sampling"]
    if "fixed_warmup_steps" in sampling:
        return int(sampling["fixed_warmup_steps"]), int(sampling["fixed_sample_steps"])
    dt = float(config["model"]["dt"])
    if condition.shear_rate <= 0.0:
        raise ValueError(
            "strain-controlled paper-scale jobs require positive shear rate"
        )
    warmup = math.ceil(float(sampling["warmup_strain"]) / (condition.shear_rate * dt))
    sample = math.ceil(float(sampling["sample_strain"]) / (condition.shear_rate * dt))
    return warmup, sample


def condition_sample_every(config: dict[str, Any], condition: Condition) -> int:
    sampling = config["sampling"]
    if "samples_per_strain" not in sampling:
        return max(1, int(sampling["sample_every"]))
    dt = float(config["model"]["dt"])
    samples_per_strain = float(sampling["samples_per_strain"])
    if samples_per_strain <= 0.0 or condition.shear_rate <= 0.0:
        raise ValueError("samples_per_strain and shear rate must be positive")
    return max(1, int(round(1.0 / (condition.shear_rate * dt * samples_per_strain))))


def prepare_cache_path(output_root: Path, p0: float, seed: int) -> Path:
    key = _condition_id({"p0": p0, "seed": seed, "stage": "prepared"})
    return output_root / "prepared" / f"{key}.npz"


def load_or_create_prepared(
    config: dict[str, Any],
    *,
    output_root: Path,
    p0: float,
    seed: int,
    binding: dict[str, str],
    resume: bool,
) -> VertexTissue:
    path = prepare_cache_path(output_root, p0, seed)
    prepared_binding = dict(binding)
    prepared_binding.update(
        {"stage": "prepared", "p0": f"{p0:.12g}", "seed": str(seed)}
    )
    if resume and path.exists():
        model, completed, _ = VertexTissue.load_checkpoint(
            path, expected_binding=prepared_binding
        )
        if completed != 0:
            raise ValueError("prepared-state checkpoint must have completed_steps=0")
        return model
    model = prepare_model(config, p0=p0, seed=seed)
    model.save_checkpoint(path, binding=prepared_binding, completed_steps=0)
    return model


def _chunk_paths(condition_root: Path) -> list[Path]:
    return sorted((condition_root / "chunks").glob("chunk_*.npz"))


def _aggregate_chunks(condition_root: Path, sample_steps: int) -> dict[str, np.ndarray]:
    chunks = _chunk_paths(condition_root)
    if not chunks:
        raise ValueError("no sampling chunks were produced")
    fields = [
        "time",
        "strain",
        "stress",
        "energy",
        "t1_count",
        "unresolved_short_edges",
    ]
    collected: dict[str, list[np.ndarray]] = {field: [] for field in fields}
    intervals: list[tuple[int, int]] = []
    for path in chunks:
        with np.load(path, allow_pickle=False) as payload:
            start = int(payload["sample_start"])
            stop = int(payload["sample_stop"])
            intervals.append((start, stop))
            for field in fields:
                collected[field].append(np.asarray(payload[field], dtype=np.float64))
    intervals.sort()
    cursor = 0
    for start, stop in intervals:
        if start != cursor or stop <= start:
            raise ValueError(
                f"sampling chunk gap/overlap at {start}:{stop}, expected {cursor}"
            )
        cursor = stop
    if cursor != sample_steps:
        raise ValueError(
            f"sampling chunks cover {cursor} steps, expected {sample_steps}"
        )
    return {field: np.concatenate(collected[field]) for field in fields}


def _snapshot_arrays(model: VertexTissue) -> dict[str, np.ndarray]:
    flat, offsets = model._flatten_cells()
    network = model.tension_network()
    return {
        "lattice": model.lattice,
        "fractional": model.fractional,
        "cell_flat": flat,
        "cell_offsets": offsets,
        "target_area": model.target_area,
        "target_perimeter": model.target_perimeter,
        "network_first": np.asarray(
            [edge["first"] for edge in network], dtype=np.int64
        ),
        "network_second": np.asarray(
            [edge["second"] for edge in network], dtype=np.int64
        ),
        "network_tension": np.asarray(
            [edge["tension"] for edge in network], dtype=np.float64
        ),
    }


def execute_condition(
    config: dict[str, Any],
    condition: Condition,
    *,
    workspace: Path,
    output_root: Path,
    resume: bool,
    prepared_model: VertexTissue | None = None,
) -> dict[str, Any]:
    config_sha = config_digest(config)
    implementation_sha = implementation_digest(workspace)
    binding = {
        "config_sha256": config_sha,
        "implementation_sha256": implementation_sha,
        "condition_id": condition.condition_id,
    }
    condition_root = output_root / "conditions" / condition.condition_id
    result_path = condition_root / "result.npz"
    record_path = condition_root / "record.json"
    if resume and result_path.exists() and record_path.exists():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("binding") != binding:
            raise ValueError("existing condition result has stale binding")
        if sha256_file(result_path) != record.get("result_sha256"):
            raise ValueError("existing condition result hash mismatch")
        return record

    warmup_steps, sample_steps = condition_step_counts(config, condition)
    checkpoint = condition_root / "checkpoint.npz"
    if resume and checkpoint.exists():
        model, completed_steps, _ = VertexTissue.load_checkpoint(
            checkpoint, expected_binding=binding
        )
    else:
        base = prepared_model or load_or_create_prepared(
            config,
            output_root=output_root,
            p0=condition.p0,
            seed=condition.seed,
            binding={
                "config_sha256": config_sha,
                "implementation_sha256": implementation_sha,
            },
            resume=resume,
        )
        model = base.copy()
        model.save_checkpoint(checkpoint, binding=binding, completed_steps=0)
        completed_steps = 0

    dt = float(config["model"]["dt"])
    sampling = config["sampling"]
    sample_every = condition_sample_every(config, condition)
    max_displacement = sampling.get("max_nonaffine_displacement")
    if completed_steps < warmup_steps:
        model.run(
            steps=warmup_steps - completed_steps,
            activity=condition.activity,
            shear_rate=condition.shear_rate,
            dt=dt,
            sample_every=sample_every,
            enable_t1=True,
            max_nonaffine_displacement=max_displacement,
            starting_step=completed_steps,
        )
        completed_steps = warmup_steps
        model.save_checkpoint(
            checkpoint, binding=binding, completed_steps=completed_steps
        )

    sample_completed = completed_steps - warmup_steps
    if sample_completed < 0 or sample_completed > sample_steps:
        raise ValueError("checkpoint completed step is outside the declared campaign")
    chunk_size = int(sampling["checkpoint_steps"])
    while sample_completed < sample_steps:
        stop = min(sample_steps, sample_completed + chunk_size)
        data = model.run(
            steps=stop - sample_completed,
            activity=condition.activity,
            shear_rate=condition.shear_rate,
            dt=dt,
            sample_every=sample_every,
            enable_t1=True,
            max_nonaffine_displacement=max_displacement,
            starting_step=warmup_steps + sample_completed,
        )
        atomic_npz(
            condition_root
            / "chunks"
            / f"chunk_{sample_completed:012d}_{stop:012d}.npz",
            sample_start=np.asarray(sample_completed, dtype=np.int64),
            sample_stop=np.asarray(stop, dtype=np.int64),
            **data,
        )
        sample_completed = stop
        completed_steps = warmup_steps + sample_completed
        model.save_checkpoint(
            checkpoint, binding=binding, completed_steps=completed_steps
        )

    data = _aggregate_chunks(condition_root, sample_steps)
    snapshot = _snapshot_arrays(model)
    positive_stress = np.maximum(data["stress"], 1e-14)
    summary = {
        "mean_stress": float(np.mean(positive_stress)),
        "median_stress": float(np.median(positive_stress)),
        "stress_std": float(np.std(positive_stress)),
        "log_stress_bimodality": bimodality_coefficient(np.log10(positive_stress)),
        "final_energy": float(data["energy"][-1]),
        "t1_count": int(model.t1_count),
        "unresolved_short_edges": int(data["unresolved_short_edges"][-1]),
        "largest_tension_component_fraction": largest_tension_component_fraction(
            model.vertex_count, model.tension_network()
        ),
    }
    atomic_npz(
        result_path,
        condition_json=np.asarray(canonical_json(condition.canonical_payload())),
        binding_json=np.asarray(canonical_json(binding)),
        **data,
        **snapshot,
    )
    try:
        result_reference = result_path.relative_to(workspace).as_posix()
    except ValueError:
        result_reference = result_path.as_posix()
    record = {
        "schema_version": 1,
        "paper_id": "2211.15015",
        "condition_id": condition.condition_id,
        "condition": condition.canonical_payload(),
        "group_ids": list(condition.group_ids),
        "target_ids": list(condition.target_ids),
        "profile": config["profile"],
        "binding": binding,
        "paper_parameters_executed": config["profile"] == "paper_scale",
        "warmup_steps": warmup_steps,
        "sample_steps": sample_steps,
        "sample_count": int(len(data["stress"])),
        "sample_every_steps": sample_every,
        "result_path": result_reference,
        "result_sha256": sha256_file(result_path),
        "state_sha256": model.state_digest(),
        "summary": summary,
        "status": "passed",
    }
    atomic_json(record_path, record)
    return record


def load_condition_results(
    workspace: Path,
    output_root: Path,
    conditions: Iterable[Condition],
    *,
    load_arrays: bool = True,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for condition in conditions:
        root = output_root / "conditions" / condition.condition_id
        record_path = root / "record.json"
        result_path = root / "result.npz"
        if not record_path.exists() or not result_path.exists():
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        item: dict[str, Any] = {
            "record": record,
            "condition": condition,
            "result_path": result_path,
        }
        if load_arrays:
            with np.load(result_path, allow_pickle=False) as payload:
                for key in payload.files:
                    if key.endswith("_json"):
                        continue
                    item[key] = np.asarray(payload[key])
        output.append(item)
    return output


def aggregate_flow_curves(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, float, float], list[dict[str, Any]]] = {}
    for item in results:
        condition: Condition = item["condition"]
        grouped.setdefault(
            (condition.p0, condition.activity, condition.shear_rate), []
        ).append(item)
    points: list[dict[str, Any]] = []
    for (p0, activity, shear_rate), replicates in sorted(grouped.items()):
        means = [float(rep["record"]["summary"]["mean_stress"]) for rep in replicates]
        points.append(
            {
                "p0": p0,
                "activity": activity,
                "shear_rate": shear_rate,
                "stress": float(np.mean(means)),
                "stress_sem": (
                    float(np.std(means, ddof=1) / np.sqrt(len(means)))
                    if len(means) > 1
                    else 0.0
                ),
                "replicates": len(means),
            }
        )
    curves_by_key: dict[tuple[float, float], list[dict[str, Any]]] = {}
    for point in points:
        curves_by_key.setdefault((point["p0"], point["activity"]), []).append(point)
    curves: list[dict[str, Any]] = []
    for (p0, activity), values in sorted(curves_by_key.items()):
        values.sort(key=lambda item: item["shear_rate"])
        rate = np.asarray([item["shear_rate"] for item in values], dtype=np.float64)
        stress = np.asarray(
            [max(item["stress"], 1e-14) for item in values], dtype=np.float64
        )
        transition = transition_rates(rate, stress)
        viscosity, viscosity_residual = newtonian_viscosity(rate, stress)
        curves.append(
            {
                "p0": p0,
                "activity": activity,
                "shear_rate": rate,
                "stress": stress,
                "stress_sem": np.asarray([item["stress_sem"] for item in values]),
                "viscosity": viscosity,
                "viscosity_relative_rms": viscosity_residual,
                "thickening_rate": transition.thickening_rate,
                "thinning_rate": transition.thinning_rate,
                "maximum_slope": transition.maximum_slope,
                "slope": transition.slope,
            }
        )
    return curves


def campaign_summary(
    config: dict[str, Any],
    conditions: list[Condition],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    curves = aggregate_flow_curves(results) if results else []
    collapse = peclet_collapse(curves) if curves else {}
    target_ids = sorted(
        {target for condition in conditions for target in condition.target_ids}
    )
    return {
        "schema_version": 1,
        "paper_id": "2211.15015",
        "profile": config["profile"],
        "conditions_planned": len(conditions),
        "conditions_complete": len(results),
        "target_ids": target_ids,
        "targets_planned": len(target_ids),
        "config_sha256": config_digest(config),
        "peclet_collapse": collapse,
        "status": "passed" if len(results) == len(conditions) else "partial",
    }
