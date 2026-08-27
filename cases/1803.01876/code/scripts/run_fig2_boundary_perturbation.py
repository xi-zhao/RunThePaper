#!/usr/bin/env python3
"""Run the Fig. 2(d) boundary perturbation target."""

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
    abs_rank_spectrum_rows,
    branch_tracked_spectrum_rows,
    open_chain_eigenvalues,
)


def main() -> int:
    required_formula_cards = ["EQC003", "EQC005"]
    assert_formula_gate(required_formula_cards)

    L = 40
    t2 = 1.0
    gamma = 4.0 / 3.0
    left_bond_delta = -0.8
    transition = analytic_transition(t2=t2, gamma=gamma)
    # The dense grid plus exact feature points keeps the two physical V bottoms
    # honest: the exact zero crossing at t1 = 0.8 + gamma/2 and the near-zero
    # (but nonzero) wiggle minimum at t1 ~ 1.025.
    t1_values = np.union1d(
        np.linspace(-3.0, 3.0, 601),
        [0.8 - gamma / 2.0, 0.8 + gamma / 2.0, 1.025],
    )

    eigenvalue_slices = []
    summaries = []
    for t1 in t1_values:
        eig = open_chain_eigenvalues(
            L=L,
            t1=float(t1),
            t2=t2,
            gamma=gamma,
            left_bond_delta=left_bond_delta,
        )
        eigenvalue_slices.append(eig)
        abs_sorted = np.sort(np.abs(eig))
        summaries.append(
            {
                "t1": float(t1),
                "abs0": float(abs_sorted[0]),
                "abs1": float(abs_sorted[1]),
                "abs2": float(abs_sorted[2]),
                "abs3": float(abs_sorted[3]),
            }
        )
    rows = branch_tracked_spectrum_rows(t1_values, eigenvalue_slices)
    sorted_artifact_rows = abs_rank_spectrum_rows(t1_values, eigenvalue_slices)

    data_path = ROOT / "outputs/data/fig2_boundary_perturbation.csv"
    figure_path = ROOT / "outputs/figures/fig2_boundary_perturbation.png"
    zoom_path = ROOT / "outputs/figures/fig2_boundary_perturbation_low_energy_zoom.png"
    artifact_zoom_path = ROOT / "outputs/figures/fig2_boundary_perturbation_sorted_artifact_zoom.png"
    checks_path = ROOT / "outputs/checks/fig2_boundary_perturbation.json"
    write_csv(data_path, rows, ["t1", "branch_id", "band_index", "real_E", "imag_E", "abs_E"])
    plot_boundary_spectrum(rows, figure_path, transition)
    plot_low_energy_zoom(rows, zoom_path, transition)
    plot_low_energy_zoom(sorted_artifact_rows, artifact_zoom_path, transition)

    probes = {
        "center": spectrum_at_t1(summaries, 0.0),
        "inside_positive": spectrum_at_t1(summaries, 1.0),
        "inside_negative": spectrum_at_t1(summaries, -1.0),
        "outside_positive": spectrum_at_t1(summaries, 1.4),
        "outside_negative": spectrum_at_t1(summaries, -1.4),
    }

    # Off-grid physics probes for the low-energy black wiggle. The exact zero
    # crossing sits at t1 = 0.8 + gamma/2 where the perturbed leftmost bond
    # t1 - 0.8 equals gamma/2 and the first site decouples in one direction.
    exact_zero_t1 = 0.8 + gamma / 2.0
    exact_zero_min_abs_E = float(
        np.min(
            np.abs(
                open_chain_eigenvalues(
                    L=L, t1=exact_zero_t1, t2=t2, gamma=gamma, left_bond_delta=left_bond_delta
                )
            )
        )
    )
    # The robust zero modes are a chiral +/-E pair, so the black wiggle is the
    # third-smallest |E| level while |t1| stays below the transition.
    wiggle_min_abs_E = min(
        float(
            np.sort(
                np.abs(
                    open_chain_eigenvalues(
                        L=L, t1=float(t1), t2=t2, gamma=gamma, left_bond_delta=left_bond_delta
                    )
                )
            )[2]
        )
        for t1 in np.linspace(0.95, 1.35, 801)
    )
    crossing_count = count_low_energy_abs_crossings(rows, t1_min=1.0, t1_max=1.2, abs_E_max=0.35)

    feature_acceptance = {
        "zero_modes_robust_inside": max(
            probes["center"]["abs1"],
            probes["inside_positive"]["abs1"],
            probes["inside_negative"]["abs1"],
        )
        < 1e-3,
        "outside_zero_modes_absent": min(
            probes["outside_positive"]["abs1"],
            probes["outside_negative"]["abs1"],
        )
        > 5e-2,
        "boundary_perturbation_has_extra_nonzero_near_zero": any(
            row["abs2"] < 0.25 for row in summaries if abs(row["t1"]) < transition - 0.15
        ),
        "exact_zero_crossing_at_first_bond_decoupling": exact_zero_min_abs_E < 1e-6,
        "black_wiggle_near_zero_without_touching": 1e-3 < wiggle_min_abs_E < 1e-2,
        "abs_crossings_rendered_as_crossings": crossing_count > 0,
    }
    checks = {
        "target": "T002",
        "comparison_mode": "feature_data_first",
        "visual_match_role": "secondary_reference",
        "required_formula_cards": required_formula_cards,
        "L": L,
        "t2": t2,
        "gamma": gamma,
        "left_bond_delta": left_bond_delta,
        "analytic_transition_abs_t1": transition,
        "physical_line_identity": "eigenvalue_continuation_branch",
        "physical_connect_rule": "connect_within_branch_id_in_t1_order",
        "spectrum_line_identity": "eigenvalue_continuation_branch",
        "spectrum_connect_rule": "connect_within_branch_id_in_t1_order",
        "render_line_identity": "eigenvalue_continuation_branch",
        "render_connect_rule": "connect_within_branch_id_in_t1_order",
        "zero_mode_render_rule": "finite_chain_lowest_abs_energy_inside_transition",
        "low_energy_zoom_figure": "outputs/figures/fig2_boundary_perturbation_low_energy_zoom.png",
        "physics_probes": {
            "exact_zero_crossing_t1": exact_zero_t1,
            "exact_zero_crossing_min_abs_E": exact_zero_min_abs_E,
            "black_wiggle_min_abs_E_in_0p95_1p35": wiggle_min_abs_E,
            "low_energy_abs_crossing_count_1p0_1p2": crossing_count,
        },
        "source_figure_artifact": {
            "kind": "sorted_line_rendering",
            "claim": (
                "The source Fig. 2(d) connects |E| samples by per-t1 sorted rank, which renders the "
                "genuine |E| crossings near t1 in [1.0, 1.2] as avoided crossings."
            ),
            "artifact_rule": "connect_abs_energy_rank_in_t1_order",
            "evidence_figure": "outputs/figures/fig2_boundary_perturbation_sorted_artifact_zoom.png",
        },
        "probe_spectra": probes,
        "feature_acceptance": feature_acceptance,
        "status": "physically_consistent" if all(feature_acceptance.values()) else "partial",
        "notes": [
            "Formula gate is checked before running.",
            "Acceptance checks that the robust zero modes survive the left-edge perturbation.",
            "The extra nonzero modes are treated as a feature, not as a failure.",
            "The visible |E| panel is rendered from eigenvalue-continuation branches; genuine |E| crossings are drawn as crossings.",
            "The source figure's sorted-rank line convention is reproduced separately as an artifact evidence figure, not as the published rendering.",
        ],
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


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_boundary_spectrum(rows: list[dict[str, float]], figure_path: Path, transition: float) -> None:
    fig = plt.figure(figsize=(9.21, 6.05))
    ax = fig.add_axes([0.095, 0.18, 0.875, 0.79])
    plot_spectrum_branches(ax, rows, "abs_E", linewidth=0.82, alpha=1.0)
    zero_curve = zero_mode_curve(rows, transition)
    ax.plot(
        [point[0] for point in zero_curve],
        [point[1] for point in zero_curve],
        color="red",
        linewidth=3.0,
        solid_capstyle="round",
        zorder=5,
    )
    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(0.0, 3.95)
    ax.set_xticks([-3, -2, -1, 0, 1, 2, 3])
    ax.set_yticks([0, 1, 2, 3])
    ax.tick_params(direction="in", top=True, right=True, length=7, width=1.0, labelsize=22)
    ax.set_xlabel(r"$t_1$", fontsize=28, labelpad=12)
    ax.set_ylabel(r"$|E|$", fontsize=28, labelpad=10)
    ax.text(-0.075, 0.995, r"(d)", transform=ax.transAxes, fontsize=34, va="top", ha="left", clip_on=False)

    arrow_style = dict(arrowstyle="->", color="#45d7ff", linewidth=2.0, shrinkA=2, shrinkB=2)
    ax.annotate(
        r"$t_2-\gamma/2$",
        xy=(1.0 - 2.0 / 3.0, 0.0),
        xytext=(-0.35, 0.45),
        textcoords="data",
        fontsize=26,
        ha="center",
        color="0.2",
        arrowprops=arrow_style,
        annotation_clip=False,
    )
    ax.annotate(
        r"$t_2+\gamma/2$",
        xy=(1.0 + 2.0 / 3.0, 0.0),
        xytext=(2.15, 0.45),
        textcoords="data",
        fontsize=26,
        ha="center",
        color="0.2",
        arrowprops=arrow_style,
        annotation_clip=False,
    )
    ax.annotate(
        r"$\sqrt{t_2^2+(\gamma/2)^2}$",
        xy=(transition, 0.0),
        xytext=(1.95, -0.55),
        textcoords="data",
        fontsize=26,
        ha="center",
        color="0.2",
        arrowprops=arrow_style,
        annotation_clip=False,
    )

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def plot_low_energy_zoom(rows: list[dict[str, float]], figure_path: Path, transition: float) -> None:
    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    plot_spectrum_branches(ax, rows, "abs_E", linewidth=0.92, alpha=0.88)
    zero_curve = zero_mode_curve(rows, transition)
    ax.plot(
        [point[0] for point in zero_curve],
        [point[1] for point in zero_curve],
        color="red",
        linewidth=2.2,
        solid_capstyle="round",
        zorder=4,
    )
    ax.axvline(1.0, color="0.65", linewidth=0.8, linestyle="--")
    ax.axvline(transition, color="#45d7ff", linewidth=1.0, linestyle=":")
    ax.set_xlim(0.75, 1.55)
    ax.set_ylim(-0.015, 0.65)
    ax.set_xticks([0.8, 1.0, 1.2, 1.4])
    ax.set_yticks([0.0, 0.2, 0.4, 0.6])
    ax.tick_params(direction="in", top=True, right=True, length=4, width=0.8, labelsize=11)
    ax.set_xlabel(r"$t_1$", fontsize=13)
    ax.set_ylabel(r"$|E|$", fontsize=13)
    ax.text(1.01, 0.57, r"$t_1=1$", fontsize=11, color="0.25")
    ax.text(1.21, 0.105, r"$\sqrt{t_2^2+(\gamma/2)^2}$", fontsize=10, color="0.25")
    ax.grid(color="0.86", linewidth=0.5)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_spectrum_branches(
    ax: plt.Axes,
    rows: list[dict[str, float]],
    y_key: str,
    linewidth: float = 0.42,
    alpha: float = 0.62,
) -> None:
    for branch_id in sorted({int(row["branch_id"]) for row in rows}):
        branch_rows = [row for row in rows if int(row["branch_id"]) == branch_id]
        branch_rows.sort(key=lambda row: row["t1"])
        ax.plot(
            [row["t1"] for row in branch_rows],
            [row[y_key] for row in branch_rows],
            color="black",
            linewidth=linewidth,
            alpha=alpha,
        )


def count_low_energy_abs_crossings(
    rows: list[dict[str, float]],
    t1_min: float,
    t1_max: float,
    abs_E_max: float,
) -> int:
    """Count |E| order swaps between branch-tracked curves inside a t1 window."""

    by_branch: dict[int, list[tuple[float, float]]] = {}
    for row in rows:
        if t1_min <= float(row["t1"]) <= t1_max:
            by_branch.setdefault(int(row["branch_id"]), []).append(
                (float(row["t1"]), float(row["abs_E"]))
            )
    curves = []
    for points in by_branch.values():
        points.sort()
        values = [abs_E for _, abs_E in points]
        if values and min(values) < abs_E_max:
            curves.append(values)
    count = 0
    for index, first in enumerate(curves):
        for second in curves[index + 1 :]:
            diffs = [a - b for a, b in zip(first, second)]
            count += sum(1 for d, e in zip(diffs, diffs[1:]) if d * e < 0)
    return count


def zero_mode_curve(rows: list[dict[str, float]], transition: float) -> list[tuple[float, float]]:
    by_t1: dict[float, list[float]] = {}
    for row in rows:
        t1 = float(row["t1"])
        if abs(t1) <= transition:
            by_t1.setdefault(t1, []).append(float(row["abs_E"]))
    return [(t1, min(values)) for t1, values in sorted(by_t1.items())]


def spectrum_at_t1(summaries: list[dict[str, float]], target_t1: float) -> dict[str, float]:
    return min(summaries, key=lambda row: abs(row["t1"] - target_t1))


if __name__ == "__main__":
    raise SystemExit(main())
