#!/usr/bin/env python3
"""Compute the open-boundary phase boundary independently for T003/T006.

The published Fig. 1 (square) and Fig. S3 (disk) red transition curves came
from the paper's tables or the analytic non-Bloch formula. This script
recomputes m*(gamma) from finite-size spectra alone:

- gap^2(m; size) = min|E|^2 of the open-boundary spectrum;
- linear extrapolation of gap^2 against 1/size^2 gives the thermodynamic
  intercept(m);
- on the trivial side the gap opens linearly, so sqrt(intercept) is fitted
  linearly in m and extrapolated to zero to locate m*(gamma).

The result is compared against the analytic non-Bloch boundary m = 2 + gamma^2
and (for the disk) the supplemental numerical boundary table, both used as
validation references only.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nonhermitian_chern import (  # noqa: E402
    DiskParams,
    SquareParams,
    disk_gap_square,
    open_boundary_non_bloch_phase_boundary,
    source_disk_numerical_boundary,
    square_gap_square,
)

GAMMA_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
SQUARE_SIZES = [16, 20, 24, 28]
DISK_RADII = [20, 24, 28, 32]
M_WINDOW_BELOW = 0.06
M_WINDOW_ABOVE = 0.24
M_STEP = 0.02
# Fit only the near-critical linear regime of the thermodynamic gap.
INTERCEPT_FIT_MIN = 3e-4
INTERCEPT_FIT_MAX = 2e-2
BOUNDARY_TOLERANCE = 0.05


def main() -> int:
    rows: list[dict[str, object]] = []
    boundaries: list[dict[str, object]] = []

    for geometry in ["square", "disk"]:
        for gamma in GAMMA_VALUES:
            analytic = open_boundary_non_bloch_phase_boundary(gamma)
            m_values = np.arange(
                analytic - M_WINDOW_BELOW, analytic + M_WINDOW_ABOVE + 1e-9, M_STEP
            )
            intercepts: list[tuple[float, float]] = []
            for m in m_values:
                inv_sq, gaps = gap_square_series(geometry, float(gamma), float(m))
                slope, intercept = np.polyfit(inv_sq, gaps, deg=1)
                intercepts.append((float(m), float(intercept)))
                rows.append(
                    {
                        "geometry": geometry,
                        "gamma": float(gamma),
                        "m": float(m),
                        "intercept": float(intercept),
                        "slope": float(slope),
                    }
                )
            m_star = extrapolate_boundary(intercepts)
            reference = {
                "analytic_non_bloch": analytic,
            }
            if geometry == "disk":
                reference["source_table"] = float(source_disk_numerical_boundary(gamma))
            deviations = {
                key: (None if m_star is None else abs(m_star - value))
                for key, value in reference.items()
            }
            boundaries.append(
                {
                    "geometry": geometry,
                    "gamma": float(gamma),
                    "m_star": m_star,
                    "references": reference,
                    "abs_deviation": deviations,
                    "within_tolerance": all(
                        d is not None and d <= BOUNDARY_TOLERANCE for d in deviations.values()
                    ),
                }
            )

    data_path = ROOT / "outputs/data/independent_obc_boundary.csv"
    checks_path = ROOT / "outputs/checks/independent_obc_boundary.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["geometry", "gamma", "m", "intercept", "slope"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    failed = [b for b in boundaries if not b["within_tolerance"]]
    max_deviation = max(
        (d for b in boundaries for d in b["abs_deviation"].values() if d is not None),
        default=None,
    )
    checks = {
        "target_ids": ["T003", "T006"],
        "gate": "independent_obc_boundary",
        "status": "passed" if not failed else "failed",
        "method": "finite_size_gap_square_extrapolation_with_sqrt_intercept_root",
        "geometries": {
            "square": {"sizes": SQUARE_SIZES, "scaling_variable": "1/L^2"},
            "disk": {"radii": DISK_RADII, "scaling_variable": "1/R^2"},
        },
        "gamma_values": GAMMA_VALUES,
        "m_step": M_STEP,
        "tolerances": {
            "boundary_abs_deviation": BOUNDARY_TOLERANCE,
            "intercept_fit_min": INTERCEPT_FIT_MIN,
            "intercept_fit_max": INTERCEPT_FIT_MAX,
        },
        "max_abs_deviation": max_deviation,
        "boundaries": boundaries,
        "failed_slices": failed,
        "data_path": "outputs/data/independent_obc_boundary.csv",
        "notes": [
            "m*(gamma) comes from independent finite-size spectra only; the analytic non-Bloch boundary and the supplemental table are validation references, not inputs.",
            "sqrt(intercept) is fitted linearly on the trivial side because the thermodynamic gap opens linearly in m at the transition.",
        ],
    }
    checks_path.write_text(json.dumps(checks, indent=2) + "\n")
    summary = {
        "status": checks["status"],
        "max_abs_deviation": max_deviation,
        "failed_slices": len(failed),
    }
    print(json.dumps(summary, indent=2))
    return 0 if checks["status"] == "passed" else 1


def gap_square_series(geometry: str, gamma: float, m: float) -> tuple[np.ndarray, np.ndarray]:
    if geometry == "square":
        sizes = SQUARE_SIZES
        gaps = [
            square_gap_square(SquareParams(gamma_x=gamma, gamma_y=gamma, m=m, L=size))
            for size in sizes
        ]
    elif geometry == "disk":
        sizes = DISK_RADII
        gaps = [
            disk_gap_square(DiskParams(gamma_x=gamma, gamma_y=gamma, m=m, radius=size))
            for size in sizes
        ]
    else:
        raise ValueError(f"unknown geometry: {geometry}")
    inv_sq = np.asarray([1.0 / (size * size) for size in sizes], dtype=float)
    return inv_sq, np.asarray(gaps, dtype=float)


def extrapolate_boundary(intercepts: list[tuple[float, float]]) -> float | None:
    """Fit sqrt(intercept) linearly in m on the trivial side and find its root."""

    fit_points = [
        (m, np.sqrt(i)) for m, i in intercepts if INTERCEPT_FIT_MIN < i < INTERCEPT_FIT_MAX
    ]
    if len(fit_points) < 3:
        return None
    m_fit = np.asarray([p[0] for p in fit_points], dtype=float)
    y_fit = np.asarray([p[1] for p in fit_points], dtype=float)
    slope, offset = np.polyfit(m_fit, y_fit, deg=1)
    if slope <= 0:
        return None
    return float(-offset / slope)


if __name__ == "__main__":
    raise SystemExit(main())
