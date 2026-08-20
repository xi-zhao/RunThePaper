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


def fermion_mode_probabilities(mode: float) -> tuple[float, float]:
    """Return ``(empty, occupied)`` probabilities for one covariance mode.

    With the paper's definitions ``b=(d_0+i d_1)/2`` and
    ``<d_0 d_1>=i nu``, the operator identity
    ``b^dagger b=(1+i d_0 d_1)/2`` gives occupation ``(1-nu)/2``.
    The paper prints the opposite sign in Eq. (11).  Keeping the labels here
    makes that source discrepancy explicit even though binary entropy and the
    unordered product spectrum are invariant under exchanging the pair.
    """

    value = float(mode)
    if value < -1e-10 or value > 1.0 + 1e-10:
        raise ValueError(f"unphysical mode {mode}")
    clipped = float(np.clip(value, 0.0, 1.0))
    occupied = (1.0 - clipped) / 2.0
    return 1.0 - occupied, occupied


def entanglement_spectrum(modes: Iterable[float]) -> np.ndarray:
    """Enumerate all product eigenvalues of rho_L from paper Eq. (20)."""

    spectrum = np.array([1.0], dtype=float)
    for mode in np.asarray(list(modes), dtype=float):
        empty_probability, occupied_probability = fermion_mode_probabilities(mode)
        spectrum = np.concatenate(
            (spectrum * empty_probability, spectrum * occupied_probability)
        )
    total = float(np.sum(spectrum))
    if abs(total - 1.0) > 1e-10:
        raise RuntimeError(f"entanglement spectrum normalization is {total}")
    return spectrum


def entropy_from_spectrum(probabilities: Iterable[float]) -> float:
    """Return the von Neumann entropy of an explicitly enumerated spectrum.

    This is deliberately kept separate from :func:`entropy_from_covariance`.
    It gives the reproduction two numerically different paths through the
    paper's Eqs. (13) and (20): a sum of binary-mode entropies and a direct
    sum over all ``2**L`` eigenvalues.
    """

    values = np.asarray(list(probabilities), dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("probabilities must be a non-empty one-dimensional array")
    if np.min(values) < -1e-14:
        raise ValueError("probabilities must be non-negative")
    total = float(np.sum(values))
    if abs(total - 1.0) > 1e-10:
        raise ValueError(f"probabilities are not normalized: {total}")
    positive = values[values > 0.0]
    return float(-np.sum(positive * np.log2(positive)))


def retained_weight_rank(
    probabilities: Iterable[float], *, retained_weight: float
) -> int:
    """Smallest number of eigenvectors retaining a declared total weight.

    The paper uses the informal phrase "relevant eigenvectors" in its DMRG
    discussion but supplies no threshold.  Making the retained weight an
    explicit input prevents that missing convention from being hidden in the
    implementation.
    """

    if retained_weight <= 0.0 or retained_weight > 1.0:
        raise ValueError("retained_weight must lie in (0, 1]")
    values = np.asarray(list(probabilities), dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("probabilities must be a non-empty one-dimensional array")
    if np.min(values) < -1e-14:
        raise ValueError("probabilities must be non-negative")
    total = float(np.sum(values))
    if abs(total - 1.0) > 1e-10:
        raise ValueError(f"probabilities are not normalized: {total}")
    descending = np.sort(np.clip(values, 0.0, None))[::-1]
    return int(np.searchsorted(np.cumsum(descending), retained_weight, side="left") + 1)


def resolved_spectrum_rank(
    probabilities: Iterable[float], *, absolute_tolerance: float = 0.0
) -> int:
    """Count eigenvalues resolved above an explicit numerical tolerance.

    This is deliberately not called an exact rank.  Finite-precision spectra
    can underflow even when the analytic finite-block state has full support.
    Reporting this quantity beside retained-weight rank prevents a numerical
    threshold proxy from being mistaken for the paper's undefined phrase
    ``relevant eigenvectors``.
    """

    if absolute_tolerance < 0.0:
        raise ValueError("absolute_tolerance must be non-negative")
    values = np.asarray(list(probabilities), dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("probabilities must be a non-empty one-dimensional array")
    if np.min(values) < -1e-14:
        raise ValueError("probabilities must be non-negative")
    return int(np.count_nonzero(values > absolute_tolerance))


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
