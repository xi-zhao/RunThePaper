"""Damped Jaynes--Cummings formulas derived independently from the paper.

The scientific generator uses only printed equations and parameters.  In
particular, it never reads a source figure.  The survival amplitude is written
with a regularized ``sinh(z)/z`` so the critical point ``gamma0=lambda/2`` is
well conditioned and the non-Markovian regime is evaluated without integrating
the singular time-local decay rate through its poles.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def _sinhc(value: np.ndarray | complex) -> np.ndarray:
    z = np.asarray(value, dtype=complex)
    out = np.empty_like(z)
    small = np.abs(z) < 1.0e-7
    z2 = z[small] * z[small]
    out[small] = 1.0 + z2 / 6.0 + z2 * z2 / 120.0
    out[~small] = np.sinh(z[~small]) / z[~small]
    return out


def survival_amplitude(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return the exact excited-state amplitude G(t).

    It solves ``G'' + lambda G' + gamma0*lambda*G/2 = 0`` with
    ``G(0)=1`` and ``G'(0)=0``.
    """

    if gamma0 < 0.0 or spectral_width <= 0.0:
        raise ValueError("gamma0 must be nonnegative and spectral_width positive")
    t = np.asarray(time, dtype=float)
    d = np.sqrt(complex(spectral_width**2 - 2.0 * gamma0 * spectral_width))
    z = d * t / 2.0
    value = np.exp(-spectral_width * t / 2.0) * (
        np.cosh(z) + spectral_width * t * _sinhc(z) / 2.0
    )
    return np.real_if_close(value, tol=1000)


def survival_amplitude_derivative(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return dG/dt in a form regular at the critical coupling."""

    if gamma0 < 0.0 or spectral_width <= 0.0:
        raise ValueError("gamma0 must be nonnegative and spectral_width positive")
    t = np.asarray(time, dtype=float)
    d = np.sqrt(complex(spectral_width**2 - 2.0 * gamma0 * spectral_width))
    z = d * t / 2.0
    value = (
        -gamma0
        * spectral_width
        * t
        * np.exp(-spectral_width * t / 2.0)
        * _sinhc(z)
        / 2.0
    )
    return np.real_if_close(value, tol=1000)


def survival_probability(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    amplitude = survival_amplitude(time, gamma0, spectral_width)
    return np.abs(amplitude) ** 2


def population_derivative(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    amplitude = survival_amplitude(time, gamma0, spectral_width)
    derivative = survival_amplitude_derivative(time, gamma0, spectral_width)
    return 2.0 * np.real(np.conjugate(amplitude) * derivative)


def decay_rate(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return the time-local rate away from zeros of the amplitude."""

    amplitude = survival_amplitude(time, gamma0, spectral_width)
    derivative = survival_amplitude_derivative(time, gamma0, spectral_width)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.real(-2.0 * derivative / amplitude)


def density_derivative(time: float, gamma0: float, spectral_width: float) -> np.ndarray:
    derivative = float(population_derivative(time, gamma0, spectral_width))
    return np.diag([derivative, -derivative])


def averaged_norms(
    gamma0: float,
    spectral_width: float,
    duration: float,
    *,
    integration_points: int,
) -> dict[str, float]:
    """Time-average the three Schatten norms of dot(rho)."""

    if duration <= 0.0 or integration_points < 3:
        raise ValueError("duration and integration_points must be positive")
    time = np.linspace(0.0, duration, integration_points)
    speed = np.abs(population_derivative(time, gamma0, spectral_width))
    total_variation = float(np.trapezoid(speed, time))
    operator = total_variation / duration
    return {
        "operator": operator,
        "hilbert_schmidt": np.sqrt(2.0) * operator,
        "trace": 2.0 * operator,
        "total_variation": total_variation,
    }


def markovian_averaged_norms(gamma0: float, duration: float) -> dict[str, float]:
    if gamma0 < 0.0 or duration <= 0.0:
        raise ValueError("gamma0 must be nonnegative and duration positive")
    operator = -np.expm1(-gamma0 * duration) / duration
    return {
        "operator": float(operator),
        "hilbert_schmidt": float(np.sqrt(2.0) * operator),
        "trace": float(2.0 * operator),
    }


def qsl_bounds(
    gamma0: float,
    spectral_width: float,
    duration: float,
    *,
    integration_points: int,
) -> dict[str, float]:
    """Return Eq. (21) resolved into operator/HS/trace contributions."""

    probability = float(survival_probability(duration, gamma0, spectral_width))
    numerator = max(0.0, 1.0 - probability)
    norms = averaged_norms(
        gamma0, spectral_width, duration, integration_points=integration_points
    )
    if gamma0 == 0.0:
        # Continuous gamma0 -> 0+ limit.  The state is stationary exactly at
        # zero coupling, so a 0/0 ratio has no operational QSL value.
        operator = duration
    else:
        operator = numerator / norms["operator"]
    return {
        "operator": float(operator),
        "hilbert_schmidt": float(operator / np.sqrt(2.0)),
        "trace": float(operator / 2.0),
        "survival_probability": probability,
        "total_variation": norms["total_variation"],
    }


def fidelity_amplitude(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return cos(Bures angle)=sqrt(<e|rho(t)|e>)=|G(t)|."""

    return np.sqrt(survival_probability(time, gamma0, spectral_width))


def pseudomode_survival_amplitude(
    time: np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Independent Markovian-embedding integration of the Lorentzian bath."""

    grid = np.asarray(time, dtype=float)
    if grid.ndim != 1 or len(grid) < 2 or np.any(np.diff(grid) <= 0.0):
        raise ValueError("time must be a strictly increasing one-dimensional grid")
    coupling = np.sqrt(gamma0 * spectral_width / 2.0)

    def rhs(_: float, state: np.ndarray) -> np.ndarray:
        excited, cavity = state
        return np.array(
            [
                -1.0j * coupling * cavity,
                -spectral_width * cavity - 1.0j * coupling * excited,
            ],
            dtype=complex,
        )

    result = solve_ivp(
        rhs,
        (float(grid[0]), float(grid[-1])),
        np.array([1.0 + 0.0j, 0.0 + 0.0j]),
        t_eval=grid,
        rtol=2.0e-11,
        atol=2.0e-13,
        method="DOP853",
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result.y[0]
