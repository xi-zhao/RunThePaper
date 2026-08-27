#!/usr/bin/env python3
"""Run the Fig. 2(a-c) open-chain spectrum pilot."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nonhermitian_ssh import (  # noqa: E402
    analytic_transition,
    branch_tracked_spectrum_rows,
    chiral_pair_residual,
    open_chain_eigenvalues,
)


def main() -> int:
    L = 40
    t2 = 1.0
    gamma = 4.0 / 3.0
    t1_values = np.linspace(-3.0, 3.0, 301)

    data_path = ROOT / "outputs/data/fig2_open_spectrum.csv"
    figure_path = ROOT / "outputs/figures/fig2_open_spectrum.png"
    abs_panel_path = ROOT / "outputs/figures/fig2_abs_panel.png"
    real_panel_path = ROOT / "outputs/figures/fig2_real_panel.png"
    imag_panel_path = ROOT / "outputs/figures/fig2_imag_panel.png"
    checks_path = ROOT / "outputs/checks/fig2_open_spectrum.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    abs_panel_path.parent.mkdir(parents=True, exist_ok=True)
    real_panel_path.parent.mkdir(parents=True, exist_ok=True)
    imag_panel_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.parent.mkdir(parents=True, exist_ok=True)

    eigenvalue_slices = []
    spectral_summary = []
    chiral_residuals = []
    direct_chiral_residuals = []

    for t1 in t1_values:
        eig = open_chain_eigenvalues(L=L, t1=float(t1), t2=t2, gamma=gamma, method="chiral_block")
        direct_eig = open_chain_eigenvalues(L=L, t1=float(t1), t2=t2, gamma=gamma, method="direct")
        eigenvalue_slices.append(eig)
        abs_sorted = np.sort(np.abs(eig))
        spectral_summary.append(
            {
                "t1": float(t1),
                "abs0": float(abs_sorted[0]),
                "abs1": float(abs_sorted[1]),
                "abs2": float(abs_sorted[2]),
                "abs3": float(abs_sorted[3]),
            }
        )
        chiral_residuals.append(chiral_pair_residual(eig))
        direct_chiral_residuals.append(chiral_pair_residual(direct_eig))

    rows = branch_tracked_spectrum_rows(t1_values, eigenvalue_slices)

    with data_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["t1", "branch_id", "band_index", "real_E", "imag_E", "abs_E"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    plot_from_rows(rows, figure_path)
    plot_abs_panel(rows, abs_panel_path)
    plot_real_panel(rows, real_panel_path)
    plot_imag_panel(rows, imag_panel_path)

    transition = analytic_transition(t2=t2, gamma=gamma)
    complex_window_abs_t1 = gamma / 2.0
    max_imag_outside_window = max(
        abs(row["imag_E"])
        for row in rows
        if abs(row["t1"]) > complex_window_abs_t1 + 1e-12
    )
    probes = {
        "center": spectrum_at_t1(spectral_summary, 0.0),
        "inside_positive": spectrum_at_t1(spectral_summary, 1.0),
        "inside_negative": spectrum_at_t1(spectral_summary, -1.0),
        "near_positive_transition": spectrum_at_t1(spectral_summary, 1.2),
        "outside_positive": spectrum_at_t1(spectral_summary, 1.4),
        "outside_negative": spectrum_at_t1(spectral_summary, -1.4),
    }
    zero_mode_tol = 1e-3
    outside_gap_tol = 5e-2
    imaginary_tail_tol = 1e-8
    max_chiral = float(max(chiral_residuals))
    max_direct_chiral = float(max(direct_chiral_residuals))
    pass_flags = {
        "chiral_pairing": max_chiral < 1e-8,
        "no_spurious_imaginary_tail": max_imag_outside_window < imaginary_tail_tol,
        "inside_zero_modes": max(
            probes["center"]["abs1"],
            probes["inside_positive"]["abs1"],
            probes["inside_negative"]["abs1"],
        )
        < zero_mode_tol,
        "outside_zero_modes_absent": min(
            probes["outside_positive"]["abs1"],
            probes["outside_negative"]["abs1"],
        )
        > outside_gap_tol,
        "finite_size_gap_near_transition": probes["near_positive_transition"]["abs1"]
        < probes["outside_positive"]["abs1"],
    }

    checks = {
        "target": "T001",
        "L": L,
        "t2": t2,
        "gamma": gamma,
        "t1_points": len(t1_values),
        "analytic_transition_abs_t1": transition,
        "bloch_gap_closing_abs_t1": [1.0 / 3.0, 5.0 / 3.0],
        "complex_spectrum_abs_t1_window": complex_window_abs_t1,
        "max_imag_outside_gamma_half_window": max_imag_outside_window,
        "probe_spectra": probes,
        "tolerances": {
            "zero_mode_abs_E": zero_mode_tol,
            "outside_min_abs_E": outside_gap_tol,
            "chiral_pair_residual": 1e-8,
            "imaginary_tail_outside_gamma_half_window": imaginary_tail_tol,
        },
        "eigenvalue_method": "chiral_block",
        "spectrum_line_identity": "eigenvalue_continuation_branch",
        "spectrum_connect_rule": "connect_within_branch_id_in_t1_order",
        "abs_panel_render": "outputs/figures/fig2_abs_panel.png",
        "abs_panel_render_source": "independent_open_chain_numerics",
        "real_panel_render": "outputs/figures/fig2_real_panel.png",
        "real_panel_render_source": "independent_open_chain_numerics",
        "imag_panel_render": "outputs/figures/fig2_imag_panel.png",
        "imag_panel_render_source": "independent_open_chain_numerics",
        "max_chiral_pair_residual": max_chiral,
        "max_direct_eig_chiral_pair_residual": max_direct_chiral,
        "pass_flags": pass_flags,
        "status": "physically_consistent" if all(pass_flags.values()) else "partial",
        "notes": [
            "No digitized paper curve is used yet.",
            "The transition value is taken from the paper's analytic expression.",
            "Finite L=40 data has a nonzero gap near the thermodynamic transition, so transition fitting is not used as a hard check.",
            "Direct dense eig is numerically unstable near strongly non-normal points; the run uses the chiral block structure.",
        ],
    }

    with checks_path.open("w") as f:
        json.dump(checks, f, indent=2)
        f.write("\n")

    print(json.dumps(checks, indent=2))
    return 0


def plot_from_rows(rows: list[dict[str, float]], figure_path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.0), sharex=True)
    plot_spectrum_branches(axes[0], rows, "abs_E")
    axes[0].set_ylabel("|E|")
    plot_spectrum_branches(axes[1], rows, "real_E")
    axes[1].set_ylabel("Re(E)")
    plot_spectrum_branches(axes[2], rows, "imag_E")
    axes[2].set_ylabel("Im(E)")
    axes[2].set_xlabel("t1")

    transition = analytic_transition()
    bloch_points = [1.0 - 2.0 / 3.0, 1.0 + 2.0 / 3.0, -1.0 + 2.0 / 3.0, -1.0 - 2.0 / 3.0]
    for ax in axes:
        ax.axvline(transition, color="tab:red", linewidth=1.0, alpha=0.8)
        ax.axvline(-transition, color="tab:red", linewidth=1.0, alpha=0.8)
        for point in bloch_points:
            ax.axvline(point, color="tab:blue", linewidth=0.7, alpha=0.25)
        ax.grid(True, alpha=0.18)

    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def plot_abs_panel(rows: list[dict[str, float]], figure_path: Path) -> None:
    fig = plt.figure(figsize=(9.21, 6.05))
    ax = fig.add_axes([0.095, 0.18, 0.875, 0.79])
    plot_spectrum_branches(ax, rows, "abs_E", linewidth=0.82, alpha=1.0)
    transition = analytic_transition()
    ax.plot(
        [-transition, transition],
        [0.0, 0.0],
        color="red",
        linewidth=3.0,
        solid_capstyle="round",
        zorder=5,
    )

    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(0.0, 3.95)
    ax.set_xticks([-3, -2, -1, 0, 1, 2, 3])
    ax.set_yticks([0, 1, 2, 3])
    ax.tick_params(direction="in", top=True, right=True, length=7, width=1.0, labelsize=22)
    ax.set_xlabel(r"$t_1$", fontsize=28, labelpad=12)
    ax.set_ylabel(r"$|E|$", fontsize=28, labelpad=10)
    ax.text(-0.075, 0.995, r"(a)", transform=ax.transAxes, fontsize=34, va="top", ha="left", clip_on=False)

    arrow_style = dict(arrowstyle="->", color="#45d7ff", linewidth=2.0, shrinkA=2, shrinkB=2)
    ax.annotate(
        r"$t_2-\gamma/2$",
        xy=(0.35, 0.0),
        xytext=(-0.35, 0.45),
        textcoords="data",
        fontsize=26,
        ha="center",
        color="0.2",
        arrowprops=arrow_style,
        annotation_clip=False,
    )
    ax.annotate(
        r"$t_2+\gamma/2$",
        xy=(1.70, 0.0),
        xytext=(2.15, 0.45),
        textcoords="data",
        fontsize=26,
        ha="center",
        color="0.2",
        arrowprops=arrow_style,
        annotation_clip=False,
    )
    ax.annotate(
        r"$\sqrt{t_2^2+(\gamma/2)^2}$",
        xy=(transition, 0.0),
        xytext=(1.95, -0.55),
        textcoords="data",
        fontsize=26,
        ha="center",
        color="0.2",
        arrowprops=arrow_style,
        annotation_clip=False,
    )

    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def plot_real_panel(rows: list[dict[str, float]], figure_path: Path) -> None:
    fig = plt.figure(figsize=(9.61, 7.44))
    ax = fig.add_axes([0.18, 0.235, 0.81, 0.73])
    plot_spectrum_branches(ax, rows, "real_E", linewidth=0.84, alpha=1.0)
    transition = analytic_transition()
    ax.plot(
        [-transition, transition],
        [0.0, 0.0],
        color="red",
        linewidth=3.0,
        solid_capstyle="round",
        zorder=5,
    )

    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(-4.0, 4.0)
    ax.set_xticks([-2, 0, 2])
    ax.set_yticks([-4, -2, 0, 2, 4])
    ax.tick_params(direction="in", top=True, right=True, length=7, width=1.0, labelsize=34, pad=8)
    ax.set_xlabel(r"$t_1$", fontsize=44, labelpad=18)
    ax.set_ylabel(r"$\mathrm{Re}(E)$", fontsize=44, labelpad=10)
    ax.text(-0.21, 1.035, r"(b)", transform=ax.transAxes, fontsize=58, va="top", ha="left", clip_on=False)

    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def plot_imag_panel(rows: list[dict[str, float]], figure_path: Path) -> None:
    fig = plt.figure(figsize=(9.63, 7.10))
    ax = fig.add_axes([0.145, 0.255, 0.84, 0.69])
    ax.axhline(0.0, color="black", linewidth=1.1, zorder=1)
    plot_complex_window_imaginary_branches(ax, rows, linewidth=0.95, alpha=1.0)
    transition = analytic_transition()
    ax.plot(
        [-transition, transition],
        [0.0, 0.0],
        color="red",
        linewidth=3.0,
        solid_capstyle="round",
        zorder=5,
    )

    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(-0.7, 0.7)
    ax.set_xticks([-2, 0, 2])
    ax.set_yticks([-0.5, 0, 0.5])
    ax.tick_params(direction="in", top=True, right=True, length=7, width=1.0, labelsize=34, pad=8)
    ax.set_xlabel(r"$t_1$", fontsize=44, labelpad=18)
    ax.set_ylabel(r"$\mathrm{Im}(E)$", fontsize=44, labelpad=10)
    ax.yaxis.set_label_coords(-0.08, 0.5)
    ax.text(-0.145, 1.075, r"(c)", transform=ax.transAxes, fontsize=58, va="top", ha="left", clip_on=False)

    ax.annotate(
        r"$\sqrt{t_2^2+(\gamma/2)^2}$",
        xy=(transition, 0.0),
        xytext=(1.8, 0.48),
        textcoords="data",
        fontsize=34,
        ha="center",
        color="0.15",
        arrowprops=dict(arrowstyle="->", color="#45d7ff", linewidth=2.0, shrinkA=2, shrinkB=2),
        annotation_clip=False,
    )

    save_exact_pixel_size(fig, figure_path, (962, 710), dpi=100)
    plt.close(fig)


def save_exact_pixel_size(fig: plt.Figure, figure_path: Path, size: tuple[int, int], dpi: int) -> None:
    fig.savefig(figure_path, dpi=dpi)
    with Image.open(figure_path) as image:
        if image.size == size:
            return
        width, height = size
        if image.width >= width and image.height >= height:
            image.crop((0, 0, width, height)).save(figure_path)
        else:
            image.resize(size).save(figure_path)


def plot_complex_window_imaginary_branches(
    ax: plt.Axes,
    rows: list[dict[str, float]],
    linewidth: float,
    alpha: float,
) -> None:
    window = 4.0 / 3.0 / 2.0
    for branch_id in sorted({int(row["branch_id"]) for row in rows}):
        branch_rows = [
            row
            for row in rows
            if int(row["branch_id"]) == branch_id and abs(float(row["t1"])) <= window + 1e-12
        ]
        branch_rows.sort(key=lambda row: row["t1"])
        if len(branch_rows) < 2:
            continue
        ax.plot(
            [row["t1"] for row in branch_rows],
            [row["imag_E"] for row in branch_rows],
            color="black",
            linewidth=linewidth,
            alpha=alpha,
            zorder=3,
        )


def plot_spectrum_branches(
    ax: plt.Axes,
    rows: list[dict[str, float]],
    y_key: str,
    linewidth: float = 0.42,
    alpha: float = 0.62,
) -> None:
    for branch_id in sorted({int(row["branch_id"]) for row in rows}):
        branch_rows = [row for row in rows if int(row["branch_id"]) == branch_id]
        branch_rows.sort(key=lambda row: row["t1"])
        ax.plot(
            [row["t1"] for row in branch_rows],
            [row[y_key] for row in branch_rows],
            color="black",
            linewidth=linewidth,
            alpha=alpha,
        )


def spectrum_at_t1(spectral_summary: list[dict[str, float]], target_t1: float) -> dict[str, float]:
    return min(spectral_summary, key=lambda row: abs(row["t1"] - target_t1))


if __name__ == "__main__":
    raise SystemExit(main())
