"""Presentation-only rendering over hash-frozen Vidal reproduction data."""

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
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import FuncFormatter, MultipleLocator
from PIL import Image, ImageDraw, ImageFont

ALLOWED_ADJUSTMENTS = {
    "canvas",
    "axes_position",
    "font",
    "line_style",
    "palette",
    "ticks",
    "camera",
    "interpolation",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _font(size: int) -> ImageFont.ImageFont:
    for path in [
        Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ]:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as left, Image.open(generated).convert(
        "RGB"
    ) as right:
        if left.size != right.size:
            raise ValueError(f"comparison canvases differ: {left.size} != {right.size}")
        title_height = max(60, left.height // 18)
        canvas = Image.new("RGB", (2 * left.width, left.height + title_height), "white")
        canvas.paste(left, (0, title_height))
        canvas.paste(right, (left.width, title_height))
        draw = ImageDraw.Draw(canvas)
        font = _font(max(22, left.width // 45))
        for index, label in enumerate(
            ["Original paper — comparison only", "Independent formula-derived result"]
        ):
            box = draw.textbbox((0, 0), label, font=font)
            center = index * left.width + left.width // 2
            draw.text(
                (center - (box[2] - box[0]) // 2, title_height // 4),
                label,
                fill="black",
                font=font,
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, optimize=True)


def _style() -> None:
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


def _new_figure(spec: dict[str, Any]) -> plt.Figure:
    width, height = spec["canvas_pixels"]
    dpi = float(spec["dpi"])
    return plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")


def _save(figure: plt.Figure, workspace: Path, spec: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "png": workspace / spec["output_png"],
        "svg": workspace / spec["output_svg"],
        "pdf": workspace / spec["output_pdf"],
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(paths["png"], dpi=spec["dpi"])
    figure.savefig(paths["svg"], format="svg")
    figure.savefig(paths["pdf"], format="pdf")
    plt.close(figure)
    svg = paths["svg"].read_text(encoding="utf-8")
    paths["svg"].write_text(
        "\n".join(line.rstrip() for line in svg.splitlines()) + "\n",
        encoding="utf-8",
    )
    with Image.open(paths["png"]) as image:
        canvas = list(image.size)
    if canvas != spec["canvas_pixels"]:
        raise RuntimeError(f"rendered canvas {canvas} != {spec['canvas_pixels']}")
    return {
        name: {"path": str(path.relative_to(workspace)), "sha256": sha256_file(path)}
        for name, path in paths.items()
    } | {"canvas_pixels": canvas}


def _plain(value: float, _position: int) -> str:
    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))
    return f"{value:g}"


def _render_fig1(
    workspace: Path, spec: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    rows = _rows(data_path)
    lengths = np.asarray(sorted({int(row["block_length"]) for row in rows}))
    a_values = np.asarray(sorted({float(row["a"]) for row in rows}))
    entropy_by_point = {
        (float(row["a"]), int(row["block_length"])): float(row["entropy_bits"])
        for row in rows
    }
    x, y = np.meshgrid(lengths, a_values)
    z = np.asarray(
        [
            [entropy_by_point[(a_value, length)] for length in lengths]
            for a_value in a_values
        ]
    )

    figure = _new_figure(spec)
    axis = figure.add_axes(spec["axes_position"], projection="3d")
    palette = LinearSegmentedColormap.from_list(
        "vidal_surface", ["#11a9df", "#72a8d5", "#9b94c2"]
    )
    facecolors = palette(Normalize(vmin=0.0, vmax=1.0)(y))
    axis.plot_surface(
        x,
        y,
        z,
        rstride=5,
        cstride=1,
        facecolors=facecolors,
        edgecolor="#202020",
        linewidth=0.75,
        antialiased=True,
        shade=False,
    )
    axis.set_xlim(1, 20)
    axis.set_ylim(0, 1)
    axis.set_zlim(0, 1.35)
    axis.set_xticks([5, 10, 15, 20])
    axis.set_yticks([0.5, 1.0])
    axis.set_zticks([0.0, 0.5, 1.0])
    axis.xaxis.set_major_formatter(FuncFormatter(_plain))
    axis.yaxis.set_major_formatter(FuncFormatter(_plain))
    axis.zaxis.set_major_formatter(FuncFormatter(_plain))
    axis.set_xlabel(r"$L$", fontsize=spec["font_sizes"]["label"], labelpad=12)
    axis.set_ylabel(r"$a$", fontsize=spec["font_sizes"]["label"], labelpad=14)
    axis.set_zlabel(r"$S_L$", fontsize=spec["font_sizes"]["label"], labelpad=10)
    axis.tick_params(labelsize=spec["font_sizes"]["tick"], pad=3, width=1.0)
    axis.view_init(elev=spec["camera"]["elevation"], azim=spec["camera"]["azimuth"])
    axis.set_box_aspect(spec["camera"]["box_aspect"])
    axis.grid(False)
    for pane in [axis.xaxis.pane, axis.yaxis.pane, axis.zaxis.pane]:
        pane.set_facecolor((1, 1, 1, 0))
        pane.set_edgecolor("#202020")
        pane.set_alpha(0.0)
    return _save(figure, workspace, spec)


def _render_fig2(
    workspace: Path, spec: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(data_path):
        grouped[row["series_id"]].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: int(row["block_length"]))

    def arrays(series: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rows = grouped[series]
        return (
            np.asarray([int(row["block_length"]) for row in rows]),
            np.asarray([float(row["entropy_bits"]) for row in rows]),
            np.asarray([float(row["guide_entropy_bits"]) for row in rows]),
        )

    ising_l, ising_s, ising_guide = arrays("critical_ising")
    xx_l, xx_s, xx_guide = arrays("critical_xx")
    xxx_l, xxx_s, _ = arrays("xxx_antiferromagnetic")

    figure = _new_figure(spec)
    axis = figure.add_axes(spec["axes_position"])
    axis.plot(xx_l, xx_guide, color="#0000ff", linestyle=":", linewidth=1.05)
    axis.plot(
        xx_l,
        xx_s,
        color="#00c91d",
        linestyle="none",
        marker="x",
        markersize=4.0,
        markeredgewidth=0.8,
    )
    axis.plot(
        xxx_l,
        xxx_s,
        color="#00cbd5",
        linestyle="none",
        marker="*",
        markersize=6.2,
        markeredgewidth=0.8,
    )
    axis.plot(ising_l, ising_guide, color="#ff00d0", linestyle=":", linewidth=1.05)
    axis.plot(
        ising_l,
        ising_s,
        color="#ff0018",
        linestyle="none",
        marker="+",
        markersize=4.6,
        markeredgewidth=0.8,
    )
    axis.set_xlim(1, 40)
    axis.set_ylim(0.5, 3.0)
    axis.xaxis.set_major_locator(MultipleLocator(5))
    axis.xaxis.set_minor_locator(MultipleLocator(2.5))
    axis.yaxis.set_major_locator(MultipleLocator(0.5))
    axis.yaxis.set_major_formatter(FuncFormatter(_plain))
    axis.tick_params(
        which="major",
        direction="in",
        top=True,
        right=True,
        length=6,
        width=1.15,
        labelsize=spec["font_sizes"]["tick"],
        pad=7,
    )
    axis.tick_params(
        which="minor", direction="in", top=True, right=True, length=4, width=1.0
    )
    axis.set_xlabel(r"$L$", fontsize=spec["font_sizes"]["label"], labelpad=8)
    axis.set_ylabel(r"$S(L)$", fontsize=spec["font_sizes"]["label"], labelpad=12)
    return _save(figure, workspace, spec)


def render(contract_path: Path) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if set(contract["allowed_adjustments"]) != ALLOWED_ADJUSTMENTS:
        raise ValueError("RenderContract contains an unapproved adjustment")
    if contract["locked_fields"]["numeric_values_may_change"] is not False:
        raise ValueError("numeric values must remain locked")
    if contract["locked_fields"]["source_pixels_may_feed_numerics"] is not False:
        raise ValueError("source pixels cannot feed numerics")
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
        references[item["figure_id"]] = path

    _style()
    specs = {item["figure_id"]: item for item in contract["figures"]}
    outputs = {
        "MAIN_FIG1": _render_fig1(
            workspace, specs["MAIN_FIG1"], frozen["fig1_ising_surface.csv"]
        ),
        "MAIN_FIG2": _render_fig2(
            workspace, specs["MAIN_FIG2"], frozen["fig2_critical_entropy.csv"]
        ),
    }
    for figure_id, spec in specs.items():
        _comparison_board(
            references[figure_id],
            workspace / spec["output_png"],
            workspace / spec["comparison"],
        )

    result = {
        "schema_version": 1,
        "paper_id": contract["paper_id"],
        "status": "passed",
        "channel": "presentation_only_after_frozen_numerics",
        "frozen_data": contract["frozen_data"],
        "source_references": contract["source_references"],
        "allowed_adjustments": sorted(ALLOWED_ADJUSTMENTS),
        "locked_fields": contract["locked_fields"],
        "outputs": outputs,
        "scientific_regions": contract["scientific_regions"],
    }
    check_path = workspace / contract["check_output"]
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
