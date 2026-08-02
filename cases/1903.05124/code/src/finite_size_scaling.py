"""Finite-size data-collapse tools for the monitored-circuit transition.

The implementation follows the supplement's scientific model: curves from
different sizes are transformed with ``x=(p-p_c)L^(1/nu)`` and compared only
inside their common interpolation support.  It uses generated numerical data
only; source-figure pixels and digitized source curves are never inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class ScalingCurve:
    size: int
    measurement_fraction: np.ndarray
    observable: np.ndarray
    standard_error: np.ndarray

    def __post_init__(self) -> None:
        p = np.asarray(self.measurement_fraction, dtype=float)
        observable = np.asarray(self.observable, dtype=float)
        standard_error = np.asarray(self.standard_error, dtype=float)
        if self.size <= 1:
            raise ValueError("size must be greater than one")
        if p.ndim != 1 or observable.ndim != 1 or standard_error.ndim != 1:
            raise ValueError("curve arrays must be one-dimensional")
        if len(p) < 3 or len(p) != len(observable) or len(p) != len(standard_error):
            raise ValueError("curve arrays must have equal length of at least three")
        if not np.all(np.isfinite(p)) or not np.all(np.isfinite(observable)):
            raise ValueError("curve values must be finite")
        if not np.all(np.isfinite(standard_error)) or np.any(standard_error < 0):
            raise ValueError("standard errors must be finite and non-negative")
        if np.any(np.diff(p) <= 0):
            raise ValueError("measurement fractions must be strictly increasing")
        object.__setattr__(self, "measurement_fraction", p)
        object.__setattr__(self, "observable", observable)
        object.__setattr__(self, "standard_error", standard_error)


@dataclass(frozen=True)
class CollapseFit:
    critical_probability: float
    critical_exponent: float
    cost: float
    comparisons: int
    evaluations: int
    critical_probability_at_boundary: bool
    critical_exponent_at_boundary: bool


@dataclass(frozen=True)
class BootstrapCollapseResult:
    critical_probabilities: np.ndarray
    critical_exponents: np.ndarray
    costs: np.ndarray


@dataclass(frozen=True)
class LogEntropyFit:
    alpha: float
    intercept: float
    alpha_standard_error: float
    r_squared: float


def scaled_curve(
    curve: ScalingCurve,
    *,
    critical_probability: float,
    critical_exponent: float,
    subtract_at_critical_probability: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if critical_exponent <= 0:
        raise ValueError("critical_exponent must be positive")
    x = (curve.measurement_fraction - critical_probability) * (
        curve.size ** (1.0 / critical_exponent)
    )
    observable = curve.observable.copy()
    standard_error = curve.standard_error.copy()
    if subtract_at_critical_probability:
        critical_observable = float(
            np.interp(
                critical_probability,
                curve.measurement_fraction,
                curve.observable,
            )
        )
        critical_error = float(
            np.interp(
                critical_probability,
                curve.measurement_fraction,
                curve.standard_error,
            )
        )
        observable -= critical_observable
        standard_error = np.sqrt(standard_error**2 + critical_error**2)
    return x, observable, standard_error


def collapse_cost(
    curves: Iterable[ScalingCurve],
    *,
    critical_probability: float,
    critical_exponent: float,
    subtract_at_critical_probability: bool = False,
) -> tuple[float, int]:
    """Symmetric uncertainty-weighted interpolation cost across system sizes."""

    selected = tuple(curves)
    if len(selected) < 2:
        raise ValueError("at least two system sizes are required")
    transformed = tuple(
        scaled_curve(
            curve,
            critical_probability=critical_probability,
            critical_exponent=critical_exponent,
            subtract_at_critical_probability=subtract_at_critical_probability,
        )
        for curve in selected
    )
    observable_scale = float(
        np.std(np.concatenate([item[1] for item in transformed]))
    )
    variance_floor = max(1e-12, (0.005 * observable_scale) ** 2)
    weighted_residual = 0.0
    comparisons = 0
    for source_index, (source_x, source_y, source_error) in enumerate(transformed):
        for reference_index, (reference_x, reference_y, reference_error) in enumerate(
            transformed
        ):
            if source_index == reference_index:
                continue
            overlap = (source_x >= reference_x[0]) & (source_x <= reference_x[-1])
            if not np.any(overlap):
                continue
            x = source_x[overlap]
            expected = np.interp(x, reference_x, reference_y)
            expected_error = np.interp(x, reference_x, reference_error)
            variance = source_error[overlap] ** 2 + expected_error**2 + variance_floor
            weighted_residual += float(
                np.sum((source_y[overlap] - expected) ** 2 / variance)
            )
            comparisons += int(np.count_nonzero(overlap))
    if comparisons == 0:
        return float("inf"), 0
    return weighted_residual / comparisons, comparisons


def fit_data_collapse(
    curves: Iterable[ScalingCurve],
    *,
    critical_probability_bounds: tuple[float, float],
    critical_exponent_bounds: tuple[float, float],
    subtract_at_critical_probability: bool = False,
    grid_points: int = 31,
    refinement_rounds: int = 3,
) -> CollapseFit:
    """Bounded deterministic grid search with local refinements."""

    selected = tuple(curves)
    if len(selected) < 2:
        raise ValueError("at least two system sizes are required")
    if grid_points < 3:
        raise ValueError("grid_points must be at least three")
    if refinement_rounds <= 0:
        raise ValueError("refinement_rounds must be positive")
    p_low, p_high = map(float, critical_probability_bounds)
    nu_low, nu_high = map(float, critical_exponent_bounds)
    if not 0.0 <= p_low < p_high <= 1.0:
        raise ValueError("critical probability bounds must satisfy 0 <= low < high <= 1")
    if not 0.0 < nu_low < nu_high:
        raise ValueError("critical exponent bounds must be positive and ordered")

    original_p_low, original_p_high = p_low, p_high
    original_nu_low, original_nu_high = nu_low, nu_high

    best_probability = p_low
    best_exponent = nu_low
    best_cost = float("inf")
    best_comparisons = 0
    evaluations = 0
    for _ in range(refinement_rounds):
        probabilities = np.linspace(p_low, p_high, grid_points)
        exponents = np.linspace(nu_low, nu_high, grid_points)
        for probability in probabilities:
            for exponent in exponents:
                cost, comparisons = collapse_cost(
                    selected,
                    critical_probability=float(probability),
                    critical_exponent=float(exponent),
                    subtract_at_critical_probability=subtract_at_critical_probability,
                )
                evaluations += 1
                if cost < best_cost:
                    best_probability = float(probability)
                    best_exponent = float(exponent)
                    best_cost = float(cost)
                    best_comparisons = comparisons
        p_step = float(probabilities[1] - probabilities[0])
        nu_step = float(exponents[1] - exponents[0])
        p_low = max(original_p_low, best_probability - p_step)
        p_high = min(original_p_high, best_probability + p_step)
        nu_low = max(original_nu_low, best_exponent - nu_step)
        nu_high = min(original_nu_high, best_exponent + nu_step)
    probability_tolerance = (
        original_p_high - original_p_low
    ) / (grid_points - 1)
    exponent_tolerance = (
        original_nu_high - original_nu_low
    ) / (grid_points - 1)
    return CollapseFit(
        critical_probability=best_probability,
        critical_exponent=best_exponent,
        cost=best_cost,
        comparisons=best_comparisons,
        evaluations=evaluations,
        critical_probability_at_boundary=(
            best_probability <= original_p_low + probability_tolerance
            or best_probability >= original_p_high - probability_tolerance
        ),
        critical_exponent_at_boundary=(
            best_exponent <= original_nu_low + exponent_tolerance
            or best_exponent >= original_nu_high - exponent_tolerance
        ),
    )


def leave_one_size_out_fits(
    curves: Iterable[ScalingCurve],
    **fit_kwargs: object,
) -> dict[int, CollapseFit]:
    """Refit after removing each size to expose finite-size instability."""

    selected = tuple(curves)
    if len(selected) < 3:
        raise ValueError("leave-one-size-out fitting requires at least three sizes")
    return {
        omitted.size: fit_data_collapse(
            (curve for curve in selected if curve.size != omitted.size),
            **fit_kwargs,
        )
        for omitted in selected
    }


def bootstrap_measurement_fractions(
    curves: Iterable[ScalingCurve],
    *,
    samples: int,
    sample_fraction: float,
    seed: int,
    **fit_kwargs: object,
) -> BootstrapCollapseResult:
    """Bootstrap the paper's measurement-probability sampling choice.

    The same sorted subset of measurement fractions is retained for every
    system size, matching the supplement's 80-of-100 resampling semantics.
    """

    selected = tuple(curves)
    if len(selected) < 2:
        raise ValueError("at least two system sizes are required")
    if samples <= 0:
        raise ValueError("samples must be positive")
    if not 0.0 < sample_fraction <= 1.0:
        raise ValueError("sample_fraction must lie in (0, 1]")
    reference_p = selected[0].measurement_fraction
    if any(
        len(curve.measurement_fraction) != len(reference_p)
        or not np.allclose(curve.measurement_fraction, reference_p, rtol=0.0, atol=1e-12)
        for curve in selected[1:]
    ):
        raise ValueError("bootstrap curves must share one measurement-fraction grid")
    retained = max(3, int(round(sample_fraction * len(reference_p))))
    retained = min(retained, len(reference_p))
    rng = np.random.default_rng(seed)
    probabilities = np.empty(samples, dtype=float)
    exponents = np.empty(samples, dtype=float)
    costs = np.empty(samples, dtype=float)
    for sample in range(samples):
        indices = np.sort(rng.choice(len(reference_p), size=retained, replace=False))
        resampled = tuple(
            ScalingCurve(
                size=curve.size,
                measurement_fraction=curve.measurement_fraction[indices],
                observable=curve.observable[indices],
                standard_error=curve.standard_error[indices],
            )
            for curve in selected
        )
        fit = fit_data_collapse(resampled, **fit_kwargs)
        probabilities[sample] = fit.critical_probability
        exponents[sample] = fit.critical_exponent
        costs[sample] = fit.cost
    return BootstrapCollapseResult(probabilities, exponents, costs)


def fit_log_entropy(
    sizes: Iterable[int],
    entropies: Iterable[float],
    standard_errors: Iterable[float],
) -> LogEntropyFit:
    """Fit ``S(p_c,L)=alpha ln(L)+c`` by weighted least squares."""

    size_values = np.asarray(tuple(sizes), dtype=float)
    entropy_values = np.asarray(tuple(entropies), dtype=float)
    error_values = np.asarray(tuple(standard_errors), dtype=float)
    if (
        size_values.ndim != 1
        or len(size_values) < 3
        or len(size_values) != len(entropy_values)
        or len(size_values) != len(error_values)
    ):
        raise ValueError("logarithmic fitting needs at least three aligned values")
    if np.any(size_values <= 1) or np.any(error_values < 0):
        raise ValueError("sizes must exceed one and standard errors must be non-negative")
    if not np.all(np.isfinite(size_values)) or not np.all(np.isfinite(entropy_values)):
        raise ValueError("fit inputs must be finite")
    positive_errors = error_values[error_values > 0]
    error_floor = (
        float(np.min(positive_errors)) if positive_errors.size else 1.0
    )
    weights = 1.0 / np.maximum(error_values, error_floor) ** 2
    design = np.column_stack((np.log(size_values), np.ones_like(size_values)))
    weighted_design = design * np.sqrt(weights)[:, None]
    weighted_entropy = entropy_values * np.sqrt(weights)
    coefficients, _, _, _ = np.linalg.lstsq(
        weighted_design,
        weighted_entropy,
        rcond=None,
    )
    predicted = design @ coefficients
    residual = entropy_values - predicted
    dof = len(size_values) - 2
    reduced_chi_square = float(np.sum(weights * residual**2) / dof)
    covariance = np.linalg.inv(design.T @ (weights[:, None] * design))
    covariance *= max(1.0, reduced_chi_square)
    total = float(np.sum((entropy_values - np.mean(entropy_values)) ** 2))
    residual_total = float(np.sum(residual**2))
    r_squared = 1.0 - residual_total / total if total > 0 else 1.0
    return LogEntropyFit(
        alpha=float(coefficients[0]),
        intercept=float(coefficients[1]),
        alpha_standard_error=float(np.sqrt(covariance[0, 0])),
        r_squared=float(r_squared),
    )
