"""Presentation-only rendering over hash-frozen Figure 2 and Figure 3 data."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, LogLocator, MultipleLocator, NullFormatter
from PIL import Image, ImageDraw, ImageFont


ALLOWED_ADJUSTMENTS = {
    "canvas",
    "axes_position",
    "font",
    "line_style",
    "palette",
    "ticks",
    "legend",
    "interpolation",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as left, Image.open(generated).convert("RGB") as right:
        if left.size != right.size:
            raise ValueError(f"comparison canvases differ: {left.size} != {right.size}")
        title_height = 92
        canvas = Image.new("RGB", (2 * left.width, left.height + title_height), "white")
        canvas.paste(left, (0, title_height))
        canvas.paste(right, (left.width, title_height))
        draw = ImageDraw.Draw(canvas)
        font = _font(34)
        for index, label in enumerate(
            ["Original paper — comparison only", "Independent formula-derived result"]
        ):
            bounds = draw.textbbox((0, 0), label, font=font)
            center = index * left.width + left.width // 2
            draw.text(
                (center - (bounds[2] - bounds[0]) // 2, 24),
                label,
                fill="black",
                font=font,
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, optimize=True)


def _set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 1.15,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def _figure(target: dict[str, Any]) -> tuple[plt.Figure, plt.Axes]:
    width, height = target["canvas_pixels"]
    dpi = int(target["dpi"])
    # The tiny sub-pixel guard prevents binary floating-point truncation from
    # turning an odd declared width (2879 px) into 2878 px at save time.
    render_dpi = dpi + 0.001
    figure = plt.figure(
        figsize=(width / dpi, height / dpi),
        dpi=render_dpi,
        facecolor="white",
    )
    axis = figure.add_axes(target["axes_position"])
    return figure, axis


def _save(figure: plt.Figure, workspace: Path, target: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "png": workspace / target["output_png"],
        "svg": workspace / target["output_svg"],
        "pdf": workspace / target["output_pdf"],
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(paths["png"], dpi=float(target["dpi"]) + 0.001)
    figure.savefig(paths["svg"], format="svg")
    figure.savefig(paths["pdf"], format="pdf")
    plt.close(figure)
    with Image.open(paths["png"]) as image:
        canvas = list(image.size)
    if canvas != target["canvas_pixels"]:
        raise RuntimeError(f"rendered canvas {canvas} != declared {target['canvas_pixels']}")
    return {
        "png": {"path": target["output_png"], "sha256": sha256_file(paths["png"])},
        "svg": {"path": target["output_svg"], "sha256": sha256_file(paths["svg"])},
        "pdf": {"path": target["output_pdf"], "sha256": sha256_file(paths["pdf"])},
        "canvas_pixels": canvas,
    }


def _plain_decimal(value: float, _position: int) -> str:
    if abs(value - round(value)) < 1.0e-10:
        return str(int(round(value)))
    return f"{value:g}"


def _render_fig2(workspace: Path, target: dict[str, Any], data_path: Path) -> dict[str, Any]:
    rows = _rows(data_path)
    if len(rows) != 11:
        raise ValueError(f"Figure 2 requires 11 charge sectors, got {len(rows)}")
    particle = np.asarray([float(row["particle_number"]) for row in rows])
    p_num = np.asarray([float(row["probability_numeric"]) for row in rows])
    s_num = np.asarray([float(row["entropy_numeric"]) for row in rows])
    p_cft = np.asarray([float(row["probability_analytic"]) for row in rows])
    s_cft = np.asarray([float(row["entropy_analytic"]) for row in rows])

    figure, axis = _figure(target)
    axis.plot(particle, p_cft, color="black", linewidth=1.15, zorder=2)
    axis.plot(particle, s_cft, color="#ff0000", linewidth=1.15, zorder=2)
    axis.plot(
        particle,
        p_num,
        linestyle="none",
        marker="o",
        markersize=7.2,
        markerfacecolor="none",
        markeredgecolor="black",
        markeredgewidth=1.1,
        zorder=3,
    )
    axis.plot(
        particle,
        s_num,
        linestyle="none",
        marker="s",
        markersize=6.8,
        markerfacecolor="none",
        markeredgecolor="#ff0000",
        markeredgewidth=1.1,
        zorder=3,
    )
    axis.set_xlim(4995, 5005)
    axis.set_ylim(0.0, 1.4)
    axis.xaxis.set_major_locator(MultipleLocator(2))
    axis.xaxis.set_minor_locator(MultipleLocator(1))
    axis.yaxis.set_major_locator(MultipleLocator(0.2))
    axis.yaxis.set_minor_locator(MultipleLocator(0.1))
    axis.yaxis.set_major_formatter(FuncFormatter(_plain_decimal))
    axis.tick_params(
        which="major", direction="in", top=True, right=True, length=11, width=1.15, labelsize=25, pad=8
    )
    axis.tick_params(which="minor", direction="in", top=True, right=True, length=6.5, width=1.05)
    axis.set_xlabel(r"$N_A$", fontsize=36, labelpad=10)
    handles = [
        Line2D([], [], color="black", marker="o", markerfacecolor="none", markersize=7.2, linewidth=1.15),
        Line2D([], [], color="#ff0000", marker="s", markerfacecolor="none", markersize=6.8, linewidth=1.15),
    ]
    legend = axis.legend(
        handles,
        [r"$P(N_A)$", r"$\mathcal{S}(N_A)$"],
        loc="upper right",
        bbox_to_anchor=(0.925, 0.93),
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        edgecolor="black",
        facecolor="white",
        fontsize=27,
        handlelength=1.9,
        borderpad=0.35,
        labelspacing=0.4,
    )
    legend.get_frame().set_linewidth(1.0)
    return _save(figure, workspace, target)


def _render_fig3(
    workspace: Path,
    target: dict[str, Any],
    numeric_path: Path,
    analytic_path: Path,
) -> dict[str, Any]:
    numeric: dict[str, list[tuple[float, float]]] = defaultdict(list)
    analytic: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for row in _rows(numeric_path):
        numeric[row["sector"]].append((float(row["x"]), float(row["integrated_count"])))
    for row in _rows(analytic_path):
        analytic[row["sector"]].append((float(row["x"]), float(row["integrated_count"])))

    labels = ["all", "0", "1", "2", "3", "4", "5"]
    colors = {
        "all": "black",
        "0": "#ff0000",
        "1": "#008000",
        "2": "#0000ee",
        "3": "#c49a96",
        "4": "#9400d3",
        "5": "#ffa000",
    }
    figure, axis = _figure(target)
    for label in labels:
        points = np.asarray(numeric[label], dtype=np.float64)
        axis.plot(
            points[:, 0],
            points[:, 1],
            color=colors[label],
            linewidth=0.92,
            marker="o",
            markersize=1.55,
            solid_capstyle="round",
            zorder=3,
        )
    handles: list[Line2D] = []
    for label in labels:
        points = np.asarray(analytic[label], dtype=np.float64)
        keep = np.isfinite(points[:, 1]) & (points[:, 1] >= 0.9) & (points[:, 1] <= 1100.0)
        axis.plot(points[keep, 0], points[keep, 1], color=colors[label], linewidth=1.18, zorder=4)
        handles.append(Line2D([], [], color=colors[label], linewidth=1.18))

    axis.set_xlim(0.0, 10.0)
    axis.set_yscale("log")
    axis.set_ylim(0.9, 1100.0)
    axis.xaxis.set_major_locator(MultipleLocator(2))
    axis.xaxis.set_minor_locator(MultipleLocator(1))
    axis.yaxis.set_major_locator(LogLocator(base=10, numticks=4))
    axis.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=40))
    axis.yaxis.set_minor_formatter(NullFormatter())
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _position: f"{value:g}"))
    axis.tick_params(
        which="major", direction="in", top=True, right=True, length=11, width=1.15, labelsize=25, pad=8
    )
    axis.tick_params(which="minor", direction="in", top=True, right=True, length=6.5, width=1.05)
    axis.set_xlabel(
        r"$2[-\ln(\lambda_{\max})\ln(\lambda_{\max}/\lambda)]^{1/2}$",
        fontsize=32,
        labelpad=12,
    )
    axis.set_ylabel(r"$n(\lambda,N_A)$", fontsize=36, labelpad=11)
    legend_labels = [r"All $N_A$"] + [rf"$\Delta N_A={charge}$" for charge in range(6)]
    legend = axis.legend(
        handles,
        legend_labels,
        loc="upper left",
        bbox_to_anchor=(0.045, 0.945),
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        edgecolor="black",
        facecolor="white",
        fontsize=23,
        handlelength=2.1,
        borderpad=0.3,
        labelspacing=0.25,
    )
    legend.get_frame().set_linewidth(1.0)
    return _save(figure, workspace, target)


def render(contract_path: Path) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if set(contract["allowed_adjustments"]) != ALLOWED_ADJUSTMENTS:
        raise ValueError("RenderContract contains an unapproved adjustment")
    workspace = contract_path.parents[1]

    frozen: dict[str, Path] = {}
    for item in contract["frozen_data"]:
        path = workspace / item["path"]
        if sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"frozen data hash changed: {item['path']}")
        frozen[Path(item["path"]).name] = path
    references: dict[str, Path] = {}
    for item in contract["source_references"]:
        path = workspace / item["path"]
        if sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"source reference hash changed: {item['path']}")
        references[item["target_id"]] = path

    _set_style()
    target_by_id = {item["target_id"]: item for item in contract["figures"]}
    outputs = {
        "T001": _render_fig2(
            workspace,
            target_by_id["T001"],
            frozen["fig2_charge_resolved.csv"],
        ),
        "T002": _render_fig3(
            workspace,
            target_by_id["T002"],
            frozen["fig3_spectrum_numeric.csv"],
            frozen["fig3_spectrum_analytic.csv"],
        ),
    }
    for target_id, target in target_by_id.items():
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
    check_path = workspace / contract["check_output"]
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result
