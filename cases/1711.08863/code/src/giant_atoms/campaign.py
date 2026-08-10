"""Checkpointed paper-scale campaign for Main Figure 2.

The public interface is deliberately small: load one machine-readable config
and run (or resume) the campaign.  Shard layout, checkpoint validation,
aggregation, independent formula cross-checks, and scientific acceptance stay
inside this module so the CLI and tests exercise the same implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    Coefficients,
    SETUPS,
    coefficients_from_ordering,
    table_coefficients,
)
from .reproduction import scientific_checks, write_dataset


COEFFICIENT_FIELDS = tuple(Coefficients.__dataclass_fields__)


class CampaignError(RuntimeError):
    """Raised when a campaign contract or checkpoint is unsafe to use."""


@dataclass(frozen=True)
class CampaignConfig:
    """Validated campaign contract used by the runner and tests."""

    path: Path
    sha256: str
    run_id: str
    target_ids: tuple[str, ...]
    gamma: float
    phi_min: float
    phi_max: float
    phi_points: int
    shard_count: int
    resume: bool
    max_abs_residual: float
    special_point_tolerance: float
    refinement_factor: int
    checkpoint_dir: str
    dataset_path: str
    acceptance_path: str
    manifest_path: str
    state_path: str

    @property
    def parameters(self) -> dict[str, float | int]:
        return {
            "gamma": self.gamma,
            "phi_min": self.phi_min,
            "phi_max": self.phi_max,
            "phi_points": self.phi_points,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise CampaignError(f"config field {key!r} must be an object")
    return value


def _require_output_path(outputs: dict[str, Any], key: str) -> str:
    value = outputs.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CampaignError(f"outputs.{key} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "outputs":
        raise CampaignError(f"outputs.{key} must be workspace-relative under outputs/")
    return value


def load_campaign_config(path: Path) -> CampaignConfig:
    """Load and validate the complete paper-scale campaign contract."""

    resolved = path.resolve()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CampaignError(f"campaign config does not exist: {resolved}") from exc
    except json.JSONDecodeError as exc:
        raise CampaignError(f"campaign config is not valid JSON: {resolved}") from exc
    if not isinstance(payload, dict):
        raise CampaignError("campaign config must be a JSON object")
    if payload.get("schema_version") != 1:
        raise CampaignError("campaign config schema_version must be 1")

    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise CampaignError("run_id must be a non-empty string")
    target_ids = payload.get("target_ids")
    if not isinstance(target_ids, list) or not target_ids or not all(
        isinstance(item, str) and item for item in target_ids
    ):
        raise CampaignError("target_ids must be a non-empty string list")
    if "T001" not in target_ids:
        raise CampaignError("paper-scale campaign must include target T001")

    parameters = _require_object(payload, "parameters")
    try:
        gamma = float(parameters["gamma"])
        phi_min = float(parameters["phi_min"])
        phi_max = float(parameters["phi_max"])
        phi_points = int(parameters["phi_points"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CampaignError(
            "parameters must define numeric gamma, phi_min, phi_max, and integer phi_points"
        ) from exc
    if not np.isfinite(gamma) or gamma <= 0.0:
        raise CampaignError("parameters.gamma must be finite and positive")
    if not np.isfinite(phi_min) or not np.isfinite(phi_max) or phi_max <= phi_min:
        raise CampaignError("parameters must satisfy finite phi_min < phi_max")
    if phi_points < 3 or phi_points % 2 == 0:
        raise CampaignError("parameters.phi_points must be an odd integer >= 3")

    campaign = _require_object(payload, "campaign")
    try:
        shard_count = int(campaign["shard_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CampaignError("campaign.shard_count must be an integer") from exc
    if shard_count < 1 or shard_count > phi_points:
        raise CampaignError("campaign.shard_count must be between 1 and phi_points")
    resume = campaign.get("resume")
    if not isinstance(resume, bool):
        raise CampaignError("campaign.resume must be boolean")

    validation = _require_object(payload, "validation")
    try:
        max_abs_residual = float(validation["max_abs_residual"])
        special_point_tolerance = float(validation["special_point_tolerance"])
        refinement_factor = int(validation["refinement_factor"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CampaignError(
            "validation must define max_abs_residual, special_point_tolerance, and refinement_factor"
        ) from exc
    if max_abs_residual <= 0.0 or special_point_tolerance <= 0.0:
        raise CampaignError("validation tolerances must be positive")
    if refinement_factor < 2:
        raise CampaignError("validation.refinement_factor must be >= 2")

    outputs = _require_object(payload, "outputs")
    return CampaignConfig(
        path=resolved,
        sha256=_sha256(resolved),
        run_id=run_id,
        target_ids=tuple(target_ids),
        gamma=gamma,
        phi_min=phi_min,
        phi_max=phi_max,
        phi_points=phi_points,
        shard_count=shard_count,
        resume=resume,
        max_abs_residual=max_abs_residual,
        special_point_tolerance=special_point_tolerance,
        refinement_factor=refinement_factor,
        checkpoint_dir=_require_output_path(outputs, "checkpoint_dir"),
        dataset_path=_require_output_path(outputs, "dataset"),
        acceptance_path=_require_output_path(outputs, "acceptance"),
        manifest_path=_require_output_path(outputs, "manifest"),
        state_path=_require_output_path(outputs, "state"),
    )


def _workspace_path(workspace_root: Path, relative: str) -> Path:
    root = workspace_root.resolve()
    resolved = (root / relative).resolve()
    if root not in resolved.parents:
        raise CampaignError(f"output escapes workspace: {relative}")
    return resolved


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _shard_bounds(config: CampaignConfig, shard_index: int) -> tuple[int, int]:
    quotient, remainder = divmod(config.phi_points, config.shard_count)
    start = shard_index * quotient + min(shard_index, remainder)
    stop = start + quotient + (1 if shard_index < remainder else 0)
    return start, stop


def _checkpoint_path(config: CampaignConfig, workspace_root: Path, shard_index: int) -> Path:
    directory = _workspace_path(workspace_root, config.checkpoint_dir)
    return directory / f"shard_{shard_index:04d}_of_{config.shard_count:04d}.npz"


def _phase_grid(config: CampaignConfig) -> np.ndarray:
    return np.linspace(
        config.phi_min,
        config.phi_max,
        config.phi_points,
        dtype=np.float64,
    )


def _compute_shard(config: CampaignConfig, shard_index: int) -> dict[str, np.ndarray]:
    start, stop = _shard_bounds(config, shard_index)
    phase = _phase_grid(config)[start:stop]
    arrays: dict[str, np.ndarray] = {
        "global_indices": np.arange(start, stop, dtype=np.int64),
        "phi": phase,
    }
    residual = 0.0
    for ordering in SETUPS:
        closed = table_coefficients(ordering, phase, gamma=config.gamma)
        general = coefficients_from_ordering(ordering, phase, gamma=config.gamma)
        for field in COEFFICIENT_FIELDS:
            closed_values = np.asarray(getattr(closed, field), dtype=np.float64)
            general_values = np.asarray(getattr(general, field), dtype=np.float64)
            residual = max(residual, float(np.max(np.abs(closed_values - general_values))))
            arrays[f"{ordering}_{field}"] = closed_values
    arrays["max_crosscheck_residual"] = np.asarray(residual, dtype=np.float64)
    if residual > config.max_abs_residual:
        raise CampaignError(
            f"shard {shard_index} closed-form/general residual {residual:.3e} exceeds "
            f"{config.max_abs_residual:.3e}"
        )
    return arrays


def _write_checkpoint(
    path: Path,
    config: CampaignConfig,
    shard_index: int,
    arrays: dict[str, np.ndarray],
) -> None:
    start, stop = _shard_bounds(config, shard_index)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            schema_version=np.asarray(1, dtype=np.int64),
            config_sha256=np.asarray(config.sha256),
            run_id=np.asarray(config.run_id),
            shard_index=np.asarray(shard_index, dtype=np.int64),
            start_index=np.asarray(start, dtype=np.int64),
            stop_index=np.asarray(stop, dtype=np.int64),
            **arrays,
        )
    temporary.replace(path)


def _load_checkpoint(
    path: Path,
    config: CampaignConfig,
    shard_index: int,
) -> dict[str, np.ndarray]:
    start, stop = _shard_bounds(config, shard_index)
    try:
        with np.load(path, allow_pickle=False) as archive:
            if int(archive["schema_version"].item()) != 1:
                raise CampaignError(f"checkpoint has unsupported schema: {path}")
            if str(archive["config_sha256"].item()) != config.sha256:
                raise CampaignError(
                    f"checkpoint fingerprint differs from the current config: {path}"
                )
            if str(archive["run_id"].item()) != config.run_id:
                raise CampaignError(f"checkpoint run_id differs from config: {path}")
            if int(archive["shard_index"].item()) != shard_index:
                raise CampaignError(f"checkpoint shard index is inconsistent: {path}")
            if int(archive["start_index"].item()) != start or int(
                archive["stop_index"].item()
            ) != stop:
                raise CampaignError(f"checkpoint bounds are inconsistent: {path}")
            keys = ["global_indices", "phi", "max_crosscheck_residual"] + [
                f"{ordering}_{field}"
                for ordering in SETUPS
                for field in COEFFICIENT_FIELDS
            ]
            arrays = {key: np.asarray(archive[key]) for key in keys}
    except (OSError, ValueError, KeyError) as exc:
        raise CampaignError(f"cannot load checkpoint {path}: {exc}") from exc

    expected_indices = np.arange(start, stop, dtype=np.int64)
    expected_phi = _phase_grid(config)[start:stop]
    if not np.array_equal(arrays["global_indices"], expected_indices):
        raise CampaignError(f"checkpoint indices are inconsistent: {path}")
    if not np.array_equal(arrays["phi"], expected_phi):
        raise CampaignError(f"checkpoint phase grid is inconsistent: {path}")
    for ordering in SETUPS:
        for field in COEFFICIENT_FIELDS:
            values = arrays[f"{ordering}_{field}"]
            if values.shape != expected_phi.shape or not np.all(np.isfinite(values)):
                raise CampaignError(f"checkpoint array is invalid: {path}:{ordering}_{field}")
    residual = float(arrays["max_crosscheck_residual"].item())
    if not np.isfinite(residual) or residual > config.max_abs_residual:
        raise CampaignError(f"checkpoint cross-check failed: {path}")
    return arrays


def _aggregate(
    config: CampaignConfig,
    checkpoints: list[dict[str, np.ndarray]],
) -> tuple[np.ndarray, dict[str, Coefficients], float]:
    indices = np.concatenate([row["global_indices"] for row in checkpoints])
    if not np.array_equal(indices, np.arange(config.phi_points, dtype=np.int64)):
        raise CampaignError("checkpoint shards do not cover every phase index exactly once")
    phase = np.concatenate([row["phi"] for row in checkpoints])
    coefficients: dict[str, Coefficients] = {}
    for ordering in SETUPS:
        values = {
            field: np.concatenate([row[f"{ordering}_{field}"] for row in checkpoints])
            for field in COEFFICIENT_FIELDS
        }
        coefficients[ordering] = Coefficients(**values)
    residual = max(float(row["max_crosscheck_residual"].item()) for row in checkpoints)
    return phase, coefficients, residual


def _refinement_residual(
    config: CampaignConfig,
    coarse: dict[str, Coefficients],
) -> tuple[float, float]:
    refined_points = config.refinement_factor * (config.phi_points - 1) + 1
    refined_phase = np.linspace(
        config.phi_min,
        config.phi_max,
        refined_points,
        dtype=np.float64,
    )
    shared_residual = 0.0
    crosscheck_residual = 0.0
    for ordering in SETUPS:
        refined_closed = table_coefficients(ordering, refined_phase, gamma=config.gamma)
        refined_general = coefficients_from_ordering(
            ordering,
            refined_phase,
            gamma=config.gamma,
        )
        for field in COEFFICIENT_FIELDS:
            closed_values = np.asarray(getattr(refined_closed, field), dtype=np.float64)
            general_values = np.asarray(getattr(refined_general, field), dtype=np.float64)
            shared_residual = max(
                shared_residual,
                float(
                    np.max(
                        np.abs(
                            closed_values[:: config.refinement_factor]
                            - np.asarray(getattr(coarse[ordering], field), dtype=np.float64)
                        )
                    )
                ),
            )
            crosscheck_residual = max(
                crosscheck_residual,
                float(np.max(np.abs(closed_values - general_values))),
            )
    return shared_residual, crosscheck_residual


def _acceptance_payload(
    config: CampaignConfig,
    phase: np.ndarray,
    coefficients: dict[str, Coefficients],
    max_crosscheck_residual: float,
) -> dict[str, Any]:
    base = scientific_checks(phase, coefficients, config.gamma)
    shared_residual, refined_crosscheck = _refinement_residual(config, coefficients)
    middle = int(np.argmin(np.abs(phase - np.pi / 2.0)))
    checks: dict[str, dict[str, Any]] = {
        "all_shards_cover_grid_once": {
            "passed": len(phase) == config.phi_points,
            "observed_points": len(phase),
            "expected_points": config.phi_points,
        },
        "paper_phase_interval": {
            "passed": bool(
                abs(float(phase[0]) - config.phi_min) <= config.special_point_tolerance
                and abs(float(phase[-1]) - config.phi_max)
                <= config.special_point_tolerance
            ),
            "observed": [float(phase[0]), float(phase[-1])],
            "expected": [config.phi_min, config.phi_max],
        },
        "grid_contains_decoherence_free_phase": {
            "passed": abs(float(phase[middle]) - np.pi / 2.0)
            <= config.special_point_tolerance,
            "observed_phi": float(phase[middle]),
            "expected_phi": float(np.pi / 2.0),
        },
        "closed_form_vs_general_sum": {
            "passed": max_crosscheck_residual <= config.max_abs_residual,
            "max_abs_residual": max_crosscheck_residual,
            "tolerance": config.max_abs_residual,
        },
        "refined_grid_shared_points_invariant": {
            "passed": shared_residual <= config.max_abs_residual,
            "max_abs_residual": shared_residual,
            "tolerance": config.max_abs_residual,
            "refinement_factor": config.refinement_factor,
        },
        "refined_grid_general_sum_crosscheck": {
            "passed": refined_crosscheck <= config.max_abs_residual,
            "max_abs_residual": refined_crosscheck,
            "tolerance": config.max_abs_residual,
        },
        "paper_claim_invariants": {
            "passed": base["status"] == "passed",
            "details": base["checks"],
        },
    }
    return {
        "schema_version": 1,
        "paper_id": "1711.08863",
        "run_id": config.run_id,
        "target_ids": list(config.target_ids),
        "status": "passed" if all(row["passed"] for row in checks.values()) else "failed",
        "assessment_scope": "reproduction checks only; protocol-v2 paper assessment requires a fresh reviewer",
        "checks": checks,
    }


def _campaign_state(
    config: CampaignConfig,
    completed: list[int],
    computed: list[int],
    resumed: list[int],
    *,
    status: str,
) -> dict[str, Any]:
    completed_set = set(completed)
    return {
        "schema_version": 1,
        "paper_id": "1711.08863",
        "run_id": config.run_id,
        "target_ids": list(config.target_ids),
        "status": status,
        "config_sha256": config.sha256,
        "shard_count": config.shard_count,
        "completed_shards": sorted(completed_set),
        "missing_shards": [
            index for index in range(config.shard_count) if index not in completed_set
        ],
        "computed_this_invocation": computed,
        "resumed_this_invocation": resumed,
        "resume_command": [
            "python",
            "scripts/run_paper_scale_campaign.py",
            "--config",
            "config/paper_scale_campaign.json",
        ],
        "aggregate_command": [
            "python",
            "scripts/run_paper_scale_campaign.py",
            "--config",
            "config/paper_scale_campaign.json",
            "--aggregate-only",
        ],
    }


def _portable_path(path: Path, workspace_root: Path) -> str:
    """Return a workspace-relative path without leaking a host filesystem."""

    try:
        return str(path.resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        return path.name


def run_campaign(
    config_or_path: CampaignConfig | Path,
    workspace_root: Path,
    *,
    shard_index: int | None = None,
    max_new_shards: int | None = None,
    aggregate_only: bool = False,
) -> dict[str, Any]:
    """Run, shard, resume, or aggregate the paper-scale campaign.

    Existing checkpoints are accepted only when their config fingerprint,
    shard bounds, phase grid, arrays, and cross-check residual all validate.
    This prevents an accidental resume across changed scientific parameters.
    """

    config = (
        config_or_path
        if isinstance(config_or_path, CampaignConfig)
        else load_campaign_config(config_or_path)
    )
    root = workspace_root.resolve()
    if shard_index is not None and not 0 <= shard_index < config.shard_count:
        raise CampaignError(
            f"shard_index must be in [0, {config.shard_count - 1}]"
        )
    if max_new_shards is not None and max_new_shards < 1:
        raise CampaignError("max_new_shards must be positive")
    if aggregate_only and (shard_index is not None or max_new_shards is not None):
        raise CampaignError("aggregate_only cannot be combined with shard selection")

    requested = [] if aggregate_only else (
        [shard_index] if shard_index is not None else list(range(config.shard_count))
    )
    computed: list[int] = []
    resumed: list[int] = []
    for index in requested:
        checkpoint = _checkpoint_path(config, root, index)
        if checkpoint.exists():
            if not config.resume:
                raise CampaignError(
                    f"checkpoint exists but campaign.resume is false: {checkpoint}"
                )
            _load_checkpoint(checkpoint, config, index)
            resumed.append(index)
            continue
        if max_new_shards is not None and len(computed) >= max_new_shards:
            break
        arrays = _compute_shard(config, index)
        _write_checkpoint(checkpoint, config, index, arrays)
        computed.append(index)

    completed: list[int] = []
    checkpoint_rows: list[dict[str, np.ndarray]] = []
    for index in range(config.shard_count):
        checkpoint = _checkpoint_path(config, root, index)
        if checkpoint.exists():
            checkpoint_rows.append(_load_checkpoint(checkpoint, config, index))
            completed.append(index)

    state_path = _workspace_path(root, config.state_path)
    if len(completed) != config.shard_count:
        state = _campaign_state(
            config,
            completed,
            computed,
            resumed,
            status="partial",
        )
        _write_json_atomic(state_path, state)
        if aggregate_only:
            raise CampaignError(
                f"cannot aggregate; missing shards: {state['missing_shards']}"
            )
        return state

    phase, coefficients, max_residual = _aggregate(config, checkpoint_rows)
    dataset_path = _workspace_path(root, config.dataset_path)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_dataset = dataset_path.with_name(
        f".{dataset_path.name}.{os.getpid()}.tmp"
    )
    write_dataset(temporary_dataset, phase, coefficients)
    temporary_dataset.replace(dataset_path)

    acceptance = _acceptance_payload(config, phase, coefficients, max_residual)
    acceptance_path = _workspace_path(root, config.acceptance_path)
    _write_json_atomic(acceptance_path, acceptance)

    checkpoint_artifacts = [
        {
            "shard_index": index,
            "path": str(_checkpoint_path(config, root, index).relative_to(root)),
            "sha256": _sha256(_checkpoint_path(config, root, index)),
        }
        for index in range(config.shard_count)
    ]
    manifest = {
        "schema_version": 1,
        "paper_id": "1711.08863",
        "run_id": config.run_id,
        "target_ids": list(config.target_ids),
        "status": acceptance["status"],
        "generated_data_provenance": "independent_numerics",
        "source_pixels_read": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "config": {
            "path": _portable_path(config.path, root),
            "sha256": config.sha256,
        },
        "implementation": {
            "campaign_module": _portable_path(Path(__file__), root),
            "campaign_module_sha256": _sha256(Path(__file__).resolve()),
            "model_module": _portable_path(Path(__file__).with_name("model.py"), root),
            "model_module_sha256": _sha256(Path(__file__).with_name("model.py").resolve()),
        },
        "artifacts": {
            "dataset": {
                "path": config.dataset_path,
                "sha256": _sha256(dataset_path),
            },
            "acceptance": {
                "path": config.acceptance_path,
                "sha256": _sha256(acceptance_path),
            },
            "checkpoints": checkpoint_artifacts,
        },
    }
    manifest_path = _workspace_path(root, config.manifest_path)
    _write_json_atomic(manifest_path, manifest)

    state = _campaign_state(
        config,
        completed,
        computed,
        resumed,
        status=acceptance["status"],
    )
    state["artifacts"] = {
        "dataset": config.dataset_path,
        "acceptance": config.acceptance_path,
        "manifest": config.manifest_path,
    }
    _write_json_atomic(state_path, state)
    if acceptance["status"] != "passed":
        raise CampaignError(f"paper-scale acceptance failed: {acceptance_path}")
    return state
