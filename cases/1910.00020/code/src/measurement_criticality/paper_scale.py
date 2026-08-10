"""Sharded, resumable paper-scale campaign for arXiv:1910.00020.

The campaign stores only sufficient statistics for each declared condition.
No author arrays, author code, or source-image pixels enter the numerical path.
Every trajectory has a deterministic global identity, so shards can be moved
between CPU workers without duplicating random streams.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .reproduction import _distance, _evolve, _pairs, _random_layer, _signed_distance
from .stabilizer import (
    MixedStabilizerState,
    StabilizerState,
    insert_bell_pair,
    two_qubit_symplectic_group,
)


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 9))

_WORKER_CAMPAIGN: "PaperScaleCampaign | None" = None


def _initialize_worker(config_path: str, output_root: str, smoke: bool) -> None:
    global _WORKER_CAMPAIGN
    _WORKER_CAMPAIGN = PaperScaleCampaign(
        Path(config_path), output_root=Path(output_root), smoke=smoke
    )


def _run_worker(specification: tuple[str, int, bool]) -> dict[str, Any]:
    if _WORKER_CAMPAIGN is None:
        raise RuntimeError("paper-scale worker was not initialized")
    condition_id, shard, resume = specification
    return _WORKER_CAMPAIGN.run_shard(condition_id, shard, resume=resume)


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _atomic_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Condition:
    target_id: str
    condition_id: str
    parameters: dict[str, Any]
    trajectories: int
    shards: int

    @property
    def identity_hash(self) -> str:
        return _canonical_hash(
            {
                "target_id": self.target_id,
                "condition_id": self.condition_id,
                "parameters": self.parameters,
                "trajectories": self.trajectories,
                "shards": self.shards,
            }
        )


def _float_label(value: float) -> str:
    return f"{value:.5f}".replace("-", "m").replace(".", "p")


def _conditions(config: dict[str, Any]) -> list[Condition]:
    targets = config["targets"]
    parameters = config["parameters"]
    result: list[Condition] = []

    target = targets["T001"]
    for length in target["sizes"]:
        for rate in target["measurement_rates"]:
            result.append(
                Condition(
                    "T001",
                    f"T001_L{length:04d}_p{_float_label(rate)}",
                    {
                        "L": length,
                        "rate": rate,
                        "pre_layers": target["encoding_layers_per_L"] * length,
                        "post_layers": target["measured_layers_per_L"] * length,
                    },
                    target["trajectories"],
                    target["shards"],
                )
            )

    target = targets["T002"]
    result.append(
        Condition(
            "T002",
            "T002_product_lightcone",
            {"L": target["L"], "duration": target["duration"], "pre_layers": 0, "pre_rate": 0.0},
            target["trajectories"],
            target["shards"],
        )
    )

    target = targets["T003"]
    for rate in target["measurement_rates"]:
        for cutoff_value in target["cutoffs"]:
            cutoff = None if cutoff_value == "full" else int(cutoff_value)
            cutoff_label = "full" if cutoff is None else f"r{cutoff:02d}"
            result.append(
                Condition(
                    "T003",
                    f"T003_p{_float_label(rate)}_{cutoff_label}",
                    {
                        "L": target["L"],
                        "duration": target["duration"],
                        "rate": rate,
                        "cutoff": cutoff,
                    },
                    target["trajectories"],
                    target["shards"],
                )
            )

    target = targets["T004"]
    for length in target["sizes"]:
        for rate in target["measurement_rates"]:
            result.append(
                Condition(
                    "T004",
                    f"T004_L{length:04d}_p{_float_label(rate)}",
                    {
                        "L": length,
                        "rate": rate,
                        "post_layers": target["post_layers_per_L"] * length,
                    },
                    target["trajectories"],
                    target["shards"],
                )
            )

    target = targets["T005"]
    for length in target["sizes"]:
        for branch, pre_factor, exponent in (
            ("surface", 0, parameters["eta_parallel_1"]),
            ("bulk", 4, parameters["eta_bulk"]),
        ):
            result.append(
                Condition(
                    "T005",
                    f"T005_{branch}_L{length:04d}",
                    {
                        "L": length,
                        "branch": branch,
                        "periodic": True,
                        "pre_layers": pre_factor * length,
                        "post_layers": target["post_layers_per_L"] * length,
                        "rate": parameters["critical_rate_correlations"],
                        "exponent": exponent,
                    },
                    target["trajectories"],
                    target["shards"],
                )
            )

    target = targets["T006"]
    mixed_exponent = 0.5 * (parameters["eta_bulk"] + parameters["eta_parallel_3"])
    for length in target["sizes"]:
        for branch, exponent in (
            ("end_to_end", parameters["eta_parallel_2"]),
            ("mixed", mixed_exponent),
        ):
            result.append(
                Condition(
                    "T006",
                    f"T006_{branch}_L{length:04d}",
                    {
                        "L": length,
                        "branch": branch,
                        "periodic": False,
                        "pre_layers": 4 * length,
                        "post_layers": target["post_layers_per_L"] * length,
                        "rate": parameters["critical_rate_correlations"],
                        "exponent": exponent,
                    },
                    target["trajectories"],
                    target["shards"],
                )
            )

    target = targets["T007"]
    for mode in target["preparation_modes"]:
        result.append(
            Condition(
                "T007",
                f"T007_{mode}",
                {
                    "L": target["L"],
                    "duration": target["duration"],
                    "pre_layers": target["pre_layers_per_L"] * target["L"],
                    "pre_rate": parameters["volume_rate"] if mode == "volume_law" else 0.0,
                    "mode": mode,
                },
                target["trajectories"],
                target["shards"],
            )
        )

    target = targets["T008"]
    for references in target["reference_counts"]:
        for length in target["sizes"]:
            result.append(
                Condition(
                    "T008",
                    f"T008_R{references}_L{length:04d}",
                    {
                        "L": length,
                        "references": references,
                        "rate": parameters["critical_rate_correlations"],
                        "post_layers": target["post_layers_per_L"] * length,
                    },
                    target["trajectories"],
                    target["shards"],
                )
            )
    return result


def _smoke_condition(condition: Condition, smoke: dict[str, Any]) -> Condition:
    parameters = dict(condition.parameters)
    if "L" in parameters:
        parameters["L"] = min(int(parameters["L"]), int(smoke["max_L"]))
    for name in ("duration", "pre_layers", "post_layers"):
        if name in parameters:
            parameters[name] = min(int(parameters[name]), int(smoke["max_duration"]))
    return replace(
        condition,
        parameters=parameters,
        trajectories=int(smoke["trajectories"]),
        shards=int(smoke["shards"]),
    )


def build_conditions(config: dict[str, Any], *, smoke: bool = False) -> list[Condition]:
    conditions = _conditions(config)
    if smoke:
        conditions = [_smoke_condition(condition, config["smoke"]) for condition in conditions]
    identities = [condition.condition_id for condition in conditions]
    if len(identities) != len(set(identities)):
        raise ValueError("condition ids must be globally unique")
    if set(condition.target_id for condition in conditions) != set(TARGET_IDS):
        raise ValueError("paper-scale campaign must cover T001-T008")
    return conditions


def trajectory_seed(seed_base: int, condition_id: str, trajectory_id: int) -> int:
    encoded = f"{seed_base}:{condition_id}:{trajectory_id}".encode()
    return int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")


def _single_reference_final(parameters: dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    length = int(parameters["L"])
    state = StabilizerState.product_zero(length + 1)
    reference = length
    pre_layers = int(parameters.get("pre_layers", 0))
    if pre_layers:
        _evolve(state, length, pre_layers, 0.0, True, rng)
    insert_bell_pair(state, reference, length // 2)
    _evolve(
        state,
        length,
        int(parameters["post_layers"]),
        float(parameters["rate"]),
        True,
        rng,
        layer_offset=pre_layers,
    )
    return np.asarray([state.entropy([reference])], dtype=float)


def _lightcone(parameters: dict[str, Any], post_rate: float, rng: np.random.Generator) -> np.ndarray:
    length = int(parameters["L"])
    duration = int(parameters["duration"])
    state = StabilizerState.product_zero(length + 1)
    reference = length
    origin = length // 2
    pre_layers = int(parameters.get("pre_layers", 0))
    if pre_layers:
        _evolve(
            state,
            length,
            pre_layers,
            float(parameters.get("pre_rate", 0.0)),
            True,
            rng,
        )
    insert_bell_pair(state, reference, origin)
    delta = np.zeros((duration, length), dtype=float)
    alive = True
    for time in range(duration):
        if not alive:
            break

        def observe(site: int) -> None:
            nonlocal alive
            before = state.entropy([reference])
            state.measure_z(site)
            drop = before - state.entropy([reference])
            if drop:
                column = _signed_distance(site, origin, length) + length // 2
                delta[time, column] += drop
                alive = False

        _random_layer(
            state,
            length,
            pre_layers + time,
            post_rate,
            True,
            rng,
            measurement_observer=observe,
        )
    return delta


def _partial_record_curve(parameters: dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    length = int(parameters["L"])
    duration = int(parameters["duration"])
    cutoff = parameters["cutoff"]
    state = MixedStabilizerState.product_zero(length + 1)
    reference = length
    origin = length // 2
    insert_bell_pair(state, reference, origin)
    curve = np.empty(duration + 1, dtype=float)
    curve[0] = 1.0
    cliffords = two_qubit_symplectic_group()
    for time in range(duration):
        for first, second in _pairs(length, time, True):
            state.apply_two_qubit(
                first, second, cliffords[int(rng.integers(len(cliffords)))]
            )
        for site_value in np.flatnonzero(rng.random(length) < float(parameters["rate"])):
            site = int(site_value)
            recorded = cutoff is None or _distance(site, origin, length, True) <= int(cutoff)
            state.measure_z(site, record_outcome=recorded)
        curve[time + 1] = state.entropy([reference])
    return curve


def _mutual_information_curve(parameters: dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    length = int(parameters["L"])
    state = StabilizerState.product_zero(length + 2)
    references = (length, length + 1)
    pre_layers = int(parameters["pre_layers"])
    rate = float(parameters["rate"])
    periodic = bool(parameters["periodic"])
    if pre_layers:
        _evolve(state, length, pre_layers, rate, periodic, rng)
    branch = parameters["branch"]
    if branch in ("surface", "bulk", "mixed"):
        sites = (0, length // 2)
    elif branch == "end_to_end":
        sites = (0, length - 1)
    else:
        raise ValueError(f"unknown correlation branch: {branch}")
    insert_bell_pair(state, references[0], sites[0])
    insert_bell_pair(state, references[1], sites[1])
    post_layers = int(parameters["post_layers"])
    curve = np.empty(post_layers + 1, dtype=float)
    curve[0] = state.mutual_information([references[0]], [references[1]])
    for time in range(post_layers):
        _random_layer(
            state,
            length,
            pre_layers + time,
            rate,
            periodic,
            rng,
        )
        curve[time + 1] = state.mutual_information([references[0]], [references[1]])
    return curve


def _purification_curve(parameters: dict[str, Any], rng: np.random.Generator) -> np.ndarray:
    length = int(parameters["L"])
    reference_count = int(parameters["references"])
    state = StabilizerState.product_zero(length + reference_count)
    references = tuple(range(length, length + reference_count))
    center = length // 2 - reference_count // 2
    for reference, site in zip(references, range(center, center + reference_count)):
        insert_bell_pair(state, reference, site)
    post_layers = int(parameters["post_layers"])
    curve = np.empty(post_layers + 1, dtype=float)
    curve[0] = state.entropy(references)
    for time in range(post_layers):
        _random_layer(
            state,
            length,
            time,
            float(parameters["rate"]),
            True,
            rng,
        )
        curve[time + 1] = state.entropy(references)
    return curve


def simulate_trajectory(condition: Condition, rng: np.random.Generator, volume_rate: float) -> np.ndarray:
    if condition.target_id in ("T001", "T004"):
        return _single_reference_final(condition.parameters, rng)
    if condition.target_id == "T002":
        return _lightcone(condition.parameters, volume_rate, rng)
    if condition.target_id == "T003":
        return _partial_record_curve(condition.parameters, rng)
    if condition.target_id in ("T005", "T006"):
        return _mutual_information_curve(condition.parameters, rng)
    if condition.target_id == "T007":
        return _lightcone(condition.parameters, volume_rate, rng)
    if condition.target_id == "T008":
        return _purification_curve(condition.parameters, rng)
    raise ValueError(f"unsupported target: {condition.target_id}")


def output_shape(condition: Condition) -> tuple[int, ...]:
    parameters = condition.parameters
    if condition.target_id in ("T001", "T004"):
        return (1,)
    if condition.target_id in ("T002", "T007"):
        return (int(parameters["duration"]), int(parameters["L"]))
    if condition.target_id == "T003":
        return (int(parameters["duration"]) + 1,)
    if condition.target_id in ("T005", "T006", "T008"):
        return (int(parameters["post_layers"]) + 1,)
    raise ValueError(condition.target_id)


class PaperScaleCampaign:
    def __init__(
        self,
        config_path: Path,
        *,
        output_root: Path | None = None,
        smoke: bool = False,
    ):
        self.config_path = config_path.resolve()
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        if self.config.get("paper_id") != "1910.00020":
            raise ValueError("paper-scale config belongs to a different paper")
        self.config_hash = _canonical_hash(self.config)
        self.smoke = bool(smoke)
        self.conditions = build_conditions(self.config, smoke=self.smoke)
        configured = Path(self.config["execution"]["output_root"])
        if output_root is None:
            workspace = self.config_path.parents[1]
            suffix = "_smoke" if smoke else ""
            output_root = workspace / f"{configured}{suffix}"
        self.output_root = output_root.resolve()
        self.by_id = {condition.condition_id: condition for condition in self.conditions}

    def _seed(self, condition: Condition, trajectory_id: int) -> int:
        stream_id = condition.condition_id
        if condition.target_id == "T003":
            stream_id = (
                f"T003_p{_float_label(float(condition.parameters['rate']))}_shared_circuit"
            )
        return trajectory_seed(
            int(self.config["parameters"]["seed_base"]),
            stream_id,
            trajectory_id,
        )

    def plan(self) -> dict[str, Any]:
        payload = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": "smoke" if self.smoke else "paper_scale",
            "config_sha256": self.config_hash,
            "conditions": len(self.conditions),
            "shards": sum(condition.shards for condition in self.conditions),
            "trajectories": sum(condition.trajectories for condition in self.conditions),
            "target_counts": {
                target_id: sum(
                    condition.trajectories
                    for condition in self.conditions
                    if condition.target_id == target_id
                )
                for target_id in TARGET_IDS
            },
            "conditions_detail": [
                {
                    "target_id": condition.target_id,
                    "condition_id": condition.condition_id,
                    "parameters": condition.parameters,
                    "trajectories": condition.trajectories,
                    "shards": condition.shards,
                    "identity_sha256": condition.identity_hash,
                }
                for condition in self.conditions
            ],
        }
        _atomic_json(self.output_root / "plan.json", payload)
        return payload

    def _shard_path(self, condition: Condition, shard: int) -> Path:
        return self.output_root / "shards" / condition.condition_id / f"shard-{shard:04d}.npz"

    def _load_shard(
        self, condition: Condition, shard: int
    ) -> tuple[np.ndarray, np.ndarray, list[int]]:
        path = self._shard_path(condition, shard)
        if not path.exists():
            shape = output_shape(condition)
            return np.zeros(shape), np.zeros(shape), []
        with np.load(path, allow_pickle=False) as payload:
            if str(payload["config_sha256"].item()) != self.config_hash:
                raise ValueError(f"config hash mismatch in {path}")
            if str(payload["condition_sha256"].item()) != condition.identity_hash:
                raise ValueError(f"condition hash mismatch in {path}")
            if int(payload["shard"].item()) != shard:
                raise ValueError(f"shard identity mismatch in {path}")
            return (
                np.asarray(payload["sum"], dtype=float),
                np.asarray(payload["sum_sq"], dtype=float),
                [int(item) for item in payload["completed_ids"]],
            )

    def _save_shard(
        self,
        condition: Condition,
        shard: int,
        total: np.ndarray,
        total_sq: np.ndarray,
        completed: Iterable[int],
    ) -> None:
        _atomic_npz(
            self._shard_path(condition, shard),
            schema_version=np.asarray(1),
            paper_id=np.asarray(self.config["paper_id"]),
            config_sha256=np.asarray(self.config_hash),
            condition_sha256=np.asarray(condition.identity_hash),
            condition_id=np.asarray(condition.condition_id),
            target_id=np.asarray(condition.target_id),
            shard=np.asarray(shard),
            completed_ids=np.asarray(tuple(completed), dtype=np.int64),
            sum=total,
            sum_sq=total_sq,
        )

    def run_shard(self, condition_id: str, shard: int, *, resume: bool = True) -> dict[str, Any]:
        condition = self.by_id[condition_id]
        if not 0 <= shard < condition.shards:
            raise ValueError(f"shard must be in [0, {condition.shards})")
        expected = list(range(shard, condition.trajectories, condition.shards))
        if resume:
            total, total_sq, completed = self._load_shard(condition, shard)
        else:
            shape = output_shape(condition)
            total, total_sq, completed = np.zeros(shape), np.zeros(shape), []
        if completed != expected[: len(completed)]:
            raise ValueError("checkpoint trajectory ids are not an expected prefix")
        for trajectory_id in expected[len(completed) :]:
            rng = np.random.default_rng(self._seed(condition, trajectory_id))
            value = simulate_trajectory(
                condition, rng, float(self.config["parameters"]["volume_rate"])
            )
            if value.shape != total.shape or not np.all(np.isfinite(value)):
                raise RuntimeError(
                    f"invalid trajectory output for {condition.condition_id}: {value.shape}"
                )
            total += value
            total_sq += value * value
            completed.append(trajectory_id)
            self._save_shard(condition, shard, total, total_sq, completed)
        path = self._shard_path(condition, shard)
        return {
            "status": "complete",
            "condition_id": condition.condition_id,
            "target_id": condition.target_id,
            "shard": shard,
            "completed": len(completed),
            "path": str(path),
            "sha256": _sha256(path),
        }

    def run_condition(self, condition_id: str, *, resume: bool = True) -> list[dict[str, Any]]:
        condition = self.by_id[condition_id]
        return [
            self.run_shard(condition_id, shard, resume=resume)
            for shard in range(condition.shards)
        ]

    def run_all(self, *, resume: bool = True, workers: int = 1) -> dict[str, Any]:
        self.plan()
        specifications = [
            (condition.condition_id, shard, resume)
            for condition in self.conditions
            for shard in range(condition.shards)
        ]
        if workers < 1:
            raise ValueError("workers must be positive")
        if workers == 1:
            results = [_run_worker_local(self, item) for item in specifications]
        else:
            with ProcessPoolExecutor(
                max_workers=workers,
                initializer=_initialize_worker,
                initargs=(str(self.config_path), str(self.output_root), self.smoke),
            ) as executor:
                results = list(executor.map(_run_worker, specifications, chunksize=1))
        completed = len(results)
        payload = {
            "status": "complete",
            "mode": "smoke" if self.smoke else "paper_scale",
            "config_sha256": self.config_hash,
            "completed_shards": completed,
            "workers": workers,
        }
        _atomic_json(self.output_root / "run_summary.json", payload)
        return payload

    def _aggregate_condition(
        self, condition: Condition
    ) -> tuple[np.ndarray, np.ndarray, int, list[str]]:
        total = np.zeros(output_shape(condition))
        total_sq = np.zeros_like(total)
        completed_ids: list[int] = []
        hashes: list[str] = []
        for shard in range(condition.shards):
            local_sum, local_sum_sq, completed = self._load_shard(condition, shard)
            expected = list(range(shard, condition.trajectories, condition.shards))
            if completed != expected:
                raise RuntimeError(
                    f"cannot aggregate incomplete shard {condition.condition_id}/{shard}"
                )
            total += local_sum
            total_sq += local_sum_sq
            completed_ids.extend(completed)
            hashes.append(_sha256(self._shard_path(condition, shard)))
        if sorted(completed_ids) != list(range(condition.trajectories)):
            raise RuntimeError(f"trajectory coverage mismatch for {condition.condition_id}")
        count = len(completed_ids)
        mean = total / count
        if count > 1:
            variance = np.maximum((total_sq - count * mean * mean) / (count - 1), 0.0)
            stderr = np.sqrt(variance / count)
        else:
            stderr = np.zeros_like(mean)
        return mean, stderr, count, hashes

    def aggregate_target(self, target_id: str) -> dict[str, Any]:
        selected = [condition for condition in self.conditions if condition.target_id == target_id]
        arrays: dict[str, Any] = {
            "schema_version": np.asarray(1),
            "paper_id": np.asarray(self.config["paper_id"]),
            "target_id": np.asarray(target_id),
            "config_sha256": np.asarray(self.config_hash),
        }
        detail: list[dict[str, Any]] = []
        for index, condition in enumerate(selected):
            mean, stderr, count, shard_hashes = self._aggregate_condition(condition)
            value_key = f"mean_{index:04d}"
            stderr_key = f"stderr_{index:04d}"
            arrays[value_key] = mean
            arrays[stderr_key] = stderr
            detail.append(
                {
                    "condition_id": condition.condition_id,
                    "parameters": condition.parameters,
                    "trajectories": count,
                    "mean_key": value_key,
                    "stderr_key": stderr_key,
                    "shard_sha256": shard_hashes,
                }
            )
        arrays["condition_manifest_json"] = np.asarray(
            json.dumps(detail, sort_keys=True, separators=(",", ":"))
        )
        output = self.output_root / "aggregates" / f"{target_id}.npz"
        _atomic_npz(output, **arrays)
        manifest = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "target_id": target_id,
            "config_sha256": self.config_hash,
            "conditions": detail,
            "aggregate_path": str(output),
            "aggregate_sha256": _sha256(output),
            "generated_data_provenance": "independent_numerics",
            "source_pixels_used_as_numeric_input": False,
        }
        _atomic_json(output.with_suffix(".manifest.json"), manifest)
        return manifest

    def aggregate_all(self) -> dict[str, Any]:
        targets = [self.aggregate_target(target_id) for target_id in TARGET_IDS]
        payload = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": "smoke" if self.smoke else "paper_scale",
            "config_sha256": self.config_hash,
            "targets": targets,
            "numerical_data_frozen": True,
        }
        _atomic_json(self.output_root / "aggregate_manifest.json", payload)
        return payload


def load_campaign(
    config_path: Path,
    *,
    output_root: Path | None = None,
    smoke: bool = False,
) -> PaperScaleCampaign:
    return PaperScaleCampaign(config_path, output_root=output_root, smoke=smoke)


def _run_worker_local(
    campaign: PaperScaleCampaign, specification: tuple[str, int, bool]
) -> dict[str, Any]:
    condition_id, shard, resume = specification
    return campaign.run_shard(condition_id, shard, resume=resume)
