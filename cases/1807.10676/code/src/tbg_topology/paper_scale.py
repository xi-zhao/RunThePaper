"""Code-ready paper-scale campaign for all formula-driven theory targets.

The publication does not provide its exact reciprocal cutoff or sampling grids.
This channel therefore freezes a conservative, independently chosen production
resolution and keeps its outputs separate from the already attested feature run.
It never reads paper figures, author code, or author numerical arrays.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .reproduction import TARGET_FILES, run_reproduction

REQUIRED_TARGET_IDS = tuple(TARGET_FILES)
CHECK_FILENAMES = (
    "scientific_formula_checks.json",
    "convergence.json",
    "target_checks.json",
    "generated_data_manifest.json",
)
NUMERIC_MINIMUMS: dict[str, int] = {
    "alpha_scan": 501,
    "gap_alpha_scan": 201,
    "gap_path_points_per_segment": 41,
    "gap_uv_grid": 24,
    "wilson_u_points": 101,
    "wilson_loop_points": 301,
    "continuum_points_per_segment": 81,
    "magic_points_per_segment": 101,
    "tb_points_per_segment": 181,
    "tb_wilson_u_points": 161,
    "tb_wilson_loop_points": 301,
    "gamma_zoom_scan": 301,
    "node_grid_points": 101,
    "node_max_count": 30,
    "ph_breaking_cutoff": 7,
    "ph_points_per_segment": 101,
    "wannier_k_grid": 51,
    "wannier_real_radius": 7,
}


class PaperScaleConfigError(ValueError):
    """The production campaign would not cover the declared scientific scope."""


def canonical_json_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_namespace(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise PaperScaleConfigError("output_namespace must be a non-empty string")
    normalized = value.replace("-", "").replace("_", "")
    if not normalized.isalnum() or Path(value).parts != (value,):
        raise PaperScaleConfigError(
            "output_namespace must be one safe directory name containing only "
            "letters, numbers, '-' or '_'"
        )
    return value


def _scan_count(numerics: dict[str, Any], key: str) -> int:
    value = numerics.get(key)
    if not isinstance(value, list) or len(value) != 3:
        raise PaperScaleConfigError(f"numerics.{key} must be [start, stop, count]")
    count = value[2]
    if isinstance(count, bool) or not isinstance(count, int):
        raise PaperScaleConfigError(f"numerics.{key}[2] must be an integer")
    return count


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("schema_version") != 1:
        raise PaperScaleConfigError("schema_version must be 1")
    if config.get("paper_id") != "1807.10676":
        raise PaperScaleConfigError("paper_id must be 1807.10676")
    if not isinstance(config.get("campaign_id"), str) or not config["campaign_id"]:
        raise PaperScaleConfigError("campaign_id must be a non-empty string")
    if config.get("execution_scale") != "paper_scale_reconstructed":
        raise PaperScaleConfigError("execution_scale must be paper_scale_reconstructed")
    namespace = _safe_namespace(config.get("output_namespace"))
    targets = config.get("target_ids")
    if targets != list(REQUIRED_TARGET_IDS):
        raise PaperScaleConfigError(
            f"target_ids must be exactly {list(REQUIRED_TARGET_IDS)}"
        )
    paper_parameters = config.get("paper_parameters")
    if not isinstance(paper_parameters, dict) or not paper_parameters:
        raise PaperScaleConfigError("paper_parameters must be a non-empty object")
    required_parameters = {
        "interlayer_w_ev",
        "v_f_k_ev",
        "first_magic_alpha",
        "fixed_theta_deg",
        "reported_magic_alphas",
        "gapped_phase_alphas",
        "supplement_band_alphas",
        "magic_generation_alphas",
        "ph_breaking_sets",
        "tb4",
        "tb4_two_valley",
        "intervalley_zeta",
        "paper_parameter_source",
    }
    missing_parameters = sorted(required_parameters - set(paper_parameters))
    if missing_parameters:
        raise PaperScaleConfigError(
            f"paper_parameters is missing required values: {missing_parameters}"
        )
    required_parameter_groups = {
        "tb4": {"t", "t_prime", "lambda", "delta"},
        "tb4_two_valley": {
            "delta_minus",
            "t_minus",
            "t_prime_minus",
            "lambda_1",
            "lambda_2",
        },
    }
    for group, required_keys in required_parameter_groups.items():
        values = paper_parameters.get(group)
        if not isinstance(values, dict) or set(values) != required_keys:
            raise PaperScaleConfigError(
                f"paper_parameters.{group} must contain exactly "
                f"{sorted(required_keys)}"
            )
    numerics = config.get("numerics")
    if not isinstance(numerics, dict):
        raise PaperScaleConfigError("numerics must be an object")
    actual_counts = {
        "alpha_scan": _scan_count(numerics, "alpha_scan"),
        "gap_alpha_scan": _scan_count(numerics, "gap_alpha_scan"),
        "gamma_zoom_scan": _scan_count(numerics, "gamma_zoom_scan"),
    }
    for key, minimum in NUMERIC_MINIMUMS.items():
        raw = actual_counts.get(key, numerics.get(key))
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < minimum:
            raise PaperScaleConfigError(
                f"numerics.{key} must be an integer >= {minimum}; got {raw!r}"
            )
    velocity_step = numerics.get("velocity_step")
    if not isinstance(velocity_step, (int, float)) or not 0 < velocity_step <= 5e-4:
        raise PaperScaleConfigError("numerics.velocity_step must be in (0, 5e-4]")
    source_policy = config.get("source_input_policy")
    forbidden = (
        "source_pixels_allowed",
        "author_code_allowed",
        "author_numerical_arrays_allowed",
        "runtime_raw_access_allowed",
    )
    if not isinstance(source_policy, dict) or any(
        source_policy.get(key) is not False for key in forbidden
    ):
        raise PaperScaleConfigError(
            "source_input_policy must explicitly disable pixels, author code/arrays, "
            "and runtime raw access"
        )
    machine = config.get("machine")
    if not isinstance(machine, dict):
        raise PaperScaleConfigError("machine must be an object")
    if int(machine.get("cpu_cores", 0)) < 1 or int(machine.get("memory_gib", 0)) < 1:
        raise PaperScaleConfigError("machine must declare positive CPU and memory")
    acceptance = config.get("acceptance")
    if (
        not isinstance(acceptance, dict)
        or acceptance.get("require_all_targets") is not True
    ):
        raise PaperScaleConfigError("acceptance.require_all_targets must be true")
    return {
        "schema_version": 1,
        "status": "ready",
        "campaign_id": config.get("campaign_id"),
        "execution_scale": config["execution_scale"],
        "output_namespace": namespace,
        "target_count": len(targets),
        "resolution": {
            key: actual_counts.get(key, numerics[key]) for key in NUMERIC_MINIMUMS
        },
        "production_started": False,
        "paper_exact_claimed": False,
        "paper_exact_blocker": (
            "the paper omits exact reciprocal cutoffs, momentum grids, and author arrays"
        ),
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_arrays_used": False,
        "config_sha256": canonical_json_hash(config),
    }


def expected_output_paths(config: dict[str, Any]) -> list[str]:
    namespace = _safe_namespace(config.get("output_namespace"))
    data = [f"outputs/data/{namespace}/{name}" for name in TARGET_FILES.values()]
    checks = [f"outputs/checks/{namespace}/{name}" for name in CHECK_FILENAMES]
    return [*data, *checks, f"outputs/checks/{namespace}/campaign_state.json"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _resume_state(config: dict[str, Any], workspace: Path) -> dict[str, Any] | None:
    namespace = _safe_namespace(config["output_namespace"])
    state_path = workspace / "outputs" / "checks" / namespace / "campaign_state.json"
    if not state_path.is_file():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if state.get("status") != "paper_scale_complete_reconstructed" or state.get(
        "config_sha256"
    ) != canonical_json_hash(config):
        return None
    hashes = state.get("outputs_sha256")
    if not isinstance(hashes, dict) or not hashes:
        return None
    if set(hashes) != set(expected_output_paths(config)[:-1]):
        return None
    for relative, expected_hash in hashes.items():
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            return None
        path = (workspace / relative).resolve()
        try:
            path.relative_to(workspace.resolve())
        except ValueError:
            return None
        if not path.is_file() or _sha256(path) != expected_hash:
            return None
    return state


def execute_campaign(
    config: dict[str, Any], workspace: Path, *, resume: bool
) -> dict[str, Any]:
    validation = validate_config(config)
    if resume:
        previous = _resume_state(config, workspace)
        if previous is not None:
            return {**previous, "resumed": True}

    result = run_reproduction(config, workspace)
    paths = expected_output_paths(config)[:-1]
    missing = [relative for relative in paths if not (workspace / relative).is_file()]
    if missing:
        raise RuntimeError(f"paper-scale runner did not produce outputs: {missing}")
    output_hashes = {relative: _sha256(workspace / relative) for relative in paths}
    passed = bool(
        result.formula_checks.get("all_passed")
        and result.convergence.get("status") == "passed"
        and result.target_checks.get("all_passed")
    )
    state = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "campaign_id": config["campaign_id"],
        "status": (
            "paper_scale_complete_reconstructed"
            if passed
            else "scientific_checks_failed"
        ),
        "config_sha256": validation["config_sha256"],
        "execution_scale": config["execution_scale"],
        "paper_parameters_executed": True,
        "paper_exact": False,
        "paper_exact_blocker": validation["paper_exact_blocker"],
        "formula_checks_passed": bool(result.formula_checks.get("all_passed")),
        "convergence_status": result.convergence.get("status"),
        "target_checks_passed": bool(result.target_checks.get("all_passed")),
        "elapsed_seconds": result.elapsed_seconds,
        "outputs_sha256": output_hashes,
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_arrays_used": False,
        "resumed": False,
    }
    namespace = _safe_namespace(config["output_namespace"])
    state_path = workspace / "outputs" / "checks" / namespace / "campaign_state.json"
    _atomic_json(state_path, state)
    return state
