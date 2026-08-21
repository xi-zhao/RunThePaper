#!/usr/bin/env python3
"""Render an audit visualization from frozen Wootters reproduction data.

The original Letter contains no figures.  This plot is therefore a new,
data-derived reader aid rather than a reconstruction of an authored panel.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent if WORKSPACE.name == "code" else WORKSPACE
sys.path.insert(0, str(WORKSPACE / "src"))

from wootters.model import entanglement_from_concurrence  # noqa: E402


def read_numeric_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def render(data_root: Path, output: Path) -> None:
    optimal = read_numeric_rows(data_root / "optimal_decompositions.csv")
    werner = read_numeric_rows(data_root / "werner_family.csv")
    if not optimal or not werner:
        raise ValueError("audit figure requires non-empty frozen data tables")

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7,
            "axes.linewidth": 0.8,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "legend.frameon": False,
        }
    )
    blue = "#3B6FB6"
    orange = "#D9822B"
    gray = "#7A7A7A"

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.0), constrained_layout=True)

    concurrence = np.asarray([float(row["concurrence"]) for row in optimal])
    ensemble_entanglement = np.asarray(
        [float(row["ensemble_average_entanglement"]) for row in optimal]
    )
    curve_c = np.linspace(0.0, 1.0, 401)
    curve_e = np.asarray(entanglement_from_concurrence(curve_c))
    residual = np.max(
        np.abs(
            ensemble_entanglement
            - np.asarray(entanglement_from_concurrence(concurrence))
        )
    )
    axes[0].plot(curve_c, curve_e, color=gray, linewidth=1.6, label="closed form")
    axes[0].scatter(
        concurrence,
        ensemble_entanglement,
        s=12,
        color=blue,
        alpha=0.68,
        edgecolors="none",
        label="constructive ensembles",
    )
    axes[0].set(
        xlabel="Concurrence, $C$",
        ylabel="Entanglement of formation, $E$ (bits)",
        xlim=(-0.02, 1.02),
        ylim=(-0.02, 1.02),
    )
    axes[0].text(
        0.04,
        0.94,
        f"max residual = {residual:.1e}",
        transform=axes[0].transAxes,
        va="top",
        color=gray,
    )
    axes[0].legend(loc="lower right")

    p = np.asarray([float(row["p"]) for row in werner])
    numeric = np.asarray([float(row["numeric_concurrence"]) for row in werner])
    analytic = np.asarray([float(row["analytic_concurrence"]) for row in werner])
    werner_error = np.max(np.abs(numeric - analytic))
    axes[1].plot(p, analytic, color=gray, linewidth=1.6, label="closed form")
    axes[1].scatter(
        p,
        numeric,
        s=11,
        color=orange,
        alpha=0.78,
        edgecolors="none",
        label="independent numerics",
    )
    axes[1].axvline(1.0 / 3.0, color="#B8B8B8", linewidth=0.8, linestyle="--")
    axes[1].set(
        xlabel="Werner mixing parameter, $p$",
        ylabel="Concurrence, $C$",
        xlim=(-0.02, 1.02),
        ylim=(-0.02, 1.02),
    )
    axes[1].text(
        0.04,
        0.94,
        f"max error = {werner_error:.1e}",
        transform=axes[1].transAxes,
        va="top",
        color=gray,
    )
    axes[1].legend(loc="lower right")

    for label, axis in zip(("a", "b"), axes, strict=True):
        axis.text(
            -0.16,
            1.04,
            label,
            transform=axis.transAxes,
            fontsize=9,
            fontweight="bold",
            va="top",
        )
    fig.suptitle(
        "Independent numerical audit (the original Letter contains no figures)",
        fontsize=8,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=CASE_ROOT / "outputs/data")
    parser.add_argument(
        "--output",
        type=Path,
        default=CASE_ROOT / "outputs/figures/wootters_formula_audit.png",
    )
    args = parser.parse_args()
    render(args.data_root, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
