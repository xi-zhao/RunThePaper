from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from finite_hilbert_dynamics import (  # noqa: E402
    simulate_finite_hilbert_grid,
    simulate_finite_hilbert_trajectory,
)
from squeezing_nonreciprocity import (  # noqa: E402
    gaussian_master_equation_energy_dynamics,
)


def test_case_a_finite_hilbert_matches_gaussian_before_cutoff() -> None:
    coupling = 1e-3
    scaled_time = np.linspace(0.0, 0.05, 3)
    finite = simulate_finite_hilbert_trajectory(
        case="a",
        cutoff=6,
        normalized_detuning=0.0,
        coupling=coupling,
        kappa=8e-5,
        drive=1e-4,
        squeezing=1.0,
        charger_phase=0.0,
        reservoir_phase=0.0,
        scaled_time_min=float(scaled_time[0]),
        scaled_time_max=float(scaled_time[-1]),
        time_points=scaled_time.size,
    )
    gaussian = gaussian_master_equation_energy_dynamics(
        "a",
        scaled_time / coupling,
        coupling,
        8e-5,
        8e-5,
        1e-4,
        1.0,
    )

    assert finite.numerical_status == "valid"
    np.testing.assert_allclose(
        finite.energy,
        gaussian,
        rtol=1.1e-4,
        atol=1e-9,
    )


def test_case_c_finite_hilbert_matches_gaussian_before_cutoff() -> None:
    coupling = 1e-3
    scaled_time = np.linspace(0.0, 0.02, 3)
    finite = simulate_finite_hilbert_trajectory(
        case="c",
        cutoff=6,
        normalized_detuning=0.0,
        coupling=coupling,
        kappa=8e-5,
        drive=1e-4,
        squeezing=1.0,
        charger_phase=0.0,
        reservoir_phase=0.0,
        scaled_time_min=float(scaled_time[0]),
        scaled_time_max=float(scaled_time[-1]),
        time_points=scaled_time.size,
    )
    gaussian = gaussian_master_equation_energy_dynamics(
        "c",
        scaled_time / coupling,
        coupling,
        8e-5,
        8e-5,
        1e-4,
        1.0,
    )

    assert finite.numerical_status == "valid"
    np.testing.assert_allclose(
        finite.energy,
        gaussian,
        rtol=2e-3,
        atol=1e-9,
    )


def test_serial_grid_preserves_panel_shape_and_invariants() -> None:
    detunings = np.asarray([-0.5, 0.5])
    grid = simulate_finite_hilbert_grid(
        panel_cases_and_couplings={
            "a_weak": ("a", 1e-3),
            "c_weak": ("c", 1e-3),
        },
        normalized_detunings=detunings,
        cutoff=2,
        kappa=8e-5,
        drive=1e-4,
        squeezing=1.0,
        charger_phase=0.0,
        reservoir_phase=0.0,
        scaled_time_min=0.0,
        scaled_time_max=0.02,
        time_points=3,
        max_workers=1,
    )

    assert grid.numerical_status == "valid"
    assert grid.worker_count == 1
    assert grid.panels["a_weak"].shape == (2, 3)
    assert grid.panels["c_weak"].shape == (2, 3)
    assert all(
        diagnostic["valid_trajectory_count"] == 2
        for diagnostic in grid.panel_diagnostics.values()
    )


def test_parallel_grid_matches_serial_grid() -> None:
    common = {
        "panel_cases_and_couplings": {
            "a_strong": ("a", 1e-3),
            "c_strong": ("c", 1e-3),
        },
        "normalized_detunings": np.asarray([0.0]),
        "cutoff": 2,
        "kappa": 8e-5,
        "drive": 1e-4,
        "squeezing": 1.0,
        "charger_phase": 0.0,
        "reservoir_phase": 0.0,
        "scaled_time_min": 0.0,
        "scaled_time_max": 0.02,
        "time_points": 3,
    }
    serial = simulate_finite_hilbert_grid(**common, max_workers=1)
    parallel = simulate_finite_hilbert_grid(**common, max_workers=2)

    assert parallel.numerical_status == "valid"
    assert parallel.worker_count == 2
    for panel_key in common["panel_cases_and_couplings"]:
        np.testing.assert_allclose(
            parallel.panels[panel_key],
            serial.panels[panel_key],
            rtol=0.0,
            atol=1e-13,
        )
