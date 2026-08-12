"""Explicit proxy for the incompletely specified acoustic-phonon inset."""

from __future__ import annotations

import numpy as np


def phonon_resistivity(
    temperature_k: np.ndarray,
    bloch_gruneisen_k: float,
    high_temperature_slope_per_k: float,
    crossover_power: float = 4.0,
) -> np.ndarray:
    """Smoothly join T^(power+1) and linear Bloch-Gruneisen limits."""

    temperature = np.asarray(temperature_k, dtype=float)
    if bloch_gruneisen_k <= 0.0 or high_temperature_slope_per_k < 0.0:
        raise ValueError("invalid phonon parameters")
    ratio = np.maximum(temperature / bloch_gruneisen_k, 0.0)
    return (
        high_temperature_slope_per_k
        * temperature
        * ratio**crossover_power
        / (1.0 + ratio**crossover_power)
    )
