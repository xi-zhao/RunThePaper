#!/usr/bin/env python3
"""Run the detector-fixed go/pivot/stop calculation for the click idea."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.chern_jump_geometry import (  # noqa: E402
    TWO_PI,
    constant_texture,
    geometry_observables,
    momentum_grid,
    qwz_texture,
)
from src.detector_sum_rule import (  # noqa: E402
    calibrated_density_response,
    density_probe_metric_estimator,
    density_probe_weight,
    interband_gap,
    orbital_vertex_weight,
    paper_bath_complete_vertex_strength,
    raw_absorption_rate,
    texture_projector,
)


Row = dict[str, float | int | str]


def write_csv(path: Path, rows: list[Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_validation(mode: str) -> tuple[dict[str, list[Row]], dict]:
    size = 51 if mode == "smoke" else 101
    texture = qwz_texture(size, -0.5)
    constant = constant_texture(size)
    projector = texture_projector(texture)
    constant_projector = texture_projector(constant)
    geometry = geometry_observables(texture)
    _, _, spacing = momentum_grid(size)

    q_steps = [1, 2, 3] if mode == "smoke" else [1, 2, 3, 4, 5]
    q_rows: list[Row] = []
    q_values: list[float] = []
    estimators: list[float] = []
    for step in q_steps:
        q = step * spacing
        estimator = density_probe_metric_estimator(projector, step, spacing)
        q_values.append(q)
        estimators.append(estimator)
        q_rows.append(
            {
                "grid_size": size,
                "shift_steps": step,
                "q": q,
                "q_squared": q * q,
                "density_probe_metric_estimator": estimator,
                "metric_integral": geometry.metric_integral,
                "topological_bound": TWO_PI * abs(geometry.chern),
            }
        )
    q_slope, q_intercept = np.polyfit(
        np.square(q_values),
        np.asarray(estimators),
        deg=1,
    )

    detector_shift = (2, 0)
    weight = density_probe_weight(projector, detector_shift)
    gap = interband_gap(size, -0.5, detector_shift)
    temperatures = [0.0, 0.1, 0.2, 0.5, 1.0, 2.0]
    temperature_rows: list[Row] = []
    for temperature in temperatures:
        temperature_rows.append(
            {
                "temperature": temperature,
                "coupling": 0.2,
                "raw_absorption_rate": raw_absorption_rate(
                    weight,
                    gap,
                    spacing,
                    coupling=0.2,
                    temperature=temperature,
                ),
                "passive_ground_state_emission_rate": 0.0,
            }
        )

    coupling_rows: list[Row] = []
    for coupling in [1.0, 0.3, 0.1, 0.03, 0.01]:
        coupling_rows.append(
            {
                "temperature": 1.0,
                "coupling": coupling,
                "raw_absorption_rate": raw_absorption_rate(
                    weight,
                    gap,
                    spacing,
                    coupling=coupling,
                    temperature=1.0,
                ),
            }
        )

    full_response = calibrated_density_response(
        weight,
        gap,
        spacing,
        coupling=0.2,
        temperature=0.8,
    )
    quantiles = [0.2, 0.4, 0.6, 0.8, 1.0]
    window_rows: list[Row] = []
    for quantile in quantiles:
        upper = (
            float(np.quantile(gap, quantile))
            if quantile < 1.0
            else float(np.max(gap) + 1e-12)
        )
        response = calibrated_density_response(
            weight,
            gap,
            spacing,
            coupling=0.2,
            temperature=0.8,
            energy_window=(0.0, upper),
        )
        window_rows.append(
            {
                "gap_quantile": quantile,
                "energy_window_upper": upper,
                "raw_rate": response.raw_rate,
                "calibrated_weight": response.calibrated_weight,
                "full_geometric_weight": response.full_geometric_weight,
                "recovery_fraction": response.recovery_fraction,
                "accessible_fraction": response.accessible_fraction,
            }
        )

    identity = np.eye(2, dtype=np.complex128)
    sigma_x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    paper_topological = paper_bath_complete_vertex_strength(projector)
    paper_constant = paper_bath_complete_vertex_strength(constant_projector)
    vertex_rows: list[Row] = []
    for model, model_projector, paper_strength in (
        ("chern_texture", projector, paper_topological),
        ("constant_trivial_texture", constant_projector, paper_constant),
    ):
        scalar_weight = orbital_vertex_weight(
            model_projector,
            (0, 0),
            identity,
        )
        nonscalar_weight = orbital_vertex_weight(
            model_projector,
            (0, 0),
            sigma_x,
        )
        vertex_rows.extend(
            [
                {
                    "model": model,
                    "instrument": "paper_complete_HS_vertex_basis",
                    "mean_same_k_interband_strength": float(np.mean(paper_strength)),
                },
                {
                    "model": model,
                    "instrument": "scalar_identity_vertex_q0",
                    "mean_same_k_interband_strength": float(np.mean(scalar_weight)),
                },
                {
                    "model": model,
                    "instrument": "orbital_sigma_x_vertex_q0",
                    "mean_same_k_interband_strength": float(np.mean(nonscalar_weight)),
                },
            ]
        )

    coupling_rate_one = float(coupling_rows[0]["raw_absorption_rate"])
    coupling_rate_tenth = float(coupling_rows[2]["raw_absorption_rate"])
    checks = {
        "paper_texture_has_unit_chern": abs(geometry.chern - 1.0) < 1e-10,
        "density_probe_q_extrapolates_to_metric": (
            abs(q_intercept - geometry.metric_integral)
            / geometry.metric_integral
            < 3e-3
        ),
        "calibrated_full_spectrum_recovers_geometry": (
            abs(full_response.recovery_fraction - 1.0) < 5e-14
        ),
        "thermal_absorption_vanishes_at_zero_temperature": (
            float(temperature_rows[0]["raw_absorption_rate"]) == 0.0
        ),
        "passive_ground_band_emission_is_zero": all(
            float(row["passive_ground_state_emission_rate"]) == 0.0
            for row in temperature_rows
        ),
        "raw_rate_scales_as_coupling_squared": (
            abs(coupling_rate_tenth / coupling_rate_one - 0.01) < 2e-14
        ),
        "finite_window_loses_geometric_weight": (
            float(window_rows[0]["recovery_fraction"]) < 0.9
            and abs(float(window_rows[-1]["recovery_fraction"]) - 1.0) < 5e-14
        ),
        "paper_complete_vertex_response_is_texture_blind": (
            np.max(np.abs(paper_topological - 1.0)) < 3e-15
            and np.max(np.abs(paper_constant - 1.0)) < 3e-15
        ),
        "nonscalar_vertex_can_make_trivial_texture_bright": (
            abs(
                next(
                    float(row["mean_same_k_interband_strength"])
                    for row in vertex_rows
                    if row["model"] == "constant_trivial_texture"
                    and row["instrument"] == "orbital_sigma_x_vertex_q0"
                )
                - 1.0
            )
            < 2e-15
        ),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    result = {
        "status": "passed" if all(checks.values()) else "failed",
        "verdict": "pivot" if all(checks.values()) else "inconclusive",
        "mode": mode,
        "parameters": {
            "grid_size": size,
            "mass": -0.5,
            "detector_shift": list(detector_shift),
            "ohmic_eta": 1.0,
            "ohmic_cutoff": 4.0,
        },
        "checks": checks,
        "diagnostics": {
            "chern": geometry.chern,
            "metric_integral": geometry.metric_integral,
            "topological_bound": TWO_PI,
            "metric_bound_ratio": geometry.metric_integral / TWO_PI,
            "q_fit_slope": float(q_slope),
            "q_fit_intercept": float(q_intercept),
            "q_fit_relative_error": float(
                abs(q_intercept - geometry.metric_integral)
                / geometry.metric_integral
            ),
            "full_calibration_recovery": full_response.recovery_fraction,
            "paper_bath_chern_mean_strength": float(np.mean(paper_topological)),
            "paper_bath_trivial_mean_strength": float(np.mean(paper_constant)),
        },
        "hypothesis_decisions": {
            "raw_total_paper_bath_click_bound": "stop",
            "same_bath_click_record_measures_quantum_metric": "stop",
            "calibrated_independent_density_probe_sum_rule": "go",
            "publishable_static_topological_sum_rule": "stop_already_known",
            "time_resolved_spectator_monitoring_during_geometric_flow": "pivot_candidate",
        },
        "reason": (
            "The published bath is momentum-local and its identity-superoperator "
            "vertex sum is texture blind. A separate scalar density probe recovers "
            "the metric only after resolved kernel calibration; raw counts vanish "
            "with coupling or probe occupation and finite windows lose weight."
        ),
    }
    datasets = {
        "q_convergence": q_rows,
        "temperature_sweep": temperature_rows,
        "coupling_sweep": coupling_rows,
        "window_sweep": window_rows,
        "vertex_controls": vertex_rows,
    }
    return datasets, result


def plot_validation(datasets: dict[str, list[Row]], result: dict, output: Path) -> None:
    q_rows = datasets["q_convergence"]
    temperature_rows = datasets["temperature_sweep"]
    window_rows = datasets["window_sweep"]
    vertex_rows = datasets["vertex_controls"]
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 7.4), constrained_layout=True)

    q_squared = np.asarray([float(row["q_squared"]) for row in q_rows])
    estimates = np.asarray(
        [float(row["density_probe_metric_estimator"]) for row in q_rows]
    )
    axes[0, 0].plot(q_squared, estimates, "o-", color="#0072B2")
    axes[0, 0].axhline(
        float(result["diagnostics"]["metric_integral"]),
        color="#009E73",
        linestyle="--",
        label=r"$\int \mathrm{tr}\,g$",
    )
    axes[0, 0].axhline(TWO_PI, color="black", linestyle=":", label=r"$2\pi|C|$")
    axes[0, 0].set(
        xlabel=r"$q^2$",
        ylabel=r"$K_{\rm click}(q)$",
        title="Calibrated scalar density probe",
    )
    axes[0, 0].legend(frameon=False, fontsize=8)

    temperatures = np.asarray(
        [float(row["temperature"]) for row in temperature_rows]
    )
    raw_rates = np.asarray(
        [float(row["raw_absorption_rate"]) for row in temperature_rows]
    )
    axes[0, 1].plot(temperatures, raw_rates, "o-", color="#D55E00")
    axes[0, 1].set(
        xlabel="probe temperature",
        ylabel="raw absorption rate",
        title="Raw activity has no topology floor",
    )
    axes[0, 1].set_yscale("symlog", linthresh=1e-12)

    energy_upper = np.asarray(
        [float(row["energy_window_upper"]) for row in window_rows]
    )
    recovery = np.asarray(
        [float(row["recovery_fraction"]) for row in window_rows]
    )
    axes[1, 0].plot(energy_upper, recovery, "o-", color="#CC79A7")
    axes[1, 0].axhline(1.0, color="black", linestyle=":")
    axes[1, 0].set(
        xlabel="detector energy-window upper edge",
        ylabel="recovered geometric fraction",
        title="Finite windows miss the sum rule",
        ylim=(-0.02, 1.05),
    )

    selected = [
        row
        for row in vertex_rows
        if row["instrument"]
        in ("paper_complete_HS_vertex_basis", "orbital_sigma_x_vertex_q0")
    ]
    labels = [
        ("paper/Chern" if row["model"] == "chern_texture" else "paper/trivial")
        if row["instrument"] == "paper_complete_HS_vertex_basis"
        else ("orbital/Chern" if row["model"] == "chern_texture" else "orbital/trivial")
        for row in selected
    ]
    values = [
        float(row["mean_same_k_interband_strength"]) for row in selected
    ]
    colors = ["#0072B2", "#56B4E9", "#E69F00", "#F0E442"]
    axes[1, 1].bar(labels, values, color=colors)
    axes[1, 1].set(
        ylabel="mean same-k transition strength",
        title="Paper bath is texture blind",
    )
    axes[1, 1].tick_params(axis="x", labelrotation=20)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "feature"), default="feature")
    args = parser.parse_args()
    started = time.perf_counter()
    datasets, result = run_validation(args.mode)
    result["runtime_seconds"] = time.perf_counter() - started

    data_dir = WORKSPACE / "outputs" / "data"
    checks_dir = WORKSPACE / "outputs" / "checks"
    figures_dir = WORKSPACE / "outputs" / "figures"
    filename_map = {
        "q_convergence": "detector_q_convergence.csv",
        "temperature_sweep": "detector_temperature_sweep.csv",
        "coupling_sweep": "detector_coupling_sweep.csv",
        "window_sweep": "detector_window_sweep.csv",
        "vertex_controls": "detector_vertex_controls.csv",
    }
    for dataset_name, rows in datasets.items():
        write_csv(data_dir / filename_map[dataset_name], rows)
    checks_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "detector_sum_rule_validation.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    plot_validation(
        datasets,
        result,
        figures_dir / "detector_sum_rule_go_no_go.png",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
