"""Bloch-space equations independently derived from the paper.

The convention follows Supplemental Eqs. (3)-(11), which are also the
equations used by the theory figures.  ``gamma_prime`` always means
``gamma / Omega`` and ``Omega`` defaults to one.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq, minimize_scalar

FloatArray = NDArray[np.float64]


def _require_physical(alpha: float, gamma_prime: ArrayLike) -> FloatArray:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must lie in [0, 1], got {alpha}")
    gamma = np.asarray(gamma_prime, dtype=float)
    if np.any(gamma <= 0.0):
        raise ValueError("gamma_prime must be strictly positive")
    return gamma


def bloch_generator(
    alpha: float, gamma_prime: float, omega: float = 1.0
) -> tuple[FloatArray, FloatArray]:
    """Return ``A, b`` for ``d(y,z)/dt = A(y,z)+b`` (Supplement Eq. 6)."""

    _require_physical(alpha, gamma_prime)
    if omega <= 0.0:
        raise ValueError("omega must be positive")
    gamma = float(gamma_prime) * omega
    matrix = np.array([[-gamma, -omega], [omega, -2.0 * alpha * gamma]], dtype=float)
    offset = np.array([0.0, -2.0 * alpha * gamma], dtype=float)
    return matrix, offset


def steady_state(gamma_prime: ArrayLike, alpha: float) -> FloatArray:
    """Return analytic steady-state Bloch coordinates ``(..., 2)=(y,z)``."""

    gamma = _require_physical(alpha, gamma_prime)
    denominator = 1.0 + 2.0 * alpha * gamma**2
    y = 2.0 * alpha * gamma / denominator
    z = -2.0 * alpha * gamma**2 / denominator
    return np.stack((y, z), axis=-1)


def steady_state_by_solve(
    gamma_prime: float, alpha: float, omega: float = 1.0
) -> FloatArray:
    """Independent affine-linear solve for the steady state."""

    matrix, offset = bloch_generator(alpha, gamma_prime, omega)
    return np.linalg.solve(matrix, -offset)


def relaxation_rates(
    gamma_prime: ArrayLike, alpha: float
) -> dict[str, NDArray[np.complex128]]:
    """Return rates normalized by ``gamma`` using the paper's branch labels.

    ``lambda_plus`` is the fast (more negative) branch above bifurcation and
    ``lambda_minus`` is the slow branch.
    """

    gamma = _require_physical(alpha, gamma_prime)
    discriminant = (alpha - 0.5) ** 2 - 1.0 / gamma**2
    root = np.lib.scimath.sqrt(discriminant).astype(np.complex128)
    common = -(alpha + 0.5)
    shape = gamma.shape
    return {
        "lambda_zero": np.zeros(shape, dtype=np.complex128),
        "lambda_x": -np.ones(shape, dtype=np.complex128),
        "lambda_plus": np.asarray(common - root, dtype=np.complex128),
        "lambda_minus": np.asarray(common + root, dtype=np.complex128),
    }


def bifurcation_temperature(alpha: float) -> float:
    """Return ``gamma'_b=1/|alpha-1/2|`` or infinity at alpha=1/2."""

    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must lie in [0, 1], got {alpha}")
    distance = abs(alpha - 0.5)
    return np.inf if distance == 0.0 else 1.0 / distance


def strong_initial_temperature(alpha: float, gamma_final_prime: float) -> float:
    """Return the strong inverse-Mpemba initial temperature (main text)."""

    _require_physical(alpha, gamma_final_prime)
    radicand = (alpha - 0.5) ** 2 - 1.0 / gamma_final_prime**2
    if alpha <= 0.5 or radicand < 0.0:
        raise ValueError(
            "strong inverse-Mpemba root requires alpha>1/2 above bifurcation"
        )
    return float(gamma_final_prime * ((alpha - 0.5) - np.sqrt(radicand)))


def slow_mode_coefficient(
    gamma_initial_prime: ArrayLike, gamma_final_prime: float, alpha: float
) -> FloatArray:
    """Supplement Eq. (11) for the plotted paper-normalized ``a_-``.

    The absolute scale depends on the paper's eigenvector normalization.  Its
    zero and sign change are the physical invariants used in acceptance tests.
    """

    gamma_i = _require_physical(alpha, gamma_initial_prime)
    _require_physical(alpha, gamma_final_prime)
    radicand = (alpha - 0.5) ** 2 - 1.0 / gamma_final_prime**2
    if radicand <= 0.0:
        raise ValueError(
            "separated slow/fast modes require gamma_final above bifurcation"
        )
    root = np.sqrt(radicand)
    prefactor = (
        alpha
        * (alpha - 0.5)
        / (
            root
            * (2.0 * alpha + 1.0 / gamma_final_prime**2)
            * (2.0 * alpha + 1.0 / gamma_i**2)
        )
        * (gamma_final_prime / gamma_i - 1.0)
    )
    bracket = (
        4.0 * alpha * (alpha - 0.5 + root)
        - 2.0 / (gamma_i * gamma_final_prime) * (alpha + 0.5 + root)
        - 2.0 / gamma_final_prime**2
    )
    return np.asarray(prefactor * bracket, dtype=float)


def modal_coefficients(
    gamma_initial_prime: float, gamma_final_prime: float, alpha: float
) -> dict[str, float]:
    """Independent two-mode decomposition of the initial displacement.

    Numpy's eigenvector normalization differs from Supplemental Eq. (11), so
    only zeros, signs, and reconstructed displacements are compared.
    """

    matrix, _ = bloch_generator(alpha, gamma_final_prime)
    values, vectors = np.linalg.eig(matrix)
    order = np.argsort(values.real)  # fast (more negative), then slow
    values = values[order]
    vectors = vectors[:, order]
    displacement = steady_state(gamma_initial_prime, alpha) - steady_state(
        gamma_final_prime, alpha
    )
    coefficients = np.linalg.solve(vectors, displacement)
    reconstructed = vectors @ coefficients
    if not np.allclose(reconstructed.real, displacement, rtol=1e-12, atol=1e-12):
        raise RuntimeError("modal decomposition failed to reconstruct displacement")
    return {
        "lambda_fast": float(values[0].real),
        "lambda_slow": float(values[1].real),
        "coefficient_fast": float(np.real_if_close(coefficients[0]).real),
        "coefficient_slow": float(np.real_if_close(coefficients[1]).real),
    }


def _modal_trajectory(
    matrix: FloatArray, displacement: FloatArray, times: FloatArray
) -> FloatArray:
    values, vectors = np.linalg.eig(matrix)
    coefficients = np.linalg.solve(vectors, displacement)
    evolved_modes = coefficients[:, None] * np.exp(values[:, None] * times[None, :])
    trajectory = (vectors @ evolved_modes).T
    trajectory = np.real_if_close(trajectory, tol=1000)
    if np.max(np.abs(np.asarray(trajectory).imag)) > 1e-10:
        raise RuntimeError(
            "real Bloch dynamics acquired a non-negligible imaginary component"
        )
    return np.asarray(trajectory.real, dtype=float)


def propagate_bloch(
    times: ArrayLike,
    gamma_initial_prime: float,
    gamma_final_prime: float,
    alpha: float,
    omega: float = 1.0,
) -> FloatArray:
    """Propagate from one steady state after a quench to ``gamma_final``."""

    time_array = np.atleast_1d(np.asarray(times, dtype=float))
    if np.any(time_array < 0.0):
        raise ValueError("times must be non-negative")
    final = steady_state(gamma_final_prime, alpha)
    initial = steady_state(gamma_initial_prime, alpha)
    matrix, _ = bloch_generator(alpha, gamma_final_prime, omega)
    displacement = np.asarray(initial - final, dtype=float)
    return final + _modal_trajectory(matrix, displacement, time_array)


def distance_to_final(
    times: ArrayLike,
    gamma_initial_prime: float,
    gamma_final_prime: float,
    alpha: float,
    omega: float = 1.0,
) -> FloatArray:
    trajectory = propagate_bloch(
        times, gamma_initial_prime, gamma_final_prime, alpha, omega
    )
    final = steady_state(gamma_final_prime, alpha)
    return np.linalg.norm(trajectory - final, axis=1)


@dataclass(frozen=True)
class CrossingMetrics:
    crossing_time: float
    maximal_advantage: float
    maximal_advantage_time: float


def crossing_metrics(
    gamma_initial_cold_prime: float,
    gamma_initial_hot_prime: float,
    gamma_final_prime: float,
    alpha: float,
    *,
    time_upper: float = 2.0,
    bracket_points: int = 2001,
) -> CrossingMetrics:
    """Find first distance crossing and largest later ``d_hot-d_cold``."""

    if not gamma_initial_cold_prime < gamma_initial_hot_prime < gamma_final_prime:
        raise ValueError("expected cold < hot < final temperatures")
    times = np.linspace(0.0, time_upper, bracket_points)
    cold = distance_to_final(times, gamma_initial_cold_prime, gamma_final_prime, alpha)
    hot = distance_to_final(times, gamma_initial_hot_prime, gamma_final_prime, alpha)
    difference = cold - hot
    crossing_indices = np.flatnonzero(difference[:-1] * difference[1:] < 0.0)
    if crossing_indices.size == 0:
        raise RuntimeError("no nontrivial distance crossing found in bracket")
    index = int(crossing_indices[0])

    def signed_difference(time: float) -> float:
        dc = distance_to_final(
            [time], gamma_initial_cold_prime, gamma_final_prime, alpha
        )[0]
        dh = distance_to_final(
            [time], gamma_initial_hot_prime, gamma_final_prime, alpha
        )[0]
        return float(dc - dh)

    crossing = brentq(
        signed_difference, float(times[index]), float(times[index + 1]), xtol=1e-13
    )

    result = minimize_scalar(
        signed_difference,
        bounds=(crossing, time_upper),
        method="bounded",
        options={"xatol": 1e-12},
    )
    if not result.success:
        raise RuntimeError(f"post-crossing maximization failed: {result.message}")
    return CrossingMetrics(
        crossing_time=float(crossing),
        maximal_advantage=float(-result.fun),
        maximal_advantage_time=float(result.x),
    )


def preparation_parameters(
    gamma_prime: ArrayLike, alpha: float
) -> tuple[FloatArray, FloatArray]:
    """Return the printed Bloch radius ``p`` and angle ``theta``."""

    gamma = _require_physical(alpha, gamma_prime)
    state = steady_state(gamma, alpha)
    p = np.linalg.norm(state, axis=-1)
    theta = -np.arctan(gamma)
    return np.asarray(p, dtype=float), np.asarray(theta, dtype=float)
