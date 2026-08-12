"""Input-driven experimental reanalysis; no paper arrays are bundled here."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import curve_fit

from .filtering import direct_estimate_at_lag


@dataclass(frozen=True)
class DecayFit:
    amplitude: float
    coherence_s: float
    frequency_hz: float
    phase_rad: float
    offset: float
    rms_residual: float


def decaying_cosine(
    time_s: ArrayLike,
    amplitude: float,
    coherence_s: float,
    frequency_hz: float,
    phase_rad: float,
    offset: float,
) -> NDArray[np.float64]:
    time = np.asarray(time_s, dtype=float)
    return offset + amplitude * np.exp(-time / coherence_s) * np.cos(
        2.0 * np.pi * frequency_hz * time + phase_rad
    )


def fit_decaying_cosine(
    time_s: ArrayLike, signal: ArrayLike, *, frequency_guess_hz: float
) -> DecayFit:
    """Fit source/sensor calibration traces with explicit physical bounds."""

    time = np.asarray(time_s, dtype=float)
    values = np.asarray(signal, dtype=float)
    if time.ndim != 1 or values.shape != time.shape or time.size < 20:
        raise ValueError("time and signal must be equal one-dimensional arrays")
    if frequency_guess_hz <= 0 or np.any(np.diff(time) <= 0):
        raise ValueError("frequency guess and time grid are invalid")
    span = float(np.ptp(values))
    initial = [
        0.5 * span,
        max(1.0, 0.25 * np.ptp(time)),
        frequency_guess_hz,
        0.0,
        float(np.mean(values)),
    ]
    lower = [
        -2.0 * span,
        np.diff(time).min(),
        0.5 * frequency_guess_hz,
        -2.0 * np.pi,
        values.min() - span,
    ]
    upper = [
        2.0 * span,
        10.0 * np.ptp(time),
        1.5 * frequency_guess_hz,
        2.0 * np.pi,
        values.max() + span,
    ]
    parameters, _ = curve_fit(
        decaying_cosine,
        time,
        values,
        p0=initial,
        bounds=(lower, upper),
        maxfev=50000,
    )
    fitted = decaying_cosine(time, *parameters)
    return DecayFit(
        amplitude=float(parameters[0]),
        coherence_s=float(parameters[1]),
        frequency_hz=float(parameters[2]),
        phase_rad=float(parameters[3]),
        offset=float(parameters[4]),
        rms_residual=float(np.sqrt(np.mean((values - fitted) ** 2))),
    )


def read_calibration_table(path: Path) -> list[dict[str, float]]:
    """Read the declared calibration-table interchange format."""

    required = {"scan_value", "polarized_xe", "coherence_s"}
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"calibration table requires columns {sorted(required)}")
        for row in reader:
            rows.append({name: float(row[name]) for name in required})
    if len(rows) < 3:
        raise ValueError("calibration table must contain at least three scan points")
    return rows


def analyze_segment_bundle(
    path: Path,
    *,
    template: ArrayLike,
    expected_lag: int = 0,
) -> dict[str, Any]:
    """Estimate every 60-second segment from a documented NPZ bundle.

    Required arrays are ``segments`` with shape (records, samples) and
    ``pulse_sign`` with one +1/-1 value per record.  This loader is only used by
    the paper-scale path after input hashes have been frozen.
    """

    with np.load(path, allow_pickle=False) as bundle:
        if "segments" not in bundle or "pulse_sign" not in bundle:
            raise ValueError("segment bundle requires segments and pulse_sign arrays")
        segments = np.asarray(bundle["segments"], dtype=float)
        signs = np.asarray(bundle["pulse_sign"], dtype=float)
    shape = np.asarray(template, dtype=float)
    if segments.ndim != 2 or signs.shape != (segments.shape[0],):
        raise ValueError("segment and pulse-sign shapes are inconsistent")
    if not np.all(np.isin(signs, (-1.0, 1.0))):
        raise ValueError("pulse_sign must contain only -1 and +1")
    estimates = np.array(
        [direct_estimate_at_lag(row, shape, expected_lag) for row in segments],
        dtype=float,
    )
    corrected = estimates * signs
    return {
        "segment_count": int(corrected.size),
        "mean": float(np.mean(corrected)),
        "sample_standard_deviation": float(np.std(corrected, ddof=1)),
        "standard_error": float(np.std(corrected, ddof=1) / np.sqrt(corrected.size)),
        "estimates": corrected,
    }
