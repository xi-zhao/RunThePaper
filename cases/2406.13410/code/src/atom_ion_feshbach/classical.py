"""Gaussian density and classical three-body recombination baseline."""

from __future__ import annotations

import numpy as np


def gaussian_density(
    displacement_um: np.ndarray | float,
    center_um: float,
    sigma_um: float,
    peak_density_cm3: float = 1.0,
) -> np.ndarray:
    if sigma_um <= 0 or peak_density_cm3 <= 0:
        raise ValueError("sigma and peak density must be positive")
    coordinate = np.asarray(displacement_um, dtype=float)
    return peak_density_cm3 * np.exp(-0.5 * ((coordinate - center_um) / sigma_um) ** 2)


def classical_tbr_rate(
    density_cm3: np.ndarray | float,
    excess_energy_k: np.ndarray | float,
    minimum_energy_k: float,
    k3_at_reference_cm6_s: float,
    reference_energy_k: float = 10.0e-3,
) -> np.ndarray:
    """Classical E^-3/4 TBR rate with the quoted 10-mK normalization."""

    density = np.asarray(density_cm3, dtype=float)
    energy = minimum_energy_k + np.asarray(excess_energy_k, dtype=float)
    if np.any(density < 0) or np.any(energy <= 0):
        raise ValueError("density must be nonnegative and energy must be positive")
    scaled_k3 = k3_at_reference_cm6_s * (energy / reference_energy_k) ** (-0.75)
    return scaled_k3 * density**2


def classical_survival(
    rate_s: np.ndarray | float, interaction_time_s: float
) -> np.ndarray:
    if interaction_time_s < 0:
        raise ValueError("interaction time must be nonnegative")
    rate = np.asarray(rate_s, dtype=float)
    if np.any(rate < 0):
        raise ValueError("rate must be nonnegative")
    return np.exp(-rate * interaction_time_s)
