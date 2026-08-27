#!/usr/bin/env python3
"""Guarded target-scoped reproduction for the spin-1 Kitaev-AKLT paper."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "scripts"))

from digitize_overlap_panels import digitize_panel  # noqa: E402
from src.kitaev_aklt import (  # noqa: E402
    all_sectors,
    exact_point_zero_mode_count,
    lowest_eigenspace,
    maximal_component_projector,
    overlap_in_sector,
    product_state_diagnostics,
    projector_from_bond_product,
    sector_hamiltonian,
)


GUARDED_TARGET_ENV = "PRAGENT_GUARDED_TARGET_ID"
GUARDED_STAGE_ENV = "PRAGENT_GUARDED_STAGE"
TARGETS = ("V001", "V002", "T001", "T002")
NUMBER_SITES = (4, 6, 8, 10, 12)
THETA_DEGREES = (40, 30, 20, 10, 0)
SERIES_STYLE = {
    40: {"color": "#edb120", "marker": "o"},
    30: {"color": "#ff00ff", "marker": "s"},
    20: {"color": "#00cc22", "marker": "D"},
    10: {"color": "#ff2020", "marker": ">"},
    0: {"color": "#2020ff", "marker": "<"},
}
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"
COMPARISON_DIR = WORKSPACE / "outputs" / "comparisons"
REFERENCE_DIR = WORKSPACE / "references" / "original_figures"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty dataset")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def source_comparison(
    source_path: Path,
    generated_path: Path,
    output_path: Path,
    title: str,
) -> None:
    source = mpimg.imread(source_path)
    generated = mpimg.imread(generated_path)
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 5.5), constrained_layout=True)
    axes[0].imshow(source)
    axes[0].set_title("Paper panel")
    axes[1].imshow(generated)
    axes[1].set_title("Independent reproduction")
    for axis in axes:
        axis.axis("off")
    figure.suptitle(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def run_v001() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    projector_errors = {}
    for axis in ("x", "y"):
        spectral = maximal_component_projector(axis)
        polynomial = projector_from_bond_product(axis)
        projector_errors[axis] = float(np.max(np.abs(spectral - polynomial)))

    counts = []
    for number_sites in (4, 6):
        result = exact_point_zero_mode_count(number_sites)
        counts.append(result)
        nullities = result["sector_nullities"]
        rows.append(
            {
                "number_sites": number_sites,
                "total_zero_modes": result["total_zero_modes"],
                "expected_zero_modes": result["expected_zero_modes"],
                "uniform_minus_nullity": nullities["-" * number_sites],
                "maximum_other_sector_nullity": max(
                    value
                    for key, value in nullities.items()
                    if key != "-" * number_sites
                ),
                "maximum_mps_energy": result["maximum_mps_energy"],
            }
        )

    data_path = DATA_DIR / "exact_point_validation.csv"
    write_csv(data_path, rows)
    checks = {
        "projector_identity": max(projector_errors.values()) < 1e-12,
        "degeneracy_matches_2n_plus_1": all(
            result["total_zero_modes"] == result["expected_zero_modes"]
            for result in counts
        ),
        "only_uniform_minus_has_second_zero_mode": all(
            result["sector_nullities"]["-" * int(result["number_sites"])] == 2
            and all(
                value == 1
                for key, value in result["sector_nullities"].items()
                if key != "-" * int(result["number_sites"])
            )
            for result in counts
        ),
        "all_fractionalized_mps_are_zero_modes": all(
            abs(float(result["maximum_mps_energy"])) < 1e-11
            for result in counts
        ),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "V001",
        "artifact_stage": "exploratory",
        "parameters": {
            "theta": "pi/4",
            "boundary": "periodic",
            "number_sites": [4, 6],
            "parameter_match": "paper_subset",
        },
        "checks": checks,
        "diagnostics": {
            "projector_max_errors": projector_errors,
            "zero_mode_counts": [
                {
                    "number_sites": result["number_sites"],
                    "total": result["total_zero_modes"],
                    "expected": result["expected_zero_modes"],
                }
                for result in counts
            ],
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "analytic_reference",
        "outputs": [str(data_path.relative_to(WORKSPACE))],
    }


def global_ground_summary(number_sites: int, theta: float) -> dict[str, object]:
    minimum_energy = np.inf
    total_multiplicity = 0
    minimizing_sectors: list[str] = []
    for sector in all_sectors(number_sites):
        hamiltonian, _ = sector_hamiltonian(number_sites, theta, sector)
        energy, eigenspace, _ = lowest_eigenspace(hamiltonian)
        if energy < minimum_energy - 1e-10:
            minimum_energy = energy
            total_multiplicity = int(eigenspace.shape[1])
            minimizing_sectors = ["".join("+" if value == 1 else "-" for value in sector)]
        elif abs(energy - minimum_energy) <= 1e-10:
            total_multiplicity += int(eigenspace.shape[1])
            minimizing_sectors.append(
                "".join("+" if value == 1 else "-" for value in sector)
            )
    return {
        "energy": float(minimum_energy),
        "multiplicity": total_multiplicity,
        "sectors": minimizing_sectors,
    }


def run_v002() -> dict[str, object]:
    number_sites = 6
    sample_angles = (
        np.pi / 4.0,
        np.pi / 3.0,
        np.pi / 2.0,
        2.0 * np.pi / 3.0,
        3.0 * np.pi / 4.0,
        3.0 * np.pi / 2.0,
    )
    rows: list[dict[str, object]] = []
    summaries = {}
    for theta in sample_angles:
        summary = global_ground_summary(number_sites, theta)
        summaries[theta] = summary
        alternating_xy = product_state_diagnostics(
            number_sites, theta, "alternating_xy"
        )
        alternating_yx = product_state_diagnostics(
            number_sites, theta, "alternating_yx"
        )
        uniform_z = product_state_diagnostics(number_sites, theta, "uniform_z")
        rows.append(
            {
                "theta_radians": theta,
                "theta_over_pi": theta / np.pi,
                "ground_energy": summary["energy"],
                "ground_multiplicity": summary["multiplicity"],
                "alternating_xy_energy": alternating_xy["energy"],
                "alternating_yx_energy": alternating_yx["energy"],
                "uniform_z_energy": uniform_z["energy"],
            }
        )

    mirror_theta = 0.27
    mirror_left = global_ground_summary(number_sites, mirror_theta)
    mirror_right = global_ground_summary(number_sites, np.pi - mirror_theta)
    data_path = DATA_DIR / "phase_controls.csv"
    write_csv(data_path, rows)

    zero_energy_angles = sample_angles[:5]
    doubly_degenerate_angles = sample_angles[1:4]
    checks = {
        "doubly_degenerate_product_energy_zero": all(
            abs(float(summaries[theta]["energy"])) < 1e-10
            for theta in zero_energy_angles
        ),
        "interior_ground_state_is_doubly_degenerate": all(
            int(summaries[theta]["multiplicity"]) == 2
            for theta in doubly_degenerate_angles
        ),
        "phase_boundaries_have_macroscopic_degeneracy": all(
            int(summaries[theta]["multiplicity"]) == 2**number_sites + 1
            for theta in (np.pi / 4.0, 3.0 * np.pi / 4.0)
        ),
        "uniform_z_energy_minus_n": abs(
            float(summaries[3.0 * np.pi / 2.0]["energy"]) + number_sites
        )
        < 1e-10,
        "uniform_z_is_unique_at_3pi_over_2": int(
            summaries[3.0 * np.pi / 2.0]["multiplicity"]
        )
        == 1,
        "k_mirror_symmetry": abs(
            float(mirror_left["energy"]) - float(mirror_right["energy"])
        )
        < 1e-10,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "V002",
        "artifact_stage": "exploratory",
        "parameters": {
            "number_sites": number_sites,
            "boundary": "periodic",
            "sample_theta_over_pi": [theta / np.pi for theta in sample_angles],
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "mirror_theta": mirror_theta,
            "mirror_energy_left": mirror_left["energy"],
            "mirror_energy_right": mirror_right["energy"],
            "ground_summaries": {
                f"{theta / np.pi:.6f}pi": summary
                for theta, summary in summaries.items()
            },
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "analytic_reference",
        "outputs": [str(data_path.relative_to(WORKSPACE))],
    }


def overlap_rows(panel: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    one_flip = panel == "first_excited"
    generated_rows: list[dict[str, object]] = []
    for theta_degrees in THETA_DEGREES:
        theta = np.deg2rad(theta_degrees)
        for number_sites in NUMBER_SITES:
            sector = (
                (-1,) + (1,) * (number_sites - 1)
                if one_flip
                else (1,) * number_sites
            )
            result = overlap_in_sector(number_sites, theta, sector)
            generated_rows.append(
                {
                    "panel": panel,
                    "theta_degrees": theta_degrees,
                    "number_sites": number_sites,
                    "fidelity": result["fidelity"],
                    "overlap_amplitude": result["overlap_amplitude"],
                    "exact_energy": result["energy"],
                    "mps_energy": result["mps_energy"],
                    "sector_dimension": result["sector_dimension"],
                    "lowest_multiplicity": result["lowest_multiplicity"],
                    "residual_norm": result["residual_norm"],
                    "generated_data_provenance": "independent_numerics",
                }
            )
    reference_rows = [dict(row) for row in digitize_panel(panel)]
    return generated_rows, reference_rows


def render_overlap_figure(
    rows: list[dict[str, object]],
    output_path: Path,
    panel_label: str,
    y_label: str,
) -> None:
    figure, axis = plt.subplots(figsize=(5.0, 6.2), constrained_layout=True)
    for theta_degrees in THETA_DEGREES:
        selected = [
            row for row in rows if int(row["theta_degrees"]) == theta_degrees
        ]
        selected.sort(key=lambda row: int(row["number_sites"]))
        style = SERIES_STYLE[theta_degrees]
        axis.plot(
            [int(row["number_sites"]) for row in selected],
            [float(row["fidelity"]) for row in selected],
            color=style["color"],
            marker=style["marker"],
            linewidth=1.2,
            markersize=7.0,
            label=rf"$\theta={theta_degrees}^\circ$",
        )
    axis.set_xlim(4, 12)
    axis.set_xticks(NUMBER_SITES)
    axis.set_ylim(0.795, 1.003)
    axis.set_yticks([0.8, 0.85, 0.9, 0.95, 1.0])
    axis.set_xlabel("N")
    axis.set_ylabel(y_label)
    axis.text(0.06, 0.035, panel_label, transform=axis.transAxes, fontsize=15)
    axis.legend(
        frameon=False,
        fontsize=8,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
    )
    axis.grid(alpha=0.18)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def comparison_diagnostics(
    generated_rows: list[dict[str, object]],
    reference_rows: list[dict[str, object]],
) -> dict[str, object]:
    generated = {
        (int(row["theta_degrees"]), int(row["number_sites"])): float(row["fidelity"])
        for row in generated_rows
    }
    reference = {
        (int(row["theta_degrees"]), int(row["number_sites"])): float(row["fidelity"])
        for row in reference_rows
    }
    point_errors = {
        key: abs(generated[key] - reference[key])
        for key in generated
    }
    worst_key = max(point_errors, key=point_errors.get)
    errors = list(point_errors.values())
    return {
        "maximum_absolute_digitized_error": max(errors),
        "mean_absolute_digitized_error": float(np.mean(errors)),
        "points_within_0_0015": sum(error < 0.0015 for error in errors),
        "points_total": len(errors),
        "worst_point": {
            "theta_degrees": worst_key[0],
            "number_sites": worst_key[1],
            "generated_fidelity": generated[worst_key],
            "digitized_source_fidelity": reference[worst_key],
            "absolute_error": point_errors[worst_key],
        },
        "digitization_one_pixel_uncertainty": max(
            float(row["one_pixel_fidelity_uncertainty"]) for row in reference_rows
        ),
    }


def one_flip_energy_spread(number_sites: int, theta: float) -> float:
    energies = []
    for flipped_bond in range(number_sites):
        sector = [1] * number_sites
        sector[flipped_bond] = -1
        hamiltonian, _ = sector_hamiltonian(number_sites, theta, sector)
        energy, _, _ = lowest_eigenspace(hamiltonian)
        energies.append(energy)
    return float(max(energies) - min(energies))


def run_overlap_target(target_id: str) -> dict[str, object]:
    is_ground = target_id == "T001"
    panel = "ground" if is_ground else "first_excited"
    generated_rows, reference_rows = overlap_rows(panel)
    data_name = "ground_state_overlaps.csv" if is_ground else "first_excited_overlaps.csv"
    reference_name = (
        "source_ground_state_overlaps_digitized.csv"
        if is_ground
        else "source_first_excited_overlaps_digitized.csv"
    )
    figure_name = (
        "ground_state_overlaps.png" if is_ground else "first_excited_overlaps.png"
    )
    comparison_name = (
        "fig5a_source_vs_reproduction.png"
        if is_ground
        else "fig5b_source_vs_reproduction.png"
    )
    source_name = (
        "Overlap_GS_MPS_shrunk.png"
        if is_ground
        else "Overlap_FE_MPS_shrunk.png"
    )

    data_path = DATA_DIR / data_name
    reference_data_path = DATA_DIR / reference_name
    figure_path = FIGURE_DIR / figure_name
    comparison_path = COMPARISON_DIR / comparison_name
    write_csv(data_path, generated_rows)
    write_csv(reference_data_path, reference_rows)
    render_overlap_figure(
        generated_rows,
        figure_path,
        "(a)" if is_ground else "(b)",
        "Ground-state fidelity" if is_ground else "First-excited-subspace fidelity",
    )
    source_comparison(
        REFERENCE_DIR / source_name,
        figure_path,
        comparison_path,
        "Main Fig. 5(a)" if is_ground else "Main Fig. 5(b)",
    )

    diagnostics = comparison_diagnostics(generated_rows, reference_rows)
    fidelities = [float(row["fidelity"]) for row in generated_rows]
    residuals = [float(row["residual_norm"]) for row in generated_rows]
    by_size = {
        number_sites: {
            int(row["theta_degrees"]): float(row["fidelity"])
            for row in generated_rows
            if int(row["number_sites"]) == number_sites
        }
        for number_sites in NUMBER_SITES
    }
    by_theta = {
        theta_degrees: [
            float(row["fidelity"])
            for row in sorted(
                (
                    row
                    for row in generated_rows
                    if int(row["theta_degrees"]) == theta_degrees
                ),
                key=lambda row: int(row["number_sites"]),
            )
        ]
        for theta_degrees in THETA_DEGREES
    }
    checks = {
        "all_overlaps_in_unit_interval": all(
            -1e-12 <= value <= 1.0 + 1e-12 for value in fidelities
        ),
        "all_eigen_residuals_below_tolerance": max(residuals) < 1e-10,
        "overlap_increases_toward_exact_point": all(
            all(
                values[upper] >= values[lower] - 1e-12
                for lower, upper in zip(
                    reversed(THETA_DEGREES[1:]), reversed(THETA_DEGREES[:-1])
                )
            )
            for values in by_size.values()
        ),
        "finite_size_trend_matches_source": all(
            all(left >= right - 1e-12 for left, right in zip(values, values[1:]))
            for values in by_theta.values()
        ),
        "all_but_at_most_one_point_within_pixel_tolerance": int(
            diagnostics["points_within_0_0015"]
        )
        >= int(diagnostics["points_total"]) - 1,
        "isolated_reference_discrepancy_below_half_percent": float(
            diagnostics["maximum_absolute_digitized_error"]
        )
        < 0.005,
    }
    checks["digitized_reference_agreement"] = bool(
        checks["all_but_at_most_one_point_within_pixel_tolerance"]
        and checks["isolated_reference_discrepancy_below_half_percent"]
    )
    if not is_ground:
        spreads = {
            f"N={number_sites}": one_flip_energy_spread(number_sites, 0.0)
            for number_sites in (4, 8, 12)
        }
        diagnostics["one_flip_energy_spreads"] = spreads
        checks["one_flip_energies_n_fold_degenerate"] = max(spreads.values()) < 1e-10

    return {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": target_id,
        "artifact_stage": "exploratory",
        "parameters": {
            "number_sites": list(NUMBER_SITES),
            "theta_degrees": list(THETA_DEGREES),
            "boundary": "periodic",
            "sector": "all +1" if is_ground else "one -1, remaining +1",
            "residual_tolerance": 1e-10,
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": diagnostics,
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "digitized_curve",
        "outputs": [
            str(data_path.relative_to(WORKSPACE)),
            str(reference_data_path.relative_to(WORKSPACE)),
            str(figure_path.relative_to(WORKSPACE)),
            str(comparison_path.relative_to(WORKSPACE)),
        ],
    }


RUNNERS: dict[str, Callable[[], dict[str, object]]] = {
    "V001": run_v001,
    "V002": run_v002,
    "T001": lambda: run_overlap_target("T001"),
    "T002": lambda: run_overlap_target("T002"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=TARGETS)
    args = parser.parse_args()

    guarded_target = os.environ.get(GUARDED_TARGET_ENV)
    if guarded_target != args.target:
        parser.error(
            f"{GUARDED_TARGET_ENV}={guarded_target!r} does not authorize "
            f"target {args.target!r}"
        )
    guarded_stage = os.environ.get(GUARDED_STAGE_ENV)
    if guarded_stage != "exploratory":
        parser.error(
            "The paper omits its eigensolver and tolerances; "
            "only exploratory reconstruction is authorized."
        )

    started = time.perf_counter()
    payload = RUNNERS[args.target]()
    payload["runtime_seconds"] = time.perf_counter() - started
    check_path = CHECK_DIR / f"{args.target.lower()}_paper_target_run.json"
    write_json(check_path, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
