#!/usr/bin/env python3
"""Render paper-facing figures from an already frozen numerical bundle.

This script deliberately has no code path that opens paper PDFs, reference
figures, or author data.  It verifies the numeric freeze and accepts only
declared presentation keys before loading any arrays.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_contract(workspace: Path, contract_path: Path) -> tuple[dict, dict, dict, list[dict]]:
    contract = _load_json(contract_path)
    freeze_path = workspace / contract["numeric_freeze"]["path"]
    actual_freeze_sha = _sha256(freeze_path)
    expected_freeze_sha = contract["numeric_freeze"]["sha256"]
    if actual_freeze_sha != expected_freeze_sha:
        raise RuntimeError(f"numeric freeze changed: {actual_freeze_sha} != {expected_freeze_sha}")

    freeze = _load_json(freeze_path)
    style_path = workspace / contract["style_config"]["path"]
    style = _load_json(style_path)
    allowed = set(contract["style_config"]["allowed_keys"])
    unknown = sorted(set(style) - allowed)
    if unknown:
        raise RuntimeError(f"render style contains non-whitelisted keys: {unknown}")

    verified = []
    for item in freeze["numeric_files"]:
        numeric_path = workspace / item["path"]
        actual = _sha256(numeric_path)
        if actual != item["sha256"]:
            raise RuntimeError(f"frozen numeric file changed: {item['path']}")
        verified.append({"path": item["path"], "sha256": actual, "bytes": numeric_path.stat().st_size})
    return contract, freeze, style, verified


def _configure(style: dict) -> None:
    plt.rcParams.update(
        {
            "font.family": style["font_family"],
            "font.size": style["font_size"],
            "axes.labelsize": style["axes_label_size"],
            "axes.linewidth": style["axes_linewidth"],
            "legend.fontsize": style["legend_font_size"],
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": style["axes_linewidth"],
            "ytick.major.width": style["axes_linewidth"],
            "mathtext.fontset": "dejavusans",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def _figure(style: dict, key: str) -> plt.Figure:
    width, height = style["figure_pixels"][key]
    dpi = style["dpi"]
    return plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)


def _finish(fig: plt.Figure, path: Path, style: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=style["dpi"], facecolor="white", edgecolor="none")
    plt.close(fig)


def _paper_axes(ax: plt.Axes, style: dict) -> None:
    ax.tick_params(length=4, width=style["axes_linewidth"], top=False, right=False)
    for spine in ax.spines.values():
        spine.set_linewidth(style["axes_linewidth"])


def render_feedback(workspace: Path, style: dict) -> list[Path]:
    data = np.load(workspace / "outputs/data/feedback_curves.npz")
    fig = _figure(style, "feedback")
    ax = fig.add_axes([0.12, 0.13, 0.83, 0.81])
    colors = ["#242424", "#6b4c78"]
    for index, theta in enumerate(data["theta"]):
        label = r"$\theta_0=0$" if abs(theta) < 1e-12 else r"$\theta_0=-0.4\pi$"
        ax.plot(data["r"], data["raw"][index], "--", color="#858585", lw=style["line_width"], label=f"{label}, no correction")
        ax.plot(data["r"], data["corrected"][index], color=colors[index], lw=style["line_width"], label=f"{label}, with correction")
    ax.set(xlabel=r"Noise scaling factor $r$", ylabel=r"$\langle Z_0\rangle$", xlim=(1, 10), ylim=(-0.05, 1.03))
    ax.set_xticks([1, 4, 7, 10])
    ax.legend(frameon=False, ncol=2, loc="lower left")
    _paper_axes(ax, style)
    output = workspace / "outputs/figures/main_fig2c_feedback.png"
    _finish(fig, output, style)
    return [output]


def render_repetition(workspace: Path, style: dict) -> list[Path]:
    one = np.load(workspace / "outputs/data/repetition_one_round.npz")
    multi = np.load(workspace / "outputs/data/repetition_multi_round.npz")
    colors = style["palette"]
    outputs: list[Path] = []

    fig = _figure(style, "repetition")
    ax = fig.add_axes([0.08, 0.15, 0.88, 0.79])
    for index, distance in enumerate(one["distances"]):
        ax.plot(one["r"], one["corrected_analytic"][index], "--", color=colors[index], lw=style["line_width"], label=rf"$d={int(distance)}$")
    ax.plot(one["r"], one["raw_analytic"], "--", color=colors[5], lw=style["line_width"], label="No correction")
    ax.set(xlabel=r"Noise scaling factor $r$", ylabel=r"$\langle Z_L\rangle$", xlim=(1, 10), ylim=(0, 1.03))
    ax.set_xticks([1, 4, 7, 10])
    ax.legend(frameon=False, ncol=2, loc="lower left")
    _paper_axes(ax, style)
    output = workspace / "outputs/figures/main_fig3c_repetition.png"
    _finish(fig, output, style)
    outputs.append(output)

    fig = _figure(style, "repetition")
    ax = fig.add_axes([0.08, 0.15, 0.88, 0.79])
    for index, distance in enumerate(one["distances"]):
        ax.plot(one["r"], one["raw_analytic"], "--", color=colors[index], lw=style["line_width"], alpha=0.72, label=rf"$d={int(distance)}$")
    ax.set(xlabel=r"Noise scaling factor $r$", ylabel=r"$\langle Z_L\rangle$", xlim=(1, 10), ylim=(0, 1.03))
    ax.set_xticks([1, 4, 7, 10])
    ax.legend(frameon=False, loc="lower left")
    _paper_axes(ax, style)
    output = workspace / "outputs/figures/supp_fig4_repetition.png"
    _finish(fig, output, style)
    outputs.append(output)

    fig = _figure(style, "repetition")
    ax = fig.add_axes([0.08, 0.15, 0.88, 0.79])
    for index, rounds in enumerate(multi["rounds"]):
        ax.plot(multi["r"], multi["corrected_analytic"][index], "--", color=colors[index + 1], lw=style["line_width"], label=rf"$M={int(rounds)}$")
    ax.set(xlabel=r"Noise scaling factor $r$", ylabel=r"$\langle Z_L\rangle$", xlim=(1, 2.5), ylim=(0.80, 1.005))
    ax.set_xticks([1.0, 1.5, 2.0, 2.5])
    ax.legend(frameon=False, loc="lower left", ncol=2)
    _paper_axes(ax, style)
    output = workspace / "outputs/figures/main_fig3e_repetition.png"
    _finish(fig, output, style)
    outputs.append(output)
    return outputs


def render_surface(workspace: Path, style: dict, contract: dict) -> list[Path]:
    data = np.load(workspace / "outputs/data/surface_code.npz")
    outputs: list[Path] = []
    crimson, blue = style["palette"][2], style["palette"][6]

    selected = contract["display_slices"]["surface_bloch_r"]
    fig = _figure(style, "surface_bloch")
    axes = fig.subplots(1, len(selected) + 1)
    for axis in axes:
        axis.axhline(0, color="#888888", lw=0.6)
        axis.axvline(0, color="#888888", lw=0.6)
        axis.set_aspect("equal")
        axis.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), xticks=[], yticks=[])
        _paper_axes(axis, style)
    axes[0].plot(data["bloch_ideal_x"], data["bloch_ideal_z"], color="#222222", lw=style["line_width"])
    axes[0].set_title("Initial states")
    for axis, scale in zip(axes[1:], selected, strict=True):
        index = int(np.argmin(np.abs(data["r"] - scale)))
        axis.plot(data["bloch_corrected_x"][index], data["bloch_corrected_z"][index], color=crimson, lw=style["line_width"], label="With correction")
        axis.plot(data["bloch_raw_x"][index], data["bloch_raw_z"][index], "--", color=blue, lw=style["line_width"], label="No correction")
        axis.set_title(rf"$r={scale:g}$")
    axes[1].legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.38), ncol=1)
    fig.subplots_adjust(left=0.025, right=0.99, bottom=0.22, top=0.88, wspace=0.22)
    output = workspace / "outputs/figures/main_fig4b_bloch.png"
    _finish(fig, output, style)
    outputs.append(output)

    fig = _figure(style, "surface_main")
    ax = fig.add_axes([0.12, 0.15, 0.83, 0.78])
    ax.plot(data["r"], data["corrected_z"][2], "--", color=crimson, lw=style["line_width"], label="With correction")
    ax.plot(data["r"], data["raw_z"][2], "--", color=blue, lw=style["line_width"], label="No correction")
    ax.set(xlabel=r"Noise scaling factor $r$", ylabel=r"$\langle Z_L\rangle$", xlim=(1, 10), ylim=(0, 0.52))
    ax.set_xticks([1, 4, 7, 10])
    ax.legend(frameon=False, loc="upper right")
    _paper_axes(ax, style)
    output = workspace / "outputs/figures/main_fig4c_surface.png"
    _finish(fig, output, style)
    outputs.append(output)

    fig = _figure(style, "surface_states")
    axes = fig.subplots(1, 3)
    panels = [
        (data["corrected_z"][0], data["raw_z"][0], r"$|0_L\rangle$", r"$\langle Z_L\rangle$"),
        (data["corrected_x"][1], data["raw_x"][1], r"$|+_L\rangle$", r"$\langle X_L\rangle$"),
        (data["corrected_x"][2], data["raw_x"][2], r"$|\psi_L\rangle$", r"$\langle X_L\rangle$"),
    ]
    for ax, (corrected, raw, state, ylabel) in zip(axes, panels, strict=True):
        ax.plot(data["r"], corrected, "--", color=crimson, lw=style["line_width"], label=f"{state} with correction")
        ax.plot(data["r"], raw, "--", color=style["palette"][7], lw=style["line_width"], label=f"{state} no correction")
        ax.set(xlabel=r"$r$", ylabel=ylabel, xlim=(1, 10), ylim=(0, 1.03))
        ax.set_xticks([1, 4, 7, 10])
        ax.legend(frameon=False, loc="upper right")
        _paper_axes(ax, style)
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.17, top=0.94, wspace=0.34)
    output = workspace / "outputs/figures/supp_fig7ace_surface.png"
    _finish(fig, output, style)
    outputs.append(output)
    return outputs


def render_complete_zne(workspace: Path, style: dict) -> list[Path]:
    data = np.load(workspace / "outputs/data/complete_zne.npz")
    fig = _figure(style, "supp_fig8")
    ax = fig.add_axes(style["axes_positions"]["supp_fig8"])
    colors = style["palette"]
    reference_eta = float(data["reference_overhead"])
    for index, distance in enumerate(data["distances"]):
        color = colors[index]
        sl = slice(None, None, 5)
        ax.plot(data["partial_delta"][index][sl], data["partial_overhead"][index][sl], "^", mfc="none", mec=color, mew=1.0, ms=style["marker_size"], ls="none")
        ax.plot(data["complete_delta"][index][sl], data["complete_overhead"][index][sl], "o", mfc="none", mec=color, mew=1.0, ms=style["marker_size"], ls="none")
        nearest = int(np.argmin(np.abs(data["complete_overhead"][index] - reference_eta)))
        raw_bias = float(data["suppression_at_reference"][index] * data["complete_delta"][index, nearest])
        ax.axvline(raw_bias, color=color, ls="-.", lw=style["line_width"])
        ax.text(raw_bias / 1.2, 1.78, rf"$\times\,{data['suppression_at_reference'][index]:.1f}$", color="#777777", ha="right", va="center", fontsize=7)
    no_color = colors[5]
    sl = slice(None, None, 5)
    ax.plot(data["no_correction_delta"][sl], data["no_correction_overhead"][sl], "o", mfc="none", mec=no_color, mew=1.0, ms=style["marker_size"], ls="none")
    nearest = int(np.argmin(np.abs(data["no_correction_overhead"] - reference_eta)))
    raw_bias = float(data["no_correction_suppression_at_reference"] * data["no_correction_delta"][nearest])
    ax.axvline(raw_bias, color=no_color, ls="-.", lw=style["line_width"])
    ax.text(raw_bias / 1.15, 1.78, rf"$\times\,{float(data['no_correction_suppression_at_reference']):.1f}$", color="#777777", ha="right", va="center", fontsize=7)
    ax.plot([], [], "^", mfc="none", mec="black", ls="none", label="ZNE")
    ax.plot([], [], "o", mfc="none", mec="black", ls="none", label="Complete ZNE")
    ax.set(xscale="log", yscale="log", xlabel=r"$\delta$", ylabel=r"$\eta$", xlim=(1e-6, 1.2e-1), ylim=(0.9, 40))
    ax.legend(frameon=False, loc="upper left", ncol=1, handlelength=1.0, borderpad=0.1, labelspacing=0.25)
    for index, distance in enumerate(data["distances"]):
        ax.text(0.055, 0.73 - 0.065 * index, rf"$d={int(distance)}$", color=colors[index], transform=ax.transAxes)
    ax.text(0.055, 0.40, "No correction", color=no_color, transform=ax.transAxes)
    _paper_axes(ax, style)
    output = workspace / "outputs/figures/supp_fig8_complete_zne.png"
    _finish(fig, output, style)
    return [output]


def render_logical_memory(workspace: Path, style: dict) -> list[Path]:
    data = np.load(workspace / "outputs/data/logical_memory.npz")
    fig = _figure(style, "supp_fig9")
    ax_a = fig.add_axes(style["axes_positions"]["supp_fig9_a"])
    ax_b = fig.add_axes(style["axes_positions"]["supp_fig9_b"])
    colors = ["#4b006e", "#327ba8", "#35b779"]
    markers = ["o", "s", "^"]
    distance_handles = []
    for index, distance in enumerate(data["distances"]):
        line, = ax_a.plot(data["orders"], data["relative_bias"][0, index], marker=markers[index], mfc="none", color=colors[index], lw=style["line_width"], ms=style["marker_size"], label=rf"$d={int(distance)}$")
        distance_handles.append(line)
        ax_a.plot(data["orders"], data["relative_bias"][1, index], "--", marker=markers[index], mfc="none", color=colors[index], lw=style["line_width"], ms=style["marker_size"])
        ax_b.plot(data["orders"], data["overhead"][0, index], marker=markers[index], mfc="none", color=colors[index], lw=style["line_width"], ms=style["marker_size"], label=rf"$d={int(distance)}$")
    solid_handle, = ax_a.plot([], [], color="black", label=r"$N=0.01/P_L(1)$")
    dashed_handle, = ax_a.plot([], [], "--", color="black", label=r"$N=0.001/P_L(1)$")
    ax_a.set(yscale="log", xlabel=r"$K$", ylabel=r"$\delta/\delta_0$", xticks=[1, 2, 3, 4], xlim=(0.9, 4.1), ylim=(4e-3, 0.55))
    ax_b.set(yscale="log", xlabel=r"$K$", ylabel=r"$\eta$", xticks=[1, 2, 3, 4], xlim=(0.9, 4.1), ylim=(6, 3e5))
    style_legend = ax_a.legend(handles=[solid_handle, dashed_handle], frameon=False, loc="upper center", handlelength=1.7, borderpad=0.1, labelspacing=0.25)
    ax_a.add_artist(style_legend)
    ax_a.legend(handles=distance_handles, frameon=False, loc="lower left", borderpad=0.1, labelspacing=0.25)
    ax_b.legend(frameon=False, loc="upper left", borderpad=0.1, labelspacing=0.25)
    ax_a.text(-0.17, 1.02, "a", transform=ax_a.transAxes, fontweight="bold", fontsize=8)
    ax_b.text(-0.17, 1.02, "b", transform=ax_b.transAxes, fontweight="bold", fontsize=8)
    _paper_axes(ax_a, style)
    _paper_axes(ax_b, style)
    output = workspace / "outputs/figures/supp_fig9_logical_memory.png"
    _finish(fig, output, style)
    return [output]


def render_table3(workspace: Path, style: dict) -> list[Path]:
    data = _load_json(workspace / "outputs/data/fixed_total_error.json")
    fig = _figure(style, "supp_table3")
    ax = fig.add_axes(style["axes_positions"]["supp_table3"])
    ax.axis("off")
    rows = [
        [r"Round, $M$", *[str(value) for value in data["rounds"]]],
        [r"Unit error probability, $p$ (%)", *[f"{value:.1f}" for value in data["paper_percentages"]]],
    ]
    table = ax.table(cellText=rows, cellLoc="center", colWidths=[0.56, 0.11, 0.11, 0.11, 0.11], bbox=[0.04, 0.12, 0.92, 0.76])
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    for (row, column), cell in table.get_celld().items():
        cell.set_facecolor("white")
        cell.set_edgecolor("black")
        cell.set_linewidth(0.6)
        cell.visible_edges = "BTR" if column == 0 else "BT"
        cell.get_text().set_fontfamily("STIXGeneral")
    ax.plot([0.04, 0.96], [0.91, 0.91], color="black", lw=0.6, transform=ax.transAxes)
    ax.plot([0.04, 0.96], [0.07, 0.07], color="black", lw=0.6, transform=ax.transAxes)
    output = workspace / "outputs/figures/supp_table3_fixed_error.png"
    _finish(fig, output, style)
    return [output]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--contract", default="RENDER_CONTRACT.json")
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = workspace / contract_path

    contract, freeze, style, verified = _verify_contract(workspace, contract_path)
    _configure(style)
    outputs = []
    outputs += render_feedback(workspace, style)
    outputs += render_repetition(workspace, style)
    outputs += render_surface(workspace, style, contract)
    outputs += render_complete_zne(workspace, style)
    outputs += render_logical_memory(workspace, style)
    outputs += render_table3(workspace, style)

    rendered = []
    for output in outputs:
        with Image.open(output) as image:
            size = list(image.size)
        rendered.append(
            {
                "path": output.relative_to(workspace).as_posix(),
                "sha256": _sha256(output),
                "bytes": output.stat().st_size,
                "pixel_size": size,
            }
        )
    check = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": contract["paper_id"],
        "numeric_freeze": {
            "path": contract["numeric_freeze"]["path"],
            "sha256": contract["numeric_freeze"]["sha256"],
            "run_id": freeze["run_id"],
        },
        "verified_numeric_files": verified,
        "style_config_sha256": _sha256(workspace / contract["style_config"]["path"]),
        "render_contract_sha256": _sha256(contract_path),
        "reference_pixels_read_by_renderer": False,
        "author_data_read_by_renderer": False,
        "physical_parameters_changed": False,
        "numeric_arrays_changed": False,
        "rendered_outputs": rendered,
    }
    check_path = workspace / "outputs/checks/render_contract_check.json"
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(check, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "rendered": len(rendered), "check": str(check_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
