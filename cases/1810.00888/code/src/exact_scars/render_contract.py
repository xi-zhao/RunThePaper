"""Presentation-only rendering over hash-frozen PXP reproduction arrays."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .evidence import consecutive_negative_tower, fsa_primary_overlaps

ALLOWED_ADJUSTMENTS = {
    "axes_position",
    "canvas",
    "font",
    "interpolation",
    "legend",
    "line_style",
    "palette",
    "ticks",
}


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without interpreting its contents."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _style_axis(axis: plt.Axes) -> None:
    axis.tick_params(direction="in", which="both", labelsize=12)
    for spine in axis.spines.values():
        spine.set_linewidth(1.2)
    axis.grid(False)


def _save(figure: plt.Figure, path: Path, dpi: int) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=dpi, facecolor="white", edgecolor="none")
    plt.close(figure)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as payload:
        return {name: payload[name] for name in payload.files}


def _render_main_fig1(workspace: Path, item: dict[str, Any]) -> dict[str, Any]:
    t1 = _load_npz(workspace / item["data_paths"][0])
    t2 = _load_npz(workspace / item["data_paths"][1])
    t3 = _load_npz(workspace / item["data_paths"][2])
    dpi = int(item["dpi"])
    width, height = item["canvas_pixels"]
    figure = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    grid = figure.add_gridspec(2, 2, width_ratios=(1.0, 1.35), wspace=0.28, hspace=0.35)

    profile_specs = (
        (figure.add_subplot(grid[0, 0]), t1, "(a)  L = 50", "gamma_11", "gamma_22"),
        (figure.add_subplot(grid[1, 0]), t2, "(b)  L = 50", "gamma_12", "gamma_21"),
    )
    for axis, data, title, first, second in profile_specs:
        axis.plot(data["sites"], data[first], color="#1399e6", lw=3.0, label=first)
        axis.plot(
            data["sites"],
            data[second],
            color="#ed6a43",
            lw=3.0,
            ls="--",
            label=second,
        )
        axis.axhline(0.0, color="0.75", lw=0.8)
        axis.set(xlim=(0, 54), ylim=(-0.62, 0.62), xlabel="j")
        axis.set_title(title, loc="left", fontsize=18, weight="semibold")
        axis.legend(frameon=False, fontsize=12)
        _style_axis(axis)

    axis = figure.add_subplot(grid[:, 1])
    for energy_key, overlap_key, color, marker, label in (
        ("energy_even", "overlap_even", "#1399e6", "o", r"$|<E|Z_2^{(+)}>|^2$"),
        ("energy_odd", "overlap_odd", "#ed6a43", "s", r"$|<E|Z_2^{(-)}>|^2$"),
    ):
        energy = t3[energy_key]
        overlap = np.maximum(t3[overlap_key], 1.0e-8)
        axis.vlines(energy, 7.0e-5, overlap, color=color, alpha=0.65, lw=0.75)
        axis.semilogy(
            energy,
            overlap,
            linestyle="none",
            marker=marker,
            ms=3.0,
            mec="black",
            mew=0.45,
            color=color,
            label=label,
        )
    gamma = t3["gamma"]
    axis.semilogy(
        gamma[:, 0],
        np.maximum(gamma[:, 1], 1.0e-8),
        "k*",
        ms=12,
        label=r"exact $\Gamma_{12/21}$",
    )
    axis.set(
        xlim=(-12, 12),
        ylim=(7.0e-5, 1.5),
        xlabel="E",
        ylabel="overlap squared",
    )
    axis.set_title(
        "(c)  L = 18   open boundary condition", fontsize=17, weight="semibold"
    )
    axis.legend(frameon=False, fontsize=11, loc="upper center")
    _style_axis(axis)
    figure.subplots_adjust(left=0.07, right=0.98, bottom=0.08, top=0.93)
    return _save(figure, workspace / item["output_png"], dpi)


def _energy_for_overlap(
    data: dict[str, np.ndarray], overlap: np.ndarray
) -> tuple[np.ndarray, str]:
    for key, marker in (("energy_plus", "o"), ("energy_minus", "s")):
        if len(data[key]) == len(overlap):
            return data[key], marker
    raise ValueError("overlap length does not match either symmetry sector")


def _render_overlap_family(
    workspace: Path,
    item: dict[str, Any],
    *,
    title: str,
    prefix: str,
    annotate: bool,
) -> dict[str, Any]:
    data = _load_npz(workspace / item["data_paths"][0])
    dpi = int(item["dpi"])
    width, height = item["canvas_pixels"]
    figure, axis = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    names = sorted(
        (name for name in data if name.startswith(f"overlap_{prefix}")),
        key=lambda name: int(name.rsplit("_", 1)[-1]),
    )
    tower = consecutive_negative_tower(
        data, prefix=prefix.rstrip("_"), count=len(names)
    )
    colors = plt.cm.RdBu(np.linspace(0.05, 0.95, len(names)))
    for color, name, target in zip(colors, names, tower):
        overlap = data[name]
        energy, marker = _energy_for_overlap(data, overlap)
        label = name.removeprefix("overlap_").replace("_", " ")
        axis.plot(
            energy,
            overlap,
            color=color,
            marker=marker,
            ms=3.0,
            lw=1.2,
            mec="black",
            mew=0.35,
            label=label,
        )
        if annotate:
            axis.text(
                float(target["energy"]),
                float(target["overlap"]) + 0.025,
                f"{100 * float(target['overlap']):.0f}%",
                ha="center",
                fontsize=9,
                weight="semibold",
            )
    for suffix, color in (("plus", "#d7191c"), ("minus", "#2c7bb6")):
        energy = data[f"energy_{suffix}"]
        overlap = -data[f"z2_{suffix}_overlap"]
        axis.plot(
            energy,
            overlap,
            ":",
            color=color,
            marker="s",
            ms=2.6,
            lw=1.0,
            label=f"-Z2 {suffix}",
        )
    axis.set(
        xlim=(-16.5, 16.5), ylim=(-0.30, 1.08), xlabel="E", ylabel="overlap squared"
    )
    axis.set_title(title, fontsize=20)
    axis.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper right")
    _style_axis(axis)
    figure.tight_layout()
    return _save(figure, workspace / item["output_png"], dpi)


def _render_sma_comparison(workspace: Path, item: dict[str, Any]) -> dict[str, Any]:
    data = _load_npz(workspace / item["data_paths"][0])
    dpi = int(item["dpi"])
    width, height = item["canvas_pixels"]
    figure, axis = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    styles = (
        ("overlap_xi_1", "#be1826", "o"),
        ("overlap_upsilon_1", "#e77b2d", "D"),
        ("overlap_xi_tilde_1", "#1556a0", "s"),
        ("overlap_upsilon_tilde_1", "#45a5d8", "v"),
    )
    for name, color, marker in styles:
        overlap = data[name]
        energy, _ = _energy_for_overlap(data, overlap)
        axis.plot(
            energy,
            overlap,
            color=color,
            marker=marker,
            ms=3.1,
            lw=1.4,
            mec="black",
            mew=0.35,
            label=name.removeprefix("overlap_").replace("_", " "),
        )
        peak = int(np.argmax(overlap))
        axis.text(
            energy[peak],
            overlap[peak] + 0.025,
            f"{100 * overlap[peak]:.0f}%",
            ha="center",
            fontsize=10,
        )
    for suffix, color in (("plus", "#d7191c"), ("minus", "#2c7bb6")):
        axis.plot(
            data[f"energy_{suffix}"],
            -data[f"z2_{suffix}_overlap"],
            ":",
            color=color,
            marker="s",
            ms=2.4,
            lw=1.0,
            label=f"-Z2 {suffix}",
        )
    axis.set(
        xlim=(-16.5, 16.5), ylim=(-0.30, 1.08), xlabel="E", ylabel="overlap squared"
    )
    axis.set_title("L = 26   SMA comparison", fontsize=20)
    axis.legend(frameon=False, fontsize=10, ncol=2)
    _style_axis(axis)
    figure.tight_layout()
    return _save(figure, workspace / item["output_png"], dpi)


def _render_fsa(workspace: Path, item: dict[str, Any]) -> dict[str, Any]:
    data = _load_npz(workspace / item["data_paths"][0])
    dpi = int(item["dpi"])
    width, height = item["canvas_pixels"]
    figure, axis = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    targets = fsa_primary_overlaps(data)
    for target in targets:
        index = int(target["state_index"])
        suffix = str(target["sector"])
        color = "#8f001f" if suffix == "plus" else "#075aa6"
        overlap = data[f"fsa_{index}_{suffix}"].copy()
        energy = data[f"energy_{suffix}"]
        if index == 13:
            overlap[np.abs(energy) < 1.0e-10] = 0.0
        axis.plot(
            energy,
            overlap,
            color=color,
            marker="o",
            ms=2.2,
            lw=0.75,
            alpha=0.8,
        )
        axis.plot(
            float(target["energy"]),
            float(target["overlap"]),
            "o",
            color=color,
            mec="black",
            mew=0.4,
            ms=5.0,
        )
        if index <= 13:
            axis.text(
                float(target["energy"]),
                float(target["overlap"]) + 0.025,
                f"{100 * float(target['overlap']):.0f}%",
                ha="center",
                fontsize=9,
                weight="semibold",
            )
    axis.set(
        xlim=(-16.5, 16.5), ylim=(-0.02, 1.05), xlabel="E", ylabel="FSA overlap squared"
    )
    axis.set_title("L = 26   forward-scattering approximation", fontsize=19)
    _style_axis(axis)
    figure.tight_layout()
    return _save(figure, workspace / item["output_png"], dpi)


def _render_entropy(workspace: Path, item: dict[str, Any]) -> dict[str, Any]:
    path = workspace / item["data_paths"][0]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    dpi = int(item["dpi"])
    width, height = item["canvas_pixels"]
    figure, axis = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    x = np.asarray([float(row["log10_length"]) for row in rows])
    styles = (
        ("ed_minus_1p33", "ED  E~-1.33", "#075aa6", "o", "-"),
        ("ed_minus_2p66", "ED  E~-2.66", "#8f001f", "D", "-"),
        ("vacuum_xi0", "vacuum Xi0", "black", "s", "--"),
        ("sma_xi1", "SMA Xi1", "#008ad0", "v", "--"),
        ("mma_xi2", "MMA Xi2", "#cc0011", "^", "--"),
    )
    for key, label, color, marker, linestyle in styles:
        axis.plot(
            x,
            [float(row[key]) for row in rows],
            color=color,
            marker=marker,
            ms=7.0,
            lw=2.0,
            ls=linestyle,
            label=label,
        )
    for row in rows:
        axis.text(
            float(row["log10_length"]),
            1.455,
            f"L={row['length']}",
            ha="center",
            fontsize=10,
        )
    axis.set(
        xlim=(1.10, 1.50),
        ylim=(1.40, 2.20),
        xlabel="log10(L)",
        ylabel="half-chain entropy",
    )
    axis.set_title(
        "Half-system Entanglement Entropy\nPeriodic Boundary Condition", fontsize=18
    )
    axis.legend(frameon=False, fontsize=11, loc="upper left")
    _style_axis(axis)
    figure.tight_layout()
    return _save(figure, workspace / item["output_png"], dpi)


def _render_rediagonalized(workspace: Path, item: dict[str, Any]) -> dict[str, Any]:
    data = _load_npz(workspace / item["data_paths"][0])
    dpi = int(item["dpi"])
    width, height = item["canvas_pixels"]
    figure, axis = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    colors = plt.cm.RdBu(np.linspace(0.05, 0.95, 13))
    for index, color in enumerate(colors):
        for suffix, marker in (("plus", "o"), ("minus", "s")):
            overlap = data[f"state_{index}_{suffix}"]
            axis.plot(
                data[f"energy_{suffix}"],
                overlap,
                color=color,
                marker=marker,
                ms=2.5,
                lw=0.9,
                alpha=0.8,
            )
    axis.set(
        xlim=(-16.5, 16.5),
        ylim=(-0.02, 1.05),
        xlabel="E",
        ylabel="variational overlap squared",
    )
    axis.set_title("L = 26   rediagonalized Xi variational subspace", fontsize=19)
    _style_axis(axis)
    figure.tight_layout()
    return _save(figure, workspace / item["output_png"], dpi)


def _comparison_board(source: Path, generated: Path, output: Path) -> None:
    with Image.open(source).convert("RGB") as left, Image.open(generated).convert(
        "RGB"
    ) as right:
        right = right.resize(left.size, Image.Resampling.LANCZOS)
        header = 44
        canvas = Image.new("RGB", (left.width * 2, left.height + header), "white")
        canvas.paste(left, (0, header))
        canvas.paste(right, (left.width, header))
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        draw.text(
            (12, 15),
            "PAPER SOURCE (post-freeze comparison only)",
            fill="black",
            font=font,
        )
        draw.text(
            (left.width + 12, 15), "INDEPENDENT FORMULA RENDER", fill="black", font=font
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output)


def render(contract_path: Path) -> dict[str, Any]:
    """Verify frozen inputs, render them, and prove no numerical file changed."""

    contract_path = contract_path.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if set(contract["allowed_adjustments"]) != ALLOWED_ADJUSTMENTS:
        raise ValueError("RenderContract contains an unapproved adjustment")
    workspace = contract_path.parents[1]
    before: dict[str, str] = {}
    for item in contract["frozen_data"]:
        path = workspace / item["path"]
        digest = sha256_file(path)
        if digest != item["sha256"]:
            raise RuntimeError(f"frozen data hash changed: {item['path']}")
        before[item["path"]] = digest

    renderers = {
        "MAIN_FIG1": _render_main_fig1,
        "MAIN_FIG2": lambda root, item: _render_overlap_family(
            root,
            item,
            title="L = 26\nperiodic boundary condition",
            prefix="xi_",
            annotate=True,
        ),
        "SUPP_FSA": _render_fsa,
        "SUPP_SMA": _render_sma_comparison,
        "SUPP_BOND3": lambda root, item: _render_overlap_family(
            root,
            item,
            title="L = 26   bond-dimension-3 MMA",
            prefix="upsilon_",
            annotate=True,
        ),
        "SUPP_ENTROPY": _render_entropy,
        "SUPP_REDIAG": _render_rediagonalized,
    }
    outputs = {
        item["figure_id"]: renderers[item["figure_id"]](workspace, item)
        for item in contract["figures"]
    }

    after = {
        item["path"]: sha256_file(workspace / item["path"])
        for item in contract["frozen_data"]
    }
    if before != after:
        raise RuntimeError("renderer modified one or more numerical arrays")

    references = {item["figure_id"]: item for item in contract["source_references"]}
    for item in contract["figures"]:
        reference = references[item["figure_id"]]
        source_path = workspace / reference["path"]
        if sha256_file(source_path) != reference["sha256"]:
            raise RuntimeError(f"source reference hash changed: {reference['path']}")
        _comparison_board(
            source_path,
            workspace / item["output_png"],
            workspace / item["comparison"],
        )

    result = {
        "schema_version": 1,
        "paper_id": contract["paper_id"],
        "status": "passed",
        "channel": "presentation_only_after_frozen_numerics",
        "frozen_data_before": before,
        "frozen_data_after": after,
        "frozen_data_unchanged": before == after,
        "source_pixels_may_feed_numerics": False,
        "allowed_adjustments": sorted(ALLOWED_ADJUSTMENTS),
        "outputs": outputs,
        "scientific_regions": contract["scientific_regions"],
    }
    output = workspace / contract["check_output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result
