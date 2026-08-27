#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.fidelity_response import (  # noqa: E402
    GateParameters,
    gate_diagnostics,
    universal_responses,
)
from src.gate_protocols import (  # noqa: E402
    fromonteil_protocol_ii_variant_1,
    integrated_rydberg_population,
    levine_pichler_protocol,
    protocol_response,
)
from src.many_body_response import (  # noqa: E402
    AdiabaticSchedule,
    ManyBodyModel,
    adiabatic_controls,
    adiabatic_response,
    quench_response,
    z2_probabilities,
)
from src.theory_targets import (  # noqa: E402
    cavity_power_transfer,
    error_budget,
    normalized_error_scalings,
    phase_flip_fidelities,
    phase_flip_proxy,
    principal_quantum_number_scaling,
    spin_lock_response,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty data table")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def style_axes(axes: np.ndarray | list[Any]) -> None:
    for axis in np.asarray(axes, dtype=object).ravel():
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(alpha=0.18, linewidth=0.6)


def build_fig7(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    rabi = np.geomspace(
        float(config["rabi_frequency_min_mhz"]),
        float(config["rabi_frequency_max_mhz"]),
        int(config["points"]),
    )
    reference = float(config["reference_rabi_mhz"])
    normalized = normalized_error_scalings(rabi, reference_rabi_mhz=reference)
    budget = error_budget(rabi)
    rows = [
        {
            "rabi_frequency_mhz": float(rabi[index]),
            "frequency_normalized": float(normalized["frequency"][index]),
            "intensity_normalized": float(normalized["intensity"][index]),
            "decay_normalized": float(normalized["decay"][index]),
            "motion_normalized": float(normalized["motion"][index]),
            "intensity_absolute": float(budget.intensity[index]),
            "decay_absolute": float(budget.decay[index]),
            "frequency_per_variance_mhz_minus_2": float(
                budget.frequency_per_mhz2[index]
            ),
            "motion_per_variance_mhz_minus_2": float(
                budget.motion_per_mhz2[index]
            ),
            "generated_data_provenance": "formula_numerics",
        }
        for index in range(len(rabi))
    ]
    data_path = data_dir / "fig7_formula_scalings.csv"
    figure_path = figure_dir / "fig7_formula_scalings.png"
    write_rows(data_path, rows)

    figure, axes = plt.subplots(1, 2, figsize=(9.4, 3.9), constrained_layout=True)
    for key, label, color, linestyle in (
        ("frequency", r"frequency $\Omega^{-2}$", "#0072BD", "-"),
        ("intensity", r"DC intensity $\Omega^{0}$", "#D95319", "-"),
        ("decay", r"decay $\Omega^{-1}$", "#7E2F8E", "-"),
        ("motion", r"motion $\Omega^{-2}$", "#EDB120", "--"),
    ):
        axes[0].loglog(
            rabi,
            normalized[key],
            linewidth=2.0,
            linestyle=linestyle,
            label=label,
            color=color,
        )
    axes[0].axvline(reference, color="0.5", linestyle=":", linewidth=1.0)
    axes[0].set_xlabel(r"Rabi frequency $\Omega/(2\pi)$ (MHz)")
    axes[0].set_ylabel(f"Contribution normalized at {reference:g} MHz")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].set_title("a  Formula-resolved power laws", loc="left", fontweight="bold")

    axes[1].loglog(rabi, budget.intensity, linewidth=2.0, label="intensity: 0.8%", color="#D95319")
    axes[1].loglog(rabi, budget.decay, linewidth=2.0, label="decay: 78/166 us", color="#7E2F8E")
    axes[1].loglog(rabi, budget.known_total, linewidth=2.2, label="known subtotal", color="#A2142F")
    axes[1].set_xlabel(r"Rabi frequency $\Omega/(2\pi)$ (MHz)")
    axes[1].set_ylabel("Absolute symmetric-Haar infidelity")
    axes[1].legend(frameon=False, fontsize=8)
    axes[1].set_title("b  Terms with published amplitudes", loc="left", fontweight="bold")
    style_axes(axes)
    figure.suptitle("Fig. 7 theory: numericalized formulas; unpublished variances left open", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return {
        "target_id": "T003",
        "figure_refs": ["Fig. 1(f)", "Fig. 7"],
        "status": "partial",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "formula_numerics",
        "formula_gate": "verified",
        "formula_dependencies": ["EQ006", "EQ007"],
        "reproduced": ["four asymptotic power laws", "absolute intensity term", "absolute lifetime term"],
        "blocked_exact": ["absolute frequency-noise term: numerical PSD unavailable", "absolute motion term: Doppler variance unavailable"],
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def build_fig8(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    n_values = np.linspace(
        float(config["principal_quantum_number_min"]),
        float(config["principal_quantum_number_max"]),
        int(config["points"]),
    )
    scaling = principal_quantum_number_scaling(n_values)
    rows = [
        {
            "principal_quantum_number": float(n_values[index]),
            "rabi_frequency_mhz": float(scaling["rabi_frequency_mhz"][index]),
            "blockade_limited_spacing_um": float(
                scaling["blockade_limited_spacing_um"][index]
            ),
            "rabi_scaling_exponent": float(scaling["rabi_scaling_exponent"]),
            "generated_data_provenance": "formula_numerics",
        }
        for index in range(len(n_values))
    ]
    data_path = data_dir / "fig8_public_anchor_scaling.csv"
    figure_path = figure_dir / "fig8_public_anchor_scaling.png"
    write_rows(data_path, rows)
    figure, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), constrained_layout=True)
    axes[0].plot(n_values, scaling["rabi_frequency_mhz"], linewidth=2.2, color="#0072BD")
    axes[0].scatter([44, 61], [13.0, 7.7], color="#D95319", zorder=3, label="printed anchors")
    axes[0].set_xlabel("Principal quantum number n")
    axes[0].set_ylabel(r"Fixed-power $\Omega/(2\pi)$ (MHz)")
    axes[0].legend(frameon=False)
    axes[0].set_title("a  Rabi scaling", loc="left", fontweight="bold")
    axes[1].plot(n_values, scaling["blockade_limited_spacing_um"], linewidth=2.2, color="#7E2F8E")
    axes[1].scatter([44, 61], [1.7, 3.3], color="#D95319", zorder=3, label="printed anchors")
    axes[1].set_xlabel("Principal quantum number n")
    axes[1].set_ylabel("Spacing at fixed blockade/Rabi ratio (um)")
    axes[1].legend(frameon=False)
    axes[1].set_title("b  Blockade geometry", loc="left", fontweight="bold")
    style_axes(axes)
    figure.suptitle("Fig. 8 independently determined scaling subset", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return {
        "target_id": "T004",
        "figure_refs": ["Fig. 8"],
        "status": "partial",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "formula_numerics",
        "formula_gate": "reconstructed",
        "formula_dependencies": ["EQ008"],
        "reproduced": ["fixed-power Rabi scaling", "fixed-blockade-ratio spacing scaling"],
        "blocked_exact": ["total infidelity and n=44 optimum: author lifetime, PSD, temperature, and electric-field arrays unavailable"],
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def build_fig9(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    frequencies = np.linspace(
        float(config["normalized_frequency_min"]),
        float(config["normalized_frequency_max"]),
        int(config["points"]),
    )
    time_optimal_curves, time_optimal_diagnostics = universal_responses(
        frequencies,
        params=GateParameters(),
        time_points=int(config["time_optimal_time_points"]),
    )
    protocols = (levine_pichler_protocol(), fromonteil_protocol_ii_variant_1())
    curves: dict[str, dict[str, np.ndarray]] = {
        "Time-optimal": {
            "frequency": time_optimal_curves["symmetric_haar_frequency"],
            "intensity": time_optimal_curves["symmetric_haar_intensity"],
        }
    }
    diagnostics: dict[str, Any] = {
        "Time-optimal": gate_diagnostics(
            np.asarray(time_optimal_diagnostics["final_propagator"])
        )
    }
    exposures: dict[str, float | None] = {"Time-optimal": None}
    for protocol in protocols:
        frequency_response, protocol_diagnostics = protocol_response(
            protocol,
            frequencies,
            noise_kind="frequency",
            points_per_radian=int(config["points_per_radian"]),
        )
        intensity_response, _ = protocol_response(
            protocol,
            frequencies,
            noise_kind="intensity",
            points_per_radian=int(config["points_per_radian"]),
        )
        curves[protocol.name] = {
            "frequency": frequency_response,
            "intensity": intensity_response,
        }
        diagnostics[protocol.name] = gate_diagnostics(
            np.asarray(protocol_diagnostics["final_propagator"])
        )
        exposures[protocol.name] = integrated_rydberg_population(
            protocol,
            points_per_radian=int(config["points_per_radian"]),
        )

    rows: list[dict[str, Any]] = []
    for protocol_name, protocol_curves in curves.items():
        for index, frequency in enumerate(frequencies):
            rows.append(
                {
                    "protocol": protocol_name,
                    "normalized_frequency": float(frequency),
                    "frequency_response": float(protocol_curves["frequency"][index]),
                    "intensity_response": float(protocol_curves["intensity"][index]),
                    "generated_data_provenance": "independent_hamiltonian_numerics",
                }
            )
    data_path = data_dir / "fig9_protocol_responses.csv"
    figure_path = figure_dir / "fig9_protocol_responses.png"
    write_rows(data_path, rows)
    figure, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), constrained_layout=True)
    colors = {
        "Time-optimal": "#0072BD",
        "Levine-Pichler": "#D95319",
        "Fromonteil Protocol II": "#7E2F8E",
    }
    for protocol_name, protocol_curves in curves.items():
        axes[0].plot(
            frequencies,
            protocol_curves["frequency"] / (2.0 * np.pi) ** 2,
            linewidth=2.0,
            label=protocol_name,
            color=colors[protocol_name],
        )
        axes[1].plot(
            frequencies,
            protocol_curves["intensity"],
            linewidth=2.0,
            label=protocol_name,
            color=colors[protocol_name],
        )
    axes[0].set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    axes[0].set_ylabel(r"Frequency response $\Omega^2I_\nu/(2\pi)^2$")
    axes[0].set_title("a  Frequency noise", loc="left", fontweight="bold")
    axes[1].set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    axes[1].set_ylabel(r"Intensity response $I_I$")
    axes[1].set_title("b  Relative intensity noise", loc="left", fontweight="bold")
    for axis in axes:
        axis.set_xlim(frequencies[0], frequencies[-1])
        axis.set_ylim(bottom=0.0)
        axis.legend(frameon=False, fontsize=8)
    style_axes(axes)
    figure.suptitle("Fig. 9(a,b): responses solved from three control Hamiltonians", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    closure_passed = all(
        item["max_return_leakage"] < 5.0e-5
        and item["controlled_phase_error_radians"] < 2.0e-2
        for item in diagnostics.values()
    )
    robust_dc = float(curves["Fromonteil Protocol II"]["intensity"][0])
    return {
        "target_id": "T005",
        "figure_refs": ["Fig. 9(a)", "Fig. 9(b)", "Fig. 9(c)"],
        "status": "passed" if closure_passed and robust_dc < 2.0e-5 else "failed",
        "artifact_stage": "exploratory",
        "parameter_match": "cited_source_reconstructed_identity",
        "generated_data_provenance": "independent_hamiltonian_numerics",
        "reference_comparison": "visual_only",
        "formula_gate": "verified",
        "formula_dependencies": ["EQ001", "EQ003", "EQ004", "EQ009"],
        "panel_coverage": {
            "a": "reproduced",
            "b": "reproduced",
            "c": "blocked_exact: experimental PSD and atomic-motion amplitude unavailable",
        },
        "gate_diagnostics": diagnostics,
        "rydberg_exposure_over_omega": exposures,
        "fromonteil_dc_intensity_response": robust_dc,
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def build_fig10(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    frequencies = np.linspace(
        float(config["frequency_min_mhz"]),
        float(config["frequency_max_mhz"]),
        int(config["points"]),
    )
    duration = float(config["duration_us"])
    locking = [float(value) for value in config["locking_frequencies_mhz"]]
    responses = {
        value: spin_lock_response(
            frequencies,
            locking_rabi_mhz=value,
            duration_us=duration,
        )
        for value in locking
    }
    rows = [
        {
            "frequency_mhz": float(frequency),
            "locking_frequency_mhz": float(locking_frequency),
            "response_us2": float(responses[locking_frequency][index]),
            "generated_data_provenance": "formula_numerics",
        }
        for locking_frequency in locking
        for index, frequency in enumerate(frequencies)
    ]
    data_path = data_dir / "fig10_spin_lock_filter.csv"
    figure_path = figure_dir / "fig10_spin_lock_filter.png"
    write_rows(data_path, rows)
    figure, axis = plt.subplots(figsize=(6.0, 3.9), constrained_layout=True)
    for locking_frequency in locking:
        axis.plot(
            frequencies,
            responses[locking_frequency],
            linewidth=1.8,
            label=f"lock {locking_frequency:g} MHz",
        )
    axis.set_xlabel("Noise frequency (MHz)")
    axis.set_ylabel(r"Finite-time response $I_\nu$ ($\mu$s$^2$)")
    axis.set_xlim(frequencies[0], frequencies[-1])
    axis.set_ylim(bottom=0.0)
    axis.legend(frameon=False)
    style_axes([axis])
    figure.suptitle(f"Fig. 10 theory: {duration:g} us spin-lock filter", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return {
        "target_id": "T006",
        "figure_refs": ["Fig. 10"],
        "status": "partial",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "formula_numerics",
        "formula_gate": "verified",
        "formula_dependencies": ["EQ010"],
        "reproduced": ["finite-time spin-lock response", "resonance-frequency selection", "lifetime-floor formula in code"],
        "blocked_exact": ["absolute decay-rate and PSD panels: author PSD array and experimental points unavailable"],
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def build_fig11(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    model = ManyBodyModel(
        sites=int(config["sites"]),
        rabi_frequency_mhz=float(config["rabi_frequency_mhz"]),
        duration_us=float(config["duration_us"]),
        nearest_neighbor_interaction_over_omega=float(
            config["nearest_neighbor_interaction_over_omega"]
        ),
    )
    schedule = AdiabaticSchedule(
        tangent_shape=float(config["tangent_shape"]),
        detuning_endpoint_over_omega=float(
            config["detuning_endpoint_over_omega"]
        ),
    )
    frequencies = np.linspace(
        float(config["normalized_frequency_min"]),
        float(config["normalized_frequency_max"]),
        int(config["frequency_points"]),
    )
    quench_frequency = quench_response(
        model,
        frequencies,
        noise_kind="frequency",
    )
    quench_intensity = quench_response(
        model,
        frequencies,
        noise_kind="intensity",
    )
    adiabatic_frequency, frequency_diagnostics = adiabatic_response(
        model,
        frequencies,
        noise_kind="frequency",
        schedule=schedule,
        time_steps=int(config["adiabatic_time_steps"]),
    )
    adiabatic_intensity, intensity_diagnostics = adiabatic_response(
        model,
        frequencies,
        noise_kind="intensity",
        schedule=schedule,
        time_steps=int(config["adiabatic_time_steps"]),
    )
    convergence_frequencies = np.linspace(
        float(config["normalized_frequency_min"]),
        float(config["normalized_frequency_max"]),
        13,
    )
    convergence_errors: dict[str, float] = {}
    for noise_kind, full_response in (
        ("frequency", adiabatic_frequency),
        ("intensity", adiabatic_intensity),
    ):
        coarse_response, _ = adiabatic_response(
            model,
            convergence_frequencies,
            noise_kind=noise_kind,
            schedule=schedule,
            time_steps=int(config["adiabatic_time_steps"]) // 2,
        )
        fine_response = np.interp(
            convergence_frequencies,
            frequencies,
            full_response,
        )
        scale = max(float(np.max(np.abs(fine_response))), 1.0e-15)
        convergence_errors[noise_kind] = float(
            np.sqrt(np.mean(np.square(coarse_response - fine_response))) / scale
        )
    z2 = z2_probabilities(model, np.asarray(frequency_diagnostics["final_state"]))
    rows = [
        {
            "normalized_frequency": float(frequency),
            "quench_frequency_response_mhz_minus_2": float(quench_frequency[index]),
            "quench_intensity_response": float(quench_intensity[index]),
            "adiabatic_frequency_response_mhz_minus_2": float(
                adiabatic_frequency[index]
            ),
            "adiabatic_intensity_response": float(adiabatic_intensity[index]),
            "generated_data_provenance": "independent_many_body_numerics",
            "parameter_match": "explicit_physical_reconstruction",
        }
        for index, frequency in enumerate(frequencies)
    ]
    data_path = data_dir / "fig11_many_body_responses.csv"
    figure_path = figure_dir / "fig11_many_body_responses.png"
    write_rows(data_path, rows)
    figure, axes = plt.subplots(2, 2, figsize=(9.4, 7.0), constrained_layout=True)
    axes[0, 0].plot(frequencies, quench_frequency, linewidth=2.0, color="#0072BD")
    axes[0, 1].plot(frequencies, quench_intensity, linewidth=2.0, color="#D95319")
    axes[1, 0].plot(frequencies, adiabatic_frequency, linewidth=2.0, color="#0072BD")
    axes[1, 1].plot(frequencies, adiabatic_intensity, linewidth=2.0, color="#D95319")
    axes[0, 0].set_title("a  Quench: frequency noise", loc="left", fontweight="bold")
    axes[0, 1].set_title("b  Quench: intensity noise", loc="left", fontweight="bold")
    axes[1, 0].set_title("c  Z2 sweep: frequency noise", loc="left", fontweight="bold")
    axes[1, 1].set_title("d  Z2 sweep: intensity noise", loc="left", fontweight="bold")
    axes[0, 0].set_ylabel(r"Response (MHz$^{-2}$)")
    axes[1, 0].set_ylabel(r"Response (MHz$^{-2}$)")
    axes[0, 1].set_ylabel("Response")
    axes[1, 1].set_ylabel("Response")
    for axis in axes[1, :]:
        axis.set_xlabel(r"Normalized frequency $2\pi f/\Omega$")
    for axis in axes.ravel():
        axis.set_xlim(frequencies[0], frequencies[-1])
        axis.set_ylim(bottom=0.0)
    style_axes(axes)
    inset = axes[1, 1].inset_axes([0.54, 0.52, 0.42, 0.42])
    times = np.linspace(0.0, model.duration_us, 201)
    omega, detuning = adiabatic_controls(model, schedule, times)
    inset.plot(times, omega / (2.0 * np.pi), color="#D95319", linewidth=1.2, label="Omega")
    inset.plot(times, detuning / (2.0 * np.pi), color="#0072BD", linewidth=1.2, label="Delta")
    inset.axhline(0.0, color="0.6", linewidth=0.5)
    inset.set_xticks([0.0, model.duration_us])
    inset.tick_params(labelsize=6)
    inset.set_title("explicit sweep (MHz)", fontsize=6)
    figure.suptitle("Fig. 11: seven-body Schrödinger and tangent-equation reconstruction", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    norm_error = max(
        float(frequency_diagnostics["norm_error"]),
        float(intensity_diagnostics["norm_error"]),
    )
    return {
        "target_id": "T009",
        "figure_refs": ["Fig. 11"],
        "status": (
            "partial"
            if norm_error < 2.0e-3 and max(convergence_errors.values()) < 8.0e-2
            else "failed"
        ),
        "artifact_stage": "exploratory",
        "parameter_match": "explicit_physical_reconstruction",
        "generated_data_provenance": "independent_many_body_numerics",
        "reference_comparison": "visual_only",
        "formula_gate": "reconstructed",
        "formula_dependencies": ["EQ003", "EQ011"],
        "model": {
            "sites": model.sites,
            "rabi_frequency_mhz": model.rabi_frequency_mhz,
            "duration_us": model.duration_us,
            "nearest_neighbor_interaction_over_omega": model.nearest_neighbor_interaction_over_omega,
            "interaction_status": config["interaction_status"],
            "detuning_sign_status": config["detuning_sign_status"],
        },
        "solver": {
            "quench": "exact spectral decomposition",
            "adiabatic": "unitary diagonal/X split-step plus midpoint first-order complex tangent equations",
            "adiabatic_time_steps": int(config["adiabatic_time_steps"]),
            "maximum_norm_error": norm_error,
            "half_grid_convergence_nrmse": convergence_errors,
        },
        "z2_final_probability": z2,
        "reproduced": ["seven-site Hamiltonian response calculation", "quench low-frequency intensity accumulation", "adiabatic finite-frequency response mechanism"],
        "blocked_exact": ["paper-exact curves: atom spacing, C6/r^6, exact Rabi ramp, and tangent-shape parameter unavailable"],
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def build_fig12(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    frequencies = np.linspace(
        float(config["frequency_min_mhz"]),
        float(config["frequency_max_mhz"]),
        int(config["points"]),
    )
    linewidth = float(config["linewidth_mhz"])
    transfer = cavity_power_transfer(frequencies, linewidth_mhz=linewidth)
    rows = [
        {
            "frequency_mhz": float(frequency),
            "cavity_power_transfer": float(transfer[index]),
            "linewidth_mhz": linewidth,
            "generated_data_provenance": "formula_numerics",
            "parameter_match": "reconstructed_transfer_convention",
        }
        for index, frequency in enumerate(frequencies)
    ]
    data_path = data_dir / "fig12_cavity_transfer.csv"
    figure_path = figure_dir / "fig12_cavity_transfer.png"
    write_rows(data_path, rows)
    figure, axis = plt.subplots(figsize=(6.0, 3.9), constrained_layout=True)
    axis.semilogy(frequencies, transfer, linewidth=2.2, color="#0072BD")
    axis.axvline(linewidth, color="#D95319", linestyle="--", label=f"{linewidth:g} MHz")
    axis.set_xlabel("Noise frequency (MHz)")
    axis.set_ylabel("Cavity power transfer")
    axis.set_xlim(frequencies[0], frequencies[-1])
    axis.set_ylim(1.0e-4, 1.1)
    axis.legend(frameon=False)
    style_axes([axis])
    figure.suptitle("Fig. 12 theory subset: projected single-pole cavity suppression", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return {
        "target_id": "T007",
        "figure_refs": ["Fig. 12"],
        "status": "partial",
        "artifact_stage": "exploratory",
        "parameter_match": "reconstructed_transfer_convention",
        "generated_data_provenance": "formula_numerics",
        "formula_gate": "reconstructed",
        "formula_dependencies": ["EQ013"],
        "reproduced": ["140 kHz cavity transfer and limiting behavior"],
        "blocked_exact": ["filtered PSD and fidelity curves: numerical current PSD unavailable", "full-model panel: calibration/error-model inputs unavailable"],
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def build_fig17(config: dict[str, Any], data_dir: Path, figure_dir: Path) -> dict[str, Any]:
    p_values = np.linspace(
        float(config["phase_flip_probability_min"]),
        float(config["phase_flip_probability_max"]),
        int(config["phase_flip_points"]),
    )
    symmetric = np.linspace(
        float(config["symmetric_infidelity_min"]),
        float(config["symmetric_infidelity_max"]),
        int(config["symmetric_infidelity_points"]),
    )
    gate_count = int(config["single_qubit_gate_count"])
    proxy = phase_flip_proxy(
        p_values,
        symmetric,
        single_qubit_gate_count=gate_count,
    )
    state_fidelities = phase_flip_fidelities(p_values)
    rows = [
        {
            "phase_flip_probability": float(p_value),
            "symmetric_infidelity": float(symmetric[index]),
            "first_order_ssb_infidelity": float(
                proxy["first_order_ssb_infidelity"][p_index, index]
            ),
            "first_order_slope": float(proxy["first_order_slope"][p_index]),
            "product_state_phase_flip_fidelity": float(
                state_fidelities["product_state_fidelity"][p_index]
            ),
            "symmetric_state_phase_flip_fidelity": float(
                state_fidelities["symmetric_state_fidelity"][p_index]
            ),
            "single_qubit_gate_count": gate_count,
            "generated_data_provenance": "formula_numerics",
        }
        for p_index, p_value in enumerate(p_values)
        for index in range(len(symmetric))
    ]
    data_path = data_dir / "fig17_phase_flip_first_order.csv"
    figure_path = figure_dir / "fig17_phase_flip_first_order.png"
    write_rows(data_path, rows)
    figure, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), constrained_layout=True)
    for p_index, p_value in enumerate(p_values):
        axes[0].plot(
            symmetric,
            proxy["first_order_ssb_infidelity"][p_index],
            linewidth=1.8,
            label=f"p={p_value:.3f}",
        )
    axes[0].plot(symmetric, symmetric, color="0.3", linestyle="--", linewidth=1.0, label="1:1")
    axes[0].set_xlabel(r"Actual symmetric infidelity $1-F_{\rm Sym}$")
    axes[0].set_ylabel(r"First-order inferred $1-F_{\rm SSB}$")
    axes[0].legend(frameon=False, fontsize=7)
    axes[0].set_title("a  Printed first-order model", loc="left", fontweight="bold")
    axes[1].plot(p_values, proxy["first_order_slope"], marker="o", linewidth=2.0, color="#0072BD")
    axes[1].set_xlabel("Phase-flip probability p")
    axes[1].set_ylabel("Predicted linear slope")
    axes[1].set_title(f"b  Slope for explicit N={gate_count}", loc="left", fontweight="bold")
    style_axes(axes)
    figure.suptitle("Fig. 17 analytical content: no fitted source-figure data", fontsize=10)
    figure.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return {
        "target_id": "T008",
        "figure_refs": ["Fig. 17"],
        "status": "partial",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_formula_with_explicit_N_reconstruction",
        "generated_data_provenance": "formula_numerics",
        "formula_gate": "verified",
        "formula_dependencies": ["EQ012"],
        "single_qubit_gate_count": gate_count,
        "gate_count_status": config["gate_count_status"],
        "reproduced": ["product/symmetric phase-flip fidelities", "first-order SSB slope and cancellation"],
        "blocked_exact": ["quadratic perfect-CZ inset and full circuit simulation: exact Fig. 17 circuit length/recovery realization unavailable"],
        "data": str(data_path.relative_to(WORKSPACE)),
        "figure": str(figure_path.relative_to(WORKSPACE)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate formula-derived theoretical targets without source-figure data inputs."
    )
    parser.add_argument(
        "--config",
        default=str(WORKSPACE / "config" / "formula_theory_targets.json"),
    )
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    checks = [
        build_fig7(config["fig7"], data_dir, figure_dir),
        build_fig8(config["fig8"], data_dir, figure_dir),
        build_fig9(config["fig9"], data_dir, figure_dir),
        build_fig10(config["fig10"], data_dir, figure_dir),
        build_fig11(config["fig11"], data_dir, figure_dir),
        build_fig12(config["fig12"], data_dir, figure_dir),
        build_fig17(config["fig17"], data_dir, figure_dir),
    ]
    payload = {
        "schema_version": 1,
        "status": "passed" if all(item["status"] != "failed" for item in checks) else "failed",
        "source_figure_data_used_as_computational_input": False,
        "targets": checks,
    }
    check_path = WORKSPACE / "outputs" / "checks" / "formula_theory_targets.json"
    write_json(check_path, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
