#!/usr/bin/env python3
"""Pixel-tune one theory-only figure from its existing independent CSV.

This script is deliberately rendering-only: it cannot evaluate the physical
model and never reads experimental counts.  Source-figure information is
limited to layout/style parameters recorded below.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(os.environ.get("TMPDIR", "/tmp")) / "pragent-2606.30255-matplotlib"),
)
os.environ.setdefault(
    "XDG_CACHE_HOME",
    str(Path(os.environ.get("TMPDIR", "/tmp")) / "pragent-2606.30255-cache"),
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from wigner_model import TARGET_SPECS  # noqa: E402


DPI = 150


@dataclass(frozen=True)
class PixelLayout:
    width_px: int
    height_px: int
    axes_left_px: int
    axes_right_px: int
    axes_top_px: int
    axes_bottom_px: int
    show_legend: bool

    @property
    def subplot_adjust(self) -> dict[str, float]:
        return {
            "left": self.axes_left_px / self.width_px,
            "right": (self.axes_right_px + 1) / self.width_px,
            "top": (self.height_px - self.axes_top_px) / self.height_px,
            "bottom": (self.height_px - self.axes_bottom_px - 1) / self.height_px,
        }


# Axis-spine coordinates were measured from the source-side PDF renders only
# after independent theory generation. They control layout, never curve data.
PIXEL_LAYOUTS = {
    "T-FIG003": PixelLayout(1504, 921, 93, 1488, 14, 708, True),
    "T-FIG004": PixelLayout(1520, 921, 109, 1504, 14, 708, True),
    "T-FIG005A": PixelLayout(1520, 798, 109, 1504, 14, 708, False),
    "T-FIG005B": PixelLayout(1520, 921, 109, 1504, 14, 708, True),
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _render(target_id: str) -> dict[str, Any]:
    spec = TARGET_SPECS[target_id]
    layout = PIXEL_LAYOUTS[target_id]
    data_path = WORKSPACE / "outputs" / "data" / f"{spec.slug}.csv"
    scientific_path = (
        WORKSPACE / "outputs" / "checks" / f"{spec.slug}_scientific.json"
    )
    output_path = WORKSPACE / "outputs" / "figures" / f"{spec.slug}.png"
    scientific = _read_json(scientific_path)
    if scientific.get("status") != "passed":
        raise ValueError(f"scientific prerequisite did not pass for {target_id}")
    if scientific.get("generated_data_provenance") != "independent_numerics":
        raise ValueError(f"generated data provenance is not independent for {target_id}")
    if not data_path.exists():
        raise FileNotFoundError(data_path)

    data = np.genfromtxt(data_path, delimiter=",", names=True)
    expected_columns = {
        "angle_deg",
        "p_abprime",
        "p_bcprime",
        "p_acprime",
        "wigner",
        "violation_limit",
    }
    if set(data.dtype.names or ()) != expected_columns:
        raise ValueError(f"unexpected CSV schema for {target_id}")

    start = time.perf_counter()
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "text.color": "black",
            "axes.edgecolor": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black",
            "axes.linewidth": 0.9,
            "font.size": 12,
            "axes.labelsize": 17,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 10,
        }
    )
    figure, axis = plt.subplots(
        figsize=(layout.width_px / DPI, layout.height_px / DPI),
        dpi=DPI,
    )
    figure.subplots_adjust(**layout.subplot_adjust)
    angle = data["angle_deg"]
    axis.axhspan(
        spec.y_range[0],
        0.0,
        color="#ff0000",
        alpha=0.20,
        zorder=0,
    )
    wigner_line = axis.plot(
        angle,
        data["wigner"],
        color="#0000ff",
        linewidth=1.0,
        label="Calculated Wigner Value",
        zorder=4,
    )[0]
    limit_line = axis.plot(
        angle,
        data["violation_limit"],
        color="#ff0000",
        linewidth=1.0,
        linestyle=":",
        label=f"Theoretical Violation Limit at {spec.violation_limit:.3f}",
        zorder=3,
    )[0]
    p_ab_line = axis.plot(
        angle,
        data["p_abprime"],
        color="#ebbf85",
        linewidth=0.9,
        label=r"Modelled $P_{++}^{\hat a\hat b^\prime}$",
        zorder=2,
    )[0]
    p_bc_line = axis.plot(
        angle,
        data["p_bcprime"],
        color="#c9eb85",
        linewidth=0.9,
        label=r"Modelled $P_{++}^{\hat b\hat c^\prime}$",
        zorder=2,
    )[0]
    p_ac_line = axis.plot(
        angle,
        data["p_acprime"],
        color="#e2a0dd",
        linewidth=0.9,
        label=r"Modelled $P_{++}^{\hat a\hat c^\prime}$",
        zorder=2,
    )[0]

    axis.set_xlim(0.0, 360.0)
    axis.set_ylim(*spec.y_range)
    axis.set_xticks(np.arange(0.0, 361.0, 20.0))
    tick_labels = axis.get_xticklabels()
    if tick_labels:
        tick_labels[0].set_horizontalalignment("left")
        tick_labels[-1].set_horizontalalignment("right")
    axis.set_xlabel(spec.x_label)
    axis.set_ylabel("Wigner Value (1)")
    axis.grid(True, color="#b0b0b0", linewidth=0.65)
    axis.set_axisbelow(True)
    if layout.show_legend:
        axis.legend(
            handles=[wigner_line, limit_line, p_ab_line, p_bc_line, p_ac_line],
            loc="upper center",
            bbox_to_anchor=(0.5, -0.15),
            ncol=3,
            frameon=True,
            columnspacing=1.6,
            handlelength=2.4,
        )

    figure.savefig(output_path, dpi=DPI, facecolor="white")
    plt.close(figure)
    rendering_seconds = time.perf_counter() - start

    check = {
        "schema_version": 1,
        "check": "pixel_tuned_render",
        "paper_id": "2606.30255",
        "target_id": target_id,
        "status": "passed",
        "input_data": str(data_path.relative_to(WORKSPACE)),
        "input_data_provenance": "independent_numerics",
        "scientific_check": str(scientific_path.relative_to(WORKSPACE)),
        "output_figure": str(output_path.relative_to(WORKSPACE)),
        "source_information_used": {
            "role": "layout_and_style_reference_only",
            "curve_coordinates_used": False,
            "experimental_markers_used": False,
            "experimental_error_bars_used": False,
            "width_px": layout.width_px,
            "height_px": layout.height_px,
            "axes_spine_box_pixels": [
                layout.axes_left_px,
                layout.axes_top_px,
                layout.axes_right_px,
                layout.axes_bottom_px,
            ],
            "theory_palette_and_grid_tuned": True,
        },
        "visible_series": [
            "wigner",
            "violation_limit",
            "p_abprime",
            "p_bcprime",
            "p_acprime",
        ],
        "experimental_series_generated": [],
        "rendering_seconds": rendering_seconds,
        "matplotlib": matplotlib.__version__,
    }
    check_path = (
        WORKSPACE / "outputs" / "checks" / f"{spec.slug}_pixel_render.json"
    )
    check_path.write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return check


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(TARGET_SPECS))
    args = parser.parse_args()
    try:
        payload = _render(args.target)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"status": "failed", "target_id": args.target, "error": str(exc)}
            )
        )
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
