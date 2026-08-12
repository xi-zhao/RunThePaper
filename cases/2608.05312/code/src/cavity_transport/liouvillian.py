"""Sparse construction and propagation of the paper's exact Liouvillian."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import expm
from scipy.sparse import csc_matrix, eye, kron
from scipy.sparse.linalg import expm_multiply


def vectorize(rho: NDArray[np.complex128]) -> NDArray[np.complex128]:
    """Column-stack a density matrix, matching SM Eq. (S19)."""

    return np.asarray(rho, dtype=np.complex128).reshape(-1, order="F")


def devectorize(vector: ArrayLike, dimension: int) -> NDArray[np.complex128]:
    return np.asarray(vector, dtype=np.complex128).reshape(
        (dimension, dimension), order="F"
    )


def hamiltonian_superoperator(h: NDArray[np.complex128]) -> csc_matrix:
    """Return ``-i[I tensor H - H^T tensor I]``."""

    h_sparse = csc_matrix(h)
    identity = eye(h.shape[0], format="csc", dtype=np.complex128)
    return csc_matrix(
        -1.0j * (kron(identity, h_sparse) - kron(h_sparse.T, identity))
    )


def dissipator_superoperator(
    jumps: list[csc_matrix],
    dimension: int,
) -> csc_matrix:
    """Sum unit-rate Lindblad dissipators for one jump family."""

    identity = eye(dimension, format="csc", dtype=np.complex128)
    result = csc_matrix((dimension * dimension, dimension * dimension), dtype=np.complex128)
    for jump in jumps:
        norm = jump.getH() @ jump
        result = result + kron(jump.conjugate(), jump) - 0.5 * (
            kron(identity, norm) + kron(norm.T, identity)
        )
    return csc_matrix(result)


def propagate_final(
    generator: csc_matrix,
    rho0: NDArray[np.complex128],
    final_time: float,
) -> NDArray[np.complex128]:
    if final_time < 0:
        raise ValueError("final_time must be non-negative")
    dimension = rho0.shape[0]
    if final_time == 0:
        return rho0.copy()
    evolved = expm_multiply(generator * final_time, vectorize(rho0))
    return devectorize(evolved, dimension)


def propagate_times(
    generator: csc_matrix,
    rho0: NDArray[np.complex128],
    times: ArrayLike,
) -> NDArray[np.complex128]:
    """Propagate on a non-negative, linearly spaced time grid."""

    grid = np.asarray(times, dtype=float)
    if grid.ndim != 1 or grid.size < 2:
        raise ValueError("times must contain at least two points")
    if grid[0] < 0 or np.any(np.diff(grid) <= 0):
        raise ValueError("times must be strictly increasing and non-negative")
    steps = np.diff(grid)
    if not np.allclose(steps, steps[0], rtol=1e-10, atol=1e-12):
        raise ValueError("expm_multiply path requires a linearly spaced grid")

    evolved = expm_multiply(
        generator,
        vectorize(rho0),
        start=float(grid[0]),
        stop=float(grid[-1]),
        num=int(grid.size),
        endpoint=True,
    )
    dimension = rho0.shape[0]
    return np.asarray(
        [devectorize(vector, dimension) for vector in evolved],
        dtype=np.complex128,
    )


def dense_propagate_final(
    generator: csc_matrix,
    rho0: NDArray[np.complex128],
    final_time: float,
) -> NDArray[np.complex128]:
    """Paper-method reference path for small-system regression tests."""

    dimension = rho0.shape[0]
    evolved = expm(generator.toarray() * final_time) @ vectorize(rho0)
    return devectorize(evolved, dimension)
