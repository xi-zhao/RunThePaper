"""Presentation-only rendering over attested, hash-frozen numerical arrays."""

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
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import CubicSpline

ALLOWED_ADJUSTMENTS = {
    "canvas",
    "axes_position",
    "font",
    "line_style",
    "palette",
    "ticks",
    "annotations",
    "interpolation",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def grouped(path: Path, key: str) -> dict[int, list[dict[str, str]]]:
    result: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows(path):
        result[int(row[key])].append(row)
    return dict(result)


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
        title_height = 64
        canvas = Image.new("RGB", (left.width * 2, left.height + title_height), "white")
        canvas.paste(left, (0, title_height))
        canvas.paste(right, (left.width, title_height))
        draw = ImageDraw.Draw(canvas)
        font = _font(24)
        for index, label in enumerate(
            ["Original paper — comparison only", "Independent formula-derived result"]
        ):
            box = draw.textbbox((0, 0), label, font=font)
            center = index * left.width + left.width // 2
            draw.text(
                (center - (box[2] - box[0]) // 2, 18), label, fill="black", font=font
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, optimize=True)


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
    dpi = int(spec["dpi"])
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
    # Matplotlib emits trailing spaces in SVG path data. Normalize only that
    # presentation artifact so generated evidence remains Git-clean; this does
    # not inspect or change any numerical array.
    svg_text = paths["svg"].read_text(encoding="utf-8")
    paths["svg"].write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    with Image.open(paths["png"]) as image:
        size = list(image.size)
    if size != spec["canvas_pixels"]:
        raise RuntimeError(
            f"rendered canvas {size} != declared {spec['canvas_pixels']}"
        )
    return {
        key: {"path": str(path.relative_to(workspace)), "sha256": sha256_file(path)}
        for key, path in paths.items()
    } | {"canvas_pixels": size}


def _ticks(axis: plt.Axes, labelsize: float = 9.5) -> None:
    axis.tick_params(
        which="major",
        direction="in",
        top=True,
        right=True,
        length=5,
        width=1,
        labelsize=labelsize,
    )
    axis.tick_params(
        which="minor", direction="in", top=True, right=True, length=3, width=0.8
    )


def _plain(value: float, _position: int) -> str:
    if abs(value - round(value)) < 1.0e-10:
        return str(int(round(value)))
    return f"{value:g}"


def _render_fig1(workspace: Path, spec: dict[str, Any]) -> dict[str, Any]:
    data = grouped(workspace / "outputs/data/fig1_kink_density.csv", "n_spins")
    figure = _new_figure(spec)
    axis = figure.add_axes([0.198, 0.267, 0.398, 0.705])
    for n_spins in sorted(data):
        points = data[n_spins]
        x = np.array([float(row["rate_tau0_over_tauq"]) for row in points])
        y = np.array([float(row["kink_density_per_spin"]) for row in points])
        axis.plot(x, y, color="black", linewidth=0.85)
    fit = [row for row in data[max(data)] if row["n100_kzm_fit_density"]]
    axis.plot(
        [float(row["rate_tau0_over_tauq"]) for row in fit],
        [float(row["n100_kzm_fit_density"]) for row in fit],
        color="black",
        linestyle="--",
        linewidth=0.85,
    )
    axis.set_xlim(0, 0.5)
    axis.set_ylim(0, 0.12)
    axis.set_xticks(np.arange(0, 0.51, 0.1))
    axis.set_yticks(np.arange(0, 0.121, 0.04))
    axis.xaxis.set_major_formatter(FuncFormatter(_plain))
    axis.yaxis.set_major_formatter(FuncFormatter(_plain))
    _ticks(axis, 9.5)
    axis.set_xlabel(r"$\tau_0/\tau_Q$", fontsize=13, labelpad=3)
    axis.set_ylabel(r"Kink density $\nu$", fontsize=13, labelpad=18)

    inset = figure.add_axes([0.685, 0.407, 0.212, 0.436])
    for n_spins in sorted(data):
        points = data[n_spins]
        inset.plot(
            [float(row["rate_tau0_over_tauq"]) for row in points],
            [float(row["kink_density_per_spin"]) for row in points],
            color="black",
            linewidth=0.75,
        )
    inset.set_xlim(0.1, 0.15)
    inset.set_ylim(0.044, 0.06)
    inset.set_xticks([0.1, 0.15])
    inset.set_yticks([0.044, 0.06])
    inset.xaxis.set_major_formatter(FuncFormatter(_plain))
    inset.yaxis.set_major_formatter(FuncFormatter(_plain))
    inset.yaxis.tick_right()
    _ticks(inset, 9.5)
    axis.indicate_inset_zoom(inset, edgecolor="black", linewidth=0.55)
    return _save(figure, workspace, spec)


def _render_fig2(workspace: Path, spec: dict[str, Any]) -> dict[str, Any]:
    figure = _new_figure(spec)
    left = figure.add_axes([0.062, 0.2817, 0.2205, 0.6907])
    spectrum: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(workspace / "outputs/data/fig2a_spectrum.csv"):
        spectrum[row["curve_id"]].append(row)
    for curve in spectrum.values():
        x = np.asarray([float(row["field_j_over_w"]) for row in curve])
        y = np.asarray([float(row["energy_over_w"]) for row in curve])
        # The author EPS contains 201 field samples across [0, 2].  Recreate
        # that presentation density from the already frozen 81-point curves;
        # this is a RenderContract interpolation and never feeds numerics back
        # into the scientific runner.
        samples = max(2, int(round((x[-1] - x[0]) / 0.01)) + 1)
        x_render = np.linspace(x[0], x[-1], samples)
        y_render = (
            CubicSpline(x, y)(x_render) if x.size >= 4 else np.interp(x_render, x, y)
        )
        left.plot(
            x_render,
            y_render,
            color="black",
            linewidth=0.50,
            linestyle=(
                "-" if curve[0]["parity"] == "accessible_even" else (0, (4.0, 2.0))
            ),
            antialiased=False,
        )
    left.set_xlim(0, 2)
    left.set_ylim(0, 6)
    left.set_xticks([0, 1, 2])
    left.set_yticks([0, 2, 4, 6])
    _ticks(left, 8.5)
    left.set_xlabel(r"$J/W$", fontsize=12, labelpad=4)
    left.set_ylabel(r"Energy$/W$", fontsize=12, labelpad=10)

    middle = figure.add_axes([0.396, 0.277, 0.22, 0.693])
    scaling = rows(workspace / "outputs/data/fig2b_fidelity_scaling.csv")
    n_values = np.array([float(row["n_spins"]) for row in scaling])
    tau = np.array(
        [float(row["tau_q_over_tau0_for_target_fidelity"]) for row in scaling]
    )
    tau_fit = np.array([float(row["tau_q_power_fit"]) for row in scaling])
    middle.plot(n_values, tau_fit, color="black", linewidth=0.85)
    middle.plot(n_values, tau, color="black", marker="o", markersize=2.2, linewidth=0)
    middle.set_xlim(0, 100)
    middle.set_ylim(0, 1600)
    middle.set_xticks([0, 20, 40, 60, 80, 100])
    middle.set_yticks([0, 400, 800, 1200, 1600])
    _ticks(middle, 8.5)
    middle.set_xlabel(r"$N$", fontsize=12, labelpad=4)
    middle.set_ylabel(r"$\tau_Q/\tau_0$", fontsize=12, labelpad=8)
    right_scale = middle.twinx()
    fidelity = np.array([float(row["fixed_time_fidelity_exact"]) for row in scaling])
    fidelity_fit = np.array([float(row["fixed_time_lzf_fit"]) for row in scaling])
    right_scale.plot(n_values, fidelity_fit, color="black", linewidth=0.85)
    right_scale.plot(
        n_values, fidelity, color="black", marker="o", markersize=2.2, linewidth=0
    )
    right_scale.set_ylim(0.7, 1.0)
    right_scale.set_yticks([0.7, 0.8, 0.9, 1.0])
    right_scale.yaxis.set_major_formatter(FuncFormatter(_plain))
    _ticks(right_scale, 8.5)
    middle.text(32, 300, "(i)", fontsize=10.5)
    middle.text(75, 300, "(ii)", fontsize=10.5)

    right = figure.add_axes([0.763, 0.277, 0.221, 0.693])
    bounds = grouped(workspace / "outputs/data/fig2c_fidelity_bounds.csv", "n_spins")
    label_positions = {
        90: (0.0015, 0.47, "(i)"),
        70: (0.010, 0.45, "(ii)"),
        50: (0.020, 0.47, "(iii)"),
        30: (0.034, 0.61, "(iv)"),
    }
    for n_spins in [90, 70, 50, 30]:
        points = bounds[n_spins]
        x = np.array([float(row["rate_tau0_over_tauq"]) for row in points])
        lower = np.array([float(row["fidelity_lower_bound"]) for row in points])
        upper = np.array([float(row["fidelity_upper_bound"]) for row in points])
        lower[(lower < 0.2) | (lower > 1.0)] = np.nan
        upper[(upper < 0.2) | (upper > 1.0)] = np.nan
        right.plot(
            x,
            lower,
            color="black",
            linewidth=0.8,
        )
        right.plot(
            x,
            upper,
            color="black",
            linewidth=0.8,
            linestyle="--",
        )
        right.plot(
            x,
            [float(row["lzf_fit_fidelity"]) for row in points],
            color="black",
            linewidth=0.75,
            linestyle=":",
        )
        x_text, y_text, text = label_positions[n_spins]
        right.text(x_text, y_text, text, fontsize=10.5)
    right.set_xlim(0, 0.04)
    right.set_ylim(0.2, 1.0)
    right.set_xticks([0, 0.01, 0.02, 0.03, 0.04])
    right.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    right.xaxis.set_major_formatter(FuncFormatter(_plain))
    right.yaxis.set_major_formatter(FuncFormatter(_plain))
    _ticks(right, 8.5)
    right.set_xlabel(r"$\tau_0/\tau_Q$", fontsize=12, labelpad=4)
    right.set_ylabel(r"$f$", fontsize=12, labelpad=9)
    figure.text(0.0, 0.925, "a)", fontsize=12)
    figure.text(0.312, 0.925, "b)", fontsize=12)
    figure.text(0.68, 0.925, "c)", fontsize=12)
    return _save(figure, workspace, spec)


def _render_fig3(workspace: Path, spec: dict[str, Any]) -> dict[str, Any]:
    data = grouped(workspace / "outputs/data/fig3_kink_count.csv", "n_spins")
    figure = _new_figure(spec)
    axis = figure.add_axes([0.307, 0.204, 0.691, 0.774])
    for n_spins in sorted(data):
        points = data[n_spins]
        x = np.array([float(row["rate_tau0_over_tauq"]) for row in points])
        axis.plot(
            x,
            [float(row["kink_count"]) for row in points],
            color="black",
            linewidth=0.85,
        )
        kzm = np.array([float(row["kzm_fit_kink_count"]) for row in points])
        lzf = np.array([float(row["lzf_kink_estimate"]) for row in points])
        axis.plot(
            x[(x >= 0.025) & (x <= 0.25)],
            kzm[(x >= 0.025) & (x <= 0.25)],
            color="#d7191c",
            linewidth=0.8,
        )
        axis.plot(x[x <= 0.025], lzf[x <= 0.025], color="#244cff", linewidth=0.8)
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlim(5e-4, 4.0)
    axis.set_ylim(1e-4, 100)
    axis.xaxis.set_major_locator(LogLocator(base=10, numticks=5))
    axis.xaxis.set_minor_locator(
        LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=50)
    )
    axis.yaxis.set_major_locator(LogLocator(base=10, numticks=7))
    axis.yaxis.set_minor_locator(
        LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=70)
    )
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.yaxis.set_minor_formatter(NullFormatter())
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:g}"))
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:g}"))
    _ticks(axis, 10.0)
    axis.set_xlabel(r"$\tau_0/\tau_Q$", fontsize=13, labelpad=4)
    axis.set_ylabel("Number of kinks", fontsize=13, labelpad=20)

    inset = figure.add_axes([0.544, 0.319, 0.414, 0.279])
    for n_spins in sorted(data):
        points = data[n_spins]
        x = np.array([float(row["rate_tau0_over_tauq"]) for row in points])
        y = np.array([float(row["kink_count"]) for row in points])
        kzm = np.array([float(row["kzm_fit_kink_count"]) for row in points])
        inset.plot(x, y, color="black", linewidth=0.65)
        inset.plot(x, kzm, color="#d7191c", linewidth=0.65)
    inset.set_xscale("log")
    inset.set_yscale("log")
    inset.set_xlim(0.025, 0.25)
    inset.set_ylim(0.7, 9)
    inset.set_xticks([0.025, 0.1, 0.25])
    inset.set_yticks([1, 8])
    inset.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:g}"))
    inset.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:g}"))
    inset.xaxis.set_minor_formatter(NullFormatter())
    inset.yaxis.set_minor_formatter(NullFormatter())
    _ticks(inset, 8.5)
    axis.indicate_inset_zoom(inset, edgecolor="black", linewidth=0.5)
    return _save(figure, workspace, spec)


def run_render_contract(workspace: Path, contract_path: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if set(contract["allowed_adjustments"]) - ALLOWED_ADJUSTMENTS:
        raise ValueError("render contract includes a non-presentation adjustment")
    if contract["locked_fields"]["numeric_values_may_change"] is not False:
        raise ValueError("numeric values must remain locked")
    if contract["locked_fields"]["source_pixels_may_feed_numerics"] is not False:
        raise ValueError("source pixels cannot feed numerics")

    checked_inputs = []
    for item in [*contract["frozen_data"], *contract["source_references"]]:
        path = workspace / item["path"]
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise ValueError(f"frozen input hash mismatch: {item['path']}")
        checked_inputs.append({"path": item["path"], "sha256": actual})

    _style()
    renderers = {
        "MAIN_FIG1": _render_fig1,
        "MAIN_FIG2": _render_fig2,
        "MAIN_FIG3": _render_fig3,
    }
    source_by_id = {
        item["figure_id"]: workspace / item["path"]
        for item in contract["source_references"]
    }
    rendered = []
    for spec in contract["figures"]:
        outputs = renderers[spec["figure_id"]](workspace, spec)
        _comparison_board(
            source_by_id[spec["figure_id"]],
            workspace / spec["output_png"],
            workspace / spec["comparison"],
        )
        rendered.append(
            {
                "figure_id": spec["figure_id"],
                "target_ids": spec["target_ids"],
                "outputs": outputs,
                "comparison": {
                    "path": spec["comparison"],
                    "sha256": sha256_file(workspace / spec["comparison"]),
                },
            }
        )

    result = {
        "schema_version": 1,
        "paper_id": contract["paper_id"],
        "status": "passed",
        "attested_run": contract["created_after_attested_run"],
        "frozen_inputs": checked_inputs,
        "locked_fields": contract["locked_fields"],
        "scientific_regions": contract["scientific_regions"],
        "rendered": rendered,
    }
    output = workspace / contract["check_output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
