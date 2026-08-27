#!/usr/bin/env python3
"""Generate all independent numerical evidence for arXiv:1812.05561.

This script is the isolated-run entry point.  It creates structured arrays and
machine-readable scientific checks only.  Rendering and source-figure
comparison happen after the generated arrays have been hash-frozen.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Callable

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
from scipy.sparse.linalg import expm_multiply

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.scar_reproduction import (
    Bipartition,
    HamiltonianFamily,
    ansatz_couplings,
    fsa_basis,
    fsa_diagnostics,
    harmonic_gap_and_period,
    level_statistics,
    low_energy_schmidt_scan,
    neel_state,
    sector_hamiltonian,
    sector_neel_vector,
    solve_h0,
    su2_constraint,
    toy_diagnostics,
)
from src.atomic_closure import (
    entropy_fit_evidence,
    perfect_revival_overlap_bound,
    revival_fit_evidence,
    turning_point_power_law,
)


ROOT = Path.cwd()
DATA_DIR = ROOT / "outputs" / "data"
CHECK_DIR = ROOT / "outputs" / "checks"


def read_config() -> dict[str, Any]:
    path = Path("config/reduced_scale.json")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["parameters"]


def timed(name: str, function: Callable[[], Any], timings: dict[str, float]) -> Any:
    started = time.perf_counter()
    result = function()
    timings[name] = round(time.perf_counter() - started, 6)
    print(f"{name}: {timings[name]:.3f} s", flush=True)
    return result


def save_npz(name: str, **arrays: Any) -> Path:
    path = DATA_DIR / name
    np.savez_compressed(path, **arrays)
    return path


def hermiticity_error(matrix: Any) -> float:
    difference = matrix - matrix.conjugate().transpose()
    if getattr(difference, "nnz", 0) == 0:
        return 0.0
    return float(np.max(np.abs(difference.data)))


def optimize_main_figure_c(
    family: HamiltonianFamily,
    h0: float,
    tau: float,
    max_iterations: int,
) -> dict[str, Any]:
    distances = np.asarray(family.distances)
    initial_couplings = ansatz_couplings(h0, int(distances[-1]))
    initial = np.asarray([initial_couplings[int(distance)] for distance in distances] + [tau])
    initial_state = np.zeros(len(family.basis), dtype=np.complex128)
    initial_index = family.indices[neel_state(family.n_sites)]
    initial_state[initial_index] = 1.0

    def objective(values: np.ndarray) -> float:
        coupling_values = values[:-1]
        revival_time = float(values[-1])
        if np.any(np.abs(coupling_values) > 0.2) or not 3.5 <= revival_time <= 6.0:
            return 1.0 + float(np.sum(np.maximum(np.abs(coupling_values) - 0.2, 0.0) ** 2))
        couplings = {int(distance): float(value) for distance, value in zip(distances, coupling_values)}
        matrix = family.matrix(couplings)
        evolved = expm_multiply(-1j * matrix * revival_time, initial_state, traceA=0.0)
        return float(1.0 - abs(evolved[initial_index]) ** 2)

    result = minimize(
        objective,
        initial,
        method="Nelder-Mead",
        options={
            "maxiter": max_iterations,
            "xatol": 2e-6,
            "fatol": 1e-11,
            "adaptive": True,
        },
    )
    return {
        "distances": distances,
        "optimized": np.asarray(result.x[:-1]),
        "ansatz": np.asarray([initial_couplings[int(distance)] for distance in distances]),
        "revival_time": float(result.x[-1]),
        "infidelity": float(result.fun),
        "success": bool(result.success),
        "message": str(result.message),
        "nfev": int(result.nfev),
    }


def run_main_figure_1(parameters: dict[str, Any], h0: float, tau: float) -> dict[str, Any]:
    config = parameters["main_figure_1"]
    n_sites = int(config["n_sites"])
    max_range = int(config["max_range"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=max_range)
    optimization = optimize_main_figure_c(family, h0, tau, int(config["optimization_maxiter"]))
    couplings = ansatz_couplings(h0, max_range)
    unperturbed = family.matrix({})
    deformed = family.matrix(couplings)
    initial = np.zeros(len(family.basis), dtype=np.complex128)
    initial_index = family.indices[neel_state(n_sites)]
    initial[initial_index] = 1.0
    times = np.linspace(0.0, float(config["time_max"]), int(config["time_points"]))
    states_pxp = expm_multiply(
        -1j * unperturbed,
        initial,
        start=float(times[0]),
        stop=float(times[-1]),
        num=len(times),
        endpoint=True,
        traceA=0.0,
    )
    states_deformed = expm_multiply(
        -1j * deformed,
        initial,
        start=float(times[0]),
        stop=float(times[-1]),
        num=len(times),
        endpoint=True,
        traceA=0.0,
    )
    fidelity_pxp = np.abs(states_pxp[:, initial_index]) ** 2
    fidelity_deformed = np.abs(states_deformed[:, initial_index]) ** 2
    inset_times = np.linspace(4.0, 6.0, 401)
    inset_infidelities: dict[str, np.ndarray] = {}
    for name, matrix in (("pxp", unperturbed), ("deformed", deformed)):
        inset_states = expm_multiply(
            -1j * matrix,
            initial,
            start=float(inset_times[0]),
            stop=float(inset_times[-1]),
            num=len(inset_times),
            endpoint=True,
            traceA=0.0,
        )
        inset_infidelities[name] = 1.0 - np.clip(
            np.abs(inset_states[:, initial_index]) ** 2, 0.0, 1.0
        )
    partition = Bipartition.from_basis(family.basis, n_sites)
    entropy_pxp = np.asarray([partition.entropy(state) for state in states_pxp])
    entropy_deformed = np.asarray([partition.entropy(state) for state in states_deformed])
    entanglement_spectrum = np.zeros((len(times), int(config["entanglement_levels"])))
    for index, state in enumerate(states_deformed):
        probabilities = partition.schmidt_probabilities(state)
        take = min(len(probabilities), entanglement_spectrum.shape[1])
        entanglement_spectrum[index, :take] = probabilities[:take]
    exact_revival_deformed = expm_multiply(-1j * deformed * tau, initial, traceA=0.0)
    exact_revival_pxp = expm_multiply(-1j * unperturbed * tau, initial, traceA=0.0)
    save_npz(
        "T001_main_figure_1.npz",
        times=times,
        fidelity_pxp=fidelity_pxp,
        fidelity_deformed=fidelity_deformed,
        inset_times=inset_times,
        inset_infidelity=inset_infidelities["deformed"],
        inset_infidelity_pxp=inset_infidelities["pxp"],
        inset_infidelity_deformed=inset_infidelities["deformed"],
        entropy_pxp=entropy_pxp,
        entropy_deformed=entropy_deformed,
        entanglement_spectrum=entanglement_spectrum,
        distances=optimization["distances"],
        optimized_couplings=optimization["optimized"],
        ansatz_couplings=optimization["ansatz"],
        optimized_revival_time=optimization["revival_time"],
        optimized_infidelity=optimization["infidelity"],
        optimization_nfev=optimization["nfev"],
        optimization_success=optimization["success"],
        n_sites=n_sites,
        paper_dynamics_n_sites=32,
        paper_optimization_n_sites=20,
        h0=h0,
        analytic_tau=tau,
    )
    return {
        "n_sites": n_sites,
        "dimension": len(family.basis),
        "hermiticity_error": max(hermiticity_error(unperturbed), hermiticity_error(deformed)),
        "deformed_first_revival_fidelity": float(abs(exact_revival_deformed[initial_index]) ** 2),
        "pxp_at_deformed_period_fidelity": float(abs(exact_revival_pxp[initial_index]) ** 2),
        "optimized_infidelity": optimization["infidelity"],
        "optimization_success": optimization["success"],
        "optimization_message": optimization["message"],
        "optimized_ansatz_correlation": float(
            np.corrcoef(optimization["optimized"], optimization["ansatz"])[0, 1]
        ),
        "maximum_deformed_entropy": float(np.max(entropy_deformed)),
        "maximum_pxp_entropy": float(np.max(entropy_pxp)),
    }


def run_main_figure_2(parameters: dict[str, Any], h0: float) -> dict[str, Any]:
    config = parameters["main_figure_2"]
    sizes = [int(value) for value in config["flow_sizes"]]
    r_k0_even: list[float] = []
    r_pi_odd: list[float] = []
    largest_payload: dict[str, Any] | None = None
    for n_sites in sizes:
        family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
        couplings = ansatz_couplings(h0, n_sites // 2)
        sector_even, transform_even = sector_hamiltonian(
            family, couplings, momentum=0, inversion=1
        )
        energies_even, vectors_even = eigh(sector_even, check_finite=False)
        neel = sector_neel_vector(transform_even, family)
        overlaps = np.abs(neel @ vectors_even) ** 2
        unfolded_even, _, mean_even = level_statistics(energies_even)
        sector_odd, _ = sector_hamiltonian(family, couplings, momentum=1, inversion=-1)
        energies_odd = eigh(sector_odd, eigvals_only=True, check_finite=False)
        unfolded_odd, _, mean_odd = level_statistics(energies_odd)
        r_k0_even.append(mean_even)
        r_pi_odd.append(mean_odd)
        if n_sites == sizes[-1]:
            bins = np.linspace(0.0, 3.5, int(config["histogram_bins"]) + 1)
            density_even, edges = np.histogram(unfolded_even, bins=bins, density=True)
            density_odd, _ = np.histogram(unfolded_odd, bins=bins, density=True)
            density_pooled, _ = np.histogram(
                np.concatenate((unfolded_even, unfolded_odd)), bins=bins, density=True
            )
            largest_payload = {
                "energies": energies_even,
                "overlaps": overlaps,
                "spacing_centers": 0.5 * (edges[:-1] + edges[1:]),
                "spacing_density_k0_even": density_even,
                "spacing_density_kpi_odd": density_odd,
                "spacing_density_pooled": density_pooled,
                "sector_dimension": sector_even.shape[0],
            }
    assert largest_payload is not None
    save_npz(
        "T002_main_figure_2.npz",
        flow_sizes=np.asarray(sizes),
        r_k0_even=np.asarray(r_k0_even),
        r_pi_odd=np.asarray(r_pi_odd),
        energies=largest_payload["energies"],
        overlaps=largest_payload["overlaps"],
        spacing_centers=largest_payload["spacing_centers"],
        spacing_density=largest_payload["spacing_density_pooled"],
        spacing_density_k0_even=largest_payload["spacing_density_k0_even"],
        spacing_density_kpi_odd=largest_payload["spacing_density_kpi_odd"],
        spacing_density_pooled=largest_payload["spacing_density_pooled"],
        goe_density=(math.pi / 2.0)
        * largest_payload["spacing_centers"]
        * np.exp(-math.pi * largest_payload["spacing_centers"] ** 2 / 4.0),
        poisson_density=np.exp(-largest_payload["spacing_centers"]),
        largest_n_sites=sizes[-1],
        paper_n_sites=32,
    )
    largest_overlaps = np.sort(largest_payload["overlaps"])[::-1]
    return {
        "largest_n_sites": sizes[-1],
        "largest_sector_dimension": int(largest_payload["sector_dimension"]),
        "mean_r_k0_even": float(r_k0_even[-1]),
        "mean_r_pi_odd": float(r_pi_odd[-1]),
        "top_overlap": float(largest_overlaps[0]),
        "top_to_median_overlap_ratio": float(
            largest_overlaps[0] / max(np.median(largest_payload["overlaps"]), 1e-300)
        ),
    }


def run_main_figure_3(parameters: dict[str, Any], h0: float) -> dict[str, Any]:
    n_sites = int(parameters["main_figure_3"]["n_sites"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    diagnostics = fsa_diagnostics(family, ansatz_couplings(h0, n_sites // 2))
    save_npz(
        "T003_main_figure_3.npz",
        **diagnostics,
        n_sites=n_sites,
    )
    return {
        "n_sites": n_sites,
        "dimension": len(family.basis),
        "beta_relative_rms": float(diagnostics["beta_relative_rms"]),
        "spacing_relative_std": float(diagnostics["spacing_relative_std"]),
        "spacing_mean": float(diagnostics["spacing_mean"]),
    }


def run_supp_figure_s1(parameters: dict[str, Any], h0: float, predicted_gap: float) -> dict[str, Any]:
    config = parameters["supp_figure_s1"]
    result = low_energy_schmidt_scan(
        int(config["n_sites"]),
        [int(value) for value in config["ranges"]],
        h0,
    )
    save_npz(
        "T004_supp_figure_s1.npz",
        **result,
        n_sites=int(config["n_sites"]),
        paper_n_sites=60,
        predicted_gap=predicted_gap,
    )
    return {
        "n_sites": int(config["n_sites"]),
        "maximum_eigensolver_residual": float(np.max(result["eigensolver_residual"])),
        "last_gap": float(result["gaps"][-1]),
        "predicted_gap": predicted_gap,
        "last_gap_relative_error": float(abs(result["gaps"][-1] - predicted_gap) / predicted_gap),
        "ground_tail_weight_r1": float(np.sum(result["ground_singular"][0, 2:] ** 2)),
        "ground_tail_weight_last": float(np.sum(result["ground_singular"][-1, 2:] ** 2)),
    }


def fsa_cost_bundle(family: HamiltonianFamily, values: np.ndarray) -> dict[str, float]:
    couplings = {distance: float(value) for distance, value in zip(family.distances, values)}
    hamiltonian = family.matrix(couplings)
    vectors, _, plus = fsa_basis(family, couplings)
    minus = plus.transpose().tocsr()
    backwards = minus @ vectors[:, 2]
    projection = float(vectors[:, 1] @ backwards)
    fsa_error = float(np.linalg.norm(backwards - projection * vectors[:, 1]) ** 2)
    projected = vectors.transpose() @ hamiltonian @ vectors
    residual = hamiltonian @ vectors - vectors @ projected
    subspace_variance = float(np.linalg.norm(residual) ** 2)
    ritz = np.linalg.eigvalsh(projected)
    coordinate = np.arange(len(ritz), dtype=np.float64)
    fit = np.polyfit(coordinate, ritz, 1)
    ritz_error = float(np.sqrt(np.mean((ritz - np.polyval(fit, coordinate)) ** 2)))
    return {
        "fsa": fsa_error,
        "trvar": subspace_variance,
        "rvals": ritz_error,
    }


def optimize_supp_figure_s2(parameters: dict[str, Any], h0: float, tau: float) -> dict[str, Any]:
    config = parameters["supp_figure_s2"]
    n_sites = int(config["n_sites"])
    max_range = int(config["max_range"])
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=max_range)
    distances = np.asarray(family.distances)
    ansatz = ansatz_couplings(h0, max_range)
    initial = np.asarray([ansatz[int(distance)] for distance in distances])
    initial_state = np.zeros(len(family.basis), dtype=np.complex128)
    initial_index = family.indices[neel_state(n_sites)]
    initial_state[initial_index] = 1.0

    def penalty(values: np.ndarray) -> float:
        excess = np.maximum(np.abs(values) - 0.2, 0.0)
        return float(1e3 * np.sum(excess * excess))

    def fidelity_objective(values: np.ndarray) -> float:
        physical = values[:-1]
        period = float(values[-1])
        if not 3.5 <= period <= 6.0:
            return 1.0 + abs(period - np.clip(period, 3.5, 6.0))
        couplings = {int(distance): float(value) for distance, value in zip(distances, physical)}
        evolved = expm_multiply(-1j * family.matrix(couplings) * period, initial_state, traceA=0.0)
        return float(1.0 - abs(evolved[initial_index]) ** 2 + penalty(physical))

    variants: dict[str, np.ndarray] = {}
    optimizer_metadata: dict[str, dict[str, Any]] = {}
    result_fidelity = minimize(
        fidelity_objective,
        np.concatenate((initial, [tau])),
        method="Nelder-Mead",
        options={"maxiter": int(config["optimization_maxiter"]), "adaptive": True},
    )
    variants["fid"] = np.asarray(result_fidelity.x[:-1])
    optimizer_metadata["fid"] = {
        "success": bool(result_fidelity.success),
        "nfev": int(result_fidelity.nfev),
    }

    for name in ("fsa", "trvar", "rvals"):
        result = minimize(
            lambda values, cost=name: fsa_cost_bundle(family, values)[cost] + penalty(values),
            initial,
            method="Nelder-Mead",
            options={"maxiter": int(config["optimization_maxiter"]), "adaptive": True},
        )
        variants[name] = np.asarray(result.x)
        optimizer_metadata[name] = {"success": bool(result.success), "nfev": int(result.nfev)}

    names = ("fid", "fsa", "trvar", "rvals")
    coupling_matrix = np.asarray([variants[name] for name in names])
    cost_names = ("fid", "fsa", "trvar", "rvals")
    raw_costs = np.zeros((len(cost_names), len(names)))
    for column, name in enumerate(names):
        values = variants[name]
        bundle = fsa_cost_bundle(family, values)
        coupling_map = {int(distance): float(value) for distance, value in zip(distances, values)}
        evolved = expm_multiply(-1j * family.matrix(coupling_map) * tau, initial_state, traceA=0.0)
        raw_costs[0, column] = 1.0 - abs(evolved[initial_index]) ** 2
        raw_costs[1, column] = bundle["fsa"]
        raw_costs[2, column] = bundle["trvar"]
        raw_costs[3, column] = bundle["rvals"]
    scale = np.maximum(np.max(raw_costs, axis=1, keepdims=True), 1e-16)
    normalized_costs = raw_costs / scale
    save_npz(
        "T005_supp_figure_s2.npz",
        distances=distances,
        variant_names=np.asarray(names),
        cost_names=np.asarray(cost_names),
        coupling_matrix=coupling_matrix,
        ansatz=np.asarray([ansatz[int(distance)] for distance in distances]),
        raw_costs=raw_costs,
        normalized_costs=normalized_costs,
        n_sites=n_sites,
    )
    correlations = [float(np.corrcoef(row, initial)[0, 1]) for row in coupling_matrix]
    return {
        "n_sites": n_sites,
        "optimizer_metadata": optimizer_metadata,
        "minimum_ansatz_correlation": float(np.min(correlations)),
        "self_cost_wins": int(
            sum(int(np.argmin(raw_costs[row])) == row for row in range(len(cost_names)))
        ),
        "raw_costs": raw_costs.tolist(),
    }


def run_supp_figure_s3(parameters: dict[str, Any], h0: float, tau: float) -> dict[str, Any]:
    config = parameters["supp_figure_s3"]
    sizes = [int(value) for value in config["sizes"]]
    m_max = int(config["m_max"])
    revival = np.arange(m_max + 1, dtype=np.float64)
    normalized_infidelity = np.zeros((len(sizes), m_max + 1))
    gamma = np.full((len(sizes), m_max + 1), np.nan)
    turning_points = np.full(len(sizes), np.nan)
    short_grid = np.arange(int(config["short_fit"][0]), int(config["short_fit"][1]) + 1)
    long_grid = np.arange(int(config["long_fit"][0]), int(config["long_fit"][1]) + 1)
    short_coefficients = np.full((len(sizes), 2), np.nan)
    long_coefficients = np.full((len(sizes), 2), np.nan)
    short_curves = np.full((len(sizes), len(short_grid)), np.nan)
    long_curves = np.full((len(sizes), len(long_grid)), np.nan)
    short_log_rms = np.full(len(sizes), np.nan)
    long_log_rms = np.full(len(sizes), np.nan)
    for row, n_sites in enumerate(sizes):
        family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
        matrix = family.matrix(ansatz_couplings(h0, n_sites // 2))
        initial = np.zeros(len(family.basis), dtype=np.complex128)
        index = family.indices[neel_state(n_sites)]
        initial[index] = 1.0
        states = expm_multiply(
            -1j * matrix,
            initial,
            start=0.0,
            stop=float(m_max * tau),
            num=m_max + 1,
            endpoint=True,
            traceA=0.0,
        )
        fidelity = np.clip(np.abs(states[:, index]) ** 2, 0.0, 1.0)
        g_tilde = np.power(np.maximum(fidelity, 1e-300), 1.0 / n_sites)
        normalized_infidelity[row] = 1.0 - g_tilde
        gamma[row, 1:] = (1.0 - g_tilde[1:]) / revival[1:]
        try:
            fits = revival_fit_evidence(
                revival,
                gamma[row],
                config["short_fit"],
                config["long_fit"],
            )
        except ValueError:
            continue
        short_coefficients[row] = fits["short"]["coefficients"]
        long_coefficients[row] = fits["long"]["coefficients"]
        short_curves[row] = fits["short"]["curve"]
        long_curves[row] = fits["long"]["curve"]
        short_log_rms[row] = fits["short"]["log_rms_residual"]
        long_log_rms[row] = fits["long"]["log_rms_residual"]
        turning_points[row] = fits["turning_point"]
    scaling = turning_point_power_law(np.asarray(sizes), turning_points)
    save_npz(
        "T006_supp_figure_s3.npz",
        sizes=np.asarray(sizes),
        revival=revival,
        normalized_infidelity=normalized_infidelity,
        gamma=gamma,
        turning_points=turning_points,
        short_fit_grid=short_grid,
        long_fit_grid=long_grid,
        short_fit_coefficients=short_coefficients,
        long_fit_coefficients=long_coefficients,
        short_fit_curves=short_curves,
        long_fit_curves=long_curves,
        short_fit_log_rms=short_log_rms,
        long_fit_log_rms=long_log_rms,
        turning_point_power_law_coefficients=scaling["coefficients"],
        turning_point_power_law_curve=scaling["curve"],
        turning_point_power_law_log_rms=scaling["log_rms_residual"],
        analytic_tau=tau,
        paper_sizes=np.asarray([22, 24, 26, 28, 30, 32]),
        paper_m_max=1000,
    )
    early = slice(5, min(21, m_max + 1))
    relative_spread = np.nanmedian(
        np.nanstd(gamma[:, early], axis=0) / np.maximum(np.nanmean(gamma[:, early], axis=0), 1e-30)
    )
    return {
        "sizes": sizes,
        "m_max": m_max,
        "early_gamma_relative_spread": float(relative_spread),
        "turning_points": turning_points.tolist(),
        "finite_turning_points": int(np.isfinite(turning_points).sum()),
        "turning_point_power_law_exponent": float(scaling["coefficients"][0]),
    }


def eigenstate_cloud(n_sites: int, couplings: dict[int, float]) -> dict[str, np.ndarray | float]:
    family = HamiltonianFamily.build(n_sites, periodic=True, max_range=n_sites // 2)
    sector, transform = sector_hamiltonian(family, couplings, momentum=0, inversion=1)
    energies, eigenvectors = eigh(sector, check_finite=False)
    neel = sector_neel_vector(transform, family)
    overlaps = np.abs(neel @ eigenvectors) ** 2
    full_vectors = transform @ eigenvectors
    partition = Bipartition.from_basis(family.basis, n_sites)
    entropies = np.asarray([partition.entropy(full_vectors[:, index]) for index in range(len(energies))])
    return {
        "energies": energies,
        "overlaps": overlaps,
        "entropies": entropies,
        "sector_dimension": float(len(energies)),
    }


def run_supp_figure_s4(parameters: dict[str, Any], h0: float) -> dict[str, Any]:
    n_sites = int(parameters["supp_figure_s4"]["n_sites"])
    variants = {
        "pxp": {},
        "h2_0p02": {2: 0.02},
        "ansatz": ansatz_couplings(h0, n_sites // 2),
    }
    clouds = {name: eigenstate_cloud(n_sites, coupling) for name, coupling in variants.items()}
    save_npz(
        "T007_supp_figure_s4.npz",
        n_sites=n_sites,
        paper_n_sites=30,
        energies_pxp=clouds["pxp"]["energies"],
        overlaps_pxp=clouds["pxp"]["overlaps"],
        entropies_pxp=clouds["pxp"]["entropies"],
        energies_h2=clouds["h2_0p02"]["energies"],
        overlaps_h2=clouds["h2_0p02"]["overlaps"],
        entropies_h2=clouds["h2_0p02"]["entropies"],
        energies_ansatz=clouds["ansatz"]["energies"],
        overlaps_ansatz=clouds["ansatz"]["overlaps"],
        entropies_ansatz=clouds["ansatz"]["entropies"],
    )
    pxp_sorted = np.sort(clouds["pxp"]["overlaps"])[::-1]
    ansatz_sorted = np.sort(clouds["ansatz"]["overlaps"])[::-1]
    count = min(n_sites // 2 + 1, len(ansatz_sorted))
    ansatz_scar_indices = np.argsort(clouds["ansatz"]["overlaps"])[-count:]
    ansatz_bulk_indices = np.argsort(clouds["ansatz"]["overlaps"])[: max(count, 1)]
    return {
        "n_sites": n_sites,
        "sector_dimension": int(clouds["ansatz"]["sector_dimension"]),
        "top_overlap_pxp": float(pxp_sorted[0]),
        "top_overlap_ansatz": float(ansatz_sorted[0]),
        "overlap_isolation_gain": float(
            (ansatz_sorted[0] / max(np.median(clouds["ansatz"]["overlaps"]), 1e-300))
            / (pxp_sorted[0] / max(np.median(clouds["pxp"]["overlaps"]), 1e-300))
        ),
        "scar_entropy_mean": float(np.mean(clouds["ansatz"]["entropies"][ansatz_scar_indices])),
        "bulk_entropy_mean": float(np.mean(clouds["ansatz"]["entropies"][ansatz_bulk_indices])),
    }


def run_supp_figure_s5(parameters: dict[str, Any], h0: float) -> dict[str, Any]:
    sizes = [int(value) for value in parameters["supp_figure_s5"]["sizes"]]
    entropy_first: list[float] = []
    entropy_second: list[float] = []
    energies_first: list[float] = []
    energies_second: list[float] = []
    for n_sites in sizes:
        cloud = eigenstate_cloud(n_sites, ansatz_couplings(h0, n_sites // 2))
        candidate_count = min(n_sites // 2 + 1, len(cloud["energies"]))
        candidates = np.argsort(cloud["overlaps"])[-candidate_count:]
        central = candidates[np.argsort(np.abs(cloud["energies"][candidates]))[:2]]
        central = central[np.argsort(cloud["energies"][central])]
        entropy_first.append(float(cloud["entropies"][central[0]]))
        entropy_second.append(float(cloud["entropies"][central[1]]))
        energies_first.append(float(cloud["energies"][central[0]]))
        energies_second.append(float(cloud["energies"][central[1]]))
    size_array = np.asarray(sizes, dtype=np.float64)
    log_n = np.log(size_array)
    fit_first = np.polyfit(log_n, entropy_first, 1)
    fits_second = entropy_fit_evidence(size_array, np.asarray(entropy_second))
    save_npz(
        "T008_supp_figure_s5.npz",
        sizes=np.asarray(sizes),
        entropy_first=np.asarray(entropy_first),
        entropy_second=np.asarray(entropy_second),
        energy_first=np.asarray(energies_first),
        energy_second=np.asarray(energies_second),
        log_fit_first=fit_first,
        log_fit_second=fits_second["log_coefficients"],
        log_fit_second_curve=fits_second["log_curve"],
        linear_fit_second=fits_second["linear_coefficients"],
        linear_fit_second_curve=fits_second["linear_curve"],
    )
    return {
        "sizes": sizes,
        "first_log_slope": float(fit_first[0]),
        "second_log_slope": float(fits_second["log_coefficients"][0]),
        "second_linear_slope": float(fits_second["linear_coefficients"][0]),
        "first_monotonic_fraction": float(np.mean(np.diff(entropy_first) >= -1e-8)),
        "second_monotonic_fraction": float(np.mean(np.diff(entropy_second) >= -1e-8)),
    }


def run_supp_figure_s6(parameters: dict[str, Any]) -> dict[str, Any]:
    config = parameters["supp_figure_s6"]
    n_sites = int(config["n_sites"])
    seed = int(config["seed"])
    result = toy_diagnostics(n_sites, seed, omega=float(config["omega"]))
    save_npz(
        "T009_supp_figure_s6.npz",
        **result,
        n_sites=n_sites,
        paper_n_sites=14,
        seed=seed,
    )
    integer_indices = [int(np.argmin(np.abs(result["times"] - value))) for value in range(5)]
    special_count = int(np.sum(result["overlaps"] > 1e-8))
    special = result["overlaps"] > 1e-8
    bulk = ~special
    return {
        "n_sites": n_sites,
        "dimension": 1 << n_sites,
        "seed": seed,
        "hermiticity_error": float(result["hermiticity_error"]),
        "minimum_integer_time_fidelity": float(np.min(result["fidelity"][integer_indices])),
        "nonzero_overlap_states": special_count,
        "expected_special_states": n_sites + 1,
        "special_entropy_mean": float(np.mean(result["entropy"][special])),
        "bulk_entropy_mean": float(np.mean(result["entropy"][bulk])),
    }


def assertion(
    assertion_id: str,
    claim: str,
    passed: bool,
    observed: Any,
    criterion: str,
    *,
    tier: str = "numeric",
) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "claim": claim,
        "status": "passed" if passed else "failed",
        "observed": observed,
        "criterion": criterion,
        "tier": tier,
        "essential": True,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    parameters = read_config()
    timings: dict[str, float] = {}
    h0 = solve_h0()
    delta, tau = harmonic_gap_and_period(h0)
    predicted_gap = 2.0 * math.pi / tau

    lemma_config = parameters["analytic_claims"]["perfect_revival_overlap_bound"]
    lemma_witnesses = [
        perfect_revival_overlap_bound(
            int(n_sites),
            float(lemma_config["local_norm_bound"]),
            float(lemma_config["tau"]),
        )
        for n_sites in lemma_config["sample_sizes"]
    ]

    results = {
        "T001": timed("T001_main_figure_1", lambda: run_main_figure_1(parameters, h0, tau), timings),
        "T002": timed("T002_main_figure_2", lambda: run_main_figure_2(parameters, h0), timings),
        "T003": timed("T003_main_figure_3", lambda: run_main_figure_3(parameters, h0), timings),
        "T004": timed(
            "T004_supp_figure_s1",
            lambda: run_supp_figure_s1(parameters, h0, predicted_gap),
            timings,
        ),
        "T005": timed(
            "T005_supp_figure_s2",
            lambda: optimize_supp_figure_s2(parameters, h0, tau),
            timings,
        ),
        "T006": timed(
            "T006_supp_figure_s3",
            lambda: run_supp_figure_s3(parameters, h0, tau),
            timings,
        ),
        "T007": timed(
            "T007_supp_figure_s4",
            lambda: run_supp_figure_s4(parameters, h0),
            timings,
        ),
        "T008": timed(
            "T008_supp_figure_s5",
            lambda: run_supp_figure_s5(parameters, h0),
            timings,
        ),
        "T009": timed(
            "T009_supp_figure_s6",
            lambda: run_supp_figure_s6(parameters),
            timings,
        ),
    }

    with np.load(DATA_DIR / "T001_main_figure_1.npz", allow_pickle=False) as payload:
        t001_data = {key: np.asarray(payload[key]) for key in payload.files}
    with np.load(DATA_DIR / "T002_main_figure_2.npz", allow_pickle=False) as payload:
        t002_data = {key: np.asarray(payload[key]) for key in payload.files}
    with np.load(DATA_DIR / "T006_supp_figure_s3.npz", allow_pickle=False) as payload:
        t006_data = {key: np.asarray(payload[key]) for key in payload.files}
    with np.load(DATA_DIR / "T008_supp_figure_s5.npz", allow_pickle=False) as payload:
        t008_data = {key: np.asarray(payload[key]) for key in payload.files}

    lemma_count_linear = all(
        row["max_distinct_energies"] <= 1.0 + row["spectral_width_bound"] / row["revival_energy_spacing"]
        for row in lemma_witnesses
    )
    lemma_phase_aligned = all(row["phase_alignment_error"] < 1e-12 for row in lemma_witnesses)
    lemma_pigeonhole = all(
        row["uniform_witness_max_probability"] + 1e-15
        >= row["overlap_probability_lower_bound"]
        and row["probability_normalization_error"] < 1e-14
        for row in lemma_witnesses
    )

    spacing_width = float(t002_data["spacing_centers"][1] - t002_data["spacing_centers"][0])
    sector_integrals = [
        float(np.sum(t002_data[key]) * spacing_width)
        for key in ("spacing_density_k0_even", "spacing_density_kpi_odd")
    ]
    short_reconstruction_error = float(
        np.max(
            np.abs(
                t006_data["short_fit_curves"]
                - np.exp(t006_data["short_fit_coefficients"][:, 1, None])
                * np.power(
                    t006_data["short_fit_grid"][None, :],
                    t006_data["short_fit_coefficients"][:, 0, None],
                )
            )
        )
    )
    long_reconstruction_error = float(
        np.max(
            np.abs(
                t006_data["long_fit_curves"]
                - np.exp(t006_data["long_fit_coefficients"][:, 1, None])
                * np.power(
                    t006_data["long_fit_grid"][None, :],
                    t006_data["long_fit_coefficients"][:, 0, None],
                )
            )
        )
    )
    scaling_coefficients = t006_data["turning_point_power_law_coefficients"]
    scaling_reconstruction_error = float(
        np.max(
            np.abs(
                t006_data["turning_point_power_law_curve"]
                - np.exp(scaling_coefficients[1])
                * np.power(t006_data["sizes"], scaling_coefficients[0])
            )
        )
    )
    linear_coefficients = t008_data["linear_fit_second"]
    linear_reconstruction_error = float(
        np.max(
            np.abs(
                t008_data["linear_fit_second_curve"]
                - np.polyval(linear_coefficients, t008_data["sizes"])
            )
        )
    )

    checks = {
        "schema_version": 1,
        "paper_id": "1812.05561",
        "formula_sanity": {
            "derived_h0": h0,
            "paper_h0": 0.0506656,
            "constraint_residual": su2_constraint(h0),
            "derived_delta": delta,
            "paper_delta": 0.835845,
            "derived_tau": tau,
            "paper_tau": 4.85962,
        },
        "targets": {
            "T001": {
                "metrics": results["T001"],
                "assertions": [
                    assertion("T001-H", "The constructed PXP Hamiltonians are Hermitian.", results["T001"]["hermiticity_error"] < 1e-12, results["T001"]["hermiticity_error"], "max |H-H^T| < 1e-12"),
                    assertion("T001-R", "The ansatz deformation gives a near-unity first revival at reduced N.", results["T001"]["deformed_first_revival_fidelity"] > 0.995, results["T001"]["deformed_first_revival_fidelity"], "fidelity > 0.995"),
                    assertion("T001-O", "Independent optimization follows the analytic distance dependence.", results["T001"]["optimized_ansatz_correlation"] > 0.9, results["T001"]["optimized_ansatz_correlation"], "Pearson correlation > 0.9"),
                ],
            },
            "T002": {
                "metrics": results["T002"],
                "assertions": [
                    assertion("T002-L", "Symmetry-resolved spacings are closer to GOE than Poisson at the largest reduced size.", abs(results["T002"]["mean_r_k0_even"] - 0.5307) < abs(results["T002"]["mean_r_k0_even"] - 0.3863), results["T002"]["mean_r_k0_even"], "distance to 0.5307 is smaller than distance to 0.3863"),
                    assertion("T002-S", "A small scar band dominates the Neel-state spectral weight.", results["T002"]["top_to_median_overlap_ratio"] > 1e3, results["T002"]["top_to_median_overlap_ratio"], "top/median overlap > 1e3"),
                ],
            },
            "T003": {
                "metrics": results["T003"],
                "assertions": [
                    assertion("T003-B", "FSA raising elements follow the spin-N/2 SU(2) square-root law.", results["T003"]["beta_relative_rms"] < 0.03, results["T003"]["beta_relative_rms"], "relative RMS < 3%"),
                    assertion("T003-Z", "FSA states have nearly harmonic H^z expectation spacing.", results["T003"]["spacing_relative_std"] < 0.03, results["T003"]["spacing_relative_std"], "relative spacing std < 3%"),
                ],
            },
            "T004": {
                "metrics": results["T004"],
                "assertions": [
                    assertion("T004-E", "Sparse low-energy eigenpairs satisfy the eigen-equation.", results["T004"]["maximum_eigensolver_residual"] < 1e-8, results["T004"]["maximum_eigensolver_residual"], "residual < 1e-8"),
                    assertion("T004-G", "The low-energy gap approaches the emergent-SU(2) prediction.", results["T004"]["last_gap_relative_error"] < 0.12, results["T004"]["last_gap_relative_error"], "relative error < 12% at reduced N"),
                ],
            },
            "T005": {
                "metrics": results["T005"],
                "assertions": [
                    assertion("T005-C", "Independent cost-function optima retain the ansatz's decaying coupling pattern.", results["T005"]["minimum_ansatz_correlation"] > 0.65, results["T005"]["minimum_ansatz_correlation"], "all correlations > 0.65"),
                ],
            },
            "T006": {
                "metrics": results["T006"],
                "assertions": [
                    assertion("T006-C", "Early-time per-site decay rates approximately collapse across reduced sizes.", results["T006"]["early_gamma_relative_spread"] < 0.5, results["T006"]["early_gamma_relative_spread"], "median relative spread < 0.5"),
                ],
            },
            "T007": {
                "metrics": results["T007"],
                "assertions": [
                    assertion("T007-I", "The ansatz isolates the dominant scar overlap more strongly than bare PXP.", results["T007"]["overlap_isolation_gain"] > 1.0, results["T007"]["overlap_isolation_gain"], "isolation gain > 1"),
                    assertion("T007-E", "High-overlap scar states are less entangled than low-overlap bulk states.", results["T007"]["scar_entropy_mean"] < results["T007"]["bulk_entropy_mean"], [results["T007"]["scar_entropy_mean"], results["T007"]["bulk_entropy_mean"]], "scar mean < bulk mean"),
                ],
            },
            "T008": {
                "metrics": results["T008"],
                "assertions": [
                    assertion("T008-L", "Central scar entropies remain compatible with logarithmic growth on the reduced size window.", results["T008"]["first_log_slope"] > -0.1 and results["T008"]["second_log_slope"] > -0.1, [results["T008"]["first_log_slope"], results["T008"]["second_log_slope"]], "both log-fit slopes > -0.1"),
                ],
            },
            "T009": {
                "metrics": results["T009"],
                "assertions": [
                    assertion("T009-H", "The independently sampled toy Hamiltonian is Hermitian.", results["T009"]["hermiticity_error"] < 1e-12, results["T009"]["hermiticity_error"], "max |H-H^dagger| < 1e-12"),
                    assertion("T009-R", "The polarized toy-model state revives perfectly at integer periods.", results["T009"]["minimum_integer_time_fidelity"] > 1.0 - 1e-10, results["T009"]["minimum_integer_time_fidelity"], "minimum > 1-1e-10"),
                    assertion("T009-N", "Exactly N+1 eigenstates carry polarized-state weight.", results["T009"]["nonzero_overlap_states"] == results["T009"]["expected_special_states"], results["T009"]["nonzero_overlap_states"], f"equals {results['T009']['expected_special_states']}"),
                ],
            },
            "T010": {
                "metrics": {"witnesses": lemma_witnesses},
                "assertions": [
                    assertion("T010-C", "The number of revival-compatible distinct energies is O(N).", lemma_count_linear, [row["max_distinct_energies"] for row in lemma_witnesses], "count <= floor(2*N*h/(2*pi/tau))+1", tier="analytic"),
                    assertion("T010-P", "Every occupied energy in the constructed witness has the same revival phase.", lemma_phase_aligned, max(row["phase_alignment_error"] for row in lemma_witnesses), "maximum phase error < 1e-12", tier="analytic"),
                    assertion("T010-O", "Normalization forces one squared overlap to be at least the reciprocal count.", lemma_pigeonhole, [row["overlap_probability_lower_bound"] for row in lemma_witnesses], "max probability >= 1/K and probabilities sum to one", tier="analytic"),
                ],
            },
            "T011": {
                "metrics": {
                    "branch_points": int(len(t001_data["inset_times"])),
                    "maximum_branch_difference": float(np.max(np.abs(t001_data["inset_infidelity_pxp"] - t001_data["inset_infidelity_deformed"]))),
                },
                "assertions": [
                    assertion("T011-B", "Both H0 and optimized inset branches are frozen independently.", bool(t001_data["inset_infidelity_pxp"].shape == t001_data["inset_times"].shape == t001_data["inset_infidelity_deformed"].shape and np.all(np.isfinite(t001_data["inset_infidelity_pxp"])) and np.all(np.isfinite(t001_data["inset_infidelity_deformed"]))), [t001_data["inset_infidelity_pxp"].shape, t001_data["inset_infidelity_deformed"].shape], "both finite branches match the inset grid"),
                    assertion("T011-I", "Each branch is a valid infidelity in [0,1].", bool(np.all((t001_data["inset_infidelity_pxp"] >= 0) & (t001_data["inset_infidelity_pxp"] <= 1)) and np.all((t001_data["inset_infidelity_deformed"] >= 0) & (t001_data["inset_infidelity_deformed"] <= 1))), [float(np.min(t001_data["inset_infidelity_pxp"])), float(np.max(t001_data["inset_infidelity_pxp"])), float(np.min(t001_data["inset_infidelity_deformed"])), float(np.max(t001_data["inset_infidelity_deformed"]))], "all values lie in [0,1]"),
                ],
            },
            "T012": {
                "metrics": {"sector_integrals": sector_integrals},
                "assertions": [
                    assertion("T012-S", "The two printed symmetry sectors retain distinct histogram arrays.", bool(t002_data["spacing_density_k0_even"].shape == t002_data["spacing_centers"].shape == t002_data["spacing_density_kpi_odd"].shape), [t002_data["spacing_density_k0_even"].shape, t002_data["spacing_density_kpi_odd"].shape], "both sector arrays match the declared bin centers"),
                    assertion("T012-N", "Each sector-resolved spacing density is normalized on the declared histogram range.", bool(np.allclose(sector_integrals, 1.0, atol=1e-10)), sector_integrals, "sum(P(s)*delta_s)=1 in each sector"),
                ],
            },
            "T013": {
                "metrics": {"maximum_short_curve_reconstruction_error": short_reconstruction_error},
                "assertions": [assertion("T013-F", "Every executed-size short-window fit is frozen with its coefficients, grid and curve.", bool(t006_data["short_fit_curves"].shape[0] == len(t006_data["sizes"]) and np.all(np.isfinite(t006_data["short_fit_coefficients"])) and short_reconstruction_error < 1e-14), short_reconstruction_error, "all branches finite and curve reconstruction error < 1e-14")],
            },
            "T014": {
                "metrics": {"maximum_long_curve_reconstruction_error": long_reconstruction_error},
                "assertions": [assertion("T014-F", "Every executed-size long-window fit is frozen with its coefficients, grid and curve.", bool(t006_data["long_fit_curves"].shape[0] == len(t006_data["sizes"]) and np.all(np.isfinite(t006_data["long_fit_coefficients"])) and long_reconstruction_error < 1e-14), long_reconstruction_error, "all branches finite and curve reconstruction error < 1e-14")],
            },
            "T015": {
                "metrics": {"power_law_exponent": float(scaling_coefficients[0]), "maximum_curve_reconstruction_error": scaling_reconstruction_error},
                "assertions": [assertion("T015-F", "The turning-point power-law guide is produced and frozen by the scientific runner.", bool(np.all(np.isfinite(scaling_coefficients)) and scaling_reconstruction_error < 1e-14), [scaling_coefficients.tolist(), scaling_reconstruction_error], "finite coefficients and reconstruction error < 1e-14")],
            },
            "T016": {
                "metrics": {"linear_slope": float(linear_coefficients[0]), "maximum_curve_reconstruction_error": linear_reconstruction_error},
                "assertions": [assertion("T016-F", "The linear guide is fit to and frozen for the second scar-entropy series.", bool(np.all(np.isfinite(linear_coefficients)) and linear_reconstruction_error < 1e-14), [linear_coefficients.tolist(), linear_reconstruction_error], "finite second-series linear coefficients and reconstruction error < 1e-14")],
            },
        },
    }
    all_assertions = [
        item
        for target in checks["targets"].values()
        for item in target["assertions"]
    ]
    checks["summary"] = {
        "passed": sum(item["status"] == "passed" for item in all_assertions),
        "failed": sum(item["status"] == "failed" for item in all_assertions),
        "status": "passed" if all(item["status"] == "passed" for item in all_assertions) else "partial",
    }
    checks["status"] = checks["summary"]["status"]
    write_json(CHECK_DIR / "target_checks.json", checks)
    closure_files = {
        "T010": "T010_perfect_revival_lemma.json",
        "T011": "T011_inset_branches.json",
        "T012": "T012_sector_spacing.json",
        "T013": "T013_short_fit_checks.json",
        "T014": "T014_long_fit_checks.json",
        "T015": "T015_power_law_fit.json",
        "T016": "T016_fit_identity.json",
    }
    for target_id, filename in closure_files.items():
        target = checks["targets"][target_id]
        write_json(
            CHECK_DIR / filename,
            {
                "schema_version": 1,
                "paper_id": "1812.05561",
                "target_id": target_id,
                "status": "passed" if all(row["status"] == "passed" for row in target["assertions"]) else "failed",
                "metrics": target["metrics"],
                "assertions": target["assertions"],
                "scientific_input_boundary": {
                    "source_pixels_used": False,
                    "author_code_used": False,
                    "author_numeric_arrays_used": False,
                },
            },
        )
    write_json(
        CHECK_DIR / "runtime_profile.json",
        {
            "schema_version": 1,
            "paper_id": "1812.05561",
            "status": "passed",
            "timings_seconds": timings,
            "total_seconds": round(sum(timings.values()), 6),
            "scope": "local reduced-scale exact diagonalization and sparse time evolution",
        },
    )

    data_files = sorted(DATA_DIR.glob("*.npz"))
    freeze = {
        "schema_version": 1,
        "paper_id": "1812.05561",
        "status": "passed",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "freeze_boundary": "before any generated rendering or source-figure comparison",
        "reference_assets_available_to_numeric_runner": False,
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
                "provenance": "independent_numerics",
            }
            for path in data_files
        ],
    }
    write_json(CHECK_DIR / "data_freeze_manifest.json", freeze)
    write_json(
        CHECK_DIR / "generated_data_manifest.json",
        {
            "schema_version": 1,
            "paper_id": "1812.05561",
            "status": "passed",
            "generator": "scripts/run_reproduction.py",
            "parameter_file": "config/reduced_scale.json",
            "source_or_reference_arrays_used": False,
            "files": freeze["files"],
        },
    )
    print(json.dumps(checks["summary"], sort_keys=True), flush=True)
    return 0


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/reduced_scale.json")
    parser.add_argument("--targets", default=",".join(f"T{index:03d}" for index in range(1, 10)))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args(argv)
    config_path = Path(arguments.config)
    with config_path.open("r", encoding="utf-8") as handle:
        profile = json.load(handle).get("profile", "reduced_scale")
    if profile == "paper_scale":
        from src.paper_scale import run_campaign

        targets = tuple(value.strip() for value in arguments.targets.split(",") if value.strip())
        return run_campaign(
            ROOT,
            config_path,
            targets=targets,
            resume=arguments.resume,
            shard_index=arguments.shard_index,
            shard_count=arguments.shard_count,
            smoke=arguments.smoke,
            validate_only=arguments.validate_only,
        )
    if any(
        (
            arguments.resume,
            arguments.shard_index is not None,
            arguments.shard_count is not None,
            arguments.smoke,
            arguments.validate_only,
        )
    ):
        parser.error("checkpoint/shard/smoke flags are available only for paper_scale configs")
    if config_path.as_posix() != "config/reduced_scale.json":
        parser.error("the legacy reduced runner accepts only config/reduced_scale.json")
    return main()


if __name__ == "__main__":
    raise SystemExit(cli_main())
