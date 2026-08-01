from __future__ import annotations

import sys
from pathlib import Path

import torch


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from ts01_truncation_probe import (  # noqa: E402
    ProbeGrid,
    _liouvillian_components,
    _rhs,
    _simulate_cutoff,
    _simulate_cutoff_sparse,
    _terminal_hypothesis,
)


def test_truncated_master_equation_rhs_preserves_trace() -> None:
    dtype = torch.complex128
    hamiltonians, collapse_operators, _ = _liouvillian_components(
        torch,
        cutoff=3,
        normalized_detunings=(0.0, 1.5),
        coupling=1e-3,
        kappa=8e-5,
        drive=1e-4,
        squeezing=1.0,
        charger_phase=0.0,
        reservoir_phase=0.0,
        device=torch.device("cpu"),
        dtype=dtype,
    )
    density = torch.zeros((2, 9, 9), dtype=dtype)
    density[:, 0, 0] = 1.0
    derivative = _rhs(
        torch,
        density,
        hamiltonians,
        collapse_operators,
    )
    trace_derivative = torch.diagonal(
        derivative,
        dim1=-2,
        dim2=-1,
    ).sum(dim=-1)
    torch.testing.assert_close(
        trace_derivative,
        torch.zeros_like(trace_derivative),
        rtol=0.0,
        atol=1e-12,
    )


def test_probe_uses_stable_default_substeps() -> None:
    assert ProbeGrid().substeps_per_output == 32


def test_small_stable_probe_satisfies_physical_invariants() -> None:
    result = _simulate_cutoff(
        torch,
        cutoff=2,
        normalized_detunings=(0.0,),
        coupling=1e-3,
        kappa=8e-5,
        drive=1e-4,
        squeezing=1.0,
        charger_phase=0.0,
        reservoir_phase=0.0,
        scaled_time_max=0.05,
        time_points=3,
        substeps_per_output=8,
        device=torch.device("cpu"),
        dtype=torch.complex128,
    )
    assert result["numerical_status"] == "valid"
    assert result["trace_max_abs_error"] <= 1e-8
    assert result["minimum_final_density_eigenvalue"] >= -1e-7


def test_sparse_exponential_matches_small_stable_rk4_probe() -> None:
    common = {
        "cutoff": 2,
        "normalized_detunings": (0.0,),
        "coupling": 1e-3,
        "kappa": 8e-5,
        "drive": 1e-4,
        "squeezing": 1.0,
        "charger_phase": 0.0,
        "reservoir_phase": 0.0,
        "scaled_time_max": 0.05,
        "time_points": 3,
    }
    sparse_result = _simulate_cutoff_sparse(**common)
    rk4_result = _simulate_cutoff(
        torch,
        **common,
        substeps_per_output=64,
        device=torch.device("cpu"),
        dtype=torch.complex128,
    )

    assert sparse_result["numerical_status"] == "valid"
    assert sparse_result["trace_max_abs_error"] <= 1e-10
    torch.testing.assert_close(
        torch.tensor(sparse_result["maximum_energy"]),
        torch.tensor(rk4_result["maximum_energy"]),
        rtol=1e-7,
        atol=1e-10,
    )
    torch.testing.assert_close(
        torch.tensor(sparse_result["final_energy"]),
        torch.tensor(rk4_result["final_energy"]),
        rtol=1e-7,
        atol=1e-10,
    )


def test_non_finite_terminal_result_is_inconclusive() -> None:
    result = _terminal_hypothesis(
        [
            {
                "cutoff": 10,
                "coupling": 1e-5,
                "numerical_status": "non_finite",
                "peak_normalized_detuning": None,
            },
            {
                "cutoff": 10,
                "coupling": 1e-3,
                "numerical_status": "valid",
                "peak_normalized_detuning": 1.5,
            },
        ],
        largest_cutoff=10,
        weak_coupling=1e-5,
        strong_coupling=1e-3,
    )
    assert result["assessment"] == "inconclusive_numerical_validation"
    assert result["finite_cutoff_restores_paper_feature_contract"] is None
