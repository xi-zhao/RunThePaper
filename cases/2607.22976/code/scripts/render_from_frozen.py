#!/usr/bin/env python3
"""Render all numerical paper figures from frozen arrays and style-only input."""
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
    return 0


def render_t001(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T001"]
    with np.load(DATA_DIR / "fig2.npz", allow_pickle=False) as data:
        values = data["eigenvalues"]
        probabilities = data["eigenvectors_abs"]
        sites = data["sites"]
        pbc = [data[f"pbc_domain_{index}"] for index in range(1, 4)]
        real_axis = data["real_axis"]
        imag_axis = data["imag_axis"]
        delta2 = data["delta2"]
        delta3 = data["delta3"]
        lengths = tuple(int(item) for item in data["domain_lengths"])
        selections = {
            key: int(data[f"representative_{key}"])
            for key in ("2|3_standing", "2|3_traveling", "3|1_standing", "3|1_traveling")
        }

    fig = new_figure(target)
    defaults = [
        [0.052, 0.13, 0.196, 0.82],
        [0.296, 0.13, 0.196, 0.82],
        [0.550, 0.13, 0.196, 0.82],
        [0.804, 0.13, 0.193, 0.82],
    ]
    axes = [add_axis(fig, target, f"panel_{letter}", box) for letter, box in zip("abcd", defaults, strict=True)]
    real_mesh, imag_mesh = np.meshgrid(real_axis, imag_axis)
    axes[0].contourf(real_mesh, imag_mesh, delta2 > 0, levels=[0.5, 1.5], colors=[palette(target, "delta2_fill", "#bfdbfe")], alpha=0.8)
    axes[0].contourf(real_mesh, imag_mesh, delta3 > 0, levels=[0.5, 1.5], colors=[palette(target, "delta3_fill", "#fecaca")], alpha=0.65)
    for index, curve in enumerate(pbc, start=1):
        axes[0].plot(
            curve.real,
            curve.imag,
            color=palette(target, f"pbc_domain_{index}", ("#159d82", "#f59e0b", "#7559f2")[index - 1]),
            **line_kwargs(target, f"pbc_domain_{index}", "--", 1.5),
        )
    axes[0].scatter(values.real, values.imag, color=palette(target, "ring_spectrum", "#606775"), **scatter_kwargs(target, "ring_spectrum", 2.0, 0.75))
    marker_map = {"2|3_standing": "s", "2|3_traveling": "s", "3|1_standing": "d", "3|1_traveling": "d"}
    for key, index in selections.items():
        color = palette(target, "interface_23", "#2563eb") if key.startswith("2|3") else palette(target, "interface_31", "#dc2626")
        axes[0].scatter(
            values[index].real,
            values[index].imag,
            marker=marker_map[key],
            s=34,
            facecolor="white" if key.endswith("traveling") else color,
            edgecolor=color,
            linewidth=1.2,
            zorder=5,
        )
    axes[0].set_xlabel(r"$\mathrm{Re}\,E$")
    axes[0].set_ylabel(r"$\mathrm{Im}\,E$")
    axes[0].set_title("(a) PBC, winding mismatch, DW ring")

    shade_domains(axes[1], lengths, target)
    for column in range(probabilities.shape[1]):
        axes[1].plot(sites, probabilities[:, column], color=palette(target, "all_profiles", "#273142"), **line_kwargs(target, "all_profiles", "-", 0.35, default_alpha=0.14))
    axes[1].set_xlim(0, values.size - 1)
    axes[1].set_ylim(0, max(0.52, float(np.max(probabilities)) * 1.02))
    axes[1].set_xlabel(r"$x$")
    axes[1].set_ylabel(r"$|\psi|$")
    axes[1].set_title("(b) all right eigenstates")

    for axis, interface in zip(axes[2:], ("2|3", "3|1"), strict=True):
        shade_domains(axis, lengths, target)
        for state_class, default_style in (("standing", "-"), ("traveling", "--")):
            index = selections[f"{interface}_{state_class}"]
            axis.semilogy(
                sites,
                np.maximum(probabilities[:, index], 1e-12),
                color=palette(target, state_class, "#273142"),
                label=state_class,
                **line_kwargs(target, state_class, default_style, 1.25),
            )
        axis.set_xlim(0, values.size - 1)
        axis.set_ylim(1e-7, 1.0)
        axis.set_xlabel(r"$x$")
        axis.set_ylabel(r"$|\psi|$")
        axis.set_title(f"({'c' if interface == '2|3' else 'd'}) interface {interface}")
    axes[2].legend(frameon=False, fontsize=font_value(target, "legend_font_size", 8))
    for axis in axes:
        style_axis(axis, target)
    save_target(fig, contract, "T001")


def render_t002(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T002"]
    with np.load(DATA_DIR / "fig3.npz", allow_pickle=False) as data:
        values = data["ring_eigenvalues"]
        thermo = data["thermodynamic_energies"]
        samples = data["sample_energies"]
        mu_axis = data["mu_axis"]
        surfaces = data["ronkin_surfaces"]
        tolerances = data["ronkin_plateau_tolerances"]
        constituent = [data[f"constituent_domain_{index}"] for index in range(1, 4)]
        obc_beta = [data[f"obc_beta_domain_{index}"] for index in range(1, 4)]
        beta_points = [data[f"domain_{index}"] for index in range(1, 4)]
        beta_classes = [data[f"domain_{index}_class"] for index in range(1, 4)]

    fig = new_figure(target)
    defaults = [
        [0.052, 0.565, 0.178, 0.415],
        [0.299, 0.565, 0.178, 0.415],
        [0.545, 0.565, 0.178, 0.415],
        [0.789, 0.565, 0.178, 0.415],
        [0.052, 0.055, 0.178, 0.405],
        [0.299, 0.055, 0.178, 0.405],
        [0.545, 0.055, 0.178, 0.405],
        [0.789, 0.055, 0.178, 0.405],
    ]
    axes = [add_axis(fig, target, f"panel_{letter}", box) for letter, box in zip("abcdefgh", defaults, strict=True)]
    axes[0].scatter(values.real, values.imag, facecolor="none", edgecolor=palette(target, "finite_ring", "#4b5563"), linewidth=0.45, **scatter_kwargs(target, "finite_ring", 2.8, 1.0))
    axes[0].scatter(thermo.real, thermo.imag, color=palette(target, "gbz_conditions", "#0f172a"), **scatter_kwargs(target, "gbz_conditions", 1.1, 0.6))
    for number, (energy, color, marker) in enumerate(
        zip(samples, (palette(target, "sample_e1", "#64748b"), palette(target, "sample_e2", "#159d82"), palette(target, "sample_e3", "#dc2626")), ("o", "s", "d"), strict=True),
        start=1,
    ):
        axes[0].scatter(energy.real, energy.imag, s=35, marker=marker, facecolor="white", edgecolor=color, linewidth=1.2, zorder=5)
        axes[0].text(energy.real + 0.06, energy.imag + 0.05, f"E{number}", color=color)
    axes[0].set_xlabel(r"$\mathrm{Re}\,E$")
    axes[0].set_ylabel(r"$\mathrm{Im}\,E$")
    axes[0].set_title("(a) ring spectrum from GBZ collapse")

    mu1, mu2 = np.meshgrid(mu_axis, mu_axis)
    for number, axis in enumerate(axes[1:4]):
        surface = surfaces[number]
        axis.contourf(mu1, mu2, surface, levels=16, cmap=palette(target, "ronkin_colormap", "Blues"))
        axis.contour(mu1, mu2, surface, levels=12, colors=palette(target, "ronkin_contours", "#7890a8"), linewidths=0.35, alpha=0.65)
        axis.contourf(mu1, mu2, surface <= tolerances[number], levels=[0.5, 1.5], colors=[palette(target, "ronkin_plateau", "#6ee7b7")], alpha=0.7)
        axis.set_xlabel(r"$\mu_1$")
        axis.set_ylabel(r"$\mu_2$")
        axis.set_title(f"({chr(98 + number)}) constrained Ronkin, E{number + 1}")

    axes[4].scatter(values.real, values.imag, color=palette(target, "dw_ring_gbz", "#dc2626"), label="DW ring", **scatter_kwargs(target, "dw_ring_gbz", 2.2, 0.8))
    for spectrum in constituent:
        axes[4].scatter(spectrum.real, spectrum.imag, color=palette(target, "constituent_obc", "#2563eb"), **scatter_kwargs(target, "constituent_obc", 1.7, 0.55))
    axes[4].set_xlabel(r"$\mathrm{Re}\,E$")
    axes[4].set_ylabel(r"$\mathrm{Im}\,E$")
    axes[4].set_title("(e) ring vs constituent (a)GBZ")

    for domain, axis in enumerate(axes[5:8]):
        for state_class in ("traveling", "standing"):
            mask = beta_classes[domain] == state_class
            axis.scatter(
                beta_points[domain][mask].real,
                beta_points[domain][mask].imag,
                color=palette(target, "dw_ring_gbz", "#dc2626"),
                **scatter_kwargs(target, "dw_ring_gbz", 1.7, 0.65),
            )
        axis.scatter(obc_beta[domain].real, obc_beta[domain].imag, color=palette(target, "constituent_obc", "#2563eb"), **scatter_kwargs(target, "constituent_obc", 2.0, 0.65))
        axis.axhline(0.0, color=palette(target, "axis_guides", "#cbd5e1"), lw=0.4)
        axis.axvline(0.0, color=palette(target, "axis_guides", "#cbd5e1"), lw=0.4)
        axis.set_xlabel(rf"$\mathrm{{Re}}\,\beta_{domain + 1}$")
        axis.set_ylabel(rf"$\mathrm{{Im}}\,\beta_{domain + 1}$")
        axis.set_title(f"({chr(102 + domain)}) domain {domain + 1} GBZ")
    for axis in axes:
        style_axis(axis, target)
    save_target(fig, contract, "T002")


def render_t003(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T003"]
    with np.load(DATA_DIR / "fig4.npz", allow_pickle=False) as data:
        real_axis = data["real_axis"]
        imag_axis = data["imag_axis"]
        winding = data["winding"]
        reliable = data["reliable_mask"]
        values = data["ring_eigenvalues"]
        classes = data["ring_classes"]
    reliable_winding = np.where(reliable, winding, 0.0)
    nonzero = np.abs(reliable_winding) >= 0.5
    real_mesh, imag_mesh = np.meshgrid(real_axis, imag_axis)

    fig = new_figure(target)
    axis = add_axis(fig, target, "main", [0.15, 0.13, 0.848, 0.86])
    axis.contourf(real_mesh, imag_mesh, nonzero, levels=[0.5, 1.5], colors=[palette(target, "winding_fill", "#fee2e2")], alpha=0.9)
    axis.contour(real_mesh, imag_mesh, nonzero, levels=[0.5], colors=[palette(target, "traveling_spectrum", "#dc2626")], linewidths=0.8)
    standing = classes == "standing"
    axis.scatter(values[~standing].real, values[~standing].imag, color=palette(target, "traveling_spectrum", "#dc2626"), **scatter_kwargs(target, "traveling_spectrum", 2.6, 1.0))
    axis.scatter(values[standing].real, values[standing].imag, color=palette(target, "standing_spectrum", "#2563eb"), **scatter_kwargs(target, "standing_spectrum", 2.6, 1.0))
    nonzero_values = reliable_winding[nonzero]
    if nonzero_values.size:
        dominant = int(np.rint(np.median(nonzero_values)))
        axis.text(0.0, 0.0, rf"$W_{{DW}}={dominant}$", ha="center", va="center", fontsize=font_value(target, "font_size", 16), bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75})
    axis.set_xlabel(r"$\mathrm{Re}\,E$")
    axis.set_ylabel(r"$\mathrm{Im}\,E$")
    axis.set_title("Flux spectral winding")
    style_axis(axis, target)
    save_target(fig, contract, "T003")


def render_t004(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T004"]
    with np.load(DATA_DIR / "figS1.npz", allow_pickle=False) as data:
        real_axis = data["real_axis"]
        imag_axis = data["imag_axis"]
        densities = [data["ronkin_density"], data["diagonal_density"]]
        values = data["eigenvalues"]
    extent = [real_axis[0], real_axis[-1], imag_axis[0], imag_axis[-1]]

    fig = new_figure(target)
    axes = [
        add_axis(fig, target, "panel_a", [0.10, 0.17, 0.325, 0.70]),
        add_axis(fig, target, "panel_b", [0.53, 0.17, 0.325, 0.70]),
    ]
    images = []
    for index, (axis, density) in enumerate(zip(axes, densities, strict=True)):
        role = "ronkin_density" if index == 0 else "diagonal_density"
        image = axis.imshow(
            density,
            origin="lower",
            extent=extent,
            aspect="auto",
            cmap=palette(target, "density_colormap", "Blues"),
            vmin=0.0,
            vmax=1.0,
            interpolation=target.get("interpolation", {}).get(role, "nearest"),
        )
        images.append(image)
        axis.scatter(values.real, values.imag, color=palette(target, "spectrum_overlay", "#173f67"), **scatter_kwargs(target, "spectrum_overlay", 1.1, 0.35))
        axis.set_xlabel(r"$\mathrm{Re}\,E$")
        axis.set_ylabel(r"$\mathrm{Im}\,E$")
        axis.set_title(f"({'a' if index == 0 else 'b'})")
        style_axis(axis, target)
    colorbar_axis = add_axis(fig, target, "colorbar", [0.87, 0.14, 0.022, 0.74])
    fig.colorbar(images[-1], cax=colorbar_axis, label=r"normalized $\rho(E)$")
    save_target(fig, contract, "T004")


def render_t005(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T005"]
    with np.load(DATA_DIR / "figS2.npz", allow_pickle=False) as data:
        ring = data["ring_eigenvalues"]
        chain = data["chain_eigenvalues"]
        constituent = [data[f"constituent_domain_{index}"] for index in range(1, 4)]

    fig = new_figure(target)
    axes = [
        add_axis(fig, target, "panel_b", [0.105, 0.18, 0.335, 0.77]),
        add_axis(fig, target, "panel_c", [0.575, 0.18, 0.335, 0.77]),
    ]
    axes[0].scatter(ring.real, ring.imag, facecolor="none", edgecolor=palette(target, "ring_spectrum", "#dc2626"), linewidth=0.5, label="DW-ring spec.", **scatter_kwargs(target, "ring_spectrum", 2.2, 1.0))
    axes[0].scatter(chain.real, chain.imag, color=palette(target, "opened_chain", "#2563eb"), label="DW-chain spec.", **scatter_kwargs(target, "opened_chain", 2.2, 1.0))
    for domain, spectrum in enumerate(constituent, start=1):
        axes[1].scatter(
            spectrum.real,
            spectrum.imag,
            color=palette(target, f"domain_{domain}_obc", ("#159d82", "#f59e0b", "#7559f2")[domain - 1]),
            label=f"domain {domain} OBC",
            **scatter_kwargs(target, f"domain_{domain}_obc", 2.4, 1.0),
        )
    for axis, label in zip(axes, ("(b)", "(c)"), strict=True):
        axis.set_xlabel(r"$\mathrm{Re}\,E$")
        axis.set_ylabel(r"$\mathrm{Im}\,E$")
        axis.set_title(label)
        axis.legend(frameon=False, fontsize=font_value(target, "legend_font_size", 8))
        style_axis(axis, target)
    save_target(fig, contract, "T005")


def new_figure(target: dict[str, Any]) -> plt.Figure:
    apply_typography(target)
    canvas = target.get("canvas", {})
    return plt.figure(
        figsize=(float(canvas.get("width_inches", 6.0)), float(canvas.get("height_inches", 4.0))),
        facecolor=canvas.get("facecolor", "white"),
    )


def add_axis(fig: plt.Figure, target: dict[str, Any], role: str, default: list[float]) -> plt.Axes:
    return fig.add_axes(target.get("axes_positions", {}).get(role, default))


def shade_domains(axis: plt.Axes, lengths: tuple[int, int, int], target: dict[str, Any]) -> None:
    start = 0
    defaults = ("#dbeafe", "#dcfce7", "#f3e8ff")
    for index, (length, default) in enumerate(zip(lengths, defaults, strict=True), start=1):
        axis.axvspan(start, start + length, color=palette(target, f"domain_{index}_background", default), alpha=0.34, linewidth=0)
        start += length
    for boundary in np.cumsum(lengths)[:-1]:
        axis.axvline(boundary, color=palette(target, "domain_boundary", "#64748b"), ls="--", lw=0.7)


def style_axis(axis: plt.Axes, target: dict[str, Any]) -> None:
    axis.tick_params(labelsize=font_value(target, "tick_label_size", 9))
    axis.xaxis.label.set_size(font_value(target, "axis_label_size", 10))
    axis.yaxis.label.set_size(font_value(target, "axis_label_size", 10))
    axis.title.set_size(font_value(target, "font_size", 9))
    axis.grid(alpha=0.12)


def line_kwargs(
    target: dict[str, Any],
    role: str,
    default_style: str,
    default_width: float,
    *,
    default_alpha: float = 1.0,
) -> dict[str, Any]:
    style = target.get("line_styles", {}).get(role, {})
    result: dict[str, Any] = {
        "linestyle": style.get("line_style", default_style),
        "linewidth": float(style.get("line_width", default_width)),
        "alpha": float(style.get("alpha", default_alpha)),
    }
    marker = style.get("marker")
    if marker and marker != "none":
        result["marker"] = marker
        result["markersize"] = float(style.get("marker_size", 3.0))
    interpolation = target.get("interpolation", {}).get(role, "linear")
    if interpolation.startswith("step-"):
        result["drawstyle"] = f"steps-{interpolation.removeprefix('step-')}"
    return result


def scatter_kwargs(target: dict[str, Any], role: str, default_marker_size: float, default_alpha: float) -> dict[str, Any]:
    style = target.get("line_styles", {}).get(role, {})
    marker = style.get("marker", "o")
    if marker == "none":
        marker = "o"
    marker_size = float(style.get("marker_size", default_marker_size))
    return {"marker": marker, "s": marker_size * marker_size, "alpha": float(style.get("alpha", default_alpha))}


def palette(target: dict[str, Any], role: str, default: str) -> str:
    return str(target.get("palette", {}).get(role, default))


def font_value(target: dict[str, Any], field: str, default: float) -> float:
    return float(target.get("typography", {}).get(field, default))


def apply_typography(target: dict[str, Any]) -> None:
    typography = target.get("typography", {})
    plt.rcParams.update(
        {
            "font.family": typography.get("font_family", "DejaVu Sans"),
            "font.size": font_value(target, "font_size", 9),
            "font.weight": typography.get("font_weight", "normal"),
            "font.style": typography.get("font_style", "normal"),
            "mathtext.fontset": typography.get("math_fontset", "dejavusans"),
        }
    )


def save_target(fig: plt.Figure, contract: dict[str, Any], target_id: str) -> None:
    target = contract["render_parameters"][target_id]
    outputs = contract["rendered_outputs"][target_id]
    if len(outputs) != 1:
        raise ValueError(f"{target_id} must declare exactly one rendered output")
    output = Path(outputs[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output,
        dpi=float(target.get("canvas", {}).get("dpi", 100)),
        facecolor=target.get("canvas", {}).get("facecolor", "white"),
    )
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
