"""Independent local Choi-bound reconstruction for the reported lambda values."""

from __future__ import annotations

import numpy as np


IDENTITY_2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
SIGMA_Z = np.diag([1.0, -1.0]).astype(complex)
SIGMA_PLUS = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
SIGMA_MINUS = SIGMA_PLUS.T


def commutator_superoperator(hamiltonian: np.ndarray) -> np.ndarray:
    """Matrix for -i[H,rho] under column-vectorization."""

    dimension = hamiltonian.shape[0]
    identity = np.eye(dimension, dtype=complex)
    return -1.0j * (
        np.kron(identity, hamiltonian)
        - np.kron(hamiltonian.T, identity)
    )


def dissipator_superoperator(jump: np.ndarray) -> np.ndarray:
    """Matrix for D[c](rho)=c rho c†-{c†c,rho}/2."""

    dimension = jump.shape[0]
    identity = np.eye(dimension, dtype=complex)
    gram = jump.conj().T @ jump
    return (
        np.kron(jump.conj(), jump)
        - 0.5 * np.kron(identity, gram)
        - 0.5 * np.kron(gram.T, identity)
    )


def choi_matrix(superoperator: np.ndarray, dimension: int) -> np.ndarray:
    choi = np.zeros((dimension**2, dimension**2), dtype=complex)
    for row in range(dimension):
        for column in range(dimension):
            basis = np.zeros((dimension, dimension), dtype=complex)
            basis[row, column] = 1.0
            output = (
                superoperator @ basis.reshape(dimension**2, order="F")
            ).reshape((dimension, dimension), order="F")
            choi[
                row * dimension : (row + 1) * dimension,
                column * dimension : (column + 1) * dimension,
            ] = output
    return choi


def positive_semidefinite_sqrt(matrix: np.ndarray) -> np.ndarray:
    hermitian = 0.5 * (matrix + matrix.conj().T)
    values, vectors = np.linalg.eigh(hermitian)
    scale = max(1.0, float(np.max(np.abs(values))))
    if float(np.min(values)) < -1.0e-10 * scale:
        raise ValueError("matrix is not positive semidefinite within tolerance")
    values = np.maximum(values, 0.0)
    return (vectors * np.sqrt(values)) @ vectors.conj().T


def partial_trace_second(matrix: np.ndarray, dimension: int) -> np.ndarray:
    return np.einsum(
        "ijkj->ik", matrix.reshape(dimension, dimension, dimension, dimension)
    )


def nechita_bound(superoperator: np.ndarray, dimension: int) -> dict[str, object]:
    """Evaluate Eq. (32) with the spectral/operator matrix norm."""

    choi = choi_matrix(superoperator, dimension)
    left = partial_trace_second(
        positive_semidefinite_sqrt(choi.conj().T @ choi), dimension
    )
    right = partial_trace_second(
        positive_semidefinite_sqrt(choi @ choi.conj().T), dimension
    )
    value = 0.5 * (
        np.linalg.norm(left, ord=2) + np.linalg.norm(right, ord=2)
    )

    def scalar_identity(matrix: np.ndarray) -> bool:
        coefficient = np.trace(matrix) / matrix.shape[0]
        return bool(
            np.allclose(
                matrix,
                coefficient * np.eye(matrix.shape[0]),
                rtol=1.0e-9,
                atol=1.0e-9,
            )
        )

    return {
        "value": float(np.real_if_close(value)),
        "equality_condition": scalar_identity(left) and scalar_identity(right),
    }


def reconstruct_reported_lambdas() -> dict[str, object]:
    xx_coupling = np.kron(SIGMA_X, SIGMA_X) + np.kron(SIGMA_Y, SIGMA_Y)
    xx_terms_source_convention = [
        ("combined_xx_yy_commutator", commutator_superoperator(xx_coupling), 4)
    ]
    xx_terms_paper_literal = list(xx_terms_source_convention)
    boundary_prefactor = np.sqrt(3.94 / 2.0)
    for label, jump in (
        ("boundary_sigma_plus", boundary_prefactor * SIGMA_PLUS),
        ("boundary_sigma_minus", boundary_prefactor * SIGMA_MINUS),
    ):
        standard = dissipator_superoperator(jump)
        xx_terms_source_convention.append((label, standard, 2))
        # Eq. (28) writes 2 L rho L†-{L†L,rho}, twice the standard
        # dissipator for the jump definition in Eq. (26).
        xx_terms_paper_literal.append((label, 2.0 * standard, 2))
    dephasing_source = dissipator_superoperator(
        np.sqrt(0.31 / 2.0) * SIGMA_Z
    )
    dephasing_paper = dissipator_superoperator(np.sqrt(0.31) * SIGMA_Z)
    xx_terms_source_convention.append(("dephasing", dephasing_source, 2))
    xx_terms_paper_literal.append(("dephasing", dephasing_paper, 2))

    tfim_terms = [
        (
            "zz_commutator",
            commutator_superoperator(-np.kron(SIGMA_Z, SIGMA_Z)),
            4,
        ),
        (
            "x_field_commutator",
            commutator_superoperator(-0.5 * SIGMA_X),
            2,
        ),
        (
            "dephasing",
            dissipator_superoperator(np.sqrt(0.1) * SIGMA_Z),
            2,
        ),
    ]

    def evaluate(terms):
        records = []
        for label, superoperator, dimension in terms:
            records.append(
                {
                    "term": label,
                    "local_dimension": dimension,
                    **nechita_bound(superoperator, dimension),
                }
            )
        return {
            "terms": records,
            "lambda_max": max(item["value"] for item in records),
        }

    return {
        "xx_source_snapshot_convention": evaluate(
            xx_terms_source_convention
        ),
        "xx_literal_equation_28_convention": evaluate(xx_terms_paper_literal),
        "tfim_literal_equation_31_convention": evaluate(tfim_terms),
    }
