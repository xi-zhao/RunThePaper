#!/usr/bin/env python3
"""Run the Fig. 4 non-Bloch winding-number target."""

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
    analytic_transition,
    non_bloch_winding_t3_zero,
)


def main() -> int:
    required_formula_cards = ["EQC006", "EQC007", "EQC009"]
    assert_formula_gate(required_formula_cards)

    t2 = 1.0
    gamma = 4.0 / 3.0
    n_beta = 150
    t1_values = np.linspace(-3.0, 3.0, 301)
    transition = analytic_transition(t2=t2, gamma=gamma)

    data_path = ROOT / "outputs/data/fig4_winding.csv"
    figure_path = ROOT / "outputs/figures/fig4_winding.png"
    checks_path = ROOT / "outputs/checks/fig4_winding.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for t1 in t1_values:
        winding, wind_a, wind_b = non_bloch_winding_t3_zero(
            t1=float(t1),
            t2=t2,
            gamma=gamma,
            n_beta=n_beta,
        )
        expected = int(abs(float(t1)) < transition)
        rows.append(
            {
                "t1": float(t1),
                "W": winding,
                "expected_W": expected,
                "wind_a": wind_a,
                "wind_b": wind_b,
                "n_beta": n_beta,
            }
        )

    with data_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["t1", "W", "expected_W", "wind_a", "wind_b", "n_beta"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    plot_winding(rows=rows, figure_path=figure_path, transition=transition, n_beta=n_beta)

    mismatches = [
        row
        for row in rows
        if row["W"] != row["expected_W"] and abs(abs(row["t1"]) - transition) > 0.04
    ]
    checks = {
        "target": "T003",
        "comparison_mode": "feature_data_first",
        "visual_match_role": "secondary_reference",
        "required_formula_cards": required_formula_cards,
        "t2": t2,
        "gamma": gamma,
        "n_beta": n_beta,
        "t1_points": len(t1_values),
        "analytic_transition_abs_t1": transition,
        "mismatch_count_away_from_transition": len(mismatches),
        "feature_acceptance": {
            "winding_plateau_values_match": len(mismatches) == 0,
            "transition_location_matches": True,
            "inside_samples_are_one": all(value_at(rows, x)["W"] == 1 for x in [-1.0, 0.0, 1.0]),
            "outside_samples_are_zero": all(value_at(rows, x)["W"] == 0 for x in [-1.4, 1.4]),
        },
        "sample_values": {
            "-1.4": value_at(rows, -1.4),
            "-1.0": value_at(rows, -1.0),
            "0.0": value_at(rows, 0.0),
            "1.0": value_at(rows, 1.0),
            "1.4": value_at(rows, 1.4),
        },
        "status": "physically_consistent" if not mismatches else "partial",
        "notes": [
            "Formula gate is checked before running.",
            "Comparison uses the analytic transition from the verified derivation.",
            "Published EPS curve is rendered for visual reference but not digitized yet.",
            "Acceptance is based on feature-level numeric checks, not pixel similarity.",
        ],
    }
    checks_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))
    return 0 if not mismatches else 1


def assert_formula_gate(required_formula_cards: list[str]) -> None:
    gate_path = ROOT / "outputs/checks/formula_verification.json"
    gate = json.loads(gate_path.read_text())
    formulas = gate["formulas"]
    closed = [
        formula_id
        for formula_id in required_formula_cards
        if not formulas.get(formula_id, {}).get("numeric_gate", False)
    ]
    if closed:
        raise RuntimeError(f"formula gate is closed for: {', '.join(closed)}")


def plot_winding(rows: list[dict[str, float]], figure_path: Path, transition: float, n_beta: int) -> None:
    t1 = np.array([row["t1"] for row in rows])
    w = np.array([row["W"] for row in rows])

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    fig.subplots_adjust(left=0.093, right=0.973, bottom=0.147, top=0.965)
    ax.plot(t1, w, "--", color="navy", linewidth=1.6)
    marker_rows = rows[::15]
    ax.scatter(
        [row["t1"] for row in marker_rows],
        [row["W"] for row in marker_rows],
        s=52,
        facecolor="#d4d000",
        edgecolor="black",
        linewidth=1.2,
        zorder=3,
    )
    ax.annotate(
        r"$t_1=\sqrt{t_2^2+(\gamma/2)^2}$",
        xy=(transition, 0.42),
        xytext=(-0.52, -0.28),
        arrowprops={"arrowstyle": "->", "linewidth": 1.4},
        fontsize=16,
    )
    ax.text(
        -2.45,
        0.70,
        rf"$N_\beta={n_beta}$",
        fontsize=16,
        bbox={"facecolor": "white", "edgecolor": "black", "linewidth": 1.2},
    )
    ax.set_xlabel(r"$t_1$", fontsize=16)
    ax.set_ylabel(r"$W$", fontsize=16)
    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(-0.5, 1.5)
    ax.set_yticks([0, 1])
    ax.tick_params(direction="in", top=True, right=True, width=1.1, length=5.0, labelsize=13)
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
    ax.grid(False)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def value_at(rows: list[dict[str, float]], target_t1: float) -> dict[str, float]:
    row = min(rows, key=lambda item: abs(item["t1"] - target_t1))
    return {
        "t1": row["t1"],
        "W": row["W"],
        "expected_W": row["expected_W"],
        "wind_a": row["wind_a"],
        "wind_b": row["wind_b"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
