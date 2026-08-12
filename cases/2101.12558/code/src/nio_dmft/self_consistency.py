"""Paper-scale multi-site Wannier DMFT fixed-point machinery.

This module contains the numerical core between public Wannier90 output and
the impurity solver. It is independent of author code and keeps the
backend-specific charge-density update behind an explicit outer-loop adapter.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .cthyb import ImpurityResult
from .dmft import fll_double_counting

ImpuritySolver = Callable[[np.ndarray, dict[str, Any]], ImpurityResult]


@dataclass(frozen=True)
class MultiSiteDMFTResult:
    converged: bool
    iterations: int
    self_energy_positive_iw: np.ndarray
    local_green_positive_iw: np.ndarray
    density_matrices: np.ndarray
    spin_correlation_tau: np.ndarray
    average_signs: np.ndarray
    residual_history: np.ndarray
    double_counting_ev: np.ndarray


def positive_matsubara(beta: float, n_iw: int) -> np.ndarray:
    if beta <= 0.0 or n_iw < 1:
        raise ValueError("beta and n_iw must be positive")
    return (2 * np.arange(n_iw) + 1) * np.pi / beta


def uniform_fractional_kmesh(kmesh: tuple[int, int, int]) -> np.ndarray:
    if len(kmesh) != 3 or any(int(value) <= 0 for value in kmesh):
        raise ValueError("kmesh must contain three positive integers")
    axes = [np.arange(int(size), dtype=float) / int(size) for size in kmesh]
    return np.asarray(np.meshgrid(*axes, indexing="ij")).reshape(3, -1).T


def validate_correlated_groups(
    n_orbitals: int,
    groups: tuple[tuple[tuple[int, ...], ...], ...],
) -> int:
    """Validate symmetry groups of equal-size spatial correlated blocks."""

    if not groups or not groups[0] or not groups[0][0]:
        raise ValueError("at least one nonempty correlated group is required")
    block_size = len(groups[0][0])
    used: set[int] = set()
    for group in groups:
        if not group:
            raise ValueError("correlated groups cannot be empty")
        for block in group:
            if len(block) != block_size:
                raise ValueError("all correlated blocks must have equal size")
            if any(index < 0 or index >= n_orbitals for index in block):
                raise ValueError("correlated orbital index is out of range")
            overlap = used.intersection(block)
            if overlap:
                raise ValueError(f"correlated blocks overlap at {sorted(overlap)}")
            used.update(block)
    return block_size


def spinful_to_spatial_self_energy(spinful: np.ndarray) -> np.ndarray:
    """Paramagnetically average spin blocks while rejecting spin mixing."""

    sigma = np.asarray(spinful, dtype=np.complex128)
    if sigma.ndim < 3 or sigma.shape[-1] != sigma.shape[-2] or sigma.shape[-1] % 2:
        raise ValueError("spinful self-energy has an invalid shape")
    up = sigma[..., 0::2, 0::2]
    down = sigma[..., 1::2, 1::2]
    mixing = max(
        float(np.max(np.abs(sigma[..., 0::2, 1::2]))),
        float(np.max(np.abs(sigma[..., 1::2, 0::2]))),
    )
    if mixing > 1e-8:
        raise ValueError(
            f"spin-mixing self-energy violates the no-SOC contract: {mixing:.3e}"
        )
    return 0.5 * (up + down)


def spatial_to_spinful_green(spatial: np.ndarray) -> np.ndarray:
    green = np.asarray(spatial, dtype=np.complex128)
    size = green.shape[-1]
    result = np.zeros((*green.shape[:-2], 2 * size, 2 * size), dtype=np.complex128)
    result[..., 0::2, 0::2] = green
    result[..., 1::2, 1::2] = green
    return result


def positive_to_full_fermionic(values: np.ndarray) -> np.ndarray:
    """Expand positive-frequency matrices to TRIQS negative/positive order."""

    positive = np.asarray(values, dtype=np.complex128)
    negative = positive[::-1].swapaxes(-1, -2).conj()
    return np.concatenate([negative, positive], axis=0)


def full_to_positive_fermionic(values: np.ndarray, n_iw: int) -> np.ndarray:
    full = np.asarray(values, dtype=np.complex128)
    if full.shape[0] != 2 * n_iw:
        raise ValueError("full fermionic mesh must contain 2*n_iw points")
    return full[n_iw:]


def embed_group_self_energy(
    n_orbitals: int,
    groups: tuple[tuple[tuple[int, ...], ...], ...],
    spinful_sigma: np.ndarray,
    double_counting: np.ndarray,
) -> np.ndarray:
    spatial_sigma = spinful_to_spatial_self_energy(spinful_sigma)
    if spatial_sigma.shape[1] != len(groups):
        raise ValueError("self-energy group count does not match correlated groups")
    if np.asarray(double_counting).shape != (len(groups),):
        raise ValueError("double-counting vector does not match correlated groups")
    result = np.zeros(
        (spatial_sigma.shape[0], n_orbitals, n_orbitals),
        dtype=np.complex128,
    )
    for group_index, group in enumerate(groups):
        effective = spatial_sigma[:, group_index].copy()
        diagonal = np.arange(effective.shape[-1])
        effective[:, diagonal, diagonal] -= float(double_counting[group_index])
        for block in group:
            indices = np.asarray(block, dtype=int)
            result[:, indices[:, None], indices[None, :]] = effective
    return result


def lattice_green_and_local_blocks(
    hamiltonian_k: np.ndarray,
    z: np.ndarray,
    embedded_sigma: np.ndarray,
    groups: tuple[tuple[tuple[int, ...], ...], ...],
    *,
    chemical_potential: float,
    k_weights: np.ndarray | None = None,
    store_green_k: bool = False,
) -> tuple[np.ndarray | None, np.ndarray]:
    h_k = np.asarray(hamiltonian_k, dtype=np.complex128)
    frequencies = np.asarray(z, dtype=np.complex128)
    if h_k.ndim != 3 or h_k.shape[1] != h_k.shape[2]:
        raise ValueError("hamiltonian_k must have shape (nk,norb,norb)")
    if embedded_sigma.shape != (frequencies.size, h_k.shape[1], h_k.shape[2]):
        raise ValueError("embedded self-energy shape mismatch")
    weights = (
        np.full(h_k.shape[0], 1.0 / h_k.shape[0])
        if k_weights is None
        else np.asarray(k_weights, dtype=float)
    )
    if weights.shape != (h_k.shape[0],) or not np.isclose(np.sum(weights), 1.0):
        raise ValueError("k weights must be normalized")
    identity = np.eye(h_k.shape[1], dtype=np.complex128)
    green_k = (
        np.empty(
            (frequencies.size, h_k.shape[0], h_k.shape[1], h_k.shape[2]),
            dtype=np.complex128,
        )
        if store_green_k
        else None
    )
    local = np.empty(
        (frequencies.size, h_k.shape[1], h_k.shape[2]),
        dtype=np.complex128,
    )
    for frequency_index, frequency in enumerate(frequencies):
        inverse = (
            (frequency + chemical_potential) * identity[None, :, :]
            - h_k
            - embedded_sigma[frequency_index][None, :, :]
        )
        frequency_green = np.linalg.inv(inverse)
        local[frequency_index] = np.einsum(
            "k,kij->ij", weights, frequency_green, optimize=True
        )
        if green_k is not None:
            green_k[frequency_index] = frequency_green
    block_size = len(groups[0][0])
    local_groups = np.empty(
        (frequencies.size, len(groups), block_size, block_size),
        dtype=np.complex128,
    )
    for group_index, group in enumerate(groups):
        blocks = []
        for block in group:
            indices = np.asarray(block, dtype=int)
            blocks.append(local[:, indices[:, None], indices[None, :]])
        local_groups[:, group_index] = np.mean(blocks, axis=0)
    return green_k, local_groups


def retarded_lattice_observables(
    hamiltonian_k: np.ndarray,
    omega: np.ndarray,
    embedded_self_energy: np.ndarray,
    *,
    chemical_potential: float,
    broadening: float,
    k_weights: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Stream retarded inversions into A(k,w) and local orbital spectra.

    Only the trace over each k point and the local diagonal are retained.  This
    keeps the paper-scale 88-orbital slab calculation bounded in memory.
    """

    h_k = np.asarray(hamiltonian_k, dtype=np.complex128)
    energies = np.asarray(omega, dtype=float)
    sigma = np.asarray(embedded_self_energy, dtype=np.complex128)
    if h_k.ndim != 3 or h_k.shape[1] != h_k.shape[2]:
        raise ValueError("hamiltonian_k must have shape (nk,norb,norb)")
    if sigma.shape != (energies.size, h_k.shape[1], h_k.shape[2]):
        raise ValueError("retarded self-energy shape mismatch")
    if broadening <= 0.0:
        raise ValueError("broadening must be positive")
    weights = (
        np.full(h_k.shape[0], 1.0 / h_k.shape[0])
        if k_weights is None
        else np.asarray(k_weights, dtype=float)
    )
    if weights.shape != (h_k.shape[0],) or not np.isclose(np.sum(weights), 1.0):
        raise ValueError("k weights must be normalized")
    identity = np.eye(h_k.shape[1], dtype=np.complex128)
    a_k = np.empty((energies.size, h_k.shape[0]), dtype=float)
    local_orbital = np.empty((energies.size, h_k.shape[1]), dtype=float)
    for index, energy in enumerate(energies):
        inverse = (
            (energy + 1j * broadening + chemical_potential) * identity[None, :, :]
            - h_k
            - sigma[index][None, :, :]
        )
        green = np.linalg.inv(inverse)
        a_k[index] = -np.imag(np.trace(green, axis1=1, axis2=2)) / np.pi
        local = np.einsum("k,kij->ij", weights, green, optimize=True)
        local_orbital[index] = -np.imag(np.diag(local)) / np.pi
    return a_k, local_orbital


def density_matrix_from_positive_green(
    local_green_positive: np.ndarray,
    *,
    beta: float,
) -> np.ndarray:
    """Return the spin-summed correlated density matrix."""

    green = np.asarray(local_green_positive, dtype=np.complex128)
    size = green.shape[-1]
    identity = np.eye(size)[None, :, :]
    density = identity + (4.0 / beta) * np.sum(green.real, axis=0)
    return 0.5 * (density + density.swapaxes(-1, -2))


def scientific_input_digest(
    hamiltonian_k: np.ndarray,
    groups: tuple[tuple[tuple[int, ...], ...], ...],
    contract: dict[str, Any],
) -> str:
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(hamiltonian_k).view(np.uint8))
    digest.update(json.dumps(groups, separators=(",", ":")).encode())
    digest.update(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode())
    return digest.hexdigest()


def _save_checkpoint(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def run_multisite_dmft(
    hamiltonian_k: np.ndarray,
    groups: tuple[tuple[tuple[int, ...], ...], ...],
    solver_contract: dict[str, Any],
    impurity_solver: ImpuritySolver,
    *,
    chemical_potential: float,
    initial_d_occupancy: float,
    mixing: float,
    tolerance: float,
    max_iterations: int,
    checkpoint_path: Path | None = None,
    resume: bool = True,
) -> MultiSiteDMFTResult:
    """Run the inner multi-site DMFT loop with atomic checkpoint/resume."""

    h_k = np.asarray(hamiltonian_k, dtype=np.complex128)
    block_size = validate_correlated_groups(h_k.shape[-1], groups)
    if int(solver_contract["n_orbitals"]) != block_size:
        raise ValueError("solver orbital count does not match correlated blocks")
    if not 0.0 < mixing <= 1.0 or tolerance <= 0.0 or max_iterations < 1:
        raise ValueError("invalid fixed-point controls")
    beta = float(solver_contract["beta_ev_inverse"])
    n_iw = int(solver_contract["n_iw"])
    frequencies = 1j * positive_matsubara(beta, n_iw)
    n_groups = len(groups)
    n_flavors = 2 * block_size
    n_correlations = len(solver_contract["spin_correlation_orbitals"])
    sigma = np.zeros((n_iw, n_groups, n_flavors, n_flavors), dtype=np.complex128)
    occupancy = np.full(n_groups, initial_d_occupancy, dtype=float)
    residuals: list[float] = []
    start_iteration = 1
    fixed_point_contract = {
        "solver": solver_contract,
        "chemical_potential": chemical_potential,
        "initial_d_occupancy": initial_d_occupancy,
        "mixing": mixing,
        "tolerance": tolerance,
        "max_iterations": max_iterations,
    }
    digest = scientific_input_digest(h_k, groups, fixed_point_contract)
    loaded_density: np.ndarray | None = None
    loaded_chi: np.ndarray | None = None
    loaded_signs: np.ndarray | None = None
    loaded_converged = False
    if checkpoint_path is not None and checkpoint_path.is_file() and resume:
        with np.load(checkpoint_path, allow_pickle=False) as checkpoint:
            if str(checkpoint["scientific_input_sha256"]) == digest:
                sigma = checkpoint["self_energy_positive_iw"]
                occupancy = checkpoint["occupancy"]
                residuals = checkpoint["residual_history"].astype(float).tolist()
                start_iteration = int(checkpoint["iteration"]) + 1
                loaded_density = checkpoint["density_matrices"]
                loaded_chi = checkpoint["spin_correlation_tau"]
                loaded_signs = checkpoint["average_signs"]
                loaded_converged = bool(checkpoint["converged"])

    converged = loaded_converged
    density_matrices = (
        loaded_density
        if loaded_density is not None
        else np.zeros((n_groups, n_flavors, n_flavors), dtype=float)
    )
    chi_tau = (
        loaded_chi
        if loaded_chi is not None
        else np.zeros(
            (n_groups, n_correlations, int(solver_contract["n_tau"])), dtype=float
        )
    )
    signs = (
        loaded_signs if loaded_signs is not None else np.zeros(n_groups, dtype=float)
    )
    local_spatial = np.empty(
        (n_iw, n_groups, block_size, block_size), dtype=np.complex128
    )
    double_counting = fll_double_counting(
        occupancy,
        hubbard_u=float(solver_contract["u_ev"]),
        hund_j=float(solver_contract["j_ev"]),
    )
    iteration = start_iteration - 1
    for iteration in range(start_iteration, max_iterations + 1):
        if converged:
            break
        embedded = embed_group_self_energy(
            h_k.shape[-1], groups, sigma, double_counting
        )
        _, local_spatial = lattice_green_and_local_blocks(
            h_k,
            frequencies,
            embedded,
            groups,
            chemical_potential=chemical_potential,
        )
        candidates = np.empty_like(sigma)
        for group_index in range(n_groups):
            sigma_spatial = spinful_to_spatial_self_energy(sigma[:, group_index])
            weiss_inverse = np.linalg.inv(local_spatial[:, group_index]) + sigma_spatial
            weiss_positive = spatial_to_spinful_green(np.linalg.inv(weiss_inverse))
            contract = dict(solver_contract)
            contract["random_seed"] = (
                int(solver_contract["random_seed"]) + group_index + 104729 * iteration
            )
            solved = impurity_solver(
                positive_to_full_fermionic(weiss_positive),
                contract,
            )
            if solved.self_energy_iw.shape != (2 * n_iw, n_flavors, n_flavors):
                raise ValueError(
                    "impurity self-energy shape violates the solver contract"
                )
            if solved.density_matrix.shape != (n_flavors, n_flavors):
                raise ValueError(
                    "impurity density-matrix shape violates the solver contract"
                )
            if solved.spin_correlation_tau.shape != (
                n_correlations,
                int(solver_contract["n_tau"]),
            ):
                raise ValueError("impurity chi(tau) shape violates the solver contract")
            candidates[:, group_index] = full_to_positive_fermionic(
                solved.self_energy_iw, n_iw
            )
            density_matrices[group_index] = solved.density_matrix.real
            chi_tau[group_index] = solved.spin_correlation_tau
            signs[group_index] = solved.average_sign
        mixed = (1.0 - mixing) * sigma + mixing * candidates
        residual = float(np.max(np.abs(mixed - sigma)))
        residuals.append(residual)
        sigma = mixed
        occupancy = np.trace(density_matrices, axis1=1, axis2=2).real
        double_counting = fll_double_counting(
            occupancy,
            hubbard_u=float(solver_contract["u_ev"]),
            hund_j=float(solver_contract["j_ev"]),
        )
        if checkpoint_path is not None:
            _save_checkpoint(
                checkpoint_path,
                scientific_input_sha256=np.asarray(digest),
                iteration=np.asarray(iteration),
                self_energy_positive_iw=sigma,
                occupancy=occupancy,
                residual_history=np.asarray(residuals),
                density_matrices=density_matrices,
                spin_correlation_tau=chi_tau,
                average_signs=signs,
                converged=np.asarray(residual <= tolerance),
            )
        if residual <= tolerance:
            converged = True
            break

    embedded = embed_group_self_energy(h_k.shape[-1], groups, sigma, double_counting)
    _, local_spatial = lattice_green_and_local_blocks(
        h_k,
        frequencies,
        embedded,
        groups,
        chemical_potential=chemical_potential,
    )
    return MultiSiteDMFTResult(
        converged=converged,
        iterations=iteration,
        self_energy_positive_iw=sigma,
        local_green_positive_iw=local_spatial,
        density_matrices=density_matrices,
        spin_correlation_tau=chi_tau,
        average_signs=signs,
        residual_history=np.asarray(residuals),
        double_counting_ev=double_counting,
    )
