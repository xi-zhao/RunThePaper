"""Level-ratio observables and finite-size crossing estimators."""

from __future__ import annotations

import numpy as np


POISSON_MEAN = 2.0 * np.log(2.0) - 1.0
GOE_MEAN_PAPER = 0.5295


def adjacent_gap_ratios(eigenvalues: np.ndarray) -> np.ndarray:
    values = np.asarray(eigenvalues, dtype=np.float64)
    if values.ndim != 1 or values.size < 3:
        raise ValueError("at least three eigenvalues are required")
    gaps = np.diff(np.sort(values))
    left = gaps[:-1]
    right = gaps[1:]
    denominator = np.maximum(left, right)
    valid = denominator > np.finfo(np.float64).eps
    ratios = np.minimum(left[valid], right[valid]) / denominator[valid]
    return ratios[(ratios >= 0.0) & (ratios <= 1.0)]


def poisson_density(ratio: np.ndarray | float) -> np.ndarray:
    ratio_array = np.asarray(ratio, dtype=np.float64)
    return 2.0 / (1.0 + ratio_array) ** 2


def random_goe_ratios(*, matrix_size: int, samples: int, seed: int) -> np.ndarray:
    if matrix_size < 3 or samples < 1:
        raise ValueError("invalid GOE campaign size")
    rng = np.random.default_rng(seed)
    batches = []
    for _ in range(samples):
        raw = rng.normal(size=(matrix_size, matrix_size))
        matrix = (raw + raw.T) / np.sqrt(2.0 * matrix_size)
        batches.append(adjacent_gap_ratios(np.linalg.eigvalsh(matrix)))
    return np.concatenate(batches)


def crossing_estimates(
    disorder: np.ndarray,
    lower_curve: np.ndarray,
    upper_curve: np.ndarray,
) -> list[dict[str, float | str]]:
    """Linearly interpolate every sign-changing crossing of two size curves."""

    x = np.asarray(disorder, dtype=np.float64)
    first = np.asarray(lower_curve, dtype=np.float64)
    second = np.asarray(upper_curve, dtype=np.float64)
    if x.ndim != 1 or first.shape != x.shape or second.shape != x.shape:
        raise ValueError("crossing inputs must be aligned one-dimensional arrays")
    difference = second - first
    crossings: list[dict[str, float | str]] = []
    for index in range(len(x) - 1):
        y0 = difference[index]
        y1 = difference[index + 1]
        if y0 == 0.0:
            crossings.append(
                {"w_cross": float(x[index]), "r_cross": float(second[index]), "method": "grid_exact"}
            )
        elif y0 * y1 < 0.0:
            fraction = -y0 / (y1 - y0)
            w_cross = x[index] + fraction * (x[index + 1] - x[index])
            r_cross = second[index] + fraction * (second[index + 1] - second[index])
            crossings.append(
                {"w_cross": float(w_cross), "r_cross": float(r_cross), "method": "linear_interpolation"}
            )
    if crossings:
        return crossings
    nearest = int(np.argmin(np.abs(difference)))
    return [
        {
            "w_cross": float(x[nearest]),
            "r_cross": float(0.5 * (first[nearest] + second[nearest])),
            "method": "nearest_approach_no_sign_change",
        }
    ]
