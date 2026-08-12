"""Matplotlib rendering for independently generated numerical arrays."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def render_rotating_levels(
    rows: np.ndarray,
    path: Path,
    *,
    all_ratios: bool,
    maximum_shell: int | None = None,
) -> None:
    ratios = sorted(set(rows["rotation_ratio"]))
    if not all_ratios:
        ratios = [ratios[0], ratios[-1]]
    fig, axes = plt.subplots(
        1, len(ratios), figsize=(3.0 * len(ratios), 3.0), squeeze=False
    )
    for axis, ratio in zip(axes[0], ratios, strict=True):
        selected = rows[np.isclose(rows["rotation_ratio"], ratio)]
        if maximum_shell is not None:
            selected = selected[selected["n"] <= maximum_shell]
        for row in selected:
            color = "#d62728" if row["n"] == row["m"] else "black"
            axis.plot(
                [row["m"] - 0.16, row["m"] + 0.16],
                [row["energy"], row["energy"]],
                color=color,
                linewidth=1.7,
            )
        axis.set_title(rf"$\Omega_{{rot}}/\omega={ratio:g}$")
        axis.set_xlabel(r"$m/\hbar$")
        axis.set_ylabel(r"$E/(\hbar\omega)$")
    _save(fig, path)


def render_curve_table(
    table: np.ndarray,
    path: Path,
    x: str,
    series: list[tuple[str, str]],
    *,
    colors: list[str] | None = None,
    linestyles: list[str] | None = None,
    xlabel: str | None = None,
    ylabel: str = "normalized observable",
    show_legend: bool = True,
) -> None:
    fig, axis = plt.subplots(figsize=(4.6, 3.2))
    for index, (name, label) in enumerate(series):
        axis.plot(
            table[x],
            table[name],
            label=label,
            linewidth=2,
            color=colors[index] if colors else None,
            linestyle=linestyles[index] if linestyles else "-",
        )
    if show_legend:
        axis.legend(frameon=False)
    axis.set_xlabel(xlabel or x.replace("_", " "))
    axis.set_ylabel(ylabel)
    _save(fig, path)


def render_density_pair(
    x: np.ndarray,
    y: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    labels: tuple[str, str],
    path: Path,
    *,
    cmaps: tuple[str, str] = ("magma", "magma"),
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.0), sharex=True, sharey=True)
    meshes = []
    for axis, density, label, cmap in zip(
        axes, (first, second), labels, cmaps, strict=True
    ):
        mesh = axis.pcolormesh(
            x,
            y,
            density,
            shading="auto",
            cmap=cmap,
            vmin=0.0,
            vmax=float(np.max(density)),
        )
        meshes.append(mesh)
        axis.set_title(label)
        axis.set_aspect("equal")
        axis.set_xlabel(r"$p_y/p_{HO}$")
        axis.set_ylabel(r"$p_x/p_{HO}$")
    for axis, mesh in zip(axes, meshes, strict=True):
        fig.colorbar(mesh, ax=axis, shrink=0.82, label="normalized density")
    _save(fig, path)


def render_spectrum(table: np.ndarray, path: Path, title: str) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(5.0, 6.8), sharex=True)
    colors = {"m0": "black", "m2": "#d62728", "m4": "#1f9fb4"}
    for axis, manifold in zip(axes[::-1], ("m0", "m2", "m4"), strict=True):
        names = [name for name in table.dtype.names if name.startswith(manifold + "_")]
        for name in names:
            axis.plot(
                table["field_g"], table[name], color=colors[manifold], linewidth=1.6
            )
        axis.set_ylabel(r"$E/\hbar\omega$")
    axes[0].set_title(title)
    axes[-1].set_xlabel("magnetic field (G)")
    _save(fig, path)


def render_heatmap(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    path: Path,
    *,
    xlabel: str,
    ylabel: str,
    color_label: str,
) -> None:
    fig, axis = plt.subplots(figsize=(5.0, 3.5))
    mesh = axis.pcolormesh(x, y, values, shading="auto", cmap="gray_r")
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    fig.colorbar(mesh, ax=axis, label=color_label)
    _save(fig, path)


def render_density_evolution(
    x: np.ndarray,
    y: np.ndarray,
    com: np.ndarray,
    relative: np.ndarray,
    fractions: np.ndarray,
    path: Path,
) -> None:
    fig, axes = plt.subplots(len(fractions), 2, figsize=(5.2, 2.35 * len(fractions)))
    for row, fraction in enumerate(fractions):
        for column, density in enumerate((com[row], relative[row])):
            axes[row, column].pcolormesh(
                x,
                y,
                density,
                shading="auto",
                cmap=("Reds", "Blues")[column],
            )
            axes[row, column].set_aspect("equal")
            axes[row, column].set_xticks([])
            axes[row, column].set_yticks([])
        axes[row, 0].set_ylabel(f"{fraction:g} T")
    axes[0, 0].set_title("center of mass")
    axes[0, 1].set_title("relative")
    _save(fig, path)
