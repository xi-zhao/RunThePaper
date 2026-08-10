"""Presentation-only renderer over the attested, hash-frozen resource arrays."""

from __future__ import annotations

import csv
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import LogLocator, NullFormatter
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ALLOWED_ADJUSTMENTS = {
    "axes_position",
    "canvas",
    "font",
    "legend",
    "line_style",
    "palette",
    "ticks",
}
MOLECULES = ["propane", "carbon dioxide", "ethane"]
DISPLAY = {
    "propane": ("propane", 46, "426.61", "6.58466", "241582"),
    "carbon dioxide": ("carbon dioxide", 54, "608.414", "10.3658", "113959"),
    "ethane": ("ethane", 60, "768.138", "4.07041", "467403"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _axes(
    figure: plt.Figure, box: tuple[int, int, int, int], canvas: tuple[int, int]
) -> plt.Axes:
    left, top, right, bottom = box
    width, height = canvas
    return figure.add_axes(
        [
            left / width,
            (height - bottom) / height,
            (right - left) / width,
            (bottom - top) / height,
        ]
    )


def _style_axis(axis: plt.Axes) -> None:
    for spine in axis.spines.values():
        spine.set_color("#666666")
        spine.set_linewidth(1.2)
    axis.tick_params(
        which="major", direction="in", length=5.0, width=1.1, colors="#444444"
    )
    axis.tick_params(
        which="minor", direction="in", length=2.8, width=0.9, colors="#666666"
    )
    axis.grid(False)


def _panel_frame(figure: plt.Figure, bounds: tuple[float, float, float, float]) -> None:
    figure.add_artist(
        FancyBboxPatch(
            (bounds[0], bounds[1]),
            bounds[2],
            bounds[3],
            boxstyle="round,pad=0.006,rounding_size=0.018",
            transform=figure.transFigure,
            fill=False,
            edgecolor="#777777",
            linewidth=1.1,
            zorder=0,
        )
    )


def _title(
    figure: plt.Figure,
    molecule: str,
    x_center: float,
    y_title: float,
    y_parameters: float,
) -> None:
    name, qubits, lambda_one, lambda_max, terms = DISPLAY[molecule]
    figure.text(
        x_center,
        y_title,
        f"{name}  - {qubits} qubits",
        ha="center",
        va="center",
        fontsize=15.5,
        weight="semibold",
    )
    figure.text(
        x_center,
        y_parameters,
        rf"$\lambda$={lambda_one}    $\Lambda$={lambda_max}    $L$={terms}",
        ha="center",
        va="center",
        fontsize=13.2,
    )


def _save(
    figure: plt.Figure, workspace: Path, target: dict[str, Any]
) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    for kind in ("png", "svg", "pdf"):
        path = workspace / target[f"output_{kind}"]
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=target["dpi"], facecolor="white", edgecolor="none")
        if kind == "svg":
            svg = path.read_text(encoding="utf-8")
            path.write_text(
                "\n".join(line.rstrip() for line in svg.splitlines()) + "\n",
                encoding="utf-8",
            )
        outputs[kind] = {"path": target[f"output_{kind}"], "sha256": _sha256(path)}
    plt.close(figure)
    outputs["canvas_pixels"] = target["canvas_pixels"]
    return outputs


def _render_fig2(
    workspace: Path, target: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    canvas = tuple(target["canvas_pixels"])
    figure = plt.figure(
        figsize=(canvas[0] / target["dpi"], canvas[1] / target["dpi"]),
        dpi=target["dpi"],
        facecolor="white",
    )
    boxes = [(148, 100, 558, 399), (786, 100, 1195, 399), (1448, 100, 1858, 399)]
    centers = [353 / canvas[0], 990.5 / canvas[0], 1653 / canvas[0]]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(data_path):
        grouped[row["molecule"]].append(row)
    styles = [
        ("qdrift", "#111111", "-", 1.7),
        ("first_order_deterministic", "#1736d8", (0, (4, 3)), 1.45),
        ("first_order_random", "#1736d8", "-", 1.45),
        ("higher_order_deterministic", "#df2b22", (0, (4, 3)), 1.45),
        ("higher_order_random", "#df2b22", "-", 1.45),
    ]
    for index, molecule in enumerate(MOLECULES):
        _panel_frame(
            figure, ((boxes[index][0] - 120) / canvas[0], 0.04, 535 / canvas[0], 0.92)
        )
        _title(figure, molecule, centers[index], 0.955, 0.895)
        axis = _axes(figure, boxes[index], canvas)
        rows = sorted(grouped[molecule], key=lambda row: float(row["time"]))
        time = np.asarray([float(row["time"]) for row in rows])
        for field, color, linestyle, linewidth in styles:
            values = np.log10(np.asarray([float(row[field]) for row in rows]))
            axis.plot(
                time,
                values,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                clip_on=True,
            )
        axis.axvline(6000.0, color="#d0d0d0", linewidth=1.2, zorder=0)
        axis.text(
            6000.0,
            30.35,
            r"$t=6000$",
            ha="left",
            va="bottom",
            fontsize=9.5,
            color="#444444",
        )
        axis.set_xscale("log")
        axis.set_xlim(1.0e2, 1.0e8)
        axis.set_ylim(10.0, 30.0)
        axis.set_yticks([10, 15, 20, 25, 30])
        axis.xaxis.set_major_locator(LogLocator(base=10, numticks=4))
        axis.xaxis.set_minor_locator(
            LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=60)
        )
        axis.xaxis.set_minor_formatter(NullFormatter())
        axis.tick_params(labelsize=10.2, pad=1.5)
        axis.set_xlabel(r"Time (s/Hr)", fontsize=11.5, labelpad=3)
        axis.set_ylabel(r"Log gate count  $\log_{10}(N)$", fontsize=10.5, labelpad=3)
        _style_axis(axis)
    legend_axis = figure.add_axes([0.795, 0.13, 0.19, 0.73])
    legend_axis.axis("off")
    handles = [
        Line2D([], [], color="#111111", lw=2.0),
        Line2D([], [], color="#1736d8", lw=1.8, ls=(0, (4, 3))),
        Line2D([], [], color="#1736d8", lw=1.8),
        Line2D([], [], color="#df2b22", lw=1.8, ls=(0, (4, 3))),
        Line2D([], [], color="#df2b22", lw=1.8),
    ]
    legend_axis.legend(
        handles,
        [
            "qDRIFT",
            "1st-order deterministic",
            "1st-order random",
            "higher-order deterministic",
            "higher-order random",
        ],
        loc="center",
        frameon=True,
        fancybox=True,
        edgecolor="#777777",
        fontsize=11,
        handlelength=3.0,
        borderpad=0.8,
    )
    return _save(figure, workspace, target)


def _render_fig4(
    workspace: Path, target: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    canvas = tuple(target["canvas_pixels"])
    figure = plt.figure(
        figsize=(canvas[0] / target["dpi"], canvas[1] / target["dpi"]),
        dpi=target["dpi"],
        facecolor="white",
    )
    boxes = [(175, 112, 600, 433), (852, 112, 1279, 433), (1528, 112, 1952, 433)]
    centers = [387.5 / canvas[0], 1065.5 / canvas[0], 1740 / canvas[0]]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(data_path):
        grouped[row["molecule"]].append(row)
    for index, molecule in enumerate(MOLECULES):
        _panel_frame(
            figure, ((boxes[index][0] - 145) / canvas[0], 0.035, 575 / canvas[0], 0.92)
        )
        _title(figure, molecule, centers[index], 0.955, 0.89)
        axis = _axes(figure, boxes[index], canvas)
        rows = sorted(
            grouped[molecule],
            key=lambda row: float(row["failure_probability"]),
            reverse=True,
        )
        failure = np.asarray([float(row["failure_probability"]) for row in rows])
        qdrift = np.log10(np.asarray([float(row["qdrift"]) for row in rows]))
        trotter = np.log10(
            np.asarray([float(row["random_trotter_second_order"]) for row in rows])
        )
        axis.plot(failure, qdrift, color="#111111", linewidth=2.0)
        axis.plot(failure, trotter, color="#e49a19", linewidth=2.0)
        axis.set_xscale("log")
        axis.set_xlim(1.0e-1, 1.0e-5)
        axis.set_ylim(18.0, 30.0)
        axis.set_yticks([18, 22, 26, 30])
        axis.xaxis.set_major_locator(LogLocator(base=10, numticks=5))
        axis.xaxis.set_minor_locator(
            LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=60)
        )
        axis.xaxis.set_minor_formatter(NullFormatter())
        axis.tick_params(labelsize=10.5, pad=1.5)
        axis.set_xlabel("Failure probability", fontsize=11.7, labelpad=3)
        axis.set_ylabel(r"Log gate count  $\log_{10}(G)$", fontsize=10.5, labelpad=3)
        _style_axis(axis)
    legend_axis = figure.add_axes([0.78, 0.22, 0.20, 0.62])
    legend_axis.axis("off")
    legend_axis.legend(
        [
            Line2D([], [], color="#111111", lw=2.2),
            Line2D([], [], color="#e49a19", lw=2.2),
        ],
        ["qDRIFT", "Random Trotter\n2nd order"],
        loc="center",
        frameon=True,
        fancybox=True,
        edgecolor="#777777",
        fontsize=12,
        handlelength=3.2,
        borderpad=1.0,
        labelspacing=1.2,
    )
    return _save(figure, workspace, target)


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as left, Image.open(generated).convert(
        "RGB"
    ) as right:
        right = right.resize(left.size, Image.Resampling.LANCZOS)
        header = 42
        canvas = Image.new("RGB", (left.width * 2, left.height + header), "white")
        canvas.paste(left, (0, header))
        canvas.paste(right, (left.width, header))
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        draw.text((12, 14), "PAPER SOURCE (comparison only)", fill="black", font=font)
        draw.text(
            (left.width + 12, 14), "INDEPENDENT FORMULA RENDER", fill="black", font=font
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output)


def render(contract_path: Path) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if set(contract["allowed_adjustments"]) != ALLOWED_ADJUSTMENTS:
        raise ValueError("RenderContract contains an unapproved adjustment")
    workspace = contract_path.parents[1]
    frozen: dict[str, Path] = {}
    for item in contract["frozen_data"]:
        path = workspace / item["path"]
        if _sha256(path) != item["sha256"]:
            raise RuntimeError(f"frozen data hash changed: {item['path']}")
        frozen[path.name] = path
    references: dict[str, Path] = {}
    for item in contract["source_references"]:
        path = workspace / item["path"]
        if _sha256(path) != item["sha256"]:
            raise RuntimeError(f"source reference hash changed: {item['path']}")
        references[item["target_id"]] = path
    targets = {item["target_id"]: item for item in contract["figures"]}
    outputs = {
        "T001": _render_fig2(
            workspace, targets["T001"], frozen["fig2_gate_counts.csv"]
        ),
        "T002": _render_fig4(
            workspace, targets["T002"], frozen["fig4_phase_estimation_counts.csv"]
        ),
    }
    for target_id, target in targets.items():
        _comparison_board(
            references[target_id],
            workspace / target["output_png"],
            workspace / target["comparison"],
        )
    result = {
        "schema_version": 1,
        "paper_id": contract["paper_id"],
        "status": "passed",
        "channel": "presentation_only_after_frozen_numerics",
        "figure_contract": contract["figure_contract"],
        "frozen_data": contract["frozen_data"],
        "source_references": contract["source_references"],
        "allowed_adjustments": sorted(ALLOWED_ADJUSTMENTS),
        "locked_fields": contract["locked_fields"],
        "outputs": outputs,
        "scientific_regions": contract["scientific_regions"],
    }
    output = workspace / contract["check_output"]
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result
