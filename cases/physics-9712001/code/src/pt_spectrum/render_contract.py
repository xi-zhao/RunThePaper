"""Presentation-only rendering over hash-frozen PT-spectrum data."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont

ALLOWED_ADJUSTMENTS = {
    "canvas",
    "axes_position",
    "font",
    "line_style",
    "palette",
    "interpolation",
    "camera",
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


def _bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.weight": "bold",
            "mathtext.fontset": "stix",
            "axes.linewidth": 1.0,
            "svg.fonttype": "none",
            "svg.hashsalt": "physics-9712001-render-contract-v1",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def _new_axes(spec: dict[str, Any]) -> tuple[plt.Figure, plt.Axes]:
    width, height = spec["canvas_pixels"]
    dpi = float(spec["dpi"])
    figure = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    return figure, figure.add_axes(spec["axes_position"])


def _normalize_svg(path: Path) -> None:
    """Keep generated vector evidence text-clean without changing geometry."""

    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def _save(figure: plt.Figure, workspace: Path, spec: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "png": workspace / spec["output_png"],
        "svg": workspace / spec["output_svg"],
        "pdf": workspace / spec["output_pdf"],
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(paths["png"], dpi=spec["dpi"])
    figure.savefig(paths["svg"], format="svg", metadata={"Date": None})
    _normalize_svg(paths["svg"])
    figure.savefig(
        paths["pdf"],
        format="pdf",
        metadata={"CreationDate": None, "ModDate": None},
    )
    plt.close(figure)
    with Image.open(paths["png"]) as image:
        canvas = list(image.size)
    if canvas != spec["canvas_pixels"]:
        raise RuntimeError(f"rendered canvas {canvas} != {spec['canvas_pixels']}")
    return {
        name: {
            "path": str(path.relative_to(workspace)),
            "sha256": sha256_file(path),
        }
        for name, path in paths.items()
    } | {"canvas_pixels": canvas}


def _common_axis_style(axis: plt.Axes) -> None:
    axis.tick_params(
        which="major",
        direction="in",
        top=True,
        right=True,
        length=10,
        width=1.0,
        labelsize=26,
        pad=10,
    )
    axis.tick_params(
        which="minor", direction="in", top=True, right=True, length=5, width=0.8
    )
    axis.set_xlabel("N", fontsize=32, fontweight="bold", labelpad=20)
    axis.set_ylabel("Energy", fontsize=32, fontweight="bold", labelpad=18)


def _contiguous_segments(
    points: list[tuple[float, float]], *, max_delta_n: float, max_delta_energy: float
) -> list[list[tuple[float, float]]]:
    """Split rank-sorted eigenvalues at missing/complex branch intervals.

    Sorting eigenvalues at every N does not assign a global eigenstate identity.
    Drawing through a gap would therefore invent a branch that the numerical
    solver never produced.  Markers remain the primary data; lines join only
    locally continuous adjacent samples.
    """

    ordered = sorted(points)
    if not ordered:
        return []
    segments: list[list[tuple[float, float]]] = [[ordered[0]]]
    for point in ordered[1:]:
        previous = segments[-1][-1]
        if (
            point[0] - previous[0] <= max_delta_n
            and abs(point[1] - previous[1]) <= max_delta_energy
        ):
            segments[-1].append(point)
        else:
            segments.append([point])
    return segments


def _render_fig1(
    workspace: Path, spec: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    visible = [
        row
        for row in _rows(data_path)
        if _bool(row["is_real"]) and _bool(row["visible_in_paper_window"])
    ]
    grouped: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for row in visible:
        grouped[int(row["mode_rank"])].append(
            (float(row["N"]), float(row["energy_real"]))
        )

    figure, axis = _new_axes(spec)
    for mode_rank in sorted(grouped):
        for points in _contiguous_segments(
            grouped[mode_rank], max_delta_n=0.061, max_delta_energy=1.0
        ):
            axis.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                color="black",
                linewidth=0.8,
                marker="o",
                markersize=5.0,
                markeredgewidth=0.0,
            )
    axis.axvline(1.0, color="#30c5cf", linestyle=(0, (8, 8)), linewidth=1.0)
    axis.axvline(2.0, color="#55c83f", linestyle=(0, (8, 8)), linewidth=1.0)
    axis.set_xlim(0.8, 5.0)
    axis.set_ylim(0.0, 20.0)
    axis.set_xticks([1, 2, 3, 4, 5])
    axis.set_xticks([1.5, 2.5, 3.5, 4.5], minor=True)
    axis.set_yticks(list(range(1, 20, 2)))
    axis.set_yticks(list(range(0, 21, 2)), minor=True)
    _common_axis_style(axis)
    return _save(figure, workspace, spec)


def _render_fig3(
    workspace: Path, spec: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    visible = [
        row
        for row in _rows(data_path)
        if _bool(row["is_real"]) and _bool(row["visible_in_paper_window"])
    ]
    palette = {0.1875: "#0000ff", 0.3125: "#ff1717", 0.4375: "#000000"}
    markers = {0.1875: "D", 0.3125: "o", 0.4375: "s"}
    labels = {
        0.1875: r"$m^2\!=\!3/16$",
        0.3125: r"$m^2\!=\!5/16$",
        0.4375: r"$m^2\!=\!7/16$",
    }
    grouped: dict[tuple[float, int], list[tuple[float, float]]] = defaultdict(list)
    for row in visible:
        key = (float(row["mass_squared"]), int(row["mode_rank"]))
        grouped[key].append((float(row["N"]), float(row["energy_real"])))

    figure, axis = _new_axes(spec)
    for key in sorted(grouped):
        mass_squared, _mode_rank = key
        for points in _contiguous_segments(
            grouped[key], max_delta_n=0.031, max_delta_energy=0.7
        ):
            axis.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                color=palette[mass_squared],
                linewidth=0.75,
                marker=markers[mass_squared],
                markersize=4.8,
                markeredgewidth=0.0,
            )
    handles = [
        Line2D(
            [0],
            [0],
            color=palette[mass_squared],
            marker=markers[mass_squared],
            markersize=7.0,
            linewidth=0.9,
            label=labels[mass_squared],
        )
        for mass_squared in [0.1875, 0.3125, 0.4375]
    ]
    axis.legend(
        handles=handles,
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.04, 0.985),
        fontsize=27,
        handlelength=2.6,
        labelspacing=0.9,
        borderaxespad=0.0,
    )
    axis.set_xlim(0.0, 1.5)
    axis.set_ylim(0.0, 12.5)
    axis.set_xticks([0.0, 0.5, 1.0, 1.5])
    axis.set_xticklabels(["0", "0.5", "1.0", "1.5"])
    axis.set_xticks([0.25, 0.75, 1.25], minor=True)
    axis.set_yticks(list(range(0, 13, 2)))
    axis.set_yticks(list(range(1, 13, 2)), minor=True)
    _common_axis_style(axis)
    return _save(figure, workspace, spec)


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as left, Image.open(generated).convert(
        "RGB"
    ) as right:
        if left.size != right.size:
            raise ValueError(f"comparison canvases differ: {left.size} != {right.size}")
        title_height = 100
        canvas = Image.new("RGB", (2 * left.width, left.height + title_height), "white")
        canvas.paste(left, (0, title_height))
        canvas.paste(right, (left.width, title_height))
        draw = ImageDraw.Draw(canvas)
        font = _font(34)
        labels = [
            "Original paper — comparison only",
            "Independent formula-derived result",
        ]
        for index, label in enumerate(labels):
            box = draw.textbbox((0, 0), label, font=font)
            center = index * left.width + left.width // 2
            draw.text(
                (center - (box[2] - box[0]) // 2, 25),
                label,
                fill="black",
                font=font,
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, optimize=True)


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
        frozen[item["path"]] = path

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
            workspace,
            specs["MAIN_FIG1"],
            frozen[specs["MAIN_FIG1"]["data_path"]],
        ),
        "MAIN_FIG3": _render_fig3(
            workspace,
            specs["MAIN_FIG3"],
            frozen[specs["MAIN_FIG3"]["data_path"]],
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
