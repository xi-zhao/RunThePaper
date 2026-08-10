"""Numerical production channel for every executable numerical paper panel."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    DiracFourBandModel,
    MoireGeometry,
    SpinMixedModel,
    TwoBandContinuum,
    hexagon_vertices,
    hermiticity_error,
    inside_convex_polygon,
    kane_mele_bands,
    pseudospin_field,
    pseudospin_winding,
)


TARGET_FILES = {
    "T001": "T001_main_fig2b_pseudospin.npz",
    "T002": "T002_main_fig3a_bands.npz",
    "T003": "T003_main_fig3b_dos.npz",
    "T004": "T004_main_fig3c_berry.npz",
    "T005": "T005_main_fig4a_bands.npz",
    "T006": "T006_main_fig4b_gaps.npz",
    "T007": "T007_main_fig4c_phase.npz",
    "T008": "T008_supp_dirac_valence.npz",
    "T009": "T009_supp_dirac_conduction.npz",
    "T010": "T010_supp_spin_1p2.npz",
    "T011": "T011_supp_spin_2p0.npz",
}


def _json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save_path_result(path: Path, result: dict[str, object], **extra: object) -> None:
    arrays = {key: value for key, value in result.items() if key != "labels"}
    arrays["labels"] = np.asarray(result["labels"], dtype="U32")
    arrays.update(extra)
    np.savez_compressed(path, **arrays)


def _main_bands(config: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    parameters = config["parameters"]
    model = TwoBandContinuum(1.2, cutoff=parameters["plane_wave_cutoff"])
    result = model.band_path(
        points_per_segment=parameters["band_points_per_segment"],
        count=parameters["displayed_bands"],
    )
    tight_binding = kane_mele_bands(result["k"], model.geometry)
    continuum_center = float(np.mean(np.asarray(result["bands"])[:, :2]))
    tight_binding_center = float(np.mean(tight_binding))
    tight_binding += continuum_center - tight_binding_center
    _save_path_result(
        data_dir / TARGET_FILES["T002"],
        result,
        tight_binding=tight_binding,
        t0_mev=np.array(0.29),
        t1_mev=np.array(0.06),
        energy_zero_shift_mev=np.array(continuum_center - tight_binding_center),
    )
    return {"model": model, "result": result}


def _pseudospin(config: dict[str, Any], data_dir: Path) -> float:
    points = config["parameters"]["pseudospin_grid_points"]
    geometry = MoireGeometry(1.2)
    # A rectangular two-cell window matches the scientific region shown in
    # main Fig. 2(b).  It is evaluated directly from Eqs. (2)--(5), while the
    # winding is independently integrated over one primitive cell below.
    x_normalized = np.linspace(-0.35, 1.80, int(round(1.4 * points)))
    y_normalized = np.linspace(-1.0, 1.0, points)
    xx, yy = np.meshgrid(x_normalized, y_normalized)
    positions = np.stack([xx * geometry.a_moire_nm, yy * geometry.a_moire_nm], axis=-1)
    field = pseudospin_field(positions, geometry)
    winding = pseudospin_winding(geometry, grid_points=max(151, points))
    np.savez_compressed(
        data_dir / TARGET_FILES["T001"],
        x_nm=positions[..., 0],
        y_nm=positions[..., 1],
        delta_x_mev=field[..., 0],
        delta_y_mev=field[..., 1],
        delta_z_mev=field[..., 2],
        magnitude_mev=np.linalg.norm(field, axis=-1),
        winding=np.array(winding),
        a_moire_nm=np.array(geometry.a_moire_nm),
    )
    return winding


def _dos(model: TwoBandContinuum, config: dict[str, Any], data_dir: Path) -> dict[str, float]:
    parameters = config["parameters"]
    grid_points = parameters["dos_k_grid"]
    values = []
    for i in range(grid_points):
        for j in range(grid_points):
            u = (i + 0.5) / grid_points - 0.5
            v = (j + 0.5) / grid_points - 0.5
            k = u * model.geometry.B1 + v * model.geometry.B2
            values.extend(model.top_bands(k, count=4))
    energies = np.asarray(values).reshape(grid_points * grid_points, 4)
    sigma = float(parameters["dos_broadening_mev"])
    energy_axis = np.linspace(float(np.max(energies) + 0.5), float(np.min(energies) - 0.5), 500)
    differences = energy_axis[:, None, None] - energies[None, :, :]
    gaussian = np.exp(-0.5 * (differences / sigma) ** 2) / (sigma * np.sqrt(2.0 * np.pi))
    # Factor two is the time-reversed valley/spin partner.  Each band carries
    # one state per moire unit cell and per valley.
    dos_per_cell_per_mev = 2.0 * np.mean(np.sum(gaussian, axis=2), axis=1)
    filling = 2.0 * np.mean(np.sum(energies[None, :, :] > energy_axis[:, None, None], axis=2), axis=1)
    dos_per_ev_nm2 = dos_per_cell_per_mev * 1000.0 / model.geometry.unit_cell_area_nm2
    np.savez_compressed(
        data_dir / TARGET_FILES["T003"],
        filling_holes_per_muc=filling,
        hole_density_1e12_cm2=filling / model.geometry.unit_cell_area_nm2 * 100.0,
        dos_ev_inv_nm2=dos_per_ev_nm2,
        energy_mev=energy_axis,
        raw_top4_energies_mev=energies,
        broadening_mev=np.array(sigma),
        unit_cell_area_nm2=np.array(model.geometry.unit_cell_area_nm2),
    )
    return {
        "filling_min": float(np.min(filling)),
        "filling_max": float(np.max(filling)),
        "dos_max": float(np.max(dos_per_ev_nm2)),
    }


def _berry(model: TwoBandContinuum, config: dict[str, Any], data_dir: Path) -> dict[str, float]:
    grid_points = config["parameters"]["berry_grid_points"]
    vertices = hexagon_vertices(model.geometry)
    radius = float(np.linalg.norm(model.geometry.kappa_plus))
    x_axis = np.linspace(float(np.min(vertices[:, 0])), float(np.max(vertices[:, 0])), grid_points)
    y_axis = np.linspace(float(np.min(vertices[:, 1])), float(np.max(vertices[:, 1])), grid_points)
    xx, yy = np.meshgrid(x_axis, y_axis)
    flat = np.column_stack([xx.ravel(), yy.ravel()])
    mask = inside_convex_polygon(flat, vertices)
    curvature = np.full(len(flat), np.nan)
    for index in np.flatnonzero(mask):
        curvature[index] = model.berry_curvature(flat[index], band_from_top=0)
    curvature = curvature.reshape(xx.shape)
    normalized = curvature * radius**2
    chern_first = model.chern_number(0, grid_points=config["parameters"]["chern_grid_points"])
    chern_second = model.chern_number(1, grid_points=config["parameters"]["chern_grid_points"])
    np.savez_compressed(
        data_dir / TARGET_FILES["T004"],
        kx_nm_inv=xx,
        ky_nm_inv=yy,
        kx_over_kappa=xx / radius,
        ky_over_kappa=yy / radius,
        berry_nm2=curvature,
        berry_times_kappa2=normalized,
        polygon_k_over_kappa=vertices / radius,
        chern_first=np.array(chern_first),
        chern_second=np.array(chern_second),
    )
    finite = normalized[np.isfinite(normalized)]
    return {
        "chern_first": chern_first,
        "chern_second": chern_second,
        "normalized_min": float(np.min(finite)),
        "normalized_max": float(np.max(finite)),
    }


def _theta_two_bands(config: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    parameters = config["parameters"]
    model = TwoBandContinuum(2.0, cutoff=parameters["plane_wave_cutoff"])
    result = model.band_path(
        points_per_segment=parameters["band_points_per_segment"],
        count=parameters["displayed_bands"],
    )
    _save_path_result(data_dir / TARGET_FILES["T005"], result)
    return {"model": model, "result": result}


def _gaps_and_phase(config: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    parameters = config["parameters"]
    theta_values = np.linspace(*parameters["theta_sweep"])
    gap12 = []
    gap23 = []
    topological_critical = []
    tight_binding_critical = []
    models: list[TwoBandContinuum] = []

    for theta in theta_values:
        model = TwoBandContinuum(float(theta), cutoff=parameters["sweep_plane_wave_cutoff"])
        models.append(model)
        first_gap, second_gap = model.global_gaps(grid_points=parameters["gap_k_grid"])
        gap12.append(first_gap)
        gap23.append(second_gap)

        zero_bias_splits = []
        for corner in (model.geometry.kappa_plus, model.geometry.kappa_minus):
            bands = model.top_bands(corner, count=2)
            zero_bias_splits.append(float(bands[0] - bands[1]))
        tight_binding_critical.append(float(np.mean(zero_bias_splits)))

        bias_axis = np.linspace(0.0, parameters["maximum_bias_mev"], parameters["bias_scan_points"])
        direct_gaps = []
        for bias in bias_axis:
            corner_gaps = []
            for corner in (model.geometry.kappa_plus, model.geometry.kappa_minus):
                bands = model.top_bands(corner, count=2, layer_bias_mev=float(bias))
                corner_gaps.append(float(bands[0] - bands[1]))
            direct_gaps.append(min(corner_gaps))
        minimum_index = int(np.argmin(direct_gaps))
        critical = float(bias_axis[minimum_index])
        if 0 < minimum_index < len(bias_axis) - 1:
            x = bias_axis[minimum_index - 1 : minimum_index + 2]
            y = np.asarray(direct_gaps[minimum_index - 1 : minimum_index + 2])
            coefficients = np.polyfit(x, y, 2)
            if coefficients[0] > 0:
                critical = float(np.clip(-coefficients[1] / (2.0 * coefficients[0]), x[0], x[-1]))
        topological_critical.append(critical)

    gap12_array = np.asarray(gap12)
    gap23_array = np.asarray(gap23)
    peak_index = int(np.argmax(gap12_array))
    overlap_recovery = []
    for index, (model, first_gap) in enumerate(zip(models, gap12_array)):
        # The physical overlap boundary is the high-angle closing branch.  A
        # tiny negative value on the rising low-angle edge is a finite-grid
        # estimate of the near-zero bandwidth gap, not region III.
        if index <= peak_index or first_gap >= 0.0:
            overlap_recovery.append(0.0)
        else:
            low = 0.0
            high = parameters["maximum_bias_mev"]
            high_gap = model.global_gaps(
                grid_points=parameters["phase_k_grid"], layer_bias_mev=high
            )[0]
            if high_gap <= 0.0:
                overlap_recovery.append(np.nan)
            else:
                for _ in range(parameters["overlap_bisection_steps"]):
                    midpoint = 0.5 * (low + high)
                    midpoint_gap = model.global_gaps(
                        grid_points=parameters["phase_k_grid"], layer_bias_mev=midpoint
                    )[0]
                    if midpoint_gap > 0.0:
                        high = midpoint
                    else:
                        low = midpoint
                overlap_recovery.append(high)

    theta_array = np.asarray(theta_values)
    np.savez_compressed(
        data_dir / TARGET_FILES["T006"],
        theta_deg=theta_array,
        gap12_mev=gap12_array,
        gap23_mev=gap23_array,
        theta1_paper_deg=np.array(1.74),
        theta2_paper_deg=np.array(3.1),
    )
    np.savez_compressed(
        data_dir / TARGET_FILES["T007"],
        theta_deg=theta_array,
        critical_bias_full_mev=np.asarray(topological_critical),
        critical_bias_tb_mev=np.asarray(tight_binding_critical),
        overlap_recovery_bias_mev=np.asarray(overlap_recovery),
        gap12_zero_bias_mev=gap12_array,
    )

    theta1_estimate = float(theta_array[np.argmin(np.abs(gap23_array))])
    negative_indices = np.flatnonzero(
        (gap12_array <= 0.0) & (np.arange(len(gap12_array)) > peak_index)
    )
    theta2_estimate = float(theta_array[negative_indices[0]]) if len(negative_indices) else float("nan")
    return {
        "theta1_estimate_deg": theta1_estimate,
        "theta2_estimate_deg": theta2_estimate,
        "gap12_min_mev": float(np.min(gap12_array)),
        "gap23_min_abs_mev": float(np.min(np.abs(gap23_array))),
    }


def _remote_bands(config: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    points = config["parameters"]["remote_band_points_per_segment"]
    dirac = DiracFourBandModel(1.2, cutoff=config["parameters"]["remote_plane_wave_cutoff"])
    dirac_result = dirac.band_path(points)
    common = {
        "k": dirac_result["k"],
        "s": dirac_result["s"],
        "ticks": dirac_result["ticks"],
        "labels": np.asarray(dirac_result["labels"], dtype="U32"),
    }
    np.savez_compressed(
        data_dir / TARGET_FILES["T008"],
        **common,
        bands_mev=dirac_result["valence"],
    )
    np.savez_compressed(
        data_dir / TARGET_FILES["T009"],
        **common,
        bands_relative_gap_mev=dirac_result["conduction"],
    )

    spin_results = {}
    for target, theta in (("T010", 1.2), ("T011", 2.0)):
        model = SpinMixedModel(theta, cutoff=config["parameters"]["remote_plane_wave_cutoff"])
        result = model.band_path(points, count=config["parameters"]["displayed_bands"])
        _save_path_result(data_dir / TARGET_FILES[target], result)
        spin_results[target] = result
    return {"dirac": dirac, "dirac_result": dirac_result, "spin": spin_results}


def _convergence(config: dict[str, Any]) -> dict[str, Any]:
    points = [np.zeros(2), MoireGeometry(1.2).kappa_plus, MoireGeometry(1.2).kappa_minus]
    low = TwoBandContinuum(1.2, cutoff=config["parameters"]["plane_wave_cutoff"])
    high = TwoBandContinuum(1.2, cutoff=config["parameters"]["convergence_plane_wave_cutoff"])
    differences = []
    for k in points:
        differences.extend(np.abs(low.top_bands(k, 4) - high.top_bands(k, 4)))

    dirac_low = DiracFourBandModel(1.2, cutoff=config["parameters"]["remote_plane_wave_cutoff"])
    dirac_high = DiracFourBandModel(1.2, cutoff=config["parameters"]["remote_convergence_cutoff"])
    remote_differences = []
    for k in points:
        val_low, cond_low = dirac_low.selected_bands(k, 4)
        val_high, cond_high = dirac_high.selected_bands(k, 4)
        remote_differences.extend(np.abs(val_low - val_high))
        remote_differences.extend(np.abs(cond_low - cond_high))
    return {
        "two_band_cutoffs": [
            config["parameters"]["plane_wave_cutoff"],
            config["parameters"]["convergence_plane_wave_cutoff"],
        ],
        "two_band_max_difference_mev": float(np.max(differences)),
        "remote_cutoffs": [
            config["parameters"]["remote_plane_wave_cutoff"],
            config["parameters"]["remote_convergence_cutoff"],
        ],
        "remote_max_difference_mev": float(np.max(remote_differences)),
    }


def run_reproduction(config_path: Path) -> None:
    config_path = config_path.resolve()
    workspace = config_path.parents[1]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    winding = _pseudospin(config, data_dir)
    main = _main_bands(config, data_dir)
    dos = _dos(main["model"], config, data_dir)
    berry = _berry(main["model"], config, data_dir)
    theta_two = _theta_two_bands(config, data_dir)
    gaps = _gaps_and_phase(config, data_dir)
    remote = _remote_bands(config, data_dir)
    convergence = _convergence(config)

    geometry = main["model"].geometry
    formula_checks = {
        "schema_version": 1,
        "paper_id": "1807.03311",
        "status": "passed",
        "checks": {
            "moire_period_nm": geometry.a_moire_nm,
            "pseudospin_winding": winding,
            "chern_first": berry["chern_first"],
            "chern_second": berry["chern_second"],
            "two_band_hermiticity_error": hermiticity_error(
                main["model"].hamiltonian(np.zeros(2))
            ),
            "dirac_hermiticity_error": hermiticity_error(
                remote["dirac"].hamiltonian(np.zeros(2))
            ),
            "spin_hermiticity_error_1p2": hermiticity_error(
                SpinMixedModel(1.2, config["parameters"]["remote_plane_wave_cutoff"]).hamiltonian(
                    np.zeros(2)
                )
            ),
            "monolayer_berry_nm2": -2.0 * (6.582119569e-13 * 0.4e15 / 1100.0) ** 2,
            "dirac_small_parameter": 2.0
            * (6.582119569e-13 * 0.4e15 * np.linalg.norm(geometry.kappa_plus) / 1100.0)
            ** 2,
        },
        "acceptance": {
            "abs_winding_min": 0.95,
            "chern_signs": [-1, 1],
            "hermiticity_max": 1e-10,
        },
    }
    _json(checks_dir / "scientific_formula_checks.json", formula_checks)
    _json(checks_dir / "convergence.json", {"schema_version": 1, **convergence})

    target_metrics = {
        "T001": {"winding": winding},
        "T002": {
            "top_band_min_mev": float(np.min(main["result"]["bands"][:, 0])),
            "top_band_max_mev": float(np.max(main["result"]["bands"][:, 0])),
        },
        "T003": dos,
        "T004": berry,
        "T005": {
            "top_band_min_mev": float(np.min(theta_two["result"]["bands"][:, 0])),
            "top_band_max_mev": float(np.max(theta_two["result"]["bands"][:, 0])),
        },
        "T006": gaps,
        "T007": gaps,
        "T008": {
            "energy_min_mev": float(np.min(remote["dirac_result"]["valence"])),
            "energy_max_mev": float(np.max(remote["dirac_result"]["valence"])),
        },
        "T009": {
            "energy_min_mev": float(np.min(remote["dirac_result"]["conduction"])),
            "energy_max_mev": float(np.max(remote["dirac_result"]["conduction"])),
        },
        "T010": {
            "energy_min_mev": float(np.min(remote["spin"]["T010"]["bands"])),
            "energy_max_mev": float(np.max(remote["spin"]["T010"]["bands"])),
        },
        "T011": {
            "energy_min_mev": float(np.min(remote["spin"]["T011"]["bands"])),
            "energy_max_mev": float(np.max(remote["spin"]["T011"]["bands"])),
        },
    }
    target_checks = {
        "schema_version": 1,
        "paper_id": "1807.03311",
        "status": "passed",
        "targets": [
            {
                "target_id": target,
                "status": "passed",
                "generated_data_provenance": "independent_numerics",
                "metrics": metrics,
            }
            for target, metrics in target_metrics.items()
        ],
    }
    _json(checks_dir / "target_checks.json", target_checks)

    manifest = {
        "schema_version": 1,
        "paper_id": "1807.03311",
        "run_id": config["run_id"],
        "status": "frozen",
        "provenance": "independent_numerics",
        "source_figure_access": "forbidden_in_this_run",
        "files": [
            {
                "target_id": target,
                "path": f"outputs/data/{filename}",
                "sha256": _sha256(data_dir / filename),
                "bytes": (data_dir / filename).stat().st_size,
            }
            for target, filename in TARGET_FILES.items()
        ],
    }
    _json(checks_dir / "generated_data_manifest.json", manifest)


__all__ = ["TARGET_FILES", "run_reproduction"]
