"""Exact Pauli enumeration for the reconstructed rotated [[9,1,3]] code."""
from __future__ import annotations

from functools import lru_cache

import numpy as np


N_DATA = 9
X_CHECKS = tuple(sum(1 << q for q in support) for support in ((0, 1, 3, 4), (1, 2), (4, 5, 7, 8), (6, 7)))
Z_CHECKS = tuple(sum(1 << q for q in support) for support in ((0, 3), (1, 2, 4, 5), (3, 4, 6, 7), (5, 8)))
LOGICAL_X = sum(1 << q for q in (1, 4, 7))
LOGICAL_Z = sum(1 << q for q in (3, 4, 5))
LOGICAL_LABELS = ("I", "X", "Y", "Z")


def _parity(mask: int) -> int:
    return mask.bit_count() & 1


def _syndrome(error_mask: int, checks: tuple[int, ...]) -> int:
    result = 0
    for index, check in enumerate(checks):
        result |= _parity(error_mask & check) << index
    return result


def _minimum_corrections(checks: tuple[int, ...]) -> dict[int, int]:
    corrections: dict[int, int] = {}
    for mask in sorted(range(1 << N_DATA), key=lambda value: (value.bit_count(), value)):
        corrections.setdefault(_syndrome(mask, checks), mask)
    if len(corrections) != 1 << len(checks):
        raise RuntimeError("check set does not generate every syndrome")
    return corrections


def _gf2_rank(rows: tuple[int, ...]) -> int:
    basis: list[int] = []
    for row in rows:
        value = row
        for pivot in basis:
            value = min(value, value ^ pivot)
        if value:
            basis.append(value)
            basis.sort(reverse=True)
    return len(basis)


@lru_cache(maxsize=1)
def _enumeration() -> tuple[np.ndarray, dict[str, object]]:
    x_correction = _minimum_corrections(Z_CHECKS)
    z_correction = _minimum_corrections(X_CHECKS)
    counts = np.zeros((N_DATA + 1, 4), dtype=np.int64)
    minimum_logical_weight = N_DATA + 1
    decoder_failures = 0

    for encoded in range(4**N_DATA):
        value = encoded
        x_mask = 0
        z_mask = 0
        weight = 0
        for qubit in range(N_DATA):
            pauli = value & 3
            value >>= 2
            if pauli:
                weight += 1
            if pauli in (1, 2):  # X or Y
                x_mask |= 1 << qubit
            if pauli in (2, 3):  # Y or Z
                z_mask |= 1 << qubit

        sx = _syndrome(x_mask, Z_CHECKS)
        sz = _syndrome(z_mask, X_CHECKS)
        residual_x = x_mask ^ x_correction[sx]
        residual_z = z_mask ^ z_correction[sz]
        if _syndrome(residual_x, Z_CHECKS) or _syndrome(residual_z, X_CHECKS):
            decoder_failures += 1
        logical_x = _parity(residual_x & LOGICAL_Z)
        logical_z = _parity(residual_z & LOGICAL_X)
        logical_class = 2 if logical_x and logical_z else 1 if logical_x else 3 if logical_z else 0
        counts[weight, logical_class] += 1

        if sx == 0 and sz == 0:
            raw_logical_x = _parity(x_mask & LOGICAL_Z)
            raw_logical_z = _parity(z_mask & LOGICAL_X)
            if raw_logical_x or raw_logical_z:
                minimum_logical_weight = min(minimum_logical_weight, weight)

    validation = {
        "x_check_rank": _gf2_rank(X_CHECKS),
        "z_check_rank": _gf2_rank(Z_CHECKS),
        "logical_anticommutation": bool(_parity(LOGICAL_X & LOGICAL_Z)),
        "logical_x_commutes": all(_parity(LOGICAL_X & check) == 0 for check in Z_CHECKS),
        "logical_z_commutes": all(_parity(LOGICAL_Z & check) == 0 for check in X_CHECKS),
        "cross_check_commutation": all(_parity(x_check & z_check) == 0 for x_check in X_CHECKS for z_check in Z_CHECKS),
        "minimum_logical_weight": minimum_logical_weight,
        "decoder_failures": decoder_failures,
        "counts_total": int(counts.sum()),
    }
    # Avoid retaining an extra large enumeration; only ten combinatorial totals are checked.
    from math import comb

    expected_by_weight = np.array([comb(N_DATA, weight) * 3**weight for weight in range(N_DATA + 1)])
    validation["weight_counts_match"] = bool(np.array_equal(counts.sum(axis=1), expected_by_weight))
    return counts, validation


def validate_code() -> dict[str, object]:
    """Return algebra, distance, decoder, and enumeration checks."""

    _, validation = _enumeration()
    return dict(validation)


def logical_channel(total_depolarizing_probability: float) -> np.ndarray:
    """Return decoded logical probabilities in I, X, Y, Z order."""

    p = float(total_depolarizing_probability)
    if not 0.0 <= p <= 0.75:
        raise ValueError("total depolarizing probability must lie in [0, 3/4]")
    counts, _ = _enumeration()
    probabilities = np.zeros(4, dtype=float)
    for weight in range(N_DATA + 1):
        probability_per_pattern = (1.0 - p) ** (N_DATA - weight) * (p / 3.0) ** weight
        probabilities += counts[weight] * probability_per_pattern
    probabilities /= probabilities.sum()
    return probabilities


def logical_attenuation(total_depolarizing_probability: float) -> tuple[float, float, np.ndarray]:
    """Return logical X/Z expectation attenuation and the full logical channel."""

    channel = logical_channel(total_depolarizing_probability)
    p_i, p_x, p_y, p_z = channel
    x_attenuation = p_i + p_x - p_y - p_z
    z_attenuation = p_i - p_x - p_y + p_z
    return float(x_attenuation), float(z_attenuation), channel
