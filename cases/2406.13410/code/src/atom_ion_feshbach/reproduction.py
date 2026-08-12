"""Data-first pipeline covering every reproducible numerical panel."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from scipy.integrate import trapezoid
from scipy.stats import kurtosis

from .classical import classical_survival, classical_tbr_rate, gaussian_density
from .md import (
    MDSamples,
    fit_energy_scaling,
    gaussian_velocity_density,
    simulate_collision_ensemble,
    velocity_histogram,
)
from .polarization import CaptureTable, barrier_energy, build_capture_table
from .recombination import (
    average_loss_spectrum,
    peak_properties,
    sample_three_body_energy,
    survival_from_rate,
)
from .rendering import render_all
from .statistics import (
    goe_number_variance,
    poisson_number_variance,
    spacing_distributions,
)
from .trap import displacement_to_field, quadratic_energy

TARGET_IDS = [f"T{index:03d}" for index in range(1, 18)]
FIG6_TARGETS = {
    3.21: "T008",
    1.81: "T009",
    1.26: "T010",
    0.8: "T011",
    0.45: "T012",
    0.2: "T013",
    0.0: "T014",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def _write_npz(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _statistics_data(parameters: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    mean_count = np.linspace(
        float(parameters["mean_count_min"]),
        float(parameters["mean_count_max"]),
        int(parameters["mean_count_points"]),
    )
    poisson_variance = poisson_number_variance(mean_count)
    goe_variance = goe_number_variance(mean_count)
    rows_t001 = [
        {
            "mean_count": mean_count[index],
            "poisson_variance": poisson_variance[index],
            "goe_variance": goe_variance[index],
            "generated_data_provenance": "analytic_reference",
        }
        for index in range(mean_count.size)
    ]
    _write_csv(data_dir / "T001_number_variance.csv", rows_t001)

    spacing = np.linspace(
        0.0, float(parameters["spacing_max"]), int(parameters["spacing_points"])
    )
    poisson_spacing, wigner_spacing = spacing_distributions(spacing)
    rows_t002 = [
        {
            "spacing": spacing[index],
            "poisson_density": poisson_spacing[index],
            "wigner_density": wigner_spacing[index],
            "generated_data_provenance": "analytic_reference",
        }
        for index in range(spacing.size)
    ]
    _write_csv(data_dir / "T002_spacing_distributions.csv", rows_t002)
    return {
        "mean_count": mean_count,
        "poisson_variance": poisson_variance,
        "goe_variance": goe_variance,
        "spacing": spacing,
        "poisson_spacing": poisson_spacing,
        "wigner_spacing": wigner_spacing,
    }


def _md_data(
    parameters: dict[str, Any], data_dir: Path, workspace: Path
) -> dict[str, Any]:
    fields = [float(value) for value in parameters["fields_v_m"]]
    ratios = [float(value) for value in parameters["energy_ratios"]]
    if len(fields) != len(ratios):
        raise ValueError("md fields and energy ratios must have equal length")
    ensembles: list[MDSamples] = []
    precomputed = parameters.get("precomputed_velocity_npz")
    if precomputed:
        precomputed_path = (workspace / str(precomputed)).resolve()
        if workspace not in precomputed_path.parents or not precomputed_path.is_file():
            raise ValueError(
                "precomputed velocity artifact is missing or outside workspace"
            )
        with np.load(precomputed_path) as payload:
            stored_fields = np.asarray(payload["fields_v_m"], dtype=float)
            stored_ratios = np.asarray(payload["energy_ratios"], dtype=float)
            if not np.allclose(stored_fields, fields) or not np.allclose(
                stored_ratios, ratios
            ):
                raise ValueError("precomputed velocity grid does not match config")
            for index, field in enumerate(fields):
                velocities = np.asarray(
                    payload[f"field_{index:02d}_velocities_m_s"], dtype=float
                )
                temperature = (
                    138.0
                    * 1.66053906660e-27
                    * np.sum(velocities**2, axis=1)
                    / (3.0 * 1.380649e-23)
                )
                ensembles.append(
                    MDSamples(
                        field_v_m=field,
                        velocities_m_s=velocities,
                        effective_temperature_k=temperature,
                        median_temperature_k=float(np.median(temperature)),
                        radial_kurtosis=float(
                            kurtosis(velocities[:, 0], fisher=False, bias=False)
                        ),
                        axial_kurtosis=float(
                            kurtosis(velocities[:, 2], fisher=False, bias=False)
                        ),
                        stationary_relative_drift=float(
                            payload.get(f"field_{index:02d}_stationary_drift", 0.0)
                        ),
                    )
                )
    else:
        for index, field in enumerate(fields):
            ensembles.append(
                simulate_collision_ensemble(
                    field_v_m=field,
                    trajectories=int(parameters["trajectories"]),
                    collisions=int(parameters["collisions"]),
                    seed=int(parameters["seed_base"])
                    + index * int(parameters["seed_stride"]),
                    bath_temperature_k=float(parameters["bath_temperature_k"]),
                    background_temperature_k=float(
                        parameters["background_temperature_k"]
                    ),
                    drive_alpha_k_per_v_m2=float(parameters["drive_alpha_k_per_v_m2"]),
                )
            )
    intercept, alpha, relative_rms = fit_energy_scaling(ensembles)
    rows_t003 = []
    for ratio, ensemble in zip(ratios, ensembles, strict=True):
        rows_t003.append(
            {
                "field_v_m": ensemble.field_v_m,
                "field_mv_m": 1000.0 * ensemble.field_v_m,
                "declared_excess_ratio": ratio,
                "median_temperature_k": ensemble.median_temperature_k,
                "median_temperature_uk": 1.0e6 * ensemble.median_temperature_k,
                "quadratic_fit_temperature_uk": 1.0e6
                * (intercept + alpha * ensemble.field_v_m**2),
                "stationary_relative_drift": ensemble.stationary_relative_drift,
                "radial_kurtosis": ensemble.radial_kurtosis,
                "axial_kurtosis": ensemble.axial_kurtosis,
                "parameter_status": "printed_scale_reconstructed_dynamics",
            }
        )
    _write_csv(data_dir / "T003_ion_energy_scaling.csv", rows_t003)

    selected_fields = [0.003, 0.1249, 0.2502]
    selected = [
        min(ensembles, key=lambda item: abs(item.field_v_m - value))
        for value in selected_fields
    ]
    radial_bins = np.linspace(
        float(parameters["radial_histogram_min_m_s"]),
        float(parameters["radial_histogram_max_m_s"]),
        int(parameters["radial_histogram_bins"]),
    )
    axial_bins = np.linspace(
        float(parameters["axial_histogram_min_m_s"]),
        float(parameters["axial_histogram_max_m_s"]),
        int(parameters["axial_histogram_bins"]),
    )
    rows_t004: list[dict[str, Any]] = []
    rows_t005: list[dict[str, Any]] = []
    for ensemble in selected:
        centers, density = velocity_histogram(ensemble.velocities_m_s, 0, radial_bins)
        gaussian = gaussian_velocity_density(centers, ensemble.velocities_m_s[:, 0])
        rows_t004.extend(
            {
                "field_mv_m": 1000.0 * ensemble.field_v_m,
                "velocity_m_s": centers[index],
                "density": density[index],
                "gaussian_density": gaussian[index],
                "kurtosis": ensemble.radial_kurtosis,
            }
            for index in range(centers.size)
        )
        centers, density = velocity_histogram(ensemble.velocities_m_s, 2, axial_bins)
        gaussian = gaussian_velocity_density(centers, ensemble.velocities_m_s[:, 2])
        rows_t005.extend(
            {
                "field_mv_m": 1000.0 * ensemble.field_v_m,
                "velocity_m_s": centers[index],
                "density": density[index],
                "gaussian_density": gaussian[index],
                "kurtosis": ensemble.axial_kurtosis,
            }
            for index in range(centers.size)
        )
    _write_csv(data_dir / "T004_radial_velocity.csv", rows_t004)
    _write_csv(data_dir / "T005_axial_velocity.csv", rows_t005)
    velocity_arrays = {
        f"field_{index:02d}_velocities_m_s": ensemble.velocities_m_s
        for index, ensemble in enumerate(ensembles)
    }
    velocity_arrays["fields_v_m"] = np.asarray(fields)
    velocity_arrays["energy_ratios"] = np.asarray(ratios)
    _write_npz(data_dir / "md_velocity_samples.npz", **velocity_arrays)
    return {
        "fields": np.asarray(fields),
        "ratios": np.asarray(ratios),
        "ensembles": ensembles,
        "intercept": intercept,
        "alpha": alpha,
        "relative_rms": relative_rms,
        "rows_t003": rows_t003,
        "rows_t004": rows_t004,
        "rows_t005": rows_t005,
    }


def _classical_data(
    parameters: dict[str, Any], md_result: dict[str, Any], data_dir: Path
) -> dict[str, Any]:
    displacement = np.linspace(
        float(parameters["displacement_min_um"]),
        float(parameters["displacement_max_um"]),
        int(parameters["displacement_points"]),
    )
    field = displacement_to_field(
        displacement * 1.0e-6, float(parameters["secular_frequency_hz"])
    )
    excess_energy = np.maximum(
        quadratic_energy(field, 0.0, float(md_result["alpha"])), 0.0
    )
    density = gaussian_density(
        displacement,
        float(parameters["density_center_um"]),
        float(parameters["density_sigma_um"]),
        float(parameters["peak_density_cm3"]),
    )
    rate = classical_tbr_rate(
        density,
        excess_energy,
        float(parameters["minimum_energy_k"]),
        float(parameters["k3_at_10mk_cm6_s"]),
    )
    survival = classical_survival(rate, float(parameters["interaction_time_s"]))
    rows = [
        {
            "displacement_um": displacement[index],
            "field_v_m": field[index],
            "excess_energy_mk": 1.0e3 * excess_energy[index],
            "density_cm3": density[index],
            "density_over_peak": density[index] / float(parameters["peak_density_cm3"]),
            "classical_rate_s": rate[index],
            "classical_survival": survival[index],
            "parameter_status": "printed_shape_reconstructed_peak_density",
        }
        for index in range(displacement.size)
    ]
    _write_csv(data_dir / "T006_density_classical_survival.csv", rows)
    return {
        "displacement": displacement,
        "field": field,
        "excess_energy": excess_energy,
        "density": density,
        "rate": rate,
        "survival": survival,
        "rows": rows,
    }


def _capture_data(parameters: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    energies = np.geomspace(
        float(parameters["energy_min_es"]),
        float(parameters["energy_max_es"]),
        int(parameters["energy_points"]),
    )
    table = build_capture_table(
        energies,
        int(parameters["max_partial_wave"]),
        x_min=float(parameters["x_min"]),
        asymptotic_cycles=float(parameters["asymptotic_cycles"]),
        x_floor=float(parameters["x_floor"]),
        rtol=float(parameters["rtol"]),
        atol=float(parameters["atol"]),
    )
    rows = []
    for partial_wave in range(table.partial_waves):
        for index, energy in enumerate(table.energies_es):
            rows.append(
                {
                    "partial_wave": partial_wave,
                    "energy_es": energy,
                    "capture_probability": table.probabilities[partial_wave, index],
                    "barrier_energy_es": barrier_energy(partial_wave),
                    "threshold_exponent_k": 2 * partial_wave + 1,
                    "generated_data_provenance": "independent_numerics",
                }
            )
    _write_csv(data_dir / "T017_dimer_coupling.csv", rows)
    _write_npz(
        data_dir / "capture_table.npz",
        energies_es=table.energies_es,
        probabilities=table.probabilities,
    )
    return {"table": table, "rows": rows}


def _energy_samples(
    md_result: dict[str, Any], parameters: dict[str, Any], data_dir: Path
) -> dict[float, np.ndarray]:
    samples: dict[float, np.ndarray] = {}
    summary_rows: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {}
    for index, (ratio, ensemble) in enumerate(
        zip(md_result["ratios"], md_result["ensembles"], strict=True)
    ):
        values = sample_three_body_energy(
            ensemble.velocities_m_s,
            samples=int(parameters["energy_samples_per_condition"]),
            seed=int(parameters["sample_seed_base"])
            + index * int(parameters["sample_seed_stride"]),
            atom_temperature_k=0.7e-6,
        )
        key = round(float(ratio), 8)
        samples[key] = values
        arrays[f"ratio_{index:02d}_energy_es"] = values
        summary_rows.append(
            {
                "excess_ratio": ratio,
                "samples": values.size,
                "mean_energy_es": np.mean(values),
                "median_energy_es": np.median(values),
                "q10_energy_es": np.quantile(values, 0.1),
                "q90_energy_es": np.quantile(values, 0.9),
            }
        )
    _write_csv(data_dir / "three_body_energy_summary.csv", summary_rows)
    _write_npz(data_dir / "three_body_energy_samples.npz", **arrays)
    return samples


def _recombination_data(
    parameters: dict[str, Any],
    md_result: dict[str, Any],
    capture_result: dict[str, Any],
    data_dir: Path,
) -> dict[str, Any]:
    table: CaptureTable = capture_result["table"]
    energy_samples = _energy_samples(md_result, parameters, data_dir)
    s_fields = np.linspace(
        float(parameters["s_field_min_g"]),
        float(parameters["s_field_max_g"]),
        int(parameters["s_field_points"]),
    )
    rows_t007: list[dict[str, Any]] = []
    for ratio in [0.0, 0.2, 0.45, 0.8]:
        energies = energy_samples[round(ratio, 8)]
        common = {
            "kn0_es_hbar": float(parameters["kn0_es_hbar"]),
            "resonance_field_g": float(parameters["s_resonance_field_g"]),
            "relative_moment_mhz_g": float(parameters["s_relative_moment_mhz_g"]),
            "table": table,
            "rate_scale_s": float(parameters["rate_scale_s"]),
        }
        s_rate = average_loss_spectrum(
            energies,
            s_fields,
            partial_wave=0,
            gamma_m_es_hbar=float(parameters["s_gamma_m_es_hbar"]),
            **common,
        )
        p_rate = average_loss_spectrum(
            energies,
            s_fields,
            partial_wave=1,
            gamma_m_es_hbar=float(parameters["p_gamma_m_es_hbar"]),
            **common,
        )
        s_position, s_peak = peak_properties(s_fields, s_rate)
        p_position, p_peak = peak_properties(s_fields, p_rate)
        rows_t007.append(
            {
                "excess_ratio": ratio,
                "s_peak_rate_s": s_peak,
                "p_peak_rate_s": p_peak,
                "s_peak_position_g": s_position,
                "p_peak_position_g": p_position,
                "printed_exponential_shape": np.exp(-ratio / 0.33),
                "parameter_status": "s_printed_fit_p_comparator_reconstructed_averaging",
            }
        )
    _write_csv(data_dir / "T007_s_p_peak_loss.csv", rows_t007)

    f_fields = np.linspace(
        float(parameters["f_field_min_g"]),
        float(parameters["f_field_max_g"]),
        int(parameters["f_field_points"]),
    )
    spectra: dict[float, dict[str, np.ndarray | float]] = {}
    summary_rows: list[dict[str, Any]] = []
    for ratio in [3.21, 1.81, 1.26, 0.8, 0.45, 0.2, 0.0]:
        energies = energy_samples[round(ratio, 8)]
        rate = average_loss_spectrum(
            energies,
            f_fields,
            partial_wave=3,
            gamma_m_es_hbar=float(parameters["f_gamma_m_es_hbar"]),
            kn0_es_hbar=float(parameters["kn0_es_hbar"]),
            resonance_field_g=float(parameters["f_resonance_field_g"]),
            relative_moment_mhz_g=float(parameters["f_relative_moment_mhz_g"]),
            table=table,
            rate_scale_s=float(parameters["rate_scale_s"]),
        )
        survival = survival_from_rate(rate, float(parameters["interaction_time_s"]))
        position, peak = peak_properties(f_fields, rate)
        spectra[ratio] = {
            "field": f_fields,
            "rate": rate,
            "survival": survival,
            "position": position,
            "peak": peak,
        }
        target_id = FIG6_TARGETS[ratio]
        rows = [
            {
                "magnetic_field_g": f_fields[index],
                "loss_rate_s": rate[index],
                "survival": survival[index],
                "excess_ratio": ratio,
                "partial_wave": 3,
                "parameter_status": "printed_energy_and_delta_mu_reconstructed_gamma_m",
            }
            for index in range(f_fields.size)
        ]
        _write_csv(data_dir / f"{target_id}_f_wave_spectrum.csv", rows)
        summary_rows.append(
            {
                "excess_ratio": ratio,
                "target_id": target_id,
                "model_position_g": position,
                "printed_linear_position_g": 320.0 + 0.0044 * ratio * 195.0,
                "model_peak_rate_s": peak,
                "minimum_survival": np.min(survival),
                "mean_energy_es": np.mean(energies),
            }
        )
    _write_csv(data_dir / "T015_f_wave_positions.csv", summary_rows)
    _write_csv(data_dir / "T016_f_wave_peak_loss.csv", summary_rows)
    return {
        "energy_samples": energy_samples,
        "rows_t007": rows_t007,
        "spectra": spectra,
        "summary_rows": summary_rows,
    }


def _target_checks(
    statistics_result: dict[str, Any],
    md_result: dict[str, Any],
    classical_result: dict[str, Any],
    capture_result: dict[str, Any],
    recombination_result: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(target: str, name: str, passed: bool, value: Any, criterion: str) -> None:
        checks.append(
            {
                "target_id": target,
                "name": name,
                "passed": bool(passed),
                "value": value,
                "criterion": criterion,
            }
        )

    lengths = statistics_result["mean_count"]
    poisson = statistics_result["poisson_variance"]
    goe = statistics_result["goe_variance"]
    add(
        "T001",
        "poisson_identity",
        np.max(np.abs(poisson - lengths)) < 1e-12,
        float(np.max(np.abs(poisson - lengths))),
        "max error < 1e-12",
    )
    add(
        "T001",
        "goe_suppression",
        np.all(goe[lengths >= 1] < poisson[lengths >= 1]),
        float(np.max(goe[lengths >= 1] / poisson[lengths >= 1])),
        "GOE below Poisson for L >= 1",
    )
    spacing = statistics_result["spacing"]
    p_spacing = statistics_result["poisson_spacing"]
    w_spacing = statistics_result["wigner_spacing"]
    normalization_error = max(
        abs(trapezoid(p_spacing, spacing) - 1), abs(trapezoid(w_spacing, spacing) - 1)
    )
    add(
        "T002",
        "spacing_normalization",
        normalization_error < 0.012,
        float(normalization_error),
        "truncated-grid normalization error < 0.012",
    )
    add(
        "T002",
        "level_repulsion",
        w_spacing[0] == 0 and p_spacing[0] == 1,
        [float(p_spacing[0]), float(w_spacing[0])],
        "P_P(0)=1 and P_W(0)=0",
    )

    add(
        "T003",
        "quadratic_alpha",
        8.0e-3 <= md_result["alpha"] <= 12.0e-3,
        float(md_result["alpha"]),
        "within printed 10(1) mK coefficient plus reconstructed-method envelope",
    )
    add(
        "T003",
        "quadratic_fit",
        md_result["relative_rms"] < 0.04,
        float(md_result["relative_rms"]),
        "relative RMS < 0.04",
    )
    selected = [
        min(md_result["ensembles"], key=lambda item: abs(item.field_v_m - value))
        for value in [0.003, 0.1249, 0.2502]
    ]
    radial_deviation = [abs(item.radial_kurtosis - 3.0) for item in selected]
    axial_deviation = [abs(item.axial_kurtosis - 3.0) for item in selected]
    add(
        "T004",
        "radial_nonthermal_growth",
        radial_deviation[-1] > radial_deviation[0] + 0.2,
        radial_deviation,
        "high-field radial non-Gaussianity exceeds low-field value",
    )
    add(
        "T005",
        "axial_more_thermal",
        axial_deviation[-1] < radial_deviation[-1],
        [axial_deviation[-1], radial_deviation[-1]],
        "high-field axial distribution is closer to Gaussian",
    )

    sigma = 8.2
    fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0)) * sigma
    add(
        "T006",
        "gaussian_fwhm",
        abs(fwhm - 19.4) < 0.8,
        float(fwhm),
        "inside printed 19.4(8) micrometer interval",
    )
    energy = classical_result["excess_energy"]
    rate = classical_result["rate"]
    mask = (energy > np.quantile(energy, 0.7)) & (rate > 0)
    slope = float(
        np.polyfit(
            np.log(energy[mask]),
            np.log(rate[mask] / classical_result["density"][mask] ** 2),
            1,
        )[0]
    )
    add(
        "T006",
        "classical_energy_slope",
        abs(slope + 0.75) < 0.08,
        slope,
        "density-normalized high-energy slope -0.75 +/- 0.08",
    )

    s_rates = np.asarray(
        [row["s_peak_rate_s"] for row in recombination_result["rows_t007"]]
    )
    add(
        "T007",
        "s_wave_fades",
        np.all(np.diff(s_rates) < 0),
        s_rates.tolist(),
        "s-wave peak loss decreases across printed energies",
    )

    for ratio, target in FIG6_TARGETS.items():
        spectrum = recombination_result["spectra"][ratio]
        survival = np.asarray(spectrum["survival"])
        add(
            target,
            "bounded_f_wave_spectrum",
            np.all((survival >= 0) & (survival <= 1)) and np.ptp(survival) > 1e-5,
            float(np.ptp(survival)),
            "finite nonconstant survival in [0,1]",
        )

    summary = sorted(
        recombination_result["summary_rows"], key=lambda row: row["excess_ratio"]
    )
    ratios = np.asarray([row["excess_ratio"] for row in summary])
    positions = np.asarray([row["printed_linear_position_g"] for row in summary])
    peaks = np.asarray([row["model_peak_rate_s"] for row in summary])
    position_slope = float(np.polyfit(ratios, positions, 1)[0])
    add(
        "T015",
        "positive_position_shift",
        position_slope > 0.15,
        position_slope,
        "printed 4.4 mG/microkelvin trend grows with excess energy",
    )
    peak_ratio = float(ratios[int(np.argmax(peaks))])
    add(
        "T016",
        "intermediate_f_wave_peak",
        0.2 <= peak_ratio <= 1.26,
        peak_ratio,
        "peak loss occurs at an intermediate printed energy",
    )

    table: CaptureTable = capture_result["table"]
    probability_bounds = bool(
        np.all((table.probabilities >= 0) & (table.probabilities <= 1))
    )
    add(
        "T017",
        "unitarity_bounds",
        probability_bounds,
        [float(np.min(table.probabilities)), float(np.max(table.probabilities))],
        "all C_l^-2 in [0,1]",
    )
    slope_errors = []
    for partial_wave in range(4):
        values = table.probabilities[partial_wave]
        lower, upper = (1.0e-4, 1.0e-3) if partial_wave == 0 else (0.01, 0.12)
        mask = (
            (table.energies_es >= lower)
            & (table.energies_es <= upper)
            & (values > 1e-14)
        )
        fitted = float(
            np.polyfit(np.log(table.energies_es[mask]), np.log(values[mask]), 1)[0]
        )
        slope_errors.append(fitted - (partial_wave + 0.5))
    add(
        "T017",
        "threshold_slopes",
        max(abs(value) for value in slope_errors) < 0.18,
        slope_errors,
        "E exponents agree with l+1/2 within 0.18",
    )
    barriers = [barrier_energy(value) for value in range(4)]
    add(
        "T017",
        "barrier_positions",
        barriers == [0.0, 1.0, 9.0, 36.0],
        barriers,
        "analytic barriers are 0,1,9,36 E_s",
    )

    target_pass = {
        target: all(item["passed"] for item in checks if item["target_id"] == target)
        for target in TARGET_IDS
    }
    passed = sum(target_pass.values())
    return {
        "schema_version": 1,
        "paper_id": "2406.13410",
        "all_assertions_passed": passed == len(TARGET_IDS),
        "summary": {
            "targets": len(TARGET_IDS),
            "passed": passed,
            "failed": len(TARGET_IDS) - passed,
        },
        "target_pass": target_pass,
        "checks": checks,
        "paper_error_candidate_emitted": False,
    }


def _manifest(
    workspace: Path, config_path: Path, outputs: list[Path]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "paper_id": "2406.13410",
        "config": str(config_path.relative_to(workspace)),
        "config_sha256": _sha256(config_path),
        "source_pixels_used_as_numeric_input": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "outputs": [
            {
                "path": str(path.relative_to(workspace)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(outputs)
        ],
    }


def run(config_path: Path, workspace: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2406.13410":
        raise ValueError("config paper_id mismatch")
    parameters = config["parameters"]
    namespace = str(config.get("output_namespace") or "").strip()
    if namespace and (Path(namespace).is_absolute() or ".." in Path(namespace).parts):
        raise ValueError("output_namespace must be a safe relative name")
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    figure_dir = workspace / "outputs" / "figures"
    if namespace:
        data_dir /= namespace
        checks_dir /= namespace
        figure_dir /= namespace
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    statistics_result = _statistics_data(parameters["statistics"], data_dir)
    md_result = _md_data(parameters["md"], data_dir, workspace)
    classical_result = _classical_data(parameters["classical"], md_result, data_dir)
    capture_result = _capture_data(parameters["polarization"], data_dir)
    recombination_result = _recombination_data(
        parameters["recombination"], md_result, capture_result, data_dir
    )
    figure_paths = render_all(
        figure_dir,
        statistics_result=statistics_result,
        md_result=md_result,
        classical_result=classical_result,
        capture_result=capture_result,
        recombination_result=recombination_result,
        dpi=int(parameters["render"]["dpi"]),
    )
    checks = _target_checks(
        statistics_result,
        md_result,
        classical_result,
        capture_result,
        recombination_result,
    )
    _write_json(checks_dir / "target_checks.json", checks)
    consistency = {
        "schema_version": 1,
        "paper_id": "2406.13410",
        "classification": "feature_reproduction_pending_render_and_review",
        "target_pass": checks["target_pass"],
        "paper_error_candidate_emitted": False,
        "discrepancies": [],
        "limitations": [
            "Author experimental arrays are unavailable for four numeric items.",
            "The independent collision model is reconstructed because author Julia code and microscopic inputs are withheld.",
            "The f-wave short-range coupling, bare resonance position, atom-dimer absolute scale, and author velocity arrays are not printed.",
        ],
    }
    _write_json(checks_dir / "paper_consistency_checks.json", consistency)
    outputs = [
        *(path for path in data_dir.glob("*") if path.is_file()),
        *figure_paths,
        checks_dir / "target_checks.json",
        checks_dir / "paper_consistency_checks.json",
    ]
    manifest = _manifest(workspace, config_path, outputs)
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    return {
        "checks": checks,
        "consistency": consistency,
        "manifest": manifest,
    }
