"""Exact transfer-matrix contraction transcribed from the published equations.

This module deliberately has no file I/O.  It accepts only scalar physical
parameters and creates all scientific arrays from the paper's MPO amplitudes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ScaledVector:
    values: np.ndarray
    log_scale: float


@dataclass(frozen=True)
class SignedLogScalar:
    sign: float
    log_abs: float


def auxiliary_dimension(size: int, delta: float) -> int:
    """Exact dimension needed by a length-``size`` return path.

    A path beginning and ending at auxiliary state zero cannot exceed
    ``floor(size / 2)``.  At Delta=1/2 the root-of-unity process additionally
    closes after auxiliary state two.
    """

    if size < 1:
        raise ValueError("size must be positive")
    dimension = size // 2 + 1
    if np.isclose(delta, 0.5, atol=1e-14, rtol=0.0):
        dimension = min(dimension, 3)
    return dimension


def auxiliary_amplitudes(
    delta: float, epsilon: float, dimension: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``a0, a_plus, a_minus`` from Eqs. (6)-(7).

    The isotropic point uses the regularized amplitudes printed after Main
    Figure 2.  For other anisotropies, the arbitrary gauge is fixed to ``c=1``
    and the paper's stable sign prescription is used.
    """

    if dimension < 1:
        raise ValueError("dimension must be positive")
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")

    a0 = np.zeros(dimension, dtype=np.complex128)
    a_plus = np.zeros(dimension, dtype=np.complex128)
    a_minus = np.zeros(dimension, dtype=np.complex128)
    a0[0] = 1.0
    a_plus[0] = 1j * epsilon
    a_minus[0] = 1.0

    if np.isclose(delta, 1.0, atol=1e-14, rtol=0.0):
        for r in range(1, dimension):
            a0[r] = 1.0 + 0.5j * epsilon * r
            if r % 2:
                k = (r + 1) // 2
                a_plus[r] = 2.0 * k + 1j * epsilon * k * (k - 0.5)
                a_minus[r] = 1j * epsilon
            else:
                k = r // 2
                a_plus[r] = 2.0 * k + 1j * epsilon * k * k
                a_minus[r] = 1j * epsilon * (k + 0.5) / k
        return a0, a_plus, a_minus

    lam = np.arccos(complex(delta))
    sin_lam = np.sin(lam)
    if abs(sin_lam) < 1e-14:
        raise ValueError("singular anisotropy requires a separately derived limit")

    for r in range(1, dimension):
        a0[r] = np.cos(r * lam) + 1j * epsilon * np.sin(r * lam) / (2.0 * sin_lam)
        tau = 1.0 if np.real(np.cos(r * lam)) >= 0.0 else -1.0
        if r % 2:
            k = (r + 1) // 2
            denominator = 2.0 * (np.cos(r * lam) + tau) * sin_lam
            a_plus[r] = np.sin(2 * k * lam) + (
                1j
                * epsilon
                * np.sin(r * lam)
                * np.sin(2 * k * lam)
                / denominator
            )
            a_minus[r] = -np.sin(r * lam) + (
                1j * epsilon * (np.cos(r * lam) + tau) / (2.0 * sin_lam)
            )
        else:
            k = r // 2
            denominator = 2.0 * (np.cos(r * lam) + tau) * sin_lam
            a_plus[r] = np.sin(r * lam) - (
                1j * epsilon * (np.cos(r * lam) + tau) / (2.0 * sin_lam)
            )
            a_minus[r] = -np.sin((2 * k + 1) * lam) - (
                1j
                * epsilon
                * np.sin(r * lam)
                * np.sin((2 * k + 1) * lam)
                / denominator
            )
    return a0, a_plus, a_minus


def transfer_operators(
    delta: float, epsilon: float, size: int
) -> tuple[np.ndarray, np.ndarray]:
    """Build the finite exact transfer matrix ``T`` and vertex ``V``."""

    dimension = auxiliary_dimension(size, delta)
    a0, a_plus, a_minus = auxiliary_amplitudes(delta, epsilon, dimension)
    transfer = np.diag(np.abs(a0) ** 2).astype(np.float64)
    vertex = np.zeros((dimension, dimension), dtype=np.float64)
    for r in range(dimension - 1):
        hop_plus = float(abs(a_plus[r]) ** 2 / 2.0)
        hop_minus = float(abs(a_minus[r]) ** 2 / 2.0)
        transfer[r, r + 1] = hop_plus
        transfer[r + 1, r] = hop_minus
        vertex[r, r + 1] = hop_plus
        vertex[r + 1, r] = -hop_minus
    return transfer, vertex


def _normalized(values: np.ndarray, log_scale: float) -> ScaledVector:
    scale = float(np.max(np.abs(values)))
    if not np.isfinite(scale) or scale == 0.0:
        raise FloatingPointError("transfer contraction produced a zero or nonfinite scale")
    return ScaledVector(values / scale, log_scale + float(np.log(scale)))


def scaled_power_vector(
    transfer: np.ndarray, exponent: int, *, transpose: bool = False
) -> ScaledVector:
    """Evaluate ``T**exponent |0>`` with stepwise rescaling."""

    if exponent < 0:
        raise ValueError("exponent must be nonnegative")
    values = np.zeros(transfer.shape[0], dtype=np.float64)
    values[0] = 1.0
    state = ScaledVector(values, 0.0)
    operator = transfer.T if transpose else transfer
    for _ in range(exponent):
        state = _normalized(operator @ state.values, state.log_scale)
    return state


def _contract_sequence(operators: list[np.ndarray]) -> SignedLogScalar:
    """Contract ``<0| O_1 ... O_n |0>`` without unreachable states.

    A state at auxiliary height ``r`` after ``k`` operators can contribute to
    the final return only when ``r <= min(k, n-k)``.  Removing the other states
    is exact, and is essential in the easy-axis regime: exponentially large
    paths that cannot return would otherwise dominate a generic vector norm
    and erase the physically relevant component through floating underflow.
    """

    if not operators:
        return SignedLogScalar(1.0, 0.0)
    dimension = operators[0].shape[0]
    if any(operator.shape != (dimension, dimension) for operator in operators):
        raise ValueError("all operators must have a shared square dimension")
    values = np.zeros(dimension, dtype=np.float64)
    values[0] = 1.0
    log_scale = 0.0
    total = len(operators)
    bands: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for operator in operators:
        bands.setdefault(
            id(operator),
            (np.diag(operator), np.diag(operator, 1), np.diag(operator, -1)),
        )
    for completed, operator in enumerate(reversed(operators), start=1):
        reachable_height = min(completed, total - completed, dimension - 1)
        # T and V are tridiagonal.  Applying only their three populated bands
        # keeps the paper's O(n^2) arithmetic contract visible at n=400 rather
        # than paying for dense zeros.
        updated = np.zeros_like(values)
        active_stop = min(reachable_height + 2, dimension)
        diagonal, upper, lower = bands[id(operator)]
        updated[:active_stop] = diagonal[:active_stop] * values[:active_stop]
        if active_stop > 1:
            updated[: active_stop - 1] += (
                upper[: active_stop - 1] * values[1:active_stop]
            )
            updated[1:active_stop] += (
                lower[: active_stop - 1] * values[: active_stop - 1]
            )
        values = updated
        values[reachable_height + 1 :] = 0.0
        scale = float(np.max(np.abs(values[: reachable_height + 1])))
        if scale == 0.0:
            return SignedLogScalar(0.0, float("-inf"))
        if not np.isfinite(scale):
            raise FloatingPointError("operator contraction vanished or became nonfinite")
        values /= scale
        log_scale += float(np.log(scale))
    scalar = float(values[0])
    if scalar == 0.0 or not np.isfinite(scalar):
        raise FloatingPointError("final contraction vanished or became nonfinite")
    return SignedLogScalar(float(np.sign(scalar)), float(np.log(abs(scalar)) + log_scale))


def _ratio(numerator: SignedLogScalar, denominator: SignedLogScalar) -> float:
    if numerator.sign == 0.0:
        return 0.0
    if denominator.sign == 0.0:
        raise ZeroDivisionError("zero denominator contraction")
    return float(
        numerator.sign
        * denominator.sign
        * np.exp(numerator.log_abs - denominator.log_abs)
    )


def spin_profile(delta: float, epsilon: float, size: int) -> np.ndarray:
    """Return all ``<sigma_j^z>`` using Eq. (15)."""

    transfer, vertex = transfer_operators(delta, epsilon, size)
    partition = _contract_sequence([transfer] * size)
    if partition.sign <= 0.0:
        raise FloatingPointError("partition contraction must be positive")
    profile = np.empty(size, dtype=np.float64)
    for j in range(1, size + 1):
        numerator = _contract_sequence(
            [transfer] * (j - 1) + [vertex] + [transfer] * (size - j)
        )
        profile[j - 1] = _ratio(numerator, partition)
    return profile


def spin_current(delta: float, epsilon: float, size: int) -> float:
    """Return the conserved current from the exact norm ratio."""

    if size < 2:
        raise ValueError("current requires at least two sites")
    transfer, _ = transfer_operators(delta, epsilon, size)
    partition_n = _contract_sequence([transfer] * size)
    partition_previous = _contract_sequence([transfer] * (size - 1))
    return float(0.5 * epsilon * _ratio(partition_previous, partition_n))


def connected_correlation(
    delta: float, epsilon: float, size: int, site_j: int, site_k: int
) -> float:
    """Return the connected ``sigma^z`` correlation for ``site_j < site_k``."""

    if not 1 <= site_j < site_k <= size:
        raise ValueError("sites must satisfy 1 <= site_j < site_k <= size")
    transfer, vertex = transfer_operators(delta, epsilon, size)
    partition = _contract_sequence([transfer] * size)
    numerator = _contract_sequence(
        [transfer] * (site_j - 1)
        + [vertex]
        + [transfer] * (site_k - site_j - 1)
        + [vertex]
        + [transfer] * (size - site_k)
    )
    two_point = _ratio(numerator, partition)
    profile = spin_profile(delta, epsilon, size)
    return float(two_point - profile[site_j - 1] * profile[site_k - 1])


def correlation_kernel(x: float, y: float) -> float:
    """Printed leading isotropic kernel ``f(min(x,y), max(x,y))``."""

    x0, y0 = sorted((float(x), float(y)))
    return float(
        2.0
        * np.pi
        * x0
        * (y0 - 1.0)
        * np.sin(np.pi * x0)
        * np.sin(np.pi * y0)
        + np.cos(np.pi * x0)
        * (
            (1.0 - 2.0 * y0) * np.sin(np.pi * y0)
            + np.pi * (y0 - 1.0) * y0 * np.cos(np.pi * y0)
        )
    )


def correlation_asymptote(x: float, y: float, size: int) -> float:
    return float(np.pi * correlation_kernel(x, y) / (4.0 * size))


def easy_plane_current_limit(epsilon: np.ndarray | float) -> np.ndarray | float:
    """Closed thermodynamic current for Delta=1/2."""

    value = np.asarray(epsilon, dtype=np.float64)
    result = (
        value
        * (np.sqrt(81.0 + 74.0 * value**2 + 9.0 * value**4) - 7.0 - 3.0 * value**2)
        / (4.0 * (1.0 + value**2))
    )
    if np.ndim(value) == 0:
        return float(result)
    return result


def isotropic_profile_asymptote(size: int) -> np.ndarray:
    x = np.arange(size, dtype=np.float64) / (size - 1)
    return np.cos(np.pi * x)


def isotropic_current_asymptote(epsilon: float, size: np.ndarray | int) -> np.ndarray:
    values = np.asarray(size, dtype=np.float64)
    return np.pi**2 / (epsilon * values**2)


def easy_axis_decay_fit(sizes: np.ndarray, currents: np.ndarray) -> dict[str, float]:
    """Fit the source-independent slope of log current versus size."""

    x = np.asarray(sizes, dtype=np.float64)
    y = np.asarray(currents, dtype=np.float64)
    if np.any(y <= 0.0):
        raise ValueError("currents must be positive")
    slope, intercept = np.polyfit(x, np.log(y), 1)
    prediction = slope * x + intercept
    residual = np.log(y) - prediction
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((np.log(y) - np.mean(np.log(y))) ** 2))
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(1.0 - ss_res / ss_tot),
    }
