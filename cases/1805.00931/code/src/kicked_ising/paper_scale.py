"""Paper-scale orchestration, checkpoints, and scientific acceptance.

This module owns execution state; :mod:`kicked_ising.model` owns the scientific
operators.  The split keeps checkpoint/resume mechanics out of the physics model
while ensuring every large run uses the same verified numerical core as tests.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .model import (
    RestartedArnoldiGapSolver,
    RestartedArnoldiState,
    SELF_DUAL,
    _as_numpy,
    array_module,
    coe_form_factor,
    protected_operator_basis,
    random_phase_trace_sff,
    thermodynamic_sff,
    transfer_multiplicities,
)


PAPER_FIG2_SIGMAS = [np.pi / 20.0, np.pi / 10.0, 100.0 * np.pi]
PAPER_GAP_TIMES = list(range(9, 16))
PAPER_GAP_H_MEANS = [0.0, 0.1, 0.3, 0.6, 0.9, 1.2]


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _safe_workspace_path(workspace: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"workspace output path must be relative and contained: {relative}")
    return workspace / candidate


def _require_close_list(actual: Iterable[float], expected: Iterable[float], label: str) -> None:
    actual_array = np.asarray(list(actual), dtype=np.float64)
    expected_array = np.asarray(list(expected), dtype=np.float64)
    if actual_array.shape != expected_array.shape or not np.allclose(
        actual_array, expected_array, atol=1e-14, rtol=1e-14
    ):
        raise ValueError(f"{label} does not match the declared paper-scale contract")


def validate_paper_scale_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate structure and the non-negotiable paper parameters."""

    if int(config.get("schema_version", 0)) != 2:
        raise ValueError("paper-scale config requires schema_version=2")
    if config.get("profile") not in {"paper_scale", "paper_scale_smoke"}:
        raise ValueError("profile must be paper_scale or paper_scale_smoke")
    parameters = config["parameters"]
    for section in ("model", "fig2", "fig3_left", "fig3_right", "solver"):
        if section not in parameters:
            raise ValueError(f"missing paper-scale parameter section: {section}")
    execution = config["execution"]
    for key in (
        "output_root",
        "output_namespace",
        "checkpoint_root",
        "sff_shards",
        "gap_shards",
    ):
        if key not in execution:
            raise ValueError(f"missing execution field: {key}")
    if int(execution["sff_shards"]) < 1 or int(execution["gap_shards"]) < 1:
        raise ValueError("shard counts must be positive")
    for key in ("output_root", "output_namespace", "checkpoint_root"):
        path = Path(str(execution[key]))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{key} must be workspace-relative")

    solver = parameters["solver"]
    if solver.get("method") != "restarted_arnoldi":
        raise ValueError(
            "paper-scale gaps require the memory-bounded restarted_arnoldi solver"
        )
    if int(solver.get("krylov_dimension", 0)) < 3:
        raise ValueError("paper-scale restarted Arnoldi requires krylov_dimension>=3")
    if len(solver.get("seeds", [])) < 2:
        raise ValueError("paper-scale acceptance requires at least two independent seeds")
    estimator = parameters["fig2"].get("trace_estimator", {})
    if estimator.get("method") != "independent_random_phase_cross":
        raise ValueError("paper-scale SFF requires the unbiased independent cross estimator")
    if int(estimator.get("probe_group_size", 0)) < 1:
        raise ValueError("trace_estimator.probe_group_size must be positive")

    if config["profile"] == "paper_scale":
        model = parameters["model"]
        if not np.isclose(float(model["J"]), SELF_DUAL) or not np.isclose(
            float(model["b"]), SELF_DUAL
        ):
            raise ValueError("paper-scale model requires J=b=pi/4")
        fig2 = parameters["fig2"]
        exact_fig2 = {
            "L": 15,
            "paper_L": 15,
            "disorder_realizations": 9490,
            "paper_disorder_realizations": 9490,
            "t_min": 1,
            "t_max": 1000,
        }
        for key, expected in exact_fig2.items():
            if int(fig2[key]) != expected:
                raise ValueError(f"fig2.{key} must equal paper value {expected}")
        if not np.isclose(float(fig2["h_mean"]), 0.6):
            raise ValueError("fig2.h_mean must equal 0.6")
        _require_close_list(fig2["sigmas"], PAPER_FIG2_SIGMAS, "fig2.sigmas")
        _require_close_list(parameters["fig3_left"]["times"], PAPER_GAP_TIMES, "fig3_left.times")
        if not np.isclose(float(parameters["fig3_left"]["h_mean"]), 0.0):
            raise ValueError("fig3_left.h_mean must equal 0")
        declared_sigma_grid = np.arange(0.0, 0.81, 0.1)
        _require_close_list(
            parameters["fig3_left"]["sigmas"],
            declared_sigma_grid,
            "fig3_left.sigmas",
        )
        if int(parameters["fig3_right"]["t"]) != 13:
            raise ValueError("fig3_right.t must equal 13")
        _require_close_list(
            parameters["fig3_right"]["h_means"],
            PAPER_GAP_H_MEANS,
            "fig3_right.h_means",
        )
        _require_close_list(
            parameters["fig3_right"]["sigmas"],
            declared_sigma_grid,
            "fig3_right.sigmas",
        )
    return config


def load_paper_scale_config(path: Path) -> dict[str, Any]:
    return validate_paper_scale_config(json.loads(path.read_text(encoding="utf-8")))


def paper_scale_preflight(config: dict[str, Any]) -> dict[str, Any]:
    """Validate a campaign without importing CuPy or allocating large vectors."""

    validate_paper_scale_config(config)
    solver = config["parameters"]["solver"]
    dtype_size = np.dtype(str(solver["dtype"])).itemsize
    fig2 = config["parameters"]["fig2"]
    estimator = fig2["trace_estimator"]
    probe_count = 2 * int(estimator["probe_group_size"])
    sff_dimension = 1 << int(fig2["L"])
    probe_matrix_bytes = (
        sff_dimension
        * probe_count
        * np.dtype(str(estimator["dtype"])).itemsize
    )
    initialization_peak = (
        2 * probe_matrix_bytes
        + sff_dimension * probe_count * np.dtype(np.int64).itemsize
    )
    kick_peak = (
        2 * probe_matrix_bytes
        + (sff_dimension // 2)
        * min(probe_count, int(estimator["butterfly_chunk_size"]))
        * np.dtype(str(estimator["dtype"])).itemsize
    )
    trace_reduction_peak = 4 * probe_matrix_bytes
    sff_peak_bytes = max(initialization_peak, kick_peak, trace_reduction_peak)
    sff_peak_gib = sff_peak_bytes / 1024**3
    configured_gap_times = sorted(
        {
            *(int(value) for value in config["parameters"]["fig3_left"]["times"]),
            int(config["parameters"]["fig3_right"]["t"]),
        }
    )
    memory_rows = []
    for time_value in configured_gap_times:
        size = 4**time_value
        estimated = (
            (int(solver["krylov_dimension"]) + 4) * size * dtype_size / 1024**3
        )
        memory_rows.append(
            {
                "time": time_value,
                "protected_rank": protected_operator_basis(time_value).rank,
                "estimated_peak_gib": estimated,
                "within_limit": estimated <= float(solver["memory_limit_gib"]),
            }
        )
    return {
        "status": (
            "passed"
            if all(row["within_limit"] for row in memory_rows)
            and sff_peak_gib <= float(solver["memory_limit_gib"])
            else "failed"
        ),
        "run_id": config["run_id"],
        "profile": config["profile"],
        "sff_algorithm": "unbiased_random_phase_cross_matrix_free_floquet",
        "sff_estimated_peak_gib": sff_peak_gib,
        "gap_algorithm": "implicit_protected_basis_restarted_arnoldi",
        "memory": memory_rows,
    }


def _derived_seed(base_seed: int, *coordinates: int) -> int:
    sequence = np.random.SeedSequence([int(base_seed), *(int(value) for value in coordinates)])
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def _shard_bounds(total: int, shard_count: int, shard_index: int) -> tuple[int, int]:
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError(f"shard_index must be in [0,{shard_count})")
    quotient, remainder = divmod(total, shard_count)
    start = shard_index * quotient + min(shard_index, remainder)
    stop = start + quotient + (1 if shard_index < remainder else 0)
    return start, stop


@dataclass
class SFFShardState:
    start: int
    stop: int
    next_realization: int
    total: np.ndarray
    total_squared: np.ndarray
    split_total: np.ndarray
    split_total_squared: np.ndarray
    split_count: np.ndarray
    field_sum: float = 0.0
    field_square_sum: float = 0.0
    field_count: int = 0
    maximum_norm_drift: float = 0.0

    @property
    def count(self) -> int:
        return self.next_realization - self.start

    @property
    def complete(self) -> bool:
        return self.next_realization >= self.stop


def _new_sff_state(start: int, stop: int, time_count: int) -> SFFShardState:
    return SFFShardState(
        start=start,
        stop=stop,
        next_realization=start,
        total=np.zeros(time_count, dtype=np.float64),
        total_squared=np.zeros(time_count, dtype=np.float64),
        split_total=np.zeros((2, time_count), dtype=np.float64),
        split_total_squared=np.zeros((2, time_count), dtype=np.float64),
        split_count=np.zeros(2, dtype=np.int64),
    )


def _save_sff_checkpoint(path: Path, state: SFFShardState, fingerprint: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez(
            handle,
            schema_version=np.asarray(1, dtype=np.int64),
            fingerprint=np.asarray(fingerprint),
            start=np.asarray(state.start, dtype=np.int64),
            stop=np.asarray(state.stop, dtype=np.int64),
            next_realization=np.asarray(state.next_realization, dtype=np.int64),
            total=state.total,
            total_squared=state.total_squared,
            split_total=state.split_total,
            split_total_squared=state.split_total_squared,
            split_count=state.split_count,
            field_sum=np.asarray(state.field_sum),
            field_square_sum=np.asarray(state.field_square_sum),
            field_count=np.asarray(state.field_count, dtype=np.int64),
            maximum_norm_drift=np.asarray(state.maximum_norm_drift),
        )
    temporary.replace(path)


def _load_sff_checkpoint(path: Path, fingerprint: str) -> SFFShardState:
    with np.load(path, allow_pickle=False) as payload:
        if str(payload["fingerprint"]) != fingerprint:
            raise ValueError(f"checkpoint/config fingerprint mismatch: {path}")
        return SFFShardState(
            start=int(payload["start"]),
            stop=int(payload["stop"]),
            next_realization=int(payload["next_realization"]),
            total=np.asarray(payload["total"], dtype=np.float64),
            total_squared=np.asarray(payload["total_squared"], dtype=np.float64),
            split_total=np.asarray(payload["split_total"], dtype=np.float64),
            split_total_squared=np.asarray(payload["split_total_squared"], dtype=np.float64),
            split_count=np.asarray(payload["split_count"], dtype=np.int64),
            field_sum=float(payload["field_sum"]),
            field_square_sum=float(payload["field_square_sum"]),
            field_count=int(payload["field_count"]),
            maximum_norm_drift=float(payload["maximum_norm_drift"]),
        )


def run_sff_shard(
    parameters: dict[str, Any],
    *,
    sigma_index: int,
    shard_index: int,
    shard_count: int,
    checkpoint_path: Path,
    resume: bool,
    max_realizations_this_call: int | None = None,
) -> tuple[SFFShardState, bool]:
    """Run or resume one deterministic ``(sigma, realization-range)`` shard."""

    fig2 = parameters["fig2"]
    model = parameters["model"]
    total_realizations = int(fig2["disorder_realizations"])
    start, stop = _shard_bounds(total_realizations, shard_count, shard_index)
    times = np.arange(int(fig2["t_min"]), int(fig2["t_max"]) + 1, dtype=np.int64)
    estimator = fig2["trace_estimator"]
    fingerprint_payload = {
        "model": model,
        "fig2": fig2,
        "sigma_index": sigma_index,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "start": start,
        "stop": stop,
    }
    fingerprint = _canonical_hash(fingerprint_payload)
    resumed = bool(resume and checkpoint_path.exists())
    state = (
        _load_sff_checkpoint(checkpoint_path, fingerprint)
        if resumed
        else _new_sff_state(start, stop, times.size)
    )
    if state.start != start or state.stop != stop:
        raise ValueError("checkpoint shard bounds do not match current configuration")
    if state.complete:
        return state, resumed

    sigma = float(fig2["sigmas"][sigma_index])
    call_stop = stop
    if max_realizations_this_call is not None:
        call_stop = min(stop, state.next_realization + int(max_realizations_this_call))
    checkpoint_every = int(estimator["checkpoint_every_realizations"])
    processed_this_call = 0
    while state.next_realization < call_stop:
        realization = state.next_realization
        field_seed = _derived_seed(int(fig2["seed"]), sigma_index, realization, 0)
        fields = np.random.default_rng(field_seed).normal(
            loc=float(fig2["h_mean"]), scale=sigma, size=int(fig2["L"])
        )
        probe_seed = _derived_seed(int(fig2["seed"]), sigma_index, realization, 1)
        sample, diagnostics = random_phase_trace_sff(
            fields,
            times,
            seed=probe_seed,
            probe_group_size=int(estimator["probe_group_size"]),
            j_coupling=float(model["J"]),
            b=float(model["b"]),
            backend=str(estimator["backend"]),
            dtype=str(estimator["dtype"]),
            butterfly_chunk_size=int(estimator["butterfly_chunk_size"]),
            norm_check_interval=int(estimator["norm_check_interval"]),
        )
        state.total += sample
        state.total_squared += sample**2
        split = realization % 2
        state.split_total[split] += sample
        state.split_total_squared[split] += sample**2
        state.split_count[split] += 1
        normalized = (fields - float(fig2["h_mean"])) / sigma
        state.field_sum += float(np.sum(normalized))
        state.field_square_sum += float(np.sum(normalized**2))
        state.field_count += int(fig2["L"])
        state.maximum_norm_drift = max(
            state.maximum_norm_drift,
            float(diagnostics["maximum_state_norm_drift"]),
        )
        state.next_realization += 1
        processed_this_call += 1
        if processed_this_call % checkpoint_every == 0:
            _save_sff_checkpoint(checkpoint_path, state, fingerprint)
    _save_sff_checkpoint(checkpoint_path, state, fingerprint)
    return state, resumed


def _merge_sff_states(states: list[SFFShardState]) -> SFFShardState:
    if not states:
        raise ValueError("cannot merge an empty SFF shard list")
    time_count = states[0].total.size
    merged = _new_sff_state(0, sum(state.stop - state.start for state in states), time_count)
    merged.next_realization = sum(state.count for state in states)
    for state in states:
        merged.total += state.total
        merged.total_squared += state.total_squared
        merged.split_total += state.split_total
        merged.split_total_squared += state.split_total_squared
        merged.split_count += state.split_count
        merged.field_sum += state.field_sum
        merged.field_square_sum += state.field_square_sum
        merged.field_count += state.field_count
        merged.maximum_norm_drift = max(merged.maximum_norm_drift, state.maximum_norm_drift)
    return merged


def _variance(total: np.ndarray, total_squared: np.ndarray, count: int) -> np.ndarray:
    if count < 2:
        return np.full_like(total, np.nan)
    return np.maximum((total_squared - total**2 / count) / (count - 1), 0.0)


def _sff_rows_and_diagnostics(
    parameters: dict[str, Any],
    states_by_sigma: list[list[SFFShardState]],
    hashes: list[str],
    parameter_match: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fig2 = parameters["fig2"]
    times = np.arange(int(fig2["t_min"]), int(fig2["t_max"]) + 1, dtype=np.int64)
    coe = coe_form_factor(times, 1 << int(fig2["L"]))
    thermodynamic = thermodynamic_sff(times, int(fig2["L"]))
    rows: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    labels = ["pi/20", "pi/10", "100*pi"]
    for sigma_index, shard_states in enumerate(states_by_sigma):
        merged = _merge_sff_states(shard_states)
        count = merged.count
        mean = merged.total / count
        standard_error = np.sqrt(_variance(merged.total, merged.total_squared, count) / count)
        split_means = merged.split_total / merged.split_count[:, None]
        split_sem = np.vstack(
            [
                np.sqrt(
                    _variance(
                        merged.split_total[index],
                        merged.split_total_squared[index],
                        int(merged.split_count[index]),
                    )
                    / int(merged.split_count[index])
                )
                for index in range(2)
            ]
        )
        combined_sem = np.sqrt(np.sum(split_sem**2, axis=0))
        split_agreement = np.abs(split_means[0] - split_means[1]) <= 3.0 * np.maximum(
            combined_sem, np.finfo(float).eps
        )
        normalized_mean = merged.field_sum / merged.field_count
        normalized_variance = merged.field_square_sum / merged.field_count - normalized_mean**2
        sigma = float(fig2["sigmas"][sigma_index])
        series.append(
            {
                "sigma": sigma,
                "realizations": count,
                "normalized_field_mean": normalized_mean,
                "normalized_field_variance": normalized_variance,
                "maximum_state_norm_drift": merged.maximum_norm_drift,
                "split_agreement_fraction": float(np.mean(split_agreement)),
            }
        )
        for index, integer_time in enumerate(times):
            rows.append(
                {
                    "time": int(integer_time),
                    "sigma_label": labels[sigma_index],
                    "sigma": f"{sigma:.17g}",
                    "sff_mean": f"{mean[index]:.17g}",
                    "sff_sem": f"{standard_error[index]:.17g}",
                    "coe_paper_N": f"{coe[index]:.17g}",
                    f"thermodynamic_prediction_L{int(fig2['L'])}": f"{thermodynamic[index]:.17g}",
                    "generated_L": int(fig2["L"]),
                    "paper_L": int(fig2["paper_L"]),
                    "generated_realizations": count,
                    "paper_realizations": int(fig2["paper_disorder_realizations"]),
                    "trace_estimator": "independent_random_phase_cross",
                    "probe_group_size": int(fig2["trace_estimator"]["probe_group_size"]),
                    "parameter_match": parameter_match,
                }
            )
    return rows, {"series": series, "checkpoint_sha256": hashes}


def _save_backend_array(path: Path, array: Any, backend: str, chunk_elements: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    host_shape = tuple(int(value) for value in array.shape)
    host_dtype = np.dtype(str(array.dtype))
    temporary = path.with_suffix(path.suffix + ".tmp")
    destination = np.lib.format.open_memmap(
        temporary, mode="w+", dtype=host_dtype, shape=host_shape
    )
    flat_destination = destination.reshape(-1)
    flat_source = array.reshape(-1)
    for start in range(0, flat_destination.size, chunk_elements):
        stop = min(start + chunk_elements, flat_destination.size)
        flat_destination[start:stop] = _as_numpy(flat_source[start:stop])
    destination.flush()
    del destination
    temporary.replace(path)


def _load_backend_array(path: Path, backend: str, chunk_elements: int) -> Any:
    source = np.load(path, mmap_mode="r", allow_pickle=False)
    module = array_module(backend)
    if backend == "numpy":
        return np.array(source, copy=True)
    destination = module.empty(source.shape, dtype=str(source.dtype))  # pragma: no cover
    flat_destination = destination.reshape(-1)
    flat_source = source.reshape(-1)
    for start in range(0, flat_source.size, chunk_elements):  # pragma: no cover
        stop = min(start + chunk_elements, flat_source.size)
        flat_destination[start:stop] = module.asarray(flat_source[start:stop])
    return destination


def _save_block_state(
    directory: Path,
    state: RestartedArnoldiState,
    *,
    backend: str,
    fingerprint: str,
    chunk_elements: int,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    # The vector gets a generation-specific name.  Only after that file is fully
    # replaced do we atomically swing state.json to it, so an interruption cannot
    # overwrite the vector referenced by the previous valid checkpoint.
    basis_path = directory / f"basis_{state.iteration:08d}.npy"
    _save_backend_array(basis_path, state.basis, backend, chunk_elements)
    _write_json(
        directory / "state.json",
        {
            "schema_version": 1,
            "fingerprint": fingerprint,
            "iteration": state.iteration,
            "eigenvalue": [state.eigenvalue.real, state.eigenvalue.imag],
            "residual": state.residual,
            "eigenvalue_change": state.eigenvalue_change,
            "stable_iterations": state.stable_iterations,
            "history": state.history or [],
            "basis_path": basis_path.name,
            "basis_sha256": _sha256(basis_path),
        },
    )
    for stale in directory.glob("basis*.npy"):
        if stale != basis_path:
            stale.unlink()


def _load_block_state(
    directory: Path,
    *,
    backend: str,
    fingerprint: str,
    chunk_elements: int,
) -> RestartedArnoldiState:
    metadata = json.loads((directory / "state.json").read_text(encoding="utf-8"))
    if metadata["fingerprint"] != fingerprint:
        raise ValueError(f"gap checkpoint/config fingerprint mismatch: {directory}")
    basis_path = directory / metadata["basis_path"]
    if _sha256(basis_path) != metadata["basis_sha256"]:
        raise ValueError(f"gap checkpoint basis hash mismatch: {basis_path}")
    return RestartedArnoldiState(
        iteration=int(metadata["iteration"]),
        basis=_load_backend_array(basis_path, backend, chunk_elements),
        eigenvalue=complex(*metadata["eigenvalue"]),
        residual=float(metadata["residual"]),
        eigenvalue_change=float(metadata["eigenvalue_change"]),
        stable_iterations=int(metadata["stable_iterations"]),
        history=list(metadata["history"]),
    )


def run_gap_seed(
    point: dict[str, Any],
    solver_parameters: dict[str, Any],
    *,
    seed: int,
    checkpoint_directory: Path,
    resume: bool,
    max_iterations_this_call: int | None = None,
) -> dict[str, Any]:
    """Run/resume one independent restarted-Arnoldi seed for one gap point."""

    fingerprint = _canonical_hash(
        {"point": point, "solver": solver_parameters, "seed": int(seed)}
    )
    result_path = checkpoint_directory / "result.json"
    if resume and result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result["fingerprint"] != fingerprint:
            raise ValueError("completed gap result/config fingerprint mismatch")
        return result
    if float(point["sigma"]) == 0.0:
        result = {
            "status": "passed",
            "fingerprint": fingerprint,
            "seed": int(seed),
            "gap": 0.0,
            "leading_modulus": 1.0,
            "residual": 0.0,
            "protected_rank": protected_operator_basis(int(point["time"])).rank,
            "converged": True,
            "iterations": 0,
            "history": [],
        }
        _write_json(result_path, result)
        return result

    solver = RestartedArnoldiGapSolver(
        int(point["time"]),
        float(point["h_mean"]),
        float(point["sigma"]),
        krylov_dimension=int(solver_parameters["krylov_dimension"]),
        tolerance=float(solver_parameters["residual_tolerance"]),
        eigenvalue_tolerance=float(solver_parameters["eigenvalue_tolerance"]),
        stable_iterations=int(solver_parameters["stable_iterations"]),
        max_iterations=int(solver_parameters["max_iterations"]),
        seed=int(seed),
        backend=str(solver_parameters["backend"]),
        dtype=str(solver_parameters["dtype"]),
        dephasing_block_rows=int(solver_parameters["dephasing_block_rows"]),
        butterfly_chunk_size=int(solver_parameters["butterfly_chunk_size"]),
        projection_block_rows=int(solver_parameters["projection_block_rows"]),
        memory_limit_gib=float(solver_parameters["memory_limit_gib"]),
    )
    state_path = checkpoint_directory / "state.json"
    chunk_elements = int(solver_parameters["checkpoint_chunk_elements"])
    resumed = bool(resume and state_path.exists())
    state = (
        _load_block_state(
            checkpoint_directory,
            backend=solver.backend,
            fingerprint=fingerprint,
            chunk_elements=chunk_elements,
        )
        if resumed
        else solver.initialize()
    )
    iterations_this_call = 0
    checkpoint_every = int(solver_parameters["checkpoint_every_iterations"])
    while state.iteration < solver.max_iterations and not solver.converged(state):
        if (
            max_iterations_this_call is not None
            and iterations_this_call >= max_iterations_this_call
        ):
            break
        state = solver.step(state)
        iterations_this_call += 1
        if state.iteration % checkpoint_every == 0:
            _save_block_state(
                checkpoint_directory,
                state,
                backend=solver.backend,
                fingerprint=fingerprint,
                chunk_elements=chunk_elements,
            )
    _save_block_state(
        checkpoint_directory,
        state,
        backend=solver.backend,
        fingerprint=fingerprint,
        chunk_elements=chunk_elements,
    )
    numerical = solver.result(state)
    completed = solver.converged(state) or state.iteration >= solver.max_iterations
    result = {
        "status": (
            "passed" if solver.converged(state) else "failed" if completed else "in_progress"
        ),
        "fingerprint": fingerprint,
        "seed": int(seed),
        "resumed": resumed,
        **numerical,
    }
    if completed:
        _write_json(result_path, result)
        # result.json is the atomic terminal checkpoint.  Once it exists, the
        # multi-GiB restart vector is no longer needed for resume and retaining
        # every completed t=15 vector would waste hundreds of GiB across the grid.
        state_path.unlink(missing_ok=True)
        for basis_path in checkpoint_directory.glob("basis*.npy"):
            basis_path.unlink()
    return result


def _gap_points(parameters: dict[str, Any], targets: set[str]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    if "T003" in targets:
        left = parameters["fig3_left"]
        overrides = left.get("sigma_overrides", {})
        for time_value in left["times"]:
            sigmas = overrides.get(str(time_value), left["sigmas"])
            for sigma in sigmas:
                points.append(
                    {
                        "target_id": "T003",
                        "panel": "left",
                        "time": int(time_value),
                        "h_mean": float(left["h_mean"]),
                        "sigma": float(sigma),
                    }
                )
    if "T004" in targets:
        right = parameters["fig3_right"]
        for h_mean in right["h_means"]:
            for sigma in right["sigmas"]:
                points.append(
                    {
                        "target_id": "T004",
                        "panel": "right",
                        "time": int(right["t"]),
                        "h_mean": float(h_mean),
                        "sigma": float(sigma),
                    }
                )
    return points


def _point_key(point: dict[str, Any]) -> str:
    return (
        f"{point['target_id']}-t{int(point['time']):02d}-"
        f"h{float(point['h_mean']):+.6f}-s{float(point['sigma']):+.6f}"
    ).replace("+", "p").replace("-", "m")


def _aggregate_gap_point(
    point: dict[str, Any],
    seed_results: list[dict[str, Any]],
    seed_tolerance: float,
    parameter_match: str,
) -> dict[str, Any]:
    complete = all(result["status"] in {"passed", "failed"} for result in seed_results)
    moduli = np.asarray([result["leading_modulus"] for result in seed_results], dtype=float)
    agreement = float(np.max(moduli) - np.min(moduli)) if moduli.size else float("inf")
    converged = complete and all(bool(result["converged"]) for result in seed_results)
    mean_modulus = float(np.mean(moduli)) if moduli.size else float("nan")
    return {
        **point,
        "status": "passed" if converged and agreement <= seed_tolerance else "in_progress" if not complete else "failed",
        "gap": float(np.clip(1.0 - mean_modulus, 0.0, 1.0)),
        "leading_modulus": mean_modulus,
        "protected_rank": int(seed_results[0]["protected_rank"]),
        "maximum_residual": max(float(result["residual"]) for result in seed_results),
        "seed_agreement_absolute": agreement,
        "seeds": [int(result["seed"]) for result in seed_results],
        "iterations": [int(result["iterations"]) for result in seed_results],
        "parameter_match": parameter_match,
    }


def _gap_row(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel": result["panel"],
        "time": result["time"],
        "h_mean": f"{float(result['h_mean']):.17g}",
        "sigma": f"{float(result['sigma']):.17g}",
        "gap": f"{float(result['gap']):.17g}",
        "leading_modulus": f"{float(result['leading_modulus']):.17g}",
        "protected_rank": result["protected_rank"],
        "maximum_residual": f"{float(result['maximum_residual']):.17g}",
        "seed_agreement_absolute": f"{float(result['seed_agreement_absolute']):.17g}",
        "solver_status": result["status"],
        "parameter_match": result["parameter_match"],
    }


def run_paper_scale(
    config: dict[str, Any],
    workspace: Path,
    *,
    targets: set[str] | None = None,
    shard_index: int | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """Execute a complete campaign or one externally schedulable shard."""

    validate_paper_scale_config(config)
    selected = set(targets or {"T001", "T002", "T003", "T004"})
    unknown = selected - {"T001", "T002", "T003", "T004"}
    if unknown:
        raise ValueError(f"unsupported paper-scale targets: {sorted(unknown)}")
    if shard_index is not None and selected & {"T001", "T002"} and selected & {
        "T003",
        "T004",
    }:
        raise ValueError("a sharded invocation must select exactly one target family")
    parameters = config["parameters"]
    parameter_match = "paper_exact" if config["profile"] == "paper_scale" else "reduced_scale"
    execution = config["execution"]
    output_root = _safe_workspace_path(workspace, str(execution["output_root"]))
    output_namespace = Path(str(execution["output_namespace"]))
    checkpoint_root = _safe_workspace_path(workspace, str(execution["checkpoint_root"]))
    data_dir = output_root / "data" / output_namespace
    checks_dir = output_root / "checks" / output_namespace
    started = time.perf_counter()
    progress: dict[str, Any] = {
        "schema_version": 1,
        "run_id": config["run_id"],
        "profile": config["profile"],
        "selected_targets": sorted(selected),
        "requested_shard": shard_index,
        "resume": resume,
        "families": {},
    }
    artifacts: list[Path] = []
    target_checks: list[dict[str, Any]] = []

    if selected & {"T001", "T002"}:
        fig2 = parameters["fig2"]
        shard_count = int(execution["sff_shards"])
        shard_indices = [shard_index] if shard_index is not None else list(range(shard_count))
        if shard_index is not None and not 0 <= shard_index < shard_count:
            raise ValueError(f"SFF shard index must be in [0,{shard_count})")
        for sigma_index in range(len(fig2["sigmas"])):
            for current_shard in shard_indices:
                path = (
                    checkpoint_root
                    / "sff"
                    / f"sigma_{sigma_index}"
                    / f"shard_{current_shard:04d}.npz"
                )
                run_sff_shard(
                    parameters,
                    sigma_index=sigma_index,
                    shard_index=current_shard,
                    shard_count=shard_count,
                    checkpoint_path=path,
                    resume=resume,
                )

        states_by_sigma: list[list[SFFShardState]] = []
        checkpoint_hashes: list[str] = []
        all_sff_complete = True
        for sigma_index in range(len(fig2["sigmas"])):
            sigma_states: list[SFFShardState] = []
            for current_shard in range(shard_count):
                path = (
                    checkpoint_root
                    / "sff"
                    / f"sigma_{sigma_index}"
                    / f"shard_{current_shard:04d}.npz"
                )
                if not path.exists():
                    all_sff_complete = False
                    continue
                fingerprint = _canonical_hash(
                    {
                        "model": parameters["model"],
                        "fig2": fig2,
                        "sigma_index": sigma_index,
                        "shard_index": current_shard,
                        "shard_count": shard_count,
                        "start": _shard_bounds(
                            int(fig2["disorder_realizations"]), shard_count, current_shard
                        )[0],
                        "stop": _shard_bounds(
                            int(fig2["disorder_realizations"]), shard_count, current_shard
                        )[1],
                    }
                )
                state = _load_sff_checkpoint(path, fingerprint)
                sigma_states.append(state)
                all_sff_complete &= state.complete
                checkpoint_hashes.append(_sha256(path))
            states_by_sigma.append(sigma_states)
        progress["families"]["sff"] = {
            "complete": all_sff_complete,
            "completed_checkpoints": len(checkpoint_hashes),
            "required_checkpoints": shard_count * len(fig2["sigmas"]),
        }
        if all_sff_complete:
            sff_rows, diagnostics = _sff_rows_and_diagnostics(
                parameters, states_by_sigma, checkpoint_hashes, parameter_match
            )
            sff_path = data_dir / "fig2_sff.csv"
            _write_csv(sff_path, list(sff_rows[0]), sff_rows)
            diagnostics_path = checks_dir / "sff_convergence.json"
            _write_json(diagnostics_path, diagnostics)
            artifacts.extend((sff_path, diagnostics_path))
            acceptance = config["acceptance"]["sff"]
            expected_row_count = len(fig2["sigmas"]) * (
                int(fig2["t_max"]) - int(fig2["t_min"]) + 1
            )
            full_configured_grid = len(sff_rows) == expected_row_count
            paper_grid = (
                config["profile"] != "paper_scale"
                or (
                    int(fig2["L"]) == 15
                    and int(fig2["disorder_realizations"]) == 9490
                    and int(fig2["t_min"]) == 1
                    and int(fig2["t_max"]) == 1000
                )
            )
            finite_sff = all(
                np.isfinite(float(row["sff_mean"]))
                and np.isfinite(float(row["sff_sem"]))
                and float(row["sff_sem"]) >= 0.0
                for row in sff_rows
            )
            nonnegative_with_uncertainty = all(
                float(row["sff_mean"]) >= -3.0 * float(row["sff_sem"])
                for row in sff_rows
            )
            distinct_checkpoint_hashes = len(set(checkpoint_hashes))
            sff_pass = (
                full_configured_grid
                and paper_grid
                and finite_sff
                and nonnegative_with_uncertainty
                and all(
                    row["realizations"] == int(fig2["disorder_realizations"])
                    and abs(row["normalized_field_mean"])
                    <= float(acceptance["field_mean_absolute"])
                    and abs(row["normalized_field_variance"] - 1.0)
                    <= float(acceptance["field_variance_absolute"])
                    and row["maximum_state_norm_drift"]
                    <= float(acceptance["maximum_norm_drift"])
                    and row["split_agreement_fraction"]
                    >= float(acceptance["minimum_split_agreement_fraction"])
                    for row in diagnostics["series"]
                )
                and distinct_checkpoint_hashes
                >= int(acceptance["minimum_distinct_checkpoint_hashes"])
            )
            if "T001" in selected:
                target_checks.append(
                    {
                        "target_id": "T001",
                        "status": "passed" if sff_pass else "failed",
                        "parameter_match": parameter_match,
                        "checks": {
                            "full_configured_grid": full_configured_grid,
                            "paper_grid_contract_or_smoke_exemption": paper_grid,
                            "matrix_free_unbiased_estimator": True,
                            "finite_sff_and_sem": finite_sff,
                            "nonnegative_within_three_sem": nonnegative_with_uncertainty,
                            "field_moments": all(
                                abs(row["normalized_field_mean"])
                                <= float(acceptance["field_mean_absolute"])
                                and abs(row["normalized_field_variance"] - 1.0)
                                <= float(acceptance["field_variance_absolute"])
                                for row in diagnostics["series"]
                            ),
                            "state_norm_drift": all(
                                row["maximum_state_norm_drift"]
                                <= float(acceptance["maximum_norm_drift"])
                                for row in diagnostics["series"]
                            ),
                            "independent_split_agreement": all(
                                row["split_agreement_fraction"]
                                >= float(acceptance["minimum_split_agreement_fraction"])
                                for row in diagnostics["series"]
                            ),
                            "minimum_distinct_checkpoint_hashes": distinct_checkpoint_hashes
                            >= int(acceptance["minimum_distinct_checkpoint_hashes"]),
                        },
                    }
                )
            if "T002" in selected:
                target_checks.append(
                    {
                        "target_id": "T002",
                        "status": "passed" if sff_pass else "failed",
                        "parameter_match": parameter_match,
                        "checks": {
                            "short_time_rows_present": sum(
                                int(row["time"]) <= 100 for row in sff_rows
                            )
                            == len(fig2["sigmas"])
                            * sum(
                                time_value <= 100
                                for time_value in range(
                                    int(fig2["t_min"]), int(fig2["t_max"]) + 1
                                )
                            ),
                            "same_frozen_data_as_main_panel": True,
                            "ensemble_acceptance_inherited": sff_pass,
                        },
                    }
                )

    gap_targets = selected & {"T003", "T004"}
    if gap_targets:
        points = _gap_points(parameters, gap_targets)
        gap_shards = int(execution["gap_shards"])
        if gap_shards > len(points):
            raise ValueError("gap_shards cannot exceed the selected point count")
        point_indices = list(range(len(points)))
        if shard_index is not None:
            if not 0 <= shard_index < gap_shards:
                raise ValueError(f"gap shard index must be in [0,{gap_shards})")
            start, stop = _shard_bounds(len(points), gap_shards, shard_index)
            point_indices = list(range(start, stop))
        solver_parameters = parameters["solver"]
        for point_index in point_indices:
            point = points[point_index]
            key = _point_key(point)
            seed_results = [
                run_gap_seed(
                    point,
                    solver_parameters,
                    seed=int(seed),
                    checkpoint_directory=checkpoint_root / "gap" / key / f"seed_{int(seed)}",
                    resume=resume,
                )
                for seed in solver_parameters["seeds"]
            ]
            aggregate = _aggregate_gap_point(
                point,
                seed_results,
                float(config["acceptance"]["gap"]["seed_agreement_absolute"]),
                parameter_match,
            )
            _write_json(checkpoint_root / "gap" / key / "aggregate.json", aggregate)

        aggregates: list[dict[str, Any]] = []
        for point in points:
            aggregate_path = checkpoint_root / "gap" / _point_key(point) / "aggregate.json"
            if aggregate_path.exists():
                aggregates.append(json.loads(aggregate_path.read_text(encoding="utf-8")))
        all_gap_complete = len(aggregates) == len(points) and all(
            row["status"] in {"passed", "failed"} for row in aggregates
        )
        progress["families"]["gap"] = {
            "complete": all_gap_complete,
            "completed_points": len(aggregates),
            "required_points": len(points),
        }
        if all_gap_complete:
            gap_fields = list(_gap_row(aggregates[0]))
            for target_id, filename in (
                ("T003", "fig3_gap_left.csv"),
                ("T004", "fig3_gap_right.csv"),
            ):
                if target_id not in gap_targets:
                    continue
                rows = [_gap_row(row) for row in aggregates if row["target_id"] == target_id]
                path = data_dir / filename
                _write_csv(path, gap_fields, rows)
                artifacts.append(path)
            convergence_path = checks_dir / "gap_convergence.json"
            _write_json(convergence_path, {"rows": aggregates})
            artifacts.append(convergence_path)
            gap_acceptance = config["acceptance"]["gap"]
            for target_id in sorted(gap_targets):
                target_rows = [row for row in aggregates if row["target_id"] == target_id]
                expected_point_count = (
                    len(parameters["fig3_left"]["times"])
                    * len(parameters["fig3_left"]["sigmas"])
                    if target_id == "T003"
                    else len(parameters["fig3_right"]["h_means"])
                    * len(parameters["fig3_right"]["sigmas"])
                )
                expected_ranks = all(
                    int(row["protected_rank"])
                    == sum(transfer_multiplicities(int(row["time"])))
                    for row in target_rows
                )
                checks = {
                    "all_points_present": len(target_rows) == expected_point_count,
                    "all_seeds_converged": all(row["status"] == "passed" for row in target_rows),
                    "residual_tolerance": max(
                        float(row["maximum_residual"]) for row in target_rows
                    )
                    <= float(gap_acceptance["maximum_residual"]),
                    "seed_agreement": max(
                        float(row["seed_agreement_absolute"]) for row in target_rows
                    )
                    <= float(gap_acceptance["seed_agreement_absolute"]),
                    "protected_rank_matches_source_inventory": expected_ranks,
                    "positive_sigma_has_subunit_mode": all(
                        float(row["sigma"]) == 0.0
                        or 0.0 < float(row["leading_modulus"]) < 1.0
                        for row in target_rows
                    ),
                }
                target_checks.append(
                    {
                        "target_id": target_id,
                        "status": "passed" if all(checks.values()) else "failed",
                        "parameter_match": parameter_match,
                        "checks": checks,
                    }
                )

    progress["elapsed_seconds"] = time.perf_counter() - started
    progress["complete"] = bool(target_checks) and {
        row["target_id"] for row in target_checks
    } == selected
    progress["status"] = (
        "passed"
        if progress["complete"]
        and all(row["status"] == "passed" for row in target_checks)
        else "failed"
        if progress["complete"]
        else "in_progress"
    )
    progress_path = checks_dir / "paper_scale_progress.json"
    _write_json(progress_path, progress)
    artifacts.append(progress_path)

    if progress["complete"]:
        checks_payload = {
            "schema_version": 1,
            "paper_id": "1805.00931",
            "run_id": config["run_id"],
            "status": progress["status"],
            "targets": target_checks,
            "global_checks": {
                "source_pixels_read": False,
                "source_pdfs_read": False,
                "reference_curves_used": False,
                "author_code_used": False,
                "author_arrays_used": False,
                "declared_parameters_loaded_from_config": True,
            },
        }
        target_path = checks_dir / "target_checks.json"
        _write_json(target_path, checks_payload)
        artifacts.append(target_path)
        performance_path = checks_dir / "performance_profile.json"
        _write_json(
            performance_path,
            {
                "schema_version": 1,
                "run_id": config["run_id"],
                "scale": config["profile"],
                "paper_scale_reached": config["profile"] == "paper_scale"
                and checks_payload["status"] == "passed",
                "elapsed_seconds": progress["elapsed_seconds"],
            },
        )
        artifacts.append(performance_path)
        manifest_path = checks_dir / "generated_data_manifest.json"
        manifest_artifacts = {
            path.relative_to(workspace).as_posix(): {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": _sha256(path),
            }
            for path in artifacts
            if path.exists()
        }
        _write_json(
            manifest_path,
            {
                "schema_version": 1,
                "status": checks_payload["status"],
                "paper_id": "1805.00931",
                "run_id": config["run_id"],
                "generated_data_provenance": "independent_formula_numerics",
                "source_pixels_read": False,
                "source_pdfs_read": False,
                "reference_curves_used": False,
                "author_code_used": False,
                "author_arrays_used": False,
                "parameter_scale": parameter_match,
                "artifacts": manifest_artifacts,
            },
        )
        artifacts.append(manifest_path)
    return progress
