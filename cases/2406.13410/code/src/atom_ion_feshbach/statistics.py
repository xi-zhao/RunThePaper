"""Analytic and independent random-matrix references for Main Figure 2."""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad
from scipy.special import sici


def poisson_number_variance(mean_count: np.ndarray | float) -> np.ndarray:
    """Variance of a unit-density Poisson point process."""

    values = np.asarray(mean_count, dtype=float)
    if np.any(values < 0):
        raise ValueError("mean count must be nonnegative")
    return values.copy()


def _sine_kernel(value: float) -> float:
    return float(np.sinc(value))


def _sine_kernel_derivative(value: float) -> float:
    if abs(value) < 1e-5:
        return float(-(np.pi**2) * value / 3.0 + (np.pi**4) * value**3 / 30.0)
    numerator = np.pi * value * np.cos(np.pi * value) - np.sin(np.pi * value)
    return float(numerator / (np.pi * value**2))


def goe_cluster_function(spacing: float) -> float:
    """Standard unfolded GOE two-level cluster function Y_2(s)."""

    if spacing < 0:
        raise ValueError("spacing must be nonnegative")
    if spacing == 0:
        return 1.0
    sine = _sine_kernel(spacing)
    sine_integral = 0.5 - float(sici(np.pi * spacing)[0]) / np.pi
    return sine * sine + _sine_kernel_derivative(spacing) * sine_integral


def goe_number_variance(mean_count: np.ndarray | float) -> np.ndarray:
    """Exact infinite-GOE number variance from the cluster-function identity."""

    values = np.atleast_1d(np.asarray(mean_count, dtype=float))
    if np.any(values < 0):
        raise ValueError("mean count must be nonnegative")
    output = np.empty_like(values)
    for index, length in enumerate(values):
        if length == 0:
            output[index] = 0.0
            continue
        integral, _ = quad(
            lambda spacing: (length - spacing) * goe_cluster_function(spacing),
            0.0,
            float(length),
            epsabs=2e-10,
            epsrel=2e-9,
            limit=250,
        )
        output[index] = length - 2.0 * integral
    return output.reshape(np.shape(mean_count))


def spacing_distributions(spacing: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit-mean Poisson and GOE Wigner-surmise densities."""

    spacing = np.asarray(spacing, dtype=float)
    if np.any(spacing < 0):
        raise ValueError("spacing must be nonnegative")
    poisson = np.exp(-spacing)
    wigner = 0.5 * np.pi * spacing * np.exp(-0.25 * np.pi * spacing**2)
    return poisson, wigner


def goe_spacing_sample(matrix_size: int, samples: int, seed: int) -> np.ndarray:
    """Seeded independent GOE spacing sample for a finite-size cross-check."""

    if matrix_size < 16 or samples < 1:
        raise ValueError("matrix_size >= 16 and samples >= 1 are required")
    rng = np.random.default_rng(seed)
    spacings: list[np.ndarray] = []
    lo = matrix_size // 4
    hi = matrix_size - lo
    for _ in range(samples):
        raw = rng.normal(size=(matrix_size, matrix_size))
        matrix = (raw + raw.T) / np.sqrt(2.0 * matrix_size)
        eigenvalues = np.linalg.eigvalsh(matrix)[lo:hi]
        local = np.diff(eigenvalues)
        local /= np.mean(local)
        spacings.append(local)
    return np.concatenate(spacings)


def empirical_number_variance(
    unfolded_levels: np.ndarray, interval_lengths: np.ndarray, origins: int = 2000
) -> np.ndarray:
    """Count variance over deterministic sliding origins of an unfolded spectrum."""

    levels = np.asarray(unfolded_levels, dtype=float)
    lengths = np.asarray(interval_lengths, dtype=float)
    if levels.ndim != 1 or levels.size < 20 or np.any(np.diff(levels) <= 0):
        raise ValueError("levels must be a strictly increasing one-dimensional array")
    maximum = float(np.max(lengths))
    start = levels[0]
    stop = levels[-1] - maximum
    if stop <= start:
        raise ValueError("spectrum is too short for requested intervals")
    grid = np.linspace(start, stop, origins)
    output = []
    for length in lengths:
        left = np.searchsorted(levels, grid, side="left")
        right = np.searchsorted(levels, grid + length, side="left")
        output.append(float(np.var(right - left, ddof=1)))
    return np.asarray(output)
