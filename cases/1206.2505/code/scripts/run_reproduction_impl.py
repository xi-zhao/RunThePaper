#!/usr/bin/env python3
"""Generate all paper-defined numerical objects without source-image input."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dqpt_tfim import (  # noqa: E402
    bogoliubov_angle,
    critical_momentum,
    critical_period,
    complex_time_postselection_check,
    cumulant_rate,
    fisher_zero_lines,
    extreme_quench_loschmidt_rates,
    loschmidt_rate,
    longitudinal_correlation_dynamics,
    magnetization_dynamics,
    mean_work_density,
    postselected_magnetization,
    postselection_normalization_check,
    ramp_mode_occupations,
    work_rate_grid,
)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fisher_rows(
    parameters: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, float]]:
    # The closed formula is finite after the logarithm guard in
    # ``fisher_zero_lines``. Including both endpoint limits prevents an
    # arbitrary momentum cutoff from truncating branches inside the paper's
    # displayed R window.
    momentum = np.linspace(0.0, np.pi, int(parameters["fisher_k_points"]))
    branches = np.asarray(parameters["fisher_branches"], dtype=int)
    rows: list[dict[str, object]] = []
    metrics: dict[str, float] = {}
    for quench in parameters["fisher_quenches"]:
        label = str(quench["label"])
        g0 = float(quench["g0"])
        g1 = float(quench["g1"])
        real, imaginary = fisher_zero_lines(momentum, g0, g1, branches)
        for branch_index, branch in enumerate(branches):
            rows.extend(
                {
                    "scenario": label,
                    "g0": g0,
                    "g1": g1,
                    "branch": int(branch),
                    "k": float(k),
                    "real_z": float(real[branch_index, index]),
                    "imag_z": float(imaginary[branch_index, index]),
                }
                for index, k in enumerate(momentum)
            )
        kstar = critical_momentum(g0, g1)
        if kstar is not None:
            zero_real, _ = fisher_zero_lines(
                np.asarray([kstar]), g0, g1, np.asarray([0])
            )
            metrics[f"{label}_critical_real_z"] = float(zero_real[0, 0])
            occupation = (
                np.sin(bogoliubov_angle(kstar, g0) - bogoliubov_angle(kstar, g1)) ** 2
            )
            metrics[f"{label}_critical_occupation"] = float(occupation)
        metrics[f"{label}_max_real_z"] = float(np.max(real))
    return rows, metrics


def work_rows(
    parameters: dict[str, object],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, float],
]:
    quench = parameters["work_quench"]
    g0 = float(quench["g0"])
    g1 = float(quench["g1"])
    tstar = float(critical_period(g0, g1))
    k_points = int(parameters["integration_k_points"])
    common = {
        "g0": g0,
        "g1": g1,
        "k_points": k_points,
        "resistance_min": float(parameters["resistance_min"]),
        "resistance_max": float(parameters["resistance_max"]),
        "resistance_points": int(parameters["resistance_points"]),
    }

    scaled_curve_time = np.linspace(
        0.0, 2.0, int(parameters["work_scaled_time_points"])
    )
    curve_time = scaled_curve_time * tstar
    curve_work = np.asarray(parameters["work_curve_densities"], dtype=float)
    curve_rates, curve_means = work_rate_grid(curve_time, curve_work, **common)
    curve_rows = [
        {
            "scaled_time": float(scaled_curve_time[t_index]),
            "time": float(curve_time[t_index]),
            "work_density": float(curve_work[w_index]),
            "rate": float(curve_rates[t_index, w_index]),
            "mean_work_density": float(curve_means[t_index]),
        }
        for t_index in range(curve_time.size)
        for w_index in range(curve_work.size)
    ]

    scaled_surface_time = np.linspace(
        0.0, 2.0, int(parameters["work_surface_time_points"])
    )
    surface_time = scaled_surface_time * tstar
    surface_work = np.linspace(
        0.0,
        float(parameters["work_surface_density_max"]),
        int(parameters["work_surface_density_points"]),
    )
    surface_rates, surface_means = work_rate_grid(surface_time, surface_work, **common)
    surface_rows = [
        {
            "scaled_time": float(scaled_surface_time[t_index]),
            "time": float(surface_time[t_index]),
            "work_density": float(surface_work[w_index]),
            "rate": float(surface_rates[t_index, w_index]),
            "mean_work_density": float(surface_means[t_index]),
        }
        for t_index in range(surface_time.size)
        for w_index in range(surface_work.size)
    ]

    rate_time = np.linspace(0.0, 3.0 * tstar, 1201)
    rates = loschmidt_rate(rate_time, g0, g1, k_points=k_points)
    rate_rows = [
        {
            "scaled_time": float(value / tstar),
            "time": float(value),
            "loschmidt_rate": float(rates[index]),
        }
        for index, value in enumerate(rate_time)
    ]

    zero_error = np.nanmax(
        np.abs(
            curve_rates[:, 0] - loschmidt_rate(curve_time, g0, g1, k_points=k_points)
        )
    )
    off_mean = np.abs(surface_work[None, :] - surface_means[:, None]) > 1e-12
    off_mean_zero_counts = np.sum(
        np.isfinite(surface_rates) & off_mean & (np.abs(surface_rates) <= 1e-14),
        axis=1,
    )
    metrics = {
        "critical_period": tstar,
        "work_rate_minimum": float(np.nanmin(surface_rates)),
        "work_zero_rate_max_error": float(zero_error),
        "work_off_mean_zero_count_max": int(np.max(off_mean_zero_counts)),
        "cumulant_at_zero_max_error": float(
            max(
                abs(cumulant_rate(0.0, float(value), g0, g1, k_points=k_points))
                for value in curve_time[::20]
            )
        ),
        "mean_work_crosscheck_max_error": float(
            np.max(
                np.abs(
                    curve_means
                    - mean_work_density(curve_time, g0, g1, k_points=k_points)
                )
            )
        ),
    }
    return curve_rows, surface_rows, rate_rows, metrics


def _first_minimum_shift(scaled_time: np.ndarray, absolute_mz: np.ndarray) -> float:
    window = (scaled_time >= 0.2) & (scaled_time <= 0.9)
    minimum = int(np.argmin(absolute_mz[window]))
    first_minimum = float(scaled_time[window][minimum])
    return first_minimum - 0.5


def magnetization_rows(parameters: dict[str, object]) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, float],
]:
    sites = int(parameters["spin_sites"])
    periodic = bool(parameters["spin_periodic"])
    pfaffian_sites = int(parameters["pfaffian_sites"])
    pfaffian_separation = int(parameters["pfaffian_separation"])
    scaled = np.linspace(
        0.0,
        float(parameters["magnetization_scaled_time_max"]),
        int(parameters["magnetization_scaled_time_points"]),
    )
    curve_rows: list[dict[str, object]] = []
    metrics: dict[str, float] = {}
    main_curve_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for quench in parameters["magnetization_quenches"]:
        label = str(quench["label"])
        g0 = float(quench["g0"])
        g1 = float(quench["g1"])
        tstar = float(critical_period(g0, g1))
        time_grid = scaled * tstar
        result = longitudinal_correlation_dynamics(
            pfaffian_sites, pfaffian_separation, g0, g1, time_grid
        )
        sigma_correlation = np.asarray(result["sigma_z_correlation"])
        spin_correlation = np.asarray(result["spin_z_correlation"])
        absolute = np.asarray(result["absolute_spin_z_correlation"])
        cluster_magnetization = np.asarray(result["cluster_magnetization"])
        shift = _first_minimum_shift(scaled, absolute)
        shifted = scaled - shift
        keep = (shifted >= 0.0) & (shifted <= 6.0)
        curve_rows.extend(
            {
                "quench": label,
                "g0": g0,
                "g1": g1,
                "sites": pfaffian_sites,
                "correlation_distance": pfaffian_separation,
                "scaled_time": float(shifted[index]),
                "time": float(time_grid[index]),
                "phase_shift_scaled": shift,
                "sigma_z_correlation": float(sigma_correlation[index]),
                "spin_z_correlation": float(spin_correlation[index]),
                "absolute_spin_z_correlation": float(absolute[index]),
                "cluster_magnetization": float(cluster_magnetization[index]),
            }
            for index in np.where(keep)[0]
        )
        main_curve_cache[label] = (scaled.copy(), absolute.copy())
        metrics[f"{label}_phase_shift_scaled"] = shift
        metrics[f"{label}_majorana_antisymmetry_error"] = float(
            result["maximum_antisymmetry_error"]
        )
        metrics[f"{label}_majorana_imaginary_error"] = float(
            result["maximum_imaginary_error"]
        )
        metrics[f"{label}_observable_convention_gap"] = float(
            np.max(np.abs(cluster_magnetization - absolute))
        )

    path_rows: list[dict[str, object]] = []
    for label, config, mode in [
        ("across", parameters["trajectory_across"], "critical_period"),
        ("within", parameters["trajectory_within"], "mass_gap"),
    ]:
        g0 = float(config["g0"])
        g1 = float(config["g1"])
        scaled_path = np.linspace(
            0.0, float(config["scaled_time_max"]), int(config["points"])
        )
        scale = (
            float(critical_period(g0, g1))
            if mode == "critical_period"
            else 1.0 / abs(g1 - 1.0)
        )
        time_grid = scaled_path * scale
        result = magnetization_dynamics(sites, g0, g1, time_grid, periodic)
        mz = np.asarray(result["magnetization_z"])
        my = np.asarray(result["magnetization_y"])
        radius = np.sqrt(mz**2 + my**2)
        path_rows.extend(
            {
                "trajectory": label,
                "g0": g0,
                "g1": g1,
                "sites": sites,
                "scaled_time": float(scaled_path[index]),
                "time": float(time_grid[index]),
                "magnetization_z": float(mz[index]),
                "magnetization_y": float(my[index]),
                "normalized_z": float(mz[index] / max(radius[index], 1e-15)),
                "normalized_y": float(my[index] / max(radius[index], 1e-15)),
            }
            for index in range(scaled_path.size)
        )
        metrics[f"trajectory_{label}_state_norm_error"] = float(
            np.max(np.abs(np.asarray(result["state_norm"]) - 1.0))
        )

    convergence_rows: list[dict[str, object]] = []
    reference_quench = parameters["magnetization_quenches"][2]
    g0 = float(reference_quench["g0"])
    g1 = float(reference_quench["g1"])
    label = str(reference_quench["label"])
    reference_scaled, reference_absolute = main_curve_cache[label]
    for convergence in parameters["pfaffian_convergence"]:
        convergence_sites = int(convergence["sites"])
        convergence_separation = int(convergence["separation"])
        if (
            convergence_sites == pfaffian_sites
            and convergence_separation == pfaffian_separation
        ):
            absolute = reference_absolute
        else:
            result = longitudinal_correlation_dynamics(
                convergence_sites,
                convergence_separation,
                g0,
                g1,
                reference_scaled * float(critical_period(g0, g1)),
            )
            absolute = np.asarray(result["absolute_spin_z_correlation"])
        first_shift = _first_minimum_shift(reference_scaled, absolute)
        convergence_rows.append(
            {
                "sites": convergence_sites,
                "correlation_distance": convergence_separation,
                "g0": g0,
                "g1": g1,
                "first_minimum_scaled_time": first_shift + 0.5,
                "phase_shift_scaled": first_shift,
                "minimum_absolute_magnetization": float(
                    np.min(
                        absolute[(reference_scaled >= 0.2) & (reference_scaled <= 0.9)]
                    )
                ),
            }
        )

    first_minima = np.asarray(
        [row["first_minimum_scaled_time"] for row in convergence_rows], dtype=float
    )
    metrics["spin_size_first_minimum_spread"] = float(np.ptp(first_minima))

    post = parameters["postselection_quench"]
    g0 = float(post["g0"])
    g1 = float(post["g1"])
    post_scaled = np.linspace(0.0, float(post["scaled_time_max"]), int(post["points"]))
    post_time = post_scaled * float(critical_period(g0, g1))
    post_result = postselected_magnetization(sites, g0, g1, post_time, periodic)
    post_rows = [
        {
            "scaled_time": float(post_scaled[index]),
            "time": float(post_time[index]),
            "g0": g0,
            "g1": g1,
            "sites": sites,
            "ordinary_magnetization": float(
                post_result["ordinary_magnetization"][index]
            ),
            "postselected_magnetization": float(
                post_result["postselected_magnetization"][index]
            ),
            "ground_sector_probability": float(
                post_result["ground_sector_probability"][index]
            ),
        }
        for index in range(post_scaled.size)
    ]
    metrics["postselected_initial_magnetization"] = float(
        post_result["initial_magnetization"]
    )
    postselected = np.asarray(post_result["postselected_magnetization"])
    sign_changes = np.flatnonzero(
        np.signbit(postselected[:-1]) != np.signbit(postselected[1:])
    )
    crossing_times = 0.5 * (post_scaled[sign_changes] + post_scaled[sign_changes + 1])
    for index, expected in enumerate((0.5, 1.5, 2.5), start=1):
        metrics[f"postselection_crossing_{index}_distance"] = float(
            np.min(np.abs(crossing_times - expected))
        )
    return curve_rows, path_rows, convergence_rows, post_rows, metrics


def supplement_rows(
    parameters: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, float]]:
    """Generate exact supplement checks, including literal source variants."""

    g1 = float(parameters["supplement_extreme_g1"])
    scaled_time = np.linspace(
        0.025,
        3.975,
        int(parameters["supplement_scaled_time_points"]),
    )
    time_grid = scaled_time * np.pi / g1
    rates = extreme_quench_loschmidt_rates(time_grid, g1)
    curve_rows = [
        {
            "scaled_time_t_over_tstar": float(scaled_time[index]),
            "time": float(time_grid[index]),
            "g1": g1,
            "physical_diagonal_rate": float(rates["physical_diagonal_rate"][index]),
            "physical_off_diagonal_rate": float(
                rates["physical_off_diagonal_rate"][index]
            ),
            "printed_diagonal_rate": float(rates["printed_diagonal_rate"][index]),
            "printed_off_diagonal_rate": float(
                rates["printed_off_diagonal_rate"][index]
            ),
            "dominant_physical_rate": float(rates["dominant_physical_rate"][index]),
        }
        for index in range(scaled_time.size)
    ]

    probabilities = np.asarray(parameters["supplement_probabilities"], dtype=float)
    energies = np.asarray(parameters["supplement_energies"], dtype=float)
    observable = np.asarray(parameters["supplement_observable"], dtype=float)
    beta = float(parameters["supplement_beta"])
    complex_time = float(parameters["supplement_complex_time"])
    normalization = postselection_normalization_check(
        probabilities, energies, observable, beta
    )
    complex_identity = complex_time_postselection_check(
        probabilities, energies, beta, complex_time
    )

    physical_diag = np.asarray(rates["physical_diagonal_rate"])
    physical_off = np.asarray(rates["physical_off_diagonal_rate"])
    difference = physical_diag - physical_off
    switches = np.flatnonzero(np.signbit(difference[:-1]) != np.signbit(difference[1:]))
    switch_times = 0.5 * (scaled_time[switches] + scaled_time[switches + 1])
    switch_error = max(
        float(np.min(np.abs(switch_times - expected)))
        for expected in (0.5, 1.5, 2.5, 3.5)
    )

    physical_definition_error = float(
        np.max(np.abs(np.exp(-physical_diag) - np.abs(np.cos(g1 * time_grid / 2.0))))
    )
    printed_definition_error = float(
        np.max(
            np.abs(
                np.exp(-np.asarray(rates["printed_diagonal_rate"]))
                - np.abs(np.cos(g1 * time_grid / 2.0))
            )
        )
    )
    normalized_postselection_error = abs(
        normalization["normalized_expectation"]
        - normalization["literal_unnormalized_expectation"] / normalization["partition"]
    )
    literal_postselection_error = abs(
        normalization["normalized_expectation"]
        - normalization["literal_unnormalized_expectation"]
    )
    corrected_complex_error = abs(
        complex_identity["normalized_characteristic"]
        - complex_identity["corrected_complex_time_amplitude"]
    )
    literal_complex_error = abs(
        complex_identity["normalized_characteristic"]
        - complex_identity["literal_complex_time_amplitude"]
    )
    check_rows = [
        {
            "check_id": "extreme_quench_rate_sign",
            "corrected_error": physical_definition_error,
            "literal_source_error": printed_definition_error,
            "normalization": 1.0,
            "note": "L_ab=exp(-N f_ab) requires f_ab=-log|amplitude|.",
        },
        {
            "check_id": "postselected_expectation_normalization",
            "corrected_error": float(normalized_postselection_error),
            "literal_source_error": float(literal_postselection_error),
            "normalization": float(normalization["partition"]),
            "note": "The normalized tilted distribution requires division by Z_beta.",
        },
        {
            "check_id": "complex_time_postselection_normalization",
            "corrected_error": float(corrected_complex_error),
            "literal_source_error": float(literal_complex_error),
            "normalization": float(complex_identity["partition"]),
            "note": "The normalized characteristic function is G(t+i beta)/G(i beta).",
        },
    ]
    metrics = {
        "supplement_switch_scaled_time_max_error": switch_error,
        "supplement_physical_rate_definition_error": physical_definition_error,
        "supplement_printed_rate_definition_error": printed_definition_error,
        "supplement_postselection_corrected_error": float(
            normalized_postselection_error
        ),
        "supplement_postselection_literal_error": float(literal_postselection_error),
        "supplement_complex_time_corrected_error": float(corrected_complex_error),
        "supplement_complex_time_literal_error": float(literal_complex_error),
    }
    return curve_rows, check_rows, metrics


def ramp_rows(
    parameters: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, float]]:
    """Run the publication's general-ramp mechanism on declared ramp families."""

    momentum = np.linspace(0.0, np.pi, int(parameters["ramp_momentum_points"]))
    rows: list[dict[str, object]] = []
    metrics: dict[str, float] = {}
    for protocol in parameters["ramp_protocols"]:
        label = str(protocol["label"])
        profile = str(protocol["profile"])
        result = ramp_mode_occupations(
            momentum,
            float(protocol["g0"]),
            float(protocol["g1"]),
            float(protocol["duration"]),
            int(protocol["steps"]),
            profile,
        )
        occupation = np.asarray(result["occupation"])
        crossing_index = int(np.argmin(np.abs(occupation - 0.5)))
        metrics[f"{label}_half_occupation_error"] = float(
            abs(occupation[crossing_index] - 0.5)
        )
        metrics[f"{label}_maximum_norm_error"] = float(result["maximum_norm_error"])
        metrics[f"{label}_endpoint_contrast"] = float(occupation[0] - occupation[-1])
        rows.extend(
            {
                "protocol": label,
                "profile": profile,
                "g0": float(protocol["g0"]),
                "g1": float(protocol["g1"]),
                "duration": float(protocol["duration"]),
                "steps": int(protocol["steps"]),
                "momentum": float(value),
                "excited_occupation": float(occupation[index]),
                "is_nearest_half_mode": index == crossing_index,
            }
            for index, value in enumerate(momentum)
        )
    return rows, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    arguments = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(arguments.config)
    output_root = Path(arguments.output_root)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    acceptance = config["acceptance"]

    fisher, fisher_metrics = fisher_rows(parameters)
    work_curves, work_surface, dqpt_rates, work_metrics = work_rows(parameters)
    magnetization, paths, convergence, postselection, spin_metrics = magnetization_rows(
        parameters
    )
    supplement_curve, supplement_checks, supplement_metrics = supplement_rows(
        parameters
    )
    ramps, ramp_metrics = ramp_rows(parameters)

    write_csv(
        output_root / "data/fisher_zero_lines.csv",
        ["scenario", "g0", "g1", "branch", "k", "real_z", "imag_z"],
        fisher,
    )
    write_csv(
        output_root / "data/work_rate_curves.csv",
        ["scaled_time", "time", "work_density", "rate", "mean_work_density"],
        work_curves,
    )
    write_csv(
        output_root / "data/work_rate_surface.csv",
        ["scaled_time", "time", "work_density", "rate", "mean_work_density"],
        work_surface,
    )
    write_csv(
        output_root / "data/dqpt_rate.csv",
        ["scaled_time", "time", "loschmidt_rate"],
        dqpt_rates,
    )
    write_csv(
        output_root / "data/magnetization_curves.csv",
        [
            "quench",
            "g0",
            "g1",
            "sites",
            "correlation_distance",
            "scaled_time",
            "time",
            "phase_shift_scaled",
            "sigma_z_correlation",
            "spin_z_correlation",
            "absolute_spin_z_correlation",
            "cluster_magnetization",
        ],
        magnetization,
    )
    write_csv(
        output_root / "data/magnetization_paths.csv",
        [
            "trajectory",
            "g0",
            "g1",
            "sites",
            "scaled_time",
            "time",
            "magnetization_z",
            "magnetization_y",
            "normalized_z",
            "normalized_y",
        ],
        paths,
    )
    write_csv(
        output_root / "data/spin_size_convergence.csv",
        [
            "sites",
            "correlation_distance",
            "g0",
            "g1",
            "first_minimum_scaled_time",
            "phase_shift_scaled",
            "minimum_absolute_magnetization",
        ],
        convergence,
    )
    write_csv(
        output_root / "data/postselected_magnetization.csv",
        [
            "scaled_time",
            "time",
            "g0",
            "g1",
            "sites",
            "ordinary_magnetization",
            "postselected_magnetization",
            "ground_sector_probability",
        ],
        postselection,
    )
    write_csv(
        output_root / "data/supplement_loschmidt_matrix.csv",
        [
            "scaled_time_t_over_tstar",
            "time",
            "g1",
            "physical_diagonal_rate",
            "physical_off_diagonal_rate",
            "printed_diagonal_rate",
            "printed_off_diagonal_rate",
            "dominant_physical_rate",
        ],
        supplement_curve,
    )
    write_csv(
        output_root / "data/supplement_formula_checks.csv",
        [
            "check_id",
            "corrected_error",
            "literal_source_error",
            "normalization",
            "note",
        ],
        supplement_checks,
    )
    write_csv(
        output_root / "data/ramp_mode_occupations.csv",
        [
            "protocol",
            "profile",
            "g0",
            "g1",
            "duration",
            "steps",
            "momentum",
            "excited_occupation",
            "is_nearest_half_mode",
        ],
        ramps,
    )

    assertions = [
        {
            "assertion_id": "across_phase_fisher_line_crosses_time_axis",
            "status": (
                "passed"
                if abs(fisher_metrics["across_critical_critical_real_z"])
                <= acceptance["fisher_crossing_real_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "same_phase_fisher_lines_stay_nonpositive",
            "status": (
                "passed"
                if fisher_metrics["same_phase_max_real_z"]
                <= acceptance["same_phase_positive_real_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "critical_mode_has_half_occupation",
            "status": (
                "passed"
                if abs(fisher_metrics["across_critical_critical_occupation"] - 0.5)
                <= acceptance["occupation_half_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "zero_work_rate_equals_loschmidt_rate",
            "status": (
                "passed"
                if work_metrics["work_zero_rate_max_error"]
                <= acceptance["work_zero_rate_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "cumulant_generator_normalizes_at_R_zero",
            "status": (
                "passed"
                if work_metrics["cumulant_at_zero_max_error"]
                <= acceptance["cumulant_zero_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "work_rate_is_nonnegative",
            "status": (
                "passed" if work_metrics["work_rate_minimum"] >= -1e-12 else "failed"
            ),
        },
        {
            "assertion_id": "work_rate_has_no_off_mean_zero_plateau",
            "status": (
                "passed"
                if work_metrics["work_off_mean_zero_count_max"]
                <= acceptance["work_off_mean_zero_count_max"]
                else "failed"
            ),
        },
        {
            "assertion_id": "finite_chain_time_evolution_preserves_norm",
            "status": (
                "passed"
                if max(
                    value
                    for key, value in spin_metrics.items()
                    if key.endswith("state_norm_error")
                )
                <= acceptance["state_norm_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "majorana_pfaffian_covariance_is_consistent",
            "status": (
                "passed"
                if max(
                    value
                    for key, value in spin_metrics.items()
                    if key.endswith("majorana_antisymmetry_error")
                    or key.endswith("majorana_imaginary_error")
                )
                <= acceptance["majorana_covariance_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "pfaffian_first_minimum_is_size_stable",
            "status": (
                "passed"
                if spin_metrics["spin_size_first_minimum_spread"]
                <= acceptance["spin_minimum_spread_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "postselected_switches_track_first_three_fisher_times",
            "status": (
                "passed"
                if max(
                    spin_metrics[f"postselection_crossing_{index}_distance"]
                    for index in (1, 2, 3)
                )
                <= acceptance["postselection_crossing_tolerance"]
                else "failed"
            ),
        },
        {
            "assertion_id": "all_numeric_subfigures_emit_data",
            "status": (
                "passed"
                if all(
                    len(rows) > 0
                    for rows in (
                        fisher,
                        work_curves,
                        work_surface,
                        dqpt_rates,
                        magnetization,
                        paths,
                        convergence,
                        postselection,
                    )
                )
                else "failed"
            ),
        },
        {
            "assertion_id": "supplement_sector_switches_track_fisher_times",
            "status": (
                "passed"
                if supplement_metrics["supplement_switch_scaled_time_max_error"] <= 0.01
                else "failed"
            ),
        },
        {
            "assertion_id": "supplement_corrected_formulas_close",
            "status": (
                "passed"
                if max(
                    supplement_metrics["supplement_physical_rate_definition_error"],
                    supplement_metrics["supplement_postselection_corrected_error"],
                    supplement_metrics["supplement_complex_time_corrected_error"],
                )
                <= 1e-12
                else "failed"
            ),
        },
        {
            "assertion_id": "supplement_literal_source_discrepancies_are_resolved",
            "status": (
                "passed"
                if min(
                    supplement_metrics["supplement_printed_rate_definition_error"],
                    supplement_metrics["supplement_postselection_literal_error"],
                    supplement_metrics["supplement_complex_time_literal_error"],
                )
                > 1e-3
                else "failed"
            ),
        },
        {
            "assertion_id": "representative_cross_critical_ramps_have_half_mode",
            "status": (
                "passed"
                if max(
                    value
                    for key, value in ramp_metrics.items()
                    if key.endswith("half_occupation_error")
                )
                <= acceptance["ramp_half_occupation_tolerance"]
                and min(
                    value
                    for key, value in ramp_metrics.items()
                    if key.endswith("endpoint_contrast")
                )
                >= acceptance["ramp_endpoint_contrast_minimum"]
                and max(
                    value
                    for key, value in ramp_metrics.items()
                    if key.endswith("maximum_norm_error")
                )
                <= acceptance["state_norm_tolerance"]
                else "failed"
            ),
        },
    ]
    status = (
        "passed" if all(item["status"] == "passed" for item in assertions) else "failed"
    )
    checks = {
        "schema_version": 1,
        "status": status,
        "assertions": assertions,
        "metrics": {
            **fisher_metrics,
            **work_metrics,
            **spin_metrics,
            **supplement_metrics,
            **ramp_metrics,
        },
        "scientific_boundary": {
            "integrable_targets": "paper equations evaluated at printed parameters",
            "magnetization_targets": "independent N=256 Majorana-Pfaffian correlation plus N=12 exact-spin cross-check; paper grid and magnetization normalization are not published",
            "author_code_or_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
            "supplement_source_discrepancies": "literal and corrected formulas are frozen separately for fresh review",
            "ramp_scope": "linear and smoothstep protocols are declared reconstructions because the paper gives no ramp function or duration",
        },
    }
    checks_path = output_root / "checks/science_checks.json"
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")

    data_paths = sorted((output_root / "data").glob("*"))
    manifest = {
        "schema_version": 1,
        "status": status,
        "config_sha256": sha256(config_path),
        "files": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in data_paths
        ],
    }
    manifest_path = output_root / "checks/generated_data_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema_version": 1,
        "status": status,
        "duration_seconds": time.perf_counter() - started,
        "parameters": parameters,
        "rows": {
            "fisher": len(fisher),
            "work_curves": len(work_curves),
            "work_surface": len(work_surface),
            "dqpt_rates": len(dqpt_rates),
            "magnetization": len(magnetization),
            "paths": len(paths),
            "convergence": len(convergence),
            "postselection": len(postselection),
            "supplement_curve": len(supplement_curve),
            "supplement_checks": len(supplement_checks),
            "ramps": len(ramps),
        },
    }
    (output_root / "checks/run_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if status != "passed":
        raise RuntimeError("scientific assertions failed")


if __name__ == "__main__":
    main()
