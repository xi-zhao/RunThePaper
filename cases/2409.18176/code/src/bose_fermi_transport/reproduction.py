"""Generate all ten formula-derived numerical targets."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from .collocation import solve_collocation
from .hydrodynamic import (
    HydroParameters,
    conductivities_closed,
    conductivities_direct,
    conductivities_printed_closed,
)
from .kinetic import GridSpec, TransportResult, solve_transport, solve_transport_sweep
from .kubo import kubo_resistivity
from .phonons import phonon_resistivity
from .rendering import render_all
from .scattering import scattering_amplitude
from .thermodynamics import ModelParameters, solve_equilibrium


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _model(payload: dict[str, Any]) -> ModelParameters:
    return ModelParameters(
        fermi_energy_mev=float(payload["fermi_energy_mev"]),
        trion_binding_mev=float(payload["trion_binding_mev"]),
        hole_mass_me=float(payload["hole_mass_me"]),
        exciton_mass_ratio_to_hole=float(payload["exciton_mass_ratio_to_hole"]),
        exciton_density_cm2=float(payload["exciton_density_cm2"]),
        relaxation_time_ps=float(payload["relaxation_time_ps"]),
    )


def _grid(payload: dict[str, Any]) -> GridSpec:
    return GridSpec(**payload)


def _hydro(payload: dict[str, Any]) -> HydroParameters:
    return HydroParameters(**payload)


def _result_row(result: TransportResult) -> dict[str, float | int]:
    return {
        "sigma_h_real": result.sigma_h.real,
        "sigma_h_imag": result.sigma_h.imag,
        "sigma_x_real": result.sigma_x.real,
        "sigma_x_imag": result.sigma_x.imag,
        "sigma_t_real": result.sigma_t.real,
        "sigma_t_imag": result.sigma_t.imag,
        "event_count": result.event_count,
        "momentum_residual": result.collision_momentum_residual,
        "collision_min_eigenvalue": result.collision_min_eigenvalue,
        "condition_number": result.condition_number,
    }


def run(config_path: Path, workspace: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    p = config["parameters"]
    model = _model(p)
    grid = _grid(p["grid"])
    closure = str(p["closure"])
    data_dir = workspace / "outputs" / "data"
    figure_dir = workspace / "outputs" / "figures"
    check_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)

    # T001: both source-labelled scattering conventions, without pixel fitting.
    scattering = p["scattering"]
    energies = np.linspace(
        scattering["energy_min_mev"], scattering["energy_max_mev"], scattering["points"]
    )
    resonance = scattering["detuning_mev"] + model.trion_binding_mev
    rows_t001: list[dict[str, Any]] = []
    for convention in ("logarithmic", "caption_pole", "printed_pole"):
        amplitude = scattering_amplitude(
            energies,
            scattering["detuning_mev"],
            model.trion_binding_mev,
            scattering["tunnel_mev"],
            convention,
            scattering["linewidth_mev"],
        )
        for energy, value in zip(energies, amplitude, strict=True):
            rows_t001.append(
                {
                    "convention": convention,
                    "energy_mev": energy,
                    "energy_over_resonance": energy / resonance,
                    "amplitude_real": value.real,
                    "amplitude_imag": value.imag,
                    "amplitude_abs": abs(value),
                }
            )
    write_csv(data_dir / "T001_scattering_amplitude.csv", rows_t001)

    detunings = np.linspace(
        p["detuning_ratio_min"], p["detuning_ratio_max"], p["detuning_points"]
    )
    transport_cache: dict[tuple[float, float, float, float], TransportResult] = {}

    def transport(
        density: float, tunnel: float, ratio: float, temperature: float
    ) -> TransportResult:
        key = (density, tunnel, ratio, temperature)
        if key not in transport_cache:
            local_model = replace(model, exciton_density_cm2=density)
            equilibrium = solve_equilibrium(
                local_model, temperature, ratio * local_model.fermi_energy_mev, closure
            )
            transport_cache[key] = solve_transport(
                local_model, equilibrium, tunnel, 0.0, grid
            )
        return transport_cache[key]

    # T002: four tunnel/density combinations.
    rows_t002: list[dict[str, Any]] = []
    for density in p["exciton_density_values_cm2"]:
        for tunnel in (0.5, 1.0):
            for ratio in detunings:
                result = transport(
                    float(density), tunnel, float(ratio), float(p["temperature_k"])
                )
                rows_t002.append(
                    {
                        "detuning_over_ef": ratio,
                        "tunnel_mev": tunnel,
                        "exciton_density_cm2": density,
                        "rho_over_rho0": 1.0 / result.sigma_h.real,
                        **_result_row(result),
                    }
                )
    write_csv(data_dir / "T002_hole_resistivity.csv", rows_t002)

    # T003 and T010 share the same independently solved transport states.
    rows_t003: list[dict[str, Any]] = []
    rows_t010: list[dict[str, Any]] = []
    default_density = float(p["exciton_density_cm2"])
    for tunnel in p["tunnel_values_mev"]:
        for ratio in detunings:
            result = transport(
                default_density, float(tunnel), float(ratio), float(p["temperature_k"])
            )
            common = {
                "detuning_over_ef": ratio,
                "tunnel_mev": tunnel,
                **_result_row(result),
            }
            rows_t003.append({**common, "sigma_x_over_sigma0": result.sigma_x.real})
            rows_t010.append({**common, "sigma_t_over_sigma0": result.sigma_t.real})
    write_csv(data_dir / "T003_exciton_drag.csv", rows_t003)
    write_csv(data_dir / "T010_trion_drag.csv", rows_t010)

    # T004 and T005: temperature lanes.
    temperatures = np.linspace(
        p["temperature_min_k"], p["temperature_max_k"], p["temperature_points"]
    )
    rows_t004: list[dict[str, Any]] = []
    by_temperature_07: dict[float, float] = {}
    for ratio in p["temperature_detuning_ratios"]:
        for temperature in temperatures:
            result = transport(default_density, 1.0, float(ratio), float(temperature))
            many_body = 1.0 / result.sigma_h.real - 1.0
            rows_t004.append(
                {
                    "temperature_k": temperature,
                    "detuning_over_ef": ratio,
                    "many_body_rho_over_rho0": many_body,
                    "rho_over_rho0": 1.0 + many_body,
                    **_result_row(result),
                }
            )
            if abs(float(ratio) - 0.7) < 1.0e-12:
                by_temperature_07[float(temperature)] = 1.0 + many_body
    write_csv(data_dir / "T004_temperature_resistivity.csv", rows_t004)
    phonon = phonon_resistivity(
        temperatures,
        p["phonon"]["bloch_gruneisen_k"],
        p["phonon"]["high_temperature_slope_per_k"],
        p["phonon"]["crossover_power"],
    )
    rows_t005: list[dict[str, Any]] = []
    for temperature, phonon_value in zip(temperatures, phonon, strict=True):
        many_body_total = by_temperature_07[float(temperature)]
        rows_t005.extend(
            [
                {
                    "temperature_k": temperature,
                    "contribution": "many_body",
                    "rho_over_rho0": many_body_total,
                },
                {
                    "temperature_k": temperature,
                    "contribution": "phonon",
                    "rho_over_rho0": phonon_value,
                },
                {
                    "temperature_k": temperature,
                    "contribution": "total",
                    "rho_over_rho0": many_body_total + phonon_value,
                },
            ]
        )
    write_csv(data_dir / "T005_total_resistivity.csv", rows_t005)

    # T006-T008: one kinetic frequency sweep plus direct and closed hydrodynamics.
    frequencies = np.linspace(
        p["frequency_min_mev"], p["frequency_max_mev"], p["frequency_points"]
    )
    ac_equilibrium = solve_equilibrium(
        model,
        p["temperature_k"],
        p["ac_detuning_ratio"] * model.fermi_energy_mev,
        closure,
    )
    kinetic_ac = solve_transport_sweep(model, ac_equilibrium, 1.0, frequencies, grid)
    hydro_params = _hydro(p["hydrodynamic"])
    hydro_direct = conductivities_direct(
        frequencies, model, ac_equilibrium, hydro_params
    )
    hydro_closed = conductivities_closed(
        frequencies, model, ac_equilibrium, hydro_params
    )
    hydro_printed = conductivities_printed_closed(
        frequencies, model, ac_equilibrium, hydro_params
    )
    for target, species_index, filename in (
        ("T006", 0, "T006_ac_hole.csv"),
        ("T007", 1, "T007_ac_exciton.csv"),
        ("T008", 2, "T008_ac_trion.csv"),
    ):
        rows_ac: list[dict[str, Any]] = []
        for frequency, kinetic_result, direct, closed, printed in zip(
            frequencies,
            kinetic_ac,
            hydro_direct[:, species_index],
            hydro_closed[:, species_index],
            hydro_printed[:, species_index],
            strict=True,
        ):
            kinetic_value = (
                kinetic_result.sigma_h,
                kinetic_result.sigma_x,
                kinetic_result.sigma_t,
            )[species_index]
            rows_ac.append(
                {
                    "target_id": target,
                    "frequency_mev": frequency,
                    "kinetic_real": kinetic_value.real,
                    "kinetic_imag": kinetic_value.imag,
                    "hydro_real": direct.real,
                    "hydro_imag": direct.imag,
                    "hydro_closed_real": closed.real,
                    "hydro_closed_imag": closed.imag,
                    "printed_closed_real": printed.real,
                    "printed_closed_imag": printed.imag,
                }
            )
        write_csv(data_dir / filename, rows_ac)

    # T009: independent broadened Kubo lane against the coupled solution.
    rows_t009: list[dict[str, Any]] = []
    kubo_config = p["kubo"]
    for density in p["exciton_density_values_cm2"]:
        local_model = replace(model, exciton_density_cm2=float(density))
        for ratio in detunings:
            result = transport(
                float(density), 1.0, float(ratio), float(p["temperature_k"])
            )
            equilibrium = solve_equilibrium(
                local_model,
                p["temperature_k"],
                float(ratio) * local_model.fermi_energy_mev,
                closure,
            )
            rho_kubo = kubo_resistivity(
                local_model,
                equilibrium,
                1.0,
                hole_points=int(kubo_config["hole_points"]),
                hole_max_pf=float(kubo_config["hole_max_pf"]),
                exciton_points=int(kubo_config["exciton_points"]),
                exciton_max_pf=float(kubo_config["exciton_max_pf"]),
                angle_points=int(kubo_config["angle_points"]),
                broadening_mev=float(kubo_config["broadening_mev"]),
            )
            rho_boltzmann = 1.0 / result.sigma_h.real
            rows_t009.append(
                {
                    "detuning_over_ef": ratio,
                    "exciton_density_cm2": density,
                    "rho_kubo": rho_kubo,
                    "rho_boltzmann": rho_boltzmann,
                    "rho_kubo_minus_boltzmann": rho_kubo - rho_boltzmann,
                }
            )
    write_csv(data_dir / "T009_kubo_difference.csv", rows_t009)

    render_all(data_dir, figure_dir)

    # Machine assertions report evidence; they never promote parameter status.
    t002_default = [
        row
        for row in rows_t002
        if float(row["tunnel_mev"]) == 1.0
        and float(row["exciton_density_cm2"]) == default_density
    ]
    peak_row = max(t002_default, key=lambda row: float(row["rho_over_rho0"]))
    t003_t1 = [row for row in rows_t003 if float(row["tunnel_mev"]) == 1.0]
    hydro_parity = float(np.max(np.abs(hydro_direct - hydro_closed)))
    printed_discrepancy = float(np.max(np.abs(hydro_direct - hydro_printed)))
    kinetic_ac_array = np.array(
        [[result.sigma_h, result.sigma_x, result.sigma_t] for result in kinetic_ac],
        dtype=complex,
    )
    kinetic_hydro_gaps = np.max(np.abs(kinetic_ac_array - hydro_direct), axis=0)
    max_kubo_gap = max(abs(float(row["rho_kubo_minus_boltzmann"])) for row in rows_t009)
    anchor_galerkin = kinetic_ac[int(np.argmin(np.abs(frequencies)))]
    anchor_collocation = solve_collocation(model, ac_equilibrium, 1.0, 0.0, grid)
    minimum_collision_eigenvalue = min(
        result.collision_min_eigenvalue for result in transport_cache.values()
    )
    maximum_momentum_residual = max(
        result.collision_momentum_residual for result in transport_cache.values()
    )
    assertions = {
        "T001": {
            "passed": bool(
                np.isfinite([row["amplitude_abs"] for row in rows_t001]).all()
            ),
            "parameter_status": "proxy_model",
        },
        "T002": {
            "passed": abs(float(peak_row["detuning_over_ef"]) - 2.0 / 3.0) <= 0.2,
            "completion_status": "pending_paper_scale_quantitative_convergence",
            "peak_detuning_over_ef": peak_row["detuning_over_ef"],
            "peak_rho_over_rho0": peak_row["rho_over_rho0"],
            "parameter_status": "reconstructed_model",
        },
        "T003": {
            "passed": min(float(row["sigma_x_over_sigma0"]) for row in t003_t1)
            < 0.0
            < max(float(row["sigma_x_over_sigma0"]) for row in t003_t1),
            "parameter_status": "reconstructed_model",
        },
        "T004": {
            "passed": all(
                np.isfinite(float(row["many_body_rho_over_rho0"])) for row in rows_t004
            ),
            "parameter_status": "reconstructed_model",
        },
        "T005": {
            "passed": float(phonon[-1]) > float(phonon[0]) >= 0.0,
            "parameter_status": "proxy_model",
        },
        "T006": {
            "passed": hydro_parity < 1.0e-12 and float(kinetic_hydro_gaps[0]) < 0.1,
            "completion_status": "pending_missing_fit_operating_densities",
            "analytic_three_fluid_passed": hydro_parity < 1.0e-12,
            "kinetic_vs_fit_max_abs": float(kinetic_hydro_gaps[0]),
            "parameter_status": "reconstructed_model",
        },
        "T007": {
            "passed": hydro_parity < 1.0e-12 and float(kinetic_hydro_gaps[1]) < 0.1,
            "completion_status": "pending_missing_fit_operating_densities",
            "analytic_three_fluid_passed": hydro_parity < 1.0e-12,
            "kinetic_vs_fit_max_abs": float(kinetic_hydro_gaps[1]),
            "parameter_status": "reconstructed_model",
        },
        "T008": {
            "passed": hydro_parity < 1.0e-12 and float(kinetic_hydro_gaps[2]) < 0.1,
            "completion_status": "pending_missing_fit_operating_densities",
            "analytic_three_fluid_passed": hydro_parity < 1.0e-12,
            "kinetic_vs_fit_max_abs": float(kinetic_hydro_gaps[2]),
            "parameter_status": "reconstructed_model",
        },
        "T009": {
            "passed": max_kubo_gap <= 0.1,
            "completion_status": "pending_paper_scale_method_convergence",
            "max_abs_difference": max_kubo_gap,
            "paper_claimed_scale": "a few percent of rho_0^h",
            "parameter_status": "reconstructed_model",
        },
        "T010": {
            "passed": max(float(row["sigma_t_over_sigma0"]) for row in rows_t010) > 0.0,
            "parameter_status": "reconstructed_model",
        },
    }
    checks = {
        "schema_version": 1,
        "paper_id": "2409.18176",
        "profile": config["profile"],
        "artifact_stage": config["artifact_stage"],
        "assertions": assertions,
        "all_assertions_passed": all(item["passed"] for item in assertions.values()),
        "physics": {
            "hydrodynamic_direct_vs_corrected_closed_max_abs": hydro_parity,
            "hydrodynamic_direct_vs_literal_printed_max_abs": printed_discrepancy,
            "collision_min_eigenvalue": minimum_collision_eigenvalue,
            "collision_momentum_residual_max": maximum_momentum_residual,
            "anchor_collocation_vs_galerkin": {
                "sigma_h_abs": abs(
                    anchor_collocation.sigma_h - anchor_galerkin.sigma_h
                ),
                "sigma_x_abs": abs(
                    anchor_collocation.sigma_x - anchor_galerkin.sigma_x
                ),
                "sigma_t_abs": abs(
                    anchor_collocation.sigma_t - anchor_galerkin.sigma_t
                ),
            },
            "literal_closed_form_discrepancy_classification": "inconclusive",
            "kubo_boltzmann_discrepancy_classification": "pending_method_convergence",
            "paper_error_candidate_emitted": False,
        },
        "source_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
            "zenodo_opened": False,
        },
    }
    checks_path = check_dir / "target_checks.json"
    checks_path.write_text(
        json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    output_paths = (
        sorted(data_dir.glob("*.csv"))
        + sorted(figure_dir.glob("*.png"))
        + [checks_path]
    )
    manifest = {
        "schema_version": 1,
        "paper_id": "2409.18176",
        "config": str(config_path.relative_to(workspace)),
        "config_sha256": sha256(config_path),
        "model_parameters": asdict(model),
        "outputs": [
            {
                "path": str(path.relative_to(workspace)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in output_paths
        ],
    }
    manifest_path = check_dir / "generated_data_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"checks": checks, "manifest": manifest}
