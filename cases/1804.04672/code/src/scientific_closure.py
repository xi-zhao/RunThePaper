"""Clean-room scientific closure for the seven previously pending targets.

The runner consumes only the frozen JSON configuration and equation-derived
case-local kernels.  Paper source, author code/data, and reference pixels are
not runtime inputs.  It records numerical evidence and publication-input
audits but intentionally does not assign an independent-review verdict.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment
import scipy.sparse.linalg as spla

from implementation_closure import _generic_open_geometry_hamiltonian
from nonhermitian_chern import (
    CylinderParams,
    SquareParams,
    cylinder_non_bloch_gap_boundaries,
    fig2_square_parameter_sets,
    generate_cylinder_spectrum_rows,
    generate_square_spectrum_rows,
    non_bloch_bulk_min_abs_energy,
    non_bloch_chern_number,
    square_hamiltonian_sparse,
    square_initial_wavepacket,
    square_site_intensity,
    square_wavepacket_snapshots,
)
from supplemental_campaign import (
    exact_cylinder_hamiltonian,
    exact_cylinder_phase_rows,
    exact_model_phase_rows,
    exact_square_similarity_transform_residual,
    s4_finite_size_scan,
    s4_parameter_rows,
    similarity_transform_residual,
)


TARGET_IDS = ("T001", "T002", "T004", "T007", "T010", "T011", "T012")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _main_edge_trace_residual(kx: float, energy: complex, gamma: float) -> float:
    return float(
        min(
            abs(energy - (np.sin(kx) + 1.0j * gamma)),
            abs(energy - (-np.sin(kx) - 1.0j * gamma)),
        )
    )


def _main_cylinder_check(parameters: dict[str, Any]) -> dict[str, Any]:
    resolutions: list[dict[str, Any]] = []
    for points in parameters["kx_grids"]:
        params = CylinderParams(
            gamma_x=float(parameters["gamma"]),
            gamma_y=float(parameters["gamma"]),
            m=float(parameters["m"]),
            L_y=int(parameters["length_y"]),
            target_id="T001",
        )
        grid = np.linspace(-np.pi, np.pi, int(points), endpoint=False)
        rows = generate_cylinder_spectrum_rows(grid, params)
        candidates: list[dict[str, Any]] = []
        bulk: list[dict[str, Any]] = []
        for row in rows:
            energy = complex(float(row["energy_real"]), float(row["energy_imag"]))
            residual = _main_edge_trace_residual(
                float(row["kx"]), energy, float(parameters["gamma"])
            )
            if (
                residual <= float(parameters["edge_trace_residual_tolerance"])
                and abs(abs(energy.imag) - float(parameters["gamma"]))
                <= float(parameters["edge_imaginary_plateau_tolerance"])
            ):
                candidates.append(
                    {
                        "trace_residual": residual,
                        "edge_weight": max(
                            float(row["edge_weight_left"]),
                            float(row["edge_weight_right"]),
                        ),
                    }
                )
            else:
                bulk.append(row)
        if not candidates or not bulk:
            raise RuntimeError("T001 classifier returned an empty scientific partition")
        resolutions.append(
            {
                "kx_points": int(points),
                "spectrum_row_count": len(rows),
                "edge_candidate_count": len(candidates),
                "edge_candidates_per_kx": len(candidates) / int(points),
                "maximum_trace_residual": max(
                    float(row["trace_residual"]) for row in candidates
                ),
                "median_edge_weight": float(
                    np.median([float(row["edge_weight"]) for row in candidates])
                ),
                "bulk_line_gap": 2.0
                * min(abs(float(row["energy_real"])) for row in bulk),
            }
        )
    density_shift = abs(
        float(resolutions[-1]["edge_candidates_per_kx"])
        - float(resolutions[0]["edge_candidates_per_kx"])
    )
    flags = {
        "paper_scale_grid_executed": resolutions[-1]["kx_points"] == 180,
        "trace_residual_pass": all(
            row["maximum_trace_residual"]
            <= float(parameters["edge_trace_residual_tolerance"])
            for row in resolutions
        ),
        "edge_localization_pass": all(
            row["median_edge_weight"]
            >= float(parameters["minimum_median_edge_weight"])
            for row in resolutions
        ),
        "bulk_line_gap_pass": all(
            row["bulk_line_gap"] >= float(parameters["minimum_bulk_line_gap"])
            for row in resolutions
        ),
        "kx_convergence_pass": density_shift
        <= float(parameters["maximum_edge_density_shift"]),
    }
    return {
        "target_id": "T001",
        "scientific_status": "author_evidence_ready_for_fresh_review",
        "method": "finite_open_y_strip_diagonalization_plus_analytic_edge_trace_and_resolution_check",
        "resolutions": resolutions,
        "edge_density_shift": density_shift,
        "flags": flags,
        "passed": all(flags.values()),
    }


def _cylinder_phase_check(parameters: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for gamma in parameters["gamma_values"]:
        lower, upper = cylinder_non_bloch_gap_boundaries(float(gamma))
        row: dict[str, Any] = {
            "gamma": float(gamma),
            "analytic_lower": lower,
            "analytic_upper": upper,
            "strip_midpoint_abs_energy": non_bloch_bulk_min_abs_energy(
                float(gamma), 0.5 * (lower + upper), coarse_points=81
            ),
            "chern_by_grid": {},
        }
        for points in parameters["chern_grids"]:
            row["chern_by_grid"][str(points)] = {
                "left": non_bloch_chern_number(
                    float(gamma),
                    lower - float(parameters["mass_margin"]),
                    kx_points=int(points),
                    ky_points=int(points),
                    gap_threshold=float(parameters["gap_threshold"]),
                ),
                "right": non_bloch_chern_number(
                    float(gamma),
                    upper + float(parameters["mass_margin"]),
                    kx_points=int(points),
                    ky_points=int(points),
                    gap_threshold=float(parameters["gap_threshold"]),
                ),
            }
        rows.append(row)
    flags = {
        "chern_quantization_pass": all(
            values == {"left": 1, "right": 0}
            for row in rows
            for values in row["chern_by_grid"].values()
        ),
        "grid_convergence_pass": all(
            len({(values["left"], values["right"]) for values in row["chern_by_grid"].values()})
            == 1
            for row in rows
        ),
        "gapless_strip_pass": all(
            row["strip_midpoint_abs_energy"]
            <= float(parameters["maximum_strip_midpoint_abs_energy"])
            for row in rows
        ),
    }
    return {
        "target_id": "T002",
        "scientific_status": "author_evidence_ready_for_fresh_review",
        "method": "biorthogonal_FHS_on_non_Bloch_torus_with_two_grid_sizes",
        "rows": rows,
        "flags": flags,
        "passed": all(flags.values()),
    }


def _density_metrics(rows: list[dict[str, Any]], length: int, layers: int) -> dict[str, float]:
    density = np.zeros((length, length), dtype=float)
    for row in rows:
        density[int(float(row["y"])) - 1, int(float(row["x"])) - 1] = float(
            row["intensity"]
        )
    y_grid, x_grid = np.indices(density.shape)
    x_grid = x_grid + 1
    y_grid = y_grid + 1
    boundary = (
        (x_grid <= layers)
        | (x_grid > length - layers)
        | (y_grid <= layers)
        | (y_grid > length - layers)
    )
    return {
        "normalization": float(density.sum()),
        "center_x": float(np.sum(density * x_grid)),
        "center_y": float(np.sum(density * y_grid)),
        "boundary_fraction": float(density[boundary].sum()),
        "interior_fraction": float(density[~boundary].sum()),
        "top_edge_fraction": float(density[:layers, :].sum()),
    }


def _square_dynamics_check(parameters: dict[str, Any]) -> dict[str, Any]:
    length = int(parameters["length"])
    parameter_sets = fig2_square_parameter_sets(length)
    spectrum = generate_square_spectrum_rows(
        parameter_sets, eigen_count=int(parameters["eigen_count"])
    )
    results: dict[str, Any] = {}
    for label, params in parameter_sets.items():
        rows = square_wavepacket_snapshots(params, parameters["times"])
        snapshots = {}
        for time in parameters["times"]:
            snapshots[str(float(time))] = _density_metrics(
                [row for row in rows if np.isclose(float(row["time"]), float(time))],
                length,
                int(parameters["boundary_layers"]),
            )
        eigenvalues = np.asarray(
            [
                complex(float(row["energy_real"]), float(row["energy_imag"]))
                for row in spectrum
                if row["parameter_set"] == label
            ],
            dtype=np.complex128,
        )
        hamiltonian = square_hamiltonian_sparse(params)
        initial = square_initial_wavepacket(params)
        direct = spla.expm_multiply((-20.0j) * hamiltonian, initial)
        half = spla.expm_multiply((-10.0j) * hamiltonian, initial)
        split = spla.expm_multiply((-10.0j) * hamiltonian, half)
        semigroup_density_l1 = float(
            np.abs(
                square_site_intensity(np.asarray(direct), length)
                - square_site_intensity(np.asarray(split), length)
            ).sum()
        )
        results[label] = {
            "paper_parameters": {
                "length": length,
                "m": float(params.m),
                "gamma_x": float(params.gamma_x),
                "gamma_y": float(params.gamma_y),
            },
            "line_gap": 2.0 * float(np.min(np.abs(eigenvalues.real))),
            "maximum_abs_imaginary_energy": float(np.max(np.abs(eigenvalues.imag))),
            "snapshots": snapshots,
            "semigroup_density_l1": semigroup_density_l1,
        }
    trivial = results["fig2a"]
    topological = results["fig2b"]
    initial_x = float(topological["snapshots"]["0.0"]["center_x"])
    flags = {
        "paper_parameters_executed": length == 30
        and parameters["times"] == [0.0, 5.0, 20.0]
        and int(parameters["eigen_count"]) == 22,
        "normalization_pass": all(
            abs(float(snapshot["normalization"]) - 1.0) <= 1e-12
            for result in results.values()
            for snapshot in result["snapshots"].values()
        ),
        "trivial_gap_pass": float(parameters["trivial_line_gap_interval"][0])
        <= float(trivial["line_gap"])
        <= float(parameters["trivial_line_gap_interval"][1]),
        "topological_in_gap_states_pass": float(topological["line_gap"])
        <= float(parameters["maximum_topological_in_gap_scale"]),
        "trivial_bulk_leakage_pass": float(
            trivial["snapshots"]["5.0"]["interior_fraction"]
        )
        >= float(parameters["minimum_trivial_interior_fraction_t5"]),
        "topological_edge_motion_pass": float(
            topological["snapshots"]["20.0"]["boundary_fraction"]
        )
        >= float(parameters["minimum_topological_boundary_fraction_t20"])
        and float(topological["snapshots"]["20.0"]["center_x"]) - initial_x
        >= float(parameters["minimum_topological_x_displacement_t20"]),
        "time_semigroup_pass": all(
            float(result["semigroup_density_l1"])
            <= float(parameters["maximum_semigroup_density_l1"])
            for result in results.values()
        ),
    }
    return {
        "target_id": "T004",
        "scientific_status": "author_evidence_ready_for_fresh_review",
        "method": "paper_scale_sparse_open_square_spectrum_and_Krylov_time_evolution",
        "parameter_sets": results,
        "flags": flags,
        "passed": all(flags.values()),
    }


def _select_s4_boundaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    keys = sorted({(str(row["panel"]), float(row["gamma"])) for row in rows})
    for family, gamma in keys:
        subset = [
            row
            for row in rows
            if str(row["panel"]) == family and float(row["gamma"]) == gamma
        ]
        best = min(subset, key=lambda row: abs(float(row["intercept_gap_square"])))
        selected.append(
            {
                "family": family,
                "gamma": gamma,
                "theory_m": float(best["theory_m"]),
                "selected_m": float(best["m"]),
                "boundary_error": abs(float(best["m"]) - float(best["theory_m"])),
                "intercept_gap_square": float(best["intercept_gap_square"]),
            }
        )
    return selected


def _s4_check(parameters: dict[str, Any]) -> dict[str, Any]:
    start = perf_counter()
    analytic_rows = s4_parameter_rows(parameters["gamma_values"])
    windows = []
    for sizes in parameters["size_windows"]:
        rows = s4_finite_size_scan(
            parameters["families"],
            parameters["gamma_values"],
            sizes,
            parameters["mass_offsets"],
        )
        windows.append({"sizes": list(sizes), "selected_boundaries": _select_s4_boundaries(rows)})
    elapsed = perf_counter() - start
    shifts = []
    first = {(row["family"], row["gamma"]): row for row in windows[0]["selected_boundaries"]}
    second = {(row["family"], row["gamma"]): row for row in windows[1]["selected_boundaries"]}
    for key in sorted(first):
        shifts.append(
            {
                "family": key[0],
                "gamma": key[1],
                "window_shift": abs(first[key]["selected_m"] - second[key]["selected_m"]),
            }
        )
    flags = {
        "all_six_analytic_series_present": len(analytic_rows)
        == 3 * len(parameters["families"]) * len(parameters["gamma_values"]),
        "finite_size_boundary_pass": all(
            row["boundary_error"] <= float(parameters["maximum_boundary_error"])
            for window in windows
            for row in window["selected_boundaries"]
        ),
        "size_window_convergence_pass": all(
            row["window_shift"] <= float(parameters["maximum_window_shift"])
            for row in shifts
        ),
    }
    return {
        "target_id": "T007",
        "scientific_status": "author_evidence_ready_for_fresh_review",
        "method": "printed_analytic_curves_plus_two_window_finite_square_gap_squared_extrapolation",
        "analytic_rows": analytic_rows,
        "finite_size_windows": windows,
        "window_shifts": shifts,
        "measured_runtime_seconds": elapsed,
        "publication_input_audit": parameters["publication_input_audit"],
        "flags": flags,
        "passed": all(flags.values()),
    }


def _exact_phase_check(parameters: dict[str, Any]) -> dict[str, Any]:
    grid = parameters["gamma_grid"]
    gammas = np.linspace(float(grid["start"]), float(grid["stop"]), int(grid["points"]))
    rows = exact_model_phase_rows(gammas, t=float(parameters["t"]))
    residuals = [
        exact_square_similarity_transform_residual(
            int(parameters["similarity_length"]), float(gamma), float(gamma), t=float(parameters["t"])
        )
        for gamma in parameters["similarity_gammas"]
    ]
    open_boundary = [float(row["m"]) for row in rows if row["series"] == "open_boundary_non_bloch"]
    flags = {
        "three_dense_series_present": len(rows) == 3 * len(gammas),
        "gamma_independent_open_boundary": max(open_boundary) - min(open_boundary) <= 1e-14,
        "two_dimensional_similarity_pass": max(residuals)
        <= float(parameters["maximum_similarity_residual"]),
    }
    return {
        "target_id": "T010",
        "scientific_status": "author_evidence_ready_for_fresh_review",
        "method": "dense_exact_phase_formulas_plus_full_open_square_similarity_identity",
        "rows": rows,
        "square_similarity_residuals": residuals,
        "flags": flags,
        "passed": all(flags.values()),
    }


def _match_spectra(left: np.ndarray, right: np.ndarray) -> float:
    assignment_left, assignment_right = linear_sum_assignment(
        np.abs(left[:, None] - right[None, :])
    )
    return float(np.max(np.abs(left[assignment_left] - right[assignment_right])))


def _exact_edge_trace_residual(kx: float, energy: complex, gamma: float) -> float:
    trace = np.sin(complex(kx, gamma))
    return float(min(abs(energy - trace), abs(energy + trace)))


def _exact_cylinder_check(parameters: dict[str, Any]) -> dict[str, Any]:
    grid = parameters["gamma_grid"]
    gamma_values = np.linspace(
        float(grid["start"]), float(grid["stop"]), int(grid["points"])
    )
    phase_rows = exact_cylinder_phase_rows(gamma_values, t=float(parameters["t"]))
    resolutions = []
    for points in parameters["kx_grids"]:
        edges = []
        bulk_real = []
        max_similarity_spectrum_residual = 0.0
        for kx in np.linspace(-np.pi, np.pi, int(points), endpoint=False):
            h = exact_cylinder_hamiltonian(
                float(kx),
                gamma_x=float(parameters["gamma"]),
                gamma_y=float(parameters["gamma"]),
                m=float(parameters["m"]),
                t=float(parameters["t"]),
                length_y=int(parameters["length_y"]),
            ).toarray()
            h_zero = exact_cylinder_hamiltonian(
                float(kx),
                gamma_x=float(parameters["gamma"]),
                gamma_y=0.0,
                m=float(parameters["m"]),
                t=float(parameters["t"]),
                length_y=int(parameters["length_y"]),
            ).toarray()
            values = np.linalg.eigvals(h)
            zero_values, zero_vectors = np.linalg.eig(h_zero)
            max_similarity_spectrum_residual = max(
                max_similarity_spectrum_residual,
                _match_spectra(values, zero_values),
            )
            for index, energy in enumerate(zero_values):
                density = np.sum(
                    np.abs(zero_vectors[:, index].reshape(int(parameters["length_y"]), 2)) ** 2,
                    axis=1,
                )
                density /= density.sum()
                layers = max(1, int(parameters["length_y"]) // 10)
                edge_weight = max(float(density[:layers].sum()), float(density[-layers:].sum()))
                residual = _exact_edge_trace_residual(
                    float(kx), complex(energy), float(parameters["gamma"])
                )
                if (
                    residual <= float(parameters["edge_trace_residual_tolerance"])
                    and edge_weight >= float(parameters["edge_weight_threshold"])
                ):
                    edges.append({"residual": residual, "edge_weight": edge_weight})
                else:
                    bulk_real.append(abs(float(energy.real)))
        if not edges or not bulk_real:
            raise RuntimeError("T011 classifier returned an empty scientific partition")
        resolutions.append(
            {
                "kx_points": int(points),
                "edge_candidate_count": len(edges),
                "edge_candidates_per_kx": len(edges) / int(points),
                "maximum_edge_trace_residual": max(row["residual"] for row in edges),
                "median_edge_weight": float(np.median([row["edge_weight"] for row in edges])),
                "bulk_line_gap": 2.0 * min(bulk_real),
                "maximum_similarity_spectrum_residual": max_similarity_spectrum_residual,
            }
        )
    density_shift = abs(
        resolutions[-1]["edge_candidates_per_kx"]
        - resolutions[0]["edge_candidates_per_kx"]
    )
    transform_residual = similarity_transform_residual(
        int(parameters["length_y"]), float(parameters["gamma"])
    )
    flags = {
        "four_dense_phase_series_present": len(phase_rows) == 4 * len(gamma_values),
        "paper_spectrum_parameters_executed": resolutions[-1]["kx_points"] == 180
        and int(parameters["length_y"]) == 40,
        "edge_trace_pass": all(
            row["maximum_edge_trace_residual"]
            <= float(parameters["edge_trace_residual_tolerance"])
            for row in resolutions
        ),
        "bulk_gap_pass": all(
            row["bulk_line_gap"] >= float(parameters["minimum_bulk_line_gap"])
            for row in resolutions
        ),
        "kx_convergence_pass": density_shift
        <= float(parameters["maximum_edge_density_shift"]),
        "similarity_transform_pass": transform_residual
        <= float(parameters["maximum_similarity_residual"])
        and all(
            row["maximum_similarity_spectrum_residual"]
            <= float(parameters["maximum_similarity_residual"])
            for row in resolutions
        ),
    }
    return {
        "target_id": "T011",
        "scientific_status": "author_evidence_ready_for_fresh_review",
        "method": "dense_exact_phase_curves_plus_paper_scale_open_y_spectrum_similarity_and_edge_trace",
        "phase_rows": phase_rows,
        "resolutions": resolutions,
        "edge_density_shift": density_shift,
        "finite_strip_similarity_transform_residual": transform_residual,
        "flags": flags,
        "passed": all(flags.values()),
    }


def _triangle_check(parameters: dict[str, Any]) -> dict[str, Any]:
    witnesses = []
    for extent in parameters["witness_extents"]:
        sites = tuple((x, y) for y in range(int(extent)) for x in range(int(extent) - y))
        gaps = []
        for mass in parameters["masses"]:
            matrix = _generic_open_geometry_hamiltonian(
                sites,
                SquareParams(
                    L=int(extent),
                    m=float(mass),
                    gamma_x=float(parameters["gamma"]),
                    gamma_y=float(parameters["gamma"]),
                    target_id="T012",
                ),
            ).toarray()
            values = np.linalg.eigvals(matrix)
            gaps.append(
                {"m": float(mass), "minimum_abs_energy": float(np.min(np.abs(values)))}
            )
        witnesses.append(
            {
                "extent": int(extent),
                "site_count": len(sites),
                "geometry": "right_isosceles_integer_site_triangle",
                "gaps": gaps,
            }
        )
    flags = {
        "representative_kernel_executed": all(
            np.isfinite(row["minimum_abs_energy"])
            for witness in witnesses
            for row in witness["gaps"]
        ),
        "publication_source_audit_complete": bool(
            parameters["publication_input_audit"]["source_refs"]
            and parameters["publication_input_audit"]["indispensable_inputs_not_published"]
        ),
    }
    return {
        "target_id": "T012",
        "scientific_status": "publication_input_missing_candidate_for_fresh_review",
        "method": "representative_triangle_witness_plus_publication_input_audit",
        "witnesses": witnesses,
        "publication_input_audit": parameters["publication_input_audit"],
        "flags": flags,
        "passed": all(flags.values()),
    }


def run_scientific_closure(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["scientific_parameters"]
    results = {
        "T001": _main_cylinder_check(parameters["T001"]),
        "T002": _cylinder_phase_check(parameters["T002"]),
        "T004": _square_dynamics_check(parameters["T004"]),
        "T007": _s4_check(parameters["T007"]),
        "T010": _exact_phase_check(parameters["T010"]),
        "T011": _exact_cylinder_check(parameters["T011"]),
        "T012": _triangle_check(parameters["T012"]),
    }
    for target_id, result in results.items():
        _write_json(output_root / "data" / "scientific_closure" / f"{target_id}.json", result)
        _write_json(
            output_root / "checks" / "scientific_closure" / f"{target_id}.json",
            {
                "schema_version": 1,
                "paper_id": config["paper_id"],
                "target_id": target_id,
                "status": "passed" if result["passed"] else "failed",
                "scientific_status": result["scientific_status"],
                "method": result["method"],
                "flags": result["flags"],
                "data_ref": f"outputs/data/scientific_closure/{target_id}.json",
            },
        )
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "target_ids": list(TARGET_IDS),
        "status": "passed" if all(result["passed"] for result in results.values()) else "failed",
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "results": {
            target_id: {
                "status": "passed" if result["passed"] else "failed",
                "scientific_status": result["scientific_status"],
            }
            for target_id, result in results.items()
        },
    }
    _write_json(output_root / "checks" / "scientific_closure" / "manifest.json", manifest)
    return manifest
