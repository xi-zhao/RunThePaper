"""Reference-free rendering of frozen scientific arrays."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .polarization import barrier_energy

COLORS = ["#253494", "#7A1FA2", "#D64F87", "#FF7043", "#F4C430"]
FIELD_COLORS = {3.0: COLORS[0], 124.9: COLORS[2], 250.2: COLORS[4]}
RATIO_COLORS = {
    0.0: "#253494",
    0.2: "#3949AB",
    0.45: "#8E24AA",
    0.8: "#D64F87",
    1.26: "#EF5350",
    1.81: "#FF7043",
    3.21: "#F4C430",
}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "legend.frameon": False,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def _save(fig: plt.Figure, path: Path, dpi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def _velocity_panel(rows: list[dict[str, Any]], *, xlabel: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(3.4, 2.8))
    fields = sorted({round(float(row["field_mv_m"]), 1) for row in rows})
    for field in fields:
        selected = [row for row in rows if round(float(row["field_mv_m"]), 1) == field]
        velocity = np.asarray([float(row["velocity_m_s"]) for row in selected])
        density = np.asarray([float(row["density"]) for row in selected])
        gaussian = np.asarray([float(row["gaussian_density"]) for row in selected])
        color = FIELD_COLORS[field]
        density = np.maximum(density / np.max(density), 1.0e-5)
        gaussian = np.maximum(gaussian / np.max(gaussian), 1.0e-5)
        ax.plot(velocity, density, color=color, lw=1.4, label=f"{field:g} mV/m")
        ax.plot(velocity, gaussian, color=color, lw=0.9, ls="--", alpha=0.7)
    ax.set_yscale("log")
    ax.set_ylim(1.0e-4, 1.2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("probability density")
    ax.legend(fontsize=7)
    return fig


def render_all(
    figure_dir: Path,
    *,
    statistics_result: dict[str, Any],
    md_result: dict[str, Any],
    classical_result: dict[str, Any],
    capture_result: dict[str, Any],
    recombination_result: dict[str, Any],
    dpi: int,
) -> list[Path]:
    """Render all 17 targets without reading raw/ or references/."""

    _style()
    output = figure_dir
    paths: list[Path] = []

    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.plot(
        statistics_result["mean_count"],
        statistics_result["poisson_variance"],
        ls="--",
        color="#F28E2B",
        lw=1.7,
        label="Poisson",
    )
    ax.plot(
        statistics_result["mean_count"],
        statistics_result["goe_variance"],
        ls="-.",
        color="#444444",
        lw=1.5,
        label="GOE",
    )
    ax.set(xlabel=r"mean count $\bar N$", ylabel=r"number variance $\Sigma^2$")
    ax.legend()
    path = output / "T001_main_fig2a.png"
    _save(fig, path, dpi)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.plot(
        statistics_result["spacing"],
        statistics_result["poisson_spacing"],
        ls="--",
        color="#F28E2B",
        lw=1.7,
        label="Poisson",
    )
    ax.plot(
        statistics_result["spacing"],
        statistics_result["wigner_spacing"],
        ls="-.",
        color="#444444",
        lw=1.5,
        label="Wigner",
    )
    ax.set(xlabel=r"normalized spacing $s$", ylabel=r"$P(s)$")
    ax.legend()
    path = output / "T002_main_fig2b.png"
    _save(fig, path, dpi)
    paths.append(path)

    rows = md_result["rows_t003"]
    field = np.asarray([float(row["field_mv_m"]) for row in rows])
    median = np.asarray([float(row["median_temperature_uk"]) for row in rows])
    fit = np.asarray([float(row["quadratic_fit_temperature_uk"]) for row in rows])
    fig, ax = plt.subplots(figsize=(4.3, 3.0))
    ax.scatter(
        field,
        median,
        edgecolors=[RATIO_COLORS[float(row["declared_excess_ratio"])] for row in rows],
        s=28,
        facecolors="none",
        linewidths=1.2,
    )
    order = np.argsort(field)
    ax.plot(field[order], fit[order], color="#777777", ls="--", lw=1.2)
    ax.set(xlabel=r"$\mathcal{E}_{dc}$ (mV/m)", ylabel=r"$E_{ion}/(3k_B/2)$ ($\mu$K)")
    path = output / "T003_main_fig3a.png"
    _save(fig, path, dpi)
    paths.append(path)

    fig = _velocity_panel(
        md_result["rows_t004"], xlabel=r"radial velocity $v_{rad}$ (m/s)"
    )
    path = output / "T004_main_fig3b.png"
    _save(fig, path, dpi)
    paths.append(path)

    fig = _velocity_panel(
        md_result["rows_t005"], xlabel=r"axial velocity $v_{ax}$ (m/s)"
    )
    path = output / "T005_main_fig3c.png"
    _save(fig, path, dpi)
    paths.append(path)

    fig, left = plt.subplots(figsize=(4.4, 3.0))
    right = left.twinx()
    left.plot(
        classical_result["displacement"],
        classical_result["density"] / np.max(classical_result["density"]),
        color="#9E9E9E",
        lw=2.0,
    )
    right.plot(
        classical_result["displacement"],
        classical_result["survival"],
        color="#FF7043",
        ls="--",
        lw=1.7,
    )
    left.set(xlabel=r"ion displacement $\Delta y$ ($\mu$m)", ylabel=r"density $n/n_0$")
    right.set_ylabel(r"classical $P_{surv}$", color="#FF7043")
    right.tick_params(axis="y", colors="#FF7043")
    path = output / "T006_main_fig4.png"
    _save(fig, path, dpi)
    paths.append(path)

    rows = sorted(
        recombination_result["rows_t007"], key=lambda item: item["excess_ratio"]
    )
    ratio = np.asarray([float(row["excess_ratio"]) for row in rows])
    s_rate = np.asarray([float(row["s_peak_rate_s"]) for row in rows])
    p_rate = np.asarray([float(row["p_peak_rate_s"]) for row in rows])
    exponential = (
        np.asarray([float(row["printed_exponential_shape"]) for row in rows])
        * s_rate[0]
    )
    fig, ax = plt.subplots(figsize=(3.4, 2.8))
    ax.plot(ratio, s_rate, "o-", color="#111111", mfc="white", label="s wave")
    ax.plot(ratio, p_rate, "x--", color="#777777", label="p wave")
    ax.plot(ratio, exponential, ":", color="#F28E2B", label=r"$e^{-x/0.33}$")
    ax.set_yscale("log")
    ax.set(
        xlabel=r"$\Delta E_{ion}/\Delta E_{s,ion}$", ylabel=r"peak loss rate (s$^{-1}$)"
    )
    ax.legend(fontsize=7)
    path = output / "T007_main_fig5b.png"
    _save(fig, path, dpi)
    paths.append(path)

    target_panel = {
        3.21: ("T008", "a"),
        1.81: ("T009", "b"),
        1.26: ("T010", "c"),
        0.8: ("T011", "d"),
        0.45: ("T012", "e"),
        0.2: ("T013", "f"),
        0.0: ("T014", "g"),
    }
    for ratio_value, (target, panel) in target_panel.items():
        spectrum = recombination_result["spectra"][ratio_value]
        fig, ax = plt.subplots(figsize=(3.8, 2.0))
        ax.plot(
            spectrum["field"],
            spectrum["survival"],
            color=RATIO_COLORS[ratio_value],
            ls=":",
            lw=1.8,
        )
        ax.set_xlim(319.8, 323.1)
        ax.set_ylim(0.45, 1.02)
        ax.set(xlabel=r"magnetic field $B$ (G)", ylabel=r"$P_{surv}$")
        ax.text(
            0.03,
            0.12,
            f"({panel})  {ratio_value:g} $\\Delta E_s$",
            transform=ax.transAxes,
            fontsize=8,
        )
        path = output / f"{target}_main_fig6{panel}.png"
        _save(fig, path, dpi)
        paths.append(path)

    summary = sorted(
        recombination_result["summary_rows"], key=lambda item: item["excess_ratio"]
    )
    ratios = np.asarray([float(row["excess_ratio"]) for row in summary])
    positions = np.asarray([float(row["printed_linear_position_g"]) for row in summary])
    peaks = np.asarray([float(row["model_peak_rate_s"]) for row in summary])
    fig, ax = plt.subplots(figsize=(3.2, 2.7))
    ax.plot(ratios, positions, "o--", color="#666666", mfc="white")
    ax.set(xlabel=r"$\Delta E_{ion}/\Delta E_{s,ion}$", ylabel=r"model $B_0$ (G)")
    path = output / "T015_main_fig6h.png"
    _save(fig, path, dpi)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(3.2, 2.7))
    ax.plot(ratios, peaks, "D-", color="#D64F87", mfc="white")
    ax.set_yscale("log")
    ax.set(
        xlabel=r"$\Delta E_{ion}/\Delta E_{s,ion}$",
        ylabel=r"model $\gamma_l$ (s$^{-1}$)",
    )
    path = output / "T016_main_fig6i.png"
    _save(fig, path, dpi)
    paths.append(path)

    table = capture_result["table"]
    fig, ax = plt.subplots(figsize=(4.3, 3.2))
    labels = ["s", "p", "d", "f"]
    for partial_wave in range(4):
        ax.loglog(
            table.energies_es,
            table.probabilities[partial_wave],
            lw=1.6,
            color=COLORS[partial_wave],
            label=labels[partial_wave],
        )
        if partial_wave > 0:
            ax.axvline(
                barrier_energy(partial_wave), color=COLORS[partial_wave], ls=":", lw=0.8
            )
    ax.set(xlabel=r"collision energy $E/E_s$", ylabel=r"$\Gamma(E)/\Gamma_m=C_l^{-2}$")
    ax.set_ylim(1e-14, 1.2)
    ax.legend(ncol=2)
    path = output / "T017_appendix_fig8.png"
    _save(fig, path, dpi)
    paths.append(path)
    return paths
