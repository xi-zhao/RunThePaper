"""Trace-constrained steady-state solver for the paper's Lindblad equation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import solve


@dataclass(frozen=True)
class SteadyStateResult:
    rho: np.ndarray
    residual_norm: float
    trace_error: float
    hermiticity_error: float
    minimum_eigenvalue: float


def liouvillian(hamiltonian: np.ndarray, annihilation: np.ndarray) -> np.ndarray:
    dimension = hamiltonian.shape[0]
    if hamiltonian.shape != (dimension, dimension):
        raise ValueError("Hamiltonian must be square")
    if annihilation.shape != hamiltonian.shape:
        raise ValueError("annihilation operator shape must match Hamiltonian")

    identity = np.eye(dimension, dtype=complex)
    number = annihilation.conj().T @ annihilation
    coherent = -1j * (
        np.kron(identity, hamiltonian) - np.kron(hamiltonian.T, identity)
    )
    dissipative = (
        np.kron(annihilation.conj(), annihilation)
        - 0.5 * np.kron(identity, number)
        - 0.5 * np.kron(number.T, identity)
    )
    return coherent + dissipative


def steady_state(hamiltonian: np.ndarray, annihilation: np.ndarray) -> SteadyStateResult:
    generator = liouvillian(hamiltonian, annihilation)
    dimension = hamiltonian.shape[0]
    constrained = generator.copy()
    rhs = np.zeros(dimension * dimension, dtype=complex)
    constrained[0, :] = np.eye(dimension, dtype=complex).reshape(-1, order="F")
    rhs[0] = 1.0
    vector = solve(constrained, rhs, assume_a="gen")
    rho = vector.reshape((dimension, dimension), order="F")
    residual = float(np.linalg.norm(generator @ vector))
    trace_error = float(abs(np.trace(rho) - 1.0))
    hermiticity_error = float(np.linalg.norm(rho - rho.conj().T))

    rho = 0.5 * (rho + rho.conj().T)
    rho /= np.trace(rho)
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(rho)).real)
    return SteadyStateResult(
        rho=rho,
        residual_norm=residual,
        trace_error=trace_error,
        hermiticity_error=hermiticity_error,
        minimum_eigenvalue=minimum_eigenvalue,
    )
