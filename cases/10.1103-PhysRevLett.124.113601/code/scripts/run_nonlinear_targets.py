#!/usr/bin/env python3
"""Generate source-independent Fig. 4(a) and finite-size diagnostics.

Supplement Fig. S1 omits its pump samples and finite-chain convention.  The
old source-calibrated diagnostic is available only behind an explicit flag and
is never part of the default scientific run.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import eigh_tridiagonal


CODE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
OUTPUT_ROOT = Path(os.environ.get("LDSI_OUTPUT_ROOT", str(DEFAULT_OUTPUT_ROOT))).resolve()
os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT_ROOT / ".cache" / "matplotlib"))
sys.path.insert(0, str(CODE_ROOT))

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from src.ldsi_model import (  # noqa: E402
    GOLDEN_GAMMA,
    aa_diagonals,
    cavity_profile,
    continue_self_consistent_branch,
    solve_self_consistent_state,
)


SCIENTIFIC_CONFIG_PATH = CODE_ROOT / "config" / "scientific_targets.json"
REFERENCE_DIAGNOSTIC_CONFIG_PATH = CODE_ROOT / "config" / "paper_exact.json"
DATA_DIR = OUTPUT_ROOT / "outputs" / "data"
FIGURE_DIR = OUTPUT_ROOT / "outputs" / "figures"
CHECK_DIR = OUTPUT_ROOT / "outputs" / "checks"

PALETTE = {
    0.0: "#222222",
    0.5: "#1F5AA6",
    1.0: "#D1495B",
    1.5: "#2A9D8F",
    1.9: "#E9C46A",
    2.03: "#55C1D3",
}

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "mathtext.fontset": "dejavusans",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 8,
        "axes.linewidth": 0.8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
        "xtick.direction": "out",
        "ytick.direction": "out",
    }
)


def load_config(path: Path = SCIENTIFIC_CONFIG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_publication_figure(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), dpi=400, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")


def solver_parameters(config: dict) -> dict[str, object]:
    global_cfg = config["global"]
    solver_cfg = config["self_consistency"]
    return {
        "atom_number": float(global_cfg["N"]),
        "delta_c": float(global_cfg["delta_c"]),
        "kappa": float(global_cfg["kappa"]),
        "dispersive_coupling": float(global_cfg["U"]),
        # Literal published Eq. (3), distinct from the curve-selected linear convention.
        "shift_factor": 1.0,
        "mixing": float(solver_cfg["mixing"]),
        "tolerance": float(solver_cfg["tolerance"]),
        "max_iterations": int(solver_cfg["max_iterations"]),
    }


def generate_fig4(config: dict) -> dict:
    global_cfg = config["global"]
    fig_cfg = config["fig4"]
    length = int(global_cfg["L"])
    gamma_c = float(global_cfg["gamma_c"])
    eta_descending = np.linspace(
        float(fig_cfg["eta_max"]),
        float(fig_cfg["eta_min"]),
        int(fig_cfg["eta_points"]),
    )
    solver_kwargs = solver_parameters(config)

    rows: list[dict[str, object]] = []
    curves: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    convergence: dict[str, float] = {}
    endpoints: dict[str, float] = {}
    onsets: dict[str, float] = {}
    for chi_value in fig_cfg["photon_chi"]:
        chi = float(chi_value)
        branch = continue_self_consistent_branch(
            eta_descending,
            length=length,
            chi=chi,
            gamma=GOLDEN_GAMMA,
            gamma_c=gamma_c,
            seed_field=2.0 + 0.0j,
            **solver_kwargs,
        )
        ordered = sorted(branch, key=lambda pair: pair[0])
        eta = np.asarray([pair[0] for pair in ordered])
        photons = np.asarray([pair[1].photon_number for pair in ordered])
        curves[chi] = (eta, photons)
        converged_fraction = float(np.mean([pair[1].converged for pair in ordered]))
        convergence[str(chi)] = converged_fraction
        endpoints[str(chi)] = float(photons[-1])
        active = np.flatnonzero(photons > 1e-3)
        onsets[str(chi)] = float(eta[active[0]]) if active.size else float("nan")
        for pump, result in ordered:
            rows.append(
                {
                    "chi_over_J": chi,
                    "eta_over_J": pump,
                    "photon_number": result.photon_number,
                    "field_real": result.field.real,
                    "field_imag": result.field.imag,
                    "state_ipr": result.ipr,
                    "iterations": result.iterations,
                    "converged": int(result.converged),
                    "density_error": result.density_error,
                    "field_error": result.field_error,
                    "cavity_shift_factor": 1.0,
                }
            )
    write_csv(
        DATA_DIR / "fig4a_photon_number.csv",
        [
            "chi_over_J",
            "eta_over_J",
            "photon_number",
            "field_real",
            "field_imag",
            "state_ipr",
            "iterations",
            "converged",
            "density_error",
            "field_error",
            "cavity_shift_factor",
        ],
        rows,
    )

    landscape = np.genfromtxt(
        DATA_DIR / "fig4b_threshold_landscape.csv",
        delimiter=",",
        names=True,
        dtype=None,
        encoding="utf-8",
    )
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.1, 2.7), constrained_layout=True)
    for chi in (0.5, 1.0, 2.03):
        eta, photons = curves[chi]
        ax_a.plot(eta, photons, lw=1.6, color=PALETTE[chi], label=rf"$\chi/J={chi:g}$")
    ax_a.set(
        xlabel=r"$\eta/J$",
        ylabel=r"$|a|^2$",
        xlim=(float(fig_cfg["eta_min"]), float(fig_cfg["eta_max"])),
        ylim=(0.0, 7.2),
    )
    ax_a.legend(loc="upper left", bbox_to_anchor=(0.04, 1.0))
    ax_a.text(-0.10, 1.03, "(a)", transform=ax_a.transAxes, va="bottom", fontweight="bold")

    for chi in (0.0, 0.5, 1.0, 1.5, 1.9, 2.03):
        selected = landscape[np.isclose(landscape["chi_over_J"], chi)]
        values = np.asarray(selected["eta_c_over_J"], dtype=float)
        values[~np.isfinite(values) | (values > 0.7)] = np.nan
        ax_b.plot(
            selected["gamma_c"],
            values,
            lw=1.25,
            color=PALETTE[chi],
            label=rf"$\chi/J={chi:g}$",
        )
    ax_b.set(xlabel=r"$\gamma_c$", ylabel=r"$\eta_c/J$", xlim=(0.0, 1.0), ylim=(0.0, 0.62))
    ax_b.legend(loc="upper center", ncol=2, fontsize=6.8)
    ax_b.text(-0.10, 1.03, "(b)", transform=ax_b.transAxes, va="bottom", fontweight="bold")
    save_publication_figure(fig, FIGURE_DIR / "fig4_phase_response")
    plt.close(fig)

    acceptance = {
        "all_branches_mostly_converged": all(value >= 0.98 for value in convergence.values()),
        "clean_onset_source_window": 0.18 <= onsets["0.5"] <= 0.22,
        "moderate_disorder_onset_source_window": 0.14 <= onsets["1.0"] <= 0.19,
        "localized_branch_active_at_small_pump": onsets["2.03"] <= 0.01,
        "endpoint_photon_numbers_source_scale": (
            4.0 <= endpoints["0.5"] <= 5.2
            and 5.0 <= endpoints["1.0"] <= 6.3
            and 6.0 <= endpoints["2.03"] <= 7.1
        ),
    }
    check = {
        "status": "passed" if all(acceptance.values()) else "failed",
        "target_id": "T003",
        "panel": "FIG004A",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "independent_numerics",
        "formula_gate": "reconstructed",
        "convention": {
            "cavity_shift_factor": 1.0,
            "reason": "literal published Eq. (3) reproduces the published nonlinear onset and endpoint scale",
            "linear_panel_b_shift_factor": 1.0,
            "linear_panel_b_note": "the same literal Eq. (3) convention is used; its disagreement with the plotted Fig. 4(b) curve is retained as source-discrepancy evidence",
        },
        "metrics": {
            "converged_fraction_by_chi": convergence,
            "onset_eta_over_J_by_chi": onsets,
            "photon_number_at_eta_0p25_by_chi": endpoints,
        },
        "acceptance": acceptance,
    }
    write_json(CHECK_DIR / "fig4a_photon_number.json", check)
    return check


def generate_figs1(config: dict) -> dict:
    """Generate the non-scoring, source-calibrated supplement diagnostic."""
    global_cfg = config["global"]
    fig_cfg = config["figs1"]
    length = int(global_cfg["L"])
    gamma = float(global_cfg["gamma"])
    gamma_c = float(global_cfg["gamma_c"])
    solver_kwargs = solver_parameters(config)
    # The supplement labels sites but does not state the finite-chain origin.
    # This origin shift maps the irrational AA phase convention to the visible
    # localized center in panel (e); it remains an explicitly reconstructed
    # presentation parameter, not a hidden model change.
    site_origin_shift = int(fig_cfg["site_origin_shift"])
    lattice_phase = float(2.0 * np.pi * gamma * site_origin_shift)
    sites = np.arange(length)
    # Fig. S1 omits eta. These source-calibrated samples reproduce its visible
    # peak-height scale while remaining on the superradiant branch.
    above_pump = {0.0: 0.25, 0.5: 0.198, 1.0: 0.164, 1.9: 0.02, 2.03: 0.12}

    rows: list[dict[str, object]] = []
    densities: dict[tuple[float, str], np.ndarray] = {}
    metrics: dict[str, dict[str, float | bool]] = {}
    for chi_value in fig_cfg["chi"]:
        chi = float(chi_value)
        normal = solve_self_consistent_state(
            length,
            chi,
            0.0,
            gamma=gamma,
            gamma_c=gamma_c,
            phase=lattice_phase,
            **solver_kwargs,
        )
        superradiant = continue_self_consistent_branch(
            [above_pump[chi]],
            length=length,
            chi=chi,
            gamma=gamma,
            gamma_c=gamma_c,
            phase=lattice_phase,
            seed_field=2.0 + 0.0j,
            **solver_kwargs,
        )[0][1]
        normal_density = np.abs(normal.state) ** 2
        superradiant_density = np.abs(superradiant.state) ** 2
        densities[(chi, "normal")] = normal_density
        densities[(chi, "superradiant")] = superradiant_density
        metrics[str(chi)] = {
            "normal_ipr": normal.ipr,
            "superradiant_ipr": superradiant.ipr,
            "normal_peak": float(np.max(normal_density)),
            "superradiant_peak": float(np.max(superradiant_density)),
            "above_eta_over_J": above_pump[chi],
            "above_photon_number": superradiant.photon_number,
            "above_converged": superradiant.converged,
        }
        for phase, pump, result, density in (
            ("normal", 0.0, normal, normal_density),
            ("superradiant", above_pump[chi], superradiant, superradiant_density),
        ):
            for site, probability in enumerate(density):
                rows.append(
                    {
                        "chi_over_J": chi,
                        "phase": phase,
                        "eta_over_J": pump,
                        "site": site,
                        "probability": float(probability),
                        "state_ipr": result.ipr,
                        "photon_number": result.photon_number,
                        "converged": int(result.converged),
                        "gamma": gamma,
                        "lattice_phase": lattice_phase,
                        "site_origin_shift": site_origin_shift,
                        "boundary": "open",
                        "cavity_shift_factor": 1.0,
                    }
                )
    write_csv(
        DATA_DIR / "figs1_density_profiles.csv",
        [
            "chi_over_J",
            "phase",
            "eta_over_J",
            "site",
            "probability",
            "state_ipr",
            "photon_number",
            "converged",
            "gamma",
            "lattice_phase",
            "site_origin_shift",
            "boundary",
            "cavity_shift_factor",
        ],
        rows,
    )

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.25), constrained_layout=True)
    axes_flat = axes.ravel()
    for panel_index, chi in enumerate((0.0, 0.5, 1.0, 1.9, 2.03)):
        ax = axes_flat[panel_index]
        normal = densities[(chi, "normal")]
        superradiant = densities[(chi, "superradiant")]
        if chi == 2.03:
            center = int(np.argmax(normal))
            mask = (sites >= center - 15) & (sites <= center + 15)
        else:
            mask = np.ones(length, dtype=bool)
        ax.plot(sites[mask], normal[mask], color="#2457E6", lw=1.15, label=r"$\eta=0$")
        ax.plot(
            sites[mask],
            superradiant[mask],
            color="#E63946",
            lw=1.0,
            ls=":",
            label=rf"$\eta/J={above_pump[chi]:g}$",
        )
        ax.set(xlabel=r"$j$", ylabel=r"$|\phi_0^j|^2$")
        ax.text(0.03, 0.94, f"({chr(97 + panel_index)})  $\\chi/J={chi:g}$", transform=ax.transAxes, va="top")
        ax.legend(loc="upper right", fontsize=6.7)
    axes_flat[-1].axis("off")
    save_publication_figure(fig, FIGURE_DIR / "figs1_density_profiles")
    plt.close(fig)

    acceptance = {
        "all_profiles_normalized": all(
            abs(float(np.sum(density)) - 1.0) < 1e-10 for density in densities.values()
        ),
        "all_above_branches_converged": all(bool(item["above_converged"]) for item in metrics.values()),
        "localized_state_sharpened": metrics["2.03"]["superradiant_ipr"] > metrics["2.03"]["normal_ipr"],
        "localized_peak_enhanced": metrics["2.03"]["superradiant_peak"] > metrics["2.03"]["normal_peak"],
        "source_peak_scale_reproduced": (
            0.008 <= metrics["0.0"]["superradiant_peak"] <= 0.012
            and 0.010 <= metrics["0.5"]["superradiant_peak"] <= 0.022
            and 0.040 <= metrics["1.0"]["superradiant_peak"] <= 0.080
            and 0.15 <= metrics["1.9"]["superradiant_peak"] <= 0.35
            and 0.65 <= metrics["2.03"]["superradiant_peak"] <= 0.90
        ),
    }
    check = {
        "status": "passed" if all(acceptance.values()) else "failed",
        "target_id": "T004",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "mixed_independent_and_source_reference",
        "formula_gate": "reconstructed",
        "reconstruction_policy": {
            "reason": "Supplement Fig. S1 omits pump samples and solver details.",
            "sample_calibration": "eta samples selected against the approximate source-panel peak-height scale",
            "normal_eta_over_J": 0.0,
            "superradiant_eta_over_J": above_pump,
            "gamma": "irrational golden ratio",
            "site_origin_shift": site_origin_shift,
            "lattice_phase": lattice_phase,
            "boundary": "open",
            "cavity_shift_factor": 1.0,
        },
        "metrics": metrics,
        "acceptance": acceptance,
    }
    write_json(CHECK_DIR / "figs1_density_profiles.json", check)
    return check


def generate_finite_size_diagnostic(config: dict) -> dict:
    global_cfg = config["global"]
    gamma_c = float(global_cfg["gamma_c"])
    rows: list[dict[str, object]] = []
    size_metrics: dict[str, dict[str, float]] = {}
    for length in (300, 377, 1000, 3000, 10000):
        size_metrics[str(length)] = {}
        for chi in (1.0, 2.03):
            diagonal, off_diagonal = aa_diagonals(length, chi, gamma=GOLDEN_GAMMA)
            _, vector = eigh_tridiagonal(
                diagonal,
                off_diagonal,
                select="i",
                select_range=(0, 0),
                check_finite=False,
            )
            probability = vector[:, 0] ** 2
            ipr = float(probability @ probability)
            self_overlap = float(probability @ cavity_profile(length, gamma_c))
            size_metrics[str(length)][f"ipr_chi_{chi}"] = ipr
            size_metrics[str(length)][f"abs_self_overlap_chi_{chi}"] = abs(self_overlap)
            rows.append(
                {
                    "diagnostic": "finite_size",
                    "L": length,
                    "chi_over_J": chi,
                    "trap_edge_offset_over_J": 0.0,
                    "ipr": ipr,
                    "self_overlap": self_overlap,
                }
            )

    length = 377
    trap_edge_offset = 0.01
    trap_curvature = trap_edge_offset / (0.5 * (length - 1)) ** 2
    trap_metrics: dict[str, dict[str, float]] = {}
    for chi in (1.0, 1.5, 1.9, 1.99, 2.03, 2.5):
        trap_metrics[str(chi)] = {}
        for label, curvature in (("untrapped", 0.0), ("weak_trap", trap_curvature)):
            diagonal, off_diagonal = aa_diagonals(
                length,
                chi,
                gamma=GOLDEN_GAMMA,
                harmonic_trap=curvature,
            )
            _, vector = eigh_tridiagonal(
                diagonal,
                off_diagonal,
                select="i",
                select_range=(0, 0),
                check_finite=False,
            )
            probability = vector[:, 0] ** 2
            ipr = float(probability @ probability)
            trap_metrics[str(chi)][label] = ipr
            rows.append(
                {
                    "diagnostic": label,
                    "L": length,
                    "chi_over_J": chi,
                    "trap_edge_offset_over_J": trap_edge_offset if curvature else 0.0,
                    "ipr": ipr,
                    "self_overlap": float(probability @ cavity_profile(length, gamma_c)),
                }
            )
    write_csv(
        DATA_DIR / "finite_size_and_trap.csv",
        ["diagnostic", "L", "chi_over_J", "trap_edge_offset_over_J", "ipr", "self_overlap"],
        rows,
    )

    extended_ipr = [size_metrics[str(length)]["ipr_chi_1.0"] for length in (300, 377, 1000, 3000, 10000)]
    localized_ipr = [size_metrics[str(length)]["ipr_chi_2.03"] for length in (300, 377, 1000, 3000, 10000)]
    localized_overlap = [
        size_metrics[str(length)]["abs_self_overlap_chi_2.03"] for length in (300, 377, 1000, 3000, 10000)
    ]
    acceptance = {
        "extended_ipr_decreases_with_size": bool(np.all(np.diff(extended_ipr) < 0.0)),
        "localized_ipr_size_stable": bool((max(localized_ipr) - min(localized_ipr)) / np.mean(localized_ipr) < 0.08),
        "localized_self_overlap_remains_finite": bool(min(localized_overlap) > 0.35),
        "weak_trap_preserves_extended_side": bool(trap_metrics["1.0"]["weak_trap"] < 0.02),
        "weak_trap_preserves_deep_localization": bool(abs(
            trap_metrics["2.5"]["weak_trap"] - trap_metrics["2.5"]["untrapped"]
        ) / trap_metrics["2.5"]["untrapped"] < 0.02),
    }
    check = {
        "status": "passed" if all(acceptance.values()) else "failed",
        "target_id": "D001",
        "parameter_match": "diagnostic_only",
        "source_claim": "main text states no finite-size effect from L=300 to 10000 and weak-trap robustness",
        "metrics": {
            "finite_size": size_metrics,
            "weak_trap_ipr": trap_metrics,
            "trap_edge_offset_over_J": trap_edge_offset,
            "trap_curvature_over_J": trap_curvature,
        },
        "acceptance": acceptance,
    }
    write_json(CHECK_DIR / "finite_size_and_trap.json", check)
    return check


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-deferred-reference-output",
        action="store_true",
        help="also generate the non-scoring Fig. S1 source-calibrated diagnostic",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    config = load_config()
    checks = {
        "fig4a": generate_fig4(config),
        "finite_size_and_trap": generate_finite_size_diagnostic(config),
    }
    if args.include_deferred_reference_output:
        checks["figs1_reference_diagnostic"] = generate_figs1(
            load_config(REFERENCE_DIAGNOSTIC_CONFIG_PATH)
        )
    summary = {
        "status": "passed" if all(item["status"] == "passed" for item in checks.values()) else "failed",
        "runtime_seconds": time.perf_counter() - started,
        "backend": "numpy-scipy-matplotlib",
        "machine_scope": "local_m4",
        "checks": {key: value["status"] for key, value in checks.items()},
        "scientific_target_ids": ["T003", "D001"],
        "deferred_reference_target_ids": ["T004"] if args.include_deferred_reference_output else [],
        "source_calibrated_inputs_in_scientific_targets": False,
    }
    write_json(CHECK_DIR / "nonlinear_targets_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
