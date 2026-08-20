"""Bulk Rashba response derived from the clean-room lattice Hamiltonian.

The paper does not print the externally cited Murakami conserved-spin operator.
This module therefore evaluates the conventional symmetrized spin-current Kubo
response and explicitly reports ``[H,s_z]``.  It supplies a falsifiable finite-
Rashba response without mislabeling an external, model-specific construction
as paper-exact.  No author arrays or plotted pixels enter the module.
"""

from __future__ import annotations

from math import pi, sqrt

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def _pauli() -> tuple[ComplexArray, ComplexArray, ComplexArray, ComplexArray]:
    identity = np.eye(2, dtype=np.complex128)
    sigma_x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    sigma_y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    sigma_z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    return identity, sigma_x, sigma_y, sigma_z


def _bulk_operator_and_velocities(
    reciprocal_u: float,
    reciprocal_v: float,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    rashba_lambda: float,
    staggered_sublattice_mass: float = 0.0,
    in_plane_zeeman: float = 0.0,
) -> tuple[ComplexArray, ComplexArray, ComplexArray]:
    """Return ``H, dH/dkx, dH/dky`` in the ``(A/B, spin_z)`` basis."""

    identity, spin_x, spin_y, spin_z = _pauli()
    delta = np.asarray(
        [[0.0, -1.0], [sqrt(3.0) / 2.0, 0.5], [-sqrt(3.0) / 2.0, 0.5]],
        dtype=float,
    )
    lattice = np.column_stack((delta[1] - delta[0], delta[2] - delta[0]))
    reciprocal = 2.0 * pi * np.linalg.inv(lattice).T
    momentum = reciprocal @ np.asarray([reciprocal_u, reciprocal_v], dtype=float)
    phases = np.exp(1j * delta @ momentum)

    bond_spin = np.asarray(
        [
            1j * rashba_lambda * (spin_x * displacement[1] - spin_y * displacement[0])
            for displacement in delta
        ]
    )
    hopping_blocks = hopping_t * identity[None, :, :] + bond_spin
    off_diagonal = np.einsum("a,aij->ij", phases, hopping_blocks)
    off_diagonal_x = np.einsum("a,a,aij->ij", 1j * delta[:, 0], phases, hopping_blocks)
    off_diagonal_y = np.einsum("a,a,aij->ij", 1j * delta[:, 1], phases, hopping_blocks)

    second = np.asarray(
        [delta[1] - delta[2], delta[2] - delta[0], delta[0] - delta[1]],
        dtype=float,
    )
    second_phase = second @ momentum
    mass = 2.0 * spin_orbit_t2 * float(np.sum(np.sin(second_phase)))
    mass_x = 2.0 * spin_orbit_t2 * float(np.sum(second[:, 0] * np.cos(second_phase)))
    mass_y = 2.0 * spin_orbit_t2 * float(np.sum(second[:, 1] * np.cos(second_phase)))

    uniform_zeeman = in_plane_zeeman * spin_x
    sublattice_mass = staggered_sublattice_mass * identity
    hamiltonian = np.block(
        [
            [mass * spin_z + sublattice_mass + uniform_zeeman, off_diagonal],
            [
                off_diagonal.conj().T,
                -mass * spin_z - sublattice_mass + uniform_zeeman,
            ],
        ]
    )
    velocity_x = np.block(
        [
            [mass_x * spin_z, off_diagonal_x],
            [off_diagonal_x.conj().T, -mass_x * spin_z],
        ]
    )
    velocity_y = np.block(
        [
            [mass_y * spin_z, off_diagonal_y],
            [off_diagonal_y.conj().T, -mass_y * spin_z],
        ]
    )
    return hamiltonian, velocity_x, velocity_y


def spinful_honeycomb_bulk_hamiltonian(
    reciprocal_u: float,
    reciprocal_v: float,
    *,
    hopping_t: float = 1.0,
    spin_orbit_t2: float = 0.03,
    rashba_lambda: float = 0.0,
    staggered_sublattice_mass: float = 0.0,
    in_plane_zeeman: float = 0.0,
) -> ComplexArray:
    """Return the primitive-cell bulk Hamiltonian with symmetry-breaking terms.

    The optional fields are both spatially uniform in the primitive cell:
    ``staggered_sublattice_mass`` is ``sigma_z`` and ``in_plane_zeeman`` is
    ``s_x``.  Keeping this path in the lattice basis makes primitive
    translation explicit and prevents a valley-mixing continuum proxy from
    being mistaken for a uniform-field mechanism.
    """

    hamiltonian, _velocity_x, _velocity_y = _bulk_operator_and_velocities(
        reciprocal_u,
        reciprocal_v,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        rashba_lambda=rashba_lambda,
        staggered_sublattice_mass=staggered_sublattice_mass,
        in_plane_zeeman=in_plane_zeeman,
    )
    return hamiltonian


def bulk_half_filling_gap_edges(
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    rashba_lambda: float,
    grid_size: int = 24,
) -> dict[str, float]:
    """Resolve the actual half-filled bulk gap of the lattice model.

    The finite-ribbon edge-state selector uses these independently sampled
    bulk band edges instead of assuming that the relevant states are those
    closest to zero energy.  The latter assumption fails once Rashba coupling
    makes the spectrum particle-hole asymmetric.
    """

    if grid_size < 12 or grid_size % 3:
        raise ValueError("grid_size must be >=12 and divisible by 3")
    valence_maximum = -float("inf")
    conduction_minimum = float("inf")
    minimum_direct_gap = float("inf")
    for first in range(grid_size):
        for second in range(grid_size):
            hamiltonian, _velocity_x, _velocity_y = _bulk_operator_and_velocities(
                first / grid_size,
                second / grid_size,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                rashba_lambda=rashba_lambda,
            )
            energies = np.linalg.eigvalsh(hamiltonian)
            valence_maximum = max(valence_maximum, float(energies[1]))
            conduction_minimum = min(conduction_minimum, float(energies[2]))
            minimum_direct_gap = min(
                minimum_direct_gap, float(energies[2] - energies[1])
            )
    return {
        "valence_maximum_over_t": valence_maximum / hopping_t,
        "conduction_minimum_over_t": conduction_minimum / hopping_t,
        "indirect_gap_over_t": (conduction_minimum - valence_maximum) / hopping_t,
        "minimum_direct_gap_over_t": minimum_direct_gap / hopping_t,
    }


def _raw_spin_hall_kubo(
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    rashba_lambda: float,
    grid_size: int,
) -> dict[str, float]:
    if grid_size < 6 or grid_size % 3:
        raise ValueError("grid_size must be >=6 and divisible by 3 to include K/K'")
    delta = np.asarray(
        [[0.0, -1.0], [sqrt(3.0) / 2.0, 0.5], [-sqrt(3.0) / 2.0, 0.5]],
        dtype=float,
    )
    lattice = np.column_stack((delta[1] - delta[0], delta[2] - delta[0]))
    reciprocal = 2.0 * pi * np.linalg.inv(lattice).T
    brillouin_area = abs(float(np.linalg.det(reciprocal)))

    response_sum = 0.0
    minimum_gap = float("inf")
    max_spin_nonconservation = 0.0
    max_hermiticity_residual = 0.0
    for first in range(grid_size):
        for second in range(grid_size):
            hamiltonian, velocity_x, velocity_y = _bulk_operator_and_velocities(
                first / grid_size,
                second / grid_size,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                rashba_lambda=rashba_lambda,
            )
            energies, vectors = np.linalg.eigh(hamiltonian)
            minimum_gap = min(minimum_gap, float(energies[2] - energies[1]))
            _identity, _spin_x, _spin_y, spin_z = _pauli()
            physical_spin = np.kron(np.eye(2, dtype=np.complex128), spin_z)
            max_spin_nonconservation = max(
                max_spin_nonconservation,
                float(
                    np.max(
                        np.abs(
                            hamiltonian @ physical_spin - physical_spin @ hamiltonian
                        )
                    )
                ),
            )
            spin_current_x = 0.5 * (
                physical_spin @ velocity_x + velocity_x @ physical_spin
            )
            max_hermiticity_residual = max(
                max_hermiticity_residual,
                float(np.max(np.abs(spin_current_x - spin_current_x.conj().T))),
            )
            occupied = range(2)
            empty = range(2, 4)
            for occupied_index in occupied:
                occupied_state = vectors[:, occupied_index]
                for empty_index in empty:
                    empty_state = vectors[:, empty_index]
                    energy_difference = float(
                        energies[empty_index] - energies[occupied_index]
                    )
                    first_matrix = np.vdot(occupied_state, spin_current_x @ empty_state)
                    second_matrix = np.vdot(empty_state, velocity_y @ occupied_state)
                    response_sum += float(
                        -2.0
                        * np.imag(first_matrix * second_matrix)
                        / energy_difference**2
                    )
    integration_weight = brillouin_area / grid_size**2 / (2.0 * pi) ** 2
    return {
        "raw_response": response_sum * integration_weight,
        "minimum_direct_gap_over_t": minimum_gap / hopping_t,
        "physical_spin_commutator_norm": max_spin_nonconservation,
        "spin_current_hermiticity_residual": max_hermiticity_residual,
    }


def conventional_spin_hall_sweep(
    rashba_ratios: FloatArray,
    *,
    hopping_t: float,
    spin_orbit_t2: float,
    grid_size: int = 24,
) -> list[dict[str, float]]:
    """Evaluate the conventional non-quantized spin Kubo response versus Rashba.

    ``rashba_ratios`` uses the continuum ratio ``lambda_R/Delta_so``.  Expanding
    the bond-vector lattice term at K gives ``lambda_R = 3 lambda_lattice / 2``
    and ``Delta_so = 3 sqrt(3) t2``; this mapping is applied before each full-BZ
    calculation.  The raw Kubo normalization is divided by the zero-Rashba
    result from the same grid, so the returned physical coefficient equals the
    paper's ``e/(2 pi)`` at the spin-conserving point without borrowing plotted
    data.
    """

    ratios = np.asarray(rashba_ratios, dtype=float)
    if ratios.ndim != 1 or len(ratios) < 2 or np.any(ratios < 0):
        raise ValueError("rashba_ratios must be a one-dimensional nonnegative sweep")
    continuum_delta = 3.0 * sqrt(3.0) * spin_orbit_t2
    raw_rows: list[dict[str, float]] = []
    for ratio in ratios:
        continuum_rashba = float(ratio * continuum_delta)
        lattice_rashba = 2.0 * continuum_rashba / 3.0
        row = _raw_spin_hall_kubo(
            hopping_t=hopping_t,
            spin_orbit_t2=spin_orbit_t2,
            rashba_lambda=lattice_rashba,
            grid_size=grid_size,
        )
        raw_rows.append(
            {
                "lambda_r_over_delta_so": float(ratio),
                "lattice_rashba_over_t": lattice_rashba / hopping_t,
                **row,
            }
        )
    baseline = raw_rows[0]["raw_response"]
    if abs(baseline) <= 1e-12:
        raise RuntimeError("zero-Rashba Kubo normalization vanished")
    for row in raw_rows:
        ratio = row["raw_response"] / baseline
        row["response_over_quantized"] = ratio
        row["spin_hall_in_e_over_2pi"] = ratio
        row["relative_correction"] = ratio - 1.0
    return raw_rows
