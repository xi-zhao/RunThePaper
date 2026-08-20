"""Fixed-particle spinless-fermion Hamiltonian from Eq. (1)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from math import comb

import numpy as np


@lru_cache(maxsize=None)
def fixed_particle_basis(length: int, particles: int) -> tuple[int, ...]:
    if not 0 <= particles <= length:
        raise ValueError("particles must lie between zero and length")
    states = []
    for occupied in combinations(range(length), particles):
        state = 0
        for site in occupied:
            state |= 1 << site
        states.append(state)
    return tuple(states)


def _fermion_sign_below(state: int, site: int) -> int:
    return -1 if (state & ((1 << site) - 1)).bit_count() % 2 else 1


def apply_hop(state: int, destination: int, source: int) -> tuple[int, int] | None:
    """Apply c_destination^dagger c_source in canonical site order."""

    if not (state >> source) & 1 or (state >> destination) & 1:
        return None
    sign = _fermion_sign_below(state, source)
    intermediate = state ^ (1 << source)
    sign *= _fermion_sign_below(intermediate, destination)
    return intermediate | (1 << destination), sign


@dataclass(frozen=True)
class FermionChain:
    length: int
    particles: int
    interaction: float = 2.0
    nearest_hopping: float = 1.0
    next_nearest_hopping: float = 1.0
    periodic: bool = True

    def __post_init__(self) -> None:
        if self.length < 4:
            raise ValueError("length must be at least four")
        if not self.periodic:
            raise ValueError("the paper contract requires periodic boundaries")
        if self.particles != self.length // 2:
            raise ValueError("the paper contract requires half filling")

    @property
    def dimension(self) -> int:
        return comb(self.length, self.particles)

    @property
    def basis(self) -> tuple[int, ...]:
        return fixed_particle_basis(self.length, self.particles)

    def occupations(self) -> np.ndarray:
        return np.asarray(
            [[(state >> site) & 1 for site in range(self.length)] for state in self.basis],
            dtype=np.float64,
        )

    def clean_hamiltonian(self) -> np.ndarray:
        basis = self.basis
        index = {state: row for row, state in enumerate(basis)}
        matrix = np.zeros((len(basis), len(basis)), dtype=np.float64)

        for row, state in enumerate(basis):
            interaction_energy = 0.0
            for site in range(self.length):
                neighbor = (site + 1) % self.length
                ni = (state >> site) & 1
                nj = (state >> neighbor) & 1
                interaction_energy += self.interaction * (ni - 0.5) * (nj - 0.5)
            matrix[row, row] = interaction_energy

            for distance, amplitude in (
                (1, self.nearest_hopping),
                (2, self.next_nearest_hopping),
            ):
                for site in range(self.length):
                    neighbor = (site + distance) % self.length
                    for destination, source in ((site, neighbor), (neighbor, site)):
                        result = apply_hop(state, destination, source)
                        if result is None:
                            continue
                        new_state, sign = result
                        matrix[index[new_state], row] += amplitude * sign

        if not np.allclose(matrix, matrix.T, atol=1e-13, rtol=0.0):
            raise RuntimeError("fermionic Hamiltonian construction is not Hermitian")
        return matrix

    def disorder_vector(self, *, strength: float, seed: int) -> np.ndarray:
        if strength < 0:
            raise ValueError("disorder strength must be nonnegative")
        rng = np.random.default_rng(seed)
        raw = rng.normal(size=self.length)
        rms = float(np.sqrt(np.mean(raw * raw)))
        if rms == 0.0:
            raise RuntimeError("zero-RMS Gaussian draw")
        return strength * raw / rms

    def hamiltonian(self, *, strength: float, seed: int, clean: np.ndarray | None = None) -> np.ndarray:
        clean_matrix = self.clean_hamiltonian() if clean is None else clean
        if clean_matrix.shape != (self.dimension, self.dimension):
            raise ValueError("clean Hamiltonian has the wrong shape")
        onsite = self.occupations() @ self.disorder_vector(strength=strength, seed=seed)
        matrix = clean_matrix.copy()
        diagonal = np.diag_indices_from(matrix)
        matrix[diagonal] += onsite
        return matrix
