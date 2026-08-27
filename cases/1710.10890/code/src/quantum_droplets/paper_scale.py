"""Paper-scale campaign orchestration for arXiv:1710.10890.

This module is the reusable case-local boundary between the scientific model
and the machine campaign: it validates one configuration, expands deterministic
tasks, binds checkpoints to task hashes, aggregates structured data, and emits
scientific acceptance/convergence/cross-check evidence. It never reads the
paper, source figures, comparison crops, or author numerical arrays.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

import numpy as np

from .coupled_gpe import lhy_finite_difference_check, run_split_step_scenario
from .model import ScatteringModel, solve_radial_profile, solve_zero_energy_profile
from .reproduction import interaction_and_critical_curves, levitation_curves


@dataclass(frozen=True)
class CampaignTask:
    task_id: str
    campaign_id: str
    profile_id: str
    scenario_id: str
    payload: dict[str, Any]
    task_hash: str


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _atomic_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            np.savez_compressed(handle, **arrays)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _require_keys(value: dict[str, Any], keys: Iterable[str], label: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-like recursive merge without mutating the config."""

    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = json.loads(json.dumps(value))
    return merged


def _validate_profile(profile: dict[str, Any], label: str) -> None:
    _require_keys(
        profile,
        ["backend", "complex_dtype", "grid", "imaginary_time", "real_time"],
        label,
    )
    shape = profile["grid"].get("shape")
    lengths = profile["grid"].get("lengths_micrometre")
    if (
        not isinstance(shape, list)
        or len(shape) != 3
        or min(int(value) for value in shape) < 8
    ):
        raise ValueError(f"{label} grid.shape must have three values >= 8")
    if (
        not isinstance(lengths, list)
        or len(lengths) != 3
        or min(float(value) for value in lengths) <= 0
    ):
        raise ValueError(f"{label} grid lengths must be positive")
    if float(profile["real_time"].get("duration_millisecond", 0.0)) <= 0.0:
        raise ValueError(f"{label} real-time duration must be positive")
    if str(profile["backend"]) not in {"numpy", "cupy"}:
        raise ValueError(f"{label} backend must be numpy or cupy")
    if str(profile["complex_dtype"]) not in {"complex64", "complex128"}:
        raise ValueError(f"{label} complex_dtype must be complex64 or complex128")
    imaginary = profile["imaginary_time"]
    real = profile["real_time"]
    if float(imaginary.get("step_microsecond", 0.0)) <= 0.0:
        raise ValueError(f"{label} imaginary-time step must be positive")
    if int(imaginary.get("maximum_steps", 0)) < 1:
        raise ValueError(f"{label} imaginary-time maximum_steps must be positive")
    if int(imaginary.get("check_every_steps", 0)) < 1:
        raise ValueError(f"{label} imaginary-time check interval must be positive")
    if float(imaginary.get("density_relative_tolerance", 0.0)) <= 0.0:
        raise ValueError(f"{label} imaginary-time tolerance must be positive")
    for key in ("output_every_steps", "checkpoint_every_steps"):
        if int(real.get(key, 0)) < 1:
            raise ValueError(f"{label} real-time {key} must be positive")
    if float(real.get("step_microsecond", 0.0)) <= 0.0:
        raise ValueError(f"{label} real-time step must be positive")


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    _require_keys(
        config,
        ["schema_version", "paper_id", "status", "parameters"],
        "campaign config",
    )
    if int(config["schema_version"]) != 2:
        raise ValueError("paper-scale campaign requires schema_version 2")
    if str(config["paper_id"]) != "1710.10890":
        raise ValueError("paper_id must be 1710.10890")
    parameters = config["parameters"]
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    _require_keys(
        parameters,
        [
            "base_theory_config",
            "contract_parameters",
            "profiles",
            "scenarios",
            "campaigns",
            "radial_crosscheck",
            "crosschecks",
            "acceptance",
            "machine",
            "source_boundary",
        ],
        "parameters",
    )
    profiles = parameters["profiles"]
    scenarios = parameters["scenarios"]
    campaigns = parameters["campaigns"]
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("parameters.profiles must be a non-empty object")
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError("parameters.scenarios must be a non-empty object")
    if not isinstance(campaigns, list) or not campaigns:
        raise ValueError("parameters.campaigns must be a non-empty list")

    required_profiles: set[str] = set()
    seen_campaigns: set[str] = set()
    for row in campaigns:
        _require_keys(
            row,
            ["campaign_id", "profile_id", "scenario_ids", "purpose"],
            "campaign",
        )
        campaign_id = str(row["campaign_id"])
        if campaign_id in seen_campaigns:
            raise ValueError(f"duplicate campaign_id {campaign_id}")
        seen_campaigns.add(campaign_id)
        profile_id = str(row["profile_id"])
        required_profiles.add(profile_id)
        if profile_id not in profiles:
            raise ValueError(f"campaign {campaign_id} references unknown profile {profile_id}")
        for scenario_id in row["scenario_ids"]:
            if str(scenario_id) not in scenarios:
                raise ValueError(
                    f"campaign {campaign_id} references unknown scenario {scenario_id}"
                )
    for profile_id in required_profiles:
        profile = profiles[profile_id]
        _validate_profile(profile, f"profile {profile_id}")
    for scenario_id, scenario in scenarios.items():
        _require_keys(
            scenario,
            [
                "target_id",
                "kind",
                "initial_total_atom_number",
                "initial_component",
                "initial_trap_hz",
                "post_transfer_fraction_1",
                "release_potential",
                "interaction",
                "parameter_status",
            ],
            f"scenario {scenario_id}",
        )
        if str(scenario["target_id"]) not in {"T007", "T008"}:
            raise ValueError(f"scenario {scenario_id} target_id must be T007 or T008")
        overrides = scenario.get("profile_overrides", {})
        if not isinstance(overrides, dict):
            raise ValueError(f"scenario {scenario_id} profile_overrides must be an object")
        for profile_id, override in overrides.items():
            if profile_id not in profiles:
                raise ValueError(
                    f"scenario {scenario_id} overrides unknown profile {profile_id}"
                )
            if not isinstance(override, dict):
                raise ValueError(
                    f"scenario {scenario_id} profile override {profile_id} must be an object"
                )
            _validate_profile(
                _deep_merge(profiles[profile_id], override),
                f"scenario {scenario_id} profile {profile_id}",
            )

    boundary = parameters["source_boundary"]
    forbidden = [
        "author_code_used",
        "author_numerical_arrays_used",
        "source_pixels_used_as_numerical_input",
        "raw_directory_is_input",
    ]
    if any(bool(boundary.get(key, True)) for key in forbidden):
        raise ValueError("source_boundary must explicitly keep all forbidden inputs false")
    return config


def load_campaign_config(path: Path) -> dict[str, Any]:
    return validate_config(_read_json(path))


def build_tasks(config: dict[str, Any]) -> list[CampaignTask]:
    validate_config(config)
    parameters = config["parameters"]
    tasks: list[CampaignTask] = []
    for campaign in parameters["campaigns"]:
        campaign_id = str(campaign["campaign_id"])
        profile_id = str(campaign["profile_id"])
        for scenario_id_raw in campaign["scenario_ids"]:
            scenario_id = str(scenario_id_raw)
            scenario = parameters["scenarios"][scenario_id]
            profile = _deep_merge(
                parameters["profiles"][profile_id],
                scenario.get("profile_overrides", {}).get(profile_id, {}),
            )
            payload = {
                "paper_id": config["paper_id"],
                "campaign_id": campaign_id,
                "profile_id": profile_id,
                "profile": profile,
                "scenario_id": scenario_id,
                "scenario": scenario,
                "base_theory_config": parameters["base_theory_config"],
            }
            task_id = f"{campaign_id}__{scenario_id}"
            tasks.append(
                CampaignTask(
                    task_id=task_id,
                    campaign_id=campaign_id,
                    profile_id=profile_id,
                    scenario_id=scenario_id,
                    payload=payload,
                    task_hash=_canonical_hash(payload),
                )
            )
    return tasks


def _memory_estimate_gib(profile: dict[str, Any]) -> float:
    cells = int(np.prod(profile["grid"]["shape"]))
    complex_bytes = 8 if profile["complex_dtype"] == "complex64" else 16
    # Two fields, FFT workspaces, potentials, k^2, densities, and phases.
    return float(cells * (8 * complex_bytes + 8 * 8) / 1024**3)


def prepare_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    tasks = build_tasks(config)
    profiles = config["parameters"]["profiles"]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "prepared",
        "config_hash": _canonical_hash(config),
        "task_count": len(tasks),
        "tasks": [
            {
                "task_id": task.task_id,
                "campaign_id": task.campaign_id,
                "profile_id": task.profile_id,
                "scenario_id": task.scenario_id,
                "task_hash": task.task_hash,
            }
            for task in tasks
        ],
        "profile_memory_estimates_gib": {
            key: _memory_estimate_gib(value) for key, value in profiles.items()
        },
        "source_boundary": config["parameters"]["source_boundary"],
        "machine": config["parameters"]["machine"],
    }
    _atomic_json(
        output_root / "checks" / "paper_scale_campaign_manifest.json", manifest
    )
    return manifest


def _scenario_interactions(
    scenario: dict[str, Any], base_config: dict[str, Any]
) -> dict[str, float]:
    interaction = scenario["interaction"]
    mode = str(interaction["mode"])
    if mode == "scattering_model":
        values = ScatteringModel.from_config(base_config).evaluate(
            float(interaction["magnetic_field_gauss"])
        )
        return {
            "a11_bohr": float(values["a11_bohr"]),
            "a22_bohr": float(values["a22_bohr"]),
            "a12_bohr": float(values["a12_bohr"]),
        }
    if mode == "explicit":
        return {
            "a11_bohr": float(interaction["a11_bohr"]),
            "a22_bohr": float(interaction["a22_bohr"]),
            "a12_bohr": float(interaction["a12_bohr"]),
        }
    raise ValueError(f"unsupported interaction mode {mode!r}")


def _task_result_path(output_root: Path, task: CampaignTask) -> Path:
    return output_root / "data" / "paper_scale_tasks" / f"{task.task_id}.npz"


def _checkpoint_path(output_root: Path, task: CampaignTask) -> Path:
    return output_root / "checks" / "paper_scale_checkpoints" / f"{task.task_id}.npz"


def run_task(
    task: CampaignTask,
    config: dict[str, Any],
    workspace: Path,
    output_root: Path,
    *,
    resume: bool,
    stop_after_real_steps: int | None = None,
) -> dict[str, Any]:
    base_path = workspace / str(config["parameters"]["base_theory_config"])
    base_config = _read_json(base_path)
    interactions = _scenario_interactions(task.payload["scenario"], base_config)
    result = run_split_step_scenario(
        task.payload["scenario"],
        task.payload["profile"],
        interactions,
        _checkpoint_path(output_root, task),
        resume=resume,
        task_hash=task.task_hash,
        stop_after_real_steps=stop_after_real_steps,
    )
    diagnostics = dict(result.pop("diagnostics"))
    if bool(diagnostics["complete"]):
        arrays = {key: value for key, value in result.items() if isinstance(value, np.ndarray)}
        _atomic_npz(
            _task_result_path(output_root, task),
            **arrays,
            task_hash=np.asarray(task.task_hash),
            task_id=np.asarray(task.task_id),
            campaign_id=np.asarray(task.campaign_id),
            profile_id=np.asarray(task.profile_id),
            scenario_id=np.asarray(task.scenario_id),
            target_id=np.asarray(task.payload["scenario"]["target_id"]),
            parameter_status=np.asarray(task.payload["scenario"]["parameter_status"]),
            interactions_json=np.asarray(json.dumps(interactions, sort_keys=True)),
            diagnostics_json=np.asarray(json.dumps(diagnostics, sort_keys=True)),
        )
    return diagnostics


def run_tasks(
    config: dict[str, Any],
    workspace: Path,
    output_root: Path,
    *,
    resume: bool,
    shard_index: int = 0,
    shard_count: int = 1,
    max_tasks: int | None = None,
    stop_after_real_steps: int | None = None,
) -> dict[str, Any]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must satisfy 0 <= index < shard_count")
    prepare_campaign(config, output_root)
    selected = [
        task
        for index, task in enumerate(build_tasks(config))
        if index % shard_count == shard_index
    ]
    if max_tasks is not None:
        selected = selected[: int(max_tasks)]
    completed: list[str] = []
    partial: list[str] = []
    skipped: list[str] = []
    for task in selected:
        result_path = _task_result_path(output_root, task)
        if resume and result_path.exists():
            with np.load(result_path, allow_pickle=False) as saved:
                if str(saved["task_hash"].item()) != task.task_hash:
                    raise RuntimeError(f"stale result hash for {task.task_id}")
            skipped.append(task.task_id)
            continue
        diagnostics = run_task(
            task,
            config,
            workspace,
            output_root,
            resume=resume,
            stop_after_real_steps=stop_after_real_steps,
        )
        (completed if diagnostics["complete"] else partial).append(task.task_id)
    return {
        "selected": [task.task_id for task in selected],
        "completed": completed,
        "partial": partial,
        "skipped": skipped,
    }


def _load_task_result(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as saved:
        result: dict[str, Any] = {key: np.asarray(saved[key]) for key in saved.files}
    result["diagnostics"] = json.loads(str(result.pop("diagnostics_json").item()))
    result["interactions"] = json.loads(str(result.pop("interactions_json").item()))
    for key in [
        "task_hash",
        "task_id",
        "campaign_id",
        "profile_id",
        "scenario_id",
        "target_id",
        "parameter_status",
    ]:
        result[key] = str(result[key].item())
    return result


def _radial_virial(profile: Any) -> dict[str, float | bool]:
    weight = 4.0 * np.pi * profile.radius**2
    kinetic = float(np.trapezoid(weight * 0.5 * profile.derivative**2, profile.radius))
    quartic = float(np.trapezoid(weight * -1.5 * profile.field**4, profile.radius))
    quintic = float(np.trapezoid(weight * profile.field**5, profile.radius))
    residual = 2.0 * kinetic + 3.0 * quartic + 4.5 * quintic
    scale = max(
        abs(2.0 * kinetic) + abs(3.0 * quartic) + abs(4.5 * quintic),
        1e-15,
    )
    relative = abs(residual) / scale
    return {
        "passed": relative < 2e-4,
        "relative_residual": relative,
        "kinetic": kinetic,
        "quartic": quartic,
        "quintic": quintic,
    }


def _radial_checks(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = config["parameters"]["radial_crosscheck"]
    production_options = dict(spec["production"])
    reference_options = dict(spec["reference"])
    metastable_mu = float(spec["metastable_mu"])
    stable_bracket = tuple(float(value) for value in spec["stable_mu_bracket"])
    production_meta = solve_radial_profile(metastable_mu, **production_options)
    production_stable = solve_zero_energy_profile(stable_bracket, **production_options)
    reference_meta = solve_radial_profile(metastable_mu, **reference_options)
    reference_stable = solve_zero_energy_profile(stable_bracket, **reference_options)

    convergence = {
        "metastable_number_relative": abs(
            production_meta.particle_number - reference_meta.particle_number
        )
        / reference_meta.particle_number,
        "metastable_width_relative": abs(
            production_meta.axis_rms - reference_meta.axis_rms
        )
        / reference_meta.axis_rms,
        "stable_number_relative": abs(
            production_stable.particle_number - reference_stable.particle_number
        )
        / reference_stable.particle_number,
        "stable_width_relative": abs(
            production_stable.axis_rms - reference_stable.axis_rms
        )
        / reference_stable.axis_rms,
    }
    tolerance = float(spec["relative_tolerance"])
    numeric_values = [float(value) for value in convergence.values()]
    convergence["passed"] = max(numeric_values) < tolerance
    crosschecks = {
        "metastable_pohozaev": _radial_virial(reference_meta),
        "stable_pohozaev": _radial_virial(reference_stable),
        "branch_order": {
            "metastable_axis_rms": reference_meta.axis_rms,
            "stable_axis_rms": reference_stable.axis_rms,
            "metastable_wider_than_stable": (
                reference_meta.axis_rms > reference_stable.axis_rms
            ),
            "assessment": "inconclusive",
            "reason": (
                "The paper does not define the theory-curve width functional, and "
                "the scattering lane is reconstructed rather than paper-exact."
            ),
        },
    }
    crosschecks["passed"] = bool(
        crosschecks["metastable_pohozaev"]["passed"]
        and crosschecks["stable_pohozaev"]["passed"]
    )
    return convergence, crosschecks


def _curve_gap(left: dict[str, Any], right: dict[str, Any], key: str) -> float:
    common = np.asarray(left["time_millisecond"], dtype=float)
    interpolated = np.interp(
        common,
        np.asarray(right["time_millisecond"], dtype=float),
        np.asarray(right[key], dtype=float),
    )
    denominator = np.maximum(np.abs(interpolated), 1e-12)
    return float(
        np.max(np.abs(np.asarray(left[key], dtype=float) - interpolated) / denominator)
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _static_rows(
    config: dict[str, Any], workspace: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = _read_json(workspace / str(config["parameters"]["base_theory_config"]))
    model = ScatteringModel.from_config(base)
    targets, diagnostics = interaction_and_critical_curves(base, model)
    levitation, levitation_diagnostics = levitation_curves(base)
    rows: list[dict[str, Any]] = []
    for target_id, payload in targets.items():
        independent_key = next(
            (
                key
                for key in payload
                if key in {"magnetic_field_gauss", "z_micrometre"}
            ),
            None,
        )
        if independent_key is None:
            independent_key = next(
                key for key, value in payload.items() if np.asarray(value).ndim == 1
            )
        independent = np.asarray(payload[independent_key])
        for index, x_value in enumerate(independent):
            for key, value in payload.items():
                array = np.asarray(value)
                if (
                    key == independent_key
                    or array.ndim != 1
                    or array.size != independent.size
                ):
                    continue
                rows.append(
                    {
                        "target_id": target_id,
                        "independent_name": independent_key,
                        "independent_value": float(x_value),
                        "observable": key,
                        "value": float(array[index]),
                    }
                )
    z = np.asarray(levitation["z_micrometre"])
    for index, z_value in enumerate(z):
        for key in [
            "potential_microkelvin",
            "gravity_microkelvin",
            "signed_curvature_hz",
        ]:
            rows.append(
                {
                    "target_id": "T006",
                    "independent_name": "z_micrometre",
                    "independent_value": float(z_value),
                    "observable": key,
                    "value": float(np.asarray(levitation[key])[index]),
                }
            )
    return rows, {"radial": diagnostics, "levitation": levitation_diagnostics}


def aggregate_campaign(
    config: dict[str, Any], workspace: Path, output_root: Path
) -> dict[str, Any]:
    tasks = build_tasks(config)
    missing = [
        task.task_id
        for task in tasks
        if not _task_result_path(output_root, task).exists()
    ]
    if missing:
        raise RuntimeError(
            "cannot finalize an incomplete campaign; missing task results: "
            + ", ".join(missing)
        )
    results = {
        task.task_id: _load_task_result(_task_result_path(output_root, task))
        for task in tasks
    }
    static_rows, static_diagnostics = _static_rows(config, workspace)
    data_root = output_root / "data"
    check_root = output_root / "checks"
    figure_root = output_root / "figures"
    _write_csv(
        data_root / "static_equilibrium.csv",
        [
            "target_id",
            "independent_name",
            "independent_value",
            "observable",
            "value",
        ],
        static_rows,
    )

    dynamic_rows: dict[str, list[dict[str, Any]]] = {"T007": [], "T008": []}
    for task in tasks:
        result = results[task.task_id]
        scenario = config["parameters"]["scenarios"][task.scenario_id]
        target_id = str(scenario["target_id"])
        for index, time in enumerate(result["time_millisecond"]):
            dynamic_rows[target_id].append(
                {
                    "campaign_id": task.campaign_id,
                    "profile_id": task.profile_id,
                    "scenario_id": task.scenario_id,
                    "parameter_status": scenario["parameter_status"],
                    "time_millisecond": float(time),
                    "sigma_micrometre": float(result["sigma_micrometre"][index]),
                    "rms_x_micrometre": float(result["rms_x_micrometre"][index]),
                    "rms_z_micrometre": float(result["rms_z_micrometre"][index]),
                    "tf_radius_z_micrometre": float(
                        result["tf_radius_z_micrometre"][index]
                    ),
                    "boundary_mass_fraction": float(
                        result["boundary_mass_fraction"][index]
                    ),
                    "number_1": float(result["number_1"][index]),
                    "number_2": float(result["number_2"][index]),
                    "peak_density_cm3": float(result["peak_density_cm3"][index]),
                }
            )
    dynamic_fields = [
        "campaign_id",
        "profile_id",
        "scenario_id",
        "parameter_status",
        "time_millisecond",
        "sigma_micrometre",
        "rms_x_micrometre",
        "rms_z_micrometre",
        "tf_radius_z_micrometre",
        "boundary_mass_fraction",
        "number_1",
        "number_2",
        "peak_density_cm3",
    ]
    _write_csv(
        data_root / "main_fig4_dynamics.csv",
        dynamic_fields,
        dynamic_rows["T008"],
    )
    _write_csv(
        data_root / "supp_s2_dynamics.csv",
        dynamic_fields,
        dynamic_rows["T007"],
    )

    radial_convergence, radial_crosschecks = _radial_checks(config)
    acceptance_spec = config["parameters"]["acceptance"]
    convergence_rows: dict[str, Any] = {
        "radial": radial_convergence,
        "dynamic": {},
    }
    production_by_scenario = {
        task.scenario_id: results[task.task_id]
        for task in tasks
        if task.campaign_id == "production"
    }
    for campaign_id in ["grid_refinement", "time_refinement"]:
        for task in tasks:
            if task.campaign_id != campaign_id:
                continue
            production = production_by_scenario[task.scenario_id]
            convergence_rows["dynamic"][f"{campaign_id}:{task.scenario_id}"] = {
                "sigma_max_relative_gap": _curve_gap(
                    production, results[task.task_id], "sigma_micrometre"
                )
            }
    dynamic_limit = float(acceptance_spec["dynamic_curve_relative_tolerance"])
    convergence_rows["status"] = (
        "passed"
        if radial_convergence["passed"]
        and all(
            row["sigma_max_relative_gap"] < dynamic_limit
            for row in convergence_rows["dynamic"].values()
        )
        else "failed"
    )

    fig4_results = [
        production_by_scenario[key]
        for key, scenario in config["parameters"]["scenarios"].items()
        if scenario["target_id"] == "T008"
    ]
    s2_results = {
        key: production_by_scenario[key]
        for key, scenario in config["parameters"]["scenarios"].items()
        if scenario["target_id"] == "T007"
    }
    norm_limit = float(acceptance_spec["norm_relative_drift_maximum"])
    boundary_limit = float(acceptance_spec["boundary_mass_fraction_maximum"])
    norm_drifts = {
        task_id: float(result["diagnostics"]["norm_relative_drift"])
        for task_id, result in results.items()
    }
    s2_free = next(result for key, result in s2_results.items() if "free" in key)
    s2_confined = next(
        result for key, result in s2_results.items() if "confined" in key
    )
    acceptance = {
        "status": "passed",
        "checks": {
            "all_values_finite": all(
                np.all(np.isfinite(result["sigma_micrometre"]))
                for result in results.values()
            ),
            "norm_conservation": max(norm_drifts.values()) < norm_limit,
            "imaginary_time_preparation": all(
                bool(result["diagnostics"]["imaginary_time_converged"])
                or not bool(
                    result["diagnostics"]["imaginary_time_convergence_required"]
                )
                for result in results.values()
            ),
            "fft_box_boundary_clear": max(
                float(np.max(result["boundary_mass_fraction"]))
                for result in results.values()
            )
            < boundary_limit,
            "fig4_positive_bounded_size": all(
                np.min(result["sigma_micrometre"]) > 0.0
                and np.max(result["sigma_micrometre"])
                < float(acceptance_spec["maximum_physical_size_micrometre"])
                for result in fig4_results
            ),
            "supp_s2_free_expands_more_than_confined": (
                float(s2_free["tf_radius_z_micrometre"][-1])
                > float(s2_confined["tf_radius_z_micrometre"][-1])
            ),
            "radial_convergence": bool(radial_convergence["passed"]),
        },
        "norm_relative_drifts": norm_drifts,
        "scope": (
            "Numerical validity only; missing atom numbers prevent paper-exact "
            "Fig. 4/S2 agreement claims."
        ),
    }
    if not all(acceptance["checks"].values()):
        acceptance["status"] = "failed"

    first_interactions = next(iter(results.values()))["interactions"]
    lhy_check = lhy_finite_difference_check(
        first_interactions["a11_bohr"],
        first_interactions["a22_bohr"],
        config["parameters"]["crosschecks"]["lhy_density_pairs_m3"],
    )
    crosschecks = {
        "status": (
            "passed"
            if lhy_check["passed"] and radial_crosschecks["passed"]
            else "failed"
        ),
        "lhy_functional_derivative": lhy_check,
        "radial_pohozaev_and_branch": radial_crosschecks,
        "method_independence": [
            "analytic finite-difference derivative of the LHY energy density",
            "Pohozaev scaling identity independent of radial collocation residuals",
            "grid and time-step refinement of the 3D split-step trajectory",
        ],
    }

    assessment = {
        "schema_version": 2,
        "paper_id": config["paper_id"],
        "status": "inconclusive",
        "paper_error_candidate": False,
        "targets": {
            "T005": {
                "assessment": "inconclusive",
                "reason": (
                    "The converged universal profiles retain a branch-order difference, "
                    "but the paper's theory-width functional and paper-exact scattering "
                    "model are not specified; no fresh-context review exists."
                ),
            },
            "T007": {
                "assessment": "inconclusive",
                "reason": (
                    "The single-component GPE method is executable, but the Supplement "
                    "Fig. S2 atom number is unpublished."
                ),
            },
            "T008": {
                "assessment": "inconclusive",
                "reason": (
                    "The coupled-GPE method is executable, but the plotted per-curve "
                    "initial atom numbers are unpublished."
                ),
            },
        },
        "protocol_v2_missing": [
            "paper-exact initial atom numbers for T007 and T008",
            "paper-exact width functional for T005",
            "frozen paper-scale production data",
            "fresh-context inventory-first falsification review",
        ],
        "defect_rule": (
            "A failed solver, invariant, or convergence gate is a "
            "reproduction_defect, never a paper error."
        ),
    }
    if (
        acceptance["status"] == "failed"
        or convergence_rows["status"] == "failed"
        or crosschecks["status"] == "failed"
    ):
        assessment["status"] = "reproduction_defect"

    _atomic_json(check_root / "scientific_acceptance.json", acceptance)
    _atomic_json(check_root / "convergence.json", convergence_rows)
    _atomic_json(check_root / "crosschecks.json", crosschecks)
    _atomic_json(check_root / "paper_review_assessment.json", assessment)

    # Rendering is intentionally imported only on the aggregation path.  The
    # numerical planner/validator can then run in the no-render isolated bundle
    # without probing host fonts or launching font-discovery subprocesses.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure_root.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0), constrained_layout=True)
    for key, result in production_by_scenario.items():
        scenario = config["parameters"]["scenarios"][key]
        axis = axes[0] if scenario["target_id"] == "T008" else axes[1]
        axis.plot(
            result["time_millisecond"],
            (
                result["sigma_micrometre"]
                if scenario["target_id"] == "T008"
                else result["tf_radius_z_micrometre"]
            ),
            label=key,
        )
    axes[0].set(
        title="Main Fig. 4 theory scenarios",
        xlabel="time (ms)",
        ylabel="Gaussian-equivalent sigma (um)",
    )
    axes[1].set(
        title="Supplement Fig. S2 theory scenarios",
        xlabel="time (ms)",
        ylabel="TF-equivalent vertical radius (um)",
    )
    for axis in axes:
        axis.legend(fontsize=7)
        axis.grid(alpha=0.2)
    fig.savefig(figure_root / "theory_campaign.png", dpi=180)
    plt.close(fig)

    manifest = prepare_campaign(config, output_root)
    manifest.update(
        {
            "status": (
                "completed"
                if assessment["status"] != "reproduction_defect"
                else "failed"
            ),
            "scientific_acceptance": acceptance["status"],
            "convergence": convergence_rows["status"],
            "crosschecks": crosschecks["status"],
            "paper_review_assessment": assessment["status"],
            "static_diagnostics": static_diagnostics,
        }
    )
    _atomic_json(
        output_root / "checks" / "paper_scale_campaign_manifest.json", manifest
    )
    return manifest


def make_smoke_config(config: dict[str, Any]) -> dict[str, Any]:
    smoke = json.loads(json.dumps(config))
    profiles = smoke["parameters"]["profiles"]
    for profile in profiles.values():
        profile["backend"] = "numpy"
        profile["complex_dtype"] = "complex128"
        profile["grid"] = {
            "shape": [12, 12, 12],
            "lengths_micrometre": [16.0, 16.0, 16.0],
        }
        profile["imaginary_time"] = {
            "step_microsecond": 0.2,
            "maximum_steps": 4,
            "check_every_steps": 2,
            "density_relative_tolerance": 1.0,
            "require_convergence": False,
        }
        profile["real_time"] = {
            "step_microsecond": 0.2,
            "duration_millisecond": 0.0008,
            "output_every_steps": 1,
            "checkpoint_every_steps": 1,
        }
    for scenario in smoke["parameters"]["scenarios"].values():
        # Production box/time overrides must not leak into a memory-bounded
        # smoke run; every scenario still exercises the same solver path.
        scenario.pop("profile_overrides", None)
    smoke["parameters"]["radial_crosscheck"]["production"] = {
        "radius_max": 16.0,
        "initial_nodes": 300,
        "tolerance": 2e-5,
        "max_nodes": 6000,
    }
    smoke["parameters"]["radial_crosscheck"]["reference"] = {
        "radius_max": 18.0,
        "initial_nodes": 500,
        "tolerance": 5e-6,
        "max_nodes": 10000,
    }
    # The smoke BVPs intentionally use only a few hundred nodes.  This gate
    # checks code-path agreement, while the production contract retains the
    # 2e-4 scientific tolerance on the 1800/3000-node pair.
    smoke["parameters"]["radial_crosscheck"]["relative_tolerance"] = 4e-3
    smoke["parameters"]["acceptance"]["dynamic_curve_relative_tolerance"] = 0.2
    smoke["status"] = "smoke_only"
    return validate_config(smoke)
