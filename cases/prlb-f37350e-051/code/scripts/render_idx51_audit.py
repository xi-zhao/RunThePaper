#!/usr/bin/env python3
"""Render the benchmark-scope sign/root audit for PRL-Bench record 051.

Figure contract
---------------
Core conclusion: the frozen response sign contradicts the supplied positive
Hessian, while the independent l1 root agrees with the printed gold.
Archetype: compact diagnostic comparison, not a source-paper figure replica.
Evidence: normalized response coefficients, direct l1 evaluation, and the
Yukawa counterexample to the frozen high-q/large-r inference.
Export: 183 mm x 82 mm, editable PDF/SVG and 300 dpi PNG, with source CSV.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from lindhard_kernel import l1, response_audit, smallest_positive_root  # noqa: E402


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
        "axes.linewidth": 0.75,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
    }
)

NAVY = "#355C7D"
TEAL = "#3B8C88"
ROSE = "#B95F73"
GOLD = "#D49A35"
GRAY = "#56616A"
LIGHT = "#E9EDF0"


def main() -> None:
    mp.mp.dps = 80
    root = smallest_positive_root()
    response = response_audit(mp.mpf("0.5"))
    magnitude = float(response.lindhard_magnitude)
    response_rows = [
        ("frozen prompt", float(response.frozen_response_coefficient) / magnitude),
        ("gold K implies", float(response.response_implied_by_gold_hessian) / magnitude),
        ("1992 source", float(response.source_response_coefficient) / magnitude),
    ]

    x_values = np.linspace(0.0, 0.999, 700)
    y_values = np.array([float(l1(str(value))) for value in x_values])
    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "idx51_audit_figure.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["kind", "x_or_label", "value"])
        for label, value in response_rows:
            writer.writerow(["normalized_response", label, f"{value:.17g}"])
        for x, value in zip(x_values, y_values):
            writer.writerow(["l1_curve", f"{x:.17g}", f"{value:.17g}"])

    fig = plt.figure(figsize=(183 / 25.4, 82 / 25.4), constrained_layout=True)
    grid = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.25, 0.95])
    ax_sign = fig.add_subplot(grid[0, 0])
    ax_root = fig.add_subplot(grid[0, 1])
    ax_logic = fig.add_subplot(grid[0, 2])

    labels = [row[0] for row in response_rows]
    values = [row[1] for row in response_rows]
    colors = [ROSE, NAVY, TEAL]
    ax_sign.axhspan(-0.08, 0.08, color=LIGHT, zorder=0)
    ax_sign.bar(np.arange(3), values, color=colors, width=0.62)
    ax_sign.axhline(0, color=GRAY, lw=0.8)
    ax_sign.set_xticks(np.arange(3), labels, rotation=24, ha="right")
    ax_sign.set_ylabel(r"$(\delta\rho/\delta V)/l(0.5)$")
    ax_sign.set_ylim(-1.28, 1.28)
    ax_sign.set_title("Frozen sign fails closure", loc="left", weight="bold")
    ax_sign.text(-0.18, 1.04, "a", transform=ax_sign.transAxes, fontsize=8, weight="bold")
    for index, value in enumerate(values):
        ax_sign.text(index, value + (0.07 if value > 0 else -0.07), f"{value:+.0f}", ha="center", va="bottom" if value > 0 else "top")

    ax_root.axhline(0, color=GRAY, lw=0.8)
    ax_root.plot(x_values, y_values, color=NAVY, lw=1.4, label=r"independent $l_1(x)$")
    ax_root.scatter([float(root)], [0], s=28, color=GOLD, edgecolor="white", linewidth=0.5, zorder=3, label="independent root")
    ax_root.axvline(0.80540452397, color=ROSE, lw=1.0, ls="--", label="frozen gold")
    ax_root.set_xlabel(r"$x=q/(2k_F)$")
    ax_root.set_ylabel(r"$l_1(x)$")
    ax_root.set_xlim(0, 1)
    ax_root.set_ylim(min(-0.12, y_values.min() - 0.03), 1.05)
    ax_root.set_title("Printed root is numerically valid", loc="left", weight="bold")
    ax_root.legend(fontsize=6.2, loc="upper right")
    ax_root.grid(color="#E1E5E8", lw=0.5)
    ax_root.text(-0.16, 1.04, "b", transform=ax_root.transAxes, fontsize=8, weight="bold")

    ax_logic.axis("off")
    ax_logic.set_title("High-q does not fix large-r", loc="left", weight="bold")
    ax_logic.text(-0.12, 1.04, "c", transform=ax_logic.transAxes, fontsize=8, weight="bold")
    ax_logic.text(
        0.02,
        0.82,
        r"$H(q)=\frac{1}{q^2+1}\sim q^{-2}$",
        fontsize=8,
        color=NAVY,
        transform=ax_logic.transAxes,
    )
    ax_logic.annotate(
        "3D inverse Fourier transform",
        xy=(0.5, 0.60),
        xytext=(0.5, 0.71),
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "->", "color": GRAY, "lw": 0.9},
        xycoords="axes fraction",
        textcoords="axes fraction",
        fontsize=6.5,
        color=GRAY,
    )
    ax_logic.text(
        0.02,
        0.49,
        r"$h(r)=\frac{e^{-r}}{4\pi r}$",
        fontsize=8,
        color=TEAL,
        transform=ax_logic.transAxes,
    )
    ax_logic.text(
        0.02,
        0.28,
        r"$M_2=\int_0^\infty r^3e^{-r}\,dr=6$",
        fontsize=8,
        color=GOLD,
        transform=ax_logic.transAxes,
    )
    ax_logic.text(
        0.02,
        0.10,
        "Same q^-2 tail; finite moment.\nThe frozen inference is not valid.",
        fontsize=6.6,
        color=GRAY,
        transform=ax_logic.transAxes,
    )

    fig.suptitle("Independent audit of PRL-Bench record 051", x=0.01, ha="left", fontsize=9, weight="bold")
    base = figure_dir / "idx51_gold_audit"
    svg_path = base.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
