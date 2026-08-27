"""Entanglement diagnostics for every control-grouped DQC1 bipartition."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np


@dataclass(frozen=True)
class BipartitionNegativity:
    """Negativity for one unique bipartition with the control kept in A."""

    register_qubits: int
    control_group_registers: tuple[int, ...]
    complement_registers: tuple[int, ...]
    negativity: float
    minimum_partial_transpose_eigenvalue: float


def partial_transpose(
    rho: np.ndarray,
    dimensions: tuple[int, ...] | list[int],
    transposed_subsystems: tuple[int, ...] | list[int],
) -> np.ndarray:
    """Transpose selected tensor factors of a density operator."""

    matrix = np.asarray(rho, dtype=complex)
    dims = tuple(int(value) for value in dimensions)
    if not dims or any(value < 1 for value in dims):
        raise ValueError("dimensions must contain positive integers")
    dimension = int(np.prod(dims))
    if matrix.shape != (dimension, dimension):
        raise ValueError("rho shape does not match dimensions")
    selected = tuple(sorted(set(int(value) for value in transposed_subsystems)))
    if any(value < 0 or value >= len(dims) for value in selected):
        raise ValueError("transposed subsystem index is out of range")

    tensor = matrix.reshape(*dims, *dims)
    axes = list(range(2 * len(dims)))
    for subsystem in selected:
        axes[subsystem], axes[len(dims) + subsystem] = (
            axes[len(dims) + subsystem],
            axes[subsystem],
        )
    return tensor.transpose(axes).reshape(dimension, dimension)


def negativity(
    rho: np.ndarray,
    dimensions: tuple[int, ...] | list[int],
    transposed_subsystems: tuple[int, ...] | list[int],
) -> tuple[float, float]:
    """Return ``(||rho^T_A||_1-1)/2`` and the lowest PT eigenvalue."""

    transposed = partial_transpose(rho, dimensions, transposed_subsystems)
    hermiticity_error = float(np.max(np.abs(transposed - transposed.conj().T)))
    if hermiticity_error > 1.0e-10:
        raise ValueError("partial transpose is not Hermitian")
    eigenvalues = np.linalg.eigvalsh((transposed + transposed.conj().T) / 2.0)
    value = max(0.0, float(-np.sum(eigenvalues[eigenvalues < 0.0])))
    return value, float(eigenvalues[0])


def control_grouped_bipartition_negativities(
    rho: np.ndarray,
    register_qubits: int,
) -> list[BipartitionNegativity]:
    """Enumerate every nontrivial split with the control assigned to side A.

    Side A contains the control and any proper subset of the register; side B
    contains the remaining register qubits.  Fixing the control on A removes
    the usual A/B duplicate without omitting a bipartition.
    """

    if register_qubits < 1:
        raise ValueError("register_qubits must be positive")
    dimensions = (2,) * (register_qubits + 1)
    expected = 1 << (register_qubits + 1)
    if np.asarray(rho).shape != (expected, expected):
        raise ValueError("rho dimension does not match register_qubits")

    registers = tuple(range(register_qubits))
    rows: list[BipartitionNegativity] = []
    for subset_size in range(register_qubits):
        for subset in combinations(registers, subset_size):
            complement = tuple(value for value in registers if value not in subset)
            transposed_subsystems = (0, *(value + 1 for value in subset))
            value, minimum = negativity(rho, dimensions, transposed_subsystems)
            rows.append(
                BipartitionNegativity(
                    register_qubits=register_qubits,
                    control_group_registers=subset,
                    complement_registers=complement,
                    negativity=value,
                    minimum_partial_transpose_eigenvalue=minimum,
                )
            )
    expected_partitions = (1 << register_qubits) - 1
    if len(rows) != expected_partitions:
        raise RuntimeError("bipartition enumeration is incomplete")
    return rows
