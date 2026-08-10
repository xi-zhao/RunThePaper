"""Restartable paper-scale execution for the formula-derived moire model.

The unit of work is an immutable numerical condition: one momentum-grid row,
one Wannier momentum row, or one moire-period point.  This keeps the expensive
campaign shardable without changing the scientific object.  Numerical workers
never read the paper, reference images, author arrays, or author code.
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
from scipy import linalg as scipy_linalg

from .model import SingleBandContinuum, exchange_couplings, screened_interactions

TARGET_FILES = {
    "T003": "T003_main_fig2b_dos.npz",
    "T004": "T004_main_fig2c_wannier.npz",
    "T005": "T005_main_fig2d_hopping.npz",
    "T006": "T006_main_fig3a_interactions.npz",
    "T007": "T007_main_fig3b_exchange.npz",
    "T008": "T008_main_fig4a_fermi_contour.npz",
    "T011": "T011_supp_fig5c_hopping.npz",
    "T012": "T012_supp_fig5d_interactions.npz",
}
TARGET_IDS = tuple(TARGET_FILES)


@dataclass(frozen=True)
class Condition:
    """One independently restartable scientific work item."""

    condition_id: str
    family: str
    target_ids: tuple[str, ...]
    parameters: dict[str, Any]


def _condition_record(condition: Condition) -> dict[str, Any]:
    """Return the JSON-stable identity used by plans and checkpoints."""

    return {
        "condition_id": condition.condition_id,
        "family": condition.family,
        "target_ids": list(condition.target_ids),
        "parameters": condition.parameters,
    }


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
    config = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "paper_id",
        "output_root",
        "parameters",
        "acceptance",
        "execution",
        "review_policy",
    }
    missing = sorted(required - config.keys())
    if missing:
        raise ValueError(f"paper-scale config missing fields: {missing}")
    if config["paper_id"] != "1804.03151":
        raise ValueError("paper-scale config belongs to a different paper")
    return config


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


def enumerate_conditions(config: dict[str, Any]) -> list[Condition]:
    parameters = config["parameters"]
    conditions: list[Condition] = []
    for row in range(int(parameters["dos_k_grid"])):
        conditions.append(
            Condition(f"DOS_ROW_{row:04d}", "dos_row", ("T003",), {"row": row})
        )
    for row in range(int(parameters["wannier_k_grid"])):
        conditions.append(
            Condition(f"WANNIER_ROW_{row:04d}", "wannier_row", ("T004",), {"row": row})
        )
    main_values = np.linspace(*parameters["main_a_moire_sweep"])
    for index, value in enumerate(main_values):
        conditions.append(
            Condition(
                f"MAIN_SWEEP_{index:04d}",
                "main_sweep",
                ("T005", "T006", "T007"),
                {"index": index, "a_moire_nm": float(value)},
            )
        )
    for row in range(int(parameters["fermi_grid"])):
        conditions.append(
            Condition(f"FERMI_ROW_{row:04d}", "fermi_row", ("T008",), {"row": row})
        )
    supplement_values = np.linspace(*parameters["supplement_a_moire_sweep"])
    for index, value in enumerate(supplement_values):
        conditions.append(
            Condition(
                f"SUPP_SWEEP_{index:04d}",
                "supplement_sweep",
                ("T011", "T012"),
                {"index": index, "a_moire_nm": float(value)},
            )
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


def _main_model(
    parameters: dict[str, Any], *, cutoff: int | None = None
) -> SingleBandContinuum:
    system = parameters["main_system"]
    a_moire = float(parameters["a0_nm"]) / np.deg2rad(
        float(parameters["band_twist_deg"])
    )
    return SingleBandContinuum(
        a_moire,
        cutoff=int(parameters["cutoff"] if cutoff is None else cutoff),
        effective_mass_me=float(parameters["effective_mass_me"]),
        potential_mev=float(system["potential_mev"]),
        potential_phase_deg=float(system["phase_deg"]),
    )


def _sweep_model(
    parameters: dict[str, Any], a_moire_nm: float, *, supplement: bool
) -> SingleBandContinuum:
    system = parameters["supplement_system" if supplement else "main_system"]
    return SingleBandContinuum(
        a_moire_nm,
        cutoff=int(parameters["cutoff"]),
        effective_mass_me=float(parameters["effective_mass_me"]),
        potential_mev=float(system["potential_mev"]),
        potential_phase_deg=float(system["phase_deg"]),
    )


def _dos_row(parameters: dict[str, Any], row: int) -> dict[str, Any]:
    model = _main_model(parameters)
    grid = int(parameters["dos_k_grid"])
    count = int(parameters["dos_band_count"])
    fractions = (np.arange(grid) + 0.5) / grid - 0.5
    u = float(fractions[row])
    energies = np.asarray(
        [
            model.top_bands(u * model.geometry.B1 + v * model.geometry.B2, count)
            for v in fractions
        ]
    )
    return {
        "row": np.asarray([row]),
        "u_fraction": np.asarray([u]),
        "energies_mev": energies,
    }


def _wannier_row(parameters: dict[str, Any], row: int) -> dict[str, Any]:
    model = _main_model(parameters)
    k_grid = int(parameters["wannier_k_grid"])
    real_grid = int(parameters["wannier_real_grid"])
    span = float(parameters["wannier_span_moire_periods"]) * model.geometry.a_moire_nm
    x = np.linspace(-span, span, real_grid)
    y = np.linspace(-span, span, real_grid)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    relative = np.column_stack([xx.ravel(), yy.ravel()])
    center = model.potential_maximum()
    absolute = relative + center[None, :]
    fractions = (np.arange(k_grid) - k_grid // 2) / k_grid
    u = float(fractions[row])
    amplitude = np.zeros(len(relative), dtype=complex)
    for v in fractions:
        k = u * model.geometry.B1 + float(v) * model.geometry.B2
        _, vector = model.top_eigenpair(k)
        momenta = k[None, :] + model.basis.vectors
        value_at_center = np.sum(vector * np.exp(1j * (momenta @ center)))
        vector = vector * np.exp(-1j * np.angle(value_at_center))
        amplitude += np.exp(1j * (absolute @ momenta.T)) @ vector
    shape = (real_grid, real_grid)
    return {
        "row": np.asarray([row]),
        "x_nm": x,
        "y_nm": y,
        "center_nm": center,
        "partial_real": amplitude.real.reshape(shape),
        "partial_imag": amplitude.imag.reshape(shape),
    }


def _sweep_point(
    parameters: dict[str, Any], *, a_moire_nm: float, supplement: bool, index: int
) -> dict[str, Any]:
    model = _sweep_model(parameters, a_moire_nm, supplement=supplement)
    fit = model.tight_binding_fit(grid_points=int(parameters["fit_k_grid"]))
    hopping = np.asarray(fit["hopping_mev"], dtype=float)
    interaction = screened_interactions(
        model,
        screening_separation_nm=float(parameters["screening_separation_nm"]),
        k_grid=int(parameters["interaction_k_grid"]),
        real_grid=int(parameters["interaction_real_grid"]),
        span_moire_periods=float(parameters["interaction_span_moire_periods"]),
    )
    onsite_u = interaction[0] * 1000.0 / float(parameters["dielectric_constant"])
    return {
        "index": np.asarray([index]),
        "a_moire_nm": np.asarray([a_moire_nm]),
        "hopping_mev": hopping,
        "fit_rms_residual_mev": np.asarray([float(fit["rms_residual_mev"])]),
        "epsilon_u_ev": interaction,
        "exchange_mev": exchange_couplings(hopping, onsite_u),
    }


def _fermi_row(parameters: dict[str, Any], row: int) -> dict[str, Any]:
    model = _main_model(parameters)
    grid = int(parameters["fermi_grid"])
    vertices = model.geometry.bz_vertices
    limit_x = float(np.max(np.abs(vertices[:, 0])))
    limit_y = float(np.max(np.abs(vertices[:, 1])))
    x = np.linspace(-1.04 * limit_x, 1.04 * limit_x, grid)
    y = np.linspace(-1.04 * limit_y, 1.04 * limit_y, grid)
    points = np.column_stack([x, np.full(grid, y[row])])
    mask = model.geometry.inside_first_bz(points)
    energy = np.full(grid, np.nan)
    energy[mask] = np.asarray([model.top_bands(point, 1)[0] for point in points[mask]])
    return {
        "row": np.asarray([row]),
        "kx": x,
        "ky_value": np.asarray([y[row]]),
        "energy_mev": energy,
        "mask": mask,
        "bz_vertices": vertices,
    }


def _crosscheck(parameters: dict[str, Any]) -> dict[str, Any]:
    primary = _main_model(parameters)
    validation = _main_model(parameters, cutoff=int(parameters["validation_cutoff"]))
    gamma = np.zeros(2)
    kappa = (2.0 * primary.geometry.B1 + primary.geometry.B2) / 3.0
    solver_differences = []
    cutoff_differences = []
    for point in (gamma, kappa):
        numpy_values = np.linalg.eigvalsh(primary.hamiltonian(point))
        scipy_values = scipy_linalg.eigh(primary.hamiltonian(point), eigvals_only=True)
        solver_differences.append(float(np.max(np.abs(numpy_values - scipy_values))))
        primary_top = primary.top_bands(point, 4)
        validation_top = validation.top_bands(point, 4)
        cutoff_differences.append(float(np.max(np.abs(primary_top - validation_top))))
    return {
        "numpy_scipy_max_abs_mev": np.asarray([max(solver_differences)]),
        "cutoff_anchor_max_abs_mev": np.asarray([max(cutoff_differences)]),
        "primary_dimension": np.asarray([primary.dimension]),
        "validation_dimension": np.asarray([validation.dimension]),
    }


def _condition_arrays(config: dict[str, Any], condition: Condition) -> dict[str, Any]:
    parameters = config["parameters"]
    if condition.family == "dos_row":
        return _dos_row(parameters, int(condition.parameters["row"]))
    if condition.family == "wannier_row":
        return _wannier_row(parameters, int(condition.parameters["row"]))
    if condition.family == "main_sweep":
        return _sweep_point(
            parameters,
            a_moire_nm=float(condition.parameters["a_moire_nm"]),
            supplement=False,
            index=int(condition.parameters["index"]),
        )
    if condition.family == "fermi_row":
        return _fermi_row(parameters, int(condition.parameters["row"]))
    if condition.family == "supplement_sweep":
        return _sweep_point(
            parameters,
            a_moire_nm=float(condition.parameters["a_moire_nm"]),
            supplement=True,
            index=int(condition.parameters["index"]),
        )
    if condition.family == "crosscheck":
        return _crosscheck(parameters)
    raise ValueError(f"unknown condition family: {condition.family}")


def _condition_paths(output_root: Path, condition: Condition) -> tuple[Path, Path]:
    base = output_root / "conditions" / condition.condition_id
    return base.with_suffix(".npz"), base.with_suffix(".manifest.json")


def _execute_condition(
    config: dict[str, Any], output_root: Path, condition: Condition, *, resume: bool
) -> dict[str, Any]:
    result_path, manifest_path = _condition_paths(output_root, condition)
    config_hash = config_sha256(config)
    implementation_hash = implementation_sha256()
    if result_path.exists() or manifest_path.exists():
        if not resume or not (result_path.exists() and manifest_path.exists()):
            if resume:
                raise RuntimeError(
                    f"partial condition checkpoint: {condition.condition_id}"
                )
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            valid = (
                manifest.get("status") == "complete"
                and manifest.get("config_sha256") == config_hash
                and manifest.get("implementation_sha256") == implementation_hash
                and manifest.get("condition") == _condition_record(condition)
                and manifest.get("output_sha256") == _sha256_file(result_path)
            )
            if not valid:
                raise RuntimeError(
                    f"stale or corrupt checkpoint: {condition.condition_id}"
                )
            return {"condition_id": condition.condition_id, "status": "resumed"}
    arrays = _condition_arrays(config, condition)
    _atomic_npz(result_path, arrays)
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "condition": _condition_record(condition),
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "output_path": str(result_path.relative_to(output_root)),
        "output_sha256": _sha256_file(result_path),
    }
    _atomic_json(manifest_path, manifest)
    return {"condition_id": condition.condition_id, "status": "computed"}


def _worker(arguments: tuple[dict[str, Any], str, Condition, bool]) -> dict[str, Any]:
    config, output_root, condition, resume = arguments
    return _execute_condition(config, Path(output_root), condition, resume=resume)


def run_shard(
    config: dict[str, Any],
    output_root: Path,
    *,
    shard_index: int,
    shard_count: int,
    workers: int,
    resume: bool,
) -> dict[str, Any]:
    if shard_count <= 0 or not 0 <= shard_index < shard_count:
        raise ValueError("shard index/count is invalid")
    if workers <= 0:
        raise ValueError("workers must be positive")
    conditions = enumerate_conditions(config)
    selected = [
        condition
        for index, condition in enumerate(conditions)
        if index % shard_count == shard_index
    ]
    arguments = [
        (config, str(output_root), condition, resume) for condition in selected
    ]
    if workers == 1 or len(arguments) < 2:
        results = [_worker(argument) for argument in arguments]
    else:
        with ProcessPoolExecutor(max_workers=min(workers, len(arguments))) as pool:
            results = list(pool.map(_worker, arguments))
    status_counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    summary = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "config_sha256": config_sha256(config),
        "implementation_sha256": implementation_sha256(),
        "shard_index": shard_index,
        "shard_count": shard_count,
        "conditions_selected": len(selected),
        "status_counts": status_counts,
        "condition_ids": [condition.condition_id for condition in selected],
    }
    _atomic_json(
        output_root / "shards" / f"shard-{shard_index:05d}-of-{shard_count:05d}.json",
        summary,
    )
    return summary


def _load_condition(
    config: dict[str, Any], output_root: Path, condition: Condition
) -> dict[str, np.ndarray]:
    result_path, manifest_path = _condition_paths(output_root, condition)
    if not result_path.exists() or not manifest_path.exists():
        raise RuntimeError(f"condition is incomplete: {condition.condition_id}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("config_sha256") != config_sha256(config)
        or manifest.get("implementation_sha256") != implementation_sha256()
        or manifest.get("condition") != _condition_record(condition)
        or manifest.get("output_sha256") != _sha256_file(result_path)
    ):
        raise RuntimeError(f"condition attestation failed: {condition.condition_id}")
    with np.load(result_path, allow_pickle=False) as payload:
        return {key: np.asarray(payload[key]) for key in payload.files}


def _aggregate_dos(
    config: dict[str, Any], rows: list[dict[str, np.ndarray]]
) -> dict[str, Any]:
    parameters = config["parameters"]
    energies = np.stack([row["energies_mev"] for row in rows])
    flattened = energies.reshape(-1)
    ordered = np.sort(flattened)[::-1]
    grid = int(parameters["dos_k_grid"])
    count = int(parameters["dos_band_count"])
    filling = np.linspace(0.0, float(count), int(parameters["dos_filling_points"]))
    ranks = np.clip(np.rint(filling * grid**2).astype(int), 0, len(ordered) - 1)
    fermi = ordered[ranks]
    broadening = float(parameters["dos_broadening_mev"])
    delta = fermi[:, None] - flattened[None, :]
    kernel = np.exp(-0.5 * (delta / broadening) ** 2) / (
        np.sqrt(2.0 * np.pi) * broadening
    )
    model = _main_model(parameters)
    dos = 2.0 * np.sum(kernel, axis=1) / (grid**2 * model.geometry.unit_cell_area_nm2)
    return {
        "filling": filling,
        "fermi_energy_mev": fermi,
        "dos_ev_inv_nm2": 1000.0 * dos,
        "full_hole_density_1e12_cm2": np.asarray(
            [200.0 / model.geometry.unit_cell_area_nm2]
        ),
        "sampled_energies_mev": energies,
    }


def _aggregate_wannier(
    config: dict[str, Any], rows: list[dict[str, np.ndarray]]
) -> dict[str, Any]:
    parameters = config["parameters"]
    amplitude = sum(row["partial_real"] + 1j * row["partial_imag"] for row in rows)
    k_grid = int(parameters["wannier_k_grid"])
    amplitude = amplitude / float(k_grid**2)
    x = rows[0]["x_nm"]
    y = rows[0]["y_nm"]
    dx = float(x[1] - x[0])
    dy = float(y[1] - y[0])
    norm = float(np.sum(np.abs(amplitude) ** 2) * dx * dy)
    amplitude = amplitude / np.sqrt(norm)
    a_moire = _main_model(parameters).geometry.a_moire_nm
    normalization = float(np.sum(np.abs(amplitude) ** 2) * dx * dy)
    return {
        "x_over_am": x / a_moire,
        "y_over_am": y / a_moire,
        "amplitude_times_am": np.abs(amplitude) * a_moire,
        "probability_nm_minus2": np.abs(amplitude) ** 2,
        "center_nm": rows[0]["center_nm"],
        "normalization": np.asarray([normalization]),
    }


def _stack_sweep(rows: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    ordered = sorted(rows, key=lambda row: int(row["index"][0]))
    return {
        "a_moire_nm": np.asarray([row["a_moire_nm"][0] for row in ordered]),
        "hopping_mev": np.stack([row["hopping_mev"] for row in ordered]),
        "fit_rms_residual_mev": np.asarray(
            [row["fit_rms_residual_mev"][0] for row in ordered]
        ),
        "epsilon_u_ev": np.stack([row["epsilon_u_ev"] for row in ordered]),
        "exchange_mev": np.stack([row["exchange_mev"] for row in ordered]),
    }


def _aggregate_fermi(
    config: dict[str, Any], rows: list[dict[str, np.ndarray]]
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: int(row["row"][0]))
    energy = np.stack([row["energy_mev"] for row in ordered])
    mask = np.stack([row["mask"] for row in ordered])
    finite = energy[mask]
    filling = float(config["parameters"]["fermi_hole_filling"])
    return {
        "kx": ordered[0]["kx"],
        "ky": np.asarray([row["ky_value"][0] for row in ordered]),
        "energy_mev": energy,
        "mask": mask,
        "fermi_energy_mev": np.asarray([float(np.quantile(finite, 1.0 - filling))]),
        "bz_vertices": ordered[0]["bz_vertices"],
    }


def _write_aggregate(
    output_root: Path,
    target_id: str,
    arrays: dict[str, Any],
    config_hash: str,
    implementation_hash: str,
) -> dict[str, Any]:
    path = output_root / "aggregates" / TARGET_FILES[target_id]
    _atomic_npz(path, arrays)
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "target_id": target_id,
        "path": str(path.relative_to(output_root)),
        "sha256": _sha256_file(path),
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
    }
    _atomic_json(path.with_suffix(".manifest.json"), manifest)
    return manifest


def _assessment(
    config: dict[str, Any],
    aggregates: dict[str, dict[str, Any]],
    crosscheck: dict[str, Any],
) -> dict[str, Any]:
    acceptance = config["acceptance"]
    solver_difference = float(crosscheck["numpy_scipy_max_abs_mev"][0])
    cutoff_difference = float(crosscheck["cutoff_anchor_max_abs_mev"][0])
    crosscheck_passed = solver_difference <= float(
        acceptance["eigensolver_max_absolute_difference_mev"]
    ) and cutoff_difference <= float(
        acceptance["cutoff_anchor_max_absolute_difference_mev"]
    )
    main_hopping = np.asarray(aggregates["T005"]["hopping_mev"])
    main_interaction = np.asarray(aggregates["T006"]["epsilon_u_ev"])
    supplement_hopping = np.asarray(aggregates["T011"]["hopping_mev"])
    supplement_interaction = np.asarray(aggregates["T012"]["epsilon_u_ev"])
    main_dominant = float(
        np.mean(
            np.abs(main_hopping[:, 0]) > np.max(np.abs(main_hopping[:, 1:]), axis=1)
        )
    )
    supplement_dominant = float(
        np.mean(
            np.abs(supplement_hopping[:, 0])
            > np.max(np.abs(supplement_hopping[:, 1:]), axis=1)
        )
    )
    main_ordered = float(
        np.mean(
            (main_interaction[:, 0] > main_interaction[:, 1])
            & (main_interaction[:, 1] > main_interaction[:, 2])
            & (main_interaction[:, 2] > 0.0)
        )
    )
    supplement_ordered = float(
        np.mean(
            (supplement_interaction[:, 0] > supplement_interaction[:, 1])
            & (supplement_interaction[:, 1] > supplement_interaction[:, 2])
            & (supplement_interaction[:, 2] > 0.0)
        )
    )
    normalization_error = abs(float(aggregates["T004"]["normalization"][0]) - 1.0)
    dos_is_valid = bool(
        np.all(np.isfinite(aggregates["T003"]["dos_ev_inv_nm2"]))
    ) and bool(np.all(aggregates["T003"]["dos_ev_inv_nm2"] >= 0.0))
    exchange_is_finite = bool(np.all(np.isfinite(aggregates["T007"]["exchange_mev"])))
    fermi_is_finite = bool(
        np.all(
            np.isfinite(aggregates["T008"]["energy_mev"][aggregates["T008"]["mask"]])
        )
    )
    checks = {
        "T003": (
            dos_is_valid,
            {"dos_nonnegative_and_finite": dos_is_valid},
        ),
        "T004": (
            normalization_error <= float(acceptance["normalization_absolute_error"]),
            {"normalization_absolute_error": normalization_error},
        ),
        "T005": (
            main_dominant >= float(acceptance["dominant_t1_fraction"]),
            {"dominant_t1_fraction": main_dominant},
        ),
        "T006": (
            main_ordered >= float(acceptance["ordered_interaction_fraction"]),
            {"ordered_interaction_fraction": main_ordered},
        ),
        "T007": (
            exchange_is_finite,
            {"exchange_finite": exchange_is_finite},
        ),
        "T008": (
            fermi_is_finite,
            {"fermi_surface_grid_finite": fermi_is_finite},
        ),
        "T011": (
            supplement_dominant >= float(acceptance["dominant_t1_fraction"]),
            {"dominant_t1_fraction": supplement_dominant},
        ),
        "T012": (
            supplement_ordered >= float(acceptance["ordered_interaction_fraction"]),
            {"ordered_interaction_fraction": supplement_ordered},
        ),
    }
    targets = []
    for target_id in TARGET_IDS:
        target_passed, metrics = checks[target_id]
        supported = bool(target_passed and crosscheck_passed)
        targets.append(
            {
                "target_id": target_id,
                "status": "supported" if supported else "inconclusive",
                "paper_error_candidate": False,
                "metrics": metrics,
                "crosscheck_passed": crosscheck_passed,
                "next_action": (
                    "retain as converged independent support"
                    if supported
                    else "inspect method and convergence before any claim about the paper"
                ),
            }
        )
    supported = all(target["status"] == "supported" for target in targets)
    return {
        "schema_version": 1,
        "status": "passed" if supported else "requires_scientific_review",
        "paper_id": config["paper_id"],
        "paper_assessment": "supported" if supported else "inconclusive",
        "paper_error_candidate": False,
        "crosscheck": {
            "numpy_scipy_max_abs_mev": solver_difference,
            "cutoff_anchor_max_abs_mev": cutoff_difference,
            "passed": crosscheck_passed,
        },
        "targets": targets,
        "review_boundary": config["review_policy"],
    }


def aggregate_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    conditions = enumerate_conditions(config)
    grouped: dict[str, list[dict[str, np.ndarray]]] = {}
    for condition in conditions:
        grouped.setdefault(condition.family, []).append(
            _load_condition(config, output_root, condition)
        )
    aggregates: dict[str, dict[str, Any]] = {}
    aggregates["T003"] = _aggregate_dos(config, grouped["dos_row"])
    aggregates["T004"] = _aggregate_wannier(config, grouped["wannier_row"])
    main = _stack_sweep(grouped["main_sweep"])
    a0 = float(config["parameters"]["a0_nm"])
    main_theta = np.rad2deg(a0 / main["a_moire_nm"])
    dielectric = float(config["parameters"]["dielectric_constant"])
    aggregates["T005"] = {
        "a_moire_nm": main["a_moire_nm"],
        "theta_deg": main_theta,
        "hopping_mev": main["hopping_mev"],
        "fit_rms_residual_mev": main["fit_rms_residual_mev"],
    }
    aggregates["T006"] = {
        "a_moire_nm": main["a_moire_nm"],
        "theta_deg": main_theta,
        "epsilon_u_ev": main["epsilon_u_ev"],
        "u0_over_t1": main["epsilon_u_ev"][:, 0]
        * 1000.0
        / dielectric
        / main["hopping_mev"][:, 0],
    }
    aggregates["T007"] = {
        "a_moire_nm": main["a_moire_nm"],
        "theta_deg": main_theta,
        "exchange_mev": main["exchange_mev"],
        "j2_over_j1": np.divide(
            main["exchange_mev"][:, 1],
            main["exchange_mev"][:, 0],
            out=np.zeros_like(main["exchange_mev"][:, 1]),
            where=main["exchange_mev"][:, 0] != 0.0,
        ),
    }
    aggregates["T008"] = _aggregate_fermi(config, grouped["fermi_row"])
    supplement = _stack_sweep(grouped["supplement_sweep"])
    mismatch = float(config["parameters"]["supplement_system"]["mismatch"])
    supplement_theta = np.rad2deg(
        np.sqrt(np.maximum((a0 / supplement["a_moire_nm"]) ** 2 - mismatch**2, 0.0))
    )
    aggregates["T011"] = {
        "a_moire_nm": supplement["a_moire_nm"],
        "theta_deg": supplement_theta,
        "hopping_mev": supplement["hopping_mev"],
        "fit_rms_residual_mev": supplement["fit_rms_residual_mev"],
    }
    aggregates["T012"] = {
        "a_moire_nm": supplement["a_moire_nm"],
        "theta_deg": supplement_theta,
        "epsilon_u_ev": supplement["epsilon_u_ev"],
    }
    crosscheck = grouped["crosscheck"][0]
    config_hash = config_sha256(config)
    implementation_hash = implementation_sha256()
    manifests = {
        target_id: _write_aggregate(
            output_root,
            target_id,
            aggregates[target_id],
            config_hash,
            implementation_hash,
        )
        for target_id in TARGET_IDS
    }
    assessment = _assessment(config, aggregates, crosscheck)
    crosscheck_payload = {
        "schema_version": 1,
        "status": "passed" if assessment["crosscheck"]["passed"] else "failed",
        **{key: float(value[0]) for key, value in crosscheck.items()},
    }
    _atomic_json(output_root / "checks" / "crosscheck.json", crosscheck_payload)
    _atomic_json(output_root / "checks" / "scientific_assessment.json", assessment)
    condition_manifests = []
    for condition in conditions:
        _, manifest_path = _condition_paths(output_root, condition)
        condition_manifests.append(
            {
                "condition_id": condition.condition_id,
                "manifest_sha256": _sha256_file(manifest_path),
            }
        )
    aggregate_manifest = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "conditions_total": len(conditions),
        "condition_manifests": condition_manifests,
        "targets": manifests,
        "assessment_status": assessment["status"],
    }
    _atomic_json(output_root / "aggregate_manifest.json", aggregate_manifest)
    shard_summaries = sorted((output_root / "shards").glob("shard-*.json"))
    summary = {
        "schema_version": 1,
        "status": "complete",
        "paper_id": config["paper_id"],
        "run_id": config.get("run_id"),
        "conditions_total": len(conditions),
        "targets_total": len(TARGET_IDS),
        "target_ids": list(TARGET_IDS),
        "shard_summaries": [
            str(path.relative_to(output_root)) for path in shard_summaries
        ],
        "paper_assessment": assessment["paper_assessment"],
        "paper_error_candidate": False,
    }
    _atomic_json(output_root / "run_summary.json", summary)
    return summary
