#!/usr/bin/env python3
"""Generate every numerical target from independent scientific numerics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pt_spectrum.model import (  # noqa: E402
    airy_matching_derivative,
    classical_escape_angle,
    classical_period,
    classical_spiral_trajectory,
    complex_wkb_turning_points,
    ground_state_shooting,
    hermitian_low_spectrum,
    hermitian_wkb_energy,
    low_spectrum,
    locate_exceptional_point,
    massive_n0_energy,
    massive_n1_energy,
    massive_n2_energy,
    near_n2_two_level_merger,
    near_one_asymptotic_energy,
    shifted_oscillator_energy,
    square_well_energy,
    stokes_wedge_angles,
    turning_point_angle,
    turning_point_passages,
    turning_points_before_escape,
    wkb_branch_cut_intersection_imag,
    wkb_energy,
)


def json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"unsupported JSON value: {type(value)!r}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n",
        encoding="utf-8",
    )


def write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def declared_grid(config: dict[str, Any]) -> np.ndarray:
    values: list[float] = []
    values.extend(float(item) for item in config.get("explicit_exponents", []))
    values.extend(float(item) for item in config.get("anchor_exponents", []))
    for start, stop, count in config.get("linear_segments", []):
        values.extend(np.linspace(float(start), float(stop), int(count)).tolist())
    if "linear_segment" in config:
        start, stop, count = config["linear_segment"]
        values.extend(np.linspace(float(start), float(stop), int(count)).tolist())
    values.extend(1.0 + float(item) for item in config.get("near_one_epsilons", []))
    if not values:
        raise ValueError("spectrum grid is empty")
    return np.array(sorted(set(round(value, 12) for value in values)), dtype=float)


def spectrum_rows(
    exponent: float,
    values: np.ndarray,
    *,
    real_tolerance: float,
    solver: str,
    energy_min: float = -np.inf,
    energy_max: float = np.inf,
    mass_squared: float = 0.0,
) -> list[dict[str, Any]]:
    rows = []
    for rank, value in enumerate(values):
        rows.append(
            {
                "N": float(exponent),
                "mass_squared": float(mass_squared),
                "mode_rank": rank,
                "energy_real": float(value.real),
                "energy_imag": float(value.imag),
                "is_real": bool(abs(value.imag) <= real_tolerance),
                "visible_in_paper_window": bool(energy_min <= value.real <= energy_max),
                "solver": solver,
            }
        )
    return rows


def run_fig1(parameters: dict[str, Any], real_tolerance: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for exponent in declared_grid(parameters):
        if exponent <= parameters["shooting_cutoff"]:
            result = ground_state_shooting(
                exponent,
                boundary=parameters["shooting_boundary"],
                relative_tolerance=parameters["shooting_rtol"],
                absolute_tolerance=parameters["shooting_atol"],
                max_step=parameters["shooting_max_step"],
            )
            values = np.array([complex(result.energy)], dtype=np.complex128)
            solver = "riccati_shooting"
        else:
            contour = exponent > 2.0
            discretization = (
                parameters["complex_contour"] if contour else parameters["real_axis"]
            )
            values = low_spectrum(
                exponent,
                half_width=discretization["half_width"],
                points=discretization["points"],
                bend_scale=discretization.get("bend_scale", 2.0),
                eigenvalues=parameters["eigenvalues"],
                shift=parameters["shift"],
                tolerance=parameters["eigensolver_tolerance"],
                use_complex_contour=contour,
            )
            solver = "complex_contour_fd" if contour else "real_axis_fd"
        rows.extend(
            spectrum_rows(
                exponent,
                values,
                real_tolerance=real_tolerance,
                solver=solver,
                energy_min=0.0,
                energy_max=parameters["energy_max"],
            )
        )
    return rows


def run_table_i(parameters: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
    rows: list[dict[str, Any]] = []
    resolution_difference = 0.0
    for exponent in parameters["exponents"]:
        count = parameters["levels_by_exponent"][str(float(exponent))]
        common = dict(
            half_width=parameters["half_width"],
            bend_scale=parameters["bend_scale"],
            eigenvalues=parameters["eigenvalues"],
            shift=parameters["shift"],
            use_complex_contour=True,
        )
        fine = low_spectrum(exponent, points=parameters["points"], **common)
        coarse = low_spectrum(exponent, points=parameters["coarse_points"], **common)
        resolution_difference = max(
            resolution_difference,
            float(np.max(np.abs(fine[:count].real - coarse[:count].real))),
        )
        for level in range(count):
            rows.append(
                {
                    "N": float(exponent),
                    "n": level,
                    "exact_fd": float(fine[level].real),
                    "exact_imag": float(fine[level].imag),
                    "coarse_fd": float(coarse[level].real),
                    "wkb": wkb_energy(exponent, level),
                }
            )
    return rows, resolution_difference


def nearest_value(values: np.ndarray, target: float) -> complex:
    return complex(min(values, key=lambda value: abs(value - target)))


def run_table_ii(parameters: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for epsilon in parameters["epsilons"]:
        exponent = 1.0 + float(epsilon)
        primary = ground_state_shooting(
            exponent,
            boundary=parameters["boundary"],
            relative_tolerance=parameters["relative_tolerance"],
            absolute_tolerance=parameters["absolute_tolerance"],
            max_step=parameters["max_step"],
        )
        secondary = ground_state_shooting(
            exponent,
            boundary=parameters["secondary_boundary"],
            relative_tolerance=parameters["relative_tolerance"],
            absolute_tolerance=parameters["absolute_tolerance"],
            max_step=parameters["max_step"],
        )
        finite_difference = low_spectrum(
            exponent,
            half_width=parameters["fd_half_width"],
            points=parameters["fd_points"],
            eigenvalues=parameters["fd_eigenvalues"],
            shift=primary.energy,
            tolerance=max(parameters["relative_tolerance"], 1e-11),
            use_complex_contour=False,
        )
        fd_value = nearest_value(finite_difference, primary.energy)
        rows.append(
            {
                "epsilon": float(epsilon),
                "N": exponent,
                "exact_shooting": primary.energy,
                "patch_residual": primary.residual,
                "secondary_boundary_energy": secondary.energy,
                "finite_difference_energy": fd_value.real,
                "finite_difference_imag": fd_value.imag,
                "asymptotic_eq11": near_one_asymptotic_energy(float(epsilon)),
            }
        )
    return rows


def run_fig3(parameters: dict[str, Any], real_tolerance: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grid = declared_grid(parameters)
    for mass_squared in parameters["mass_squared_values"]:
        for exponent in grid:
            values = low_spectrum(
                exponent,
                mass_squared=mass_squared,
                half_width=parameters["half_width"],
                points=parameters["points"],
                eigenvalues=parameters["eigenvalues"],
                shift=parameters["shift"],
                tolerance=parameters["eigensolver_tolerance"],
                use_complex_contour=False,
            )
            rows.extend(
                spectrum_rows(
                    exponent,
                    values,
                    real_tolerance=real_tolerance,
                    solver="real_axis_fd",
                    energy_min=parameters["energy_min"],
                    energy_max=parameters["energy_max"],
                    mass_squared=mass_squared,
                )
            )
    return rows


def run_quantitative_claims(parameters: dict[str, Any]) -> dict[str, Any]:
    """Evaluate quantitative prose/equation claims omitted by figure-only scope."""

    cubic_rows = []
    for case in parameters["cubic_cases"]:
        linear = complex(case["linear_real"], case["linear_imag"])
        values = low_spectrum(
            3.0,
            mass_squared=float(case["mass_squared"]),
            linear_coefficient=linear,
            half_width=float(parameters["cubic_half_width"]),
            points=int(parameters["cubic_points"]),
            bend_scale=float(parameters["cubic_bend_scale"]),
            eigenvalues=int(parameters["cubic_levels"]),
            shift=float(parameters["cubic_shift"]),
            tolerance=float(parameters["cubic_tolerance"]),
            use_complex_contour=True,
        )
        for level, value in enumerate(values[: int(parameters["cubic_levels"])]):
            cubic_rows.append(
                {
                    "case_id": case["case_id"],
                    "expected_class": case["expected_class"],
                    "level": level,
                    "energy_real": float(value.real),
                    "energy_imag": float(value.imag),
                }
            )

    shifted_rows = []
    for case in parameters["shifted_oscillators"]:
        coefficient = complex(case["linear_real"], case["linear_imag"])
        for level in range(int(parameters["shifted_levels"])):
            value = shifted_oscillator_energy(coefficient, level)
            shifted_rows.append(
                {
                    "case_id": case["case_id"],
                    "level": level,
                    "energy_real": float(value.real),
                    "energy_imag": float(value.imag),
                }
            )

    wedge_rows = [
        {"N": float(exponent), **stokes_wedge_angles(float(exponent))}
        for exponent in parameters["wedge_exponents"]
    ]
    airy_rows = [
        {
            "energy": float(energy),
            "matching_derivative": airy_matching_derivative(float(energy)),
        }
        for energy in parameters["airy_energies"]
    ]
    classical_rows = [
        {
            "N": float(exponent),
            "energy": float(parameters["classical_energy"]),
            "period": classical_period(
                float(parameters["classical_energy"]), float(exponent)
            ),
        }
        for exponent in parameters["classical_period_exponents"]
    ]
    turning_point_rows = []
    turning_point_energy = float(parameters["wkb_turning_point_energy"])
    for exponent in parameters["wkb_geometry_exponents"]:
        left, right = complex_wkb_turning_points(float(exponent), turning_point_energy)
        branch_cut_intersection_imag = wkb_branch_cut_intersection_imag(
            float(exponent), turning_point_energy
        )
        if exponent > 2.0:
            expected_half_plane = "lower"
        elif exponent < 2.0:
            expected_half_plane = "upper"
        else:
            expected_half_plane = "real"
        turning_point_rows.append(
            {
                "N": float(exponent),
                "energy": turning_point_energy,
                "left_real": left.real,
                "left_imag": left.imag,
                "right_real": right.real,
                "right_imag": right.imag,
                "expected_half_plane": expected_half_plane,
                "branch_cut_intersection_imag": branch_cut_intersection_imag,
                "crosses_positive_imaginary_branch_cut": bool(
                    branch_cut_intersection_imag > 1e-12
                ),
                "continuous_wkb_path_valid": bool(
                    branch_cut_intersection_imag <= 1e-12
                ),
            }
        )

    contour_deformation_rows = []
    for exponent in parameters["contour_deformation_exponents"]:
        for bend_scale in parameters["contour_deformation_bend_scales"]:
            values = low_spectrum(
                float(exponent),
                half_width=float(parameters["contour_deformation_half_width"]),
                points=int(parameters["contour_deformation_points"]),
                bend_scale=float(bend_scale),
                eigenvalues=int(parameters["contour_deformation_levels"]),
                shift=float(parameters["contour_deformation_shift"]),
                tolerance=float(parameters["cubic_tolerance"]),
                use_complex_contour=True,
            )
            for level, value in enumerate(
                values[: int(parameters["contour_deformation_levels"])]
            ):
                contour_deformation_rows.append(
                    {
                        "N": float(exponent),
                        "bend_scale": float(bend_scale),
                        "level": level,
                        "energy_real": float(value.real),
                        "energy_imag": float(value.imag),
                    }
                )

    massless_wkb_large_n_rows = [
        {
            "N": float(exponent),
            "level": int(level),
            "wkb_energy": wkb_energy(float(exponent), int(level)),
        }
        for level in parameters["massless_wkb_large_n_levels"]
        for exponent in parameters["massless_wkb_large_n_exponents"]
    ]

    near_n2_merger_rows = []
    for order in parameters["near_n2_quadrature_orders"]:
        for level in parameters["near_n2_merger_levels"]:
            near_n2_merger_rows.append(
                {
                    "quadrature_order": int(order),
                    **near_n2_two_level_merger(int(level), quadrature_order=int(order)),
                }
            )

    classical_near_transition_rows = [
        {
            "N": float(exponent),
            "escape_angle": classical_escape_angle(float(exponent)),
            "turning_point_spacing": float(2.0 * np.pi / float(exponent)),
        }
        for exponent in parameters["classical_near_transition_exponents"]
    ]

    solver_crosscheck_rows = []
    for exponent in parameters["solver_crosscheck_exponents"]:
        shooting = ground_state_shooting(
            float(exponent),
            boundary=float(parameters["solver_crosscheck_boundary"]),
            relative_tolerance=float(parameters["solver_crosscheck_rtol"]),
            absolute_tolerance=float(parameters["solver_crosscheck_atol"]),
            max_step=float(parameters["solver_crosscheck_max_step"]),
        )
        matrix_values = low_spectrum(
            float(exponent),
            half_width=float(parameters["solver_crosscheck_fd_half_width"]),
            points=int(parameters["solver_crosscheck_fd_points"]),
            eigenvalues=int(parameters["solver_crosscheck_fd_eigenvalues"]),
            shift=shooting.energy,
            tolerance=float(parameters["solver_crosscheck_fd_tolerance"]),
            use_complex_contour=False,
        )
        matrix_energy = nearest_value(matrix_values, shooting.energy)
        solver_crosscheck_rows.append(
            {
                "N": float(exponent),
                "shooting_energy": float(shooting.energy),
                "shooting_residual": float(shooting.residual),
                "finite_difference_energy_real": float(matrix_energy.real),
                "finite_difference_energy_imag": float(matrix_energy.imag),
                "absolute_difference": float(abs(matrix_energy.real - shooting.energy)),
            }
        )

    exceptional_point_rows = []
    ep_bracket = [float(value) for value in parameters["exceptional_point_bracket"]]
    for points in parameters["exceptional_point_resolution_points"]:
        estimate = locate_exceptional_point(
            ep_bracket[0],
            ep_bracket[1],
            half_width=float(parameters["exceptional_point_half_width"]),
            points=int(points),
            eigenvalues=int(parameters["exceptional_point_eigenvalues"]),
            shift=float(parameters["exceptional_point_shift"]),
            tolerance=float(parameters["exceptional_point_eigensolver_tolerance"]),
            root_tolerance=float(parameters["exceptional_point_root_tolerance"]),
        )
        exceptional_point_rows.append(
            {
                "points": int(points),
                "bracket_lower": ep_bracket[0],
                "bracket_upper": ep_bracket[1],
                "estimated_N": estimate,
            }
        )

    trajectory_exponent = float(parameters["classical_trajectory_exponent"])
    trajectory_energy = float(parameters["classical_trajectory_energy"])
    trajectory = classical_spiral_trajectory(
        trajectory_exponent,
        trajectory_energy,
        maximum_time=float(parameters["classical_trajectory_maximum_time"]),
        samples=int(parameters["classical_trajectory_samples"]),
        maximum_step=float(parameters["classical_trajectory_maximum_step"]),
        relative_tolerance=float(parameters["classical_trajectory_rtol"]),
        absolute_tolerance=float(parameters["classical_trajectory_atol"]),
    )
    trajectory_passages = turning_point_passages(
        trajectory, trajectory_exponent, trajectory_energy
    )
    trajectory_stride = int(parameters["classical_trajectory_output_stride"])
    trajectory_rows = [
        {
            "time": float(trajectory.time[index]),
            "x_real": float(trajectory.position[index].real),
            "x_imag": float(trajectory.position[index].imag),
            "p_real": float(trajectory.momentum[index].real),
            "p_imag": float(trajectory.momentum[index].imag),
            "unwrapped_x_angle": float(
                trajectory.unwrapped_z_angle[index] - np.pi / 2.0
            ),
        }
        for index in range(0, len(trajectory.time), trajectory_stride)
    ]

    finest_merger_order = max(
        int(value) for value in parameters["near_n2_quadrature_orders"]
    )
    classical_quantum_rows = []
    for row in near_n2_merger_rows:
        if int(row["quadrature_order"]) != finest_merger_order:
            continue
        merger_exponent = 2.0 - float(row["epsilon_merger"])
        classical_quantum_rows.append(
            {
                "level_lower": int(row["level_lower"]),
                "epsilon_merger": float(row["epsilon_merger"]),
                "N_merger": merger_exponent,
                "classical_turning_points_before_escape": turning_points_before_escape(
                    merger_exponent
                ),
            }
        )

    massive_phase_anchor_rows = []
    for mass_squared in parameters["massive_phase_mass_squared_values"]:
        for exponent in parameters["massive_phase_exponents"]:
            values = low_spectrum(
                float(exponent),
                mass_squared=float(mass_squared),
                half_width=float(parameters["massive_phase_half_width"]),
                points=int(parameters["massive_phase_points"]),
                eigenvalues=int(parameters["massive_phase_levels"]),
                shift=float(parameters["massive_phase_shift"]),
                tolerance=float(parameters["massive_phase_tolerance"]),
                use_complex_contour=False,
            )
            for level, value in enumerate(
                values[: int(parameters["massive_phase_levels"])]
            ):
                if exponent == 0.0:
                    exact = massive_n0_energy(float(mass_squared), level)
                elif exponent == 1.0:
                    exact = massive_n1_energy(float(mass_squared), level)
                elif exponent == 2.0:
                    exact = massive_n2_energy(float(mass_squared), level)
                else:
                    raise ValueError("massive phase anchors require N=0, 1, or 2")
                massive_phase_anchor_rows.append(
                    {
                        "N": float(exponent),
                        "mass_squared": float(mass_squared),
                        "level": level,
                        "energy_real": float(value.real),
                        "energy_imag": float(value.imag),
                        "exact_energy": exact,
                    }
                )

    hermitian_rows = []
    hermitian_resolution_difference = 0.0
    hermitian_levels = int(parameters["hermitian_levels"])
    for exponent in parameters["hermitian_exponents"]:
        half_width = float(
            np.clip(
                float(parameters["hermitian_boundary_potential"])
                ** (1.0 / float(exponent)),
                float(parameters["hermitian_min_half_width"]),
                float(parameters["hermitian_max_half_width"]),
            )
        )
        common = {
            "half_width": half_width,
            "eigenvalues": hermitian_levels,
            "tolerance": float(parameters["hermitian_tolerance"]),
        }
        fine = hermitian_low_spectrum(
            float(exponent), points=int(parameters["hermitian_points"]), **common
        )
        coarse = hermitian_low_spectrum(
            float(exponent),
            points=int(parameters["hermitian_coarse_points"]),
            **common,
        )
        hermitian_resolution_difference = max(
            hermitian_resolution_difference,
            float(np.max(np.abs(fine - coarse))),
        )
        for level in range(hermitian_levels):
            well = square_well_energy(level)
            hermitian_rows.append(
                {
                    "N": float(exponent),
                    "n": level,
                    "half_width": half_width,
                    "exact_fd": float(fine[level]),
                    "coarse_fd": float(coarse[level]),
                    "wkb": hermitian_wkb_energy(float(exponent), level),
                    "square_well": well,
                    "relative_square_well_error": float(abs(fine[level] / well - 1.0)),
                }
            )

    decimal_exponents = np.asarray(
        parameters["near_one_scaling_decimal_exponents"], dtype=float
    )
    near_one_epsilons = 10.0 ** (-decimal_exponents)
    near_one_energies = np.asarray(
        [near_one_asymptotic_energy(float(value)) for value in near_one_epsilons]
    )
    near_one_slope = float(
        np.polyfit(np.log(-np.log(near_one_epsilons)), np.log(near_one_energies), 1)[0]
    )
    near_one_scaling_rows = [
        {
            "decimal_exponent": float(decimal_exponent),
            "epsilon": float(epsilon),
            "asymptotic_energy": float(energy),
        }
        for decimal_exponent, epsilon, energy in zip(
            decimal_exponents, near_one_epsilons, near_one_energies, strict=True
        )
    ]
    subcritical_n = float(parameters["classical_subcritical_exponent"])
    return {
        "schema_version": 1,
        "cubic_spectra": cubic_rows,
        "shifted_oscillator_spectra": shifted_rows,
        "stokes_wedges": wedge_rows,
        "airy_matching": airy_rows,
        "classical_periods": classical_rows,
        "complex_wkb_turning_points": turning_point_rows,
        "contour_deformation_spectra": contour_deformation_rows,
        "massless_wkb_large_n": massless_wkb_large_n_rows,
        "near_n2_two_level_mergers": near_n2_merger_rows,
        "classical_near_transition": classical_near_transition_rows,
        "same_parameter_two_solver_crosscheck": solver_crosscheck_rows,
        "exceptional_point_convergence": exceptional_point_rows,
        "classical_spiral_trajectory": trajectory_rows,
        "classical_spiral_passages": trajectory_passages,
        "classical_spiral_energy_max_abs_error": trajectory.energy_max_abs_error,
        "classical_quantum_event_correspondence": classical_quantum_rows,
        "massive_phase_anchors": massive_phase_anchor_rows,
        "hermitian_abs_x_spectrum": hermitian_rows,
        "hermitian_resolution_max_abs_difference": hermitian_resolution_difference,
        "near_one_logarithmic_scaling": near_one_scaling_rows,
        "near_one_logarithmic_scaling_slope": near_one_slope,
        "classical_subcritical_geometry": {
            "N": subcritical_n,
            "escape_angle": classical_escape_angle(subcritical_n),
            "turning_point_angles": [
                turning_point_angle(subcritical_n, index)
                for index in range(int(parameters["classical_turning_points"]))
            ],
            "period_classification": "infinite_nonperiodic_spiral",
        },
    }


def check_record(
    check_id: str,
    value: float,
    threshold: float,
    *,
    comparison: str = "max_abs",
    target_ids: list[str] | None = None,
    claim_ids: list[str] | None = None,
) -> dict[str, Any]:
    record = {
        "check_id": check_id,
        "status": "passed" if value <= threshold else "failed",
        "value": float(value),
        "threshold": float(threshold),
        "comparison": comparison,
    }
    if target_ids:
        record["target_ids"] = target_ids
    if claim_ids:
        record["claim_ids"] = claim_ids
    return record


def build_science_checks(
    config: dict[str, Any],
    fig1_rows: list[dict[str, Any]],
    table_i_rows: list[dict[str, Any]],
    table_i_resolution_difference: float,
    table_ii_rows: list[dict[str, Any]],
    fig3_rows: list[dict[str, Any]],
    quantitative_claims: dict[str, Any],
) -> dict[str, Any]:
    references = config["printed_references_for_validation_only"]
    tolerance = config["acceptance"]

    exact_i_errors = []
    wkb_i_errors = []
    for row in table_i_rows:
        reference = references["table_i"][str(row["N"])]
        exact_i_errors.append(abs(row["exact_fd"] - reference["exact"][row["n"]]))
        wkb_i_errors.append(abs(row["wkb"] - reference["wkb"][row["n"]]))

    table_ii_exact_errors = [
        abs(row["exact_shooting"] - references["table_ii"]["exact"][index])
        for index, row in enumerate(table_ii_rows)
    ]
    table_ii_asymptotic_errors = [
        abs(row["asymptotic_eq11"] - references["table_ii"]["asymptotic"][index])
        for index, row in enumerate(table_ii_rows)
    ]
    table_ii_solver_differences = [
        abs(row["exact_shooting"] - row["finite_difference_energy"])
        for row in table_ii_rows
    ]
    domain_differences = [
        abs(row["exact_shooting"] - row["secondary_boundary_energy"])
        for row in table_ii_rows
    ]

    n2_rows = [
        row for row in fig1_rows if abs(row["N"] - 2.0) < 1e-12 and row["mode_rank"] < 6
    ]
    n2_error = max(
        abs(row["energy_real"] - (2 * row["mode_rank"] + 1)) for row in n2_rows
    )

    massive_errors = []
    for row in fig3_rows:
        if abs(row["N"] - 1.0) < 1e-12 and row["mode_rank"] < 5:
            expected = massive_n1_energy(row["mass_squared"], row["mode_rank"])
            massive_errors.append(abs(row["energy_real"] - expected))

    discrepancy_rows = []
    for index, row in enumerate(table_ii_rows):
        difference = row["exact_shooting"] - references["table_ii"]["exact"][index]
        if abs(difference) > tolerance["table_ii_first_four_max_abs_error"]:
            discrepancy_rows.append(
                {
                    "epsilon": row["epsilon"],
                    "paper_exact": references["table_ii"]["exact"][index],
                    "independent_shooting": row["exact_shooting"],
                    "independent_finite_difference": row["finite_difference_energy"],
                    "difference": difference,
                    "classification": "inconclusive_pending_fresh_review",
                }
            )

    cubic_rows = quantitative_claims["cubic_spectra"]
    nonpt_cubic = [row for row in cubic_rows if row["expected_class"] == "complex"]
    cubic_nonpt_min_imag = min(abs(row["energy_imag"]) for row in nonpt_cubic)
    cubic_by_case = {
        case_id: [row for row in cubic_rows if row["case_id"] == case_id]
        for case_id in {row["case_id"] for row in cubic_rows}
    }

    shifted_errors: dict[str, list[float]] = {}
    for row in quantitative_claims["shifted_oscillator_spectra"]:
        reference = references["shifted_oscillators"][row["case_id"]]
        expected = complex(
            2 * row["level"] + reference["offset_real"], reference["offset_imag"]
        )
        shifted_errors.setdefault(row["case_id"], []).append(
            abs(complex(row["energy_real"], row["energy_imag"]) - expected)
        )
    n1_wedge = next(
        row for row in quantitative_claims["stokes_wedges"] if row["N"] == 1.0
    )
    wedge_error = max(
        abs(n1_wedge["left_center"] % (2.0 * np.pi) - 5.0 * np.pi / 6.0),
        abs(n1_wedge["right_center"] - np.pi / 6.0),
        abs(n1_wedge["opening"] - 2.0 * np.pi / 3.0),
    )
    airy_error = max(
        abs(row["matching_derivative"] + 1.0 / (2.0 * np.pi))
        for row in quantitative_claims["airy_matching"]
    )
    n2_period = next(
        row for row in quantitative_claims["classical_periods"] if row["N"] == 2.0
    )["period"]
    turning_point_failures = 0
    for row in quantitative_claims["complex_wkb_turning_points"]:
        imag_parts = (row["left_imag"], row["right_imag"])
        expected = row["expected_half_plane"]
        if expected == "lower" and not all(value < 0.0 for value in imag_parts):
            turning_point_failures += 1
        elif expected == "upper" and not all(value > 0.0 for value in imag_parts):
            turning_point_failures += 1
        elif expected == "real" and not all(abs(value) < 1e-12 for value in imag_parts):
            turning_point_failures += 1

    hermitian_rows = quantitative_claims["hermitian_abs_x_spectrum"]
    maximum_hermitian_n = max(row["N"] for row in hermitian_rows)
    square_well_error = max(
        row["relative_square_well_error"]
        for row in hermitian_rows
        if row["N"] == maximum_hermitian_n
    )
    hermitian_n2_error = max(
        abs(row["exact_fd"] - (2 * row["n"] + 1))
        for row in hermitian_rows
        if row["N"] == 2.0
    )
    near_one_slope_error = abs(
        quantitative_claims["near_one_logarithmic_scaling_slope"] - 2.0 / 3.0
    )

    contour_rows = quantitative_claims["contour_deformation_spectra"]
    contour_max_difference = 0.0
    for exponent in sorted({row["N"] for row in contour_rows}):
        for level in sorted(
            {row["level"] for row in contour_rows if row["N"] == exponent}
        ):
            values = [
                complex(row["energy_real"], row["energy_imag"])
                for row in contour_rows
                if row["N"] == exponent and row["level"] == level
            ]
            contour_max_difference = max(
                contour_max_difference,
                max(abs(value - values[0]) for value in values[1:]),
            )

    turning_point_residual = max(
        abs(
            row["energy"]
            + (1j * complex(row["left_real"], row["left_imag"])) ** row["N"]
        )
        for row in quantitative_claims["complex_wkb_turning_points"]
    )
    wkb_domain_failures = 0
    for row in quantitative_claims["complex_wkb_turning_points"]:
        crossing = row["branch_cut_intersection_imag"]
        crosses_cut = row["crosses_positive_imaginary_branch_cut"]
        path_valid = row["continuous_wkb_path_valid"]
        if row["expected_half_plane"] == "upper":
            wkb_domain_failures += int(crossing <= 0.0 or not crosses_cut or path_valid)
        else:
            wkb_domain_failures += int(
                crossing > 1e-12 or crosses_cut or not path_valid
            )

    wkb_growth_failures = 0
    for level in sorted(
        {row["level"] for row in quantitative_claims["massless_wkb_large_n"]}
    ):
        energies = [
            row["wkb_energy"]
            for row in sorted(
                (
                    row
                    for row in quantitative_claims["massless_wkb_large_n"]
                    if row["level"] == level
                ),
                key=lambda row: row["N"],
            )
        ]
        wkb_growth_failures += sum(
            right <= left for left, right in zip(energies, energies[1:])
        )

    visible_unbroken = [
        row for row in fig1_rows if row["N"] >= 2.0 and row["visible_in_paper_window"]
    ]
    massless_unbroken_failures = sum(
        (not row["is_real"]) or row["energy_real"] <= 0.0 for row in visible_unbroken
    )
    below_threshold = [row for row in fig1_rows if abs(row["N"] - 1.421) < 1e-12]
    above_threshold = [row for row in fig1_rows if abs(row["N"] - 1.423) < 1e-12]
    threshold_failures = int(
        sum(row["is_real"] for row in below_threshold) != 1
        or sum(row["is_real"] for row in above_threshold) < 3
        or not any(not row["is_real"] for row in below_threshold)
    )
    exceptional_point_rows = sorted(
        quantitative_claims["exceptional_point_convergence"],
        key=lambda row: row["points"],
    )
    exceptional_point_estimate = exceptional_point_rows[-1]["estimated_N"]
    exceptional_point_resolution_difference = abs(
        exceptional_point_rows[-1]["estimated_N"]
        - exceptional_point_rows[-2]["estimated_N"]
    )
    exceptional_point_printed_difference = abs(
        exceptional_point_estimate - float(references["exceptional_point"])
    )
    near_one_ground = sorted(
        (
            row
            for row in fig1_rows
            if row["solver"] == "riccati_shooting" and row["mode_rank"] == 0
        ),
        key=lambda row: row["N"] - 1.0,
    )
    near_one_divergence_failures = sum(
        right["energy_real"] >= left["energy_real"]
        for left, right in zip(near_one_ground, near_one_ground[1:])
    )

    merger_rows = quantitative_claims["near_n2_two_level_mergers"]
    merger_orders = sorted({row["quadrature_order"] for row in merger_rows})
    merger_levels = sorted({int(row["level_lower"]) for row in merger_rows})
    merger_quadrature_difference = 0.0
    for level in merger_levels:
        values = [
            next(
                row["epsilon_merger"]
                for row in merger_rows
                if row["quadrature_order"] == order and int(row["level_lower"]) == level
            )
            for order in merger_orders
        ]
        merger_quadrature_difference = max(
            merger_quadrature_difference, max(values) - min(values)
        )
    finest_mergers = [
        next(
            row["epsilon_merger"]
            for row in merger_rows
            if row["quadrature_order"] == merger_orders[-1]
            and int(row["level_lower"]) == level
        )
        for level in merger_levels
    ]
    merger_order_failures = sum(
        right >= left for left, right in zip(finest_mergers, finest_mergers[1:])
    )

    classical_near = sorted(
        quantitative_claims["classical_near_transition"], key=lambda row: row["N"]
    )
    classical_spiral_failures = sum(
        right["escape_angle"] <= left["escape_angle"]
        for left, right in zip(classical_near, classical_near[1:])
    )
    trajectory_passages = quantitative_claims["classical_spiral_passages"]
    trajectory_failures = int(
        len(trajectory_passages) < int(tolerance["classical_trajectory_min_passages"])
    )
    correspondence_rows = sorted(
        quantitative_claims["classical_quantum_event_correspondence"],
        key=lambda row: row["level_lower"],
    )
    classical_quantum_mapping_failures = sum(
        right["epsilon_merger"] >= left["epsilon_merger"]
        or right["classical_turning_points_before_escape"]
        <= left["classical_turning_points_before_escape"]
        for left, right in zip(correspondence_rows, correspondence_rows[1:])
    )

    massive_anchor_errors = [
        abs(row["energy_real"] - row["exact_energy"])
        for row in quantitative_claims["massive_phase_anchors"]
    ]
    massive_anchor_imag = [
        abs(row["energy_imag"]) for row in quantitative_claims["massive_phase_anchors"]
    ]
    massive_phase_failures = 0
    for mass_squared in sorted({row["mass_squared"] for row in fig3_rows}):
        counts = {}
        for exponent in (0.0, 0.8, 1.0, 1.1):
            probe = [
                row
                for row in fig3_rows
                if row["mass_squared"] == mass_squared
                and abs(row["N"] - exponent) < 1e-12
            ]
            counts[exponent] = sum(row["is_real"] for row in probe)
        massive_phase_failures += int(
            counts[0.0]
            != len(
                [
                    row
                    for row in fig3_rows
                    if row["mass_squared"] == mass_squared and row["N"] == 0.0
                ]
            )
            or counts[1.0]
            != len(
                [
                    row
                    for row in fig3_rows
                    if row["mass_squared"] == mass_squared and row["N"] == 1.0
                ]
            )
            or counts[0.8] >= counts[1.0]
            or counts[1.1] >= counts[1.0]
            or counts[0.8] % 2 != 0
            or (counts[1.1] - 1) % 2 != 0
        )

    two_solver_difference = max(
        (
            row["absolute_difference"]
            for row in quantitative_claims["same_parameter_two_solver_crosscheck"]
        ),
        default=0.0,
    )

    checks = [
        check_record(
            "table_i_exact_values",
            max(exact_i_errors, default=0.0),
            tolerance["table_i_exact_max_abs_error"],
            target_ids=["T002", "T003"],
            claim_ids=["I018_table1_exact_vs_wkb"],
        ),
        check_record(
            "table_i_wkb_formula",
            max(wkb_i_errors, default=0.0),
            tolerance["printed_four_digit_formula_tolerance"],
            target_ids=["T002", "T003", "T008"],
            claim_ids=["I018_table1_exact_vs_wkb", "I016_leading_wkb_spectrum"],
        ),
        check_record(
            "table_i_resolution_convergence",
            table_i_resolution_difference,
            tolerance["table_i_resolution_max_abs_difference"],
            target_ids=["T002", "T003"],
            claim_ids=["I018_table1_exact_vs_wkb"],
        ),
        check_record(
            "table_ii_first_four_exact_values",
            max(table_ii_exact_errors[:4], default=0.0),
            tolerance["table_ii_first_four_max_abs_error"],
            target_ids=["T004"],
            claim_ids=["I022_table2_near_N1_ground_state"],
        ),
        check_record(
            "table_ii_asymptotic_formula",
            max(table_ii_asymptotic_errors, default=0.0),
            tolerance["printed_four_digit_formula_tolerance"],
            target_ids=["T004", "T010"],
            claim_ids=[
                "I021_near_N1_ground_state_asymptotics",
                "I022_table2_near_N1_ground_state",
            ],
        ),
        check_record(
            "table_ii_independent_solver_agreement",
            max(table_ii_solver_differences, default=0.0),
            tolerance["table_ii_independent_solver_max_abs_difference"],
            target_ids=["T004", "T023"],
            claim_ids=[
                "I015_two_solver_numerical_crosscheck",
                "I022_table2_near_N1_ground_state",
            ],
        ),
        check_record(
            "table_ii_domain_convergence",
            max(domain_differences, default=0.0),
            tolerance["table_ii_domain_max_abs_difference"],
            target_ids=["T004"],
            claim_ids=["I022_table2_near_N1_ground_state"],
        ),
        check_record(
            "massless_n2_harmonic_spectrum",
            n2_error,
            tolerance["harmonic_n2_max_abs_error"],
            target_ids=["T001", "T013", "T017"],
            claim_ids=[
                "I003_harmonic_oscillator_exact_spectrum",
                "I007_figure1_massless_energy_branches",
                "I008_massless_unbroken_region",
            ],
        ),
        check_record(
            "massive_n1_shifted_oscillator",
            max(massive_errors, default=np.inf),
            tolerance["massive_n1_max_abs_error"],
            target_ids=["T005", "T006", "T007", "T029"],
            claim_ids=[
                "I026_figure3_massive_energy_branches",
                "I027_massive_phase_structure",
            ],
        ),
        check_record(
            "bessis_cubic_spectrum_real",
            max(abs(row["energy_imag"]) for row in cubic_by_case["bessis_x2_plus_ix3"]),
            tolerance["intro_pt_cubic_max_abs_imag"],
            target_ids=["T011"],
            claim_ids=["I001_bessis_cubic_spectrum"],
        ),
        check_record(
            "bessis_cubic_spectrum_positive",
            max(
                0.0,
                -min(row["energy_real"] for row in cubic_by_case["bessis_x2_plus_ix3"]),
            ),
            0.0,
            target_ids=["T011"],
            claim_ids=["I001_bessis_cubic_spectrum"],
        ),
        check_record(
            "pt_cubic_linear_spectrum_real_positive",
            max(
                max(abs(row["energy_imag"]) for row in cubic_by_case["pt_ix3_plus_ix"]),
                max(
                    0.0,
                    -min(row["energy_real"] for row in cubic_by_case["pt_ix3_plus_ix"]),
                ),
            ),
            tolerance["intro_pt_cubic_max_abs_imag"],
            target_ids=["T012"],
            claim_ids=["I002_cubic_linear_pt_contrast"],
        ),
        check_record(
            "nonpt_cubic_linear_spectrum_complex",
            max(
                0.0, tolerance["intro_nonpt_cubic_min_abs_imag"] - cubic_nonpt_min_imag
            ),
            0.0,
            target_ids=["T012"],
            claim_ids=["I002_cubic_linear_pt_contrast"],
        ),
        check_record(
            "harmonic_oscillator_exact_sequence",
            max(shifted_errors["harmonic"], default=np.inf),
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T013"],
            claim_ids=["I003_harmonic_oscillator_exact_spectrum"],
        ),
        check_record(
            "imaginary_linear_shift_exact_sequence",
            max(shifted_errors["plus_ix"], default=np.inf),
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T014"],
            claim_ids=["I004_imaginary_linear_shift_spectrum"],
        ),
        check_record(
            "real_linear_shift_exact_sequence",
            max(shifted_errors["minus_x"], default=np.inf),
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T015"],
            claim_ids=["I005_real_linear_shift_spectrum"],
        ),
        check_record(
            "combined_linear_shift_complex_sequence",
            max(shifted_errors["plus_ix_minus_x"], default=np.inf),
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T016"],
            claim_ids=["I006_combined_linear_shift_complex_spectrum"],
        ),
        check_record(
            "stokes_wedge_geometry",
            wedge_error,
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T020"],
            claim_ids=["I012_antistokes_wedge_geometry"],
        ),
        check_record(
            "n1_airy_matching_obstruction",
            airy_error,
            tolerance["airy_identity_max_abs_error"],
            target_ids=["T019", "T025"],
            claim_ids=[
                "I010_massless_N1_boundary",
                "I020_exact_N1_airy_no_real_eigenvalue",
            ],
        ),
        check_record(
            "classical_n2_period_anchor",
            abs(n2_period - np.pi),
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T027"],
            claim_ids=["I024_classical_period_transition"],
        ),
        check_record(
            "complex_wkb_turning_point_half_planes",
            float(turning_point_failures),
            0.0,
            target_ids=["T022", "T024"],
            claim_ids=[
                "I014_turning_point_formula_and_location",
                "I017_wkb_domain_failure_below_N2",
            ],
        ),
        check_record(
            "hermitian_n2_harmonic_anchor",
            hermitian_n2_error,
            tolerance["hermitian_n2_max_abs_error"],
            target_ids=["T009"],
            claim_ids=["I019_absolute_power_potential_limit"],
        ),
        check_record(
            "hermitian_square_well_limit",
            square_well_error,
            tolerance["hermitian_square_well_max_relative_error"],
            target_ids=["T009"],
            claim_ids=["I019_absolute_power_potential_limit"],
        ),
        check_record(
            "hermitian_resolution_convergence",
            quantitative_claims["hermitian_resolution_max_abs_difference"],
            tolerance["hermitian_resolution_max_abs_difference"],
            target_ids=["T009"],
            claim_ids=["I019_absolute_power_potential_limit"],
        ),
        check_record(
            "near_one_logarithmic_two_thirds_scaling",
            near_one_slope_error,
            tolerance["near_one_logarithmic_slope_max_abs_error"],
            target_ids=["T010", "T019"],
            claim_ids=[
                "I010_massless_N1_boundary",
                "I021_near_N1_ground_state_asymptotics",
            ],
        ),
        check_record(
            "complex_contour_deformation_invariance",
            contour_max_difference,
            tolerance["contour_deformation_max_abs_difference"],
            target_ids=["T021"],
            claim_ids=["I013_complex_contour_deformation_invariance"],
        ),
        check_record(
            "complex_turning_point_equation_residual",
            turning_point_residual,
            tolerance["analytic_identity_max_abs_error"],
            target_ids=["T022"],
            claim_ids=["I014_turning_point_formula_and_location"],
        ),
        check_record(
            "same_parameter_two_solver_crosscheck",
            two_solver_difference,
            tolerance["table_ii_independent_solver_max_abs_difference"],
            target_ids=["T023"],
            claim_ids=["I015_two_solver_numerical_crosscheck"],
        ),
        check_record(
            "wkb_contour_domain_boundary",
            float(wkb_domain_failures),
            0.0,
            target_ids=["T024"],
            claim_ids=["I017_wkb_domain_failure_below_N2"],
        ),
        check_record(
            "massless_unbroken_sample_real_positive",
            float(massless_unbroken_failures),
            0.0,
            target_ids=["T017"],
            claim_ids=["I008_massless_unbroken_region"],
        ),
        check_record(
            "massless_large_n_wkb_divergence",
            float(wkb_growth_failures),
            0.0,
            target_ids=["T008", "T017"],
            claim_ids=["I008_massless_unbroken_region", "I016_leading_wkb_spectrum"],
        ),
        check_record(
            "massless_broken_region_threshold",
            float(threshold_failures),
            0.0,
            target_ids=["T018"],
            claim_ids=["I009_massless_broken_region_and_threshold"],
        ),
        check_record(
            "exceptional_point_independent_location",
            exceptional_point_printed_difference,
            tolerance["exceptional_point_max_abs_error"],
            target_ids=["T018"],
            claim_ids=["I009_massless_broken_region_and_threshold"],
        ),
        check_record(
            "exceptional_point_resolution_convergence",
            exceptional_point_resolution_difference,
            tolerance["exceptional_point_resolution_max_abs_difference"],
            target_ids=["T018"],
            claim_ids=["I009_massless_broken_region_and_threshold"],
        ),
        check_record(
            "massless_near_n1_ground_divergence",
            float(near_one_divergence_failures),
            0.0,
            target_ids=["T019"],
            claim_ids=["I010_massless_N1_boundary"],
        ),
        check_record(
            "near_n2_merger_quadrature_convergence",
            merger_quadrature_difference,
            tolerance["near_n2_quadrature_max_abs_difference"],
            target_ids=["T026"],
            claim_ids=["I023_near_N2_level_merging_perturbation"],
        ),
        check_record(
            "near_n2_high_levels_merge_first",
            float(merger_order_failures),
            0.0,
            target_ids=["T026", "T028"],
            claim_ids=[
                "I023_near_N2_level_merging_perturbation",
                "I025_classical_spiral_and_quantum_mergers",
            ],
        ),
        check_record(
            "classical_spiral_rotation_diverges_below_n2",
            float(classical_spiral_failures),
            0.0,
            target_ids=["T028"],
            claim_ids=["I025_classical_spiral_and_quantum_mergers"],
        ),
        check_record(
            "classical_spiral_trajectory_energy_conservation",
            float(quantitative_claims["classical_spiral_energy_max_abs_error"]),
            tolerance["classical_trajectory_energy_max_abs_error"],
            target_ids=["T028"],
            claim_ids=["I025_classical_spiral_and_quantum_mergers"],
        ),
        check_record(
            "classical_spiral_turning_point_passages",
            float(trajectory_failures),
            0.0,
            target_ids=["T028"],
            claim_ids=["I025_classical_spiral_and_quantum_mergers"],
        ),
        check_record(
            "classical_quantum_event_order_correspondence",
            float(classical_quantum_mapping_failures),
            0.0,
            target_ids=["T028"],
            claim_ids=["I025_classical_spiral_and_quantum_mergers"],
        ),
        check_record(
            "massive_n0_n1_n2_exact_anchors",
            max(max(massive_anchor_errors), max(massive_anchor_imag)),
            tolerance["massive_phase_anchor_max_abs_error"],
            target_ids=["T029"],
            claim_ids=["I027_massive_phase_structure"],
        ),
        check_record(
            "massive_pairwise_phase_structure",
            float(massive_phase_failures),
            0.0,
            target_ids=["T029"],
            claim_ids=["I027_massive_phase_structure"],
        ),
    ]
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": (
            "passed" if all(item["status"] == "passed" for item in checks) else "failed"
        ),
        "checks": checks,
        "table_ii_paper_discrepancies": discrepancy_rows,
        "paper_error_candidate_emitted": False,
        "paper_assessment": (
            "inconclusive_pending_fresh_review"
            if discrepancy_rows
            else "paper_supported_pending_fresh_review"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    arguments = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(arguments.config).resolve()
    output_root = Path(arguments.output_root).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "physics-9712001":
        raise ValueError("config paper_id mismatch")

    parameters = config["parameters"]
    real_tolerance = float(parameters["real_imag_tolerance"])
    fig1_rows = run_fig1(parameters["fig1"], real_tolerance)
    table_i_rows, table_i_resolution_difference = run_table_i(parameters["table_i"])
    table_ii_rows = run_table_ii(parameters["table_ii"])
    fig3_rows = run_fig3(parameters["fig3"], real_tolerance)
    quantitative_claims = run_quantitative_claims(parameters["claim_audit"])

    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    spectrum_fields = [
        "N",
        "mass_squared",
        "mode_rank",
        "energy_real",
        "energy_imag",
        "is_real",
        "visible_in_paper_window",
        "solver",
    ]
    write_csv(data_dir / "fig1_massless_spectrum.csv", spectrum_fields, fig1_rows)
    write_csv(
        data_dir / "table_i_exact_wkb.csv",
        ["N", "n", "exact_fd", "exact_imag", "coarse_fd", "wkb"],
        table_i_rows,
    )
    write_csv(
        data_dir / "table_ii_near_one.csv",
        [
            "epsilon",
            "N",
            "exact_shooting",
            "patch_residual",
            "secondary_boundary_energy",
            "finite_difference_energy",
            "finite_difference_imag",
            "asymptotic_eq11",
        ],
        table_ii_rows,
    )
    write_csv(data_dir / "fig3_massive_spectrum.csv", spectrum_fields, fig3_rows)
    write_json(data_dir / "quantitative_claim_checks.json", quantitative_claims)

    science = build_science_checks(
        config,
        fig1_rows,
        table_i_rows,
        table_i_resolution_difference,
        table_ii_rows,
        fig3_rows,
        quantitative_claims,
    )
    write_json(checks_dir / "science_checks.json", science)

    data_paths = sorted(data_dir.glob("*.csv")) + [
        data_dir / "quantitative_claim_checks.json"
    ]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "status": science["status"],
        "config_path": str(config_path),
        "config_sha256": sha256(config_path),
        "generated_data": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in data_paths
        ],
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }
    write_json(checks_dir / "generated_data_manifest.json", manifest)
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "status": science["status"],
        "elapsed_seconds": time.perf_counter() - started,
        "fig1_rows": len(fig1_rows),
        "fig3_rows": len(fig3_rows),
        "table_i_rows": len(table_i_rows),
        "table_ii_rows": len(table_ii_rows),
        "paper_error_candidate_emitted": False,
        "paper_assessment": science["paper_assessment"],
    }
    write_json(checks_dir / "run_summary.json", summary)
    print(json.dumps(summary, sort_keys=True, default=json_default))


if __name__ == "__main__":
    main()
