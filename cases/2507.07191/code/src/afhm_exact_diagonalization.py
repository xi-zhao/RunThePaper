"""Exact-diagonalization primitives for the paper's 4x4 AFHM case study.

The public paper fixes the Hamiltonian and the middle-chain bipartition but
does not ship its numerical code.  This module therefore makes every choice
needed by the independent reproduction explicit: row-major site labels,
fixed-magnetization sectors, a real-valued Hamiltonian, and the first half of
the site labels as subsystem A.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class EntropyBatch:
    """Per-eigenstate half-chain entanglement values."""

    min_entropy: np.ndarray
    von_neumann_entropy: np.ndarray


def schmidt_probabilities_from_sector_state(
    state: Sequence[float],
    basis: Sequence[int],
    number_of_spins: int,
    number_up: int,
) -> np.ndarray:
    """Return the descending half-chain Schmidt probabilities of one state."""

    vector = np.asarray(state, dtype=np.float64)
    if vector.ndim != 1 or len(vector) != len(basis):
        raise ValueError("state must be a vector matching the sector basis")
    probabilities: list[np.ndarray] = []
    for selected, rows, columns in schmidt_block_indices(
        basis,
        number_of_spins,
        number_up,
    ):
        matrix = vector[selected].reshape(columns, rows).T
        probabilities.append(np.linalg.svd(matrix, compute_uv=False) ** 2)
    output = np.sort(np.concatenate(probabilities))[::-1]
    if not np.isclose(output.sum(), np.dot(vector, vector), atol=1e-11):
        raise RuntimeError("Schmidt probabilities do not preserve state norm")
    return output


def square_torus_bonds(linear_size: int) -> tuple[tuple[int, int], ...]:
    """Return distinct nearest-neighbour bonds of an LxL periodic square grid.

    Site ``x + L*y`` is the row-major label.  Deduplication matters only for
    the tiny L=2 test lattice, where +x and -x identify the same neighbour.
    """

    if linear_size < 2:
        raise ValueError("linear_size must be at least 2")
    bonds: set[tuple[int, int]] = set()
    for y in range(linear_size):
        for x in range(linear_size):
            site = x + linear_size * y
            for neighbour in (
                ((x + 1) % linear_size) + linear_size * y,
                x + linear_size * ((y + 1) % linear_size),
            ):
                bonds.add(tuple(sorted((site, neighbour))))
    return tuple(sorted(bonds))


def fixed_magnetization_basis(number_of_spins: int, number_up: int) -> np.ndarray:
    """Return sorted computational-basis integers with ``number_up`` one bits."""

    if not 0 <= number_up <= number_of_spins:
        raise ValueError("number_up must lie in [0, number_of_spins]")
    states = [sum(1 << index for index in occupied) for occupied in combinations(range(number_of_spins), number_up)]
    return np.asarray(sorted(states), dtype=np.int64)


def build_sector_hamiltonian(
    number_of_spins: int,
    bonds: Iterable[tuple[int, int]],
    basis: Sequence[int],
) -> np.ndarray:
    """Build H=sum_<ij> S_i.S_j in a fixed-magnetization basis.

    In the computational basis, equal spins contribute +1/4 to the diagonal;
    unequal spins contribute -1/4 and are exchanged with amplitude 1/2.
    """

    states = np.asarray(basis, dtype=np.int64)
    lookup = {int(state): index for index, state in enumerate(states)}
    hamiltonian = np.zeros((len(states), len(states)), dtype=np.float64)
    normalized_bonds = tuple(tuple(sorted(bond)) for bond in bonds)
    for column, state_value in enumerate(states):
        state = int(state_value)
        diagonal = 0.0
        for left, right in normalized_bonds:
            if not (0 <= left < right < number_of_spins):
                raise ValueError(f"invalid bond {(left, right)}")
            left_bit = (state >> left) & 1
            right_bit = (state >> right) & 1
            if left_bit == right_bit:
                diagonal += 0.25
            else:
                diagonal -= 0.25
                flipped = state ^ (1 << left) ^ (1 << right)
                hamiltonian[lookup[flipped], column] += 0.5
        hamiltonian[column, column] += diagonal
    return hamiltonian


def schmidt_block_indices(
    basis: Sequence[int],
    number_of_spins: int,
    number_up: int,
) -> tuple[tuple[np.ndarray, int, int], ...]:
    """Describe coefficient-matrix blocks for the equal half-chain cut."""

    if number_of_spins % 2:
        raise ValueError("the reproduction uses an even equal bipartition")
    half = number_of_spins // 2
    mask = (1 << half) - 1
    states = np.asarray(basis, dtype=np.int64)
    blocks: list[tuple[np.ndarray, int, int]] = []
    for number_up_a in range(max(0, number_up - half), min(half, number_up) + 1):
        number_up_b = number_up - number_up_a
        selected = np.asarray(
            [
                index
                for index, state in enumerate(states)
                if (int(state) & mask).bit_count() == number_up_a
            ],
            dtype=np.int64,
        )
        rows = len(tuple(combinations(range(half), number_up_a)))
        columns = len(tuple(combinations(range(half), number_up_b)))
        if len(selected) != rows * columns:
            raise RuntimeError("basis ordering does not form the expected Schmidt blocks")
        blocks.append((selected, rows, columns))
    return tuple(blocks)


def entropies_from_sector_eigenvectors(
    eigenvectors,
    basis: Sequence[int],
    number_of_spins: int,
    number_up: int,
    *,
    batch_size: int = 256,
) -> EntropyBatch:
    """Compute S_min and S_1 for every eigenvector using batched block SVDs.

    ``eigenvectors`` is a torch tensor whose columns are normalized states.
    Keeping this function backend-local avoids transferring the largest
    12,870 x 12,870 eigenvector matrix away from the A100.
    """

    import torch

    if eigenvectors.ndim != 2 or eigenvectors.shape[0] != len(basis):
        raise ValueError("eigenvectors must be a square column-eigenvector matrix")
    blocks = schmidt_block_indices(basis, number_of_spins, number_up)
    count = eigenvectors.shape[1]
    s_min = torch.empty(count, dtype=eigenvectors.dtype, device=eigenvectors.device)
    s_one = torch.empty_like(s_min)
    tiny = torch.finfo(eigenvectors.dtype).tiny

    for start in range(0, count, batch_size):
        stop = min(start + batch_size, count)
        entropy = torch.zeros(stop - start, dtype=eigenvectors.dtype, device=eigenvectors.device)
        largest_probability = torch.zeros_like(entropy)
        for selected_cpu, rows, columns in blocks:
            selected = torch.as_tensor(selected_cpu, dtype=torch.long, device=eigenvectors.device)
            coefficients = eigenvectors.index_select(0, selected)[:, start:stop].T
            # Sorted integer basis order is B-major then A-major for fixed
            # particle counts, hence the reshape followed by the transpose.
            matrices = coefficients.reshape(stop - start, columns, rows).transpose(1, 2)
            singular_values = torch.linalg.svdvals(matrices)
            probabilities = singular_values.square()
            entropy -= torch.sum(
                torch.where(probabilities > 0, probabilities * torch.log2(probabilities.clamp_min(tiny)), probabilities),
                dim=1,
            )
            largest_probability = torch.maximum(largest_probability, probabilities[:, 0])
        s_one[start:stop] = entropy
        s_min[start:stop] = -torch.log2(largest_probability)

    return EntropyBatch(
        min_entropy=s_min.detach().cpu().numpy(),
        von_neumann_entropy=s_one.detach().cpu().numpy(),
    )


def bin_entropies(
    excitation_energy: Sequence[float],
    min_entropy: Sequence[float],
    von_neumann_entropy: Sequence[float],
    *,
    width: float = 0.1,
) -> list[dict[str, float | int]]:
    """Apply the paper's half-open [0.1j-0.05, 0.1j+0.05) bins."""

    energies = np.asarray(excitation_energy, dtype=np.float64)
    s_min = np.asarray(min_entropy, dtype=np.float64)
    s_one = np.asarray(von_neumann_entropy, dtype=np.float64)
    if not (energies.shape == s_min.shape == s_one.shape):
        raise ValueError("energy and entropy arrays must have identical shapes")
    indices = np.floor((energies + width / 2) / width + 1e-12).astype(np.int64)
    rows: list[dict[str, float | int]] = []
    for index in np.unique(indices):
        selected = indices == index
        rows.append(
            {
                "bin_index": int(index),
                "excitation_energy": float(index * width),
                "state_count": int(np.sum(selected)),
                "s_min": float(np.mean(s_min[selected])),
                "s_1": float(np.mean(s_one[selected])),
            }
        )
    return rows
