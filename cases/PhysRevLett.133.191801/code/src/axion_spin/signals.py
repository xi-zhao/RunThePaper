"""Source fields and the closed resonant response from Eqs. (2) and (4)."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _time_array(time_s: ArrayLike) -> NDArray[np.float64]:
    time = np.asarray(time_s, dtype=float)
    if time.ndim != 1 or time.size < 2:
        raise ValueError(
            "time_s must be a one-dimensional array with at least two points"
        )
    if np.any(time < 0) or np.any(np.diff(time) <= 0):
        raise ValueError("time_s must be strictly increasing and nonnegative")
    return time


def rotating_free_decay(
    time_s: ArrayLike,
    *,
    amplitude: float,
    frequency_hz: float,
    coherence_s: float,
    phase_rad: float = 0.0,
) -> NDArray[np.complex128]:
    """Return Bx+i By for the rotating free-decay field in Eq. (2)."""

    time = _time_array(time_s)
    if coherence_s <= 0 or frequency_hz < 0:
        raise ValueError("coherence_s must be positive and frequency_hz nonnegative")
    return amplitude * np.exp(
        -time / coherence_s + 1j * (2.0 * np.pi * frequency_hz * time + phase_rad)
    )


def resonant_free_decay_envelope(
    time_s: ArrayLike,
    *,
    amplitude: float,
    amplification: float,
    sensor_coherence_s: float,
    source_coherence_s: float,
) -> NDArray[np.float64]:
    """Stable difference-of-exponentials envelope in Eq. (4).

    ``amplitude`` is the product ``|Bp| N_II*``.  The equal-coherence limit is
    evaluated analytically so near-degenerate parameters do not lose precision.
    """

    time = _time_array(time_s)
    ti = float(sensor_coherence_s)
    tii = float(source_coherence_s)
    if ti <= 0 or tii <= 0 or amplification <= 0:
        raise ValueError("coherence times and amplification must be positive")
    scale = max(ti, tii)
    if abs(ti - tii) <= 1e-9 * scale:
        ratio = -(time / ti) * np.exp(-time / ti)
    else:
        exponent_delta = time * (1.0 / ti - 1.0 / tii)
        numerator = -np.exp(-time / ti) * np.expm1(exponent_delta)
        ratio = numerator / (1.0 - ti / tii)
    return 2.0 * amplification * amplitude * ratio


def resonant_free_decay_response(
    time_s: ArrayLike,
    *,
    amplitude: float,
    amplification: float,
    sensor_coherence_s: float,
    source_coherence_s: float,
    frequency_hz: float,
    phase_rad: float = 0.0,
) -> NDArray[np.float64]:
    """Return the real ``By`` response printed in Eq. (4)."""

    time = _time_array(time_s)
    envelope = resonant_free_decay_envelope(
        time,
        amplitude=amplitude,
        amplification=amplification,
        sensor_coherence_s=sensor_coherence_s,
        source_coherence_s=source_coherence_s,
    )
    return envelope * np.cos(2.0 * np.pi * frequency_hz * time + phase_rad)


def gaussian_modulated_drive(
    time_s: ArrayLike,
    *,
    amplitude: float,
    center_s: float,
    sigma_s: float,
    carrier_hz: float,
    phase_rad: float = 0.0,
) -> NDArray[np.complex128]:
    """Declared Gaussian-envelope drive used for the independent feature test."""

    time = _time_array(time_s)
    if sigma_s <= 0:
        raise ValueError("sigma_s must be positive")
    envelope = amplitude * np.exp(-0.5 * ((time - center_s) / sigma_s) ** 2)
    phase = 2.0 * np.pi * carrier_hz * time + phase_rad
    return envelope * np.exp(1j * phase)


def linear_chirp_drive(
    time_s: ArrayLike,
    *,
    amplitude: float,
    start_hz: float,
    stop_hz: float,
    duration_s: float,
    envelope_ramp_s: float = 0.0,
) -> NDArray[np.complex128]:
    """Complex analytic signal with linearly increasing instantaneous frequency."""

    time = _time_array(time_s)
    if duration_s <= 0 or start_hz < 0 or stop_hz < 0:
        raise ValueError("chirp duration must be positive and frequencies nonnegative")
    slope = (stop_hz - start_hz) / duration_s
    phase = 2.0 * np.pi * (start_hz * time + 0.5 * slope * time**2)
    envelope = np.ones_like(time)
    if envelope_ramp_s > 0:
        ramp = np.clip(time / envelope_ramp_s, 0.0, 1.0)
        fall = np.clip((duration_s - time) / envelope_ramp_s, 0.0, 1.0)
        envelope = np.sin(0.5 * np.pi * np.minimum(ramp, fall)) ** 2
    envelope = np.where(time <= duration_s, envelope, 0.0)
    return amplitude * envelope * np.exp(1j * phase)
