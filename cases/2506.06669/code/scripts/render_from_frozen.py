#!/usr/bin/env python3
"""Render the public-theory figures from frozen numerical arrays.

The script deliberately has no source-PDF or reference-image input.  Numerical
coordinates and observables come only from ``outputs/data``; the JSON contract
may change typography, canvas geometry, axes placement, line appearance,
palette, and interpolation, but not the science.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from typing import Any


MPL_CONFIG = Path(os.environ.get("MPLCONFIGDIR", ".matplotlib"))
MPL_CONFIG.mkdir(parents=True, exist_ok=True)
FONT_CACHE_TARGET = MPL_CONFIG / "fontlist-v390.json"
if not FONT_CACHE_TARGET.exists():
    shutil.copyfile(Path("config/fontlist-v390.json"), FONT_CACHE_TARGET)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np


CONTRACT_PATH = Path("render_contract.json")
DATA_DIR = Path("outputs/data")


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    render_t001(contract)
    render_t002(contract)
    render_t003(contract)
    render_t004(contract)
    render_t005(contract)
    render_t006(contract)
    render_t007(contract)
    render_t008(contract)
    render_t009(contract)
    render_t010(contract)
    return 0


def target_parameters(contract: dict[str, Any], target_id: str) -> dict[str, Any]:
    return contract["render_parameters"][target_id]


def new_figure(target: dict[str, Any], fallback: tuple[float, float, float] = (8.0, 5.0, 100.0)) -> plt.Figure:
    canvas = target.get("canvas", {})
    width = float(canvas.get("width_inches", fallback[0]))
    height = float(canvas.get("height_inches", fallback[1]))
    dpi = float(canvas.get("dpi", fallback[2]))
    return plt.figure(figsize=(width, height), dpi=dpi, facecolor=canvas.get("facecolor", "white"))


def fixed_figure(target: dict[str, Any], width: float, height: float) -> plt.Figure:
    canvas = target.get("canvas", {})
    return plt.figure(
        figsize=(width, height),
        dpi=float(canvas.get("dpi", 100.0)),
        facecolor=canvas.get("facecolor", "white"),
    )


def add_axis(
    figure: plt.Figure,
    target: dict[str, Any],
    role: str,
    fallback: list[float],
    *,
    projection: str | None = None,
) -> plt.Axes:
    box = target.get("axes_positions", {}).get(role, fallback)
    return figure.add_axes(box, projection=projection)


def font_value(target: dict[str, Any], key: str, fallback: float) -> float:
    return float(target.get("typography", {}).get(key, fallback))


def palette(target: dict[str, Any], role: str, fallback: str) -> str:
    return str(target.get("palette", {}).get(role, fallback))


def interpolation(target: dict[str, Any], role: str, fallback: str = "nearest") -> str:
    return str(target.get("interpolation", {}).get(role, fallback))


def line_kwargs(
    target: dict[str, Any],
    series_id: str,
    *,
    color: str,
    fallback_style: str = "-",
    fallback_width: float = 1.2,
    fallback_marker: str = "none",
    fallback_marker_size: float = 3.0,
    fallback_alpha: float = 1.0,
) -> dict[str, Any]:
    style = target.get("line_styles", {}).get(series_id, {})
    marker = style.get("marker", fallback_marker)
    return {
        "color": color,
        "linestyle": style.get("line_style", fallback_style),
        "linewidth": float(style.get("line_width", fallback_width)),
        "marker": None if marker == "none" else marker,
        "markersize": float(style.get("marker_size", fallback_marker_size)),
        "alpha": float(style.get("alpha", fallback_alpha)),
    }


def style_axis(axis: plt.Axes, target: dict[str, Any]) -> None:
    typography = target.get("typography", {})
    family = typography.get("font_family", "DejaVu Sans")
    label_size = font_value(target, "axis_label_size", 10.0)
    tick_size = font_value(target, "tick_label_size", 8.0)
    for label in [axis.xaxis.label, axis.yaxis.label, axis.title]:
        label.set_fontfamily(family)
    axis.xaxis.label.set_size(label_size)
    axis.yaxis.label.set_size(label_size)
    axis.title.set_size(font_value(target, "font_size", 10.0))
    axis.tick_params(direction="in", top=True, right=True, labelsize=tick_size, width=0.8)
    for tick in axis.get_xticklabels() + axis.get_yticklabels():
        tick.set_fontfamily(family)


def panel_label(figure: plt.Figure, target: dict[str, Any], text: str, x: float, y: float) -> None:
    figure.text(
        x,
        y,
        text,
        fontsize=font_value(target, "font_size", 11.0),
        fontweight="bold",
        fontfamily=target.get("typography", {}).get("font_family", "DejaVu Sans"),
    )


def save_output(figure: plt.Figure, contract: dict[str, Any], target_id: str, index: int = 0) -> None:
    output = Path(contract["rendered_outputs"][target_id][index])
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = target_parameters(contract, target_id).get("canvas", {})
    figure.savefig(output, dpi=float(canvas.get("dpi", figure.dpi)), facecolor=figure.get_facecolor())
    plt.close(figure)


def render_t001(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T001")
    with np.load(DATA_DIR / "fig1cd.npz", allow_pickle=False) as data:
        eigenvalues = {m: data[f"eigenvalues_m{m}"] for m in (0, 4)}
        eigenvectors = {m: data[f"eigenvectors_m{m}"] for m in (0, 4)}

    figure = new_figure(target)
    cmap = plt.get_cmap(palette(target, "eigenfunction_colormap", "Spectral_r"))
    all_values = np.concatenate([eigenvalues[0], eigenvalues[4]])
    norm = colors.Normalize(float(all_values.min()), float(all_values.max()))
    sites = np.arange(1, 6)
    for column, (m, letter) in enumerate(((0, "c"), (4, "d"))):
        for row in range(5):
            role = f"panel_{letter}_{row}"
            fallback = [0.245 + 0.325 * column, 0.105 + 0.086 * row, 0.205, 0.076]
            axis = add_axis(figure, target, role, fallback)
            state = eigenvectors[m][:, row]
            axis.bar(sites, state, width=0.38, color=cmap(norm(eigenvalues[m][row])), edgecolor="none")
            axis.axhline(0.0, color="#8c8c8c", linewidth=0.75)
            axis.set_xlim(0.4, 5.6)
            axis.set_ylim(-0.9, 0.9)
            axis.set_yticks([])
            if row == 0:
                axis.set_xticks(sites)
                axis.set_xlabel("Site")
            else:
                axis.set_xticks([])
            for spine in ("top", "right", "bottom"):
                axis.spines[spine].set_visible(False)
            style_axis(axis, target)
        figure.text(0.285 + 0.325 * column, 0.555, "Eigenfunctions", color="#777777", fontsize=font_value(target, "font_size", 12))
        panel_label(figure, target, letter, 0.04 + 0.53 * column, 0.57)
        figure.text(0.35 + 0.325 * column, 0.54, rf"$m={m}$", ha="center", fontsize=font_value(target, "font_size", 11))
    save_output(figure, contract, "T001")


def render_t002(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T002")
    with np.load(DATA_DIR / "fig2_3site.npz", allow_pickle=False) as data:
        offset = data["offset_mhz"]
        times = data["fine_time_ns"]
        scans = {
            (kind, m): data[f"{kind}_scan_m{m}"]
            for kind in ("q2", "q1")
            for m in range(4)
        }
        delta = data["delta_mhz"]
        coupling = data["coupling_mhz"]
        solution = data["solution_p3"]

    figure = new_figure(target)
    image = None
    for row, kind in enumerate(("q2", "q1")):
        for column, m in enumerate(range(4)):
            letter = "abcdefgh"[row * 4 + column]
            role = f"panel_{letter}"
            fallback = [0.067 + 0.212 * column, 0.565 - 0.50 * row, 0.17, 0.37]
            axis = add_axis(figure, target, role, fallback)
            image = axis.imshow(
                scans[(kind, m)],
                origin="lower",
                aspect="auto",
                extent=[offset[0], offset[-1], times[0], times[-1]],
                vmin=0.0,
                vmax=1.0,
                cmap=palette(target, "population_colormap", "inferno"),
                interpolation=interpolation(target, "population_map", "nearest"),
            )
            axis.set_title(rf"$m={m}$")
            axis.set_xlabel(rf"$\delta\omega_{{Q_{{{2 if kind == 'q2' else 1}}}}}/2\pi$ (MHz)")
            if column == 0:
                axis.set_ylabel("Time (ns)")
            else:
                axis.set_yticklabels([])
            panel_label(figure, target, letter, fallback[0] - 0.03, fallback[1] + fallback[3] + 0.015)
            style_axis(axis, target)
    if image is not None:
        caxis = add_axis(figure, target, "colorbar", [0.93, 0.145, 0.018, 0.72])
        colorbar = figure.colorbar(image, cax=caxis)
        colorbar.set_label(r"$P_{Q_3}$", fontsize=font_value(target, "axis_label_size", 10))
        colorbar.ax.tick_params(labelsize=font_value(target, "tick_label_size", 8), direction="in")
    save_output(figure, contract, "T002", 0)

    # Analytic solution-space companion.  It is a source-blind scientific plot,
    # but the S3 panel above is the registered pixel target for T002.
    figure = fixed_figure(target, 12.46, 11.63)
    axes = [
        add_axis(figure, target, "solution_a", [0.055, 0.54, 0.48, 0.42]),
        add_axis(figure, target, "solution_b", [0.625, 0.70, 0.275, 0.23]),
        add_axis(figure, target, "solution_c", [0.625, 0.42, 0.275, 0.23]),
    ]
    solution_image = axes[0].imshow(
        solution,
        origin="lower",
        aspect="auto",
        extent=[delta[0], delta[-1], coupling[0], coupling[-1]],
        vmin=0.0,
        vmax=1.0,
        cmap=palette(target, "population_colormap", "inferno"),
        interpolation=interpolation(target, "solution_map", "nearest"),
    )
    axes[0].set_xlabel(r"$\Delta/2\pi$ (MHz)")
    axes[0].set_ylabel(r"$J_{1,2}/2\pi$ (MHz)")
    for axis, m in zip(axes[1:], (0, 3), strict=True):
        axis.imshow(
            scans[("q2", m)],
            origin="lower",
            aspect="auto",
            extent=[offset[0], offset[-1], times[0], times[-1]],
            vmin=0.0,
            vmax=1.0,
            cmap=palette(target, "population_colormap", "inferno"),
            interpolation=interpolation(target, "population_map", "nearest"),
        )
        axis.set_xlabel(r"$\delta\Delta/2\pi$ (MHz)")
        axis.set_ylabel("Time (ns)")
        axis.set_title(rf"$m={m}$")
    caxis = add_axis(figure, target, "solution_colorbar", [0.925, 0.54, 0.018, 0.42])
    figure.colorbar(solution_image, cax=caxis).set_label(r"$P_{Q_3}$")
    for index, axis in enumerate(axes):
        panel_label(figure, target, "abc"[index], axis.get_position().x0 - 0.04, axis.get_position().y1 + 0.01)
        style_axis(axis, target)
    save_output(figure, contract, "T002", 1)


def signed_population(populations: np.ndarray) -> np.ndarray:
    result = populations.copy()
    result[:, 1::2] *= -1.0
    return result


def population_spectrum(
    axis: plt.Axes,
    target: dict[str, Any],
    times: np.ndarray,
    populations: np.ndarray,
    *,
    coordinates: list[str],
    vmax_negative: float,
) -> Any:
    image = axis.imshow(
        signed_population(populations),
        origin="lower",
        aspect="auto",
        extent=[0.5, populations.shape[1] + 0.5, times[0], times[-1]],
        cmap=palette(target, "signed_population_colormap", "RdBu_r"),
        norm=colors.TwoSlopeNorm(vmin=-vmax_negative, vcenter=0.0, vmax=1.0),
        interpolation=interpolation(target, "population_spectrum", "nearest"),
    )
    axis.set_xticks(np.arange(1, populations.shape[1] + 1), coordinates, rotation=90)
    axis.set_ylabel("Time (ns)")
    return image


def render_t003(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T003")
    with np.load(DATA_DIR / "fig2_5site.npz", allow_pickle=False) as data:
        times = data["time_ns"]
        populations = {m: data[f"populations_m{m}"] for m in (0, 4, 6)}
    figure = new_figure(target)
    for column, (letter, m) in enumerate(zip("def", (0, 4, 6), strict=True)):
        fallback = [0.055 + 0.318 * column, 0.03, 0.205, 0.42]
        axis = add_axis(figure, target, f"panel_{letter}", fallback)
        population_spectrum(axis, target, times, populations[m], coordinates=[rf"$Q_{n}$" for n in range(1, 6)], vmax_negative=0.5)
        axis.set_title(rf"$m={m}$")
        axis.set_xlabel("Qubit")
        panel_label(figure, target, letter, fallback[0] - 0.035, fallback[1] + fallback[3] + 0.015)
        style_axis(axis, target)
    save_output(figure, contract, "T003")


def render_t004(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T004")
    with np.load(DATA_DIR / "fig3ab.npz", allow_pickle=False) as data:
        times = data["time_ns"]
        populations = {m: data[f"populations_m{m}"] for m in (0, 4)}
    figure = new_figure(target)
    series_colors = ["#173b70", "#58cbe8", "#b5b5b5", "#ffb4ad", "#e6292f"]
    for column, m in enumerate((0, 4)):
        for site in range(5):
            fallback = [0.068 + 0.235 * column, 0.08 + (4 - site) * 0.175, 0.17, 0.145]
            axis = add_axis(figure, target, f"m{m}_q{site + 1}", fallback)
            axis.plot(
                times,
                populations[m][:, site],
                **line_kwargs(target, f"q{site + 1}", color=palette(target, f"q{site + 1}", series_colors[site]), fallback_width=1.1),
            )
            axis.axvline(55.5556, color="#555555", linestyle="--", linewidth=0.8)
            axis.set_xlim(times[0], times[-1])
            axis.set_ylim(0.0, 1.02 if site in (0, 2, 4) else 0.52)
            axis.set_ylabel(rf"$P_{{Q_{site + 1}}}$")
            if site == 4:
                axis.set_xlabel("Time (ns)")
            else:
                axis.set_xticklabels([])
            style_axis(axis, target)
        panel_label(figure, target, "ab"[column], 0.025 + 0.235 * column, 0.965)
        figure.text(0.15 + 0.235 * column, 0.96, rf"$m={m}$", ha="center", fontsize=font_value(target, "font_size", 11))
    save_output(figure, contract, "T004")


def density_bars(axis: plt.Axes, density: np.ndarray, *, max_height: float, cmap_name: str) -> None:
    values = np.real(density)
    size = values.shape[0]
    xx, yy = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    x = xx.ravel()
    y = yy.ravel()
    z = np.zeros(size * size)
    heights = values.ravel()
    norm = colors.TwoSlopeNorm(vmin=-max_height, vcenter=0.0, vmax=max_height)
    bar_colors = plt.get_cmap(cmap_name)(norm(heights))
    axis.bar3d(x, y, z, 0.65, 0.65, heights, color=bar_colors, edgecolor="#555555", linewidth=0.35, shade=False)
    axis.set_xlim(0, size)
    axis.set_ylim(0, size)
    axis.set_zlim(-0.04 * max_height, max_height)
    ticks = np.arange(size) + 0.325
    labels = [format(index, f"0{int(np.log2(size))}b") for index in range(size)]
    axis.set_xticks(ticks, labels, fontsize=6)
    axis.set_yticks(ticks, labels, fontsize=6)
    axis.set_zticks([0.0, max_height])
    axis.view_init(elev=27, azim=-54)


def render_t005(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T005")
    with np.load(DATA_DIR / "fig3cd.npz", allow_pickle=False) as data:
        densities = {m: data[f"reduced_density_m{m}"] for m in (0, 4)}
    figure = new_figure(target)
    for column, (letter, m) in enumerate(zip("cd", (0, 4), strict=True)):
        fallback = [0.49 + 0.255 * column, 0.46, 0.19, 0.45]
        axis = add_axis(figure, target, f"panel_{letter}", fallback, projection="3d")
        density_bars(axis, densities[m], max_height=0.6, cmap_name=palette(target, "density_colormap", "coolwarm"))
        axis.set_title(rf"$m={m}$")
        panel_label(figure, target, letter, fallback[0] - 0.025, fallback[1] + fallback[3] + 0.02)
    save_output(figure, contract, "T005")


def render_noise_target(contract: dict[str, Any], target_id: str, filename: str) -> None:
    target = target_parameters(contract, target_id)
    with np.load(DATA_DIR / filename, allow_pickle=False) as data:
        m_values = data["m_values"].astype(int)
        frequency_sigma = data["frequency_sigma_mhz"]
        coupling_sigma = data["coupling_sigma_mhz"]
        means = [data["even_mean"], data["odd_mean"], data["coupling_mean"]]
        stds = [data["even_std"], data["odd_std"], data["coupling_std"]]
    figure = new_figure(target)
    colors_by_m = {0: "#b9d7ee", 4: "#ff6548", 6: "#c91519", 50: "#6f0000"}
    for column, (letter, x_values, mean, std) in enumerate(
        zip("def", (frequency_sigma, frequency_sigma, coupling_sigma), means, stds, strict=True)
    ):
        fallback = [0.06 + 0.335 * column, 0.08, 0.265, 0.33]
        axis = add_axis(figure, target, f"panel_{letter}", fallback)
        for row, m in enumerate(m_values):
            axis.errorbar(
                x_values,
                mean[row],
                yerr=std[row],
                capsize=0,
                elinewidth=0.8,
                **line_kwargs(
                    target,
                    f"m{m}",
                    color=palette(target, f"m{m}", colors_by_m[int(m)]),
                    fallback_width=1.1,
                    fallback_marker="o",
                    fallback_marker_size=2.8,
                ),
                label=rf"$m={m}$",
            )
        axis.set_ylim(0.2, 1.02)
        axis.set_ylabel(r"$F/F_0$")
        labels = (r"$\sigma/2\pi$ on $\omega_{\rm even}$ (MHz)", r"$\sigma/2\pi$ on $\omega_{\rm odd}$ (MHz)", r"$\sigma/2\pi$ on $J_n$ (MHz)")
        axis.set_xlabel(labels[column])
        axis.set_title("Sim.")
        panel_label(figure, target, letter, fallback[0] - 0.035, fallback[1] + fallback[3] + 0.02)
        if column == 0:
            axis.legend(frameon=False, fontsize=font_value(target, "legend_font_size", 7), ncol=2)
        style_axis(axis, target)
    save_output(figure, contract, target_id)


def render_t006(contract: dict[str, Any]) -> None:
    render_noise_target(contract, "T006", "figS8.npz")


def render_t007(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T007")
    with np.load(DATA_DIR / "fig4_theory.npz", allow_pickle=False) as data:
        times = data["time_ns"]
        populations = data["populations"]
        selected_times = data["selected_times_ns"]
        maps = data["selected_population_maps"]
        ideal_density = data["ideal_w_density"]
    figure = new_figure(target)
    image = None
    for column, letter in enumerate("abc"):
        fallback = [0.055 + 0.32 * column, 0.73, 0.24, 0.17]
        axis = add_axis(figure, target, f"panel_{letter}", fallback)
        image = axis.imshow(
            maps[column],
            origin="lower",
            vmin=0.0,
            vmax=1.0,
            cmap=palette(target, "population_colormap", "coolwarm"),
            interpolation=interpolation(target, "population_map", "nearest"),
        )
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_title(f"{selected_times[column]:.0f} ns")
        panel_label(figure, target, letter, fallback[0] - 0.045, fallback[1] + fallback[3] + 0.01)
    dynamics = add_axis(figure, target, "panel_d", [0.13, 0.44, 0.82, 0.25])
    corner_indices = [0, 2, 6, 8]
    corner_colors = ["#173b70", "#55cbe8", "#ff9b93", "#e6292f"]
    for index, site in enumerate(corner_indices):
        dynamics.plot(
            times,
            populations[:, site],
            **line_kwargs(target, f"corner{index + 1}", color=palette(target, f"corner{index + 1}", corner_colors[index]), fallback_width=1.2),
            label=(r"$P_{Q_{(1,1)}}$", r"$P_{Q_{(1,3)}}$", r"$P_{Q_{(3,1)}}$", r"$P_{Q_{(3,3)}}$")[index],
        )
    dynamics.axvline(55.5556, color="#444444", linestyle="--", linewidth=0.8)
    dynamics.axvline(111.1111, color="#444444", linestyle="--", linewidth=0.8)
    dynamics.set_xlim(times[0], times[-1])
    dynamics.set_ylim(0.0, 1.0)
    dynamics.set_xlabel("Time (ns)")
    dynamics.set_ylabel("Population")
    dynamics.legend(frameon=False, fontsize=font_value(target, "legend_font_size", 6), loc="upper right")
    panel_label(figure, target, "d", 0.035, 0.69)
    style_axis(dynamics, target)
    density = add_axis(figure, target, "panel_f", [0.50, 0.08, 0.42, 0.28])
    density_image = density.imshow(
        np.abs(ideal_density),
        origin="lower",
        vmin=0.0,
        vmax=0.3,
        cmap=palette(target, "density_colormap", "magma"),
        interpolation=interpolation(target, "density_map", "nearest"),
    )
    density.set_xticks([])
    density.set_yticks([])
    panel_label(figure, target, "f", 0.45, 0.37)
    caxis = add_axis(figure, target, "density_colorbar", [0.94, 0.08, 0.02, 0.28])
    figure.colorbar(density_image, cax=caxis).set_label(r"$|\rho|$")
    save_output(figure, contract, "T007")


def render_t008(contract: dict[str, Any]) -> None:
    render_noise_target(contract, "T008", "figS7.npz")


def render_t009(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T009")
    with np.load(DATA_DIR / "figS9.npz", allow_pickle=False) as data:
        m_values = data["m_values"]
        fidelity = data["fidelity"]
        densities = {m: data[f"reduced_density_m{m}"] for m in (0, 4, 50)}
    figure = new_figure(target)
    axis = add_axis(figure, target, "panel_a", [0.075, 0.54, 0.915, 0.42])
    axis.plot(
        m_values,
        fidelity,
        **line_kwargs(target, "fidelity", color=palette(target, "fidelity", "#173b70"), fallback_width=1.2, fallback_marker="o", fallback_marker_size=3.0),
    )
    axis.axhline(float(fidelity[0]), color="#999999", linestyle="--", linewidth=0.8)
    axis.set_xlabel(r"$m$")
    axis.set_ylabel(r"$F$")
    panel_label(figure, target, "a", 0.035, 0.96)
    style_axis(axis, target)
    for column, (letter, m) in enumerate(zip("bcd", (0, 4, 50), strict=True)):
        fallback = [0.08 + 0.31 * column, 0.07, 0.23, 0.36]
        density_axis = add_axis(figure, target, f"panel_{letter}", fallback, projection="3d")
        density_bars(density_axis, densities[m], max_height=0.5, cmap_name=palette(target, "density_colormap", "coolwarm"))
        density_axis.set_title(rf"$m={m}$")
        panel_label(figure, target, letter, fallback[0] - 0.035, fallback[1] + fallback[3] + 0.015)
    save_output(figure, contract, "T009")


def render_t010(contract: dict[str, Any]) -> None:
    target = target_parameters(contract, "T010")
    with np.load(DATA_DIR / "figS10.npz", allow_pickle=False) as data:
        m_values = data["m_values"]
        fidelity = data["fidelity"]
        times = data["evolution_time_ns"]
        populations = {m: data[f"populations_m{m}"] for m in (0, 10, 50)}
    figure = new_figure(target)
    axis = add_axis(figure, target, "panel_a", [0.07, 0.61, 0.92, 0.35])
    axis.plot(
        m_values,
        fidelity,
        **line_kwargs(target, "fidelity", color=palette(target, "fidelity", "#173b70"), fallback_width=1.2, fallback_marker="o", fallback_marker_size=3.0),
    )
    axis.axhline(float(fidelity[0]), color="#999999", linestyle="--", linewidth=0.8)
    axis.set_xlabel(r"$m$")
    axis.set_ylabel(r"$F$")
    panel_label(figure, target, "a", 0.025, 0.96)
    style_axis(axis, target)
    labels = [rf"$({row},{column})$" for row in range(1, 4) for column in range(1, 4)]
    for column, (letter, m) in enumerate(zip("bcd", (0, 10, 50), strict=True)):
        fallback = [0.07 + 0.31 * column, 0.07, 0.24, 0.44]
        heatmap = add_axis(figure, target, f"panel_{letter}", fallback)
        population_spectrum(heatmap, target, times, populations[m], coordinates=labels, vmax_negative=0.25)
        heatmap.set_xlabel("Qubit")
        heatmap.set_title(rf"$m={m}$")
        panel_label(figure, target, letter, fallback[0] - 0.035, fallback[1] + fallback[3] + 0.015)
        style_axis(heatmap, target)
    save_output(figure, contract, "T010")


if __name__ == "__main__":
    raise SystemExit(main())
