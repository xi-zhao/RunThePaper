"""Small statistical identities used by the published result."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def combine_independent_uncertainties(components: ArrayLike) -> float:
    values = np.asarray(components, dtype=float)
    if values.ndim != 1 or values.size == 0 or np.any(values < 0):
        raise ValueError("uncertainty components must be a nonempty nonnegative vector")
    return float(np.sqrt(np.sum(values**2)))


def normal_pdf(grid: ArrayLike, *, mean: float, sigma: float) -> NDArray[np.float64]:
    values = np.asarray(grid, dtype=float)
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    z = (values - mean) / sigma
    return np.exp(-0.5 * z**2) / (np.sqrt(2.0 * np.pi) * sigma)


def standard_error(sample_sigma: float, sample_count: int) -> float:
    if sample_sigma <= 0 or sample_count <= 0:
        raise ValueError("sample_sigma and sample_count must be positive")
    return float(sample_sigma / np.sqrt(sample_count))
