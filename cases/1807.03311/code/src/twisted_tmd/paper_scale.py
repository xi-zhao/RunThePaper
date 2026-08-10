"""Restartable paper-scale numerics for the continuum-only sweep panels.

Each condition is either one DOS momentum row or one twist-angle point.  The
workers read only case-authored code and configuration; paper/source figures
are deliberately outside this execution graph.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from .model import MoireGeometry, TwoBandContinuum

TARGET_FILES = {
    "T003": "T003_main_fig3b_dos.npz",
    "T006": "T006_main_fig4b_gaps.npz",
    "T007": "T007_main_fig4c_phase.npz",
}
TARGET_IDS = tuple(TARGET_FILES)


@dataclass(frozen=True)
class Condition:
    condition_id: str
    family: str
    target_ids: tuple[str, ...]
    parameters: dict[str, Any]


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_npz(path: Path, arrays: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "paper_id",
        "output_root",
        "parameters",
        "acceptance",
        "execution",
        "review_policy",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"paper-scale config missing fields: {missing}")
    if payload["paper_id"] != "1807.03311":
        raise ValueError("paper-scale config belongs to another paper")
    parameters = payload["parameters"]
    if len(parameters.get("theta_sweep", [])) != 3:
        raise ValueError("theta_sweep must be [start, stop, count]")
    if int(parameters["dos_k_grid"]) < 2 or int(parameters["theta_sweep"][2]) < 2:
        raise ValueError("paper-scale grids require at least two samples")
    return payload


def config_sha256(config: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical_json(config))


def implementation_sha256() -> str:
    paths = [Path(__file__), Path(__file__).with_name("model.py")]
    runner = Path(__file__).resolve().parents[2] / "scripts" / "run_paper_scale.py"
    if runner.exists():
        paths.append(runner)
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _condition_record(condition: Condition) -> dict[str, Any]:
    return {
        "condition_id": condition.condition_id,
        "family": condition.family,
        "target_ids": list(condition.target_ids),
        "parameters": condition.parameters,
    }


def enumerate_conditions(config: dict[str, Any]) -> list[Condition]:
    parameters = config["parameters"]
    conditions = [
        Condition(f"DOS_ROW_{row:04d}", "dos_row", ("T003",), {"row": row})
        for row in range(int(parameters["dos_k_grid"]))
    ]
    theta_values = np.linspace(*parameters["theta_sweep"])
    conditions.extend(
        Condition(
            f"THETA_{index:04d}",
            "theta_point",
            ("T006", "T007"),
            {"index": index, "theta_deg": float(theta)},
        )
        for index, theta in enumerate(theta_values)
    )
    conditions.append(
        Condition(
            "CROSSCHECK_0000", "crosscheck", TARGET_IDS, {"anchor": "Gamma_and_K"}
        )
    )
    identifiers = [condition.condition_id for condition in conditions]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("condition identifiers are not unique")
    return conditions


def plan_campaign(
    config: dict[str, Any], output_root: Path, *, write: bool = False
) -> dict[str, Any]:
    conditions = enumerate_conditions(config)
    by_family: dict[str, int] = {}
    for condition in conditions:
        by_family[condition.family] = by_family.get(condition.family, 0) + 1
    payload = {
        "schema_version": 1,
        "status": "ready",
        "paper_id": config["paper_id"],
        "run_id": config.get("run_id"),
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "target_ids": list(TARGET_IDS),
        "conditions_total": len(conditions),
        "conditions_by_family": by_family,
        "recommended_shards": config["execution"]["recommended_shards"],
        "conditions": [_condition_record(condition) for condition in conditions],
    }
    if write:
        _atomic_json(output_root / "plan.json", payload)
    return payload


def _model(
    parameters: dict[str, Any], theta: float = 1.2, *, validation: bool = False
) -> TwoBandContinuum:
    key = "convergence_plane_wave_cutoff" if validation else "plane_wave_cutoff"
    return TwoBandContinuum(
        theta,
        cutoff=int(parameters[key]),
        a0_nm=float(parameters["a0_nm"]),
        effective_mass_me=float(parameters["effective_mass_me"]),
        potential_mev=float(parameters["potential_mev"]),
        potential_phase_deg=float(parameters["potential_phase_deg"]),
        tunneling_mev=float(parameters["tunneling_mev"]),
    )


def _dos_row(parameters: dict[str, Any], row: int) -> dict[str, Any]:
    model = _model(parameters)
    grid = int(parameters["dos_k_grid"])
    fractions = (np.arange(grid) + 0.5) / grid - 0.5
    u = float(fractions[row])
    count = int(parameters["dos_band_count"])
    energies = np.asarray(
        [
            model.top_bands(u * model.geometry.B1 + float(v) * model.geometry.B2, count)
            for v in fractions
        ]
    )
    return {
        "row": np.asarray([row]),
        "u_fraction": np.asarray([u]),
        "energies_mev": energies,
    }


def _corner_critical_bias(
    model: TwoBandContinuum, parameters: dict[str, Any]
) -> tuple[float, float]:
    corners = (model.geometry.kappa_plus, model.geometry.kappa_minus)
    zero_splits = [
        float(np.diff(model.top_bands(corner, 2))[0] * -1.0) for corner in corners
    ]
    bias_axis = np.linspace(
        0.0, parameters["maximum_bias_mev"], parameters["bias_scan_points"]
    )
    direct_gaps = np.asarray(
        [
            min(
                float(np.diff(model.top_bands(corner, 2, float(bias)))[0] * -1.0)
                for corner in corners
            )
            for bias in bias_axis
        ]
    )
    minimum = int(np.argmin(direct_gaps))
    critical = float(bias_axis[minimum])
    if 0 < minimum < len(bias_axis) - 1:
        x = bias_axis[minimum - 1 : minimum + 2]
        y = direct_gaps[minimum - 1 : minimum + 2]
        coefficients = np.polyfit(x, y, 2)
        if coefficients[0] > 0.0:
            critical = float(
                np.clip(-coefficients[1] / (2.0 * coefficients[0]), x[0], x[-1])
            )
    return critical, float(np.mean(zero_splits))


def _overlap_recovery_bias(
    model: TwoBandContinuum, parameters: dict[str, Any], first_gap: float
) -> float:
    if first_gap >= 0.0:
        return 0.0
    high = float(parameters["maximum_bias_mev"])
    grid = int(parameters["phase_k_grid"])
    if model.global_gaps(grid_points=grid, layer_bias_mev=high)[0] <= 0.0:
        return float("nan")
    low = 0.0
    for _ in range(int(parameters["overlap_bisection_steps"])):
        midpoint = 0.5 * (low + high)
        if model.global_gaps(grid_points=grid, layer_bias_mev=midpoint)[0] > 0.0:
            high = midpoint
        else:
            low = midpoint
    return high


def _theta_point(
    parameters: dict[str, Any], index: int, theta: float
) -> dict[str, Any]:
    model = _model(parameters, theta)
    gap12, gap23 = model.global_gaps(grid_points=int(parameters["gap_k_grid"]))
    critical_full, critical_tb = _corner_critical_bias(model, parameters)
    recovery = _overlap_recovery_bias(model, parameters, gap12)
    return {
        "index": np.asarray([index]),
        "theta_deg": np.asarray([theta]),
        "gap12_mev": np.asarray([gap12]),
        "gap23_mev": np.asarray([gap23]),
        "critical_bias_full_mev": np.asarray([critical_full]),
        "critical_bias_tb_mev": np.asarray([critical_tb]),
        "overlap_recovery_bias_mev": np.asarray([recovery]),
    }


def _crosscheck(parameters: dict[str, Any]) -> dict[str, Any]:
    primary = _model(parameters)
    validation = _model(parameters, validation=True)
    anchors = (np.zeros(2), primary.geometry.kappa_plus, primary.geometry.kappa_minus)
    path_differences = []
    residuals = []
    cutoff_differences = []
    for point in anchors:
        matrix = primary.hamiltonian(point)
        values_only = np.linalg.eigvalsh(matrix)
        values, vectors = np.linalg.eigh(matrix)
        path_differences.append(float(np.max(np.abs(values_only - values))))
        residual = matrix @ vectors - vectors * values[None, :]
        residuals.append(
            float(np.linalg.norm(residual) / max(np.linalg.norm(matrix), 1.0))
        )
        cutoff_differences.append(
            float(
                np.max(
                    np.abs(primary.top_bands(point, 4) - validation.top_bands(point, 4))
                )
            )
        )
    gap_grid_differences = []
    for theta in (1.2, 2.0, 3.2):
        model = _model(parameters, theta)
        primary_gaps = np.asarray(
            model.global_gaps(grid_points=int(parameters["gap_k_grid"]))
        )
        validation_gaps = np.asarray(
            model.global_gaps(grid_points=int(parameters["validation_gap_k_grid"]))
        )
        gap_grid_differences.append(
            float(np.max(np.abs(primary_gaps - validation_gaps)))
        )
    return {
        "eigensolver_path_max_absolute_difference_mev": np.asarray(
            [max(path_differences)]
        ),
        "eigensolver_residual_max": np.asarray([max(residuals)]),
        "cutoff_anchor_max_absolute_difference_mev": np.asarray(
            [max(cutoff_differences)]
        ),
        "gap_grid_crosscheck_max_absolute_difference_mev": np.asarray(
            [max(gap_grid_differences)]
        ),
        "primary_dimension": np.asarray([primary.dimension]),
        "validation_dimension": np.asarray([validation.dimension]),
    }


def _condition_arrays(config: dict[str, Any], condition: Condition) -> dict[str, Any]:
    parameters = config["parameters"]
    if condition.family == "dos_row":
        return _dos_row(parameters, int(condition.parameters["row"]))
    if condition.family == "theta_point":
        return _theta_point(
            parameters,
            int(condition.parameters["index"]),
            float(condition.parameters["theta_deg"]),
        )
    if condition.family == "crosscheck":
        return _crosscheck(parameters)
    raise ValueError(f"unknown condition family: {condition.family}")


def _condition_paths(output_root: Path, condition: Condition) -> tuple[Path, Path]:
    base = output_root / "conditions" / condition.condition_id
    return base.with_suffix(".npz"), base.with_suffix(".manifest.json")


def _valid_checkpoint(
    config: dict[str, Any], result_path: Path, manifest_path: Path, condition: Condition
) -> bool:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return bool(
        manifest.get("status") == "complete"
        and manifest.get("config_sha256") == config_sha256(config)
        and manifest.get("implementation_sha256") == implementation_sha256()
        and manifest.get("condition") == _condition_record(condition)
        and manifest.get("output_sha256") == _sha256_file(result_path)
    )


def _execute_condition(
    config: dict[str, Any], output_root: Path, condition: Condition, *, resume: bool
) -> dict[str, str]:
    result_path, manifest_path = _condition_paths(output_root, condition)
    if result_path.exists() or manifest_path.exists():
        if not resume or not (result_path.exists() and manifest_path.exists()):
            raise RuntimeError(f"partial checkpoint: {condition.condition_id}")
        if not _valid_checkpoint(config, result_path, manifest_path, condition):
            raise RuntimeError(f"stale or corrupt checkpoint: {condition.condition_id}")
        return {"condition_id": condition.condition_id, "status": "resumed"}
    _atomic_npz(result_path, _condition_arrays(config, condition))
    _atomic_json(
        manifest_path,
        {
            "schema_version": 1,
            "status": "complete",
            "paper_id": config["paper_id"],
            "condition": _condition_record(condition),
            "config_sha256": config_sha256(config),
            "implementation_sha256": implementation_sha256(),
            "output_path": str(result_path.relative_to(output_root)),
            "output_sha256": _sha256_file(result_path),
        },
    )
    return {"condition_id": condition.condition_id, "status": "computed"}


def _worker(arguments: tuple[dict[str, Any], str, Condition, bool]) -> dict[str, str]:
    config, output_root, condition, resume = arguments
    return _execute_condition(config, Path(output_root), condition, resume=resume)


def run_shard(
    config: dict[str, Any],
    output_root: Path,
    *,
    shard_index: int,
    shard_count: int,
    workers: int = 1,
    resume: bool = True,
) -> dict[str, Any]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("shard index must be in [0, shard_count)")
    if workers < 1:
        raise ValueError("workers must be positive")
    conditions = [
        condition
        for index, condition in enumerate(enumerate_conditions(config))
        if index % shard_count == shard_index
    ]
    arguments = [
        (config, str(output_root), condition, resume) for condition in conditions
    ]
    if workers == 1:
        results = [_worker(argument) for argument in arguments]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_worker, arguments))
    summary = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "conditions_assigned": len(conditions),
        "computed": sum(result["status"] == "computed" for result in results),
        "resumed": sum(result["status"] == "resumed" for result in results),
        "results": results,
    }
    summary_path = (
        output_root / "run_summary.json"
        if shard_count == 1
        else output_root / "runs" / f"shard-{shard_index:04d}-of-{shard_count:04d}.json"
    )
    _atomic_json(summary_path, summary)
    return summary


def _load_condition(
    config: dict[str, Any], output_root: Path, condition: Condition
) -> dict[str, np.ndarray]:
    result_path, manifest_path = _condition_paths(output_root, condition)
    if not result_path.exists() or not manifest_path.exists():
        raise RuntimeError(f"missing condition: {condition.condition_id}")
    if not _valid_checkpoint(config, result_path, manifest_path, condition):
        raise RuntimeError(f"invalid condition: {condition.condition_id}")
    with np.load(result_path, allow_pickle=False) as archive:
        return {name: np.asarray(archive[name]) for name in archive.files}


def _zero_crossing(x: np.ndarray, y: np.ndarray, *, high_branch: bool = False) -> float:
    candidates = []
    for index in range(len(x) - 1):
        if y[index] == 0.0:
            candidates.append(float(x[index]))
        elif y[index] * y[index + 1] < 0.0:
            weight = abs(y[index]) / (abs(y[index]) + abs(y[index + 1]))
            candidates.append(float(x[index] + weight * (x[index + 1] - x[index])))
    if not candidates:
        return float(x[int(np.argmin(np.abs(y)))])
    return max(candidates) if high_branch else min(candidates)


def _aggregate_dos(
    config: dict[str, Any], rows: list[dict[str, np.ndarray]]
) -> dict[str, Any]:
    parameters = config["parameters"]
    ordered = sorted(rows, key=lambda row: int(row["row"][0]))
    energies = np.concatenate([row["energies_mev"] for row in ordered], axis=0)
    sigma = float(parameters["dos_broadening_mev"])
    padding = float(parameters["dos_energy_padding_sigma"]) * sigma
    energy = np.linspace(
        float(np.max(energies) + padding),
        float(np.min(energies) - padding),
        int(parameters["dos_energy_points"]),
    )
    difference = energy[:, None, None] - energies[None, :, :]
    gaussian = np.exp(-0.5 * (difference / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))
    dos_per_cell_per_mev = 2.0 * np.mean(np.sum(gaussian, axis=2), axis=1)
    filling = 2.0 * np.mean(
        np.sum(energies[None, :, :] > energy[:, None, None], axis=2), axis=1
    )
    geometry = MoireGeometry(1.2)
    dos_per_ev_nm2 = dos_per_cell_per_mev * 1000.0 / geometry.unit_cell_area_nm2
    return {
        "filling_holes_per_muc": filling,
        "hole_density_1e12_cm2": filling / geometry.unit_cell_area_nm2 * 100.0,
        "dos_ev_inv_nm2": dos_per_ev_nm2,
        "dos_per_cell_per_mev": dos_per_cell_per_mev,
        "energy_mev": energy,
        "raw_top4_energies_mev": energies,
        "broadening_mev": np.asarray(sigma),
        "unit_cell_area_nm2": np.asarray(geometry.unit_cell_area_nm2),
    }


def _aggregate_theta(
    rows: list[dict[str, np.ndarray]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: int(row["index"][0]))
    theta = np.asarray([row["theta_deg"][0] for row in ordered])
    gap12 = np.asarray([row["gap12_mev"][0] for row in ordered])
    gap23 = np.asarray([row["gap23_mev"][0] for row in ordered])
    critical_full = np.asarray([row["critical_bias_full_mev"][0] for row in ordered])
    critical_tb = np.asarray([row["critical_bias_tb_mev"][0] for row in ordered])
    recovery = np.asarray([row["overlap_recovery_bias_mev"][0] for row in ordered])
    peak = int(np.argmax(gap12))
    recovery[: peak + 1] = 0.0
    gaps = {
        "theta_deg": theta,
        "gap12_mev": gap12,
        "gap23_mev": gap23,
        "theta1_estimate_deg": np.asarray(_zero_crossing(theta, gap23)),
        "theta2_estimate_deg": np.asarray(
            _zero_crossing(theta, gap12, high_branch=True)
        ),
        "theta1_paper_deg": np.asarray(1.74),
        "theta2_paper_deg": np.asarray(3.1),
    }
    phase = {
        "theta_deg": theta,
        "critical_bias_full_mev": critical_full,
        "critical_bias_tb_mev": critical_tb,
        "overlap_recovery_bias_mev": recovery,
        "gap12_zero_bias_mev": gap12,
    }
    return gaps, phase


def _gate(
    name: str, value: float, threshold: float, *, minimum: bool = False
) -> dict[str, Any]:
    passed = value >= threshold if minimum else value <= threshold
    return {
        "name": name,
        "value": value,
        "threshold": threshold,
        "passed": bool(passed),
    }


def _trapezoid_integral(y: np.ndarray, x: np.ndarray) -> float:
    """Support both NumPy 1.x (`trapz`) and NumPy 2.x (`trapezoid`)."""

    trapezoid = getattr(np, "trapezoid", None)
    if trapezoid is not None:
        return float(trapezoid(y, x))
    return float(np.trapz(y, x))  # type: ignore[attr-defined]


def aggregate_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    conditions = enumerate_conditions(config)
    loaded = [
        (condition, _load_condition(config, output_root, condition))
        for condition in conditions
    ]
    dos_rows = [arrays for condition, arrays in loaded if condition.family == "dos_row"]
    theta_rows = [
        arrays for condition, arrays in loaded if condition.family == "theta_point"
    ]
    crosscheck = next(
        arrays for condition, arrays in loaded if condition.family == "crosscheck"
    )
    dos = _aggregate_dos(config, dos_rows)
    gaps, phase = _aggregate_theta(theta_rows)

    aggregate_dir = output_root / "aggregates"
    paths = {
        "T003": aggregate_dir / TARGET_FILES["T003"],
        "T006": aggregate_dir / TARGET_FILES["T006"],
        "T007": aggregate_dir / TARGET_FILES["T007"],
    }
    _atomic_npz(paths["T003"], dos)
    _atomic_npz(paths["T006"], gaps)
    _atomic_npz(paths["T007"], phase)

    acceptance = config["acceptance"]
    energy_ascending = np.asarray(dos["energy_mev"])[::-1]
    dos_ascending = np.asarray(dos["dos_per_cell_per_mev"])[::-1]
    dos_integral = _trapezoid_integral(dos_ascending, energy_ascending)
    expected_states = 2.0 * float(config["parameters"]["dos_band_count"])
    finite_values = np.concatenate(
        [
            np.ravel(np.asarray(value, dtype=float))
            for payload in (dos, gaps, phase)
            for value in payload.values()
        ]
    )
    finite_fraction = float(np.mean(np.isfinite(finite_values)))
    checks = [
        _gate(
            "finite_fraction",
            finite_fraction,
            float(acceptance["finite_fraction"]),
            minimum=True,
        ),
        _gate(
            "dos_integral_absolute_error",
            abs(dos_integral - expected_states),
            float(acceptance["dos_integral_absolute_error"]),
        ),
        _gate(
            "dos_filling_endpoint_absolute_error",
            max(
                abs(float(dos["filling_holes_per_muc"][0])),
                abs(float(dos["filling_holes_per_muc"][-1]) - expected_states),
            ),
            float(acceptance["dos_filling_endpoint_absolute_error"]),
        ),
        _gate(
            "eigensolver_residual_max",
            float(crosscheck["eigensolver_residual_max"][0]),
            float(acceptance["eigensolver_residual_max"]),
        ),
        _gate(
            "eigensolver_path_max_absolute_difference_mev",
            float(crosscheck["eigensolver_path_max_absolute_difference_mev"][0]),
            float(acceptance["eigensolver_path_max_absolute_difference_mev"]),
        ),
        _gate(
            "cutoff_anchor_max_absolute_difference_mev",
            float(crosscheck["cutoff_anchor_max_absolute_difference_mev"][0]),
            float(acceptance["cutoff_anchor_max_absolute_difference_mev"]),
        ),
        _gate(
            "gap_grid_crosscheck_max_absolute_difference_mev",
            float(crosscheck["gap_grid_crosscheck_max_absolute_difference_mev"][0]),
            float(acceptance["gap_grid_crosscheck_max_absolute_difference_mev"]),
        ),
    ]
    theta1 = float(gaps["theta1_estimate_deg"])
    theta2 = float(gaps["theta2_estimate_deg"])
    theta1_interval = acceptance["theta1_interval_deg"]
    theta2_interval = acceptance["theta2_interval_deg"]
    checks.extend(
        [
            {
                "name": "theta1_interval_deg",
                "value": theta1,
                "interval": theta1_interval,
                "passed": bool(theta1_interval[0] <= theta1 <= theta1_interval[1]),
            },
            {
                "name": "theta2_interval_deg",
                "value": theta2,
                "interval": theta2_interval,
                "passed": bool(theta2_interval[0] <= theta2 <= theta2_interval[1]),
            },
        ]
    )
    status = "passed" if all(check["passed"] for check in checks) else "failed"
    crosscheck_payload = {
        "schema_version": 1,
        "status": (
            "passed" if all(check["passed"] for check in checks[3:7]) else "failed"
        ),
        **{key: float(value[0]) for key, value in crosscheck.items()},
    }
    assessment = {
        "schema_version": 1,
        "status": status,
        "paper_id": config["paper_id"],
        "artifact_stage": "paper_scale_candidate",
        "paper_parameters_executed": True,
        "paper_error_candidate_emitted": False,
        "checks": checks,
        "review_boundary": "A stable mismatch remains inconclusive until protocol-v2 independent review and paper-error gates pass.",
    }
    _atomic_json(output_root / "checks" / "crosscheck.json", crosscheck_payload)
    _atomic_json(output_root / "checks" / "scientific_assessment.json", assessment)
    manifest = {
        "schema_version": 1,
        "status": status,
        "paper_id": config["paper_id"],
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "conditions_total": len(conditions),
        "outputs": [
            {
                "target_id": target_id,
                "path": str(path.relative_to(output_root)),
                "sha256": _sha256_file(path),
            }
            for target_id, path in paths.items()
        ],
    }
    _atomic_json(output_root / "aggregate_manifest.json", manifest)
    return {"status": status, "conditions_total": len(conditions), "checks": checks}


__all__ = [
    "Condition",
    "TARGET_FILES",
    "aggregate_campaign",
    "config_sha256",
    "enumerate_conditions",
    "implementation_sha256",
    "load_config",
    "plan_campaign",
    "run_shard",
]
