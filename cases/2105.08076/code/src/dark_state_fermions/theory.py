"""Independent replica/dark-state calculations from the printed formulas."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import quad, solve_ivp

FloatArray = NDArray[np.float64]


def dark_state_exponents(exponent: float) -> tuple[float, float]:
    """Return `(a,b)` from Main Eqs. (9)-(10)."""

    if not 1.0 < exponent < 1.5:
        raise ValueError("dark-state algebraic exponents require 1 < p < 3/2")
    a = exponent + 0.5
    b = 1.5 - exponent
    return float(a), float(b)


def infrared_kernel(exponent: float, q: float) -> float:
    """Evaluate Supplement Eq. (12) without a source curve.

    The oscillatory integral is transformed to the dimensionless variable
    `s=q y`; an analytic tail average controls the infinite interval.
    """

    if exponent <= 1.0:
        raise ValueError("p must exceed one")
    if q <= 0.0:
        raise ValueError("q must be positive")
    # Directly integrate in y up to a q-dependent oscillatory cutoff.  Beyond
    # that point sin^2 averages to 1/2; the neglected oscillatory tail is below
    # the convergence tolerance for the q ranges used by this case.
    cutoff = max(200.0, 80.0 * np.pi / q)
    value, _ = quad(
        lambda y: np.sin(0.5 * q * y) ** 2 / y ** (2.0 * exponent),
        1.0,
        cutoff,
        epsabs=1e-10,
        epsrel=2e-8,
        limit=1000,
    )
    tail_average = 0.5 * cutoff ** (1.0 - 2.0 * exponent) / (2.0 * exponent - 1.0)
    return float(value + tail_average)


def kernel_log_slope(exponent: float, q_values: FloatArray) -> float:
    q = np.asarray(q_values, dtype=float)
    values = np.asarray([infrared_kernel(exponent, value) for value in q], dtype=float)
    slope, _ = np.polyfit(np.log(q), np.log(values), 1)
    return float(slope)


def dark_state_covariance(
    q_values: FloatArray,
    *,
    exponent: float,
    delta_p: float = 1.0,
    eta_abs: float = 1.0,
) -> FloatArray:
    """Leading covariance from Supplement Eq. (19)."""

    if delta_p <= 0 or eta_abs <= 0:
        raise ValueError("delta_p and eta_abs must be positive")
    q = np.asarray(q_values, dtype=float)
    if np.any(q <= 0):
        raise ValueError("all q values must be positive")
    prefactor = 1.5 * np.pi * np.sqrt(delta_p / eta_abs)
    return np.asarray(prefactor * q ** (exponent - 2.5), dtype=float)


def integrate_rg(
    *,
    exponent: float,
    eta0: float,
    delta0: float,
    scale_max: float = 8.0,
    points: int = 201,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Integrate Main Eqs. (6)-(7) as a real flow-direction diagnostic."""

    if eta0 < 0 or delta0 <= 0 or scale_max <= 0:
        raise ValueError("invalid RG initial condition")

    def rhs(_scale: float, state: FloatArray) -> FloatArray:
        delta, eta = state
        return np.asarray(
            [(3.0 - 2.0 * exponent - eta) * delta, -(eta**2) * delta],
            dtype=float,
        )

    scale = np.linspace(0.0, scale_max, points)
    solution = solve_ivp(
        rhs,
        (0.0, scale_max),
        np.asarray([delta0, eta0], dtype=float),
        t_eval=scale,
        rtol=1e-9,
        atol=1e-11,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return scale, solution.y[0], solution.y[1]
