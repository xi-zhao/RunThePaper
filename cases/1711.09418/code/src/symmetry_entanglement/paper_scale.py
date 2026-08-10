"""Checkpointed paper-scale execution for the two numerical paper figures.

This module only consumes the machine-readable configuration and formula-derived
quantities from :mod:`symmetry_entanglement.model`.  It never reads the paper,
source figures, comparison images, author code, or author numerical arrays.

The expensive ``2**24`` spectrum enumeration is exact for the plotted rank
window while being streaming: each shard retains only the largest requested
many-body weights for the all-charge curve and every requested charge sector.
Merging those per-shard top-k sets yields the same global top-k set as a
monolithic enumeration, without keeping all 16,777,216 states resident.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import time
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from scipy.linalg import toeplitz

from .model import (
    analytic_charge_curves,
    analytic_integrated_spectrum,
    correlation_eigenvalues,
    enumerate_many_body_spectrum,
    half_filled_toeplitz_column,
)

PAPER_ID = "1711.09418"
CONFIG_SCHEMA_VERSION = 1
CHECKPOINT_SCHEMA_VERSION = 1


class PaperScaleConfigError(ValueError):
    """Raised when the paper-scale configuration is incomplete or unsafe."""


@dataclass(frozen=True)
class SpectrumInputs:
    """Precomputed quantities shared by all many-body spectrum shards."""

    selected_probabilities: np.ndarray
    ground_occupancy: np.ndarray
    log_fixed: float
    central_log_lambda_max: float
    selected_entanglement_energies: np.ndarray


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _array_hash(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.tobytes())
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _portable_path(path: Path) -> str:
    """Prefer a workspace-relative artifact path and never require it."""

    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _atomic_npz(path: Path, **arrays: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            np.savez_compressed(handle, **arrays)
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _required_object(payload: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PaperScaleConfigError(f"{key} must be an object")
    return value


def _required_positive_int(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PaperScaleConfigError(f"{key} must be a positive integer")
    return value


def load_config(path: Path) -> dict[str, Any]:
    """Load and strictly validate a paper-scale configuration."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PaperScaleConfigError(f"cannot load JSON config {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PaperScaleConfigError("configuration root must be an object")
    if payload.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise PaperScaleConfigError(f"schema_version must be {CONFIG_SCHEMA_VERSION}")
    if payload.get("paper_id") != PAPER_ID:
        raise PaperScaleConfigError(f"paper_id must be {PAPER_ID}")

    scientific = _required_object(payload, "scientific_parameters")
    execution = _required_object(payload, "execution")
    targets = _required_object(payload, "targets")
    review = _required_object(payload, "review_protocol")
    for target_id in ("T001", "T002"):
        target = _required_object(targets, target_id)
        criteria = target.get("acceptance_criteria")
        if (
            not isinstance(criteria, list)
            or not criteria
            or not all(isinstance(item, str) and item.strip() for item in criteria)
        ):
            raise PaperScaleConfigError(
                f"targets.{target_id}.acceptance_criteria must be non-empty strings"
            )
        machine = _required_object(target, "machine_acceptance")
        _required_positive_int(machine, "minimum_logical_cpus")
        _required_positive_int(machine, "minimum_ram_gib")

    length = _required_positive_int(scientific, "subsystem_length")
    active_modes = _required_positive_int(scientific, "active_correlation_modes")
    selected_modes = _required_positive_int(scientific, "fig3_selected_modes")
    if length % 2 or active_modes % 2 or selected_modes % 2:
        raise PaperScaleConfigError("subsystem_length and mode counts must be even")
    if not selected_modes <= active_modes < length:
        raise PaperScaleConfigError(
            "require fig3_selected_modes <= active_correlation_modes < subsystem_length"
        )
    if scientific.get("filling") != 0.5 or scientific.get("luttinger_k") != 1.0:
        raise PaperScaleConfigError("the paper figure requires half filling and K=1")
    sectors = scientific.get("fig3_sectors")
    if sectors != [0, 1, 2, 3, 4, 5]:
        raise PaperScaleConfigError("paper-exact Fig. 3 sectors must be [0,1,2,3,4,5]")

    _required_positive_int(execution, "spectrum_shards")
    _required_positive_int(execution, "analytic_shards")
    _required_positive_int(execution, "state_chunk_size")
    _required_positive_int(execution, "checkpoint_every_modes")
    if review.get("paper_error_candidate_emitted") is not False:
        raise PaperScaleConfigError(
            "execution config may not emit paper_error_candidate"
        )
    if review.get("current_figure3_legend_assessment") != "inconclusive":
        raise PaperScaleConfigError(
            "Fig. 3 legend assessment must remain inconclusive before protocol-v2 review"
        )
    profiles = payload.get("profiles", {})
    if not isinstance(profiles, dict) or not isinstance(profiles.get("smoke"), dict):
        raise PaperScaleConfigError("profiles.smoke must be configured")
    return payload


def effective_config(config: Mapping[str, Any], profile: str) -> dict[str, Any]:
    """Return the base config with the named profile overrides applied."""

    if profile not in {"paper", "smoke"}:
        raise PaperScaleConfigError("profile must be 'paper' or 'smoke'")
    result = deepcopy(dict(config))
    if profile == "smoke":
        overrides = result["profiles"]["smoke"]
        for section in ("scientific_parameters", "execution"):
            if section in overrides:
                if not isinstance(overrides[section], dict):
                    raise PaperScaleConfigError(
                        f"profiles.smoke.{section} must be an object"
                    )
                result[section].update(overrides[section])
    result["active_profile"] = profile
    return result


def config_fingerprint(config: Mapping[str, Any]) -> str:
    """Bind checkpoints to effective settings and numerical implementation code."""

    module_path = Path(__file__).resolve()
    model_path = module_path.with_name("model.py")
    selected = {
        "paper_id": config["paper_id"],
        "active_profile": config["active_profile"],
        "scientific_parameters": config["scientific_parameters"],
        "execution": config["execution"],
        "implementation_sha256": {
            "paper_scale.py": _sha256_file(module_path),
            "model.py": _sha256_file(model_path),
        },
    }
    return _canonical_hash(selected)


def _metadata_scalar(archive: Mapping[str, np.ndarray], key: str) -> str:
    value = np.asarray(archive[key])
    return str(value.item())


def _assert_checkpoint_identity(
    archive: Mapping[str, np.ndarray],
    *,
    expected_config_hash: str,
    expected_eigen_hash: str | None = None,
) -> None:
    if int(np.asarray(archive["schema_version"]).item()) != CHECKPOINT_SCHEMA_VERSION:
        raise RuntimeError("checkpoint schema mismatch")
    if _metadata_scalar(archive, "config_hash") != expected_config_hash:
        raise RuntimeError("checkpoint belongs to a different effective configuration")
    if (
        expected_eigen_hash is not None
        and _metadata_scalar(archive, "eigenvalues_hash") != expected_eigen_hash
    ):
        raise RuntimeError(
            "checkpoint belongs to a different correlation eigenspectrum"
        )


def prepare_eigenvalues(
    config: Mapping[str, Any], output_root: Path, *, resume: bool
) -> tuple[np.ndarray, dict[str, Any]]:
    """Compute the shared correlation eigenspectrum once and checkpoint it."""

    scientific = config["scientific_parameters"]
    length = int(scientific["subsystem_length"])
    active_modes = int(scientific["active_correlation_modes"])
    config_hash = config_fingerprint(config)
    checkpoint = output_root / "checkpoints" / "correlation_eigenvalues.npz"
    if resume and checkpoint.exists():
        with np.load(checkpoint, allow_pickle=False) as archive:
            _assert_checkpoint_identity(archive, expected_config_hash=config_hash)
            eigenvalues = np.asarray(archive["eigenvalues"], dtype=np.float64)
            elapsed = float(np.asarray(archive["elapsed_seconds"]).item())
        if eigenvalues.shape != (active_modes,):
            raise RuntimeError("cached eigenspectrum has the wrong mode count")
        return eigenvalues, {
            "status": "resumed",
            "elapsed_seconds": elapsed,
            "path": _portable_path(checkpoint),
        }

    started = time.perf_counter()
    eigenvalues = correlation_eigenvalues(length, active_modes)
    elapsed = time.perf_counter() - started
    _atomic_npz(
        checkpoint,
        schema_version=np.int64(CHECKPOINT_SCHEMA_VERSION),
        config_hash=np.array(config_hash),
        eigenvalues=eigenvalues,
        elapsed_seconds=np.float64(elapsed),
    )
    return eigenvalues, {
        "status": "computed",
        "elapsed_seconds": elapsed,
        "path": _portable_path(checkpoint),
    }


def _resolved_recurrence_step(
    distribution: np.ndarray, entropy: np.ndarray, probability: float
) -> tuple[np.ndarray, np.ndarray]:
    empty = 1.0 - probability
    new_distribution = np.zeros(distribution.size + 1, dtype=np.float64)
    new_entropy = np.zeros(entropy.size + 1, dtype=np.float64)
    new_distribution[:-1] += empty * distribution
    new_distribution[1:] += probability * distribution
    new_entropy[:-1] += empty * entropy
    new_entropy[1:] += probability * entropy
    if empty > 0.0:
        new_entropy[:-1] -= empty * np.log(empty) * distribution
    if probability > 0.0:
        new_entropy[1:] -= probability * np.log(probability) * distribution
    return new_distribution, new_entropy


def checkpointed_resolved_thermodynamics(
    eigenvalues: np.ndarray,
    *,
    subsystem_length: int,
    checkpoint: Path,
    config_hash: str,
    checkpoint_every: int,
    resume: bool,
    stop_after_modes: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Run the exact charge recurrence with atomic mode-level checkpoints."""

    probabilities = np.asarray(eigenvalues, dtype=np.float64)
    eigen_hash = _array_hash(probabilities)
    next_mode = 0
    distribution = np.ones(1, dtype=np.float64)
    entropy = np.zeros(1, dtype=np.float64)
    if resume and checkpoint.exists():
        with np.load(checkpoint, allow_pickle=False) as archive:
            _assert_checkpoint_identity(
                archive,
                expected_config_hash=config_hash,
                expected_eigen_hash=eigen_hash,
            )
            next_mode = int(np.asarray(archive["next_mode"]).item())
            distribution = np.asarray(archive["distribution"], dtype=np.float64)
            entropy = np.asarray(archive["entropy"], dtype=np.float64)
        if distribution.size != next_mode + 1 or entropy.size != next_mode + 1:
            raise RuntimeError(
                "Fig. 2 recurrence checkpoint is internally inconsistent"
            )

    limit = (
        probabilities.size
        if stop_after_modes is None
        else min(probabilities.size, stop_after_modes)
    )
    for mode in range(next_mode, limit):
        distribution, entropy = _resolved_recurrence_step(
            distribution, entropy, float(probabilities[mode])
        )
        next_mode = mode + 1
        if next_mode % checkpoint_every == 0 or next_mode == limit:
            _atomic_npz(
                checkpoint,
                schema_version=np.int64(CHECKPOINT_SCHEMA_VERSION),
                config_hash=np.array(config_hash),
                eigenvalues_hash=np.array(eigen_hash),
                next_mode=np.int64(next_mode),
                distribution=distribution,
                entropy=entropy,
            )
    complete = next_mode == probabilities.size
    deterministic_particles = subsystem_length // 2 - int(
        np.count_nonzero(probabilities > 0.5)
    )
    particle_numbers = deterministic_particles + np.arange(
        distribution.size, dtype=np.int64
    )
    return particle_numbers, distribution, entropy, complete


def run_fig2(
    config: Mapping[str, Any],
    output_root: Path,
    eigenvalues: np.ndarray,
    *,
    resume: bool,
    stop_after_modes: int | None = None,
) -> dict[str, Any]:
    """Generate T001 data, preserving a resumable recurrence checkpoint."""

    scientific = config["scientific_parameters"]
    execution = config["execution"]
    config_hash = config_fingerprint(config)
    checkpoint = output_root / "checkpoints" / "fig2_recurrence.npz"
    particle_numbers, probability, entropy, complete = (
        checkpointed_resolved_thermodynamics(
            eigenvalues,
            subsystem_length=int(scientific["subsystem_length"]),
            checkpoint=checkpoint,
            config_hash=config_hash,
            checkpoint_every=int(execution["checkpoint_every_modes"]),
            resume=resume,
            stop_after_modes=stop_after_modes,
        )
    )
    if not complete:
        return {
            "status": "checkpointed",
            "completed_modes": int(probability.size - 1),
            "total_modes": int(eigenvalues.size),
            "checkpoint": _portable_path(checkpoint),
        }

    length = int(scientific["subsystem_length"])
    delta_values = np.arange(
        int(scientific["fig2_delta_min"]),
        int(scientific["fig2_delta_max"]) + 1,
        dtype=np.int64,
    )
    wanted_particles = length // 2 + delta_values
    index = {int(number): offset for offset, number in enumerate(particle_numbers)}
    numeric_probability = np.asarray(
        [probability[index[int(number)]] for number in wanted_particles]
    )
    numeric_entropy = np.asarray(
        [entropy[index[int(number)]] for number in wanted_particles]
    )
    analytic_probability, analytic_entropy, constants = analytic_charge_curves(
        delta_values, length
    )

    data_path = output_root / "data" / "fig2_charge_resolved.csv"
    rows = [
        {
            "delta_n": int(delta),
            "particle_number": int(wanted_particles[offset]),
            "probability_numeric": format(float(numeric_probability[offset]), ".17g"),
            "entropy_numeric": format(float(numeric_entropy[offset]), ".17g"),
            "probability_analytic": format(float(analytic_probability[offset]), ".17g"),
            "entropy_analytic": format(float(analytic_entropy[offset]), ".17g"),
        }
        for offset, delta in enumerate(delta_values)
    ]
    _write_csv(
        data_path,
        [
            "delta_n",
            "particle_number",
            "probability_numeric",
            "entropy_numeric",
            "probability_analytic",
            "entropy_analytic",
        ],
        rows,
    )

    safe = np.clip(eigenvalues, np.finfo(float).tiny, 1.0 - np.finfo(float).eps)
    energies = np.log1p(-safe) - np.log(safe)
    spectrum_path = output_root / "data" / "single_particle_spectrum.csv"
    _write_csv(
        spectrum_path,
        ["mode", "correlation_eigenvalue", "entanglement_energy"],
        (
            {
                "mode": offset,
                "correlation_eigenvalue": format(float(value), ".17g"),
                "entanglement_energy": format(float(energies[offset]), ".17g"),
            }
            for offset, value in enumerate(eigenvalues)
        ),
    )
    mode_entropy = -float(np.sum(safe * np.log(safe) + (1.0 - safe) * np.log1p(-safe)))
    metrics = {
        "status": "completed",
        "target_id": "T001",
        "probability_sum": float(probability.sum()),
        "resolved_entropy_sum": float(entropy.sum()),
        "mode_entropy": mode_entropy,
        "particle_hole_residual": float(
            np.max(np.abs(eigenvalues + eigenvalues[::-1] - 1.0))
        ),
        "lowest_eigenvalue": float(eigenvalues[0]),
        "highest_eigenvalue": float(eigenvalues[-1]),
        "display_probability_symmetry_residual": float(
            np.max(np.abs(numeric_probability - numeric_probability[::-1]))
        ),
        "display_entropy_symmetry_residual": float(
            np.max(np.abs(numeric_entropy - numeric_entropy[::-1]))
        ),
        "analytic_constants": constants,
        "outputs": [_portable_path(data_path), _portable_path(spectrum_path)],
    }
    _atomic_json(output_root / "checks" / "fig2_metrics.json", metrics)
    return metrics


def build_spectrum_inputs(
    eigenvalues: np.ndarray, *, selected_modes: int
) -> SpectrumInputs:
    """Select the caption-declared modes and freeze all inactive occupations."""

    values = np.asarray(eigenvalues, dtype=np.float64)
    safe = np.clip(values, np.finfo(float).tiny, 1.0 - np.finfo(float).eps)
    energies = np.log1p(-safe) - np.log(safe)
    indices = np.argsort(np.abs(energies))[:selected_modes]
    indices = indices[np.argsort(energies[indices])]
    selected_mask = np.zeros(values.size, dtype=bool)
    selected_mask[indices] = True
    fixed = safe[~selected_mask]
    log_fixed = float(np.log(np.maximum(fixed, 1.0 - fixed)).sum())
    selected = safe[indices]
    ground = (selected > 0.5).astype(np.int8)
    central_log_lambda_max = log_fixed + float(
        np.log(np.maximum(selected, 1.0 - selected)).sum()
    )
    return SpectrumInputs(
        selected_probabilities=selected,
        ground_occupancy=ground,
        log_fixed=log_fixed,
        central_log_lambda_max=central_log_lambda_max,
        selected_entanglement_energies=energies[indices],
    )


def shard_bounds(total: int, shard_index: int, num_shards: int) -> tuple[int, int]:
    if num_shards <= 0 or not 0 <= shard_index < num_shards:
        raise ValueError("require 0 <= shard_index < num_shards")
    return (total * shard_index // num_shards, total * (shard_index + 1) // num_shards)


def _top_k_descending(values: np.ndarray, keep: int) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.size > keep:
        array = np.partition(array, array.size - keep)[-keep:]
    return np.sort(array)[::-1]


def _merge_top(existing: np.ndarray, candidates: np.ndarray, keep: int) -> np.ndarray:
    if candidates.size == 0:
        return existing
    if existing.size == 0:
        return _top_k_descending(candidates, keep)
    return _top_k_descending(np.concatenate([existing, candidates]), keep)


def run_spectrum_shard(
    config: Mapping[str, Any],
    output_root: Path,
    eigenvalues: np.ndarray,
    *,
    shard_index: int,
    num_shards: int,
    resume: bool,
    stop_after_chunks: int | None = None,
) -> dict[str, Any]:
    """Stream one exact subset of the many-body occupation state space."""

    scientific = config["scientific_parameters"]
    execution = config["execution"]
    selected_modes = int(scientific["fig3_selected_modes"])
    rank_max = int(scientific["fig3_rank_max"])
    sectors = tuple(int(value) for value in scientific["fig3_sectors"])
    labels = ("all", *(str(value) for value in sectors))
    inputs = build_spectrum_inputs(eigenvalues, selected_modes=selected_modes)
    total_states = 1 << selected_modes
    start, end = shard_bounds(total_states, shard_index, num_shards)
    config_hash = config_fingerprint(config)
    eigen_hash = _array_hash(eigenvalues)
    stem = f"part-{shard_index:04d}-of-{num_shards:04d}"
    checkpoint = output_root / "checkpoints" / "fig3_numeric" / f"{stem}.npz"
    final_path = output_root / "shards" / "fig3_numeric" / f"{stem}.npz"
    if resume and final_path.exists():
        with np.load(final_path, allow_pickle=False) as archive:
            _assert_checkpoint_identity(
                archive,
                expected_config_hash=config_hash,
                expected_eigen_hash=eigen_hash,
            )
            if (
                int(np.asarray(archive["start"]).item()) != start
                or int(np.asarray(archive["end"]).item()) != end
            ):
                raise RuntimeError("completed spectrum shard has incompatible bounds")
        return {
            "status": "resumed_complete",
            "path": _portable_path(final_path),
            "start": start,
            "end": end,
        }

    next_state = start
    top = {label: np.empty(0, dtype=np.float64) for label in labels}
    if resume and checkpoint.exists():
        with np.load(checkpoint, allow_pickle=False) as archive:
            _assert_checkpoint_identity(
                archive,
                expected_config_hash=config_hash,
                expected_eigen_hash=eigen_hash,
            )
            if (
                int(np.asarray(archive["start"]).item()) != start
                or int(np.asarray(archive["end"]).item()) != end
            ):
                raise RuntimeError("spectrum checkpoint has incompatible bounds")
            next_state = int(np.asarray(archive["next_state"]).item())
            top = {
                label: np.asarray(archive[f"top_{label}"], dtype=np.float64)
                for label in labels
            }

    probabilities = inputs.selected_probabilities
    ground = inputs.ground_occupancy
    log_empty = np.log1p(-probabilities)
    log_odds = np.log(probabilities) - log_empty
    chunk_size = int(execution["state_chunk_size"])
    chunks_completed = 0
    for chunk_start in range(next_state, end, chunk_size):
        chunk_end = min(end, chunk_start + chunk_size)
        states = np.arange(chunk_start, chunk_end, dtype=np.uint64)
        log_weights = np.full(
            states.size, inputs.log_fixed + float(log_empty.sum()), dtype=np.float64
        )
        delta_charges = np.full(states.size, -int(ground.sum()), dtype=np.int16)
        for mode in range(selected_modes):
            occupied = ((states >> np.uint64(mode)) & np.uint64(1)).astype(np.int8)
            log_weights += occupied * log_odds[mode]
            delta_charges += occupied
        top["all"] = _merge_top(top["all"], log_weights, rank_max)
        for sector in sectors:
            top[str(sector)] = _merge_top(
                top[str(sector)], log_weights[delta_charges == sector], rank_max
            )
        next_state = chunk_end
        chunks_completed += 1
        checkpoint_payload: dict[str, object] = {
            "schema_version": np.int64(CHECKPOINT_SCHEMA_VERSION),
            "config_hash": np.array(config_hash),
            "eigenvalues_hash": np.array(eigen_hash),
            "shard_index": np.int64(shard_index),
            "num_shards": np.int64(num_shards),
            "start": np.int64(start),
            "end": np.int64(end),
            "next_state": np.int64(next_state),
        }
        checkpoint_payload.update(
            {f"top_{label}": values for label, values in top.items()}
        )
        _atomic_npz(checkpoint, **checkpoint_payload)
        if (
            stop_after_chunks is not None
            and chunks_completed >= stop_after_chunks
            and next_state < end
        ):
            return {
                "status": "checkpointed",
                "path": _portable_path(checkpoint),
                "start": start,
                "end": end,
                "next_state": next_state,
            }

    final_payload: dict[str, object] = {
        "schema_version": np.int64(CHECKPOINT_SCHEMA_VERSION),
        "config_hash": np.array(config_hash),
        "eigenvalues_hash": np.array(eigen_hash),
        "shard_index": np.int64(shard_index),
        "num_shards": np.int64(num_shards),
        "start": np.int64(start),
        "end": np.int64(end),
        "next_state": np.int64(end),
        "central_log_lambda_max": np.float64(inputs.central_log_lambda_max),
        "selected_entanglement_energies": inputs.selected_entanglement_energies,
    }
    final_payload.update({f"top_{label}": values for label, values in top.items()})
    _atomic_npz(final_path, **final_payload)
    checkpoint.unlink(missing_ok=True)
    return {
        "status": "completed",
        "path": _portable_path(final_path),
        "start": start,
        "end": end,
    }


def run_analytic_shard(
    config: Mapping[str, Any],
    output_root: Path,
    *,
    shard_index: int,
    num_shards: int,
    resume: bool,
) -> dict[str, Any]:
    """Evaluate one deterministic shard of the Eq. (11) quadrature grid."""

    scientific = config["scientific_parameters"]
    total_points = int(scientific["fig3_analytic_points"])
    start, end = shard_bounds(total_points, shard_index, num_shards)
    config_hash = config_fingerprint(config)
    stem = f"part-{shard_index:04d}-of-{num_shards:04d}"
    output = output_root / "shards" / "fig3_analytic" / f"{stem}.npz"
    if resume and output.exists():
        with np.load(output, allow_pickle=False) as archive:
            _assert_checkpoint_identity(archive, expected_config_hash=config_hash)
            if (
                int(np.asarray(archive["start"]).item()) != start
                or int(np.asarray(archive["end"]).item()) != end
            ):
                raise RuntimeError("analytic shard has incompatible bounds")
        return {
            "status": "resumed_complete",
            "path": _portable_path(output),
            "start": start,
            "end": end,
        }

    all_x = np.linspace(
        0.0, float(scientific["fig3_x_max"]), total_points, dtype=np.float64
    )
    x = all_x[start:end]
    sectors = tuple(int(value) for value in scientific["fig3_sectors"])
    curves = analytic_integrated_spectrum(
        x,
        sectors,
        quadrature_nodes=int(scientific["quadrature_nodes"]),
        luttinger_k=float(scientific["luttinger_k"]),
    )
    payload: dict[str, object] = {
        "schema_version": np.int64(CHECKPOINT_SCHEMA_VERSION),
        "config_hash": np.array(config_hash),
        "shard_index": np.int64(shard_index),
        "num_shards": np.int64(num_shards),
        "start": np.int64(start),
        "end": np.int64(end),
        "x": x,
    }
    payload.update({f"curve_{label}": values for label, values in curves.items()})
    _atomic_npz(output, **payload)
    return {
        "status": "completed",
        "path": _portable_path(output),
        "start": start,
        "end": end,
    }


def _load_spectrum_shards(
    config: Mapping[str, Any],
    output_root: Path,
    num_shards: int,
    eigenvalues: np.ndarray,
) -> tuple[dict[str, np.ndarray], float, list[dict[str, Any]]]:
    scientific = config["scientific_parameters"]
    sectors = tuple(int(value) for value in scientific["fig3_sectors"])
    labels = ("all", *(str(value) for value in sectors))
    rank_max = int(scientific["fig3_rank_max"])
    config_hash = config_fingerprint(config)
    eigen_hash = _array_hash(eigenvalues)
    total_states = 1 << int(scientific["fig3_selected_modes"])
    merged = {label: np.empty(0, dtype=np.float64) for label in labels}
    manifests: list[dict[str, Any]] = []
    central_values: list[float] = []
    for shard_index in range(num_shards):
        start, end = shard_bounds(total_states, shard_index, num_shards)
        path = (
            output_root
            / "shards"
            / "fig3_numeric"
            / f"part-{shard_index:04d}-of-{num_shards:04d}.npz"
        )
        if not path.exists():
            raise RuntimeError(f"missing spectrum shard {path}")
        with np.load(path, allow_pickle=False) as archive:
            _assert_checkpoint_identity(
                archive,
                expected_config_hash=config_hash,
                expected_eigen_hash=eigen_hash,
            )
            observed = (
                int(np.asarray(archive["start"]).item()),
                int(np.asarray(archive["end"]).item()),
            )
            if observed != (start, end):
                raise RuntimeError(
                    f"spectrum shard {shard_index} has noncanonical bounds {observed}"
                )
            central_values.append(
                float(np.asarray(archive["central_log_lambda_max"]).item())
            )
            for label in labels:
                merged[label] = _merge_top(
                    merged[label],
                    np.asarray(archive[f"top_{label}"], dtype=np.float64),
                    rank_max,
                )
        manifests.append(
            {
                "shard_index": shard_index,
                "start": start,
                "end": end,
                "path": _portable_path(path),
            }
        )
    if not np.allclose(central_values, central_values[0], rtol=0.0, atol=1.0e-14):
        raise RuntimeError("spectrum shards disagree on central lambda_max")
    return merged, central_values[0], manifests


def aggregate_spectrum(
    config: Mapping[str, Any],
    output_root: Path,
    eigenvalues: np.ndarray,
    *,
    num_shards: int,
) -> dict[str, Any]:
    """Merge exact per-shard top-k sets and write the plotted numeric curves."""

    scientific = config["scientific_parameters"]
    merged, central_log_lambda_max, manifests = _load_spectrum_shards(
        config, output_root, num_shards, eigenvalues
    )
    x_max = float(scientific["fig3_x_max"])
    numeric_rows: list[dict[str, object]] = []
    onsets: dict[str, float] = {}
    retained: dict[str, int] = {}
    for label, values in merged.items():
        ranks = np.arange(1, values.size + 1, dtype=np.int64)
        x = 2.0 * np.sqrt(
            np.maximum(0.0, -central_log_lambda_max * (central_log_lambda_max - values))
        )
        keep = x <= x_max
        x = x[keep]
        ranks = ranks[keep]
        retained[label] = int(ranks.size)
        onsets[label] = float(x[0]) if x.size else float("nan")
        numeric_rows.extend(
            {
                "sector": label,
                "x": format(float(x_value), ".17g"),
                "integrated_count": int(rank),
            }
            for x_value, rank in zip(x, ranks)
        )
    output = output_root / "data" / "fig3_spectrum_numeric.csv"
    _write_csv(output, ["sector", "x", "integrated_count"], numeric_rows)
    payload = {
        "status": "completed",
        "target_id": "T002",
        "central_log_lambda_max": central_log_lambda_max,
        "onsets": onsets,
        "retained_rows": retained,
        "state_coverage": {
            "expected_states": 1 << int(scientific["fig3_selected_modes"]),
            "covered_states": sum(item["end"] - item["start"] for item in manifests),
            "shards": manifests,
        },
        "output": _portable_path(output),
    }
    _atomic_json(output_root / "checks" / "fig3_numeric_metrics.json", payload)
    return payload


def aggregate_analytic(
    config: Mapping[str, Any], output_root: Path, *, num_shards: int
) -> dict[str, Any]:
    """Concatenate the canonical x-grid shards and write Eq. (11) curves."""

    scientific = config["scientific_parameters"]
    sectors = tuple(int(value) for value in scientific["fig3_sectors"])
    labels = ("all", *(str(value) for value in sectors))
    total_points = int(scientific["fig3_analytic_points"])
    config_hash = config_fingerprint(config)
    x_parts: list[np.ndarray] = []
    curve_parts = {label: [] for label in labels}
    manifests: list[dict[str, Any]] = []
    for shard_index in range(num_shards):
        start, end = shard_bounds(total_points, shard_index, num_shards)
        path = (
            output_root
            / "shards"
            / "fig3_analytic"
            / f"part-{shard_index:04d}-of-{num_shards:04d}.npz"
        )
        if not path.exists():
            raise RuntimeError(f"missing analytic shard {path}")
        with np.load(path, allow_pickle=False) as archive:
            _assert_checkpoint_identity(archive, expected_config_hash=config_hash)
            observed = (
                int(np.asarray(archive["start"]).item()),
                int(np.asarray(archive["end"]).item()),
            )
            if observed != (start, end):
                raise RuntimeError(
                    f"analytic shard {shard_index} has noncanonical bounds {observed}"
                )
            x_parts.append(np.asarray(archive["x"], dtype=np.float64))
            for label in labels:
                curve_parts[label].append(
                    np.asarray(archive[f"curve_{label}"], dtype=np.float64)
                )
        manifests.append(
            {
                "shard_index": shard_index,
                "start": start,
                "end": end,
                "path": _portable_path(path),
            }
        )

    x = np.concatenate(x_parts)
    curves = {label: np.concatenate(parts) for label, parts in curve_parts.items()}
    expected_x = np.linspace(
        0.0, float(scientific["fig3_x_max"]), total_points, dtype=np.float64
    )
    if not np.array_equal(x, expected_x):
        raise RuntimeError("analytic shards do not reconstruct the canonical x grid")
    rows = [
        {
            "sector": label,
            "x": format(float(x_value), ".17g"),
            "integrated_count": format(float(count), ".17g"),
        }
        for label in labels
        for x_value, count in zip(x, curves[label])
    ]
    output = output_root / "data" / "fig3_spectrum_analytic.csv"
    _write_csv(output, ["sector", "x", "integrated_count"], rows)
    identity_residual = float(np.max(np.abs(curves["all"] - np.i0(x))))
    payload = {
        "status": "completed",
        "target_id": "T002",
        "all_sector_i0_max_abs_residual": identity_residual,
        "grid_points": total_points,
        "shards": manifests,
        "output": _portable_path(output),
    }
    _atomic_json(output_root / "checks" / "fig3_analytic_metrics.json", payload)
    return payload


def _central_window(values: np.ndarray, count: int) -> np.ndarray:
    if count <= 0 or count % 2 or count > values.size:
        raise ValueError(
            "central window must be positive, even, and no larger than the spectrum"
        )
    offset = (values.size - count) // 2
    return values[offset : offset + count]


def _uncheckpointed_recurrence(
    eigenvalues: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    probability = np.ones(1, dtype=np.float64)
    entropy = np.zeros(1, dtype=np.float64)
    for value in eigenvalues:
        probability, entropy = _resolved_recurrence_step(
            probability, entropy, float(value)
        )
    return probability, entropy


def ising_parity_formula(n: float, subsystem_length: int, parity: int) -> float:
    """Evaluate the unplotted critical-Ising parity formula printed in the text."""

    if n <= 0.0 or subsystem_length <= 1 or parity not in (0, 1):
        raise ValueError("require n>0, L>1, and parity in {0,1}")
    total = subsystem_length ** (-(n - 1.0 / n) / 12.0)
    contrast = subsystem_length ** (-1.0 / (4.0 * n))
    return 0.5 * total * (1.0 + ((-1.0) ** parity) * contrast)


def backend_benchmark(config: Mapping[str, Any], output_root: Path) -> dict[str, Any]:
    """Run small independent backend and streaming/monolithic parity checks."""

    profile = config["active_profile"]
    scientific = config["scientific_parameters"]
    length = min(int(scientific["subsystem_length"]), 96)
    if length % 2:
        length -= 1
    active_modes = min(int(scientific["active_correlation_modes"]), length - 2)
    if active_modes % 2:
        active_modes -= 1
    started = time.perf_counter()
    subset = correlation_eigenvalues(length, active_modes)
    subset_seconds = time.perf_counter() - started
    started = time.perf_counter()
    full = np.linalg.eigvalsh(toeplitz(half_filled_toeplitz_column(length)))
    full_seconds = time.perf_counter() - started
    reference = _central_window(full, active_modes)
    backend_residual = float(np.max(np.abs(subset - reference)))

    selected_modes = min(12, active_modes)
    if selected_modes % 2:
        selected_modes -= 1
    sectors = tuple(value for value in (0, 1, 2, 3) if value <= selected_modes // 2)
    rank_max = min(128, int(scientific["fig3_rank_max"]))
    monolithic = enumerate_many_body_spectrum(
        subset,
        selected_modes=selected_modes,
        sectors=sectors,
        rank_max=rank_max,
        x_max=100.0,
    )
    inputs = build_spectrum_inputs(subset, selected_modes=selected_modes)
    total = 1 << selected_modes
    labels = ("all", *(str(value) for value in sectors))
    merged = {label: np.empty(0, dtype=np.float64) for label in labels}
    for shard_index in range(3):
        start, end = shard_bounds(total, shard_index, 3)
        states = np.arange(start, end, dtype=np.uint64)
        probabilities = inputs.selected_probabilities
        ground = inputs.ground_occupancy
        log_empty = np.log1p(-probabilities)
        log_weights = np.full(
            states.size, inputs.log_fixed + float(log_empty.sum()), dtype=np.float64
        )
        charges = np.full(states.size, -int(ground.sum()), dtype=np.int16)
        for mode in range(selected_modes):
            occupied = ((states >> np.uint64(mode)) & np.uint64(1)).astype(np.int8)
            log_weights += occupied * (np.log(probabilities[mode]) - log_empty[mode])
            charges += occupied
        merged["all"] = _merge_top(merged["all"], log_weights, rank_max)
        for sector in sectors:
            merged[str(sector)] = _merge_top(
                merged[str(sector)], log_weights[charges == sector], rank_max
            )
    stream_residuals: dict[str, float] = {}
    for label in labels:
        values = merged[label]
        stream_x = 2.0 * np.sqrt(
            np.maximum(
                0.0,
                -inputs.central_log_lambda_max
                * (inputs.central_log_lambda_max - values),
            )
        )
        reference_x = monolithic.curves[label][0]
        stream_residuals[label] = float(np.max(np.abs(stream_x - reference_x)))

    n = 2.0
    lengths = (32, 128)
    contrasts = []
    normalization_residuals = []
    for lattice_length in lengths:
        even = ising_parity_formula(n, lattice_length, 0)
        odd = ising_parity_formula(n, lattice_length, 1)
        total_moment = lattice_length ** (-(n - 1.0 / n) / 12.0)
        contrasts.append((even - odd) / (even + odd))
        normalization_residuals.append(abs(even + odd - total_moment))
    expected_ratio = (lengths[1] / lengths[0]) ** (-1.0 / (4.0 * n))
    observed_ratio = contrasts[1] / contrasts[0]

    payload = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": profile,
        "status": "passed",
        "backend_parity": {
            "scipy_subset_seconds": subset_seconds,
            "numpy_full_seconds": full_seconds,
            "max_abs_eigenvalue_residual": backend_residual,
            "tolerance": 1.0e-11,
            "passed": backend_residual < 1.0e-11,
        },
        "streaming_parity": {
            "selected_modes": selected_modes,
            "num_shards": 3,
            "max_abs_x_residual_by_sector": stream_residuals,
            "tolerance": 1.0e-12,
            "passed": max(stream_residuals.values()) < 1.0e-12,
        },
        "unplotted_ising_claim_formula_sanity": {
            "scope": "formula-level only; author numerical setup is undisclosed",
            "normalization_max_abs_residual": max(normalization_residuals),
            "contrast_scaling_ratio_observed": observed_ratio,
            "contrast_scaling_ratio_expected": expected_ratio,
            "passed": max(normalization_residuals) < 1.0e-14
            and abs(observed_ratio - expected_ratio) < 1.0e-14,
        },
    }
    payload["status"] = (
        "passed"
        if all(
            payload[key]["passed"]
            for key in (
                "backend_parity",
                "streaming_parity",
                "unplotted_ising_claim_formula_sanity",
            )
        )
        else "failed"
    )
    _atomic_json(output_root / "checks" / "backend_benchmark.json", payload)
    if payload["status"] != "passed":
        raise RuntimeError("backend/parity benchmark failed")
    return payload


def acceptance_report(
    config: Mapping[str, Any],
    output_root: Path,
    eigenvalues: np.ndarray,
    *,
    spectrum_shards: int,
) -> dict[str, Any]:
    """Evaluate per-target machine acceptance without consulting paper pixels."""

    fig2 = json.loads(
        (output_root / "checks" / "fig2_metrics.json").read_text(encoding="utf-8")
    )
    fig3_numeric = json.loads(
        (output_root / "checks" / "fig3_numeric_metrics.json").read_text(
            encoding="utf-8"
        )
    )
    fig3_analytic = json.loads(
        (output_root / "checks" / "fig3_analytic_metrics.json").read_text(
            encoding="utf-8"
        )
    )
    benchmark = json.loads(
        (output_root / "checks" / "backend_benchmark.json").read_text(encoding="utf-8")
    )
    scientific = config["scientific_parameters"]
    profile = config["active_profile"]

    smaller_count = min(
        int(scientific["active_correlation_modes"]) - 8, eigenvalues.size
    )
    if smaller_count % 2:
        smaller_count -= 1
    smaller = _central_window(eigenvalues, smaller_count)
    base_probability, base_entropy = _uncheckpointed_recurrence(eigenvalues)
    small_probability, small_entropy = _uncheckpointed_recurrence(smaller)
    offset = (base_probability.size - small_probability.size) // 2
    probability_convergence = float(
        np.max(
            np.abs(
                base_probability[offset : offset + small_probability.size]
                - small_probability
            )
        )
    )
    entropy_convergence = float(
        np.max(
            np.abs(base_entropy[offset : offset + small_entropy.size] - small_entropy)
        )
    )

    probe_x = np.linspace(0.0, float(scientific["fig3_x_max"]), 41)
    sectors = tuple(int(value) for value in scientific["fig3_sectors"])
    main_nodes = int(scientific["quadrature_nodes"])
    coarse_nodes = max(32, main_nodes // 2)
    main_curves = analytic_integrated_spectrum(
        probe_x, sectors, quadrature_nodes=main_nodes
    )
    coarse_curves = analytic_integrated_spectrum(
        probe_x, sectors, quadrature_nodes=coarse_nodes
    )
    quadrature_convergence = max(
        float(np.max(np.abs(main_curves[label] - coarse_curves[label])))
        for label in main_curves
    )

    is_paper = profile == "paper"
    t001_checks = {
        "parameter_profile_valid": (profile == "smoke")
        or (
            int(scientific["subsystem_length"]) == 10000
            and int(scientific["active_correlation_modes"]) == 96
        ),
        "correlation_window_saturated": (not is_paper)
        or (
            fig2["lowest_eigenvalue"] < 1.0e-13
            and fig2["highest_eigenvalue"] > 1.0 - 1.0e-13
        ),
        "probability_normalized": abs(fig2["probability_sum"] - 1.0) < 1.0e-12,
        "entropy_sum_preserved": abs(
            fig2["resolved_entropy_sum"] - fig2["mode_entropy"]
        )
        < 1.0e-11,
        "particle_hole_symmetry": fig2["particle_hole_residual"]
        < (5.0e-11 if is_paper else 1.0e-9),
        "active_window_convergence": (not is_paper)
        or (probability_convergence < 5.0e-12 and entropy_convergence < 5.0e-11),
        "independent_backend_parity": benchmark["backend_parity"]["passed"],
    }
    expected_states = 1 << int(scientific["fig3_selected_modes"])
    sector_onsets = [
        fig3_numeric["onsets"][str(value)] for value in scientific["fig3_sectors"]
    ]
    t002_checks = {
        "parameter_profile_valid": (profile == "smoke")
        or (
            int(scientific["fig3_selected_modes"]) == 24
            and int(scientific["fig3_rank_max"]) == 1000
            and scientific["fig3_sectors"] == [0, 1, 2, 3, 4, 5]
        ),
        "complete_nonoverlapping_state_coverage": fig3_numeric["state_coverage"][
            "covered_states"
        ]
        == expected_states
        and len(fig3_numeric["state_coverage"]["shards"]) == spectrum_shards,
        "sector_onsets_monotone": sector_onsets == sorted(sector_onsets),
        "all_sector_i0_identity": fig3_analytic["all_sector_i0_max_abs_residual"]
        < 2.0e-12,
        "quadrature_convergence": quadrature_convergence < 2.0e-9,
        "streaming_monolithic_parity": benchmark["streaming_parity"]["passed"],
    }
    report = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": profile,
        "artifact_stage": "final_reproduction_candidate" if is_paper else "exploratory",
        "paper_parameters_executed": is_paper,
        "status": (
            "passed"
            if all(t001_checks.values()) and all(t002_checks.values())
            else "failed"
        ),
        "targets": {
            "T001": {
                "status": "passed" if all(t001_checks.values()) else "failed",
                "checks": t001_checks,
                "metrics": {
                    "probability_window_convergence_max_abs": probability_convergence,
                    "entropy_window_convergence_max_abs": entropy_convergence,
                },
            },
            "T002": {
                "status": "passed" if all(t002_checks.values()) else "failed",
                "checks": t002_checks,
                "metrics": {"quadrature_convergence_max_abs": quadrature_convergence},
            },
        },
        "review_protocol": {
            "paper_error_candidate_emitted": False,
            "figure3_legend_assessment": "inconclusive",
            "missing_before_candidate": config["review_protocol"][
                "missing_before_paper_error_candidate"
            ],
        },
    }
    _atomic_json(output_root / "checks" / "acceptance.json", report)
    if report["status"] != "passed":
        raise RuntimeError("paper-scale acceptance checks failed")
    return report


def artifact_manifest(config: Mapping[str, Any], output_root: Path) -> dict[str, Any]:
    """Freeze output hashes and the source-access boundary for this execution."""

    paths = [
        output_root / "data" / "fig2_charge_resolved.csv",
        output_root / "data" / "single_particle_spectrum.csv",
        output_root / "data" / "fig3_spectrum_numeric.csv",
        output_root / "data" / "fig3_spectrum_analytic.csv",
        output_root / "checks" / "fig2_metrics.json",
        output_root / "checks" / "fig3_numeric_metrics.json",
        output_root / "checks" / "fig3_analytic_metrics.json",
        output_root / "checks" / "backend_benchmark.json",
        output_root / "checks" / "acceptance.json",
    ]
    missing = [_portable_path(path) for path in paths if not path.exists()]
    if missing:
        raise RuntimeError(f"cannot manifest missing outputs: {missing}")
    payload = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": config["active_profile"],
        "status": "passed",
        "config_hash": config_fingerprint(config),
        "implementation_sha256": {
            "paper_scale.py": _sha256_file(Path(__file__).resolve()),
            "model.py": _sha256_file(Path(__file__).resolve().with_name("model.py")),
        },
        "generated_data_provenance": "independent_formula_numerics",
        "source_pixels_read": False,
        "paper_pdf_read": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "artifacts": [
            {
                "path": _portable_path(path),
                "sha256": _sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in paths
        ],
    }
    _atomic_json(output_root / "checks" / "manifest.json", payload)
    return payload


def run_all(
    config: Mapping[str, Any], output_root: Path, *, resume: bool
) -> dict[str, Any]:
    """Execute the complete configured profile, then aggregate and accept it."""

    output_root.mkdir(parents=True, exist_ok=True)
    eigenvalues, eigen_stage = prepare_eigenvalues(config, output_root, resume=resume)
    fig2 = run_fig2(config, output_root, eigenvalues, resume=resume)
    spectrum_shards = int(config["execution"]["spectrum_shards"])
    analytic_shards = int(config["execution"]["analytic_shards"])
    spectrum_results = [
        run_spectrum_shard(
            config,
            output_root,
            eigenvalues,
            shard_index=shard_index,
            num_shards=spectrum_shards,
            resume=resume,
        )
        for shard_index in range(spectrum_shards)
    ]
    analytic_results = [
        run_analytic_shard(
            config,
            output_root,
            shard_index=shard_index,
            num_shards=analytic_shards,
            resume=resume,
        )
        for shard_index in range(analytic_shards)
    ]
    fig3_numeric = aggregate_spectrum(
        config, output_root, eigenvalues, num_shards=spectrum_shards
    )
    fig3_analytic = aggregate_analytic(config, output_root, num_shards=analytic_shards)
    benchmark = backend_benchmark(config, output_root)
    acceptance = acceptance_report(
        config, output_root, eigenvalues, spectrum_shards=spectrum_shards
    )
    artifact_manifest(config, output_root)
    summary = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": config["active_profile"],
        "status": "passed",
        "eigen_stage": eigen_stage,
        "fig2": fig2,
        "spectrum_shards": spectrum_results,
        "analytic_shards": analytic_results,
        "fig3_numeric": fig3_numeric,
        "fig3_analytic": fig3_analytic,
        "backend_benchmark": benchmark,
        "acceptance": acceptance,
        "manifest": _portable_path(output_root / "checks" / "manifest.json"),
        "manifest_sha256": _sha256_file(output_root / "checks" / "manifest.json"),
    }
    _atomic_json(output_root / "run_summary.json", summary)
    return summary
