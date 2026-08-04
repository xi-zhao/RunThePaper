#!/usr/bin/env python3
"""Generate a source-image-free OBC activity grid and broad phase boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nonreciprocal_condensate import (  # noqa: E402
    ModelParameters,
    complex_rhs,
    thermodynamic_vacuum_threshold,
)


DATA_DIR = WORKSPACE / "outputs" / "data"
CHECK_DIR = WORKSPACE / "outputs" / "checks"
DT = 0.05


def batched_rhs(
    state: np.ndarray, kappa: np.ndarray, gamma: np.ndarray
) -> np.ndarray:
    result = (
        kappa[:, None] - 2.0 * gamma[:, None] - np.abs(state) ** 2
    ) * state
    result[:, :-1] += 1j * (1.0 - gamma)[:, None] * state[:, 1:]
    result[:, 1:] += 1j * (1.0 + gamma)[:, None] * state[:, :-1]
    return result


def batched_step(
    state: np.ndarray, kappa: np.ndarray, gamma: np.ndarray
) -> np.ndarray:
    k1 = batched_rhs(state, kappa, gamma)
    k2 = batched_rhs(state + 0.5 * DT * k1, kappa, gamma)
    k3 = batched_rhs(state + 0.5 * DT * k2, kappa, gamma)
    k4 = batched_rhs(state + DT * k3, kappa, gamma)
    return state + (DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    started = time.perf_counter()
    n = 100
    gamma_axis = np.linspace(0.1, 1.0, 10)
    kappa_axis = np.linspace(0.0, 2.6, 27)
    gamma_grid, kappa_grid = np.meshgrid(gamma_axis, kappa_axis, indexing="ij")
    gamma = gamma_grid.ravel()
    kappa = kappa_grid.ravel()
    rng = np.random.default_rng(101)
    state = 1.0e-3 * (
        rng.normal(size=(gamma.size, n))
        + 1j * rng.normal(size=(gamma.size, n))
    )
    for _ in range(int(round(3000.0 / DT))):
        state = batched_step(state, kappa, gamma)

    activity = np.zeros(gamma.size)
    density_activity = np.zeros(gamma.size)
    amplitude = np.zeros(gamma.size)
    samples = 0
    for step in range(int(round(100.0 / DT))):
        state = batched_step(state, kappa, gamma)
        if step % 5 == 0:
            rhs = batched_rhs(state, kappa, gamma)
            activity += np.mean(np.abs(rhs), axis=1)
            density_activity += np.mean(
                np.abs(2.0 * np.real(state.conj() * rhs)), axis=1
            )
            amplitude += np.mean(np.abs(state), axis=1)
            samples += 1
    activity /= samples
    density_activity /= samples
    amplitude /= samples

    kernel_error = 0.0
    for index in (0, gamma.size // 2, gamma.size - 1):
        expected = complex_rhs(
            state[index],
            ModelParameters(kappa=float(kappa[index]), gamma=float(gamma[index])),
        )
        actual = batched_rhs(
            state[index][None, :],
            np.asarray([kappa[index]]),
            np.asarray([gamma[index]]),
        )[0]
        kernel_error = max(kernel_error, float(np.max(np.abs(expected - actual))))

    activity_grid = activity.reshape(gamma_grid.shape)
    density_grid = density_activity.reshape(gamma_grid.shape)
    amplitude_grid = amplitude.reshape(gamma_grid.shape)
    static_boundary = np.full(gamma_axis.shape, np.nan)
    for row in range(gamma_axis.size):
        static = (activity_grid[row] < 1.0e-3) & (amplitude_grid[row] > 1.0e-3)
        indices = np.flatnonzero(static)
        if indices.size:
            static_boundary[row] = kappa_axis[indices[0]]

    broad_gamma = np.linspace(0.0, 3.0, 601)
    payload = {
        "n": np.asarray(n),
        "gamma_axis": gamma_axis,
        "kappa_axis": kappa_axis,
        "mean_abs_rhs": activity_grid,
        "mean_abs_density_rate": density_grid,
        "mean_amplitude": amplitude_grid,
        "static_boundary_gamma": gamma_axis,
        "static_boundary_kappa": static_boundary,
        "broad_gamma": broad_gamma,
        "vacuum_boundary": thermodynamic_vacuum_threshold(broad_gamma),
        "kernel_max_error": np.asarray(kernel_error),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "obc_phase_activity_grid.npz"
    np.savez_compressed(output, **payload)
    valid_boundary = static_boundary[np.isfinite(static_boundary)]
    checks = {
        "schema_version": 1,
        "status": "partial",
        "paper_id": "10.1103/gphr-d1bc",
        "data_provenance": "independent_numerics",
        "source_image_access": False,
        "author_numerical_code_access": False,
        "protocol": {
            "n": n,
            "burn_time": 3000.0,
            "observation_time": 100.0,
            "dt": DT,
            "seed": 101,
            "status": "reconstructed_paper_does_not_declare_seed_or_integrator",
        },
        "targets": {
            "main_fig3_a": {
                "status": "feature_match",
                "vacuum_boundary": "analytic_exact",
                "dynamic_static_boundary": "coarse_long_time_basin_scan",
                "boundary_min": float(np.min(valid_boundary)),
                "boundary_max": float(np.max(valid_boundary)),
            },
            "main_fig4_a": {
                "status": "partial",
                "reason": "coarse activity and edge-amplitude observables reproduced; fine multistable phase stripes require paper-scale basin continuation",
            },
        },
        "kernel_max_error": kernel_error,
        "output": {
            "path": "outputs/data/obc_phase_activity_grid.npz",
            "sha256": sha256(output),
        },
        "runtime_seconds": time.perf_counter() - started,
    }
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (CHECK_DIR / "phase_diagram_targets.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
