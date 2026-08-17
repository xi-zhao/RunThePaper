"""Large-deviation observables derived from a tilted generator."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def cumulants_from_theta(
    theta_function: Callable[[float], float],
    s_values: np.ndarray,
    *,
    derivative_step: float = 1e-4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate theta, k=-theta' and Q=-theta''/theta'-1."""

    if derivative_step <= 0:
        raise ValueError("derivative_step must be positive")
    s_values = np.asarray(s_values, dtype=np.float64)
    theta = np.array([theta_function(float(s)) for s in s_values])
    theta_minus = np.array(
        [theta_function(float(s - derivative_step)) for s in s_values]
    )
    theta_plus = np.array(
        [theta_function(float(s + derivative_step)) for s in s_values]
    )
    first = (theta_plus - theta_minus) / (2.0 * derivative_step)
    second = (theta_plus - 2.0 * theta + theta_minus) / derivative_step**2
    activity = -first
    with np.errstate(divide="ignore", invalid="ignore"):
        mandel = -second / first - 1.0
    return theta, activity, mandel


def rate_function(
    k_values: np.ndarray,
    s_values: np.ndarray,
    theta_values: np.ndarray,
) -> np.ndarray:
    """Legendre-Fenchel dual phi(k)=sup_s[-s*k-theta(s)]."""

    k_values = np.asarray(k_values, dtype=np.float64)
    s_values = np.asarray(s_values, dtype=np.float64)
    theta_values = np.asarray(theta_values, dtype=np.float64)
    if s_values.shape != theta_values.shape or s_values.ndim != 1:
        raise ValueError("s_values and theta_values must be matching vectors")
    return np.max(
        -k_values[:, np.newaxis] * s_values[np.newaxis, :]
        - theta_values[np.newaxis, :],
        axis=1,
    )


def two_level_rate_exact(k_values: np.ndarray, omega: float = 1.0) -> np.ndarray:
    k_values = np.asarray(k_values, dtype=np.float64)
    if np.any(k_values <= 0):
        raise ValueError("k must be positive for the closed-form rate function")
    k0 = 2.0 * omega / 3.0
    return 3.0 * (k_values * np.log(k_values / k0) - (k_values - k0))
