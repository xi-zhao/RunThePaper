"""Feature-level acceptance contract for Supplemental Figure S1.

The source claim is qualitative: weak coupling is resonance compatible, while
strong coupling develops a useful finite-detuning optimum.  A discrete-grid
``argmax`` is too brittle for the weak-coupling statement because a visually
indistinguishable off-resonant point can win by less than one percent.  This
module keeps the scientific interpretation and its tolerances explicit,
testable, and separate from plotting code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
PANEL_KEYS = ("a_weak", "c_weak", "a_strong", "c_strong")
WEAK_PANEL_KEYS = ("a_weak", "c_weak")
STRONG_PANEL_KEYS = ("a_strong", "c_strong")


@dataclass(frozen=True)
class TS01DetuningAssessment:
    """Measured evidence and verdict for the Figure S1 regime change."""

    symmetry_max_abs_error: dict[str, float]
    peak_normalized_detuning: dict[str, float]
    exact_weak_argmax_at_resonance: dict[str, bool]
    weak_relative_resonance_gap: dict[str, float]
    strong_relative_detuning_gain: dict[str, float]
    weak_resonance_within_visual_tolerance: bool
    strong_has_material_finite_detuning_gain: bool
    zero_detuning_nonnegative: bool
    symmetry_within_tolerance: bool
    passed: bool

    def as_metrics(
        self,
        *,
        weak_relative_tolerance: float,
        strong_min_abs_normalized_detuning: float,
        strong_relative_gain_minimum: float,
        symmetry_abs_tolerance: float,
    ) -> dict[str, object]:
        """Return the stable JSON-facing metric vocabulary."""

        return {
            "detuning_symmetry_max_abs_error": (
                self.symmetry_max_abs_error
            ),
            "detuning_symmetry_abs_tolerance": symmetry_abs_tolerance,
            "peak_normalized_detuning": self.peak_normalized_detuning,
            "exact_weak_coupling_argmax_at_resonance": (
                self.exact_weak_argmax_at_resonance
            ),
            "weak_coupling_relative_resonance_gap": (
                self.weak_relative_resonance_gap
            ),
            "weak_resonance_relative_tolerance": (
                weak_relative_tolerance
            ),
            "strong_coupling_relative_detuning_gain": (
                self.strong_relative_detuning_gain
            ),
            "strong_min_abs_normalized_detuning": (
                strong_min_abs_normalized_detuning
            ),
            "strong_detuning_relative_gain_minimum": (
                strong_relative_gain_minimum
            ),
            "weak_coupling_resonance_within_visual_tolerance": (
                self.weak_resonance_within_visual_tolerance
            ),
            "strong_coupling_has_material_finite_detuning_gain": (
                self.strong_has_material_finite_detuning_gain
            ),
            "zero_detuning_energy_nonnegative": (
                self.zero_detuning_nonnegative
            ),
            "detuning_regime_contract": {
                "status": "passed" if self.passed else "failed",
                "weak_interpretation": (
                    "resonance_within_visual_resolution_tolerance"
                ),
                "strong_interpretation": (
                    "finite_detuning_with_material_energy_gain"
                ),
            },
        }


@dataclass(frozen=True)
class TS01TruncationAssessment:
    """Diagnose whether the published surface is controlled by Fock truncation."""

    gaussian_peak_energy: dict[str, float]
    finite_probe_peak_energy: dict[str, float]
    finite_probe_cutoff: int
    finite_probe_energy_ceiling: float
    exact_c_strong_over_cutoff_ceiling: float
    exact_c_strong_over_source_visual_upper_bound: float
    finite_surface_supports_paper_feature_contract: bool
    cutoff_convergence: str
    paper_cutoff_disclosed: bool
    discrepancy_detected: bool
    passed: bool

    def as_metrics(self, *, source_visual_peak_upper_bound: float) -> dict[str, object]:
        return {
            "gaussian_peak_energy": self.gaussian_peak_energy,
            "finite_probe_peak_energy": self.finite_probe_peak_energy,
            "finite_probe_fock_cutoff": self.finite_probe_cutoff,
            "finite_probe_energy_ceiling": self.finite_probe_energy_ceiling,
            "exact_c_strong_over_cutoff_ceiling": (
                self.exact_c_strong_over_cutoff_ceiling
            ),
            "source_visual_c_strong_peak_upper_bound": (
                source_visual_peak_upper_bound
            ),
            "exact_c_strong_over_source_visual_upper_bound": (
                self.exact_c_strong_over_source_visual_upper_bound
            ),
            "finite_surface_supports_paper_feature_contract": (
                self.finite_surface_supports_paper_feature_contract
            ),
            "cutoff_convergence": self.cutoff_convergence,
            "paper_fock_cutoff_disclosed": self.paper_cutoff_disclosed,
            "scientific_discrepancy": {
                "status": "detected" if self.discrepancy_detected else "not_detected",
                "interpretation": (
                    "published_panel_d_is_consistent_with_an_unconverged_finite_fock_"
                    "surface_not_the_cutoff_free_gaussian_solution"
                ),
            },
        }


def assess_ts01_truncation_discrepancy(
    panels: Mapping[str, FloatArray],
    finite_surface_probe: Mapping[str, object],
    truncation_probe: Mapping[str, object],
    *,
    paper_cutoff_disclosed: bool,
    source_visual_peak_upper_bound: float,
) -> TS01TruncationAssessment:
    """Compare cutoff-free output with independent finite-Fock probes.

    The source-figure scale enters only as post-generation validation. It
    never feeds either numerical calculation.
    """

    if source_visual_peak_upper_bound <= 0.0:
        raise ValueError("source_visual_peak_upper_bound must be positive")
    gaussian_peaks = {
        key: float(np.max(np.asarray(panels[key], dtype=float)))
        for key in PANEL_KEYS
    }
    cutoff = int(finite_surface_probe.get("fock_cutoff") or 0)
    if cutoff < 2:
        raise ValueError("finite surface probe must declare fock_cutoff >= 2")
    raw_diagnostics = finite_surface_probe.get("panel_numerical_diagnostics")
    if not isinstance(raw_diagnostics, Mapping):
        raise ValueError("finite surface probe is missing panel diagnostics")
    finite_peaks = {}
    for key in PANEL_KEYS:
        diagnostic = raw_diagnostics.get(key)
        if not isinstance(diagnostic, Mapping):
            raise ValueError(f"finite surface probe is missing {key}")
        finite_peaks[key] = float(diagnostic["energy_maximum"])

    feature_contract = finite_surface_probe.get("feature_contract")
    finite_contract_supported = bool(
        isinstance(feature_contract, Mapping)
        and feature_contract.get("assessment") == "supported"
    )
    terminal_hypothesis = truncation_probe.get("terminal_hypothesis")
    cutoff_convergence = (
        str(terminal_hypothesis.get("cutoff_convergence") or "unknown")
        if isinstance(terminal_hypothesis, Mapping)
        else "unknown"
    )
    ceiling = float(cutoff - 1)
    exact_peak = gaussian_peaks["c_strong"]
    exact_over_ceiling = exact_peak / ceiling
    exact_over_source = exact_peak / source_visual_peak_upper_bound
    discrepancy_detected = bool(
        not paper_cutoff_disclosed
        and cutoff_convergence != "established"
        and finite_contract_supported
        and finite_peaks["c_strong"] <= source_visual_peak_upper_bound
        and exact_peak > ceiling
        and exact_peak > source_visual_peak_upper_bound
    )
    return TS01TruncationAssessment(
        gaussian_peak_energy=gaussian_peaks,
        finite_probe_peak_energy=finite_peaks,
        finite_probe_cutoff=cutoff,
        finite_probe_energy_ceiling=ceiling,
        exact_c_strong_over_cutoff_ceiling=float(exact_over_ceiling),
        exact_c_strong_over_source_visual_upper_bound=float(exact_over_source),
        finite_surface_supports_paper_feature_contract=finite_contract_supported,
        cutoff_convergence=cutoff_convergence,
        paper_cutoff_disclosed=paper_cutoff_disclosed,
        discrepancy_detected=discrepancy_detected,
        passed=discrepancy_detected,
    )


def assess_ts01_detuning_regime(
    panels: Mapping[str, FloatArray],
    normalized_detuning: FloatArray,
    *,
    weak_relative_tolerance: float,
    strong_min_abs_normalized_detuning: float,
    strong_relative_gain_minimum: float,
    symmetry_abs_tolerance: float,
    nonnegative_abs_tolerance: float,
) -> TS01DetuningAssessment:
    """Assess the published weak/strong detuning-regime feature contract."""

    detunings = np.asarray(normalized_detuning, dtype=float).reshape(-1)
    _validate_inputs(
        panels,
        detunings,
        weak_relative_tolerance=weak_relative_tolerance,
        strong_min_abs_normalized_detuning=(
            strong_min_abs_normalized_detuning
        ),
        strong_relative_gain_minimum=strong_relative_gain_minimum,
        symmetry_abs_tolerance=symmetry_abs_tolerance,
        nonnegative_abs_tolerance=nonnegative_abs_tolerance,
    )
    zero_index = int(np.argmin(np.abs(detunings)))

    symmetry_errors: dict[str, float] = {}
    peak_detunings: dict[str, float] = {}
    exact_weak_argmax: dict[str, bool] = {}
    weak_gaps: dict[str, float] = {}
    strong_gains: dict[str, float] = {}
    zero_detuning_nonnegative = True

    for panel_key in PANEL_KEYS:
        values = np.asarray(panels[panel_key], dtype=float)
        symmetry_errors[panel_key] = float(
            np.max(np.abs(values - values[::-1]))
        )
        peak_by_detuning = np.max(values, axis=1)
        peak_index = int(np.argmax(peak_by_detuning))
        peak_energy = float(peak_by_detuning[peak_index])
        zero_energy = float(peak_by_detuning[zero_index])
        relative_advantage = (peak_energy - zero_energy) / peak_energy
        peak_detunings[panel_key] = float(detunings[peak_index])
        zero_detuning_nonnegative = (
            zero_detuning_nonnegative
            and float(np.min(values[zero_index]))
            >= -nonnegative_abs_tolerance
        )
        if panel_key in WEAK_PANEL_KEYS:
            weak_gaps[panel_key] = float(relative_advantage)
            exact_weak_argmax[panel_key] = peak_index == zero_index
        else:
            strong_gains[panel_key] = float(relative_advantage)

    weak_resonance_compatible = all(
        weak_gaps[key] <= weak_relative_tolerance
        for key in WEAK_PANEL_KEYS
    )
    strong_detuning_material = all(
        abs(peak_detunings[key]) >= strong_min_abs_normalized_detuning
        and strong_gains[key] >= strong_relative_gain_minimum
        for key in STRONG_PANEL_KEYS
    )
    symmetry_within_tolerance = (
        max(symmetry_errors.values()) <= symmetry_abs_tolerance
    )
    passed = bool(
        symmetry_within_tolerance
        and weak_resonance_compatible
        and strong_detuning_material
        and zero_detuning_nonnegative
    )
    return TS01DetuningAssessment(
        symmetry_max_abs_error=symmetry_errors,
        peak_normalized_detuning=peak_detunings,
        exact_weak_argmax_at_resonance=exact_weak_argmax,
        weak_relative_resonance_gap=weak_gaps,
        strong_relative_detuning_gain=strong_gains,
        weak_resonance_within_visual_tolerance=(
            weak_resonance_compatible
        ),
        strong_has_material_finite_detuning_gain=(
            strong_detuning_material
        ),
        zero_detuning_nonnegative=zero_detuning_nonnegative,
        symmetry_within_tolerance=symmetry_within_tolerance,
        passed=passed,
    )


def _validate_inputs(
    panels: Mapping[str, FloatArray],
    detunings: FloatArray,
    *,
    weak_relative_tolerance: float,
    strong_min_abs_normalized_detuning: float,
    strong_relative_gain_minimum: float,
    symmetry_abs_tolerance: float,
    nonnegative_abs_tolerance: float,
) -> None:
    missing = sorted(set(PANEL_KEYS) - set(panels))
    if missing:
        raise ValueError(f"missing TS01 panels: {', '.join(missing)}")
    if detunings.size < 3 or not np.isfinite(detunings).all():
        raise ValueError("normalized_detuning must be a finite grid")
    if not np.allclose(detunings, -detunings[::-1], rtol=0.0, atol=1e-12):
        raise ValueError("normalized_detuning must be symmetric about zero")
    zero_index = int(np.argmin(np.abs(detunings)))
    if abs(float(detunings[zero_index])) > 1e-12:
        raise ValueError("normalized_detuning must contain zero")

    for panel_key in PANEL_KEYS:
        values = np.asarray(panels[panel_key], dtype=float)
        if values.ndim != 2 or values.shape[0] != detunings.size:
            raise ValueError(
                f"{panel_key} must have shape (detuning, time)"
            )
        if values.shape[1] < 2 or not np.isfinite(values).all():
            raise ValueError(f"{panel_key} must be a finite time surface")
        if float(np.max(values)) <= 0.0:
            raise ValueError(f"{panel_key} must contain positive energy")

    bounded_fractions = {
        "weak_relative_tolerance": weak_relative_tolerance,
        "strong_relative_gain_minimum": strong_relative_gain_minimum,
    }
    for name, value in bounded_fractions.items():
        if not 0.0 <= value < 1.0:
            raise ValueError(f"{name} must be in [0, 1)")
    positive_tolerances = {
        "strong_min_abs_normalized_detuning": (
            strong_min_abs_normalized_detuning
        ),
        "symmetry_abs_tolerance": symmetry_abs_tolerance,
        "nonnegative_abs_tolerance": nonnegative_abs_tolerance,
    }
    for name, value in positive_tolerances.items():
        if value < 0.0:
            raise ValueError(f"{name} must be nonnegative")
