"""End-to-end Wannier Hamiltonian to NiO paper-observable channel.

The module owns the scientific part of the production path.  Quantum
ESPRESSO/Wannier90 and the public TRIQS impurity solver are replaceable
infrastructure; the multi-site fixed point, continuation, layer projection,
and evidence outputs stay explicit and versioned here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .cthyb import SolverUnavailable, solve_impurity_triqs
from .maxent import maximum_entropy_continue
from .observables import imaginary_time_symmetry_error, rational_continue
from .qe import ExternalInputError, hamiltonian_from_hr, parse_wannier_hr
from .self_consistency import (
    MultiSiteDMFTResult,
    embed_group_self_energy,
    positive_matsubara,
    retarded_lattice_observables,
    run_multisite_dmft,
    spatial_to_spinful_green,
    spinful_to_spatial_self_energy,
    uniform_fractional_kmesh,
)


@dataclass(frozen=True)
class WannierDMFTExecution:
    translations: np.ndarray
    degeneracies: np.ndarray
    hopping_matrices: np.ndarray
    kpoints: np.ndarray
    hamiltonian_k: np.ndarray
    groups: tuple[tuple[tuple[int, ...], ...], ...]
    result: MultiSiteDMFTResult


def _groups_from_contract(
    contract: dict[str, Any],
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    try:
        groups = tuple(
            tuple(tuple(int(index) for index in block) for block in group)
            for group in contract["correlated_groups"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ExternalInputError("invalid correlated-group contract") from exc
    return groups


def _save_npz_atomic(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def solve_wannier_dmft(
    wannier_hr: Path,
    contract: dict[str, Any],
    output_root: Path,
    *,
    checkpoint_name: str,
    resume: bool = True,
) -> WannierDMFTExecution:
    """Run the material-specific inner DMFT fixed point and freeze its arrays."""

    translations, degeneracies, hoppings = parse_wannier_hr(wannier_hr)
    kmesh = tuple(int(value) for value in contract["kmesh"])
    kpoints = uniform_fractional_kmesh(kmesh)
    hamiltonian_k = hamiltonian_from_hr(
        translations,
        degeneracies,
        hoppings,
        kpoints,
    )
    expected_n_wann = int(contract["wannier"]["n_wann"])
    if hamiltonian_k.shape[-1] != expected_n_wann:
        raise ExternalInputError(
            "Wannier Hamiltonian size differs from the frozen projection contract"
        )
    groups = _groups_from_contract(contract)
    convergence = contract["dmft_convergence"]
    try:
        result = run_multisite_dmft(
            hamiltonian_k,
            groups,
            contract["cthyb"],
            solve_impurity_triqs,
            chemical_potential=float(contract["chemical_potential_ev"]),
            initial_d_occupancy=float(contract["initial_d_occupancy"]),
            mixing=float(convergence["mixing"]),
            tolerance=float(convergence["self_energy_max_tolerance_ev"]),
            max_iterations=int(convergence["maximum_iterations"]),
            checkpoint_path=output_root / "checkpoints" / checkpoint_name,
            resume=resume,
        )
    except SolverUnavailable as exc:
        raise ExternalInputError(str(exc)) from exc

    _save_npz_atomic(
        output_root / "lattice_hamiltonian.npz",
        translations=translations,
        degeneracies=degeneracies,
        hopping_matrices=hoppings,
        fractional_kpoints=kpoints,
        hamiltonian_k=hamiltonian_k,
    )
    _save_npz_atomic(
        output_root / "self_energy.npz",
        self_energy_positive_iw=result.self_energy_positive_iw,
        local_green_positive_iw=result.local_green_positive_iw,
        density_matrices=result.density_matrices,
        spin_correlation_tau=result.spin_correlation_tau,
        average_signs=result.average_signs,
        residual_history=result.residual_history,
        double_counting_ev=result.double_counting_ev,
        converged=np.asarray(result.converged),
        iterations=np.asarray(result.iterations),
    )
    _save_density_feedback(
        output_root, hamiltonian_k.shape[-1], groups, result, contract
    )
    return WannierDMFTExecution(
        translations=translations,
        degeneracies=degeneracies,
        hopping_matrices=hoppings,
        kpoints=kpoints,
        hamiltonian_k=hamiltonian_k,
        groups=groups,
        result=result,
    )


def _save_density_feedback(
    output_root: Path,
    n_orbitals: int,
    groups: tuple[tuple[tuple[int, ...], ...], ...],
    result: MultiSiteDMFTResult,
    contract: dict[str, Any],
) -> None:
    density = np.zeros((n_orbitals, n_orbitals), dtype=float)
    baseline = np.zeros_like(density)
    reference_per_d_orbital = float(contract["initial_d_occupancy"]) / 5.0
    for group_index, group in enumerate(groups):
        spinful = result.density_matrices[group_index]
        spatial = spinful[0::2, 0::2] + spinful[1::2, 1::2]
        for block in group:
            indices = np.asarray(block, dtype=int)
            density[indices[:, None], indices[None, :]] = spatial
            baseline[indices, indices] = reference_per_d_orbital
    correction = density - baseline
    _save_npz_atomic(
        output_root / "density_feedback.npz",
        correlated_density_matrix=density,
        reference_density_matrix=baseline,
        density_correction=correction,
    )


def _fractional_k_path(contract: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    path = contract["continuation"]["k_path"]
    vertices = np.asarray(path["vertices"], dtype=float)
    points_per_segment = int(path["points_per_segment"])
    if vertices.ndim != 2 or vertices.shape[1] != 3 or vertices.shape[0] < 2:
        raise ExternalInputError("k-path vertices must have shape (n,3)")
    if points_per_segment < 2:
        raise ExternalInputError("k-path requires at least two points per segment")
    pieces = []
    distance = []
    offset = 0.0
    for index, (start, stop) in enumerate(zip(vertices[:-1], vertices[1:])):
        parameter = np.linspace(0.0, 1.0, points_per_segment)
        segment = start[None, :] + parameter[:, None] * (stop - start)[None, :]
        distance_index = np.arange(points_per_segment)
        if index:
            segment = segment[1:]
            distance_index = distance_index[1:]
        step = float(np.linalg.norm(stop - start)) / (points_per_segment - 1)
        segment_distance = offset + step * distance_index
        pieces.append(segment)
        distance.append(segment_distance)
        offset = float(segment_distance[-1]) if segment_distance.size else offset
    return np.concatenate(pieces), np.concatenate(distance)


def _continue_self_energy(
    execution: WannierDMFTExecution,
    contract: dict[str, Any],
    omega: np.ndarray,
) -> np.ndarray:
    continuation = contract["continuation"]
    n_input = min(
        int(continuation["pade_input_points"]),
        execution.result.self_energy_positive_iw.shape[0],
    )
    beta = float(contract["cthyb"]["beta_ev_inverse"])
    z_input = 1j * positive_matsubara(beta, n_input)
    z_output = omega + 1j * float(continuation["pade_broadening_ev"])
    spatial = spinful_to_spatial_self_energy(
        execution.result.self_energy_positive_iw[:n_input]
    )
    sigma_w = np.empty(
        (omega.size, spatial.shape[1], spatial.shape[2], spatial.shape[3]),
        dtype=np.complex128,
    )
    for group_index in range(spatial.shape[1]):
        for row in range(spatial.shape[2]):
            for column in range(spatial.shape[3]):
                sigma_w[:, group_index, row, column] = rational_continue(
                    z_input,
                    spatial[:, group_index, row, column],
                    z_output,
                    numerator_degree=int(continuation["pade_numerator_degree"]),
                    denominator_degree=int(continuation["pade_denominator_degree"]),
                    regularization=float(continuation["pade_regularization"]),
                )
    return sigma_w


def _maximum_entropy_group_spectra(
    execution: WannierDMFTExecution,
    contract: dict[str, Any],
    omega: np.ndarray,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    continuation = contract["continuation"]
    n_input = min(
        int(continuation["maxent_input_points"]),
        execution.result.local_green_positive_iw.shape[0],
    )
    z_input = 1j * positive_matsubara(
        float(contract["cthyb"]["beta_ev_inverse"]), n_input
    )
    local = execution.result.local_green_positive_iw[:n_input]
    spectra = np.empty((omega.size, local.shape[1], local.shape[2]), dtype=float)
    records: list[dict[str, Any]] = []
    for group_index in range(local.shape[1]):
        for orbital_index in range(local.shape[2]):
            result = maximum_entropy_continue(
                z_input,
                local[:, group_index, orbital_index, orbital_index],
                omega,
                error=float(continuation["assumed_green_error"]),
                alpha_grid=np.asarray(continuation["maxent_alpha_grid"], dtype=float),
                max_iterations=int(continuation["maxent_max_iterations"]),
            )
            spectra[:, group_index, orbital_index] = result.spectrum
            records.append(
                {
                    "group_index": group_index,
                    "orbital_index": orbital_index,
                    "selected_alpha": result.selected_alpha,
                    "chi_squared": result.chi_squared,
                    "normalization": result.normalization,
                    "candidates": list(result.candidates),
                }
            )
    return spectra, records


def build_paper_observables(
    execution: WannierDMFTExecution,
    contract: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    """Continue the frozen DMFT solution and build every target array family."""

    continuation = contract["continuation"]
    omega = np.linspace(
        float(continuation["omega_min_ev"]),
        float(continuation["omega_max_ev"]),
        int(continuation["omega_points"]),
    )
    sigma_group_w = _continue_self_energy(execution, contract, omega)
    spinful_group_w = spatial_to_spinful_green(sigma_group_w)
    embedded_sigma_w = embed_group_self_energy(
        execution.hamiltonian_k.shape[-1],
        execution.groups,
        spinful_group_w,
        execution.result.double_counting_ev,
    )
    broadening = float(continuation["pade_broadening_ev"])
    _, local_orbital_pade = retarded_lattice_observables(
        execution.hamiltonian_k,
        omega,
        embedded_sigma_w,
        chemical_potential=float(contract["chemical_potential_ev"]),
        broadening=broadening,
    )
    path_kpoints, path_distance = _fractional_k_path(contract)
    path_hamiltonian = hamiltonian_from_hr(
        execution.translations,
        execution.degeneracies,
        execution.hopping_matrices,
        path_kpoints,
    )
    a_k_path, _ = retarded_lattice_observables(
        path_hamiltonian,
        omega,
        embedded_sigma_w,
        chemical_potential=float(contract["chemical_potential_ev"]),
        broadening=broadening,
    )
    group_d_maxent, maxent_records = _maximum_entropy_group_spectra(
        execution, contract, omega
    )
    layer_count = execution.hamiltonian_k.shape[-1] // 8
    layer_d_orbital = np.stack(
        [
            local_orbital_pade[:, 8 * layer : 8 * layer + 5]
            for layer in range(layer_count)
        ],
        axis=1,
    )
    layer_p_orbital = np.stack(
        [
            local_orbital_pade[:, 8 * layer + 5 : 8 * layer + 8]
            for layer in range(layer_count)
        ],
        axis=1,
    )
    beta = float(contract["cthyb"]["beta_ev_inverse"])
    tau = np.linspace(0.0, beta, execution.result.spin_correlation_tau.shape[-1])
    _save_npz_atomic(
        output_root / "observables.npz",
        omega_ev=omega,
        fractional_k_path=path_kpoints,
        k_path_distance=path_distance,
        a_k_path=a_k_path,
        local_orbital_pade=local_orbital_pade,
        layer_d_orbital_pade=layer_d_orbital,
        layer_p_orbital_pade=layer_p_orbital,
        group_d_orbital_maxent=group_d_maxent,
        sigma_group_retarded=sigma_group_w,
        tau_ev_inverse=tau,
        spin_correlation_tau=execution.result.spin_correlation_tau,
    )
    diagonal_sigma_imag = np.imag(np.diagonal(sigma_group_w, axis1=-2, axis2=-1))
    acceptance = {
        "schema_version": 1,
        "unit_id": contract["unit_id"],
        "target_ids": contract["target_ids"],
        "inner_dmft_converged": execution.result.converged,
        "inner_dmft_iterations": execution.result.iterations,
        "self_energy_final_residual_ev": (
            float(execution.result.residual_history[-1])
            if execution.result.residual_history.size
            else None
        ),
        "minimum_average_sign": float(np.min(execution.result.average_signs)),
        "causality_max_imaginary_self_energy_ev": float(np.max(diagonal_sigma_imag)),
        "minimum_pade_spectral_density": float(np.min(local_orbital_pade)),
        "maxent_normalization_max_error": float(
            max(abs(row["normalization"] - 1.0) for row in maxent_records)
        ),
        "chi_tau_symmetry_max_error": float(
            max(
                imaginary_time_symmetry_error(curve)
                for group in execution.result.spin_correlation_tau
                for curve in group
            )
        ),
        "maxent_records": maxent_records,
        "paper_exact": False,
        "promotion_allowed": False,
        "promotion_reason": (
            "outer charge convergence, strict-reference comparison, parameter "
            "provenance, and fresh independent review remain separate gates"
        ),
    }
    _write_json_atomic(output_root / "inner_acceptance.json", acceptance)
    return acceptance
