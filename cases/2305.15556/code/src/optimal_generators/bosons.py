"""Fixed-particle symmetric boson basis and exact bilinear operators."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from math import exp, lgamma, sqrt
from typing import Iterable, Sequence

import numpy as np
from scipy import sparse


@lru_cache(maxsize=None)
def _compositions(total: int, parts: int) -> tuple[tuple[int, ...], ...]:
    if parts == 1:
        return ((total,),)
    rows: list[tuple[int, ...]] = []
    for first in range(total, -1, -1):
        for tail in _compositions(total - first, parts - 1):
            rows.append((first, *tail))
    return tuple(rows)


@dataclass(slots=True)
class FixedNBosons:
    """Symmetric Fock representation with a fixed total particle number."""

    particles: int
    modes: tuple[str, ...]
    basis: tuple[tuple[int, ...], ...] = field(init=False)
    index: dict[tuple[int, ...], int] = field(init=False)

    def __post_init__(self) -> None:
        if self.particles < 0:
            raise ValueError("particles must be nonnegative")
        if len(self.modes) < 2 or len(set(self.modes)) != len(self.modes):
            raise ValueError("modes must contain at least two unique labels")
        self.basis = _compositions(self.particles, len(self.modes))
        self.index = {occupation: idx for idx, occupation in enumerate(self.basis)}

    @property
    def dimension(self) -> int:
        return len(self.basis)

    def mode_index(self, mode: str | int) -> int:
        if isinstance(mode, int):
            if mode < 0 or mode >= len(self.modes):
                raise IndexError(mode)
            return mode
        try:
            return self.modes.index(mode)
        except ValueError as exc:
            raise KeyError(mode) from exc

    def bilinear(self, create: str | int, annihilate: str | int) -> sparse.csr_matrix:
        """Return ``a_create^dagger a_annihilate`` in the fixed-N basis."""

        i = self.mode_index(create)
        j = self.mode_index(annihilate)
        rows: list[int] = []
        cols: list[int] = []
        data: list[complex] = []

        for col, occupation in enumerate(self.basis):
            if i == j:
                value = occupation[i]
                if value:
                    rows.append(col)
                    cols.append(col)
                    data.append(complex(value))
                continue
            if occupation[j] == 0:
                continue
            target = list(occupation)
            target[i] += 1
            target[j] -= 1
            rows.append(self.index[tuple(target)])
            cols.append(col)
            data.append(complex(sqrt((occupation[i] + 1) * occupation[j])))

        return sparse.coo_matrix(
            (data, (rows, cols)),
            shape=(self.dimension, self.dimension),
            dtype=np.complex128,
        ).tocsr()

    def number(self, mode: str | int) -> sparse.csr_matrix:
        return self.bilinear(mode, mode)

    def coherent_state(self, amplitudes: Sequence[complex]) -> np.ndarray:
        """Return ``(sum_i amplitudes[i] a_i^dagger)^N/sqrt(N!)|0>``."""

        values = np.asarray(amplitudes, dtype=np.complex128)
        if values.shape != (len(self.modes),):
            raise ValueError("one amplitude is required for every mode")
        norm = float(np.vdot(values, values).real)
        if not np.isclose(norm, 1.0, rtol=0.0, atol=1e-13):
            raise ValueError(f"single-particle amplitudes are not normalized: {norm}")

        state = np.empty(self.dimension, dtype=np.complex128)
        log_n_factorial = lgamma(self.particles + 1)
        for row, occupation in enumerate(self.basis):
            log_multinomial = log_n_factorial - sum(lgamma(n + 1) for n in occupation)
            coefficient = exp(0.5 * log_multinomial)
            for amplitude, count in zip(values, occupation, strict=True):
                if count:
                    coefficient *= amplitude**count
            state[row] = coefficient
        state /= np.linalg.norm(state)
        return state


def trace_product(left: sparse.spmatrix, right: sparse.spmatrix) -> complex:
    """Compute Tr(left @ right) without forming a matrix product."""

    return complex(left.multiply(right.T).sum())


def trace_gram(operators: Iterable[sparse.spmatrix]) -> np.ndarray:
    ops = tuple(operators)
    gram = np.empty((len(ops), len(ops)), dtype=np.complex128)
    for i, left in enumerate(ops):
        for j, right in enumerate(ops):
            gram[i, j] = trace_product(left, right)
    return gram
