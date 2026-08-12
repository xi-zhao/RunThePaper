"""Deterministic renderers over already generated CSV data."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm

COLORS = {
    "blue": "#2369bd",
    "red": "#d62728",
    "green": "#2ca02c",
    "purple": "#7b3294",
    "orange": "#ff7f0e",
    "brown": "#8c564b",
    "pink": "#e78ac3",
    "gray": "#777777",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _style_axes(axis: plt.Axes) -> None:
    axis.grid(True, color="#d9d9d9", linewidth=0.7, alpha=0.75)
    axis.tick_params(direction="in", top=True, right=True)


def render_t001(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    fig, axis = plt.subplots(figsize=(4.15, 3.65))
    angle = np.linspace(-np.pi / 2.0, np.pi / 2.0, 500)
    axis.plot(
        np.cos(angle),
        np.sin(angle),
        color="black",
        linewidth=1.15,
        label="Bloch sphere",
    )
    alpha_colors = {0.21: COLORS["orange"], 0.51: COLORS["brown"]}
    for alpha, color in alpha_colors.items():
        selected = [row for row in rows if np.isclose(_float(row, "alpha"), alpha)]
        axis.plot(
            [_float(row, "y") for row in selected],
            [_float(row, "z") for row in selected],
            color=color,
            linewidth=2.0,
            label=rf"$\alpha={alpha:.2f}$",
        )
    selected = [row for row in rows if np.isclose(_float(row, "alpha"), 0.94)]
    y = np.asarray([_float(row, "y") for row in selected])
    z = np.asarray([_float(row, "z") for row in selected])
    gamma = np.asarray([_float(row, "gamma_prime") for row in selected])
    points = np.column_stack((y, z)).reshape(-1, 1, 2)
    segments = np.concatenate((points[:-1], points[1:]), axis=1)
    collection = LineCollection(
        segments, cmap="turbo", norm=LogNorm(gamma.min(), gamma.max()), linewidth=2.6
    )
    collection.set_array(gamma[:-1])
    axis.add_collection(collection)
    bar = fig.colorbar(collection, ax=axis, pad=0.035)
    bar.set_label(r"$\gamma'$", rotation=270, labelpad=14)
    axis.set(
        xlabel=r"$\langle y\rangle$",
        ylabel=r"$\langle z\rangle$",
        xlim=(-0.03, 1.03),
        ylim=(-1.04, 0.08),
    )
    axis.set_aspect("equal", adjustable="box")
    axis.legend(loc="upper left", fontsize=8, frameon=False)
    _style_axes(axis)
    _save(fig, output_path)


def render_t002(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    fig, axis = plt.subplots(figsize=(4.4, 3.35))
    curve = [row for row in rows if row["role"] == "curve"]
    axis.plot(
        [_float(row, "gamma_initial_prime") for row in curve],
        [_float(row, "a_minus") for row in curve],
        color="black",
        linewidth=1.8,
    )
    markers = {
        "strong_root": (COLORS["purple"], "o", "strong root"),
        "cold_highlight": (COLORS["blue"], "o", "cold"),
        "hot_highlight": (COLORS["red"], "o", "hot"),
    }
    for role, (color, marker, label) in markers.items():
        row = next(item for item in rows if item["role"] == role)
        axis.scatter(
            _float(row, "gamma_initial_prime"),
            _float(row, "a_minus"),
            s=42,
            c=color,
            marker=marker,
            edgecolor="white",
            linewidth=0.6,
            zorder=4,
            label=label,
        )
    axis.scatter(
        15.0,
        0.0,
        marker="*",
        s=95,
        c=COLORS["green"],
        edgecolor="black",
        linewidth=0.4,
        zorder=5,
        label=r"$\gamma_f'=15$",
    )
    axis.axhline(0.0, color="#888888", linewidth=0.8)
    axis.set(xlabel=r"$\gamma_i'$", ylabel=r"$a_-$", xlim=(0.0, 20.0), ylim=(-2.3, 9.0))
    axis.legend(fontsize=8, frameon=False)
    _style_axes(axis)
    _save(fig, output_path)


def render_t003(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    fig, axis = plt.subplots(figsize=(5.1, 3.35))
    styles = {
        "alpha_0.94": (COLORS["green"], r"Theory $\alpha=0.94$"),
        "alpha_1_over_3": (COLORS["red"], r"Theory $\alpha=1/3$"),
    }
    for series, (color, label) in styles.items():
        selected = [row for row in rows if row["series"] == series]
        axis.plot(
            [_float(row, "tau_gamma_f_t") for row in selected],
            [_float(row, "d_cold_minus_hot") for row in selected],
            color=color,
            linewidth=2.2,
            label=label,
        )
    axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    axis.set(
        xlabel=r"Relaxation time, $\gamma_f t$",
        ylabel=r"$d_{ss}^{C}-d_{ss}^{H}$",
        xlim=(0.0, 8.0),
    )
    axis.legend(frameon=False, fontsize=9)
    _style_axes(axis)
    _save(fig, output_path)


def render_t004(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    gamma = np.asarray([_float(row, "gamma_final_prime") for row in rows])
    fig, axis = plt.subplots(figsize=(5.0, 3.55))
    axis.plot(
        gamma,
        [_float(row, "lambda_zero_over_gamma_real") for row in rows],
        color=COLORS["blue"],
        label=r"$\lambda_0$",
    )
    axis.plot(
        gamma,
        [_float(row, "lambda_x_over_gamma_real") for row in rows],
        color=COLORS["orange"],
        label=r"$\lambda_x$",
    )
    axis.plot(
        gamma,
        [_float(row, "lambda_plus_over_gamma_real") for row in rows],
        color="#7cae00",
        label=r"$\lambda_+$",
    )
    axis.plot(
        gamma,
        [_float(row, "lambda_minus_over_gamma_real") for row in rows],
        color=COLORS["red"],
        label=r"$\lambda_-$",
    )
    axis.scatter(
        [2.0],
        [-1.5],
        facecolors="white",
        edgecolors=COLORS["purple"],
        s=40,
        linewidth=1.4,
        zorder=5,
        label="bifurcation",
    )
    axis.set(
        xlabel=r"$\gamma_f'$",
        ylabel=r"$\mathrm{Re}(\lambda)/\gamma_f$",
        xlim=(0.0, 10.0),
        ylim=(-2.08, 0.1),
    )
    axis.legend(
        loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9
    )
    _style_axes(axis)
    _save(fig, output_path)


def render_t005(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    fig, axis = plt.subplots(figsize=(4.55, 4.25))
    colors = ["#4477aa", "#ee9911", "#99aa00", "#ee5533", "#8888cc"]
    for alpha, color in zip([0.1, 0.25, 0.5, 0.75, 1.0], colors, strict=True):
        selected = [
            row
            for row in rows
            if row["series_kind"] == "locus" and np.isclose(_float(row, "alpha"), alpha)
        ]
        axis.plot(
            [_float(row, "y") for row in selected],
            [_float(row, "z") for row in selected],
            color=color,
            linewidth=1.8,
            label=rf"$\alpha={alpha:g}$",
        )
    first = True
    for branch in ("upper_alpha_lt_half", "lower_alpha_gt_half"):
        selected = [row for row in rows if row["branch"] == branch]
        axis.plot(
            [_float(row, "y") for row in selected],
            [_float(row, "z") for row in selected],
            color=COLORS["purple"],
            linestyle="--",
            linewidth=1.45,
            label="bifurcation points" if first else None,
        )
        first = False
    axis.set(
        xlabel=r"$y$ (Bloch)",
        ylabel=r"$z$ (Bloch)",
        xlim=(-0.02, 0.73),
        ylim=(-1.04, 0.04),
    )
    axis.legend(
        loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=8
    )
    _style_axes(axis)
    _save(fig, output_path)


def render_t006(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    fig, axis = plt.subplots(figsize=(5.2, 4.5))
    angle = np.linspace(0.0, 2.0 * np.pi, 600)
    axis.plot(
        np.cos(angle),
        np.sin(angle),
        color="#cccccc",
        linewidth=1.0,
        label="Bloch sphere",
    )
    locus = [row for row in rows if row["series_kind"] == "locus"]
    axis.plot(
        [_float(row, "y") for row in locus],
        [_float(row, "z") for row in locus],
        color=COLORS["pink"],
        linewidth=2.1,
        label=r"steady locus, $\alpha=1$",
    )
    chord_ids = sorted(
        {int(row["chord_id"]) for row in rows if row["series_kind"] == "fast_chord"}
    )
    for index, chord_id in enumerate(chord_ids):
        selected = [
            row
            for row in rows
            if row["series_kind"] == "fast_chord" and int(row["chord_id"]) == chord_id
        ]
        axis.plot(
            [_float(row, "y") for row in selected],
            [_float(row, "z") for row in selected],
            color="black",
            linewidth=0.65,
            alpha=0.78,
            label=r"$v_+$ chords" if index == 0 else None,
        )
    bifurcation = [
        row
        for row in locus
        if abs(_float(row, "gamma_initial_prime") - 2.0)
        == min(abs(_float(item, "gamma_initial_prime") - 2.0) for item in locus)
    ][0]
    axis.scatter(
        _float(bifurcation, "y"),
        _float(bifurcation, "z"),
        s=38,
        c=COLORS["purple"],
        zorder=4,
        label=r"$\gamma_b'=2$",
    )
    axis.set(xlabel=r"$y$", ylabel=r"$z$", xlim=(-1.05, 1.05), ylim=(-1.08, 1.05))
    axis.set_aspect("equal", adjustable="box")
    axis.legend(
        loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=8
    )
    _style_axes(axis)
    _save(fig, output_path)


def _render_trajectory_panel(data_path: Path, output_path: Path, zoom: bool) -> None:
    rows = _rows(data_path)
    fig, axis = plt.subplots(figsize=(4.75, 4.05))
    styles = {
        "colder_0.02": (COLORS["purple"], r"$\gamma_i'=0.02$"),
        "strong_cold": (COLORS["blue"], r"$\gamma_{i,\mathrm{SME}}'$"),
        "hot_0.74": (COLORS["green"], r"$\gamma_i'=0.74$"),
    }
    for series, (color, label) in styles.items():
        selected = [row for row in rows if row["series"] == series]
        axis.plot(
            [_float(row, "y") for row in selected],
            [_float(row, "z") for row in selected],
            color=color,
            linewidth=2.0,
            label=label,
        )
        if not zoom:
            axis.scatter(
                _float(selected[0], "y"), _float(selected[0], "z"), color=color, s=25
            )
    if zoom:
        all_y = np.asarray([_float(row, "y") for row in rows])
        all_z = np.asarray([_float(row, "z") for row in rows])
        margin_y = max(np.ptp(all_y) * 0.12, 1e-8)
        margin_z = max(np.ptp(all_z) * 0.12, 1e-8)
        axis.set_xlim(all_y.min() - margin_y, all_y.max() + margin_y)
        axis.set_ylim(all_z.min() - margin_z, all_z.max() + margin_z)
        axis.ticklabel_format(
            style="sci", axis="both", scilimits=(-2, 2), useOffset=True
        )
        axis.set_title("Late-time mode directions", fontsize=10)
    else:
        angle = np.linspace(0.0, 2.0 * np.pi, 600)
        axis.plot(np.cos(angle), np.sin(angle), color="#cccccc", linewidth=0.9)
        axis.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05))
        axis.set_aspect("equal", adjustable="box")
    axis.set(xlabel=r"$y$", ylabel=r"$z$")
    axis.legend(frameon=False, fontsize=8)
    _style_axes(axis)
    _save(fig, output_path)


def render_t009(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    x = np.asarray([_float(row, "gamma_initial_prime") for row in rows])
    y = np.asarray([_float(row, "crossing_time_omega_inverse") for row in rows])
    strong = _float(rows[0], "strong_gamma_initial_prime")
    fig, axis = plt.subplots(figsize=(4.55, 3.25))
    axis.plot(x, y, color=COLORS["blue"], linewidth=2.0)
    axis.axvline(
        strong,
        color="#888888",
        linestyle="--",
        linewidth=1.1,
        label=r"$\gamma_{i,\mathrm{SME}}'$",
    )
    axis.set(
        xlabel=r"$\gamma_i'$", ylabel=r"$t_{\mathrm{cross}}\,\Omega$", xlim=(0.02, 0.74)
    )
    axis.legend(frameon=False, fontsize=8)
    _style_axes(axis)
    _save(fig, output_path)


def render_t010(data_path: Path, output_path: Path) -> None:
    rows = _rows(data_path)
    x = np.asarray([_float(row, "gamma_initial_prime") for row in rows])
    y = np.asarray([_float(row, "maximal_distance_advantage") for row in rows])
    strong = _float(rows[0], "strong_gamma_initial_prime")
    fig, axis = plt.subplots(figsize=(4.55, 3.25))
    axis.plot(x, y, color=COLORS["blue"], linewidth=2.0)
    axis.axvline(
        strong,
        color="#888888",
        linestyle="--",
        linewidth=1.1,
        label=r"$\gamma_{i,\mathrm{SME}}'$",
    )
    axis.set(
        xlabel=r"$\gamma_i'$",
        ylabel="Max. distance after crossing",
        xlim=(0.02, 0.74),
        ylim=(0.0, max(y) * 1.08),
    )
    axis.legend(frameon=False, fontsize=8)
    _style_axes(axis)
    _save(fig, output_path)


def render_all(workspace: Path, config: dict[str, Any]) -> list[Path]:
    del config  # rendering reads only hash-frozen generated CSVs
    data = workspace / "outputs" / "data"
    figures = workspace / "outputs" / "figures"
    mapping = [
        (render_t001, "T001_main_fig2_left.csv", "T001_main_fig2_left.png"),
        (render_t002, "T002_main_fig2_right.csv", "T002_main_fig2_right.png"),
        (render_t003, "T003_main_fig4_theory.csv", "T003_main_fig4_theory.png"),
        (render_t004, "T004_supp_fig1.csv", "T004_supp_fig1.png"),
        (render_t005, "T005_supp_fig2.csv", "T005_supp_fig2.png"),
        (render_t006, "T006_supp_fig3.csv", "T006_supp_fig3.png"),
    ]
    outputs: list[Path] = []
    for function, data_name, figure_name in mapping:
        output = figures / figure_name
        function(data / data_name, output)
        outputs.append(output)
    trajectory_left = figures / "T007_supp_fig4_left.png"
    _render_trajectory_panel(
        data / "T007_supp_fig4_left.csv", trajectory_left, zoom=False
    )
    outputs.append(trajectory_left)
    trajectory_right = figures / "T008_supp_fig4_right.png"
    _render_trajectory_panel(
        data / "T008_supp_fig4_right.csv", trajectory_right, zoom=True
    )
    outputs.append(trajectory_right)
    for function, data_name, figure_name in (
        (render_t009, "T009_supp_fig5_left.csv", "T009_supp_fig5_left.png"),
        (render_t010, "T010_supp_fig5_right.csv", "T010_supp_fig5_right.png"),
    ):
        output = figures / figure_name
        function(data / data_name, output)
        outputs.append(output)
    return outputs
