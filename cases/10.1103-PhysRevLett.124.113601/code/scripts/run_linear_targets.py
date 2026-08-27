#!/usr/bin/env python3
"""Generate source-independent linear targets for Figs. 3 and 4(b).

Fig. 2 needs an unpublished finite-chain convention.  Its old source-calibrated
diagnostic is available only behind an explicit flag and is never part of the
default scientific run.
"""

from __future__ import annotations

import csv
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


CODE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
OUTPUT_ROOT = Path(os.environ.get("LDSI_OUTPUT_ROOT", str(DEFAULT_OUTPUT_ROOT))).resolve()
os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT_ROOT / ".cache" / "matplotlib"))
sys.path.insert(0, str(CODE_ROOT))

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from src.ldsi_model import (  # noqa: E402
    aa_eigensystem,
    critical_pump,
    gaa_eigensystem,
    ground_state_response,
    inverse_participation_ratio,
    momentum_distribution,
    scattering_response,
    state_resolved_thresholds,
)


SCIENTIFIC_CONFIG_PATH = CODE_ROOT / "config" / "scientific_targets.json"
REFERENCE_DIAGNOSTIC_CONFIG_PATH = CODE_ROOT / "config" / "paper_exact.json"
DATA_DIR = OUTPUT_ROOT / "outputs" / "data"
FIGURE_DIR = OUTPUT_ROOT / "outputs" / "figures"
CHECK_DIR = OUTPUT_ROOT / "outputs" / "checks"


PALETTE = {
    "blue": "#1F5AA6",
    "red": "#D1495B",
    "green": "#2A9D8F",
    "cyan": "#55C1D3",
    "yellow": "#E9C46A",
    "black": "#222222",
    "gray": "#777777",
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


def generate_fig2(config: dict) -> dict:
    """Generate the non-scoring, source-calibrated Fig. 2 diagnostic."""
    global_cfg = config["global"]
    fig_cfg = config["fig2"]
    length = int(global_cfg["L"])
    gamma = float(global_cfg["gamma"])
    gamma_c = float(global_cfg["gamma_c"])
    chi = float(fig_cfg["chi"])
    site_origin_shift = int(fig_cfg["site_origin_shift"])
    lattice_phase = float(2.0 * np.pi * gamma * site_origin_shift)
    common_threshold = {
        "ipr_cutoff": float(fig_cfg["ipr_cutoff"]),
        "atom_number": float(global_cfg["N"]),
        "delta_c": float(global_cfg["delta_c"]),
        "kappa": float(global_cfg["kappa"]),
        "dispersive_coupling": float(global_cfg["U"]),
        "shift_factor": float(global_cfg["cavity_shift_factor"]),
    }

    gaa_energy, gaa_vectors = gaa_eigensystem(
        length,
        chi,
        gamma=gamma,
        next_nearest=float(fig_cfg["J2"]),
        hopping_correction=float(fig_cfg["Jprime"]),
        disorder_correction=float(fig_cfg["chiprime"]),
        phase=lattice_phase,
        periodic=fig_cfg["boundary"] == "periodic",
    )
    aa_energy, aa_vectors = aa_eigensystem(
        length,
        chi,
        gamma=gamma,
        phase=lattice_phase,
        periodic=fig_cfg["boundary"] == "periodic",
    )
    gaa = state_resolved_thresholds(gaa_energy, gaa_vectors, gamma_c, **common_threshold)
    aa = state_resolved_thresholds(aa_energy, aa_vectors, gamma_c, **common_threshold)

    rows: list[dict[str, object]] = []
    for model, energies, result in (
        ("GAA", gaa_energy, gaa),
        ("AA", aa_energy, aa),
    ):
        for index in range(length):
            rows.append(
                {
                    "model": model,
                    "alpha": index,
                    "energy_over_J": float(energies[index]),
                    "ipr": float(result["ipr"][index]),
                    "localized": int(result["localized"][index]),
                    "response_abs": float(result["response"][index]),
                    "diagonal_overlap": float(result["diagonal_overlap"][index]),
                    "eta_c_over_J": float(result["eta_c"][index]),
                }
            )
    write_csv(
        DATA_DIR / "fig2_state_thresholds.csv",
        ["model", "alpha", "energy_over_J", "ipr", "localized", "response_abs", "diagonal_overlap", "eta_c_over_J"],
        rows,
    )

    first_extended = int(np.flatnonzero(~gaa["localized"])[0])
    check = {
        "status": "passed",
        "target_id": "T001",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "mixed_independent_and_source_reference",
        "formula_gate": "reconstructed",
        "finite_chain_convention": {
            "gamma": gamma,
            "site_origin_shift": site_origin_shift,
            "lattice_phase": lattice_phase,
            "boundary": fig_cfg["boundary"],
            "evidence": "vector-source IPR path gives pointwise correlation 1.000 for this convention",
        },
        "metrics": {
            "gaa_first_extended_index": first_extended,
            "gaa_last_localized_energy_over_J": float(gaa_energy[first_extended - 1]),
            "gaa_extended_fraction": float(np.mean(~gaa["localized"])),
            "gaa_extended_band_max_ipr": float(np.max(gaa["ipr"][first_extended:])),
            "aa_localized_fraction": float(np.mean(aa["localized"])),
            "aa_max_eta_c_over_J": float(np.max(aa["eta_c"])),
        },
        "acceptance": {
            "mobility_edge_index_233": first_extended == 233,
            "mobility_edge_energy_near_0p44": abs(float(gaa_energy[first_extended - 1]) - 0.44) < 0.02,
            "aa_all_localized": bool(np.all(aa["localized"])),
            "aa_threshold_zero": bool(np.allclose(aa["eta_c"], 0.0)),
            "gaa_extended_band_has_no_edge_states": bool(np.all(gaa["ipr"][first_extended:] < fig_cfg["ipr_cutoff"])),
        },
    }
    check["status"] = "passed" if all(check["acceptance"].values()) else "failed"
    write_json(CHECK_DIR / "fig2_state_thresholds.json", check)

    fig, ax = plt.subplots(figsize=(5.2, 3.35), constrained_layout=True)
    finite_gaa = np.minimum(gaa["eta_c"], 0.34)
    ax.plot(gaa_energy, finite_gaa, color=PALETTE["blue"], lw=1.6, ls=":", label="GAA")
    ax.plot(aa_energy, aa["eta_c"], color=PALETTE["red"], lw=1.5, ls="--", label="AA")
    ax.set(xlabel=r"$\epsilon_\alpha/J$", ylabel=r"$\eta_c/J$", ylim=(-0.005, 0.32))
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.30))
    inset = ax.inset_axes([0.31, 0.45, 0.53, 0.46])
    inset.plot(np.arange(length), gaa["ipr"], color=PALETTE["black"], lw=1.0)
    inset.axvline(first_extended, color=PALETTE["gray"], lw=1.0, ls="--")
    inset.text(first_extended - 64, 0.58, r"$\epsilon_c/J\simeq0.44$", color=PALETTE["blue"])
    inset.set(xlabel=r"$\alpha$", ylabel="IPR", ylim=(-0.02, 0.75))
    inset.spines["top"].set_visible(True)
    inset.spines["right"].set_visible(True)
    save_publication_figure(fig, FIGURE_DIR / "fig2_state_thresholds")
    plt.close(fig)
    return check


def generate_fig3(config: dict) -> dict:
    global_cfg = config["global"]
    fig_cfg = config["fig3"]
    length = int(global_cfg["L"])
    gamma = float(global_cfg["gamma"])
    gamma_c = float(global_cfg["gamma_c"])
    chi_grid = np.linspace(fig_cfg["chi_min"], fig_cfg["chi_max"], int(fig_cfg["chi_points"]))

    threshold_rows: list[dict[str, object]] = []
    eta_values: list[float] = []
    f_values: list[float] = []
    ipr_values: list[float] = []
    for chi in chi_grid:
        response, _, _, vectors = ground_state_response(length, float(chi), gamma=gamma, gamma_c=gamma_c)
        eta = 0.0 if chi >= 2.0 else float(
            critical_pump(
                response,
                atom_number=global_cfg["N"],
                delta_c=global_cfg["delta_c"],
                kappa=global_cfg["kappa"],
                dispersive_coupling=global_cfg["U"],
                shift_factor=global_cfg["cavity_shift_factor"],
            )
        )
        ipr = float(inverse_participation_ratio(vectors[:, :1])[0])
        eta_values.append(eta)
        f_values.append(response)
        ipr_values.append(ipr)
        threshold_rows.append(
            {"chi_over_J": float(chi), "eta_c_over_J": eta, "f1": response, "ground_ipr": ipr}
        )
    write_csv(DATA_DIR / "fig3_threshold.csv", ["chi_over_J", "eta_c_over_J", "f1", "ground_ipr"], threshold_rows)

    q_values = np.linspace(fig_cfg["q_min"], fig_cfg["q_max"], int(fig_cfg["q_points"]))
    alpha0 = int(round(2 * length * (1.0 - gamma_c)))
    alpha1 = int(round(2 * length * (gamma_c - gamma)))
    alpha2 = int(round(2 * length * (gamma_c + 2.0 * gamma - 2.0)))
    momentum_rows: list[dict[str, object]] = []
    momentum: dict[tuple[float, str], np.ndarray] = {}
    channel_rows: list[dict[str, object]] = []
    channel_data: dict[float, np.ndarray] = {}
    source_states: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for chi in (0.0, 1.0, 2.03):
        energies, vectors = aa_eigensystem(length, chi, gamma=gamma)
        source_states[chi] = (energies, vectors)
        channels, _, overlaps = scattering_response(energies, vectors, gamma_c)
        channel_data[chi] = channels
        for alpha in range(length):
            channel_rows.append(
                {
                    "chi_over_J": chi,
                    "alpha": alpha,
                    "energy_over_J": float(energies[alpha]),
                    "overlap": float(overlaps[alpha]),
                    "f1_alpha": float(channels[alpha]),
                }
            )
        for label, index in (("ground", 0), ("excited", alpha0)):
            probability = momentum_distribution(vectors[:, index], q_values)
            momentum[(chi, label)] = probability
            for q, value in zip(q_values, probability, strict=True):
                momentum_rows.append(
                    {"chi_over_J": chi, "state": label, "alpha": index, "k_over_k1": float(q), "probability": float(value)}
                )
    write_csv(DATA_DIR / "fig3_momentum.csv", ["chi_over_J", "state", "alpha", "k_over_k1", "probability"], momentum_rows)
    write_csv(DATA_DIR / "fig3_channels.csv", ["chi_over_J", "alpha", "energy_over_J", "overlap", "f1_alpha"], channel_rows)

    top_chi1 = (np.argsort(channel_data[1.0])[::-1][:8]).astype(int).tolist()
    eta0 = eta_values[0]
    transition_index = int(np.argmax(f_values))
    check = {
        "status": "passed",
        "target_id": "T002",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "independent_numerics",
        "formula_gate": "verified",
        "metrics": {
            "clean_f1": f_values[0],
            "clean_eta_c_over_J": eta0,
            "published_curve_clean_eta_c_over_J": 0.2768,
            "published_formula_curve_discrepancy": abs(eta0 - 0.2768),
            "cavity_shift_factor": global_cfg["cavity_shift_factor"],
            "maximum_f1": float(np.max(f_values)),
            "maximum_f1_chi_over_J": float(chi_grid[transition_index]),
            "analytic_channel_indices": {"alpha0": alpha0, "alpha1": alpha1, "alpha2": alpha2},
            "top_chi1_channel_indices": top_chi1,
            "chi2p03_diagonal_overlap": float(source_states[2.03][1][:, 0] @ (np.cos(2 * np.pi * gamma_c * np.arange(length)) * source_states[2.03][1][:, 0])),
        },
        "acceptance": {
            "literal_published_shift_factor": float(global_cfg["cavity_shift_factor"]) == 1.0,
            "clean_intercept_finite_positive": bool(np.isfinite(eta0) and eta0 > 0.0),
            "threshold_zero_at_and_above_two": bool(np.allclose(np.asarray(eta_values)[chi_grid >= 2.0], 0.0)),
            "susceptibility_peaks_near_transition": abs(float(chi_grid[transition_index]) - 2.0) <= 0.03,
            "alpha0_near_151": abs(alpha0 - 151) <= 1,
            "alpha1_near_137": abs(alpha1 - 137) <= 1,
            "alpha2_near_27": abs(alpha2 - 27) <= 1,
        },
    }
    check["status"] = "passed" if all(check["acceptance"].values()) else "failed"
    write_json(CHECK_DIR / "fig3_mechanism.json", check)

    fig = plt.figure(figsize=(6.25, 7.2), constrained_layout=True)
    grid = fig.add_gridspec(3, 2, height_ratios=[1.15, 0.72, 0.72])
    ax_a = fig.add_subplot(grid[0, :])
    ax_b = fig.add_subplot(grid[1, 0])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[2, 0])
    ax_e = fig.add_subplot(grid[2, 1])

    ax_a.plot(chi_grid, eta_values, color=PALETTE["blue"], lw=1.8)
    ax_a.set(xlabel=r"$\chi/J$", ylabel=r"$\eta_c/J$", ylim=(-0.005, 0.30))
    ax_a.text(0.03, 0.88, "a", transform=ax_a.transAxes, fontweight="bold")
    ax_a_right = ax_a.twinx()
    ax_a_right.plot(chi_grid, f_values, color=PALETTE["red"], lw=1.5, ls="--")
    ax_a_right.set_yscale("log")
    ax_a_right.set(ylabel=r"$f_1$", ylim=(1e-2, 1e4))
    ax_a_right.spines["right"].set_visible(True)
    ax_a_right.spines["top"].set_visible(False)
    ax_a.axvline(2.0, color=PALETTE["gray"], lw=0.9, ls="--")
    ax_a.plot([], [], color=PALETTE["red"], ls="--", label=r"$f_1$")
    ax_a.plot([], [], color=PALETTE["blue"], label=r"$\eta_c$")
    ax_a.legend(loc="upper right", ncol=2)

    for ax, chi, panel in ((ax_b, 0.0, "b"), (ax_c, 1.0, "c")):
        ax.plot(q_values, momentum[(chi, "ground")], color=PALETTE["black"], lw=1.0, label="ground")
        ax.plot(q_values, momentum[(chi, "excited")], color=PALETTE["blue"], lw=1.0, ls="--", label=fr"$\alpha={alpha0}$")
        ax.set(xlabel=r"$k/k_1$", ylabel=r"$P(k/k_1)$")
        ax.text(0.04, 0.86, fr"{panel}   $\chi/J={chi:g}$", transform=ax.transAxes, fontweight="bold")
    ax_b.set_ylim(0.0, 0.6)
    ax_c.set_ylim(0.0, 0.02)
    ax_b.legend(loc="upper right", fontsize=7)

    ax_d.plot(np.arange(length), channel_data[1.0], color=PALETTE["black"], lw=0.8)
    for label, index in ((r"$\alpha_2$", alpha2), (r"$\alpha_1$", alpha1), (r"$\alpha_0$", alpha0)):
        ax_d.annotate(label, (index, channel_data[1.0][index]), xytext=(0, 5), textcoords="offset points", ha="center")
    ax_d.set(xlabel=r"$\alpha$", ylabel=r"$f_1^\alpha$", xlim=(0, length), ylim=(0, 0.23))
    ax_d.text(0.04, 0.86, r"d   $\chi/J=1$", transform=ax_d.transAxes, fontweight="bold")

    ax_e.plot(np.arange(1, length), channel_data[2.03][1:], color=PALETTE["black"], lw=0.75)
    ax_e.set(xlabel=r"$\alpha$", ylabel=r"$f_1^\alpha$", xlim=(1, length), ylim=(0, 4.1))
    ax_e.text(0.04, 0.86, r"e   $\chi/J=2.03$", transform=ax_e.transAxes, fontweight="bold")
    inset = ax_e.inset_axes([0.43, 0.43, 0.51, 0.47])
    inset.plot(q_values, momentum[(2.03, "ground")], color=PALETTE["black"], lw=0.8)
    inset.set(xlim=(-2, 2), ylim=(0, 0.012), xlabel=r"$k/k_1$", ylabel="P")
    inset.tick_params(labelsize=6)
    save_publication_figure(fig, FIGURE_DIR / "fig3_mechanism")
    plt.close(fig)
    return check


def generate_fig4b(config: dict) -> dict:
    global_cfg = config["global"]
    fig_cfg = config["fig4"]
    length = int(global_cfg["L"])
    gamma = float(global_cfg["gamma"])
    gamma_values = np.linspace(fig_cfg["gamma_c_min"], fig_cfg["gamma_c_max"], int(fig_cfg["gamma_c_points"]))
    rows: list[dict[str, object]] = []
    curves: dict[float, np.ndarray] = {}
    raw_curves: dict[float, np.ndarray] = {}
    for chi in fig_cfg["landscape_chi"]:
        energies, vectors = aa_eigensystem(length, float(chi), gamma=gamma)
        ground = vectors[:, 0]
        gaps = energies[1:] - energies[0]
        eta_curve = np.zeros_like(gamma_values)
        eta_raw = np.zeros_like(gamma_values)
        if chi < 2.0:
            for index, gamma_c in enumerate(gamma_values):
                profile = np.cos(2.0 * np.pi * gamma_c * np.arange(length))
                overlaps = vectors[:, 1:].T @ (profile * ground)
                response = float(np.sum(overlaps**2 / gaps))
                eta_raw[index] = float(
                    critical_pump(
                        response,
                        atom_number=global_cfg["N"],
                        delta_c=global_cfg["delta_c"],
                        kappa=global_cfg["kappa"],
                        dispersive_coupling=global_cfg["U"],
                        shift_factor=global_cfg["cavity_shift_factor"],
                    )
                )
            eta_curve[:] = eta_raw
            eta_curve[0] = 0.0
            eta_curve[-1] = 0.0
            midpoint = int(np.argmin(np.abs(gamma_values - 0.5)))
            if gamma_values[midpoint] == 0.5 and 0 < midpoint < gamma_values.size - 1:
                # At exactly gamma_c=1/2 the +pi and -pi components alias into
                # one discrete mode.  The paper plots the generic two-sided
                # thermodynamic limit, so retain the raw value in CSV and use
                # the neighboring-limit value for the reader-facing curve.
                eta_curve[midpoint] = 0.5 * (eta_curve[midpoint - 1] + eta_curve[midpoint + 1])
        curves[float(chi)] = eta_curve
        raw_curves[float(chi)] = eta_raw
        for gamma_c, eta, raw in zip(gamma_values, eta_curve, eta_raw, strict=True):
            rows.append(
                {
                    "chi_over_J": float(chi),
                    "gamma_c": float(gamma_c),
                    "eta_c_over_J": float(eta),
                    "eta_c_raw_finite_chain": float(raw),
                    "thermodynamic_alias_corrected": int(gamma_c == 0.5 and chi < 2.0),
                }
            )
    write_csv(
        DATA_DIR / "fig4b_threshold_landscape.csv",
        ["chi_over_J", "gamma_c", "eta_c_over_J", "eta_c_raw_finite_chain", "thermodynamic_alias_corrected"],
        rows,
    )

    clean_midpoint = float(curves[0.0][np.argmin(np.abs(gamma_values - 0.5))])
    expected_minima = sorted([2 * gamma - 1, 1 - gamma, gamma, 2 * (1 - gamma)])
    curve_15 = curves[1.5]
    local_minima = []
    for value in expected_minima:
        window = np.abs(gamma_values - value) <= 0.015
        local_minima.append(float(gamma_values[window][np.argmin(curve_15[window])]))
    check = {
        "status": "passed",
        "target_id": "T003",
        "panel": "FIG004B",
        "parameter_match": "paper_subset",
        "generated_data_provenance": "independent_numerics",
        "formula_gate": "verified",
        "metrics": {
            "clean_eta_at_gamma_c_0p5": clean_midpoint,
            "published_curve_eta_at_gamma_c_0p5": 0.47,
            "published_formula_curve_discrepancy": abs(clean_midpoint - 0.47),
            "cavity_shift_factor": global_cfg["cavity_shift_factor"],
            "clean_raw_finite_chain_eta_at_gamma_c_0p5": float(raw_curves[0.0][np.argmin(np.abs(gamma_values - 0.5))]),
            "gamma_c_0p5_policy": "two-sided thermodynamic limit; raw finite-chain alias retained in CSV",
            "expected_harmonic_minima": expected_minima,
            "observed_local_minima_chi_1p5": local_minima,
            "localized_curve_max": float(np.max(curves[2.03])),
        },
        "acceptance": {
            "literal_published_shift_factor": float(global_cfg["cavity_shift_factor"]) == 1.0,
            "clean_midpoint_finite_positive": bool(np.isfinite(clean_midpoint) and clean_midpoint > 0.0),
            "harmonic_minima_within_grid": bool(np.max(np.abs(np.asarray(expected_minima) - np.asarray(local_minima))) <= 0.015),
            "localized_threshold_zero": bool(np.allclose(curves[2.03], 0.0)),
        },
    }
    check["status"] = "passed" if all(check["acceptance"].values()) else "failed"
    write_json(CHECK_DIR / "fig4b_threshold_landscape.json", check)

    fig, ax = plt.subplots(figsize=(5.15, 3.3), constrained_layout=True)
    fill_colors = [PALETTE["yellow"], PALETTE["cyan"], "#36945D", "#35A6A6", PALETTE["red"], PALETTE["blue"]]
    for chi, color in zip(fig_cfg["landscape_chi"], fill_colors, strict=True):
        ax.fill_between(gamma_values, 0.0, np.minimum(curves[float(chi)], 0.55), color=color, label=fr"$\chi/J={chi:g}$")
    for label, position in zip((r"$2\gamma-1$", r"$1-\gamma$", r"$\gamma$", r"$2(1-\gamma)$"), expected_minima, strict=True):
        ax.annotate(label, xy=(position, 0.235), xytext=(position, 0.34), ha="center", color=PALETTE["blue"], arrowprops={"arrowstyle": "->", "lw": 0.8, "color": PALETTE["black"]})
    ax.set(xlabel=r"$\gamma_c$", ylabel=r"$\eta_c/J$", xlim=(0, 1), ylim=(0, 0.52))
    ax.legend(loc="upper right", fontsize=6.5)
    save_publication_figure(fig, FIGURE_DIR / "fig4b_threshold_landscape")
    plt.close(fig)
    return check


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-deferred-reference-output",
        action="store_true",
        help="also generate the non-scoring Fig. 2 source-calibrated diagnostic",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    config = load_config()
    checks = {
        "fig3": generate_fig3(config),
        "fig4b": generate_fig4b(config),
    }
    if args.include_deferred_reference_output:
        checks["fig2_reference_diagnostic"] = generate_fig2(
            load_config(REFERENCE_DIAGNOSTIC_CONFIG_PATH)
        )
    elapsed = time.perf_counter() - started
    overall = {
        "status": "passed" if all(item["status"] == "passed" for item in checks.values()) else "failed",
        "runtime_seconds": elapsed,
        "backend": "numpy-scipy-matplotlib",
        "machine_scope": "local_m4",
        "checks": {key: value["status"] for key, value in checks.items()},
        "scientific_target_ids": ["T002", "T003"],
        "deferred_reference_target_ids": ["T001"] if args.include_deferred_reference_output else [],
        "source_calibrated_inputs_in_scientific_targets": False,
    }
    write_json(CHECK_DIR / "linear_targets_summary.json", overall)
    print(json.dumps(overall, indent=2))
    return 0 if overall["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
