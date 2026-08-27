from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
import time

import numpy as np
import scipy.stats

from lyapunov_band import (
    LongRangeModel,
    classify_state,
    clean_beta_exponents,
    density_from_potential,
    density_overlap,
    direct_twist_winding,
    essential_lyapunov,
    finite_potential,
    finite_spectrum,
    lyapunov_exponents,
    lyapunov_potentials,
    normalized_positive_density,
    sample_onsite,
    site_transfer_matrices,
    smoothed_spectral_histogram,
    winding_from_lyapunov,
    write_csv,
    write_json,
)


def run_feature_case(workspace: Path, config_path: Path | None = None) -> dict:
    workspace = workspace.resolve()
    config_path = config_path or workspace / "config" / "feature_run.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model = LongRangeModel(**{key: value for key, value in config["model"].items() if key != "M"})
    seed = int(config["seed"])
    started = time.perf_counter()

    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    formula_checks = run_formula_sanity(model, seed)
    write_json(checks_dir / "numerical_formula_sanity.json", formula_checks)

    fig34_result = run_fig3_fig4(workspace, model, config["fig3_fig4"], seed + 100)
    fig5_result = run_fig5(workspace, model, config["fig5"], seed + 500)

    runtime = time.perf_counter() - started
    summary = {
        "status": "physically_consistent"
        if formula_checks["status"] == "passed"
        and fig34_result["fig3"]["status"] == "physically_consistent"
        and fig34_result["fig4"]["status"] == "physically_consistent"
        and fig5_result["status"] == "physically_consistent"
        else "partial",
        "artifact_stage": config["artifact_stage"],
        "parameter_match": config["parameter_match"],
        "model": asdict(model),
        "seed": seed,
        "runtime_seconds": runtime,
        "formula_sanity": formula_checks,
        "fig3": fig34_result["fig3"],
        "fig4": fig34_result["fig4"],
        "fig5": fig5_result,
    }
    write_json(checks_dir / "reproduction_feature_checks.json", summary)
    write_json(
        checks_dir / "performance_profile.json",
        {
            "status": "passed",
            "run": "feature_run",
            "runtime_seconds": runtime,
            "config_path": str(config_path.relative_to(workspace)),
            "parameter_match": config["parameter_match"],
            "artifact_stage": config["artifact_stage"],
        },
    )
    return summary


def run_formula_sanity(model: LongRangeModel, seed: int) -> dict:
    clean_energies = np.asarray([-0.6 + 0.0j, -1.05 + 0.32j, 2.5 + 0.0j])
    qr = lyapunov_exponents(clean_energies, np.zeros(6000), model)
    analytic = np.vstack([clean_beta_exponents(energy, model) for energy in clean_energies])
    clean_error = float(np.max(np.abs(qr - analytic)))

    rng = np.random.default_rng(seed)
    values = rng.normal(size=4) + 1j * rng.normal(size=4)
    energy = -0.73 + 0.21j
    onsite = 0.17
    propagated = site_transfer_matrices(energy, onsite, model) @ values
    row_residual = (
        model.t_2 * propagated[0]
        + model.t_1 * values[0]
        + (onsite - energy) * values[1]
        + model.t_minus_1 * values[2]
        + model.t_minus_2 * values[3]
    )
    transfer_error = float(abs(row_residual))
    flags = {
        "clean_beta_limit": clean_error < 2e-3,
        "transfer_recurrence": transfer_error < 1e-12,
    }
    return {
        "status": "passed" if all(flags.values()) else "failed",
        "gate_flags": flags,
        "clean_beta_max_abs_error": clean_error,
        "transfer_recurrence_abs_error": transfer_error,
        "clean_transfer_length": 6000,
    }


def run_fig3_fig4(
    workspace: Path,
    model: LongRangeModel,
    config: dict,
    seed: int,
) -> dict:
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    rng = np.random.default_rng(seed)
    length = int(config["diagonalization_length"])
    realization_count = int(config["disorder_realizations"])
    disorder_strength = float(config["W"])

    obc_spectra: list[np.ndarray] = []
    pbc_spectra: list[np.ndarray] = []
    obc_rows: list[dict] = []
    pbc_rows: list[dict] = []
    for realization in range(realization_count):
        onsite = sample_onsite(length, disorder_strength, rng)
        obc = finite_spectrum(onsite, model, boundary="obc")
        pbc = finite_spectrum(onsite, model, boundary="pbc")
        obc_spectra.append(obc)
        pbc_spectra.append(pbc)
        obc_rows.extend(_spectrum_rows("T001", "OBC", realization, disorder_strength, obc))
        pbc_rows.extend(_spectrum_rows("T002", "PBC", realization, disorder_strength, pbc))
    obc_array = np.vstack(obc_spectra)
    pbc_array = np.vstack(pbc_spectra)
    write_csv(data_dir / "fig3_obc_spectrum.csv", obc_rows)
    write_csv(data_dir / "fig4_pbc_spectrum.csv", pbc_rows)

    grid_config = config["energy_grid"]
    real_axis = np.linspace(grid_config["real_min"], grid_config["real_max"], grid_config["real_points"])
    imag_axis = np.linspace(grid_config["imag_min"], grid_config["imag_max"], grid_config["imag_points"])
    real_grid, imag_grid = np.meshgrid(real_axis, imag_axis)
    energies = real_grid + 1j * imag_grid
    transfer_rng = np.random.default_rng(seed + 1)
    transfer_onsite = sample_onsite(int(config["transfer_length"]), disorder_strength, transfer_rng)
    exponents = lyapunov_exponents(energies, transfer_onsite, model)
    obc_potential, pbc_potential = lyapunov_potentials(exponents, model)
    sigma = float(config["density_smoothing_sigma_cells"])
    obc_density = density_from_potential(obc_potential, real_axis, imag_axis, smoothing_sigma=sigma)
    pbc_density = density_from_potential(pbc_potential, real_axis, imag_axis, smoothing_sigma=sigma)
    obc_hist = smoothed_spectral_histogram(obc_array, real_axis, imag_axis, smoothing_sigma=sigma)
    pbc_hist = smoothed_spectral_histogram(pbc_array, real_axis, imag_axis, smoothing_sigma=sigma)
    obc_finite_potential = finite_potential(obc_array, energies)
    pbc_finite_potential = finite_potential(pbc_array, energies)
    gamma_ess = essential_lyapunov(exponents)
    state_code = classify_state(exponents, tolerance=2.0 / int(config["transfer_length"]))
    winding = winding_from_lyapunov(exponents, tolerance=2.0 / int(config["transfer_length"]))
    obc_density_norm = normalized_positive_density(obc_density)
    pbc_density_norm = normalized_positive_density(pbc_density)

    fig3_rows: list[dict] = []
    fig4_rows: list[dict] = []
    for index in np.ndindex(energies.shape):
        base = {
            "real_energy": real_grid[index],
            "imag_energy": imag_grid[index],
            "gamma_1": exponents[index + (0,)],
            "gamma_2": exponents[index + (1,)],
            "gamma_3": exponents[index + (2,)],
            "gamma_4": exponents[index + (3,)],
            "gamma_ess": gamma_ess[index],
            "state_code": int(state_code[index]),
            "winding": int(winding[index]),
            "W": disorder_strength,
            "transfer_length": int(config["transfer_length"]),
        }
        fig3_rows.append(
            {
                **base,
                "lyapunov_potential": obc_potential[index],
                "finite_ed_potential": obc_finite_potential[index],
                "lyapunov_density_raw": obc_density[index],
                "lyapunov_density_positive_norm": obc_density_norm[index],
                "ed_histogram_norm": obc_hist[index],
            }
        )
        fig4_rows.append(
            {
                **base,
                "lyapunov_potential": pbc_potential[index],
                "finite_ed_potential": pbc_finite_potential[index],
                "lyapunov_density_raw": pbc_density[index],
                "lyapunov_density_positive_norm": pbc_density_norm[index],
                "ed_histogram_norm": pbc_hist[index],
            }
        )
    write_csv(data_dir / "fig3_lyapunov_grid.csv", fig3_rows)
    write_csv(data_dir / "fig4_lyapunov_grid.csv", fig4_rows)

    scaling_result = run_potential_scaling(workspace, model, config, seed + 2)
    winding_result = run_winding_checks(workspace, model, disorder_strength, seed + 3)

    fig3_metrics = {
        "potential_mae": float(np.mean(np.abs(obc_finite_potential - obc_potential))),
        "density_overlap": density_overlap(obc_hist, obc_density),
        "scaling": scaling_result,
    }
    fig3_flags = {
        "potential_mae_below_0_15": fig3_metrics["potential_mae"] < 0.15,
        "density_overlap_above_0_20": fig3_metrics["density_overlap"] > 0.20,
        "potential_deviation_decreases": scaling_result["all_end_below_start"],
        "paper_scaling_exponents_within_0_20": scaling_result["all_exponent_gaps_below_0_20"],
    }
    fig3_check = {
        "status": "physically_consistent" if all(fig3_flags.values()) else "partial",
        "target_id": "T001",
        "paper_item": "Fig. 3",
        "artifact_stage": "exploratory",
        "parameter_match": "reduced_scale",
        "generated_data_provenance": "independent_numerics",
        "gate_flags": fig3_flags,
        "metrics": fig3_metrics,
        "generated_parameters": {
            "L": length,
            "disorder_realizations": realization_count,
            "transfer_length": int(config["transfer_length"]),
            "grid_shape": list(energies.shape),
        },
    }
    write_json(checks_dir / "fig3_features.json", fig3_check)

    fig4_metrics = {
        "potential_mae": float(np.mean(np.abs(pbc_finite_potential - pbc_potential))),
        "density_overlap": density_overlap(pbc_hist, pbc_density),
        "winding": winding_result,
    }
    fig4_flags = {
        "potential_mae_below_0_15": fig4_metrics["potential_mae"] < 0.15,
        "density_overlap_above_0_20": fig4_metrics["density_overlap"] > 0.20,
        "direct_winding_matches_lyapunov": winding_result["all_match"],
    }
    fig4_check = {
        "status": "physically_consistent" if all(fig4_flags.values()) else "partial",
        "target_id": "T002",
        "paper_item": "Fig. 4",
        "artifact_stage": "exploratory",
        "parameter_match": "reduced_scale",
        "generated_data_provenance": "independent_numerics",
        "gate_flags": fig4_flags,
        "metrics": fig4_metrics,
        "generated_parameters": {
            "L": length,
            "disorder_realizations": realization_count,
            "transfer_length": int(config["transfer_length"]),
            "grid_shape": list(energies.shape),
        },
    }
    write_json(checks_dir / "fig4_features.json", fig4_check)
    return {"fig3": fig3_check, "fig4": fig4_check}


def run_potential_scaling(workspace: Path, model: LongRangeModel, config: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    lengths = [int(value) for value in config["scaling_lengths"]]
    realization_count = int(config["scaling_realizations"])
    disorder_strength = float(config["W"])
    energy_specs = config["scaling_energies"]
    energies = np.asarray([complex(item["real"], item["imag"]) for item in energy_specs])
    theory_onsite = sample_onsite(300000, disorder_strength, np.random.default_rng(seed + 1))
    theory_exponents = lyapunov_exponents(energies, theory_onsite, model)
    theory_potential, _ = lyapunov_potentials(theory_exponents, model)

    maximum_length = max(lengths)
    disorder_samples = [sample_onsite(maximum_length, disorder_strength, rng) for _ in range(realization_count)]
    rows: list[dict] = []
    deviations: dict[str, list[float]] = {item["label"]: [] for item in energy_specs}
    for length in lengths:
        spectra = np.vstack([finite_spectrum(onsite[:length], model, boundary="obc") for onsite in disorder_samples])
        finite_values = finite_potential(spectra, energies)
        for index, item in enumerate(energy_specs):
            deviation = float(abs(finite_values[index] - theory_potential[index]))
            deviations[item["label"]].append(deviation)
            rows.append(
                {
                    "label": item["label"],
                    "real_energy": item["real"],
                    "imag_energy": item["imag"],
                    "L": length,
                    "realizations": realization_count,
                    "finite_potential": finite_values[index],
                    "lyapunov_potential": theory_potential[index],
                    "delta_phi": deviation,
                    "paper_exponent_L": item["paper_exponent"],
                }
            )
    write_csv(workspace / "outputs" / "data" / "fig3_potential_scaling.csv", rows)

    fits: dict[str, dict] = {}
    all_end_below_start = True
    all_exponent_gaps_below_0_20 = True
    for item in energy_specs:
        label = item["label"]
        values = np.asarray(deviations[label])
        slope, intercept = np.polyfit(np.log(np.asarray(lengths, dtype=float)), np.log(values), 1)
        all_end_below_start &= bool(values[-1] < values[0])
        all_exponent_gaps_below_0_20 &= bool(abs(slope - item["paper_exponent"]) < 0.20)
        fits[label] = {
            "fit_exponent_L": float(slope),
            "fit_intercept": float(intercept),
            "paper_exponent_L": float(item["paper_exponent"]),
            "absolute_exponent_gap": float(abs(slope - item["paper_exponent"])),
            "delta_phi_start": float(values[0]),
            "delta_phi_end": float(values[-1]),
        }
    return {
        "fits": fits,
        "all_end_below_start": bool(all_end_below_start),
        "all_exponent_gaps_below_0_20": bool(all_exponent_gaps_below_0_20),
        "lengths": lengths,
        "realizations": realization_count,
        "theory_transfer_length": 300000,
    }


def run_winding_checks(
    workspace: Path,
    model: LongRangeModel,
    disorder_strength: float,
    seed: int,
) -> dict:
    points = [
        ("left_hole", -1.65 + 0.60j, -1),
        ("center_hole", -0.60 + 0.00j, 1),
        ("right_hole", 3.10 + 0.00j, -1),
        ("alm_region", -1.90 + 0.35j, 0),
    ]
    rng = np.random.default_rng(seed)
    long_onsite = sample_onsite(12000, disorder_strength, rng)
    finite_onsite = long_onsite[:160]
    energies = np.asarray([item[1] for item in points])
    exponents = lyapunov_exponents(energies, long_onsite, model)
    le_winding = winding_from_lyapunov(exponents)
    rows: list[dict] = []
    matches: list[bool] = []
    paper_matches: list[bool] = []
    for index, (label, energy, paper_value) in enumerate(points):
        direct = direct_twist_winding(energy, finite_onsite, model, theta_points=129)
        predicted = int(le_winding[index])
        matches.append(direct == predicted)
        paper_matches.append(predicted == paper_value)
        rows.append(
            {
                "label": label,
                "real_energy": energy.real,
                "imag_energy": energy.imag,
                "gamma_1": exponents[index, 0],
                "gamma_2": exponents[index, 1],
                "gamma_3": exponents[index, 2],
                "gamma_4": exponents[index, 3],
                "lyapunov_winding": predicted,
                "direct_twist_winding": direct,
                "paper_region_winding": paper_value,
                "methods_match": direct == predicted,
            }
        )
    write_csv(workspace / "outputs" / "data" / "fig4_winding_checks.csv", rows)
    return {
        "all_match": bool(all(matches)),
        "paper_region_labels_match": bool(all(paper_matches)),
        "matches": int(sum(matches)),
        "points": len(points),
        "transfer_length": len(long_onsite),
        "twisted_chain_length": len(finite_onsite),
        "theta_points": 129,
    }


def run_fig5(workspace: Path, model: LongRangeModel, config: dict, seed: int) -> dict:
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    grid_config = config["energy_grid"]
    real_axis = np.linspace(grid_config["real_min"], grid_config["real_max"], grid_config["real_points"])
    imag_axis = np.linspace(grid_config["imag_min"], grid_config["imag_max"], grid_config["imag_points"])
    real_grid, imag_grid = np.meshgrid(real_axis, imag_axis)
    energies = real_grid + 1j * imag_grid
    transfer_length = int(config["transfer_length"])

    contour_rows: list[dict] = []
    area_rows: list[dict] = []
    for w_index, disorder_strength in enumerate(config["contour_W"]):
        rng = np.random.default_rng(seed + w_index)
        onsite = sample_onsite(transfer_length, float(disorder_strength), rng)
        exponents = lyapunov_exponents(energies, onsite, model)
        gamma_ess = essential_lyapunov(exponents)
        state_code = classify_state(exponents, tolerance=2.0 / transfer_length)
        skin_area_proxy = float(np.mean(state_code == -1))
        area_rows.append({"W": disorder_strength, "skin_area_fraction_of_grid": skin_area_proxy})
        for index in np.ndindex(energies.shape):
            contour_rows.append(
                {
                    "W": disorder_strength,
                    "real_energy": real_grid[index],
                    "imag_energy": imag_grid[index],
                    "gamma_2": exponents[index + (1,)],
                    "gamma_3": exponents[index + (2,)],
                    "gamma_ess": gamma_ess[index],
                    "state_code": int(state_code[index]),
                }
            )
    write_csv(data_dir / "fig5_mobility_grid.csv", contour_rows)
    write_csv(data_dir / "fig5_skin_area_proxy.csv", area_rows)

    alpha_rows: list[dict] = []
    alpha_values: list[float] = []
    length = int(config["diagonalization_length"])
    realization_count = int(config["disorder_realizations"])
    for w_index, disorder_strength in enumerate(config["alpha_W"]):
        rng = np.random.default_rng(seed + 100 + w_index)
        spectra = np.concatenate(
            [
                finite_spectrum(sample_onsite(length, float(disorder_strength), rng), model, boundary="obc")
                for _ in range(realization_count)
            ]
        )
        le_onsite = sample_onsite(transfer_length, float(disorder_strength), np.random.default_rng(seed + 200 + w_index))
        exponents = lyapunov_exponents(spectra, le_onsite, model)
        state_code = classify_state(exponents, tolerance=2.0 / transfer_length)
        alpha = float(np.mean(state_code == 1))
        standard_error = float(np.sqrt(max(alpha * (1.0 - alpha), 0.0) / spectra.size))
        alpha_values.append(alpha)
        alpha_rows.append(
            {
                "W": disorder_strength,
                "alpha": alpha,
                "binomial_standard_error": standard_error,
                "eigenvalues": spectra.size,
                "L": length,
                "realizations": realization_count,
                "transfer_length": transfer_length,
            }
        )
    write_csv(data_dir / "fig5_alpha.csv", alpha_rows)

    w_values = np.asarray(config["alpha_W"], dtype=float)
    alphas = np.asarray(alpha_values)
    threshold_candidates = w_values[alphas >= 0.98]
    estimated_wc = float(threshold_candidates[0]) if threshold_candidates.size else None
    spearman = scipy.stats.spearmanr(w_values, alphas).statistic
    areas = np.asarray([row["skin_area_fraction_of_grid"] for row in area_rows])
    contour_spearman = scipy.stats.spearmanr(np.asarray(config["contour_W"]), areas).statistic
    flags = {
        "alpha_bounded": bool(np.all((alphas >= 0.0) & (alphas <= 1.0))),
        "alpha_increases_with_W": bool(spearman > 0.90),
        "high_disorder_is_mostly_alm": bool(alphas[-1] >= 0.95),
        "transition_near_paper_value": estimated_wc is not None and abs(estimated_wc - 2.1) <= 0.5,
        "mobility_skin_area_shrinks": bool(contour_spearman < -0.80),
    }
    result = {
        "status": "physically_consistent" if all(flags.values()) else "partial",
        "target_id": "T003",
        "paper_item": "Fig. 5",
        "artifact_stage": "exploratory",
        "parameter_match": "reduced_scale",
        "generated_data_provenance": "independent_numerics",
        "gate_flags": flags,
        "metrics": {
            "estimated_Wc_alpha_ge_0_98": estimated_wc,
            "paper_Wc": 2.1,
            "alpha_spearman": float(spearman),
            "contour_area_spearman": float(contour_spearman),
            "alpha_at_W_3": float(alphas[-1]),
        },
        "generated_parameters": {
            "L": length,
            "realizations": realization_count,
            "transfer_length": transfer_length,
            "grid_shape": list(energies.shape),
        },
    }
    write_json(checks_dir / "fig5_features.json", result)
    return result


def _spectrum_rows(
    target_id: str,
    boundary: str,
    realization: int,
    disorder_strength: float,
    eigenvalues: np.ndarray,
) -> list[dict]:
    return [
        {
            "target_id": target_id,
            "boundary": boundary,
            "realization": realization,
            "level": level,
            "W": disorder_strength,
            "real_energy": value.real,
            "imag_energy": value.imag,
        }
        for level, value in enumerate(eigenvalues)
    ]
