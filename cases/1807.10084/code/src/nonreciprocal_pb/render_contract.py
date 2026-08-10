"""Post-run render contracts over immutable numerical arrays.

This module is intentionally outside the isolated numerical command.  It may
adjust presentation only after verifying the frozen dataset hash.  It never
reads a paper image and never changes curve coordinates or physics parameters.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frozen_rows(workspace: Path, target: dict[str, Any]) -> tuple[list[dict[str, str]], str]:
    source = workspace / str(target["source_data"])
    observed_hash = sha256_file(source)
    expected_hash = str(target["source_data_sha256"])
    if observed_hash != expected_hash:
        raise RuntimeError(
            f"render contract refused changed numerical data: expected {expected_hash}, got {observed_hash}"
        )
    with source.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle)), observed_hash


def render_t006(workspace: Path, target: dict[str, Any]) -> dict[str, Any]:
    rows, data_hash = load_frozen_rows(workspace, target)
    width, height = [int(value) for value in target["canvas_pixels"]]
    dpi = int(target["dpi"])
    plt.rcParams.update(
        {
            "font.family": str(target["font_family"]),
            "mathtext.fontset": str(target["math_fontset"]),
            "axes.linewidth": 1.5,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
        }
    )
    figure = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    axis = figure.add_axes(target["axes_rect"])
    for direction, color_key in [(1, "positive"), (-1, "negative")]:
        selected = [row for row in rows if int(row["direction"]) == direction]
        axis.plot(
            [float(row["omega_khz"]) for row in selected],
            [float(row["delta_f_mhz"]) for row in selected],
            color=target["colors"][color_key],
            lw=float(target["line_width"]),
        )
    axis.set_xlim(*target["x_limits"])
    axis.set_ylim(*target["y_limits"])
    axis.set_xticks(target["x_ticks"])
    axis.set_yticks(target["y_ticks"])
    axis.tick_params(labelsize=int(target["tick_font_size"]), width=1.5, length=7, pad=8)
    axis.set_xlabel(r"Angular velocity $\Omega$ (kHz)", fontsize=int(target["label_font_size"]), labelpad=18)
    axis.set_ylabel(
        r"Fizeau drag $\Delta_{\rm F}$ (MHz)",
        fontsize=int(target["label_font_size"]),
        labelpad=float(target["y_label_pad"]),
    )
    annotation_size = int(target["annotation_font_size"])
    arrow_size = int(target["arrow_font_size"])
    annotations = target["annotations"]
    arrow_font = str(target["arrow_font_family"])
    for key, arrow, label in [
        ("positive", "↻", r"$(\Delta_{\rm F}>0)$"),
        ("negative", "↺", r"$(\Delta_{\rm F}<0)$"),
    ]:
        color = target["colors"][key]
        axis.text(
            *annotations[key]["arrow_xy"],
            arrow,
            color=color,
            fontsize=arrow_size,
            fontfamily=arrow_font,
        )
        axis.text(*annotations[key]["label_xy"], label, color=color, fontsize=annotation_size)
    output = workspace / str(target["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=dpi, facecolor="white")
    plt.close(figure)
    if plt.imread(output).shape[:2] != (height, width):
        raise RuntimeError("render contract produced the wrong canvas size")
    return {
        "target_id": "T006",
        "source_data": str(target["source_data"]),
        "source_data_sha256": data_hash,
        "output": str(target["output"]),
        "output_sha256": sha256_file(output),
        "canvas_pixels": [width, height],
        "numerical_arrays_modified": False,
    }


def run_render_contract(config_path: Path) -> dict[str, Any]:
    workspace = config_path.resolve().parents[1]
    contract = json.loads(config_path.read_text(encoding="utf-8"))
    results = [render_t006(workspace, contract["targets"]["T006"])]
    payload = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": contract["paper_id"],
        "channel": contract["channel"],
        "numerical_run_id": contract["numerical_run_id"],
        "source_pixels_used_as_numerical_inputs": False,
        "allowed_adjustments": contract["allowed_adjustments"],
        "forbidden_adjustments": contract["forbidden_adjustments"],
        "targets": results,
    }
    check_path = workspace / "outputs" / "checks" / "render_contract.json"
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
