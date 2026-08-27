#!/usr/bin/env python3
"""Run the Fig. 3 beta-root, C_beta, and skin-effect target."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nonhermitian_ssh import (  # noqa: E402
    analytic_left_zero_mode_profile,
    analytic_transition,
    beta_roots_from_energy,
    cell_profile,
    generalized_brillouin_radius,
    open_chain_eigensystem,
)


def main() -> int:
    required_formula_cards = ["EQC003", "EQC006", "EQC007"]
    assert_formula_gate(required_formula_cards)

    L = 40
    t2 = 1.0
    gamma = 4.0 / 3.0
    t1_main = 1.0
    t1_transition = analytic_transition(t2=t2, gamma=gamma)
    energy_values = np.linspace(0.0, 2.35, 500)
    beta_points = 360

    beta_rows = build_beta_root_rows(
        energy_values=energy_values,
        t1_values=[("main_t1_1", t1_main), ("transition", t1_transition)],
        t2=t2,
        gamma=gamma,
    )
    cbeta_rows = build_cbeta_rows(t1=t1_main, t2=t2, gamma=gamma, beta_points=beta_points)
    profile_rows, profile_checks = build_profile_rows(L=L, t1=t1_main, t2=t2, gamma=gamma)

    beta_path = ROOT / "outputs/data/fig3_beta_roots.csv"
    cbeta_path = ROOT / "outputs/data/fig3_cbeta.csv"
    profiles_path = ROOT / "outputs/data/fig3_profiles.csv"
    figure_path = ROOT / "outputs/figures/fig3_beta_skin.png"
    absbeta_panel_path = ROOT / "outputs/figures/fig3_absbeta_panel.png"
    cbeta_panel_path = ROOT / "outputs/figures/fig3_cbeta_panel.png"
    profile_panel_path = ROOT / "outputs/figures/fig3_profile_panel.png"
    checks_path = ROOT / "outputs/checks/fig3_beta_skin.json"

    write_csv(beta_path, beta_rows, ["series", "t1", "E", "root_index", "beta_real", "beta_imag", "abs_beta"])
    write_csv(cbeta_path, cbeta_rows, ["curve", "t1", "theta", "beta_real", "beta_imag", "abs_beta"])
    write_csv(profiles_path, profile_rows, ["profile_id", "kind", "cell", "amplitude", "eigenvalue_real", "eigenvalue_imag", "abs_eigenvalue"])
    plot_figure(
        beta_rows=beta_rows,
        cbeta_rows=cbeta_rows,
        profile_rows=profile_rows,
        figure_path=figure_path,
        t1_main=t1_main,
        t1_transition=t1_transition,
        gamma=gamma,
    )
    plot_absbeta_panel(beta_rows=beta_rows, figure_path=absbeta_panel_path)
    plot_cbeta_panel(cbeta_rows=cbeta_rows, figure_path=cbeta_panel_path)
    plot_profile_panel(profile_rows=profile_rows, figure_path=profile_panel_path)

    radius = generalized_brillouin_radius(t1=t1_main, gamma=gamma)
    checks = {
        "target": "T002",
        "comparison_mode": "feature_data_first",
        "visual_match_role": "secondary_reference",
        "required_formula_cards": required_formula_cards,
        "L": L,
        "t1_main": t1_main,
        "t1_transition": t1_transition,
        "t2": t2,
        "gamma": gamma,
        "cbeta_radius": radius,
        "absbeta_panel_render": str(absbeta_panel_path.relative_to(ROOT)),
        "cbeta_panel_render": str(cbeta_panel_path.relative_to(ROOT)),
        "profile_panel_render": str(profile_panel_path.relative_to(ROOT)),
        "expected_radius_t1_1": np.sqrt(0.2),
        "radius_error": abs(radius - np.sqrt(0.2)),
        "beta_equal_modulus_error": beta_equal_modulus_error(beta_rows, series="main_t1_1", radius=radius),
        "transition_low_energy_radius_error": transition_low_energy_radius_error(beta_rows, t1_transition, gamma),
        "profile_checks": profile_checks,
        "feature_acceptance": {
            "cbeta_radius_matches": bool(abs(radius - np.sqrt(0.2)) < 1e-12),
            "bulk_beta_equal_modulus": bool(beta_equal_modulus_error(beta_rows, series="main_t1_1", radius=radius) < 1e-12),
            "transition_beta_touches_low_energy": bool(transition_low_energy_radius_error(beta_rows, t1_transition, gamma) < 1e-12),
            "zero_mode_left_localized": profile_checks["zero_profile_left_localized"],
            "bulk_profiles_left_localized": profile_checks["bulk_profiles_left_localized"],
        },
        "status": "physically_consistent"
        if profile_checks["bulk_profiles_left_localized"] and profile_checks["zero_profile_left_localized"]
        else "partial",
        "notes": [
            "Formula gate is checked before running.",
            "Panel (a) uses beta roots from Eq. (bulkeigen).",
            "Panel (b) uses the verified C_beta radius.",
            "Panel (c) uses the analytic zero-mode profile plus deterministic bulk right eigenvectors.",
            "Published EPS panels are rendered for visual reference but not digitized.",
            "Acceptance is based on feature-level numeric checks, not pixel similarity.",
        ],
    }
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))
    return 0 if checks["status"] == "physically_consistent" else 1


def assert_formula_gate(required_formula_cards: list[str]) -> None:
    gate = json.loads((ROOT / "outputs/checks/formula_verification.json").read_text())
    formulas = gate["formulas"]
    closed = [
        formula_id
        for formula_id in required_formula_cards
        if not formulas.get(formula_id, {}).get("numeric_gate", False)
    ]
    if closed:
        raise RuntimeError(f"formula gate is closed for: {', '.join(closed)}")


def build_beta_root_rows(
    energy_values: np.ndarray,
    t1_values: list[tuple[str, float]],
    t2: float,
    gamma: float,
) -> list[dict[str, float | str | int]]:
    rows = []
    for series, t1 in t1_values:
        beta_1, beta_2 = beta_roots_from_energy(energy_values, t1=t1, t2=t2, gamma=gamma)
        for root_index, beta_values in [(1, beta_1), (2, beta_2)]:
            for energy, beta in zip(energy_values, beta_values):
                rows.append(
                    {
                        "series": series,
                        "t1": t1,
                        "E": float(np.real(energy)),
                        "root_index": root_index,
                        "beta_real": float(np.real(beta)),
                        "beta_imag": float(np.imag(beta)),
                        "abs_beta": float(abs(beta)),
                    }
                )
    return rows


def build_cbeta_rows(t1: float, t2: float, gamma: float, beta_points: int) -> list[dict[str, float | str]]:
    radius = generalized_brillouin_radius(t1=t1, gamma=gamma)
    angles = np.linspace(0.0, 2.0 * np.pi, beta_points, endpoint=True)
    rows = []
    for curve, r_value in [("C_beta", radius), ("unit_circle", 1.0)]:
        for theta in angles:
            beta = r_value * np.exp(1j * theta)
            rows.append(
                {
                    "curve": curve,
                    "t1": t1,
                    "theta": float(theta),
                    "beta_real": float(np.real(beta)),
                    "beta_imag": float(np.imag(beta)),
                    "abs_beta": float(abs(beta)),
                }
            )
    return rows


def build_profile_rows(L: int, t1: float, t2: float, gamma: float) -> tuple[list[dict[str, float | str | int]], dict[str, object]]:
    rows = []
    zero_cell_profile = analytic_left_zero_mode_profile(L=L, t1=t1, t2=t2, gamma=gamma)
    zero_site_profile = zero_mode_site_profile(unit_cell_count=L, t1=t1, t2=t2, gamma=gamma)
    for site_index, amplitude in enumerate(zero_site_profile, start=1):
        rows.append(
            {
                "profile_id": "zero_mode",
                "kind": "analytic_zero_site_resolved",
                "cell": float(site_index) / 2.0,
                "amplitude": float(amplitude),
                "eigenvalue_real": 0.0,
                "eigenvalue_imag": 0.0,
                "abs_eigenvalue": 0.0,
            }
        )

    eigenvalues, eigenvectors = open_chain_eigensystem(L=L, t1=t1, t2=t2, gamma=gamma)
    order = np.argsort(np.abs(eigenvalues))
    bulk_indices = [idx for idx in order if abs(eigenvalues[idx]) > 0.05]
    chosen = np.linspace(0, len(bulk_indices) - 1, 8, dtype=int)
    left_weight_ratios = []
    for profile_number, bulk_pos in enumerate(chosen, start=1):
        eig_index = int(bulk_indices[int(bulk_pos)])
        profile = cell_profile(eigenvectors[:, eig_index])
        left_weight = float(np.sum(profile[:8] ** 2))
        right_weight = float(np.sum(profile[-8:] ** 2))
        left_weight_ratios.append(left_weight / max(right_weight, 1e-15))
        site_profile = right_eigenvector_site_profile(eigenvectors[:, eig_index])
        for site_index, amplitude in enumerate(site_profile, start=1):
            rows.append(
                {
                    "profile_id": f"bulk_{profile_number}",
                    "kind": "bulk_right_eigenvector",
                    "cell": float(site_index) / 2.0,
                    "amplitude": float(amplitude),
                    "eigenvalue_real": float(np.real(eigenvalues[eig_index])),
                    "eigenvalue_imag": float(np.imag(eigenvalues[eig_index])),
                    "abs_eigenvalue": float(abs(eigenvalues[eig_index])),
                }
            )

    checks = {
        "zero_profile_left_localized": bool(zero_cell_profile[0] > 0.99 and zero_cell_profile[8] < 1e-3),
        "zero_profile_cell_2_ratio": float(zero_cell_profile[1] / zero_cell_profile[0]),
        "expected_zero_profile_cell_2_ratio": abs(-(t1 - gamma / 2.0) / t2),
        "zero_profile_sites_total": int(len(zero_site_profile)),
        "zero_profile_site_even_sublattice_is_zero": bool(np.max(zero_site_profile[1::2]) < 1e-12),
        "bulk_left_right_weight_ratios": left_weight_ratios,
        "bulk_profiles_left_localized": bool(min(left_weight_ratios) > 10.0),
    }
    return rows, checks


def zero_mode_site_profile(unit_cell_count: int, t1: float, t2: float, gamma: float) -> np.ndarray:
    """Return the 2L-sublattice zero-mode profile for the plotted coordinate n."""

    beta_zero = abs(-(t1 - gamma / 2.0) / t2)
    sites = np.arange(2 * unit_cell_count)
    profile = np.zeros(2 * unit_cell_count, dtype=float)
    occupied = sites % 2 == 0
    profile[occupied] = beta_zero ** (sites[occupied] // 2)
    scale = np.max(profile)
    return profile / scale if scale else profile


def right_eigenvector_site_profile(vector: np.ndarray) -> np.ndarray:
    """Return the 2L-sublattice right-eigenvector profile for the plotted coordinate n."""

    profile = np.abs(vector)
    scale = np.max(profile)
    return profile / scale if scale else profile


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_figure(
    beta_rows: list[dict[str, float | str | int]],
    cbeta_rows: list[dict[str, float | str]],
    profile_rows: list[dict[str, float | str | int]],
    figure_path: Path,
    t1_main: float,
    t1_transition: float,
    gamma: float,
) -> None:
    fig = plt.figure(figsize=(13.5, 4.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.05])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[0, 2])

    plot_beta_roots(ax0, beta_rows, t1_main=t1_main, t1_transition=t1_transition, gamma=gamma)
    plot_cbeta(ax1, cbeta_rows)
    plot_profiles(ax2, profile_rows)

    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)


def plot_beta_roots(ax: plt.Axes, rows: list[dict[str, float | str | int]], t1_main: float, t1_transition: float, gamma: float) -> None:
    colors = {
        ("main_t1_1", 1): "#2457b2",
        ("main_t1_1", 2): "#c86428",
        ("transition", 1): "#9fb4ba",
        ("transition", 2): "#e3aa9c",
    }
    for series in ["transition", "main_t1_1"]:
        for root_index in [1, 2]:
            selected = [row for row in rows if row["series"] == series and row["root_index"] == root_index]
            ax.plot(
                [row["E"] for row in selected],
                [row["abs_beta"] for row in selected],
                color=colors[(series, root_index)],
                linewidth=1.8 if series == "main_t1_1" else 1.4,
                alpha=0.95 if series == "main_t1_1" else 0.55,
            )
    r_main = generalized_brillouin_radius(t1=t1_main, gamma=gamma)
    r_transition = generalized_brillouin_radius(t1=t1_transition, gamma=gamma)
    ax.axhline(r_transition, color="#d8b4aa", linewidth=1.0, alpha=0.7)
    ax.axhline(r_main, color="#264fb0", linewidth=1.0, alpha=0.75)
    ax.set_xlim(0.0, 2.35)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel(r"$E$")
    ax.set_ylabel(r"$|\beta|$")
    ax.text(0.05, 0.92, "(a)", transform=ax.transAxes, fontsize=13)
    ax.text(1.52, 0.76, r"$|\beta_1|$", fontsize=13)
    ax.text(1.56, 0.18, r"$|\beta_2|$", fontsize=13)
    ax.text(0.55, r_main + 0.045, r"$|\beta_1|=|\beta_2|$", fontsize=11)


def plot_absbeta_panel(beta_rows: list[dict[str, float | str | int]], figure_path: Path) -> None:
    fig = plt.figure(figsize=(13.5, 8.9), dpi=100)
    ax = fig.add_axes([0.074, 0.095, 0.924, 0.865])

    styles = {
        ("transition", 1): {"color": "#b9c8cb", "linewidth": 4.2, "alpha": 0.85, "zorder": 2},
        ("transition", 2): {"color": "#e5b8ad", "linewidth": 4.2, "alpha": 0.75, "zorder": 2},
        ("main_t1_1", 1): {"color": "#315fb4", "linewidth": 4.4, "alpha": 1.0, "zorder": 4},
        ("main_t1_1", 2): {"color": "#cc6d2d", "linewidth": 4.4, "alpha": 1.0, "zorder": 4},
    }
    for series in ["transition", "main_t1_1"]:
        for root_index in [1, 2]:
            selected = _select_beta_branch(beta_rows, series, root_index)
            style = styles[(series, root_index)]
            ax.plot(
                [row["E"] for row in selected],
                [row["abs_beta"] for row in selected],
                solid_capstyle="round",
                **style,
            )

    f_energy, g_energy, radius = _equal_modulus_window(beta_rows, series="main_t1_1")
    ax.scatter([f_energy, g_energy], [radius, radius], s=150, color="black", zorder=7)

    ax.set_xlim(0.0, 2.4)
    ax.set_ylim(0.0, 1.0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color("#6f7478")
        ax.spines[side].set_linewidth(1.4)
    ax.tick_params(axis="both", which="major", direction="in", length=9, width=1.2, color="#6f7478", labelsize=44)
    ax.tick_params(axis="both", which="minor", direction="in", length=5, width=0.9, color="#6f7478")
    ax.xaxis.set_major_locator(MultipleLocator(0.5))
    ax.xaxis.set_minor_locator(MultipleLocator(0.1))
    ax.set_yticks(np.arange(0.0, 1.0, 0.2))
    ax.yaxis.set_minor_locator(MultipleLocator(0.05))
    ax.set_xlabel("")
    ax.set_ylabel("")

    ax.text(-0.08, 0.94, r"(a)", transform=ax.transAxes, fontsize=66, ha="left", va="center", clip_on=False)
    ax.text(0.04, 0.94, r"$|\beta|$", transform=ax.transAxes, fontsize=70, ha="left", va="center", clip_on=False)
    ax.text(0.98, -0.075, r"$E$", transform=ax.transAxes, fontsize=70, ha="right", va="center", clip_on=False)
    ax.text(f_energy - 0.08, radius + 0.03, r"$\mathrm{F}$", fontsize=56, ha="center", va="center")
    ax.text(g_energy + 0.06, radius + 0.03, r"$\mathrm{G}$", fontsize=56, ha="center", va="center")
    ax.text(0.98, radius - 0.06, r"$|\beta_1|=|\beta_2|$", fontsize=58, ha="center", va="center")
    ax.text(1.62, 0.77, r"$|\beta_1|$", fontsize=58, ha="center", va="center")
    ax.text(1.70, 0.18, r"$|\beta_2|$", fontsize=58, ha="center", va="center")

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def _select_beta_branch(
    rows: list[dict[str, float | str | int]],
    series: str,
    root_index: int,
) -> list[dict[str, float | str | int]]:
    selected = [
        row
        for row in rows
        if row["series"] == series and int(row["root_index"]) == root_index
    ]
    return sorted(selected, key=lambda row: float(row["E"]))


def _equal_modulus_window(rows: list[dict[str, float | str | int]], series: str) -> tuple[float, float, float]:
    by_energy: dict[float, dict[int, float]] = {}
    for row in rows:
        if row["series"] != series:
            continue
        energy = float(row["E"])
        root_index = int(row["root_index"])
        by_energy.setdefault(energy, {})[root_index] = float(row["abs_beta"])

    equal_rows = [
        (energy, pair[1], pair[2])
        for energy, pair in by_energy.items()
        if 1 in pair and 2 in pair and abs(pair[1] - pair[2]) < 1e-10
    ]
    if not equal_rows:
        raise RuntimeError(f"no equal-modulus beta-root window found for {series}")
    energies = [item[0] for item in equal_rows]
    radii = [(item[1] + item[2]) / 2.0 for item in equal_rows]
    return min(energies), max(energies), float(np.mean(radii))


def plot_cbeta(ax: plt.Axes, rows: list[dict[str, float | str]]) -> None:
    for curve, style, color in [("unit_circle", "--", "gray"), ("C_beta", "-", "#2858b8")]:
        selected = [row for row in rows if row["curve"] == curve]
        ax.plot(
            [row["beta_real"] for row in selected],
            [row["beta_imag"] for row in selected],
            linestyle=style,
            color=color,
            linewidth=1.8,
        )
    selected = [row for row in rows if row["curve"] == "C_beta"]
    lower = [row for row in selected if np.pi <= float(row["theta"]) <= 2.0 * np.pi]
    ax.plot([row["beta_real"] for row in lower], [row["beta_imag"] for row in lower], color="#c86428", linewidth=2.0)
    ax.axhline(0.0, color="black", linewidth=0.7, alpha=0.45)
    ax.axvline(0.0, color="black", linewidth=0.7, alpha=0.45)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel(r"$\mathrm{Re}(\beta)$")
    ax.set_ylabel(r"$\mathrm{Im}(\beta)$")
    ax.text(0.05, 0.92, "(b)", transform=ax.transAxes, fontsize=13)
    ax.text(-0.52, 0.33, r"$C_\beta$", fontsize=13)


def plot_cbeta_panel(cbeta_rows: list[dict[str, float | str]], figure_path: Path) -> None:
    fig = plt.figure(figsize=(13.5, 13.5), dpi=100)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.25, 1.25)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    tick_values = np.arange(-1.2, 1.21, 0.1)
    ax.plot([-1.25, 1.25], [0.0, 0.0], color="#6f7478", linewidth=1.4, zorder=1)
    ax.plot([0.0, 0.0], [-1.25, 1.25], color="#6f7478", linewidth=1.4, zorder=1)
    for value in tick_values:
        if abs(value) < 1e-12:
            continue
        tick = 0.012 if round(value, 1) not in {-1.0, 1.0} else 0.02
        ax.plot([value, value], [0.0, tick], color="#6f7478", linewidth=0.9, zorder=1)
        ax.plot([0.0, tick], [value, value], color="#6f7478", linewidth=0.9, zorder=1)

    unit = _select_curve(cbeta_rows, "unit_circle")
    cbeta = _select_curve(cbeta_rows, "C_beta")
    upper = [row for row in cbeta if 0.0 <= float(row["theta"]) <= np.pi]
    lower = [row for row in cbeta if np.pi <= float(row["theta"]) <= 2.0 * np.pi]

    ax.plot(
        [row["beta_real"] for row in unit],
        [row["beta_imag"] for row in unit],
        color="#7d7f82",
        linewidth=4.0,
        linestyle=(0, (4.0, 3.0)),
        dash_capstyle="butt",
        zorder=2,
    )
    ax.plot(
        [row["beta_real"] for row in upper],
        [row["beta_imag"] for row in upper],
        color="#315fb4",
        linewidth=4.2,
        solid_capstyle="round",
        zorder=4,
    )
    ax.plot(
        [row["beta_real"] for row in lower],
        [row["beta_imag"] for row in lower],
        color="#cc6d2d",
        linewidth=4.2,
        solid_capstyle="round",
        zorder=4,
    )
    ax.scatter(
        [-0.4472135954999579, 0.4472135954999579],
        [0.0, 0.0],
        s=150,
        color="black",
        zorder=6,
    )

    _add_tangent_arrow(ax, radius=1.0, theta=0.78, color="black", scale=92)
    _add_tangent_arrow(ax, radius=0.4472135954999579, theta=0.83, color="black", scale=92)
    _add_tangent_arrow(ax, radius=0.4472135954999579, theta=3.98, color="black", scale=92)

    ax.text(-1.10, 1.10, r"(b)", fontsize=70, ha="left", va="center")
    ax.text(0.02, 1.15, r"$\mathrm{Im}(\beta)$", fontsize=70, ha="center", va="center")
    ax.text(0.80, 0.08, r"$\mathrm{Re}(\beta)$", fontsize=62, ha="left", va="center")
    ax.text(-1.02, -0.11, r"$-1.0$", fontsize=48, ha="center", va="center")
    ax.text(1.00, -0.11, r"$1.0$", fontsize=48, ha="center", va="center")
    ax.text(-0.11, 1.00, r"$1.0$", fontsize=48, ha="center", va="center")
    ax.text(-0.10, -1.01, r"$-1.0$", fontsize=48, ha="center", va="center")
    ax.text(-0.34, 0.42, r"$C_\beta$", fontsize=62, ha="center", va="center")
    ax.text(0.36, 0.42, r"$\beta_1$", fontsize=58, ha="center", va="center")
    ax.text(0.32, -0.40, r"$\beta_2$", fontsize=58, ha="center", va="center")
    ax.text(-0.35, 0.00, r"$\mathrm{F}$", fontsize=54, ha="center", va="center")
    ax.text(0.36, 0.00, r"$\mathrm{G}$", fontsize=54, ha="center", va="center")

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def _select_curve(rows: list[dict[str, float | str]], curve: str) -> list[dict[str, float | str]]:
    return [row for row in rows if row["curve"] == curve]


def _add_tangent_arrow(ax: plt.Axes, radius: float, theta: float, color: str, scale: float) -> None:
    delta = 0.07
    start = np.array([radius * np.cos(theta - delta), radius * np.sin(theta - delta)])
    end = np.array([radius * np.cos(theta + delta), radius * np.sin(theta + delta)])
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "-|>",
            "color": color,
            "linewidth": 0.0,
            "mutation_scale": scale,
            "shrinkA": 0.0,
            "shrinkB": 0.0,
        },
        zorder=7,
    )


def plot_profiles(ax: plt.Axes, rows: list[dict[str, float | str | int]]) -> None:
    zero = [row for row in rows if row["profile_id"] == "zero_mode"]
    ax.plot([row["cell"] for row in zero], [row["amplitude"] for row in zero], color="red", linewidth=1.1)
    for profile_id in sorted({row["profile_id"] for row in rows if row["kind"] == "bulk_right_eigenvector"}):
        selected = [row for row in rows if row["profile_id"] == profile_id]
        ax.plot([row["cell"] for row in selected], [row["amplitude"] for row in selected], color="black", linewidth=0.7, alpha=0.45)
    ax.set_xlim(1, 40)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel(r"$n$")
    ax.set_ylabel(r"$|\psi|$")
    ax.text(0.02, 0.92, "(c)", transform=ax.transAxes, fontsize=13)


def plot_profile_panel(profile_rows: list[dict[str, float | str | int]], figure_path: Path) -> None:
    fig = plt.figure(figsize=(7.95, 6.22), dpi=100)
    ax = fig.add_axes([0.117, 0.1205, 0.853, 0.8585])
    _style_profile_axis(ax, labelsize=28)

    zero = _select_profile(profile_rows, "zero_mode")
    ax.plot(
        [row["cell"] for row in zero],
        [row["amplitude"] for row in zero],
        color="#ff2f2f",
        linewidth=1.0,
        solid_capstyle="butt",
        zorder=4,
    )
    label_color = "#4f4f4f"
    ax.text(-0.12, 0.94, r"(c)", transform=ax.transAxes, fontsize=28, color=label_color, ha="left", va="center", clip_on=False)
    ax.text(-0.095, 0.50, r"$|\psi|$", transform=ax.transAxes, rotation=90, fontsize=30, color=label_color, ha="center", va="center", clip_on=False)
    ax.text(0.64, -0.067, r"$n$", transform=ax.transAxes, fontsize=40, color=label_color, ha="center", va="center")

    inset = fig.add_axes([0.40, 0.38, 0.515, 0.54])
    _style_profile_axis(inset, labelsize=17, inset=True)
    for profile_id in _bulk_profile_ids(profile_rows):
        selected = _select_profile(profile_rows, profile_id)
        inset.plot(
            [row["cell"] for row in selected],
            [row["amplitude"] for row in selected],
            color="#303030",
            linewidth=0.28,
            alpha=0.24,
            zorder=2,
        )

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=100)
    plt.close(fig)


def _style_profile_axis(ax: plt.Axes, labelsize: int, inset: bool = False) -> None:
    ax.set_xlim(0.0, 40.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_color("#555555")
        spine.set_linewidth(0.62 if inset else 0.75)
    ax.tick_params(axis="both", which="major", direction="in", length=7 if not inset else 4, width=0.58, color="#555555", labelsize=labelsize, labelcolor="#4f4f4f")
    ax.tick_params(axis="both", which="minor", direction="in", length=3 if not inset else 2, width=0.45, color="#555555")
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_minor_locator(MultipleLocator(5))
    if inset:
        ax.set_yticks([0.0, 0.2, 0.6, 1.0])
        ax.set_yticklabels(["0", "0.2", "0.6", "1"])
        ax.xaxis.set_ticks_position("both")
        ax.yaxis.set_ticks_position("both")
        ax.tick_params(labelright=False, labeltop=False)
    else:
        ax.set_ylim(0.0, 1.06)
        ax.set_xticks([10, 20, 30, 40])
        ax.set_yticks(np.arange(0.0, 1.01, 0.2))
        ax.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])
        ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax.xaxis.set_ticks_position("both")
        ax.yaxis.set_ticks_position("both")
        ax.tick_params(labeltop=False, labelright=False)


def _select_profile(rows: list[dict[str, float | str | int]], profile_id: str) -> list[dict[str, float | str | int]]:
    selected = [row for row in rows if row["profile_id"] == profile_id]
    return sorted(selected, key=lambda row: float(row["cell"]))


def _bulk_profile_ids(rows: list[dict[str, float | str | int]]) -> list[str]:
    return sorted(
        {
            str(row["profile_id"])
            for row in rows
            if row["kind"] == "bulk_right_eigenvector"
        },
        key=lambda value: int(value.split("_")[-1]),
    )


def beta_equal_modulus_error(rows: list[dict[str, float | str | int]], series: str, radius: float) -> float:
    selected = [
        row
        for row in rows
        if row["series"] == series and 0.34 < row["E"] < 1.70
    ]
    return float(max(abs(row["abs_beta"] - radius) for row in selected))


def transition_low_energy_radius_error(rows: list[dict[str, float | str | int]], t1_transition: float, gamma: float) -> float:
    radius = generalized_brillouin_radius(t1=t1_transition, gamma=gamma)
    selected = [
        row
        for row in rows
        if row["series"] == "transition" and row["E"] < 0.02
    ]
    return float(min(abs(row["abs_beta"] - radius) for row in selected))


if __name__ == "__main__":
    raise SystemExit(main())
