"""Small, source-independent checks for atomized claims in arXiv:1812.05561.

The functions in this module operate only on independently generated arrays or
on the analytic assumptions printed in the paper.  They never read paper
figures, digitized curves, author arrays, or author code.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np


def _window(start_stop: Sequence[int]) -> np.ndarray:
    if len(start_stop) != 2:
        raise ValueError("fit window must contain [start, stop]")
    start, stop = (int(value) for value in start_stop)
    if start < 1 or stop < start:
        raise ValueError("fit window must satisfy 1 <= start <= stop")
    return np.arange(start, stop + 1, dtype=np.float64)


def log_power_law_fit(
    x_values: np.ndarray,
    y_values: np.ndarray,
    start_stop: Sequence[int],
) -> dict[str, Any]:
    """Fit ``y = exp(intercept) * x**slope`` on an integer x window."""

    x = np.asarray(x_values, dtype=np.float64)
    y = np.asarray(y_values, dtype=np.float64)
    grid = _window(start_stop)
    indices = grid.astype(np.int64)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
        raise ValueError("x_values and y_values must be equal-length vectors")
    if indices[-1] >= len(y) or not np.allclose(x[indices], grid):
        raise ValueError("fit window must address the declared integer grid")
    selected = y[indices]
    if np.any(~np.isfinite(selected)) or np.any(selected <= 0.0):
        raise ValueError("power-law fitting requires positive finite values")
    slope, intercept = np.polyfit(np.log(grid), np.log(selected), 1)
    curve = np.exp(intercept) * np.power(grid, slope)
    residual = np.log(selected) - np.log(curve)
    return {
        "grid": grid,
        "curve": curve,
        "coefficients": np.asarray([slope, intercept], dtype=np.float64),
        "log_rms_residual": float(np.sqrt(np.mean(residual * residual))),
    }


def revival_fit_evidence(
    revival: np.ndarray,
    gamma: np.ndarray,
    short_fit: Sequence[int],
    long_fit: Sequence[int],
) -> dict[str, Any]:
    """Freeze both fitted branches and their positive intersection."""

    short = log_power_law_fit(revival, gamma, short_fit)
    long = log_power_law_fit(revival, gamma, long_fit)
    slope_short, intercept_short = short["coefficients"]
    slope_long, intercept_long = long["coefficients"]
    denominator = float(slope_short - slope_long)
    turning_point = float("nan")
    if abs(denominator) > 1e-12:
        turning_point = float(math.exp((intercept_long - intercept_short) / denominator))
    return {"short": short, "long": long, "turning_point": turning_point}


def turning_point_power_law(
    sizes: np.ndarray,
    turning_points: np.ndarray,
) -> dict[str, Any]:
    """Fit and freeze the Supplement Fig. S3(c) power-law guide."""

    x = np.asarray(sizes, dtype=np.float64)
    y = np.asarray(turning_points, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape or len(x) < 2:
        raise ValueError("sizes and turning_points must be equal vectors with >=2 rows")
    if np.any(~np.isfinite(x)) or np.any(~np.isfinite(y)) or np.any(x <= 0) or np.any(y <= 0):
        raise ValueError("power-law scaling requires positive finite values")
    exponent, intercept = np.polyfit(np.log(x), np.log(y), 1)
    curve = np.exp(intercept) * np.power(x, exponent)
    residual = np.log(y) - np.log(curve)
    return {
        "coefficients": np.asarray([exponent, intercept], dtype=np.float64),
        "curve": curve,
        "log_rms_residual": float(np.sqrt(np.mean(residual * residual))),
    }


def entropy_fit_evidence(sizes: np.ndarray, entropy_second: np.ndarray) -> dict[str, Any]:
    """Freeze the linear and logarithmic guides for the same second-scar series."""

    x = np.asarray(sizes, dtype=np.float64)
    y = np.asarray(entropy_second, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape or len(x) < 2:
        raise ValueError("sizes and entropy_second must be equal vectors with >=2 rows")
    linear = np.polyfit(x, y, 1)
    logarithmic = np.polyfit(np.log(x), y, 1)
    return {
        "linear_coefficients": linear,
        "linear_curve": np.polyval(linear, x),
        "log_coefficients": logarithmic,
        "log_curve": np.polyval(logarithmic, np.log(x)),
    }


def perfect_revival_overlap_bound(
    n_sites: int,
    local_norm_bound: float,
    tau: float,
    *,
    alpha: float = 0.0,
) -> dict[str, Any]:
    """Construct the counting/pigeonhole witness behind Supplement Sec. S7.

    From ``||H|| <= N h`` the spectral width is at most ``2 N h``.  Perfect
    revival restricts every occupied energy to ``(alpha + 2*pi*m)/tau``.
    Hence at most ``floor(2*N*h*tau/(2*pi)) + 1`` distinct occupied energies
    fit inside the band, and normalization forces one squared overlap to be at
    least the reciprocal of that count.
    """

    if n_sites < 1 or local_norm_bound <= 0.0 or tau <= 0.0:
        raise ValueError("n_sites, local_norm_bound and tau must be positive")
    half_width = float(n_sites * local_norm_bound)
    spacing = float(2.0 * math.pi / tau)
    max_distinct_energies = int(math.floor((2.0 * half_width) / spacing) + 1)
    m_min = math.ceil((-half_width * tau - alpha) / (2.0 * math.pi))
    m_max = math.floor((half_width * tau - alpha) / (2.0 * math.pi))
    integers = np.arange(m_min, m_max + 1, dtype=np.float64)
    energies = (alpha + 2.0 * math.pi * integers) / tau
    phases = np.exp(-1j * energies * tau)
    expected_phase = np.exp(-1j * alpha)
    phase_alignment_error = float(np.max(np.abs(phases - expected_phase), initial=0.0))
    weights = np.full(len(energies), 1.0 / len(energies), dtype=np.float64)
    overlap_probability_lower_bound = float(1.0 / max_distinct_energies)
    return {
        "n_sites": int(n_sites),
        "local_norm_bound": float(local_norm_bound),
        "tau": float(tau),
        "alpha": float(alpha),
        "operator_norm_bound": half_width,
        "spectral_width_bound": 2.0 * half_width,
        "revival_energy_spacing": spacing,
        "max_distinct_energies": max_distinct_energies,
        "constructed_distinct_energies": int(len(energies)),
        "phase_alignment_error": phase_alignment_error,
        "overlap_probability_lower_bound": overlap_probability_lower_bound,
        "overlap_amplitude_lower_bound": float(math.sqrt(overlap_probability_lower_bound)),
        "uniform_witness_max_probability": float(np.max(weights)),
        "probability_normalization_error": float(abs(np.sum(weights) - 1.0)),
    }
