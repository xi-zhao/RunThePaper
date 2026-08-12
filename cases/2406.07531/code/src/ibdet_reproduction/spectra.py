"""Dyson spectra and figure-level observables."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]
RealArray = NDArray[np.float64]


def dyson_green_function(
    one_body: ComplexArray,
    self_energy: ComplexArray,
    frequencies: Sequence[float],
    *,
    chemical_potential: float = 0.0,
    broadening: float = 0.05,
    overlap: ComplexArray | None = None,
) -> ComplexArray:
    """Solve Dyson's equation for a frequency-dependent self-energy."""

    hamiltonian = np.asarray(one_body, dtype=np.complex128)
    sigma = np.asarray(self_energy, dtype=np.complex128)
    omega = np.asarray(frequencies, dtype=float)
    if sigma.shape != (omega.size, hamiltonian.shape[0], hamiltonian.shape[1]):
        raise ValueError("self_energy shape must be (frequency,basis,basis)")
    metric = (
        np.eye(hamiltonian.shape[0], dtype=np.complex128)
        if overlap is None
        else np.asarray(overlap, dtype=np.complex128)
    )
    green = np.empty_like(sigma)
    for index, value in enumerate(omega):
        operator = (value + chemical_potential + 1j * broadening) * metric
        operator = operator - hamiltonian - sigma[index]
        green[index] = np.linalg.inv(operator)
    return green


def spectral_function(
    green_function: ComplexArray,
    *,
    overlap: ComplexArray | None = None,
) -> RealArray:
    """Return A(omega)=-(1/pi) Im Tr[S G(omega)]."""

    green = np.asarray(green_function, dtype=np.complex128)
    if green.ndim == 3:
        metric = (
            np.eye(green.shape[-1], dtype=np.complex128)
            if overlap is None
            else np.asarray(overlap, dtype=np.complex128)
        )
        trace = np.einsum("ij,wji->w", metric, green, optimize=True)
        return np.asarray(-np.imag(trace) / np.pi, dtype=float)
    if green.ndim == 4:
        metric = (
            np.eye(green.shape[-1], dtype=np.complex128)
            if overlap is None
            else np.asarray(overlap, dtype=np.complex128)
        )
        trace = np.einsum("ij,kwji->kw", metric, green, optimize=True)
        return np.asarray(-np.imag(trace) / np.pi, dtype=float)
    raise ValueError("green_function must be (w,n,n) or (k,w,n,n)")


def density_of_states(
    spectral_map: RealArray, k_weights: Sequence[float] | None = None
) -> RealArray:
    """Integrate a k-resolved spectral map using normalized weights."""

    values = np.asarray(spectral_map, dtype=float)
    if values.ndim == 1:
        return values.copy()
    if values.ndim != 2:
        raise ValueError("spectral_map must be (frequency) or (k,frequency)")
    if k_weights is None:
        weights = np.full(values.shape[0], 1.0 / values.shape[0])
    else:
        weights = np.asarray(k_weights, dtype=float)
        if weights.shape != (values.shape[0],) or np.any(weights < 0):
            raise ValueError("invalid k weights")
        weights = weights / np.sum(weights)
    return np.einsum("k,kw->w", weights, values, optimize=True)


def occupied_bandwidth(
    frequencies: Sequence[float],
    density: Sequence[float],
    *,
    chemical_potential: float = 0.0,
    relative_threshold: float = 0.02,
) -> float:
    """Estimate occupied bandwidth from a declared spectral-weight threshold."""

    omega = np.asarray(frequencies, dtype=float)
    dos = np.asarray(density, dtype=float)
    mask = (omega <= chemical_potential) & (dos >= relative_threshold * np.max(dos))
    if np.count_nonzero(mask) < 2:
        raise ValueError("not enough occupied spectral support")
    return float(chemical_potential - np.min(omega[mask]))


def neighbour_shell_correction(
    correction: ComplexArray,
    shell_labels: Sequence[int],
    reference_orbital: int,
) -> dict[int, ComplexArray]:
    """Average one row of a self-energy stack over equal neighbour shells."""

    sigma = np.asarray(correction, dtype=np.complex128)
    labels = np.asarray(shell_labels, dtype=int)
    if sigma.ndim != 3 or sigma.shape[1] != labels.size:
        raise ValueError("correction must be (frequency,basis,basis)")
    result: dict[int, ComplexArray] = {}
    for shell in sorted(set(int(value) for value in labels)):
        indices = np.flatnonzero(labels == shell)
        result[shell] = np.mean(sigma[:, reference_orbital, indices], axis=1)
    return result


def extract_gap_from_levels(
    occupied_levels: Sequence[float],
    virtual_levels: Sequence[float],
) -> float:
    """Extract a quasiparticle gap from explicitly separated level sets."""

    occupied = np.asarray(occupied_levels, dtype=float)
    virtual = np.asarray(virtual_levels, dtype=float)
    if occupied.size == 0 or virtual.size == 0:
        raise ValueError("occupied and virtual level sets must be nonempty")
    return float(np.min(virtual) - np.max(occupied))
