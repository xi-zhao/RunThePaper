"""Resumable paper-scale trajectory campaign for arXiv:2412.14271.

The paper states that *each* trajectory draws its initial state independently
from the infinite-temperature ensemble.  This module makes that sampling rule
explicit, assigns every trajectory a stable integer index, and accumulates
reduced photon density matrices without retaining all full-system states.

Only paper equations, declared parameters, and independently chosen seeds are
accepted as numerical inputs.  Paper PDFs, source figures, author arrays, and
author programs are deliberately outside this runner's interface.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

import numpy as np
from numpy.typing import NDArray

from src.dicke import QuantumModel, operators

ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class CampaignJob:
    """One immutable physical parameter point in the campaign."""

    label: str
    system_size: int
    photon_cutoff: int
    coupling: float
    final_time: float
    seed_base: int
    wigner: bool


@dataclass
class ShardState:
    """Online sufficient statistics for one deterministic trajectory shard."""

    processed_indices: list[int]
    rho_sums: ComplexArray
    spin_z_sums: NDArray[np.float64]
    runtime_seconds: float = 0.0


def canonical_digest(payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def file_digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted((item.resolve() for item in paths), key=str):
        digest.update(str(path.name).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_safe_output_root(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("execution.output_root must be a non-empty string")
    path = Path(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.parts[0] != "outputs"
    ):
        raise ValueError(
            "execution.output_root must be workspace-relative under outputs/"
        )
    return path


def effective_campaign(
    payload: Mapping[str, Any], *, smoke: bool = False
) -> dict[str, Any]:
    """Validate and freeze the effective scientific/execution configuration."""

    if int(payload.get("schema_version", 0)) != 1:
        raise ValueError("paper-scale config schema_version must be 1")
    parameter_key = "smoke_parameters" if smoke else "parameters"
    parameters = payload.get(parameter_key)
    execution = payload.get("execution")
    acceptance_key = "smoke_acceptance" if smoke else "acceptance"
    acceptance = payload.get(acceptance_key)
    input_boundary = payload.get("input_boundary")
    if not isinstance(parameters, dict):
        raise ValueError(f"{parameter_key} must be an object")
    if not isinstance(execution, dict) or not isinstance(acceptance, dict):
        raise ValueError(f"execution and {acceptance_key} must be objects")
    if not isinstance(input_boundary, dict):
        raise ValueError("input_boundary must be an object")
    if input_boundary.get("numeric_runner_reads_reference_assets") is not False:
        raise ValueError("numeric runner must explicitly forbid reference-asset reads")
    forbidden = input_boundary.get("forbidden")
    if not isinstance(forbidden, list) or not forbidden:
        raise ValueError("input_boundary.forbidden must declare excluded inputs")

    physical = parameters.get("physical")
    jobs = parameters.get("jobs")
    trajectory_count = parameters.get("trajectory_count")
    snapshot_counts = parameters.get("snapshot_counts")
    if not isinstance(physical, dict):
        raise ValueError("parameters.physical must be an object")
    required_physical = {"omega_c", "omega_a", "kappa1", "kappa2"}
    if not required_physical.issubset(physical):
        raise ValueError(
            f"physical parameters must contain {sorted(required_physical)}"
        )
    if not isinstance(trajectory_count, int) or trajectory_count <= 0:
        raise ValueError("trajectory_count must be a positive integer")
    if (
        not isinstance(snapshot_counts, list)
        or not snapshot_counts
        or any(not isinstance(value, int) or value <= 0 for value in snapshot_counts)
        or snapshot_counts != sorted(set(snapshot_counts))
        or snapshot_counts[-1] != trajectory_count
    ):
        raise ValueError(
            "snapshot_counts must be sorted, unique, positive, and end at trajectory_count"
        )
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("parameters.jobs must be a non-empty list")

    labels: set[str] = set()
    seed_ranges: list[tuple[int, int, str]] = []
    for raw_job in jobs:
        if not isinstance(raw_job, dict):
            raise ValueError("every job must be an object")
        label = raw_job.get("label")
        if not isinstance(label, str) or not label or label in labels:
            raise ValueError("job labels must be non-empty and unique")
        labels.add(label)
        for field in ("N", "M", "seed_base"):
            if not isinstance(raw_job.get(field), int) or int(raw_job[field]) <= 0:
                raise ValueError(f"{label}.{field} must be a positive integer")
        for field in ("lambda", "final_time"):
            if (
                not isinstance(raw_job.get(field), (int, float))
                or float(raw_job[field]) <= 0
            ):
                raise ValueError(f"{label}.{field} must be positive")
        first_seed = int(raw_job["seed_base"])
        last_seed = first_seed + 2 * trajectory_count - 1
        seed_ranges.append((first_seed, last_seed, label))
    for index, (first, last, label) in enumerate(sorted(seed_ranges)):
        if index and first <= sorted(seed_ranges)[index - 1][1]:
            raise ValueError(f"seed range for {label} overlaps another job")

    default_shards_key = "smoke_shard_count" if smoke else "default_shard_count"
    shard_count = execution.get(default_shards_key)
    checkpoint_every = execution.get("checkpoint_every")
    if not isinstance(shard_count, int) or shard_count <= 0:
        raise ValueError(f"execution.{default_shards_key} must be positive")
    if not isinstance(checkpoint_every, int) or checkpoint_every <= 0:
        raise ValueError("execution.checkpoint_every must be positive")
    output_key = "smoke_output_root" if smoke else "output_root"
    output_root = _require_safe_output_root(execution.get(output_key))

    return {
        "schema_version": 1,
        "profile": "smoke" if smoke else "paper_scale",
        "run_id": f"{payload.get('run_id')}-smoke" if smoke else payload.get("run_id"),
        "parameters": parameters,
        "execution": {
            **execution,
            "effective_shard_count": shard_count,
            "effective_output_root": str(output_root),
        },
        "acceptance": acceptance,
        "input_boundary": input_boundary,
    }


def campaign_jobs(campaign: Mapping[str, Any]) -> list[CampaignJob]:
    return [
        CampaignJob(
            label=str(raw["label"]),
            system_size=int(raw["N"]),
            photon_cutoff=int(raw["M"]),
            coupling=float(raw["lambda"]),
            final_time=float(raw["final_time"]),
            seed_base=int(raw["seed_base"]),
            wigner=bool(raw.get("wigner", False)),
        )
        for raw in campaign["parameters"]["jobs"]
    ]


def artifact_prefix(campaign: Mapping[str, Any]) -> str:
    return (
        "paper_scale_quantum_smoke"
        if campaign["profile"] == "smoke"
        else "paper_scale_quantum"
    )


def seeds_for_trajectory(seed_base: int, trajectory_index: int) -> tuple[int, int]:
    """Return disjoint initial-state and jump-process seeds for one trajectory."""

    if trajectory_index < 0:
        raise ValueError("trajectory_index must be non-negative")
    initial_seed = seed_base + 2 * trajectory_index
    jump_seed = initial_seed + 1
    return initial_seed, jump_seed


def assigned_indices(total: int, shard_index: int, shard_count: int) -> tuple[int, ...]:
    if total <= 0 or shard_count <= 0 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid total/shard assignment")
    return tuple(range(shard_index, total, shard_count))


def empty_shard_state(snapshot_counts: list[int], photon_cutoff: int) -> ShardState:
    return ShardState(
        processed_indices=[],
        rho_sums=np.zeros(
            (len(snapshot_counts), photon_cutoff, photon_cutoff),
            dtype=np.complex128,
        ),
        spin_z_sums=np.zeros(len(snapshot_counts), dtype=float),
    )


def add_sample(
    state: ShardState,
    *,
    trajectory_index: int,
    photon_density: ComplexArray,
    spin_z: float,
    snapshot_counts: list[int],
) -> None:
    """Accumulate one sample into every prefix ensemble containing its index."""

    if trajectory_index in state.processed_indices:
        raise ValueError(f"trajectory {trajectory_index} is already present")
    if photon_density.shape != state.rho_sums.shape[1:]:
        raise ValueError("photon-density shape does not match the configured cutoff")
    for snapshot_index, count in enumerate(snapshot_counts):
        if trajectory_index < count:
            state.rho_sums[snapshot_index] += photon_density
            state.spin_z_sums[snapshot_index] += spin_z
    state.processed_indices.append(trajectory_index)


def _atomic_npz(path: Path, **arrays: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            np.savez_compressed(handle, **arrays)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def save_shard_state(
    path: Path,
    state: ShardState,
    *,
    config_digest: str,
    implementation_digest: str,
    job: CampaignJob,
    shard_index: int,
    shard_count: int,
    assigned: tuple[int, ...],
) -> None:
    complete = set(state.processed_indices) == set(assigned)
    _atomic_npz(
        path,
        schema_version=np.asarray(1, dtype=np.int64),
        config_digest=np.asarray(config_digest),
        implementation_digest=np.asarray(implementation_digest),
        job_label=np.asarray(job.label),
        shard_index=np.asarray(shard_index, dtype=np.int64),
        shard_count=np.asarray(shard_count, dtype=np.int64),
        assigned_indices=np.asarray(assigned, dtype=np.int64),
        processed_indices=np.asarray(sorted(state.processed_indices), dtype=np.int64),
        rho_sums=state.rho_sums,
        spin_z_sums=state.spin_z_sums,
        runtime_seconds=np.asarray(state.runtime_seconds, dtype=float),
        complete=np.asarray(complete),
    )


def load_shard_state(
    path: Path,
    *,
    config_digest: str,
    implementation_digest: str,
    job: CampaignJob,
    shard_index: int,
    shard_count: int,
    assigned: tuple[int, ...],
) -> ShardState:
    with np.load(path, allow_pickle=False) as payload:
        checks = {
            "config_digest": (str(payload["config_digest"].item()), config_digest),
            "implementation_digest": (
                str(payload["implementation_digest"].item()),
                implementation_digest,
            ),
            "job_label": (str(payload["job_label"].item()), job.label),
            "shard_index": (int(payload["shard_index"].item()), shard_index),
            "shard_count": (int(payload["shard_count"].item()), shard_count),
        }
        mismatches = [
            name
            for name, (observed, expected) in checks.items()
            if observed != expected
        ]
        if mismatches:
            raise ValueError(f"checkpoint identity mismatch: {', '.join(mismatches)}")
        stored_assigned = tuple(int(value) for value in payload["assigned_indices"])
        if stored_assigned != assigned:
            raise ValueError("checkpoint assigned-index set does not match this shard")
        processed = [int(value) for value in payload["processed_indices"]]
        if len(processed) != len(set(processed)) or not set(processed).issubset(
            assigned
        ):
            raise ValueError(
                "checkpoint has duplicate or out-of-shard trajectory indices"
            )
        return ShardState(
            processed_indices=processed,
            rho_sums=np.asarray(payload["rho_sums"], dtype=np.complex128),
            spin_z_sums=np.asarray(payload["spin_z_sums"], dtype=float),
            runtime_seconds=float(payload["runtime_seconds"].item()),
        )


def run_randomized_trajectory(
    model: QuantumModel,
    job: CampaignJob,
    trajectory_index: int,
    *,
    solver_options: Mapping[str, Any],
) -> tuple[ComplexArray, float]:
    """Run one trajectory with an independently randomized initial state."""

    import qutip as qt

    initial_seed, jump_seed = seeds_for_trajectory(job.seed_base, trajectory_index)
    initial = qt.rand_ket([job.photon_cutoff, job.system_size + 1], seed=initial_seed)
    result = qt.mcsolve(
        model.hamiltonian,
        initial,
        [0.0, job.final_time],
        list(model.collapse_operators),
        ntraj=1,
        seeds=jump_seed,
        options={
            **solver_options,
            "store_final_state": True,
            "keep_runs_results": True,
        },
    )
    final_state = result.runs_final_states[0]
    photon_density = np.asarray(final_state.ptrace(0).full(), dtype=np.complex128)
    spin_z = float(np.real(qt.expect(model.spin_z, final_state))) / job.system_size
    return photon_density, spin_z


def run_shard(
    campaign: Mapping[str, Any],
    job: CampaignJob,
    *,
    shard_index: int,
    shard_count: int,
    config_digest: str,
    implementation_digest: str,
    resume: bool,
) -> Path:
    parameters = campaign["parameters"]
    physical = parameters["physical"]
    snapshots = [int(value) for value in parameters["snapshot_counts"]]
    total = int(parameters["trajectory_count"])
    assigned = assigned_indices(total, shard_index, shard_count)
    output_root = Path(campaign["execution"]["effective_output_root"])
    checkpoint = (
        output_root
        / "checks"
        / f"{artifact_prefix(campaign)}_checkpoints"
        / job.label
        / f"shard-{shard_index:04d}-of-{shard_count:04d}.npz"
    )
    if resume and checkpoint.exists():
        state = load_shard_state(
            checkpoint,
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            job=job,
            shard_index=shard_index,
            shard_count=shard_count,
            assigned=assigned,
        )
    else:
        state = empty_shard_state(snapshots, job.photon_cutoff)

    pending = [value for value in assigned if value not in set(state.processed_indices)]
    if not pending:
        return checkpoint

    model = operators(
        job.system_size,
        job.photon_cutoff,
        job.coupling,
        omega_c=float(physical["omega_c"]),
        omega_a=float(physical["omega_a"]),
        kappa1=float(physical["kappa1"]),
        kappa2=float(physical["kappa2"]),
    )
    solver_options = parameters["solver_options"]
    checkpoint_every = int(campaign["execution"]["checkpoint_every"])
    started = time.monotonic()
    for local_index, trajectory_index in enumerate(pending, start=1):
        density, spin_z = run_randomized_trajectory(
            model,
            job,
            trajectory_index,
            solver_options=solver_options,
        )
        add_sample(
            state,
            trajectory_index=trajectory_index,
            photon_density=density,
            spin_z=spin_z,
            snapshot_counts=snapshots,
        )
        if local_index % checkpoint_every == 0:
            state.runtime_seconds += time.monotonic() - started
            save_shard_state(
                checkpoint,
                state,
                config_digest=config_digest,
                implementation_digest=implementation_digest,
                job=job,
                shard_index=shard_index,
                shard_count=shard_count,
                assigned=assigned,
            )
            started = time.monotonic()
    state.runtime_seconds += time.monotonic() - started
    save_shard_state(
        checkpoint,
        state,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        job=job,
        shard_index=shard_index,
        shard_count=shard_count,
        assigned=assigned,
    )
    return checkpoint


def merge_job_shards(
    campaign: Mapping[str, Any],
    job: CampaignJob,
    *,
    shard_count: int,
    config_digest: str,
    implementation_digest: str,
) -> tuple[ComplexArray, NDArray[np.float64], list[dict[str, Any]]]:
    parameters = campaign["parameters"]
    snapshots = [int(value) for value in parameters["snapshot_counts"]]
    total = int(parameters["trajectory_count"])
    output_root = Path(campaign["execution"]["effective_output_root"])
    rho_sums = np.zeros(
        (len(snapshots), job.photon_cutoff, job.photon_cutoff), dtype=np.complex128
    )
    spin_z_sums = np.zeros(len(snapshots), dtype=float)
    all_indices: list[int] = []
    shard_records: list[dict[str, Any]] = []
    for shard_index in range(shard_count):
        assigned = assigned_indices(total, shard_index, shard_count)
        path = (
            output_root
            / "checks"
            / f"{artifact_prefix(campaign)}_checkpoints"
            / job.label
            / f"shard-{shard_index:04d}-of-{shard_count:04d}.npz"
        )
        if not path.exists():
            raise FileNotFoundError(f"missing shard checkpoint: {path}")
        state = load_shard_state(
            path,
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            job=job,
            shard_index=shard_index,
            shard_count=shard_count,
            assigned=assigned,
        )
        if set(state.processed_indices) != set(assigned):
            raise ValueError(f"incomplete shard checkpoint: {path}")
        rho_sums += state.rho_sums
        spin_z_sums += state.spin_z_sums
        all_indices.extend(state.processed_indices)
        shard_records.append(
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "trajectory_count": len(state.processed_indices),
                "runtime_seconds": state.runtime_seconds,
            }
        )
    if len(all_indices) != len(set(all_indices)):
        raise ValueError(f"duplicate trajectory index while merging {job.label}")
    if set(all_indices) != set(range(total)):
        raise ValueError(f"trajectory index coverage is incomplete for {job.label}")
    densities = np.stack(
        [rho_sums[index] / count for index, count in enumerate(snapshots)],
        axis=0,
    )
    spin_means = np.asarray(
        [spin_z_sums[index] / count for index, count in enumerate(snapshots)],
        dtype=float,
    )
    return densities, spin_means, shard_records


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
