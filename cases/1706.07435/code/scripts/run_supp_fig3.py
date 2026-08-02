#!/usr/bin/env python3
"""Diagonalize the n=40 cylinder and generate Supplement Figure 3."""

from __future__ import annotations

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

sys.path.insert(0, str(CODE / "src"))

from nonhermitian_topology import (  # noqa: E402
    cylinder_blocks,
    cylinder_boundary_weights,
    cylinder_hamiltonian,
    lattice_bloch_hamiltonian,
)


TARGET_ID = "T005"
SITES = 40
MASS = -0.5
DELTA = 0.0
KY_SAMPLES = 241
CASES = {
    "a": {"kappa_x": 0.1, "kappa_y": 0.0},
    "b": {"kappa_x": 0.0, "kappa_y": 0.1},
}


def diagonalize_case(ky_values: np.ndarray, *, kappa_x: float, kappa_y: float) -> dict[str, np.ndarray]:
    dimension = 2 * SITES
    eigenvalues = np.empty((ky_values.size, dimension), dtype=np.complex128)
    left_weights = np.empty((ky_values.size, dimension), dtype=np.float64)
    right_weights = np.empty((ky_values.size, dimension), dtype=np.float64)
    residuals = np.empty(ky_values.size, dtype=np.float64)

    for index, ky in enumerate(ky_values):
        matrix = cylinder_hamiltonian(
            SITES,
            float(ky),
            kappa_x=kappa_x,
            kappa_y=kappa_y,
            mass=MASS,
            delta=DELTA,
        )
        values, vectors = np.linalg.eig(matrix)
        order = np.lexsort((values.imag, values.real))
        values = values[order]
        vectors = vectors[:, order]
        eigenvalues[index] = values
        left, right = cylinder_boundary_weights(vectors, sites=SITES, edge_sites=4)
        left_weights[index] = left
        right_weights[index] = right
        numerator = np.linalg.norm(matrix @ vectors - vectors * values[np.newaxis, :], axis=0)
        denominator = np.maximum(1.0, np.linalg.norm(matrix) * np.linalg.norm(vectors, axis=0))
        residuals[index] = float(np.max(numerator / denominator))

    return {
        "eigenvalues": eigenvalues,
        "left_weights": left_weights,
        "right_weights": right_weights,
        "max_eigenpair_residual_by_ky": residuals,
    }


def matched_edge_states(
    ky_values: np.ndarray,
    case: dict[str, np.ndarray],
    *,
    kappa_y: float,
) -> dict[str, np.ndarray]:
    selected = np.flatnonzero((np.abs(ky_values) >= 0.12) & (np.abs(ky_values) <= 0.82))
    matched_values = np.empty((selected.size, 2), dtype=np.complex128)
    matched_weights = np.empty((selected.size, 2), dtype=np.float64)
    matched_sides = np.empty((selected.size, 2), dtype=np.int8)

    for output_index, ky_index in enumerate(selected):
        values = case["eigenvalues"][ky_index]
        predictions = np.array(
            [np.sin(ky_values[ky_index]) + 1.0j * kappa_y, -np.sin(ky_values[ky_index]) - 1.0j * kappa_y]
        )
        used: set[int] = set()
        for branch_index, prediction in enumerate(predictions):
            for candidate in np.argsort(np.abs(values - prediction)):
                candidate_index = int(candidate)
                if candidate_index not in used:
                    used.add(candidate_index)
                    break
            matched_values[output_index, branch_index] = values[candidate_index]
            left = case["left_weights"][ky_index, candidate_index]
            right = case["right_weights"][ky_index, candidate_index]
            matched_weights[output_index, branch_index] = max(left, right)
            matched_sides[output_index, branch_index] = 0 if left >= right else 1

    return {
        "ky_indices": selected,
        "values": matched_values,
        "weights": matched_weights,
        "sides": matched_sides,
    }


def scientific_checks(ky_values: np.ndarray, spectra: dict[str, dict[str, np.ndarray]]) -> dict[str, object]:
    kx_test, ky_test = 0.37, -0.81
    parameters = {"kappa_x": 0.13, "kappa_y": -0.07, "mass": MASS, "delta": 0.04}
    onsite, forward, reverse = cylinder_blocks(ky_test, **parameters)
    reconstructed = onsite + forward * np.exp(1.0j * kx_test) + reverse * np.exp(-1.0j * kx_test)
    fourier_error = float(
        np.linalg.norm(reconstructed - lattice_bloch_hamiltonian(kx_test, ky_test, **parameters))
    )

    hermitian_matrix = cylinder_hamiltonian(
        SITES,
        0.29,
        kappa_x=0.0,
        kappa_y=0.0,
        mass=MASS,
        delta=0.0,
    )
    hermiticity_error = float(np.linalg.norm(hermitian_matrix - hermitian_matrix.conj().T))

    edge_metrics: dict[str, object] = {}
    all_edge_errors = []
    all_edge_weights = []
    for label, parameters_case in CASES.items():
        matched = matched_edge_states(
            ky_values,
            spectra[label],
            kappa_y=parameters_case["kappa_y"],
        )
        selected_ky = ky_values[matched["ky_indices"]]
        predictions = np.stack(
            (
                np.sin(selected_ky) + 1.0j * parameters_case["kappa_y"],
                -np.sin(selected_ky) - 1.0j * parameters_case["kappa_y"],
            ),
            axis=1,
        )
        edge_error = np.abs(matched["values"] - predictions)
        imaginary_error = np.abs(matched["values"].imag - predictions.imag)
        all_edge_errors.extend(edge_error.ravel())
        all_edge_weights.extend(matched["weights"].ravel())
        edge_metrics[label] = {
            "max_edge_dispersion_error": float(np.max(edge_error)),
            "max_edge_imaginary_energy_error": float(np.max(imaginary_error)),
            "minimum_boundary_weight": float(np.min(matched["weights"])),
            "left_right_branches_both_present": bool(
                set(np.unique(matched["sides"][:, 0])).union(np.unique(matched["sides"][:, 1])) == {0, 1}
            ),
        }

    max_residual = float(
        max(np.max(case["max_eigenpair_residual_by_ky"]) for case in spectra.values())
    )
    metrics = {
        "matrix_dimension": 2 * SITES,
        "ky_samples": int(ky_values.size),
        "block_fourier_identity_error": fourier_error,
        "hermiticity_limit_error": hermiticity_error,
        "max_normalized_eigenpair_residual": max_residual,
        "max_edge_dispersion_error": float(max(all_edge_errors)),
        "minimum_matched_edge_boundary_weight": float(min(all_edge_weights)),
        "cases": edge_metrics,
    }
    criteria = {
        "paper_matrix_size": metrics["matrix_dimension"] == 80,
        "block_fourier_identity": fourier_error < 1e-13,
        "hermitian_limit": hermiticity_error < 1e-13,
        "eigenpair_residuals": max_residual < 1e-11,
        "analytic_edge_dispersion": metrics["max_edge_dispersion_error"] < 1e-10,
        "edge_localization": metrics["minimum_matched_edge_boundary_weight"] > 0.95,
        "both_physical_edges": all(
            bool(case_metrics["left_right_branches_both_present"])
            for case_metrics in edge_metrics.values()
        ),
    }
    return {
        "schema_version": 1,
        "paper_id": "1706.07435",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "paper_parameters": {
            "sites": SITES,
            "mass": MASS,
            "delta": DELTA,
            "cases": CASES,
        },
        "metrics": metrics,
        "criteria": criteria,
    }


def render_figure(path: Path, ky_values: np.ndarray, spectra: dict[str, dict[str, np.ndarray]]) -> None:
    plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.7})
    figure, axes = plt.subplots(2, 2, figsize=(9.2, 6.2), sharex=True)
    bulk_color = "#4db8e9"
    edge_color = "#197dad"

    for row, label in enumerate(("a", "b")):
        case = spectra[label]
        x = np.repeat(ky_values[:, None], case["eigenvalues"].shape[1], axis=1)
        edge_weight = np.maximum(case["left_weights"], case["right_weights"])
        edge_mask = edge_weight > 0.65
        for column, component in enumerate((np.real, np.imag)):
            axis = axes[row, column]
            values = component(case["eigenvalues"])
            axis.scatter(x, values, s=0.45, color=bulk_color, alpha=0.72, linewidths=0)
            axis.scatter(x[edge_mask], values[edge_mask], s=2.0, color=edge_color, alpha=0.9, linewidths=0)
            axis.axhline(0.0, color="#b9dff1", lw=0.4, zorder=0)
            axis.set_xlim(-4.0, 4.0)
            axis.set_xticks([-4, -2, 0, 2, 4])
            axis.spines[["top", "right"]].set_visible(False)
        axes[row, 0].set_ylim(-3.0, 3.0)
        axes[row, 0].set_ylabel(r"Re[$E(k_y)$]")
        axes[row, 1].set_ylabel(r"Im[$E(k_y)$]")
        axes[row, 1].set_ylim((-0.1, 0.1) if label == "a" else (-0.15, 0.15))
        axes[row, 0].set_title(f"({label})", loc="left", fontsize=14)

    axes[1, 0].set_xlabel(r"$k_y$")
    axes[1, 1].set_xlabel(r"$k_y$")
    figure.subplots_adjust(left=0.09, right=0.98, bottom=0.10, top=0.97, wspace=0.22, hspace=0.18)
    figure.savefig(path, dpi=200, facecolor="white")
    plt.close(figure)


def main() -> int:
    started = time.perf_counter()
    data_dir = CASE / "outputs" / "data"
    figure_dir = CASE / "outputs" / "figures"
    check_dir = CASE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)

    ky_values = np.linspace(-np.pi, np.pi, KY_SAMPLES)
    spectra = {
        label: diagonalize_case(ky_values, **parameters)
        for label, parameters in CASES.items()
    }

    data_path = data_dir / "supp_fig3_cylinder_spectra.npz"
    check_path = check_dir / "t005_scientific_checks.json"
    figure_path = figure_dir / "supp_fig3_reproduction.png"
    np.savez_compressed(
        data_path,
        ky=ky_values,
        eigenvalues_a=spectra["a"]["eigenvalues"],
        left_weights_a=spectra["a"]["left_weights"],
        right_weights_a=spectra["a"]["right_weights"],
        eigenvalues_b=spectra["b"]["eigenvalues"],
        left_weights_b=spectra["b"]["left_weights"],
        right_weights_b=spectra["b"]["right_weights"],
    )

    checks = scientific_checks(ky_values, spectra)
    checks["runtime_seconds"] = time.perf_counter() - started
    check_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checks["status"] != "passed":
        print(json.dumps(checks, indent=2))
        return 1

    render_figure(figure_path, ky_values, spectra)
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": TARGET_ID,
                "runtime_seconds": time.perf_counter() - started,
                "outputs": [
                    str(data_path.relative_to(CASE)),
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
