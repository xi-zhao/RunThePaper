"""Similarity-map checks for the generalized quantum Doob transform."""

from __future__ import annotations

import numpy as np
import scipy.linalg

from .liouvillian import dominant_eigenpair, tilted_liouvillian
from .models import QuantumJumpModel


def positive_matrix_power(matrix: np.ndarray, power: float) -> np.ndarray:
    hermitian = 0.5 * (matrix + matrix.conj().T)
    values, vectors = scipy.linalg.eigh(hermitian)
    if np.min(values) <= 0:
        if np.min(values) < -1e-9:
            raise ValueError("matrix is not positive definite")
        values = np.maximum(values, 1e-12)
    return (vectors * values**power) @ vectors.conj().T


def doob_similarity_superoperator(
    model: QuantumJumpModel,
    s: float,
) -> tuple[np.ndarray, complex, np.ndarray]:
    tilted = tilted_liouvillian(
        model.hamiltonian, model.jumps, s, counted_jump=model.counted_jump
    )
    pair = dominant_eigenpair(tilted)
    left_half = positive_matrix_power(pair.left_matrix, 0.5)
    inverse_left_half = positive_matrix_power(pair.left_matrix, -0.5)
    transform = np.kron(left_half.T, left_half)
    inverse_transform = np.kron(inverse_left_half.T, inverse_left_half)
    doob = transform @ tilted @ inverse_transform
    doob -= pair.eigenvalue * np.eye(doob.shape[0])
    return doob, pair.eigenvalue, pair.left_matrix


def transformed_jumps(model: QuantumJumpModel, s: float) -> tuple[np.ndarray, ...]:
    tilted = tilted_liouvillian(
        model.hamiltonian, model.jumps, s, counted_jump=model.counted_jump
    )
    left = dominant_eigenpair(tilted).left_matrix
    left_half = positive_matrix_power(left, 0.5)
    inverse_left_half = positive_matrix_power(left, -0.5)
    result = []
    for index, jump in enumerate(model.jumps):
        bias = np.exp(-0.5 * s) if index == model.counted_jump else 1.0
        result.append(bias * left_half @ jump @ inverse_left_half)
    return tuple(result)
