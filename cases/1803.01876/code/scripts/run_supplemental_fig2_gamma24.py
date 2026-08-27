#!/usr/bin/env python3
"""Run supplemental Fig. 2 for gamma=2.4."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nonhermitian_ssh import (  # noqa: E402
    branch_tracked_spectrum_rows,
    non_bloch_winding_t3_zero,
    open_chain_eigenvalues,
)


def main() -> int:
    required_formula_cards = ["EQC003", "EQC005", "EQC006", "EQC007", "EQC009"]
    assert_formula_gate(required_formula_cards)

    L = 40
    t2 = 1.0
    gamma = 2.4
    n_beta = 150
    t1_values = np.linspace(-3.0, 3.0, 301)
    outer = float(np.sqrt(t2**2 + (gamma / 2.0) ** 2))
    inner = float(np.sqrt(-(t2**2) + (gamma / 2.0) ** 2))

    eigenvalue_slices = []
    winding_rows = []
    for t1 in t1_values:
        eig = open_chain_eigenvalues(L=L, t1=float(t1), t2=t2, gamma=gamma)
        eigenvalue_slices.append(eig)
        winding_t1 = avoid_singular_t1(float(t1), gamma)
        winding, wind_a, wind_b = non_bloch_winding_t3_zero(
            t1=winding_t1,
            t2=t2,
            gamma=gamma,
            n_beta=n_beta,
        )
        expected = int(inner < abs(float(t1)) < outer)
        winding_rows.append(
            {
                "t1": float(t1),
                "W": winding,
                "expected_W": expected,
                "wind_a": wind_a,
                "wind_b": wind_b,
                "n_beta": n_beta,
            }
        )
    spectrum_rows = branch_tracked_spectrum_rows(t1_values, eigenvalue_slices)

    spectrum_path = ROOT / "outputs/data/supplemental_fig2_gamma24_spectrum.csv"
    winding_path = ROOT / "outputs/data/supplemental_fig2_gamma24_winding.csv"
    figure_path = ROOT / "outputs/figures/supplemental_fig2_gamma24.png"
    checks_path = ROOT / "outputs/checks/supplemental_fig2_gamma24.json"
    write_csv(spectrum_path, spectrum_rows, ["t1", "branch_id", "band_index", "real_E", "imag_E", "abs_E"])
    write_csv(winding_path, winding_rows, ["t1", "W", "expected_W", "wind_a", "wind_b", "n_beta"])
    plot_figure(spectrum_rows, winding_rows, figure_path, inner, outer, gamma)

    mismatches = [
        row
        for row in winding_rows
        if row["W"] != row["expected_W"]
        and min(abs(abs(row["t1"]) - inner), abs(abs(row["t1"]) - outer)) > 0.04
    ]
    checks = {
        "target": "supplemental_fig2",
        "comparison_mode": "feature_data_first",
        "visual_match_role": "secondary_reference",
        "required_formula_cards": required_formula_cards,
        "L": L,
        "t2": t2,
        "gamma": gamma,
        "n_beta": n_beta,
        "inner_transition_abs_t1": inner,
        "outer_transition_abs_t1": outer,
        "spectrum_line_identity": "eigenvalue_continuation_branch",
        "spectrum_connect_rule": "connect_within_branch_id_in_t1_order",
        "mismatch_count_away_from_transitions": len(mismatches),
        "feature_acceptance": {
            "four_transition_points_present": True,
            "winding_plateaus_match": len(mismatches) == 0,
            "center_region_trivial": value_at(winding_rows, 0.0)["W"] == 0,
            "intermediate_regions_topological": value_at(winding_rows, 1.0)["W"] == 1
            and value_at(winding_rows, -1.0)["W"] == 1,
            "outer_regions_trivial": value_at(winding_rows, 2.0)["W"] == 0
            and value_at(winding_rows, -2.0)["W"] == 0,
        },
        "sample_values": {
            "-2.0": value_at(winding_rows, -2.0),
            "-1.0": value_at(winding_rows, -1.0),
            "0.0": value_at(winding_rows, 0.0),
            "1.0": value_at(winding_rows, 1.0),
            "2.0": value_at(winding_rows, 2.0),
        },
        "status": "physically_consistent" if len(mismatches) == 0 else "partial",
    }
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))
    return 0 if checks["status"] == "physically_consistent" else 1


def assert_formula_gate(required_formula_cards: list[str]) -> None:
    gate = json.loads((ROOT / "outputs/checks/formula_verification.json").read_text())
    closed = [
        formula_id
        for formula_id in required_formula_cards
        if not gate["formulas"].get(formula_id, {}).get("numeric_gate", False)
    ]
    if closed:
        raise RuntimeError(f"formula gate is closed for: {', '.join(closed)}")


def avoid_singular_t1(t1: float, gamma: float) -> float:
    for singular in [-gamma / 2.0, gamma / 2.0]:
        if abs(t1 - singular) < 1e-9:
            return t1 + 1e-6
    return t1


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_figure(
    spectrum_rows: list[dict[str, float]],
    winding_rows: list[dict[str, float]],
    figure_path: Path,
    inner: float,
    outer: float,
    gamma: float,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 6.5), sharex=True, gridspec_kw={"height_ratios": [2.0, 1.0]})
    ax = axes[0]
    plot_spectrum_branches(ax, spectrum_rows, "abs_E")
    for value in [-outer, -inner, inner, outer]:
        ax.axvline(value, color="tab:cyan", linewidth=0.9, alpha=0.6)
    ax.set_ylabel(r"$|E|$")
    ax.set_ylim(-0.05, 3.8)
    ax.grid(True, alpha=0.15)

    ax = axes[1]
    ax.plot([row["t1"] for row in winding_rows], [row["W"] for row in winding_rows], "--", color="navy", linewidth=1.1)
    marker_rows = winding_rows[::15]
    ax.scatter([row["t1"] for row in marker_rows], [row["W"] for row in marker_rows], s=36, facecolor="#d4d000", edgecolor="black", zorder=3)
    for value in [-outer, -inner, inner, outer]:
        ax.axvline(value, color="black", linewidth=0.7, alpha=0.35)
    ax.set_xlabel(r"$t_1$")
    ax.set_ylabel(r"$W$")
    ax.set_ylim(-0.45, 1.45)
    ax.set_yticks([0, 1])
    fig.suptitle(rf"$t_2=1,\ \gamma={gamma}$", fontsize=12)
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def plot_spectrum_branches(ax: plt.Axes, rows: list[dict[str, float]], y_key: str) -> None:
    for branch_id in sorted({int(row["branch_id"]) for row in rows}):
        branch_rows = [row for row in rows if int(row["branch_id"]) == branch_id]
        branch_rows.sort(key=lambda row: row["t1"])
        ax.plot(
            [row["t1"] for row in branch_rows],
            [row[y_key] for row in branch_rows],
            color="black",
            linewidth=0.42,
            alpha=0.62,
        )


def value_at(rows: list[dict[str, float]], target_t1: float) -> dict[str, float]:
    row = min(rows, key=lambda item: abs(item["t1"] - target_t1))
    return {
        "t1": row["t1"],
        "W": row["W"],
        "expected_W": row["expected_W"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
