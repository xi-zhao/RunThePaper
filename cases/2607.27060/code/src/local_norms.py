"""Independent local Choi-bound audit for the paper's lambda parameters."""

from __future__ import annotations

from math import sqrt

import numpy as np


I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
CREATE = np.array([[0, 0], [1, 0]], dtype=complex)
DESTROY = CREATE.conj().T


def liouvillian_matrix(hamiltonian: np.ndarray, collapses: tuple[np.ndarray, ...] = ()) -> np.ndarray:
    """Column-vectorized GKSL superoperator, matching the stated local map."""
    dimension = hamiltonian.shape[0]
    identity = np.eye(dimension, dtype=complex)
    matrix = -1j * (
        np.kron(identity, hamiltonian)
        - np.kron(hamiltonian.T, identity)
    )
    for collapse in collapses:
        cdc = collapse.conj().T @ collapse
        matrix += (
            np.kron(collapse.conj(), collapse)
            - 0.5 * np.kron(identity, cdc)
            - 0.5 * np.kron(cdc.T, identity)
        )
    return matrix


def choi_matrix(superoperator: np.ndarray, dimension: int) -> np.ndarray:
    choi = np.zeros((dimension**2, dimension**2), dtype=complex)
    for row in range(dimension):
        for column in range(dimension):
            basis = np.zeros((dimension, dimension), dtype=complex)
            basis[row, column] = 1.0
            output = (superoperator @ basis.reshape(-1, order="F")).reshape(
                (dimension, dimension), order="F"
            )
            choi[
                row * dimension : (row + 1) * dimension,
                column * dimension : (column + 1) * dimension,
            ] = output
    return choi


def _partial_trace_second(matrix: np.ndarray, dimension: int) -> np.ndarray:
    return np.einsum(
        "ijkj->ik",
        matrix.reshape(dimension, dimension, dimension, dimension),
    )


def nechita_bound(superoperator: np.ndarray, dimension: int) -> tuple[float, bool]:
    """Evaluate the paper's Choi-matrix upper bound and equality condition."""
    choi = choi_matrix(superoperator, dimension)

    def positive_square_root(matrix: np.ndarray) -> np.ndarray:
        hermitian = (matrix + matrix.conj().T) / 2.0
        eigenvalues, eigenvectors = np.linalg.eigh(hermitian)
        return (eigenvectors * np.sqrt(np.clip(eigenvalues, 0.0, None))) @ eigenvectors.conj().T

    left_root = positive_square_root(choi.conj().T @ choi)
    right_root = positive_square_root(choi @ choi.conj().T)
    left = _partial_trace_second(left_root, dimension)
    right = _partial_trace_second(right_root, dimension)
    bound = (np.linalg.norm(left, ord=2) + np.linalg.norm(right, ord=2)) / 2.0

    def scalar_identity(matrix: np.ndarray) -> bool:
        scalar = np.trace(matrix) / dimension
        return bool(np.allclose(matrix, scalar * np.eye(dimension), atol=1e-8, rtol=0.0))

    return float(np.real_if_close(bound)), scalar_identity(left) and scalar_identity(right)


def xx_local_bounds(omega: float = 3.94, gamma: float = 0.31) -> list[dict[str, float | str | bool]]:
    h_bond = np.kron(X, X) + np.kron(Y, Y)
    terms: list[tuple[str, np.ndarray, int]] = [
        ("XX+YY bond", liouvillian_matrix(h_bond), 4),
        ("boundary sigma+", liouvillian_matrix(np.zeros((2, 2), dtype=complex), (sqrt(omega / 2.0) * CREATE,)), 2),
        ("boundary sigma-", liouvillian_matrix(np.zeros((2, 2), dtype=complex), (sqrt(omega / 2.0) * DESTROY,)), 2),
        ("local dephasing", liouvillian_matrix(np.zeros((2, 2), dtype=complex), (sqrt(gamma / 2.0) * Z,)), 2),
    ]
    return [
        {"term": label, "bound": bound, "equality_condition": exact}
        for label, matrix, dimension in terms
        for bound, exact in [nechita_bound(matrix, dimension)]
    ]


def tfim_local_bounds(j_coupling: float = 1.0, field: float = 0.5, gamma: float = 0.1) -> list[dict[str, float | str | bool]]:
    # A global phase multiplying a linear map leaves the bound unchanged.  The
    # physical Hamiltonians -J ZZ and -h X implement iJ[ZZ,.] and ih[X,.].
    h_zz = -j_coupling * np.kron(Z, Z)
    h_x = -field * X
    terms: list[tuple[str, np.ndarray, int]] = [
        ("ZZ coupling", liouvillian_matrix(h_zz), 4),
        ("X field", liouvillian_matrix(h_x), 2),
        ("Z dephasing", liouvillian_matrix(np.zeros((2, 2), dtype=complex), (sqrt(gamma) * Z,)), 2),
    ]
    return [
        {"term": label, "bound": bound, "equality_condition": exact}
        for label, matrix, dimension in terms
        for bound, exact in [nechita_bound(matrix, dimension)]
    ]


def model_lambda(model: str) -> tuple[float, list[dict[str, float | str | bool]]]:
    if model == "xx_spin_chain":
        terms = xx_local_bounds()
    elif model == "tfim_lattice":
        terms = tfim_local_bounds()
    else:
        raise ValueError(f"unknown model: {model}")
    return max(float(term["bound"]) for term in terms), terms
