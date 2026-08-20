"""Floquet statistics, order parameters and spectral weights."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .model import FloquetEigensystem

Array = np.ndarray


def adjacent_gap_ratio(angles: Sequence[float], *, circular: bool = True) -> float:
    """Mean adjacent-gap ratio for sorted dimensionless quasienergy angles."""
    values = np.sort(np.mod(np.asarray(angles, dtype=float), 2 * np.pi))
    if values.size < 4:
        raise ValueError("at least four quasienergies are required")
    if circular:
        gaps = np.diff(np.concatenate([values, [values[0] + 2 * np.pi]]))
        following = np.roll(gaps, -1)
    else:
        gaps = np.diff(values)
        following = gaps[1:]
        gaps = gaps[:-1]
    denominator = np.maximum(gaps, following)
    ratios = np.divide(
        np.minimum(gaps, following),
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 1e-14,
    )
    return float(np.mean(ratios))


def pauli_pair_operator(
    basis: Array, system_size: int, left: int, right: int, axis: str
) -> Array:
    """Build X_i X_j or Y_i Y_j in one parity basis."""
    if axis not in {"x", "y"}:
        raise ValueError("axis must be x or y")
    if not (0 <= left < system_size and 0 <= right < system_size):
        raise ValueError("site index out of range")
    dimension = basis.size
    if left == right:
        return np.eye(dimension, dtype=complex)
    index = {int(state): row for row, state in enumerate(basis)}
    operator = np.zeros((dimension, dimension), dtype=complex)
    mask = (1 << left) ^ (1 << right)
    for column, raw_state in enumerate(basis):
        state = int(raw_state)
        coefficient = 1.0 + 0.0j
        if axis == "y":
            for site in (left, right):
                coefficient *= 1j if ((state >> site) & 1) == 0 else -1j
        operator[index[state ^ mask], column] = coefficient
    return operator


def spin_raising_operator(output_basis: Array, input_basis: Array, site: int) -> Array:
    """Build sigma-plus mapping between opposite parity sectors."""
    output_index = {int(state): row for row, state in enumerate(output_basis)}
    operator = np.zeros((output_basis.size, input_basis.size), dtype=complex)
    for column, raw_state in enumerate(input_basis):
        state = int(raw_state)
        if ((state >> site) & 1) == 0:
            continue
        target = state ^ (1 << site)
        operator[output_index[target], column] = 1.0
    return operator


def eigenstate_expectations(vectors: Array, operator: Array) -> Array:
    operated = operator @ vectors
    return np.sum(vectors.conj() * operated, axis=0)


def spin_glass_susceptibility(
    vectors: Array,
    basis: Array,
    system_size: int,
    *,
    eigenstate_stride: int = 1,
) -> float:
    """Average Eq. (6) over the selected Floquet eigenstates."""
    if eigenstate_stride < 1:
        raise ValueError("eigenstate_stride must be positive")
    selected = vectors[:, ::eigenstate_stride]
    total = np.ones(selected.shape[1], dtype=float) * system_size
    for left in range(system_size):
        for right in range(left + 1, system_size):
            operator = pauli_pair_operator(basis, system_size, left, right, "x")
            expectation = eigenstate_expectations(selected, operator).real
            total += 2.0 * expectation**2
    return float(np.mean(total / system_size**2))


def distance_correlator(
    state: Array,
    basis: Array,
    system_size: int,
    *,
    axis: str,
    distance: int | None = None,
) -> float:
    """Average C_AA over all open-chain pairs at one separation."""
    separation = system_size // 2 if distance is None else int(distance)
    pairs = [(site, site + separation) for site in range(system_size - separation)]
    values = []
    for left, right in pairs:
        operator = pauli_pair_operator(basis, system_size, left, right, axis)
        values.append(np.vdot(state, operator @ state).real)
    return float(np.mean(values))


def spectral_histogram(
    even: FloquetEigensystem,
    odd: FloquetEigensystem,
    even_basis: Array,
    odd_basis: Array,
    *,
    site: int,
    bins: int,
    gaussian_sigma_bins: float = 1.25,
) -> dict[str, Array | float]:
    """Positive full-Hilbert spin-raising spectral density on the Floquet circle."""
    if even.vectors is None or odd.vectors is None:
        raise ValueError("spectral function requires eigenvectors")
    if bins < 9:
        raise ValueError("bins must be at least 9")
    if abs(even.total_period - odd.total_period) > 1e-12:
        raise ValueError("parity sectors use different periods")
    period = even.total_period
    operator_eo = spin_raising_operator(even_basis, odd_basis, site)
    operator_oe = spin_raising_operator(odd_basis, even_basis, site)
    matrix_eo = even.vectors.conj().T @ operator_eo @ odd.vectors
    matrix_oe = odd.vectors.conj().T @ operator_oe @ even.vectors
    weight_eo = np.abs(matrix_eo) ** 2
    weight_oe = np.abs(matrix_oe) ** 2
    difference_eo = _wrapped_angle_difference(even.angles[:, None], odd.angles[None, :])
    difference_oe = _wrapped_angle_difference(odd.angles[:, None], even.angles[None, :])
    edges = np.linspace(-np.pi / period, np.pi / period, bins + 1)
    raw_eo, _ = np.histogram(
        difference_eo.ravel() / period,
        bins=edges,
        weights=weight_eo.ravel(),
    )
    raw_oe, _ = np.histogram(
        difference_oe.ravel() / period,
        bins=edges,
        weights=weight_oe.ravel(),
    )
    width = edges[1] - edges[0]
    full_dimension = even_basis.size + odd_basis.size
    raw_density = (raw_eo + raw_oe) / (full_dimension * width)
    density = _circular_gaussian(raw_density, gaussian_sigma_bins)

    literal_sum = np.sum(matrix_eo) + np.sum(matrix_oe)
    literal_imag_rms = float(
        np.sqrt(
            np.mean(
                np.concatenate([matrix_eo.imag.ravel(), matrix_oe.imag.ravel()]) ** 2
            )
        )
    )
    return {
        "omega": 0.5 * (edges[:-1] + edges[1:]),
        "density": density,
        "raw_density": raw_density,
        "integrated_weight": float(np.sum(raw_density) * width),
        "literal_unsquared_sum_real": float(literal_sum.real / full_dimension),
        "literal_unsquared_sum_imag": float(literal_sum.imag / full_dimension),
        "literal_unsquared_imag_rms": literal_imag_rms,
    }


def count_absolute_crossings(first: Sequence[float], second: Sequence[float]) -> int:
    difference = np.abs(np.asarray(first, dtype=float)) - np.abs(
        np.asarray(second, dtype=float)
    )
    signs = np.sign(difference)
    for index in range(1, signs.size):
        if signs[index] == 0:
            signs[index] = signs[index - 1]
    return int(np.count_nonzero(signs[1:] * signs[:-1] < 0))


def _wrapped_angle_difference(left: Array, right: Array) -> Array:
    return (left - right + np.pi) % (2 * np.pi) - np.pi


def _circular_gaussian(values: Array, sigma_bins: float) -> Array:
    if sigma_bins <= 0:
        return values.copy()
    radius = max(1, int(np.ceil(4 * sigma_bins)))
    offsets = np.arange(-radius, radius + 1)
    kernel = np.exp(-0.5 * (offsets / sigma_bins) ** 2)
    kernel /= np.sum(kernel)
    output = np.zeros_like(values, dtype=float)
    for offset, weight in zip(offsets, kernel, strict=True):
        output += weight * np.roll(values, int(offset))
    return output
