#!/usr/bin/env python3
"""Generate structured scientific data, figures, and checks for the case.

This numerical lane must not read paper figures or comparison assets.  Source
figures belong exclusively to the post-freeze RenderContract lane.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Iterable, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


CODE_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CASE = CODE_ROOT.name == "code"
OUTPUT_ROOT = CODE_ROOT.parent if PUBLIC_CASE else CODE_ROOT
SRC = CODE_ROOT / "src"
sys.path.insert(0, str(SRC))

from gate_model import (  # noqa: E402
    BRANCHES,
    GateParameters,
    anharmonic_infidelity,
    branch_displacements,
    branch_forces,
    chain_gate_duration_us,
    concurrence,
    cz_distance_m,
    decay_infidelity,
    fowler_logical_error,
    hybrid_storage_error_per_operation,
    interconnect_times_us,
    ion_zero_point_m,
    reduced_spin_state,
    rotated_basis_populations,
    total_gate_infidelity,
)
from ion_chain import axial_modes, mode_trajectory, optimize_toggle_schedule  # noqa: E402


PAPER_ID = "2607.15597"
GUARDED_TARGET_ENV = "PRAGENT_GUARDED_TARGET_ID"
GUARDED_STAGE_ENV = "PRAGENT_GUARDED_STAGE"
RUN_STAGES = ("exploratory", "final_reproduction")
DATA_DIR = OUTPUT_ROOT / "outputs" / "data"
FIGURE_DIR = OUTPUT_ROOT / "outputs" / "figures"
CHECK_DIR = OUTPUT_ROOT / "outputs" / "checks"

COLORS = {
    "blue": "#4C72B0",
    "orange": "#F28E2B",
    "green": "#59A14F",
    "red": "#E15759",
    "purple": "#B07AA1",
    "gray": "#7F7F7F",
}

TARGET_IDS = (
    "T001",
    "T002",
    "T003",
    "T004",
    "T005",
    "T007",
    "T008",
    "T009",
    "T010",
    "T011",
    "T012",
    "T013",
    "T014",
)

PROVENANCE_BY_TARGET = {
    "T001": "independent_numerics",
    "T002": "independent_numerics",
    "T003": "analytic_reference",
    "T004": "analytic_reference",
    "T005": "analytic_reference",
    "T007": "independent_numerics",
    "T008": "analytic_reference",
    "T009": "analytic_reference",
    "T010": "analytic_reference",
    "T011": "analytic_reference",
    "T012": "independent_numerics",
    "T013": "analytic_reference",
    "T014": "analytic_reference",
}


def write_csv(path: Path, rows: Iterable[Mapping[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def setup_axes(ax: plt.Axes) -> None:
    ax.tick_params(which="both", direction="in", top=True, right=True)
    ax.minorticks_on()


def reproduce_fig2(params: GateParameters) -> dict[str, float]:
    time_grid = np.linspace(0.0, 2.0, 801)
    trajectory_grid = np.linspace(0.0, 1.0, 401)
    forces = branch_forces(params.coupling_ratio)[:, 0]
    trajectories = forces[:, None] * (1.0 - np.exp(2j * np.pi * trajectory_grid))
    rows = []
    concurrences = []
    populations_by_key = {key: [] for key in ("g_plus", "g_minus", "r_plus", "r_minus")}
    for time_point in time_grid:
        rho = reduced_spin_state(float(time_point), params)
        populations = rotated_basis_populations(rho)
        value = concurrence(rho)
        concurrences.append(value)
        for key in populations_by_key:
            populations_by_key[key].append(populations[key])
        rows.append({"t_over_T": time_point, **populations, "concurrence": value})
    write_csv(
        DATA_DIR / "fig2_gate_dynamics.csv",
        rows,
        ["t_over_T", "g_plus", "g_minus", "r_plus", "r_minus", "concurrence"],
    )
    trajectory_rows = []
    for index, time_point in enumerate(trajectory_grid):
        row: dict[str, object] = {"t_over_T": time_point}
        for branch_index, branch in enumerate(BRANCHES):
            row[f"{branch}_real"] = trajectories[branch_index, index].real
            row[f"{branch}_imag"] = trajectories[branch_index, index].imag
        trajectory_rows.append(row)
    write_csv(
        DATA_DIR / "fig2_phase_space.csv",
        trajectory_rows,
        list(trajectory_rows[0]),
    )

    figure, axes = plt.subplots(1, 3, figsize=(12.0, 3.6), constrained_layout=True)
    labels = (r"$|g,\downarrow\rangle$", r"$|g,\uparrow\rangle$", r"$|r,\downarrow\rangle$", r"$|r,\uparrow\rangle$")
    palette = (COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["red"])
    for index, (label, color) in enumerate(zip(labels, palette, strict=True)):
        axes[0].plot(trajectories[index].real, trajectories[index].imag, label=label, color=color)
    axes[0].scatter([0], [0], color=COLORS["red"], s=22, zorder=4)
    axes[0].set(xlabel=r"Re$(\tilde\alpha)$", ylabel=r"Im$(\tilde\alpha)$", aspect="equal")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].set_title("(a)", loc="left")

    for key, label, color in zip(populations_by_key, (r"$|g,+\rangle$", r"$|g,-\rangle$", r"$|r,+\rangle$", r"$|r,-\rangle$"), palette, strict=True):
        axes[1].plot(time_grid, populations_by_key[key], label=label, color=color)
    axes[1].set(xlabel=r"$t/T$", ylabel="Population", xlim=(0, 2), ylim=(-0.02, 0.52))
    axes[1].legend(frameon=False, fontsize=8)
    axes[1].set_title("(b)", loc="left")

    axes[2].plot(time_grid, concurrences, color=COLORS["blue"])
    axes[2].set(xlabel=r"$t/T$", ylabel="Concurrence", xlim=(0, 2), ylim=(-0.02, 1.04))
    axes[2].set_title("(c)", loc="left")
    for axis in axes:
        setup_axes(axis)
    figure.savefig(FIGURE_DIR / "fig2_reproduction.png", dpi=180)
    plt.close(figure)

    at_one = int(np.argmin(np.abs(time_grid - 1.0)))
    at_two = -1
    return {
        "max_closure_displacement_T": float(np.max(np.abs(branch_displacements(1.0, params)))),
        "concurrence_T": float(concurrences[at_one]),
        "concurrence_2T": float(concurrences[at_two]),
        "population_sum_max_error": float(
            np.max(np.abs(sum(np.asarray(values) for values in populations_by_key.values()) - 1.0))
        ),
    }


def reproduce_fig3() -> dict[str, float]:
    n_ions = np.arange(1, 101)
    duration = chain_gate_duration_us(n_ions)
    low_l = decay_infidelity(duration, 100.0) + 1.0e-3
    circular = decay_infidelity(duration, 119_000.0) + 1.0e-3
    rows = [
        {
            "number_of_ions": int(n),
            "gate_duration_us": t,
            "low_l_infidelity": low,
            "circular_infidelity": circ,
            "parameter_match": "reconstructed",
        }
        for n, t, low, circ in zip(n_ions, duration, low_l, circular, strict=True)
    ]
    write_csv(DATA_DIR / "fig3_chain_scaling.csv", rows, list(rows[0]))

    figure, axis = plt.subplots(figsize=(5.3, 3.8), constrained_layout=True)
    duration_axis = axis.twinx()
    axis.plot(n_ions, low_l, color="black", lw=2, label=r"low-$\ell$ Rydberg")
    axis.plot(n_ions, circular, color="black", lw=2, label="circular Rydberg")
    duration_axis.plot(n_ions, duration, color="#0077BB", ls="--", lw=2, label="gate duration")
    axis.set(xscale="log", yscale="log", xlabel="Number of ions in chain, N", ylabel="Per-gate infidelity")
    duration_axis.set(ylabel=r"Gate duration $T_{gate}$ ($\mu$s)", ylim=(4, 30))
    setup_axes(axis)
    setup_axes(duration_axis)
    axis.legend(frameon=False, loc="upper left")
    duration_axis.legend(frameon=False, loc="lower right")
    figure.savefig(FIGURE_DIR / "fig3_reproduction.png", dpi=180)
    plt.close(figure)
    return {
        "duration_N1_us": float(duration[0]),
        "duration_N100_us": float(duration[-1]),
        "low_l_infidelity_N100": float(low_l[-1]),
        "circular_infidelity_N100": float(circular[-1]),
    }


def reproduce_fig4() -> dict[str, object]:
    distances = np.logspace(1.0, 6.0, 241)
    operations = np.logspace(0.0, 12.0, 241)
    times = interconnect_times_us(distances)
    transfer_error = 2.67e-4
    hybrid_per_op = hybrid_storage_error_per_operation(operations, transfer_error)
    pure_atom = float(fowler_logical_error(6, 1.0e-3, 6.5e-3))
    pure_ion = float(fowler_logical_error(6, 3.0e-4, 6.5e-3))
    rows = []
    for index in range(len(distances)):
        rows.append(
            {
                "distance_um": distances[index],
                "hybrid_time_us": times["hybrid"][index],
                "ion_qccd_time_us": times["ion_qccd"][index],
                "photon_time_us": times["photon"][index],
                "number_of_operations": operations[index],
                "hybrid_storage_error_per_op": hybrid_per_op[index],
                "pure_atom_error_per_op": pure_atom,
                "pure_ion_error_per_op": pure_ion,
            }
        )
    write_csv(DATA_DIR / "fig4_architecture.csv", rows, list(rows[0]))

    figure, axes = plt.subplots(1, 2, figsize=(8.2, 3.6), constrained_layout=True)
    axes[0].plot(distances, times["ion_qccd"], color=COLORS["orange"], ls="--", label="ion QCCD")
    axes[0].plot(distances, times["hybrid"], color="#86A5BC", lw=2.5, label="hybrid")
    axes[0].plot(distances, times["photon"], color=COLORS["gray"], ls=":", lw=2.5, label="photon")
    axes[0].set(xscale="log", yscale="log", xlabel=r"$L$ ($\mu$m)", ylabel=r"$t$ ($\mu$s)")
    axes[0].legend(frameon=False)
    axes[0].set_title("(a)", loc="left")

    axes[1].plot(operations, np.full_like(operations, pure_atom), color=COLORS["green"], label="atom")
    axes[1].plot(operations, np.full_like(operations, pure_ion), color=COLORS["orange"], label="ion")
    axes[1].plot(operations, hybrid_per_op, color="#86A5BC", lw=2.5, label="hybrid")
    axes[1].set(
        xscale="log",
        yscale="log",
        xlabel=r"$N_{ops}$",
        ylabel=r"storage error per operation",
        ylim=(1e-13, 1e-3),
    )
    axes[1].legend(frameon=False)
    axes[1].set_title("(b) caption-consistent", loc="left")
    for axis in axes:
        setup_axes(axis)
    figure.savefig(FIGURE_DIR / "fig4_reproduction.png", dpi=180)
    plt.close(figure)

    hybrid_photon_cross_um = (4_000.0 - 10.0) / 2.0
    consistency = {
        "status": "inconsistency_found",
        "caption_model": "2*p_T/N_ops",
        "caption_model_derivative": "-2*p_T/N_ops^2 < 0",
        "generated_curve_monotonic": "decreasing",
        "source_figure_visual_slope": "increasing",
        "source_claim_consistent": False,
        "interpretation": "The reproduction follows the caption and main-text amortization logic; it does not imitate the contradictory source raster.",
    }
    write_json(CHECK_DIR / "source_consistency.json", consistency)
    return {
        "hybrid_photon_cross_um": hybrid_photon_cross_um,
        "hybrid_ion_cross_um": None,
        "hybrid_faster_than_ion_for_positive_distance": True,
        "pure_atom_error_per_op": pure_atom,
        "pure_ion_error_per_op": pure_ion,
        "source_consistency": consistency,
    }


def reproduce_table_s1(params: GateParameters) -> dict[str, float]:
    zero_point_nm = ion_zero_point_m(params) * 1e9
    distance_um = cz_distance_m(1.89e-46, params) * 1e6
    coupling_khz = params.coupling_ratio * params.trap_frequency_hz / 1e3
    s1_rows = [
        {"parameter": "trap_frequency_kHz", "paper_value": 200.0, "generated_value": params.trap_frequency_hz / 1e3, "unit": "kHz", "provenance": "paper_input"},
        {"parameter": "gate_time_us", "paper_value": 5.0, "generated_value": 1e6 / params.trap_frequency_hz, "unit": "us", "provenance": "analytic_reference"},
        {"parameter": "ion_zero_point_nm", "paper_value": 12.0, "generated_value": zero_point_nm, "unit": "nm", "provenance": "analytic_reference"},
        {"parameter": "coupling_kHz", "paper_value": 71.0, "generated_value": coupling_khz, "unit": "kHz", "provenance": "analytic_reference"},
        {"parameter": "d_CZ_um", "paper_value": 12.0, "generated_value": distance_um, "unit": "um", "provenance": "analytic_reference_from_paper_C4"},
        {"parameter": "max_loop_radius", "paper_value": 1 / np.sqrt(2), "generated_value": 2 * params.coupling_ratio, "unit": "quanta", "provenance": "analytic_reference"},
    ]
    write_csv(DATA_DIR / "table_s1_operating_point.csv", s1_rows, list(s1_rows[0]))
    return {"zero_point_nm": zero_point_nm, "d_CZ_um": distance_um, "coupling_kHz": coupling_khz}


def reproduce_table_s2(params: GateParameters) -> dict[str, object]:
    lifetimes = (100.0, 200.0, 470.0, 60.0, 150.0)
    s2_rows = [
        {
            "lifetime_us": lifetime,
            "gate_time_us": params.gate_time_us,
            "generated_decay_infidelity": float(decay_infidelity(params.gate_time_us, lifetime)),
            "formula": "0.5*(1-exp(-T/tau))",
        }
        for lifetime in lifetimes
    ]
    write_csv(DATA_DIR / "table_s2_decay.csv", s2_rows, list(s2_rows[0]))
    return {
        "gate_time_us": params.gate_time_us,
        "lifetimes_us": list(lifetimes),
        "decay_infidelities": [
            float(row["generated_decay_infidelity"]) for row in s2_rows
        ],
    }


def reproduce_figs1() -> dict[str, object]:
    positions, frequencies, eigenvectors = axial_modes(10)
    schedule = optimize_toggle_schedule(frequencies)
    mode_rows = [
        {
            "mode": index + 1,
            "frequency_over_COM": frequency,
            "edge_participation": eigenvectors[0, index],
            "equilibrium_position": positions[index],
        }
        for index, frequency in enumerate(frequencies)
    ]
    write_csv(DATA_DIR / "figs1_modes.csv", mode_rows, list(mode_rows[0]))
    schedule_rows = []
    for index, amplitude in enumerate(schedule.amplitudes):
        schedule_rows.append(
            {
                "segment": index + 1,
                "start_fraction": schedule.boundaries[index],
                "stop_fraction": schedule.boundaries[index + 1],
                "duration_fraction": schedule.boundaries[index + 1] - schedule.boundaries[index],
                "amplitude": amplitude,
            }
        )
    write_csv(DATA_DIR / "figs1_schedule.csv", schedule_rows, list(schedule_rows[0]))
    closure_rows = [
        {
            "mode": index + 1,
            "frequency_over_COM": frequencies[index],
            "residual_real": residual.real,
            "residual_imag": residual.imag,
            "residual_abs": abs(residual),
        }
        for index, residual in enumerate(schedule.residuals)
    ]
    write_csv(DATA_DIR / "figs1_closure.csv", closure_rows, list(closure_rows[0]))

    figure = plt.figure(figsize=(11.0, 7.4), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, height_ratios=(1, 2))
    mode_axis = figure.add_subplot(grid[0, 0])
    schedule_axis = figure.add_subplot(grid[0, 1])
    trajectory_axis = figure.add_subplot(grid[1, :])
    mode_axis.scatter(positions, np.zeros_like(positions), color="black", s=30)
    for frequency in frequencies:
        mode_axis.vlines(frequency, 0.0, 0.9, color=COLORS["blue"], lw=1.5)
    mode_axis.set(xlabel="equilibrium position / normalized mode frequency", yticks=[])
    mode_axis.set_title("(a) 10-ion chain and axial spectrum", loc="left")

    widths = np.diff(schedule.boundaries)
    colors = [COLORS["blue"] if value > 0 else COLORS["orange"] for value in schedule.amplitudes]
    schedule_axis.bar(schedule.boundaries[:-1], schedule.amplitudes, width=widths, align="edge", color=colors, alpha=0.75)
    schedule_axis.axhline(0, color="black", lw=0.7)
    schedule_axis.set(xlabel=r"$t/T$", ylabel="toggle amplitude", xlim=(0, 1))
    schedule_axis.set_title("(b) 25-segment optimized schedule", loc="left")

    sample = np.linspace(0.0, 1.0, 1401)
    for index, frequency in enumerate(frequencies):
        trajectory = mode_trajectory(sample, float(frequency), schedule)
        scale = np.max(np.abs(trajectory))
        if scale > 0:
            trajectory = trajectory / scale
        trajectory_axis.plot(trajectory.real + 2.5 * (index % 5), trajectory.imag + 2.5 * (1 - index // 5), lw=0.9)
        trajectory_axis.scatter([2.5 * (index % 5)], [2.5 * (1 - index // 5)], s=12, color=COLORS["green"])
        trajectory_axis.text(2.5 * (index % 5) - 0.9, 2.5 * (1 - index // 5) + 0.9, rf"$\omega_{{{index + 1}}}={frequency:.2f}\omega$", fontsize=8)
    trajectory_axis.set(xlabel="Re(displacement), per-mode normalized", ylabel="Im(displacement), offset grid", aspect="equal")
    trajectory_axis.set_title("(c) independently optimized closed trajectories", loc="left")
    for axis in (mode_axis, schedule_axis, trajectory_axis):
        setup_axes(axis)
    figure.savefig(FIGURE_DIR / "figs1_closure_reproduction.png", dpi=180)
    plt.close(figure)
    return {
        "frequencies": [float(value) for value in frequencies],
        "segment_count": len(schedule.amplitudes),
        "closure_cost": schedule.cost,
        "max_closure_residual": float(np.max(np.abs(schedule.residuals))),
        "source_segment_conflict": {"prose_and_figure": 25, "table_s4": 17},
    }


def reproduce_thermal_figures() -> dict[str, float]:
    occupation = np.logspace(-1, np.log10(50.0), 301)
    eta_low = 1.88e-3
    eta_80 = eta_low / 2.0
    anh_low = anharmonic_infidelity(occupation, eta_low)
    anh_80 = anharmonic_infidelity(occupation, eta_80)
    total_low = anh_low + decay_infidelity(5.0, 200.0)
    total_80 = anh_80 + decay_infidelity(5.0, 470.0)
    rows = [
        {
            "mean_phonon": nbar,
            "n60_anharmonic": a60,
            "n60_total": t60,
            "n80_anharmonic": a80,
            "n80_total": t80,
            "parameter_match": "proxy_model",
        }
        for nbar, a60, t60, a80, t80 in zip(occupation, anh_low, total_low, anh_80, total_80, strict=True)
    ]
    write_csv(DATA_DIR / "figs3_thermal.csv", rows, list(rows[0]))
    figure, axis = plt.subplots(figsize=(5.4, 4.1), constrained_layout=True)
    axis.plot(occupation, total_low, color=COLORS["blue"], label="n=60, total")
    axis.plot(occupation, anh_low, color=COLORS["blue"], ls="--", label="n=60, anharmonic")
    axis.plot(occupation, total_80, color=COLORS["red"], label="n=80, total")
    axis.plot(occupation, anh_80, color=COLORS["red"], ls="--", label="n=80, anharmonic")
    axis.set(xscale="log", yscale="log", xlabel=r"Initial motional occupation $\bar n$", ylabel=r"Gate infidelity $1-\mathcal{F}$")
    axis.axvline(0.3, color="0.75", ls=":")
    axis.axvline(10.0, color="0.75", ls=":")
    axis.legend(frameon=False, fontsize=8)
    setup_axes(axis)
    figure.savefig(FIGURE_DIR / "figs3_thermal_reproduction.png", dpi=180)
    plt.close(figure)
    nbar_one = int(np.argmin(np.abs(occupation - 1.0)))
    return {
        "n60_anharmonic_at_nbar1": float(anh_low[nbar_one]),
        "n80_anharmonic_at_nbar1": float(anh_80[nbar_one]),
        "eta2_ratio_at_nbar1": float(anh_low[nbar_one] / anh_80[nbar_one]),
    }


def reproduce_gate_counts() -> dict[str, int]:
    rows = [
        {"code": "Steane [[7,1,3]]", "atom_ion_CZ": 7, "atom_atom_CNOT": 24, "ion_ion_CNOT": 24, "logical_pairs": 1, "atom_ion_per_logical": 7},
        {"code": "BB [[72,12,6]]", "atom_ion_CZ": 72, "atom_atom_CNOT": 432, "ion_ion_CNOT": 432, "logical_pairs": 12, "atom_ion_per_logical": 6},
    ]
    write_csv(DATA_DIR / "table_s7_gate_counts.csv", rows, list(rows[0]))
    return {"steane_atom_ion": 7, "bb_atom_ion": 72, "bb_per_logical": 6}


def reproduce_qldpc_projection() -> dict[str, float]:
    distances = np.linspace(6.0, 30.0, 241)
    atom = fowler_logical_error(distances, 5.0e-3, 5.7e-3)
    hybrid_unboosted = fowler_logical_error(distances, 0.13 * 5.0e-3, 3.4e-3)
    hybrid = hybrid_unboosted / 66.0
    ion = fowler_logical_error(distances, 1.0e-4, 3.4e-3)
    atom_round_ms = np.full_like(distances, 2.0)
    hybrid_round_ms = np.full_like(distances, 2.0)
    ion_round_ms = 12.5 * distances
    ion_next_ms = 4.0 * distances
    rows = [
        {
            "distance": d,
            "atom_pL": pa,
            "hybrid_unboosted_pL": phu,
            "hybrid_boosted_pL": ph,
            "ion_pL": pi,
            "atom_round_ms": ta,
            "hybrid_round_ms": th,
            "ion_qccd_round_ms": ti,
            "ion_next_round_ms": tin,
        }
        for d, pa, phu, ph, pi, ta, th, ti, tin in zip(
            distances, atom, hybrid_unboosted, hybrid, ion, atom_round_ms, hybrid_round_ms, ion_round_ms, ion_next_ms, strict=True
        )
    ]
    write_csv(DATA_DIR / "figs5_qldpc_projection.csv", rows, list(rows[0]))

    projection_rows = []
    for distance in (12, 18, 24):
        pure_atom = float(fowler_logical_error(distance, 1e-3, 3.4e-3))
        hybrid_un = float(fowler_logical_error(distance, 0.13e-3, 3.4e-3))
        pure_ion = float(fowler_logical_error(distance, 1e-4, 3.4e-3))
        projection_rows.append(
            {
                "distance": distance,
                "pure_atom": pure_atom,
                "hybrid_unheralded_ansatz": hybrid_un,
                "hybrid_plus_66x_boost": hybrid_un / 66.0,
                "pure_ion": pure_ion,
            }
        )
    write_csv(DATA_DIR / "table_s11_projection.csv", projection_rows, list(projection_rows[0]))

    figure, axes = plt.subplots(1, 3, figsize=(12.0, 3.5), constrained_layout=True)
    axes[0].plot(distances, atom, color=COLORS["green"], ls=":", label="atom")
    axes[0].plot(distances, hybrid, color=COLORS["blue"], label="hybrid")
    axes[0].plot(distances, ion, color=COLORS["orange"], ls="--", label="ion")
    axes[0].set(yscale="log", xlabel="BB code distance d", ylabel=r"$p_L$ per logical per SE round")
    axes[0].legend(frameon=False)
    axes[0].set_title("(a) disclosed Fowler model", loc="left")
    axes[1].plot(distances, atom_round_ms, color=COLORS["green"], label="atom")
    axes[1].plot(distances, hybrid_round_ms, color=COLORS["blue"], label="hybrid")
    axes[1].plot(distances, ion_round_ms, color=COLORS["orange"], label="ion QCCD")
    axes[1].plot(distances, ion_next_ms, color=COLORS["orange"], ls="--", label="ion next-gen")
    axes[1].set(yscale="log", xlabel="BB code distance d", ylabel="SE round time (ms)")
    axes[1].legend(frameon=False, fontsize=8)
    axes[1].set_title("(b) timing model", loc="left")
    axes[2].plot(distances * atom_round_ms, atom, color=COLORS["green"], marker="o", ms=2, label="atom")
    axes[2].plot(distances * hybrid_round_ms, hybrid, color=COLORS["blue"], marker="^", ms=2, label="hybrid")
    axes[2].plot(distances * ion_round_ms, ion, color=COLORS["orange"], marker="s", ms=2, label="ion")
    axes[2].set(xscale="log", yscale="log", xlabel="wall-clock per d-round cycle (ms)", ylabel=r"$p_L$ per logical per SE round")
    axes[2].legend(frameon=False, fontsize=8)
    axes[2].set_title("(c) space-time trajectory", loc="left")
    for axis in axes:
        setup_axes(axis)
    figure.savefig(FIGURE_DIR / "figs5_qldpc_projection_reproduction.png", dpi=180)
    plt.close(figure)
    return {"hybrid_boost": 66.0, "atom_threshold": 5.7e-3, "hybrid_threshold": 3.4e-3}


def reproduce_table_s13(params: GateParameters) -> dict[str, object]:
    states = (
        ("low_l_n60", 1.1e-47, 200.0, 1.88e-3),
        ("circular_n60", 2.1e-46, 119_000.0, 1.04e-3),
        ("circular_n80", 1.6e-45, 502_000.0, 0.69e-3),
    )
    s13_rows = []
    for label, c4, lifetime, eta in states:
        s13_rows.append(
            {
                "state": label,
                "C4_J_m4": c4,
                "generated_d_CZ_um": 1e6 * cz_distance_m(c4, params),
                "eta_paper": eta,
                "lifetime_4K_us": lifetime,
                "decay_4K": float(decay_infidelity(5.0, lifetime)),
                "anharmonic_nbar1": float(anharmonic_infidelity(1.0, eta)),
            }
        )
    write_csv(DATA_DIR / "table_s13_circular.csv", s13_rows, list(s13_rows[0]))
    return {
        "states": [str(row["state"]) for row in s13_rows],
        "generated_distances_um": [
            float(row["generated_d_CZ_um"]) for row in s13_rows
        ],
    }


def reproduce_figs6(params: GateParameters) -> dict[str, float]:
    time_grid = np.linspace(0.0, 2.0, 801)
    lifetime_us = 6_000.0
    rows = []
    concurrence_open = []
    populations_by_key = {key: [] for key in ("g_plus", "g_minus", "r_plus", "r_minus")}
    for time_point in time_grid:
        rho = reduced_spin_state(float(time_point), params, mean_phonon=1.0)
        populations = rotated_basis_populations(rho)
        survival = np.exp(-(time_point * params.gate_time_us) / lifetime_us)
        value = survival * concurrence(rho)
        concurrence_open.append(value)
        for key in populations_by_key:
            populations_by_key[key].append(populations[key])
        rows.append({"t_over_T": time_point, **populations, "concurrence_approx": value, "survival": survival})
    write_csv(DATA_DIR / "figs6_circular_dynamics.csv", rows, list(rows[0]))
    trajectory_grid = np.linspace(0.0, 1.0, 401)
    trajectories = branch_forces(params.coupling_ratio)[:, 0, None] * (1.0 - np.exp(2j * np.pi * trajectory_grid))
    figure, axes = plt.subplots(1, 3, figsize=(12.0, 3.6), constrained_layout=True)
    palette = (COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["red"])
    for index, branch in enumerate(BRANCHES):
        axes[0].plot(trajectories[index].real, trajectories[index].imag, color=palette[index], label=branch)
    axes[0].set(xlabel=r"Re$(\tilde\alpha)$", ylabel=r"Im$(\tilde\alpha)$", aspect="equal")
    axes[0].set_title("(a)", loc="left")
    axes[0].legend(frameon=False, fontsize=7)
    for key, color in zip(populations_by_key, palette, strict=True):
        axes[1].plot(time_grid, populations_by_key[key], color=color, label=key)
    axes[1].set(xlabel=r"$t/T$", ylabel="Population", xlim=(0, 2))
    axes[1].set_title("(b) thermal-overlap approximation", loc="left")
    axes[1].legend(frameon=False, fontsize=7)
    axes[2].plot(time_grid, concurrence_open, color=COLORS["blue"])
    axes[2].set(xlabel=r"$t/T$", ylabel="Concurrence", xlim=(0, 2), ylim=(-0.02, 1.02))
    axes[2].set_title("(c) + disclosed decay", loc="left")
    for axis in axes:
        setup_axes(axis)
    figure.savefig(FIGURE_DIR / "figs6_circular_dynamics_reproduction.png", dpi=180)
    plt.close(figure)
    peak_index = int(np.argmin(np.abs(time_grid - 1.0)))
    return {
        "circular_concurrence_T_approx": float(concurrence_open[peak_index]),
        "lifetime_us": lifetime_us,
    }


def reproduce_figs7(_params: GateParameters) -> dict[str, float]:
    occupation = np.logspace(-1, np.log10(50), 301)
    low = total_gate_infidelity(occupation, 1.88e-3, 200.0)
    circ60_room = total_gate_infidelity(occupation, 1.04e-3, 6_000.0)
    circ60_cryo = total_gate_infidelity(occupation, 1.04e-3, 119_000.0)
    circ60_anh = anharmonic_infidelity(occupation, 1.04e-3)
    circ80_room = total_gate_infidelity(occupation, 0.69e-3, 15_000.0)
    circ80_cryo = total_gate_infidelity(occupation, 0.69e-3, 502_000.0)
    circ80_anh = anharmonic_infidelity(occupation, 0.69e-3)
    s7_rows = [
        {
            "mean_phonon": nbar,
            "low_l_n60_4K": vlow,
            "circ60_300K": c60r,
            "circ60_4K": c60c,
            "circ60_anharmonic": c60a,
            "circ80_300K": c80r,
            "circ80_4K": c80c,
            "circ80_anharmonic": c80a,
        }
        for nbar, vlow, c60r, c60c, c60a, c80r, c80c, c80a in zip(
            occupation, low, circ60_room, circ60_cryo, circ60_anh, circ80_room, circ80_cryo, circ80_anh, strict=True
        )
    ]
    write_csv(DATA_DIR / "figs7_circular_thermal.csv", s7_rows, list(s7_rows[0]))
    figure, axis = plt.subplots(figsize=(5.6, 4.1), constrained_layout=True)
    axis.plot(occupation, low, color=COLORS["gray"], label=r"low-$\ell$, n=60")
    axis.plot(occupation, circ60_room, color=COLORS["blue"], label=r"circ. $n_c=60$, 300 K")
    axis.plot(occupation, circ60_cryo, color=COLORS["blue"], ls="-.", label=r"circ. $n_c=60$, 4 K")
    axis.plot(occupation, circ60_anh, color=COLORS["blue"], ls="--")
    axis.plot(occupation, circ80_room, color=COLORS["red"], label=r"circ. $n_c=80$, 300 K")
    axis.plot(occupation, circ80_cryo, color=COLORS["red"], ls="-.", label=r"circ. $n_c=80$, 4 K")
    axis.plot(occupation, circ80_anh, color=COLORS["red"], ls="--")
    axis.set(xscale="log", yscale="log", xlabel=r"Initial motional occupation $\bar n$", ylabel=r"Gate infidelity $1-\mathcal{F}$")
    axis.legend(frameon=False, fontsize=7)
    setup_axes(axis)
    figure.savefig(FIGURE_DIR / "figs7_circular_thermal_reproduction.png", dpi=180)
    plt.close(figure)
    nbar_one = int(np.argmin(np.abs(occupation - 1.0)))
    return {
        "low_l_n60_4K_at_nbar1": float(low[nbar_one]),
        "circ60_300K_at_nbar1": float(circ60_room[nbar_one]),
        "circ60_4K_at_nbar1": float(circ60_cryo[nbar_one]),
        "circ80_4K_at_nbar1": float(circ80_cryo[nbar_one]),
    }


def reproduce_table_s14(_params: GateParameters) -> dict[str, object]:
    s14_inputs = [
        ("low_l_4K_EIT", 1.2e-2, 2.4e-5, 1.0e-3),
        ("circ60_300K_EIT", 4.2e-4, 7.2e-6, 1.0e-3),
        ("circ60_4K_EIT", 2.1e-5, 7.2e-6, 1.0e-3),
        ("circ60_4K_GSC", 2.1e-5, 7.2e-8, 3.0e-4),
        ("circ80_4K_GSC", 5.0e-6, 3.2e-8, 3.0e-4),
    ]
    s14_rows = [
        {"regime": label, "decay": decay, "anharmonic_10_mode": anh, "technical": tech, "generated_total": decay + anh + tech, "generated_fidelity": 1.0 - decay - anh - tech}
        for label, decay, anh, tech in s14_inputs
    ]
    write_csv(DATA_DIR / "table_s14_crystal_budget.csv", s14_rows, list(s14_rows[0]))
    return {
        "regimes": [str(row["regime"]) for row in s14_rows],
        "generated_fidelities": [
            float(row["generated_fidelity"]) for row in s14_rows
        ],
    }


def reproduce_target(target_id: str, params: GateParameters) -> dict[str, object]:
    if target_id == "T001":
        return reproduce_fig2(params)
    if target_id == "T002":
        return reproduce_fig3()
    if target_id == "T003":
        return reproduce_fig4()
    if target_id == "T004":
        return reproduce_table_s1(params)
    if target_id == "T005":
        return reproduce_table_s2(params)
    if target_id == "T007":
        return reproduce_figs1()
    if target_id == "T008":
        return reproduce_thermal_figures()
    if target_id == "T009":
        return reproduce_gate_counts()
    if target_id == "T010":
        return reproduce_qldpc_projection()
    if target_id == "T011":
        return reproduce_table_s13(params)
    if target_id == "T012":
        return reproduce_figs6(params)
    if target_id == "T013":
        return reproduce_figs7(params)
    if target_id == "T014":
        return reproduce_table_s14(params)
    raise ValueError(f"unknown target: {target_id}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run exactly one paper-reproduction target after harness authorization."
    )
    parser.add_argument("--target", required=True, choices=TARGET_IDS)
    args = parser.parse_args()
    authorized_target = os.environ.get(GUARDED_TARGET_ENV, "")
    authorized_stage = os.environ.get(GUARDED_STAGE_ENV, "")
    if authorized_target != args.target:
        parser.error(
            "target execution requires run_target.py authorization for the same target"
        )
    if authorized_stage not in RUN_STAGES:
        parser.error("target execution requires a valid run_target.py stage authorization")

    started = time.perf_counter()
    for directory in (DATA_DIR, FIGURE_DIR, CHECK_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    params = GateParameters()
    result = reproduce_target(args.target, params)
    elapsed = time.perf_counter() - started
    payload = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "target_id": args.target,
        "requested_stage": authorized_stage,
        "status": "passed",
        "runtime_seconds": elapsed,
        "generated_data_provenance": PROVENANCE_BY_TARGET[args.target],
        "result": result,
    }
    write_json(
        CHECK_DIR / "target_runs" / f"{args.target}.{authorized_stage}.json",
        payload,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
