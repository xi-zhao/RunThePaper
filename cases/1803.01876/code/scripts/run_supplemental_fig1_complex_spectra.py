#!/usr/bin/env python3
"""Run supplemental Fig. 1 complex-plane spectra."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nonhermitian_ssh import generalized_brillouin_radius, non_bloch_ab, open_chain_eigenvalues  # noqa: E402


def main() -> int:
    required_formula_cards = ["EQC006", "EQC007", "EQC008"]
    assert_formula_gate(required_formula_cards)

    L = 120
    t2 = 1.0
    gamma = 4.0 / 3.0
    t1_values = [0.2, 0.6, 1.0]
    k_points = 600

    theory_rows = []
    finite_rows = []
    checks_by_t1 = {}
    for t1 in t1_values:
        theory = theory_spectrum(t1=t1, t2=t2, gamma=gamma, k_points=k_points)
        finite = open_chain_eigenvalues(L=L, t1=t1, t2=t2, gamma=gamma)
        finite_bulk = finite[np.abs(finite) > 1e-4]
        for branch, values in theory:
            for value in values:
                theory_rows.append(row("theory", t1, branch, value))
        for band_index, value in enumerate(finite):
            finite_rows.append(row("open_chain", t1, band_index, value))
        distances = nearest_distances(finite_bulk, np.concatenate([values for _, values in theory]))
        checks_by_t1[str(t1)] = {
            "finite_bulk_count": int(len(finite_bulk)),
            "median_nearest_theory_distance": float(np.median(distances)),
            "p95_nearest_theory_distance": float(np.percentile(distances, 95)),
        }

    theory_path = ROOT / "outputs/data/supplemental_fig1_theory_complex_spectra.csv"
    finite_path = ROOT / "outputs/data/supplemental_fig1_open_chain_complex_spectra.csv"
    figure_path = ROOT / "outputs/figures/supplemental_fig1_complex_spectra.png"
    checks_path = ROOT / "outputs/checks/supplemental_fig1_complex_spectra.json"
    write_csv(theory_path, theory_rows, ["kind", "t1", "band_index", "real_E", "imag_E", "abs_E"])
    write_csv(finite_path, finite_rows, ["kind", "t1", "band_index", "real_E", "imag_E", "abs_E"])
    plot_figure(theory_rows, finite_rows, t1_values, figure_path)

    feature_acceptance = {
        "finite_spectra_close_to_theory": all(item["p95_nearest_theory_distance"] < 0.08 for item in checks_by_t1.values()),
        "three_t1_cases_present": len(checks_by_t1) == 3,
    }
    checks = {
        "target": "supplemental_fig1",
        "comparison_mode": "feature_data_first",
        "visual_match_role": "secondary_reference",
        "required_formula_cards": required_formula_cards,
        "L": L,
        "t2": t2,
        "gamma": gamma,
        "t1_values": t1_values,
        "checks_by_t1": checks_by_t1,
        "feature_acceptance": feature_acceptance,
        "status": "physically_consistent" if all(feature_acceptance.values()) else "partial",
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


def theory_spectrum(t1: float, t2: float, gamma: float, k_points: int) -> list[tuple[int, np.ndarray]]:
    radius = generalized_brillouin_radius(t1=t1, gamma=gamma)
    k = np.linspace(0.0, 2.0 * np.pi, k_points, endpoint=False)
    beta = radius * np.exp(1j * k)
    a_beta, b_beta = non_bloch_ab(beta=beta, t1=t1, t2=t2, gamma=gamma)
    energy = np.sqrt(a_beta * b_beta)
    return [(0, energy), (1, -energy)]


def nearest_distances(points: np.ndarray, reference: np.ndarray) -> np.ndarray:
    distances = np.abs(points[:, None] - reference[None, :])
    return np.min(distances, axis=1)


def row(kind: str, t1: float, band_index: int, value: complex) -> dict[str, float | str | int]:
    return {
        "kind": kind,
        "t1": t1,
        "band_index": band_index,
        "real_E": float(np.real(value)),
        "imag_E": float(np.imag(value)),
        "abs_E": float(abs(value)),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_figure(theory_rows: list[dict[str, object]], finite_rows: list[dict[str, object]], t1_values: list[float], figure_path: Path) -> None:
    fig, axes = plt.subplots(3, 2, figsize=(7.8, 10.0), sharex=False, sharey=False)
    for row_index, t1 in enumerate(t1_values):
        for col, (rows, title) in enumerate([(theory_rows, "Theory"), (finite_rows, "Open chain")]):
            ax = axes[row_index, col]
            selected = [row for row in rows if row["t1"] == t1]
            ax.scatter([row["real_E"] for row in selected], [row["imag_E"] for row in selected], s=2.0, alpha=0.7)
            ax.axhline(0.0, color="black", linewidth=0.5, alpha=0.25)
            ax.axvline(0.0, color="black", linewidth=0.5, alpha=0.25)
            ax.set_title(rf"$t_1={t1}$ {title}", fontsize=10)
            ax.set_xlabel("Re(E)")
            ax.set_ylabel("Im(E)")
            ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
