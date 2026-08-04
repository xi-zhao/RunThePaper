"""Independent audit utilities for PRL-Bench record 088."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize_scalar


@dataclass(frozen=True)
class AngularCoefficients:
    g: float
    ax2: float
    ay2: float
    az2: float
    az4: float
    az6: float
    dg: float
    dax2: float
    day2: float
    daz2: float
    daz4: float
    daz6: float


def angular_coefficients(theta: float, alpha: float = 1.0, lam: float = -2.0) -> AngularCoefficients:
    cos2 = np.cos(2.0 * theta)
    sin2 = np.sin(2.0 * theta)
    cos4 = np.cos(4.0 * theta)
    sin4 = np.sin(4.0 * theta)
    return AngularCoefficients(
        g=1.0 - 3.0 * np.cos(theta) ** 2,
        ax2=-3.0 / 16.0 * (9.0 + 20.0 * cos2 + 35.0 * cos4),
        ay2=3.0 / 16.0 * (-3.0 + 35.0 * cos4),
        az2=3.0 / 4.0 * (3.0 + 5.0 * cos2),
        az4=15.0 / 16.0 * (5.0 + 7.0 * cos2),
        az6=alpha * (1.0 + lam * cos2),
        dg=3.0 * sin2,
        dax2=15.0 / 2.0 * sin2 + 105.0 / 4.0 * sin4,
        day2=-105.0 / 4.0 * sin4,
        daz2=-15.0 / 2.0 * sin2,
        daz4=-105.0 / 8.0 * sin2,
        daz6=-2.0 * alpha * lam * sin2,
    )


def mean_and_variance(
    theta: float,
    beta: float,
    s: float,
    *,
    alpha: float = 1.0,
    lam: float = -2.0,
    closure_as_written: bool = True,
) -> tuple[float, float]:
    """Return the strict mean and variance truncations.

    The prompt states ``Cov(z^2/r^2,R6)=Az2*Az6*Cov/r^8``.  The variance
    therefore receives another factor ``Az2`` from ``Q2``.  Setting
    ``closure_as_written=False`` reproduces the frozen answer's missing factor.
    """

    c = angular_coefficients(theta, alpha, lam)
    mean = (
        c.g
        + s * (c.az2 + beta * (c.ax2 + c.ay2))
        + 3.0 * s**2 * c.az4
        + 15.0 * s**3 * c.az6
    )
    sextic = c.az2**2 * c.az6 if closure_as_written else c.az2 * c.az6
    variance = (
        2.0 * s**2 * (c.az2**2 + beta**2 * (c.ax2**2 + c.ay2**2))
        + 24.0 * s**3 * c.az2 * c.az4
        + (180.0 * sextic + 96.0 * c.az4**2) * s**4
    )
    return mean, variance


def quality_factor(
    theta: float,
    beta: float,
    s: float,
    *,
    alpha: float = 1.0,
    lam: float = -2.0,
    closure_as_written: bool = True,
) -> float:
    mean, variance = mean_and_variance(
        theta, beta, s, alpha=alpha, lam=lam, closure_as_written=closure_as_written
    )
    if variance <= 0.0:
        return float("nan")
    return abs(mean) / np.sqrt(variance)


def global_quality_maximum(
    beta: float,
    s: float,
    *,
    alpha: float = 1.0,
    lam: float = -2.0,
    closure_as_written: bool = True,
    grid_points: int = 100_001,
) -> tuple[float, float, float]:
    """Bracket every grid-resolved peak, refine the best, and report its gap."""

    epsilon = 1e-10
    grid = np.linspace(epsilon, np.pi / 2.0 - epsilon, grid_points)
    values = np.array(
        [
            quality_factor(
                theta,
                beta,
                s,
                alpha=alpha,
                lam=lam,
                closure_as_written=closure_as_written,
            )
            for theta in grid
        ]
    )
    values[~np.isfinite(values)] = -np.inf
    peak_indices = np.flatnonzero((values[1:-1] > values[:-2]) & (values[1:-1] > values[2:])) + 1
    candidates: list[tuple[float, float]] = [
        (grid[0], values[0]),
        (grid[-1], values[-1]),
    ]
    for index in peak_indices:
        result = minimize_scalar(
            lambda theta: -quality_factor(
                theta,
                beta,
                s,
                alpha=alpha,
                lam=lam,
                closure_as_written=closure_as_written,
            ),
            bounds=(grid[index - 1], grid[index + 1]),
            method="bounded",
            options={"xatol": 1e-15},
        )
        candidates.append((float(result.x), float(-result.fun)))
    candidates.sort(key=lambda item: item[1], reverse=True)
    gap = candidates[0][1] - candidates[1][1]
    return candidates[0][0], candidates[0][1], gap


def magic_angle() -> float:
    return 0.5 * np.arccos(-3.0 / 5.0)


def asymptotic_shift_coefficient() -> float:
    """Exact leading coefficient for beta=sqrt(s): 563/100 radians."""

    return 563.0 / 100.0


def scaled_magic_shift(s: float, lam: float) -> float:
    beta = np.sqrt(s)
    theta, _, _ = global_quality_maximum(
        beta, s, lam=lam, closure_as_written=True, grid_points=40_001
    )
    return (theta - magic_angle()) / s


def xy_hamiltonian(size: int, j0: float, j1: float) -> np.ndarray:
    if size < 4 or size % 2:
        raise ValueError("size must be even and at least four")
    matrix = np.zeros((size, size), dtype=np.complex128)
    for site in range(size):
        neighbor = (site + 1) % size
        coupling = (j0 if site % 2 == 0 else j1) / 2.0
        matrix[site, neighbor] += coupling
        matrix[neighbor, site] += coupling
    return matrix


def translated_xy_hamiltonian(size: int, j0: float, j1: float) -> np.ndarray:
    return xy_hamiltonian(size, j1, j0)


def dimerization_norm_factor(size: int) -> float:
    """Return ||H-H'||/|J0-J1| for an even ring."""

    return 1.0 if size % 4 == 0 else float(np.cos(np.pi / size))


def cesaro_error_norm(size: int, m: int, j0: float, j1: float) -> float:
    if m <= 0:
        raise ValueError("m must be positive")
    if m % 2 == 0:
        return 0.0
    return abs(j0 - j1) * dimerization_norm_factor(size) / (2.0 * m)


def floquet_cycle(size: int, m: int, time: float, j0: float, j1: float) -> tuple[np.ndarray, np.ndarray]:
    h = xy_hamiltonian(size, j0, j1)
    hp = translated_xy_hamiltonian(size, j0, j1)
    unitary = np.eye(size, dtype=np.complex128)
    for step in range(m):
        unitary = unitary @ expm(-1j * time * (h if step % 2 == 0 else hp))
    average = (h + hp) / 2.0
    homogenized = expm(-1j * time * m * average)
    return unitary, homogenized


def floquet_error_ratio(size: int, m: int, time: float, j0: float, j1: float) -> float:
    contrast = abs(j0 - j1)
    if contrast == 0.0:
        raise ValueError("j0 and j1 must differ")
    unitary, homogenized = floquet_cycle(size, m, time, j0, j1)
    return float(np.linalg.norm(unitary - homogenized, 2) / contrast)
