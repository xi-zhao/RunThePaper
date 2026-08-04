#!/usr/bin/env python3
"""Finite-size analysis of the leaf-typicality outlier exponent.

This is a secondary analysis of the independently generated campaign data.  It
does not add a new reproduction target; it quantifies the ETH discussion in the
reader-facing note.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
SHARDS = WORKSPACE / "outputs" / "data" / "campaign_shards"
DATA_OUT = WORKSPACE / "outputs" / "data" / "eth_scaling_summary.csv"
FIGURE_OUT = WORKSPACE / "outputs" / "figures" / "eth_scaling_summary.png"
CHECK_OUT = WORKSPACE / "outputs" / "checks" / "eth_scaling_summary.json"
LENGTHS = (6, 8, 10, 12)
THRESHOLDS = (0.05, 0.10, 0.15)
GROUPS = (
    ("main", "main_L*_typicality.csv", "main-text nonintegrable leaf", "#e55309", "o"),
    (
        "supplemental",
        "supplemental_L*_typicality.csv",
        "supplemental nonintegrable leaf",
        "#5b6fc7",
        "s",
    ),
    ("integrable", "integrable_L*_typicality.csv", "integrable foliation", "#313131", "^"),
)


def load(pattern: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(SHARDS.glob(pattern)):
        with path.open(encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                if raw["family"] != "leaf":
                    continue
                rows.append(
                    {
                        "length": int(raw["length"]),
                        "delta": float(raw["delta"]),
                        "alpha": float(raw["log_d_count"]) if raw["log_d_count"] else 0.0,
                        "observable": raw["observable"],
                        "beta": float(raw["beta"]),
                    }
                )
    return rows


def summarize() -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for group, pattern, label, _color, _marker in GROUPS:
        rows = load(pattern)
        indexed: dict[tuple[int, float], list[float]] = defaultdict(list)
        for row in rows:
            for threshold in THRESHOLDS:
                if abs(row["delta"] - threshold) < 1e-12:
                    indexed[(row["length"], threshold)].append(row["alpha"])
        for threshold in THRESHOLDS:
            for length in LENGTHS:
                values = np.asarray(indexed[(length, threshold)])
                summary.append(
                    {
                        "group": group,
                        "label": label,
                        "length": length,
                        "delta": threshold,
                        "samples": values.size,
                        "minimum_alpha": float(np.min(values)),
                        "median_alpha": float(np.median(values)),
                        "maximum_alpha": float(np.max(values)),
                    }
                )
    return summary


def write_csv(rows: list[dict[str, Any]]) -> None:
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    with DATA_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render(rows: list[dict[str, Any]]) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "mathtext.fontset": "cm",
            "axes.linewidth": 0.7,
            "xtick.direction": "in",
            "ytick.direction": "in",
        }
    )
    figure, axes = plt.subplots(1, 3, figsize=(11.4, 3.8), sharex=True, sharey=True)
    for axis, threshold in zip(axes, THRESHOLDS, strict=True):
        for group, _pattern, label, color, marker in GROUPS:
            points = [
                row for row in rows if row["group"] == group and row["delta"] == threshold
            ]
            x = np.asarray([row["length"] for row in points])
            median = np.asarray([row["median_alpha"] for row in points])
            low = np.asarray([row["minimum_alpha"] for row in points])
            high = np.asarray([row["maximum_alpha"] for row in points])
            axis.fill_between(x, low, high, color=color, alpha=0.10, linewidth=0)
            axis.plot(
                x,
                median,
                color=color,
                marker=marker,
                linewidth=1.8,
                markersize=5,
                label=label,
            )
        axis.set_title(rf"$\Delta={threshold:.2f}$")
        axis.set_xticks(LENGTHS)
        axis.set_xlabel(r"$L$")
        axis.grid(color="#d2d2d2", linewidth=0.5)
        axis.tick_params(top=True, right=True)
    axes[0].set_ylabel(r"median $\alpha_L(\Delta)=\log_d N_\Delta$")
    axes[-1].legend(frameon=False, fontsize=8, loc="upper right")
    figure.tight_layout()
    FIGURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_OUT, dpi=220)
    plt.close(figure)


def main() -> int:
    rows = summarize()
    write_csv(rows)
    render(rows)
    lookup = {
        (row["group"], row["delta"], row["length"]): row["median_alpha"]
        for row in rows
    }
    changes = {
        group: {
            f"delta_{threshold:.2f}": (
                lookup[(group, threshold, 12)] - lookup[(group, threshold, 6)]
            )
            for threshold in THRESHOLDS
        }
        for group, *_rest in GROUPS
    }
    payload = {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "status": "passed",
        "definition": "alpha_L(Delta)=log_d N_Delta; empty outlier sets are assigned alpha=0",
        "interpretation": (
            "Negative L=6 to L=12 changes indicate finite-size sharpening. "
            "These four sizes do not determine the thermodynamic-limit exponent."
        ),
        "median_alpha_change_L6_to_L12": changes,
        "data": str(DATA_OUT.relative_to(WORKSPACE)),
        "figure": str(FIGURE_OUT.relative_to(WORKSPACE)),
    }
    CHECK_OUT.parent.mkdir(parents=True, exist_ok=True)
    CHECK_OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
