"""Independent numerical model for the non-Hermitian AAH paper.

This module contains physics only.  It does not import plotting code and has no
path to the frozen source figures; original pixels therefore cannot affect any
generated numerical value.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import eig
from scipy.optimize import brentq


GOLDEN_ALPHA = (np.sqrt(5.0) - 1.0) / 2.0


def aah_potential(
    indices: np.ndarray,
    *,
    potential_strength: float,
    alpha: float,
    theta: float,
    complex_phase: float,
) -> np.ndarray:
    """Return V cos(2 pi alpha n + theta + i h)."""

    n = np.asarray(indices, dtype=float)
    return potential_strength * np.cos(2.0 * np.pi * alpha * n + theta + 1j * complex_phase)


def aah_hamiltonian(
    length: int,
    *,
    hopping: float = 1.0,
    potential_strength: float = 1.0,
    alpha: float = GOLDEN_ALPHA,
    theta: float = 0.0,
    complex_phase: float = 0.0,
    boundary: str = "periodic",
    index_start: int = 1,
) -> np.ndarray:
    """Build the finite matrix printed in main Eq. (1) and Supplement (S-3)."""

    if length < 2:
        raise ValueError("length must be at least two")
    if boundary not in {"periodic", "open"}:
        raise ValueError("boundary must be 'periodic' or 'open'")

    indices = np.arange(index_start, index_start + length, dtype=float)
    diagonal = aah_potential(
        indices,
        potential_strength=potential_strength,
        alpha=alpha,
        theta=theta,
        complex_phase=complex_phase,
    )
    matrix = np.diag(diagonal.astype(complex))
    off_diagonal = np.full(length - 1, hopping, dtype=complex)
    matrix += np.diag(off_diagonal, 1) + np.diag(off_diagonal, -1)
    if boundary == "periodic":
        matrix[0, -1] = hopping
        matrix[-1, 0] = hopping
    return matrix


def dual_hatano_nelson_hamiltonian(
    length: int,
    *,
    hopping: float = 1.0,
    potential_strength: float = 1.0,
    alpha: float = GOLDEN_ALPHA,
    theta: float = 0.0,
    complex_phase: float = 0.0,
) -> np.ndarray:
    """Build the Fourier-dual matrix in Supplement Eq. (S-6)."""

    indices = np.arange(length, dtype=float)
    diagonal = 2.0 * hopping * np.cos(2.0 * np.pi * alpha * indices)
    forward = 0.5 * potential_strength * np.exp(1j * theta - complex_phase)
    backward = 0.5 * potential_strength * np.exp(-1j * theta + complex_phase)
    matrix = np.diag(diagonal.astype(complex))
    matrix += np.diag(np.full(length - 1, forward, dtype=complex), 1)
    matrix += np.diag(np.full(length - 1, backward, dtype=complex), -1)
    matrix[-1, 0] = forward
    matrix[0, -1] = backward
    return matrix


def normalized_eigensystem(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return right eigenvectors normalized columnwise."""

    values, vectors = eig(matrix, check_finite=False, overwrite_a=True)
    norms = np.linalg.norm(vectors, axis=0)
    if np.any(norms == 0.0):
        raise RuntimeError("eigensolver returned a zero eigenvector")
    return values, vectors / norms


def inverse_participation_ratios(vectors: np.ndarray) -> np.ndarray:
    """Evaluate the paper's IPR definition for eigenvector columns."""

    weights = np.abs(np.asarray(vectors, dtype=complex)) ** 2
    denominators = np.sum(weights, axis=0)
    if np.any(denominators == 0.0):
        raise ValueError("vectors must have nonzero norm")
    return np.sum(weights**2, axis=0) / denominators**2


def critical_phase(hopping: float, potential_strength: float) -> float:
    """Return h_c=log(2J/V) in the V<2J regime."""

    if hopping <= 0.0 or potential_strength <= 0.0:
        raise ValueError("hopping and potential_strength must be positive")
    return float(np.log(2.0 * hopping / potential_strength))


def winding_number(
    complex_phase: float,
    *,
    length: int,
    hopping: float = 1.0,
    potential_strength: float = 1.0,
    theta_points: int = 1025,
) -> float:
    """Numerically unwrap the determinant circle derived in Supplement S.2."""

    h_c = critical_phase(hopping, potential_strength)
    if np.isclose(complex_phase, h_c, atol=1e-14, rtol=0.0):
        return -0.5
    log_ratio = np.clip(length * (complex_phase - h_c), -700.0, 700.0)
    ratio = float(np.exp(log_ratio))
    theta = np.linspace(0.0, 2.0 * np.pi, theta_points)
    determinant_curve = 1.0 + ratio * np.exp(-1j * theta)
    phase = np.unwrap(np.angle(determinant_curve))
    return float((phase[-1] - phase[0]) / (2.0 * np.pi))


def analytic_winding(complex_phase: float, *, hopping: float = 1.0, potential_strength: float = 1.0) -> float:
    """Return the thermodynamic winding from main Eq. (6)."""

    h_c = critical_phase(hopping, potential_strength)
    if np.isclose(complex_phase, h_c, atol=1e-14, rtol=0.0):
        return -0.5
    return 0.0 if complex_phase < h_c else -1.0


def edge_state_counts(
    vectors: np.ndarray,
    *,
    edge_width: int = 12,
    minimum_edge_weight: float = 0.55,
) -> tuple[int, int]:
    """Classify normalized right eigenstates by dominant boundary weight."""

    weights = np.abs(np.asarray(vectors, dtype=complex)) ** 2
    weights /= np.sum(weights, axis=0, keepdims=True)
    if not 1 <= edge_width < weights.shape[0] // 2:
        raise ValueError("edge_width must fit within one side of the chain")
    left = np.sum(weights[:edge_width], axis=0)
    right = np.sum(weights[-edge_width:], axis=0)
    left_count = int(np.count_nonzero((left >= minimum_edge_weight) & (left > right)))
    right_count = int(np.count_nonzero((right >= minimum_edge_weight) & (right > left)))
    return left_count, right_count


@dataclass(frozen=True)
class EtalonTransmission:
    normalized_frequency: np.ndarray
    exact: np.ndarray
    first_order: np.ndarray
    reflectance: float


def etalon_transmission(
    normalized_frequency: np.ndarray,
    *,
    refractive_index: float = 2.2321,
    phase: float = 0.0,
) -> EtalonTransmission:
    """Evaluate Supplement Eqs. (S-27)-(S-29)."""

    frequency = np.asarray(normalized_frequency, dtype=float)
    if refractive_index <= 0.0:
        raise ValueError("refractive_index must be positive")
    reflectance = ((refractive_index - 1.0) / (refractive_index + 1.0)) ** 2
    propagation = 2.0 * np.pi * frequency + phase
    exact = (1.0 - reflectance) / (1.0 - reflectance * np.exp(1j * propagation))
    first_order = 1.0 - reflectance + reflectance * np.exp(1j * propagation)
    return EtalonTransmission(frequency, exact, first_order, float(reflectance))


def laser_operator(
    mode_indices: np.ndarray,
    *,
    modulation_depth: float,
    potential_strength: float,
    alpha: float,
    theta: float,
    cavity_loss: float,
    saturated_gain: float,
    modulation_to_gainwidth_ratio: float,
) -> np.ndarray:
    """Build the linear field operator in main Eq. (8) at fixed gain."""

    modes = np.asarray(mode_indices, dtype=float)
    if modes.ndim != 1 or modes.size < 3:
        raise ValueError("mode_indices must be a one-dimensional mode grid")
    hopping = modulation_depth / 2.0
    gain_profile = saturated_gain / (1.0 + 4.0 * modes**2 * modulation_to_gainwidth_ratio**2)
    diagonal = (
        potential_strength * np.exp(2j * np.pi * alpha * modes + 1j * theta)
        + 1j * (-cavity_loss + gain_profile)
    )
    matrix = np.diag(diagonal)
    coupling = np.full(modes.size - 1, hopping, dtype=complex)
    matrix += np.diag(coupling, 1) + np.diag(coupling, -1)
    return matrix


@dataclass(frozen=True)
class LaserSteadyState:
    mode_indices: np.ndarray
    normalized_spectrum: np.ndarray
    saturated_gain: float
    total_intensity: float
    residual_growth: float
    bandwidth: float


def spectral_bandwidth(mode_indices: np.ndarray, spectrum: np.ndarray) -> float:
    """Return the RMS displacement from the central axial mode."""

    modes = np.asarray(mode_indices, dtype=float)
    weights = np.asarray(spectrum, dtype=float)
    total = float(np.sum(weights))
    if total <= 0.0:
        raise ValueError("spectrum must have positive total intensity")
    probability = weights / total
    return float(np.sqrt(np.sum(modes**2 * probability)))


def stationary_laser_spectrum(
    modulation_depth: float,
    *,
    potential_strength: float = 0.14,
    alpha: float = GOLDEN_ALPHA,
    theta: float = 0.0,
    cavity_loss: float = 0.19,
    small_signal_gain: float = 0.57,
    modulation_frequency_ghz: float = 1.384,
    gain_width_ghz: float = 126.0,
    mode_limit: int = 60,
) -> LaserSteadyState:
    """Solve the neutral-growth fixed point of main Eqs. (8)-(9)."""

    if modulation_depth < 0.0:
        raise ValueError("modulation_depth must be nonnegative")
    modes = np.arange(-mode_limit, mode_limit + 1, dtype=float)
    ratio = modulation_frequency_ghz / gain_width_ghz

    def dominant(gain: float) -> tuple[float, np.ndarray]:
        matrix = laser_operator(
            modes,
            modulation_depth=modulation_depth,
            potential_strength=potential_strength,
            alpha=alpha,
            theta=theta,
            cavity_loss=cavity_loss,
            saturated_gain=gain,
            modulation_to_gainwidth_ratio=ratio,
        )
        values, vectors = normalized_eigensystem(matrix)
        index = int(np.argmax(values.imag))
        return float(values[index].imag), vectors[:, index]

    low_growth, _ = dominant(0.0)
    high_growth, _ = dominant(small_signal_gain)
    if low_growth >= 0.0:
        gain = 0.0
    elif high_growth <= 0.0:
        gain = small_signal_gain
    else:
        gain = float(brentq(lambda value: dominant(value)[0], 0.0, small_signal_gain, xtol=1e-10, rtol=1e-10))
    residual_growth, vector = dominant(gain)
    spectrum = np.abs(vector) ** 2
    spectrum /= np.sum(spectrum)
    intensity = 0.0 if gain <= 0.0 else max(small_signal_gain / gain - 1.0, 0.0)
    bandwidth = spectral_bandwidth(modes, spectrum)
    return LaserSteadyState(modes, spectrum, gain, intensity, residual_growth, bandwidth)
