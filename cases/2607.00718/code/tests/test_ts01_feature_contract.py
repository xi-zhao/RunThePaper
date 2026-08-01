from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from ts01_feature_contract import (  # noqa: E402
    assess_ts01_detuning_regime,
    assess_ts01_truncation_discrepancy,
)


def _panels() -> dict[str, np.ndarray]:
    return {
        "a_weak": np.asarray([[0.0, 9.95], [0.0, 10.0], [0.0, 9.95]]),
        "c_weak": np.asarray([[0.0, 10.08], [0.0, 10.0], [0.0, 10.08]]),
        "a_strong": np.asarray([[0.0, 12.0], [0.0, 10.0], [0.0, 12.0]]),
        "c_strong": np.asarray([[0.0, 11.0], [0.0, 10.0], [0.0, 11.0]]),
    }


def _assess(
    *,
    weak_tolerance: float = 0.01,
    strong_gain_minimum: float = 0.05,
):
    return assess_ts01_detuning_regime(
        _panels(),
        np.asarray([-1.0, 0.0, 1.0]),
        weak_relative_tolerance=weak_tolerance,
        strong_min_abs_normalized_detuning=0.75,
        strong_relative_gain_minimum=strong_gain_minimum,
        symmetry_abs_tolerance=1e-12,
        nonnegative_abs_tolerance=1e-12,
    )


def test_visual_resolution_contract_accepts_subpercent_weak_gap() -> None:
    assessment = _assess()

    assert assessment.passed
    assert assessment.weak_resonance_within_visual_tolerance
    assert assessment.strong_has_material_finite_detuning_gain
    assert assessment.exact_weak_argmax_at_resonance == {
        "a_weak": True,
        "c_weak": False,
    }
    assert assessment.weak_relative_resonance_gap["c_weak"] < 0.01


def test_visual_resolution_contract_rejects_unreviewed_tighter_gate() -> None:
    assessment = _assess(weak_tolerance=0.005)

    assert not assessment.passed
    assert not assessment.weak_resonance_within_visual_tolerance


def test_material_gain_contract_rejects_small_strong_detuning_gain() -> None:
    assessment = _assess(strong_gain_minimum=0.10)

    assert not assessment.passed
    assert not assessment.strong_has_material_finite_detuning_gain


def test_truncation_discrepancy_separates_exact_and_finite_surfaces() -> None:
    panels = _panels()
    panels["c_strong"] = np.asarray(
        [[0.0, 60.0], [0.0, 1.0], [0.0, 60.0]]
    )
    finite_surface_probe = {
        "fock_cutoff": 10,
        "panel_numerical_diagnostics": {
            "a_weak": {"energy_maximum": 0.73},
            "c_weak": {"energy_maximum": 1.04},
            "a_strong": {"energy_maximum": 7.86},
            "c_strong": {"energy_maximum": 3.75},
        },
        "feature_contract": {"assessment": "supported"},
    }
    truncation_probe = {
        "terminal_hypothesis": {"cutoff_convergence": "not_established"}
    }

    assessment = assess_ts01_truncation_discrepancy(
        panels,
        finite_surface_probe,
        truncation_probe,
        paper_cutoff_disclosed=False,
        source_visual_peak_upper_bound=5.0,
    )

    assert assessment.passed
    assert assessment.discrepancy_detected
    assert assessment.finite_probe_energy_ceiling == 9.0
    assert assessment.exact_c_strong_over_cutoff_ceiling > 6.0
