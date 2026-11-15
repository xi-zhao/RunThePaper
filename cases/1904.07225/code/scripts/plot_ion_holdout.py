"""Plot simultaneous intervals for the two uniform-sampling baselines."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    result = json.loads(Path("results/ion-holdout-scores.json").read_text())
    fig, panels = plt.subplots(1, 2, figsize=(9, 4.1), sharey=True, layout="constrained")
    comparisons = [
        ("difference_nmqa_minus_naive", "simultaneous_95_interval", "Raw uniform", "#0072B2"),
        ("difference_nmqa_minus_jeffreys", "simultaneous_95_interval_vs_jeffreys", "Smoothed uniform", "#D55E00"),
    ]
    for axis, (scheme, data) in zip(panels, result["results"].items()):
        rows = data["comparisons"]
        budgets = [row["shots"] for row in rows]
        axis.axhline(0, c="0.45", lw=1, ls="--")
        for point, interval, label, color in comparisons:
            values = np.array([row[point] for row in rows])
            bounds = np.array([row[interval] for row in rows])
            error = np.array([values - bounds[:, 0], bounds[:, 1] - values])
            axis.errorbar(budgets, values, yerr=error, label=label, color=color,
                          marker="o", markersize=3, linewidth=1.4, capsize=2)
        axis.set_xscale("log")
        axis.set_xticks([1, 3, 6, 12, 24, 60, 120, 246], labels=[1, 3, 6, 12, 24, 60, 120, 246])
        axis.tick_params(axis="x", labelsize=9)
        axis.set_title(f"{scheme.capitalize()} group split")
        axis.set_xlabel("Single-ion measurements")
        axis.grid(axis="y", alpha=.2)
    panels[0].set_ylabel("Brier score difference (NMQA − uniform)")
    panels[1].legend(loc="upper right", frameon=False, fontsize=9)
    fig.savefig("figures/ion-holdout-brier.png", dpi=155)


if __name__ == "__main__":
    main()
