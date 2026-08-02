#!/usr/bin/env python3
"""Generate Main Figure 1 from bulk Dirac spectra and domain-wall matching."""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
CASE = CODE.parent
os.environ.setdefault("MPLCONFIGDIR", str(CASE / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

sys.path.insert(0, str(CODE / "src"))

from nonhermitian_topology import (  # noqa: E402
    DiracDomain,
    dirac_eigenvalues,
    dirac_hamiltonian,
    solve_domain_wall_edge,
    unordered_pair_error,
)


TARGET_ID = "T001"
BULK = DiracDomain(kappa_x=0.2, kappa_y=0.3, mass=-1.0, delta=0.4)
VACUUM = DiracDomain(kappa_x=0.0, kappa_y=0.0, mass=1.0, delta=0.0)
BULK_RADIAL_MAX = 4.5
BULK_RADIAL_SAMPLES = 241
BULK_ANGULAR_SAMPLES = 721
EDGE_KY_SAMPLES = 1601
GAP_DISTANCE_THRESHOLD = 0.01


def build_bulk_data() -> dict[str, np.ndarray]:
    radius = np.linspace(0.0, BULK_RADIAL_MAX, BULK_RADIAL_SAMPLES)
    angle = np.linspace(0.0, 2.0 * np.pi, BULK_ANGULAR_SAMPLES, endpoint=False)
    radial_grid, angular_grid = np.meshgrid(radius, angle, indexing="ij")
    kx = radial_grid * np.cos(angular_grid)
    ky = radial_grid * np.sin(angular_grid)
    energy_plus, energy_minus = dirac_eigenvalues(
        kx,
        ky,
        kappa_x=BULK.kappa_x,
        kappa_y=BULK.kappa_y,
        mass=BULK.mass,
        delta=BULK.delta,
    )
    return {
        "radius": radial_grid,
        "angle": angular_grid,
        "kx": kx,
        "ky": ky,
        "energy_plus": energy_plus,
        "energy_minus": energy_minus,
    }


def build_edge_data(
    bulk: dict[str, np.ndarray],
) -> tuple[np.ndarray, list[object], np.ndarray, np.ndarray, np.ndarray]:
    ky_values = np.linspace(-4.0, 4.0, EDGE_KY_SAMPLES)
    solutions = [solve_domain_wall_edge(float(ky), VACUUM, BULK) for ky in ky_values]
    edge_energy = np.array([solution.energy for solution in solutions], dtype=np.complex128)

    plus_points = np.column_stack((bulk["energy_plus"].real.ravel(), bulk["energy_plus"].imag.ravel()))
    minus_points = np.column_stack((bulk["energy_minus"].real.ravel(), bulk["energy_minus"].imag.ravel()))
    bulk_points = np.vstack((plus_points, minus_points))
    tree = cKDTree(bulk_points)
    distances, nearest_indices = tree.query(np.column_stack((edge_energy.real, edge_energy.imag)))
    nearest_sheet = np.where(nearest_indices < plus_points.shape[0], 1, -1).astype(np.int8)
    raw_gap = distances > GAP_DISTANCE_THRESHOLD
    transitions = np.diff(np.pad(raw_gap.astype(np.int8), (1, 1)))
    starts = np.flatnonzero(transitions == 1)
    stops = np.flatnonzero(transitions == -1)
    peak_index = int(np.argmax(distances))
    containing_peak = [
        (int(start), int(stop))
        for start, stop in zip(starts, stops, strict=True)
        if start <= peak_index < stop
    ]
    if len(containing_peak) != 1:
        raise RuntimeError("could not identify one main bulk-gap component around the maximum separation")
    visible_gap = np.zeros_like(raw_gap)
    visible_gap[slice(*containing_peak[0])] = True
    return ky_values, solutions, edge_energy, distances, np.column_stack((visible_gap, nearest_sheet))


def write_edge_csv(
    path: Path,
    ky_values: np.ndarray,
    solutions: list[object],
    edge_energy: np.ndarray,
    distances: np.ndarray,
    flags: np.ndarray,
) -> None:
    fields = [
        "ky",
        "energy_real",
        "energy_imag",
        "inverse_left_real",
        "inverse_left_imag",
        "inverse_right_real",
        "inverse_right_imag",
        "equation_residual",
        "localization_margin",
        "nearest_bulk_distance",
        "visible_gap_segment",
        "nearest_bulk_sheet",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, solution in enumerate(solutions):
            writer.writerow(
                {
                    "ky": f"{ky_values[index]:.17g}",
                    "energy_real": f"{edge_energy[index].real:.17g}",
                    "energy_imag": f"{edge_energy[index].imag:.17g}",
                    "inverse_left_real": f"{solution.inverse_length_left.real:.17g}",
                    "inverse_left_imag": f"{solution.inverse_length_left.imag:.17g}",
                    "inverse_right_real": f"{solution.inverse_length_right.real:.17g}",
                    "inverse_right_imag": f"{solution.inverse_length_right.imag:.17g}",
                    "equation_residual": f"{solution.equation_residual:.17g}",
                    "localization_margin": f"{solution.localization_margin:.17g}",
                    "nearest_bulk_distance": f"{distances[index]:.17g}",
                    "visible_gap_segment": int(flags[index, 0]),
                    "nearest_bulk_sheet": "plus" if flags[index, 1] > 0 else "minus",
                }
            )


def scientific_checks(
    bulk: dict[str, np.ndarray],
    ky_values: np.ndarray,
    solutions: list[object],
    edge_energy: np.ndarray,
    distances: np.ndarray,
    flags: np.ndarray,
) -> dict[str, object]:
    analytic_direct_errors = []
    for kx, ky in [(-1.2, -0.7), (-0.4, 0.9), (0.0, 0.0), (0.8, -0.5), (1.6, 1.1)]:
        plus, minus = dirac_eigenvalues(
            kx,
            ky,
            kappa_x=BULK.kappa_x,
            kappa_y=BULK.kappa_y,
            mass=BULK.mass,
            delta=BULK.delta,
        )
        direct = np.linalg.eigvals(
            dirac_hamiltonian(
                kx,
                ky,
                kappa_x=BULK.kappa_x,
                kappa_y=BULK.kappa_y,
                mass=BULK.mass,
                delta=BULK.delta,
            )
        )
        analytic_direct_errors.append(unordered_pair_error([plus, minus], direct))

    selected = np.flatnonzero(flags[:, 0] > 0)
    if selected.size == 0:
        raise RuntimeError("no edge interval was separated from the independently generated bulk regions")
    contiguous = bool(np.all(np.diff(selected) == 1))
    first, last = int(selected[0]), int(selected[-1])
    endpoint_sheets = {int(flags[first, 1]), int(flags[last, 1])}

    equation_residuals = np.array([solution.equation_residual for solution in solutions])
    localization_margins = np.array([solution.localization_margin for solution in solutions])
    bulk_kappa = float(np.hypot(BULK.kappa_x, BULK.kappa_y))
    metrics = {
        "max_bulk_analytic_vs_direct_error": float(max(analytic_direct_errors)),
        "max_domain_wall_equation_residual": float(np.max(equation_residuals)),
        "minimum_domain_wall_localization_margin": float(np.min(localization_margins)),
        "bulk_separability_margin_abs_m_minus_kappa": float(abs(BULK.mass) - bulk_kappa),
        "visible_gap_segment_is_contiguous": contiguous,
        "visible_gap_ky_range": [float(ky_values[first]), float(ky_values[last])],
        "visible_gap_energy_endpoints": [
            [float(edge_energy[first].real), float(edge_energy[first].imag)],
            [float(edge_energy[last].real), float(edge_energy[last].imag)],
        ],
        "endpoint_bulk_distances": [float(distances[first]), float(distances[last])],
        "endpoint_bulk_sheets": sorted(endpoint_sheets),
        "maximum_gap_distance": float(np.max(distances[selected])),
    }
    criteria = {
        "bulk_formula_matches_direct_matrix": metrics["max_bulk_analytic_vs_direct_error"] < 1e-12,
        "matching_equations": metrics["max_domain_wall_equation_residual"] < 3e-12,
        "localized_across_sampled_branch": metrics["minimum_domain_wall_localization_margin"] > 0.6,
        "bulk_bands_are_separable": metrics["bulk_separability_margin_abs_m_minus_kappa"] > 0.6,
        "single_gap_branch": contiguous,
        "edge_connects_both_bulk_sheets": endpoint_sheets == {-1, 1},
        "gap_is_resolved": metrics["maximum_gap_distance"] > 0.8,
        "mass_ratio_matches_caption": abs(VACUUM.mass / BULK.mass + 1.0) < 1e-14,
    }
    return {
        "schema_version": 1,
        "paper_id": "1706.07435",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "paper_parameters": {
            "bulk": BULK.__dict__,
            "vacuum": VACUUM.__dict__,
            "mass_ratio": VACUUM.mass / BULK.mass,
        },
        "metrics": metrics,
        "criteria": criteria,
    }


def render_figure(
    path: Path,
    bulk: dict[str, np.ndarray],
    edge_energy: np.ndarray,
    visible_gap: np.ndarray,
) -> None:
    plt.rcParams.update({"font.size": 14, "axes.linewidth": 1.2})
    figure, axis = plt.subplots(figsize=(8.2, 7.0))
    plus = bulk["energy_plus"].ravel()
    minus = bulk["energy_minus"].ravel()
    keep_plus = (np.abs(plus.real) <= 4.1) & (np.abs(plus.imag) <= 0.62)
    keep_minus = (np.abs(minus.real) <= 4.1) & (np.abs(minus.imag) <= 0.62)
    axis.scatter(
        minus.real[keep_minus],
        minus.imag[keep_minus],
        s=0.45,
        color="#f6d37a",
        alpha=0.34,
        linewidths=0,
        rasterized=True,
    )
    axis.scatter(
        plus.real[keep_plus],
        plus.imag[keep_plus],
        s=0.45,
        color="#84bce1",
        alpha=0.34,
        linewidths=0,
        rasterized=True,
    )
    axis.plot(
        edge_energy.real[visible_gap],
        edge_energy.imag[visible_gap],
        color="#2fa04f",
        lw=3.0,
        solid_capstyle="round",
    )
    axis.spines["left"].set_position("zero")
    axis.spines["bottom"].set_position("zero")
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_xlim(-4.2, 4.2)
    axis.set_ylim(-0.62, 0.62)
    axis.set_xticks([-4, -2, 0, 2, 4])
    axis.set_yticks([-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6])
    axis.set_xlabel("Re(E)", loc="right", labelpad=8)
    axis.set_ylabel("Im(E)", loc="top", rotation=0, labelpad=10)
    axis.set_aspect(5.8)
    figure.subplots_adjust(left=0.04, right=0.96, bottom=0.04, top=0.96)
    figure.savefig(path, dpi=200, facecolor="white")
    plt.close(figure)


def main() -> int:
    started = time.perf_counter()
    data_dir = CASE / "outputs" / "data"
    figure_dir = CASE / "outputs" / "figures"
    check_dir = CASE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)

    bulk = build_bulk_data()
    ky_values, solutions, edge_energy, distances, flags = build_edge_data(bulk)
    visible_gap = flags[:, 0] > 0

    bulk_path = data_dir / "main_fig1_bulk_spectra.npz"
    edge_path = data_dir / "main_fig1_domain_wall_edge.csv"
    check_path = check_dir / "t001_scientific_checks.json"
    figure_path = figure_dir / "main_fig1_reproduction.png"
    np.savez_compressed(bulk_path, **bulk)
    write_edge_csv(edge_path, ky_values, solutions, edge_energy, distances, flags)

    checks = scientific_checks(bulk, ky_values, solutions, edge_energy, distances, flags)
    checks["runtime_seconds"] = time.perf_counter() - started
    check_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checks["status"] != "passed":
        print(json.dumps(checks, indent=2))
        return 1

    render_figure(figure_path, bulk, edge_energy, visible_gap)
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": TARGET_ID,
                "runtime_seconds": time.perf_counter() - started,
                "outputs": [
                    str(bulk_path.relative_to(CASE)),
                    str(edge_path.relative_to(CASE)),
                    str(check_path.relative_to(CASE)),
                    str(figure_path.relative_to(CASE)),
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
