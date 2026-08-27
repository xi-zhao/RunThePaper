"""Parameterized higher-dimensional area-law analysis boundary."""

from __future__ import annotations

from typing import Any

import numpy as np


def fit_area_law(
    boundary_measure: np.ndarray,
    entropy: np.ndarray,
) -> dict[str, float | int]:
    """Fit ``S = kappa * sigma + intercept`` and test ratio convergence."""

    sigma = np.asarray(boundary_measure, dtype=float)
    values = np.asarray(entropy, dtype=float)
    if sigma.ndim != 1 or values.shape != sigma.shape or sigma.size < 3:
        raise ValueError("boundary_measure and entropy need at least three aligned values")
    if np.any(~np.isfinite(sigma)) or np.any(~np.isfinite(values)):
        raise ValueError("area-law samples must be finite")
    if np.any(sigma <= 0.0) or np.any(np.diff(sigma) <= 0.0):
        raise ValueError("boundary_measure must be strictly increasing and positive")
    design = np.column_stack([sigma, np.ones_like(sigma)])
    kappa, intercept = np.linalg.lstsq(design, values, rcond=None)[0]
    fitted = design @ np.asarray([kappa, intercept])
    residual = values - fitted
    total = values - np.mean(values)
    r_squared = 1.0 - float(np.dot(residual, residual)) / max(
        float(np.dot(total, total)), 1e-30
    )
    ratios = values / sigma
    tail = ratios[max(0, ratios.size // 2) :]
    relative_tail_spread = float(np.ptp(tail) / max(abs(float(np.mean(tail))), 1e-30))
    return {
        "sample_count": int(sigma.size),
        "kappa": float(kappa),
        "intercept": float(intercept),
        "r_squared": r_squared,
        "relative_tail_ratio_spread": relative_tail_spread,
    }


def evaluate_area_law_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """Validate provenance and analyze one independently generated dataset."""

    if dataset.get("data_provenance") != "independent_numerics":
        raise ValueError("area-law samples must come from independent_numerics")
    forbidden_flags = (
        "source_pixels_used",
        "author_code_used",
        "author_numeric_arrays_used",
    )
    if any(bool(dataset.get(flag)) for flag in forbidden_flags):
        raise ValueError("source pixels, author code, and author arrays are forbidden inputs")
    result = fit_area_law(
        np.asarray(dataset["boundary_measure"], dtype=float),
        np.asarray(dataset["entropy"], dtype=float),
    )
    return {"dataset_id": str(dataset["dataset_id"]), **result}
