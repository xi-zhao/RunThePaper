#!/usr/bin/env python3
"""Run the independently implemented analytic targets for arXiv:2607.00718."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.io import loadmat


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_PATH = WORKSPACE.parent
sys.path.insert(0, str(WORKSPACE / "src"))

from finite_hilbert_dynamics import simulate_finite_hilbert_grid  # noqa: E402
from squeezing_nonreciprocity import (  # noqa: E402
    closed_charger_squeezed_energy_dynamics,
    effective_enhancement,
    forward_transmission,
    forward_transmission_zero_squeezed_frequency,
    gaussian_battery_energy_dynamics,
    gaussian_master_equation_energy_dynamics,
    gaussian_invariant,
    optimal_transmission_coupling,
    passive_state_energy,
    steady_state_energy,
    steady_state_energy_derivative,
    steady_state_ergotropy,
    steady_state_energy_nonsqueezed,
)
from ts01_feature_contract import (  # noqa: E402
    assess_ts01_detuning_regime,
    assess_ts01_truncation_discrepancy,
)


COLORS = {
    "a": "#147ce5",
    "b": "#009795",
    "c": "#ff3b52",
    "baseline": "#94418d",
}
LINESTYLES = {
    "a": "-.",
    "b": "--",
    "c": "-",
    "baseline": ":",
}


def _load_config(target_id: str) -> dict[str, Any]:
    path = WORKSPACE / "config" / f"{target_id.lower()}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _case_input(relative_path: str) -> Path:
    """Resolve master-case inputs and the sanitized public data layout."""

    relative = Path(relative_path)
    master_path = CASE_PATH / relative
    if master_path.is_file():
        return master_path

    author_prefix = Path("raw") / "author_data" / "data"
    try:
        author_relative = relative.relative_to(author_prefix)
    except ValueError:
        return master_path
    return CASE_PATH / "reference_data" / "author" / author_relative


def _source_figure_artifact(name: str) -> str:
    """Keep private source paths out of the sanitized public projection."""

    if WORKSPACE.name == "workspace":
        return str(Path("workspace") / "references" / "original_figures" / name)
    return f"source figure {name} is validation-only and not redistributed"


def _ensure_outputs() -> None:
    for relative in ("outputs/data", "outputs/figures", "outputs/checks"):
        (WORKSPACE / relative).mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, header: list[str], rows: list[tuple[Any, ...]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _write_check(target_id: str, payload: dict[str, Any]) -> Path:
    path = WORKSPACE / "outputs" / "checks" / f"{target_id.lower()}_checks.json"
    complete = {
        "schema_version": 1,
        "paper_id": CASE_PATH.name,
        "target_id": target_id,
        **payload,
    }
    path.write_text(
        json.dumps(complete, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _paper_axes(ax: plt.Axes) -> None:
    ax.tick_params(direction="in", top=True, right=True, width=1.1, labelsize=10)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)


def run_t001(config: dict[str, Any]) -> dict[str, Any]:
    r = float(config["representative_r"])
    fractions = np.asarray(config["delta_r_fractions"], dtype=float)
    phase = np.linspace(0.0, 2.0 * np.pi, int(config["phase_points"]))
    rows: list[tuple[Any, ...]] = []
    curves: list[tuple[float, np.ndarray]] = []
    for fraction in fractions:
        delta_r = fraction * 2.0 * r
        r_a = r + delta_r / 2.0
        r_b = r - delta_r / 2.0
        enhancement = effective_enhancement(r_a, r_b, phase)
        curves.append((delta_r, enhancement))
        rows.extend(
            (float(theta), float(delta_r), float(value))
            for theta, value in zip(phase, enhancement, strict=True)
        )

    data_path = WORKSPACE / "outputs" / "data" / "fig1c_enhancement.csv"
    _write_csv(data_path, ["delta_theta", "delta_r", "G"], rows)

    fig = plt.figure(figsize=(3.09, 3.295), dpi=200)
    ax = fig.add_subplot(111, projection="polar")
    cmap = LinearSegmentedColormap.from_list(
        "delta_r", ["#369c9d", "#abd7a1", "#f7a56f", "#ff6672"]
    )
    for index, (delta_r, enhancement) in enumerate(curves):
        color = cmap(index / max(1, len(curves) - 1))
        ax.plot(phase, enhancement, color=color, linewidth=2.2)
    ax.scatter([0.0], [1.0], color="red", marker="*", s=90, zorder=5)
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_thetagrids([0, 90, 180, 270], labels=["0°", "90°", "180°", "270°"])
    ax.set_ylim(0.0, np.cosh(2.0 * r) * 1.08)
    ax.set_yticklabels([])
    ax.grid(color="#d0d0d0", linewidth=0.6)
    ax.set_title(r"$G(\Delta\theta,\Delta r)$", fontsize=12, pad=10)
    fig.subplots_adjust(left=0.17, right=0.83, top=0.86, bottom=0.12)
    figure_path = WORKSPACE / "outputs" / "figures" / "fig1c_enhancement.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    delta_r_dense = np.linspace(0.0, 2.0 * r, 101)
    r_a_dense = r + delta_r_dense / 2.0
    r_b_dense = r - delta_r_dense / 2.0
    phase_dense = np.linspace(0.0, 2.0 * np.pi, 361)
    symmetric_error = float(abs(effective_enhancement(r, r, 0.0) - 1.0))
    pi_error = float(
        np.max(
            np.abs(
                effective_enhancement(r_a_dense, r_b_dense, np.pi)
                - np.cosh(2.0 * r)
            )
        )
    )
    one_mode_error = float(
        np.max(
            np.abs(
                effective_enhancement(2.0 * r, 0.0, phase_dense)
                - np.cosh(2.0 * r)
            )
        )
    )
    mirror_error = float(
        np.max(
            np.abs(
                effective_enhancement(r, r, phase_dense)
                - effective_enhancement(r, r, 2.0 * np.pi - phase_dense)
            )
        )
    )
    passed = max(symmetric_error, pi_error, one_mode_error, mirror_error) < 1e-11
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "exploratory",
        "parameter_match": "not_applicable",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "metrics": {
            "symmetric_basepoint_abs_error": symmetric_error,
            "pi_phase_constant_radius_max_abs_error": pi_error,
            "single_mode_constant_radius_max_abs_error": one_mode_error,
            "phase_mirror_symmetry_max_abs_error": mirror_error,
            "outer_radius_cosh_2r": float(np.cosh(2.0 * r)),
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
        },
    }


def run_t002c(config: dict[str, Any]) -> dict[str, Any]:
    coupling = float(config["coupling"])
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    squeezing = np.linspace(
        float(config["squeezing_min"]),
        float(config["squeezing_max"]),
        int(config["points"]),
    )
    baseline = float(steady_state_energy_nonsqueezed(coupling, kappa, drive))
    enhancements = {
        case: steady_state_energy(case, coupling, squeezing, kappa, drive) / baseline
        for case in ("a", "b", "c")
    }

    data_path = WORKSPACE / "outputs" / "data" / "fig2c_energy_enhancement.csv"
    _write_csv(
        data_path,
        ["r", "Ea_over_E0", "Eb_over_E0", "Ec_over_E0"],
        [
            (
                float(value),
                float(enhancements["a"][index]),
                float(enhancements["b"][index]),
                float(enhancements["c"][index]),
            )
            for index, value in enumerate(squeezing)
        ],
    )

    fig, ax = plt.subplots(figsize=(5.25, 3.95), dpi=200)
    for case in ("a", "b", "c"):
        ax.plot(
            squeezing,
            enhancements[case],
            color=COLORS[case],
            linestyle=LINESTYLES[case],
            linewidth=3.0,
        )
    ax.set_yscale("log")
    ax.set_xlim(0.0, 2.0)
    ax.set_ylim(0.75, 420.0)
    ax.set_xticks([0.0, 0.5, 1.0, 1.5, 2.0])
    ax.set_xlabel(r"$r$", fontsize=14)
    ax.set_ylabel(r"$E_i^{\rm ss}/E^{\rm ss}$", fontsize=14)
    ax.text(
        0.20,
        0.65,
        r"$E_c^{\rm ss}/E^{\rm ss}$",
        color=COLORS["c"],
        transform=ax.transAxes,
        fontsize=13,
    )
    ax.text(
        0.56,
        0.54,
        r"$E_b^{\rm ss}/E^{\rm ss}$",
        color=COLORS["b"],
        transform=ax.transAxes,
        fontsize=13,
    )
    ax.text(
        0.56,
        0.15,
        r"$E_a^{\rm ss}/E^{\rm ss}$",
        color=COLORS["a"],
        transform=ax.transAxes,
        fontsize=13,
    )
    fig.text(0.01, 0.94, "(c)", fontsize=22)
    _paper_axes(ax)
    fig.subplots_adjust(left=0.202, right=0.948, top=0.944, bottom=0.194)
    figure_path = WORKSPACE / "outputs" / "figures" / "fig2c_energy_enhancement.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    author = loadmat(_case_input(str(config["author_data_path"])))
    author_map = {"a": "Eta1", "b": "Eta2", "c": "Eta3"}
    max_errors: dict[str, float] = {}
    rmse: dict[str, float] = {}
    for case, key in author_map.items():
        reference = np.asarray(author[key], dtype=float).ravel()
        residual = enhancements[case] - reference
        max_errors[case] = float(np.max(np.abs(residual)))
        rmse[case] = float(np.sqrt(np.mean(residual**2)))
    passed = max(max_errors.values()) < 5e-10
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "author_data",
        "metrics": {
            "author_data_max_abs_error": max_errors,
            "author_data_rmse": rmse,
            "author_points_per_curve": int(squeezing.size),
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "author_data": str(config["author_data_path"]),
        },
    }


def _optimal_branch(
    coupling: np.ndarray,
    squeezing: np.ndarray,
    derivative: Callable[[np.ndarray, float], np.ndarray],
) -> np.ndarray:
    branch = np.full(squeezing.shape, np.nan, dtype=float)
    log_coupling = np.log(coupling)
    for row, squeezing_value in enumerate(squeezing):
        values = derivative(coupling, float(squeezing_value))
        transitions = np.flatnonzero((values[:-1] > 0.0) & (values[1:] <= 0.0))
        if transitions.size == 0:
            continue
        index = int(transitions[0])
        weight = values[index] / (values[index] - values[index + 1])
        branch[row] = np.exp(
            log_coupling[index]
            + weight * (log_coupling[index + 1] - log_coupling[index])
        )
    return branch


def _global_threshold(
    case: str,
    coupling: np.ndarray,
    kappa: float,
    drive: float,
) -> float:
    if case == "b":
        denominator = (
            kappa
            * (2.0 * coupling + kappa)
            * (12.0 * coupling**2 - 4.0 * coupling * kappa + kappa**2)
        )
    elif case == "c":
        denominator = kappa * (2.0 * coupling + kappa) ** 3
    else:
        raise ValueError(case)
    value = 64.0 * coupling * drive**2 * (2.0 * coupling - kappa) / denominator
    positive = value > 0.0
    thresholds = np.full_like(value, np.nan)
    thresholds[positive] = np.arcsinh(np.sqrt(value[positive]))
    return float(np.nanmax(thresholds))


def run_t003(config: dict[str, Any]) -> dict[str, Any]:
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    coupling = np.logspace(
        np.log10(float(config["coupling_min"])),
        np.log10(float(config["coupling_max"])),
        int(config["coupling_points"]),
    )
    squeezing = np.linspace(
        float(config["squeezing_min"]),
        float(config["squeezing_max"]),
        int(config["squeezing_points"]),
    )
    coupling_mesh, squeezing_mesh = np.meshgrid(coupling, squeezing)
    energies = {
        case: steady_state_energy(
            case, coupling_mesh, squeezing_mesh, kappa, drive
        )
        for case in ("a", "b", "c")
    }
    derivatives = {
        case: steady_state_energy_derivative(
            case, coupling_mesh, squeezing_mesh, kappa, drive
        )
        for case in ("a", "b", "c")
    }
    branches = {
        case: _optimal_branch(
            coupling,
            squeezing,
            lambda values, r, selected=case: steady_state_energy_derivative(
                selected, values, r, kappa, drive
            ),
        )
        for case in ("a", "b", "c")
    }
    thresholds = {
        case: _global_threshold(case, coupling, kappa, drive)
        for case in ("b", "c")
    }

    line_coupling = np.linspace(
        1e-8, float(config["line_coupling_max"]), int(config["line_points"])
    )
    line_squeezing = float(config["line_squeezing"])
    line_energies = {
        "baseline": steady_state_energy_nonsqueezed(
            line_coupling, kappa, drive
        ),
        **{
            case: steady_state_energy(
                case, line_coupling, line_squeezing, kappa, drive
            )
            for case in ("a", "b", "c")
        },
    }

    data_path = WORKSPACE / "outputs" / "data" / "fig3_steady_energies.npz"
    np.savez_compressed(
        data_path,
        coupling=coupling,
        squeezing=squeezing,
        energy_a=energies["a"],
        energy_b=energies["b"],
        energy_c=energies["c"],
        derivative_a=derivatives["a"],
        derivative_b=derivatives["b"],
        derivative_c=derivatives["c"],
        optimal_a=branches["a"],
        optimal_b=branches["b"],
        optimal_c=branches["c"],
        line_coupling=line_coupling,
        line_baseline=line_energies["baseline"],
        line_a=line_energies["a"],
        line_b=line_energies["b"],
        line_c=line_energies["c"],
    )

    fig, axes = plt.subplots(2, 2, figsize=(11.79, 9.77), dpi=200)
    contour_levels = {"a": 55, "b": 55, "c": 55}
    for index, case in enumerate(("a", "b", "c")):
        ax = axes.flat[index]
        contour = ax.contourf(
            coupling_mesh,
            squeezing_mesh,
            energies[case],
            levels=contour_levels[case],
            cmap="coolwarm",
        )
        valid = np.isfinite(branches[case])
        ax.plot(
            branches[case][valid],
            squeezing[valid],
            color="white",
            linewidth=2.2,
            linestyle="--",
        )
        if case in thresholds:
            ax.axhline(
                thresholds[case],
                color="black",
                linestyle=":",
                linewidth=2.0,
            )
            ax.text(
                2.4e-6,
                min(1.82, thresholds[case] + 0.18),
                r"Threshold value $r_{\rm th}$",
                fontsize=12,
            )
        ax.set_xscale("log")
        ax.set_xlim(coupling[0], coupling[-1])
        ax.set_ylim(squeezing[0], squeezing[-1])
        ax.set_xlabel(r"$J/\omega_b$", fontsize=13)
        ax.set_ylabel(r"$r$", fontsize=13)
        ax.text(
            0.72,
            0.08,
            fr"case $({case})$",
            transform=ax.transAxes,
            color="white",
            fontsize=14,
        )
        ax.text(-0.23, 1.02, f"({chr(97 + index)})", transform=ax.transAxes, fontsize=18)
        _paper_axes(ax)
        color_axis = inset_axes(
            ax,
            width="45%",
            height="5%",
            loc="lower left",
            bbox_to_anchor=(0.06, 0.11, 1, 1),
            bbox_transform=ax.transAxes,
            borderpad=0,
        )
        fig.colorbar(contour, cax=color_axis, orientation="horizontal")
        color_axis.xaxis.set_major_locator(MaxNLocator(5))
        color_axis.tick_params(labelsize=8)

    ax = axes.flat[3]
    for series in ("baseline", "a", "b", "c"):
        ax.plot(
            line_coupling,
            line_energies[series],
            color=COLORS[series],
            linestyle=LINESTYLES[series],
            linewidth=2.7,
        )
    ax.set_xlim(0.0, float(config["line_coupling_max"]))
    ax.set_ylim(0.0, 5.0)
    ax.set_xticks([0.0, 0.001, 0.002])
    ax.set_xticklabels(["0", "0.001", "0.002"])
    ax.set_xlabel(r"$J/\omega_b$", fontsize=13)
    ax.set_ylabel(r"$E_i^{\rm ss}/\omega_b$", fontsize=13)
    ax.text(-0.23, 1.02, "(d)", transform=ax.transAxes, fontsize=18)
    ax.text(
        0.40,
        0.35,
        r"scales $\sim\sinh^2 r$",
        transform=ax.transAxes,
        fontsize=14,
    )
    _paper_axes(ax)
    fig.subplots_adjust(
        left=0.10, right=0.98, top=0.97, bottom=0.09, wspace=0.28, hspace=0.30
    )
    figure_path = WORKSPACE / "outputs" / "figures" / "fig3_steady_energies.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    author = loadmat(_case_input(str(config["author_data_path"])))
    author_coupling = np.asarray(author["J1"], dtype=float).ravel()
    author_reference = {
        "baseline": np.asarray(author["E_b4"], dtype=float).ravel(),
        "a": np.asarray(author["E_b1"], dtype=float).ravel(),
        "b": np.asarray(author["E_b2"], dtype=float).ravel(),
        "c": np.asarray(author["E_b3"], dtype=float).ravel(),
    }
    author_generated = {
        "baseline": steady_state_energy_nonsqueezed(
            author_coupling, kappa, drive
        ),
        **{
            case: steady_state_energy(
                case, author_coupling, line_squeezing, kappa, drive
            )
            for case in ("a", "b", "c")
        },
    }
    max_errors = {
        key: float(np.max(np.abs(author_generated[key] - author_reference[key])))
        for key in author_reference
    }
    baseline_mesh = steady_state_energy_nonsqueezed(
        coupling_mesh, kappa, drive
    )
    identity_error = float(
        np.max(
            np.abs(
                energies["a"] + energies["b"] - baseline_mesh - energies["c"]
            )
        )
    )
    passed = max(max_errors.values()) < 5e-12 and identity_error < 5e-12
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "author_data",
        "metrics": {
            "author_panel_d_max_abs_error": max_errors,
            "steady_energy_identity_max_abs_error": identity_error,
            "threshold_r_b": thresholds["b"],
            "threshold_r_c": thresholds["c"],
            "grid_shape": [int(squeezing.size), int(coupling.size)],
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "author_data": str(config["author_data_path"]),
        },
    }


def run_t004(config: dict[str, Any]) -> dict[str, Any]:
    kappa_a = float(config["kappa_a"])
    kappa_b = float(config["kappa_b"])
    coupling = optimal_transmission_coupling(kappa_a, kappa_b)
    collective_decay = 2.0 * coupling
    map_axis = np.linspace(
        float(config["normalized_frequency_min"]),
        float(config["normalized_frequency_max"]),
        int(config["map_points"]),
    )
    omega_normalized, omega_s_normalized = np.meshgrid(map_axis, map_axis)
    transmission_map = forward_transmission(
        omega_normalized * collective_decay,
        omega_s_normalized * collective_decay,
        1.0,
        1.0,
        np.pi,
        coupling,
        kappa_a,
        kappa_b,
        collective_decay,
    )
    line_axis = np.linspace(
        float(config["normalized_frequency_min"]),
        float(config["normalized_frequency_max"]),
        int(config["line_points"]),
    )
    configurations = {
        "symmetric_pi": (1.0, 1.0, np.pi),
        "asymmetric_pi_over_2": (0.2, 1.8, np.pi / 2.0),
        "symmetric_pi_over_2": (1.0, 1.0, np.pi / 2.0),
        "nonsqueezed": (0.0, 0.0, 0.0),
    }
    transmissions = {
        name: forward_transmission_zero_squeezed_frequency(
            line_axis * collective_decay,
            r_a,
            r_b,
            phase,
            coupling,
            kappa_a,
            kappa_b,
            collective_decay,
        )
        for name, (r_a, r_b, phase) in configurations.items()
    }

    data_path = WORKSPACE / "outputs" / "data" / "fig4_transmission.npz"
    np.savez_compressed(
        data_path,
        omega_over_gamma=map_axis,
        omega_s_over_gamma=map_axis,
        transmission_map=transmission_map,
        line_omega_over_gamma=line_axis,
        **transmissions,
    )

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.775), dpi=200)
    image = axes[0].pcolormesh(
        omega_normalized,
        omega_s_normalized,
        transmission_map,
        shading="auto",
        cmap="Blues",
        vmin=0.0,
        vmax=30.0,
    )
    axes[0].set_xlim(map_axis[0], map_axis[-1])
    axes[0].set_ylim(map_axis[0], map_axis[-1])
    axes[0].set_xlabel(r"$\omega/\Gamma$", fontsize=14)
    axes[0].set_ylabel(r"$\omega_s/\Gamma$", fontsize=14)
    axes[0].text(-0.24, 1.02, "(a)", transform=axes[0].transAxes, fontsize=20)
    _paper_axes(axes[0])
    colorbar = fig.colorbar(image, ax=axes[0], pad=0.05)
    colorbar.set_label(r"$T_{ba}$", fontsize=14)
    colorbar.ax.tick_params(labelsize=10)

    styles = {
        "symmetric_pi": (COLORS["c"], "-", 3.0),
        "asymmetric_pi_over_2": (COLORS["b"], "--", 3.0),
        "symmetric_pi_over_2": (COLORS["a"], "-.", 3.0),
        "nonsqueezed": (COLORS["baseline"], ":", 3.0),
    }
    for name, values in transmissions.items():
        color, linestyle, width = styles[name]
        axes[1].plot(
            line_axis,
            values,
            color=color,
            linestyle=linestyle,
            linewidth=width,
        )
    axes[1].set_xlim(line_axis[0], line_axis[-1])
    axes[1].set_ylim(-1.0, 30.0)
    axes[1].set_xlabel(r"$\omega/\Gamma$", fontsize=14)
    axes[1].set_ylabel(r"$T_{ba}$", fontsize=14)
    axes[1].text(-0.22, 1.02, "(b)", transform=axes[1].transAxes, fontsize=20)
    _paper_axes(axes[1])
    fig.subplots_adjust(left=0.09, right=0.98, top=0.94, bottom=0.18, wspace=0.34)
    figure_path = WORKSPACE / "outputs" / "figures" / "fig4_transmission.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    general_zero = forward_transmission(
        line_axis * collective_decay,
        0.0,
        1.0,
        1.0,
        np.pi,
        coupling,
        kappa_a,
        kappa_b,
        collective_decay,
    )
    reduction_error = float(
        np.max(np.abs(general_zero - transmissions["symmetric_pi"]))
    )
    peak_values = {name: float(np.max(values)) for name, values in transmissions.items()}

    def optimum_peak(coupling_value: float) -> float:
        return float(
            forward_transmission_zero_squeezed_frequency(
                0.0,
                1.0,
                1.0,
                np.pi,
                coupling_value,
                kappa_a,
                kappa_b,
                2.0 * coupling_value,
            )
        )

    optimum_margin = min(
        optimum_peak(coupling) - optimum_peak(0.9 * coupling),
        optimum_peak(coupling) - optimum_peak(1.1 * coupling),
    )

    author_map = loadmat(_case_input(str(config["author_map_path"])))
    author_lines = loadmat(_case_input(str(config["author_lines_path"])))
    author_map_max = float(np.max(np.asarray(author_map["Tab"], dtype=float)))
    author_line_max = float(
        max(
            np.max(np.asarray(author_lines[key], dtype=float))
            for key in ("Tab1", "Tab2", "Tab3")
        )
    )
    published_peak = peak_values["symmetric_pi"]
    author_version_ratio = max(author_map_max, author_line_max) / published_peak
    author_data_compatible = bool(author_version_ratio > 0.8)

    passed = (
        reduction_error < 1e-11
        and optimum_margin > 0.0
        and peak_values["symmetric_pi"]
        > peak_values["asymmetric_pi_over_2"]
        > peak_values["symmetric_pi_over_2"]
        > peak_values["nonsqueezed"]
    )
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "visual_feature_contract",
        "metrics": {
            "general_to_omega_s_zero_max_abs_error": reduction_error,
            "optimal_coupling_local_margin": float(optimum_margin),
            "line_peak_values": peak_values,
            "published_formula_peak": published_peak,
            "zenodo_map_peak": author_map_max,
            "zenodo_line_peak": author_line_max,
            "zenodo_to_published_peak_ratio": author_version_ratio,
            "zenodo_data_compatible_with_final_figure": author_data_compatible,
        },
        "notes": [
            "The final-paper formula and final source figure peak near 27.3.",
            "The deposited fig3 arrays peak at 10.07 or below and appear to belong to an older manuscript version; they are retained as provenance evidence but excluded from the final numerical acceptance gate.",
        ],
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "author_map_data": str(config["author_map_path"]),
            "author_line_data": str(config["author_lines_path"]),
        },
    }


def run_t002a(config: dict[str, Any]) -> dict[str, Any]:
    coupling = float(config["coupling"])
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    squeezing = float(config["squeezing"])
    omega_s = float(config["omega_s"])
    kappa_b_offset = float(config["closed_form_kappa_b_offset"])
    kappa_b = kappa + kappa_b_offset
    times = np.linspace(
        0.0,
        float(config["time_max"]),
        int(config["time_points"]),
    )
    cases = ("baseline", "a", "b", "c")
    energies = {
        "baseline": gaussian_battery_energy_dynamics(
            "baseline",
            times,
            coupling,
            kappa,
            kappa_b,
            drive,
            squeezing,
            omega_s,
        )
    }
    energies["a"] = closed_charger_squeezed_energy_dynamics(
        times,
        coupling,
        2.0 * coupling + kappa,
        2.0 * coupling + kappa_b,
        drive,
        squeezing,
    )
    energies["b"] = gaussian_battery_energy_dynamics(
        "b",
        times,
        coupling,
        kappa,
        kappa_b,
        drive,
        squeezing,
        omega_s,
    )
    energies["c"] = np.maximum(
        energies["a"] + energies["b"] - energies["baseline"],
        0.0,
    )
    powers = {
        case: np.divide(
            values,
            times,
            out=np.full_like(values, np.nan),
            where=times > 0.0,
        )
        for case, values in energies.items()
    }

    data_path = WORKSPACE / "outputs" / "data" / "fig2ab_dynamics.npz"
    np.savez_compressed(
        data_path,
        time=times,
        scaled_time=coupling * times,
        energy_baseline=energies["baseline"],
        energy_a=energies["a"],
        energy_b=energies["b"],
        energy_c=energies["c"],
        power_baseline=powers["baseline"],
        power_a=powers["a"],
        power_b=powers["b"],
        power_c=powers["c"],
    )

    fig, axes = plt.subplots(1, 2, figsize=(10.39, 4.0), dpi=200)
    for case in cases:
        axes[0].plot(
            coupling * times,
            energies[case],
            color=COLORS[case],
            linestyle=LINESTYLES[case],
            linewidth=3.0,
        )
    axes[0].set_xlim(0.0, 10.0)
    axes[0].set_ylim(-0.1, 5.0)
    axes[0].set_xlabel(r"$Jt$", fontsize=14)
    axes[0].set_ylabel(r"$E_i/\omega_b$", fontsize=14)
    axes[0].text(-0.18, 1.02, "(a)", transform=axes[0].transAxes, fontsize=20)
    _paper_axes(axes[0])

    power_window = coupling * times <= 3.0
    for case in cases:
        axes[1].plot(
            coupling * times[power_window],
            powers[case][power_window],
            color=COLORS[case],
            linestyle=LINESTYLES[case],
            linewidth=3.0,
        )
    axes[1].set_yscale("log")
    axes[1].set_xlim(0.0, 3.0)
    axes[1].set_ylim(1e-10, 1e-2)
    axes[1].set_xlabel(r"$Jt$", fontsize=14)
    axes[1].set_ylabel(r"$P_i/\omega_b$", fontsize=14)
    axes[1].text(-0.18, 1.02, "(b)", transform=axes[1].transAxes, fontsize=20)
    _paper_axes(axes[1])
    fig.subplots_adjust(left=0.09, right=0.985, top=0.94, bottom=0.18, wspace=0.30)
    figure_path = WORKSPACE / "outputs" / "figures" / "fig2ab_dynamics.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    author_energy = loadmat(_case_input(str(config["author_energy_path"])))
    author_power = loadmat(_case_input(str(config["author_power_path"])))
    author_times = np.asarray(author_energy["tlist"], dtype=float).ravel()
    author_gamma = float(np.asarray(author_energy["Gamma"]).item())
    author_kappa_a = float(np.asarray(author_energy["Lambda_a"]).item()) - author_gamma
    author_kappa_b = float(np.asarray(author_energy["Lambda_b"]).item()) - author_gamma
    author_coupling = float(np.asarray(author_energy["J"]).item())
    author_drive = float(np.asarray(author_energy["epsilon"]).item())
    author_squeezing = float(np.asarray(author_energy["r"]).item())
    author_generated = {
        "baseline": gaussian_battery_energy_dynamics(
            "baseline",
            author_times,
            author_coupling,
            author_kappa_a,
            author_kappa_b,
            author_drive,
            author_squeezing,
            0.0,
        )
    }
    author_generated["a"] = closed_charger_squeezed_energy_dynamics(
        author_times,
        author_coupling,
        author_gamma + author_kappa_a,
        author_gamma + author_kappa_b,
        author_drive,
        author_squeezing,
    )
    author_generated["b"] = gaussian_battery_energy_dynamics(
        "b",
        author_times,
        author_coupling,
        author_kappa_a,
        author_kappa_b,
        author_drive,
        author_squeezing,
        0.0,
    )
    author_generated["c"] = np.maximum(
        author_generated["a"]
        + author_generated["b"]
        - author_generated["baseline"],
        0.0,
    )
    author_energy_keys = {
        "baseline": "E_b4",
        "a": "E_b1",
        "b": "E_b2",
        "c": "E_b3",
    }
    author_power_keys = {
        "baseline": "P_b4",
        "a": "P_b1",
        "b": "P_b2",
        "c": "P_b3",
    }
    energy_errors = {
        case: float(
            np.max(
                np.abs(
                    author_generated[case]
                    - np.asarray(author_energy[key], dtype=float).ravel()
                )
            )
        )
        for case, key in author_energy_keys.items()
    }
    author_generated_power = {
        case: np.divide(
            values,
            author_times,
            out=np.full_like(values, np.nan),
            where=author_times > 0.0,
        )
        for case, values in author_generated.items()
    }
    power_errors = {}
    for case, key in author_power_keys.items():
        reference = np.asarray(author_power[key], dtype=float).ravel()
        valid = np.isfinite(reference) & np.isfinite(author_generated_power[case])
        power_errors[case] = float(
            np.max(np.abs(author_generated_power[case][valid] - reference[valid]))
        )
    author_dynamic_identity_error = float(
        np.max(
            np.abs(
                np.asarray(author_energy["E_b1"], dtype=float).ravel()
                + np.asarray(author_energy["E_b2"], dtype=float).ravel()
                - np.asarray(author_energy["E_b4"], dtype=float).ravel()
                - np.asarray(author_energy["E_b3"], dtype=float).ravel()
            )
        )
    )

    steady_reference = {
        "baseline": float(steady_state_energy_nonsqueezed(coupling, kappa, drive)),
        **{
            case: float(steady_state_energy(case, coupling, squeezing, kappa, drive))
            for case in ("a", "b", "c")
        },
    }
    steady_relative_errors = {
        case: float(abs(energies[case][-1] - expected) / max(abs(expected), 1e-15))
        for case, expected in steady_reference.items()
    }
    first_step = float(times[1] - times[0])
    expected_initial_slope = 2.0 * coupling * np.sinh(squeezing) ** 2
    initial_slopes = {
        case: float((energies[case][1] - energies[case][0]) / first_step)
        for case in ("b", "c")
    }
    initial_slope_relative_errors = {
        case: float(abs(value - expected_initial_slope) / expected_initial_slope)
        for case, value in initial_slopes.items()
    }
    passed = (
        max(energy_errors.values()) < 3e-4
        and max(power_errors.values()) < 4e-6
        and max(steady_relative_errors.values()) < 2e-3
        and max(initial_slope_relative_errors.values()) < 5e-3
    )
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "author_data",
        "metrics": {
            "author_energy_max_abs_error": energy_errors,
            "author_power_max_abs_error": power_errors,
            "steady_state_relative_error": steady_relative_errors,
            "initial_slope_expected": float(expected_initial_slope),
            "initial_slope_observed": initial_slopes,
            "initial_slope_relative_error": initial_slope_relative_errors,
            "author_dynamic_superposition_max_abs_residual": (
                author_dynamic_identity_error
            ),
            "time_points": int(times.size),
            "closed_form_kappa_b_offset": kappa_b_offset,
            "author_kappa_regularizer": {
                "kappa_a": author_kappa_a,
                "kappa_b": author_kappa_b,
            },
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "author_energy": str(config["author_energy_path"]),
            "author_power": str(config["author_power_path"]),
        },
    }


def run_t002d(config: dict[str, Any]) -> dict[str, Any]:
    coupling = float(config["coupling"])
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    squeezing = np.linspace(
        float(config["squeezing_min"]),
        float(config["squeezing_max"]),
        int(config["points"]),
    )
    baseline = float(steady_state_energy_nonsqueezed(coupling, kappa, drive))
    ergotropy = {
        case: steady_state_ergotropy(case, coupling, squeezing, kappa, drive)
        for case in ("a", "b", "c")
    }
    enhancements = {case: values / baseline for case, values in ergotropy.items()}
    passive = {
        case: passive_state_energy(case, coupling, squeezing, kappa, drive)
        for case in ("a", "b", "c")
    }

    data_path = WORKSPACE / "outputs" / "data" / "fig2d_ergotropy.csv"
    _write_csv(
        data_path,
        ["r", "ergotropy_a_over_E0", "ergotropy_b_over_E0", "ergotropy_c_over_E0"],
        [
            (
                float(value),
                float(enhancements["a"][index]),
                float(enhancements["b"][index]),
                float(enhancements["c"][index]),
            )
            for index, value in enumerate(squeezing)
        ],
    )

    fig, ax = plt.subplots(figsize=(5.14, 3.95), dpi=200)
    for case in ("a", "b", "c"):
        ax.plot(
            squeezing,
            enhancements[case],
            color=COLORS[case],
            linestyle=LINESTYLES[case],
            linewidth=3.0,
        )
    ax.set_yscale("log")
    ax.set_xlim(0.0, 2.0)
    ax.set_ylim(0.75, 420.0)
    ax.set_xlabel(r"$r$", fontsize=14)
    ax.set_ylabel(r"$\mathcal{E}_i^{\rm ss}/\mathcal{E}^{\rm ss}$", fontsize=14)
    ax.text(-0.18, 1.02, "(d)", transform=ax.transAxes, fontsize=20)
    _paper_axes(ax)
    fig.subplots_adjust(left=0.21, right=0.97, top=0.94, bottom=0.19)
    figure_path = WORKSPACE / "outputs" / "figures" / "fig2d_ergotropy.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    author = loadmat(_case_input(str(config["author_data_path"])))
    author_keys = {"a": "eta1", "b": "eta2", "c": "eta3"}
    author_errors = {}
    for case, key in author_keys.items():
        reference = np.real(np.asarray(author[key]).ravel())
        author_errors[case] = float(np.max(np.abs(enhancements[case] - reference)))
    invariant_min = {
        case: float(np.min(gaussian_invariant(case, coupling, squeezing, kappa, drive)))
        for case in ("a", "b", "c")
    }
    passive_margin = {
        case: float(
            np.min(
                steady_state_energy(case, coupling, squeezing, kappa, drive)
                - passive[case]
            )
        )
        for case in ("a", "b", "c")
    }
    endpoint_order = enhancements["b"][-1] > enhancements["c"][-1] > enhancements["a"][-1]
    passed = (
        max(author_errors.values()) < 5e-9
        and min(invariant_min.values()) >= 1.0 - 1e-10
        and min(passive_margin.values()) >= -1e-11
        and bool(endpoint_order)
    )
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "author_data",
        "metrics": {
            "author_data_max_abs_error": author_errors,
            "gaussian_invariant_minimum": invariant_min,
            "ergotropy_minimum": passive_margin,
            "endpoint_order_b_gt_c_gt_a": bool(endpoint_order),
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "author_data": str(config["author_data_path"]),
        },
    }


def run_ts01(config: dict[str, Any]) -> dict[str, Any]:
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    squeezing = float(config["squeezing"])
    charger_phase = float(config["charger_phase"])
    reservoir_phase = float(config["reservoir_phase"])
    scaled_time = np.linspace(
        float(config["scaled_time_min"]),
        float(config["scaled_time_max"]),
        int(config["time_points"]),
    )
    normalized_detuning = np.linspace(
        float(config["normalized_detuning_min"]),
        float(config["normalized_detuning_max"]),
        int(config["detuning_points"]),
    )
    coupling_values = [float(value) for value in config["coupling_values"]]
    panels: dict[str, np.ndarray] = {}
    for coupling_label, coupling in zip(
        ("weak", "strong"),
        coupling_values,
        strict=True,
    ):
        times = scaled_time / coupling
        for case in ("a", "c"):
            panels[f"{case}_{coupling_label}"] = np.vstack(
                [
                    gaussian_master_equation_energy_dynamics(
                        case,
                        times,
                        coupling,
                        kappa,
                        kappa,
                        drive,
                        squeezing,
                        detuning * coupling,
                        charger_phase,
                        reservoir_phase,
                    )
                    for detuning in normalized_detuning
                ]
            )

    data_path = WORKSPACE / "outputs" / "data" / "figs1_detuned_dynamics.npz"
    np.savez_compressed(
        data_path,
        scaled_time=scaled_time,
        normalized_detuning=normalized_detuning,
        coupling_weak=coupling_values[0],
        coupling_strong=coupling_values[1],
        solver_backend="affine_gaussian_expm",
        **panels,
    )

    fig = plt.figure(figsize=(14.63, 12.745), dpi=200)
    plot_specs = [
        ("a_weak", "(a)"),
        ("c_weak", "(b)"),
        ("a_strong", "(c)"),
        ("c_strong", "(d)"),
    ]
    time_mesh, detuning_mesh = np.meshgrid(scaled_time, normalized_detuning)
    for index, (key, label) in enumerate(plot_specs, start=1):
        ax = fig.add_subplot(2, 2, index, projection="3d")
        ax.plot_surface(
            detuning_mesh,
            time_mesh,
            panels[key],
            cmap="inferno",
            linewidth=0,
            antialiased=True,
            rstride=2,
            cstride=2,
        )
        ax.set_xlim(normalized_detuning[-1], normalized_detuning[0])
        ax.set_ylim(scaled_time[0], scaled_time[-1])
        ax.set_xlabel(r"$\omega_s/J$", fontsize=11, labelpad=8)
        ax.set_ylabel(r"$Jt$", fontsize=11, labelpad=8)
        ax.set_zlabel(r"$E_i/\omega_b$", fontsize=11, labelpad=5)
        ax.view_init(elev=24, azim=-45)
        ax.text2D(0.01, 0.93, label, transform=ax.transAxes, fontsize=20)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.99, bottom=0.02, wspace=0.02, hspace=0.08)
    figure_path = WORKSPACE / "outputs" / "figures" / "figs1_detuned_dynamics.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    weak_tolerance = float(config["weak_resonance_relative_tolerance"])
    strong_min_detuning = float(
        config["strong_min_abs_normalized_detuning"]
    )
    strong_gain_minimum = float(
        config["strong_detuning_relative_gain_minimum"]
    )
    symmetry_tolerance = float(
        config["detuning_symmetry_abs_tolerance"]
    )
    nonnegative_tolerance = float(
        config["energy_nonnegative_abs_tolerance"]
    )
    assessment = assess_ts01_detuning_regime(
        panels,
        normalized_detuning,
        weak_relative_tolerance=weak_tolerance,
        strong_min_abs_normalized_detuning=strong_min_detuning,
        strong_relative_gain_minimum=strong_gain_minimum,
        symmetry_abs_tolerance=symmetry_tolerance,
        nonnegative_abs_tolerance=nonnegative_tolerance,
    )
    finite_surface_path = CASE_PATH / str(
        config["finite_surface_probe_check_path"]
    )
    truncation_path = CASE_PATH / str(config["truncation_probe_check_path"])
    finite_surface_probe = json.loads(
        finite_surface_path.read_text(encoding="utf-8")
    )
    truncation_probe = json.loads(truncation_path.read_text(encoding="utf-8"))
    source_visual_peak_upper_bound = float(
        config["source_visual_c_strong_peak_upper_bound"]
    )
    truncation_assessment = assess_ts01_truncation_discrepancy(
        panels,
        finite_surface_probe,
        truncation_probe,
        paper_cutoff_disclosed=bool(config["paper_fock_cutoff_disclosed"]),
        source_visual_peak_upper_bound=source_visual_peak_upper_bound,
    )
    passed = assessment.passed and truncation_assessment.passed
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "visual_feature_contract",
        "scientific_verdict": (
            "reproduced_with_unconverged_fock_truncation_discrepancy"
            if passed
            else "unresolved"
        ),
        "metrics": {
            "solver_backend": "affine_gaussian_expm",
            **assessment.as_metrics(
                weak_relative_tolerance=weak_tolerance,
                strong_min_abs_normalized_detuning=strong_min_detuning,
                strong_relative_gain_minimum=strong_gain_minimum,
                symmetry_abs_tolerance=symmetry_tolerance,
            ),
            **truncation_assessment.as_metrics(
                source_visual_peak_upper_bound=(
                    source_visual_peak_upper_bound
                )
            ),
            "grid_shape": [int(normalized_detuning.size), int(scaled_time.size)],
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "source_figure": _source_figure_artifact("figs1.png"),
            "finite_surface_probe": str(finite_surface_path.relative_to(CASE_PATH)),
            "truncation_probe": str(truncation_path.relative_to(CASE_PATH)),
        },
    }


def run_ts01_finite_surface_probe(
    config: dict[str, Any],
) -> dict[str, Any]:
    normalized_detuning = np.asarray(
        config["surface_probe_normalized_detunings"],
        dtype=float,
    )
    coupling_values = [float(value) for value in config["coupling_values"]]
    panel_cases_and_couplings = {
        "a_weak": ("a", coupling_values[0]),
        "c_weak": ("c", coupling_values[0]),
        "a_strong": ("a", coupling_values[1]),
        "c_strong": ("c", coupling_values[1]),
    }
    finite_grid = simulate_finite_hilbert_grid(
        panel_cases_and_couplings=panel_cases_and_couplings,
        normalized_detunings=normalized_detuning,
        cutoff=int(config["surface_probe_fock_cutoff"]),
        kappa=float(config["kappa"]),
        drive=float(config["drive"]),
        squeezing=float(config["squeezing"]),
        charger_phase=float(config["charger_phase"]),
        reservoir_phase=float(config["reservoir_phase"]),
        scaled_time_min=float(config["scaled_time_min"]),
        scaled_time_max=float(config["scaled_time_max"]),
        time_points=int(config["time_points"]),
        max_workers=int(config.get("surface_probe_workers", 1)),
    )
    peak_detunings = {}
    if finite_grid.numerical_status == "valid":
        for key, values in finite_grid.panels.items():
            peak_by_detuning = np.max(values, axis=1)
            peak_detunings[key] = float(
                normalized_detuning[int(np.argmax(peak_by_detuning))]
            )
    weak_resonant = bool(
        peak_detunings
        and all(
            abs(peak_detunings[key]) <= 0.5
            for key in ("a_weak", "c_weak")
        )
    )
    strong_detuned = bool(
        peak_detunings
        and all(
            abs(peak_detunings[key]) >= 0.75
            for key in ("a_strong", "c_strong")
        )
    )
    return {
        "schema_version": 1,
        "status": (
            "completed"
            if finite_grid.numerical_status == "valid"
            else "invalid"
        ),
        "probe_role": "finite_truncation_sensitivity_smoke_test",
        "paper_id": CASE_PATH.name,
        "target_id": "TS01",
        "artifact_stage": "exploratory",
        "solver_backend": "scipy_sparse_expm",
        "fock_cutoff": finite_grid.cutoff,
        "worker_count": finite_grid.worker_count,
        "normalized_detunings": normalized_detuning.tolist(),
        "time_points": int(config["time_points"]),
        "panel_numerical_diagnostics": finite_grid.panel_diagnostics,
        "feature_contract": {
            "peak_normalized_detuning": peak_detunings,
            "weak_coupling_resonance_is_optimal": weak_resonant,
            "strong_coupling_has_finite_optimal_detuning": strong_detuned,
            "assessment": (
                "supported"
                if weak_resonant and strong_detuned
                else "rejected"
            ),
        },
    }


def run_ts02(config: dict[str, Any]) -> dict[str, Any]:
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    coupling = np.linspace(
        float(config["coupling_min"]),
        float(config["coupling_max"]),
        int(config["coupling_points"]),
    )
    squeezing = np.linspace(
        float(config["squeezing_min"]),
        float(config["squeezing_max"]),
        int(config["squeezing_points"]),
    )
    coupling_mesh, squeezing_mesh = np.meshgrid(coupling, squeezing)
    derivatives = {
        case: steady_state_energy_derivative(
            case, coupling_mesh, squeezing_mesh, kappa, drive
        )
        for case in ("a", "b", "c")
    }
    data_path = WORKSPACE / "outputs" / "data" / "figs2_energy_derivatives.npz"
    np.savez_compressed(
        data_path,
        coupling=coupling,
        squeezing=squeezing,
        derivative_a=derivatives["a"],
        derivative_b=derivatives["b"],
        derivative_c=derivatives["c"],
    )

    fig, axes = plt.subplots(1, 3, figsize=(16.225, 4.335), dpi=200)
    scale = max(float(np.percentile(np.abs(value), 98.0)) for value in derivatives.values())
    for index, case in enumerate(("a", "b", "c")):
        ax = axes[index]
        image = ax.pcolormesh(
            coupling,
            squeezing,
            derivatives[case],
            shading="auto",
            cmap="bwr",
            vmin=-scale,
            vmax=scale,
        )
        ax.contour(
            coupling,
            squeezing,
            derivatives[case],
            levels=[0.0],
            colors="black",
            linewidths=1.6,
        )
        ax.set_xlim(0.0, float(config["coupling_max"]))
        ax.set_ylim(0.0, 2.0)
        ax.set_xlabel(r"$J/\omega_b$", fontsize=13)
        ax.set_ylabel(r"$r$", fontsize=13)
        ax.text(0.87, 0.08, f"({chr(97 + index)})", transform=ax.transAxes, fontsize=16)
        _paper_axes(ax)
        fig.colorbar(image, ax=ax, pad=0.04)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.96, bottom=0.18, wspace=0.30)
    figure_path = WORKSPACE / "outputs" / "figures" / "figs2_energy_derivatives.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    test_coupling = np.geomspace(2e-6, 4e-4, 41)
    test_squeezing = np.linspace(0.05, 1.95, 39)
    test_j, test_r = np.meshgrid(test_coupling, test_squeezing)
    step = np.maximum(test_j * 1e-5, 1e-11)
    finite_difference_errors = {}
    for case in ("a", "b", "c"):
        numerical = (
            steady_state_energy(case, test_j + step, test_r, kappa, drive)
            - steady_state_energy(case, test_j - step, test_r, kappa, drive)
        ) / (2.0 * step)
        analytic = steady_state_energy_derivative(case, test_j, test_r, kappa, drive)
        finite_difference_errors[case] = float(
            np.max(np.abs(numerical - analytic) / np.maximum(1.0, np.abs(analytic)))
        )
    thresholds = {
        case: _global_threshold(case, coupling, kappa, drive)
        for case in ("b", "c")
    }
    sign_coverage = {
        case: {
            "positive": bool(np.any(values > 0.0)),
            "negative": bool(np.any(values < 0.0)),
        }
        for case, values in derivatives.items()
    }
    passed = (
        max(finite_difference_errors.values()) < 2e-7
        and all(row["positive"] and row["negative"] for row in sign_coverage.values())
        and thresholds["b"] < thresholds["c"]
    )
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "metrics": {
            "finite_difference_scaled_max_error": finite_difference_errors,
            "threshold_r_b": thresholds["b"],
            "threshold_r_c": thresholds["c"],
            "sign_coverage": sign_coverage,
            "grid_shape": [int(squeezing.size), int(coupling.size)],
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "source_figure": _source_figure_artifact("figs2.png"),
        },
    }


def run_ts03(config: dict[str, Any]) -> dict[str, Any]:
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    coupling_values = [float(value) for value in config["coupling_values"]]
    squeezing = np.linspace(
        float(config["squeezing_min"]),
        float(config["squeezing_max"]),
        int(config["points"]),
    )
    energies = {
        f"{case}_{index}": steady_state_energy(
            case, coupling, squeezing, kappa, drive
        )
        for index, coupling in enumerate(coupling_values)
        for case in ("a", "b", "c")
    }
    data_path = WORKSPACE / "outputs" / "data" / "figs3_energy_vs_squeezing.npz"
    np.savez_compressed(
        data_path,
        squeezing=squeezing,
        coupling_values=np.asarray(coupling_values),
        **energies,
    )

    fig, axes = plt.subplots(1, 3, figsize=(16.115, 4.345), dpi=200)
    for index, coupling in enumerate(coupling_values):
        ax = axes[index]
        for case in ("a", "b", "c"):
            ax.plot(
                squeezing,
                energies[f"{case}_{index}"],
                color=COLORS[case],
                linestyle=LINESTYLES[case],
                linewidth=3.0,
            )
        if index == 2:
            ax.set_yscale("log")
        ax.set_xlim(0.0, 2.0)
        ax.set_xlabel(r"$r$", fontsize=14)
        ax.set_ylabel(r"$E_i^{\rm ss}/\omega_b$", fontsize=14)
        ax.text(0.03, 0.90, f"({chr(97 + index)})", transform=ax.transAxes, fontsize=18)
        _paper_axes(ax)
    fig.subplots_adjust(left=0.06, right=0.985, top=0.95, bottom=0.18, wspace=0.26)
    figure_path = WORKSPACE / "outputs" / "figures" / "figs3_energy_vs_squeezing.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    monotonic_min_steps = {
        key: float(np.min(np.diff(values)))
        for key, values in energies.items()
    }
    identity_errors = {}
    for index, coupling in enumerate(coupling_values):
        baseline = steady_state_energy_nonsqueezed(coupling, kappa, drive)
        identity_errors[str(index)] = float(
            np.max(
                np.abs(
                    energies[f"a_{index}"]
                    + energies[f"b_{index}"]
                    - baseline
                    - energies[f"c_{index}"]
                )
            )
        )
    endpoint_orders = {
        str(index): bool(
            energies[f"c_{index}"][-1]
            > energies[f"b_{index}"][-1]
            > energies[f"a_{index}"][-1]
        )
        for index in range(len(coupling_values))
    }
    passed = (
        min(monotonic_min_steps.values()) >= -1e-12
        and max(identity_errors.values()) < 2e-12
        and all(endpoint_orders.values())
    )
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "metrics": {
            "minimum_forward_difference": monotonic_min_steps,
            "steady_energy_identity_max_abs_error": identity_errors,
            "endpoint_order_c_gt_b_gt_a": endpoint_orders,
            "points_per_curve": int(squeezing.size),
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "source_figure": _source_figure_artifact("figs3.png"),
        },
    }


def run_ts04(config: dict[str, Any]) -> dict[str, Any]:
    kappa = float(config["kappa"])
    drive = float(config["drive"])
    fixed_coupling = float(config["fixed_coupling"])
    fixed_squeezing = float(config["fixed_squeezing"])
    coupling = np.linspace(
        float(config["coupling_min"]),
        float(config["coupling_max"]),
        int(config["coupling_points"]),
    )
    squeezing = np.linspace(
        float(config["squeezing_min"]),
        float(config["squeezing_max"]),
        int(config["squeezing_points"]),
    )
    coupling_curves = {
        case: passive_state_energy(case, coupling, fixed_squeezing, kappa, drive)
        for case in ("a", "b", "c")
    }
    squeezing_curves = {
        case: passive_state_energy(case, fixed_coupling, squeezing, kappa, drive)
        for case in ("a", "b", "c")
    }
    data_path = WORKSPACE / "outputs" / "data" / "figs4_passive_energy.npz"
    np.savez_compressed(
        data_path,
        coupling=coupling,
        squeezing=squeezing,
        coupling_a=coupling_curves["a"],
        coupling_b=coupling_curves["b"],
        coupling_c=coupling_curves["c"],
        squeezing_a=squeezing_curves["a"],
        squeezing_b=squeezing_curves["b"],
        squeezing_c=squeezing_curves["c"],
    )

    fig, axes = plt.subplots(1, 2, figsize=(10.745, 4.715), dpi=200)
    for case in ("a", "b", "c"):
        axes[0].plot(
            coupling,
            coupling_curves[case],
            color=COLORS[case],
            linestyle=LINESTYLES[case],
            linewidth=3.0,
        )
        axes[1].plot(
            squeezing,
            squeezing_curves[case],
            color=COLORS[case],
            linestyle=LINESTYLES[case],
            linewidth=3.0,
        )
    axes[0].set_xlim(0.0, 0.002)
    axes[0].set_xlabel(r"$J/\omega_b$", fontsize=14)
    axes[0].set_ylabel(r"$\widetilde{E}_i^{\rm ss}/\omega_b$", fontsize=14)
    axes[0].text(-0.20, 1.02, "(a)", transform=axes[0].transAxes, fontsize=20)
    axes[1].set_xlim(0.0, 1.5)
    axes[1].set_xlabel(r"$r$", fontsize=14)
    axes[1].set_ylabel(r"$\widetilde{E}_i^{\rm ss}/\omega_b$", fontsize=14)
    axes[1].text(-0.20, 1.02, "(b)", transform=axes[1].transAxes, fontsize=20)
    for ax in axes:
        _paper_axes(ax)
    fig.subplots_adjust(left=0.10, right=0.98, top=0.94, bottom=0.18, wspace=0.30)
    figure_path = WORKSPACE / "outputs" / "figures" / "figs4_passive_energy.png"
    fig.savefig(figure_path, dpi=200, facecolor="white")
    plt.close(fig)

    interior_maxima = {
        case: int(np.argmax(values)) not in {0, values.size - 1}
        for case, values in coupling_curves.items()
    }
    monotonic_r = {
        case: float(np.min(np.diff(values)))
        for case, values in squeezing_curves.items()
    }
    passive_margins = {}
    for case in ("a", "b", "c"):
        total_j = steady_state_energy(case, coupling, fixed_squeezing, kappa, drive)
        total_r = steady_state_energy(case, fixed_coupling, squeezing, kappa, drive)
        passive_margins[case] = float(
            min(
                np.min(total_j - coupling_curves[case]),
                np.min(total_r - squeezing_curves[case]),
            )
        )
    passed = (
        all(interior_maxima.values())
        and min(monotonic_r.values()) >= -1e-12
        and min(passive_margins.values()) >= -1e-10
    )
    return {
        "status": "passed" if passed else "failed",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "analytic_reference",
        "reference_comparison": "analytic_reference",
        "metrics": {
            "coupling_curves_have_interior_maximum": interior_maxima,
            "squeezing_curve_minimum_forward_difference": monotonic_r,
            "ergotropy_nonnegative_margin": passive_margins,
        },
        "artifacts": {
            "data": str(data_path.relative_to(CASE_PATH)),
            "figure": str(figure_path.relative_to(CASE_PATH)),
            "source_figure": _source_figure_artifact("figs4.png"),
        },
    }


RUNNERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "T001": run_t001,
    "T002A": run_t002a,
    "T002C": run_t002c,
    "T002D": run_t002d,
    "T003": run_t003,
    "T004": run_t004,
    "TS01": run_ts01,
    "TS02": run_ts02,
    "TS03": run_ts03,
    "TS04": run_ts04,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_id", choices=sorted(RUNNERS))
    parser.add_argument(
        "--mode",
        choices=(
            "target",
            "truncation-probe",
            "finite-surface-probe",
        ),
        default="target",
    )
    parser.add_argument(
        "--probe-backend",
        choices=("scipy_sparse_expm", "torch_rk4"),
        default="scipy_sparse_expm",
    )
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    _ensure_outputs()
    config = _load_config(args.target_id)
    if args.mode == "truncation-probe":
        if args.target_id != "TS01":
            parser.error("truncation-probe mode is available only for TS01")
        from ts01_truncation_probe import run_truncation_probe

        result = run_truncation_probe(
            config,
            backend=args.probe_backend,
            device_name=args.device,
        )
        check_path = (
            WORKSPACE
            / "outputs"
            / "checks"
            / "ts01_truncation_probe.json"
        )
        check_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"check_path": str(check_path), **result}, indent=2))
        return 0 if result["status"] == "completed" else 1
    if args.mode == "finite-surface-probe":
        if args.target_id != "TS01":
            parser.error(
                "finite-surface-probe mode is available only for TS01"
            )
        result = run_ts01_finite_surface_probe(config)
        check_path = (
            WORKSPACE
            / "outputs"
            / "checks"
            / "ts01_finite_surface_probe.json"
        )
        check_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"check_path": str(check_path), **result}, indent=2))
        return 0 if result["status"] == "completed" else 1

    result = RUNNERS[args.target_id](config)
    check_path = _write_check(args.target_id, result)
    print(json.dumps({"check_path": str(check_path), **result}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
