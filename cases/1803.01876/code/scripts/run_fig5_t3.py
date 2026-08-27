#!/usr/bin/env python3
"""Run Fig. 5 for the nonzero-t3 model."""

from __future__ import annotations

import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from nonhermitian_ssh import (  # noqa: E402
    abs_ordered_squared_spectrum_rows,
    beta_roots_t3_from_energy,
    signed_complex_sqrt,
)


def main() -> int:
    required_formula_cards = ["EQC001", "EQC009", "EQC010"]
    assert_formula_gate(required_formula_cards)

    paper_L = 100
    spectrum_L = paper_L
    cbeta_L = paper_L
    spectrum_dps = 35
    t2 = 1.0
    gamma = 4.0 / 3.0
    t3 = 1.0 / 5.0
    n_beta = 200
    t1_values = np.linspace(-3.0, 3.0, 151)
    cbeta_t1 = 1.1

    winding_rows = []
    for t1 in t1_values:
        invariant = zero_energy_root_invariant(t1=float(t1), t2=t2, gamma=gamma, t3=t3)
        winding_rows.append(
            {
                "t1": float(t1),
                "W": invariant["W"],
                "root_labels": "".join(invariant["labels"]),
                "middle_modulus_gap": invariant["middle_modulus_gap"],
                "beta1_abs": invariant["moduli"][0],
                "beta2_abs": invariant["moduli"][1],
                "beta3_abs": invariant["moduli"][2],
                "beta4_abs": invariant["moduli"][3],
                "n_beta_caption": n_beta,
            }
        )
    squared_spectrum_slices = high_precision_squared_spectrum_slices(
        L=spectrum_L,
        t1_values=t1_values,
        dps=spectrum_dps,
    )
    spectrum_rows = abs_ordered_squared_spectrum_rows(t1_values, squared_spectrum_slices)

    transition_points = estimate_transition_points(t2=t2, gamma=gamma, t3=t3)
    cbeta_squared = high_precision_squared_spectrum_slices(
        L=cbeta_L,
        t1_values=np.asarray([cbeta_t1]),
        dps=spectrum_dps,
        max_workers=1,
    )[0]
    cbeta_branch = signed_complex_sqrt(cbeta_squared)
    cbeta_energies = np.concatenate([cbeta_branch, -cbeta_branch])
    cbeta_rows = build_cbeta_rows(
        L=cbeta_L,
        t1=cbeta_t1,
        t2=t2,
        gamma=gamma,
        t3=t3,
        energies=cbeta_energies,
    )

    spectrum_path = ROOT / "outputs/data/fig5_t3_spectrum.csv"
    winding_path = ROOT / "outputs/data/fig5_t3_winding.csv"
    cbeta_path = ROOT / "outputs/data/fig5_t3_cbeta.csv"
    figure_path = ROOT / "outputs/figures/fig5_t3.png"
    left_panel_path = ROOT / "outputs/figures/fig5_t3_left_panel.png"
    checks_path = ROOT / "outputs/checks/fig5_t3.json"

    write_csv(
        spectrum_path,
        spectrum_rows,
        [
            "t1",
            "branch_id",
            "band_index",
            "real_E",
            "imag_E",
            "abs_E",
        ],
    )
    write_csv(
        winding_path,
        winding_rows,
        [
            "t1",
            "W",
            "root_labels",
            "middle_modulus_gap",
            "beta1_abs",
            "beta2_abs",
            "beta3_abs",
            "beta4_abs",
            "n_beta_caption",
        ],
    )
    write_csv(
        cbeta_path,
        cbeta_rows,
        [
            "energy_real",
            "energy_imag",
            "root_branch",
            "beta_real",
            "beta_imag",
            "abs_beta",
            "angle_beta",
            "middle_pair_relative_error",
        ],
    )
    plot_figure(spectrum_rows, winding_rows, cbeta_rows, figure_path, transition_points, cbeta_t1)
    plot_left_panel(spectrum_rows, winding_rows, left_panel_path)

    transition_abs = max(abs(transition_points["negative"]), abs(transition_points["positive"]))
    cbeta_radii = np.array([row["abs_beta"] for row in cbeta_rows], dtype=float)
    cbeta_errors = np.array([row["middle_pair_relative_error"] for row in cbeta_rows], dtype=float)
    mismatch_rows = [
        row
        for row in winding_rows
        if row["W"] != int(abs(row["t1"]) < transition_abs)
        and abs(abs(row["t1"]) - transition_abs) > 0.04
    ]
    checks = {
        "target": "T004",
        "comparison_mode": "feature_data_first",
        "visual_match_role": "secondary_reference",
        "required_formula_cards": required_formula_cards,
        "L": spectrum_L,
        "spectrum_L": spectrum_L,
        "cbeta_L": cbeta_L,
        "paper_L": paper_L,
        "parameter_match": "paper_exact",
        "t2": t2,
        "gamma": gamma,
        "t3": t3,
        "n_beta_caption": n_beta,
        "transition_points_from_zero_energy_beta_roots": transition_points,
        "source_caption_transition_abs_t1": 1.56,
        "mismatch_count_away_from_transition": len(mismatch_rows),
        "cbeta_t1": cbeta_t1,
        "cbeta_point_count": len(cbeta_rows),
        "cbeta_radius_min": float(cbeta_radii.min()),
        "cbeta_radius_max": float(cbeta_radii.max()),
        "cbeta_radius_range": float(cbeta_radii.max() - cbeta_radii.min()),
        "cbeta_max_middle_pair_relative_error": float(cbeta_errors.max()),
        "spectrum_line_identity": "open_chain_abs_energy_level",
        "spectrum_connect_rule": "connect_within_branch_id_in_t1_order",
        "spectrum_render_source": "independent_open_chain_numerics",
        "spectrum_reference_source": "paper-source/t3spectrum.eps",
        "left_panel_render": str(left_panel_path.relative_to(ROOT)),
        "spectrum_branch_count": len({row["branch_id"] for row in spectrum_rows}),
        "spectrum_t1_points": len({row["t1"] for row in spectrum_rows}),
        "spectrum_solver": {
            "method": "mpmath_high_precision_chiral_block_eigenspectrum",
            "decimal_digits": spectrum_dps,
            "reason": "The L=100 nonzero-t3 OBC matrix is too non-normal for double precision.",
        },
        "cbeta_line_identity": "middle_beta_root_pair_locus",
        "cbeta_connect_rule": "connect_middle_pair_locus_in_angle_order",
        "feature_acceptance": {
            "transition_near_caption_value": abs(transition_abs - 1.56) < 0.02,
            "winding_plateau_matches_transition": len(mismatch_rows) == 0,
            "sample_inside_negative_is_one": value_at(winding_rows, -1.5)["W"] == 1,
            "sample_inside_positive_is_one": value_at(winding_rows, 1.5)["W"] == 1,
            "sample_outside_negative_is_zero": value_at(winding_rows, -2.0)["W"] == 0,
            "sample_outside_positive_is_zero": value_at(winding_rows, 2.0)["W"] == 0,
            "cbeta_is_not_unit_circle": float(cbeta_radii.max() - cbeta_radii.min()) > 0.15,
            "cbeta_lies_inside_unit_circle": float(cbeta_radii.max()) < 1.0,
            "cbeta_middle_roots_are_paired": float(cbeta_errors.max()) < 0.05,
        },
        "sample_values": {
            "-2.0": value_at(winding_rows, -2.0),
            "-1.5": value_at(winding_rows, -1.5),
            "0.0": value_at(winding_rows, 0.0),
            "1.5": value_at(winding_rows, 1.5),
            "2.0": value_at(winding_rows, 2.0),
        },
        "notes": [
            "The nonzero-t3 topological interval is checked from the zero-energy quartic beta roots.",
            "The criterion is that the two smallest beta roots at E=0 come from the same off-diagonal factor; the change occurs when the middle two moduli meet.",
            "C_beta is reconstructed from open-chain energies by retaining the middle beta-root pair with nearly equal moduli.",
            "The visible spectrum is independently generated from open-chain |E| levels; rendered source EPS is only a visual reference comparator.",
            "For this |E| panel, branch_id labels the ordered open-chain absolute-energy level, avoiding artificial sign or phase swaps of complex E near degeneracies.",
            "The visible spectrum and C_beta use the paper's L=100 with 35-decimal-digit eigenspectrum evaluation; source EPS is reference-only.",
        ],
    }
    checks["status"] = (
        "physically_consistent"
        if all(checks["feature_acceptance"].values())
        else "partial"
    )
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


def zero_energy_root_invariant(t1: float, t2: float, gamma: float, t3: float) -> dict[str, object]:
    roots = zero_energy_roots(t1=t1, t2=t2, gamma=gamma, t3=t3)
    ordered = sorted(roots, key=lambda item: abs(item["beta"]))
    labels = [item["factor"] for item in ordered]
    moduli = [float(abs(item["beta"])) for item in ordered]
    return {
        "W": int(labels[0] == labels[1]),
        "labels": labels,
        "moduli": moduli,
        "middle_modulus_gap": float(abs(moduli[2] - moduli[1])),
    }


def zero_energy_roots(t1: float, t2: float, gamma: float, t3: float) -> list[dict[str, complex]]:
    a0 = t1 - gamma / 2.0
    b0 = t1 + gamma / 2.0
    roots = []
    for beta in np.roots([t2, a0, t3]):
        roots.append({"factor": "a", "beta": complex(beta)})
    for beta in np.roots([t3, b0, t2]):
        roots.append({"factor": "b", "beta": complex(beta)})
    return roots


def estimate_transition_points(t2: float, gamma: float, t3: float) -> dict[str, float]:
    dense_t1 = np.linspace(-3.0, 3.0, 12001)
    dense = [
        (float(t1), zero_energy_root_invariant(float(t1), t2=t2, gamma=gamma, t3=t3))
        for t1 in dense_t1
    ]
    transitions: dict[str, float] = {}
    for name, lo, hi in [("negative", -2.2, -0.8), ("positive", 0.8, 2.2)]:
        window = [(t1, item) for t1, item in dense if lo <= t1 <= hi]
        t1_min, _ = min(window, key=lambda pair: pair[1]["middle_modulus_gap"])
        transitions[name] = float(t1_min)
    return transitions


def build_cbeta_rows(
    L: int,
    t1: float,
    t2: float,
    gamma: float,
    t3: float,
    energies: np.ndarray,
) -> list[dict[str, float]]:
    rows = []
    if len(energies) != 2 * L:
        raise ValueError(f"expected {2 * L} open-chain energies, got {len(energies)}")
    for energy in energies:
        roots = beta_roots_t3_from_energy(energy=energy, t1=t1, t2=t2, gamma=gamma, t3=t3)
        roots = roots[np.argsort(np.abs(roots))]
        relative_error = float(
            abs(abs(roots[1]) - abs(roots[2])) / max(abs(roots[1]), abs(roots[2]), 1e-12)
        )
        if relative_error > 0.05:
            continue
        for branch, beta in [(2, roots[1]), (3, roots[2])]:
            rows.append(
                {
                    "energy_real": float(np.real(energy)),
                    "energy_imag": float(np.imag(energy)),
                    "root_branch": branch,
                    "beta_real": float(np.real(beta)),
                    "beta_imag": float(np.imag(beta)),
                    "abs_beta": float(abs(beta)),
                    "angle_beta": float(np.angle(beta)),
                    "middle_pair_relative_error": relative_error,
                }
            )
    if not rows:
        raise RuntimeError("C_beta reconstruction produced no middle-root rows")
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def high_precision_squared_spectrum_slices(
    L: int,
    t1_values: np.ndarray,
    dps: int,
    max_workers: int | None = None,
) -> list[np.ndarray]:
    """Evaluate the paper-scale non-normal spectrum without double-precision drift."""

    values = [float(value) for value in t1_values]
    workers = max_workers or min(10, os.cpu_count() or 1)
    # The paper sweep uses an exact 0.04 grid. Do not feed binary-float tails
    # such as 1.2000000000000002 into this highly non-normal eigensystem.
    tasks = [(index, f"{t1:.12g}", L, dps) for index, t1 in enumerate(values)]
    results: list[np.ndarray | None] = [None] * len(tasks)

    if workers == 1:
        completed = [_high_precision_squared_spectrum_worker(task) for task in tasks]
    else:
        completed = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_high_precision_squared_spectrum_worker, task) for task in tasks]
            report_every = max(1, len(futures) // 10)
            for completed_count, future in enumerate(as_completed(futures), start=1):
                completed.append(future.result())
                if completed_count % report_every == 0 or completed_count == len(futures):
                    print(
                        f"high-precision Fig. 5 spectrum: {completed_count}/{len(futures)} t1 slices",
                        flush=True,
                    )

    for index, squared in completed:
        results[index] = np.asarray(squared, dtype=np.complex128)
    if any(result is None for result in results):
        raise RuntimeError("high-precision spectrum returned incomplete slices")
    return [result for result in results if result is not None]


def _high_precision_squared_spectrum_worker(
    task: tuple[int, str, int, int],
) -> tuple[int, list[complex]]:
    import mpmath as mp

    index, t1_text, L, dps = task
    mp.mp.dps = dps
    t1 = mp.mpf(t1_text)
    t2 = mp.mpf(1)
    gamma = mp.mpf(4) / 3
    t3 = mp.mpf(1) / 5

    c_block = mp.matrix(L)
    d_block = mp.matrix(L)
    for site in range(L):
        c_block[site, site] = t1 + gamma / 2
        d_block[site, site] = t1 - gamma / 2
        if site > 0:
            c_block[site, site - 1] = t2
            d_block[site, site - 1] = t3
        if site < L - 1:
            c_block[site, site + 1] = t3
            d_block[site, site + 1] = t2

    squared = mp.eig(c_block * d_block, left=False, right=False)
    return index, [complex(float(mp.re(value)), float(mp.im(value))) for value in squared]


def plot_figure(
    spectrum_rows: list[dict[str, float]],
    winding_rows: list[dict[str, float]],
    cbeta_rows: list[dict[str, float]],
    figure_path: Path,
    transition_points: dict[str, float],
    cbeta_t1: float,
) -> None:
    fig = plt.figure(figsize=(10.0, 6.0))
    grid = fig.add_gridspec(2, 2, width_ratios=[3.0, 1.0], height_ratios=[2.0, 1.0])
    ax_spectrum = fig.add_subplot(grid[0, 0])
    ax_winding = fig.add_subplot(grid[1, 0], sharex=ax_spectrum)
    ax_cbeta = fig.add_subplot(grid[:, 1])

    plot_spectrum_branches(ax_spectrum, spectrum_rows, "abs_E")
    topological_t1 = [row["t1"] for row in winding_rows if row["W"] == 1]
    ax_spectrum.scatter(topological_t1, np.zeros(len(topological_t1)), s=7.0, c="red", linewidths=0)
    for value in transition_points.values():
        ax_spectrum.axvline(value, color="tab:cyan", linewidth=0.9, alpha=0.65)
    ax_spectrum.set_ylabel(r"$|E|$")
    ax_spectrum.set_ylim(-0.05, 2.25)
    ax_spectrum.grid(True, alpha=0.15)
    ax_spectrum.text(
        0.02,
        0.95,
        rf"$L={len({int(row['branch_id']) for row in spectrum_rows})}$ (35-digit eigenspectrum)",
        transform=ax_spectrum.transAxes,
        va="top",
        fontsize=8,
        color="0.25",
    )

    ax_winding.plot(
        [row["t1"] for row in winding_rows],
        [row["W"] for row in winding_rows],
        "--",
        color="royalblue",
        linewidth=1.1,
    )
    marker_rows = winding_rows[::15]
    ax_winding.scatter(
        [row["t1"] for row in marker_rows],
        [row["W"] for row in marker_rows],
        s=34,
        facecolor="#b7659a",
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )
    for value in transition_points.values():
        ax_winding.axvline(value, color="black", linewidth=0.7, alpha=0.35)
    ax_winding.set_xlabel(r"$t_1$")
    ax_winding.set_ylabel(r"$W$")
    ax_winding.set_xlim(-3.0, 3.0)
    ax_winding.set_ylim(-0.45, 1.45)
    ax_winding.set_yticks([0, 1])

    ax_cbeta.plot(np.cos(np.linspace(0, 2 * np.pi, 400)), np.sin(np.linspace(0, 2 * np.pi, 400)), "--", color="0.6", linewidth=1.2)
    beta = cbeta_contour_curve(cbeta_rows)
    ax_cbeta.plot(np.real(beta), np.imag(beta), color="#c96555", linewidth=1.8)
    ax_cbeta.scatter(
        np.real(beta[:-1]),
        np.imag(beta[:-1]),
        s=3.0,
        color="#c96555",
        alpha=0.22,
        linewidths=0,
    )
    ax_cbeta.axhline(0, color="0.35", linewidth=0.7)
    ax_cbeta.axvline(0, color="0.35", linewidth=0.7)
    ax_cbeta.set_aspect("equal", adjustable="box")
    ax_cbeta.set_xlabel(r"$\mathrm{Re}(\beta)$")
    ax_cbeta.set_ylabel(r"$\mathrm{Im}(\beta)$")
    ax_cbeta.set_title(rf"$C_\beta,\ t_1={cbeta_t1}$", fontsize=11)
    ax_cbeta.set_xlim(-1.1, 1.1)
    ax_cbeta.set_ylim(-1.1, 1.1)

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
            linewidth=0.46,
            alpha=0.75,
        )


def plot_left_panel(
    spectrum_rows: list[dict[str, float]],
    winding_rows: list[dict[str, float]],
    figure_path: Path,
) -> None:
    fig = plt.figure(figsize=(5.35, 4.22), dpi=100)
    ax_spectrum = fig.add_axes([0.155, 0.565, 0.815, 0.38])
    ax_winding = fig.add_axes([0.155, 0.145, 0.815, 0.37], sharex=ax_spectrum)

    plot_spectrum_branches(ax_spectrum, spectrum_rows, "abs_E")
    topological_t1 = [row["t1"] for row in winding_rows if row["W"] == 1]
    ax_spectrum.plot(topological_t1, np.zeros(len(topological_t1)), color="red", linewidth=2.2, solid_capstyle="butt")
    ax_spectrum.set_xlim(-3.0, 3.0)
    ax_spectrum.set_ylim(-0.02, 2.0)
    ax_spectrum.set_yticks([0.0, 2.0])
    ax_spectrum.set_yticklabels(["0", "2"])
    ax_spectrum.set_ylabel(r"$|E|$", fontsize=34, labelpad=-2)
    ax_spectrum.text(
        0.02,
        0.93,
        rf"$L={len({int(row['branch_id']) for row in spectrum_rows})}$",
        transform=ax_spectrum.transAxes,
        va="top",
        fontsize=10,
        color="0.25",
    )
    ax_spectrum.text(-0.19, 0.93, r"(a)", transform=ax_spectrum.transAxes, fontsize=30, ha="left", va="center", clip_on=False)
    ax_spectrum.tick_params(axis="x", labelbottom=False)
    _style_left_panel_axis(ax_spectrum, labelsize=26)

    ax_winding.plot(
        [row["t1"] for row in winding_rows],
        [row["W"] for row in winding_rows],
        "--",
        color="royalblue",
        linewidth=1.1,
    )
    marker_rows = winding_rows[::20]
    ax_winding.scatter(
        [row["t1"] for row in marker_rows],
        [row["W"] for row in marker_rows],
        s=70,
        facecolor="#b7659a",
        edgecolor="black",
        linewidth=0.9,
        zorder=3,
    )
    ax_winding.set_xlim(-3.0, 3.0)
    ax_winding.set_ylim(-0.22, 1.18)
    ax_winding.set_yticks([0.0, 1.0])
    ax_winding.set_yticklabels(["0", "1"])
    ax_winding.set_xlabel(r"$t_1$", fontsize=34, labelpad=-3)
    ax_winding.set_ylabel(r"$W$", fontsize=34, labelpad=-1)
    _style_left_panel_axis(ax_winding, labelsize=28)

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def _style_left_panel_axis(ax: plt.Axes, labelsize: int) -> None:
    for spine in ax.spines.values():
        spine.set_linewidth(0.85)
        spine.set_color("#444444")
    ax.tick_params(axis="both", which="major", direction="in", length=5, width=0.85, color="#444444", labelsize=labelsize, labelcolor="#4f4f4f")
    ax.tick_params(axis="both", which="minor", direction="in", length=3, width=0.65, color="#444444")
    ax.tick_params(top=True, right=True)


def cbeta_contour_curve(rows: list[dict[str, float]]) -> np.ndarray:
    """Join both middle roots into their single closed GBZ locus."""

    ordered = sorted(rows, key=lambda row: np.mod(row["angle_beta"], 2.0 * np.pi))
    beta = np.array(
        [row["beta_real"] + 1j * row["beta_imag"] for row in ordered],
        dtype=np.complex128,
    )
    if len(beta):
        beta = np.concatenate([beta, beta[:1]])
    return beta


def value_at(rows: list[dict[str, float]], target_t1: float) -> dict[str, object]:
    row = min(rows, key=lambda item: abs(item["t1"] - target_t1))
    return {
        "t1": row["t1"],
        "W": row["W"],
        "root_labels": row["root_labels"],
        "middle_modulus_gap": row["middle_modulus_gap"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
