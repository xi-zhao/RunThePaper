"""PSD-weighted template estimation without using any paper trace as data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.fft import next_fast_len


@dataclass(frozen=True)
class FilterResult:
    lags: NDArray[np.int64]
    estimates: NDArray[np.float64]
    best_lag: int
    best_amplitude: float


def _vectors(
    data: ArrayLike, template: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    record = np.asarray(data, dtype=float)
    shape = np.asarray(template, dtype=float)
    if record.ndim != 1 or shape.ndim != 1 or shape.size < 2:
        raise ValueError("data and template must be one-dimensional")
    if record.size < shape.size:
        raise ValueError("data must be at least as long as template")
    if not np.all(np.isfinite(record)) or not np.all(np.isfinite(shape)):
        raise ValueError("data and template must be finite")
    if np.dot(shape, shape) <= 0:
        raise ValueError("template must have nonzero norm")
    return record, shape


def matched_filter(
    data: ArrayLike,
    template: ArrayLike,
    *,
    one_sided_psd: ArrayLike | None = None,
) -> FilterResult:
    """Return valid-lag Eq. (5) amplitudes with unit-injection normalization."""

    record, shape = _vectors(data, template)
    nfft = next_fast_len(record.size + shape.size - 1)
    data_fft = np.fft.rfft(record, n=nfft)
    template_fft = np.fft.rfft(shape, n=nfft)
    if one_sided_psd is None:
        psd = np.ones_like(data_fft.real)
    else:
        psd = np.asarray(one_sided_psd, dtype=float)
        if (
            psd.shape != data_fft.shape
            or np.any(psd <= 0)
            or not np.all(np.isfinite(psd))
        ):
            raise ValueError(
                "one_sided_psd must be positive, finite, and match the rFFT grid"
            )
    circular = np.fft.irfft(data_fft * np.conjugate(template_fft) / psd, n=nfft)
    normalization = float(np.fft.irfft(np.abs(template_fft) ** 2 / psd, n=nfft)[0])
    lags = np.arange(record.size - shape.size + 1, dtype=np.int64)
    estimates = np.asarray(circular[lags] / normalization, dtype=float)
    best_index = int(np.argmax(np.abs(estimates)))
    return FilterResult(
        lags=lags,
        estimates=estimates,
        best_lag=int(lags[best_index]),
        best_amplitude=float(estimates[best_index]),
    )


def direct_estimate_at_lag(data: ArrayLike, template: ArrayLike, lag: int) -> float:
    """Direct white-noise least-squares estimator for an independent check."""

    record, shape = _vectors(data, template)
    if lag < 0 or lag + shape.size > record.size:
        raise ValueError("lag does not place the full template inside data")
    return float(np.dot(record[lag : lag + shape.size], shape) / np.dot(shape, shape))


def inject_template(
    data: ArrayLike, template: ArrayLike, *, lag: int, amplitude: float
) -> NDArray[np.float64]:
    """Return a copy with one full template injected at a declared lag."""

    record, shape = _vectors(data, template)
    if lag < 0 or lag + shape.size > record.size:
        raise ValueError("lag does not place the full template inside data")
    output = record.copy()
    output[lag : lag + shape.size] += amplitude * shape
    return output


def white_noise_estimator_sigma(template: ArrayLike, sample_sigma: float) -> float:
    """Analytic standard deviation of the unit-normalized white-noise estimate."""

    shape = np.asarray(template, dtype=float)
    if sample_sigma <= 0 or shape.ndim != 1 or np.dot(shape, shape) <= 0:
        raise ValueError("sample_sigma and template norm must be positive")
    return float(sample_sigma / np.sqrt(np.dot(shape, shape)))


def deterministic_sensor_noise(
    time_s: ArrayLike,
    *,
    sample_sigma: float,
    line_frequency_hz: float,
    line_amplitude: float,
    seed: int,
) -> NDArray[np.float64]:
    """Declared synthetic noise for algorithm validation, never paper data."""

    time = np.asarray(time_s, dtype=float)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sample_sigma, size=time.size)
    line_phase = rng.uniform(0.0, 2.0 * np.pi)
    return noise + line_amplitude * np.sin(
        2.0 * np.pi * line_frequency_hz * time + line_phase
    )
