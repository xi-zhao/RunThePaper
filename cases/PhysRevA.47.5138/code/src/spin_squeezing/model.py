"""Exact collective-spin model derived from Phys. Rev. A 47, 5138 (1993)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize_scalar
from scipy.special import gammaln


@dataclass(frozen=True)
class MinimumResult:
    """A first physical squeezing minimum and its numerical diagnostics."""

    spin: float
    mu: float
    variance: float
    boundary_hit: bool
    coarse_spacing: float


def _two_spin(spin: float) -> int:
    value = int(round(2.0 * float(spin)))
    if value < 1 or not np.isclose(value, 2.0 * float(spin), atol=1e-12):
        raise ValueError("spin must be a positive integer or half-integer")
    return value


def magnetic_numbers(spin: float) -> np.ndarray:
    """Return m=-S,...,S in the basis used throughout the case."""

    two_spin = _two_spin(spin)
    return np.arange(-two_spin, two_spin + 1, 2, dtype=float) / 2.0


def spin_operators(
    spin: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return m, S+, S-, Sx, Sy and Sz for a finite spin S."""

    m = magnetic_numbers(spin)
    dimension = len(m)
    raising = np.zeros((dimension, dimension), dtype=complex)
    for column, value in enumerate(m[:-1]):
        raising[column + 1, column] = np.sqrt(
            spin * (spin + 1.0) - value * (value + 1.0)
        )
    lowering = raising.conj().T
    sx = 0.5 * (raising + lowering)
    sy = (raising - lowering) / (2.0j)
    sz = np.diag(m).astype(complex)
    return m, raising, lowering, sx, sy, sz


def coherent_state(spin: float, theta: float, phi: float) -> np.ndarray:
    """Construct the normalized spin coherent state printed in the Appendix."""

    two_spin = _two_spin(spin)
    m = magnetic_numbers(spin)
    k_up = np.rint(spin + m).astype(int)
    log_binomial = (
        gammaln(two_spin + 1) - gammaln(k_up + 1) - gammaln(two_spin - k_up + 1)
    )
    amplitudes = (
        np.exp(0.5 * log_binomial)
        * np.cos(theta / 2.0) ** (spin + m)
        * np.sin(theta / 2.0) ** (spin - m)
        * np.exp(-1.0j * m * phi)
    )
    norm = np.linalg.norm(amplitudes)
    if norm == 0.0:
        raise FloatingPointError("coherent-state construction produced zero norm")
    return amplitudes / norm


def one_axis_state(spin: float, mu: float) -> np.ndarray:
    """Apply U=exp(-i mu Sz^2/2) to the x-polarized coherent state."""

    m = magnetic_numbers(spin)
    initial = coherent_state(spin, np.pi / 2.0, 0.0)
    return initial * np.exp(-0.5j * float(mu) * m * m)


def two_axis_generator(spin: float) -> np.ndarray:
    """Return K=Sx Sy+Sy Sx from the paper's +/-45 degree axes."""

    _, _, _, sx, sy, _ = spin_operators(spin)
    return sx @ sy + sy @ sx


def two_axis_ladder_generator(spin: float) -> np.ndarray:
    """Return Eq. (6) in its independent ladder-operator representation."""

    _, raising, lowering, _, _, _ = spin_operators(spin)
    return (raising @ raising - lowering @ lowering) / (2.0j)


def two_axis_eigensystem(
    spin: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Diagonalize the Hermitian countertwisting generator once."""

    generator = two_axis_generator(spin)
    eigenvalues, eigenvectors = eigh(generator)
    initial = coherent_state(spin, 0.0, 0.0)
    coefficients = eigenvectors.conj().T @ initial
    return eigenvalues, eigenvectors, coefficients


def state_from_two_axis_eigensystem(
    mu: float,
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    coefficients: np.ndarray,
) -> np.ndarray:
    phases = np.exp(-0.25j * float(mu) * eigenvalues)
    return eigenvectors @ (phases * coefficients)


def two_axis_state(spin: float, mu: float) -> np.ndarray:
    """Apply the exact TACT unitary to the north-pole coherent state."""

    return state_from_two_axis_eigensystem(mu, *two_axis_eigensystem(spin))


def _coherent_amplitude_table(spin: float, theta: np.ndarray) -> np.ndarray:
    two_spin = _two_spin(spin)
    m = magnetic_numbers(spin)
    k_up = np.rint(spin + m).astype(int)
    log_binomial = (
        gammaln(two_spin + 1) - gammaln(k_up + 1) - gammaln(two_spin - k_up + 1)
    )
    return (
        np.exp(0.5 * log_binomial)[None, :]
        * np.cos(theta[:, None] / 2.0) ** (spin + m[None, :])
        * np.sin(theta[:, None] / 2.0) ** (spin - m[None, :])
    )


def husimi_q(
    state: np.ndarray,
    spin: float,
    theta: np.ndarray,
    phi: np.ndarray,
) -> np.ndarray:
    """Evaluate Q(theta,phi)=|<theta,phi|state>|^2 on a product grid."""

    state = np.asarray(state, dtype=complex)
    if state.shape != (_two_spin(spin) + 1,):
        raise ValueError("state dimension does not match spin")
    theta = np.asarray(theta, dtype=float)
    phi = np.asarray(phi, dtype=float)
    m = magnetic_numbers(spin)
    radial = _coherent_amplitude_table(spin, theta)
    phase = np.exp(1.0j * phi[:, None] * m[None, :])
    overlaps = np.einsum("tm,pm,m->tp", radial, phase, state, optimize=True)
    q = np.abs(overlaps) ** 2
    return np.clip(q.real, 0.0, 1.0 + 32.0 * np.finfo(float).eps)


def expectation(state: np.ndarray, operator: np.ndarray) -> complex:
    return complex(np.vdot(state, operator @ state))


def covariance_element(
    state: np.ndarray, first: np.ndarray, second: np.ndarray
) -> float:
    first_mean = expectation(state, first)
    second_mean = expectation(state, second)
    symmetric = 0.5 * (first @ second + second @ first)
    return float((expectation(state, symmetric) - first_mean * second_mean).real)


def minimum_transverse_variance(
    state: np.ndarray, first: np.ndarray, second: np.ndarray
) -> float:
    """Return the smaller eigenvalue of a two-axis symmetric covariance."""

    c11 = covariance_element(state, first, first)
    c22 = covariance_element(state, second, second)
    c12 = covariance_element(state, first, second)
    discriminant = np.sqrt(max(0.0, (c11 - c22) ** 2 + 4.0 * c12 * c12))
    return 0.5 * (c11 + c22 - discriminant)


def one_axis_variances(spin: float, mu: float) -> tuple[float, float]:
    """Evaluate the exact smaller/larger variances in paper Eq. (4)."""

    if spin <= 0.5:
        raise ValueError("one-axis squeezing needs S>1/2")
    cosine = np.cos(float(mu))
    half_cosine = np.cos(float(mu) / 2.0)
    a_value = 1.0 - cosine ** int(round(2.0 * spin - 2.0))
    b_value = (
        4.0 * np.sin(float(mu) / 2.0) * half_cosine ** int(round(2.0 * spin - 2.0))
    )
    radius = np.hypot(a_value, b_value)
    coefficient = 0.5 * (spin - 0.5)
    prefactor = 0.5 * spin
    return (
        float(prefactor * (1.0 + coefficient * (a_value - radius))),
        float(prefactor * (1.0 + coefficient * (a_value + radius))),
    )


def one_axis_mean_spin(spin: float, mu: float) -> float:
    """Return the exact mean spin along x following Appendix Eq. (A1)."""

    _two_spin(spin)
    return float(spin * np.cos(float(mu) / 2.0) ** int(round(2.0 * spin - 1.0)))


def one_axis_uncertainty_product(spin: float, mu: float) -> float:
    """Return the normalized OAT uncertainty product printed below Eq. (5)."""

    smaller, larger = one_axis_variances(spin, mu)
    mean_spin = one_axis_mean_spin(spin, mu)
    if abs(mean_spin) <= np.finfo(float).tiny:
        return float("inf")
    return float(4.0 * smaller * larger / (mean_spin * mean_spin))


def twisted_moment_identity_residuals(spin: float, mu: float) -> dict[str, float]:
    """Independently contract Appendix Eqs. (A1)-(A3) and return residuals."""

    m, raising, _, _, _, sz = spin_operators(spin)
    state = coherent_state(spin, np.pi / 2.0, 0.0)
    identity = np.eye(len(m), dtype=complex)
    phase = np.diag(np.exp(1.0j * float(mu) * (m + 0.5)))
    twisted_raising = raising @ phase
    lhs_a1 = expectation(state, twisted_raising)
    rhs_a1 = spin * np.cos(float(mu) / 2.0) ** int(round(2.0 * spin - 1.0))
    lhs_a2 = expectation(state, twisted_raising @ twisted_raising)
    rhs_a2 = spin * (spin - 0.5) * np.cos(float(mu)) ** int(round(2.0 * spin - 2.0))
    lhs_a3 = expectation(state, 1.0j * twisted_raising @ (sz + 0.5 * identity))
    rhs_a3 = (
        -spin
        * (spin - 0.5)
        * np.cos(float(mu) / 2.0) ** int(round(2.0 * spin - 2.0))
        * np.sin(float(mu) / 2.0)
    )
    return {
        "A1": float(abs(lhs_a1 - rhs_a1)),
        "A2": float(abs(lhs_a2 - rhs_a2)),
        "A3": float(abs(lhs_a3 - rhs_a3)),
    }


def schwinger_spin_operators(
    total_particles: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return the fixed-N two-mode operators in paper Eq. (7).

    The basis is ordered by n_A=0,...,N, so S_z=(N_A-N_B)/2 and
    S_+=a^dagger b.  This construction is independent of the abstract-spin
    ladder formula used by :func:`spin_operators`.
    """

    if int(total_particles) != total_particles or total_particles < 1:
        raise ValueError("total_particles must be a positive integer")
    particle_count = int(total_particles)
    dimension = particle_count + 1
    raising = np.zeros((dimension, dimension), dtype=complex)
    for n_a in range(particle_count):
        n_b = particle_count - n_a
        raising[n_a + 1, n_a] = np.sqrt((n_a + 1) * n_b)
    lowering = raising.conj().T
    sx = 0.5 * (raising + lowering)
    sy = (raising - lowering) / (2.0j)
    n_a_values = np.arange(dimension, dtype=float)
    sz = np.diag(n_a_values - 0.5 * particle_count).astype(complex)
    return raising, sx, sy, sz


def minimum_one_axis_variance(
    spin: float, *, mu_max: float = 1.5, tolerance: float = 1e-11
) -> MinimumResult:
    """Minimize the exact OAT expression over its first physical lobe."""

    result = minimize_scalar(
        lambda value: one_axis_variances(spin, value)[0],
        method="bounded",
        bounds=(0.0, float(mu_max)),
        options={"xatol": tolerance},
    )
    return MinimumResult(
        spin=float(spin),
        mu=float(result.x),
        variance=float(result.fun),
        boundary_hit=bool(
            result.x < 10.0 * tolerance or mu_max - result.x < 10.0 * tolerance
        ),
        coarse_spacing=float("nan"),
    )


def minimum_two_axis_variance(
    spin: float,
    *,
    mu_max: float = 1.5,
    coarse_points: int = 241,
    tolerance: float = 1e-11,
) -> MinimumResult:
    """Find the first TACT squeezing minimum before the distribution re-expands."""

    if coarse_points < 5:
        raise ValueError("coarse_points must be at least 5")
    _, _, _, sx, sy, _ = spin_operators(spin)
    eigensystem = two_axis_eigensystem(spin)

    def objective(value: float) -> float:
        state = state_from_two_axis_eigensystem(value, *eigensystem)
        return minimum_transverse_variance(state, sx, sy)

    grid = np.linspace(0.0, float(mu_max), int(coarse_points))
    values = np.asarray([objective(value) for value in grid])
    local = (
        np.flatnonzero((values[1:-1] <= values[:-2]) & (values[1:-1] < values[2:])) + 1
    )
    index = int(local[0]) if len(local) else int(np.argmin(values))
    lower = grid[max(0, index - 1)]
    upper = grid[min(len(grid) - 1, index + 1)]
    result = minimize_scalar(
        objective,
        method="bounded",
        bounds=(float(lower), float(upper)),
        options={"xatol": tolerance},
    )
    return MinimumResult(
        spin=float(spin),
        mu=float(result.x),
        variance=float(result.fun),
        boundary_hit=bool(index in {0, len(grid) - 1}),
        coarse_spacing=float(grid[1] - grid[0]),
    )
