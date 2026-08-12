"""Independent multi-site DMFT equations and a bounded Hubbard-I validator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lattice import (
    LayeredPDModel,
    lattice_green_function,
    layer_diagonal,
    matsubara_frequencies,
)


@dataclass(frozen=True)
class DMFTResult:
    converged: bool
    iterations: int
    occupancies: np.ndarray
    self_energy_iw: np.ndarray
    local_green_iw: np.ndarray
    weiss_iw: np.ndarray
    residual_history: np.ndarray


def fll_double_counting(
    occupancy: np.ndarray, *, hubbard_u: float, hund_j: float
) -> np.ndarray:
    """Paramagnetic fully-localized-limit potential used in the case contract."""

    values = np.asarray(occupancy, dtype=float)
    return hubbard_u * (values - 0.5) - hund_j * (0.5 * values - 0.5)


def hubbard_i_self_energy(
    z: np.ndarray,
    *,
    occupancy: np.ndarray,
    epsilon_d: float,
    chemical_potential: float,
    hubbard_u: float,
    double_counting: np.ndarray,
) -> np.ndarray:
    """Spin-degenerate one-orbital Hubbard-I self-energy for validation.

    ``occupancy`` is the total two-spin d occupancy per layer. The rational
    term is causal in the upper half plane and supplies a strong independent
    check of the lattice Dyson path.
    """

    frequencies = np.asarray(z, dtype=np.complex128)[:, None]
    density = np.asarray(occupancy, dtype=float)[None, :]
    dc = np.asarray(double_counting, dtype=float)[None, :]
    per_spin = np.clip(0.5 * density, 1e-8, 1.0 - 1e-8)
    hartree = hubbard_u * per_spin - dc
    numerator = hubbard_u**2 * per_spin * (1.0 - per_spin)
    denominator = (
        frequencies + chemical_potential - epsilon_d - hubbard_u * (1.0 - per_spin)
    )
    return hartree + numerator / denominator


def weiss_field(local_green: np.ndarray, layer_sigma: np.ndarray) -> np.ndarray:
    """Compute G0^{-1}=G_loc^{-1}+Sigma for scalar layer blocks."""

    green = np.asarray(local_green, dtype=np.complex128)
    sigma = np.asarray(layer_sigma, dtype=np.complex128)
    if green.shape != sigma.shape:
        raise ValueError("local Green function and self-energy shapes differ")
    return 1.0 / green + sigma


def occupancy_from_matsubara(
    local_green_iw: np.ndarray,
    *,
    beta: float,
) -> np.ndarray:
    """Estimate total two-spin occupancy from positive Matsubara values."""

    density = 1.0 + (4.0 / beta) * np.sum(np.real(local_green_iw), axis=0)
    return np.clip(density, 0.02, 1.98)


def run_hubbard_i_dmft(
    model: LayeredPDModel,
    *,
    beta: float,
    n_iw: int,
    chemical_potential: float,
    epsilon_d: float,
    hubbard_u: float,
    hund_j: float,
    initial_occupancy: float,
    mixing: float,
    tolerance: float,
    max_iterations: int,
) -> DMFTResult:
    """Run a deterministic multi-site Hubbard-I fixed-point iteration."""

    if not 0.0 < mixing <= 1.0:
        raise ValueError("mixing must lie in (0, 1]")
    iw = matsubara_frequencies(beta, n_iw)
    z = 1j * iw
    occupancy = np.full(model.n_layers, initial_occupancy, dtype=float)
    residuals: list[float] = []
    converged = False

    for iteration in range(1, max_iterations + 1):
        double_counting = fll_double_counting(
            occupancy,
            hubbard_u=hubbard_u,
            hund_j=hund_j,
        )
        sigma = hubbard_i_self_energy(
            z,
            occupancy=occupancy,
            epsilon_d=epsilon_d,
            chemical_potential=chemical_potential,
            hubbard_u=hubbard_u,
            double_counting=double_counting,
        )
        _, local_matrix = lattice_green_function(
            model,
            z,
            sigma,
            chemical_potential=chemical_potential,
        )
        d_green, _ = layer_diagonal(model, local_matrix)
        candidate = occupancy_from_matsubara(d_green, beta=beta)
        updated = (1.0 - mixing) * occupancy + mixing * candidate
        residual = float(np.max(np.abs(updated - occupancy)))
        residuals.append(residual)
        occupancy = updated
        if residual < tolerance:
            converged = True
            break

    double_counting = fll_double_counting(
        occupancy,
        hubbard_u=hubbard_u,
        hund_j=hund_j,
    )
    sigma = hubbard_i_self_energy(
        z,
        occupancy=occupancy,
        epsilon_d=epsilon_d,
        chemical_potential=chemical_potential,
        hubbard_u=hubbard_u,
        double_counting=double_counting,
    )
    _, local_matrix = lattice_green_function(
        model,
        z,
        sigma,
        chemical_potential=chemical_potential,
    )
    d_green, _ = layer_diagonal(model, local_matrix)
    return DMFTResult(
        converged=converged,
        iterations=iteration,
        occupancies=occupancy,
        self_energy_iw=sigma,
        local_green_iw=d_green,
        weiss_iw=weiss_field(d_green, sigma),
        residual_history=np.asarray(residuals),
    )


def atomic_spin_correlation(
    tau: np.ndarray,
    *,
    beta: float,
    epsilon_d: float,
    chemical_potential: float,
    hubbard_u: float,
) -> np.ndarray:
    """Exact single-orbital atomic chi(tau), constant by spin conservation."""

    times = np.asarray(tau, dtype=float)
    if np.any(times < 0.0) or np.any(times > beta):
        raise ValueError("tau must lie inside [0, beta]")
    single_energy = epsilon_d - chemical_potential
    weights = np.array(
        [
            1.0,
            np.exp(-beta * single_energy),
            np.exp(-beta * single_energy),
            np.exp(-beta * (2.0 * single_energy + hubbard_u)),
        ],
        dtype=float,
    )
    mean_mz_squared = (weights[1] + weights[2]) / np.sum(weights)
    return np.full(times.shape, mean_mz_squared, dtype=float)
