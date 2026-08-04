#!/usr/bin/env python3
"""Render paper figures from frozen numerical arrays and a style-only contract."""
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
    return 0


def render_t001(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T001"]
    with np.load(DATA_DIR / "fig2_optimal.npz", allow_pickle=False) as data:
        phi = data["phi_over_pi"]
        curves = [
            (0.75, data["hermitian_p_0p75"], data["nonhermitian_p_0p75"]),
            (0.15, data["hermitian_p_0p15"], data["nonhermitian_p_0p15"]),
        ]

    fig = new_figure(target)
    axes = [
        add_axis(fig, target, "panel_c", [0.13, 0.53, 0.855, 0.43]),
        add_axis(fig, target, "panel_d", [0.13, 0.16, 0.855, 0.37]),
    ]
    panel_labels = ["(c)", "(d)"]
    colors = [palette(target, "p_0p75", "#0000ff"), palette(target, "p_0p15", "#ff2020")]
    for axis, (p_value, h_curve, nh_curve), color, label in zip(
        axes, curves, colors, panel_labels, strict=True
    ):
        axis.plot(phi, nh_curve, color=color, **line_kwargs(target, "nonhermitian", "--", 0.8))
        axis.plot(phi, h_curve, color=color, **line_kwargs(target, "hermitian", "-", 0.8))
        axis.set_xlim(0.0, 4.1)
        axis.set_xticks([0, 1, 2, 3, 4])
        axis.text(-0.13, 0.92, label, transform=axis.transAxes, va="top")
        axis.text(0.98, 0.86, f"$p={p_value:g}$", transform=axis.transAxes, ha="right")
        style_axis(axis, target)
    axes[0].set_ylim(0.28, 0.62)
    axes[0].set_yticks([0.4, 0.6])
    axes[0].tick_params(labelbottom=False)
    axes[1].set_ylim(0.0, 1.02)
    axes[1].set_yticks([0.0, 0.5, 1.0])
    axes[1].set_xlabel(r"$\phi/\pi$")
    fig.text(0.018, 0.52, r"$I/n_0$", rotation=90, va="center", fontsize=font_value(target, "axis_label_size", 10))
    save_target(fig, contract, "T001")


def render_t002(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T002"]
    with np.load(DATA_DIR / "fig2_expectations.npz", allow_pickle=False) as data:
        theta = data["theta_over_pi"]
        payload = {key: data[key] for key in data.files if key != "theta_over_pi"}

    fig = new_figure(target)
    axes = [
        fig.add_axes(
            target.get("axes_positions", {}).get("panel_e", [0.03, 0.52, 0.96, 0.46]),
            projection="3d",
        ),
        fig.add_axes(
            target.get("axes_positions", {}).get("panel_f", [0.03, 0.02, 0.96, 0.46]),
            projection="3d",
        ),
    ]
    colors = {
        "H": palette(target, "hermitian", "#111111"),
        "nH": palette(target, "nonhermitian", "#ff2020"),
        "nH_dagger": palette(target, "nonhermitian_adjoint", "#0000ff"),
    }
    lane_labels = [r"$A'_H$", r"$A'_{nH}$", r"$A_{nH}^{\prime\dagger}$"]
    for axis, p_value, panel_label in zip(axes, (0.15, 0.75), ("(e)", "(f)"), strict=True):
        key = str(p_value).replace(".", "p")
        for lane, name in enumerate(("H", "nH", "nH_dagger")):
            values = payload[f"{name}_p_{key}"]
            lane_axis = np.full(theta.shape, float(lane))
            axis.plot(
                theta,
                lane_axis,
                values.real,
                color=colors[name],
                **line_kwargs(target, f"{name}_real", "-", 0.8),
            )
            axis.plot(
                theta,
                lane_axis,
                values.imag,
                color=colors[name],
                **line_kwargs(target, f"{name}_imag", "--", 0.8),
            )
        axis.set_xlim(-2.0, 4.0)
        axis.set_ylim(-0.25, 5.25)
        axis.set_yticks(range(6))
        axis.set_yticklabels(lane_labels + ["", "", ""])
        axis.set_zlim((-0.82, 0.82) if p_value == 0.15 else (-0.62, 0.62))
        axis.set_xticks([-2, 0, 2, 4])
        axis.set_box_aspect((2.5, 1.2, 1.0), zoom=1.08)
        axis.view_init(elev=18.0, azim=-66.0)
        axis.tick_params(labelsize=font_value(target, "tick_label_size", 9), pad=0)
        axis.set_title(rf"{panel_label}  $p={p_value:g}$", pad=0)
        axis.grid(True, alpha=0.25)
        axis.xaxis.pane.set_alpha(0.0)
        axis.yaxis.pane.set_alpha(0.0)
        axis.zaxis.pane.set_alpha(0.0)
    save_target(fig, contract, "T002")


def render_t003(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T003"]
    with np.load(DATA_DIR / "fig3a.npz", allow_pickle=False) as data:
        p_grid = data["p"]
        hermitian = data["hermitian"]
        nonhermitian = data["nonhermitian_paper_intended"]

    fig = new_figure(target)
    left = add_axis(fig, target, "left_branch", [0.14, 0.17, 0.405, 0.77])
    right = add_axis(fig, target, "right_branch", [0.565, 0.17, 0.405, 0.77])
    for axis in (left, right):
        axis.plot(p_grid, nonhermitian, color=palette(target, "nonhermitian", "#ff2020"), label="non-Hermitian", **line_kwargs(target, "nonhermitian", "-", 0.8))
        axis.plot(p_grid, hermitian, color=palette(target, "hermitian", "#111111"), label="Hermitian", **line_kwargs(target, "hermitian", "-", 0.8))
        axis.set_ylim(-1.5, 24.0)
        axis.set_yticks([0, 5, 10, 15, 20])
        style_axis(axis, target)
    left.set_xlim(0.0, 0.43)
    right.set_xlim(0.57, 1.0)
    left.set_xticks([0.0, 0.2])
    right.set_xticks([0.8, 1.0])
    left.spines["right"].set_visible(False)
    right.spines["left"].set_visible(False)
    left.tick_params(which="both", right=False)
    right.tick_params(which="both", left=False, labelleft=False)
    diagonal = 0.018
    cut_style = {"color": palette(target, "axis", "#111111"), "clip_on": False, "linewidth": 0.8}
    left.plot((1 - diagonal, 1 + diagonal), (-diagonal, +diagonal), transform=left.transAxes, **cut_style)
    right.plot((-diagonal, +diagonal), (-diagonal, +diagonal), transform=right.transAxes, **cut_style)
    left.set_ylabel(r"$(\Delta\theta)^2$")
    fig.supxlabel(r"$p$", fontsize=font_value(target, "axis_label_size", 10), y=0.02)
    left.legend(
        handles=[left.lines[1], left.lines[0]],
        labels=["Hermitian", "non-Hermitian"],
        frameon=False,
        fontsize=font_value(target, "legend_font_size", 8),
        loc="upper left",
    )
    left.text(-0.18, 1.03, "(a)", transform=left.transAxes)
    save_target(fig, contract, "T003")


def render_t004(contract: dict[str, Any]) -> None:
    target = contract["render_parameters"]["T004"]
    with np.load(DATA_DIR / "fig3bc.npz", allow_pickle=False) as data:
        gamma = data["gamma"]
        h_variance = data["hermitian_variance"]
        nh_variance = data["nonhermitian_variance"]
        h_rate = data["hermitian_rate"]
        nh_rate = data["nonhermitian_rate"]

    fig = new_figure(target)
    axes = [
        add_axis(fig, target, "panel_b", [0.09, 0.17, 0.405, 0.77]),
        add_axis(fig, target, "panel_c", [0.58, 0.17, 0.405, 0.77]),
    ]
    axes[0].plot(gamma, h_variance, color=palette(target, "hermitian", "#111111"), label="Hermitian", **line_kwargs(target, "hermitian", "-", 0.8))
    axes[0].plot(gamma, nh_variance, color=palette(target, "nonhermitian", "#ff2020"), label="non-Hermitian", **line_kwargs(target, "nonhermitian", "-", 0.8))
    axes[0].set_ylabel(r"$(\Delta\theta)^2$")
    axes[0].set_ylim(0.0, 3.35)
    axes[0].set_yticks([0, 1, 2, 3])
    axes[1].plot(gamma, h_rate, color=palette(target, "hermitian", "#111111"), label="Hermitian", **line_kwargs(target, "hermitian", "-", 0.8))
    axes[1].plot(gamma, nh_rate, color=palette(target, "nonhermitian", "#ff2020"), label="non-Hermitian", **line_kwargs(target, "nonhermitian", "-", 0.8))
    axes[1].set_ylabel(r"$\partial_\gamma(\Delta\theta)^2$")
    axes[1].set_ylim(0.0, 9.2)
    axes[1].set_yticks([0, 2, 4, 6, 8])
    for axis, panel_label in zip(axes, ["(b)", "(c)"], strict=True):
        axis.set_xlim(-0.03, 0.63)
        axis.set_xticks([0.0, 0.2, 0.4, 0.6])
        axis.set_xlabel(r"$\gamma$")
        style_axis(axis, target)
        axis.text(-0.16, 1.03, panel_label, transform=axis.transAxes)
        axis.legend(frameon=False, fontsize=font_value(target, "legend_font_size", 8), loc="upper left")
    save_target(fig, contract, "T004")


def new_figure(target: dict[str, Any]) -> plt.Figure:
    apply_typography(target)
    canvas = target.get("canvas", {})
    return plt.figure(
        figsize=(float(canvas.get("width_inches", 6.0)), float(canvas.get("height_inches", 4.0))),
        facecolor=canvas.get("facecolor", "white"),
    )


def add_axis(fig: plt.Figure, target: dict[str, Any], role: str, default: list[float]) -> plt.Axes:
    return fig.add_axes(target.get("axes_positions", {}).get(role, default))


def style_axis(axis: plt.Axes, target: dict[str, Any]) -> None:
    axis.grid(False)
    axis.tick_params(
        which="both",
        direction="in",
        top=True,
        right=True,
        width=0.8,
        labelsize=font_value(target, "tick_label_size", 9),
    )
    axis.minorticks_on()
    axis.xaxis.label.set_size(font_value(target, "axis_label_size", 10))
    axis.yaxis.label.set_size(font_value(target, "axis_label_size", 10))
    for spine in axis.spines.values():
        spine.set_linewidth(0.8)


def line_kwargs(target: dict[str, Any], role: str, default_style: str, default_width: float) -> dict[str, Any]:
    style = target.get("line_styles", {}).get(role, {})
    result: dict[str, Any] = {
        "linestyle": style.get("line_style", default_style),
        "linewidth": float(style.get("line_width", default_width)),
        "alpha": float(style.get("alpha", 1.0)),
    }
    marker = style.get("marker")
    if marker and marker != "none":
        result["marker"] = marker
        result["markersize"] = float(style.get("marker_size", 3.0))
    interpolation = target.get("interpolation", {}).get(role, "linear")
    if interpolation.startswith("step-"):
        result["drawstyle"] = f"steps-{interpolation.removeprefix('step-')}"
    return result


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
    dpi = float(target.get("canvas", {}).get("dpi", 100))
    fig.savefig(output, dpi=dpi, facecolor=target.get("canvas", {}).get("facecolor", "white"))
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
