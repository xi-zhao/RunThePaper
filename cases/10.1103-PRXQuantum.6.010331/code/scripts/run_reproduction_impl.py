#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent
sys.path.insert(0, str(WORKSPACE))

from src.fidelity_response import (  # noqa: E402
    GateParameters,
    appendix_fit,
    gate_diagnostics,
    ideal_hamiltonian,
    intensity_noise_operator,
    normalized_rmse,
    scale_universal_response,
    universal_responses,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_universal_csv(
    path: Path,
    frequencies: np.ndarray,
    fits: dict[str, np.ndarray],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "normalized_frequency",
        "haar_frequency_response",
        "symmetric_haar_frequency_response",
        "haar_intensity_response",
        "symmetric_haar_intensity_response",
        "generated_data_provenance",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, frequency in enumerate(frequencies):
            writer.writerow(
                {
                    "normalized_frequency": float(frequency),
                    "haar_frequency_response": float(fits["haar_frequency"][index]),
                    "symmetric_haar_frequency_response": float(
                        fits["symmetric_haar_frequency"][index]
                    ),
                    "haar_intensity_response": float(fits["haar_intensity"][index]),
                    "symmetric_haar_intensity_response": float(
                        fits["symmetric_haar_intensity"][index]
                    ),
                    "generated_data_provenance": "analytic_reference",
                }
            )


def write_direct_diagnostic_csv(
    path: Path,
    frequencies: np.ndarray,
    curves: dict[str, np.ndarray],
    fits: dict[str, np.ndarray],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "normalized_frequency",
        "metric",
        "noise_kind",
        "reconstructed_direct_response",
        "appendix_l_reference",
        "generated_data_provenance",
        "parameter_match",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for metric in ("haar", "symmetric_haar"):
            for noise_kind in ("frequency", "intensity"):
                key = f"{metric}_{noise_kind}"
                for index, frequency in enumerate(frequencies):
                    writer.writerow(
                        {
                            "normalized_frequency": float(frequency),
                            "metric": metric,
                            "noise_kind": noise_kind,
                            "reconstructed_direct_response": float(curves[key][index]),
                            "appendix_l_reference": float(fits[key][index]),
                            "generated_data_provenance": "independent_numerics",
                            "parameter_match": "reconstructed",
                        }
                    )


def render_fig15(
    path: Path,
    frequencies: np.ndarray,
    fits: dict[str, np.ndarray],
    plot_max: float,
) -> None:
    mask = frequencies <= plot_max + 1.0e-12
    x = frequencies[mask]
    scale = (2.0 * np.pi) ** 2
    blue = "#0072BD"
    orange = "#D95319"
    figure, axes = plt.subplots(1, 2, figsize=(8.8, 3.8), constrained_layout=True)

    for metric, color, label in (
        ("haar", blue, "Haar"),
        ("symmetric_haar", orange, "Sym"),
    ):
        axes[0].plot(
            x,
            fits[f"{metric}_frequency"][mask] / scale,
            color=color,
            linewidth=2.2,
            label=label,
        )
        axes[1].plot(x, fits[f"{metric}_intensity"][mask], color=color, linewidth=2.2, label=label)

    axes[0].set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    axes[0].set_ylabel(r"Frequency response $\Omega^2 I_\nu/(2\pi)^2$")
    axes[0].set_xlim(0.0, plot_max)
    axes[0].set_ylim(bottom=0.0)
    axes[0].legend(frameon=False)
    axes[0].set_title("a", loc="left", fontweight="bold")

    axes[1].set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    axes[1].set_ylabel(r"Intensity response $I_I$")
    axes[1].set_xlim(0.0, plot_max)
    axes[1].set_ylim(bottom=0.0)
    axes[1].legend(frameon=False)
    axes[1].set_title("b", loc="left", fontweight="bold")

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(alpha=0.18, linewidth=0.6)
    figure.suptitle("Appendix-L universal response envelope", fontsize=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def render_direct_diagnostic(
    path: Path,
    frequencies: np.ndarray,
    curves: dict[str, np.ndarray],
    fits: dict[str, np.ndarray],
    plot_max: float,
) -> None:
    mask = frequencies <= plot_max + 1.0e-12
    x = frequencies[mask]
    scale = (2.0 * np.pi) ** 2
    figure, axes = plt.subplots(1, 2, figsize=(8.8, 3.8), constrained_layout=True)
    for metric, color, label in (
        ("haar", "#0072BD", "Haar"),
        ("symmetric_haar", "#D95319", "Sym"),
    ):
        axes[0].plot(
            x,
            curves[f"{metric}_frequency"][mask] / scale,
            color=color,
            linewidth=2.0,
            label=f"{label} reconstructed",
        )
        axes[0].plot(
            x,
            fits[f"{metric}_frequency"][mask] / scale,
            color=color,
            linewidth=1.3,
            linestyle="--",
            label=f"{label} Appendix L",
        )
        axes[1].plot(
            x,
            curves[f"{metric}_intensity"][mask],
            color=color,
            linewidth=2.0,
            label=f"{label} reconstructed",
        )
        axes[1].plot(
            x,
            fits[f"{metric}_intensity"][mask],
            color=color,
            linewidth=1.3,
            linestyle="--",
            label=f"{label} Appendix L",
        )
    axes[0].set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    axes[0].set_ylabel(r"Frequency response $\Omega^2 I_\nu/(2\pi)^2$")
    axes[1].set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    axes[1].set_ylabel(r"Intensity response $I_I$")
    for axis in axes:
        axis.set_xlim(0.0, plot_max)
        axis.set_ylim(bottom=0.0)
        axis.legend(frameon=False, fontsize=7)
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(alpha=0.18, linewidth=0.6)
    figure.suptitle(
        "Diagnostic: cited generic pulse is not the undisclosed Fig. 15 trajectory",
        fontsize=10,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def build_scaled_rows(
    normalized_grid: np.ndarray,
    curves: dict[str, np.ndarray],
    physical_frequencies: np.ndarray,
    rabi_frequencies: list[float],
) -> tuple[list[dict[str, float | str]], float]:
    rows: list[dict[str, float | str]] = []
    collapse_errors: list[float] = []
    for rabi in rabi_frequencies:
        scaled_frequency, scaled_intensity = scale_universal_response(
            normalized_grid,
            curves["haar_frequency"],
            curves["haar_intensity"],
            physical_frequencies,
            rabi,
        )
        x_values = physical_frequencies / rabi
        expected_frequency = np.interp(x_values, normalized_grid, curves["haar_frequency"])
        expected_intensity = np.interp(x_values, normalized_grid, curves["haar_intensity"])
        collapse_errors.append(
            float(np.max(np.abs(scaled_frequency * (2.0 * np.pi * rabi) ** 2 - expected_frequency)))
        )
        collapse_errors.append(float(np.max(np.abs(scaled_intensity - expected_intensity))))
        for index, frequency in enumerate(physical_frequencies):
            rows.append(
                {
                    "physical_frequency_mhz": float(frequency),
                    "rabi_frequency_mhz": float(rabi),
                    "normalized_frequency": float(x_values[index]),
                    "frequency_response_mhz_minus_2": float(scaled_frequency[index]),
                    "intensity_response": float(scaled_intensity[index]),
                    "generated_data_provenance": "analytic_reference",
                }
            )
    return rows, max(collapse_errors)


def write_scaled_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def render_fig6a(path: Path, rows: list[dict[str, float | str]], rabi_values: list[float]) -> None:
    blue = "#0072BD"
    orange = "#EDB120"
    figure, axes = plt.subplots(2, 1, figsize=(5.6, 6.8), sharex=True, constrained_layout=True)
    for rabi, color in zip(rabi_values, (blue, orange), strict=True):
        selected = [row for row in rows if float(row["rabi_frequency_mhz"]) == rabi]
        frequency = np.asarray([float(row["physical_frequency_mhz"]) for row in selected])
        response_frequency = np.asarray(
            [float(row["frequency_response_mhz_minus_2"]) for row in selected]
        )
        response_intensity = np.asarray([float(row["intensity_response"]) for row in selected])
        label = rf"$\Omega=2\pi\times {rabi:g}\,\mathrm{{MHz}}$"
        axes[0].plot(frequency, response_frequency, color=color, linewidth=2.2, label=label)
        axes[1].plot(frequency, response_intensity, color=color, linewidth=2.2, label=label)
    axes[0].set_ylabel(r"Frequency response $I_\nu$ (MHz$^{-2}$)")
    axes[1].set_ylabel(r"Intensity response $I_I$")
    axes[1].set_xlabel("Frequency f (MHz)")
    axes[0].set_ylim(bottom=0.0)
    axes[1].set_ylim(bottom=0.0)
    axes[1].set_xlim(0.0, 15.0)
    for axis in axes:
        axis.legend(frameon=False, fontsize=9)
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(alpha=0.18, linewidth=0.6)
    figure.suptitle("Fig. 6(a): envelope rescaled from Appendix-L functions", fontsize=11)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def render_side_by_side(reference: Path, generated: Path, output: Path, right_title: str) -> None:
    reference_image = plt.imread(reference)
    generated_image = plt.imread(generated)
    figure, axes = plt.subplots(1, 2, figsize=(13.0, 5.0), constrained_layout=True)
    axes[0].imshow(reference_image)
    axes[0].set_title("Paper source figure (reference only)", fontsize=11)
    axes[1].imshow(generated_image)
    axes[1].set_title(right_title, fontsize=11)
    for axis in axes:
        axis.axis("off")
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce Fig. 15 and Fig. 6(a) FRT responses.")
    parser.add_argument(
        "--config",
        default=str(WORKSPACE / "config" / "frt_paper_exact.json"),
        help="Paper-parameter configuration JSON.",
    )
    parser.add_argument(
        "--skip-reference-comparison",
        action="store_true",
        help="Generate numerical data and figures without reading source-figure pixels.",
    )
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model = config["model"]
    universal_config = config["universal_response"]
    fig6_config = config["fig6a"]
    params = GateParameters(
        omega_angular=float(model["omega_angular"]),
        phase_amplitude=float(model["phase_amplitude"]),
        phase_frequency_over_omega=float(model["phase_frequency_over_omega"]),
        phase_offset=float(model["phase_offset"]),
        detuning_over_omega=float(model["detuning_over_omega"]),
        omega_duration_over_2pi=float(model["omega_duration_over_2pi"]),
    )
    frequencies = np.linspace(
        float(universal_config["normalized_frequency_min"]),
        float(universal_config["normalized_frequency_max"]),
        int(universal_config["frequency_points"]),
    )

    start = time.perf_counter()
    curves, diagnostics = universal_responses(
        frequencies,
        params=params,
        time_points=int(universal_config["time_points"]),
    )
    runtime_seconds = time.perf_counter() - start
    fits = {
        f"{metric}_{noise}": appendix_fit(frequencies, metric, noise)
        for metric in ("haar", "symmetric_haar")
        for noise in ("frequency", "intensity")
    }

    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    check_dir = WORKSPACE / "outputs" / "checks"
    comparison_dir = WORKSPACE / "docs" / "comparisons"
    universal_csv = data_dir / "universal_response.csv"
    direct_csv = data_dir / "reconstructed_direct_response.csv"
    fig15_path = figure_dir / "fig15_universal_response.png"
    direct_fig15_path = figure_dir / "fig15_direct_diagnostic.png"
    write_universal_csv(universal_csv, frequencies, fits)
    write_direct_diagnostic_csv(direct_csv, frequencies, curves, fits)
    render_fig15(
        fig15_path,
        frequencies,
        fits,
        float(universal_config["fig15_plot_max"]),
    )
    render_direct_diagnostic(
        direct_fig15_path,
        frequencies,
        curves,
        fits,
        float(universal_config["fig15_plot_max"]),
    )

    plot_mask = frequencies <= float(universal_config["fig15_plot_max"]) + 1.0e-12
    fit_nrmse = {
        key: normalized_rmse(curves[key][plot_mask], fits[key][plot_mask]) for key in curves
    }
    convergence_frequencies = np.linspace(0.0, 3.0, 121)
    coarse_curves, _ = universal_responses(
        convergence_frequencies,
        params=params,
        time_points=int(universal_config["convergence_time_points"]),
    )
    convergence_nrmse = {
        key: normalized_rmse(
            coarse_curves[key],
            np.interp(convergence_frequencies, frequencies, curves[key]),
        )
        for key in coarse_curves
    }
    gate_checks = gate_diagnostics(np.asarray(diagnostics["final_propagator"]))
    sample_times = np.linspace(0.0, params.duration, 9)
    hermiticity_error = max(
        float(np.max(np.abs(operator - operator.conj().T)))
        for sample_time in sample_times
        for operator in (
            ideal_hamiltonian(float(sample_time), params),
            intensity_noise_operator(float(sample_time), params),
        )
    )
    direct_response_at_half = float(np.interp(0.5, frequencies, curves["haar_intensity"]))
    response_at_half = float(np.interp(0.5, frequencies, fits["haar_intensity"]))
    minimum_response = min(float(np.min(curve)) for curve in fits.values())
    second_peak_window = (frequencies >= 1.0) & (frequencies <= 1.4)
    frequency_peak_locations = {
        metric: float(
            frequencies[second_peak_window][
                np.argmax(fits[f"{metric}_frequency"][second_peak_window])
            ]
        )
        for metric in ("haar", "symmetric_haar")
    }
    acceptance = {
        "responses_nonnegative": minimum_response >= -1.0e-8,
        "published_1p5_mhz_response": abs(response_at_half - 1.04) < 0.15,
        "frequency_second_peak_present": all(
            1.0 <= location <= 1.4 for location in frequency_peak_locations.values()
        ),
    }
    universal_check = {
        "schema_version": 1,
        "target_id": "T001",
        "figure_refs": ["Fig. 15"],
        "status": "passed" if all(acceptance.values()) else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "formula_gate": "source_only",
        "formula_dependencies": ["EQ005", "EQ006"],
        "normalized_frequency_points": int(universal_config["frequency_points"]),
        "minimum_response": minimum_response,
        "frequency_second_peak_locations": frequency_peak_locations,
        "haar_intensity_response_x_0p5": response_at_half,
        "paper_reference_x_0p5": 1.04,
        "acceptance": acceptance,
        "known_residuals": [
            {
                "feature": "high-frequency intensity-response side peaks",
                "status": "not_reproduced_by_appendix_l_fit",
                "reason": (
                    "The paper labels Appendix L as approximate; its monotone fit omits "
                    "the small side peaks visible near normalized frequencies 1.5 and 2.5."
                ),
            }
        ],
        "data": str(universal_csv.relative_to(WORKSPACE)),
        "figure": str(fig15_path.relative_to(WORKSPACE)),
    }
    write_json(check_dir / "universal_response.json", universal_check)

    direct_acceptance = {
        "hamiltonian_and_noise_hermitian": hermiticity_error < 1.0e-12,
        "final_propagator_unitary": float(diagnostics["unitarity_error"]) < 1.0e-10,
        "computational_return": gate_checks["max_return_leakage"] < 5.0e-5,
        "controlled_phase": gate_checks["controlled_phase_error_radians"] < 2.0e-2,
        "responses_nonnegative": min(float(np.min(curve)) for curve in curves.values()) >= -1.0e-8,
        "time_grid_converged": max(convergence_nrmse.values()) < 5.0e-3,
    }
    direct_check = {
        "schema_version": 1,
        "target_id": "D001",
        "figure_refs": ["Fig. 15"],
        "status": "partial",
        "artifact_stage": "exploratory",
        "parameter_match": "reconstructed",
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "analytic_reference",
        "formula_gate": "reconstructed",
        "formula_dependencies": ["EQ001", "EQ002", "EQ003", "EQ004"],
        "failure_type": "missing_parameters",
        "limitation": (
            "The paper does not disclose the exact Fig. 15 phase trajectory. The cited "
            "generic Evered pulse closes to a high-fidelity CZ but does not reproduce the "
            "Appendix-L response features, so this diagnostic is intentionally unscored."
        ),
        "runtime_seconds": runtime_seconds,
        "time_points": int(universal_config["time_points"]),
        "normalized_frequency_points": int(universal_config["frequency_points"]),
        "hermiticity_error": hermiticity_error,
        "unitarity_error": float(diagnostics["unitarity_error"]),
        "gate_diagnostics": gate_checks,
        "appendix_fit_nrmse": fit_nrmse,
        "convergence_nrmse": convergence_nrmse,
        "haar_intensity_response_x_0p5": direct_response_at_half,
        "acceptance": direct_acceptance,
        "data": str(direct_csv.relative_to(WORKSPACE)),
        "figure": str(direct_fig15_path.relative_to(WORKSPACE)),
    }
    write_json(check_dir / "direct_response_diagnostic.json", direct_check)

    physical_frequencies = np.linspace(
        float(fig6_config["frequency_min_mhz"]),
        float(fig6_config["frequency_max_mhz"]),
        int(fig6_config["frequency_points"]),
    )
    rabi_values = [float(value) for value in fig6_config["rabi_frequencies_mhz"]]
    scaled_rows, collapse_error = build_scaled_rows(
        frequencies,
        fits,
        physical_frequencies,
        rabi_values,
    )
    scaled_csv = data_dir / "fig6a_scaled_response.csv"
    fig6_path = figure_dir / "fig6a_scaled_response.png"
    write_scaled_csv(scaled_csv, scaled_rows)
    render_fig6a(fig6_path, scaled_rows, rabi_values)
    fig6_check = {
        "schema_version": 1,
        "target_id": "T002",
        "figure_refs": ["Fig. 6"],
        "status": "passed" if collapse_error < 1.0e-12 else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "formula_gate": "source_only",
        "formula_dependencies": ["EQ005", "EQ006"],
        "panel_coverage": {
            "panels": [
                {
                    "panel_id": "a",
                    "status": "reproduced",
                    "evidence": "outputs/figures/fig6a_scaled_response.png",
                },
                {"panel_id": "b", "status": "not_applicable", "note": "measured PSD context"},
                {"panel_id": "c", "status": "not_reproduced", "note": "raw PSD arrays unavailable"}
            ]
        },
        "rabi_frequencies_mhz": rabi_values,
        "frequency_range_mhz": [float(physical_frequencies[0]), float(physical_frequencies[-1])],
        "maximum_scaling_collapse_error": collapse_error,
        "known_residuals": [
            {
                "feature": "small high-frequency intensity-response peaks in panel (a)",
                "status": "not_reproduced_by_appendix_l_fit",
                "reason": "They are absent from the paper's approximate Appendix-L function.",
            },
            {
                "feature": "panel (c) infidelity histograms",
                "status": "not_reproduced",
                "reason": "The measured PSD arrays are unavailable.",
            },
        ],
        "data": str(scaled_csv.relative_to(WORKSPACE)),
        "figure": str(fig6_path.relative_to(WORKSPACE)),
    }
    write_json(check_dir / "fig6a_scaled_response.json", fig6_check)

    if not args.skip_reference_comparison:
        render_side_by_side(
            WORKSPACE / "references" / "original_figures" / "SI_response_compare.png",
            fig15_path,
            comparison_dir / "fig15_source_vs_reproduction.png",
            "Appendix-L analytic envelope",
        )
        render_side_by_side(
            WORKSPACE / "references" / "original_figures" / "Fig_linear_response.png",
            fig6_path,
            comparison_dir / "fig6_source_vs_reproduction.png",
            "Appendix-L envelope for panel (a); panels (b,c) excluded",
        )

    summary = {
        "status": (
            "passed"
            if universal_check["status"] == fig6_check["status"] == "passed"
            else "failed"
        ),
        "targets": {"T001": universal_check["status"], "T002": fig6_check["status"]},
        "diagnostics": {"D001": direct_check["status"]},
        "direct_diagnostic_runtime_seconds": runtime_seconds,
    }
    write_json(check_dir / "run_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
