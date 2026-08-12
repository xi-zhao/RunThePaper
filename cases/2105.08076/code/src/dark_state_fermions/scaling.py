"""Finite-size fits matching the paper's declared analysis contracts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from .observables import chord_length

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class FitResult:
    parameters: dict[str, float]
    relative_rms: float
    success: bool


def _relative_rms(observed: FloatArray, predicted: FloatArray) -> float:
    scale = max(float(np.ptp(observed)), float(np.mean(np.abs(observed))), 1e-12)
    return float(np.sqrt(np.mean((observed - predicted) ** 2)) / scale)


def fit_effective_central_charge(
    length: int,
    ell: FloatArray,
    entropy: FloatArray,
) -> FitResult:
    """Fit Supplement Eq. (7) on L/4 <= ell <= 3L/4."""

    ell_array = np.asarray(ell, dtype=float)
    entropy_array = np.asarray(entropy, dtype=float)
    mask = (ell_array >= length / 4) & (ell_array <= 3 * length / 4)
    if np.count_nonzero(mask) < 3:
        raise ValueError(
            "central-charge fit requires at least three points in the window"
        )
    x = np.log(chord_length(length, ell_array[mask]))
    slope, intercept = np.polyfit(x, entropy_array[mask], 1)
    prediction = slope * x + intercept
    return FitResult(
        parameters={"c": float(3.0 * slope), "s0": float(intercept)},
        relative_rms=_relative_rms(entropy_array[mask], prediction),
        success=bool(np.isfinite(slope) and slope >= -1e-8),
    )


def fit_entropy_size(lengths: FloatArray, entropy: FloatArray) -> FitResult:
    """Fit the mixed algebraic/logarithmic ansatz in Supplement Eq. (9)."""

    length_array = np.asarray(lengths, dtype=float)
    entropy_array = np.asarray(entropy, dtype=float)
    if length_array.size < 5:
        raise ValueError("entropy size fit requires at least five sizes")

    def model(parameters: FloatArray) -> FloatArray:
        amplitude, exponent, central_charge, offset = parameters
        return (
            amplitude * length_array**exponent
            + (central_charge / 3.0) * np.log(length_array / np.pi)
            + offset
        )

    def residual(parameters: FloatArray) -> FloatArray:
        return model(parameters) - entropy_array

    initial_slope = max(
        0.0,
        float(np.polyfit(np.log(length_array), entropy_array, 1)[0]),
    )
    fit = least_squares(
        residual,
        x0=np.asarray([0.2, min(0.5, max(0.05, initial_slope)), 0.5, 0.0]),
        bounds=(
            np.asarray([0.0, 0.0, 0.0, -100.0]),
            np.asarray([100.0, 1.0, 100.0, 100.0]),
        ),
        max_nfev=10000,
    )
    amplitude, exponent, central_charge, offset = fit.x
    prediction = model(fit.x)
    return FitResult(
        parameters={
            "B": float(amplitude),
            "b": float(exponent),
            "c": float(central_charge),
            "s0": float(offset),
        },
        relative_rms=_relative_rms(entropy_array, prediction),
        success=bool(fit.success),
    )


def fit_correlation_size(lengths: FloatArray, correlation: FloatArray) -> FitResult:
    """Fit `C=1/(A L^a + D L)` from Supplement Eq. (9)."""

    length_array = np.asarray(lengths, dtype=float)
    correlation_array = np.asarray(correlation, dtype=float)
    if length_array.size < 4 or np.any(correlation_array <= 0):
        raise ValueError("positive correlation data at four or more sizes are required")

    direct_slope = -float(
        np.polyfit(np.log(length_array), np.log(correlation_array), 1)[0]
    )

    def model(parameters: FloatArray) -> FloatArray:
        log_amplitude, exponent, log_linear = parameters
        amplitude = np.exp(log_amplitude)
        linear = np.exp(log_linear)
        return 1.0 / (amplitude * length_array**exponent + linear * length_array)

    def residual(parameters: FloatArray) -> FloatArray:
        return np.log(model(parameters)) - np.log(correlation_array)

    exponent_guesses = np.unique(np.clip([1.0, direct_slope, 1.5, 2.0, 2.5], 0.5, 4.0))
    fits = []
    for exponent_guess in exponent_guesses:
        denominator0 = 1.0 / correlation_array[0]
        for linear_fraction in (1e-6, 0.05, 0.25, 0.75):
            linear_guess = max(1e-14, linear_fraction * denominator0 / length_array[0])
            amplitude_guess = max(
                1e-14,
                (1.0 - linear_fraction)
                * denominator0
                / length_array[0] ** exponent_guess,
            )
            fits.append(
                least_squares(
                    residual,
                    x0=np.asarray(
                        [np.log(amplitude_guess), exponent_guess, np.log(linear_guess)]
                    ),
                    bounds=(
                        np.asarray([-40.0, 0.5, -40.0]),
                        np.asarray([40.0, 4.0, 40.0]),
                    ),
                    max_nfev=10000,
                )
            )
    fit = min(fits, key=lambda candidate: float(np.sum(candidate.fun**2)))
    prediction = model(fit.x)
    return FitResult(
        parameters={
            "A": float(np.exp(fit.x[0])),
            "a": float(fit.x[1]),
            "D": float(np.exp(fit.x[2])),
            "direct_a": float(direct_slope),
        },
        relative_rms=_relative_rms(np.log(correlation_array), np.log(prediction)),
        success=bool(fit.success),
    )


def local_power_slope(x: FloatArray, y: FloatArray) -> float:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if np.any(x_array <= 0) or np.any(y_array <= 0) or x_array.size < 3:
        raise ValueError("positive x/y arrays with at least three points are required")
    return float(np.polyfit(np.log(x_array), np.log(y_array), 1)[0])
