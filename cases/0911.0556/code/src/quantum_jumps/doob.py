"""Physical realization of the generalized quantum Doob transform.

The mapped Hamiltonian and jumps implement the two equations printed in the
final paragraph of the Letter.  They are derived from the dominant left
eigenmatrix of the tilted generator; no trajectory or figure data enter this
module.
"""

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


def mapped_lindblad_model(model: QuantumJumpModel, s: float) -> QuantumJumpModel:
    """Return the trace-preserving dynamics whose typical paths realize ``s``.

    This is Eqs. (10)-(11) of the paper.  In particular,

    ``H_tilde = 1/2 l^-1/2 ({H,l} + i/2 [sum L^dag L,l]) l^-1/2``.

    The explicit formula is preferable to reverse-engineering a Hamiltonian
    from the transformed superoperator because it preserves the physical
    operator interpretation used by the three-level claim.
    """

    tilted = tilted_liouvillian(
        model.hamiltonian, model.jumps, s, counted_jump=model.counted_jump
    )
    left = dominant_eigenpair(tilted).left_matrix
    left_half = positive_matrix_power(left, 0.5)
    inverse_left_half = positive_matrix_power(left, -0.5)

    jump_norm = np.zeros_like(model.hamiltonian)
    for jump in model.jumps:
        jump_norm += jump.conj().T @ jump
    numerator = (
        model.hamiltonian @ left
        + left @ model.hamiltonian
        + 0.5j * (jump_norm @ left - left @ jump_norm)
    )
    hamiltonian = 0.5 * inverse_left_half @ numerator @ inverse_left_half
    # Remove only round-off anti-Hermitian noise.  A material discrepancy is
    # caught by the generator-reconstruction check in the target probe.
    hamiltonian = 0.5 * (hamiltonian + hamiltonian.conj().T)

    jumps = []
    for index, jump in enumerate(model.jumps):
        bias = np.exp(-0.5 * s) if index == model.counted_jump else 1.0
        jumps.append(bias * left_half @ jump @ inverse_left_half)
    return QuantumJumpModel(
        hamiltonian=hamiltonian,
        jumps=tuple(jumps),
        counted_jump=model.counted_jump,
    )


def rank_one_jump_basis(jump: np.ndarray) -> np.ndarray:
    """Return the canonical ``|0~>, |1~>, ...`` basis of a rank-one jump.

    If ``jump = rate * |0~><1~|``, the first two columns are ``|0~>`` and
    ``|1~>``.  Remaining columns span the dark subspace.  This lets a mapped
    Hamiltonian be decomposed in the physical basis defined by its own photon
    emission channel rather than by an arbitrary numerical eigenbasis.
    """

    array = np.asarray(jump, dtype=np.complex128)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("jump must be a square matrix")
    left_vectors, singular_values, right_vectors_h = scipy.linalg.svd(array)
    scale = max(float(singular_values[0]), 1.0)
    rank = int(np.count_nonzero(singular_values > 1e-10 * scale))
    if rank != 1:
        raise ValueError("canonical jump basis requires a rank-one jump")

    ground = left_vectors[:, 0]
    excited = right_vectors_h.conj().T[:, 0]
    if abs(np.vdot(ground, excited)) > 1e-9:
        raise ValueError("rank-one jump is not a lowering transition")
    bright = np.column_stack((ground, excited))
    dark = scipy.linalg.null_space(bright.conj().T)
    basis = np.column_stack((bright, dark))
    if np.linalg.norm(basis.conj().T @ basis - np.eye(array.shape[0])) > 1e-9:
        raise RuntimeError("failed to construct an orthonormal jump basis")
    return basis
