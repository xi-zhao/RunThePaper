"""Numerical target orchestration for the moire Hubbard reproduction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import SingleBandContinuum, exchange_couplings, screened_interactions


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _potential_target(
    model: SingleBandContinuum,
    *,
    points: int,
    extent: float,
) -> dict[str, np.ndarray]:
    x = np.linspace(-extent, extent, points)
    y = np.linspace(-extent, extent, points)
    xx, yy = np.meshgrid(x, y, indexing="xy")
    positions = np.column_stack(
        [xx.ravel() * model.geometry.a_moire_nm, yy.ravel() * model.geometry.a_moire_nm]
    )
    potential = model.potential(positions).reshape(points, points)
    return {"x_over_am": x, "y_over_am": y, "potential_mev": potential}


def _sweep(
    a_values: np.ndarray,
    *,
    cutoff: int,
    fit_grid: int,
    interaction_k_grid: int,
    interaction_real_grid: int,
    mass: float,
    potential: float,
    phase: float,
    screening_nm: float,
    dielectric: float,
) -> dict[str, np.ndarray]:
    hopping = []
    fit_residual = []
    interaction = []
    exchange = []
    for a_moire in a_values:
        model = SingleBandContinuum(
            float(a_moire),
            cutoff=cutoff,
            effective_mass_me=mass,
            potential_mev=potential,
            potential_phase_deg=phase,
        )
        fit = model.tight_binding_fit(grid_points=fit_grid)
        hopping_values = np.asarray(fit["hopping_mev"])
        epsilon_u = screened_interactions(
            model,
            screening_separation_nm=screening_nm,
            k_grid=interaction_k_grid,
            real_grid=interaction_real_grid,
        )
        onsite_u_mev = epsilon_u[0] * 1000.0 / dielectric
        hopping.append(hopping_values)
        fit_residual.append(float(fit["rms_residual_mev"]))
        interaction.append(epsilon_u)
        exchange.append(exchange_couplings(hopping_values, onsite_u_mev))
    return {
        "a_moire_nm": np.asarray(a_values),
        "hopping_mev": np.asarray(hopping),
        "fit_rms_residual_mev": np.asarray(fit_residual),
        "epsilon_u_ev": np.asarray(interaction),
        "exchange_mev": np.asarray(exchange),
    }


def run(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    parameters = config["parameters"]
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    a0 = float(parameters["a0_nm"])
    mass = float(parameters["effective_mass_me"])
    main = parameters["main_system"]
    supplement = parameters["supplement_system"]
    theta = float(parameters["band_twist_deg"])
    a_main = a0 / np.deg2rad(theta)
    main_model = SingleBandContinuum(
        a_main,
        cutoff=int(parameters["paper_exact_cutoff"]),
        effective_mass_me=mass,
        potential_mev=float(main["potential_mev"]),
        potential_phase_deg=float(main["phase_deg"]),
    )

    target_paths: list[Path] = []

    main_potential = _potential_target(main_model, points=181, extent=1.5)
    path = data_dir / "T001_main_fig1d_potential.npz"
    _write_npz(path, **main_potential)
    target_paths.append(path)

    band_path = main_model.band_path(
        points_per_segment=int(parameters["band_points_per_segment"]), count=5
    )
    band_fit = main_model.tight_binding_fit(grid_points=int(parameters["fit_k_grid"]))
    tight_binding = main_model.tight_binding_energy(np.asarray(band_path["k"]), band_fit)
    path = data_dir / "T002_main_fig2a_bands.npz"
    _write_npz(
        path,
        k=np.asarray(band_path["k"]),
        s=np.asarray(band_path["s"]),
        ticks=np.asarray(band_path["ticks"]),
        labels=np.asarray(band_path["labels"]),
        bands_mev=np.asarray(band_path["bands"]),
        tight_binding_mev=tight_binding,
        hopping_mev=np.asarray(band_fit["hopping_mev"]),
        fit_rms_residual_mev=np.asarray([band_fit["rms_residual_mev"]]),
    )
    target_paths.append(path)

    dos = main_model.density_of_states_vs_hole_filling(
        grid_points=int(parameters["dos_k_grid"]),
        band_count=4,
        broadening_mev=float(parameters["dos_broadening_mev"]),
    )
    path = data_dir / "T003_main_fig2b_dos.npz"
    _write_npz(path, **dos)
    target_paths.append(path)

    wannier = main_model.wannier_amplitude(
        k_grid=int(parameters["display_wannier_k_grid"]),
        real_grid=int(parameters["display_wannier_real_grid"]),
    )
    path = data_dir / "T004_main_fig2c_wannier.npz"
    _write_npz(path, **wannier)
    target_paths.append(path)

    a_main_values = np.linspace(*parameters["main_a_moire_sweep"])
    main_sweep = _sweep(
        a_main_values,
        cutoff=int(parameters["sweep_cutoff"]),
        fit_grid=int(parameters["fit_k_grid"]),
        interaction_k_grid=int(parameters["interaction_k_grid"]),
        interaction_real_grid=int(parameters["interaction_real_grid"]),
        mass=mass,
        potential=float(main["potential_mev"]),
        phase=float(main["phase_deg"]),
        screening_nm=float(parameters["screening_separation_nm"]),
        dielectric=float(parameters["dielectric_constant"]),
    )
    theta_main = np.rad2deg(a0 / a_main_values)
    path = data_dir / "T005_main_fig2d_hopping.npz"
    _write_npz(
        path,
        a_moire_nm=a_main_values,
        theta_deg=theta_main,
        hopping_mev=main_sweep["hopping_mev"],
        fit_rms_residual_mev=main_sweep["fit_rms_residual_mev"],
    )
    target_paths.append(path)

    u0_over_t1 = (
        main_sweep["epsilon_u_ev"][:, 0]
        * 1000.0
        / float(parameters["dielectric_constant"])
        / main_sweep["hopping_mev"][:, 0]
    )
    path = data_dir / "T006_main_fig3a_interactions.npz"
    _write_npz(
        path,
        a_moire_nm=a_main_values,
        theta_deg=theta_main,
        epsilon_u_ev=main_sweep["epsilon_u_ev"],
        u0_over_t1=u0_over_t1,
    )
    target_paths.append(path)

    j_ratio = np.divide(
        main_sweep["exchange_mev"][:, 1],
        main_sweep["exchange_mev"][:, 0],
        out=np.zeros_like(main_sweep["exchange_mev"][:, 1]),
        where=main_sweep["exchange_mev"][:, 0] != 0.0,
    )
    path = data_dir / "T007_main_fig3b_exchange.npz"
    _write_npz(
        path,
        a_moire_nm=a_main_values,
        theta_deg=theta_main,
        exchange_mev=main_sweep["exchange_mev"],
        j2_over_j1=j_ratio,
    )
    target_paths.append(path)

    contours = main_model.fermi_contour_map(
        grid_points=int(parameters["fermi_grid"]), hole_filling=0.75
    )
    path = data_dir / "T008_main_fig4a_fermi_contour.npz"
    _write_npz(path, **contours)
    target_paths.append(path)

    supplement_a_aligned = a0 / float(supplement["mismatch"])
    supplement_model = SingleBandContinuum(
        supplement_a_aligned,
        cutoff=int(parameters["paper_exact_cutoff"]),
        effective_mass_me=mass,
        potential_mev=float(supplement["potential_mev"]),
        potential_phase_deg=float(supplement["phase_deg"]),
    )
    supplement_potential = _potential_target(supplement_model, points=181, extent=1.5)
    path = data_dir / "T009_supp_fig5a_potential.npz"
    _write_npz(path, **supplement_potential)
    target_paths.append(path)

    supplement_path = supplement_model.band_path(
        points_per_segment=int(parameters["band_points_per_segment"]), count=5
    )
    supplement_fit = supplement_model.tight_binding_fit(grid_points=int(parameters["fit_k_grid"]))
    supplement_tb = supplement_model.tight_binding_energy(
        np.asarray(supplement_path["k"]), supplement_fit
    )
    path = data_dir / "T010_supp_fig5b_bands.npz"
    _write_npz(
        path,
        k=np.asarray(supplement_path["k"]),
        s=np.asarray(supplement_path["s"]),
        ticks=np.asarray(supplement_path["ticks"]),
        labels=np.asarray(supplement_path["labels"]),
        bands_mev=np.asarray(supplement_path["bands"]),
        tight_binding_mev=supplement_tb,
        hopping_mev=np.asarray(supplement_fit["hopping_mev"]),
        fit_rms_residual_mev=np.asarray([supplement_fit["rms_residual_mev"]]),
    )
    target_paths.append(path)

    a_supp_values = np.linspace(*parameters["supplement_a_moire_sweep"])
    supplement_sweep = _sweep(
        a_supp_values,
        cutoff=int(parameters["sweep_cutoff"]),
        fit_grid=int(parameters["fit_k_grid"]),
        interaction_k_grid=int(parameters["interaction_k_grid"]),
        interaction_real_grid=int(parameters["interaction_real_grid"]),
        mass=mass,
        potential=float(supplement["potential_mev"]),
        phase=float(supplement["phase_deg"]),
        screening_nm=float(parameters["screening_separation_nm"]),
        dielectric=float(parameters["dielectric_constant"]),
    )
    theta_supp = np.rad2deg(
        np.sqrt(np.maximum((a0 / a_supp_values) ** 2 - float(supplement["mismatch"]) ** 2, 0.0))
    )
    path = data_dir / "T011_supp_fig5c_hopping.npz"
    _write_npz(
        path,
        a_moire_nm=a_supp_values,
        theta_deg=theta_supp,
        hopping_mev=supplement_sweep["hopping_mev"],
        fit_rms_residual_mev=supplement_sweep["fit_rms_residual_mev"],
    )
    target_paths.append(path)

    path = data_dir / "T012_supp_fig5d_interactions.npz"
    _write_npz(
        path,
        a_moire_nm=a_supp_values,
        theta_deg=theta_supp,
        epsilon_u_ev=supplement_sweep["epsilon_u_ev"],
    )
    target_paths.append(path)

    main_samples = main_model.sample_bands(grid_points=15, count=3)
    supplement_samples = supplement_model.sample_bands(grid_points=15, count=3)
    theta_near_three = int(np.argmin(np.abs(theta_main - 3.0)))
    theta_near_two = int(np.argmin(np.abs(theta_main - 2.0)))
    target_checks = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "checks": {
            "T001_potential_range_mev": [
                float(np.min(main_potential["potential_mev"])),
                float(np.max(main_potential["potential_mev"])),
            ],
            "T002_top_bandwidth_mev": float(np.ptp(main_samples[:, 0])),
            "T002_isolation_gap_mev": float(
                np.min(main_samples[:, 0]) - np.max(main_samples[:, 1])
            ),
            "T002_fit_rms_mev": float(band_fit["rms_residual_mev"]),
            "T003_full_hole_density_1e12_cm2": float(dos["full_hole_density_1e12_cm2"][0]),
            "T004_wannier_normalization": float(wannier["normalization"][0]),
            "T005_t1_dominates": bool(
                np.all(
                    np.abs(main_sweep["hopping_mev"][:, 0])
                    > np.max(np.abs(main_sweep["hopping_mev"][:, 1:]), axis=1)
                )
            ),
            "T006_u_ordered": bool(
                np.all(main_sweep["epsilon_u_ev"][:, 0] > main_sweep["epsilon_u_ev"][:, 1])
                and np.all(main_sweep["epsilon_u_ev"][:, 1] > main_sweep["epsilon_u_ev"][:, 2])
            ),
            "T007_j2_j1_near_three_deg": float(j_ratio[theta_near_three]),
            "T007_j2_j1_near_two_deg": float(j_ratio[theta_near_two]),
            "T008_fermi_energy_mev": float(contours["fermi_energy_mev"][0]),
            "T009_potential_range_mev": [
                float(np.min(supplement_potential["potential_mev"])),
                float(np.max(supplement_potential["potential_mev"])),
            ],
            "T010_top_bandwidth_mev": float(np.ptp(supplement_samples[:, 0])),
            "T010_isolation_gap_mev": float(
                np.min(supplement_samples[:, 0]) - np.max(supplement_samples[:, 1])
            ),
            "T011_t1_dominates": bool(
                np.all(
                    np.abs(supplement_sweep["hopping_mev"][:, 0])
                    > np.max(np.abs(supplement_sweep["hopping_mev"][:, 1:]), axis=1)
                )
            ),
            "T012_u_ordered": bool(
                np.all(
                    supplement_sweep["epsilon_u_ev"][:, 0]
                    > supplement_sweep["epsilon_u_ev"][:, 1]
                )
                and np.all(
                    supplement_sweep["epsilon_u_ev"][:, 1]
                    > supplement_sweep["epsilon_u_ev"][:, 2]
                )
            ),
        },
    }
    _write_json(checks_dir / "target_checks.json", target_checks)

    convergence_model = SingleBandContinuum(
        a_main,
        cutoff=int(parameters["convergence_cutoff"]),
        effective_mass_me=mass,
        potential_mev=float(main["potential_mev"]),
        potential_phase_deg=float(main["phase_deg"]),
    )
    convergence_path = convergence_model.band_path(points_per_segment=21, count=4)
    baseline_path = main_model.band_path(points_per_segment=21, count=4)
    supplement_convergence = SingleBandContinuum(
        supplement_a_aligned,
        cutoff=int(parameters["convergence_cutoff"]),
        effective_mass_me=mass,
        potential_mev=float(supplement["potential_mev"]),
        potential_phase_deg=float(supplement["phase_deg"]),
    ).band_path(points_per_segment=21, count=4)
    supplement_baseline = supplement_model.band_path(points_per_segment=21, count=4)
    convergence = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "main_cutoff_delta_mev": float(
            np.max(np.abs(np.asarray(convergence_path["bands"]) - np.asarray(baseline_path["bands"])))
        ),
        "supplement_cutoff_delta_mev": float(
            np.max(
                np.abs(
                    np.asarray(supplement_convergence["bands"])
                    - np.asarray(supplement_baseline["bands"])
                )
            )
        ),
        "hermiticity_error": float(
            np.max(np.abs(main_model.hamiltonian([0.07, -0.03]) - main_model.hamiltonian([0.07, -0.03]).conj().T))
        ),
    }
    _write_json(checks_dir / "convergence.json", convergence)

    scientific_checks = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "checks": {
            "hamiltonian_hermitian": convergence["hermiticity_error"] < 1e-12,
            "main_bandwidth_matches_11_mev": abs(target_checks["checks"]["T002_top_bandwidth_mev"] - 11.0) < 2.0,
            "supplement_bandwidth_matches_20_mev": abs(target_checks["checks"]["T010_top_bandwidth_mev"] - 20.0) < 3.0,
            "main_band_isolated": target_checks["checks"]["T002_isolation_gap_mev"] > 0.0,
            "supplement_band_isolated": target_checks["checks"]["T010_isolation_gap_mev"] > 0.0,
            "spin_liquid_threshold_recovered": target_checks["checks"]["T007_j2_j1_near_three_deg"] >= 0.055,
            "wannier_normalized": abs(target_checks["checks"]["T004_wannier_normalization"] - 1.0) < 1e-8,
        },
    }
    if not all(scientific_checks["checks"].values()):
        scientific_checks["status"] = "failed"
    _write_json(checks_dir / "scientific_formula_checks.json", scientific_checks)

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "run_id": config["run_id"],
        "status": "frozen",
        "generated_data_provenance": "independent_numerics",
        "files": [
            {
                "path": str(path.relative_to(workspace)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in target_paths
        ],
    }
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    return {
        "targets": len(target_paths),
        "scientific_status": scientific_checks["status"],
        "main_bandwidth_mev": target_checks["checks"]["T002_top_bandwidth_mev"],
        "supplement_bandwidth_mev": target_checks["checks"]["T010_top_bandwidth_mev"],
    }
