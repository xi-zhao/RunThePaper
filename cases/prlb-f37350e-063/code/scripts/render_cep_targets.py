#!/usr/bin/env python3
"""Render Supplemental Fig. S1 from independent Jacobian continuation data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
DATA = WORKSPACE / "outputs" / "data" / "supp_fig_s1_cep.npz"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"


def main() -> None:
    data = np.load(DATA)
    figure, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    colors = plt.get_cmap("tab10").colors
    for index, gamma in enumerate(data["gamma"]):
        axes[0].plot(
            data["distance"],
            data["lambda_2"][index],
            "o-",
            ms=3,
            lw=1.5,
            color=colors[index],
            label=fr"$\gamma={gamma:.1f}$",
        )
        axes[1].plot(
            data["distance"],
            data["angle_12"][index],
            "o-",
            ms=3,
            lw=1.5,
            color=colors[index],
            label=fr"$\gamma={gamma:.1f}$",
        )
    axes[0].set(xlim=(0, 0.015), ylim=(-0.26, 0.01), xlabel=r"$\kappa-\kappa_c$", ylabel=r"$\lambda_2/J$", title="(a) critical slowing")
    axes[1].set(xlim=(0, 0.015), ylim=(0, np.pi / 2), xlabel=r"$\kappa-\kappa_c$", ylabel=r"$\theta_{12}$", title="(b) eigenvector coalescence")
    axes[1].set_yticks([0, np.pi / 8, np.pi / 4, 3 * np.pi / 8, np.pi / 2])
    axes[1].set_yticklabels(["0", r"$\pi/8$", r"$\pi/4$", r"$3\pi/8$", r"$\pi/2$"])
    for axis in axes:
        axis.grid(alpha=0.25)
    axes[1].legend(fontsize=8)
    figure.suptitle("Supplemental Fig. S1 — independent static continuation and exact Jacobian", fontsize=11)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("png",):
        figure.savefig(
            FIGURE_DIR / f"supp_fig_s1_cep_independent.{suffix}",
            dpi=220,
            bbox_inches="tight",
        )
    plt.close(figure)


if __name__ == "__main__":
    main()
