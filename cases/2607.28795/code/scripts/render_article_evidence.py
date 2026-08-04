#!/usr/bin/env python3
"""Render source-blind article evidence figures from frozen qLDPC target data."""

from __future__ import annotations

import csv
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

MPL_CONFIG = Path(os.environ.get("MPLCONFIGDIR", ".matplotlib"))
MPL_CONFIG.mkdir(parents=True, exist_ok=True)
FONT_CACHE_TARGET = MPL_CONFIG / "fontlist-v390.json"
if not FONT_CACHE_TARGET.exists():
    shutil.copyfile(Path("config/fontlist-v390.json"), FONT_CACHE_TARGET)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm
import numpy as np


EXPECTED_TARGETS = ("T001", "T002", "T003", "T004")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def numerical_artifact(contract: dict[str, Any], suffix: str) -> Path:
    matches = [
        Path(row["path"])
        for row in contract["numerical_artifacts"]
        if str(row["path"]).endswith(suffix)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one frozen artifact ending in {suffix}, found {matches}")
    return matches[0]


def configure_matplotlib(style: dict[str, Any]) -> None:
    typography = style["typography"]
    plt.rcParams.update(
        {
            "font.family": typography["font_family"],
            "font.size": typography["font_size"],
            "axes.labelsize": typography.get("axis_label_size", typography["font_size"]),
            "xtick.labelsize": typography.get("tick_label_size", typography["font_size"]),
            "ytick.labelsize": typography.get("tick_label_size", typography["font_size"]),
            "legend.fontsize": typography.get("legend_font_size", typography["font_size"]),
            "axes.spines.right": False,
            "axes.spines.top": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def new_figure(style: dict[str, Any]) -> plt.Figure:
    configure_matplotlib(style)
    canvas = style["canvas"]
    return plt.figure(
        figsize=(canvas["width_inches"], canvas["height_inches"]),
        dpi=canvas["dpi"],
        facecolor=canvas["facecolor"],
    )


def save_figure(figure: plt.Figure, contract: dict[str, Any], target_id: str) -> None:
    outputs = contract["rendered_outputs"][target_id]
    if len(outputs) != 1:
        raise ValueError(f"{target_id} renderer expects exactly one output")
    output = Path(outputs[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = contract["render_parameters"][target_id]["canvas"]
    figure.savefig(output, dpi=canvas["dpi"], facecolor=canvas["facecolor"])
    plt.close(figure)


def render_t001(contract: dict[str, Any]) -> None:
    target_id = "T001"
    style = contract["render_parameters"][target_id]
    payload = read_json(numerical_artifact(contract, "T001_code_parameters.json"))
    codes = payload["codes"]
    columns: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        ("CSS", lambda row: bool(row["invariants"]["css_commutation"])),
        (
            "full ranks",
            lambda row: bool(row["invariants"]["full_hx_rank"])
            and bool(row["invariants"]["full_hz_rank"]),
        ),
        ("k=|G|", lambda row: bool(row["invariants"]["dimension_equals_group_order"])),
        ("rate=1/5", lambda row: bool(row["invariants"]["rate_is_one_fifth"])),
        ("weight=9", lambda row: bool(row["invariants"]["row_check_weight_is_nine"])),
        ("left pivot", lambda row: bool(row["invariants"]["left_a1_invertible"])),
        ("right pivot", lambda row: bool(row["invariants"]["right_b1_invertible"])),
        (
            "logical basis",
            lambda row: row["canonical_basis"]["status"] == "constructed",
        ),
    ]
    matrix = np.asarray(
        [[int(check(row)) for _, check in columns] for row in codes],
        dtype=float,
    )
    palette = style["palette"]
    figure = new_figure(style)
    audit_axes = figure.add_axes(style["axes_positions"]["audit"])
    weights_axes = figure.add_axes(style["axes_positions"]["weights"])
    audit_axes.imshow(
        matrix,
        aspect="auto",
        vmin=0,
        vmax=1,
        cmap=ListedColormap([palette["fail"], palette["pass"]]),
        interpolation=style["interpolation"].get("matrix", "nearest"),
    )
    audit_axes.set_xticks(np.arange(len(columns)), [label for label, _ in columns])
    audit_axes.tick_params(axis="x", rotation=35)
    audit_axes.set_yticks(
        np.arange(len(codes)),
        [f"n={int(row['n'])}" for row in codes],
    )
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            audit_axes.text(
                column_index,
                row_index,
                "✓" if matrix[row_index, column_index] else "×",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
            )
    audit_axes.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    audit_axes.set_yticks(np.arange(-0.5, len(codes), 1), minor=True)
    grid_style = style["line_styles"]["grid"]
    audit_axes.grid(
        which="minor",
        color=palette["grid"],
        linewidth=grid_style["line_width"],
        alpha=grid_style["alpha"],
    )
    audit_axes.tick_params(which="minor", bottom=False, left=False)
    audit_axes.set_title("a  Structural invariants", loc="left", fontweight="bold")

    positions = np.arange(len(codes), dtype=float)
    width = 0.34
    x_weights = np.asarray(
        [np.nan if row["canonical_x_weight"] is None else row["canonical_x_weight"] for row in codes],
        dtype=float,
    )
    z_weights = np.asarray(
        [np.nan if row["canonical_z_weight"] is None else row["canonical_z_weight"] for row in codes],
        dtype=float,
    )
    bar_style = style["line_styles"]["bars"]
    weights_axes.barh(
        positions - width / 2,
        x_weights,
        height=width,
        color=palette["x_logical"],
        edgecolor=palette["axis"],
        linewidth=bar_style["line_width"],
        label="canonical X",
    )
    weights_axes.barh(
        positions + width / 2,
        z_weights,
        height=width,
        color=palette["z_logical"],
        edgecolor=palette["axis"],
        linewidth=bar_style["line_width"],
        label="canonical Z",
    )
    weights_axes.set_yticks(positions, [f"n={int(row['n'])}" for row in codes])
    weights_axes.invert_yaxis()
    weights_axes.set_xlabel("Logical-operator weight")
    weights_axes.grid(
        axis="x",
        linestyle=grid_style["line_style"],
        linewidth=grid_style["line_width"],
        alpha=grid_style["alpha"],
    )
    blocked_index = next(
        index for index, row in enumerate(codes) if row["canonical_basis"]["status"] != "constructed"
    )
    weights_axes.text(
        0,
        blocked_index,
        "  blocked: singular pivots",
        ha="left",
        va="center",
        color=palette["fail"],
        fontweight="bold",
    )
    weights_axes.text(
        x_weights[0] + 1.5,
        positions[0] - width / 2,
        "X",
        ha="left",
        va="center",
        color=palette["axis"],
        fontweight="bold",
    )
    weights_axes.text(
        z_weights[0] + 1.5,
        positions[0] + width / 2,
        "Z",
        ha="left",
        va="center",
        color=palette["axis"],
        fontweight="bold",
    )
    weights_axes.set_title("b  Canonical logical weights", loc="left", fontweight="bold")
    figure.suptitle(
        "Independent mitten-code algebra audit",
        x=0.52,
        y=0.98,
        fontweight="bold",
    )
    save_figure(figure, contract, target_id)


def render_t002(contract: dict[str, Any]) -> None:
    target_id = "T002"
    style = contract["render_parameters"][target_id]
    rows = read_csv(numerical_artifact(contract, "T002_magic_counts.csv"))
    codes = sorted({row["code_id"] for row in rows}, key=lambda value: int(value.rsplit("-", 1)[1]))
    distances = sorted({int(row["d_rep"]) for row in rows})
    values = {
        (row["code_id"], int(row["d_rep"])): int(row["qubits"])
        for row in rows
    }
    matrix = np.asarray(
        [[values[(code, distance)] for distance in distances] for code in codes],
        dtype=float,
    )
    palette = style["palette"]
    figure = new_figure(style)
    axes = figure.add_axes(style["axes_positions"]["main"])
    colorbar_axes = figure.add_axes(style["axes_positions"]["colorbar"])
    color_map = LinearSegmentedColormap.from_list(
        "resource_scale",
        [palette["low"], palette["high"]],
    )
    image = axes.imshow(
        matrix,
        aspect="auto",
        cmap=color_map,
        norm=LogNorm(vmin=float(matrix.min()), vmax=float(matrix.max())),
        interpolation=style["interpolation"].get("matrix", "nearest"),
    )
    axes.set_xticks(np.arange(len(distances)), [f"d={distance}" for distance in distances])
    axes.set_yticks(np.arange(len(codes)), [f"n={code.rsplit('-', 1)[1]}" for code in codes])
    axes.set_xlabel("Repetition distance")
    axes.set_ylabel("Mitten code")
    threshold = float(np.sqrt(matrix.min() * matrix.max()))
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = int(matrix[row_index, column_index])
            axes.text(
                column_index,
                row_index,
                f"{value:,}",
                ha="center",
                va="center",
                color=palette["dark_text"] if value < threshold else palette["light_text"],
                fontsize=style["typography"].get("tick_label_size", 7),
            )
    axes.set_title(
        "Eq. E15 resource landscape — all 32 Table V entries reproduced",
        loc="left",
        fontweight="bold",
    )
    colorbar = figure.colorbar(image, cax=colorbar_axes)
    colorbar.set_label("Physical qubits (log scale)")
    save_figure(figure, contract, target_id)


def render_t003(contract: dict[str, Any]) -> None:
    target_id = "T003"
    style = contract["render_parameters"][target_id]
    rows = read_csv(numerical_artifact(contract, "T003_sqetch_benchmark.csv"))
    codes = sorted({row["code_id"] for row in rows}, key=lambda code: int(code.rsplit("-", 1)[1]))
    methods = ["sqetch", "full_nullspace_rref"]
    values = {
        (row["code_id"], row["method"]): float(row["projected_seconds"]) / 86400.0
        for row in rows
    }
    palette = style["palette"]
    line_styles = style["line_styles"]
    figure = new_figure(style)
    axes = figure.add_axes(style["axes_positions"]["main"])
    positions = np.arange(len(codes), dtype=float)
    width = 0.34
    bar_style = line_styles["bars"]
    grid_style = line_styles["grid"]
    for index, method in enumerate(methods):
        offset = (index - 0.5) * width
        axes.bar(
            positions + offset,
            [values[(code, method)] for code in codes],
            width=width,
            color=palette[method],
            edgecolor=palette["axis"],
            linewidth=bar_style["line_width"],
            alpha=bar_style["alpha"],
            label="sQetch" if method == "sqetch" else "full-nullspace RREF",
        )
    axes.set_yscale("log")
    axes.set_xticks(positions, [f"n={code.rsplit('-', 1)[1]}" for code in codes])
    axes.set_ylabel("Projected wall time for $10^5$ trials (days)")
    axes.set_xlabel("Independently reconstructed mitten code")
    axes.grid(
        axis="y",
        which="both",
        alpha=grid_style["alpha"],
        linewidth=grid_style["line_width"],
        linestyle=grid_style["line_style"],
    )
    axes.legend(frameon=False)
    axes.set_title("Reduced-scale Algorithm 1 benchmark")
    save_figure(figure, contract, target_id)


def render_t004(contract: dict[str, Any]) -> None:
    target_id = "T004"
    style = contract["render_parameters"][target_id]
    rows = read_csv(numerical_artifact(contract, "T004_realtime.csv"))
    experiments = list(dict.fromkeys(row["experiment_id"] for row in rows))
    stages = ["S1", "S2", "S3A", "S3B", "S3C", "S4_mean", "S4_worst"]
    short_names = {
        "mitten-200-memory": "n=200 memory",
        "mitten-300-memory": "n=300 memory",
        "mitten-540-xx-surgery": "n=540 XX surgery",
    }
    palette_roles = {
        "mitten-200-memory": "memory_200",
        "mitten-300-memory": "memory_300",
        "mitten-540-xx-surgery": "surgery_540",
    }
    row_map = {(row["experiment_id"], row["stage"]): row for row in rows}
    palette = style["palette"]
    line_styles = style["line_styles"]
    figure = new_figure(style)
    utilization_axes = figure.add_axes(style["axes_positions"]["utilization"])
    latency_axes = figure.add_axes(style["axes_positions"]["latency"])
    positions = np.arange(len(stages), dtype=float)
    offsets = np.linspace(-0.2, 0.2, len(experiments))
    for offset, experiment in zip(offsets, experiments, strict=True):
        role = palette_roles[experiment]
        series_style = line_styles[role]
        utilization_axes.plot(
            positions + offset,
            [float(row_map[(experiment, stage)]["utilization"]) for stage in stages],
            linestyle=series_style["line_style"],
            linewidth=series_style["line_width"],
            marker=series_style["marker"],
            markersize=series_style["marker_size"],
            color=palette[role],
            label=short_names[experiment],
        )
    threshold_style = line_styles["cycle_threshold"]
    utilization_axes.axhline(
        1.0,
        color=palette["cycle_threshold"],
        linestyle=threshold_style["line_style"],
        linewidth=threshold_style["line_width"],
        label="real-time limit",
    )
    utilization_axes.set_yscale("log")
    utilization_axes.set_xticks(positions, stages, rotation=35)
    utilization_axes.set_ylabel("Stage utilization $\\rho_i$")
    utilization_axes.set_xlabel("Decoder stage")
    utilization_axes.grid(
        axis="y",
        which="both",
        alpha=line_styles["grid"]["alpha"],
        linewidth=line_styles["grid"]["line_width"],
        linestyle=line_styles["grid"]["line_style"],
    )
    utilization_axes.legend(frameon=False, loc="lower left")
    utilization_axes.set_title("a  Every stage remains below $\\rho_i=1$", loc="left", fontweight="bold")

    mean_latency_ms = [
        float(row_map[(experiment, "S1")]["mean_latency_seconds"]) * 1000.0
        for experiment in experiments
    ]
    bars = latency_axes.bar(
        np.arange(len(experiments)),
        mean_latency_ms,
        color=[palette[palette_roles[experiment]] for experiment in experiments],
        edgecolor=palette["axis"],
        linewidth=line_styles["bars"]["line_width"],
    )
    latency_axes.axhline(
        1.0,
        color=palette["cycle_threshold"],
        linestyle=threshold_style["line_style"],
        linewidth=threshold_style["line_width"],
    )
    latency_axes.set_xticks(
        np.arange(len(experiments)),
        ["n=200\nmemory", "n=300\nmemory", "n=540\nXX surgery"],
    )
    latency_axes.set_ylabel("Mean reaction latency (ms)")
    latency_axes.set_title("b  Mean latency", loc="left", fontweight="bold")
    latency_axes.grid(
        axis="y",
        alpha=line_styles["grid"]["alpha"],
        linewidth=line_styles["grid"]["line_width"],
        linestyle=line_styles["grid"]["line_style"],
    )
    for bar, value in zip(bars, mean_latency_ms, strict=True):
        latency_axes.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
        )
    figure.suptitle(
        "Eq. I1 real-time decoder arithmetic",
        x=0.52,
        y=0.98,
        fontweight="bold",
    )
    save_figure(figure, contract, target_id)


def main() -> None:
    contract = read_json(Path("render_contract.json"))
    target_ids = tuple(contract["target_ids"])
    if target_ids != EXPECTED_TARGETS:
        raise ValueError(f"unexpected render target order: {target_ids}")
    renderers = {
        "T001": render_t001,
        "T002": render_t002,
        "T003": render_t003,
        "T004": render_t004,
    }
    for target_id in target_ids:
        renderers[target_id](contract)


if __name__ == "__main__":
    main()
