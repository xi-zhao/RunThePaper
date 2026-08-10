"""Reference-independent rendering of the generated numerical arrays."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


COLORS = {1: "#f26b38", -1: "#2b9fd9", 0: "#70ad47"}
LABELS = {1: r"$\Delta_F>0$", -1: r"$\Delta_F<0$", 0: r"$\Omega=0$"}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "axes.linewidth": 0.9,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "savefig.dpi": 220,
        }
    )


def _save(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _rows(rows: Iterable[dict], **matches: float | int) -> list[dict]:
    return [
        row
        for row in rows
        if all(np.isclose(float(row[key]), float(value)) for key, value in matches.items())
    ]


def plot_energy_cases(cases: list[dict], output: Path, *, columns: int = 2) -> None:
    _style()
    rows = int(np.ceil(len(cases) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(3.3 * columns, 2.65 * rows), squeeze=False)
    for axis, case in zip(axes.ravel(), cases, strict=False):
        energies = np.asarray(case["energies_over_u"], dtype=float)
        color = case.get("color", "#555555")
        grouped_levels: list[tuple[float, list[int]]] = []
        for number, energy in enumerate(energies):
            matching = next(
                (entry for entry in grouped_levels if np.isclose(entry[0], energy, atol=1e-10)),
                None,
            )
            if matching is None:
                grouped_levels.append((float(energy), [number]))
            else:
                matching[1].append(number)
        for energy, numbers in grouped_levels:
            axis.hlines(energy, 0.18, 0.82, color=color, lw=2.0)
            state_label = ", ".join(rf"$|{number}\rangle$" for number in numbers)
            axis.text(0.85, energy, state_label, va="center")
        for target in case.get("resonant_targets", []):
            target = int(target)
            axis.scatter(
                [0.5],
                [energies[target]],
                marker="D",
                s=24,
                facecolor="white",
                edgecolor=color,
                linewidth=1.4,
                zorder=4,
            )
            axis.text(
                0.5,
                energies[target],
                f"  {target}PR",
                color=color,
                va="bottom",
                ha="left",
                fontsize=7,
            )
        axis.set_title(case["title"])
        axis.set_ylabel(r"$E_n/U$")
        axis.set_xlim(0.0, 1.1)
        margin = max(0.5, 0.1 * (np.max(energies) - np.min(energies) + 1.0))
        axis.set_ylim(np.min(energies) - margin, np.max(energies) + margin)
        axis.set_xticks([])
        axis.spines["bottom"].set_visible(False)
    for axis in axes.ravel()[len(cases) :]:
        axis.axis("off")
    fig.tight_layout()
    _save(fig, output)


def plot_fizeau(rows: list[dict], output: Path) -> None:
    _style()
    fig, axis = plt.subplots(figsize=(5.8, 4.1))
    for direction in [1, -1]:
        selected = _rows(rows, direction=direction)
        axis.plot(
            [row["omega_khz"] for row in selected],
            [row["delta_f_mhz"] for row in selected],
            color=COLORS[direction],
            lw=2,
            label=LABELS[direction],
        )
    axis.axhline(0.0, color="0.7", lw=0.7)
    axis.set(xlabel=r"Angular velocity $\Omega$ (kHz)", ylabel=r"Fizeau drag $\Delta_F$ (MHz)", xlim=(0, 60))
    axis.legend(frameon=False)
    fig.tight_layout()
    _save(fig, output)


def plot_main_fig2(rows: list[dict], output: Path) -> None:
    _style()
    fig, axis = plt.subplots(figsize=(6.0, 4.5))
    for direction in [-1, 0, 1]:
        selected = _rows(rows, direction=direction)
        axis.plot(
            [row["k"] for row in selected],
            [row["g2"] for row in selected],
            color=COLORS[direction],
            lw=2,
            label=LABELS[direction],
        )
    axis.axvspan(1.45, 1.55, color="#fff6c7", alpha=0.45, lw=0)
    axis.set_yscale("log")
    axis.set(xlabel="Tuning parameter $k$", ylabel=r"Optical correlation $g^{(2)}(0)$", xlim=(0, 3), ylim=(5e-4, 2e3))
    axis.legend(loc="upper left", frameon=True)
    inset = axis.inset_axes([0.67, 0.14, 0.28, 0.28])
    for direction in [-1, 1]:
        selected = [row for row in _rows(rows, direction=direction) if 1.38 <= row["k"] <= 1.62]
        inset.plot([row["k"] for row in selected], [row["g2"] for row in selected], color=COLORS[direction], lw=1.4)
    inset.set_yscale("log")
    inset.set_xlim(1.38, 1.62)
    inset.set_ylim(5e-4, 2e3)
    inset.tick_params(labelsize=7)
    fig.tight_layout()
    _save(fig, output)


def plot_main_multiphonon(
    rows: list[dict],
    distributions: list[dict],
    output: Path,
    *,
    focus_k: float,
    focus_direction: int,
    xlim: tuple[float, float],
    title_left: str,
    title_right: str,
) -> None:
    _style()
    fig = plt.figure(figsize=(7.2, 7.0))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.15, 0.85], hspace=0.34, wspace=0.3)
    correlation_axis = fig.add_subplot(grid[0, 0])
    criterion_axis = fig.add_subplot(grid[0, 1])
    left_axis = fig.add_subplot(grid[1, 0])
    right_axis = fig.add_subplot(grid[1, 1])

    for direction in [1, -1]:
        selected = _rows(rows, direction=direction)
        k_values = [row["k"] for row in selected]
        correlation_axis.plot(k_values, [row["g3"] for row in selected], color=COLORS[direction], lw=2)
        correlation_axis.plot(k_values, [row["g2"] for row in selected], color=COLORS[direction], lw=1.7, ls="--")
    correlation_axis.set_yscale("log")
    correlation_axis.set(xlabel="Tuning parameter $k$", ylabel="Optical correlation", xlim=xlim)
    correlation_axis.set_title("(a) $g^{(3)}$ (solid), $g^{(2)}$ (dashed)")

    selected = [row for row in _rows(rows, direction=focus_direction) if abs(row["k"] - focus_k) <= 0.025]
    criterion_axis.plot([row["k"] for row in selected], [row["g3"] for row in selected], color=COLORS[focus_direction], lw=1.8, label=r"$g^{(3)}$")
    criterion_axis.plot([row["k"] for row in selected], [row["f"] for row in selected], color="#8c7a5b", lw=1.4, label="$f$")
    criterion_axis.plot([row["k"] for row in selected], [row["g2"] for row in selected], color=COLORS[focus_direction], lw=1.8, ls="--", label=r"$g^{(2)}$")
    criterion_axis.plot([row["k"] for row in selected], [row["f2"] for row in selected], color="#8c7a5b", lw=1.4, ls="--", label=r"$f^{(2)}$")
    criterion_axis.set(xlabel="Tuning parameter $k$", title="(b) Two-photon blockade criteria")
    criterion_axis.legend(frameon=False, ncol=2)

    for axis, direction, title in [(left_axis, 1, title_left), (right_axis, -1, title_right)]:
        selected_dist = _rows(distributions, direction=direction)
        axis.bar(
            [row["photon_number"] for row in selected_dist],
            [row["relative_poisson_deviation"] for row in selected_dist],
            color=COLORS[direction],
            width=0.75,
        )
        axis.axhline(0.0, color="0.25", lw=0.8)
        axis.set(xlabel="Photon number", ylabel=r"$(P-\mathcal{P})/\mathcal{P}$", title=title)
    _save(fig, output)


def plot_nonspinning_diagnostics(
    rows: list[dict],
    distributions: list[dict],
    output: Path,
    *,
    probe_ks: list[float],
    title: str,
) -> None:
    _style()
    fig = plt.figure(figsize=(8.2, 6.8))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.1, 0.9], hspace=0.38, wspace=0.34)
    correlation_axis = fig.add_subplot(grid[0, :2])
    distribution_axis = fig.add_subplot(grid[0, 2])
    deviation_axes = [fig.add_subplot(grid[1, index]) for index in range(3)]

    correlation_axis.plot([row["k"] for row in rows], [row["g2"] for row in rows], color="#e53935", lw=1.8, label=r"$g^{(2)}$")
    correlation_axis.plot([row["k"] for row in rows], [row["g3"] for row in rows], color="#2468d8", lw=1.8, label=r"$g^{(3)}$")
    correlation_axis.plot([row["k"] for row in rows], [row["g4"] for row in rows], color="#3a9d5d", lw=1.8, label=r"$g^{(4)}$")
    correlation_axis.axhline(1.0, color="0.5", lw=0.8)
    correlation_axis.set_yscale("log")
    correlation_axis.set(xlabel="Tuning parameter $k$", ylabel=r"$g^{(m)}(0)$", title=title)
    correlation_axis.legend(frameon=False)

    styles = ["-", "--", ":"]
    for style, probe_k in zip(styles, probe_ks, strict=False):
        selected = [row for row in distributions if np.isclose(row["probe_k"], probe_k)]
        distribution_axis.plot([row["photon_number"] for row in selected], [row["probability"] for row in selected], color="#e53935", ls=style, marker="o", ms=3, label=f"P, k={probe_k:g}")
        distribution_axis.plot([row["photon_number"] for row in selected], [row["poisson_probability"] for row in selected], color="#2468d8", ls=style, marker="x", ms=3, label=f"Poisson, k={probe_k:g}")
    distribution_axis.set_yscale("log")
    distribution_axis.set(xlabel="Photon number", ylabel="Probability")
    distribution_axis.legend(frameon=False, fontsize=6)

    for axis, probe_k in zip(deviation_axes, probe_ks, strict=False):
        selected = [row for row in distributions if np.isclose(row["probe_k"], probe_k)]
        axis.bar([row["photon_number"] for row in selected], [row["relative_poisson_deviation"] for row in selected], color="#3757c5")
        axis.axhline(0.0, color="0.2", lw=0.8)
        axis.set(xlabel="Photon number", title=f"k={probe_k:g}")
    for axis in deviation_axes[len(probe_ks) :]:
        axis.axis("off")
    _save(fig, output)


def plot_analytic_numeric(rows: list[dict], output: Path) -> None:
    _style()
    fig, axis = plt.subplots(figsize=(6.2, 4.6))
    axis.plot([row["k"] for row in rows], [row["g2"] for row in rows], color="#70ad47", lw=2, label=r"numerical $g^{(2)}$")
    axis.plot([row["k"] for row in rows], [row["g3"] for row in rows], color="#264d5f", lw=2, label=r"numerical $g^{(3)}$")
    axis.plot([row["k"] for row in rows], [row["analytic_g2"] for row in rows], color="#70ad47", lw=0, marker="o", ms=2.2, markevery=8, label=r"analytic $g^{(2)}$")
    axis.plot([row["k"] for row in rows], [row["analytic_g3"] for row in rows], color="#264d5f", lw=0, marker="D", ms=2.2, markevery=8, label=r"analytic $g^{(3)}$")
    axis.set_yscale("log")
    axis.set(xlabel="Tuning parameter $k$", ylabel="Optical correlation")
    axis.legend(frameon=False)
    fig.tight_layout()
    _save(fig, output)


def plot_rotation_sweep(rows: list[dict], output: Path) -> None:
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.7), sharey=True)
    palette = plt.cm.viridis(np.linspace(0.2, 0.9, len(sorted({row["omega_khz"] for row in rows}))))
    for axis, direction in zip(axes, [-1, 1], strict=True):
        for color, omega in zip(palette, sorted({row["omega_khz"] for row in rows}), strict=True):
            selected = _rows(rows, direction=direction, omega_khz=omega)
            axis.plot([row["k"] for row in selected], [row["g2"] for row in selected], color=color, lw=1.6, marker="o", ms=2, markevery=16, label=f"{omega:g} kHz")
        axis.set_yscale("log")
        axis.set(xlabel="Tuning parameter $k$", title=LABELS[direction], xlim=(0, 3))
    axes[0].set_ylabel(r"$g^{(2)}(0)$")
    axes[1].legend(frameon=False, fontsize=7)
    fig.tight_layout()
    _save(fig, output)


def plot_s8(rows: list[dict], output: Path) -> None:
    _style()
    fig, axis = plt.subplots(figsize=(6.0, 4.4))
    for direction in [-1, 0, 1]:
        selected = _rows(rows, direction=direction)
        axis.plot([row["k"] for row in selected], [row["g2"] for row in selected], color=COLORS[direction], lw=2, label=LABELS[direction])
    axis.axvspan(1.48, 1.52, color="#fff6c7", alpha=0.5, lw=0)
    axis.set_yscale("log")
    axis.set(xlabel="Tuning parameter $k$", ylabel=r"$g^{(2)}(0)$", xlim=(0, 3))
    axis.legend(frameon=False)
    fig.tight_layout()
    _save(fig, output)


def plot_s9(rows_58: list[dict], rows_29: list[dict], distributions: list[dict], output: Path) -> None:
    _style()
    fig = plt.figure(figsize=(9.0, 7.0))
    outer = fig.add_gridspec(2, 2, width_ratios=[1.25, 1.0], hspace=0.36, wspace=0.28)
    for row_index, (rows, omega) in enumerate([(rows_58, 58.0), (rows_29, 29.0)]):
        correlation_axis = fig.add_subplot(outer[row_index, 0])
        for direction in [1, -1]:
            selected = _rows(rows, direction=direction)
            correlation_axis.plot([row["k"] for row in selected], [row["g3"] for row in selected], color=COLORS[direction], lw=1.8)
            correlation_axis.plot([row["k"] for row in selected], [row["g2"] for row in selected], color=COLORS[direction], lw=1.5, ls="--")
        correlation_axis.set_yscale("log")
        correlation_axis.set(xlabel="Tuning parameter $k$", ylabel="Optical correlation", title=fr"$\Omega={omega:g}$ kHz")

        selected_dist = [row for row in distributions if np.isclose(row["omega_khz"], omega)]
        bar_grid = outer[row_index, 1].subgridspec(2, 2, hspace=0.42, wspace=0.34)
        for probe_index, probe_k in enumerate(sorted({row["probe_k"] for row in selected_dist})):
            for direction_index, direction in enumerate([1, -1]):
                block = [row for row in selected_dist if np.isclose(row["probe_k"], probe_k) and row["direction"] == direction]
                axis = fig.add_subplot(bar_grid[probe_index, direction_index])
                axis.bar(
                    [item["photon_number"] for item in block],
                    [item["relative_poisson_deviation"] for item in block],
                    color=COLORS[direction],
                    width=0.75,
                )
                axis.axhline(0.0, color="0.25", lw=0.7)
                axis.set_title(f"k={probe_k:g}, {LABELS[direction]}", fontsize=7)
                axis.tick_params(labelsize=7)
                if probe_index == 1:
                    axis.set_xlabel("Photon number", fontsize=7)
                if direction_index == 0:
                    axis.set_ylabel(r"$(P-\mathcal{P})/\mathcal{P}$", fontsize=7)
    _save(fig, output)
