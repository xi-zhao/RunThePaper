"""Clean-room implementation closure for the uncovered droplet observables.

This module executes only equations and scalar parameters declared in frozen
JSON configurations.  It never reads the paper, source figures, author arrays,
or author code.  A successful campaign proves that the numerical routes exist;
it does not by itself promote any item to scientific coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.constants import atomic_mass, g
from scipy.linalg import eigvals
from scipy.optimize import brentq

from .model import (
    ScatteringModel,
    equilibrium_scales,
    solve_radial_profile,
)
from .paper_scale import build_tasks, validate_config as validate_paper_scale_config
from .reproduction import expansion_proxy, interaction_and_critical_curves


ITEMS_BY_TARGET: dict[str, list[str]] = {
    "T001": [
        "PFIG-001-A-A11",
        "PFIG-001-A-A12",
        "PFIG-001-A-A22",
        "PFIG-001-A-DELTA-A",
    ],
    "T002": ["PFIG-001-B-NC"],
    "T003": [
        "PFIG-002-C-RATIO-BAND",
        "PFIG-002-C-RATIO-EQ",
        "PFIG-003-C-RATIO-BAND",
        "PFIG-003-C-RATIO-EQ",
    ],
    "T004": ["PFIG-003-A-NC-METASTABLE", "PFIG-003-A-NC-STABLE"],
    "T005": ["PFIG-003-B-SIGMA-METASTABLE", "PFIG-003-B-SIGMA-STABLE"],
    "T007": ["PFIG-S02-GPE-CONFINED12", "PFIG-S02-GPE-FREE"],
    "T008": ["PFIG-004-GPE-B56P45", "PFIG-004-GPE-B56P64"],
    "T009": ["PCLM-MAIN-DENSITY-N-INVARIANT"],
    "T010": ["PCLM-MAIN-SELF-EVAP-N1E6"],
    "T011": ["PCLM-SI-CURVATURE-X", "PCLM-SI-CURVATURE-Y"],
    "T012": ["PCLM-SI-IMAGING-SIGMA-THEORY"],
}


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _validate_source_boundary(boundary: dict[str, Any]) -> None:
    forbidden = (
        "author_code_used",
        "author_numerical_arrays_used",
        "source_pixels_used_as_numerical_input",
        "raw_directory_is_input",
        "reference_figures_are_inputs",
    )
    if any(bool(boundary.get(key, True)) for key in forbidden):
        raise ValueError("all forbidden clean-room inputs must be explicitly false")


def _physical_number_factor(theory: dict[str, Any], field_gauss: float) -> float:
    model = ScatteringModel.from_config(theory)
    interactions = model.evaluate(field_gauss)
    scales = equilibrium_scales(
        interactions["a11_bohr"],
        interactions["a22_bohr"],
        interactions["a12_bohr"],
    )
    return float(
        (scales["n1_per_bohr3"] + scales["n2_per_bohr3"])
        * scales["xi_bohr"] ** 3
    )


def density_plateau_check(
    theory: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Solve finite droplets and test their large-N central-density plateau."""

    factor = _physical_number_factor(theory, float(parameters["field_gauss"]))
    solver = parameters["radial_solver"]
    rows: list[dict[str, float]] = []
    for chemical_potential in parameters["chemical_potentials"]:
        profile = solve_radial_profile(
            float(chemical_potential),
            radius_max=float(solver["radius_max"]),
            initial_nodes=int(solver["initial_nodes"]),
            tolerance=float(solver["tolerance"]),
            max_nodes=int(solver["max_nodes"]),
        )
        rows.append(
            {
                "chemical_potential": float(chemical_potential),
                "particle_number": float(profile.particle_number * factor),
                "central_density_over_bulk": float(profile.central_field**2),
            }
        )
    plateau_points = int(parameters["plateau_points"])
    plateau = np.asarray(
        [row["central_density_over_bulk"] for row in rows[-plateau_points:]],
        dtype=float,
    )
    relative_span = float(np.ptp(plateau) / np.mean(plateau))
    return {
        "rows": rows,
        "plateau_relative_span": relative_span,
        "tolerance": float(parameters["plateau_relative_span_maximum"]),
        "passed": bool(
            np.all(np.diff([row["particle_number"] for row in rows]) > 0.0)
            and relative_span
            <= float(parameters["plateau_relative_span_maximum"])
        ),
        "evidence_level": "clean_room_reduced_numerics",
    }


def _lowest_quadrupole_mode(
    chemical_potential: float,
    *,
    matrix_points: int,
    radius_max: float,
    radial_solver: dict[str, Any],
) -> tuple[float, float]:
    """Return dimensionless N and the lowest l=2 BdG mode.

    The BdG matrix is the linearization of
    ``i dphi/dt = [-laplacian/2 - 3|phi|^2 + 5|phi|^3/2] phi``.
    The radial transform ``u(r)=r delta_phi(r)`` removes the first derivative;
    Dirichlet endpoints and the l(l+1)/(2r^2) term give the quadrupole sector.
    """

    profile = solve_radial_profile(
        float(chemical_potential),
        radius_max=float(radius_max),
        initial_nodes=int(radial_solver["initial_nodes"]),
        tolerance=float(radial_solver["tolerance"]),
        max_nodes=int(radial_solver["max_nodes"]),
    )
    points = int(matrix_points)
    spacing = float(radius_max) / (points + 1)
    radius = spacing * np.arange(1, points + 1, dtype=float)
    field = np.interp(radius, profile.radius, profile.field)
    density = field**2
    second_derivative = (
        np.diag(np.full(points, -2.0))
        + np.diag(np.ones(points - 1), 1)
        + np.diag(np.ones(points - 1), -1)
    ) / spacing**2
    angular_momentum = 2.0
    kinetic = -0.5 * second_derivative + np.diag(
        angular_momentum * (angular_momentum + 1.0) / (2.0 * radius**2)
    )
    diagonal = kinetic + np.diag(
        -6.0 * density + 6.25 * density**1.5 - float(chemical_potential)
    )
    pairing = np.diag(-3.0 * density + 3.75 * density**1.5)
    matrix = np.block([[diagonal, pairing], [-pairing, -diagonal]])
    spectrum = eigvals(matrix, check_finite=False)
    nearly_real = np.real(spectrum[np.abs(np.imag(spectrum)) < 1e-6])
    positive = np.sort(nearly_real[nearly_real > 1e-5])
    if positive.size == 0:
        raise RuntimeError("quadrupole BdG matrix has no positive real mode")
    return float(profile.particle_number), float(positive[0])


def self_evaporation_threshold(
    theory: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Bracket where the first quadrupole mode falls below emission energy."""

    field_gauss = float(parameters["field_gauss"])
    factor = _physical_number_factor(theory, field_gauss)
    bracket = tuple(float(value) for value in parameters["chemical_potential_bracket"])
    radial_solver = parameters["radial_solver"]
    radius_max = float(parameters["radius_max"])

    def threshold_for_points(matrix_points: int) -> dict[str, float]:
        cache: dict[float, tuple[float, float]] = {}

        def gap(chemical_potential: float) -> float:
            key = round(float(chemical_potential), 12)
            if key not in cache:
                cache[key] = _lowest_quadrupole_mode(
                    float(chemical_potential),
                    matrix_points=matrix_points,
                    radius_max=radius_max,
                    radial_solver=radial_solver,
                )
            _, mode = cache[key]
            return float(mode + chemical_potential)

        low_gap = gap(bracket[0])
        high_gap = gap(bracket[1])
        if low_gap * high_gap >= 0.0:
            raise RuntimeError("declared chemical-potential bracket does not cross the emission threshold")
        root = float(
            brentq(
                gap,
                bracket[0],
                bracket[1],
                xtol=float(parameters["root_tolerance"]),
            )
        )
        dimensionless_number, mode = _lowest_quadrupole_mode(
            root,
            matrix_points=matrix_points,
            radius_max=radius_max,
            radial_solver=radial_solver,
        )
        return {
            "matrix_points": int(matrix_points),
            "chemical_potential": root,
            "dimensionless_number": dimensionless_number,
            "particle_number": float(dimensionless_number * factor),
            "quadrupole_mode": mode,
            "emission_threshold": -root,
        }

    coarse = threshold_for_points(int(parameters["coarse_matrix_points"]))
    refined = threshold_for_points(int(parameters["refined_matrix_points"]))
    refinement_relative_difference = abs(
        refined["particle_number"] - coarse["particle_number"]
    ) / refined["particle_number"]
    published_claim = float(parameters["published_threshold_particle_number"])
    return {
        "coarse": coarse,
        "refined": refined,
        "refinement_relative_difference": refinement_relative_difference,
        "refinement_tolerance": float(parameters["refinement_relative_tolerance"]),
        "relative_difference_from_published_claim": abs(
            refined["particle_number"] - published_claim
        )
        / published_claim,
        "published_claim_used_only_as_comparison": published_claim,
        "passed": bool(
            refinement_relative_difference
            <= float(parameters["refinement_relative_tolerance"])
        ),
        "evidence_level": "clean_room_reduced_bdg",
    }


def transverse_optical_hessian(parameters: dict[str, Any]) -> dict[str, Any]:
    """Derive transverse curvatures of the scanned elliptical Gaussian beam."""

    mass = float(parameters.get("mass_atomic_units", 38.9637064864)) * atomic_mass
    wavelength = float(parameters["wavelength_nanometre"]) * 1e-9
    waist_y = float(parameters["waist_y_micrometre"]) * 1e-6
    waist_z = float(parameters["waist_z_micrometre"]) * 1e-6
    amplitude = float(parameters["scan_amplitude_micrometre"]) * 1e-6
    offset = float(parameters["scan_offset_micrometre"]) * 1e-6
    phase = np.linspace(0.0, 1.0, int(parameters["quadrature_samples"]))
    centers = amplitude * (2.0 * np.sqrt(np.abs(1.0 - 2.0 * phase)) - 1.0) + offset
    central_profile = np.exp(-2.0 * centers**2 / waist_z**2)
    vertical_derivative = float(np.mean(4.0 * centers / waist_z**2 * central_profile))
    optical_amplitude = -mass * g / vertical_derivative

    curvature_y = optical_amplitude * float(np.mean(central_profile)) * (-4.0 / waist_y**2)
    frequency_y = float(np.sqrt(max(curvature_y / mass, 0.0)) / (2.0 * np.pi))

    rayleigh_y = np.pi * waist_y**2 / wavelength
    rayleigh_z = np.pi * waist_z**2 / wavelength

    def averaged_profile_x(position: float) -> float:
        scale_y = 1.0 + (position / rayleigh_y) ** 2
        scale_z = 1.0 + (position / rayleigh_z) ** 2
        return float(
            np.mean(
                np.exp(-2.0 * centers**2 / (waist_z**2 * scale_z))
                / np.sqrt(scale_y * scale_z)
            )
        )

    step = float(parameters["propagation_finite_difference_step_micrometre"]) * 1e-6
    curvature_x = optical_amplitude * (
        averaged_profile_x(step)
        - 2.0 * averaged_profile_x(0.0)
        + averaged_profile_x(-step)
    ) / step**2
    signed_frequency_x = float(
        np.sign(curvature_x)
        * np.sqrt(abs(curvature_x) / mass)
        / (2.0 * np.pi)
    )
    expected_x = float(parameters["published_frequency_x_hz"])
    expected_y = float(parameters["published_frequency_y_hz"])
    return {
        "frequency_x_hz": signed_frequency_x,
        "frequency_y_hz": frequency_y,
        "published_frequency_x_hz_used_only_as_comparison": expected_x,
        "published_frequency_y_hz_used_only_as_comparison": expected_y,
        "relative_difference_x": abs(signed_frequency_x - expected_x) / expected_x,
        "relative_difference_y": abs(frequency_y - expected_y) / expected_y,
        "x_status": "missing_scan_geometry_or_additional_confinement",
        "y_status": "independently_reproduced_from_published_beam_waist",
        "passed": bool(np.isfinite(signed_frequency_x) and np.isfinite(frequency_y)),
        "scientific_match": bool(
            abs(frequency_y - expected_y) / expected_y
            <= float(parameters["frequency_y_relative_tolerance"])
            and abs(signed_frequency_x - expected_x) / expected_x
            <= float(parameters["frequency_x_relative_tolerance"])
        ),
    }


def calibration_input_contract(parameters: dict[str, Any]) -> dict[str, Any]:
    required = list(parameters["required_paper_inputs"])
    provided = parameters.get("paper_inputs")
    if provided is None:
        return {
            "status": "input_blocked",
            "required_paper_inputs": required,
            "missing_paper_inputs": required,
            "runner": "quantum_droplets.coupled_gpe.run_split_step_scenario",
        }
    missing = [name for name in required if name not in provided]
    if missing:
        raise ValueError(f"calibration paper_inputs missing: {', '.join(missing)}")
    return {
        "status": "ready",
        "required_paper_inputs": required,
        "missing_paper_inputs": [],
        "runner": "quantum_droplets.coupled_gpe.run_split_step_scenario",
    }


def run_campaign(config: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    if int(config.get("schema_version", 0)) != 1:
        raise ValueError("implementation closure requires schema_version 1")
    if str(config.get("paper_id")) != "1710.10890":
        raise ValueError("paper_id must be 1710.10890")
    parameters = config["parameters"]
    _validate_source_boundary(parameters["source_boundary"])
    theory = _read_object(workspace / parameters["paper_theory_config"])
    paper_scale = _read_object(workspace / parameters["paper_scale_config"])
    validate_paper_scale_config(paper_scale)

    model = ScatteringModel.from_config(theory)
    reduced_targets, reduced_diagnostics = interaction_and_critical_curves(theory, model)
    expansion, expansion_diagnostics = expansion_proxy(theory)
    paper_scale_tasks = build_tasks(paper_scale)
    density = density_plateau_check(theory, parameters["density_plateau"])
    self_evaporation = self_evaporation_threshold(
        theory, parameters["self_evaporation"]
    )
    transverse = transverse_optical_hessian(parameters["transverse_hessian"])
    calibration = calibration_input_contract(parameters["imaging_calibration"])

    target_checks: dict[str, dict[str, Any]] = {
        "T001": {
            "passed": bool(np.all(np.isfinite(reduced_targets["T001"]["a11_bohr"]))),
            "scientific_status": "input_blocked_paper_exact_scattering_lane",
        },
        "T002": {
            "passed": bool(np.all(np.isfinite(reduced_targets["T002"]["critical_number_stable"]))),
            "scientific_status": "input_blocked_paper_exact_scattering_lane",
        },
        "T003": {
            "passed": bool(np.all(np.isfinite(reduced_targets["T003"]["equilibrium_ratio"]))),
            "scientific_status": "input_blocked_paper_exact_scattering_lane",
        },
        "T004": {
            "passed": bool(np.all(np.isfinite(reduced_targets["T004"]["critical_number_stable"]))),
            "scientific_status": "input_blocked_paper_exact_scattering_lane",
        },
        "T005": {
            "passed": bool(np.all(np.isfinite(reduced_targets["T005"]["sigma_stable_micrometre"]))),
            "scientific_status": "generated_method_equivalence_unresolved",
            "radial_diagnostics": reduced_diagnostics,
        },
        "T007": {
            "passed": bool(
                np.all(np.isfinite(expansion["free_radius_micrometre"]))
                and len([task for task in paper_scale_tasks if task.payload["scenario"]["target_id"] == "T007"]) == 6
            ),
            "scientific_status": "paper_scale_execution_pending",
            "proxy_diagnostics": expansion_diagnostics,
        },
        "T008": {
            "passed": bool(
                len([task for task in paper_scale_tasks if task.payload["scenario"]["target_id"] == "T008"]) == 6
            ),
            "scientific_status": "input_blocked_exact_atom_numbers",
        },
        "T009": density,
        "T010": self_evaporation,
        "T011": transverse,
        "T012": {
            "passed": True,
            "scientific_status": calibration["status"],
            "input_contract": calibration,
        },
    }
    if not all(bool(check["passed"]) for check in target_checks.values()):
        raise RuntimeError("one or more implementation checks failed")

    item_results: dict[str, dict[str, Any]] = {}
    for target_id, items in ITEMS_BY_TARGET.items():
        scientific_status = str(
            target_checks[target_id].get("scientific_status", "review_pending")
        )
        for item_id in items:
            item_results[item_id] = {
                "target_id": target_id,
                "implementation_status": "smoke_attested",
                "scientific_status": scientific_status,
            }
    return {
        "schema_version": 1,
        "paper_id": "1710.10890",
        "profile": str(config["profile"]),
        "status": "passed",
        "target_checks": target_checks,
        "item_results": item_results,
        "scientific_coverage_changed": False,
        "source_boundary": parameters["source_boundary"],
    }
