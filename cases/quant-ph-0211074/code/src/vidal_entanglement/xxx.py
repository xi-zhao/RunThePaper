"""Independent finite-chain XXX calculations for the paper's Fig. 2."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import comb

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import eigsh


@lru_cache(maxsize=None)
def fixed_weight_basis(n_spins: int, n_up: int) -> tuple[int, ...]:
    """Computational-basis integers with exactly n_up one bits."""

    if n_spins < 2 or n_up < 0 or n_up > n_spins:
        raise ValueError("invalid fixed-weight sector")
    return tuple(state for state in range(1 << n_spins) if state.bit_count() == n_up)


def xxx_hamiltonian(
    n_spins: int,
    *,
    n_up: int,
    delta: float = 1.0,
    coupling_sign: float = 1.0,
) -> tuple[csr_matrix, np.ndarray]:
    """Periodic Pauli XXZ Hamiltonian in one total-Sz sector.

    ``coupling_sign=+1`` is the antiferromagnet implied by the Fig. 2 critical
    description. ``coupling_sign=-1`` is the literal sign printed in Eq. (3).
    """

    if coupling_sign == 0:
        raise ValueError("coupling_sign must be non-zero")
    basis_tuple = fixed_weight_basis(n_spins, n_up)
    basis = np.asarray(basis_tuple, dtype=np.uint64)
    index = {state: row for row, state in enumerate(basis_tuple)}
    dimension = len(basis_tuple)
    capacity = dimension * (n_spins + 1)
    rows = np.empty(capacity, dtype=np.int32)
    columns = np.empty(capacity, dtype=np.int32)
    values = np.empty(capacity, dtype=float)
    cursor = 0

    for row, state in enumerate(basis_tuple):
        diagonal = 0.0
        for site in range(n_spins):
            neighbor = (site + 1) % n_spins
            first = (state >> site) & 1
            second = (state >> neighbor) & 1
            if first == second:
                diagonal += delta
            else:
                diagonal -= delta
                flipped = state ^ (1 << site) ^ (1 << neighbor)
                rows[cursor] = row
                columns[cursor] = index[flipped]
                values[cursor] = 2.0 * coupling_sign
                cursor += 1
        rows[cursor] = row
        columns[cursor] = row
        values[cursor] = coupling_sign * diagonal
        cursor += 1

    matrix = coo_matrix(
        (values[:cursor], (rows[:cursor], columns[:cursor])),
        shape=(dimension, dimension),
    ).tocsr()
    matrix.sum_duplicates()
    return matrix, basis


@dataclass(frozen=True)
class GroundState:
    n_spins: int
    n_up: int
    delta: float
    coupling_sign: float
    energy: float
    residual_norm: float
    translation_overlap: complex
    basis: np.ndarray
    amplitudes: np.ndarray


def _translation_overlap(
    basis: np.ndarray, amplitudes: np.ndarray, n_spins: int
) -> complex:
    index = {int(state): row for row, state in enumerate(basis)}
    mask = (1 << n_spins) - 1
    translated = np.empty_like(amplitudes)
    for row, state_value in enumerate(basis):
        state = int(state_value)
        rotated = ((state << 1) & mask) | (state >> (n_spins - 1))
        translated[index[rotated]] = amplitudes[row]
    return complex(np.vdot(amplitudes, translated))


def xxx_ground_state(
    n_spins: int,
    *,
    n_up: int | None = None,
    delta: float = 1.0,
    coupling_sign: float = 1.0,
    tolerance: float = 1e-11,
    seed: int = 2101074,
) -> GroundState:
    """Compute one extremal state by sparse exact diagonalization."""

    selected_up = n_spins // 2 if n_up is None else n_up
    matrix, basis = xxx_hamiltonian(
        n_spins,
        n_up=selected_up,
        delta=delta,
        coupling_sign=coupling_sign,
    )
    generator = np.random.default_rng(seed)
    initial = generator.normal(size=matrix.shape[0])
    values, vectors = eigsh(
        matrix,
        k=1,
        which="SA",
        v0=initial,
        tol=tolerance,
        maxiter=max(5000, 20 * n_spins),
    )
    amplitudes = np.asarray(vectors[:, 0], dtype=float)
    amplitudes /= np.linalg.norm(amplitudes)
    energy = float(values[0])
    residual = float(np.linalg.norm(matrix @ amplitudes - energy * amplitudes))
    return GroundState(
        n_spins=n_spins,
        n_up=selected_up,
        delta=delta,
        coupling_sign=coupling_sign,
        energy=energy,
        residual_norm=residual,
        translation_overlap=_translation_overlap(basis, amplitudes, n_spins),
        basis=basis,
        amplitudes=amplitudes,
    )


def _sector_configurations(n_sites: int, n_up: int) -> tuple[int, ...]:
    if n_up < 0 or n_up > n_sites:
        return ()
    return (
        fixed_weight_basis(n_sites, n_up)
        if n_sites >= 2
        else tuple(state for state in range(1 << n_sites) if state.bit_count() == n_up)
    )


def schmidt_probabilities(
    basis: np.ndarray,
    amplitudes: np.ndarray,
    *,
    n_spins: int,
    n_up: int,
    block_length: int,
) -> np.ndarray:
    """Schmidt weights assembled blockwise by conserved magnetization."""

    if block_length < 1 or block_length >= n_spins:
        raise ValueError("block_length must lie in [1, n_spins-1]")
    if len(basis) != len(amplitudes):
        raise ValueError("basis and amplitudes must have the same length")
    left_mask = (1 << block_length) - 1
    weights: list[np.ndarray] = []

    for left_up in range(block_length + 1):
        right_up = n_up - left_up
        left_states = _sector_configurations(block_length, left_up)
        right_states = _sector_configurations(n_spins - block_length, right_up)
        if not left_states or not right_states:
            continue
        left_index = {state: index for index, state in enumerate(left_states)}
        right_index = {state: index for index, state in enumerate(right_states)}
        coefficient = np.zeros((len(left_states), len(right_states)), dtype=float)
        for state_value, amplitude in zip(basis, amplitudes, strict=True):
            state = int(state_value)
            left = state & left_mask
            if left.bit_count() != left_up:
                continue
            right = state >> block_length
            coefficient[left_index[left], right_index[right]] = amplitude
        singular_values = np.linalg.svd(coefficient, compute_uv=False)
        weights.append(singular_values**2)

    result = np.concatenate(weights)
    result = result[result > 1e-15]
    result /= np.sum(result)
    return result


def entropy_from_probabilities(probabilities: np.ndarray) -> float:
    values = np.asarray(probabilities, dtype=float)
    positive = values[values > 0.0]
    return float(-np.sum(positive * np.log2(positive)))


def block_entropies(
    ground_state: GroundState, block_lengths: list[int]
) -> dict[int, float]:
    return {
        length: entropy_from_probabilities(
            schmidt_probabilities(
                ground_state.basis,
                ground_state.amplitudes,
                n_spins=ground_state.n_spins,
                n_up=ground_state.n_up,
                block_length=length,
            )
        )
        for length in block_lengths
    }


def dicke_entropy(n_spins: int, n_up: int, block_length: int) -> float:
    """Entropy of the symmetric fixed-magnetization ferromagnetic ground state."""

    probabilities = []
    denominator = comb(n_spins, n_up)
    for left_up in range(block_length + 1):
        right_up = n_up - left_up
        if 0 <= right_up <= n_spins - block_length:
            probabilities.append(
                comb(block_length, left_up)
                * comb(n_spins - block_length, right_up)
                / denominator
            )
    return entropy_from_probabilities(np.asarray(probabilities, dtype=float))
