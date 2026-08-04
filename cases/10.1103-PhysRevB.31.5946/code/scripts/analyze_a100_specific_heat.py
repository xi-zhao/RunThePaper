#!/usr/bin/env python3
"""Audit and plot the exploratory A100 specific-heat scan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--figure", required=True)
    parser.add_argument("--check", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    figure_path = Path(args.figure)
    check_path = Path(args.check)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    records = payload["records"]
    sizes = np.asarray([record["size"] for record in records], dtype=float)
    peak_temperatures = np.asarray([record["peak_temperature_grid"] for record in records], dtype=float)
    peak_heights = np.asarray([record["peak_specific_heat"] for record in records], dtype=float)
    paper_tc = float(payload["paper_observation_tc2"])
    intercept = float(payload["linear_peak_fit_vs_inverse_l"]["intercept_tc_infinite"])

    checks = {
        "all_peak_temperatures_within_0p15_of_paper_tc2": bool(
            np.all(np.abs(peak_temperatures - paper_tc) <= 0.15)
        ),
        "peak_height_nondecreasing_with_size": bool(np.all(np.diff(peak_heights) >= 0.0)),
        "infinite_size_intercept_within_0p15_of_paper_tc2": bool(abs(intercept - paper_tc) <= 0.15),
    }
    audit = {
        "schema_version": 1,
        "status": "passed",
        "input": str(input_path),
        "artifact_stage": "exploratory",
        "verdict": "feature_not_reproduced",
        "paper_tc2": paper_tc,
        "peak_temperatures": peak_temperatures.tolist(),
        "peak_heights": peak_heights.tolist(),
        "linear_intercept_tc_infinite": intercept,
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "diagnosis": (
            "The short random-start Metropolis trajectories are not equilibrated across the first-order region: "
            "peak locations are size-inconsistent and peak heights do not show the required growth."
        ),
        "recommended_action": (
            "Use ordered/disordered starts, replica exchange or multicanonical sampling, convergence traces, "
            "and at least paper-scale kept sweeps before treating Figs. 9-10 as a reproduction."
        ),
    }

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0), constrained_layout=True)
    for record in records:
        axes[0].errorbar(
            record["temperatures"],
            record["specific_heat_per_spin"],
            yerr=record["specific_heat_sem"],
            marker="o",
            markersize=2.5,
            linewidth=1.0,
            capsize=1.5,
            label=f"L={record['size']}",
        )
    axes[0].axvline(paper_tc, color="black", linestyle="--", linewidth=1.0, label="paper Tc2≈0.7")
    axes[0].set(xlabel="T / |JNN|", ylabel="specific heat per spin", title="Exploratory A100 scan")
    axes[0].legend(fontsize=7, ncol=2)

    inverse_sizes = 1.0 / sizes
    axes[1].scatter(inverse_sizes, peak_temperatures, color="#b2182b", label="grid peaks")
    fit_x = np.linspace(0.0, float(inverse_sizes.max()) * 1.05, 100)
    slope = float(payload["linear_peak_fit_vs_inverse_l"]["slope"])
    axes[1].plot(fit_x, slope * fit_x + intercept, color="#2166ac", label="linear fit")
    axes[1].axhline(paper_tc, color="black", linestyle="--", linewidth=1.0, label="paper Tc2≈0.7")
    axes[1].set(xlabel="1/L", ylabel="grid peak temperature", title="Failed finite-size trend")
    axes[1].legend(fontsize=7)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": audit["verdict"], "failed_checks": audit["failed_checks"]}))


if __name__ == "__main__":
    main()
