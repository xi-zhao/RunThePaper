"""Independent dense Lindblad fixed-point solver for small XXZ chains.

This module intentionally does not import the transfer implementation.  It is
an independent cross-check of the Hamiltonian, dissipator and observables.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
SIGMA_PLUS = 0.5 * (SIGMA_X + 1j * SIGMA_Y)
SIGMA_MINUS = SIGMA_PLUS.conj().T
IDENTITY_2 = np.eye(2, dtype=np.complex128)


@dataclass(frozen=True)
class DenseNESSResult:
    density_matrix: np.ndarray
    magnetization: np.ndarray
    bond_currents: np.ndarray
    residual_norm: float
    trace_error: float
    hermiticity_error: float


def _site_operator(operator: np.ndarray, site: int, size: int) -> np.ndarray:
    result = np.array([[1.0]], dtype=np.complex128)
    for index in range(size):
        result = np.kron(result, operator if index == site else IDENTITY_2)
    return result


def hamiltonian(delta: float, size: int) -> np.ndarray:
    dimension = 2**size
    result = np.zeros((dimension, dimension), dtype=np.complex128)
    for site in range(size - 1):
        plus_left = _site_operator(SIGMA_PLUS, site, size)
        minus_left = _site_operator(SIGMA_MINUS, site, size)
        plus_right = _site_operator(SIGMA_PLUS, site + 1, size)
        minus_right = _site_operator(SIGMA_MINUS, site + 1, size)
        z_left = _site_operator(SIGMA_Z, site, size)
        z_right = _site_operator(SIGMA_Z, site + 1, size)
        result += (
            2.0 * plus_left @ minus_right
            + 2.0 * minus_left @ plus_right
            + delta * z_left @ z_right
        )
    return result


def liouvillian(delta: float, epsilon: float, size: int) -> np.ndarray:
    if size < 2:
        raise ValueError("dense NESS requires at least two sites")
    hilbert_dimension = 2**size
    identity = np.eye(hilbert_dimension, dtype=np.complex128)
    h_value = hamiltonian(delta, size)
    generator = -1j * (
        np.kron(identity, h_value) - np.kron(h_value.T, identity)
    )
    jumps = [
        np.sqrt(epsilon) * _site_operator(SIGMA_PLUS, 0, size),
        np.sqrt(epsilon) * _site_operator(SIGMA_MINUS, size - 1, size),
    ]
    for jump in jumps:
        rate = jump.conj().T @ jump
        generator += (
            2.0 * np.kron(jump.conj(), jump)
            - np.kron(identity, rate)
            - np.kron(rate.T, identity)
        )
    return generator


def solve_dense_ness(delta: float, epsilon: float, size: int) -> DenseNESSResult:
    generator = liouvillian(delta, epsilon, size)
    hilbert_dimension = 2**size
    system = generator.copy()
    right_hand_side = np.zeros(hilbert_dimension**2, dtype=np.complex128)
    system[0, :] = np.eye(hilbert_dimension, dtype=np.complex128).reshape(
        -1, order="F"
    )
    right_hand_side[0] = 1.0
    vector = np.linalg.solve(system, right_hand_side)
    density = vector.reshape((hilbert_dimension, hilbert_dimension), order="F")

    magnetization = np.array(
        [
            np.trace(density @ _site_operator(SIGMA_Z, site, size)).real
            for site in range(size)
        ],
        dtype=np.float64,
    )
    currents = []
    for site in range(size - 1):
        hopping = 1j * (
            _site_operator(SIGMA_PLUS, site, size)
            @ _site_operator(SIGMA_MINUS, site + 1, size)
            - _site_operator(SIGMA_MINUS, site, size)
            @ _site_operator(SIGMA_PLUS, site + 1, size)
        )
        currents.append(float(np.trace(density @ hopping).real))

    residual = generator @ vector
    return DenseNESSResult(
        density_matrix=density,
        magnetization=magnetization,
        bond_currents=np.asarray(currents, dtype=np.float64),
        residual_norm=float(np.linalg.norm(residual)),
        trace_error=float(abs(np.trace(density) - 1.0)),
        hermiticity_error=float(np.max(np.abs(density - density.conj().T))),
    )
