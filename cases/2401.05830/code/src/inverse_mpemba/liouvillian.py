"""Independent density-matrix realization used to cross-check Bloch dynamics."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm

ComplexArray = NDArray[np.complex128]

IDENTITY = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_MINUS = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=complex)
PROJECTOR_UP = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)


def _dissipator_superoperator(collapse: ComplexArray) -> ComplexArray:
    product = collapse.conj().T @ collapse
    return (
        np.kron(collapse.conj(), collapse)
        - 0.5 * np.kron(IDENTITY, product)
        - 0.5 * np.kron(product.T, IDENTITY)
    )


def _liouvillian(
    alpha: float, gamma_prime: float, omega: float, rate_scale: float
) -> ComplexArray:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must lie in [0, 1]")
    if gamma_prime <= 0.0 or omega <= 0.0:
        raise ValueError("gamma_prime and omega must be positive")
    gamma = gamma_prime * omega
    hamiltonian = 0.5 * omega * SIGMA_X
    coherent = -1j * (np.kron(IDENTITY, hamiltonian) - np.kron(hamiltonian.T, IDENTITY))
    decay = _dissipator_superoperator(SIGMA_MINUS)
    dephase = _dissipator_superoperator(PROJECTOR_UP)
    return (
        coherent
        + rate_scale * alpha * gamma * decay
        + rate_scale * (1.0 - alpha) * gamma * dephase
    )


def liouvillian(alpha: float, gamma_prime: float, omega: float = 1.0) -> ComplexArray:
    """Supplement/figure-consistent generator with doubled printed rates."""

    return _liouvillian(alpha, gamma_prime, omega, rate_scale=2.0)


def liouvillian_literal_main(
    alpha: float, gamma_prime: float, omega: float = 1.0
) -> ComplexArray:
    """Literal Main Eqs. (1)-(2), used only as a falsification comparator."""

    return _liouvillian(alpha, gamma_prime, omega, rate_scale=1.0)


def density_from_bloch(y: float, z: float, x: float = 0.0) -> ComplexArray:
    return np.array(
        [
            [(1.0 + z) / 2.0, (x - 1j * y) / 2.0],
            [(x + 1j * y) / 2.0, (1.0 - z) / 2.0],
        ],
        dtype=complex,
    )


def bloch_from_density(density: ComplexArray) -> NDArray[np.float64]:
    x = float(np.real(density[0, 1] + density[1, 0]))
    y = float(np.real(1j * (density[0, 1] - density[1, 0])))
    z = float(np.real(density[0, 0] - density[1, 1]))
    return np.array([x, y, z], dtype=float)


def propagate_density(
    density: ComplexArray, times: NDArray[np.float64], generator: ComplexArray
) -> ComplexArray:
    vector = np.asarray(density, dtype=complex).reshape(4, order="F")
    propagated = []
    for time in np.atleast_1d(times):
        state = (expm(generator * float(time)) @ vector).reshape((2, 2), order="F")
        propagated.append(state)
    return np.asarray(propagated, dtype=complex)


def steady_density(generator: ComplexArray) -> ComplexArray:
    system = np.array(generator, copy=True)
    rhs = np.zeros(4, dtype=complex)
    trace_row = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex)
    system[0, :] = trace_row
    rhs[0] = 1.0
    solution = np.linalg.solve(system, rhs)
    density = solution.reshape((2, 2), order="F")
    return 0.5 * (density + density.conj().T)
