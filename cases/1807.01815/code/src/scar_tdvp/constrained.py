"""Exact constrained-chain numerics in symmetry-adapted orbit bases.

The implementation follows the Hamiltonian printed in main Eq. (1).  It does
not consume author code, author arrays, or figure geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import sqrt

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import expm_multiply


State = tuple[int, ...]


@lru_cache(maxsize=None)
def constrained_states(length: int, max_occupation: int) -> tuple[State, ...]:
    """Enumerate periodic words with no adjacent nonzero occupations."""

    result: list[State] = []

    def visit(site: int, partial: list[int]) -> None:
        if site == length:
            if not (partial[0] and partial[-1]):
                result.append(tuple(partial))
            return
        for occupation in range(max_occupation + 1):
            if occupation and site and partial[-1]:
                continue
            if occupation and site == length - 1 and partial[0]:
                continue
            partial.append(occupation)
            visit(site + 1, partial)
            partial.pop()

    visit(0, [])
    return tuple(result)


def _rotations(state: State, step: int) -> tuple[State, ...]:
    length = len(state)
    return tuple(state[offset:] + state[:offset] for offset in range(0, length, step))


def canonical_state(state: State, symmetry: str) -> State:
    """Return a canonical representative for T^2 or the dihedral group."""

    if symmetry == "translation_two":
        return min(_rotations(state, 2))
    if symmetry == "dihedral":
        reflected = tuple(reversed(state))
        return min(_rotations(state, 1) + _rotations(reflected, 1))
    raise ValueError(f"unknown symmetry: {symmetry}")


def _spin_flip_amplitude(max_occupation: int, occupation: int, delta: int) -> float:
    if delta == 1:
        return 0.5 * sqrt((max_occupation - occupation) * (occupation + 1))
    return 0.5 * sqrt(occupation * (max_occupation - occupation + 1))


def full_hamiltonian(
    states: tuple[State, ...],
    max_occupation: int,
    *,
    omega: float = 1.0,
    deformation: float = 0.0,
) -> csr_matrix:
    """Build the full constrained Hamiltonian, including supplement Eq. (V)."""

    index = {state: position for position, state in enumerate(states)}
    spin = max_occupation / 2.0
    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    length = len(states[0])
    for column, state in enumerate(states):
        for site, occupation in enumerate(state):
            if state[(site - 1) % length] or state[(site + 1) % length]:
                continue
            local_prefactor = omega
            if deformation:
                # In the occupation convention used here, |0> has n=0.  The
                # sign below is fixed independently by projecting this matrix
                # Hamiltonian: its O(h) tangent velocity agrees with the two
                # supplemental deformed-flow equations only with this mapping.
                local_prefactor -= deformation * (
                    state[(site - 2) % length]
                    + state[(site + 2) % length]
                    - 2.0 * spin
                )
            for delta in (-1, 1):
                changed = occupation + delta
                if changed < 0 or changed > max_occupation:
                    continue
                target = list(state)
                target[site] = changed
                rows.append(index[tuple(target)])
                cols.append(column)
                values.append(
                    local_prefactor
                    * _spin_flip_amplitude(max_occupation, occupation, delta)
                )
    matrix = coo_matrix((values, (rows, cols)), shape=(len(states), len(states))).tocsr()
    return 0.5 * (matrix + matrix.T)


@dataclass
class ReducedConstrainedChain:
    """A normalized orbit-basis representation of the constrained chain."""

    length: int
    spin: float
    symmetry: str = "translation_two"

    def __post_init__(self) -> None:
        max_occupation = int(round(2 * self.spin))
        if abs(max_occupation - 2 * self.spin) > 1e-12:
            raise ValueError("spin must be integer or half-integer")
        if self.symmetry == "translation_two" and self.length % 2:
            raise ValueError("translation-by-two reduction requires even L")
        self.max_occupation = max_occupation
        self.states = constrained_states(self.length, max_occupation)
        grouped: dict[State, list[State]] = {}
        for state in self.states:
            grouped.setdefault(canonical_state(state, self.symmetry), []).append(state)
        self.representatives = tuple(sorted(grouped))
        self.members = tuple(tuple(grouped[key]) for key in self.representatives)
        self.orbit_sizes = np.asarray([len(members) for members in self.members], dtype=float)
        self.orbit_index = {state: i for i, members in enumerate(self.members) for state in members}
        self.representative_index = {state: i for i, state in enumerate(self.representatives)}
        self.hamiltonian = self._build_reduced_hamiltonian()

    @property
    def dimension(self) -> int:
        return len(self.representatives)

    def _build_reduced_hamiltonian(self) -> csr_matrix:
        rows: list[int] = []
        cols: list[int] = []
        values: list[float] = []
        for column, state in enumerate(self.representatives):
            accumulated: dict[int, float] = {}
            for site, occupation in enumerate(state):
                if state[(site - 1) % self.length] or state[(site + 1) % self.length]:
                    continue
                for delta in (-1, 1):
                    changed = occupation + delta
                    if changed < 0 or changed > self.max_occupation:
                        continue
                    target = list(state)
                    target[site] = changed
                    row = self.representative_index[
                        canonical_state(tuple(target), self.symmetry)
                    ]
                    accumulated[row] = accumulated.get(row, 0.0) + _spin_flip_amplitude(
                        self.max_occupation, occupation, delta
                    )
            for row, amplitude in accumulated.items():
                rows.append(row)
                cols.append(column)
                values.append(
                    amplitude * sqrt(self.orbit_sizes[column] / self.orbit_sizes[row])
                )
        matrix = coo_matrix(
            (values, (rows, cols)), shape=(self.dimension, self.dimension)
        ).tocsr()
        asymmetry = matrix - matrix.T
        if asymmetry.nnz and np.max(np.abs(asymmetry.data)) > 1e-10:
            raise RuntimeError("orbit edge counting did not produce a Hermitian block")
        return 0.5 * (matrix + matrix.T)

    def initial_vector(self, kind: str) -> np.ndarray:
        if kind == "zero":
            state = (0,) * self.length
        elif kind == "z2":
            state = tuple(
                0 if site % 2 == 0 else self.max_occupation
                for site in range(self.length)
            )
        else:
            raise ValueError(f"unknown initial state: {kind}")
        vector = np.zeros(self.dimension, dtype=complex)
        vector[self.orbit_index[state]] = 1.0
        return vector

    def sublattice_magnetization(self) -> np.ndarray:
        """Mean Sz on the sublattice which starts in the local |0> state."""

        values = []
        sites = tuple(range(0, self.length, 2))
        for state in self.representatives:
            values.append(np.mean([state[site] - self.spin for site in sites]))
        return np.asarray(values, dtype=float)

    def evolve(self, kind: str, times: np.ndarray) -> np.ndarray:
        times = np.asarray(times, dtype=float)
        if times.ndim != 1 or len(times) < 2 or not np.allclose(np.diff(times), times[1] - times[0]):
            raise ValueError("times must be an evenly spaced one-dimensional grid")
        return expm_multiply(
            -1j * self.hamiltonian,
            self.initial_vector(kind),
            start=float(times[0]),
            stop=float(times[-1]),
            num=len(times),
            endpoint=True,
            traceA=0.0,
        )

    def magnetization_dynamics(self, kind: str, times: np.ndarray) -> np.ndarray:
        states = self.evolve(kind, times)
        observable = self.sublattice_magnetization()
        return np.real((np.abs(states) ** 2) @ observable)

    def entanglement_dynamics(
        self, kind: str, times: np.ndarray, subsystem_sites: int
    ) -> np.ndarray:
        """Compute base-2 entropy after expanding the normalized orbit state."""

        orbit_states = self.evolve(kind, times)
        local_dimension = self.max_occupation + 1
        subsystem_dimension = local_dimension**subsystem_sites
        subsystem_index = np.empty(len(self.states), dtype=np.int64)
        environment_index = np.empty(len(self.states), dtype=np.int64)
        orbit_index = np.empty(len(self.states), dtype=np.int64)
        orbit_weight = np.empty(len(self.states), dtype=float)
        for position, state in enumerate(self.states):
            left = 0
            right = 0
            for occupation in state[:subsystem_sites]:
                left = left * local_dimension + occupation
            for occupation in state[subsystem_sites:]:
                right = right * local_dimension + occupation
            idx = self.orbit_index[state]
            subsystem_index[position] = left
            environment_index[position] = right
            orbit_index[position] = idx
            orbit_weight[position] = 1.0 / sqrt(self.orbit_sizes[idx])

        grouped: dict[int, list[int]] = {}
        for position, environment in enumerate(environment_index):
            grouped.setdefault(int(environment), []).append(position)
        pair_left: list[int] = []
        pair_right: list[int] = []
        density_row: list[int] = []
        density_col: list[int] = []
        for positions in grouped.values():
            for left_position in positions:
                for right_position in positions:
                    pair_left.append(left_position)
                    pair_right.append(right_position)
                    density_row.append(int(subsystem_index[left_position]))
                    density_col.append(int(subsystem_index[right_position]))
        pair_left_array = np.asarray(pair_left, dtype=np.int64)
        pair_right_array = np.asarray(pair_right, dtype=np.int64)
        density_row_array = np.asarray(density_row, dtype=np.int64)
        density_col_array = np.asarray(density_col, dtype=np.int64)

        entropies = np.empty(len(times), dtype=float)
        for time_index, coefficients in enumerate(orbit_states):
            amplitudes = coefficients[orbit_index] * orbit_weight
            density = np.zeros((subsystem_dimension, subsystem_dimension), dtype=complex)
            np.add.at(
                density,
                (density_row_array, density_col_array),
                amplitudes[pair_left_array] * amplitudes[pair_right_array].conj(),
            )
            eigenvalues = np.linalg.eigvalsh(density)
            eigenvalues = eigenvalues[eigenvalues > 1e-14]
            entropies[time_index] = float(-np.sum(eigenvalues * np.log2(eigenvalues)))
        return entropies

    def adjacent_gap_ratio(self) -> float:
        eigenvalues = np.linalg.eigvalsh(self.hamiltonian.toarray())
        gaps = np.diff(eigenvalues)
        scale = max(float(np.max(np.abs(eigenvalues))), 1.0)
        gaps = gaps[gaps > 1e-10 * scale]
        if len(gaps) < 3:
            return float("nan")
        ratios = np.minimum(gaps[1:], gaps[:-1]) / np.maximum(gaps[1:], gaps[:-1])
        return float(np.mean(ratios))


def thermal_magnetization(spin: float) -> float:
    root = sqrt(1.0 + 8.0 * spin)
    return -spin * (-1.0 + 4.0 * spin + root) / (1.0 + 8.0 * spin + root)
