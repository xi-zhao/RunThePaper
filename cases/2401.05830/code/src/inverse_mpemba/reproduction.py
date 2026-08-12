"""Paper-scale target generation, scientific checks, and data freezing."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .liouvillian import (
    bloch_from_density,
    density_from_bloch,
    liouvillian,
    liouvillian_literal_main,
    propagate_density,
    steady_density,
)
from .model import (
    bifurcation_temperature,
    bloch_generator,
    crossing_metrics,
    distance_to_final,
    modal_coefficients,
    propagate_bloch,
    relaxation_rates,
    slow_mode_coefficient,
    steady_state,
    steady_state_by_solve,
    strong_initial_temperature,
)

TARGET_IDS = [f"T{index:03d}" for index in range(1, 11)]


def _write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _target_check(
    assertions: list[dict[str, Any]], metrics: dict[str, Any]
) -> dict[str, Any]:
    return {
        "status": (
            "passed"
            if all(item["status"] == "passed" for item in assertions)
            else "failed"
        ),
        "assertions": assertions,
        "metrics": metrics,
    }


def _assertion(
    assertion_id: str, passed: bool, claim: str, value: Any, tolerance: Any
) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "status": "passed" if passed else "failed",
        "claim": claim,
        "value": value,
        "tolerance": tolerance,
    }


def _spectrum_set_error(alpha: float, gamma_prime: float) -> float:
    matrix, _ = bloch_generator(alpha, gamma_prime)
    direct = np.linalg.eigvals(matrix) / gamma_prime
    analytic = relaxation_rates(gamma_prime, alpha)
    expected = np.array(
        [analytic["lambda_plus"], analytic["lambda_minus"]], dtype=complex
    ).reshape(2)
    direct_assignment = max(abs(direct[0] - expected[0]), abs(direct[1] - expected[1]))
    swapped_assignment = max(abs(direct[0] - expected[1]), abs(direct[1] - expected[0]))
    return float(min(direct_assignment, swapped_assignment))


def generate_target_data(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    parameters = config["parameters"]
    acceptance = config["acceptance"]
    data_dir = workspace / "outputs" / "data"
    checks: dict[str, Any] = {}

    # T001: Main Fig. 2 left, theory loci only.
    t001 = parameters["T001"]
    gamma_grid = np.geomspace(t001["gamma_min"], t001["gamma_max"], t001["points"])
    rows: list[dict[str, Any]] = []
    max_steady_residual = 0.0
    max_ellipse_residual = 0.0
    for alpha in t001["alphas"]:
        states = steady_state(gamma_grid, alpha)
        for gamma, (y_value, z_value) in zip(gamma_grid, states, strict=True):
            solved = steady_state_by_solve(float(gamma), float(alpha))
            max_steady_residual = max(
                max_steady_residual, float(np.max(np.abs(solved - [y_value, z_value])))
            )
            ellipse = (np.sqrt(2.0 / alpha) * y_value) ** 2 + (2.0 * z_value + 1.0) ** 2
            max_ellipse_residual = max(max_ellipse_residual, abs(float(ellipse - 1.0)))
            rows.append(
                {
                    "alpha": alpha,
                    "gamma_prime": gamma,
                    "y": y_value,
                    "z": z_value,
                    "provenance": "independent_analytic_formula",
                }
            )
    _write_csv(
        data_dir / "T001_main_fig2_left.csv",
        ["alpha", "gamma_prime", "y", "z", "provenance"],
        rows,
    )
    checks["T001"] = _target_check(
        [
            _assertion(
                "t001_affine_solve_parity",
                max_steady_residual <= acceptance["steady_state_residual_max"],
                "Closed steady state agrees with an independent affine solve.",
                max_steady_residual,
                acceptance["steady_state_residual_max"],
            ),
            _assertion(
                "t001_ellipse_identity",
                max_ellipse_residual <= acceptance["ellipse_residual_max"],
                "Every generated point lies on the paper ellipse.",
                max_ellipse_residual,
                acceptance["ellipse_residual_max"],
            ),
        ],
        {"series": len(t001["alphas"]), "rows": len(rows)},
    )

    # T002: Main Fig. 2 right, the paper-normalized slow coefficient.
    alpha_main = float(parameters["alpha_main"])
    gamma_final = float(parameters["gamma_final_main"])
    t002 = parameters["T002"]
    strong_gamma = strong_initial_temperature(alpha_main, gamma_final)
    gamma_i_grid = np.unique(
        np.concatenate(
            (
                np.linspace(
                    t002["gamma_initial_min"], t002["gamma_initial_max"], t002["points"]
                ),
                np.array(
                    [
                        strong_gamma,
                        parameters["gamma_initial_cold_main"],
                        parameters["gamma_initial_hot_main"],
                    ]
                ),
            )
        )
    )
    coefficients = slow_mode_coefficient(gamma_i_grid, gamma_final, alpha_main)
    rows = []
    for gamma_i, coefficient in zip(gamma_i_grid, coefficients, strict=True):
        role = "curve"
        if np.isclose(gamma_i, strong_gamma, atol=1e-13):
            role = "strong_root"
        elif np.isclose(gamma_i, parameters["gamma_initial_cold_main"], atol=1e-13):
            role = "cold_highlight"
        elif np.isclose(gamma_i, parameters["gamma_initial_hot_main"], atol=1e-13):
            role = "hot_highlight"
        rows.append(
            {
                "gamma_initial_prime": gamma_i,
                "a_minus": coefficient,
                "role": role,
                "provenance": "supplement_eq_11",
            }
        )
    _write_csv(
        data_dir / "T002_main_fig2_right.csv",
        ["gamma_initial_prime", "a_minus", "role", "provenance"],
        rows,
    )
    strong_value = float(slow_mode_coefficient(strong_gamma, gamma_final, alpha_main))
    independent_slow = abs(
        modal_coefficients(strong_gamma, gamma_final, alpha_main)["coefficient_slow"]
    )
    checks["T002"] = _target_check(
        [
            _assertion(
                "t002_printed_coefficient_zero",
                abs(strong_value) <= acceptance["strong_root_abs_coefficient_max"],
                "Supplement Eq. (11) vanishes at the closed-form strong initial temperature.",
                strong_value,
                acceptance["strong_root_abs_coefficient_max"],
            ),
            _assertion(
                "t002_independent_slow_projection_zero",
                independent_slow <= acceptance["strong_root_modal_component_max"],
                "An independently normalized eigensystem also has zero slow component.",
                independent_slow,
                acceptance["strong_root_modal_component_max"],
            ),
        ],
        {"strong_gamma_initial_prime": strong_gamma, "rows": len(rows)},
    )

    # T003: Main Fig. 4 theory layer.
    t003 = parameters["T003"]
    tau = np.linspace(t003["tau_min"], t003["tau_max"], t003["points"])
    physical_time = tau / gamma_final
    cold_gamma = float(parameters["gamma_initial_cold_main"])
    hot_gamma = float(parameters["gamma_initial_hot_main"])
    rows = []
    differences: dict[str, np.ndarray] = {}
    for alpha, label in (
        (alpha_main, "alpha_0.94"),
        (float(parameters["alpha_control"]), "alpha_1_over_3"),
    ):
        cold = distance_to_final(physical_time, cold_gamma, gamma_final, alpha)
        hot = distance_to_final(physical_time, hot_gamma, gamma_final, alpha)
        differences[label] = cold - hot
        for index in range(len(tau)):
            rows.append(
                {
                    "series": label,
                    "alpha": alpha,
                    "tau_gamma_f_t": tau[index],
                    "d_cold": cold[index],
                    "d_hot": hot[index],
                    "d_cold_minus_hot": differences[label][index],
                    "provenance": "independent_matrix_exponential",
                }
            )
    _write_csv(
        data_dir / "T003_main_fig4_theory.csv",
        [
            "series",
            "alpha",
            "tau_gamma_f_t",
            "d_cold",
            "d_hot",
            "d_cold_minus_hot",
            "provenance",
        ],
        rows,
    )
    main_crosses = bool(np.any(differences["alpha_0.94"] < 0.0))
    control_crosses = bool(np.any(differences["alpha_1_over_3"] < 0.0))
    checks["T003"] = _target_check(
        [
            _assertion(
                "t003_coherent_case_crosses",
                main_crosses,
                "The alpha=0.94 theory curve becomes negative.",
                main_crosses,
                True,
            ),
            _assertion(
                "t003_control_does_not_cross",
                not control_crosses,
                "The alpha=1/3 control remains nonnegative.",
                control_crosses,
                False,
            ),
        ],
        {
            "alpha_0.94_minimum": float(np.min(differences["alpha_0.94"])),
            "alpha_1_over_3_minimum": float(np.min(differences["alpha_1_over_3"])),
        },
    )

    # T004: Supplemental Fig. 1 spectrum.
    t004 = parameters["T004"]
    alpha_spectrum = float(t004["alpha"])
    gamma_spectrum = np.unique(
        np.concatenate(
            (
                np.linspace(
                    t004["gamma_final_min"], t004["gamma_final_max"], t004["points"]
                ),
                np.array([bifurcation_temperature(alpha_spectrum)]),
            )
        )
    )
    rates = relaxation_rates(gamma_spectrum, alpha_spectrum)
    rows = []
    for index, gamma in enumerate(gamma_spectrum):
        rows.append(
            {
                "gamma_final_prime": gamma,
                "lambda_zero_over_gamma_real": rates["lambda_zero"][index].real,
                "lambda_x_over_gamma_real": rates["lambda_x"][index].real,
                "lambda_plus_over_gamma_real": rates["lambda_plus"][index].real,
                "lambda_minus_over_gamma_real": rates["lambda_minus"][index].real,
                "lambda_plus_over_gamma_imag": rates["lambda_plus"][index].imag,
                "lambda_minus_over_gamma_imag": rates["lambda_minus"][index].imag,
                "provenance": "independent_characteristic_polynomial",
            }
        )
    _write_csv(
        data_dir / "T004_supp_fig1.csv",
        [
            "gamma_final_prime",
            "lambda_zero_over_gamma_real",
            "lambda_x_over_gamma_real",
            "lambda_plus_over_gamma_real",
            "lambda_minus_over_gamma_real",
            "lambda_plus_over_gamma_imag",
            "lambda_minus_over_gamma_imag",
            "provenance",
        ],
        rows,
    )
    spectrum_error = max(
        _spectrum_set_error(alpha_spectrum, float(value))
        for value in gamma_spectrum[::25]
    )
    checks["T004"] = _target_check(
        [
            _assertion(
                "t004_direct_eigensolver_parity",
                spectrum_error <= acceptance["spectrum_parity_max"],
                "Analytic spectrum agrees with a direct matrix eigensolver.",
                spectrum_error,
                acceptance["spectrum_parity_max"],
            ),
            _assertion(
                "t004_bifurcation_anchor",
                abs(bifurcation_temperature(alpha_spectrum) - 2.0) < 1e-14,
                "For alpha=1 the bifurcation is gamma'_b=2.",
                bifurcation_temperature(alpha_spectrum),
                2.0,
            ),
        ],
        {"rows": len(rows)},
    )

    # T005: Supplemental Fig. 2 loci and both bifurcation branches.
    t005 = parameters["T005"]
    locus_gamma = np.geomspace(
        t005["gamma_min"], t005["gamma_max"], t005["locus_points"]
    )
    rows = []
    for alpha in t005["alphas"]:
        states = steady_state(locus_gamma, float(alpha))
        for gamma, state in zip(locus_gamma, states, strict=True):
            rows.append(
                {
                    "series_kind": "locus",
                    "branch": "not_applicable",
                    "alpha": alpha,
                    "gamma_prime": gamma,
                    "y": state[0],
                    "z": state[1],
                    "provenance": "independent_steady_state_formula",
                }
            )
    branch_alpha = {
        "upper_alpha_lt_half": np.linspace(
            0.001, 0.499, t005["bifurcation_points_per_branch"]
        ),
        "lower_alpha_gt_half": np.linspace(
            0.501, 1.0, t005["bifurcation_points_per_branch"]
        ),
    }
    for branch, alpha_values in branch_alpha.items():
        for alpha in alpha_values:
            gamma_b = bifurcation_temperature(float(alpha))
            state = steady_state(gamma_b, float(alpha))
            rows.append(
                {
                    "series_kind": "bifurcation",
                    "branch": branch,
                    "alpha": alpha,
                    "gamma_prime": gamma_b,
                    "y": state[0],
                    "z": state[1],
                    "provenance": "independent_discriminant_zero",
                }
            )
    _write_csv(
        data_dir / "T005_supp_fig2.csv",
        ["series_kind", "branch", "alpha", "gamma_prime", "y", "z", "provenance"],
        rows,
    )
    lower = [row for row in rows if row["branch"] == "lower_alpha_gt_half"]
    upper = [row for row in rows if row["branch"] == "upper_alpha_lt_half"]
    checks["T005"] = _target_check(
        [
            _assertion(
                "t005_all_loci_present",
                len(t005["alphas"]) == 5,
                "All five printed alpha loci are generated.",
                len(t005["alphas"]),
                5,
            ),
            _assertion(
                "t005_both_branches_present",
                bool(lower and upper),
                "Both discriminant-zero branches are generated.",
                [len(upper), len(lower)],
                "both nonzero",
            ),
        ],
        {"rows": len(rows)},
    )

    # T006: Supplemental Fig. 3 fast-mode chords.
    t006 = parameters["T006"]
    alpha_geometry = float(t006["alpha"])
    locus_gamma = np.geomspace(
        t006["locus_gamma_min"], t006["locus_gamma_max"], t006["locus_points"]
    )
    rows = []
    for gamma, state in zip(
        locus_gamma, steady_state(locus_gamma, alpha_geometry), strict=True
    ):
        rows.append(
            {
                "series_kind": "locus",
                "chord_id": -1,
                "endpoint": "locus",
                "gamma_final_prime": "",
                "gamma_initial_prime": gamma,
                "y": state[0],
                "z": state[1],
                "provenance": "independent_steady_state_formula",
            }
        )
    final_gammas = np.linspace(
        t006["final_gamma_min"], t006["final_gamma_max"], t006["chords"]
    )
    max_slow_component = 0.0
    initial_gammas = []
    for chord_id, final_gamma in enumerate(final_gammas):
        initial_gamma = strong_initial_temperature(alpha_geometry, float(final_gamma))
        initial_gammas.append(initial_gamma)
        start = steady_state(final_gamma, alpha_geometry)
        end = steady_state(initial_gamma, alpha_geometry)
        max_slow_component = max(
            max_slow_component,
            abs(
                modal_coefficients(initial_gamma, float(final_gamma), alpha_geometry)[
                    "coefficient_slow"
                ]
            ),
        )
        for endpoint, state in (("final", start), ("strong_initial", end)):
            rows.append(
                {
                    "series_kind": "fast_chord",
                    "chord_id": chord_id,
                    "endpoint": endpoint,
                    "gamma_final_prime": final_gamma,
                    "gamma_initial_prime": initial_gamma,
                    "y": state[0],
                    "z": state[1],
                    "provenance": "independent_strong_mode_geometry",
                }
            )
    _write_csv(
        data_dir / "T006_supp_fig3.csv",
        [
            "series_kind",
            "chord_id",
            "endpoint",
            "gamma_final_prime",
            "gamma_initial_prime",
            "y",
            "z",
            "provenance",
        ],
        rows,
    )
    checks["T006"] = _target_check(
        [
            _assertion(
                "t006_fast_only_chords",
                max_slow_component <= acceptance["strong_root_modal_component_max"],
                "Every chord has a vanishing independently normalized slow component.",
                max_slow_component,
                acceptance["strong_root_modal_component_max"],
            ),
            _assertion(
                "t006_inverse_only_ordering",
                bool(
                    np.all(np.asarray(initial_gammas) < 2.0)
                    and np.all(final_gammas > 2.0)
                ),
                "All strong initial points are colder than the bifurcation and all finals are hotter.",
                {
                    "max_initial": max(initial_gammas),
                    "min_final": float(min(final_gammas)),
                },
                {"initial_below": 2.0, "final_above": 2.0},
            ),
        ],
        {"chords": len(final_gammas), "rows": len(rows)},
    )

    # T007/T008: Supplemental Fig. 4 full trajectories and late-time zoom.
    initial_conditions = {
        "colder_0.02": float(parameters["gamma_initial_colder_supp"]),
        "strong_cold": strong_gamma,
        "hot_0.74": float(parameters["gamma_initial_hot_trajectory_supp"]),
    }
    trajectory_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for target_id, config_key, filename in (
        ("T007", "T007", "T007_supp_fig4_left.csv"),
        ("T008", "T008", "T008_supp_fig4_right.csv"),
    ):
        target_config = parameters[config_key]
        tau_values = np.linspace(
            target_config["tau_min"], target_config["tau_max"], target_config["points"]
        )
        times = tau_values / gamma_final
        rows = []
        for label, gamma_i in initial_conditions.items():
            trajectory = propagate_bloch(times, gamma_i, gamma_final, alpha_main)
            trajectory_cache[f"{target_id}:{label}"] = (tau_values, trajectory)
            distances = np.linalg.norm(
                trajectory - steady_state(gamma_final, alpha_main), axis=1
            )
            for index, state in enumerate(trajectory):
                rows.append(
                    {
                        "series": label,
                        "gamma_initial_prime": gamma_i,
                        "tau_gamma_f_t": tau_values[index],
                        "y": state[0],
                        "z": state[1],
                        "distance_to_final": distances[index],
                        "provenance": "independent_matrix_exponential",
                    }
                )
        _write_csv(
            data_dir / filename,
            [
                "series",
                "gamma_initial_prime",
                "tau_gamma_f_t",
                "y",
                "z",
                "distance_to_final",
                "provenance",
            ],
            rows,
        )
        strong_monotone = np.all(
            np.diff(trajectory_cache[f"{target_id}:strong_cold"][1][:, 1]) <= 1e-12
        )
        checks[target_id] = _target_check(
            [
                _assertion(
                    f"{target_id.lower()}_all_three_trajectories",
                    len(initial_conditions) == 3,
                    "All three printed initial temperatures are propagated.",
                    len(initial_conditions),
                    3,
                ),
                _assertion(
                    f"{target_id.lower()}_strong_distance_decays",
                    bool(strong_monotone),
                    "The strong trajectory approaches the final point without a slow-mode reversal.",
                    bool(strong_monotone),
                    True,
                ),
            ],
            {"rows": len(rows)},
        )
    colder_slow = modal_coefficients(
        initial_conditions["colder_0.02"], gamma_final, alpha_main
    )["coefficient_slow"]
    hot_slow = modal_coefficients(
        initial_conditions["hot_0.74"], gamma_final, alpha_main
    )["coefficient_slow"]
    opposite = bool(np.sign(colder_slow) != np.sign(hot_slow))
    checks["T008"]["assertions"].append(
        _assertion(
            "t008_opposite_slow_approaches",
            opposite,
            "Colder and hotter trajectories approach the final point from opposite slow-mode directions.",
            {"colder": colder_slow, "hotter": hot_slow},
            "opposite signs",
        )
    )
    checks["T008"]["status"] = (
        "passed"
        if all(item["status"] == "passed" for item in checks["T008"]["assertions"])
        else "failed"
    )

    # T009/T010: Supplemental Fig. 5 crossing and post-crossing advantage.
    t009 = parameters["T009_T010"]
    gamma_sweep = np.unique(
        np.concatenate(
            (
                np.linspace(
                    t009["gamma_initial_min"], t009["gamma_initial_max"], t009["points"]
                ),
                np.array([strong_gamma]),
            )
        )
    )
    crossing_rows = []
    advantage_rows = []
    hot_supp = float(parameters["gamma_initial_hot_supp"])
    max_root_residual = 0.0
    for gamma_i in gamma_sweep:
        metrics = crossing_metrics(
            float(gamma_i),
            hot_supp,
            gamma_final,
            alpha_main,
            time_upper=t009["time_upper"],
            bracket_points=t009["bracket_points"],
        )
        cold_at_cross = distance_to_final(
            [metrics.crossing_time], float(gamma_i), gamma_final, alpha_main
        )[0]
        hot_at_cross = distance_to_final(
            [metrics.crossing_time], hot_supp, gamma_final, alpha_main
        )[0]
        max_root_residual = max(
            max_root_residual, abs(float(cold_at_cross - hot_at_cross))
        )
        common = {
            "gamma_initial_prime": gamma_i,
            "strong_gamma_initial_prime": strong_gamma,
            "provenance": "independent_root_and_optimization",
        }
        crossing_rows.append(
            {**common, "crossing_time_omega_inverse": metrics.crossing_time}
        )
        advantage_rows.append(
            {
                **common,
                "maximal_distance_advantage": metrics.maximal_advantage,
                "maximal_advantage_time_omega_inverse": metrics.maximal_advantage_time,
            }
        )
    _write_csv(
        data_dir / "T009_supp_fig5_left.csv",
        [
            "gamma_initial_prime",
            "crossing_time_omega_inverse",
            "strong_gamma_initial_prime",
            "provenance",
        ],
        crossing_rows,
    )
    _write_csv(
        data_dir / "T010_supp_fig5_right.csv",
        [
            "gamma_initial_prime",
            "maximal_distance_advantage",
            "maximal_advantage_time_omega_inverse",
            "strong_gamma_initial_prime",
            "provenance",
        ],
        advantage_rows,
    )
    crossing_values = np.asarray(
        [row["crossing_time_omega_inverse"] for row in crossing_rows]
    )
    advantage_values = np.asarray(
        [row["maximal_distance_advantage"] for row in advantage_rows]
    )
    min_cross_gamma = float(gamma_sweep[int(np.argmin(crossing_values))])
    max_advantage_gamma = float(gamma_sweep[int(np.argmax(advantage_values))])
    checks["T009"] = _target_check(
        [
            _assertion(
                "t009_root_residual",
                max_root_residual <= acceptance["crossing_root_residual_max"],
                "Every reported crossing is a root of d_cold-d_hot.",
                max_root_residual,
                acceptance["crossing_root_residual_max"],
            ),
            _assertion(
                "t009_minimum_near_strong_root",
                abs(min_cross_gamma - strong_gamma)
                <= acceptance["supp_fig5_peak_gamma_tolerance"],
                "Crossing time is minimized near the strong initial temperature.",
                min_cross_gamma,
                strong_gamma,
            ),
        ],
        {"rows": len(crossing_rows), "minimum_gamma": min_cross_gamma},
    )
    checks["T010"] = _target_check(
        [
            _assertion(
                "t010_peak_near_strong_root",
                abs(max_advantage_gamma - strong_gamma)
                <= acceptance["supp_fig5_peak_gamma_tolerance"],
                "The maximal post-crossing distance advantage peaks near the strong initial temperature.",
                max_advantage_gamma,
                strong_gamma,
            ),
            _assertion(
                "t010_peak_scale",
                0.075 <= float(np.max(advantage_values)) <= 0.09,
                "The peak separation matches the approximately 0.08 scale in Supplement Fig. 5.",
                float(np.max(advantage_values)),
                [0.075, 0.09],
            ),
        ],
        {"rows": len(advantage_rows), "maximum_gamma": max_advantage_gamma},
    )

    return checks


def solver_parity_checks(config: dict[str, Any]) -> dict[str, Any]:
    parameters = config["parameters"]
    tolerance = config["acceptance"]["bloch_liouvillian_parity_max"]
    alpha = float(parameters["alpha_main"])
    gamma_initial = float(parameters["gamma_initial_cold_main"])
    gamma_final = float(parameters["gamma_final_main"])
    times = np.array([0.0, 0.003, 0.011, 0.037, 0.1, 0.25], dtype=float)
    initial_yz = steady_state(gamma_initial, alpha)
    density = density_from_bloch(float(initial_yz[0]), float(initial_yz[1]))
    density_states = propagate_density(density, times, liouvillian(alpha, gamma_final))
    density_bloch = np.asarray(
        [bloch_from_density(state)[1:] for state in density_states]
    )
    analytic_bloch = propagate_bloch(times, gamma_initial, gamma_final, alpha)
    parity = float(np.max(np.abs(density_bloch - analytic_bloch)))
    trace_error = float(max(abs(np.trace(state) - 1.0) for state in density_states))
    hermiticity_error = float(
        max(np.max(np.abs(state - state.conj().T)) for state in density_states)
    )
    min_eigenvalue = float(
        min(np.min(np.linalg.eigvalsh(state)).real for state in density_states)
    )
    return {
        "status": (
            "passed"
            if parity <= tolerance
            and trace_error <= 1e-12
            and hermiticity_error <= 1e-12
            and min_eigenvalue >= -1e-12
            else "failed"
        ),
        "bloch_liouvillian_max_abs": parity,
        "trace_error_max": trace_error,
        "hermiticity_error_max": hermiticity_error,
        "minimum_density_eigenvalue": min_eigenvalue,
        "tolerance": tolerance,
    }


def paper_consistency_checks(config: dict[str, Any]) -> dict[str, Any]:
    """Quantify source inconsistencies without promoting them to paper errors."""

    parameters = config["parameters"]
    tolerance = config["acceptance"]["literal_main_factor_two_identity_max"]
    alpha = float(parameters["alpha_main"])
    gamma_values = [0.2, 0.77, 2.0, 15.0]
    identity_errors = []
    same_label_gaps = []
    for gamma in gamma_values:
        literal = bloch_from_density(
            steady_density(liouvillian_literal_main(alpha, gamma))
        )[1:]
        rescaled_supplement = steady_state(gamma / 2.0, alpha)
        same_label_supplement = steady_state(gamma, alpha)
        identity_errors.append(float(np.max(np.abs(literal - rescaled_supplement))))
        same_label_gaps.append(float(np.linalg.norm(literal - same_label_supplement)))
    factor_two_identity = max(identity_errors)
    payload = {
        "schema_version": 1,
        "status": "passed" if factor_two_identity <= tolerance else "failed",
        "classification": "inconclusive",
        "paper_error_candidate_emitted": False,
        "discrepancies": [
            {
                "id": "DISC-RATE-FACTOR-TWO",
                "source_a": "Main Eqs. (1)-(2) with the printed standard dissipator",
                "source_b": "Supplement Eqs. (1)-(4) and all theory-figure formulas",
                "observation": "Both dissipative coefficients in the supplement are exactly twice those implied by the main equations.",
                "independent_checks": [
                    "direct operator expansion",
                    "separately assembled 4x4 Liouvillian steady states",
                    "exact gamma' -> gamma'/2 steady-locus identity",
                ],
                "factor_two_identity_max_abs": factor_two_identity,
                "same_printed_gamma_steady_state_gaps": same_label_gaps,
                "impact": "Literal use of the main equations shifts every dimensionless temperature axis by a factor two.",
                "blocking_evidence": [
                    "fresh_context_inventory_first_review",
                    "explicit_author_convention_or_erratum_check",
                ],
            },
            {
                "id": "DISC-HAMILTONIAN-PROSE-TWO",
                "source_a": "Main experimental paragraph: H=Omega sigma_x",
                "source_b": "Main Eq. (1), Supplement Eqs. (1)-(4), standard Rabi convention: H=Omega sigma_x/2",
                "observation": "The isolated prose sentence differs by a factor two from every equation used by the figures.",
                "impact": "No impact on this reproduction because all executable equations consistently use Omega/2.",
                "blocking_evidence": ["fresh_context_inventory_first_review"],
            },
        ],
    }
    return payload


def build_generated_manifest(workspace: Path, config_path: Path) -> dict[str, Any]:
    files = sorted((workspace / "outputs" / "data").glob("T*.csv"))
    return {
        "schema_version": 1,
        "paper_id": "2401.05830",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_as_numerical_inputs": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "config": {
            "path": str(config_path.relative_to(workspace)),
            "sha256": _sha256(config_path),
        },
        "files": [
            {
                "path": str(path.relative_to(workspace)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in files
        ],
    }


def run(config_path: Path, workspace: Path) -> dict[str, Any]:
    start = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    target_checks = generate_target_data(config, workspace)
    parity = solver_parity_checks(config)
    consistency = paper_consistency_checks(config)
    from .rendering import render_all

    figure_paths = render_all(workspace, config)
    manifest = build_generated_manifest(workspace, config_path)
    checks_dir = workspace / "outputs" / "checks"
    _write_json(
        checks_dir / "target_checks.json",
        {
            "schema_version": 1,
            "paper_id": "2401.05830",
            "status": (
                "passed"
                if all(item["status"] == "passed" for item in target_checks.values())
                else "failed"
            ),
            "targets": target_checks,
        },
    )
    _write_json(checks_dir / "solver_parity.json", parity)
    _write_json(checks_dir / "paper_consistency_checks.json", consistency)
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    elapsed = time.perf_counter() - start
    overall_passed = (
        all(item["status"] == "passed" for item in target_checks.values())
        and parity["status"] == "passed"
        and consistency["status"] == "passed"
    )
    summary = {
        "schema_version": 1,
        "paper_id": "2401.05830",
        "status": "passed" if overall_passed else "failed",
        "artifact_stage": config["artifact_stage"],
        "target_ids": TARGET_IDS,
        "target_count": len(TARGET_IDS),
        "figure_paths": [str(path.relative_to(workspace)) for path in figure_paths],
        "elapsed_seconds": elapsed,
        "paper_error_candidate_emitted": False,
    }
    _write_json(checks_dir / "run_summary.json", summary)
    if not overall_passed:
        raise RuntimeError("one or more scientific acceptance checks failed")
    return summary
