"""Thermodynamic-limit XY-chain entanglement from the printed equations."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np


def correlation_coefficients(
    max_l: int,
    *,
    a: float,
    gamma: float,
    quadrature_points: int = 65536,
) -> dict[int, float]:
    """Return g_l for -max_l <= l <= max_l from paper Eq. (8).

    A midpoint grid avoids sampling the isolated gap-closing momenta at the
    critical points. ``a=inf`` denotes the zero-field limit after dividing the
    numerator by ``a``.
    """

    if max_l < 0:
        raise ValueError("max_l must be non-negative")
    if quadrature_points < 64 or quadrature_points % 2:
        raise ValueError("quadrature_points must be an even integer >= 64")
    if gamma < 0 or gamma > 1:
        raise ValueError("gamma must lie in [0, 1]")
    if a < 0:
        raise ValueError("a must be non-negative")

    points = np.arange(quadrature_points, dtype=float) + 0.5
    phi = 2.0 * np.pi * points / quadrature_points
    if np.isinf(a):
        numerator = np.cos(phi) - 1j * gamma * np.sin(phi)
    else:
        numerator = a * np.cos(phi) - 1.0 - 1j * a * gamma * np.sin(phi)
    modulus = np.abs(numerator)
    if np.any(modulus == 0):
        raise RuntimeError("midpoint quadrature unexpectedly sampled a zero mode")
    phase = numerator / modulus
    transform = np.fft.fft(phase) / quadrature_points

    coefficients: dict[int, float] = {}
    for ell in range(-max_l, max_l + 1):
        value = transform[ell % quadrature_points] * np.exp(
            -1j * np.pi * ell / quadrature_points
        )
        if abs(value.imag) > 5e-11:
            raise RuntimeError(f"g_{ell} has unexpected imaginary part {value.imag}")
        coefficients[ell] = float(value.real)
    return coefficients


def block_covariance(block_length: int, coefficients: dict[int, float]) -> np.ndarray:
    """Assemble the paper's 2L by 2L real antisymmetric B_L matrix."""

    if block_length < 1:
        raise ValueError("block_length must be positive")
    required = range(1 - block_length, block_length)
    missing = [ell for ell in required if ell not in coefficients]
    if missing:
        raise ValueError(f"missing correlation coefficients: {missing[:4]}")

    covariance = np.zeros((2 * block_length, 2 * block_length), dtype=float)
    for row_site in range(block_length):
        for column_site in range(block_length):
            ell = column_site - row_site
            covariance[2 * row_site, 2 * column_site + 1] = coefficients[ell]
            covariance[2 * row_site + 1, 2 * column_site] = -coefficients[-ell]
    return 0.5 * (covariance - covariance.T)


def covariance_modes(covariance: np.ndarray, *, tolerance: float = 5e-9) -> np.ndarray:
    """Return the L non-negative normal-mode values nu_m of B_L."""

    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.shape[0] % 2:
        raise ValueError("covariance must be an even-dimensional square matrix")
    if np.max(np.abs(matrix + matrix.T)) > tolerance:
        raise ValueError("covariance is not antisymmetric")
    block_length = matrix.shape[0] // 2
    values = np.linalg.eigvalsh(1j * matrix)
    positive = np.asarray(values[block_length:], dtype=float)
    if positive[0] < -tolerance or positive[-1] > 1.0 + tolerance:
        raise ValueError(f"unphysical covariance modes [{positive[0]}, {positive[-1]}]")
    return np.clip(positive, 0.0, 1.0)


def binary_entropy(probability: np.ndarray | float) -> np.ndarray | float:
    """Stable base-two binary entropy."""

    values = np.asarray(probability, dtype=float)
    clipped = np.clip(values, 0.0, 1.0)
    result = np.zeros_like(clipped)
    interior = (clipped > 0.0) & (clipped < 1.0)
    x = clipped[interior]
    result[interior] = -x * np.log2(x) - (1.0 - x) * np.log2(1.0 - x)
    return float(result) if result.ndim == 0 else result


def entropy_from_covariance(covariance: np.ndarray) -> tuple[float, np.ndarray]:
    """Evaluate paper Eq. (13) and return entropy plus nu_m."""

    modes = covariance_modes(covariance)
    entropy = float(np.sum(binary_entropy((1.0 + modes) / 2.0)))
    return entropy, modes


def xy_entropy(
    block_length: int,
    *,
    a: float,
    gamma: float,
    quadrature_points: int = 65536,
) -> tuple[float, np.ndarray]:
    """Compute S_L directly from Eqs. (8)-(13)."""

    coefficients = correlation_coefficients(
        block_length - 1,
        a=a,
        gamma=gamma,
        quadrature_points=quadrature_points,
    )
    return entropy_from_covariance(block_covariance(block_length, coefficients))


def entanglement_spectrum(modes: Iterable[float]) -> np.ndarray:
    """Enumerate all product eigenvalues of rho_L from paper Eq. (20)."""

    spectrum = np.array([1.0], dtype=float)
    for mode in np.asarray(list(modes), dtype=float):
        if mode < -1e-10 or mode > 1.0 + 1e-10:
            raise ValueError(f"unphysical mode {mode}")
        probability = (1.0 + np.clip(mode, 0.0, 1.0)) / 2.0
        spectrum = np.concatenate(
            (spectrum * probability, spectrum * (1.0 - probability))
        )
    total = float(np.sum(spectrum))
    if abs(total - 1.0) > 1e-10:
        raise RuntimeError(f"entanglement spectrum normalization is {total}")
    return spectrum


def majorization_margin(
    smaller_modes: Iterable[float], larger_modes: Iterable[float]
) -> dict[str, float | int | bool]:
    """Test lambda_(L+2) prec lambda_L with explicit zero padding.

    A non-negative margin means every descending partial sum of the smaller-L
    spectrum is at least that of the larger-L spectrum.
    """

    smaller = np.sort(entanglement_spectrum(smaller_modes))[::-1]
    larger = np.sort(entanglement_spectrum(larger_modes))[::-1]
    if larger.size < smaller.size:
        raise ValueError("larger_modes must describe the larger Hilbert space")
    padded = np.pad(smaller, (0, larger.size - smaller.size))
    margins = np.cumsum(padded) - np.cumsum(larger)
    # The final entry vanishes by normalization and carries no ordering signal.
    relevant = margins[:-1] if margins.size > 1 else margins
    worst_index = int(np.argmin(relevant))
    minimum = float(relevant[worst_index])
    return {
        "minimum_margin": minimum,
        "worst_partial_sum_index": worst_index + 1,
        "normalization_error": float(abs(margins[-1])),
        "passed_at_1e_10": bool(minimum >= -1e-10),
    }
