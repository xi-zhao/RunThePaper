"""First-star projection of the microscopic Pauli spin-orbit operator."""

from __future__ import annotations

from math import pi, sqrt

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]


def _pauli() -> tuple[ComplexArray, ComplexArray]:
    identity = np.eye(2, dtype=np.complex128)
    sigma_z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    return identity, sigma_z


def first_star_spin_orbit_matrix(lattice_constant: float = 1.0) -> ComplexArray:
    """Construct the full first-star matrix in ``(A/B,K/K',spin)`` order.

    Units set ``e^2 hbar^2/(m^2 c^2)=1``.  The two-dimensional Fourier
    transform of ``1/r`` is divided by the honeycomb primitive-cell area.
    The outer factor 1/4 is the Pauli spin-orbit prefactor in Eq. (7).
    """

    if lattice_constant <= 0:
        raise ValueError("lattice_constant must be positive")
    wavevector = 4.0 * pi / (3.0 * lattice_constant)
    first_star = np.asarray(
        [
            [
                wavevector * np.cos(2.0 * pi * corner / 3.0),
                wavevector * np.sin(2.0 * pi * corner / 3.0),
            ]
            for corner in range(3)
        ],
        dtype=float,
    )
    basis_positions = np.asarray(
        [
            [0.0, lattice_constant / sqrt(3.0)],
            [0.0, -lattice_constant / sqrt(3.0)],
        ],
        dtype=float,
    )
    cell_area = sqrt(3.0) * lattice_constant**2 / 2.0
    orbital = np.zeros((4, 4), dtype=np.complex128)
    for valley_index, valley_sign in enumerate((1.0, -1.0)):
        momenta = valley_sign * first_star
        for target_sublattice in range(2):
            for source_sublattice in range(2):
                element = 0.0j
                for target_corner in range(3):
                    for source_corner in range(3):
                        if target_corner == source_corner:
                            continue
                        transfer = momenta[target_corner] - momenta[source_corner]
                        coulomb_fourier = (
                            2.0 * pi / (np.linalg.norm(transfer) * cell_area)
                        )
                        cross = (
                            momenta[target_corner, 0] * momenta[source_corner, 1]
                            - momenta[target_corner, 1] * momenta[source_corner, 0]
                        )
                        bra_phase = np.exp(
                            1j
                            * momenta[target_corner]
                            @ basis_positions[target_sublattice]
                        )
                        ket_phase = np.exp(
                            -1j
                            * momenta[source_corner]
                            @ basis_positions[source_sublattice]
                        )
                        element += (
                            bra_phase
                            * ket_phase
                            * 1j
                            * cross
                            * coulomb_fourier
                            / 3.0
                            / 4.0
                        )
                target = 2 * target_sublattice + valley_index
                source = 2 * source_sublattice + valley_index
                orbital[target, source] = element
    _identity, spin_z = _pauli()
    return np.kron(orbital, spin_z)


def first_star_projection_diagnostics(
    lattice_constant: float = 1.0,
) -> dict[str, float | list[float]]:
    """Compare the explicit plane-wave sum with ``sigma_z tau_z s_z``."""

    _identity, sigma_z = _pauli()
    matrix = first_star_spin_orbit_matrix(lattice_constant)
    coefficient = 2.0 * pi**2 / (3.0 * lattice_constant**3)
    expected = coefficient * np.kron(np.kron(sigma_z, sigma_z), sigma_z)
    return {
        "matrix_dimension": int(matrix.shape[0]),
        "coefficient_in_e2_hbar2_over_m2c2": coefficient,
        "max_sigma_z_tau_z_s_z_residual": float(np.max(np.abs(matrix - expected))),
        "max_hermiticity_residual": float(np.max(np.abs(matrix - matrix.conj().T))),
        "eigenvalues": [float(value) for value in np.linalg.eigvalsh(matrix)],
        "trace": float(np.real(np.trace(matrix))),
    }
