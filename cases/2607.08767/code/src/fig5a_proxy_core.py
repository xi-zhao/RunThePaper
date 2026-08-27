from __future__ import annotations

import math

import numpy as np
from scipy.linalg import expm


X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
IDENTITY = np.eye(2, dtype=complex)
H = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex) / math.sqrt(2.0)


def pauli_twirl_probability(theta: float) -> float:
    """Return the X and Z probabilities in the paper's Equation (10)."""

    return float(math.sin(math.sqrt(2.0) * math.pi * theta) ** 2 / 2.0)


def coherent_error_unitary(theta: float) -> np.ndarray:
    """Return U = exp[-i theta pi (X + Z)] from Equation (9)."""

    return expm(-1j * theta * math.pi * (X + Z))


def _tensor_power(operator: np.ndarray, count: int) -> np.ndarray:
    result = np.array([[1.0]], dtype=complex)
    for _ in range(count):
        result = np.kron(result, operator)
    return result


def _qubit_operator(operator: np.ndarray, qubit: int, count: int) -> np.ndarray:
    factors = [operator if index == qubit else IDENTITY for index in range(count)]
    result = factors[0]
    for factor in factors[1:]:
        result = np.kron(result, factor)
    return result


def _ghz_density(distance: int) -> np.ndarray:
    if distance < 3 or distance % 2 == 0:
        raise ValueError("distance must be an odd integer >= 3")
    state = np.zeros(2**distance, dtype=complex)
    state[0] = 1.0 / math.sqrt(2.0)
    state[-1] = 1.0 / math.sqrt(2.0)
    return np.outer(state, state.conj())


def _odd_x_parity_probability(state: np.ndarray, distance: int) -> float:
    transform = _tensor_power(H, distance)
    x_basis = transform @ state @ transform.conj().T
    diagonal = np.real(np.diag(x_basis))
    return float(
        sum(
            probability
            for index, probability in enumerate(diagonal)
            if index.bit_count() % 2 == 1
        )
    )


def deterministic_proxy_probabilities(
    *, theta: float, distance: int, rounds: int
) -> dict[str, float]:
    """Propagate the public coherent and Pauli-twirled channels on a GHZ proxy.

    This deterministic density-matrix calculation is an implementation smoke
    for Eqs. (9)-(10), not the paper's unpublished circuit/decoder experiment.
    """

    if rounds < 1:
        raise ValueError("rounds must be positive")
    coherent_state = _ghz_density(distance)
    twirled_state = coherent_state.copy()
    unitary = _tensor_power(coherent_error_unitary(theta), distance)
    probability = pauli_twirl_probability(theta)
    for _ in range(rounds):
        coherent_state = unitary @ coherent_state @ unitary.conj().T
        for qubit in range(distance):
            x = _qubit_operator(X, qubit, distance)
            z = _qubit_operator(Z, qubit, distance)
            twirled_state = (
                (1.0 - 2.0 * probability) * twirled_state
                + probability * (x @ twirled_state @ x)
                + probability * (z @ twirled_state @ z)
            )
    return {
        "coherent_odd_x_parity_probability": _odd_x_parity_probability(
            coherent_state, distance
        ),
        "twirled_odd_x_parity_probability": _odd_x_parity_probability(
            twirled_state, distance
        ),
        "coherent_trace_error": float(abs(np.trace(coherent_state) - 1.0)),
        "twirled_trace_error": float(abs(np.trace(twirled_state) - 1.0)),
    }
