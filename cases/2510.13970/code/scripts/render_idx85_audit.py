#!/usr/bin/env python3
"""Render a submission-grade diagnostic for the idx85 benchmark audit."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
DATA = WORKSPACE / "outputs" / "data" / "idx85_gold_audit.json"


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    task4 = payload["task_4"]
    points = payload["task_6"]["adaptive_points"]

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 6.8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.3,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.65), constrained_layout=True)

    labels = [r"$ZZ$", r"$YY$", r"$X_{\rm edge}$", r"$X_{\rm bulk}$", r"$ZXZ$"]
    positions = np.arange(len(labels))
    width = 0.25
    axes[0].bar(
        positions - width,
        task4["phase_independent_van_vleck_coefficients"],
        width,
        color="#0072B2",
        label="van Vleck",
    )
    axes[0].bar(
        positions,
        task4["principal_log_t0_zero_coefficients"],
        width,
        color="#009E73",
        label=r"principal log, $t_0=0$",
    )
    axes[0].bar(
        positions + width,
        task4["source_and_frozen_coefficients"],
        width,
        color="#D55E00",
        label="source Eq. (3) / gold",
    )
    axes[0].axhline(0, color="0.25", linewidth=0.65)
    axes[0].set_xticks(positions, labels)
    axes[0].set_ylabel(r"coefficient in $\omega^2(H-A)$")
    axes[0].set_title("Operator content at second order")
    axes[0].legend(frameon=False, loc="lower left")
    axes[0].text(-0.13, 1.04, "a", transform=axes[0].transAxes, fontweight="bold", fontsize=9)

    omega = np.array([point["omega"] for point in points])
    omega2 = np.array([point["omega2_norm"] for point in points])
    omega3 = np.array([point["omega3_norm"] for point in points])
    left_color = "#0072B2"
    right_color = "#D55E00"
    axes[1].plot(omega, omega2, "o-", color=left_color, label=r"$\omega^2\|\Delta\|_\infty$")
    axes[1].axhline(
        payload["task_6"]["leading_mismatch_operator_norm"],
        color=left_color,
        linestyle="--",
        linewidth=0.9,
        label="asymptotic coefficient",
    )
    axes[1].set_xlabel(r"drive frequency $\omega$")
    axes[1].set_ylabel(r"$\omega^2\|\Delta\|_\infty$", color=left_color)
    axes[1].tick_params(axis="y", colors=left_color)
    axes[1].set_xscale("log", base=2)
    axes[1].set_ylim(100.9, 103.0)
    twin = axes[1].twinx()
    twin.plot(omega, omega3, "s-", color=right_color, label=r"$\omega^3\|\Delta\|_\infty$")
    twin.set_ylabel(r"$\omega^3\|\Delta\|_\infty$", color=right_color)
    twin.tick_params(axis="y", colors=right_color)
    twin.ticklabel_format(axis="y", style="sci", scilimits=(4, 4))
    axes[1].set_title("The claimed constant is not a limit")
    handles1, labels1 = axes[1].get_legend_handles_labels()
    handles2, labels2 = twin.get_legend_handles_labels()
    axes[1].legend(handles1 + handles2, labels1 + labels2, frameon=False, loc="upper left")
    axes[1].text(-0.13, 1.04, "b", transform=axes[1].transAxes, fontweight="bold", fontsize=9)

    output = WORKSPACE / "outputs" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "idx85_gold_audit.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "idx85_gold_audit.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
