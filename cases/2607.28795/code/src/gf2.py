"""Small, explicit linear-algebra helpers over GF(2)."""

from __future__ import annotations

import numpy as np


def binary_matrix(value: np.ndarray) -> np.ndarray:
    """Return a defensive uint8 copy reduced modulo two."""

    return np.asarray(value, dtype=np.uint8).copy() & 1


def matmul_mod2(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Matrix multiplication over GF(2) without uint8 accumulation overflow."""

    a = np.asarray(left, dtype=np.uint16)
    b = np.asarray(right, dtype=np.uint16)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[0]:
        raise ValueError(f"incompatible matrix shapes: {a.shape} and {b.shape}")
    return np.asarray((a @ b) & 1, dtype=np.uint8)


def rref(matrix: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Reduced row-echelon form and pivot columns over GF(2)."""

    reduced = binary_matrix(matrix)
    rows, columns = reduced.shape
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(columns):
        candidates = np.flatnonzero(reduced[pivot_row:, column])
        if candidates.size == 0:
            continue
        selected = pivot_row + int(candidates[0])
        if selected != pivot_row:
            reduced[[pivot_row, selected]] = reduced[[selected, pivot_row]]
        eliminate = np.flatnonzero(reduced[:, column])
        eliminate = eliminate[eliminate != pivot_row]
        if eliminate.size:
            reduced[eliminate] ^= reduced[pivot_row]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    return reduced, pivot_columns


def rank(matrix: np.ndarray) -> int:
    """Binary rank."""

    return len(rref(matrix)[1])


def inverse(matrix: np.ndarray) -> np.ndarray:
    """Inverse of a square binary matrix."""

    value = binary_matrix(matrix)
    rows, columns = value.shape
    if rows != columns:
        raise ValueError("GF(2) inverse requires a square matrix")
    augmented = np.concatenate((value, np.eye(rows, dtype=np.uint8)), axis=1)
    reduced, pivots = rref(augmented)
    if pivots[:rows] != list(range(rows)):
        raise ValueError("matrix is singular over GF(2)")
    if not np.array_equal(reduced[:, :rows], np.eye(rows, dtype=np.uint8)):
        raise ValueError("matrix is singular over GF(2)")
    return reduced[:, rows:]


def nullspace(matrix: np.ndarray) -> np.ndarray:
    """Return a row basis for the right null space over GF(2)."""

    value = binary_matrix(matrix)
    reduced, pivots = rref(value)
    pivot_set = set(pivots)
    free_columns = [column for column in range(value.shape[1]) if column not in pivot_set]
    basis = np.zeros((len(free_columns), value.shape[1]), dtype=np.uint8)
    for basis_row, free_column in enumerate(free_columns):
        basis[basis_row, free_column] = 1
        for row, pivot_column in enumerate(pivots):
            basis[basis_row, pivot_column] = reduced[row, free_column]
    return basis


def hamming_weights(rows: np.ndarray) -> np.ndarray:
    """Hamming weight of every row."""

    value = binary_matrix(rows)
    return np.sum(value, axis=1, dtype=np.int64)
