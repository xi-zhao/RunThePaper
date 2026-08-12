"""Render frozen numerical arrays without changing scientific values."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

COLORS = {"blue": "#3B73C5", "red": "#A3345B", "gold": "#B28B19", "gray": "#444444"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _finish(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_grouped_lines(
    csv_path: Path,
    output: Path,
    x_column: str,
    y_column: str,
    group_columns: Iterable[str],
    xlabel: str,
    ylabel: str,
    title: str,
    horizontal_zero: bool = False,
) -> None:
    rows = read_csv(csv_path)
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    columns = tuple(group_columns)
    for row in rows:
        groups.setdefault(tuple(row[column] for column in columns), []).append(row)
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    palette = plt.get_cmap("tab10")
    for index, (key, values) in enumerate(sorted(groups.items())):
        values.sort(key=lambda row: float(row[x_column]))
        label = ", ".join(
            f"{name}={value}" for name, value in zip(columns, key, strict=True)
        )
        ax.plot(
            [float(row[x_column]) for row in values],
            [float(row[y_column]) for row in values],
            lw=1.6,
            color=palette(index % 10),
            label=label,
        )
    if horizontal_zero:
        ax.axhline(0.0, color="#777777", lw=0.7, ls=":")
    ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
    ax.tick_params(direction="in", top=True, right=True)
    if groups:
        ax.legend(frameon=False, fontsize=7)
    _finish(fig, output)


def plot_ac(csv_path: Path, output: Path, species: str) -> None:
    rows = read_csv(csv_path)
    rows.sort(key=lambda row: float(row["frequency_mev"]))
    x = np.array([float(row["frequency_mev"]) for row in rows])
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    color = {"h": COLORS["blue"], "x": COLORS["red"], "t": COLORS["gold"]}[species]
    ax.plot(
        x,
        [float(row["kinetic_real"]) for row in rows],
        color=color,
        lw=1.7,
        label="Re kinetic",
    )
    ax.plot(
        x,
        [float(row["kinetic_imag"]) for row in rows],
        color=color,
        lw=1.2,
        alpha=0.42,
        label="Im kinetic",
    )
    ax.plot(
        x,
        [float(row["hydro_real"]) for row in rows],
        color="#111111",
        lw=1.0,
        ls="--",
        label="Re three-fluid",
    )
    ax.plot(
        x,
        [float(row["hydro_imag"]) for row in rows],
        color="#777777",
        lw=1.0,
        ls="--",
        label="Im three-fluid",
    )
    ax.axhline(0.0, color="#777777", lw=0.6, ls=":")
    ax.set(
        xlabel=r"frequency $\hbar\Omega$ (meV)",
        ylabel=r"$\sigma/\sigma_0^h$",
        title=f"AC response: {species}",
    )
    ax.tick_params(direction="in", top=True, right=True)
    ax.legend(frameon=False, fontsize=7, ncol=2)
    _finish(fig, output)


def render_all(data_dir: Path, figure_dir: Path) -> None:
    plot_grouped_lines(
        data_dir / "T001_scattering_amplitude.csv",
        figure_dir / "T001_main_fig1b_scattering.png",
        "energy_over_resonance",
        "amplitude_abs",
        ("convention",),
        r"$E/E_{res}$",
        r"$|f(E)|$",
        "Vacuum scattering amplitude",
    )
    plot_grouped_lines(
        data_dir / "T002_hole_resistivity.csv",
        figure_dir / "T002_main_fig1c_resistivity.png",
        "detuning_over_ef",
        "rho_over_rho0",
        ("tunnel_mev", "exciton_density_cm2"),
        r"$\Delta/E_F^h$",
        r"$\rho^h/\rho_0^h$",
        "Hole resistivity",
    )
    plot_grouped_lines(
        data_dir / "T003_exciton_drag.csv",
        figure_dir / "T003_main_fig2_exciton_drag.png",
        "detuning_over_ef",
        "sigma_x_over_sigma0",
        ("tunnel_mev",),
        r"$\Delta/E_F^h$",
        r"$\sigma^x/\sigma_0^h$",
        "Exciton drag",
        True,
    )
    plot_grouped_lines(
        data_dir / "T004_temperature_resistivity.csv",
        figure_dir / "T004_main_fig3_temperature.png",
        "temperature_k",
        "many_body_rho_over_rho0",
        ("detuning_over_ef",),
        "temperature (K)",
        r"$(\rho^h-\rho_0^h)/\rho_0^h$",
        "Many-body temperature dependence",
    )
    plot_grouped_lines(
        data_dir / "T005_total_resistivity.csv",
        figure_dir / "T005_main_fig3_inset.png",
        "temperature_k",
        "rho_over_rho0",
        ("contribution",),
        "temperature (K)",
        r"$\rho/\rho_0^h$",
        "Phonon crossover (proxy)",
    )
    for target, output_name, species in (
        ("T006_ac_hole.csv", "T006_main_fig4a_ac_hole.png", "h"),
        ("T007_ac_exciton.csv", "T007_main_fig4b_ac_exciton.png", "x"),
        ("T008_ac_trion.csv", "T008_main_fig4c_ac_trion.png", "t"),
    ):
        plot_ac(data_dir / target, figure_dir / output_name, species)
    plot_grouped_lines(
        data_dir / "T009_kubo_difference.csv",
        figure_dir / "T009_supp_fig6_kubo_difference.png",
        "detuning_over_ef",
        "rho_kubo_minus_boltzmann",
        ("exciton_density_cm2",),
        r"$\Delta/E_F^h$",
        r"$(\rho_K^h-\rho^h)/\rho_0^h$",
        "Kubo--Boltzmann difference",
    )
    plot_grouped_lines(
        data_dir / "T010_trion_drag.csv",
        figure_dir / "T010_supp_fig7_trion_drag.png",
        "detuning_over_ef",
        "sigma_t_over_sigma0",
        ("tunnel_mev",),
        r"$\Delta/E_F^h$",
        r"$\sigma^t/\sigma_0^h$",
        "Trion drag",
        True,
    )
