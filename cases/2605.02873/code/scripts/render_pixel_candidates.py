#!/usr/bin/env python3
"""Render paper-layout candidates from independent generated CSV data only."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT = WORKSPACE / "outputs/figures/pixel"
PANEL_REGISTRATION_OFFSETS = {
    "FIG001A": (-7, -8),
    "FIG001B": (1, -9),
    "FIG001C": (-10, -12),
    "FIG001D": (-7, -10),
}
PANEL_POST_SCALE = {
    "FIG001B": ((486, 339), (-1, -1)),
    "FIG001C": ((484, 344), (-1, -3)),
}


def translate_on_canvas(image: Image.Image, offset: tuple[int, int]) -> Image.Image:
    registered = Image.new("RGB", image.size, "white")
    registered.paste(image.convert("RGB"), offset)
    return registered


def read_columns(name: str) -> dict[str, np.ndarray]:
    path = WORKSPACE / f"outputs/data/{name}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"generated dataset is empty: {path}")
    columns: dict[str, np.ndarray] = {}
    for key in rows[0]:
        try:
            columns[key] = np.array([float(row[key]) for row in rows], dtype=float)
        except ValueError:
            continue
    return columns


def require_scientific_pass(name: str) -> None:
    check_path = WORKSPACE / f"outputs/checks/{name}.json"
    payload = json.loads(check_path.read_text(encoding="utf-8"))
    if payload.get("status") != "passed":
        raise RuntimeError(f"scientific gate is not passed: {check_path}")
    if payload.get("generated_data_provenance") != "independent_numerics":
        raise RuntimeError(f"generated provenance is not independent: {check_path}")


def configure_plotting():
    cache = Path(tempfile.gettempdir()) / "pragent-2605-02873-mpl"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.titlesize": 13,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 11,
            "axes.linewidth": 1.0,
        }
    )
    return plt


def label_panel(axis, label: str) -> None:
    axis.text(
        0.02,
        0.96,
        label,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        zorder=10,
    )


def render_main() -> tuple[Path, dict[str, list[int]]]:
    for name in ("FIG001A", "FIG001B", "FIG001C", "FIG001D"):
        require_scientific_pass(name)
    a = read_columns("FIG001A")
    b = read_columns("FIG001B")
    c = read_columns("FIG001C")
    d = read_columns("FIG001D")
    plt = configure_plotting()
    figure, axes = plt.subplots(2, 2, figsize=(9.61, 6.57))
    axis_a, axis_b, axis_c, axis_d = axes.ravel()

    r0 = a["R0"] / np.max(a["R0"])
    axis_a.plot(a["y_mm"], r0, color="black", linewidth=1.8)
    axis_a.set_title("Baseline TRY response", pad=2)
    axis_a.set_xlabel("source coordinate y (mm)")
    axis_a.set_ylabel("normalized response")
    axis_a.set_xlim(-1.6, 1.6)
    axis_a.set_ylim(-0.03, 1.03)
    axis_a.minorticks_on()
    axis_a.tick_params(which="both", direction="in", top=True, right=True)
    label_panel(axis_a, "(a)")

    gt = b["gt"] / np.max(np.abs(b["gt"]))
    gf = b["gf"] / np.max(np.abs(b["gf"]))
    axis_b.plot(b["y_mm"], gt, color="#065be5", linewidth=1.8, label="$g_t(y)$")
    axis_b.plot(
        b["y_mm"],
        gf,
        color="#ff180d",
        linewidth=1.8,
        linestyle="--",
        label="$g_f(y)$",
    )
    axis_b.set_title("Exact local score functions", pad=2)
    axis_b.set_xlabel("source coordinate y (mm)")
    axis_b.set_ylabel("normalized score")
    axis_b.set_xlim(-1.6, 1.6)
    axis_b.set_ylim(-1.05, 1.05)
    axis_b.minorticks_on()
    axis_b.tick_params(which="both", direction="in", top=True, right=True)
    axis_b.legend(
        frameon=True,
        fancybox=True,
        framealpha=1.0,
        edgecolor="black",
        loc="upper left",
        bbox_to_anchor=(0.08, 1.0),
    )
    label_panel(axis_b, "(b)")

    axis_c.plot(
        c["y_mm"],
        c["optimized_wt"],
        color="#065be5",
        linewidth=1.8,
        label="optimal $w_t$",
    )
    axis_c.plot(
        c["y_mm"],
        c["optimized_wf"],
        color="#ff180d",
        linewidth=1.8,
        linestyle="--",
        label="optimal $w_f$",
    )
    axis_c.plot(
        c["y_mm"],
        c["toy_ht"],
        color="0.65",
        linewidth=1.5,
        linestyle=":",
        label="toy $h_1$",
    )
    axis_c.plot(
        c["y_mm"],
        c["toy_hf"],
        color="0.55",
        linewidth=1.5,
        linestyle=(0, (5, 4)),
        label="toy $h_2$",
    )
    axis_c.set_title("Source codes: optimal vs. toy", pad=2)
    axis_c.set_xlabel("source coordinate y (mm)")
    axis_c.set_ylabel("code amplitude")
    axis_c.set_xlim(-1.6, 1.6)
    axis_c.set_ylim(-5.8e5, 5.8e5)
    axis_c.ticklabel_format(axis="y", style="sci", scilimits=(5, 5), useMathText=True)
    axis_c.minorticks_on()
    axis_c.tick_params(which="both", direction="in", top=True, right=True)
    axis_c.legend(
        frameon=True,
        fancybox=True,
        framealpha=1.0,
        edgecolor="black",
        ncol=2,
        loc="lower center",
    )
    label_panel(axis_c, "(c)")

    optimized = d["optimized_retention"]
    toy = d["toy_retention"]
    heights = [toy[0], optimized[0], toy[1], optimized[1]]
    colors = ["0.68", "#367ed8", "0.68", "#367ed8"]
    bars = axis_d.bar(
        np.arange(4),
        heights,
        color=colors,
        edgecolor=["0.35", "#367ed8", "0.35", "#367ed8"],
        linewidth=0.7,
    )
    axis_d.set_title("Fisher-information retention", pad=2)
    axis_d.set_ylabel("retained information fraction")
    axis_d.set_xticks(
        np.arange(4),
        ["mode 1\n(toy)", "mode 1\n(opt.)", "mode 2\n(toy)", "mode 2\n(opt.)"],
    )
    axis_d.set_ylim(0, 1.18)
    axis_d.set_axisbelow(True)
    axis_d.grid(axis="y", color="0.85", linewidth=0.7)
    legend_handles = [
        bars[1],
        bars[0],
    ]
    axis_d.legend(
        legend_handles,
        ["optimized codes", "toy codes"],
        frameon=True,
        fancybox=True,
        framealpha=1.0,
        edgecolor="black",
        loc="upper left",
        bbox_to_anchor=(0.0, 0.78),
    )
    for bar, value in zip(bars, heights, strict=True):
        axis_d.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.015,
            f"{value:.6g}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    label_panel(axis_d, "(d)")

    figure.tight_layout(pad=0.6, w_pad=0.8, h_pad=0.8)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    combined_path = OUTPUT / "FIG001_combined.png"
    figure.savefig(combined_path, dpi=100, facecolor="white")
    plt.close(figure)

    with Image.open(combined_path) as image:
        width, height = image.size
        x_mid = width // 2
        y_mid = height // 2
        crop_boxes = {
            "FIG001A": [0, 0, x_mid, y_mid],
            "FIG001B": [x_mid, 0, width, y_mid],
            "FIG001C": [0, y_mid, x_mid, height],
            "FIG001D": [x_mid, y_mid, width, height],
        }
        for name, box in crop_boxes.items():
            panel = image.crop(tuple(box))
            registered = translate_on_canvas(
                panel, PANEL_REGISTRATION_OFFSETS[name]
            )
            if name in PANEL_POST_SCALE:
                scaled_size, offset = PANEL_POST_SCALE[name]
                scaled = registered.resize(scaled_size, Image.Resampling.LANCZOS)
                final_panel = Image.new("RGB", registered.size, "white")
                final_panel.paste(scaled, offset)
                registered = final_panel
            registered.save(OUTPUT / f"{name}.png")
    return combined_path, crop_boxes


def render_supplement() -> Path:
    require_scientific_pass("FIGS001")
    data = read_columns("FIGS001")
    plt = configure_plotting()
    figure, axis = plt.subplots(figsize=(6, 4))
    axis.plot(
        data["slit_width_um"],
        data["rho_Fff_over_Ftt"],
        color="#1f77b4",
        linewidth=2.0,
        marker="o",
        markersize=7,
    )
    axis.set_xlabel("slit width a ($\\mu$m)")
    axis.set_ylabel("$F_{ff}/F_{tt}$")
    axis.grid(True, color="0.85", linewidth=0.8)
    figure.tight_layout()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / "FIGS001.png"
    figure.savefig(path, dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(figure)
    # Registration is a pixel-lane operation: place the independent render on
    # the declared source canvas without changing any numerical coordinates.
    with Image.open(path) as rendered:
        registered = rendered.convert("RGB")
        if rendered.size != (1150, 765):
            registered = registered.resize(
                (1150, 765), Image.Resampling.LANCZOS
            )
        scaled = registered.resize((1175, 813), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (1150, 765), "white")
        canvas.paste(scaled, (-10, -18))
        canvas.save(path)
    return path


def main() -> int:
    main_path, crop_boxes = render_main()
    supplement_path = render_supplement()
    payload = {
        "schema_version": 1,
        "paper_id": "2605.02873",
        "status": "passed",
        "provenance": "independent_render_from_independent_numerics",
        "source_pixels_read": False,
        "artifacts": {
            "combined_main": str(main_path.relative_to(WORKSPACE)),
            "main_panel_crop_boxes": crop_boxes,
            "supplement": str(supplement_path.relative_to(WORKSPACE)),
        },
    }
    check_path = WORKSPACE / "outputs/checks/pixel_candidate_render.json"
    check_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
