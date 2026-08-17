"""Presentation-only rendering over hash-frozen spin-squeezing data."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import map_coordinates

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


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 1.0,
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
    with Image.open(paths["png"]) as image:
        canvas = list(image.size)
        if canvas != spec["canvas_pixels"]:
            if any(
                abs(observed - expected) > 1
                for observed, expected in zip(canvas, spec["canvas_pixels"])
            ):
                raise RuntimeError(
                    f"rendered canvas {canvas} != {spec['canvas_pixels']}"
                )
            resized = image.resize(
                tuple(spec["canvas_pixels"]), Image.Resampling.LANCZOS
            )
            resized.save(paths["png"])
            canvas = list(resized.size)
    return {
        name: {"path": str(path.relative_to(workspace)), "sha256": sha256_file(path)}
        for name, path in paths.items()
    } | {"canvas_pixels": canvas}


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as left, Image.open(generated).convert(
        "RGB"
    ) as right:
        if left.size != right.size:
            raise ValueError(f"comparison canvases differ: {left.size} != {right.size}")
        title_height = max(52, left.height // 8)
        canvas = Image.new("RGB", (2 * left.width, left.height + title_height), "white")
        canvas.paste(left, (0, title_height))
        canvas.paste(right, (left.width, title_height))
        draw = ImageDraw.Draw(canvas)
        font = _font(max(18, left.width // 35))
        labels = [
            "Original paper — comparison only",
            "Independent formula-derived result",
        ]
        for index, label in enumerate(labels):
            box = draw.textbbox((0, 0), label, font=font)
            center = index * left.width + left.width // 2
            draw.text(
                (center - (box[2] - box[0]) // 2, title_height // 5),
                label,
                fill="black",
                font=font,
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, optimize=True)


def _load_axes(path: Path) -> tuple[np.ndarray, np.ndarray]:
    theta: list[float] = []
    phi: list[float] = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            target = theta if row["axis"] == "theta" else phi
            target.append(float(row["radians"]))
    return np.asarray(theta), np.asarray(phi)


def _sample_disk(
    q_values: np.ndarray,
    theta: np.ndarray,
    phi: np.ndarray,
    projection: str,
    pixels: int = 501,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    coordinate = np.linspace(-1.0, 1.0, pixels)
    horizontal, vertical = np.meshgrid(coordinate, coordinate)
    radius_squared = horizontal * horizontal + vertical * vertical
    inside = radius_squared <= 1.0
    third = np.sqrt(np.clip(1.0 - radius_squared, 0.0, 1.0))
    if projection == "front_x":
        sampled_theta = np.arccos(np.clip(vertical, -1.0, 1.0))
        sampled_phi = np.arctan2(horizontal, third)
    elif projection == "front_z":
        sampled_theta = np.arccos(third)
        sampled_phi = np.arctan2(vertical, horizontal)
    else:
        raise ValueError(f"unsupported projection: {projection}")
    theta_index = (sampled_theta - theta[0]) / (theta[-1] - theta[0]) * (len(theta) - 1)
    phi_index = (sampled_phi - phi[0]) / (phi[-1] - phi[0]) * (len(phi) - 1)
    sampled = map_coordinates(
        q_values,
        [theta_index, phi_index],
        order=1,
        mode="wrap",
    )
    normalized = sampled / max(float(np.max(sampled[inside])), np.finfo(float).tiny)
    gray = np.ones_like(normalized)
    gray[inside] = 1.0 - np.power(np.clip(normalized[inside], 0.0, 1.0), 0.48)
    return horizontal, vertical, gray


def _sphere_grid(axis: plt.Axes, projection: str) -> None:
    angle = np.linspace(0.0, 2.0 * np.pi, 361)
    axis.plot(np.cos(angle), np.sin(angle), color="black", linewidth=1.15, zorder=5)
    if projection == "front_x":
        front_phi = np.linspace(-np.pi / 2.0, np.pi / 2.0, 241)
        for theta in np.deg2rad(np.arange(15, 180, 15)):
            axis.plot(
                np.sin(theta) * np.sin(front_phi),
                np.full_like(front_phi, np.cos(theta)),
                color="black",
                linewidth=0.46,
                alpha=0.9,
                zorder=4,
            )
        polar = np.linspace(0.0, np.pi, 241)
        for phi in np.deg2rad(np.arange(-75, 90, 15)):
            axis.plot(
                np.sin(polar) * np.sin(phi),
                np.cos(polar),
                color="black",
                linewidth=0.46,
                alpha=0.9,
                zorder=4,
            )
    else:
        for radius in np.sin(np.deg2rad(np.arange(10, 90, 10))):
            axis.plot(
                radius * np.cos(angle),
                radius * np.sin(angle),
                color="black",
                linewidth=0.46,
                alpha=0.9,
                zorder=4,
            )
        radius = np.linspace(0.0, 1.0, 121)
        for azimuth in np.deg2rad(np.arange(0, 360, 15)):
            axis.plot(
                radius * np.cos(azimuth),
                radius * np.sin(azimuth),
                color="black",
                linewidth=0.46,
                alpha=0.9,
                zorder=4,
            )


def _rotation_marks(axis: plt.Axes, projection: str) -> None:
    if projection == "front_x":
        axis.add_patch(Arc((0.0, 1.12), 0.42, 0.18, theta1=15, theta2=325, lw=0.9))
        axis.annotate(
            "",
            xy=(0.18, 1.14),
            xytext=(0.12, 1.20),
            arrowprops={"arrowstyle": "->", "lw": 0.9},
        )
        axis.add_patch(Arc((0.0, -1.12), 0.42, 0.18, theta1=195, theta2=505, lw=0.9))
        axis.annotate(
            "",
            xy=(-0.18, -1.14),
            xytext=(-0.12, -1.20),
            arrowprops={"arrowstyle": "->", "lw": 0.9},
        )
    else:
        for center, start, end in [
            ((-0.84, 0.84), 70, 260),
            ((0.84, 0.84), -80, 110),
            ((-0.84, -0.84), 100, 290),
            ((0.84, -0.84), -110, 80),
        ]:
            axis.add_patch(Arc(center, 0.35, 0.24, theta1=start, theta2=end, lw=0.8))


def _render_qpd_figure(
    workspace: Path,
    spec: dict[str, Any],
    axes_path: Path,
    data_paths: list[Path],
    projection: str,
) -> dict[str, Any]:
    theta, phi = _load_axes(axes_path)
    figure = _new_figure(spec)
    for index, (position, path) in enumerate(zip(spec["panel_positions"], data_paths)):
        axis = figure.add_axes(position)
        q_values = np.load(path, allow_pickle=False)
        _, _, gray = _sample_disk(q_values, theta, phi, projection)
        axis.imshow(
            gray,
            extent=(-1.0, 1.0, -1.0, 1.0),
            origin="lower",
            cmap="gray",
            vmin=0.0,
            vmax=1.0,
            interpolation=spec["interpolation"],
            zorder=1,
        )
        _sphere_grid(axis, projection)
        if index > 0:
            _rotation_marks(axis, projection)
        axis.set_xlim(-1.24, 1.24)
        axis.set_ylim(-1.30, 1.26)
        axis.set_aspect("equal")
        axis.axis("off")
        horizontal_label = "y" if projection == "front_x" else "x"
        vertical_label = "z" if projection == "front_x" else "y"
        axis.text(
            1.05, -0.03, horizontal_label, fontsize=spec["axis_font_size"], va="center"
        )
        axis.text(
            0.0, 1.08, vertical_label, fontsize=spec["axis_font_size"], ha="center"
        )
        axis.text(
            0.0,
            -1.26,
            f"({chr(ord('a') + index)})",
            fontsize=spec["panel_font_size"],
            ha="center",
            va="top",
        )
    return _save(figure, workspace, spec)


def _plain_log(value: float, _position: int) -> str:
    if value >= 1.0 and abs(value - round(value)) < 1e-10:
        return str(int(round(value)))
    return f"{value:g}"


def _render_variance(
    workspace: Path, spec: dict[str, Any], data_path: Path
) -> dict[str, Any]:
    with data_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    spin = np.asarray([float(row["spin"]) for row in rows])
    css = np.asarray([float(row["css_variance"]) for row in rows])
    oat = np.asarray([float(row["one_axis_minimum"]) for row in rows])
    oat_asym = np.asarray([float(row["one_axis_asymptote"]) for row in rows])
    tact = np.asarray([float(row["two_axis_minimum"]) for row in rows])
    tact_asym = np.asarray([float(row["two_axis_asymptote"]) for row in rows])

    figure = _new_figure(spec)
    axis = figure.add_axes(spec["axes_position"])
    axis.set_xscale("log")
    axis.set_yscale("log")
    large = spin >= 10.0
    asymptotic = spin >= 20.0
    axis.plot(spin, css, color="black", linestyle="none", marker=".", markersize=3.0)
    axis.plot(spin[large], css[large], color="black", linewidth=1.25)
    axis.plot(spin, oat, color="black", marker=".", markersize=3.0, linewidth=1.0)
    axis.plot(
        spin[asymptotic],
        oat_asym[asymptotic],
        color="black",
        linestyle="--",
        linewidth=0.9,
    )
    axis.plot(spin, tact, color="black", marker=".", markersize=3.0, linewidth=1.0)
    axis.plot(
        spin[asymptotic],
        tact_asym[asymptotic],
        color="black",
        linestyle="--",
        linewidth=0.9,
    )
    axis.set_xlim(1.1, 150.0)
    axis.set_ylim(0.23, 60.0)
    axis.set_xticks([])
    axis.set_yticks([])
    axis.tick_params(which="both", length=0)
    axis.axhline(1.0, color="black", linewidth=0.75)
    axis.axvline(1.5, color="black", linewidth=0.75)
    for value in [2, 5, 10, 50, 100]:
        axis.plot([value, value], [0.95, 1.055], color="black", linewidth=0.65)
        axis.text(
            value,
            0.88,
            _plain_log(value, 0),
            ha="center",
            va="top",
            fontsize=spec["tick_font_size"],
        )
    for value in [0.5, 2, 5, 10, 20, 50]:
        axis.plot([1.46, 1.54], [value, value], color="black", linewidth=0.65)
        axis.text(
            1.43,
            value,
            _plain_log(value, 0),
            ha="right",
            va="center",
            fontsize=spec["tick_font_size"],
        )
    axis.text(
        8.0, 0.62, r"$S$", fontsize=spec["label_font_size"], ha="center", va="center"
    )
    axis.text(
        0.02,
        0.53,
        r"$V_{\min}$",
        fontsize=spec["label_font_size"],
        rotation=90,
        ha="center",
        va="center",
        transform=axis.transAxes,
    )
    axis.text(50, 28, "CSS", fontsize=spec["annotation_font_size"], rotation=46)
    axis.text(45, 1.62, "one-axis", fontsize=spec["annotation_font_size"], rotation=16)
    axis.text(46, 0.56, "two-axis", fontsize=spec["annotation_font_size"])
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
    q_axes = frozen["qpd_axes.csv"]
    outputs = {
        "MAIN_FIG2": _render_qpd_figure(
            workspace,
            specs["MAIN_FIG2"],
            q_axes,
            [frozen[f"T{index:03d}_qpd.npy"] for index in range(1, 4)],
            "front_x",
        ),
        "MAIN_FIG3": _render_qpd_figure(
            workspace,
            specs["MAIN_FIG3"],
            q_axes,
            [frozen[f"T{index:03d}_qpd.npy"] for index in range(4, 7)],
            "front_z",
        ),
        "MAIN_FIG4": _render_variance(
            workspace, specs["MAIN_FIG4"], frozen["variance_scaling.csv"]
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
