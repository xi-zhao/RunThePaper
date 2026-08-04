#!/usr/bin/env python3
"""Render one target panel with the source figure's publication geometry.

This is a style-only pixel-lane action. It reads an already accepted
target-specific CSV and never changes generated scientific data.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))
os.environ.setdefault(
    "MPLCONFIGDIR", str(WORKSPACE / "outputs" / ".matplotlib-cache")
)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import LogFormatterSciNotation, LogLocator  # noqa: E402

from trotter_bounds import TARGET_SPECS, target_slug, write_json  # noqa: E402


PANEL_WIDTH_PX = 2160
PANEL_HEIGHT_PX = 1570
DPI = 300
# These normalized margins reproduce a source-panel crop whose source axes are
# 1920x1235 px with 144 px left, 96 px right, 152 px top, and 183 px bottom.
AXES_RECT = (
    144.0 / PANEL_WIDTH_PX,
    183.0 / PANEL_HEIGHT_PX,
    1920.0 / PANEL_WIDTH_PX,
    1235.0 / PANEL_HEIGHT_PX,
)


def read_rows(path: Path) -> list[dict[str, int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append(
                {
                    key: int(row[key])
                    for key in (
                        "M",
                        "N_analytic",
                        "N_min",
                        "g_analytic",
                        "g_min",
                    )
                }
            )
    if not rows:
        raise ValueError(f"empty target dataset: {path}")
    return rows


def method_label_parts(method: str) -> tuple[str, str]:
    order = "1" if method in {"det1", "ran1"} else "2"
    family = r"\mathrm{det}" if method in {"det1", "det2"} else r"\mathrm{ran}"
    return order, family


def render(path: Path, spec, rows: list[dict[str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(
        figsize=(PANEL_WIDTH_PX / DPI, PANEL_HEIGHT_PX / DPI),
        dpi=DPI,
        facecolor="white",
    )
    axis = fig.add_axes(AXES_RECT)
    m_values = [row["M"] for row in rows]
    order, family = method_label_parts(spec.method)
    styles = (
        (
            "N_analytic",
            rf"$N^{{analytic}}_{{{order},{family}}}$",
            "--",
            "s",
            5,
            "#1b9e77",
        ),
        (
            "N_min",
            rf"$N^{{min}}_{{{order},{family}}}$",
            "--",
            "x",
            5,
            "#66a61e",
        ),
        (
            "g_analytic",
            rf"$g^{{analytic}}_{{{order},{family}}}$",
            ":",
            "o",
            4,
            "#6a3d9a",
        ),
        (
            "g_min",
            rf"$g^{{min}}_{{{order},{family}}}$",
            ":",
            "D",
            4,
            "#7570b3",
        ),
    )
    for key, label, linestyle, marker, markersize, color in styles:
        axis.plot(
            m_values,
            [row[key] for row in rows],
            linestyle=linestyle,
            marker=marker,
            linewidth=1.2,
            markersize=markersize,
            color=color,
            label=label,
        )

    axis.set_title(spec.title, fontsize=18)
    axis.set_xlabel("Number of Liouvillian Terms, $M$", fontsize=16)
    axis.set_xticks(m_values)
    axis.tick_params(axis="both", labelsize=13)
    axis.set_yscale("log")
    axis.yaxis.set_major_locator(LogLocator(base=10, numticks=8))
    axis.yaxis.set_major_formatter(LogFormatterSciNotation(base=10))
    axis.legend(loc="upper left", fontsize=11, frameon=True)
    axis.grid(alpha=0.3, which="both")
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(TARGET_SPECS))
    args = parser.parse_args()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    spec = TARGET_SPECS[args.target]
    slug = target_slug(args.target)
    data_path = WORKSPACE / "outputs" / "data" / f"{slug}.csv"
    output_path = (
        WORKSPACE / "outputs" / "figures" / "pixel" / f"{slug}_panel.png"
    )
    check_path = (
        WORKSPACE
        / "outputs"
        / "checks"
        / "pixel_render"
        / f"{slug}.json"
    )
    rows = read_rows(data_path)
    render(output_path, spec, rows)
    payload = {
        "schema_version": 1,
        "status": "passed",
        "target_id": args.target,
        "action": "style_only_pixel_render",
        "scientific_data_changed": False,
        "input_data": f"outputs/data/{slug}.csv",
        "output_figure": f"outputs/figures/pixel/{slug}_panel.png",
        "output_size_pixels": [PANEL_WIDTH_PX, PANEL_HEIGHT_PX],
        "timing": {
            "wall_seconds": time.perf_counter() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu,
        },
    }
    write_json(check_path, payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
