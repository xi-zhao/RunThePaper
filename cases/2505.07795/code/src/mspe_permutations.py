"""Small-S_k audit helpers for the mixed-state projected-ensemble benchmark."""

from __future__ import annotations

from itertools import permutations
from math import prod

import numpy as np


Permutation = tuple[int, ...]


def all_permutations(k: int) -> list[Permutation]:
    return list(permutations(range(k)))


def compose(left: Permutation, right: Permutation) -> Permutation:
    """Return ``left o right`` in image notation."""

    return tuple(left[right[index]] for index in range(len(left)))


def inverse(permutation: Permutation) -> Permutation:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def cycle_count(permutation: Permutation) -> int:
    seen: set[int] = set()
    cycles = 0
    for start in range(len(permutation)):
        if start in seen:
            continue
        cycles += 1
        cursor = start
        while cursor not in seen:
            seen.add(cursor)
            cursor = permutation[cursor]
    return cycles


def right_transpose(permutation: Permutation, first: int, second: int) -> Permutation:
    transposition = list(range(len(permutation)))
    transposition[first], transposition[second] = second, first
    return compose(permutation, tuple(transposition))


def rising_factorial(value: int, order: int) -> int:
    return prod(value + offset for offset in range(order))


def permutation_trace(permutation: Permutation, d: int, n_a: int) -> int:
    return d ** (n_a * cycle_count(permutation))


def frozen_late_coefficients(d: int, m: int, k: int) -> dict[Permutation, float]:
    group = all_permutations(k)
    denominator = float(sum(d ** (m * cycle_count(g)) for g in group))
    return {g: d ** (m * cycle_count(g)) / denominator for g in group}


def normalized_late_coefficients(
    d: int, n_a: int, m: int, k: int
) -> dict[Permutation, float]:
    """Trace-normalized GHS coefficients from arXiv:2505.07795 SM."""

    group = all_permutations(k)
    denominator = float(rising_factorial(d ** (n_a + m), k))
    return {g: d ** (m * cycle_count(g)) / denominator for g in group}


def operator_trace(
    coefficients: dict[Permutation, float], d: int, n_a: int
) -> float:
    return float(
        sum(value * permutation_trace(g, d, n_a) for g, value in coefficients.items())
    )


def source_leading_correction(
    d: int, n_a: int, m: int, k: int
) -> dict[Permutation, float]:
    """Coefficient of x=d^{-(t+1)} after trace normalization.

    This implements the supplement's first-order expansion before and after
    the normalization factor C, without taking its later large-N_A limit.
    """

    group = all_permutations(k)
    weights = {g: float(d ** (m * cycle_count(g))) for g in group}
    raw_correction: dict[Permutation, float] = {}
    for g in group:
        l_g = cycle_count(g)
        correction = 0.0
        for first in range(k):
            for second in range(first + 1, k):
                gs = right_transpose(g, first, second)
                l_gs = cycle_count(gs)
                correction += (
                    d ** (0.5 * m * (l_g + l_gs + 1)) - d ** (m * l_gs)
                )
        raw_correction[g] = correction

    normalization = float(
        sum(weights[g] * permutation_trace(g, d, n_a) for g in group)
    )
    correction_normalization = float(
        sum(raw_correction[g] * permutation_trace(g, d, n_a) for g in group)
    )
    return {
        g: raw_correction[g] / normalization
        - weights[g] * correction_normalization / normalization**2
        for g in group
    }


def frozen_leading_correction(
    d: int, m: int, k: int
) -> dict[Permutation, float]:
    """Task-2 frozen-gold expression, transcribed literally."""

    group = all_permutations(k)
    weights = {g: float(d ** (m * cycle_count(g))) for g in group}
    sums: dict[Permutation, float] = {}
    for g in group:
        l_g = cycle_count(g)
        value = 0.0
        for first in range(k):
            for second in range(first + 1, k):
                delta = cycle_count(right_transpose(g, first, second)) - l_g
                value += d ** (-m) - d ** (-m * delta)
        sums[g] = value
    projection = sum(weights[g] * sums[g] for g in group) / sum(weights.values())
    return {g: weights[g] * (sums[g] - projection) for g in group}


def exact_source_coefficients(
    d: int, n_a: int, m: int, k: int, t: int
) -> dict[Permutation, float]:
    """Solve source Eq. (A3), then impose the physical trace normalization."""

    group = all_permutations(k)
    size = len(group)
    gram = np.empty((size, size), dtype=float)
    overlap = np.empty(size, dtype=float)
    for row, g in enumerate(group):
        inv_g = inverse(g)
        overlap[row] = sum(
            d
            ** (
                0.5 * m * (cycle_count(g) + cycle_count(g_prime))
                + (t + 1 - 0.5 * m) * cycle_count(compose(inv_g, g_prime))
                - k * (0.5 * m + t + 1)
            )
            for g_prime in group
        )
        for column, g_prime in enumerate(group):
            gram[row, column] = d ** (
                (t + 1) * (cycle_count(compose(inv_g, g_prime)) - k)
            )
    raw = np.linalg.solve(gram, overlap)
    normalization = sum(
        raw[index] * permutation_trace(g, d, n_a)
        for index, g in enumerate(group)
    )
    return {g: float(raw[index] / normalization) for index, g in enumerate(group)}
