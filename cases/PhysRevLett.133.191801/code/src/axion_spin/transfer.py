"""Independent implementations of the narrow-band xenon transfer function."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def complex_transfer_gain(
    frequency_hz: ArrayLike,
    *,
    resonance_hz: float,
    coherence_s: float,
    amplification: float,
) -> NDArray[np.complex128]:
    """Scalar Lorentzian factor multiplying the Eq. (3) quadrature matrix."""

    frequency = np.asarray(frequency_hz, dtype=float)
    if coherence_s <= 0 or amplification <= 0:
        raise ValueError("coherence_s and amplification must be positive")
    return (amplification / coherence_s) / (
        1.0 / coherence_s + 1j * 2.0 * np.pi * (frequency - resonance_hz)
    )


def transfer_matrix(
    frequency_hz: ArrayLike,
    *,
    resonance_hz: float,
    coherence_s: float,
    amplification: float,
) -> NDArray[np.complex128]:
    """Return the full 2x2 transfer matrix printed in Eq. (3)."""

    gain = complex_transfer_gain(
        frequency_hz,
        resonance_hz=resonance_hz,
        coherence_s=coherence_s,
        amplification=amplification,
    )
    quadrature = np.array([[1.0, 1.0], [-1.0, 1.0]], dtype=complex)
    return gain[..., None, None] * quadrature


def amplification_factor(
    *,
    kappa_zero: float,
    maximum_magnetization: float,
    equilibrium_polarization: float,
    gyromagnetic_ratio: float,
    coherence_s: float,
) -> float:
    """Evaluate ``4 pi kappa0 M P gamma T / 3`` from the main text."""

    values = (
        kappa_zero,
        maximum_magnetization,
        equilibrium_polarization,
        gyromagnetic_ratio,
        coherence_s,
    )
    if any(value <= 0 for value in values):
        raise ValueError("all amplification-factor inputs must be positive")
    return float(
        4.0
        * np.pi
        * kappa_zero
        * maximum_magnetization
        * equilibrium_polarization
        * gyromagnetic_ratio
        * coherence_s
        / 3.0
    )


def _uniform_time(time_s: ArrayLike) -> tuple[NDArray[np.float64], float]:
    time = np.asarray(time_s, dtype=float)
    if time.ndim != 1 or time.size < 2:
        raise ValueError("time_s must be one-dimensional with at least two samples")
    steps = np.diff(time)
    if np.any(steps <= 0) or not np.allclose(steps, steps[0], rtol=1e-10, atol=1e-14):
        raise ValueError("time_s must be a uniformly increasing grid")
    return time, float(steps[0])


def resonator_response(
    time_s: ArrayLike,
    drive: ArrayLike,
    *,
    resonance_hz: float,
    coherence_s: float,
    amplification: float,
) -> NDArray[np.complex128]:
    """Causal linear-input exact-step solution of the resonator ODE.

    The ODE is ``z' = (-1/T + i 2 pi nu_I) z + eta u/T``.  A sinusoidal
    steady state reproduces the scalar factor in Eq. (3).  Each input sample is
    treated as linear over its following time step.
    """

    time, dt = _uniform_time(time_s)
    signal = np.asarray(drive, dtype=complex)
    if signal.shape != time.shape:
        raise ValueError("drive must have the same shape as time_s")
    if coherence_s <= 0 or amplification <= 0:
        raise ValueError("coherence_s and amplification must be positive")
    lam = -1.0 / coherence_s + 1j * 2.0 * np.pi * resonance_hz
    step = np.exp(lam * dt)
    integral_constant = np.expm1(lam * dt) / lam
    integral_linear = dt * integral_constant - (step * (lam * dt - 1.0) + 1.0) / lam**2
    force = amplification / coherence_s
    output = np.zeros(signal.size, dtype=complex)
    for index in range(signal.size - 1):
        delta = signal[index + 1] - signal[index]
        output[index + 1] = (
            step * output[index]
            + force * integral_constant * signal[index]
            + force * integral_linear * delta / dt
        )
    return output


def resonator_response_rk4(
    time_s: ArrayLike,
    drive: ArrayLike,
    *,
    resonance_hz: float,
    coherence_s: float,
    amplification: float,
) -> NDArray[np.complex128]:
    """Independent fourth-order integration used only as a parity check."""

    time, dt = _uniform_time(time_s)
    signal = np.asarray(drive, dtype=complex)
    if signal.shape != time.shape:
        raise ValueError("drive must have the same shape as time_s")
    lam = -1.0 / coherence_s + 1j * 2.0 * np.pi * resonance_hz
    force = amplification / coherence_s
    output = np.zeros(signal.size, dtype=complex)
    for index in range(signal.size - 1):
        u0 = signal[index]
        u1 = signal[index + 1]
        um = 0.5 * (u0 + u1)
        value = output[index]
        k1 = lam * value + force * u0
        k2 = lam * (value + 0.5 * dt * k1) + force * um
        k3 = lam * (value + 0.5 * dt * k2) + force * um
        k4 = lam * (value + dt * k3) + force * u1
        output[index + 1] = value + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
    return output
