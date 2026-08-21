#!/usr/bin/env python3
"""Run the whole-paper LMG reproduction from frozen configuration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from lmg_scaling.model import (  # noqa: E402
    classical_ground_energy,
    classical_minimum_mu,
    coordinate_ordered_sector,
    critical_excitation_spectrum,
    critical_excitation_spectra,
    exceptional_point_candidates,
    lmg_sector,
    local_separatrix_spacing,
    same_parity_spacing_profile,
    sector_diagonals,
    separatrix_spacing_with_selector,
    super_scar_record,
    theory_separatrix_coefficient,
    wkb_separatrix_index,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def full_spectrum(particles: int, coupling: float) -> np.ndarray:
    return np.sort(
        np.concatenate(
            [lmg_sector(particles, coupling, sector).energies for sector in (0, 1)]
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()

    config_path = (WORKSPACE / args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    output = (WORKSPACE / args.output_root).resolve()
    data_dir = output / "data"
    checks_dir = output / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    # Main Fig. 1: exact finite-N same-parity gaps, followed by the fit stated
    # in the caption.  The lambda grid is an explicit reconstruction because
    # the paper publishes no underlying point coordinates.
    fig1_samples: list[dict[str, object]] = []
    fig1_fits: list[dict[str, object]] = []
    for coupling in parameters["fig1_couplings"]:
        for sector in parameters["fig1_sectors"]:
            for selector in parameters["fig1_selectors"]:
                samples = []
                for particles in parameters["fig1_particle_numbers"]:
                    record = separatrix_spacing_with_selector(
                        particles,
                        coupling,
                        sector,
                        selector=selector,
                    )
                    samples.append(float(record["spacing"]))
                    fig1_samples.append(record)
                x = 1.0 / np.log(
                    np.asarray(parameters["fig1_particle_numbers"], dtype=float)
                )
                y = np.asarray(samples)
                fitted = float(np.dot(x, y) / np.dot(x, x))
                theory = theory_separatrix_coefficient(coupling)
                predicted = fitted * x
                fig1_fits.append(
                    {
                        "coupling": coupling,
                        "sector": sector,
                        "selector": selector,
                        "fitted_coefficient": fitted,
                        "theory_coefficient": theory,
                        "relative_difference": (fitted - theory) / theory,
                        "fit_rms": float(np.sqrt(np.mean((y - predicted) ** 2))),
                    }
                )

    # Larger-N data distinguish a slow/non-uniform asymptotic limit from a
    # stable contradiction.  A second 1/log(N)^2 term is reported rather than
    # silently forcing the finite paper window onto the leading coefficient.
    fig1_convergence: list[dict[str, object]] = []
    convergence_best_relative_errors = []
    for coupling in parameters["fig1_convergence_couplings"]:
        sector_errors = []
        for sector in parameters["fig1_sectors"]:
            numbers = np.asarray(
                parameters["fig1_convergence_particle_numbers"], dtype=float
            )
            gaps = np.asarray(
                [
                    local_separatrix_spacing(int(particles), coupling, sector)
                    for particles in numbers
                ]
            )
            inverse_log = 1.0 / np.log(numbers)
            design = np.column_stack((inverse_log, inverse_log**2))
            leading, subleading = np.linalg.lstsq(design, gaps, rcond=None)[0]
            theory = theory_separatrix_coefficient(coupling)
            relative = float((leading - theory) / theory)
            sector_errors.append(abs(relative))
            for particles, gap in zip(numbers.astype(int), gaps, strict=True):
                fig1_convergence.append(
                    {
                        "coupling": coupling,
                        "sector": sector,
                        "particles": int(particles),
                        "spacing": float(gap),
                        "leading_coefficient": float(leading),
                        "subleading_coefficient": float(subleading),
                        "theory_coefficient": theory,
                        "leading_relative_difference": relative,
                    }
                )
        convergence_best_relative_errors.append(min(sector_errors))

    # Main Fig. 2: the exact N=5000 spectrum and the printed every-eighth
    # display subset.  Fitting uses all positive k in the declared range.
    fig2_rows: list[dict[str, object]] = []
    fig2_fits: dict[str, tuple[float, float]] = {}
    spectra_by_convention = critical_excitation_spectra(
        parameters["fig2_particles"], parameters["fig2_levels"]
    )
    for convention, (k, excitation) in spectra_by_convention.items():
        select_fit = (k >= parameters["fig2_fit_min_k"]) & (
            k <= parameters["fig2_fit_max_k"]
        )
        slope, intercept = np.polyfit(
            np.log(k[select_fit]), np.log(excitation[select_fit]), 1
        )
        fig2_fits[convention] = (float(slope), float(intercept))
        display = (k % parameters["fig2_stride"]) == 0
        fig2_rows.extend(
            {
                "convention": convention,
                "k": int(index),
                "excitation_energy": float(energy),
                "ln_k": float(np.log(index)),
                "ln_excitation_energy": float(np.log(energy)),
                "displayed_in_reproduction": bool(show),
                "fitted_slope": float(slope),
                "fitted_log_intercept": float(intercept),
            }
            for index, energy, show in zip(k, excitation, display, strict=True)
        )
    slope, intercept = fig2_fits["merged"]

    # Independent N^{-1/3} check at fixed level index.
    scaling_rows: list[dict[str, object]] = []
    scaling_particles = np.asarray([1000, 2000, 3000, 4000, 5000])
    spectra = {
        int(particles): critical_excitation_spectrum(int(particles), 32)[1]
        for particles in scaling_particles
    }
    scaling_exponents = []
    for level in (8, 16, 32):
        values = np.asarray([spectra[int(n)][level - 1] for n in scaling_particles])
        exponent, log_amplitude = np.polyfit(
            np.log(scaling_particles), np.log(values), 1
        )
        scaling_exponents.append(float(exponent))
        for particles, value in zip(scaling_particles, values, strict=True):
            scaling_rows.append(
                {
                    "k": level,
                    "particles": int(particles),
                    "excitation_energy": float(value),
                    "fitted_n_exponent": float(exponent),
                    "fitted_amplitude": float(np.exp(log_amplitude)),
                }
            )

    # Super-scarring and transition indices quoted in the prose.
    quoted_denominators = {1.1: 120.0, 1.5: 16.0, 2.0: 8.0}
    scar_rows: list[dict[str, object]] = []
    scar_localization_rows: list[dict[str, object]] = []
    transition_relative_errors: list[float] = []
    largest_n_transition_errors: list[float] = []
    largest_n_wkb_errors: list[float] = []
    for coupling in parameters["scarring_couplings"]:
        for particles in parameters["scarring_particle_numbers"]:
            row = super_scar_record(
                particles,
                coupling,
                components=parameters["scarring_components"],
                mass_thresholds=tuple(
                    float(value) for value in parameters["scarring_mass_thresholds"]
                ),
            )
            quoted = particles / quoted_denominators[coupling]
            observed = float(row["full_spectrum_index_estimate"])
            relative_error = abs(observed - quoted) / max(quoted, 1.0)
            transition_relative_errors.append(relative_error)
            if particles == max(parameters["scarring_particle_numbers"]):
                largest_n_transition_errors.append(relative_error)
                largest_n_wkb_errors.append(float(row["wkb_index_relative_error"]))
            scar_rows.append(
                {
                    **row,
                    "quoted_transition_index": quoted,
                    "transition_index_relative_error": relative_error,
                }
            )

    # A fixed number of components cannot demonstrate an emergent localization
    # width.  Fit the actual interval needed to contain several fixed masses.
    # The threshold dependence is part of the evidence: a shrinking 50% core
    # must not be silently promoted to whole-wavefunction concentration.
    for coupling in parameters["scarring_couplings"]:
        selected_rows = [
            row for row in scar_rows if float(row["coupling"]) == float(coupling)
        ]
        particles = np.asarray(
            [int(row["particles"]) for row in selected_rows], dtype=float
        )
        for threshold in parameters["scarring_mass_thresholds"]:
            label = f"mass_{int(round(100 * float(threshold)))}"
            for branch in ("pair_lower", "pair_upper"):
                widths = np.asarray(
                    [float(row[f"{branch}_{label}_mu_width"]) for row in selected_rows]
                )
                exponent, log_amplitude = np.polyfit(
                    np.log(particles), np.log(widths), 1
                )
                scar_localization_rows.append(
                    {
                        "coupling": float(coupling),
                        "mass_threshold": float(threshold),
                        "branch": branch,
                        "fitted_width_n_exponent": float(exponent),
                        "fitted_width_amplitude": float(np.exp(log_amplitude)),
                        "minimum_width": float(np.min(widths)),
                        "maximum_width": float(np.max(widths)),
                    }
                )

    # Small-system dense diagonalization is intentionally independent of the
    # production tridiagonal eigensolver.
    diagonal, off_diagonal = sector_diagonals(18, 1.7)
    dense = np.diag(diagonal) + np.diag(off_diagonal, 1) + np.diag(off_diagonal, -1)
    dense_error = float(
        np.max(np.abs(np.linalg.eigvalsh(dense) - lmg_sector(18, 1.7).energies))
    )

    # Other quantitative claims: low-energy frequencies, classical minima,
    # non-equidistant normal-phase spectrum, and exponential doublet splitting.
    normal_n = int(parameters["normal_spacing_particles"])
    normal_coupling = float(parameters["normal_spacing_coupling"])
    normal_energies = full_spectrum(normal_n, normal_coupling)
    normal_gap = float(normal_energies[1] - normal_energies[0])
    normal_theory = float(np.sqrt(1.0 - normal_coupling**2))
    deformed_coupling = 1.5
    deformed_sector = lmg_sector(normal_n, deformed_coupling).energies
    deformed_gap = float(deformed_sector[1] - deformed_sector[0])
    deformed_theory = float(np.sqrt(2.0 * (deformed_coupling**2 - 1.0)))
    upper_gap = float(
        normal_energies[normal_n // 4 + 1] - normal_energies[normal_n // 4]
    )

    # The prose claim about the normal-phase spacing concerns an energy
    # dependence, not two selected gaps.  Freeze both parity sectors over the
    # complete band, and separately quantify the lower-energy branch and the
    # full-band trend.
    normal_spacing_rows: list[dict[str, object]] = []
    normal_spacing_metrics: dict[str, dict[str, float]] = {}
    for sector in (0, 1):
        rows = same_parity_spacing_profile(
            normal_n,
            normal_coupling,
            sector,
            bin_count=int(parameters["normal_spacing_bin_count"]),
        )
        normal_spacing_rows.extend(rows)
        normalized_energy = np.asarray(
            [float(row["normalized_energy"]) for row in rows]
        )
        mean_spacing = np.asarray([float(row["mean_spacing"]) for row in rows])
        lower = normalized_energy <= 0.5
        lower_slope = float(
            np.polyfit(normalized_energy[lower], mean_spacing[lower], 1)[0]
        )
        full_slope = float(np.polyfit(normalized_energy, mean_spacing, 1)[0])
        normal_spacing_metrics[str(sector)] = {
            "lower_half_slope": lower_slope,
            "full_band_slope": full_slope,
            "lower_half_correlation": float(
                np.corrcoef(normalized_energy[lower], mean_spacing[lower])[0, 1]
            ),
        }

    tunnel_rows = []
    for particles in (40, 60, 80, 100, 120):
        even = lmg_sector(particles, 1.5, 0).energies[0]
        odd = lmg_sector(particles, 1.5, 1).energies[0]
        tunnel_rows.append(
            {"particles": particles, "ground_doublet_splitting": float(abs(even - odd))}
        )
    positive_tunnel = [
        row for row in tunnel_rows if row["ground_doublet_splitting"] > 0
    ]
    tunnel_slope = float(
        np.polyfit(
            [row["particles"] for row in positive_tunnel],
            np.log([row["ground_doublet_splitting"] for row in positive_tunnel]),
            1,
        )[0]
    )

    # The paper explicitly leaves the coordinate-operator ordering
    # unspecified.  Run two natural self-adjoint prescriptions rather than
    # silently choosing one, and expose their convergence against Eq. (1).
    ordering_rows: list[dict[str, object]] = []
    ordering_scaling: dict[str, float] = {}
    for coupling in parameters["ordering_couplings"]:
        for sector in (0, 1):
            for ordering in parameters["ordering_prescriptions"]:
                particle_numbers: list[int] = []
                rms_errors: list[float] = []
                for particles in parameters["ordering_particle_numbers"]:
                    exact = (
                        2.0
                        * lmg_sector(int(particles), float(coupling), sector).energies
                        / int(particles)
                    )
                    ordered = coordinate_ordered_sector(
                        int(particles),
                        float(coupling),
                        sector,
                        ordering=str(ordering),
                    )
                    difference = ordered - exact
                    rms = float(np.sqrt(np.mean(difference**2)))
                    particle_numbers.append(int(particles))
                    rms_errors.append(rms)
                    ordering_rows.append(
                        {
                            "particles": int(particles),
                            "coupling": float(coupling),
                            "sector": sector,
                            "ordering": str(ordering),
                            "rms_normalized_spectrum_difference": rms,
                            "max_normalized_spectrum_difference": float(
                                np.max(np.abs(difference))
                            ),
                        }
                    )
                exponent = float(
                    np.polyfit(np.log(particle_numbers), np.log(rms_errors), 1)[0]
                )
                key = f"lambda_{coupling}:sector_{sector}:{ordering}"
                ordering_scaling[key] = exponent
                for row in ordering_rows:
                    if (
                        float(row["coupling"]) == float(coupling)
                        and int(row["sector"]) == sector
                        and str(row["ordering"]) == str(ordering)
                    ):
                        row["fitted_rms_n_exponent"] = exponent

    # Exceptional points are located as double roots of the characteristic
    # polynomial in complex coupling.  This is a genuine complex-plane solve,
    # not a real-axis nearest-gap proxy.
    exceptional_rows: list[dict[str, object]] = []
    exceptional_summary_rows: list[dict[str, object]] = []
    for particles in parameters["exceptional_point_particle_numbers"]:
        candidates = exceptional_point_candidates(
            int(particles),
            real_seeds=tuple(
                float(value) for value in parameters["exceptional_point_real_seeds"]
            ),
            imaginary_seeds=tuple(
                float(value)
                for value in parameters["exceptional_point_imaginary_seeds"]
            ),
            residual_tolerance=float(
                parameters["exceptional_point_backward_error_tolerance"]
            ),
            eigenvalue_gap_tolerance=float(
                parameters["exceptional_point_relative_gap_tolerance"]
            ),
            center_tolerance=float(parameters["exceptional_point_center_tolerance"]),
            minimum_eigenvector_condition=float(
                parameters["exceptional_point_minimum_condition"]
            ),
        )
        exceptional_rows.extend(candidates)
        near_real_threshold = float(parameters["exceptional_point_near_real_threshold"])
        energy_window = float(
            parameters["exceptional_point_separatrix_energy_window_per_particle"]
        )
        near_real = [
            row
            for row in candidates
            if float(row["coupling_imaginary"]) < near_real_threshold
        ]
        near_separatrix = [
            row
            for row in near_real
            if abs(abs(float(row["energy_per_particle_real"])) - 0.5) < energy_window
        ]
        below_transition = [
            row for row in near_real if float(row["coupling_real"]) < 1.0
        ]
        away_from_separatrix = [
            row
            for row in near_real
            if float(row["coupling_real"]) > 1.0
            and abs(abs(float(row["energy_per_particle_real"])) - 0.5) >= energy_window
        ]
        closest = min(
            candidates,
            key=lambda row: (
                float(row["coupling_imaginary"]),
                abs(abs(float(row["energy_per_particle_real"])) - 0.5),
            ),
        )
        exceptional_summary_rows.append(
            {
                "particles": int(particles),
                "candidate_count": len(candidates),
                "attempted_seed_count": sum(
                    max(len(lmg_sector(int(particles), seed, sector).energies) - 1, 0)
                    for sector in (0, 1)
                    for seed in parameters["exceptional_point_real_seeds"]
                )
                * len(parameters["exceptional_point_imaginary_seeds"]),
                "search_real_seed_min": min(parameters["exceptional_point_real_seeds"]),
                "search_real_seed_max": max(parameters["exceptional_point_real_seeds"]),
                "search_imaginary_seed_min": min(
                    parameters["exceptional_point_imaginary_seeds"]
                ),
                "search_imaginary_seed_max": max(
                    parameters["exceptional_point_imaginary_seeds"]
                ),
                "nearest_real_coupling": float(closest["coupling_real"]),
                "nearest_imaginary_coupling": float(closest["coupling_imaginary"]),
                "nearest_energy_per_particle": float(
                    closest["energy_per_particle_real"]
                ),
                "distance_to_lambda_one": float(
                    abs(
                        complex(
                            float(closest["coupling_real"]) - 1.0,
                            float(closest["coupling_imaginary"]),
                        )
                    )
                ),
                "near_real_count": len(near_real),
                "near_real_near_separatrix_count": len(near_separatrix),
                "near_real_below_transition_count": len(below_transition),
                "near_real_above_transition_away_from_separatrix_count": len(
                    away_from_separatrix
                ),
            }
        )

    exact_ground = float(full_spectrum(5000, 1.5)[0])
    classical_ground = classical_ground_energy(5000, 1.5)
    ground_relative = abs(exact_ground - classical_ground) / abs(classical_ground)
    primary_fig1 = [
        row
        for row in fig1_fits
        if row["selector"] == parameters["fig1_primary_selector"]
    ]
    max_fig1_relative = float(
        max(abs(float(row["relative_difference"])) for row in primary_fig1)
    )

    formula_rows = [
        {
            "check": "tridiagonal_dense",
            "value": dense_error,
            "reference": 0.0,
            "absolute_error": dense_error,
        },
        {
            "check": "normal_harmonic_gap",
            "value": normal_gap,
            "reference": normal_theory,
            "absolute_error": abs(normal_gap - normal_theory),
        },
        {
            "check": "deformed_harmonic_gap",
            "value": deformed_gap,
            "reference": deformed_theory,
            "absolute_error": abs(deformed_gap - deformed_theory),
        },
        {
            "check": "classical_mu_lambda_2",
            "value": classical_minimum_mu(2.0),
            "reference": np.sqrt(3.0) / 2.0,
            "absolute_error": 0.0,
        },
        {
            "check": "large_n_ground_energy",
            "value": exact_ground,
            "reference": classical_ground,
            "absolute_error": abs(exact_ground - classical_ground),
        },
        {
            "check": "normal_spectrum_upper_gap",
            "value": upper_gap,
            "reference": normal_gap,
            "absolute_error": abs(upper_gap - normal_gap),
        },
        {
            "check": "tunneling_log_slope",
            "value": tunnel_slope,
            "reference": 0.0,
            "absolute_error": abs(tunnel_slope),
        },
        {
            "check": "critical_k_exponent",
            "value": float(slope),
            "reference": 4.0 / 3.0,
            "absolute_error": abs(float(slope) - 4.0 / 3.0),
        },
        {
            "check": "critical_n_exponent_mean",
            "value": float(np.mean(scaling_exponents)),
            "reference": -1.0 / 3.0,
            "absolute_error": abs(float(np.mean(scaling_exponents)) + 1.0 / 3.0),
        },
    ]
    formula_rows.extend(
        {
            "check": f"separatrix_wkb_index_lambda_{coupling}",
            "value": wkb_separatrix_index(
                max(parameters["scarring_particle_numbers"]), coupling
            ),
            "reference": max(parameters["scarring_particle_numbers"])
            / quoted_denominators[coupling],
            "absolute_error": abs(
                wkb_separatrix_index(
                    max(parameters["scarring_particle_numbers"]), coupling
                )
                - max(parameters["scarring_particle_numbers"])
                / quoted_denominators[coupling]
            ),
        }
        for coupling in parameters["scarring_couplings"]
    )

    write_csv(data_dir / "fig1_spacing_samples.csv", fig1_samples)
    write_csv(data_dir / "fig1_spacing_scaling.csv", fig1_fits)
    write_csv(data_dir / "fig1_asymptotic_convergence.csv", fig1_convergence)
    write_csv(data_dir / "fig2_critical_spectrum.csv", fig2_rows)
    write_csv(data_dir / "critical_n_scaling.csv", scaling_rows)
    write_csv(data_dir / "super_scar_checks.csv", scar_rows)
    write_csv(data_dir / "super_scar_localization_scaling.csv", scar_localization_rows)
    write_csv(data_dir / "tunneling_checks.csv", tunnel_rows)
    write_csv(data_dir / "normal_spacing_profile.csv", normal_spacing_rows)
    write_csv(data_dir / "ordering_comparison.csv", ordering_rows)
    write_csv(data_dir / "exceptional_points.csv", exceptional_rows)
    write_csv(data_dir / "exceptional_point_summary.csv", exceptional_summary_rows)
    write_csv(data_dir / "formula_checks.csv", formula_rows)

    assertions = {
        "exact_tridiagonal_crosscheck": dense_error
        < tolerances["tridiagonal_dense_max_error"],
        "critical_k_four_thirds": abs(slope / (4.0 / 3.0) - 1.0)
        < tolerances["critical_slope_relative"],
        "critical_n_minus_one_third": max(
            abs(value + 1.0 / 3.0) for value in scaling_exponents
        )
        < tolerances["critical_n_exponent_absolute"],
        "large_n_ground_energy": ground_relative
        < tolerances["ground_energy_relative_large_n"],
        "normal_frequency": abs(normal_gap / normal_theory - 1.0) < 0.01,
        "deformed_frequency": abs(deformed_gap / deformed_theory - 1.0) < 0.01,
        "normal_spacing_full_band_frozen": all(
            sum(
                int(row["level_pair_count"])
                for row in normal_spacing_rows
                if int(row["sector"]) == sector
            )
            == len(lmg_sector(normal_n, normal_coupling, sector).energies) - 1
            for sector in (0, 1)
        ),
        "normal_spacing_lower_branch_increases": all(
            metrics["lower_half_slope"] > 0.0
            and metrics["lower_half_correlation"] > 0.9
            for metrics in normal_spacing_metrics.values()
        ),
        "doublet_splitting_exponential": tunnel_slope < 0.0,
        "transition_indices_large_n": max(largest_n_transition_errors)
        < tolerances["transition_index_relative"],
        "wkb_action_predicts_transition_indices": max(largest_n_wkb_errors)
        < tolerances["wkb_transition_index_relative"],
        "super_scar_pair_exceeds_outside_neighbors": all(
            float(row["pair_minus_outside_mean"]) > 0.0 for row in scar_rows
        ),
        "fig1_caption_strict_n_interval": all(
            500 < particles < 1500 for particles in parameters["fig1_particle_numbers"]
        ),
        "fig1_selector_and_parity_sensitivity_frozen": len(fig1_fits)
        == len(parameters["fig1_couplings"])
        * len(parameters["fig1_sectors"])
        * len(parameters["fig1_selectors"]),
        "fig1_large_n_asymptotic_crosscheck": max(convergence_best_relative_errors)
        < tolerances["fig1_asymptotic_best_sector_relative"],
        "fig2_literal_every_eighth_indices": all(
            (int(row["k"]) % parameters["fig2_stride"] == 0)
            == bool(row["displayed_in_reproduction"])
            for row in fig2_rows
        ),
        "ordering_campaign_complete": len(ordering_rows)
        == len(parameters["ordering_particle_numbers"])
        * len(parameters["ordering_couplings"])
        * len(parameters["ordering_prescriptions"])
        * 2,
        "exceptional_point_double_roots_found": all(
            int(row["candidate_count"]) > 0 for row in exceptional_summary_rows
        ),
        "exceptional_point_residuals_small": all(
            float(row["relative_characteristic_backward_error"])
            < parameters["exceptional_point_backward_error_tolerance"]
            and float(row["relative_derivative_backward_error"])
            < parameters["exceptional_point_backward_error_tolerance"]
            and float(row["relative_eigenvalue_gap"])
            < parameters["exceptional_point_relative_gap_tolerance"]
            and float(row["eigenvector_condition_number"])
            > parameters["exceptional_point_minimum_condition"]
            for row in exceptional_rows
        ),
    }
    science = {
        "schema_version": 1,
        "paper_id": "quant-ph-0507004",
        "status": "passed" if all(assertions.values()) else "failed",
        "assertions": [
            {"assertion_id": key, "status": "passed" if value else "failed"}
            for key, value in assertions.items()
        ],
        "metrics": {
            "fig1_max_finite_fit_vs_asymptotic_relative_difference": max_fig1_relative,
            "fig1_large_n_best_sector_relative_errors": convergence_best_relative_errors,
            "fig2_fitted_k_exponents": {
                key: value[0] for key, value in fig2_fits.items()
            },
            "fig2_merged_fitted_log_intercept": float(intercept),
            "critical_n_exponents": scaling_exponents,
            "ground_energy_relative_error": ground_relative,
            "super_scar_weight_range": [
                min(float(row["pair_mean_weight"]) for row in scar_rows),
                max(float(row["pair_mean_weight"]) for row in scar_rows),
            ],
            "transition_index_max_relative_error": max(transition_relative_errors),
            "transition_index_largest_n_max_relative_error": max(
                largest_n_transition_errors
            ),
            "wkb_transition_index_largest_n_max_relative_error": max(
                largest_n_wkb_errors
            ),
            "wkb_transition_indices": {
                str(coupling): wkb_separatrix_index(
                    max(parameters["scarring_particle_numbers"]), coupling
                )
                for coupling in parameters["scarring_couplings"]
            },
            "super_scar_localization_scaling": scar_localization_rows,
            "tunneling_log_slope": tunnel_slope,
            "normal_spacing_energy_trends": normal_spacing_metrics,
            "ordering_rms_n_exponents": ordering_scaling,
            "exceptional_point_summary": exceptional_summary_rows,
        },
        "paper_comparison_findings": [
            {
                "finding_id": "FIG1-FINITE-N-MISMATCH",
                "classification": "inconclusive_pending_fresh_review",
                "source_ref": "Main Fig. 1 and Eq. (12)",
                "observed": "Exact finite-N midpoint-selected same-parity gaps do not uniformly match the printed asymptotic coefficient over N=500..1500.",
                "max_relative_difference": max_fig1_relative,
                "boundary": "The paper omits raw fitted gaps and its precise level-selection/tie-breaking procedure. Both parities, three selectors, the strict caption N interval, and a larger-N convergence campaign are frozen; no paper-error claim is made by the runner.",
            },
            {
                "finding_id": "NORMAL-SPACING-RANGE",
                "classification": "range_resolved_pending_fresh_review",
                "source_ref": "Paragraph after Eq. (10)",
                "observed": "The mean same-parity spacing rises strongly on the lower-energy half but returns symmetrically on the upper half, so a literal full-band monotonic reading is false.",
                "boundary": "The paper does not state the intended energy interval. The runner reports both branches and does not silently convert the lower-branch result into a full-band pass.",
            },
            {
                "finding_id": "ORDERING-NONUNIQUENESS",
                "classification": "publication_underspecified",
                "source_ref": "Ordering paragraph after Eq. (15)",
                "observed": "Two explicit self-adjoint orderings give different finite-N convergence exponents and neither prescription is identified by the paper.",
                "boundary": "This campaign makes the missing ordering operational; it cannot prove that the authors used either reconstructed prescription.",
            },
            {
                "finding_id": "EXCEPTIONAL-POINT-CAMPAIGN",
                "classification": "finite_domain_certified_feature_test",
                "source_ref": "Exceptional-point claims (i)-(iii)",
                "observed": "Finite-N complex-coupling double roots pass scale-aware characteristic errors, direct eigenvalue coalescence, energy-center agreement, and an eigenvector-conditioning certificate.",
                "boundary": "The complete seed census is recorded, but local root discovery is not a certified count over a continuous complex domain. It therefore tests finite-N features and cannot prove global exclusion or the N-to-infinity accumulation statement.",
            },
            {
                "finding_id": "SUPER-SCAR-ACTION-AND-WIDTH",
                "classification": "claim_resolved_by_explicit_observable",
                "source_ref": "WKB Eq. (10), super-scarring paragraph, and Eq. (16)",
                "observed": "The two-lobe separatrix action predicts the quoted transition indices without fitting them. Fixed-mass widths are measured at 50%, 75%, 90%, and 99%, so the shrinking localized core is separated from any stronger whole-wavefunction claim.",
                "boundary": "A threshold-dependent finite-N width campaign does not assume that every fixed probability mass must shrink. Any threshold that fails to shrink remains visible rather than being converted into a pass.",
            },
        ],
    }
    science_path = checks_dir / "science_checks.json"
    science_path.write_text(json.dumps(science, indent=2) + "\n", encoding="utf-8")

    output_paths = [
        data_dir / "fig1_spacing_samples.csv",
        data_dir / "fig1_spacing_scaling.csv",
        data_dir / "fig1_asymptotic_convergence.csv",
        data_dir / "fig2_critical_spectrum.csv",
        data_dir / "critical_n_scaling.csv",
        data_dir / "super_scar_checks.csv",
        data_dir / "super_scar_localization_scaling.csv",
        data_dir / "tunneling_checks.csv",
        data_dir / "normal_spacing_profile.csv",
        data_dir / "ordering_comparison.csv",
        data_dir / "exceptional_points.csv",
        data_dir / "exceptional_point_summary.csv",
        data_dir / "formula_checks.csv",
        science_path,
    ]
    manifest = {
        "schema_version": 1,
        "files": [
            {
                "path": str(path.relative_to(output)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in output_paths
        ],
    }
    (checks_dir / "generated_data_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "schema_version": 1,
        "paper_id": "quant-ph-0507004",
        "status": science["status"],
        "parameters": parameters,
        "config_sha256": sha256(config_path),
        "outputs_sha256": {
            str(path.relative_to(output)): sha256(path) for path in output_paths
        },
    }
    (checks_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if science["status"] != "passed":
        raise SystemExit("implementation-level scientific assertions failed")


if __name__ == "__main__":
    main()
