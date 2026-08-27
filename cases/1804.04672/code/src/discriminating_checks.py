"""Target-specific code-fault checks for the unresolved 1804.04672 items.

The campaign consumes only frozen equation parameters.  It checks numerical
construction, fitting, geometry, and eigenstate invariants; it does not compare
against source pixels or promote the reduced calculations to paper-exact
scientific evidence.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

import numpy as np

from nonhermitian_chern import (
    DiskParams,
    SquareParams,
    disk_gap_square,
    disk_hamiltonian_sparse,
    disk_lattice_sites,
    fig_s2_gap_scaling_parameter_sets,
    generate_disk_gap_scaling_rows,
    open_boundary_bloch_phase_boundaries,
    open_boundary_non_bloch_phase_boundary,
    square_gap_square,
)
from supplemental_campaign import skin_profile_arrays


TARGET_IDS = ("T003", "T005", "T006", "T008", "T009")


def _finite_size_boundary(
    *,
    geometry: str,
    gamma: float,
    sizes: Iterable[int],
    offsets: Iterable[float],
) -> dict[str, Any]:
    sizes = tuple(int(value) for value in sizes)
    theory = open_boundary_non_bloch_phase_boundary(gamma)
    rows: list[dict[str, Any]] = []
    for offset in offsets:
        mass = theory + float(offset)
        gaps = []
        for size in sizes:
            if geometry == "square":
                gap = square_gap_square(
                    SquareParams(
                        L=size,
                        m=mass,
                        gamma_x=gamma,
                        gamma_y=gamma,
                    ),
                    eigen_count=6,
                )
            elif geometry == "disk":
                gap = disk_gap_square(
                    DiskParams(
                        radius=size,
                        m=mass,
                        gamma_x=gamma,
                        gamma_y=gamma,
                    ),
                    eigen_count=6,
                )
            else:
                raise ValueError(f"unsupported geometry {geometry!r}")
            gaps.append(float(gap))
        slope, intercept = np.polyfit(
            1.0 / np.asarray(sizes, dtype=float) ** 2,
            np.asarray(gaps, dtype=float),
            1,
        )
        rows.append(
            {
                "mass": mass,
                "offset": float(offset),
                "gaps": gaps,
                "slope": float(slope),
                "intercept": float(intercept),
            }
        )
    selected = min(rows, key=lambda row: abs(float(row["intercept"])))
    return {
        "geometry": geometry,
        "sizes": list(sizes),
        "rows": rows,
        "boundary": float(selected["mass"]),
        "theory_boundary": float(theory),
    }


def _phase_boundary_check(parameters: dict[str, Any]) -> dict[str, Any]:
    gamma = float(parameters["gamma"])
    coarse = _finite_size_boundary(
        geometry="square",
        gamma=gamma,
        sizes=parameters["coarse_sizes"],
        offsets=parameters["mass_offsets"],
    )
    refined = _finite_size_boundary(
        geometry="square",
        gamma=gamma,
        sizes=parameters["refined_sizes"],
        offsets=parameters["mass_offsets"],
    )
    lower, upper = open_boundary_bloch_phase_boundaries(gamma)
    symmetry_residual = abs((lower + upper) - 4.0)
    refinement_shift = abs(coarse["boundary"] - refined["boundary"])
    return {
        "target_id": "T003",
        "checks": {
            "bloch_fan_symmetry": {
                "kind": "invariant",
                "value": symmetry_residual,
                "tolerance": float(parameters["symmetry_tolerance"]),
                "passed": symmetry_residual <= float(parameters["symmetry_tolerance"]),
            },
            "finite_size_sensitivity": {
                "kind": "convergence",
                "value": refinement_shift,
                "tolerance": float(parameters["refinement_shift_maximum"]),
                "passed": refinement_shift
                <= float(parameters["refinement_shift_maximum"]),
            },
        },
        "coarse": coarse,
        "refined": refined,
        "scientific_boundary": "paper finite-size sequence and estimator remain unpublished",
    }


def _gap_fit_check(parameters: dict[str, Any]) -> dict[str, Any]:
    radii = [int(value) for value in parameters["radii"]]
    base = {
        label: replace(value, radius=radii[0])
        for label, value in fig_s2_gap_scaling_parameter_sets().items()
    }
    rows = generate_disk_gap_scaling_rows(
        base,
        radii,
        eigen_count=int(parameters["eigen_count"]),
    )
    fit_rows = []
    maximum_oracle_residual = 0.0
    maximum_window_shift = 0.0
    for label in sorted(base):
        selected = [row for row in rows if row["parameter_set"] == label]
        x = np.asarray([float(row["inverse_radius_square"]) for row in selected])
        y = np.asarray([float(row["gap_square"]) for row in selected])
        slope, intercept = np.polyfit(x, y, 1)
        design = np.column_stack([x, np.ones_like(x)])
        oracle_slope, oracle_intercept = np.linalg.lstsq(design, y, rcond=None)[0]
        tail_slope, tail_intercept = np.polyfit(x[-3:], y[-3:], 1)
        residual = max(abs(slope - oracle_slope), abs(intercept - oracle_intercept))
        window_shift = abs(intercept - tail_intercept)
        maximum_oracle_residual = max(maximum_oracle_residual, float(residual))
        maximum_window_shift = max(maximum_window_shift, float(window_shift))
        fit_rows.append(
            {
                "parameter_set": label,
                "mass": float(selected[0]["m"]),
                "all_radius_intercept": float(intercept),
                "tail_intercept": float(tail_intercept),
                "all_radius_slope": float(slope),
                "tail_slope": float(tail_slope),
                "least_squares_oracle_intercept": float(oracle_intercept),
            }
        )
    return {
        "target_id": "T005",
        "checks": {
            "independent_fit_oracle": {
                "kind": "exact_rederivation",
                "value": maximum_oracle_residual,
                "tolerance": float(parameters["fit_oracle_tolerance"]),
                "passed": maximum_oracle_residual
                <= float(parameters["fit_oracle_tolerance"]),
            },
            "radius_window_sensitivity": {
                "kind": "convergence",
                "value": maximum_window_shift,
                "tolerance": float(parameters["window_shift_maximum"]),
                "passed": maximum_window_shift
                <= float(parameters["window_shift_maximum"]),
            },
        },
        "fits": fit_rows,
        "scientific_boundary": "paper radius convention, fit weighting, and uncertainty rule remain unpublished",
    }


def _disk_boundary_check(parameters: dict[str, Any]) -> dict[str, Any]:
    rows = []
    maximum_shift = 0.0
    maximum_dimension_residual = 0
    for gamma in parameters["gamma_values"]:
        coarse = _finite_size_boundary(
            geometry="disk",
            gamma=float(gamma),
            sizes=parameters["coarse_radii"],
            offsets=parameters["mass_offsets"],
        )
        refined = _finite_size_boundary(
            geometry="disk",
            gamma=float(gamma),
            sizes=parameters["refined_radii"],
            offsets=parameters["mass_offsets"],
        )
        maximum_shift = max(maximum_shift, abs(coarse["boundary"] - refined["boundary"]))
        radius = int(parameters["refined_radii"][-1])
        matrix = disk_hamiltonian_sparse(DiskParams(radius=radius, m=2.0))
        expected_dimension = 2 * len(disk_lattice_sites(radius))
        maximum_dimension_residual = max(
            maximum_dimension_residual,
            abs(matrix.shape[0] - expected_dimension),
            abs(matrix.shape[1] - expected_dimension),
        )
        rows.append({"gamma": float(gamma), "coarse": coarse, "refined": refined})
    return {
        "target_id": "T006",
        "checks": {
            "disk_hamiltonian_dimension": {
                "kind": "invariant",
                "value": maximum_dimension_residual,
                "tolerance": 0,
                "passed": maximum_dimension_residual == 0,
            },
            "radius_refinement_sensitivity": {
                "kind": "convergence",
                "value": maximum_shift,
                "tolerance": float(parameters["refinement_shift_maximum"]),
                "passed": maximum_shift
                <= float(parameters["refinement_shift_maximum"]),
            },
        },
        "rows": rows,
        "scientific_boundary": "paper disk size sequence and transition estimator remain unpublished",
    }


def _skin_checks(parameters: dict[str, Any]) -> dict[str, dict[str, Any]]:
    arrays, summaries = skin_profile_arrays(
        square_size=int(parameters["square_size"]),
        disk_radius=int(parameters["disk_radius"]),
        shifts=[complex(*value) for value in parameters["state_shifts"]],
    )
    results: dict[str, dict[str, Any]] = {}
    for target_id in ("T008", "T009"):
        target_rows = [row for row in summaries if row["target_id"] == target_id]
        normalization_residual = 0.0
        center_residual = 0.0
        boundary_fractions = []
        for row in target_rows:
            geometry = str(row["geometry"])
            state_index = int(float(row["state_index"]))
            density = arrays[f"{target_id}_{geometry}_state_{state_index}_density"]
            coordinates = arrays[f"{target_id}_{geometry}_coordinates"]
            normalization_residual = max(
                normalization_residual, abs(float(np.sum(density)) - 1.0)
            )
            center = density @ coordinates
            center_residual = max(
                center_residual,
                abs(float(center[0]) - float(row["center_x"])),
                abs(float(center[1]) - float(row["center_y"])),
            )
            radius = np.linalg.norm(coordinates - np.mean(coordinates, axis=0), axis=1)
            cutoff = float(np.quantile(radius, 0.8))
            boundary_fractions.append(float(np.sum(density[radius >= cutoff])))
        results[target_id] = {
            "target_id": target_id,
            "checks": {
                "density_normalization": {
                    "kind": "invariant",
                    "value": normalization_residual,
                    "tolerance": float(parameters["normalization_tolerance"]),
                    "passed": normalization_residual
                    <= float(parameters["normalization_tolerance"]),
                },
                "center_rederivation": {
                    "kind": "exact_rederivation",
                    "value": center_residual,
                    "tolerance": float(parameters["center_tolerance"]),
                    "passed": center_residual <= float(parameters["center_tolerance"]),
                },
            },
            "state_count": len(target_rows),
            "boundary_mass_fractions": boundary_fractions,
            "scientific_boundary": "paper does not uniquely identify the displayed eigenstates",
        }
    return results


def run_campaign(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("paper_id") != "1804.04672":
        raise ValueError("paper_id must be 1804.04672")
    source_policy = config["source_policy"]
    if any(bool(source_policy.get(key, True)) for key in source_policy):
        raise ValueError("all forbidden scientific inputs must be explicitly false")
    parameters = config["parameters"]
    results = {
        "T003": _phase_boundary_check(parameters["T003"]),
        "T005": _gap_fit_check(parameters["T005"]),
        "T006": _disk_boundary_check(parameters["T006"]),
        **_skin_checks(parameters["skin_states"]),
    }
    for target_id, result in results.items():
        if target_id not in TARGET_IDS:
            raise RuntimeError(f"unexpected target {target_id}")
        result["passed"] = bool(
            result["checks"]
            and all(bool(check["passed"]) for check in result["checks"].values())
        )
    return {
        "schema_version": 1,
        "paper_id": "1804.04672",
        "profile": config["profile"],
        "purpose": "code_fault_discrimination_only",
        "target_results": results,
        "status": "passed" if all(row["passed"] for row in results.values()) else "failed",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
    }
