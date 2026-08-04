#!/usr/bin/env python3
"""Generate every numerical axis of arXiv:1905.09460 from equations.

Only the case config and the scientific module are imported.  Frozen EPS/PNG
references are intentionally unreachable from this generation path.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / ".cache" / "matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec  # noqa: E402

sys.path.insert(0, str(WORKSPACE))

from src.nonhermitian_quasicrystal import (  # noqa: E402
    aah_hamiltonian,
    analytic_winding,
    critical_phase,
    edge_state_counts,
    etalon_transmission,
    inverse_participation_ratios,
    normalized_eigensystem,
    stationary_laser_spectrum,
    winding_number,
)


CONFIG_PATH = WORKSPACE / "config" / "paper_exact.json"
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"

BLUE = "#3b51b5"
GREEN = "#278b3b"
ORANGE = "#f26b21"
BLACK = "#111111"


def _load_config() -> dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _write_csv(path: Path, columns: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _clean_svg(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def _save_figure(fig: plt.Figure, stem: str, dpi: int) -> dict[str, str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for suffix in ("png", "pdf", "svg"):
        path = FIGURE_DIR / f"{stem}.{suffix}"
        fig.savefig(path, dpi=dpi, facecolor="white")
        if suffix == "svg":
            _clean_svg(path)
        paths[suffix] = str(path.relative_to(WORKSPACE))
    plt.close(fig)
    return paths


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 13,
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.7,
            "axes.edgecolor": "#555555",
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "savefig.facecolor": "white",
        }
    )


def _solve_aah_family(config: dict[str, object], *, boundary: str, length: int) -> dict[str, object]:
    scan = np.linspace(config["phase_scan_min"], config["phase_scan_max"], int(config["phase_scan_points"]))
    spectral_phases = np.asarray(config["spectral_phases"], dtype=float)
    phases = sorted({round(float(value), 12) for value in np.concatenate([scan, spectral_phases])})
    scan_keys = {round(float(value), 12) for value in scan}
    spectral_keys = {round(float(value), 12) for value in spectral_phases}

    scan_records: dict[float, dict[str, float]] = {}
    spectra: dict[float, np.ndarray] = {}
    edge_records: dict[float, tuple[int, int]] = {}
    for index, h in enumerate(phases, start=1):
        matrix = aah_hamiltonian(
            length,
            hopping=float(config["hopping"]),
            potential_strength=float(config["potential_strength"]),
            alpha=float(config["alpha"]),
            theta=float(config["theta"]),
            complex_phase=h,
            boundary=boundary,
        )
        values, vectors = normalized_eigensystem(matrix)
        ipr = inverse_participation_ratios(vectors)
        key = round(h, 12)
        if key in scan_keys:
            scan_records[key] = {
                "max_abs_imag": float(np.max(np.abs(values.imag))),
                "min_ipr": float(np.min(ipr)),
                "max_ipr": float(np.max(ipr)),
            }
            if boundary == "open":
                edge_records[key] = edge_state_counts(
                    vectors,
                    edge_width=int(config["edge_width"]),
                    minimum_edge_weight=float(config["minimum_edge_weight"]),
                )
        if key in spectral_keys:
            spectra[key] = values
        if index == 1 or index % 10 == 0 or index == len(phases):
            print(f"{boundary} AAH: {index}/{len(phases)} phases", flush=True)

    ordered_records = [scan_records[round(float(h), 12)] for h in scan]
    return {
        "scan": scan,
        "max_abs_imag": np.array([item["max_abs_imag"] for item in ordered_records]),
        "min_ipr": np.array([item["min_ipr"] for item in ordered_records]),
        "max_ipr": np.array([item["max_ipr"] for item in ordered_records]),
        "spectra": spectra,
        "edges": edge_records,
    }


def _render_main_figure_1(
    family: dict[str, object],
    *,
    h_c: float,
    config: dict[str, object],
    canvas: list[int],
    dpi: int,
) -> dict[str, str]:
    _style()
    width, height = canvas
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    outer = GridSpec(1, 4, figure=fig, left=0.045, right=0.992, bottom=0.15, top=0.94, wspace=0.34)
    first = GridSpecFromSubplotSpec(4, 1, subplot_spec=outer[0], hspace=0.1)
    spectral_phases = [float(value) for value in config["spectral_phases"]]
    y_limits = [(-0.1, 0.1), (-0.1, 0.1), (-0.1, 0.1), (-0.5, 0.5)]
    for row, (h, limits) in enumerate(zip(spectral_phases, y_limits, strict=True)):
        ax = fig.add_subplot(first[row])
        values = family["spectra"][round(h, 12)]
        ax.scatter(values.real, values.imag, s=7, color=BLUE, edgecolors="none")
        ax.set_xlim(-2.9, 2.9)
        ax.set_ylim(*limits)
        ax.set_yticks([limits[0], 0.0, limits[1]])
        ax.tick_params(labelsize=10)
        ax.text(0.84, 0.74, rf"$h={h:g}$", transform=ax.transAxes, fontsize=13)
        if row < 3:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel(r"$\mathrm{Re}(E)$", fontsize=14)
        ax.set_ylabel(r"$\mathrm{Im}(E)$", fontsize=12)
        if row == 0:
            ax.set_title("(a)", loc="left", fontsize=19, pad=8)

    h = family["scan"]
    ax = fig.add_subplot(outer[1])
    ax.plot(h, family["max_abs_imag"], color=BLUE, linewidth=1.7)
    ax.axvline(h_c, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.25)
    ax.set_xlim(0.0, 1.5)
    ax.set_ylim(0.0, 1.8)
    ax.set_xlabel(r"complex phase $h$", fontsize=14)
    ax.set_ylabel(r"largest value of $|\mathrm{Im}(E)|$", fontsize=13)
    ax.set_title("(b)", loc="left", fontsize=19, pad=8)
    ax.text(0.16, 0.72, "unbroken\nPT phase", transform=ax.transAxes, fontsize=14)
    ax.text(0.62, 0.72, "broken\nPT phase", transform=ax.transAxes, fontsize=14)
    ax.text(0.32, 0.12, r"$h=h_c$", transform=ax.transAxes, fontsize=13)
    ax.annotate("", xy=(0.13, 0.9), xytext=(0.44, 0.9), xycoords="axes fraction", arrowprops={"arrowstyle": "->", "lw": 2})
    ax.annotate("", xy=(0.88, 0.9), xytext=(0.57, 0.9), xycoords="axes fraction", arrowprops={"arrowstyle": "->", "lw": 2})

    ax = fig.add_subplot(outer[2])
    ax.scatter(h, family["max_ipr"], s=14, color=BLUE)
    ax.scatter(h, family["min_ipr"], s=12, color=GREEN, marker="s")
    ax.axvline(h_c, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.25)
    ax.set_xlim(0.0, 1.5)
    ax.set_ylim(0.0, 0.9)
    ax.set_xlabel(r"complex phase $h$", fontsize=14)
    ax.set_ylabel("Inverse Participation Ratio IPR", fontsize=13)
    ax.set_title("(c)", loc="left", fontsize=19, pad=8)
    ax.text(0.22, 0.66, "metallic\nphase", transform=ax.transAxes, fontsize=14)
    ax.text(0.60, 0.66, "insulating\nphase", transform=ax.transAxes, fontsize=14)
    ax.text(0.18, 0.16, r"$h=h_c$", transform=ax.transAxes, fontsize=13)

    ax = fig.add_subplot(outer[3])
    numeric_winding = np.array([winding_number(float(value), length=int(config["main_length"])) for value in h])
    analytic = np.array([analytic_winding(float(value)) for value in h])
    ax.scatter(h, numeric_winding, s=24, color=BLUE, zorder=3)
    ax.scatter(h[::3], analytic[::3], s=28, facecolors="none", edgecolors=ORANGE, marker="s", linewidths=1.2, zorder=4)
    ax.axvline(h_c, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.25)
    ax.set_xlim(0.0, 1.5)
    ax.set_ylim(-1.6, 0.02)
    ax.set_xlabel(r"complex phase $h$", fontsize=14)
    ax.set_ylabel(r"winding number $w$", fontsize=13)
    ax.set_title("(d)", loc="left", fontsize=19, pad=8)
    ax.text(0.07, 0.76, "topological\nphase $w=0$", transform=ax.transAxes, fontsize=13)
    ax.text(0.57, 0.76, "topological\nphase $w=-1$", transform=ax.transAxes, fontsize=13)
    ax.text(0.28, 0.05, r"$h=h_c$", transform=ax.transAxes, fontsize=13)
    return _save_figure(fig, "main_figure_1_topological_transition", dpi)


def _render_supp_figure_1(
    family: dict[str, object],
    *,
    h_c: float,
    config: dict[str, object],
    canvas: list[int],
    dpi: int,
) -> dict[str, str]:
    _style()
    width, height = canvas
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    outer = GridSpec(1, 4, figure=fig, left=0.045, right=0.992, bottom=0.15, top=0.94, wspace=0.34)
    first = GridSpecFromSubplotSpec(4, 1, subplot_spec=outer[0], hspace=0.1)
    spectral_phases = [float(value) for value in config["spectral_phases"]]
    y_limits = [(-0.1, 0.1), (-0.2, 0.2), (-0.25, 0.25), (-0.5, 0.5)]
    for row, (h_value, limits) in enumerate(zip(spectral_phases, y_limits, strict=True)):
        ax = fig.add_subplot(first[row])
        values = family["spectra"][round(h_value, 12)]
        ax.scatter(values.real, values.imag, s=7, color=BLUE, facecolors="none" if row < 2 else BLUE, linewidths=0.6)
        ax.set_xlim(-2.9, 2.9)
        ax.set_ylim(*limits)
        ax.set_yticks([limits[0], 0.0, limits[1]])
        ax.tick_params(labelsize=10)
        ax.text(0.84, 0.73, rf"$h={h_value:g}$", transform=ax.transAxes, fontsize=13)
        if row < 3:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel(r"$\mathrm{Re}(E)$", fontsize=14)
        ax.set_ylabel(r"$\mathrm{Im}(E)$", fontsize=12)
        if row == 0:
            ax.set_title("(a)", loc="left", fontsize=19, pad=8)

    h = family["scan"]
    ax = fig.add_subplot(outer[1])
    ax.plot(h, family["max_abs_imag"], color=BLUE, linewidth=1.7)
    ax.axvline(h_c, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.25)
    ax.set_xlim(0.0, 1.5)
    ax.set_ylim(0.0, 1.8)
    ax.set_xlabel(r"complex phase $h$", fontsize=14)
    ax.set_ylabel(r"largest value of $|\mathrm{Im}(E)|$", fontsize=13)
    ax.set_title("(b)", loc="left", fontsize=19, pad=8)
    ax.text(0.58, 0.72, "broken\nPT phase", transform=ax.transAxes, fontsize=14)
    ax.text(0.31, 0.45, r"$h=h_c$", transform=ax.transAxes, fontsize=13)

    ax = fig.add_subplot(outer[2])
    ax.scatter(h, family["max_ipr"], s=14, color=BLUE)
    ax.scatter(h, family["min_ipr"], s=12, color=GREEN, marker="s")
    ax.axvline(h_c, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.25)
    ax.axvline(0.41, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.0)
    ax.set_xlim(0.0, 1.5)
    ax.set_ylim(0.0, 0.9)
    ax.set_xlabel(r"complex phase $h$", fontsize=14)
    ax.set_ylabel("Inverse Participation Ratio IPR", fontsize=13)
    ax.set_title("(c)", loc="left", fontsize=19, pad=8)
    ax.text(0.19, 0.66, "metallic\nphase", transform=ax.transAxes, fontsize=14)
    ax.text(0.62, 0.66, "insulating\nphase", transform=ax.transAxes, fontsize=14)

    edge_h = np.array([value for value in h if value <= h_c + 1e-12])
    left = np.array([family["edges"][round(float(value), 12)][0] for value in edge_h])
    right = np.array([family["edges"][round(float(value), 12)][1] for value in edge_h])
    ax = fig.add_subplot(outer[3])
    ax.scatter(edge_h, right, s=27, facecolors="none", edgecolors=BLUE, linewidths=1.2)
    ax.scatter(edge_h, left, s=25, facecolors="none", edgecolors=GREEN, marker="s", linewidths=1.2)
    ax.axvline(h_c, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.25)
    ax.axvline(0.41, color=BLACK, linestyle=(0, (5, 5)), linewidth=1.0)
    ax.set_xlim(0.0, 0.71)
    ax.set_ylim(0.0, max(20.0, float(np.max(right) + 2)))
    ax.set_xlabel(r"complex phase $h$", fontsize=14)
    ax.set_ylabel(r"number $N$ of edge states", fontsize=13)
    ax.set_title("(d)", loc="left", fontsize=19, pad=8)
    ax.text(0.18, 0.28, r"$N_R$ (right edge)", transform=ax.transAxes, fontsize=13)
    ax.text(0.08, 0.04, r"$N_L$ (left edge)", transform=ax.transAxes, fontsize=13)
    return _save_figure(fig, "supp_figure_1_edge_effects", dpi)


def _render_main_figure_3(
    laser_scan: list[object],
    profiles: dict[float, object],
    *,
    config: dict[str, object],
    canvas: list[int],
    dpi: int,
) -> dict[str, str]:
    _style()
    width, height = canvas
    # Avoid a floating-point floor from 1525 to 1524 pixels at this canvas.
    fig = plt.figure(figsize=(width / dpi, (height + 0.01) / dpi), dpi=dpi)
    outer = GridSpec(1, 2, figure=fig, left=0.08, right=0.985, bottom=0.12, top=0.94, width_ratios=[0.47, 0.53], wspace=0.22)
    depths = np.array([item[0] for item in laser_scan], dtype=float)
    bandwidths = np.array([item[1].bandwidth for item in laser_scan], dtype=float)
    ax = fig.add_subplot(outer[0])
    ax.scatter(depths, bandwidths, s=20, color=BLUE)
    ax.axvline(2.0 * float(config["potential_strength"]), color=BLACK, linestyle=(0, (5, 5)), linewidth=1.2)
    ax.set_yscale("log")
    ax.set_xlim(0.09, 0.36)
    ax.set_ylim(0.08, 100.0)
    ax.set_xlabel(r"modulation depth $\Delta_{FM}$", fontsize=15)
    ax.set_ylabel("oscillating laser bandwidth", fontsize=15)
    ax.set_title("(a)", loc="left", fontsize=24, pad=8)

    right = GridSpecFromSubplotSpec(4, 1, subplot_spec=outer[1], hspace=0.06)
    for row, depth in enumerate([float(value) for value in config["profile_depths"]]):
        state = profiles[round(depth, 12)]
        ax = fig.add_subplot(right[row])
        scale = state.normalized_spectrum / max(float(np.max(state.normalized_spectrum)), 1e-15)
        ax.bar(state.mode_indices, scale, width=0.86, color=BLUE, edgecolor=BLUE, linewidth=0.2)
        ax.set_xlim(-40.0, 40.0)
        ax.set_ylim(0.0, 1.08)
        ax.set_yticks([])
        ax.text(0.72, 0.70, rf"$\Delta_{{FM}}={depth:g}$", transform=ax.transAxes, fontsize=17)
        if row < 3:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel(r"axial mode index $n$", fontsize=15)
        if row == 0:
            ax.set_title("(b)", loc="left", fontsize=24, pad=8)
    fig.text(0.535, 0.51, r"laser spectrum $|\psi_n|^2$ (arb. units)", va="center", rotation=90, fontsize=15)
    return _save_figure(fig, "main_figure_3_laser_transition", dpi)


def _render_supp_figure_2(result: object, *, canvas: list[int], dpi: int) -> dict[str, str]:
    _style()
    width, height = canvas
    fig, axes = plt.subplots(2, 1, figsize=(width / dpi, height / dpi), dpi=dpi, sharex=True)
    fig.subplots_adjust(left=0.13, right=0.985, bottom=0.17, top=0.97, hspace=0.2)
    axes[0].plot(result.normalized_frequency, result.exact.real, color=BLUE, linewidth=2.1)
    axes[0].plot(result.normalized_frequency, result.first_order.real, color=GREEN, linewidth=1.6, linestyle=(0, (5, 4)))
    axes[0].set_ylim(0.5, 1.0)
    axes[0].set_ylabel(r"$\mathrm{Re}(t)$", fontsize=18)
    axes[1].plot(result.normalized_frequency, result.exact.imag, color=BLUE, linewidth=2.1)
    axes[1].plot(result.normalized_frequency, result.first_order.imag, color=GREEN, linewidth=1.6, linestyle=(0, (5, 4)))
    axes[1].set_ylim(-0.2, 0.2)
    axes[1].set_ylabel(r"$\mathrm{Im}(t)$", fontsize=18)
    axes[1].set_xlabel(r"normalized frequency $\omega/\Delta\omega_{etal}$", fontsize=18)
    for ax in axes:
        ax.set_xlim(-2.0, 2.0)
        ax.tick_params(labelsize=14)
    return _save_figure(fig, "supp_figure_2_etalon_transmission", dpi)


def main() -> int:
    started = time.perf_counter()
    config = _load_config()
    aah = config["aah"]
    laser = config["laser"]
    etalon = config["etalon"]
    rendering = config["rendering"]
    h_c = critical_phase(float(aah["hopping"]), float(aah["potential_strength"]))

    print("Solving paper-sized periodic AAH family...", flush=True)
    periodic = _solve_aah_family(aah, boundary="periodic", length=int(aah["main_length"]))
    print("Solving paper-sized open AAH family...", flush=True)
    open_family = _solve_aah_family(aah, boundary="open", length=int(aah["supplement_length"]))

    scan = periodic["scan"]
    periodic_rows = []
    for h, max_imag, min_ipr, max_ipr in zip(scan, periodic["max_abs_imag"], periodic["min_ipr"], periodic["max_ipr"], strict=True):
        periodic_rows.append([f"{h:.12g}", f"{max_imag:.16g}", f"{min_ipr:.16g}", f"{max_ipr:.16g}", f"{winding_number(float(h), length=int(aah['main_length'])):.16g}", f"{analytic_winding(float(h)):.16g}"])
    _write_csv(DATA_DIR / "main_figure_1_scan.csv", ["h", "max_abs_imag_E", "min_ipr", "max_ipr", "winding_numeric", "winding_analytic"], periodic_rows)
    spectra_rows = []
    for h in [float(value) for value in aah["spectral_phases"]]:
        for value in periodic["spectra"][round(h, 12)]:
            spectra_rows.append([f"{h:.12g}", f"{value.real:.16g}", f"{value.imag:.16g}"])
    _write_csv(DATA_DIR / "main_figure_1_spectra.csv", ["h", "real_E", "imag_E"], spectra_rows)

    open_rows = []
    edge_rows = []
    for h, max_imag, min_ipr, max_ipr in zip(scan, open_family["max_abs_imag"], open_family["min_ipr"], open_family["max_ipr"], strict=True):
        left, right = open_family["edges"][round(float(h), 12)]
        open_rows.append([f"{h:.12g}", f"{max_imag:.16g}", f"{min_ipr:.16g}", f"{max_ipr:.16g}"])
        if h <= h_c + 1e-12:
            edge_rows.append([f"{h:.12g}", left, right])
    _write_csv(DATA_DIR / "supp_figure_1_scan.csv", ["h", "max_abs_imag_E", "min_ipr", "max_ipr"], open_rows)
    _write_csv(DATA_DIR / "supp_figure_1_edge_counts.csv", ["h", "left_edge_states", "right_edge_states"], edge_rows)
    open_spectra_rows = []
    for h in [float(value) for value in aah["spectral_phases"]]:
        for value in open_family["spectra"][round(h, 12)]:
            open_spectra_rows.append([f"{h:.12g}", f"{value.real:.16g}", f"{value.imag:.16g}"])
    _write_csv(DATA_DIR / "supp_figure_1_spectra.csv", ["h", "real_E", "imag_E"], open_spectra_rows)

    print("Solving stationary laser family...", flush=True)
    modulation_depths = np.linspace(float(laser["modulation_min"]), float(laser["modulation_max"]), int(laser["modulation_points"]))
    required_depths = sorted({round(float(value), 12) for value in np.concatenate([modulation_depths, np.asarray(laser["profile_depths"], dtype=float)])})
    states: dict[float, object] = {}
    for index, depth in enumerate(required_depths, start=1):
        states[depth] = stationary_laser_spectrum(
            depth,
            potential_strength=float(laser["potential_strength"]),
            alpha=float(laser["alpha"]),
            theta=float(laser["theta"]),
            cavity_loss=float(laser["cavity_loss"]),
            small_signal_gain=float(laser["small_signal_gain"]),
            modulation_frequency_ghz=float(laser["modulation_frequency_ghz"]),
            gain_width_ghz=float(laser["gain_width_ghz"]),
            mode_limit=int(laser["mode_limit"]),
        )
        if index == 1 or index % 10 == 0 or index == len(required_depths):
            print(f"laser: {index}/{len(required_depths)} depths", flush=True)
    laser_scan = [(float(depth), states[round(float(depth), 12)]) for depth in modulation_depths]
    _write_csv(
        DATA_DIR / "main_figure_3_bandwidth.csv",
        ["modulation_depth", "bandwidth", "saturated_gain", "total_intensity", "residual_growth"],
        [[f"{depth:.12g}", f"{state.bandwidth:.16g}", f"{state.saturated_gain:.16g}", f"{state.total_intensity:.16g}", f"{state.residual_growth:.16g}"] for depth, state in laser_scan],
    )
    laser_profile_rows = []
    profiles = {round(float(depth), 12): states[round(float(depth), 12)] for depth in laser["profile_depths"]}
    for depth, state in profiles.items():
        for mode, intensity in zip(state.mode_indices, state.normalized_spectrum, strict=True):
            laser_profile_rows.append([f"{depth:.12g}", f"{mode:.12g}", f"{intensity:.16g}"])
    _write_csv(DATA_DIR / "main_figure_3_spectra.csv", ["modulation_depth", "mode_index", "normalized_intensity"], laser_profile_rows)

    frequency = np.linspace(float(etalon["normalized_frequency_min"]), float(etalon["normalized_frequency_max"]), int(etalon["points"]))
    transmission = etalon_transmission(frequency, refractive_index=float(etalon["refractive_index"]), phase=float(etalon["phase"]))
    _write_csv(
        DATA_DIR / "supp_figure_2_etalon.csv",
        ["normalized_frequency", "exact_real", "exact_imag", "first_order_real", "first_order_imag"],
        [[f"{x:.16g}", f"{exact.real:.16g}", f"{exact.imag:.16g}", f"{approx.real:.16g}", f"{approx.imag:.16g}"] for x, exact, approx in zip(frequency, transmission.exact, transmission.first_order, strict=True)],
    )

    dpi = int(rendering["dpi"])
    figure_paths = {
        "T001": _render_main_figure_1(periodic, h_c=h_c, config=aah, canvas=rendering["main_figure_1_canvas_pixels"], dpi=dpi),
        "T002": _render_main_figure_3(laser_scan, profiles, config=laser, canvas=rendering["main_figure_3_canvas_pixels"], dpi=dpi),
        "T003": _render_supp_figure_1(open_family, h_c=h_c, config=aah, canvas=rendering["supp_figure_1_canvas_pixels"], dpi=dpi),
        "T004": _render_supp_figure_2(transmission, canvas=rendering["supp_figure_2_canvas_pixels"], dpi=dpi),
    }

    scan_index_below = int(np.argmin(np.abs(scan - 0.66)))
    scan_index_above = int(np.argmin(np.abs(scan - 0.75)))
    zero_edges = open_family["edges"][round(float(scan[0]), 12)]
    bandwidth_lookup = {round(depth, 12): state.bandwidth for depth, state in laser_scan}
    max_residual = max(abs(state.residual_growth) for _, state in laser_scan)
    scientific = {
        "schema_version": 1,
        "paper_id": "1905.09460",
        "status": "passed",
        "generation_policy": {
            "source_pixels_used_in_generation": False,
            "digitized_data_used": False,
            "reference_files_read": [],
            "inputs": ["config/paper_exact.json", "src/nonhermitian_quasicrystal.py"],
        },
        "checks": {
            "critical_phase": h_c,
            "critical_phase_abs_error_from_ln2": abs(h_c - float(np.log(2.0))),
            "periodic_max_imag_below_transition": float(periodic["max_abs_imag"][scan_index_below]),
            "periodic_max_imag_above_transition": float(periodic["max_abs_imag"][scan_index_above]),
            "periodic_max_ipr_below_transition": float(periodic["max_ipr"][scan_index_below]),
            "periodic_max_ipr_at_h_1_5": float(periodic["max_ipr"][-1]),
            "winding_below": winding_number(0.5, length=int(aah["main_length"])),
            "winding_above": winding_number(0.9, length=int(aah["main_length"])),
            "open_edge_counts_at_h_0": {"left": zero_edges[0], "right": zero_edges[1]},
            "laser_transition_depth": 2.0 * float(laser["potential_strength"]),
            "laser_bandwidth_at_0_1": bandwidth_lookup[0.1],
            "laser_bandwidth_at_0_28": bandwidth_lookup[0.28],
            "laser_bandwidth_at_0_35": bandwidth_lookup[0.35],
            "laser_max_neutral_growth_residual": max_residual,
            "etalon_reflectance": transmission.reflectance,
            "etalon_max_first_order_abs_error": float(np.max(np.abs(transmission.exact - transmission.first_order))),
        },
    }
    passed = (
        scientific["checks"]["critical_phase_abs_error_from_ln2"] < 1e-14
        and scientific["checks"]["periodic_max_imag_below_transition"] < 0.03
        and scientific["checks"]["periodic_max_imag_above_transition"] > 0.02
        and scientific["checks"]["periodic_max_ipr_at_h_1_5"] > 0.6
        and scientific["checks"]["winding_below"] > -0.01
        and scientific["checks"]["winding_above"] < -0.99
        and zero_edges == (0, 3)
        and scientific["checks"]["laser_bandwidth_at_0_1"] < 1.0
        and scientific["checks"]["laser_bandwidth_at_0_28"] > 5.0
        and scientific["checks"]["laser_bandwidth_at_0_35"] > 4.0
        and max_residual < 1e-7
        and scientific["checks"]["etalon_max_first_order_abs_error"] < 0.05
    )
    scientific["status"] = "passed" if passed else "failed"
    _write_json(CHECK_DIR / "scientific_validation.json", scientific)

    elapsed = time.perf_counter() - started
    run_payload = {
        "schema_version": 1,
        "paper_id": "1905.09460",
        "status": scientific["status"],
        "runtime_seconds": elapsed,
        "command": "python3 code/scripts/run_reproduction.py",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "numeric_axes_generated": 21,
        "outputs": {
            "data": [str(path.relative_to(WORKSPACE)) for path in sorted(DATA_DIR.glob("*.csv"))],
            "figures": figure_paths,
            "checks": ["outputs/checks/scientific_validation.json"],
        },
    }
    _write_json(CHECK_DIR / "reproduction_run.json", run_payload)
    print(json.dumps(run_payload, indent=2, ensure_ascii=False), flush=True)
    return 0 if scientific["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
