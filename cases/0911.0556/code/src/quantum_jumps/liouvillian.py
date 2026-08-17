"""Dense Lindblad and tilted-Lindblad superoperators.

The implementation uses column-major vectorization, ``vec_F``.  For this
convention ``vec(A X B) = (B.T kron A) vec(X)``.  Only the recycling term of
the counted jump is multiplied by ``exp(-s)``, exactly as in Eq. (4).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.linalg


@dataclass(frozen=True)
class DominantEigenpair:
    eigenvalue: complex
    right_matrix: np.ndarray
    left_matrix: np.ndarray
    right_residual: float
    left_residual: float


def _as_square(name: str, value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=np.complex128)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError(f"{name} must be a square matrix")
    return array


def tilted_liouvillian(
    hamiltonian: np.ndarray,
    jumps: list[np.ndarray] | tuple[np.ndarray, ...],
    s: float,
    *,
    counted_jump: int = 0,
) -> np.ndarray:
    """Return the tilted superoperator in the paper's counting convention."""

    hamiltonian = _as_square("hamiltonian", hamiltonian)
    dimension = hamiltonian.shape[0]
    identity = np.eye(dimension, dtype=np.complex128)
    jump_arrays = [_as_square("jump", jump) for jump in jumps]
    if not jump_arrays:
        raise ValueError("at least one jump operator is required")
    if not 0 <= counted_jump < len(jump_arrays):
        raise IndexError("counted_jump is outside the jump list")

    generator = -1j * (
        np.kron(identity, hamiltonian) - np.kron(hamiltonian.T, identity)
    )
    for index, jump in enumerate(jump_arrays):
        if jump.shape != hamiltonian.shape:
            raise ValueError("all jump operators must match the Hamiltonian")
        rate_weight = np.exp(-float(s)) if index == counted_jump else 1.0
        jump_norm = jump.conj().T @ jump
        generator += rate_weight * np.kron(jump.conj(), jump)
        generator -= 0.5 * np.kron(identity, jump_norm)
        generator -= 0.5 * np.kron(jump_norm.T, identity)
    return generator


def lindblad_superoperator(
    hamiltonian: np.ndarray,
    jumps: list[np.ndarray] | tuple[np.ndarray, ...],
) -> np.ndarray:
    return tilted_liouvillian(hamiltonian, jumps, 0.0)


def dominant_eigenpair(superoperator: np.ndarray) -> DominantEigenpair:
    """Return normalized dominant left/right eigenmatrices and residuals."""

    operator = _as_square("superoperator", superoperator)
    vector_dimension = operator.shape[0]
    dimension = int(round(np.sqrt(vector_dimension)))
    if dimension * dimension != vector_dimension:
        raise ValueError("superoperator dimension must be a perfect square")

    eigenvalues, left_vectors, right_vectors = scipy.linalg.eig(
        operator, left=True, right=True
    )
    index = int(np.argmax(eigenvalues.real))
    eigenvalue = complex(eigenvalues[index])
    right_vector = right_vectors[:, index]
    left_vector = left_vectors[:, index]

    # scipy's left vector obeys a^H W = lambda a^H.  The corresponding
    # left eigenmatrix is unvec(conj(a)) so Tr(l X)=a^H vec(X).
    right_matrix = right_vector.reshape((dimension, dimension), order="F")
    left_matrix = left_vector.conj().reshape((dimension, dimension), order="F").T
    right_matrix = 0.5 * (right_matrix + right_matrix.conj().T)
    left_matrix = 0.5 * (left_matrix + left_matrix.conj().T)

    right_trace = np.trace(right_matrix)
    if abs(right_trace) < 1e-14:
        raise RuntimeError("dominant right eigenmatrix has vanishing trace")
    right_matrix /= right_trace

    overlap = np.trace(left_matrix @ right_matrix)
    if abs(overlap) < 1e-14:
        raise RuntimeError("dominant left/right eigenmatrices have zero overlap")
    left_matrix /= overlap

    right_flat = right_matrix.reshape(-1, order="F")
    left_flat = left_matrix.T.reshape(-1, order="F")
    right_residual = float(
        np.linalg.norm(operator @ right_flat - eigenvalue * right_flat)
    )
    left_residual = float(np.linalg.norm(left_flat @ operator - eigenvalue * left_flat))
    return DominantEigenpair(
        eigenvalue=eigenvalue,
        right_matrix=right_matrix,
        left_matrix=left_matrix,
        right_residual=right_residual,
        left_residual=left_residual,
    )


def trace_preservation_residual(superoperator: np.ndarray) -> float:
    operator = _as_square("superoperator", superoperator)
    dimension = int(round(np.sqrt(operator.shape[0])))
    identity_flat = np.eye(dimension).reshape(-1, order="F")
    return float(np.linalg.norm(identity_flat.conj() @ operator))
