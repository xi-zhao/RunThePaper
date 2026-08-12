"""Independent exact Lehmann solver for small interacting embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]


def fock_basis(n_spin_orbitals: int, n_electrons: int) -> tuple[int, ...]:
    """Enumerate fixed-particle-number bit strings in integer order."""

    if not 0 <= n_electrons <= n_spin_orbitals:
        raise ValueError("invalid electron count")
    states = []
    for occupied in combinations(range(n_spin_orbitals), n_electrons):
        state = 0
        for orbital in occupied:
            state |= 1 << orbital
        states.append(state)
    return tuple(states)


def annihilate(state: int, orbital: int) -> tuple[int, int] | None:
    """Apply c_orbital and return fermionic sign and new state."""

    bit = 1 << orbital
    if not state & bit:
        return None
    sign = -1 if (state & (bit - 1)).bit_count() % 2 else 1
    return sign, state ^ bit


def create(state: int, orbital: int) -> tuple[int, int] | None:
    """Apply c_orbital dagger and return fermionic sign and new state."""

    bit = 1 << orbital
    if state & bit:
        return None
    sign = -1 if (state & (bit - 1)).bit_count() % 2 else 1
    return sign, state | bit


def one_body_matrix(
    n_sites: int, hopping: float, *, periodic: bool = True
) -> ComplexArray:
    """Spinful nearest-neighbour tight-binding matrix."""

    n_orbitals = 2 * n_sites
    matrix = np.zeros((n_orbitals, n_orbitals), dtype=np.complex128)
    bonds = [(site, site + 1) for site in range(n_sites - 1)]
    if periodic and n_sites > 2:
        bonds.append((n_sites - 1, 0))
    for left, right in bonds:
        for spin in (0, 1):
            p = 2 * left + spin
            q = 2 * right + spin
            matrix[p, q] -= hopping
            matrix[q, p] -= hopping
    return matrix


def build_hubbard_hamiltonian(
    n_sites: int,
    n_electrons: int,
    *,
    hopping: float,
    onsite_u: float,
    nearest_v: float = 0.0,
    periodic: bool = True,
) -> tuple[ComplexArray, tuple[int, ...]]:
    """Build a spinful extended-Hubbard Hamiltonian in one number sector."""

    n_orbitals = 2 * n_sites
    basis = fock_basis(n_orbitals, n_electrons)
    index = {state: position for position, state in enumerate(basis)}
    hamiltonian = np.zeros((len(basis), len(basis)), dtype=np.complex128)
    one_body = one_body_matrix(n_sites, hopping, periodic=periodic)
    for column, state in enumerate(basis):
        diagonal = 0.0
        for site in range(n_sites):
            up = int(bool(state & (1 << (2 * site))))
            down = int(bool(state & (1 << (2 * site + 1))))
            diagonal += onsite_u * up * down
        bonds = [(site, site + 1) for site in range(n_sites - 1)]
        if periodic and n_sites > 2:
            bonds.append((n_sites - 1, 0))
        for left, right in bonds:
            n_left = int(bool(state & (1 << (2 * left)))) + int(
                bool(state & (1 << (2 * left + 1)))
            )
            n_right = int(bool(state & (1 << (2 * right)))) + int(
                bool(state & (1 << (2 * right + 1)))
            )
            diagonal += nearest_v * n_left * n_right
        hamiltonian[column, column] = diagonal
        for p in range(n_orbitals):
            for q in range(n_orbitals):
                coefficient = one_body[p, q]
                if p == q or abs(coefficient) < 1e-15:
                    continue
                removed = annihilate(state, q)
                if removed is None:
                    continue
                sign_q, intermediate = removed
                added = create(intermediate, p)
                if added is None:
                    continue
                sign_p, new_state = added
                hamiltonian[index[new_state], column] += coefficient * sign_q * sign_p
    hermiticity = np.max(np.abs(hamiltonian - hamiltonian.conj().T))
    if hermiticity > 1e-12:
        raise RuntimeError(f"Hamiltonian is not Hermitian: {hermiticity:.3e}")
    return hamiltonian, basis


def transition_vectors(
    source_basis: tuple[int, ...],
    source_vector: ComplexArray,
    target_basis: tuple[int, ...],
    *,
    creation: bool,
    n_spin_orbitals: int,
) -> ComplexArray:
    """Return c_p dagger|psi> or c_p|psi> in a target number sector."""

    target_index = {state: position for position, state in enumerate(target_basis)}
    vectors = np.zeros((n_spin_orbitals, len(target_basis)), dtype=np.complex128)
    operator = create if creation else annihilate
    for source_index, state in enumerate(source_basis):
        amplitude = source_vector[source_index]
        for orbital in range(n_spin_orbitals):
            result = operator(state, orbital)
            if result is None:
                continue
            sign, target_state = result
            vectors[orbital, target_index[target_state]] += sign * amplitude
    return vectors


@dataclass(frozen=True)
class LehmannResult:
    frequencies: NDArray[np.float64]
    green: ComplexArray
    self_energy: ComplexArray
    density: ComplexArray
    chemical_potential: float
    ground_energy: float
    addition_threshold: float
    removal_threshold: float


def one_body_density(
    basis: tuple[int, ...],
    state_vector: ComplexArray,
    n_spin_orbitals: int,
) -> ComplexArray:
    """Compute gamma_pq=<c_p dagger c_q>."""

    index = {state: position for position, state in enumerate(basis)}
    density = np.zeros((n_spin_orbitals, n_spin_orbitals), dtype=np.complex128)
    for right_index, state in enumerate(basis):
        amplitude = state_vector[right_index]
        for q in range(n_spin_orbitals):
            removed = annihilate(state, q)
            if removed is None:
                continue
            sign_q, intermediate = removed
            for p in range(n_spin_orbitals):
                added = create(intermediate, p)
                if added is None:
                    continue
                sign_p, final_state = added
                density[p, q] += (
                    np.conj(state_vector[index[final_state]])
                    * amplitude
                    * sign_q
                    * sign_p
                )
    return density


def solve_lehmann_green_function(
    n_sites: int,
    n_electrons: int,
    frequencies: NDArray[np.float64],
    *,
    hopping: float,
    onsite_u: float,
    nearest_v: float = 0.0,
    broadening: float = 0.08,
    periodic: bool = True,
) -> LehmannResult:
    """Diagonalize N and N+-1 sectors and construct the full retarded Green function."""

    if n_electrons in {0, 2 * n_sites}:
        raise ValueError("Lehmann solver requires both addition and removal sectors")
    h_n, basis_n = build_hubbard_hamiltonian(
        n_sites,
        n_electrons,
        hopping=hopping,
        onsite_u=onsite_u,
        nearest_v=nearest_v,
        periodic=periodic,
    )
    h_plus, basis_plus = build_hubbard_hamiltonian(
        n_sites,
        n_electrons + 1,
        hopping=hopping,
        onsite_u=onsite_u,
        nearest_v=nearest_v,
        periodic=periodic,
    )
    h_minus, basis_minus = build_hubbard_hamiltonian(
        n_sites,
        n_electrons - 1,
        hopping=hopping,
        onsite_u=onsite_u,
        nearest_v=nearest_v,
        periodic=periodic,
    )
    energies_n, vectors_n = np.linalg.eigh(h_n)
    energies_plus, vectors_plus = np.linalg.eigh(h_plus)
    energies_minus, vectors_minus = np.linalg.eigh(h_minus)
    ground_energy = float(energies_n[0])
    ground = vectors_n[:, 0]
    addition_threshold = float(energies_plus[0] - ground_energy)
    removal_threshold = float(ground_energy - energies_minus[0])
    chemical_potential = 0.5 * (addition_threshold + removal_threshold)
    n_orbitals = 2 * n_sites
    created = transition_vectors(
        basis_n,
        ground,
        basis_plus,
        creation=True,
        n_spin_orbitals=n_orbitals,
    )
    removed = transition_vectors(
        basis_n,
        ground,
        basis_minus,
        creation=False,
        n_spin_orbitals=n_orbitals,
    )
    addition_amplitudes = created @ vectors_plus.conj()
    removal_amplitudes = removed @ vectors_minus.conj()
    omega = np.asarray(frequencies, dtype=float)
    green = np.empty((omega.size, n_orbitals, n_orbitals), dtype=np.complex128)
    addition_poles = energies_plus - ground_energy
    removal_poles = ground_energy - energies_minus
    for index, value in enumerate(omega):
        addition_denominator = (
            value + chemical_potential - addition_poles + 1j * broadening
        )
        removal_denominator = (
            value + chemical_potential - removal_poles + 1j * broadening
        )
        addition = np.einsum(
            "pm,qm,m->pq",
            addition_amplitudes.conj(),
            addition_amplitudes,
            1.0 / addition_denominator,
            optimize=True,
        )
        removal = np.einsum(
            "pm,qm,m->pq",
            removal_amplitudes,
            removal_amplitudes.conj(),
            1.0 / removal_denominator,
            optimize=True,
        )
        green[index] = addition + removal
    one_body = one_body_matrix(n_sites, hopping, periodic=periodic)
    identity = np.eye(n_orbitals, dtype=np.complex128)
    self_energy = np.empty_like(green)
    for index, value in enumerate(omega):
        g0_inverse = (
            value + chemical_potential + 1j * broadening
        ) * identity - one_body
        self_energy[index] = g0_inverse - np.linalg.inv(green[index])
    density = one_body_density(basis_n, ground, n_orbitals)
    return LehmannResult(
        frequencies=omega,
        green=green,
        self_energy=self_energy,
        density=density,
        chemical_potential=chemical_potential,
        ground_energy=ground_energy,
        addition_threshold=addition_threshold,
        removal_threshold=removal_threshold,
    )
