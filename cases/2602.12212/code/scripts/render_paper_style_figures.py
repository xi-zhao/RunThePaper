#!/usr/bin/env python3
"""Render paper-layout replicas from the independently generated data.

The scientific data in these plots are never read from the paper figures.  The
paper PNGs are used only to reconstruct canvas geometry, typography, colour,
line style, and camera choices.  Every output therefore remains an independent
numerical/analytic reproduction while being suitable for registered image
comparison.
"""

from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import leaf_thermodynamics as leaf  # noqa: E402


DATA = WORKSPACE / "outputs" / "data"
SHARDS = DATA / "campaign_shards"
OUTPUT = WORKSPACE / "outputs" / "pixel_registered"
PAPER_SIZES = (6, 8, 10, 12)
BETAS = (0.25, 0.75, 1.75)
COLORS = {
    6: "#b02ec5",
    8: "#ef9200",
    10: "#5b6fc7",
    12: "#e55309",
}
OBSERVABLES = (
    "sigma_x",
    "sigma_y",
    "sigma_z",
    "sigma_x_sigma_x",
    "sigma_y_sigma_z",
    "sigma_z_sigma_y",
    "sigma_y_sigma_y",
    "sigma_z_sigma_x",
    "sigma_x_sigma_z",
    "sigma_z_sigma_z",
    "sigma_x_sigma_y",
    "sigma_y_sigma_x",
)
OBSERVABLE_TITLES = {
    "sigma_x": r"$O=\sigma^x$",
    "sigma_y": r"$O=\sigma^y$",
    "sigma_z": r"$O=\sigma^z$",
    **{
        f"sigma_{left}_sigma_{right}": rf"$O=\sigma^{left}\otimes\sigma^{right}$"
        for left in "xyz"
        for right in "xyz"
    },
}


def observable_math(observable: str) -> str:
    parts = observable.removeprefix("sigma_").split("_sigma_")
    if len(parts) == 1:
        return rf"\sigma^{parts[0]}"
    return rf"\sigma^{parts[0]}\otimes\sigma^{parts[1]}"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "Times New Roman", "DejaVu Serif"],
            "mathtext.fontset": "cm",
            "axes.linewidth": 0.58,
            "xtick.major.width": 0.58,
            "ytick.major.width": 0.58,
            "xtick.minor.width": 0.45,
            "ytick.minor.width": 0.45,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def read_csvs(pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(SHARDS.glob(pattern)):
        with path.open(encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                row: dict[str, Any] = dict(raw)
                for key in ("length", "dimension", "shell_width", "count"):
                    if key in row and row[key]:
                        row[key] = int(row[key])
                for key in (
                    "beta",
                    "delta",
                    "log_d_count",
                    "energy_density",
                    "diagonal_entropy",
                    "participation_number",
                    "population",
                ):
                    if key in row and row[key]:
                        row[key] = float(row[key])
                rows.append(row)
    return rows


def select(rows: Iterable[dict[str, Any]], **conditions: Any) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if all(row.get(field) == value for field, value in conditions.items())
    ]


def xy(rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    ordered = sorted(rows, key=lambda row: row["delta"])
    return (
        np.asarray([row["delta"] for row in ordered]),
        np.asarray([row["log_d_count"] for row in ordered]),
    )


def save_exact(figure: plt.Figure, path: Path, width: int, height: int, dpi: int = 180) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.set_size_inches(width / dpi, height / dpi, forward=True)
    figure.savefig(path, dpi=dpi, bbox_inches=None, pad_inches=0)
    plt.close(figure)


def typicality_axes(axes: Iterable[plt.Axes], *, label_size: float, tick_size: float) -> None:
    for axis in axes:
        axis.set_xlim(0.0, 0.17)
        axis.set_ylim(0.0, 1.05)
        axis.set_xticks((0.0, 0.05, 0.10, 0.15))
        axis.set_yticks((0.2, 0.4, 0.6, 0.8, 1.0))
        axis.tick_params(
            top=True,
            right=False,
            labelsize=tick_size,
            length=3.6,
            pad=3.0,
        )
    for axis in axes:
        axis.xaxis.label.set_size(label_size)
        axis.yaxis.label.set_size(label_size)


def draw_curves(
    axis: plt.Axes,
    rows: list[dict[str, Any]],
    *,
    observable: str,
    beta: float,
    families: tuple[tuple[str, str], ...],
) -> None:
    for length in PAPER_SIZES:
        for family, linestyle in families:
            points = select(
                rows,
                length=length,
                beta=beta,
                observable=observable,
                family=family,
            )
            if not points:
                continue
            x, y = xy(points)
            axis.plot(
                x,
                y,
                linestyle=linestyle,
                color=COLORS[length],
                linewidth=0.72 + 0.11 * (length - 6),
                solid_capstyle="butt",
                dash_capstyle="butt",
            )


def add_size_legend(axis: plt.Axes, *, fontsize: float) -> None:
    handles = [
        plt.Line2D([], [], color=COLORS[length], linewidth=1.4, label=str(length))
        for length in reversed(PAPER_SIZES)
    ]
    axis.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.012, 0.008),
        frameon=False,
        fontsize=fontsize,
        handlelength=1.35,
        labelspacing=0.52,
        borderpad=0.0,
    )


def render_main_typicality(rows: list[dict[str, Any]]) -> Path:
    figure, axes = plt.subplots(2, 3, sharex=True, sharey=True)
    incoherence = {0.25: 0.96, 0.75: 0.84, 1.75: 0.75}
    for row_index, observable in enumerate(("sigma_z", "sigma_z_sigma_z")):
        for column, beta in enumerate(BETAS):
            axis = axes[row_index, column]
            draw_curves(
                axis,
                rows,
                observable=observable,
                beta=beta,
                families=(
                    ("leaf", "-"),
                    ("eth_nonintegrable", (0, (3.2, 3.2))),
                    ("eth_integrable", (0, (1.0, 2.5))),
                ),
            )
            axis.text(
                0.13 if row_index == 0 else 0.25,
                0.095,
                rf"$O={observable_math(observable)}\quad\beta={beta:g}$",
                transform=axis.transAxes,
                fontsize=13.0,
            )
            axis.text(
                0.15 if row_index == 0 else 0.35,
                0.025,
                rf"$(\mathfrak{{I}}[\mathcal{{L}}_H(\rho_\beta)]"
                rf"\!\approx\!{incoherence[beta]:.2f}\log d)$",
                transform=axis.transAxes,
                fontsize=10.0,
            )
    typicality_axes(axes.flat, label_size=18, tick_size=14.5)
    for axis in axes[:, 0]:
        axis.set_ylabel(r"$\log_d N_\Delta$", labelpad=8)
        axis.set_yticklabels(("0.2", "0.4", "0.6", "0.8", "1."))
    for axis in axes[-1, :]:
        axis.set_xlabel(r"$\Delta$", labelpad=10)
    for axis in axes[:, 1:].flat:
        axis.tick_params(labelleft=False)
    for axis in axes[0, :]:
        axis.tick_params(labelbottom=False)
    add_size_legend(axes[1, 0], fontsize=12)
    figure.subplots_adjust(left=0.078, right=0.923, bottom=0.116, top=0.883, wspace=0, hspace=0)
    output = OUTPUT / "t002_main_typicality_paper_style.png"
    save_exact(figure, output, 1620, 1080)
    return output


def render_supplemental(
    rows: list[dict[str, Any]],
    *,
    beta: float,
    filename: str,
    integrable: bool = False,
) -> Path:
    figure, axes = plt.subplots(4, 3, sharex=True, sharey=True)
    families = (
        ("leaf", "-"),
        ("eth_integrable" if integrable else "eth_nonintegrable", (0, (3.2, 3.2))),
    )
    for panel_index, (axis, observable) in enumerate(
        zip(axes.flat, OBSERVABLES, strict=True)
    ):
        draw_curves(
            axis,
            rows,
            observable=observable,
            beta=beta,
            families=families,
        )
        axis.text(
            0.25 if panel_index == 9 else 0.06,
            0.055,
            rf"$O={observable_math(observable)}$",
            transform=axis.transAxes,
            fontsize=12.5,
        )
    typicality_axes(axes.flat, label_size=17, tick_size=13.5)
    for axis in axes[:, 0]:
        axis.set_ylabel(r"$\log_d N_\Delta$", labelpad=7)
        axis.set_yticklabels(("0.2", "0.4", "0.6", "0.8", "1."))
    for axis in axes[-1, :]:
        axis.set_xlabel(r"$\Delta$", labelpad=9)
    for axis in axes[:, 1:].flat:
        axis.tick_params(labelleft=False)
    for axis in axes[:-1, :].flat:
        axis.tick_params(labelbottom=False)
    add_size_legend(axes[-1, 0], fontsize=11.5)
    figure.subplots_adjust(left=0.078, right=0.923, bottom=0.058, top=0.942, wspace=0, hspace=0)
    output = OUTPUT / filename
    save_exact(figure, output, 1620, 2160)
    return output


def render_dynamics() -> Path:
    with (DATA / "t003_dynamics.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in (
            "time",
            "display_offset",
            "mixed_exact",
            "representative",
            "lower_68",
            "upper_68",
            "lower_95",
            "upper_95",
        ):
            row[key] = float(row[key])
    specs = (
        ("sigma_x", "#e95b10", "o", r"$\sigma^x$"),
        ("sigma_y", "#5b6fc7", "s", r"$\sigma^y+0.4\mathrm{I}$"),
        ("sigma_z", "#f39a00", "D", r"$\sigma^z-0.2\mathrm{I}$"),
        ("sigma_x_sigma_x", "#aa42bb", "^", r"$\sigma^x\otimes\sigma^x+\mathrm{I}$"),
    )
    figure, axis = plt.subplots()
    for name, color, marker, label in specs:
        points = [row for row in rows if row["observable"] == name]
        x = np.asarray([row["time"] for row in points])
        offset = points[0]["display_offset"]
        mixed = np.asarray([row["mixed_exact"] + offset for row in points])
        representative = np.asarray([row["representative"] + offset for row in points])
        lower68 = np.asarray([row["lower_68"] + offset for row in points])
        upper68 = np.asarray([row["upper_68"] + offset for row in points])
        lower95 = np.asarray([row["lower_95"] + offset for row in points])
        upper95 = np.asarray([row["upper_95"] + offset for row in points])
        axis.fill_between(x, lower95, upper95, color=color, alpha=0.13, linewidth=0)
        axis.fill_between(x, lower68, upper68, color=color, alpha=0.23, linewidth=0)
        axis.plot(x, mixed, color=color, linewidth=2.0, label=label)
        axis.plot(
            x[::2],
            representative[::2],
            linestyle="none",
            marker=marker,
            markersize=5.8,
            color=color,
            markeredgewidth=0,
        )
    axis.axhline(0, color="#777777", linewidth=0.55)
    axis.set_xlim(-0.06, 3.06)
    axis.set_ylim(-2.0, 1.06)
    axis.set_xticks(np.arange(0.4, 3.0, 0.4))
    axis.set_yticks(np.arange(-1.4, 1.01, 0.3))
    axis.tick_params(top=False, right=False, labelsize=17, length=4)
    axis.set_xlabel(r"$t$", fontsize=23, labelpad=17)
    axis.set_ylabel(r"$\langle O\rangle$", fontsize=19, labelpad=8)
    axis.legend(
        loc="lower center",
        bbox_to_anchor=(0.52, 0.035),
        frameon=False,
        fontsize=17,
        handlelength=1.25,
        labelspacing=0.55,
    )
    figure.subplots_adjust(left=157 / 810, right=808 / 810, bottom=140 / 810, top=788 / 810)
    output = OUTPUT / "t003_dynamics_paper_style.png"
    save_exact(figure, output, 810, 810)
    return output


def render_compression(rows: list[dict[str, Any]], filename: str) -> Path:
    figure, axes = plt.subplots(1, 3, sharex=True, sharey=True)
    for axis, beta in zip(axes, BETAS, strict=True):
        for decomposition, color, label in (
            ("min_variance", "#e95b10", "min-var"),
            ("eigen", "#5b6fc7", "eigen"),
        ):
            points = select(rows, length=12, beta=beta, decomposition=decomposition)
            axis.scatter(
                [point["energy_density"] for point in points],
                [point["participation_number"] for point in points],
                s=1.8,
                color=color,
                alpha=0.95,
                linewidths=0,
                rasterized=True,
                label=label,
            )
        axis.set_xlim(-1.7, 1.8)
        axis.set_ylim(1, 3200)
        axis.set_yscale("log")
        axis.set_xticks(np.arange(-1.5, 1.6, 0.5))
        axis.tick_params(top=True, right=True, which="both", labelsize=13.5, length=3.5)
        axis.text(0.69, 0.88, rf"$\beta={beta:g}$", transform=axis.transAxes, fontsize=15)
        axis.set_xlabel(r"$E/L$", fontsize=20, labelpad=9)
    axes[0].set_ylabel(r"$e^{S_{\mathrm{vN}}[\overline{\Pi_i}]}$", fontsize=18, labelpad=10)
    handles = [
        plt.Line2D([], [], color="#e95b10", marker="o", linestyle="none", markersize=4, label="min-var"),
        plt.Line2D([], [], color="#5b6fc7", marker="o", linestyle="none", markersize=4, label="eigen"),
    ]
    axes[0].legend(
        handles=handles,
        loc="upper left",
        frameon=False,
        fontsize=14,
        handlelength=0.7,
        labelspacing=0.65,
        borderpad=0.0,
    )
    for axis in axes[1:]:
        axis.tick_params(labelleft=False)
    figure.subplots_adjust(left=0.089, right=0.912, bottom=0.20, top=0.799, wspace=0)
    output = OUTPUT / filename
    save_exact(figure, output, 1620, 720)
    return output


def entropy_gain(rows: list[dict[str, Any]], group: str, length: int, beta: float) -> float:
    subset = select(rows, group=group, length=length, beta=beta)
    means: dict[str, float] = {}
    for decomposition in ("eigen", "min_variance"):
        points = [row for row in subset if row["decomposition"] == decomposition]
        means[decomposition] = sum(
            point["population"] * point["diagonal_entropy"] for point in points
        )
    return (means["eigen"] - means["min_variance"]) / length


def render_gain(rows: list[dict[str, Any]]) -> Path:
    figure, axes = plt.subplots(1, 2, sharex=True, sharey=True)
    specs = (
        (0.25, "#e95b10", "o"),
        (0.75, "#5b6fc7", "s"),
        (1.75, "#f39a00", "D"),
    )
    lengths = (8, 9, 10, 11, 12)
    for axis, (group, h0z) in zip(
        axes,
        (("main", 1.5), ("supplemental", 0.5)),
        strict=True,
    ):
        for beta, color, marker in specs:
            values = [entropy_gain(rows, group, length, beta) for length in lengths]
            axis.plot(
                lengths,
                values,
                linestyle="none",
                marker=marker,
                markersize=6.8,
                color=color,
                markeredgewidth=0,
                label=f"{beta:g}",
            )
        axis.set_xlim(7.8, 12.2)
        axis.set_ylim(0.0, 0.4)
        axis.set_xticks(lengths)
        axis.set_yticks(np.arange(0.0, 0.41, 0.1))
        axis.minorticks_on()
        axis.grid(which="major", color="#777777", linewidth=0.45)
        axis.tick_params(top=True, right=True, which="both", labelsize=15)
        axis.set_xlabel(r"$L$", fontsize=21, labelpad=7)
        axis.text(
            0.64,
            0.57,
            rf"$h_{{0,z}}={h0z:g}$",
            transform=axis.transAxes,
            fontsize=16.5,
            bbox={"facecolor": "#fffed5", "edgecolor": "none", "pad": 2.0},
        )
    axes[0].set_ylabel(
        r"$\frac{1}{L}\left(\overline{S}^{\mathrm{eig}}_{\mathrm{diag}}"
        r"-\overline{S}^{\mathrm{mv}}_{\mathrm{diag}}\right)$",
        fontsize=16,
        labelpad=3,
    )
    axes[1].tick_params(labelleft=False)
    axes[1].legend(
        loc="center left",
        bbox_to_anchor=(1.22, 0.51),
        frameon=False,
        fontsize=16,
        handlelength=0.8,
        labelspacing=0.9,
    )
    figure.subplots_adjust(left=0.078, right=0.641, bottom=0.174, top=0.825, wspace=0)
    output = OUTPUT / "t009_entropy_gain_paper_style.png"
    save_exact(figure, output, 1620, 720)
    return output


def render_spin1() -> Path:
    transverse_components = np.asarray(
        [0.0, 0.12, 0.24, 0.36, 0.48, 0.60, 0.72, 0.82, 0.90, 0.96]
    )
    betas = np.linspace(-10, 10, 241)
    cmap = LinearSegmentedColormap.from_list(
        "paper_leaf",
        ["#fbf7dd", "#eadcc0", "#caae8a"],
    )
    entropy_max = math.log(3)
    figure = plt.figure()
    axes = (
        figure.add_axes((0.065, 0.47, 0.29, 0.45)),
        figure.add_axes((0.365, 0.47, 0.30, 0.45)),
    )
    projections = (
        lambda point: np.asarray(
            [
                0.50 + 0.42 * point[1] + 0.04 * point[0],
                (point[2] + 2 / np.sqrt(3)) / np.sqrt(3) * (0.82 + 0.14 * point[0]),
            ]
        ),
        lambda point: np.asarray(
            [
                0.47 + 0.33 * point[1] + 0.18 * point[0],
                (point[2] + 2 / np.sqrt(3)) / np.sqrt(3)
                * (0.82 + 0.10 * point[0] + 0.13 * point[1]),
            ]
        ),
    )
    for axis, project in zip(axes, projections, strict=True):
        for transverse in transverse_components:
            vertices = leaf.spin1_leaf_vertices(float(transverse))
            canonical = leaf.spin1_leaf_canonical_curve(float(transverse), betas)
            entropy = leaf.spin1_barycenter_entropy(float(transverse))
            color = cmap(np.clip(1 - entropy / entropy_max, 0, 1))
            projected_vertices = np.asarray([project(point) for point in vertices])
            projected_canonical = np.asarray([project(point) for point in canonical])
            axis.add_patch(
                Polygon(
                    projected_vertices,
                    closed=True,
                    facecolor=color,
                    edgecolor="none",
                    alpha=0.48,
                )
            )
            axis.plot(
                projected_canonical[:, 0],
                projected_canonical[:, 1],
                color="black",
                linewidth=1.15,
            )
        axis.set_xlim(0, 1)
        axis.set_ylim(-0.02, 1)
        axis.set_aspect("equal", adjustable="box")
        axis.set_axis_off()
    output = OUTPUT / "t001_spin1_foliation_paper_style.png"
    save_exact(figure, output, 2560, 1920, dpi=200)
    return output


def main() -> int:
    configure_style()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    main_rows = read_csvs("main_L*_typicality.csv")
    supplemental_rows = read_csvs("supplemental_L*_typicality.csv")
    integrable_rows = read_csvs("integrable_L*_typicality.csv")
    main_compression = read_csvs("main_L*_compression.csv")
    supplemental_compression = read_csvs("supplemental_L*_compression.csv")

    outputs = [
        render_spin1(),
        render_main_typicality(main_rows),
        render_dynamics(),
        render_supplemental(
            supplemental_rows,
            beta=0.25,
            filename="t004_s1_beta025_paper_style.png",
        ),
        render_supplemental(
            supplemental_rows,
            beta=0.75,
            filename="t005_s2_beta075_paper_style.png",
        ),
        render_supplemental(
            supplemental_rows,
            beta=1.75,
            filename="t006_s3_beta175_paper_style.png",
        ),
        render_supplemental(
            integrable_rows,
            beta=0.25,
            filename="t007_s4_integrable_paper_style.png",
            integrable=True,
        ),
        render_compression(main_compression, "t008a_main_compression_paper_style.png"),
        render_compression(
            supplemental_compression,
            "t008b_supp_compression_paper_style.png",
        ),
        render_gain(main_compression + supplemental_compression),
    ]
    print("\n".join(str(path.relative_to(WORKSPACE)) for path in outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
