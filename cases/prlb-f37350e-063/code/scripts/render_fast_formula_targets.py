#!/usr/bin/env python3
"""Render paper-style figures exclusively from independently generated NPZ data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"


def save_figure(figure: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("png",):
        figure.savefig(FIGURE_DIR / f"{stem}.{suffix}", dpi=220, bbox_inches="tight")
    plt.close(figure)


def render_fig1() -> None:
    data = np.load(DATA_DIR / "fig1_linear_spectra.npz")
    figure, axes = plt.subplots(1, 3, figsize=(9.2, 3.25), sharey=True)
    titles = {
        "b": r"(b) $\gamma<J,\ \theta=\pi$",
        "c": r"(c) $\gamma>J,\ \theta=\pi$",
        "d": r"(d) $\theta=\pi/2$",
    }
    for axis, label in zip(axes, "bcd", strict=True):
        pbc = data[f"{label}_pbc"]
        obc = data[f"{label}_obc"]
        axis.scatter(obc.real, obc.imag, s=22, color="#4c72b0", label="OBC", zorder=3)
        axis.scatter(pbc.real, pbc.imag, s=28, color="#55a868", label="PBC", zorder=2)
        axis.set_title(titles[label], loc="left")
        axis.set_xlabel(r"$\mathrm{Re}(E)/J$")
        axis.grid(alpha=0.35)
        axis.set_xlim(-2.2, 2.2)
    axes[0].set_ylabel(r"$\mathrm{Im}(E)/J$")
    axes[-1].legend(frameon=True, loc="lower right")
    figure.suptitle("Independent Eq. (1) reproduction", y=1.02, fontsize=11)
    save_figure(figure, "main_fig1_bcd_independent")


def render_fig2() -> None:
    data = np.load(DATA_DIR / "fig2_pbc_stability.npz")
    q = data["q_grid"]
    kappa = data["kappa_grid"]
    stable = data["stable_amplitude"]
    figure, axis = plt.subplots(figsize=(6.4, 4.5))
    mesh = axis.pcolormesh(q, kappa, stable, shading="auto", cmap="viridis", vmin=0, vmax=3.2)
    finite_q = np.broadcast_to(data["finite_q"], data["finite_stable"].shape)
    finite_kappa = np.broadcast_to(data["finite_kappa"][:, None], data["finite_stable"].shape)
    mask = data["finite_stable"].astype(bool)
    colors = data["finite_frequency"][mask]
    axis.scatter(
        finite_q[mask],
        finite_kappa[mask],
        c=colors,
        cmap="RdBu",
        norm=Normalize(-2, 2),
        s=15,
        edgecolors="none",
    )
    axis.plot(q, data["decay_curve"], color="red", lw=1.8, label=r"$\gamma_q/J$")
    axis.set_xlim(-np.pi, np.pi)
    axis.set_ylim(0, 10)
    axis.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
    axis.set_xticklabels([r"$-\pi$", r"$-\pi/2$", "0", r"$\pi/2$", r"$\pi$"])
    axis.set_xlabel(r"$q$")
    axis.set_ylabel(r"$\kappa/J$")
    axis.grid(alpha=0.28)
    axis.legend(loc="upper left", bbox_to_anchor=(0.03, 0.43))
    colorbar = figure.colorbar(mesh, ax=axis, pad=0.02)
    colorbar.set_label(r"$r_q\sqrt{\Gamma/J}$")
    axis.set_title("Main Fig. 2 — stability from the displayed 2×2 matrix", fontsize=10)
    save_figure(figure, "main_fig2_pbc_stability_independent")


def render_fig3_static() -> None:
    data = np.load(DATA_DIR / "fig3_static_kink.npz")
    figure = plt.figure(figsize=(11.8, 6.2))
    grid = figure.add_gridspec(2, 2, width_ratios=(0.8, 1.8), hspace=0.42, wspace=0.3)
    phase = figure.add_subplot(grid[:, 0])
    profiles = figure.add_subplot(grid[0, 1])
    mean = figure.add_subplot(grid[1, 1])

    gamma = data["phase_gamma"]
    boundary = data["vacuum_boundary"]
    phase.fill_between(gamma, 0, boundary, color="#f2c14e", alpha=0.9, label=r"vacuum $\alpha_j=0$")
    phase.fill_between(gamma, boundary, 3, color="#4c9ac2", alpha=0.85, label="condensed/dynamic")
    phase.plot(gamma, boundary, color="black", lw=1.8, label="Eq. (5) boundary")
    phase.set(xlim=(0, 3), ylim=(0, 3), xlabel=r"$\gamma/J$", ylabel=r"$\kappa/J$")
    phase.set_title("(a) exact vacuum boundary", loc="left")
    phase.legend(fontsize=8, loc="upper right")
    phase.grid(alpha=0.25)

    sites = np.arange(1, int(data["n"]) + 1)
    cmap = plt.get_cmap("viridis")
    for index, (profile, log_delta) in enumerate(zip(data["profiles"], data["log_deltas"], strict=True)):
        kappa = float(data["finite_threshold"] + 10.0**log_delta)
        profiles.plot(
            sites,
            np.abs(profile) / np.sqrt(kappa),
            lw=2.1,
            color=cmap(index / 3),
            label=fr"$\log_{{10}}(\kappa-\kappa_c)={log_delta:.1f}$",
        )
    profiles.set(xlim=(1, 200), ylim=(-0.03, 1.05), xlabel="site $j$", ylabel=r"$r_j^s\sqrt{\Gamma/\kappa}$")
    profiles.set_title("(b) independently solved static kink", loc="left")
    profiles.grid(alpha=0.28)
    profiles.legend(fontsize=7, ncol=2)

    mean.plot(data["mean_kappa"], data["mean_amplitude"], color="#4c72b0", lw=2)
    mean.axvline(float(data["finite_threshold"]), color="black", lw=0.8, ls="--")
    mean.set(xlim=(0, 2), ylim=(-0.03, 1.04), xlabel=r"$\kappa/J$", ylabel=r"$\langle r_j\rangle_j\sqrt{\Gamma/\kappa}$")
    mean.set_title("(c) stable static branch; inset: Eq. (5) scaling", loc="left")
    mean.grid(alpha=0.28)
    inset = mean.inset_axes([0.53, 0.18, 0.43, 0.55])
    inset.loglog(data["exponent_delta"], data["kink_position"], "o", ms=3.5)
    beta = float(data["fitted_exponent"])
    fit = 10.0 ** float(data["fitted_intercept"]) * data["exponent_delta"] ** beta
    inset.loglog(data["exponent_delta"], fit, lw=1.4, label=fr"$\beta={beta:.3f}$")
    inset.set_xlabel(r"$\kappa-\kappa_c$", fontsize=7)
    inset.set_ylabel("kink position", fontsize=7)
    inset.tick_params(labelsize=7)
    inset.legend(fontsize=7)
    inset.grid(alpha=0.2)
    save_figure(figure, "main_fig3_abc_formula_portion_independent")


def main() -> None:
    render_fig1()
    render_fig2()
    render_fig3_static()


if __name__ == "__main__":
    main()
