"""Rheology observables and preregistered falsification diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class TransitionResult:
    thickening_rate: float | None
    thinning_rate: float | None
    maximum_slope: float
    slope: FloatArray


def _positive_sorted(x: FloatArray, y: FloatArray) -> tuple[FloatArray, FloatArray]:
    first = np.asarray(x, dtype=np.float64)
    second = np.asarray(y, dtype=np.float64)
    if first.shape != second.shape or first.ndim != 1:
        raise ValueError("x and y must be one-dimensional arrays with equal shape")
    valid = np.isfinite(first) & np.isfinite(second) & (first > 0.0) & (second > 0.0)
    if np.count_nonzero(valid) < 2:
        raise ValueError("at least two positive finite samples are required")
    order = np.argsort(first[valid])
    return first[valid][order], second[valid][order]


def log_slope(shear_rate: FloatArray, stress: FloatArray) -> FloatArray:
    """Compute ``d log(stress) / d log(shear_rate)`` on an irregular grid."""

    rate, sigma = _positive_sorted(shear_rate, stress)
    return np.gradient(np.log(sigma), np.log(rate), edge_order=1)


def transition_rates(
    shear_rate: FloatArray,
    stress: FloatArray,
    *,
    thickening_threshold: float = 1.2,
    thinning_threshold: float = 0.9,
) -> TransitionResult:
    rate, sigma = _positive_sorted(shear_rate, stress)
    slope = log_slope(rate, sigma)
    above = np.flatnonzero(slope > thickening_threshold)
    thickening_index = int(above[0]) if len(above) else None
    thickening = float(rate[thickening_index]) if thickening_index is not None else None
    thinning: float | None = None
    if thickening_index is not None:
        below = np.flatnonzero(slope[thickening_index:] < thinning_threshold)
        if len(below):
            thinning = float(rate[thickening_index + int(below[0])])
    return TransitionResult(
        thickening_rate=thickening,
        thinning_rate=thinning,
        maximum_slope=float(np.max(slope)),
        slope=slope,
    )


def newtonian_viscosity(
    shear_rate: FloatArray,
    stress: FloatArray,
    *,
    point_count: int = 3,
) -> tuple[float, float]:
    """Fit the low-rate branch through the origin and return eta and relative RMS."""

    rate, sigma = _positive_sorted(shear_rate, stress)
    count = min(max(point_count, 2), len(rate))
    x = rate[:count]
    y = sigma[:count]
    eta = float(np.dot(x, y) / np.dot(x, x))
    residual = y - eta * x
    relative_rms = float(np.sqrt(np.mean(residual**2)) / max(np.mean(y), 1e-30))
    return eta, relative_rms


def fit_vft(activity: FloatArray, viscosity: FloatArray) -> dict[str, float]:
    """Fit ``log eta = a + b/(v-vc)`` by an explicit vc grid search."""

    v, eta = _positive_sorted(activity, viscosity)
    lower = max(0.0, float(np.min(v)) - 2.0 * float(np.ptp(v)))
    upper = float(np.min(v)) - max(1e-6, 1e-3 * float(np.ptp(v)))
    candidates = np.linspace(lower, upper, 500, dtype=np.float64)
    best: dict[str, float] | None = None
    target = np.log(eta)
    for critical in candidates:
        coordinate = 1.0 / (v - critical)
        design = np.column_stack([np.ones_like(coordinate), coordinate])
        coefficient, *_ = np.linalg.lstsq(design, target, rcond=None)
        prediction = design @ coefficient
        rms = float(np.sqrt(np.mean((target - prediction) ** 2)))
        if best is None or rms < best["log_rms"]:
            best = {
                "critical_activity": float(critical),
                "log_prefactor": float(coefficient[0]),
                "activation_scale": float(coefficient[1]),
                "log_rms": rms,
            }
    if best is None:
        raise RuntimeError("VFT search unexpectedly produced no candidate")
    return best


def power_law_fit(x: FloatArray, y: FloatArray) -> dict[str, float]:
    first, second = _positive_sorted(x, y)
    coefficient = np.polyfit(np.log(first), np.log(second), 1)
    prediction = np.polyval(coefficient, np.log(first))
    residual = np.log(second) - prediction
    total = np.log(second) - np.mean(np.log(second))
    r_squared = 1.0 - float(np.sum(residual**2) / max(np.sum(total**2), 1e-30))
    return {
        "exponent": float(coefficient[0]),
        "prefactor": float(np.exp(coefficient[1])),
        "log_rms": float(np.sqrt(np.mean(residual**2))),
        "r_squared": r_squared,
    }


def linear_fit_through_origin(x: FloatArray, y: FloatArray) -> tuple[float, float, float]:
    first = np.asarray(x, dtype=np.float64)
    second = np.asarray(y, dtype=np.float64)
    valid = np.isfinite(first) & np.isfinite(second)
    if np.count_nonzero(valid) < 2:
        raise ValueError("at least two finite samples are required")
    first = first[valid]
    second = second[valid]
    slope = float(np.dot(first, second) / max(np.dot(first, first), 1e-30))
    intercept = 0.0
    prediction = slope * first
    residual = second - prediction
    total = second - np.mean(second)
    r_squared = 1.0 - float(np.sum(residual**2) / max(np.sum(total**2), 1e-30))
    return slope, intercept, r_squared


def threshold_crossing(
    x: FloatArray,
    y: FloatArray,
    *,
    threshold: float,
    rising: bool,
) -> float | None:
    first = np.asarray(x, dtype=np.float64)
    second = np.asarray(y, dtype=np.float64)
    if first.shape != second.shape or first.ndim != 1 or len(first) < 2:
        return None
    order = np.argsort(first)
    first = first[order]
    second = second[order]
    for left in range(len(first) - 1):
        y0 = float(second[left])
        y1 = float(second[left + 1])
        crossed = (y0 <= threshold <= y1) if rising else (y0 >= threshold >= y1)
        if not crossed or np.isclose(y0, y1):
            continue
        weight = (threshold - y0) / (y1 - y0)
        return float(first[left] + weight * (first[left + 1] - first[left]))
    return None


def green_kubo_viscosity(
    stress: FloatArray,
    time_step: float,
    *,
    max_lag_fraction: float = 0.5,
) -> float:
    values = np.asarray(stress, dtype=np.float64)
    values = values[np.isfinite(values)]
    if len(values) < 4:
        return float("nan")
    centered = values - np.mean(values)
    max_lag = max(2, int(len(centered) * max_lag_fraction))
    correlation = np.empty(max_lag, dtype=np.float64)
    for lag in range(max_lag):
        left = centered[: len(centered) - lag]
        right = centered[lag:]
        correlation[lag] = float(np.mean(left * right))
    correlation = correlation[correlation > 0.0]
    if not len(correlation):
        return 0.0
    return float(np.trapezoid(correlation, dx=time_step))


def bimodality_coefficient(samples: FloatArray) -> float:
    values = np.asarray(samples, dtype=np.float64)
    values = values[np.isfinite(values)]
    if len(values) < 4 or np.std(values) <= 0.0:
        return 0.0
    centered = (values - np.mean(values)) / np.std(values)
    skewness = float(np.mean(centered**3))
    kurtosis = float(np.mean(centered**4))
    return float((skewness**2 + 1.0) / max(kurtosis, 1e-30))


def collapse_error(curves: list[dict[str, FloatArray]], exponent: float) -> float:
    """Measure log-stress spread after scaling rate by ``eta/v**exponent``."""

    prepared: list[tuple[FloatArray, FloatArray]] = []
    for curve in curves:
        activity = float(curve["activity"])
        viscosity = float(curve["viscosity"])
        if activity <= 0.0 or viscosity <= 0.0:
            continue
        rate, stress = _positive_sorted(curve["shear_rate"], curve["stress"])
        scaled = rate * viscosity / activity**exponent
        prepared.append((np.log(scaled), np.log(stress)))
    if len(prepared) < 2:
        return float("nan")
    lower = max(float(np.min(item[0])) for item in prepared)
    upper = min(float(np.max(item[0])) for item in prepared)
    if upper <= lower:
        return float("inf")
    grid = np.linspace(lower, upper, 80)
    interpolated = np.vstack([np.interp(grid, x, y) for x, y in prepared])
    return float(np.mean(np.std(interpolated, axis=0)))


def peclet_collapse(curves: list[dict[str, FloatArray]]) -> dict[str, float]:
    """Test the printed v^-2 scaling against preregistered alternatives."""

    exponents = np.linspace(0.0, 4.0, 81)
    errors = np.asarray([collapse_error(curves, float(value)) for value in exponents])
    finite = np.isfinite(errors)
    if not np.any(finite):
        return {
            "printed_exponent": 2.0,
            "printed_error": float("nan"),
            "eta_only_error": float("nan"),
            "best_exponent": float("nan"),
            "best_error": float("nan"),
            "onset_slope": float("nan"),
            "onset_r_squared": float("nan"),
        }
    best_index = np.flatnonzero(finite)[int(np.argmin(errors[finite]))]
    printed_error = collapse_error(curves, 2.0)
    eta_only_error = collapse_error(curves, 0.0)

    onset_x: list[float] = []
    onset_y: list[float] = []
    for curve in curves:
        onset = curve.get("thickening_rate")
        activity = float(curve["activity"])
        viscosity = float(curve["viscosity"])
        if onset is None or float(onset) <= 0.0 or activity <= 0.0 or viscosity <= 0.0:
            continue
        onset_x.append(viscosity / activity**2)
        onset_y.append(1.0 / float(onset))
    if len(onset_x) >= 2:
        fit = power_law_fit(np.asarray(onset_x), np.asarray(onset_y))
        slope = fit["exponent"]
        r_squared = fit["r_squared"]
    else:
        slope = float("nan")
        r_squared = float("nan")
    return {
        "printed_exponent": 2.0,
        "printed_error": float(printed_error),
        "eta_only_error": float(eta_only_error),
        "best_exponent": float(exponents[best_index]),
        "best_error": float(errors[best_index]),
        "onset_slope": float(slope),
        "onset_r_squared": float(r_squared),
    }


def largest_tension_component_fraction(
    vertex_count: int,
    network: list[dict[str, float | int]],
    *,
    quantile: float = 0.8,
) -> float:
    """Return the largest connected high-tension vertex fraction."""

    if not network:
        return 0.0
    tension = np.asarray([float(edge["tension"]) for edge in network])
    positive = tension[tension > 0.0]
    if not len(positive):
        return 0.0
    cutoff = float(np.quantile(positive, quantile))
    parent = np.arange(vertex_count)

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = int(parent[item])
        return item

    def union(first: int, second: int) -> None:
        root_first = find(first)
        root_second = find(second)
        if root_first != root_second:
            parent[root_second] = root_first

    active: set[int] = set()
    for edge in network:
        if float(edge["tension"]) >= cutoff:
            first = int(edge["first"])
            second = int(edge["second"])
            active.update((first, second))
            union(first, second)
    if not active:
        return 0.0
    counts: dict[int, int] = {}
    for vertex in active:
        root = find(vertex)
        counts[root] = counts.get(root, 0) + 1
    return float(max(counts.values()) / vertex_count)
