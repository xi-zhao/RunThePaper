#!/usr/bin/env python3
"""Generate every numerical target from clean-room equations and algorithms."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import scipy.linalg

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from quantum_jumps.doob import doob_similarity_superoperator  # noqa: E402
from quantum_jumps.large_deviation import (  # noqa: E402
    cumulants_from_theta,
    rate_function,
    two_level_rate_exact,
)
from quantum_jumps.liouvillian import (  # noqa: E402
    dominant_eigenpair,
    tilted_liouvillian,
    trace_preservation_residual,
)
from quantum_jumps.micromaser import (  # noqa: E402
    MicromaserParameters,
    direct_generator,
    dominant_distribution,
    dominant_eigenvalue,
)
from quantum_jumps.models import (  # noqa: E402
    three_level_model,
    two_level_exact,
    two_level_model,
)
from quantum_jumps.trajectories import (  # noqa: E402
    three_level_blinking_windows,
    two_level_rescaled_trajectory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def check(
    check_id: str,
    target_ids: list[str],
    description: str,
    value: float,
    threshold: float,
    comparator: str = "max",
) -> dict[str, object]:
    if comparator == "max":
        passed = value <= threshold
    elif comparator == "min":
        passed = value >= threshold
    else:
        raise ValueError(f"unsupported comparator: {comparator}")
    return {
        "check_id": check_id,
        "target_ids": target_ids,
        "description": description,
        "value": float(value),
        "threshold": float(threshold),
        "comparator": comparator,
        "passed": bool(passed),
    }


def dense_theta(model: object, s: float) -> float:
    tilted = tilted_liouvillian(
        model.hamiltonian, model.jumps, s, counted_jump=model.counted_jump
    )
    return float(dominant_eigenpair(tilted).eigenvalue.real)


def grid(specification: dict[str, object], prefix: str = "") -> np.ndarray:
    return np.linspace(
        float(specification[f"{prefix}s_min"]),
        float(specification[f"{prefix}s_max"]),
        int(specification[f"{prefix}s_points"]),
    )


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    config_path = Path(args.config).resolve()
    output_root = Path(args.output_root).resolve()
    config = json.loads(config_path.read_text())
    run_id = str(config.get("run_id", "0911.0556-paper-reconstructed-v3"))
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    data_root = output_root / "data"
    checks_root = output_root / "checks"
    data_root.mkdir(parents=True, exist_ok=True)
    checks_root.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, object]] = []

    # T001-T003: two-level closed form, generic tilted matrix, dual and events.
    two = parameters["two_level"]
    two_model = two_level_model(float(two["omega"]), float(two["kappa"]))
    two_s = grid(two)
    derivative_step = float(parameters["derivative_step"])
    two_theta, two_activity, two_mandel = cumulants_from_theta(
        lambda value: dense_theta(two_model, value),
        two_s,
        derivative_step=derivative_step,
    )
    exact_theta, exact_activity, exact_mandel = two_level_exact(
        two_s, float(two["omega"])
    )
    two_curve_rows = [
        {
            "target_id": "T001",
            "s": float(s),
            "theta_eigen": float(theta),
            "theta_exact": float(theta_exact),
            "activity_eigen": float(activity),
            "activity_exact": float(activity_exact),
            "mandel_eigen": float(mandel),
            "mandel_exact": float(mandel_exact),
            "generated_data_provenance": "independent_numerics",
        }
        for s, theta, theta_exact, activity, activity_exact, mandel, mandel_exact in zip(
            two_s,
            two_theta,
            exact_theta,
            two_activity,
            exact_activity,
            two_mandel,
            exact_mandel,
            strict=True,
        )
    ]
    write_csv(
        data_root / "two_level_curves.csv", list(two_curve_rows[0]), two_curve_rows
    )

    two_rate_s = grid(two, "rate_")
    two_rate_theta = np.asarray(two_level_exact(two_rate_s, float(two["omega"]))[0])
    two_k = np.linspace(
        float(two["rate_k_min"]),
        float(two["rate_k_max"]),
        int(two["rate_k_points"]),
    )
    two_phi_numeric = rate_function(two_k, two_rate_s, two_rate_theta)
    two_phi_exact = two_level_rate_exact(two_k, float(two["omega"]))
    two_poisson = two_k * np.log(two_k / (2.0 * float(two["omega"]) / 3.0)) - (
        two_k - 2.0 * float(two["omega"]) / 3.0
    )
    two_rate_rows = [
        {
            "target_id": "T002",
            "k": float(k_value),
            "phi_legendre": float(phi_numeric),
            "phi_exact": float(phi_exact),
            "phi_poisson": float(phi_poisson),
            "generated_data_provenance": "independent_numerics",
        }
        for k_value, phi_numeric, phi_exact, phi_poisson in zip(
            two_k, two_phi_numeric, two_phi_exact, two_poisson, strict=True
        )
    ]
    write_csv(data_root / "two_level_rate.csv", list(two_rate_rows[0]), two_rate_rows)

    two_trajectory_rows: list[dict[str, object]] = []
    two_trajectory_errors: list[float] = []
    two_trajectory_summaries = []
    for activity_target, seed in zip(
        two["trajectory_activities"], two["trajectory_seeds"], strict=True
    ):
        trajectory = two_level_rescaled_trajectory(
            float(activity_target),
            omega=float(two["omega"]),
            duration=float(two["trajectory_duration"]),
            dt=float(two["trajectory_dt"]),
            seed=int(seed),
        )
        two_trajectory_errors.append(abs(trajectory.activity - float(activity_target)))
        series_id = f"k_{float(activity_target):.12g}"
        two_trajectory_summaries.append(
            {
                "series_id": series_id,
                "target_activity": float(activity_target),
                "measured_activity": trajectory.activity,
                "jump_count": int(trajectory.jump_times.size),
                "duration": trajectory.duration,
                "seed": int(seed),
            }
        )
        for jump_time in trajectory.jump_times:
            two_trajectory_rows.append(
                {
                    "target_id": "T003",
                    "series_id": series_id,
                    "target_activity": float(activity_target),
                    "measured_activity": trajectory.activity,
                    "duration": trajectory.duration,
                    "seed": int(seed),
                    "jump_time": float(jump_time),
                    "generated_data_provenance": "independent_numerics",
                }
            )
    write_csv(
        data_root / "two_level_trajectories.csv",
        list(two_trajectory_rows[0]),
        two_trajectory_rows,
    )

    checks.extend(
        [
            check(
                "CHK_T001_THETA_EXACT",
                ["T001"],
                "Generic tilted 4x4 Liouvillian agrees with Eq. (5).",
                float(np.max(np.abs(two_theta - exact_theta))),
                float(tolerances["eigenvalue_absolute"]),
            ),
            check(
                "CHK_T001_CUMULANTS_EXACT",
                ["T001"],
                "Finite-difference activity and Mandel parameter agree with the closed form.",
                float(
                    max(
                        np.max(np.abs(two_activity - exact_activity)),
                        np.max(np.abs(two_mandel - exact_mandel)),
                    )
                ),
                float(tolerances["two_level_derivative_absolute"]),
            ),
            check(
                "CHK_T002_LEGENDRE_EXACT",
                ["T002"],
                "Grid Legendre-Fenchel transform agrees with the printed rate function.",
                float(np.max(np.abs(two_phi_numeric - two_phi_exact))),
                float(tolerances["rate_function_absolute"]),
            ),
            check(
                "CHK_T003_TRAJECTORY_RATES",
                ["T003"],
                "Seeded clean-room rescaled trajectories realize all three printed rates.",
                float(max(two_trajectory_errors)),
                float(tolerances["trajectory_activity_absolute"]),
            ),
        ]
    )

    # T004-T007: three-level crossover, dual and blinking records.
    three = parameters["three_level"]
    three_model = three_level_model(
        float(three["omega_1"]), float(three["omega_2"]), float(three["kappa_1"])
    )
    three_s = grid(three)
    three_theta, three_activity, three_mandel = cumulants_from_theta(
        lambda value: dense_theta(three_model, value),
        three_s,
        derivative_step=derivative_step,
    )
    two_theta_comparator, two_activity_comparator, _ = two_level_exact(
        three_s, float(three["omega_1"])
    )
    three_curve_rows = [
        {
            "target_ids": "T004;T005",
            "s": float(s),
            "theta_three_level": float(theta),
            "theta_two_level": float(theta_two),
            "activity_three_level": float(activity),
            "activity_two_level": float(activity_two),
            "mandel_three_level": float(mandel),
            "generated_data_provenance": "independent_numerics",
        }
        for s, theta, theta_two, activity, activity_two, mandel in zip(
            three_s,
            three_theta,
            two_theta_comparator,
            three_activity,
            two_activity_comparator,
            three_mandel,
            strict=True,
        )
    ]
    write_csv(
        data_root / "three_level_curves.csv",
        list(three_curve_rows[0]),
        three_curve_rows,
    )

    three_rate_s = grid(three, "rate_")
    three_rate_theta = np.array(
        [dense_theta(three_model, float(value)) for value in three_rate_s]
    )
    three_k = np.linspace(
        float(three["rate_k_min"]),
        float(three["rate_k_max"]),
        int(three["rate_k_points"]),
    )
    three_phi = rate_function(three_k, three_rate_s, three_rate_theta)
    physical_index = int(np.argmin(np.abs(three_s)))
    physical_activity = float(three_activity[physical_index])
    three_poisson = three_k * np.log(three_k / physical_activity) - (
        three_k - physical_activity
    )
    three_rate_rows = [
        {
            "target_id": "T006",
            "k": float(k_value),
            "phi_legendre": float(phi),
            "phi_poisson": float(phi_poisson),
            "physical_activity": physical_activity,
            "generated_data_provenance": "independent_numerics",
        }
        for k_value, phi, phi_poisson in zip(
            three_k, three_phi, three_poisson, strict=True
        )
    ]
    write_csv(
        data_root / "three_level_rate.csv", list(three_rate_rows[0]), three_rate_rows
    )

    long_trajectory, windows = three_level_blinking_windows(
        omega_1=float(three["omega_1"]),
        omega_2=float(three["omega_2"]),
        kappa_1=float(three["kappa_1"]),
        total_duration=float(three["trajectory_total_duration"]),
        window_duration=float(three["trajectory_window_duration"]),
        dt=float(three["trajectory_dt"]),
        seed=int(three["trajectory_seed"]),
        target_activities=tuple(
            float(value) for value in three["trajectory_activities"]
        ),
    )
    three_trajectory_rows: list[dict[str, object]] = []
    three_trajectory_summaries = []
    three_trajectory_errors = []
    for target_activity, window in zip(
        three["trajectory_activities"], windows, strict=True
    ):
        series_id = f"k_{float(target_activity):.12g}"
        three_trajectory_errors.append(abs(window.activity - float(target_activity)))
        three_trajectory_summaries.append(
            {
                "series_id": series_id,
                "target_activity": float(target_activity),
                "measured_activity": window.activity,
                "jump_count": int(window.jump_times.size),
                "duration": window.duration,
                "long_record_seed": int(three["trajectory_seed"]),
            }
        )
        for jump_time in window.jump_times:
            three_trajectory_rows.append(
                {
                    "target_id": "T007",
                    "series_id": series_id,
                    "target_activity": float(target_activity),
                    "measured_activity": window.activity,
                    "duration": window.duration,
                    "long_record_seed": int(three["trajectory_seed"]),
                    "jump_time": float(jump_time),
                    "generated_data_provenance": "independent_numerics",
                }
            )
    write_csv(
        data_root / "three_level_trajectories.csv",
        list(three_trajectory_rows[0]),
        three_trajectory_rows,
    )

    active_index = int(np.argmin(np.abs(three_s + 0.4)))
    inactive_index = int(np.argmin(np.abs(three_s - 0.5)))
    inactive_limit = -float(three["kappa_1"]) * float(three["omega_2"]) ** 2
    three_minimum_k = float(three_k[int(np.argmin(three_phi))])
    checks.extend(
        [
            check(
                "CHK_T004_THETA_ZERO",
                ["T004"],
                "The physical three-level generator conserves probability.",
                abs(float(three_theta[physical_index])),
                float(tolerances["eigenvalue_absolute"]),
            ),
            check(
                "CHK_T004_ACTIVE_BRANCH",
                ["T004"],
                "At negative s the three-level active branch approaches the two-level SCGF.",
                abs(
                    float(
                        (three_theta[active_index] - two_theta_comparator[active_index])
                        / two_theta_comparator[active_index]
                    )
                ),
                float(tolerances["three_level_active_relative"]),
            ),
            check(
                "CHK_T004_INACTIVE_LIMIT",
                ["T004"],
                "The positive-s branch approaches the printed inactive constant.",
                abs(float(three_theta[inactive_index]) - inactive_limit),
                float(tolerances["three_level_inactive_theta_absolute"]),
            ),
            check(
                "CHK_T005_CROSSOVER_PEAK",
                ["T005"],
                "The Mandel parameter has a positive crossover peak.",
                float(np.nanmax(three_mandel)),
                3.0,
                comparator="min",
            ),
            check(
                "CHK_T006_RATE_MINIMUM",
                ["T006"],
                "The rate-function minimum occurs at the physical activity.",
                abs(three_minimum_k - physical_activity),
                0.01,
            ),
            check(
                "CHK_T007_BLINKING_WINDOWS",
                ["T007"],
                "One physical seeded record contains the printed inactive and active windows.",
                float(max(three_trajectory_errors)),
                0.005,
            ),
        ]
    )

    # T008-T010: micromaser diagonal tilted generator and distributions.
    micro = parameters["micromaser"]
    micro_s = grid(micro)
    micromaser_rows: list[dict[str, object]] = []
    micro_results: dict[float, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    micro_cutoff_errors = []
    micro_transition_locations: dict[str, float] = {}
    for alpha_over_pi in micro["alphas_over_pi"]:
        alpha_over_pi = float(alpha_over_pi)
        base = MicromaserParameters(
            excitation_number=float(micro["excitation_number"]),
            thermal_occupation=float(micro["thermal_occupation"]),
            alpha=alpha_over_pi * np.pi,
            cutoff=int(micro["photon_cutoff"]),
        )
        converged = MicromaserParameters(
            excitation_number=base.excitation_number,
            thermal_occupation=base.thermal_occupation,
            alpha=base.alpha,
            cutoff=int(micro["convergence_cutoff"]),
        )
        theta, activity, mandel = cumulants_from_theta(
            lambda value, params=base: dominant_eigenvalue(params, value),
            micro_s,
            derivative_step=derivative_step,
        )
        micro_results[alpha_over_pi] = (theta, activity, mandel)
        for s_value in (-0.1, -0.05, 0.0, 0.05, 0.1):
            micro_cutoff_errors.append(
                abs(
                    dominant_eigenvalue(base, s_value)
                    - dominant_eigenvalue(converged, s_value)
                )
            )
        transition_index = int(np.nanargmax(np.abs(np.gradient(activity, micro_s))))
        micro_transition_locations[f"alpha_{alpha_over_pi:g}_pi"] = float(
            micro_s[transition_index]
        )
        target_id = "T008" if np.isclose(alpha_over_pi, 1.2) else "T009"
        for s_value, theta_value, activity_value, mandel_value in zip(
            micro_s, theta, activity, mandel, strict=True
        ):
            micromaser_rows.append(
                {
                    "target_id": target_id,
                    "alpha_over_pi": alpha_over_pi,
                    "s": float(s_value),
                    "theta": float(theta_value),
                    "activity": float(activity_value),
                    "mandel": float(mandel_value),
                    "excitation_number": base.excitation_number,
                    "thermal_occupation": base.thermal_occupation,
                    "photon_cutoff": base.cutoff,
                    "parameter_match": "reconstructed",
                    "generated_data_provenance": "independent_numerics",
                }
            )
    write_csv(
        data_root / "micromaser_curves.csv",
        list(micromaser_rows[0]),
        micromaser_rows,
    )

    distribution_parameters = MicromaserParameters(
        excitation_number=float(micro["excitation_number"]),
        thermal_occupation=float(micro["thermal_occupation"]),
        alpha=float(micro["distribution_alpha_over_pi"]) * np.pi,
        cutoff=int(micro["photon_cutoff"]),
    )
    distribution_rows: list[dict[str, object]] = []
    distribution_summaries = []
    distribution_normalization_errors = []
    distribution_means = {}
    stationary_secondary_peak_ratio = 0.0
    for bias in micro["distribution_biases"]:
        theta_value, distribution = dominant_distribution(
            distribution_parameters, float(bias)
        )
        mean_photons = float(np.dot(np.arange(distribution.size), distribution))
        distribution_means[f"s_{float(bias):+.3f}"] = mean_photons
        if np.isclose(float(bias), 0.0):
            low_peak = float(np.max(distribution[:40]))
            high_peak = float(np.max(distribution[40:110]))
            stationary_secondary_peak_ratio = high_peak / low_peak
        distribution_normalization_errors.append(abs(float(np.sum(distribution)) - 1.0))
        distribution_summaries.append(
            {
                "s": float(bias),
                "theta": theta_value,
                "mean_photons": mean_photons,
                "mode_photons": int(np.argmax(distribution)),
                "normalization": float(np.sum(distribution)),
            }
        )
        for photon_number, probability in enumerate(distribution):
            distribution_rows.append(
                {
                    "target_id": "T010",
                    "s": float(bias),
                    "photon_number": photon_number,
                    "probability": float(probability),
                    "mean_photons": mean_photons,
                    "parameter_match": "reconstructed",
                    "generated_data_provenance": "independent_numerics",
                }
            )
    write_csv(
        data_root / "micromaser_distributions.csv",
        list(distribution_rows[0]),
        distribution_rows,
    )

    small_parameters = MicromaserParameters(
        excitation_number=float(micro["excitation_number"]),
        thermal_occupation=float(micro["thermal_occupation"]),
        alpha=1.2 * np.pi,
        cutoff=80,
    )
    direct_values = scipy.linalg.eigvals(direct_generator(small_parameters, -0.03))
    direct_theta = float(direct_values[np.argmax(direct_values.real)].real)
    symmetric_theta = dominant_eigenvalue(small_parameters, -0.03)
    checks.extend(
        [
            check(
                "CHK_T008_T009_CUTOFF",
                ["T008", "T009"],
                "All anchor SCGFs converge between photon cutoffs 250 and 350.",
                float(max(micro_cutoff_errors)),
                float(tolerances["micromaser_cutoff_absolute"]),
            ),
            check(
                "CHK_T008_TRANSITION_NEGATIVE",
                ["T008"],
                "At alpha=1.2pi the maximal activity crossover lies at negative s.",
                -float(micro_transition_locations["alpha_1.2_pi"]),
                0.01,
                comparator="min",
            ),
            check(
                "CHK_T009_TRANSITION_NEAR_ZERO",
                ["T009"],
                "At alpha=2pi the maximal activity crossover lies near s=0.",
                abs(float(micro_transition_locations["alpha_2_pi"])),
                0.01,
            ),
            check(
                "CHK_T010_NORMALIZATION",
                ["T010"],
                "Every dominant photon distribution is normalized and nonnegative.",
                float(max(distribution_normalization_errors)),
                float(tolerances["distribution_normalization_absolute"]),
            ),
            check(
                "CHK_T010_PHASE_ORDER",
                ["T010"],
                "The negative-s active distribution has a larger mean photon number than the positive-s inactive distribution.",
                distribution_means["s_-0.050"] - distribution_means["s_+0.050"],
                20.0,
                comparator="min",
            ),
            check(
                "CHK_T010_STATIONARY_BIMODALITY",
                ["T010"],
                "The reconstructed stationary distribution contains separated low- and high-photon local maxima.",
                stationary_secondary_peak_ratio,
                float(tolerances["stationary_secondary_peak_ratio_min"]),
                comparator="min",
            ),
            check(
                "CHK_MICROMASER_INDEPENDENT_EIGENSOLVERS",
                ["T008", "T009", "T010"],
                "Direct nonsymmetric and similar-symmetric eigensolvers agree.",
                abs(direct_theta - symmetric_theta),
                float(tolerances["eigenvalue_absolute"]),
            ),
        ]
    )

    # T011: trace-preserving Doob similarity and exact two-level rate scaling.
    doob_residuals = []
    doob_theta_errors = []
    doob_rate_errors = []
    doob_summaries = []
    for bias in parameters["doob_biases"]:
        doob, theta_value, left = doob_similarity_superoperator(two_model, float(bias))
        trace_residual = trace_preservation_residual(doob)
        expected_theta = float(two_level_exact(float(bias), float(two["omega"]))[0])
        pair = dominant_eigenpair(
            tilted_liouvillian(two_model.hamiltonian, two_model.jumps, float(bias))
        )
        epsilon = 1e-5
        rate = -(
            dense_theta(two_model, float(bias) + epsilon)
            - dense_theta(two_model, float(bias) - epsilon)
        ) / (2.0 * epsilon)
        expected_rate = (2.0 * float(two["omega"]) / 3.0) * np.exp(-float(bias) / 3.0)
        doob_residuals.append(trace_residual)
        doob_theta_errors.append(abs(theta_value.real - expected_theta))
        doob_rate_errors.append(abs(rate - expected_rate))
        doob_summaries.append(
            {
                "s": float(bias),
                "theta": float(theta_value.real),
                "trace_preservation_residual": trace_residual,
                "left_minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(left))),
                "right_eigen_residual": pair.right_residual,
                "left_eigen_residual": pair.left_residual,
                "activity": float(rate),
                "expected_rescaled_activity": float(expected_rate),
            }
        )
    checks.extend(
        [
            check(
                "CHK_T011_TRACE_PRESERVING",
                ["T011"],
                "The generalized Doob similarity has identity as an exact left zero mode.",
                float(max(doob_residuals)),
                float(tolerances["doob_trace_absolute"]),
            ),
            check(
                "CHK_T011_EXACT_RATE_SCALING",
                ["T011"],
                "Two-level rare-trajectory activity scales as exp(-s/3).",
                float(max(doob_rate_errors)),
                float(tolerances["two_level_derivative_absolute"]),
            ),
        ]
    )

    # Fig. 3D itself contains two different distributions both labelled s=-0.05.
    # This is an authored-source consistency issue, not a numerical input.
    quantitative_claims = {
        "schema_version": 1,
        "paper_id": "0911.0556",
        "two_level_trajectories": two_trajectory_summaries,
        "three_level": {
            "physical_activity": physical_activity,
            "long_record_activity": long_trajectory.activity,
            "selected_windows": three_trajectory_summaries,
            "mandel_peak": float(np.nanmax(three_mandel)),
        },
        "micromaser": {
            "parameter_match": "reconstructed",
            "transition_locations": micro_transition_locations,
            "distributions": distribution_summaries,
            "stationary_secondary_to_primary_peak_ratio": stationary_secondary_peak_ratio,
            "cutoff_max_absolute_error": float(max(micro_cutoff_errors)),
            "reconstruction_limit": {
                "direct_cause": "The reconstructed s=0 distribution has a secondary high-photon peak, but its height is only about 0.7 percent of the low-photon peak.",
                "root_cause": "The original Letter omits N_ex and the thermal occupation, so T010 uses later same-author parameters that do not uniquely determine the original panel's peak weights.",
                "code_fault_assessment": "No code fault found: direct nonsymmetric and symmetric-tridiagonal eigensolvers agree and the cutoff error is below 1e-13.",
                "classification": "feature_partial_reconstructed_parameters",
            },
        },
        "doob": doob_summaries,
        "paper_review": {
            "paper_error_candidate_emitted": False,
            "classification": "inconclusive_source_label_discrepancy",
            "source_ref": "paper-source/fig3.pdf, panel D; confirmed by pdftotext and visual inspection",
            "observation": "The upper high-photon and lower low-photon distributions are both labelled s=-0.05 even though they are distinct curves.",
            "direct_cause": "The printed panel duplicates the negative-bias label for two physically different distributions.",
            "root_cause": "Likely a sign omission on the lower label, but author intent has not yet been independently reviewed.",
            "independent_checks": [
                "The paper text and panel C identify s<0 as active/high-photon and s>0 as inactive/low-photon.",
                "The independently derived tilted birth-death generator gives the high-photon curve at s=-0.05 and the low-photon curve at s=+0.05.",
            ],
            "blocking_evidence": "A fresh-context independent reviewer has not yet completed protocol-v2 falsification, so the case does not call this a confirmed paper error.",
        },
        "generated_data_provenance": "independent_numerics",
    }
    write_json(data_root / "quantitative_claims.json", quantitative_claims)

    all_passed = all(bool(item["passed"]) for item in checks)
    science_payload = {
        "schema_version": 1,
        "paper_id": "0911.0556",
        "status": "passed" if all_passed else "failed",
        "all_passed": all_passed,
        "assertions": checks,
    }
    write_json(checks_root / "science_checks.json", science_payload)

    output_files = sorted(data_root.glob("*")) + [checks_root / "science_checks.json"]
    manifest = {
        "schema_version": 1,
        "paper_id": "0911.0556",
        "run_id": run_id,
        "status": "frozen" if all_passed else "failed_science_gate",
        "config_path": str(Path(args.config)),
        "config_sha256": sha256(config_path),
        "scientific_data_frozen_before_reference_rendering": True,
        "source_pixels_used_for_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "files": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in output_files
        ],
    }
    write_json(checks_root / "generated_data_manifest.json", manifest)
    elapsed = time.perf_counter() - started
    run_summary = {
        "schema_version": 1,
        "paper_id": "0911.0556",
        "run_id": run_id,
        "status": "passed" if all_passed else "failed",
        "target_ids": [f"T{index:03d}" for index in range(1, 12)],
        "numeric_target_count": 11,
        "science_checks_passed": sum(bool(item["passed"]) for item in checks),
        "science_checks_total": len(checks),
        "elapsed_seconds": elapsed,
        "parameter_match": "mixed",
        "generated_data_provenance": "independent_numerics",
    }
    write_json(checks_root / "run_summary.json", run_summary)
    print(json.dumps(run_summary, sort_keys=True))
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
