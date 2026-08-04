"""Formula-derived quantum-error-mitigation models.

This module contains no paper images, digitized points, or author arrays.  Its
inputs are scalar parameters and equations transcribed in the equation cards.
"""
from __future__ import annotations

from math import comb
from typing import Iterable

import numpy as np


def xor_probability(probabilities: Iterable[float] | np.ndarray) -> float | np.ndarray:
    """Probability that an odd number of independent Bernoulli events occurs."""

    values = np.asarray(probabilities, dtype=float)
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("Bernoulli probabilities must lie in [0, 1]")
    return 0.5 * (1.0 - np.prod(1.0 - 2.0 * values, axis=0))


def compose_depolarizing_probabilities(probabilities: Iterable[float]) -> float:
    """Compose total-Pauli-probability depolarizing channels.

    A channel with total non-identity Pauli probability ``p`` shrinks any
    non-identity single-qubit Pauli by ``1-4p/3``.  Shrink factors multiply.
    """

    values = np.asarray(tuple(probabilities), dtype=float)
    if np.any((values < 0.0) | (values > 0.75)):
        raise ValueError("This depolarizing composition requires p in [0, 3/4]")
    shrink = float(np.prod(1.0 - 4.0 * values / 3.0))
    return 0.75 * (1.0 - shrink)


def zne_weights(scales: Iterable[float], distance: int, order: int | None = None) -> np.ndarray:
    """Return distance-aware ZNE weights from Main Methods Eqs. (3)--(4)."""

    r = np.asarray(tuple(scales), dtype=float)
    if r.ndim != 1 or len(r) < 1 or np.any(r <= 0.0):
        raise ValueError("scales must be a non-empty positive one-dimensional sequence")
    if len(np.unique(r)) != len(r):
        raise ValueError("scales must be distinct")
    if distance < 1:
        raise ValueError("distance must be positive")
    inferred_order = len(r) - 1
    if order is None:
        order = inferred_order
    if order != inferred_order:
        raise ValueError("Kth-order extrapolation requires exactly K+1 scales")

    leading_power = (distance + 1) // 2
    matrix = np.ones((len(r), len(r)), dtype=float)
    for column in range(1, len(r)):
        matrix[:, column] = r ** (leading_power + column - 1)
    unit_constant = np.zeros(len(r), dtype=float)
    unit_constant[0] = 1.0
    return np.linalg.solve(matrix.T, unit_constant)


def zne_estimate(values: Iterable[float], scales: Iterable[float], distance: int) -> tuple[float, np.ndarray]:
    observations = np.asarray(tuple(values), dtype=float)
    r = np.asarray(tuple(scales), dtype=float)
    if observations.shape != r.shape:
        raise ValueError("values and scales must have the same shape")
    weights = zne_weights(r, distance)
    return float(weights @ observations), weights


def zne_metrics(
    values: Iterable[float],
    scales: Iterable[float],
    distance: int,
    ideal: float = 1.0,
) -> dict[str, float | list[float]]:
    """Compute mitigated value, bias, and the paper's sampling overhead."""

    observations = np.asarray(tuple(values), dtype=float)
    estimate, weights = zne_estimate(observations, scales, distance)
    weight_norm = float(np.abs(weights).sum())
    raw_variance = float(1.0 - observations[0] ** 2)
    numerator = float(weight_norm * np.sum(np.abs(weights) * (1.0 - observations**2)))
    if raw_variance < -1e-12 or numerator < -1e-12:
        raise ValueError("Pauli expectations must lie in [-1, 1]")
    if abs(raw_variance) <= 1e-15:
        overhead = 1.0 if len(observations) == 1 and abs(numerator) <= 1e-15 else float("inf")
    else:
        overhead = max(0.0, numerator / raw_variance)
    return {
        "estimate": estimate,
        "bias": abs(estimate - ideal),
        "overhead": overhead,
        "weights": weights.tolist(),
    }


def feedback_expectation(scale: float | np.ndarray, p: float, theta: float, corrected: bool) -> np.ndarray:
    """Closed-form injection-only response for Main Fig. 2."""

    r = np.asarray(scale, dtype=float)
    total_pauli_probability = r * p
    if np.any((total_pauli_probability < 0.0) | (total_pauli_probability > 1.0)):
        raise ValueError("r*p must remain a valid total Pauli probability")
    bit_flip_probability = 2.0 * total_pauli_probability / 3.0
    raw = np.cos(theta) * (1.0 - 2.0 * bit_flip_probability)
    if not corrected:
        return raw
    acceptance = (1.0 - bit_flip_probability) ** 2 + bit_flip_probability**2
    return raw / acceptance


def feedback_acceptance(scale: float | np.ndarray, p: float) -> np.ndarray:
    r = np.asarray(scale, dtype=float)
    total_pauli_probability = r * p
    if np.any((total_pauli_probability < 0.0) | (total_pauli_probability > 1.0)):
        raise ValueError("r*p must remain a valid total Pauli probability")
    q = 2.0 * total_pauli_probability / 3.0
    return (1.0 - q) ** 2 + q**2


def feedback_expectation_enumerated(scale: float, p: float, theta: float, corrected: bool) -> tuple[float, float]:
    """Enumerate all 4^3 injected Pauli patterns as an independent check."""

    total = scale * p
    if not 0.0 <= total <= 1.0:
        raise ValueError("r*p must remain a valid total Pauli probability")
    probabilities = (1.0 - total, total / 3.0, total / 3.0, total / 3.0)
    z_flip = (0, 1, 1, 0)  # I, X, Y, Z
    raw_sum = 0.0
    accepted_sum = 0.0
    corrected_sum = 0.0
    for p0 in range(4):
        for p2 in range(4):
            for p4 in range(4):
                probability = probabilities[p0] * probabilities[p2] * probabilities[p4]
                e0, e2, e4 = z_flip[p0], z_flip[p2], z_flip[p4]
                raw_sum += probability * (-1.0 if e0 else 1.0)
                if e2 == e4:
                    accepted_sum += probability
                    corrected_sum += probability * (-1.0 if e2 else 1.0)
    value = corrected_sum / accepted_sum if corrected else raw_sum
    return float(np.cos(theta) * value), accepted_sum


def repetition_logical_failure(distance: int, bit_flip_probability: float | np.ndarray) -> np.ndarray:
    """Exact majority-decoder failure probability for an odd repetition code."""

    if distance < 1 or distance % 2 == 0:
        raise ValueError("distance must be a positive odd integer")
    q = np.asarray(bit_flip_probability, dtype=float)
    if np.any((q < 0.0) | (q > 1.0)):
        raise ValueError("bit-flip probability must lie in [0, 1]")
    threshold = (distance + 1) // 2
    result = np.zeros_like(q, dtype=float)
    for errors in range(threshold, distance + 1):
        result += comb(distance, errors) * q**errors * (1.0 - q) ** (distance - errors)
    return result


def repetition_expectation(
    distance: int,
    rounds: int,
    scale: float | np.ndarray,
    injected_pauli_probability: float,
    *,
    corrected: bool,
    base_bit_flip_probability: float = 0.0,
    amplify_base: bool = False,
) -> np.ndarray:
    """Logical-Z expectation for M parity rounds plus the terminal layer."""

    if rounds < 0:
        raise ValueError("rounds must be non-negative")
    r = np.asarray(scale, dtype=float)
    injected_total = r * injected_pauli_probability
    if np.any((injected_total < 0.0) | (injected_total > 1.0)):
        raise ValueError("scaled injected Pauli probability must lie in [0, 1]")
    injected_flip = 2.0 * injected_total / 3.0
    base_scale = r if amplify_base else np.ones_like(r)
    base_flip = base_scale * base_bit_flip_probability
    if np.any((base_flip < 0.0) | (base_flip > 1.0)):
        raise ValueError("scaled base bit-flip probability must lie in [0, 1]")
    effective_flip = injected_flip + base_flip - 2.0 * injected_flip * base_flip
    layers = rounds + 1
    if corrected:
        logical_failure = repetition_logical_failure(distance, effective_flip)
        return (1.0 - 2.0 * logical_failure) ** layers
    return (1.0 - 2.0 * effective_flip) ** layers


def fixed_total_error_schedule(rounds: Iterable[int], anchor_p: float, anchor_round: int = 1) -> np.ndarray:
    """Unit probabilities that preserve cumulative error over M+1 layers."""

    values = np.asarray(tuple(rounds), dtype=int)
    if np.any(values < 0) or not 0.0 <= anchor_p <= 1.0:
        raise ValueError("invalid rounds or anchor probability")
    total = 1.0 - (1.0 - anchor_p) ** (anchor_round + 1)
    return 1.0 - (1.0 - total) ** (1.0 / (values + 1))


def bravyi_vargo_path_error(p: float | np.ndarray, distance: int) -> np.ndarray:
    """Noisy-syndrome path-like logical error fit used by Supplementary Fig. 9."""

    physical_error = np.asarray(p, dtype=float)
    if np.any((physical_error <= 0.0) | (physical_error >= 0.01)):
        raise ValueError("the cited low-p fit is used only for 0 < p < 0.01")
    if distance < 7 or distance % 4 != 3:
        raise ValueError("target-paper mapping requires d=4*r_defect-1 with d >= 7")
    defect_radius = (distance + 1.0) / 4.0
    x = 9.88 + 1.17e3 * physical_error - 7.64e4 * physical_error**2
    y = 880.0 * physical_error + 4.69e3 * physical_error**2 + 6.04e6 * physical_error**3
    negative_alpha = 7.52 + 2.0 * np.log(physical_error) + np.log1p(y)
    log_probability = negative_alpha * (defect_radius - 2.0) + 4.0 * np.log(physical_error) + x
    return np.exp(log_probability)


def logical_memory_expectation(
    scale: float | np.ndarray,
    p: float,
    distance: int,
    logical_gates: float,
) -> np.ndarray:
    """Expectation [1-2 P_L(r p)]^N evaluated stably."""

    logical_error = bravyi_vargo_path_error(np.asarray(scale, dtype=float) * p, distance)
    return np.exp(logical_gates * np.log1p(-2.0 * logical_error))
