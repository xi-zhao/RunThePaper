"""Numerical rules behind the AFHM overlap-bound table columns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class TunedInverseSquareSpectrum:
    """Inverse-square distribution tuned to a requested ground probability."""

    nu: float
    compression_bound: float
    probabilities: np.ndarray
    ground_probability: float
    stationarity_relative_residual: float


def tuned_inverse_square_spectrum(
    energies: Sequence[float],
    stable_schmidt_ranks: Sequence[float],
    target_ground_probability: float,
    *,
    iterations: int = 160,
) -> TunedInverseSquareSpectrum:
    """Tune ``nu < E1`` so the normalized inverse-square law has target p1.

    Proposition 2 gives weights proportional to
    ``1 / (M_i * (E_i - nu)**2)`` and its stationarity equation gives
    ``m = B2 / B1**2``.  This scalar form avoids materializing any dense
    state-space object after exact diagonalization.
    """

    levels = np.asarray(energies, dtype=np.float64)
    ranks = np.asarray(stable_schmidt_ranks, dtype=np.float64)
    if levels.ndim != 1 or ranks.shape != levels.shape or len(levels) < 2:
        raise ValueError("energies and ranks must be equal-length vectors")
    if np.any(ranks <= 0) or not 0 < target_ground_probability < 1:
        raise ValueError("ranks must be positive and target probability must lie in (0, 1)")
    ground_index = int(np.argmin(levels))
    ground_energy = float(levels[ground_index])
    if np.count_nonzero(np.isclose(levels, ground_energy, atol=1e-10, rtol=0)) != 1:
        raise ValueError("the table reproduction requires a unique ground state")

    inverse_ranks = 1.0 / ranks
    asymptotic_ground_probability = float(
        inverse_ranks[ground_index] / inverse_ranks.sum()
    )
    if target_ground_probability <= asymptotic_ground_probability:
        raise ValueError("target ground probability is below the inverse-rank asymptote")

    def distribution(nu: float) -> np.ndarray:
        weights = inverse_ranks / (levels - nu) ** 2
        return weights / weights.sum()

    span = max(1.0, float(np.max(levels) - ground_energy))
    lower = ground_energy - span
    while distribution(lower)[ground_index] > target_ground_probability:
        span *= 2.0
        lower = ground_energy - span
        if not np.isfinite(lower):
            raise RuntimeError("failed to bracket the ground-probability root")
    upper = ground_energy - max(1e-14, span * np.finfo(np.float64).eps)
    if distribution(upper)[ground_index] < target_ground_probability:
        raise RuntimeError("failed to bracket the root below the ground energy")

    for _ in range(iterations):
        middle = (lower + upper) / 2.0
        if distribution(middle)[ground_index] < target_ground_probability:
            lower = middle
        else:
            upper = middle
    nu = (lower + upper) / 2.0
    probabilities = distribution(nu)
    energy_gaps = levels - nu
    b1 = float(np.sum(inverse_ranks / energy_gaps))
    b2 = float(np.sum(inverse_ranks / energy_gaps**2))
    compression_bound = b2 / b1**2
    residual = abs(b2 / compression_bound - b1**2) / b1**2
    return TunedInverseSquareSpectrum(
        nu=nu,
        compression_bound=compression_bound,
        probabilities=probabilities,
        ground_probability=float(probabilities[ground_index]),
        stationarity_relative_residual=float(residual),
    )


def printed_value_tolerance(value: float, significant_figures: int = 4) -> float:
    """Half a unit in the last printed significant digit."""

    if value == 0:
        return 0.5 * 10 ** (1 - significant_figures)
    exponent = int(np.floor(np.log10(abs(value))))
    return 0.5 * 10 ** (exponent - significant_figures + 1)
