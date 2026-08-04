"""Detector-fixed tests for the proposed Chern-band click sum rule.

There are two physically distinct instruments in this module:

* the Mera--Ozawa bath, whose published Bloch vertex is local in momentum and
  acts as an Ohmic identity superoperator in orbital-matrix space;
* an independent scalar density probe carrying a controlled momentum q.

Only the second instrument contains the Bloch overlap whose calibrated
small-q coefficient is the integrated quantum metric.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .chern_jump_geometry import TWO_PI, qwz_d_vector


RealArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class CalibratedResponse:
    """Raw and kernel-divided response for one detector window."""

    raw_rate: float
    calibrated_weight: float
    full_geometric_weight: float
    recovery_fraction: float
    accessible_fraction: float


def texture_projector(texture: RealArray) -> ComplexArray:
    """Return P=(1+n.sigma)/2 for a normalized two-band texture."""

    if texture.ndim < 1 or texture.shape[-1] != 3:
        raise ValueError("texture must have shape (..., 3)")
    norms = np.linalg.norm(texture, axis=-1)
    if not np.allclose(norms, 1.0, atol=2e-12):
        raise ValueError("texture must be normalized")
    nx, ny, nz = np.moveaxis(texture, -1, 0)
    projector = np.empty(texture.shape[:-1] + (2, 2), dtype=np.complex128)
    projector[..., 0, 0] = 0.5 * (1.0 + nz)
    projector[..., 0, 1] = 0.5 * (nx - 1j * ny)
    projector[..., 1, 0] = 0.5 * (nx + 1j * ny)
    projector[..., 1, 1] = 0.5 * (1.0 - nz)
    return projector


def shifted_field(field: NDArray, shift: tuple[int, int]) -> NDArray:
    """Evaluate a periodic grid field at k+q for integer-grid q."""

    shifted = np.roll(field, -shift[0], axis=0)
    return np.roll(shifted, -shift[1], axis=1)


def _complement(projector: ComplexArray) -> ComplexArray:
    identity = np.eye(projector.shape[-1], dtype=np.complex128)
    return identity - projector


def density_probe_weight(
    projector: ComplexArray,
    shift: tuple[int, int],
) -> RealArray:
    """Return tr[P(k)(1-P(k+q))] for a scalar density probe."""

    shifted_complement = _complement(shifted_field(projector, shift))
    weight = np.einsum(
        "...ij,...ji->...",
        projector,
        shifted_complement,
        optimize=True,
    )
    return np.maximum(np.real_if_close(weight, tol=1000).real, 0.0)


def orbital_vertex_weight(
    projector: ComplexArray,
    shift: tuple[int, int],
    vertex: ComplexArray,
) -> RealArray:
    """Return tr[P M^dagger (1-P(k+q)) M] for a fixed orbital vertex."""

    if vertex.shape != (projector.shape[-1], projector.shape[-1]):
        raise ValueError("vertex dimension must match projector dimension")
    shifted_complement = _complement(shifted_field(projector, shift))
    weight_matrix = (
        projector
        @ vertex.conj().T
        @ shifted_complement
        @ vertex
    )
    weight = np.trace(weight_matrix, axis1=-2, axis2=-1)
    return np.maximum(np.real_if_close(weight, tol=1000).real, 0.0)


def density_probe_metric_estimator(
    projector: ComplexArray,
    shift_steps: int,
    spacing: float,
) -> float:
    """Four-direction density-probe estimator of integral tr(g)."""

    if shift_steps <= 0 or spacing <= 0.0:
        raise ValueError("shift_steps and spacing must be positive")
    shifts = (
        (shift_steps, 0),
        (-shift_steps, 0),
        (0, shift_steps),
        (0, -shift_steps),
    )
    average_weight = sum(
        density_probe_weight(projector, shift) for shift in shifts
    ) / len(shifts)
    q = shift_steps * spacing
    geometric_weight = float(np.sum(average_weight) * spacing * spacing)
    return 2.0 * geometric_weight / (q * q)


def paper_bath_complete_vertex_strength(projector: ComplexArray) -> RealArray:
    """Sum same-k interband strength over a Hilbert-Schmidt matrix basis.

    The normalized Pauli basis realizes the identity superoperator used in
    Supplemental Eqs. (74), (76), and (104). For any two-band rank-one
    projector the result is exactly one, independently of its texture.
    """

    identity = np.eye(2, dtype=np.complex128)
    sigma_x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sigma_y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    sigma_z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    basis = (identity, sigma_x, sigma_y, sigma_z)
    strength = np.zeros(projector.shape[:-2], dtype=np.float64)
    for matrix in basis:
        strength += orbital_vertex_weight(
            projector,
            shift=(0, 0),
            vertex=matrix / np.sqrt(2.0),
        )
    return strength


def interband_gap(
    size: int,
    mass: float,
    shift: tuple[int, int],
) -> RealArray:
    """Energy needed for lower(k) to upper(k+q) in the QWZ model."""

    energy = np.linalg.norm(qwz_d_vector(size, mass), axis=-1)
    return energy + shifted_field(energy, shift)


def ohmic_kernel(
    frequency: RealArray,
    eta: float = 1.0,
    cutoff: float = 4.0,
) -> RealArray:
    """Ohmic detector spectral density eta*omega*exp(-omega/cutoff)."""

    if eta < 0.0 or cutoff <= 0.0:
        raise ValueError("eta must be nonnegative and cutoff must be positive")
    frequency = np.asarray(frequency, dtype=float)
    if np.any(frequency < 0.0):
        raise ValueError("frequency must be nonnegative")
    return eta * frequency * np.exp(-frequency / cutoff)


def bose_occupation(frequency: RealArray, temperature: float) -> RealArray:
    """Bose occupation with a stable zero-temperature limit."""

    if temperature < 0.0:
        raise ValueError("temperature must be nonnegative")
    frequency = np.asarray(frequency, dtype=float)
    if temperature == 0.0:
        return np.zeros_like(frequency)
    argument = frequency / temperature
    occupation = np.zeros_like(argument)
    finite = argument < 700.0
    occupation[finite] = 1.0 / np.expm1(argument[finite])
    return occupation


def raw_absorption_rate(
    weight: RealArray,
    gap: RealArray,
    spacing: float,
    coupling: float,
    temperature: float,
    eta: float = 1.0,
    cutoff: float = 4.0,
) -> float:
    """Thermal probe absorption rate integrated over the Brillouin zone."""

    if coupling < 0.0 or spacing <= 0.0:
        raise ValueError("coupling must be nonnegative and spacing positive")
    detector_factor = (
        TWO_PI
        * coupling
        * coupling
        * ohmic_kernel(gap, eta=eta, cutoff=cutoff)
        * bose_occupation(gap, temperature)
    )
    return float(np.sum(detector_factor * weight) * spacing * spacing)


def calibrated_density_response(
    weight: RealArray,
    gap: RealArray,
    spacing: float,
    coupling: float,
    temperature: float,
    eta: float = 1.0,
    cutoff: float = 4.0,
    energy_window: tuple[float, float] | None = None,
) -> CalibratedResponse:
    """Calibrate each resolved transition before summing over frequency."""

    detector_factor = (
        TWO_PI
        * coupling
        * coupling
        * ohmic_kernel(gap, eta=eta, cutoff=cutoff)
        * bose_occupation(gap, temperature)
    )
    if energy_window is None:
        window_mask = np.ones_like(gap, dtype=bool)
    else:
        lower, upper = energy_window
        if lower < 0.0 or upper < lower:
            raise ValueError("invalid energy window")
        window_mask = (gap >= lower) & (gap <= upper)
    accessible = window_mask & (detector_factor > np.finfo(float).tiny)
    raw_contribution = detector_factor * weight
    calibrated = np.zeros_like(weight, dtype=float)
    calibrated[accessible] = (
        raw_contribution[accessible] / detector_factor[accessible]
    )
    area_element = spacing * spacing
    full_weight = float(np.sum(weight) * area_element)
    calibrated_weight = float(np.sum(calibrated) * area_element)
    accessible_weight = float(np.sum(weight[window_mask]) * area_element)
    denominator = max(full_weight, np.finfo(float).tiny)
    return CalibratedResponse(
        raw_rate=float(np.sum(raw_contribution[window_mask]) * area_element),
        calibrated_weight=calibrated_weight,
        full_geometric_weight=full_weight,
        recovery_fraction=calibrated_weight / denominator,
        accessible_fraction=accessible_weight / denominator,
    )
