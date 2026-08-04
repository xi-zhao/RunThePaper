#!/usr/bin/env python3
"""Render the reduced Fig.-8 target from frozen independent benchmark data."""

from __future__ import annotations

import csv
import json
import os
import shutil
from pathlib import Path

MPL_CONFIG = Path(os.environ.get("MPLCONFIGDIR", ".matplotlib"))
MPL_CONFIG.mkdir(parents=True, exist_ok=True)
FONT_CACHE_TARGET = MPL_CONFIG / "fontlist-v390.json"
if not FONT_CACHE_TARGET.exists():
    shutil.copyfile(Path("config/fontlist-v390.json"), FONT_CACHE_TARGET)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    contract = json.loads(Path("render_contract.json").read_text(encoding="utf-8"))
    style = contract["render_parameters"]["T003"]
    data_path = next(
        Path(row["path"])
        for row in contract["numerical_artifacts"]
        if row["path"].endswith("T003_sqetch_benchmark.csv")
    )
    with data_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    codes = sorted({row["code_id"] for row in rows}, key=lambda code: int(code.rsplit("-", 1)[1]))
    methods = ["sqetch", "full_nullspace_rref"]
    values = {
        (row["code_id"], row["method"]): float(row["projected_seconds"]) / 86400.0
        for row in rows
    }
    canvas = style["canvas"]
    typography = style["typography"]
    palette = style["palette"]
    line_styles = style["line_styles"]
    plt.rcParams.update(
        {
            "font.family": typography["font_family"],
            "font.size": typography["font_size"],
        }
    )
    figure = plt.figure(
        figsize=(canvas["width_inches"], canvas["height_inches"]),
        dpi=canvas["dpi"],
        facecolor=canvas["facecolor"],
    )
    axes = figure.add_axes(style["axes_positions"]["main"])
    positions = np.arange(len(codes), dtype=float)
    width = 0.34
    bar_style = line_styles["bars"]
    grid_style = line_styles["grid"]
    for index, method in enumerate(methods):
        offset = (index - 0.5) * width
        axes.bar(
            positions + offset,
            [values[(code, method)] for code in codes],
            width=width,
            color=palette[method],
            edgecolor=palette["axis"],
            linewidth=bar_style["line_width"],
            alpha=bar_style["alpha"],
            label="sQetch" if method == "sqetch" else "full-nullspace RREF",
        )
    axes.set_yscale("log")
    axes.set_xticks(positions, [f"n={code.rsplit('-', 1)[1]}" for code in codes])
    axes.set_ylabel("Projected wall time for $10^5$ trials (days)")
    axes.set_xlabel("Independently reconstructed mitten code")
    axes.grid(
        axis="y",
        which="both",
        alpha=grid_style["alpha"],
        linewidth=grid_style["line_width"],
        linestyle=grid_style["line_style"],
    )
    axes.legend(frameon=False)
    axes.set_title("Reduced-scale Algorithm 1 benchmark")
    output = Path(contract["rendered_outputs"]["T003"][0])
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=canvas["dpi"], facecolor=canvas["facecolor"])
    plt.close(figure)


if __name__ == "__main__":
    main()
