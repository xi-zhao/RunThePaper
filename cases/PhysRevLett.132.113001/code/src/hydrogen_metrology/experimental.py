"""Fail-closed reanalysis channel for unavailable experimental arrays.

The paper does not deposit the individual observations behind Fig. 3 and
Fig. 5.  This module specifies the exact schemas needed to reanalyse those
observations if they become available.  It never fabricates replacement data.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class RequiredInput:
    filename: str
    columns: tuple[str, ...]
    purpose: str


REQUIRED_INPUTS = (
    RequiredInput(
        "spectrum_fig3.csv",
        ("frequency_mhz", "signal", "sigma"),
        "measured spectrum and uncertainty for the Fig. 3 joint line-shape fit",
    ),
    RequiredInput(
        "ionization_estimates.csv",
        ("dataset_id", "estimate_khz", "sigma_khz"),
        "the 525 corrected ionization-frequency estimates in Fig. 5(a)",
    ),
    RequiredInput(
        "field_scan.csv",
        ("field_v_per_cm", "offset_khz", "sigma_khz"),
        "individual quadratic-Stark observations in Fig. 5(b)",
    ),
    RequiredInput(
        "doppler_scan.csv",
        ("doppler_shift_mhz", "offset_khz", "sigma_khz"),
        "individual first-order-Doppler observations in Fig. 5(c)",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_inputs(root: Path) -> dict[str, object]:
    """Return a machine-readable inventory without opening missing files."""

    rows: list[dict[str, object]] = []
    for requirement in REQUIRED_INPUTS:
        path = root / requirement.filename
        row: dict[str, object] = {
            "filename": requirement.filename,
            "required_columns": list(requirement.columns),
            "purpose": requirement.purpose,
            "present": path.is_file(),
        }
        if path.is_file():
            row["sha256"] = sha256_file(path)
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                actual = tuple(reader.fieldnames or ())
            row["actual_columns"] = list(actual)
            row["schema_valid"] = actual == requirement.columns
        rows.append(row)
    ready = all(row["present"] and row.get("schema_valid") for row in rows)
    return {"status": "ready" if ready else "blocked_missing_inputs", "inputs": rows}


def load_numeric_csv(root: Path, requirement: RequiredInput) -> dict[str, np.ndarray]:
    """Load one author-provided table only after an exact schema check."""

    path = root / requirement.filename
    if not path.is_file():
        raise FileNotFoundError(f"required author data is missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != requirement.columns:
            raise ValueError(f"schema mismatch for {path.name}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"empty author-data file: {path.name}")
    columns: dict[str, np.ndarray] = {}
    for name in requirement.columns:
        if name == "dataset_id":
            columns[name] = np.asarray([row[name] for row in rows], dtype=str)
        else:
            columns[name] = np.asarray([float(row[name]) for row in rows])
    return columns


def weighted_linear_fit(
    x: np.ndarray, y: np.ndarray, sigma: np.ndarray, *, power: int
) -> dict[str, float]:
    """Fit y = intercept + slope*x**power with known point uncertainties."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    if not (x.shape == y.shape == sigma.shape) or x.ndim != 1:
        raise ValueError("x, y, and sigma must be equal one-dimensional arrays")
    if np.any(~np.isfinite(x)) or np.any(~np.isfinite(y)) or np.any(sigma <= 0):
        raise ValueError("fit inputs must be finite and sigma must be positive")
    design = np.column_stack((np.ones_like(x), x**power))
    weighted = design / sigma[:, None]
    normal = weighted.T @ weighted
    covariance = np.linalg.inv(normal)
    coefficients = covariance @ (weighted.T @ (y / sigma))
    residual = (y - design @ coefficients) / sigma
    return {
        "intercept": float(coefficients[0]),
        "slope": float(coefficients[1]),
        "intercept_sigma": float(np.sqrt(covariance[0, 0])),
        "slope_sigma": float(np.sqrt(covariance[1, 1])),
        "chi2": float(residual @ residual),
        "dof": int(x.size - 2),
    }


def reanalyse_available_inputs(root: Path) -> dict[str, object]:
    """Run the declared regressions, failing before analysis if any input is absent."""

    inventory = inspect_inputs(root)
    if inventory["status"] != "ready":
        raise FileNotFoundError(
            "experimental reanalysis is blocked by missing author arrays"
        )
    field = load_numeric_csv(root, REQUIRED_INPUTS[2])
    doppler = load_numeric_csv(root, REQUIRED_INPUTS[3])
    estimates = load_numeric_csv(root, REQUIRED_INPUTS[1])
    weights = 1.0 / estimates["sigma_khz"] ** 2
    weighted_mean = float(np.sum(weights * estimates["estimate_khz"]) / np.sum(weights))
    return {
        "inventory": inventory,
        "field_fit": weighted_linear_fit(
            field["field_v_per_cm"],
            field["offset_khz"],
            field["sigma_khz"],
            power=2,
        ),
        "doppler_fit": weighted_linear_fit(
            doppler["doppler_shift_mhz"],
            doppler["offset_khz"],
            doppler["sigma_khz"],
            power=1,
        ),
        "ionization_weighted_mean_khz": weighted_mean,
        "ionization_weighted_sigma_khz": float(np.sqrt(1.0 / np.sum(weights))),
    }
