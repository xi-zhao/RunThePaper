"""Checkpointed paper-scale campaign for all numerical panels.

The campaign is a union of three scientifically distinct job families rather
than a wasteful rectangular grid.  Every condition is hash-bound, assigned to
exactly one scheduler shard, and resumable at condition granularity.  On an
A100 host the Torch backend batches trajectories on CUDA; NumPy remains the
auditable CPU reference.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

from .gaussian import EnsembleResult, simulate_ensemble
from .observables import chord_length
from .rendering import render_all
from .reproduction import _sha256, _write_csv, _write_json
from .scaling import (
    fit_correlation_size,
    fit_effective_central_charge,
    fit_entropy_size,
    local_power_slope,
)
from .theory import dark_state_exponents
from .torch_backend import simulate_ensemble_torch, torch_cuda_available


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _implementation_hash(workspace: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "src/dark_state_fermions/gaussian.py",
        "src/dark_state_fermions/observables.py",
        "src/dark_state_fermions/scaling.py",
        "src/dark_state_fermions/theory.py",
        "src/dark_state_fermions/torch_backend.py",
        "src/dark_state_fermions/paper_scale.py",
    ):
        path = workspace / relative
        digest.update(relative.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _condition(
    *,
    family: str,
    target_ids: list[str],
    length: int,
    exponent: float,
    gamma: float,
    dynamics: dict[str, Any],
    family_index: int,
) -> dict[str, Any]:
    payload = {
        "family": family,
        "target_ids": target_ids,
        "L": int(length),
        "p": float(exponent),
        "gamma": float(gamma),
        "dt": float(dynamics["dt"]),
        "burn_time": float(dynamics["burn_time"]),
        "sample_time": float(dynamics["sample_time"]),
        "sample_interval": float(dynamics["sample_interval"]),
        "trajectories": int(dynamics["trajectories"]),
        "entropy_origins": int(dynamics["entropy_origins"]),
        "family_index": family_index,
    }
    payload["condition_id"] = f"{family}-{_canonical_hash(payload)[:16]}"
    return payload


def build_conditions(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand the immutable union of target-specific paper-scale jobs."""

    conditions: list[dict[str, Any]] = []
    for family in config["families"]:
        name = str(family["name"])
        target_ids = [str(value) for value in family["target_ids"]]
        if "parameter_pairs" in family:
            tuples = [
                (int(length), float(pair["p"]), float(pair["gamma"]))
                for pair in family["parameter_pairs"]
                for length in family["sizes"]
            ]
        else:
            tuples = list(
                product(
                    [int(value) for value in family["sizes"]],
                    [float(value) for value in family["p_values"]],
                    [float(value) for value in family["gamma_values"]],
                )
            )
        for family_index, (length, exponent, gamma) in enumerate(tuples):
            conditions.append(
                _condition(
                    family=name,
                    target_ids=target_ids,
                    length=length,
                    exponent=exponent,
                    gamma=gamma,
                    dynamics=family["dynamics"],
                    family_index=family_index,
                )
            )

    identifiers = [row["condition_id"] for row in conditions]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("paper-scale condition identifiers are not unique")
    stride = int(config["scheduler"]["seed_stride"])
    max_trajectories = max(row["trajectories"] for row in conditions)
    if stride <= max_trajectories:
        raise ValueError("seed_stride must exceed every condition trajectory count")
    for index, row in enumerate(conditions):
        row["condition_index"] = index
        row["seed_base"] = int(config["scheduler"]["seed_base"]) + index * stride
        row["shard_index"] = index % int(config["scheduler"]["shards"])
    return conditions


def campaign_plan(config_path: Path, workspace: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    conditions = build_conditions(config)
    by_family: dict[str, dict[str, int]] = {}
    for condition in conditions:
        summary = by_family.setdefault(
            condition["family"], {"conditions": 0, "trajectories": 0}
        )
        summary["conditions"] += 1
        summary["trajectories"] += condition["trajectories"]
    return {
        "schema_version": 1,
        "paper_id": "2105.08076",
        "profile": "paper_scale",
        "output_namespace": config.get("output_namespace", "paper_scale"),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _implementation_hash(workspace),
        "condition_count": len(conditions),
        "trajectory_count": sum(row["trajectories"] for row in conditions),
        "shards": config["scheduler"]["shards"],
        "families": by_family,
        "a100": {
            "available_to_user": True,
            "backend": "torch_cuda_batched_complex128",
            "local_cuda_available": torch_cuda_available(),
            "cpu_reference_backend": "numpy_complex128",
            "batch_size": config["machine"]["gpu_batch_size"],
        },
        "source_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
            "raw_or_reference_paths_read": False,
        },
        "conditions": conditions,
    }


def write_plan(config_path: Path, workspace: Path) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = campaign_plan(config_path, workspace)
    _, _, check_dir = _output_roots(config, workspace)
    path = check_dir / "plan.json"
    _write_json(path, plan)
    return path


def _result_payload(result: EnsembleResult) -> dict[str, Any]:
    payload = asdict(result)
    for key, value in list(payload.items()):
        if isinstance(value, np.ndarray):
            payload[key] = value.tolist()
    return payload


def _result_from_payload(payload: dict[str, Any]) -> EnsembleResult:
    return EnsembleResult(
        length=int(payload["length"]),
        exponent=float(payload["exponent"]),
        gamma=float(payload["gamma"]),
        ell=np.asarray(payload["ell"], dtype=float),
        entropy_mean=np.asarray(payload["entropy_mean"], dtype=float),
        entropy_sem=np.asarray(payload["entropy_sem"], dtype=float),
        correlation_positive_mean=np.asarray(
            payload["correlation_positive_mean"], dtype=float
        ),
        correlation_positive_sem=np.asarray(
            payload["correlation_positive_sem"], dtype=float
        ),
        correlation_connected_mean=np.asarray(
            payload["correlation_connected_mean"], dtype=float
        ),
        trajectories=int(payload["trajectories"]),
        samples_per_trajectory=int(payload["samples_per_trajectory"]),
        max_invariant_residual=float(payload["max_invariant_residual"]),
        stationary_relative_drift=float(payload["stationary_relative_drift"]),
    )


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.partial")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _output_roots(config: dict[str, Any], workspace: Path) -> tuple[Path, Path, Path]:
    namespace = str(config.get("output_namespace", "paper_scale"))
    if not namespace or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789_-"
        for character in namespace
    ):
        raise ValueError("output_namespace must be a safe lowercase path component")
    return (
        workspace / "outputs" / "data" / namespace,
        workspace / "outputs" / "figures" / namespace,
        workspace / "outputs" / "checks" / namespace,
    )


def _select_backend(requested: str) -> str:
    if requested == "auto":
        return "torch_cuda" if torch_cuda_available() else "numpy"
    if requested not in {"numpy", "torch_cpu", "torch_cuda"}:
        raise ValueError(f"unsupported backend: {requested}")
    return requested


def _execute_condition(
    condition: dict[str, Any],
    *,
    backend: str,
    gpu_batch_size: int,
) -> EnsembleResult:
    kwargs = {
        "length": condition["L"],
        "exponent": condition["p"],
        "gamma": condition["gamma"],
        "dt": condition["dt"],
        "burn_time": condition["burn_time"],
        "sample_time": condition["sample_time"],
        "sample_interval": condition["sample_interval"],
        "trajectories": condition["trajectories"],
        "seed_base": condition["seed_base"],
        "entropy_origins": condition["entropy_origins"],
    }
    if backend == "numpy":
        return simulate_ensemble(**kwargs)
    return simulate_ensemble_torch(
        **kwargs,
        device="cuda" if backend == "torch_cuda" else "cpu",
        batch_size=gpu_batch_size,
    )


def run_shard(
    config_path: Path,
    workspace: Path,
    *,
    shard_index: int,
    shard_count: int | None,
    backend: str,
    resume: bool,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = campaign_plan(config_path, workspace)
    expected_shards = int(config["scheduler"]["shards"])
    actual_shards = expected_shards if shard_count is None else shard_count
    if actual_shards != expected_shards:
        raise ValueError("shard_count must match the frozen paper-scale config")
    if not 0 <= shard_index < actual_shards:
        raise ValueError("shard_index is outside the configured range")
    selected_backend = _select_backend(backend)
    _, _, check_dir = _output_roots(config, workspace)
    checkpoints = check_dir / "checkpoints"
    completed = 0
    resumed = 0
    for condition in plan["conditions"]:
        if condition["condition_index"] % actual_shards != shard_index:
            continue
        checkpoint = checkpoints / f"{condition['condition_id']}.json"
        if checkpoint.exists() and resume:
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            if (
                payload.get("config_sha256") != plan["config_sha256"]
                or payload.get("implementation_sha256") != plan["implementation_sha256"]
                or payload.get("condition") != condition
            ):
                raise ValueError(f"stale or mismatched checkpoint: {checkpoint}")
            resumed += 1
            continue
        result = _execute_condition(
            condition,
            backend=selected_backend,
            gpu_batch_size=int(config["machine"]["gpu_batch_size"]),
        )
        _atomic_json(
            checkpoint,
            {
                "schema_version": 1,
                "paper_id": "2105.08076",
                "config_sha256": plan["config_sha256"],
                "implementation_sha256": plan["implementation_sha256"],
                "backend": selected_backend,
                "condition": condition,
                "result": _result_payload(result),
            },
        )
        completed += 1
    summary = {
        "schema_version": 1,
        "shard_index": shard_index,
        "shard_count": actual_shards,
        "backend": selected_backend,
        "completed": completed,
        "resumed": resumed,
    }
    _atomic_json(
        check_dir / "shards" / f"shard-{shard_index:03d}.json",
        summary,
    )
    return summary


def _load_complete_results(
    plan: dict[str, Any], workspace: Path
) -> dict[str, dict[tuple[int, float, float, float], EnsembleResult]]:
    namespace = str(plan["output_namespace"])
    checkpoints = workspace / "outputs" / "checks" / namespace / "checkpoints"
    results: dict[str, dict[tuple[int, float, float, float], EnsembleResult]] = {}
    missing: list[str] = []
    for condition in plan["conditions"]:
        path = checkpoints / f"{condition['condition_id']}.json"
        if not path.exists():
            missing.append(condition["condition_id"])
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            payload.get("config_sha256") != plan["config_sha256"]
            or payload.get("implementation_sha256") != plan["implementation_sha256"]
            or payload.get("condition") != condition
        ):
            raise ValueError(f"checkpoint contract mismatch: {path}")
        key = (
            condition["L"],
            condition["p"],
            condition["gamma"],
            condition["dt"],
        )
        results.setdefault(condition["family"], {})[key] = _result_from_payload(
            payload["result"]
        )
    if missing:
        raise RuntimeError(
            f"paper-scale aggregation refused: {len(missing)} conditions missing; "
            f"first={missing[0]}"
        )
    return results


def _family_config(config: dict[str, Any], name: str) -> dict[str, Any]:
    return next(item for item in config["families"] if item["name"] == name)


def _lookup(
    family_results: dict[tuple[int, float, float, float], EnsembleResult],
    *,
    length: int,
    exponent: float,
    gamma: float,
    dt: float,
) -> EnsembleResult:
    return family_results[(length, float(exponent), float(gamma), float(dt))]


def _write_paper_target_data(
    config: dict[str, Any],
    results: dict[str, dict[tuple[int, float, float, float], EnsembleResult]],
    data_dir: Path,
) -> dict[str, list[dict[str, Any]]]:
    phase = _family_config(config, "phase_map")
    exponent_family = _family_config(config, "exponent_scaling")
    representative = _family_config(config, "representative_profiles")
    phase_results = results["phase_map"]
    exponent_results = results["exponent_scaling"]
    representative_results = results["representative_profiles"]

    phase_length = int(phase["sizes"][0])
    phase_dt = float(phase["dynamics"]["dt"])
    rows_t001: list[dict[str, Any]] = []
    for gamma in phase["gamma_values"]:
        for exponent in phase["p_values"]:
            result = _lookup(
                phase_results,
                length=phase_length,
                exponent=exponent,
                gamma=gamma,
                dt=phase_dt,
            )
            fit = fit_effective_central_charge(
                phase_length, result.ell, result.entropy_mean
            )
            rows_t001.append(
                {
                    "gamma": gamma,
                    "p": exponent,
                    "inverse_p": 1.0 / exponent,
                    "L": phase_length,
                    "c_eff": fit.parameters["c"],
                    "fit_relative_rms": fit.relative_rms,
                    "parameter_status": "paper_size_reconstructed_dynamics",
                }
            )

    scaling_sizes = [int(value) for value in exponent_family["sizes"]]
    scaling_dt = float(exponent_family["dynamics"]["dt"])
    rows_t002: list[dict[str, Any]] = []
    rows_t003: list[dict[str, Any]] = []
    rows_t006: list[dict[str, Any]] = []
    for gamma in exponent_family["gamma_values"]:
        for exponent in exponent_family["p_values"]:
            series = [
                _lookup(
                    exponent_results,
                    length=length,
                    exponent=exponent,
                    gamma=gamma,
                    dt=scaling_dt,
                )
                for length in scaling_sizes
            ]
            half = [item.half_chain() for item in series]
            entropy = np.asarray([item["entropy"] for item in half])
            correlation = np.asarray([item["correlation_positive"] for item in half])
            fit_s = fit_entropy_size(np.asarray(scaling_sizes, dtype=float), entropy)
            fit_c = fit_correlation_size(
                np.asarray(scaling_sizes, dtype=float), correlation
            )
            theory_a: float | str = ""
            theory_b: float | str = ""
            if 1.0 < float(exponent) < 1.5:
                theory_a, theory_b = dark_state_exponents(float(exponent))
            rows_t002.append(
                {
                    "gamma": gamma,
                    "p": exponent,
                    "inverse_p": 1.0 / exponent,
                    "fitted_a": fit_c.parameters["a"],
                    "direct_a": fit_c.parameters["direct_a"],
                    "theory_a": theory_a,
                    "fit_relative_rms": fit_c.relative_rms,
                    "parameter_status": "paper_sizes_reconstructed_dynamics",
                }
            )
            rows_t003.append(
                {
                    "gamma": gamma,
                    "p": exponent,
                    "inverse_p": 1.0 / exponent,
                    "fitted_b": fit_s.parameters["b"],
                    "direct_b": local_power_slope(
                        np.asarray(scaling_sizes, dtype=float), entropy
                    ),
                    "theory_b": theory_b,
                    "fit_relative_rms": fit_s.relative_rms,
                    "parameter_status": "paper_sizes_reconstructed_dynamics",
                }
            )
            for length, current in zip(scaling_sizes, series, strict=True):
                fit = fit_effective_central_charge(
                    length, current.ell, current.entropy_mean
                )
                rows_t006.append(
                    {
                        "gamma": gamma,
                        "L": length,
                        "p": exponent,
                        "inverse_p": 1.0 / exponent,
                        "c_eff": fit.parameters["c"],
                        "fit_relative_rms": fit.relative_rms,
                        "parameter_status": "paper_size_reconstructed_dynamics",
                    }
                )

    rep_dt = float(representative["dynamics"]["dt"])
    rep_sizes = [int(value) for value in representative["sizes"]]
    pairs = [dict(item) for item in representative["parameter_pairs"]]
    rows_t004: list[dict[str, Any]] = []
    rows_t005: list[dict[str, Any]] = []
    rows_t008: list[dict[str, Any]] = []
    rows_t009: list[dict[str, Any]] = []
    for pair in pairs:
        for length in rep_sizes:
            current = _lookup(
                representative_results,
                length=length,
                exponent=pair["p"],
                gamma=pair["gamma"],
                dt=rep_dt,
            )
            half = current.half_chain()
            common = {
                "physics_phase": pair["physics_phase"],
                "caption_phase": pair["caption_phase"],
                "gamma": pair["gamma"],
                "p": pair["p"],
                "L": length,
                "parameter_status": "paper_size_reconstructed_dynamics",
            }
            rows_t004.append(
                {
                    **common,
                    "entropy": half["entropy"],
                    "entropy_sem": half["entropy_sem"],
                }
            )
            rows_t005.append(
                {
                    **common,
                    "correlation_positive": half["correlation_positive"],
                    "correlation_positive_sem": half["correlation_positive_sem"],
                }
            )
            chords = chord_length(length, current.ell)
            for index, ell in enumerate(current.ell):
                profile = {**common, "ell": ell, "chord_length": chords[index]}
                rows_t008.append(
                    {
                        **profile,
                        "entropy": current.entropy_mean[index],
                        "entropy_sem": current.entropy_sem[index],
                    }
                )
                rows_t009.append(
                    {
                        **profile,
                        "correlation_positive": current.correlation_positive_mean[
                            index
                        ],
                        "correlation_positive_sem": current.correlation_positive_sem[
                            index
                        ],
                    }
                )

    algebraic = next(item for item in pairs if item["physics_phase"] == "algebraic")
    profile_length = max(rep_sizes)
    profile = _lookup(
        representative_results,
        length=profile_length,
        exponent=algebraic["p"],
        gamma=algebraic["gamma"],
        dt=rep_dt,
    )
    a, b = dark_state_exponents(float(algebraic["p"]))
    anchor = int(np.argmin(np.abs(profile.ell - profile_length / 4)))
    theory_entropy = profile.ell**b
    theory_entropy *= profile.entropy_mean[anchor] / theory_entropy[anchor]
    theory_rescaled = profile.ell ** (2.0 - a)
    observed_rescaled = 20.0 * profile.ell**2 * profile.correlation_positive_mean
    theory_rescaled *= observed_rescaled[anchor] / theory_rescaled[anchor]
    rows_t007 = [
        {
            "L": profile_length,
            "gamma": algebraic["gamma"],
            "p": algebraic["p"],
            "ell": profile.ell[index],
            "entropy": profile.entropy_mean[index],
            "correlation_positive": profile.correlation_positive_mean[index],
            "theory_entropy": theory_entropy[index],
            "theory_rescaled_correlation": theory_rescaled[index],
            "theory_a": a,
            "theory_b": b,
            "parameter_status": "paper_size_reconstructed_dynamics",
        }
        for index in range(profile.ell.size)
    ]

    rows = {
        "T001": rows_t001,
        "T002": rows_t002,
        "T003": rows_t003,
        "T004": rows_t004,
        "T005": rows_t005,
        "T006": rows_t006,
        "T007": rows_t007,
        "T008": rows_t008,
        "T009": rows_t009,
    }
    filenames = {
        "T001": "T001_phase_map.csv",
        "T002": "T002_correlation_exponent.csv",
        "T003": "T003_entropy_exponent.csv",
        "T004": "T004_entropy_size.csv",
        "T005": "T005_correlation_size.csv",
        "T006": "T006_effective_central_charge.csv",
        "T007": "T007_algebraic_scaling.csv",
        "T008": "T008_subsystem_entropy.csv",
        "T009": "T009_subsystem_correlation.csv",
    }
    for target, target_rows in rows.items():
        _write_csv(data_dir / filenames[target], target_rows)
    return rows


def aggregate(config_path: Path, workspace: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = campaign_plan(config_path, workspace)
    results = _load_complete_results(plan, workspace)
    data_dir, figure_dir, check_dir = _output_roots(config, workspace)
    rows = _write_paper_target_data(config, results, data_dir)
    render_all(data_dir, figure_dir)

    convergence = results["convergence"]
    convergence_rows: list[dict[str, Any]] = []
    for pair in _family_config(config, "convergence")["parameter_pairs"]:
        values = []
        for dt in sorted({key[3] for key in convergence}):
            current = _lookup(
                convergence,
                length=400,
                exponent=pair["p"],
                gamma=pair["gamma"],
                dt=dt,
            ).half_chain()
            values.append((dt, current))
        finest = values[0][1]
        for dt, current in values[1:]:
            convergence_rows.append(
                {
                    "physics_phase": pair["physics_phase"],
                    "dt": dt,
                    "entropy_relative_to_finest": abs(
                        current["entropy"] - finest["entropy"]
                    )
                    / max(abs(finest["entropy"]), 1e-12),
                    "correlation_relative_to_finest": abs(
                        current["correlation_positive"] - finest["correlation_positive"]
                    )
                    / max(abs(finest["correlation_positive"]), 1e-12),
                }
            )
    _write_csv(check_dir / "convergence.csv", convergence_rows)
    convergence_max = max(
        max(row["entropy_relative_to_finest"], row["correlation_relative_to_finest"])
        for row in convergence_rows
    )
    acceptance = {
        "schema_version": 1,
        "paper_id": "2105.08076",
        "conditions_complete": plan["condition_count"],
        "targets_generated": sorted(rows),
        "all_targets_generated": sorted(rows)
        == [f"T{index:03d}" for index in range(1, 10)],
        "maximum_dt_convergence_relative_change": convergence_max,
        "dt_convergence_passed": convergence_max
        <= float(config["acceptance"]["dt_relative_change_max"]),
        "paper_parameters_executed": bool(
            config.get("paper_parameters_executed", False)
        ),
        "parameter_status": "paper_sizes_reconstructed_dynamics",
        "source_boundary": plan["source_boundary"],
    }
    _write_json(check_dir / "target_acceptance.json", acceptance)

    manifest_paths = sorted(
        [
            *data_dir.glob("*.csv"),
            *figure_dir.glob("*.png"),
            check_dir / "convergence.csv",
            check_dir / "target_acceptance.json",
        ]
    )
    manifest = {
        "schema_version": 1,
        "paper_id": "2105.08076",
        "config_sha256": plan["config_sha256"],
        "implementation_sha256": plan["implementation_sha256"],
        "outputs": [
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in manifest_paths
        ],
        "source_boundary": plan["source_boundary"],
    }
    _write_json(check_dir / "campaign_manifest.json", manifest)
    return {"acceptance": acceptance, "manifest": manifest}


def run_all(
    config_path: Path,
    workspace: Path,
    *,
    backend: str,
    resume: bool,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    write_plan(config_path, workspace)
    summaries = []
    for shard_index in range(int(config["scheduler"]["shards"])):
        summaries.append(
            run_shard(
                config_path,
                workspace,
                shard_index=shard_index,
                shard_count=None,
                backend=backend,
                resume=resume,
            )
        )
    aggregated = aggregate(config_path, workspace)
    return {"shards": summaries, **aggregated}
