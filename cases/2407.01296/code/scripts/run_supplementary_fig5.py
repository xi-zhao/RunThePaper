#!/usr/bin/env python3
"""Independently reproduce all six numerical panels of Supplementary Fig. S5.

The Hamiltonian is constructed only from Supplementary Eq. (S27). State
selection, finite-size scaling, exact OBC spectra, and Eq. (10) densities are
all generated numerically; source-figure pixels and released curve arrays are
never consumed by this runner.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree


CODE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = CODE_ROOT.parent if CODE_ROOT.name == "code" else CODE_ROOT
sys.path.insert(0, str(CODE_ROOT))

from src.geometry_adaptive import (  # noqa: E402
    build_obc_hamiltonian,
    diamond_sites,
    full_spectrum,
    geometry_adaptive_potential,
    spectral_density_from_potential,
    square_sites,
    symmetric_cloud_distance,
)
from src.supplementary_models import (  # noqa: E402
    model_s27,
    select_target_spatial_eigenstate,
    spatial_profile_metrics,
)


CONFIGS: dict[str, dict[str, object]] = {
    "smoke": {
        "square_length": 24,
        "diamond_radius": 17,
        "scaling_lengths": (12, 16, 20, 24),
        "real_points": 33,
        "imaginary_points": 65,
        "momentum_samples": 48,
        "minimizer_tolerance": 1e-3,
        "candidate_count_a": 8,
        "candidate_count_b": 10,
        "candidate_count_rhombus": 8,
    },
    "paper": {
        "square_length": 80,
        "diamond_radius": 56,
        "scaling_lengths": (20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120),
        "real_points": 101,
        "imaginary_points": 161,
        "momentum_samples": 160,
        "minimizer_tolerance": 2e-5,
        "candidate_count_a": 12,
        "candidate_count_b": 16,
        "candidate_count_rhombus": 12,
    },
}
TARGET_A = 1.5 + 8.0j
TARGET_B = -1.0 + 10.0j
TARGET_RHOMBUS = 0.0 + 8.0j


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=tuple(CONFIGS), default="paper")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--reuse-completed", action="store_true")
    return parser.parse_args()


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "pragent-2407.01296",
        }
    )


def output_directory(scale: str) -> Path:
    if scale == "paper":
        return OUTPUT_ROOT / "outputs"
    return OUTPUT_ROOT / "outputs" / "smoke" / "supp_fig_s5"


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write an empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _potential_row(
    task: tuple[str, float, np.ndarray, int, float],
) -> tuple[np.ndarray, int]:
    basis, imaginary, real_axis, momentum_samples, tolerance = task
    row = np.empty(real_axis.size, dtype=np.float64)
    evaluations = 0
    hoppings = model_s27()
    for column, real in enumerate(real_axis):
        result = geometry_adaptive_potential(
            complex(float(real), imaginary),
            hoppings,
            basis=basis,
            momentum_samples=momentum_samples,
            tolerance=tolerance,
        )
        row[column] = result.potential
        evaluations += result.cylinder_1.evaluations + result.cylinder_2.evaluations
    return row, evaluations


def _compute_potential(
    basis: str,
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    *,
    momentum_samples: int,
    tolerance: float,
    workers: int,
) -> tuple[np.ndarray, int]:
    tasks = [
        (basis, float(imaginary), real_axis, momentum_samples, tolerance)
        for imaginary in imaginary_axis
    ]
    potential = np.empty((imaginary_axis.size, real_axis.size), dtype=np.float64)
    evaluations = 0
    if workers == 1:
        results = map(_potential_row, tasks)
        executor = None
    else:
        # A thread pool is portable to sandboxed Codex hosts where POSIX
        # process semaphores may be unavailable. The heavy root calculations
        # execute in NumPy/SciPy kernels and still release the Python GIL.
        executor = ThreadPoolExecutor(max_workers=workers)
        results = executor.map(_potential_row, tasks, chunksize=1)
    try:
        report_every = max(1, imaginary_axis.size // 8)
        for row_index, (row, row_evaluations) in enumerate(results):
            potential[row_index] = row
            evaluations += row_evaluations
            if (row_index + 1) % report_every == 0 or row_index + 1 == imaginary_axis.size:
                print(
                    f"S5 {basis} potential rows {row_index + 1}/{imaginary_axis.size}",
                    flush=True,
                )
    finally:
        if executor is not None:
            executor.shutdown()
    return potential, evaluations


def _load_or_compute_spectrum(
    sites: tuple[tuple[int, int], ...],
    checkpoint: Path,
    *,
    reuse_completed: bool,
) -> tuple[np.ndarray, float, str]:
    if reuse_completed and checkpoint.exists():
        stored = np.load(checkpoint)
        if int(stored["site_count"]) != len(sites):
            raise ValueError(f"checkpoint geometry mismatch: {checkpoint}")
        return (
            np.asarray(stored["eigenvalues"], dtype=np.complex128),
            float(stored["runtime_seconds"]),
            "stored_checkpoint",
        )
    started = time.perf_counter()
    eigenvalues = full_spectrum(build_obc_hamiltonian(sites, model_s27()))
    runtime = time.perf_counter() - started
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        checkpoint,
        site_count=len(sites),
        eigenvalues=eigenvalues,
        runtime_seconds=runtime,
    )
    return eigenvalues, runtime, "fresh_compute"


def _load_or_compute_density(
    basis: str,
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    checkpoint: Path,
    *,
    momentum_samples: int,
    tolerance: float,
    workers: int,
    reuse_completed: bool,
) -> tuple[np.ndarray, np.ndarray, int, float, str]:
    started = time.perf_counter()
    if reuse_completed and checkpoint.exists():
        stored = np.load(checkpoint)
        np.testing.assert_allclose(stored["real_axis"], real_axis)
        np.testing.assert_allclose(stored["imaginary_axis"], imaginary_axis)
        if int(stored["momentum_samples"]) != momentum_samples:
            raise ValueError(f"checkpoint momentum mismatch: {checkpoint}")
        potential = np.asarray(stored["potential"], dtype=np.float64)
        evaluations = int(stored["objective_evaluations"])
        runtime = float(stored["runtime_seconds"])
        source = "stored_checkpoint"
    else:
        potential, evaluations = _compute_potential(
            basis,
            real_axis,
            imaginary_axis,
            momentum_samples=momentum_samples,
            tolerance=tolerance,
            workers=workers,
        )
        runtime = time.perf_counter() - started
        source = "fresh_compute"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            checkpoint,
            real_axis=real_axis,
            imaginary_axis=imaginary_axis,
            potential=potential,
            momentum_samples=momentum_samples,
            minimizer_tolerance=tolerance,
            objective_evaluations=evaluations,
            runtime_seconds=runtime,
        )
    density = spectral_density_from_potential(
        potential,
        real_step=float(real_axis[1] - real_axis[0]),
        imaginary_step=float(imaginary_axis[1] - imaginary_axis[0]),
    )
    return potential, density, evaluations, runtime, source


def _state_probability(vector: np.ndarray) -> np.ndarray:
    probability = np.abs(np.asarray(vector, dtype=np.complex128).reshape(-1)) ** 2
    return np.asarray(probability / np.sum(probability), dtype=np.float64)


def _linear_fit(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    coefficients = np.polyfit(x, y, 1)
    prediction = np.polyval(coefficients, x)
    total = float(np.sum((y - np.mean(y)) ** 2))
    residual = float(np.sum((y - prediction) ** 2))
    return {
        "slope": float(coefficients[0]),
        "intercept": float(coefficients[1]),
        "r_squared": 1.0 - residual / total if total > 0.0 else 1.0,
    }


def _cut_spreads(
    sites: tuple[tuple[int, int], ...], probability: np.ndarray
) -> dict[str, float]:
    coordinates = np.asarray(sites, dtype=np.float64)
    u = coordinates[:, 0] + coordinates[:, 1]
    v = -coordinates[:, 0] + coordinates[:, 1]
    mean_u = float(probability @ u)
    mean_v = float(probability @ v)
    sigma_u = float(np.sqrt(probability @ (u - mean_u) ** 2))
    sigma_v = float(np.sqrt(probability @ (v - mean_v) ** 2))
    return {
        "mean_u": mean_u,
        "mean_v": mean_v,
        "sigma_u": sigma_u,
        "sigma_v": sigma_v,
        "edge_extension_ratio": sigma_v / max(sigma_u, np.finfo(float).eps),
    }


def _support_distances(
    eigenvalues: np.ndarray,
    density: np.ndarray,
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
) -> np.ndarray:
    positive = np.clip(density, 0.0, None)
    threshold = 0.025 * float(np.max(positive))
    rows, columns = np.nonzero(positive >= threshold)
    if rows.size < 4:
        raise RuntimeError("theoretical density support was not numerically resolved")
    support = np.column_stack((real_axis[columns], imaginary_axis[rows]))
    points = np.column_stack((eigenvalues.real, eigenvalues.imag))
    return np.asarray(cKDTree(support).query(points)[0], dtype=np.float64)


def _spectrum_rows(
    square_spectrum: np.ndarray, rhombus_spectrum: np.ndarray
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for geometry, values in (
        ("square", square_spectrum),
        ("rhombus", rhombus_spectrum),
    ):
        for value in values:
            rows.append(
                {
                    "geometry": geometry,
                    "real_energy": float(value.real),
                    "imaginary_energy": float(value.imag),
                }
            )
    return rows


def _density_rows(
    real_axis: np.ndarray,
    imaginary_axis: np.ndarray,
    results: dict[str, dict[str, np.ndarray]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for geometry in ("square", "rhombus"):
        potential = results[geometry]["potential"]
        density = results[geometry]["density"]
        for row, imaginary in enumerate(imaginary_axis):
            for column, real in enumerate(real_axis):
                rows.append(
                    {
                        "geometry": geometry,
                        "real_energy": float(real),
                        "imaginary_energy": float(imaginary),
                        "potential": float(potential[row, column]),
                        "density": float(density[row, column]),
                        "positive_density": float(max(0.0, density[row, column])),
                    }
                )
    return rows


def compute(
    scale: str,
    *,
    workers: int,
    reuse_completed: bool,
) -> dict[str, object]:
    if workers < 1:
        raise ValueError("workers must be positive")
    config = CONFIGS[scale]
    started = time.perf_counter()
    square_length = int(config["square_length"])
    diamond_radius = int(config["diamond_radius"])
    scaling_lengths = tuple(int(value) for value in config["scaling_lengths"])
    square = square_sites(square_length)
    rhombus = diamond_sites(diamond_radius)
    output_root = output_directory(scale)
    checkpoint_root = output_root / "checkpoints"

    square_spectrum, square_spectrum_runtime, square_spectrum_source = (
        _load_or_compute_spectrum(
            square,
            checkpoint_root / "square_spectrum.npz",
            reuse_completed=reuse_completed,
        )
    )
    print(f"S5 square spectrum complete: N={len(square)}", flush=True)
    rhombus_spectrum, rhombus_spectrum_runtime, rhombus_spectrum_source = (
        _load_or_compute_spectrum(
            rhombus,
            checkpoint_root / "rhombus_spectrum.npz",
            reuse_completed=reuse_completed,
        )
    )
    print(f"S5 rhombus spectrum complete: N={len(rhombus)}", flush=True)

    broadening_rows: list[dict[str, object]] = []
    state_rows: list[dict[str, object]] = []
    display_probabilities: dict[str, np.ndarray] = {}
    maximum_residual = 0.0
    for length in scaling_lengths:
        sites = square_sites(length)
        matrix = build_obc_hamiltonian(sites, model_s27())
        for state, target, selection, candidate_count in (
            ("A_normal", TARGET_A, "narrowest", int(config["candidate_count_a"])),
            ("B_scale_free", TARGET_B, "widest", int(config["candidate_count_b"])),
        ):
            result = select_target_spatial_eigenstate(
                sites,
                matrix,
                target,
                selection=selection,
                candidate_count=candidate_count,
            )
            metrics = spatial_profile_metrics(sites, result.right_eigenvector)
            maximum_residual = max(maximum_residual, result.normalized_residual)
            broadening_rows.append(
                {
                    "state": state,
                    "selection_rule": selection,
                    "length": length,
                    "inverse_length": 1.0 / length,
                    "site_count": len(sites),
                    "target_real": target.real,
                    "target_imaginary": target.imag,
                    "eigenvalue_real": result.eigenvalue.real,
                    "eigenvalue_imaginary": result.eigenvalue.imag,
                    "rms_width": metrics.rms_width,
                    "inverse_rms_width": 1.0 / metrics.rms_width,
                    "effective_site_count": metrics.effective_site_count,
                    "boundary_mass": metrics.boundary_mass,
                    "normalized_residual": result.normalized_residual,
                }
            )
            if length == square_length:
                probability = _state_probability(result.right_eigenvector)
                display_probabilities[state] = probability
                for (x, y), value in zip(sites, probability, strict=True):
                    state_rows.append(
                        {
                            "state": state,
                            "geometry": "square",
                            "x": x,
                            "y": y,
                            "probability": float(value),
                            "probability_over_max": float(value / probability.max()),
                        }
                    )
        print(f"S5 broadening complete: L={length}", flush=True)

    rhombus_state = select_target_spatial_eigenstate(
        rhombus,
        build_obc_hamiltonian(rhombus, model_s27()),
        TARGET_RHOMBUS,
        selection="nearest",
        candidate_count=int(config["candidate_count_rhombus"]),
    )
    rhombus_metrics = spatial_profile_metrics(
        rhombus, rhombus_state.right_eigenvector
    )
    rhombus_probability = _state_probability(rhombus_state.right_eigenvector)
    rhombus_cut = _cut_spreads(rhombus, rhombus_probability)
    maximum_residual = max(maximum_residual, rhombus_state.normalized_residual)
    display_probabilities["rhombus_edge"] = rhombus_probability
    for (x, y), value in zip(rhombus, rhombus_probability, strict=True):
        state_rows.append(
            {
                "state": "rhombus_edge",
                "geometry": "rhombus",
                "x": x,
                "y": y,
                "probability": float(value),
                "probability_over_max": float(value / rhombus_probability.max()),
            }
        )

    real_axis = np.linspace(-2.0, 2.0, int(config["real_points"]))
    imaginary_axis = np.linspace(-20.0, 20.0, int(config["imaginary_points"]))
    density_results: dict[str, dict[str, np.ndarray]] = {}
    density_diagnostics: dict[str, dict[str, object]] = {}
    for basis in ("square", "rhombus"):
        potential, density, evaluations, runtime, source = _load_or_compute_density(
            basis,
            real_axis,
            imaginary_axis,
            checkpoint_root / f"{basis}_potential.npz",
            momentum_samples=int(config["momentum_samples"]),
            tolerance=float(config["minimizer_tolerance"]),
            workers=workers,
            reuse_completed=reuse_completed,
        )
        density_results[basis] = {"potential": potential, "density": density}
        positive = np.clip(density, 0.0, None)
        density_diagnostics[basis] = {
            "potential_source": source,
            "runtime_seconds": runtime,
            "objective_evaluations": evaluations,
            "potential_finite": bool(np.all(np.isfinite(potential))),
            "density_finite": bool(np.all(np.isfinite(density))),
            "positive_density_mass_in_window": float(
                np.sum(positive)
                * (real_axis[1] - real_axis[0])
                * (imaginary_axis[1] - imaginary_axis[0])
            ),
            "negative_density_fraction": float(np.mean(density < 0.0)),
        }

    square_distance = _support_distances(
        square_spectrum,
        density_results["square"]["density"],
        real_axis,
        imaginary_axis,
    )
    rhombus_distance = _support_distances(
        rhombus_spectrum,
        density_results["rhombus"]["density"],
        real_axis,
        imaginary_axis,
    )
    square_central = np.abs(square_spectrum.real) <= 0.35
    if np.count_nonzero(square_central) < 10:
        raise RuntimeError("square central spectral line was not resolved")

    a_rows = [row for row in broadening_rows if row["state"] == "A_normal"]
    b_rows = [row for row in broadening_rows if row["state"] == "B_scale_free"]
    lengths = np.asarray([row["length"] for row in a_rows], dtype=np.float64)
    inverse_lengths = 1.0 / lengths
    a_width = np.asarray([row["rms_width"] for row in a_rows], dtype=np.float64)
    b_width = np.asarray([row["rms_width"] for row in b_rows], dtype=np.float64)
    a_kappa_fit = _linear_fit(inverse_lengths, 1.0 / a_width)
    b_kappa_fit = _linear_fit(inverse_lengths, 1.0 / b_width)
    b_width_fit = _linear_fit(lengths, b_width)
    a_width_cv = float(np.std(a_width) / np.mean(a_width))
    b_scaled_width_cv = float(np.std(b_width / lengths) / np.mean(b_width / lengths))

    quadrature_probes = (0.0 + 0.0j, 0.0 + 8.0j, -1.0 + 10.0j, 1.5 + 8.0j)
    convergence: dict[str, float] = {}
    for basis in ("square", "rhombus"):
        differences = []
        for energy in quadrature_probes:
            fine = geometry_adaptive_potential(
                energy,
                model_s27(),
                basis=basis,
                momentum_samples=int(config["momentum_samples"]),
                tolerance=float(config["minimizer_tolerance"]),
            ).potential
            coarse = geometry_adaptive_potential(
                energy,
                model_s27(),
                basis=basis,
                momentum_samples=max(24, int(config["momentum_samples"]) // 2),
                tolerance=max(5e-4, 4.0 * float(config["minimizer_tolerance"])),
            ).potential
            differences.append(abs(fine - coarse))
        convergence[basis] = float(max(differences))

    spectrum_diagnostics = {
        "square": {
            "site_count": len(square),
            "runtime_seconds": square_spectrum_runtime,
            "source": square_spectrum_source,
            "trace_per_site_abs": float(abs(np.sum(square_spectrum)) / len(square)),
            "conjugation_symmetry": symmetric_cloud_distance(
                square_spectrum, np.conjugate(square_spectrum)
            ),
            "all_support_distance_median": float(np.median(square_distance)),
            "central_support_distance_median": float(
                np.median(square_distance[square_central])
            ),
        },
        "rhombus": {
            "site_count": len(rhombus),
            "runtime_seconds": rhombus_spectrum_runtime,
            "source": rhombus_spectrum_source,
            "trace_per_site_abs": float(abs(np.sum(rhombus_spectrum)) / len(rhombus)),
            "conjugation_symmetry": symmetric_cloud_distance(
                rhombus_spectrum, np.conjugate(rhombus_spectrum)
            ),
            "all_support_distance_median": float(np.median(rhombus_distance)),
        },
    }
    expected_counts_hold = (
        len(square) == square_length**2
        and len(rhombus) == 1 + 2 * diamond_radius * (diamond_radius + 1)
    )
    paper_counts_hold = scale != "paper" or (len(square) == 6400 and len(rhombus) == 6385)
    acceptance = {
        "all_six_numeric_subfigures_generated": True,
        "declared_geometry_counts_hold": expected_counts_hold and paper_counts_hold,
        "exact_spectra_have_declared_state_counts": (
            square_spectrum.size == len(square) and rhombus_spectrum.size == len(rhombus)
        ),
        "exact_spectra_obey_real_matrix_conjugation_symmetry": (
            spectrum_diagnostics["square"]["conjugation_symmetry"]["p95"] < 1e-6
            and spectrum_diagnostics["rhombus"]["conjugation_symmetry"]["p95"]
            < 1e-6
        ),
        "selected_eigenpairs_have_small_residual": maximum_residual < 1e-8,
        "normal_state_width_is_size_stable": a_width_cv < 0.16,
        "normal_state_retains_finite_inverse_width": a_kappa_fit["intercept"] > 0.15,
        "scale_free_width_is_linear_in_boundary_length": b_width_fit["r_squared"] > 0.97,
        "scale_free_width_over_length_is_stable": b_scaled_width_cv < 0.08,
        "scale_free_inverse_width_extrapolates_to_zero": abs(b_kappa_fit["intercept"])
        < 0.02,
        "rhombus_state_is_boundary_enriched": rhombus_metrics.boundary_mass > 0.25,
        "rhombus_state_extends_along_minus1_plus1_cut": rhombus_cut[
            "edge_extension_ratio"
        ]
        > 2.0,
        "geometry_potentials_are_converged": max(convergence.values()) < 0.03,
        "geometry_densities_are_finite": all(
            bool(item["density_finite"]) for item in density_diagnostics.values()
        ),
        "square_theory_prefers_stable_central_spectrum": (
            spectrum_diagnostics["square"]["central_support_distance_median"]
            < spectrum_diagnostics["square"]["all_support_distance_median"]
        ),
        "rhombus_theory_tracks_full_finite_spectrum": spectrum_diagnostics["rhombus"][
            "all_support_distance_median"
        ]
        < 0.8,
    }
    check = {
        "schema_version": 1,
        "paper_id": "2407.01296",
        "target_id": "T008",
        "figure_refs": [
            "Supplementary Fig. S5(a)",
            "Supplementary Fig. S5(b)",
            "Supplementary Fig. S5(c)",
            "Supplementary Fig. S5(d)",
            "Supplementary Fig. S5(e)",
            "Supplementary Fig. S5(f)",
        ],
        "status": "passed" if all(acceptance.values()) else "failed",
        "artifact_stage": "scientific_reproduction",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_copied_into_reproduction": False,
        "source_curves_used_as_generated_inputs": False,
        "formula_refs": ["EQC014"],
        "formula_interpretation": (
            "Eq. (S27) is expanded into eight directed hoppings. Square and "
            "rhombus OBC matrices are diagonalized independently; Eq. (10) is "
            "evaluated in each cut basis. A is the narrowest state and B is the "
            "widest state in declared local shift-invert windows; neither choice "
            "inspects source pixels."
        ),
        "scale": scale,
        "config": config,
        "state_targets": {
            "A_normal": [TARGET_A.real, TARGET_A.imag],
            "B_scale_free": [TARGET_B.real, TARGET_B.imag],
            "rhombus_edge": [TARGET_RHOMBUS.real, TARGET_RHOMBUS.imag],
        },
        "state_selection_rules": {
            "A_normal": "minimum RMS width in deterministic local shift-invert set",
            "B_scale_free": "maximum RMS width in deterministic local shift-invert set",
            "rhombus_edge": "nearest eigenvalue in deterministic local shift-invert set",
        },
        "broadening": {
            "normal_width_coefficient_of_variation": a_width_cv,
            "scale_free_width_over_length_coefficient_of_variation": b_scaled_width_cv,
            "normal_inverse_width_fit": a_kappa_fit,
            "scale_free_inverse_width_fit": b_kappa_fit,
            "scale_free_width_fit": b_width_fit,
        },
        "rhombus_state": {
            "eigenvalue": [rhombus_state.eigenvalue.real, rhombus_state.eigenvalue.imag],
            "normalized_residual": rhombus_state.normalized_residual,
            "profile": asdict(rhombus_metrics),
            "cut_spreads": rhombus_cut,
        },
        "maximum_selected_eigenpair_residual": maximum_residual,
        "potential_quadrature_max_changes": convergence,
        "density_diagnostics": density_diagnostics,
        "spectrum_diagnostics": spectrum_diagnostics,
        "acceptance": acceptance,
        "runtime_seconds": time.perf_counter() - started,
    }

    data_dir = output_root / "data"
    write_rows(data_dir / "supp_fig_s5_spectra.csv", _spectrum_rows(square_spectrum, rhombus_spectrum))
    write_rows(data_dir / "supp_fig_s5_states.csv", state_rows)
    write_rows(data_dir / "supp_fig_s5_broadening.csv", broadening_rows)
    write_rows(
        data_dir / "supp_fig_s5_density.csv",
        _density_rows(real_axis, imaginary_axis, density_results),
    )
    np.savez_compressed(
        data_dir / "supp_fig_s5_arrays.npz",
        real_axis=real_axis,
        imaginary_axis=imaginary_axis,
        square_spectrum=square_spectrum,
        rhombus_spectrum=rhombus_spectrum,
        square_potential=density_results["square"]["potential"],
        square_density=density_results["square"]["density"],
        rhombus_potential=density_results["rhombus"]["potential"],
        rhombus_density=density_results["rhombus"]["density"],
        square_state_a=display_probabilities["A_normal"],
        square_state_b=display_probabilities["B_scale_free"],
        rhombus_state=rhombus_probability,
    )
    return {
        "check": check,
        "output_root": output_root,
        "square_sites": square,
        "rhombus_sites": rhombus,
        "square_spectrum": square_spectrum,
        "rhombus_spectrum": rhombus_spectrum,
        "broadening_rows": broadening_rows,
        "display_probabilities": display_probabilities,
        "real_axis": real_axis,
        "imaginary_axis": imaginary_axis,
        "density_results": density_results,
    }


def render(result: dict[str, object]) -> None:
    configure_matplotlib()
    output_root = Path(result["output_root"])
    square_sites_data = result["square_sites"]
    rhombus_sites_data = result["rhombus_sites"]
    square_spectrum = np.asarray(result["square_spectrum"])
    rhombus_spectrum = np.asarray(result["rhombus_spectrum"])
    broadening_rows = result["broadening_rows"]
    probabilities = result["display_probabilities"]
    real_axis = np.asarray(result["real_axis"])
    imaginary_axis = np.asarray(result["imaginary_axis"])
    density_results = result["density_results"]

    figure = plt.figure(figsize=(11.2, 7.4), constrained_layout=True)
    outer = figure.add_gridspec(2, 3)
    panel_a = outer[0, 0].subgridspec(2, 2, height_ratios=(1.0, 0.82))
    state_a_axis = figure.add_subplot(panel_a[0, 0])
    state_b_axis = figure.add_subplot(panel_a[0, 1])
    scaling_axis = figure.add_subplot(panel_a[1, :])
    rhombus_state_axis = figure.add_subplot(outer[0, 1])
    square_spectrum_axis = figure.add_subplot(outer[0, 2])
    rhombus_spectrum_axis = figure.add_subplot(outer[1, 0])
    square_density_axis = figure.add_subplot(outer[1, 1])
    rhombus_density_axis = figure.add_subplot(outer[1, 2])

    square_length = int(round(np.sqrt(len(square_sites_data))))
    for axis, state, label in (
        (state_a_axis, "A_normal", "A: normal"),
        (state_b_axis, "B_scale_free", "B: scale-free"),
    ):
        image = np.asarray(probabilities[state]).reshape(square_length, square_length)
        axis.imshow(
            image / image.max(),
            origin="lower",
            cmap="Reds",
            vmin=0.0,
            vmax=1.0,
            interpolation="nearest",
        )
        axis.set_title(label, fontsize=8)
        axis.set_xticks([])
        axis.set_yticks([])
    state_a_axis.text(-0.3, 1.18, "(a)", transform=state_a_axis.transAxes, fontsize=10)

    for state, marker, color, label in (
        ("A_normal", "o", "#0072B2", "A normal"),
        ("B_scale_free", "s", "#D55E00", "B scale-free"),
    ):
        rows = [row for row in broadening_rows if row["state"] == state]
        scaling_axis.plot(
            [row["inverse_length"] for row in rows],
            [row["inverse_rms_width"] for row in rows],
            marker=marker,
            markersize=3.2,
            linewidth=1.0,
            color=color,
            label=label,
        )
    scaling_axis.set_xlabel(r"$1/L$", fontsize=8)
    scaling_axis.set_ylabel(r"$1/\sigma_r$", fontsize=8)
    scaling_axis.tick_params(labelsize=7)
    scaling_axis.legend(frameon=False, fontsize=6)

    rhombus_coordinates = np.asarray(rhombus_sites_data)
    rhombus_probability = np.asarray(probabilities["rhombus_edge"])
    rhombus_state_axis.scatter(
        rhombus_coordinates[:, 0],
        rhombus_coordinates[:, 1],
        c=rhombus_probability / rhombus_probability.max(),
        s=max(0.35, 4500.0 / len(rhombus_sites_data)),
        cmap="Reds",
        vmin=0.0,
        vmax=1.0,
        linewidths=0,
    )
    rhombus_state_axis.set_aspect("equal")
    rhombus_state_axis.set_xticks([])
    rhombus_state_axis.set_yticks([])
    rhombus_state_axis.set_title("(b) rhombus edge state", loc="left", fontsize=9)

    for axis, spectrum, title in (
        (square_spectrum_axis, square_spectrum, "(c) square exact OBC spectrum"),
        (rhombus_spectrum_axis, rhombus_spectrum, "(d) rhombus exact OBC spectrum"),
    ):
        axis.scatter(spectrum.real, spectrum.imag, s=1.0, color="black", linewidths=0)
        axis.set_xlim(-2.0, 2.0)
        axis.set_ylim(-20.0, 20.0)
        axis.set_xlabel(r"Re $E$")
        axis.set_ylabel(r"Im $E$")
        axis.set_title(title, loc="left", fontsize=9)

    for axis, geometry, title in (
        (square_density_axis, "square", "(e) square Eq. (10) density"),
        (rhombus_density_axis, "rhombus", "(f) rhombus Eq. (10) density"),
    ):
        positive = np.clip(density_results[geometry]["density"], 0.0, None)
        nonzero = positive[positive > 0.0]
        vmax = float(np.quantile(nonzero, 0.995)) if nonzero.size else 1.0
        image = axis.imshow(
            positive,
            origin="lower",
            extent=(real_axis[0], real_axis[-1], imaginary_axis[0], imaginary_axis[-1]),
            cmap="afmhot",
            vmin=0.0,
            vmax=max(vmax, np.finfo(float).eps),
            interpolation="nearest",
            aspect="auto",
        )
        axis.set_xlabel(r"Re $E$")
        axis.set_ylabel(r"Im $E$")
        axis.set_title(title, loc="left", fontsize=9)
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.03, label=r"$\rho(E)$")

    figure_path = output_root / "figures" / "supp_fig_s5_reproduction.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path, dpi=240)
    figure.savefig(
        figure_path.with_suffix(".pdf"),
        metadata={"CreationDate": None, "ModDate": None},
    )
    svg_path = figure_path.with_suffix(".svg")
    figure.savefig(svg_path, metadata={"Date": None})
    plt.close(figure)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    result = compute(
        args.scale,
        workers=args.workers,
        reuse_completed=args.reuse_completed,
    )
    render(result)
    check = result["check"]
    check_dir = Path(result["output_root"]) / "checks"
    check_dir.mkdir(parents=True, exist_ok=True)
    (check_dir / "supp_fig_s5.json").write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(check, indent=2, ensure_ascii=False))
    return 0 if check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
