"""Formula-derived free-fermion and CFT calculations for Figs. 2 and 3.

No function in this module reads paper figures, author arrays, or author code.
The lattice lane starts from the printed half-filled correlation kernel, while
the CFT lane starts from the charged moments and Bessel-integral formulas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.linalg import eigh, toeplitz
from scipy.special import i0, iv


ENTROPY_CONSTANT_FREE_FERMION = 0.495017908135137


def half_filled_toeplitz_column(length: int) -> np.ndarray:
    """Return C[i,0] for C_ij=sin(pi(i-j)/2)/(pi(i-j))."""

    if length < 2 or length % 2:
        raise ValueError("the paper-exact subsystem length must be positive and even")
    separation = np.arange(length, dtype=np.float64)
    column = np.empty(length, dtype=np.float64)
    column[0] = 0.5
    column[1:] = np.sin(0.5 * np.pi * separation[1:]) / (np.pi * separation[1:])
    return column


def correlation_eigenvalues(length: int, active_modes: int) -> np.ndarray:
    """Diagonalize only the transition eigenvalues of the Toeplitz matrix."""

    if active_modes <= 0 or active_modes % 2 or active_modes >= length:
        raise ValueError("active_modes must be positive, even, and below length")
    matrix = toeplitz(half_filled_toeplitz_column(length))
    lower = length // 2 - active_modes // 2
    upper = lower + active_modes - 1
    values = eigh(
        matrix,
        eigvals_only=True,
        subset_by_index=[lower, upper],
        driver="evr",
        overwrite_a=True,
        check_finite=False,
    )
    return np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)


@dataclass(frozen=True)
class ResolvedThermodynamics:
    particle_numbers: np.ndarray
    probability: np.ndarray
    entropy_contribution: np.ndarray


def resolved_probability_and_entropy(
    eigenvalues: np.ndarray,
    *,
    subsystem_length: int,
) -> ResolvedThermodynamics:
    """Convolve independent modes by particle number and entropy weight."""

    probabilities = np.asarray(eigenvalues, dtype=np.float64)
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("correlation eigenvalues must be probabilities")
    count = probabilities.size
    distribution = np.zeros(count + 1, dtype=np.float64)
    entropy = np.zeros(count + 1, dtype=np.float64)
    distribution[0] = 1.0
    occupied = 0
    for f in probabilities:
        empty = 1.0 - f
        old_distribution = distribution.copy()
        old_entropy = entropy.copy()
        distribution.fill(0.0)
        entropy.fill(0.0)
        distribution[: occupied + 1] += empty * old_distribution[: occupied + 1]
        distribution[1 : occupied + 2] += f * old_distribution[: occupied + 1]
        entropy[: occupied + 1] += empty * old_entropy[: occupied + 1]
        entropy[1 : occupied + 2] += f * old_entropy[: occupied + 1]
        if empty > 0.0:
            entropy[: occupied + 1] -= empty * np.log(empty) * old_distribution[: occupied + 1]
        if f > 0.0:
            entropy[1 : occupied + 2] -= f * np.log(f) * old_distribution[: occupied + 1]
        occupied += 1

    deterministic_particles = subsystem_length // 2 - int(np.count_nonzero(probabilities > 0.5))
    particle_numbers = deterministic_particles + np.arange(count + 1, dtype=int)
    return ResolvedThermodynamics(particle_numbers, distribution, entropy)


def analytic_charge_curves(delta_number: np.ndarray, length: int) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """CFT/Fisher-Hartwig charge probability and entropy curves."""

    delta = np.asarray(delta_number, dtype=np.float64)
    variance = (np.log(2.0 * length) + np.euler_gamma + 1.0) / np.pi**2
    probability = np.exp(-(delta**2) / (2.0 * variance)) / np.sqrt(2.0 * np.pi * variance)
    total_entropy = np.log(2.0 * length) / 3.0 + ENTROPY_CONSTANT_FREE_FERMION
    sector_entropy = probability * (total_entropy - 0.5 + delta**2 / (2.0 * variance))
    return probability, sector_entropy, {
        "variance": float(variance),
        "total_entropy": float(total_entropy),
    }


@dataclass(frozen=True)
class ManyBodySpectrum:
    central_log_lambda_max: float
    curves: dict[str, tuple[np.ndarray, np.ndarray]]
    selected_entanglement_energies: np.ndarray


def enumerate_many_body_spectrum(
    eigenvalues: np.ndarray,
    *,
    selected_modes: int,
    sectors: tuple[int, ...],
    rank_max: int,
    x_max: float,
) -> ManyBodySpectrum:
    """Enumerate the 2^selected_modes highest-spectrum free-fermion states."""

    f_all = np.asarray(eigenvalues, dtype=np.float64)
    safe = np.clip(f_all, np.finfo(float).tiny, 1.0 - np.finfo(float).eps)
    energies_all = np.log1p(-safe) - np.log(safe)
    selected_indices = np.argsort(np.abs(energies_all))[:selected_modes]
    selected_indices = selected_indices[np.argsort(energies_all[selected_indices])]
    selected_mask = np.zeros(f_all.size, dtype=bool)
    selected_mask[selected_indices] = True
    fixed = f_all[~selected_mask]
    log_fixed = float(np.log(np.maximum(fixed, 1.0 - fixed)).sum())

    selected = safe[selected_indices]
    ground_occupancy = (selected > 0.5).astype(np.int8)
    log_weights = np.array([log_fixed], dtype=np.float64)
    delta_charges = np.array([0], dtype=np.int8)
    for probability, ground in zip(selected, ground_occupancy):
        previous_logs = log_weights
        previous_charges = delta_charges
        log_weights = np.concatenate(
            [previous_logs + np.log1p(-probability), previous_logs + np.log(probability)]
        )
        delta_charges = np.concatenate(
            [previous_charges - ground, previous_charges + (1 - ground)]
        ).astype(np.int8, copy=False)

    central_mask = delta_charges == 0
    central_log_lambda_max = float(np.max(log_weights[central_mask]))
    curves: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    masks: list[tuple[str, np.ndarray]] = [("all", np.ones(log_weights.size, dtype=bool))]
    masks.extend((str(sector), delta_charges == sector) for sector in sectors)
    for label, mask in masks:
        values = np.sort(log_weights[mask])[::-1]
        ranks = np.arange(1, values.size + 1, dtype=np.int64)
        x = 2.0 * np.sqrt(
            np.maximum(0.0, -central_log_lambda_max * (central_log_lambda_max - values))
        )
        keep = (ranks <= rank_max) & (x <= x_max)
        curves[label] = (x[keep], ranks[keep])

    return ManyBodySpectrum(
        central_log_lambda_max=central_log_lambda_max,
        curves=curves,
        selected_entanglement_energies=energies_all[selected_indices],
    )


def analytic_integrated_spectrum(
    x: np.ndarray,
    sectors: tuple[int, ...],
    *,
    quadrature_nodes: int,
    luttinger_k: float = 1.0,
) -> dict[str, np.ndarray]:
    """Evaluate the printed Bessel-integral spectrum formula."""

    x_values = np.asarray(x, dtype=np.float64)
    nodes, weights = leggauss(quadrature_nodes)
    alpha = 0.5 * np.pi * (nodes + 1.0)
    weights = 0.5 * np.pi * weights
    r_alpha = 1.0 - 3.0 * luttinger_k * alpha**2 / np.pi**2
    argument = x_values[:, None] * np.sqrt(r_alpha.astype(np.complex128))[None, :]
    bessel = iv(0, argument).real
    curves = {"all": i0(x_values)}
    for sector in sectors:
        curves[str(sector)] = (bessel @ (weights * np.cos(alpha * sector))) / np.pi
    return curves
