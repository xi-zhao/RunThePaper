#!/usr/bin/env python3
"""Render broad and coarse OBC phase diagrams from independent activity data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
DATA = WORKSPACE / "outputs" / "data" / "obc_phase_activity_grid.npz"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"


def save(figure: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("png",):
        figure.savefig(FIGURE_DIR / f"{stem}.{suffix}", dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    data = np.load(DATA)
    measured_gamma = data["static_boundary_gamma"]
    measured_boundary = data["static_boundary_kappa"]
    valid = np.isfinite(measured_boundary)
    # The gamma=0 limit is singular for random basin selection; extend the
    # independently measured low-gamma value continuously.  At gamma=1 the
    # static and exact vacuum boundaries meet at kappa=2.
    interpolation_gamma = np.r_[0.0, measured_gamma[valid], 1.0]
    interpolation_boundary = np.r_[
        measured_boundary[valid][0], measured_boundary[valid], 2.0
    ]
    order = np.argsort(interpolation_gamma)
    unique_gamma, unique_index = np.unique(interpolation_gamma[order], return_index=True)
    unique_boundary = interpolation_boundary[order][unique_index]
    gamma_left = np.linspace(0.0, 1.0, 401)
    dynamic_static = np.interp(gamma_left, unique_gamma, unique_boundary)
    vacuum_left = np.interp(
        gamma_left, data["broad_gamma"], data["vacuum_boundary"]
    )

    figure, axis = plt.subplots(figsize=(4.6, 5.2))
    axis.fill_between(gamma_left, 0, vacuum_left, color="#f2c14e", label=r"vacuum $\alpha_j=0$")
    axis.fill_between(gamma_left, vacuum_left, dynamic_static, color="#57b89c", label=r"dynamic $\partial_t\alpha_j\ne0$")
    axis.fill_between(gamma_left, dynamic_static, 3, color="#4c9ac2", label=r"static $\alpha_j\ne0$")
    right_start = int(np.searchsorted(data["broad_gamma"], 1.0))
    gamma_right = data["broad_gamma"][right_start:]
    vacuum_right = data["vacuum_boundary"][right_start:]
    axis.fill_between(gamma_right, 0, vacuum_right, color="#f2c14e")
    axis.fill_between(gamma_right, vacuum_right, 3, color="#4c9ac2")
    axis.plot(data["broad_gamma"], data["vacuum_boundary"], color="black", lw=2, label="Eq. (5)")
    axis.plot(gamma_left, dynamic_static, color="red", lw=2, label="long-time activity boundary")
    axis.scatter(measured_gamma[valid], measured_boundary[valid], color="red", s=18, zorder=4)
    axis.set(xlim=(0, 3), ylim=(0, 3), xlabel=r"$\gamma/J$", ylabel=r"$\kappa/J$", title="Main Fig. 3(a) — broad OBC phase structure")
    axis.grid(alpha=0.22)
    axis.legend(fontsize=7, loc="upper right")
    save(figure, "main_fig3a_obc_phase_structure_independent")

    figure, axes = plt.subplots(1, 2, figsize=(9.8, 4.0), sharex=True, sharey=True)
    gamma = data["gamma_axis"]
    kappa = data["kappa_axis"]
    image0 = axes[0].pcolormesh(
        gamma,
        kappa,
        np.maximum(data["mean_abs_rhs"].T, 1e-6),
        shading="auto",
        cmap="magma",
        norm=LogNorm(1e-6, max(1.0, float(np.max(data["mean_abs_rhs"])))),
    )
    image1 = axes[1].pcolormesh(
        gamma,
        kappa,
        np.maximum(data["mean_abs_density_rate"].T, 1e-7),
        shading="auto",
        cmap="viridis",
        norm=LogNorm(1e-7, max(0.1, float(np.max(data["mean_abs_density_rate"])))),
    )
    axes[0].set(title=r"total activity $\langle|\dot\alpha|\rangle$", xlabel=r"$\gamma/J$", ylabel=r"$\kappa/J$")
    axes[1].set(title=r"amplitude activity $\langle|\partial_t r^2|\rangle$", xlabel=r"$\gamma/J$")
    figure.colorbar(image0, ax=axes[0], pad=0.02)
    figure.colorbar(image1, ax=axes[1], pad=0.02)
    figure.suptitle("Main Fig. 4(a) diagnostic — coarse basin scan (fine stripes not claimed)", fontsize=11)
    save(figure, "main_fig4a_coarse_activity_independent")


if __name__ == "__main__":
    main()
