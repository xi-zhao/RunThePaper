"""Qubit formulas used by the theory-only reproduction of arXiv:2607.23978.

The module deliberately exposes both the literal operator order printed in
Eq. (3) and the order that reproduces the paper's stated non-Hermitian Fisher
bound.  Keeping the distinction explicit prevents a scientific discrepancy
from being hidden in plotting code.
"""
from __future__ import annotations

import numpy as np


def probe_state(p: float) -> np.ndarray:
    """Return Eq. (1) in the computational basis."""
    _require_probability(p, "p")
    coherence = 0.5 * (2.0 * p - 1.0)
    return np.array([[0.5, coherence], [coherence, 0.5]], dtype=complex)


def encoded_state(p: float, theta: float) -> np.ndarray:
    """Apply M_theta=exp(i theta sigma_z/2), Eq. (2)."""
    phase = np.exp(1j * theta)
    coherence = 0.5 * (2.0 * p - 1.0)
    return np.array(
        [[0.5, coherence * phase], [coherence * phase.conjugate(), 0.5]],
        dtype=complex,
    )


def optimal_nonhermitian(p: float, theta: float) -> np.ndarray:
    """Return the matrix printed as A_nH in Eq. (5)."""
    _require_nonsingular_p(p)
    return np.array(
        [
            [1.0 / (2.0 * (p - 1.0)) + 1.0 / (2.0 * p), np.exp(1j * theta) / (2.0 * p * (p - 1.0))],
            [np.exp(-1j * theta) / (2.0 * p * (1.0 - p)), 1.0 / (2.0 * (1.0 - p)) - 1.0 / (2.0 * p)],
        ],
        dtype=complex,
    )


def optimal_hermitian(p: float, theta: float) -> np.ndarray:
    """Return the optimal Hermitian observable following Eq. (5)."""
    scale = 0.5 * (2.0 * p - 1.0)
    return np.array(
        [[0.0, -1j * np.exp(1j * theta) * scale], [1j * np.exp(-1j * theta) * scale, 0.0]],
        dtype=complex,
    )


def fisher_information_nonhermitian(p: np.ndarray | float) -> np.ndarray:
    p_array = np.asarray(p, dtype=float)
    return (2.0 * p_array - 1.0) ** 2 / (4.0 * p_array * (1.0 - p_array))


def fisher_information_hermitian(p: np.ndarray | float) -> np.ndarray:
    p_array = np.asarray(p, dtype=float)
    return (2.0 * p_array - 1.0) ** 2


def expectation(rho: np.ndarray, observable: np.ndarray) -> complex:
    return complex(np.trace(rho @ observable))


def polar_normalize(observable: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Return A'=A/a, R'=sqrt(A^dagger A)/a, and a=max singular value."""
    gram = observable.conjugate().T @ observable
    values, vectors = np.linalg.eigh(gram)
    values = np.clip(values.real, 0.0, None)
    root = (vectors * np.sqrt(values)) @ vectors.conjugate().T
    scale = float(np.sqrt(values.max(initial=0.0)))
    if scale <= np.finfo(float).eps:
        raise ValueError("observable must be nonzero")
    return observable / scale, root / scale, scale


def normalized_fringe(rho: np.ndarray, observable: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """Return I(phi)/n0 from Eq. (8)."""
    normalized, root, _ = polar_normalize(observable)
    mean = expectation(rho, normalized)
    root_square_mean = expectation(rho, root @ root).real
    xi = float(np.angle(mean)) if abs(mean) > 1e-14 else 0.0
    fringe = 0.25 * (
        1.0
        + root_square_mean
        + 2.0 * abs(mean) * np.cos(xi - np.asarray(phi, dtype=float) + np.pi / 2.0)
    )
    return np.real_if_close(fringe).astype(float)


def amplitude_damping(rho: np.ndarray, gamma: float) -> np.ndarray:
    """Apply the Kraus channel in Eq. (12)."""
    _require_probability(gamma, "gamma")
    e0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=complex)
    e1 = np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=complex)
    return e0 @ rho @ e0.conjugate().T + e1 @ rho @ e1.conjugate().T


def error_propagation_variance(
    p: float,
    theta: float,
    observable: np.ndarray,
    *,
    gamma: float = 0.0,
    theta_step: float = 1e-5,
    ordering: str = "literal",
) -> float:
    """Evaluate Eq. (3), with an explicit alternative operator ordering.

    ``literal`` uses A^dagger A as printed. ``paper_intended`` uses A A^dagger,
    which is equivalent to applying the printed equation to A^dagger and is
    the lane that reproduces the paper's F_nH curve.
    """
    if ordering not in {"literal", "paper_intended"}:
        raise ValueError("ordering must be 'literal' or 'paper_intended'")
    rho = amplitude_damping(encoded_state(p, theta), gamma)
    mean = expectation(rho, observable)
    product = (
        observable.conjugate().T @ observable
        if ordering == "literal"
        else observable @ observable.conjugate().T
    )
    numerator = expectation(rho, product).real - abs(mean) ** 2
    plus = expectation(amplitude_damping(encoded_state(p, theta + theta_step), gamma), observable)
    minus = expectation(amplitude_damping(encoded_state(p, theta - theta_step), gamma), observable)
    derivative = (plus - minus) / (2.0 * theta_step)
    denominator = abs(derivative) ** 2
    if denominator <= np.finfo(float).eps:
        raise ZeroDivisionError("observable expectation has zero local theta derivative")
    return float(numerator / denominator)


def central_difference(values: np.ndarray, coordinates: np.ndarray) -> np.ndarray:
    """Second-order numerical derivative, including one-sided endpoints."""
    values = np.asarray(values, dtype=float)
    coordinates = np.asarray(coordinates, dtype=float)
    if values.shape != coordinates.shape or values.ndim != 1 or values.size < 3:
        raise ValueError("values and coordinates must be equal one-dimensional arrays of length >=3")
    return np.gradient(values, coordinates, edge_order=2)


def _require_probability(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]")


def _require_nonsingular_p(p: float) -> None:
    _require_probability(p, "p")
    if p in {0.0, 1.0}:
        raise ValueError("A_nH is singular at p=0 and p=1")
