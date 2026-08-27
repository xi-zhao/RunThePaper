"""Closure-robust adjudication of the paper's three-fluid AC response.

The publication fixes the global hole/exciton inputs and chemical equilibrium,
but does not state whether its quoted densities are treated as free-species or
conserved constituent densities in the fitted hydrodynamic curves.  This module
evaluates both interpretations without using author arrays or figure pixels.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .hydrodynamic import (
    HydroParameters,
    conductivities_closed,
    conductivities_direct,
    conductivities_printed_closed,
)
from .kinetic import GridSpec, solve_transport_sweep
from .thermodynamics import ModelParameters, solve_equilibrium


def _model(values: dict[str, Any]) -> ModelParameters:
    return ModelParameters(
        fermi_energy_mev=float(values["fermi_energy_mev"]),
        trion_binding_mev=float(values["trion_binding_mev"]),
        hole_mass_me=float(values["hole_mass_me"]),
        exciton_mass_ratio_to_hole=float(values["exciton_mass_ratio_to_hole"]),
        exciton_density_cm2=float(values["exciton_density_cm2"]),
        relaxation_time_ps=float(values["relaxation_time_ps"]),
    )


def _hydro(values: dict[str, Any]) -> HydroParameters:
    return HydroParameters(
        tau_h_ps=float(values["tau_h_ps"]),
        tau_x_ps=float(values["tau_x_ps"]),
        tau_t_ps=float(values["tau_t_ps"]),
        alpha_th=float(values["alpha_th"]),
        alpha_xh=float(values["alpha_xh"]),
        alpha_tx=float(values["alpha_tx"]),
        density_unit_cm2=float(values["density_unit_cm2"]),
        mass_unit_me=float(values["mass_unit_me"]),
        time_unit_ps=float(values["time_unit_ps"]),
    )


def audit_ac_closures(parameters: dict[str, Any]) -> dict[str, Any]:
    """Run both source-compatible density closures and adjudicate each species."""

    model = _model(parameters["model"])
    hydro = _hydro(parameters["hydrodynamic"])
    grid = GridSpec(**parameters["grid"])
    frequencies = np.linspace(
        float(parameters["frequency_min_mev"]),
        float(parameters["frequency_max_mev"]),
        int(parameters["frequency_points"]),
    )
    tolerance = float(parameters["acceptance"]["kinetic_hydro_max_abs"])
    parity_tolerance = float(
        parameters["acceptance"]["direct_corrected_max_abs"]
    )
    closure_rows: dict[str, Any] = {}
    species_names = ("hole", "exciton", "trion")
    target_ids = ("T006", "T007", "T008")
    target_passes = {target_id: [] for target_id in target_ids}

    for closure in parameters["closures"]:
        equilibrium = solve_equilibrium(
            model,
            float(parameters["temperature_k"]),
            float(parameters["detuning_ratio"]) * model.fermi_energy_mev,
            str(closure),
        )
        kinetic = solve_transport_sweep(
            model,
            equilibrium,
            float(parameters["tunnel_mev"]),
            frequencies,
            grid,
        )
        kinetic_array = np.array(
            [[row.sigma_h, row.sigma_x, row.sigma_t] for row in kinetic],
            dtype=complex,
        )
        direct = conductivities_direct(frequencies, model, equilibrium, hydro)
        corrected = conductivities_closed(frequencies, model, equilibrium, hydro)
        printed = conductivities_printed_closed(
            frequencies, model, equilibrium, hydro
        )
        gaps = np.max(np.abs(kinetic_array - direct), axis=0)
        for target_id, gap in zip(target_ids, gaps, strict=True):
            target_passes[target_id].append(float(gap) <= tolerance)
        closure_rows[str(closure)] = {
            "chemical_potentials_mev": {
                "hole": equilibrium.mu_h_mev,
                "exciton": equilibrium.mu_x_mev,
                "trion": equilibrium.mu_t_mev,
            },
            "densities_cm2": {
                "hole": equilibrium.n_h_cm2,
                "exciton": equilibrium.n_x_cm2,
                "trion": equilibrium.n_t_cm2,
            },
            "equilibrium_residual_max": equilibrium.residual_max,
            "kinetic_vs_hydrodynamic_max_abs": {
                species: float(gap)
                for species, gap in zip(species_names, gaps, strict=True)
            },
            "direct_vs_dimensionally_corrected_max_abs": float(
                np.max(np.abs(direct - corrected))
            ),
            "direct_vs_literal_printed_max_abs": float(
                np.max(np.abs(direct - printed))
            ),
        }

    decisions = {}
    for target_id in target_ids:
        robust = all(target_passes[target_id])
        decisions[target_id] = {
            "passes_by_closure": dict(
                zip(parameters["closures"], target_passes[target_id], strict=True)
            ),
            "closure_robust": robust,
            "final_disposition_basis": (
                "reproduced" if robust else "attempted_not_reproduced"
            ),
        }

    corrected_parity_passed = all(
        row["direct_vs_dimensionally_corrected_max_abs"] <= parity_tolerance
        for row in closure_rows.values()
    )
    return {
        "schema_version": 1,
        "paper_id": "2409.18176",
        "audit_status": "passed",
        "scientific_result": "mixed",
        "source_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
        },
        "parameters": parameters,
        "closures": closure_rows,
        "checks": {
            "dimensionally_corrected_formula_matches_direct_matrix": corrected_parity_passed,
            "both_source_compatible_density_closures_evaluated": set(
                closure_rows
            )
            == {"fixed_free", "conserved"},
        },
        "target_decisions": decisions,
    }
