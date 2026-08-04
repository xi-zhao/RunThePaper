#!/usr/bin/env python3
"""Render the two decisive idx88 asymptotic/spectral counterchecks."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]


def main() -> None:
    data = json.loads((WORKSPACE / "outputs" / "data" / "idx88_gold_audit.json").read_text())
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 6.8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.3,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.65), constrained_layout=True)
    colors = ["#0072B2", "#009E73", "#E69F00", "#CC79A7"]
    for color, (lam, points) in zip(colors, data["task_2"]["numeric_sequences"].items(), strict=True):
        s_values = np.array([point["s"] for point in points])
        shifts = np.array([point["scaled_shift"] for point in points])
        axes[0].plot(s_values, shifts, "o-", color=color, label=rf"$\lambda={float(lam):g}$")
    axes[0].axhline(5.63, color="0.2", linestyle="--", label=r"$563/100$")
    axes[0].set_xscale("log")
    axes[0].invert_xaxis()
    axes[0].set_xlabel(r"$s$")
    axes[0].set_ylabel(r"$(\theta_\star-\theta_m)/s$ (rad)")
    axes[0].set_title("The magic-angle shift has a finite limit")
    axes[0].legend(frameon=False, ncol=2)
    axes[0].text(-0.13, 1.04, "a", transform=axes[0].transAxes, fontweight="bold", fontsize=9)

    rings = data["task_4"]["ring_norms"]
    sizes = np.array([row["N"] for row in rings])
    factors = np.array([row["factor"] for row in rings])
    axes[1].plot(sizes, factors, "o-", color="#0072B2", label=r"$\|H-H'\|/|J_0-J_1|$")
    axes[1].axhline(1.0, color="#D55E00", linestyle="--", label="frozen N-independent value")
    axes[1].set_xticks(sizes)
    axes[1].set_xlabel(r"ring size $N$")
    axes[1].set_ylabel("dimerization norm factor")
    axes[1].set_ylim(0.83, 1.02)
    axes[1].set_title("Exact homogenization retains ring parity")
    axes[1].legend(frameon=False, loc="lower right")
    axes[1].annotate(
        r"$\cos(\pi/6)$",
        xy=(6, factors[1]),
        xytext=(6.7, 0.88),
        arrowprops={"arrowstyle": "->", "linewidth": 0.7},
    )
    axes[1].text(-0.13, 1.04, "b", transform=axes[1].transAxes, fontweight="bold", fontsize=9)

    output = WORKSPACE / "outputs" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "idx88_gold_audit.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "idx88_gold_audit.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
