"""Hash-guarded presentation-only rendering for Main Fig. 2.

This module is deliberately separate from the numerical runner.  It may read
the source reference to verify the declared canvas, but it can only render the
already-frozen CSV.  Physics parameters and arrays are protected by SHA-256.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw, ImageFont


ALLOWED_ADJUSTMENTS = {
    "canvas",
    "axes_position",
    "font",
    "line_style",
    "palette",
    "ticks",
    "legend",
    "grid",
    "interpolation",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1001:
        raise ValueError(f"expected 1001 frozen phase rows, got {len(rows)}")
    return {
        field: np.asarray([float(row[field]) for row in rows], dtype=np.float64)
        for field in rows[0]
    }


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as source_image, Image.open(generated).convert("RGB") as generated_image:
        if source_image.size != generated_image.size:
            raise ValueError(f"comparison images must share a canvas: {source_image.size} != {generated_image.size}")
        title_height = 92
        canvas = Image.new("RGB", (source_image.width * 2, source_image.height + title_height), "white")
        canvas.paste(source_image, (0, title_height))
        canvas.paste(generated_image, (source_image.width, title_height))
        draw = ImageDraw.Draw(canvas)
        font = _font(34)
        labels = ["Original paper — comparison only", "Independent formula-derived result"]
        for index, label in enumerate(labels):
            box = draw.textbbox((0, 0), label, font=font)
            center = source_image.width * index + source_image.width // 2
            draw.text((center - (box[2] - box[0]) // 2, 24), label, fill="black", font=font)
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, optimize=True)


def _custom_legend(axis, styles: dict[str, Any]) -> None:
    legend = styles["legend"]
    box = legend["box_axes"]
    rectangle = Rectangle(
        (box[0], box[1]),
        box[2],
        box[3],
        transform=axis.transAxes,
        facecolor="white",
        edgecolor="black",
        linewidth=legend["border_width"],
        zorder=20,
    )
    axis.add_patch(rectangle)
    setup_x = legend["setup_x"]
    row_y = legend["row_y"]
    for x, setup in zip(setup_x, ["ab", "aabb", "abab", "abba"]):
        axis.text(
            x,
            legend["header_y"],
            rf"${setup}$",
            transform=axis.transAxes,
            ha="center",
            va="center",
            fontsize=legend["font_size"],
            zorder=21,
        )
    for label, y in zip([r"$g$", r"$\Gamma_j$", r"$\Gamma_{\rm coll}$"], row_y):
        axis.text(
            legend["label_x"],
            y,
            label,
            transform=axis.transAxes,
            ha="left",
            va="center",
            fontsize=legend["font_size"],
            zorder=21,
        )
    line_styles = ["-", tuple(styles["dash_patterns"]["dashed"]), tuple(styles["dash_patterns"]["dotted"])]
    for x, setup in zip(setup_x, ["ab", "aabb", "abab", "abba"]):
        for y, line_style in zip(row_y, line_styles):
            axis.plot(
                [x - legend["line_half_width"], x + legend["line_half_width"]],
                [y, y],
                transform=axis.transAxes,
                color=styles["palette"][setup],
                linestyle=line_style,
                linewidth=styles["line_width"],
                solid_capstyle="butt",
                dash_capstyle="butt",
                zorder=22,
            )


def render(contract_path: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if set(contract["allowed_adjustments"]) != ALLOWED_ADJUSTMENTS:
        raise ValueError("RenderContract adjustment set is not the approved presentation-only set")

    workspace = contract_path.resolve().parents[1]
    data_path = workspace / contract["frozen_data"]["path"]
    source_path = workspace / contract["source_reference"]["path"]
    if sha256_file(data_path) != contract["frozen_data"]["sha256"]:
        raise RuntimeError("frozen numerical array hash changed; rendering is forbidden")
    if sha256_file(source_path) != contract["source_reference"]["sha256"]:
        raise RuntimeError("source reference hash changed")
    data = _read_csv(data_path)
    styles = contract["style"]

    canvas = styles["canvas_pixels"]
    dpi = int(styles["dpi"])
    plt.rcParams.update(
        {
            "font.family": styles["font"]["family"],
            "font.size": styles["font"]["base_size"],
            "mathtext.fontset": styles["font"]["mathtext_fontset"],
            "axes.linewidth": styles["axes_line_width"],
            "lines.scale_dashes": False,
        }
    )
    page_points = styles["vector_page_points"]
    figure = plt.figure(figsize=(page_points[0] / 72.0, page_points[1] / 72.0), dpi=dpi, facecolor="white")
    axis = figure.add_axes(styles["axes_position"])
    palette = styles["palette"]
    phase = data["phi"]

    axis.set_axisbelow(True)
    axis.grid(
        True,
        which="major",
        color=styles["grid"]["color"],
        linestyle=tuple(styles["dash_patterns"]["dotted"]),
        linewidth=styles["grid"]["line_width"],
    )
    axis.axhline(0.0, color="black", linewidth=styles["zero_line_width"], zorder=2)
    axis.axhline(
        1.0,
        color="black",
        linestyle=tuple(styles["dash_patterns"]["dashdot"]),
        linewidth=styles["reference_line_width"],
        zorder=2,
    )

    # Matplotlib 1.5.3 emitted the paper's paths grouped by line identity:
    # exchange (solid), individual decay (dashed), then collective decay
    # (dotted).  Preserve that presentation-only draw order so coincident
    # formula-derived curves have the same visible stacking as the paper.
    for setup in ["ab", "aabb", "abab", "abba"]:
        color = palette[setup]
        axis.plot(
            phase,
            data[f"{setup}_g"],
            color=color,
            linestyle="-",
            linewidth=styles["line_width"],
            zorder=3,
        )

    for setup in ["ab", "aabb", "abab", "abba"]:
        color = palette[setup]
        axis.plot(
            phase,
            data[f"{setup}_gamma_a"],
            color=color,
            linestyle=tuple(styles["dash_patterns"]["dashed"]),
            linewidth=styles["line_width"],
            zorder=3,
        )
        if setup == "abba":
            axis.plot(
                phase,
                data[f"{setup}_gamma_b"],
                color=color,
                linestyle=tuple(styles["dash_patterns"]["dashed"]),
                linewidth=styles["line_width"],
                zorder=3,
            )

    for setup in ["ab", "aabb", "abab", "abba"]:
        color = palette[setup]
        axis.plot(
            phase,
            data[f"{setup}_gamma_coll"],
            color=color,
            linestyle=tuple(styles["dash_patterns"]["dotted"]),
            linewidth=styles["line_width"],
            zorder=3,
        )

    axis.set_xlim(0.0, np.pi)
    axis.set_ylim(-4.0, 4.0)
    axis.set_xticks([0.0, np.pi / 4.0, np.pi / 2.0, 3.0 * np.pi / 4.0, np.pi])
    axis.set_xticklabels([r"$0$", r"$\pi/4$", r"$\pi/2$", r"$3\pi/4$", r"$\pi$"])
    axis.set_yticks(np.arange(-4, 5, dtype=int))
    axis.tick_params(
        axis="both",
        which="major",
        direction="in",
        top=True,
        right=True,
        length=styles["ticks"]["length"],
        width=styles["ticks"]["width"],
        labelsize=styles["ticks"]["font_size"],
        pad=styles["ticks"]["pad"],
    )
    axis.set_xlabel(r"$\varphi$", fontsize=styles["font"]["axis_label_size"], labelpad=styles["font"]["x_label_pad"])
    axis.set_ylabel(
        r"$\{g,\ \Gamma_j,\ \Gamma_{\rm coll}\}/\gamma$",
        fontsize=styles["font"]["axis_label_size"],
        labelpad=styles["font"]["y_label_pad"],
    )
    _custom_legend(axis, styles)

    output_path = workspace / contract["output"]["path"]
    eps_path = workspace / contract["output"]["vector_eps_path"]
    pdf_path = workspace / contract["output"]["vector_pdf_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=dpi, facecolor="white")
    figure.savefig(eps_path, format="eps", facecolor="white")
    plt.close(figure)
    subprocess.run(
        [
            "gs",
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pdfwrite",
            "-dEPSCrop",
            f"-sOutputFile={pdf_path}",
            str(eps_path),
        ],
        check=True,
        capture_output=True,
    )

    with Image.open(output_path) as generated_image:
        generated_size = list(generated_image.size)
    if generated_size != canvas:
        raise RuntimeError(f"rendered canvas {generated_size} != declared canvas {canvas}")

    comparison_path = workspace / contract["comparison"]["path"]
    _comparison_board(source_path, output_path, comparison_path)
    result = {
        "schema_version": 1,
        "paper_id": "1711.08863",
        "status": "passed",
        "channel": "presentation_only_after_frozen_numerics",
        "frozen_data": {
            "path": contract["frozen_data"]["path"],
            "sha256": sha256_file(data_path),
        },
        "source_reference": {
            "path": contract["source_reference"]["path"],
            "sha256": sha256_file(source_path),
        },
        "allowed_adjustments": sorted(ALLOWED_ADJUSTMENTS),
        "locked_fields": contract["locked_fields"],
        "output": {
            "path": contract["output"]["path"],
            "sha256": sha256_file(output_path),
            "canvas_pixels": generated_size,
            "vector_eps_path": contract["output"]["vector_eps_path"],
            "vector_eps_sha256": sha256_file(eps_path),
            "vector_pdf_path": contract["output"]["vector_pdf_path"],
            "vector_pdf_sha256": sha256_file(pdf_path),
        },
        "scientific_regions": contract["scientific_regions"],
    }
    check_path = workspace / contract["check_output"]
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result
