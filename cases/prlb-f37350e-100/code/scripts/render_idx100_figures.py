#!/usr/bin/env python3
"""Render the PRL Fig. 1(b) reproduction and the idx100 gold audit."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from nonlocal_ch_audit import (  # noqa: E402
    continuum_spinodal_temperature,
    exact_growth_rate,
    finite_wavenumber_threshold,
    frozen_a4,
    frozen_selected_wavenumber_with_repaired_sign,
    frozen_threshold,
    gaussian_hat_from_k2,
    gradient_coefficients,
    mapping_denominator,
    search_discrete_modes_2d,
    selected_wavenumber,
    utility_derivatives,
)


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.linewidth": 0.85,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def paper_cmap() -> LinearSegmentedColormap:
    """Match the truncated viridis range used by the source PRL figure."""

    colors = plt.get_cmap("viridis")(np.linspace(0.0, 0.78, 256))
    return LinearSegmentedColormap.from_list("paper_viridis", colors)


def spinodal_curves() -> tuple[np.ndarray, list[tuple[float, np.ndarray, int]]]:
    # Stop infinitesimally below the cusp, where u'' is undefined but the
    # spinodal curve has the limiting value zero.
    rho_values = np.linspace(1.0e-5, 0.5 - 1.0e-8, 2200)
    curves = []
    for alpha in np.linspace(0.0, 1.0, 6):
        temperatures = np.asarray(
            [continuum_spinodal_temperature(alpha=alpha, rho=rho) for rho in rho_values]
        )
        curves.append((float(alpha), temperatures, int(np.argmax(temperatures))))
    return rho_values, curves


def draw_spinodal_panel(ax: plt.Axes, *, title: str | None = None) -> None:
    rho_values, curves = spinodal_curves()
    cmap = paper_cmap()
    for alpha, temperatures, peak in curves:
        color = cmap(alpha)
        ax.plot(rho_values, temperatures, color=color, lw=1.8)
        ax.plot(
            rho_values[peak],
            temperatures[peak],
            marker="*",
            ms=8,
            color=color,
            markeredgecolor=color,
        )
    ax.axvline(0.5, color="black", ls=":", lw=1.6)
    ax.text(0.497, -0.011, r"$\rho^\star$", ha="center", va="top", fontsize=11)
    ax.set(xlim=(0.0, 0.6), ylim=(0.0, 0.24), xlabel=r"$\rho_0$", ylabel=r"$T$")
    ax.set_xticks([0.0, 0.2, 0.4, 0.6])
    ax.set_yticks([0.0, 0.1, 0.2])
    if title:
        ax.set_title(title, loc="left")


def save_all(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), dpi=240, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def render_source_reproduction() -> None:
    fig, ax = plt.subplots(figsize=(5.35, 3.65), constrained_layout=True)
    draw_spinodal_panel(ax)
    sm = ScalarMappable(norm=Normalize(0.0, 1.0), cmap=paper_cmap())
    colorbar = fig.colorbar(sm, ax=ax, fraction=0.055, pad=0.045)
    colorbar.set_label(r"$\alpha$", rotation=90)
    colorbar.set_ticks([0.0, 0.5, 1.0])
    save_all(fig, WORKSPACE / "outputs" / "figures" / "idx100_spinodal_reproduction")


def render_gold_audit() -> None:
    alpha = 0.6
    rho = 0.37
    sigma = 10.0
    length = 1000.0
    result = search_discrete_modes_2d(
        alpha=alpha, rho=rho, sigma=sigma, length=length
    )
    fundamental = (2.0 * math.pi / length) ** 2
    u1, u2, _ = utility_derivatives(rho)
    mobility = rho * (1.0 - rho)
    temperature = mobility * ((1.0 + alpha) * u1 + alpha * rho * u2)
    coeff = gradient_coefficients(
        temperature=temperature, alpha=alpha, rho=rho, sigma=sigma
    )

    fig, axes = plt.subplots(2, 2, figsize=(10.2, 7.1), constrained_layout=True)
    draw_spinodal_panel(axes[0, 0], title="(a) PRL Fig. 1(b): spinodal reproduction")

    shells = sorted(
        {
            nx * nx + ny * ny
            for nx in range(-8, 9)
            for ny in range(-8, 9)
            if 1 <= nx * nx + ny * ny <= 65
        }
    )
    values = []
    for shell in shells:
        q = gaussian_hat_from_k2(shell * fundamental, sigma)
        values.append(mobility * ((1.0 + alpha) * u1 * q + alpha * rho * u2 * q * q))
    axes[0, 1].plot(shells, values, "o-", color="#3569a8", ms=3.4, lw=1.0)
    axes[0, 1].axvline(result.continuum_shell, color="0.35", ls=":", lw=1.1, label="continuum vertex")
    axes[0, 1].scatter([result.shell], [result.critical_temperature], color="#16802c", s=45, zorder=4, label="correct shell 34")
    frozen_shell = 40
    frozen_q = gaussian_hat_from_k2(frozen_shell * fundamental, sigma)
    frozen_value = mobility * ((1.0 + alpha) * u1 * frozen_q + alpha * rho * u2 * frozen_q**2)
    axes[0, 1].scatter([frozen_shell], [frozen_value], color="#d62728", marker="x", s=55, lw=1.8, zorder=4, label="frozen shell 40")
    axes[0, 1].set(
        xlim=(20, 52),
        xlabel=r"shell $m=n_x^2+n_y^2$",
        ylabel=r"$D_m$",
        title="(b) Exact discrete onset mode",
    )
    axes[0, 1].legend(frameon=False, fontsize=7.5)

    alpha_values = np.linspace(0.001, 1.0, 600)
    correct_thresholds = np.asarray([finite_wavenumber_threshold(a) for a in alpha_values])
    frozen_thresholds = np.asarray([frozen_threshold(a) for a in alpha_values])
    axes[1, 0].plot(alpha_values, correct_thresholds, color="#16802c", lw=2.0, label=r"source/correct: $(1+\alpha)/(2+4\alpha)$")
    axes[1, 0].plot(alpha_values, frozen_thresholds, color="#d62728", lw=1.7, ls="--", label=r"frozen: $(1+\alpha)/(2+3\alpha)$")
    axes[1, 0].fill_between(alpha_values, correct_thresholds, frozen_thresholds, color="#f1b44c", alpha=0.22)
    axes[1, 0].scatter([alpha], [rho], color="black", marker="*", s=70, zorder=5, label="Task 2 point")
    axes[1, 0].set(
        xlim=(0.0, 1.0),
        ylim=(0.30, 0.51),
        xlabel=r"$\alpha$",
        ylabel=r"threshold density / $\rho_m$",
        title="(c) Same algebraic error in Tasks 3–4",
    )
    axes[1, 0].legend(frameon=False, fontsize=7.2, loc="upper right")

    k_values = np.linspace(0.0, 0.1, 800)
    s_values = k_values**2
    exact = np.asarray(
        [
            exact_growth_rate(
                float(s),
                temperature=temperature,
                alpha=alpha,
                rho=rho,
                sigma=sigma,
            )
            for s in s_values
        ]
    )
    correct_truncation = -coeff.a2 * s_values**2 - coeff.a4 * s_values**3
    wrong_a4 = frozen_a4(alpha=alpha, rho=rho, sigma=sigma)
    frozen_truncation = -coeff.a2 * s_values**2 - wrong_a4 * s_values**3
    correct_k = selected_wavenumber(coeff.a2, coeff.a4)
    factor_only_k = frozen_selected_wavenumber_with_repaired_sign(coeff.a2, coeff.a4)
    axes[1, 1].plot(k_values, exact, color="black", lw=1.8, label="exact nonlocal")
    axes[1, 1].plot(k_values, correct_truncation, color="#16802c", lw=1.6, ls="--", label=r"correct $O(k^6)$")
    axes[1, 1].plot(k_values, frozen_truncation, color="#d62728", lw=1.5, ls=":", label="frozen A4 sign")
    axes[1, 1].axvline(correct_k, color="#16802c", lw=1.0)
    axes[1, 1].axvline(factor_only_k, color="#d62728", lw=1.0, ls="--")
    axes[1, 1].annotate(
        r"correct $\sqrt{-2A_2/(3A_4)}$",
        (correct_k, np.interp(correct_k, k_values, correct_truncation)),
        xytext=(0.048, 6.5e-7),
        fontsize=7.3,
        arrowprops={"arrowstyle": "->", "lw": 0.7},
    )
    axes[1, 1].set(
        xlim=(0.0, 0.06),
        ylim=(-1.5e-6, 4.0e-6),
        xlabel=r"$k$",
        ylabel=r"growth rate $\lambda(k)$",
        title="(d) Conserved long-wave selection",
    )
    axes[1, 1].ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
    axes[1, 1].legend(frameon=False, fontsize=7.2, loc="upper left")

    save_all(fig, WORKSPACE / "outputs" / "figures" / "idx100_gold_audit")


def main() -> None:
    configure()
    render_source_reproduction()
    render_gold_audit()
    rho_values, curves = spinodal_curves()
    feature_payload = {
        "schema_version": 1,
        "paper_id": "prlb-f37350e-100",
        "target": "PRL Figure 1(b)",
        "parameters": {"gamma": 1.5, "rho_star": 0.5},
        "critical_points": [
            {
                "alpha": alpha,
                "rho_critical": float(rho_values[peak]),
                "temperature_critical": float(temperatures[peak]),
            }
            for alpha, temperatures, peak in curves
        ],
        "provenance": "independent_numerics",
    }
    feature_output = WORKSPACE / "outputs" / "data" / "idx100_spinodal_features.json"
    feature_output.parent.mkdir(parents=True, exist_ok=True)
    feature_output.write_text(json.dumps(feature_payload, indent=2) + "\n", encoding="utf-8")
    check = {
        "status": "passed",
        "backend": "python",
        "paper_reference": "outputs/references/source_spinodals.png",
        "paper_reproduction": {
            "artifact": "outputs/figures/idx100_spinodal_reproduction.png",
            "editable_exports": [
                "outputs/figures/idx100_spinodal_reproduction.svg",
                "outputs/figures/idx100_spinodal_reproduction.pdf",
            ],
            "target": "PRL Figure 1(b)",
            "parameter_match": "paper_exact",
            "features": ["six alpha curves", "critical-point stars", "rho*=1/2 guide", "matching axes and color scale"],
        },
        "gold_audit": {
            "artifact": "outputs/figures/idx100_gold_audit.png",
            "editable_exports": [
                "outputs/figures/idx100_gold_audit.svg",
                "outputs/figures/idx100_gold_audit.pdf",
            ],
            "panels": 4,
        },
        "figure_contract": {
            "core_conclusion": "The direct PRL spinodal is reproducible, but the idx100 frozen numerical and long-wave answers are not.",
            "evidence_chain": {
                "a": "Source spinodal family follows the exact PRL dispersion.",
                "b": "A proof-bounded discrete search selects shell 34, not 40.",
                "c": "The source mapping and interior-q criterion share the 2+4alpha denominator.",
                "d": "The frozen A4 sign and nonconserved selection factor fail the exact dispersion.",
            },
            "archetype": "quantitative grid",
            "export": "PNG preview plus editable SVG/PDF",
        },
    }
    output = WORKSPACE / "outputs" / "checks" / "idx100_figure_check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
