"""Paper-scale campaign runner for every numerical target in arXiv:2005.09722.

The core object is a :class:`Campaign`.  It expands the declared physics
conditions into deterministic shards, evolves one trajectory at a time, and
atomically checkpoints scalar observable records.  Full orbital matrices are
never written to disk or accumulated across trajectories.  In particular,
the six 5000-trajectory histogram targets retain only one scalar entropy per
trajectory.

This module is an executable numerical channel, not a claim that the paper's
formula/reference gates have passed.  Those independent lifecycle blockers
are carried into the machine acceptance report by :meth:`Campaign.accept`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator

import numpy as np

from backends import evolve_qsd_backend
from monitored_fermion import (
    QSDConfig,
    cft_fit,
    cross_ratio,
    density_correlation_components,
    evolve_qsd,
    evolve_quantum_jumps,
    evolve_random_hopping_qsd,
    fixed_separation_mutual_information,
    interval_entropy,
    mutual_information,
    orthonormality_residual,
    qsd_step,
    spatial_correlations,
    subsystem_entropy,
    two_time_on_site_correlation,
)

TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 32))
FAMILY_ORDER = (
    "regular_qsd",
    "time_qsd",
    "quantum_jump",
    "qsdc_control",
    "autocorrelation",
    "density_identity",
    "random_hopping",
    "histogram_qsd",
    "histogram_qsdc",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _write_csv_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty aggregate: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    temporary = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _slug_number(value: float) -> str:
    return f"{value:.12g}".replace("-", "m").replace(".", "p")


def _length_grid(length: int, count: int) -> list[int]:
    upper = max(2, length // 2)
    return [
        int(value)
        for value in np.unique(np.rint(np.geomspace(2, upper, count)).astype(int))
    ]


def _distance_grid(length: int, count: int) -> list[int]:
    upper = max(1, length // 2)
    return [
        int(value)
        for value in np.unique(np.rint(np.geomspace(1, upper, count)).astype(int))
    ]


@dataclass(frozen=True)
class Condition:
    family: str
    condition_id: str
    parameters: dict[str, Any]
    trajectories: int
    shards: int
    global_start: int

    def indices_for_shard(self, shard_id: int) -> tuple[int, ...]:
        if shard_id < 0 or shard_id >= self.shards:
            raise ValueError(
                f"shard {shard_id} outside [0, {self.shards}) for {self.condition_id}"
            )
        start = self.trajectories * shard_id // self.shards
        stop = self.trajectories * (shard_id + 1) // self.shards
        return tuple(range(start, stop))

    def global_index(self, trajectory_index: int) -> int:
        return self.global_start + trajectory_index


@dataclass
class OnlineStats:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    minimum: float = math.inf
    maximum: float = -math.inf

    def add(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)

    def row(self) -> dict[str, Any]:
        return {
            "samples": self.count,
            "mean": self.mean,
            "std": math.sqrt(self.m2 / (self.count - 1)) if self.count > 1 else 0.0,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


class Campaign:
    """Validated paper-scale plan plus deterministic execution state."""

    def __init__(
        self,
        config: dict[str, Any],
        *,
        config_path: Path,
        output_root: Path | None = None,
        smoke: bool = False,
        backend: str | None = None,
    ) -> None:
        self.config = config
        self.config_path = config_path.resolve()
        self.workspace = self.config_path.parent.parent.resolve()
        configured_output = Path(str(config["execution"]["output_root"]))
        self.output_root = (
            output_root.resolve()
            if output_root is not None
            else (self.workspace / configured_output).resolve()
        )
        self.smoke = smoke
        self.backend = backend or str(config["execution"]["default_backend"])
        self.config_hash = _digest(config)
        self.validate()
        self.conditions = self._build_conditions()

    @classmethod
    def load(
        cls,
        config_path: Path,
        *,
        output_root: Path | None = None,
        smoke: bool = False,
        backend: str | None = None,
    ) -> "Campaign":
        with config_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(
            payload,
            config_path=config_path,
            output_root=output_root,
            smoke=smoke,
            backend=backend,
        )

    @property
    def mode(self) -> str:
        return "smoke" if self.smoke else "paper_scale"

    def validate(self) -> None:
        commitment_payload = dict(self.config)
        committed_parameters = dict(self.config.get("parameters", {}))
        expected_commitment = str(
            committed_parameters.pop("campaign_contract_sha256", "")
        )
        commitment_payload["parameters"] = committed_parameters
        actual_commitment = _digest(commitment_payload)
        if expected_commitment != actual_commitment:
            raise ValueError(
                "campaign_contract_sha256 does not bind the complete paper-scale config"
            )
        if self.config.get("paper_id") != "2005.09722":
            raise ValueError("paper_id must be 2005.09722")
        if int(self.config.get("schema_version", 0)) != 2:
            raise ValueError("paper-scale config schema_version must be 2")
        target_map = self.config.get("target_map", {})
        if tuple(sorted(target_map)) != TARGET_IDS:
            raise ValueError("target_map must cover T001-T031 exactly once")
        families = self.config.get("families", {})
        if tuple(families) != FAMILY_ORDER:
            raise ValueError(f"families must be ordered exactly as {FAMILY_ORDER}")
        mapped = [str(value) for value in target_map.values()]
        unknown = sorted(set(mapped) - set(FAMILY_ORDER))
        if unknown:
            raise ValueError(f"target_map names unknown families: {unknown}")
        for family in FAMILY_ORDER:
            declared = sorted(str(value) for value in families[family]["target_ids"])
            expected = sorted(
                target for target, name in target_map.items() if name == family
            )
            if declared != expected:
                raise ValueError(f"{family} target_ids disagree with target_map")
            trajectories = int(families[family]["trajectories"])
            shards = int(families[family]["shards"])
            if trajectories < 1 or shards < 1 or shards > trajectories:
                raise ValueError(f"invalid trajectories/shards for {family}")
        parameters = self.config["parameters"]
        if float(parameters["dt"]) != 0.05:
            raise ValueError("paper-scale dt must preserve the published 0.05")
        regular_sizes = [int(value) for value in families["regular_qsd"]["sizes"]]
        if regular_sizes != [200, 400, 600, 800]:
            raise ValueError("regular_qsd must declare paper sizes 200,400,600,800")
        for name in ("histogram_qsd", "histogram_qsdc"):
            if int(families[name]["length"]) != 200:
                raise ValueError(f"{name} must use published L=200")
            if int(families[name]["trajectories"]) != 5000:
                raise ValueError(f"{name} must use published 5000 trajectories")
        density = families["density_identity"]
        if int(density["trajectories"]) != 250 or density["groups"] != [
            "product",
            "density_density",
        ]:
            raise ValueError("density identity requires independent 250+250 ensembles")
        forbidden_tokens = ("raw/", "references/", "figure", ".png", ".pdf")
        flattened = _canonical_json(self.config).lower()
        if any(token in flattened for token in forbidden_tokens):
            raise ValueError(
                "numerical config must not depend on source/reference images"
            )
        if self.backend not in {"numpy", "cupy"}:
            raise ValueError("backend must be numpy or cupy")

    def _steady_time(self, gamma: float, maximum: float | None = None) -> float:
        values = self.config["parameters"]["steady_state"]
        if gamma == 0.0:
            return float(values["gamma_zero_time"])
        upper = float(values["maximum"] if maximum is None else maximum)
        return float(
            np.clip(
                float(values["gamma_time_product"]) / gamma,
                float(values["minimum"]),
                upper,
            )
        )

    def _condition_rows(self, family: str) -> list[dict[str, Any]]:
        cfg = self.config["families"][family]
        rows: list[dict[str, Any]] = []
        if family == "regular_qsd":
            for length in cfg["sizes"]:
                for gamma in cfg["gammas"]:
                    rows.append(
                        {
                            "length": int(length),
                            "gamma": float(gamma),
                            "protocol": "qsd",
                        }
                    )
        elif family in {
            "time_qsd",
            "quantum_jump",
            "qsdc_control",
            "autocorrelation",
            "random_hopping",
        }:
            protocol = "qsdc" if family == "qsdc_control" else "qsd"
            for gamma in cfg["gammas"]:
                rows.append(
                    {
                        "length": int(cfg["length"]),
                        "gamma": float(gamma),
                        "protocol": protocol,
                    }
                )
        elif family == "density_identity":
            for group in cfg["groups"]:
                rows.append(
                    {
                        "length": int(cfg["length"]),
                        "gamma": float(cfg["gamma"]),
                        "protocol": "qsd",
                        "group": str(group),
                    }
                )
        elif family in {"histogram_qsd", "histogram_qsdc"}:
            protocol = "qsd" if family == "histogram_qsd" else "qsdc"
            for gamma in cfg["gammas"]:
                rows.append(
                    {
                        "length": int(cfg["length"]),
                        "gamma": float(gamma),
                        "protocol": protocol,
                    }
                )
        else:  # pragma: no cover - validate guards this branch
            raise AssertionError(family)
        return rows

    def _smoke_parameters(self, family: str, row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["length"] = int(self.config["smoke"]["length"])
        result["gamma"] = float(self.config["smoke"]["gamma"])
        result["smoke_original_condition"] = self._condition_id(family, row)
        return result

    @staticmethod
    def _condition_id(family: str, parameters: dict[str, Any]) -> str:
        parts = [
            family,
            f"L{int(parameters['length'])}",
            f"g{_slug_number(float(parameters['gamma']))}",
        ]
        if "group" in parameters:
            parts.append(str(parameters["group"]))
        return "-".join(parts)

    def _build_conditions(self) -> tuple[Condition, ...]:
        conditions: list[Condition] = []
        global_start = 0
        for family in FAMILY_ORDER:
            cfg = self.config["families"][family]
            rows = self._condition_rows(family)
            if self.smoke:
                smoke_rows = rows if family == "density_identity" else rows[:1]
                rows = [self._smoke_parameters(family, row) for row in smoke_rows]
            trajectories = 1 if self.smoke else int(cfg["trajectories"])
            shards = 1 if self.smoke else int(cfg["shards"])
            for row in rows:
                condition_id = self._condition_id(family, row)
                conditions.append(
                    Condition(
                        family=family,
                        condition_id=condition_id,
                        parameters=row,
                        trajectories=trajectories,
                        shards=shards,
                        global_start=global_start,
                    )
                )
                global_start += trajectories
        return tuple(conditions)

    def plan(self) -> dict[str, Any]:
        shards = []
        seen_indices: set[int] = set()
        seen_seeds: set[int] = set()
        for condition in self.conditions:
            for shard_id in range(condition.shards):
                indices = condition.indices_for_shard(shard_id)
                globals_ = [condition.global_index(value) for value in indices]
                seeds = [self._seed(value) for value in globals_]
                overlap = seen_indices.intersection(globals_)
                seed_overlap = seen_seeds.intersection(seeds)
                if overlap or seed_overlap:
                    raise AssertionError(
                        "campaign seed/global-index allocation overlaps"
                    )
                seen_indices.update(globals_)
                seen_seeds.update(seeds)
                shards.append(
                    {
                        "family": condition.family,
                        "condition_id": condition.condition_id,
                        "shard_id": shard_id,
                        "trajectory_start": indices[0],
                        "trajectory_stop_exclusive": indices[-1] + 1,
                        "global_start": globals_[0],
                        "global_stop_exclusive": globals_[-1] + 1,
                        "seed_start": seeds[0],
                        "seed_stop_inclusive": seeds[-1],
                        "checkpoint": str(self._checkpoint_path(condition, shard_id)),
                    }
                )
        return {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": self.mode,
            "config_sha256": self.config_hash,
            "conditions": len(self.conditions),
            "shards": len(shards),
            "trajectories": len(seen_indices),
            "deterministic_disjoint_seed_allocation": True,
            "shard_plan": shards,
        }

    def _seed(self, global_index: int) -> int:
        return int(self.config["parameters"]["seed_base"]) + global_index

    def _checkpoint_path(self, condition: Condition, shard_id: int) -> Path:
        return (
            self.output_root
            / "checkpoints"
            / self.mode
            / condition.family
            / condition.condition_id
            / f"shard-{shard_id:03d}.json"
        )

    def _portable_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.workspace))
        except ValueError:
            return str(path.resolve())

    def _resolve_portable_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.workspace / path

    def _checkpoint_identity(
        self, condition: Condition, shard_id: int
    ) -> dict[str, Any]:
        return {
            "paper_id": self.config["paper_id"],
            "mode": self.mode,
            "config_sha256": self.config_hash,
            "backend": self.backend,
            "family": condition.family,
            "condition_id": condition.condition_id,
            "condition_parameters": condition.parameters,
            "shard_id": shard_id,
            "expected_trajectory_indices": list(condition.indices_for_shard(shard_id)),
        }

    def _validate_checkpoint_payload(
        self,
        condition: Condition,
        shard_id: int,
        checkpoint: dict[str, Any],
        *,
        require_complete: bool,
    ) -> None:
        expected = set(condition.indices_for_shard(shard_id))
        completed_values = [
            int(value) for value in checkpoint.get("completed_trajectory_indices", [])
        ]
        completed = set(completed_values)
        if len(completed_values) != len(completed):
            raise ValueError(
                "checkpoint contains duplicate completed trajectory indices"
            )
        if not completed.issubset(expected):
            raise ValueError("checkpoint completed indices escape the declared shard")
        if require_complete and completed != expected:
            raise ValueError("complete checkpoint does not cover its declared shard")

        record_trajectories: set[int] = set()
        record_identities: set[tuple[Any, ...]] = set()
        for record in checkpoint.get("records", []):
            if not isinstance(record, dict) or not self._scalar_record(record):
                raise ValueError("checkpoint records must contain scalar values only")
            trajectory_index = int(record["trajectory_index"])
            if trajectory_index not in completed:
                raise ValueError(
                    "checkpoint record belongs to an incomplete trajectory"
                )
            global_index = condition.global_index(trajectory_index)
            required_values = {
                "family": condition.family,
                "condition_id": condition.condition_id,
                "global_trajectory_index": global_index,
                "seed": self._seed(global_index),
                "length": int(condition.parameters["length"]),
                "gamma": float(condition.parameters["gamma"]),
                "protocol": str(condition.parameters["protocol"]),
                "group": condition.parameters.get("group"),
            }
            if any(record.get(key) != value for key, value in required_values.items()):
                raise ValueError(
                    "checkpoint record metadata disagrees with its condition"
                )
            identity = (
                trajectory_index,
                record.get("metric"),
                record.get("coordinate_name"),
                record.get("coordinate"),
                record.get("auxiliary_name"),
                record.get("auxiliary"),
            )
            if identity in record_identities:
                raise ValueError("checkpoint contains a duplicate observable record")
            record_identities.add(identity)
            record_trajectories.add(trajectory_index)
        if record_trajectories != completed:
            raise ValueError(
                "checkpoint has no scalar records for a completed trajectory"
            )

    def _load_checkpoint(
        self, condition: Condition, shard_id: int, *, resume: bool
    ) -> dict[str, Any]:
        identity = self._checkpoint_identity(condition, shard_id)
        path = self._checkpoint_path(condition, shard_id)
        if resume and path.exists():
            with path.open(encoding="utf-8") as handle:
                checkpoint = json.load(handle)
            for key, value in identity.items():
                if checkpoint.get(key) != value:
                    raise ValueError(f"checkpoint identity mismatch for {path}: {key}")
            if checkpoint.get("records_sha256") != _digest(
                checkpoint.get("records", [])
            ):
                raise ValueError(f"checkpoint record hash mismatch for {path}")
            self._validate_checkpoint_payload(
                condition,
                shard_id,
                checkpoint,
                require_complete=checkpoint.get("status") == "complete",
            )
            return checkpoint
        return {
            "schema_version": 1,
            **identity,
            "status": "running",
            "completed_trajectory_indices": [],
            "records": [],
            "records_sha256": _digest([]),
        }

    def run_shard(
        self,
        family: str,
        condition_id: str,
        shard_id: int,
        *,
        resume: bool = True,
    ) -> dict[str, Any]:
        condition = next(
            (
                item
                for item in self.conditions
                if item.family == family and item.condition_id == condition_id
            ),
            None,
        )
        if condition is None:
            raise ValueError(f"unknown condition: {family}/{condition_id}")
        checkpoint = self._load_checkpoint(condition, shard_id, resume=resume)
        completed = {int(value) for value in checkpoint["completed_trajectory_indices"]}
        started = perf_counter()
        for trajectory_index in condition.indices_for_shard(shard_id):
            if trajectory_index in completed:
                continue
            global_index = condition.global_index(trajectory_index)
            seed = self._seed(global_index)
            new_records = self._simulate_trajectory(
                condition,
                trajectory_index=trajectory_index,
                global_index=global_index,
                seed=seed,
            )
            if any(not self._scalar_record(record) for record in new_records):
                raise AssertionError(
                    "checkpoint attempted to retain a non-scalar value"
                )
            checkpoint["records"].extend(new_records)
            checkpoint["completed_trajectory_indices"].append(trajectory_index)
            checkpoint["records_sha256"] = _digest(checkpoint["records"])
            checkpoint["status"] = "running"
            self._validate_checkpoint_payload(
                condition, shard_id, checkpoint, require_complete=False
            )
            _write_json_atomic(self._checkpoint_path(condition, shard_id), checkpoint)
            completed.add(trajectory_index)
        checkpoint["status"] = "complete"
        checkpoint["wall_seconds_last_invocation"] = perf_counter() - started
        checkpoint["records_sha256"] = _digest(checkpoint["records"])
        self._validate_checkpoint_payload(
            condition, shard_id, checkpoint, require_complete=True
        )
        _write_json_atomic(self._checkpoint_path(condition, shard_id), checkpoint)
        return {
            "family": family,
            "condition_id": condition_id,
            "shard_id": shard_id,
            "status": "complete",
            "completed_trajectories": len(completed),
            "record_count": len(checkpoint["records"]),
            "checkpoint": str(self._checkpoint_path(condition, shard_id)),
        }

    @staticmethod
    def _scalar_record(record: dict[str, Any]) -> bool:
        scalar_types = (str, int, float, bool, type(None))
        return all(isinstance(value, scalar_types) for value in record.values())

    def run_family(self, family: str, *, resume: bool = True) -> list[dict[str, Any]]:
        if family not in FAMILY_ORDER:
            raise ValueError(f"unknown family: {family}")
        results = []
        for condition in self.conditions:
            if condition.family != family:
                continue
            for shard_id in range(condition.shards):
                results.append(
                    self.run_shard(
                        family,
                        condition.condition_id,
                        shard_id,
                        resume=resume,
                    )
                )
        return results

    def run_all(self, *, resume: bool = True) -> dict[str, Any]:
        plan_path = self.output_root / "paper_scale_plan.json"
        _write_json_atomic(plan_path, self.plan())
        results: list[dict[str, Any]] = []
        for family in FAMILY_ORDER:
            results.extend(self.run_family(family, resume=resume))
        payload = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": self.mode,
            "status": "complete",
            "config_sha256": self.config_hash,
            "backend": self.backend,
            "shards": results,
        }
        _write_json_atomic(self.output_root / "run_summary.json", payload)
        return payload

    def _common_record(
        self,
        condition: Condition,
        *,
        trajectory_index: int,
        global_index: int,
        seed: int,
    ) -> dict[str, Any]:
        return {
            "family": condition.family,
            "condition_id": condition.condition_id,
            "trajectory_index": trajectory_index,
            "global_trajectory_index": global_index,
            "seed": seed,
            "length": int(condition.parameters["length"]),
            "gamma": float(condition.parameters["gamma"]),
            "protocol": str(condition.parameters["protocol"]),
            "group": condition.parameters.get("group"),
        }

    def _record(
        self,
        common: dict[str, Any],
        *,
        metric: str,
        value: float,
        coordinate_name: str = "none",
        coordinate: float = 0.0,
        auxiliary_name: str = "none",
        auxiliary: float = 0.0,
    ) -> dict[str, Any]:
        return {
            **common,
            "metric": metric,
            "coordinate_name": coordinate_name,
            "coordinate": float(coordinate),
            "auxiliary_name": auxiliary_name,
            "auxiliary": float(auxiliary),
            "value": float(value),
        }

    def _qsd_state(self, condition: Condition, seed: int) -> np.ndarray:
        length = int(condition.parameters["length"])
        gamma = float(condition.parameters["gamma"])
        protocol = str(condition.parameters["protocol"])
        t_final = self._trajectory_final_time(condition.family, gamma)
        return evolve_qsd_backend(
            length=length,
            gamma=gamma,
            dt=float(self.config["parameters"]["dt"]),
            t_final=t_final,
            protocol=protocol,
            seed=seed,
            backend_name=self.backend,
        )

    def _trajectory_final_time(self, family: str, gamma: float) -> float:
        if self.smoke:
            return float(self.config["smoke"]["t_final"])
        cfg = self.config["families"][family]
        if "t_final" in cfg:
            return float(cfg["t_final"])
        maximum = float(cfg["steady_time_max"]) if "steady_time_max" in cfg else None
        return self._steady_time(gamma, maximum=maximum)

    def _simulate_trajectory(
        self,
        condition: Condition,
        *,
        trajectory_index: int,
        global_index: int,
        seed: int,
    ) -> list[dict[str, Any]]:
        common = self._common_record(
            condition,
            trajectory_index=trajectory_index,
            global_index=global_index,
            seed=seed,
        )
        family = condition.family
        if family == "time_qsd":
            return self._time_records(condition, common, seed)
        if family == "autocorrelation":
            return self._autocorrelation_records(condition, common, seed)
        if family == "quantum_jump":
            state = evolve_quantum_jumps(
                length=int(condition.parameters["length"]),
                gamma=float(condition.parameters["gamma"]),
                t_final=self._trajectory_final_time(
                    family, float(condition.parameters["gamma"])
                ),
                seed=seed,
            )
        elif family == "random_hopping":
            state = evolve_random_hopping_qsd(
                QSDConfig(
                    length=int(condition.parameters["length"]),
                    gamma=float(condition.parameters["gamma"]),
                    dt=float(self.config["parameters"]["dt"]),
                    t_final=self._trajectory_final_time(
                        family, float(condition.parameters["gamma"])
                    ),
                    protocol="qsd",
                ),
                seed=seed,
                update_interval=float(
                    self.config["families"][family]["update_interval"]
                ),
            )
        else:
            state = self._qsd_state(condition, seed)
        if family == "regular_qsd":
            return self._regular_records(condition, common, state)
        if family == "quantum_jump":
            return self._entropy_mi_records(condition, common, state)
        if family == "qsdc_control":
            return [
                self._record(
                    common,
                    metric="fixed_mutual_information",
                    value=fixed_separation_mutual_information(state),
                ),
                self._record(
                    common,
                    metric="half_entropy",
                    value=subsystem_entropy(state, range(state.shape[0] // 2)),
                ),
                self._record(
                    common,
                    metric="orthonormality_residual",
                    value=orthonormality_residual(state),
                ),
            ]
        if family == "density_identity":
            return self._density_records(condition, common, state)
        if family == "random_hopping":
            return self._entropy_records(condition, common, state)
        if family in {"histogram_qsd", "histogram_qsdc"}:
            # The full state goes out of scope immediately after this scalar is
            # produced; neither the checkpoint nor aggregation retains it.
            return [
                self._record(
                    common,
                    metric="half_entropy",
                    value=subsystem_entropy(state, range(state.shape[0] // 2)),
                ),
                self._record(
                    common,
                    metric="orthonormality_residual",
                    value=orthonormality_residual(state),
                ),
            ]
        raise AssertionError(family)

    def _entropy_records(
        self, condition: Condition, common: dict[str, Any], state: np.ndarray
    ) -> list[dict[str, Any]]:
        count = int(
            self.config["families"][condition.family].get("subsystem_points", 18)
        )
        rows = [
            self._record(
                common,
                metric="interval_entropy",
                coordinate_name="subsystem",
                coordinate=subsystem,
                auxiliary_name="chord_coordinate",
                auxiliary=float(np.sin(np.pi * subsystem / state.shape[0])),
                value=interval_entropy(state, 0, subsystem),
            )
            for subsystem in _length_grid(state.shape[0], count)
        ]
        rows.append(
            self._record(
                common,
                metric="orthonormality_residual",
                value=orthonormality_residual(state),
            )
        )
        return rows

    def _entropy_mi_records(
        self, condition: Condition, common: dict[str, Any], state: np.ndarray
    ) -> list[dict[str, Any]]:
        rows = self._entropy_records(condition, common, state)
        rows.append(
            self._record(
                common,
                metric="fixed_mutual_information",
                value=fixed_separation_mutual_information(state),
            )
        )
        return rows

    def _regular_records(
        self, condition: Condition, common: dict[str, Any], state: np.ndarray
    ) -> list[dict[str, Any]]:
        cfg = self.config["families"]["regular_qsd"]
        rows = self._entropy_mi_records(condition, common, state)
        length = state.shape[0]
        rows.append(
            self._record(
                common,
                metric="half_entropy",
                value=subsystem_entropy(state, range(length // 2)),
            )
        )
        for distance, value in zip(
            _distance_grid(length, int(cfg["distance_points"])),
            spatial_correlations(
                state, _distance_grid(length, int(cfg["distance_points"]))
            ),
            strict=True,
        ):
            rows.append(
                self._record(
                    common,
                    metric="spatial_correlation",
                    coordinate_name="distance",
                    coordinate=distance,
                    auxiliary_name="scaled_distance",
                    auxiliary=length / np.pi * np.sin(np.pi * distance / length),
                    value=float(value),
                )
            )
        cross_cfg = cfg["cross_ratio"]
        gamma = float(condition.parameters["gamma"])
        cross_enabled = self.smoke or (
            length == int(cross_cfg["length"])
            and any(
                math.isclose(gamma, float(item), abs_tol=1e-12)
                for item in cross_cfg["gammas"]
            )
        )
        if cross_enabled:
            blocks = [1] if self.smoke else cross_cfg["blocks"]
            gaps = [1] if self.smoke else cross_cfg["gaps"]
            for block in blocks:
                for gap in gaps:
                    if 2 * int(block) + int(gap) >= length:
                        continue
                    endpoints = (
                        0,
                        int(block),
                        int(block) + int(gap),
                        2 * int(block) + int(gap),
                    )
                    eta = cross_ratio(endpoints, length)
                    interval_a = range(0, int(block))
                    interval_b = range(int(block) + int(gap), 2 * int(block) + int(gap))
                    rows.append(
                        self._record(
                            common,
                            metric="cross_ratio_mutual_information",
                            coordinate_name="eta",
                            coordinate=eta,
                            auxiliary_name="block",
                            auxiliary=int(block),
                            value=mutual_information(state, interval_a, interval_b),
                        )
                    )
        return rows

    def _time_records(
        self, condition: Condition, common: dict[str, Any], seed: int
    ) -> list[dict[str, Any]]:
        cfg = self.config["families"]["time_qsd"]
        sample_times = (
            [
                0.0,
                float(self.config["parameters"]["dt"]),
                float(self.config["smoke"]["t_final"]),
            ]
            if self.smoke
            else [float(value) for value in cfg["sample_times"]]
        )
        rows: list[dict[str, Any]] = []

        def capture(time: float, state: np.ndarray) -> None:
            rows.append(
                self._record(
                    common,
                    metric="half_entropy_time",
                    coordinate_name="time",
                    coordinate=time,
                    value=subsystem_entropy(state, range(state.shape[0] // 2)),
                )
            )

        final = evolve_qsd(
            QSDConfig(
                length=int(condition.parameters["length"]),
                gamma=float(condition.parameters["gamma"]),
                dt=float(self.config["parameters"]["dt"]),
                t_final=max(sample_times),
                protocol="qsd",
            ),
            seed=seed,
            sample_times=sample_times,
            callback=capture,
        )
        rows.append(
            self._record(
                common,
                metric="orthonormality_residual",
                value=orthonormality_residual(final),
            )
        )
        return rows

    def _autocorrelation_records(
        self, condition: Condition, common: dict[str, Any], seed: int
    ) -> list[dict[str, Any]]:
        cfg = self.config["families"]["autocorrelation"]
        dt = float(self.config["parameters"]["dt"])
        taus = (
            [0.0, dt, float(self.config["smoke"]["t_final"])]
            if self.smoke
            else [float(value) for value in cfg["taus"]]
        )
        reference = evolve_qsd(
            QSDConfig(
                length=int(condition.parameters["length"]),
                gamma=float(condition.parameters["gamma"]),
                dt=dt,
                t_final=self._trajectory_final_time(
                    "autocorrelation", float(condition.parameters["gamma"])
                ),
                protocol="qsd",
            ),
            seed=seed,
        )
        current = reference.copy()
        generator = np.random.default_rng(
            seed + int(self.config["parameters"]["lag_seed_offset"])
        )
        rows = [
            self._record(
                common,
                metric="two_time_on_site_correlation",
                coordinate_name="tau",
                coordinate=0.0,
                value=two_time_on_site_correlation(reference, current),
            )
        ]
        sample_index = 1
        for step in range(1, int(math.ceil(max(taus) / dt - 1e-12)) + 1):
            current = qsd_step(
                current,
                gamma=float(condition.parameters["gamma"]),
                dt=dt,
                generator=generator,
                protocol="qsd",
            )
            time = step * dt
            while sample_index < len(taus) and taus[sample_index] <= time + 1e-12:
                rows.append(
                    self._record(
                        common,
                        metric="two_time_on_site_correlation",
                        coordinate_name="tau",
                        coordinate=taus[sample_index],
                        value=two_time_on_site_correlation(reference, current),
                    )
                )
                sample_index += 1
        rows.append(
            self._record(
                common,
                metric="orthonormality_residual",
                value=orthonormality_residual(current),
            )
        )
        return rows

    def _density_records(
        self, condition: Condition, common: dict[str, Any], state: np.ndarray
    ) -> list[dict[str, Any]]:
        cfg = self.config["families"]["density_identity"]
        distances = _distance_grid(state.shape[0], int(cfg["distance_points"]))
        products, density_density = density_correlation_components(state, distances)
        direct = spatial_correlations(state, distances)
        group = str(condition.parameters["group"])
        selected_metric = "density_product" if group == "product" else "density_density"
        selected_values = products if group == "product" else density_density
        rows: list[dict[str, Any]] = []
        for distance, selected, direct_value in zip(
            distances, selected_values, direct, strict=True
        ):
            common_args = {
                "coordinate_name": "distance",
                "coordinate": distance,
                "auxiliary_name": "scaled_distance",
                "auxiliary": state.shape[0]
                / np.pi
                * np.sin(np.pi * distance / state.shape[0]),
            }
            rows.append(
                self._record(
                    common, metric=selected_metric, value=float(selected), **common_args
                )
            )
            rows.append(
                self._record(
                    common,
                    metric="direct_fock_correlation",
                    value=float(direct_value),
                    **common_args,
                )
            )
        rows.append(
            self._record(
                common,
                metric="orthonormality_residual",
                value=orthonormality_residual(state),
            )
        )
        return rows

    def _iter_complete_checkpoints(
        self, family: str
    ) -> Iterator[tuple[Condition, int, dict[str, Any]]]:
        for condition in self.conditions:
            if condition.family != family:
                continue
            covered: set[int] = set()
            for shard_id in range(condition.shards):
                path = self._checkpoint_path(condition, shard_id)
                if not path.exists():
                    raise FileNotFoundError(f"missing shard checkpoint: {path}")
                with path.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
                if payload.get("status") != "complete":
                    raise ValueError(f"incomplete shard checkpoint: {path}")
                if payload.get("records_sha256") != _digest(payload.get("records", [])):
                    raise ValueError(f"record hash mismatch: {path}")
                self._validate_checkpoint_payload(
                    condition, shard_id, payload, require_complete=True
                )
                actual = {
                    int(value) for value in payload["completed_trajectory_indices"]
                }
                if covered.intersection(actual):
                    raise ValueError(f"trajectory coverage mismatch: {path}")
                covered.update(actual)
                yield condition, shard_id, payload
            if covered != set(range(condition.trajectories)):
                raise ValueError(
                    f"incomplete condition coverage: {condition.condition_id}"
                )

    @staticmethod
    def _aggregate_key(record: dict[str, Any]) -> tuple[Any, ...]:
        return (
            record["condition_id"],
            record["metric"],
            record["coordinate_name"],
            float(record["coordinate"]),
            record["auxiliary_name"],
            float(record["auxiliary"]),
        )

    def aggregate_family(self, family: str) -> dict[str, Any]:
        if family not in FAMILY_ORDER:
            raise ValueError(f"unknown family: {family}")
        statistics: dict[tuple[Any, ...], OnlineStats] = {}
        metadata: dict[tuple[Any, ...], dict[str, Any]] = {}
        shard_statistics: dict[tuple[str, int, str, str, float], OnlineStats] = {}
        scalar_records = 0
        checkpoint_hashes: list[dict[str, Any]] = []
        scalar_path = self.output_root / "aggregates" / f"{family}.scalar_records.jsonl"
        scalar_path.parent.mkdir(parents=True, exist_ok=True)
        scalar_temporary = scalar_path.with_suffix(
            scalar_path.suffix + f".tmp-{os.getpid()}"
        )
        try:
            with scalar_temporary.open("w", encoding="utf-8") as scalar_handle:
                for condition, shard_id, checkpoint in self._iter_complete_checkpoints(
                    family
                ):
                    checkpoint_path = self._checkpoint_path(condition, shard_id)
                    checkpoint_hashes.append(
                        {
                            "condition_id": condition.condition_id,
                            "shard_id": shard_id,
                            "path": self._portable_path(checkpoint_path),
                            "sha256": _file_sha256(checkpoint_path),
                        }
                    )
                    for record in checkpoint["records"]:
                        scalar_handle.write(_canonical_json(record) + "\n")
                        scalar_records += 1
                        key = self._aggregate_key(record)
                        statistics.setdefault(key, OnlineStats()).add(
                            float(record["value"])
                        )
                        metadata.setdefault(
                            key,
                            {
                                "family": family,
                                "condition_id": record["condition_id"],
                                "protocol": record["protocol"],
                                "group": record.get("group"),
                                "length": record["length"],
                                "gamma": record["gamma"],
                                "metric": record["metric"],
                                "coordinate_name": record["coordinate_name"],
                                "coordinate": record["coordinate"],
                                "auxiliary_name": record["auxiliary_name"],
                                "auxiliary": record["auxiliary"],
                            },
                        )
                        shard_key = (
                            record["condition_id"],
                            shard_id,
                            record["metric"],
                            record["coordinate_name"],
                            float(record["coordinate"]),
                        )
                        shard_statistics.setdefault(shard_key, OnlineStats()).add(
                            float(record["value"])
                        )
            os.replace(scalar_temporary, scalar_path)
        finally:
            if scalar_temporary.exists():
                scalar_temporary.unlink()
        rows = [{**metadata[key], **stats.row()} for key, stats in statistics.items()]
        rows.extend(self._derived_rows(family, rows))
        rows.sort(
            key=lambda row: (
                str(row.get("condition_id")),
                str(row.get("metric")),
                float(row.get("coordinate", 0.0)),
            )
        )
        aggregate_path = self.output_root / "aggregates" / f"{family}.csv"
        _write_csv_atomic(aggregate_path, rows)
        stability = self._shard_stability(shard_statistics)
        manifest = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": self.mode,
            "family": family,
            "status": "complete",
            "config_sha256": self.config_hash,
            "backend": self.backend,
            "streaming_statistics": True,
            "full_states_persisted": 0,
            "scalar_checkpoint_records": scalar_records,
            "aggregate_rows": len(rows),
            "aggregate_path": self._portable_path(aggregate_path),
            "aggregate_sha256": _file_sha256(aggregate_path),
            "scalar_records_path": self._portable_path(scalar_path),
            "scalar_records_sha256": _file_sha256(scalar_path),
            "checkpoint_hashes": checkpoint_hashes,
            "leave_one_shard_out": stability,
        }
        manifest_path = self.output_root / "aggregates" / f"{family}.manifest.json"
        _write_json_atomic(manifest_path, manifest)
        return manifest

    def _derived_rows(
        self, family: str, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        derived: list[dict[str, Any]] = []
        if family in {"regular_qsd", "quantum_jump", "random_hopping"}:
            conditions = sorted({row["condition_id"] for row in rows})
            for condition_id in conditions:
                entropy = [
                    row
                    for row in rows
                    if row["condition_id"] == condition_id
                    and row["metric"] == "interval_entropy"
                ]
                if len(entropy) < 3:
                    continue
                entropy.sort(key=lambda row: float(row["coordinate"]))
                central, residual, r_squared = cft_fit(
                    np.asarray([row["coordinate"] for row in entropy], dtype=float),
                    np.asarray([row["mean"] for row in entropy], dtype=float),
                    int(entropy[0]["length"]),
                )
                base = dict(entropy[0])
                for metric, value in (
                    ("effective_central_charge", central),
                    ("residual_entropy", residual),
                    ("cft_fit_r_squared", r_squared),
                ):
                    derived.append(
                        {
                            **base,
                            "metric": metric,
                            "coordinate_name": "none",
                            "coordinate": 0.0,
                            "auxiliary_name": "none",
                            "auxiliary": 0.0,
                            "samples": min(int(row["samples"]) for row in entropy),
                            "mean": value,
                            "std": 0.0,
                            "minimum": value,
                            "maximum": value,
                        }
                    )
        if family == "regular_qsd":
            bkt = self.config["parameters"]["bkt_transform"]
            gamma_c = float(bkt["gamma_c"])
            alpha = float(bkt["alpha"])
            half_rows = [row for row in rows if row["metric"] == "half_entropy"]
            by_length: dict[int, list[dict[str, Any]]] = {}
            for row in half_rows:
                by_length.setdefault(int(row["length"]), []).append(row)
            for length, length_rows in by_length.items():
                length_rows.sort(key=lambda row: float(row["gamma"]))
                gammas = np.asarray([row["gamma"] for row in length_rows], dtype=float)
                entropies = np.asarray(
                    [row["mean"] for row in length_rows], dtype=float
                )
                critical_entropy = float(np.interp(gamma_c, gammas, entropies))
                for row in length_rows:
                    gamma = float(row["gamma"])
                    x_value = (gamma - gamma_c) * math.log(float(length)) ** 2
                    y_value = float(row["mean"]) - critical_entropy
                    derived.append(
                        {
                            **row,
                            "metric": "bkt_entropy_transform",
                            "coordinate_name": "scaled_gamma",
                            "coordinate": x_value,
                            "mean": y_value,
                            "std": float(row["std"]),
                            "minimum": y_value,
                            "maximum": y_value,
                        }
                    )
            fit_rows = [
                row
                for row in derived
                if row["metric"] == "effective_central_charge"
                and float(row["gamma"]) > gamma_c
            ]
            for row in fit_rows:
                length = int(row["length"])
                gamma = float(row["gamma"])
                x_value = math.log(float(length)) - alpha / math.sqrt(gamma - gamma_c)
                g_length = 1.0 / (1.0 + 1.0 / (2.0 * math.log(float(length)) - 4.37))
                y_value = g_length * gamma * max(float(row["mean"]), 0.0)
                derived.append(
                    {
                        **row,
                        "metric": "bkt_central_charge_transform",
                        "coordinate_name": "bkt_x",
                        "coordinate": x_value,
                        "mean": y_value,
                        "std": 0.0,
                        "minimum": y_value,
                        "maximum": y_value,
                    }
                )
        if family == "density_identity":
            by_coordinate: dict[tuple[float, float], dict[str, dict[str, Any]]] = {}
            for row in rows:
                by_coordinate.setdefault(
                    (float(row["coordinate"]), float(row["auxiliary"])), {}
                )[str(row["metric"])] = row
            for (distance, scaled), metrics in by_coordinate.items():
                if "density_product" not in metrics or "density_density" not in metrics:
                    continue
                product = metrics["density_product"]
                density = metrics["density_density"]
                difference = float(product["mean"]) - float(density["mean"])
                derived.append(
                    {
                        **product,
                        "condition_id": "density_identity-independent_difference",
                        "group": "independent_250_plus_250",
                        "metric": "independent_density_difference",
                        "coordinate": distance,
                        "auxiliary": scaled,
                        "samples": min(
                            int(product["samples"]), int(density["samples"])
                        ),
                        "mean": difference,
                        "std": math.sqrt(
                            float(product["std"]) ** 2 + float(density["std"]) ** 2
                        ),
                        "standard_error": math.sqrt(
                            float(product["std"]) ** 2 / int(product["samples"])
                            + float(density["std"]) ** 2 / int(density["samples"])
                        ),
                        "minimum": difference,
                        "maximum": difference,
                    }
                )
        if family in {"histogram_qsd", "histogram_qsdc"}:
            histogram_cfg = self.config["parameters"]["histogram"]
            bins = int(histogram_cfg["bins"])
            low = float(histogram_cfg["minimum"])
            high = float(histogram_cfg["maximum"])
            # Aggregate summary records are sufficient for ordinary means but
            # not bin counts; take a second streaming pass over scalar
            # checkpoints.  This remains O(1) in trajectory states and O(bins)
            # in memory.
            by_condition: dict[str, np.ndarray] = {}
            totals: dict[str, int] = {}
            underflow: dict[str, int] = {}
            overflow: dict[str, int] = {}
            width = (high - low) / bins
            for _, _, checkpoint in self._iter_complete_checkpoints(family):
                for record in checkpoint["records"]:
                    if record["metric"] != "half_entropy":
                        continue
                    condition_id = str(record["condition_id"])
                    counts = by_condition.setdefault(
                        condition_id, np.zeros(bins, dtype=np.int64)
                    )
                    totals[condition_id] = totals.get(condition_id, 0) + 1
                    value = float(record["value"])
                    if value < low:
                        underflow[condition_id] = underflow.get(condition_id, 0) + 1
                    elif value > high:
                        overflow[condition_id] = overflow.get(condition_id, 0) + 1
                    else:
                        index = min(bins - 1, int((value - low) / width))
                        counts[index] += 1
            lookup = {
                row["condition_id"]: row
                for row in rows
                if row["metric"] == "half_entropy"
            }
            for condition_id, counts in by_condition.items():
                template = lookup[condition_id]
                total = totals[condition_id]
                for index, count in enumerate(counts):
                    left = low + index * width
                    derived.append(
                        {
                            **template,
                            "metric": "half_entropy_histogram",
                            "coordinate_name": "bin_center",
                            "coordinate": left + width / 2.0,
                            "auxiliary_name": "bin_width",
                            "auxiliary": width,
                            "samples": total,
                            "mean": int(count) / (total * width),
                            "std": 0.0,
                            "minimum": int(count),
                            "maximum": int(count),
                            "bin_count": int(count),
                            "underflow": underflow.get(condition_id, 0),
                            "overflow": overflow.get(condition_id, 0),
                        }
                    )
        return derived

    @staticmethod
    def _shard_stability(
        shard_statistics: dict[tuple[str, int, str, str, float], OnlineStats],
    ) -> dict[str, Any]:
        grouped: dict[tuple[str, str, str, float], list[float]] = {}
        for (
            condition_id,
            _,
            metric,
            coordinate_name,
            coordinate,
        ), stats in shard_statistics.items():
            grouped.setdefault(
                (condition_id, metric, coordinate_name, coordinate), []
            ).append(stats.mean)
        rows = []
        for (
            condition_id,
            metric,
            coordinate_name,
            coordinate,
        ), means in sorted(grouped.items()):
            overall = float(np.mean(means))
            loo = [
                float(np.mean(means[:index] + means[index + 1 :]))
                for index in range(len(means))
                if len(means) > 1
            ]
            max_deviation = max((abs(value - overall) for value in loo), default=0.0)
            rows.append(
                {
                    "condition_id": condition_id,
                    "metric": metric,
                    "coordinate_name": coordinate_name,
                    "coordinate": coordinate,
                    "shards": len(means),
                    "mean_of_shard_means": overall,
                    "max_leave_one_shard_out_abs_deviation": max_deviation,
                }
            )
        return {"method": "streamed coordinate-specific shard means", "rows": rows}

    def aggregate_all(self) -> dict[str, Any]:
        manifests = [self.aggregate_family(family) for family in FAMILY_ORDER]
        payload = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": self.mode,
            "status": "complete",
            "config_sha256": self.config_hash,
            "backend": self.backend,
            "families": manifests,
            "all_full_states_persisted": 0,
        }
        _write_json_atomic(self.output_root / "aggregates" / "manifest.json", payload)
        return payload

    def accept(self, acceptance_path: Path) -> dict[str, Any]:
        with acceptance_path.open(encoding="utf-8") as handle:
            acceptance = json.load(handle)
        if acceptance.get("paper_id") != self.config["paper_id"]:
            raise ValueError("acceptance paper_id mismatch")
        declared = acceptance.get("targets", {})
        if tuple(sorted(declared)) != TARGET_IDS:
            raise ValueError("acceptance must declare T001-T031 exactly")
        global_criteria = acceptance["global_criteria"]
        tolerance = float(global_criteria["orthonormality_tolerance"])
        # Rebuilding the plan also proves deterministic seed/index disjointness.
        self.plan()
        global_failures: list[str] = []
        benchmark_path = self.output_root / "checks" / "backend_benchmark.json"
        if not benchmark_path.exists():
            global_failures.append("backend_benchmark_missing")
        else:
            benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
            expected_benchmark_mode = "smoke" if self.smoke else "paper_scale_benchmark"
            if benchmark.get("execution_mode") != expected_benchmark_mode:
                global_failures.append("backend_benchmark_mode_mismatch")
            if benchmark.get("benchmark_config_sha256") != _digest(
                self.config["backend_benchmark"]
            ):
                global_failures.append("backend_benchmark_config_mismatch")
            matching_backend_rows = [
                row
                for row in benchmark.get("results", [])
                if row.get("backend") == self.backend
            ]
            if benchmark.get("status") != "passed" or not matching_backend_rows:
                global_failures.append("backend_benchmark_failed")
            elif not all(row.get("passed") for row in matching_backend_rows):
                global_failures.append("selected_backend_parity_failed")
        family_manifests: dict[str, dict[str, Any]] = {}
        family_rows: dict[str, list[dict[str, str]]] = {}
        for family in FAMILY_ORDER:
            path = self.output_root / "aggregates" / f"{family}.manifest.json"
            if not path.exists():
                family_manifests[family] = {"status": "missing"}
                family_rows[family] = []
            else:
                family_manifests[family] = json.loads(path.read_text(encoding="utf-8"))
                csv_path = self.output_root / "aggregates" / f"{family}.csv"
                if csv_path.exists():
                    with csv_path.open(encoding="utf-8", newline="") as handle:
                        family_rows[family] = list(csv.DictReader(handle))
                else:
                    family_rows[family] = []
        results = []
        for target_id in TARGET_IDS:
            contract = declared[target_id]
            family = str(contract["family"])
            manifest = family_manifests.get(family, {})
            rows = family_rows.get(family, [])
            failures = list(global_failures)
            if manifest.get("status") != "complete":
                failures.append("family_manifest_incomplete")
            if manifest.get("config_sha256") != self.config_hash:
                failures.append("family_manifest_config_mismatch")
            if manifest.get("mode") != self.mode:
                failures.append("family_manifest_mode_mismatch")
            if manifest.get("backend") != self.backend:
                failures.append("family_manifest_backend_mismatch")
            if int(manifest.get("full_states_persisted", -1)) != 0:
                failures.append("full_states_were_persisted")
            aggregate_path = self.output_root / "aggregates" / f"{family}.csv"
            if not aggregate_path.exists():
                failures.append("aggregate_csv_missing")
            elif manifest.get("aggregate_sha256") != _file_sha256(aggregate_path):
                failures.append("aggregate_hash_mismatch")
            scalar_path_value = manifest.get("scalar_records_path")
            if not scalar_path_value:
                failures.append("scalar_record_archive_missing")
            else:
                scalar_path = self._resolve_portable_path(str(scalar_path_value))
                if not scalar_path.exists():
                    failures.append("scalar_record_archive_missing")
                elif manifest.get("scalar_records_sha256") != _file_sha256(scalar_path):
                    failures.append("scalar_record_archive_hash_mismatch")
            for checkpoint in manifest.get("checkpoint_hashes", []):
                checkpoint_path = self._resolve_portable_path(str(checkpoint["path"]))
                if not checkpoint_path.exists() or checkpoint.get(
                    "sha256"
                ) != _file_sha256(checkpoint_path):
                    failures.append("checkpoint_hash_mismatch")
                    break
            finite_fields = ("mean", "std", "minimum", "maximum")
            if any(
                not math.isfinite(float(row[field]))
                for row in rows
                for field in finite_fields
                if row.get(field) not in {None, ""}
            ):
                failures.append("non_finite_scalar_output")
            residual_rows = [
                row for row in rows if row.get("metric") == "orthonormality_residual"
            ]
            if (
                not residual_rows
                or max(float(row["maximum"]) for row in residual_rows) > tolerance
            ):
                failures.append("orthonormality_tolerance_failed")
            criteria = contract["criteria"]
            metric_rows = [
                row for row in rows if row.get("metric") == criteria["metric"]
            ]
            if not metric_rows:
                failures.append("required_metric_missing")
            if not self.smoke and metric_rows:
                for required_length in criteria.get("lengths", []):
                    if not any(
                        int(float(row["length"])) == int(required_length)
                        for row in metric_rows
                    ):
                        failures.append(f"required_length_missing:{required_length}")
                for required_gamma in criteria.get("gammas", []):
                    if not any(
                        math.isclose(
                            float(row["gamma"]), float(required_gamma), abs_tol=1e-12
                        )
                        for row in metric_rows
                    ):
                        failures.append(f"required_gamma_missing:{required_gamma}")
                relevant = [
                    row
                    for row in metric_rows
                    if (
                        not criteria.get("lengths")
                        or int(float(row["length"]))
                        in {int(value) for value in criteria["lengths"]}
                    )
                    and (
                        not criteria.get("gammas")
                        or any(
                            math.isclose(
                                float(row["gamma"]), float(value), abs_tol=1e-12
                            )
                            for value in criteria["gammas"]
                        )
                    )
                ]
                if not relevant or min(
                    int(float(row["samples"])) for row in relevant
                ) < int(criteria["minimum_samples"]):
                    failures.append("minimum_samples_not_met")
                if criteria.get("independent_groups"):
                    groups = {
                        row.get("group")
                        for row in rows
                        if row.get("metric") in {"density_product", "density_density"}
                    }
                    if len(groups) < int(criteria["independent_groups"]):
                        failures.append("independent_groups_missing")
            machine_passed = not failures
            formula_gate = str(contract["formula_gate"])
            reference_gate = str(contract["reference_gate"])
            scientific_blockers = []
            if formula_gate != "verified":
                scientific_blockers.append("formula_not_verified")
            if reference_gate == "missing":
                scientific_blockers.append("strict_reference_not_available")
            results.append(
                {
                    "target_id": target_id,
                    "family": family,
                    "mode": self.mode,
                    "machine_contract_passed": machine_passed,
                    "machine_failures": failures,
                    "formula_gate": formula_gate,
                    "reference_gate": reference_gate,
                    "scientific_blockers": scientific_blockers,
                    "status": (
                        "machine_passed_with_science_blockers"
                        if machine_passed and scientific_blockers
                        else "machine_passed" if machine_passed else "machine_failed"
                    ),
                    "criteria": contract["criteria"],
                }
            )
        payload = {
            "schema_version": 1,
            "paper_id": self.config["paper_id"],
            "mode": self.mode,
            "status": (
                "machine_passed"
                if all(row["machine_contract_passed"] for row in results)
                else "machine_failed"
            ),
            "lifecycle_promotion_allowed": False,
            "reason": "machine execution cannot promote formula or strict-reference gates",
            "targets": results,
        }
        checks = self.output_root / "checks"
        _write_json_atomic(checks / "paper_scale_acceptance.json", payload)
        return payload


def load_campaign(
    config_path: Path,
    *,
    output_root: Path | None = None,
    smoke: bool = False,
    backend: str | None = None,
) -> Campaign:
    """Public constructor used by CLI adapters and contract-level tests."""

    return Campaign.load(
        config_path,
        output_root=output_root,
        smoke=smoke,
        backend=backend,
    )
