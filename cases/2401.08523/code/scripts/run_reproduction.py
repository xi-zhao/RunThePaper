#!/usr/bin/env python3
"""Generate all numerical panels of arXiv:2401.08523v2 from formulas.

The generation path reads only the explicit JSON configuration and the local
science module.  Original paper figures are intentionally absent from this
script so reference pixels cannot influence data or rendering.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / ".cache" / "matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(WORKSPACE))

from src.fermionic_phase_space import (  # noqa: E402
    covariance_determinants,
    crossing_points,
    entropy_lower_bound,
    fermi_dirac_occupation,
    phase_space_bodies,
    renyi_entropy,
    thermal_loss_output_occupation,
)


CONFIG_PATH = WORKSPACE / "config" / "paper_exact.json"
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"

PURPLE = "#241478"
TEAL = "#278f8d"
GREEN = "#83cb70"
BLUE = "#356a9d"
RED = "#e66d7b"
BLUE_BG = "#eff2f6"
RED_BG = "#fcf3f4"


def _load_config() -> dict[str, object]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _write_csv(path: Path, columns: list[str], arrays: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in zip(*arrays, strict=True):
            writer.writerow([f"{float(value):.16g}" for value in row])


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _numeric_tick(value: float, _position: int) -> str:
    if abs(value) < 5e-13:
        value = 0.0
    return f"{value:g}"


def _set_font_style(base_size: float) -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": base_size,
            "mathtext.fontset": "custom",
            "mathtext.rm": "Arial",
            "mathtext.it": "Arial:italic",
            "mathtext.bf": "Arial:bold",
            "axes.linewidth": 0.8,
            "axes.edgecolor": "#666666",
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "savefig.facecolor": "white",
        }
    )


def _save_figure(fig: plt.Figure, stem: str, dpi: int) -> dict[str, str]:
    paths: dict[str, str] = {}
    for suffix in ("png", "pdf", "svg"):
        path = FIGURE_DIR / f"{stem}.{suffix}"
        fig.savefig(path, dpi=dpi, facecolor="white")
        if suffix == "svg":
            lines = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
        paths[suffix] = str(path.relative_to(WORKSPACE))
    plt.close(fig)
    return paths


def _temperature_annotations(ax: plt.Axes, y: float) -> None:
    ax.text(0.05, y, r"$T\to0^{+}$", color=BLUE, transform=ax.transAxes, fontsize=10.2)
    ax.text(0.34, y, r"$T\to\infty^{+}$", color=BLUE, transform=ax.transAxes, fontsize=10.2)
    ax.text(0.55, y, r"$T\to\infty^{-}$", color=RED, transform=ax.transAxes, fontsize=10.2)
    ax.text(0.83, y, r"$T\to0^{-}$", color=RED, transform=ax.transAxes, fontsize=10.2)


def _style_occupation_axis(ax: plt.Axes, y_limits: tuple[float, float], y_ticks: list[float]) -> None:
    ax.axvspan(0.0, 0.5, color=BLUE_BG, zorder=0)
    ax.axvspan(0.5, 1.0, color=RED_BG, zorder=0)
    ax.axvline(0.5, color="#222222", linewidth=0.75, linestyle=(0, (5, 5)), zorder=1)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(*y_limits)
    ax.set_xticks(np.linspace(0.0, 1.0, 6))
    ax.set_yticks(y_ticks)
    ax.xaxis.set_major_formatter(FuncFormatter(_numeric_tick))
    ax.yaxis.set_major_formatter(FuncFormatter(_numeric_tick))
    ax.grid(True, color="#2b2b2b", linewidth=0.65, linestyle=(0, (1, 4)), alpha=0.82)
    ax.set_axisbelow(True)
    ax.set_xlabel(r"$\langle n\rangle$", fontsize=12.0, labelpad=8)
    ax.tick_params(labelsize=10.0, pad=3)


def _render_figure_1(x: np.ndarray, occupation: np.ndarray, dpi: int, canvas: list[int]) -> dict[str, str]:
    _set_font_style(14.0)
    width, height = canvas
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    ax = fig.add_axes([0.123, 0.174, 0.861, 0.792])
    ax.axvspan(-6.0, 0.0, color=RED_BG, zorder=0)
    ax.axvspan(0.0, 6.0, color=BLUE_BG, zorder=0)
    ax.plot(x, occupation, color="#0d090a", linewidth=2.7, zorder=3)
    ax.axvline(0.0, color="#222222", linewidth=0.8, linestyle=(0, (5, 5)), zorder=1)
    ax.plot(0.0, 0.5, marker="o", markersize=6.7, markerfacecolor="white", markeredgecolor="#111111", markeredgewidth=1.5, zorder=4)
    ax.set_xlim(-6.0, 6.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks(np.arange(-6.0, 6.1, 2.0))
    ax.set_yticks(np.linspace(0.0, 1.0, 6))
    ax.yaxis.set_major_formatter(FuncFormatter(_numeric_tick))
    ax.grid(True, color="#222222", linewidth=0.75, linestyle=(0, (1, 4)), alpha=0.88)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=13.5, pad=3)
    ax.set_xlabel(r"$\epsilon/T$", fontsize=16.0, labelpad=9)
    ax.set_ylabel(r"$\langle n\rangle$", fontsize=16.0, labelpad=6)
    ax.text(-5.62, 0.875, r"$T\to0^{-}$", color=RED, fontsize=14.0)
    ax.text(-1.72, 0.475, r"$T\to\infty^{-}$", color=RED, fontsize=14.0)
    ax.text(0.30, 0.475, r"$T\to\infty^{+}$", color=BLUE, fontsize=14.0)
    ax.text(4.36, 0.075, r"$T\to0^{+}$", color=BLUE, fontsize=14.0)
    return _save_figure(fig, "figure_1_fermi_dirac", dpi)


def _render_figure_2(
    n: np.ndarray,
    moments: object,
    entropies: dict[str, np.ndarray],
    renyi_curves: dict[float, np.ndarray],
    dpi: int,
    canvas: list[int],
) -> dict[str, str]:
    _set_font_style(10.0)
    width, height = canvas
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    axes = [
        fig.add_axes([0.059, 0.174, 0.272, 0.736]),
        fig.add_axes([0.393, 0.174, 0.272, 0.736]),
        fig.add_axes([0.726, 0.174, 0.271, 0.736]),
    ]

    ax = axes[0]
    _style_occupation_axis(ax, (-1.25, 0.25), [-1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25])
    ax.plot(n, moments.glauber_p, color=PURPLE, linewidth=2.0)
    ax.plot(n, moments.wigner_w, color=TEAL, linewidth=2.0)
    ax.plot(n, moments.husimi_q, color=GREEN, linewidth=2.0)
    ax.axhline(-1.0, color="#111111", linewidth=1.25, linestyle=(0, (1, 3)))
    ax.axhline(-0.25, color="#111111", linewidth=1.25, linestyle=(0, (1, 3)))
    for x0, y0 in ((0.25, -0.0625), (0.75, -0.0625)):
        ax.plot(x0, y0, marker="^", markersize=5.8, markerfacecolor="#b8b8b8", markeredgecolor="#111111", markeredgewidth=1.0, zorder=5)
    ax.plot(0.5, -0.25, marker="D", markersize=5.2, markerfacecolor="#b8b8b8", markeredgecolor="#111111", markeredgewidth=1.0, zorder=5)
    ax.plot([0.0, 1.0], [-0.25, -0.25], linestyle="none", marker="o", markersize=5.2, markerfacecolor="white", markeredgecolor=TEAL, markeredgewidth=1.3, zorder=5)
    ax.plot(1.0, -1.0, marker="o", markersize=5.2, markerfacecolor="white", markeredgecolor=PURPLE, markeredgewidth=1.3, zorder=5)
    ax.plot(0.0, -1.0, marker="o", markersize=5.2, markerfacecolor="white", markeredgecolor=GREEN, markeredgewidth=1.3, zorder=5)
    ax.set_ylabel(r"$\det\gamma$", fontsize=12.0, labelpad=5)
    ax.set_title(r"$\mathbf{(a)}$ Second-order moments", fontsize=11.5, pad=6)
    ax.text(0.05, 0.89, r"$\gamma(P)$", color=PURPLE, transform=ax.transAxes, fontsize=11.0)
    ax.text(0.35, 0.89, r"$\gamma(W)$", color=TEAL, transform=ax.transAxes, fontsize=11.0)
    ax.text(0.83, 0.89, r"$\gamma(Q)$", color=GREEN, transform=ax.transAxes, fontsize=11.0)
    _temperature_annotations(ax, 0.05)

    ax = axes[1]
    _style_occupation_axis(ax, (-3.0, 4.5), [-3.0, -1.5, 0.0, 1.5, 3.0, 4.5])
    ax.plot(n, entropies["P"], color=PURPLE, linewidth=2.0)
    ax.plot(n, entropies["W"], color=TEAL, linewidth=2.0)
    ax.plot(n, entropies["Q"], color=GREEN, linewidth=2.0)
    ax.axhline(-1.0, color="#111111", linewidth=1.25, linestyle=(0, (1, 3)))
    ax.axhline(-1.0 + np.log(2.0), color="#111111", linewidth=1.25, linestyle=(0, (1, 3)))
    crossing_entropy = -1.0 + np.log(4.0)
    for x0 in (0.25, 0.75):
        ax.plot(x0, crossing_entropy, marker="^", markersize=5.8, markerfacecolor="#b8b8b8", markeredgecolor="#111111", markeredgewidth=1.0, zorder=5)
    ax.plot(0.5, -1.0 + np.log(2.0), marker="D", markersize=5.2, markerfacecolor="#b8b8b8", markeredgecolor="#111111", markeredgewidth=1.0, zorder=5)
    ax.plot([0.0, 1.0], [-1.0 + np.log(2.0)] * 2, linestyle="none", marker="o", markersize=5.2, markerfacecolor="white", markeredgecolor=TEAL, markeredgewidth=1.3, zorder=5)
    ax.plot(1.0, -1.0, marker="o", markersize=5.2, markerfacecolor="white", markeredgecolor=PURPLE, markeredgewidth=1.3, zorder=5)
    ax.plot(0.0, -1.0, marker="o", markersize=5.2, markerfacecolor="white", markeredgecolor=GREEN, markeredgewidth=1.3, zorder=5)
    ax.set_ylabel(r"$S$", fontsize=12.0, labelpad=5)
    ax.set_title(r"$\mathbf{(b)}$ Entropies", fontsize=11.5, pad=6)
    ax.text(0.05, 0.87, r"$S(P)$", color=PURPLE, transform=ax.transAxes, fontsize=11.0)
    ax.text(0.35, 0.87, r"$S(W)$", color=TEAL, transform=ax.transAxes, fontsize=11.0)
    ax.text(0.83, 0.87, r"$S(Q)$", color=GREEN, transform=ax.transAxes, fontsize=11.0)
    _temperature_annotations(ax, 0.05)

    ax = axes[2]
    _style_occupation_axis(ax, (-3.0, 4.5), [-3.0, -1.5, 0.0, 1.5, 3.0, 4.5])
    order_colors = {0.25: PURPLE, 0.5: "#235f91", 1.0: TEAL, 2.0: "#42b878", 4.0: GREEN}
    for order, curve in renyi_curves.items():
        ax.plot(n, curve, color=order_colors[order], linewidth=2.0)
    ax.set_ylabel(r"$S_r(W)$", fontsize=12.0, labelpad=5)
    ax.set_title(r"$\mathbf{(c)}$ Rényi entropies", fontsize=11.5, pad=6)
    label_specs = [
        (0.25, 0.04, 0.86, r"$r\!=\!1/4$"),
        (0.5, 0.04, 0.75, r"$r\!=\!1/2$"),
        (1.0, 0.04, 0.64, r"$r\!=\!1$"),
        (2.0, 0.27, 0.86, r"$r\!=\!2$"),
        (4.0, 0.27, 0.75, r"$r\!=\!4$"),
    ]
    for order, x0, y0, label in label_specs:
        ax.text(x0, y0, label, color=order_colors[order], transform=ax.transAxes, fontsize=10.7)
    _temperature_annotations(ax, 0.05)

    return _save_figure(fig, "figure_2_uncertainty_relations", dpi)


def _scientific_checks() -> dict[str, object]:
    occupation = np.linspace(0.0, 1.0, 10001)
    bodies = phase_space_bodies(occupation)
    moments = covariance_determinants(occupation)
    crossings = crossing_points()
    thermal_output = thermal_loss_output_occupation(0.1, 0.6, 0.6)
    thermal_entropy = float(renyi_entropy(thermal_output, 2.0, "W"))
    orders = (0.25, 0.5, 1.0, 2.0, 4.0)
    renyi_values = np.array([float(renyi_entropy(0.2, order, "W")) for order in orders])
    checks = {
        "fermi_particle_hole_max_abs_error": float(
            np.max(
                np.abs(
                    fermi_dirac_occupation(np.linspace(-12.0, 12.0, 1001))
                    + fermi_dirac_occupation(np.linspace(12.0, -12.0, 1001))
                    - 1.0
                )
            )
        ),
        "body_spacing_p_to_w_max_abs_error": float(np.max(np.abs(bodies.wigner_w - bodies.glauber_p - 0.5))),
        "body_spacing_w_to_q_max_abs_error": float(np.max(np.abs(bodies.husimi_q - bodies.wigner_w - 0.5))),
        "moment_minima": {
            "P": float(np.min(moments.glauber_p)),
            "W": float(np.min(moments.wigner_w)),
            "Q": float(np.min(moments.husimi_q)),
        },
        "crossings": {key: {"occupation": value[0], "moment": value[1]} for key, value in crossings.items()},
        "wigner_entropy_bounds": {str(order): entropy_lower_bound(order, "W") for order in orders},
        "wigner_renyi_monotonic_min_step": float(np.min(np.diff(renyi_values))),
        "thermal_channel": {
            "input_occupation": 0.1,
            "environment_occupation": 0.6,
            "transmissivity": 0.6,
            "output_occupation": thermal_output,
            "S2_W_output": thermal_entropy,
            "expected_exact": "ln(2.5)",
            "absolute_error": abs(thermal_entropy - float(np.log(2.5))),
        },
    }
    passed = (
        checks["fermi_particle_hole_max_abs_error"] < 1e-14
        and checks["body_spacing_p_to_w_max_abs_error"] < 1e-14
        and checks["body_spacing_w_to_q_max_abs_error"] < 1e-14
        and checks["moment_minima"] == {"P": -1.0, "W": -0.25, "Q": -1.0}
        and checks["wigner_renyi_monotonic_min_step"] > 0.0
        and checks["thermal_channel"]["absolute_error"] < 1e-14
    )
    return {
        "schema_version": 1,
        "paper_id": "2401.08523",
        "status": "passed" if passed else "failed",
        "generation_policy": {
            "source_pixels_used_in_generation": False,
            "digitized_data_used": False,
            "reference_files_read": [],
            "inputs": ["config/paper_exact.json", "src/fermionic_phase_space.py"],
        },
        "checks": checks,
    }


def main() -> int:
    started = time.perf_counter()
    config = _load_config()
    grid = config["scientific_grid"]
    rendering = config["rendering"]
    dpi = int(rendering["dpi"])
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    x = np.linspace(float(grid["fermi_x_min"]), float(grid["fermi_x_max"]), int(grid["fermi_points"]))
    occupation = fermi_dirac_occupation(x)
    n = np.linspace(0.0, 1.0, int(grid["occupation_points"]))
    moments = covariance_determinants(n)
    entropies = {distribution: renyi_entropy(n, 1.0, distribution) for distribution in ("P", "W", "Q")}
    renyi_curves = {float(order): renyi_entropy(n, float(order), "W") for order in grid["renyi_orders"]}

    _write_csv(DATA_DIR / "figure_1_fermi_dirac.csv", ["epsilon_over_T", "occupation"], [x, occupation])
    _write_csv(
        DATA_DIR / "figure_2_moments.csv",
        ["occupation", "det_gamma_P", "det_gamma_W", "det_gamma_Q"],
        [n, moments.glauber_p, moments.wigner_w, moments.husimi_q],
    )
    _write_csv(
        DATA_DIR / "figure_2_entropies.csv",
        ["occupation", "S_P", "S_W", "S_Q", "S_W_r_1_4", "S_W_r_1_2", "S_W_r_1", "S_W_r_2", "S_W_r_4"],
        [n, entropies["P"], entropies["W"], entropies["Q"], *[renyi_curves[order] for order in (0.25, 0.5, 1.0, 2.0, 4.0)]],
    )

    fig1_paths = _render_figure_1(x, occupation, dpi, rendering["figure_1_canvas_pixels"])
    fig2_paths = _render_figure_2(n, moments, entropies, renyi_curves, dpi, rendering["figure_2_canvas_pixels"])
    validation = _scientific_checks()
    _write_json(CHECK_DIR / "scientific_validation.json", validation)
    elapsed = time.perf_counter() - started
    run_payload = {
        "schema_version": 1,
        "paper_id": "2401.08523",
        "status": validation["status"],
        "runtime_seconds": elapsed,
        "command": "python3 code/scripts/run_reproduction.py",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "outputs": {
            "data": [
                "outputs/data/figure_1_fermi_dirac.csv",
                "outputs/data/figure_2_moments.csv",
                "outputs/data/figure_2_entropies.csv"
            ],
            "figure_1": fig1_paths,
            "figure_2": fig2_paths,
            "checks": ["outputs/checks/scientific_validation.json"]
        }
    }
    _write_json(CHECK_DIR / "reproduction_run.json", run_payload)
    print(json.dumps(run_payload, indent=2, ensure_ascii=False))
    return 0 if validation["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
