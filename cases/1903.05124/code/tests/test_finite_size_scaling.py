from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from finite_size_scaling import (  # noqa: E402
    ScalingCurve,
    bootstrap_measurement_fractions,
    collapse_cost,
    fit_data_collapse,
    fit_log_entropy,
    leave_one_size_out_fits,
)


class FiniteSizeScalingTests(unittest.TestCase):
    def synthetic_curves(
        self,
        *,
        critical_probability: float,
        critical_exponent: float,
        subtract_offsets: bool,
    ) -> tuple[ScalingCurve, ...]:
        measurement_fractions = np.linspace(0.33, 0.51, 37)
        curves: list[ScalingCurve] = []
        for size in (12, 16, 24, 32, 48):
            x = (measurement_fractions - critical_probability) * (
                size ** (1.0 / critical_exponent)
            )
            observable = -4.0 * np.tanh(x)
            if subtract_offsets:
                observable = observable + 0.35 * np.log(size)
            curves.append(
                ScalingCurve(
                    size=size,
                    measurement_fraction=measurement_fractions,
                    observable=observable,
                    standard_error=np.full_like(observable, 0.02),
                )
            )
        return tuple(curves)

    def test_recovers_tripartite_scaling_parameters(self) -> None:
        curves = self.synthetic_curves(
            critical_probability=0.42,
            critical_exponent=1.25,
            subtract_offsets=False,
        )
        fit = fit_data_collapse(
            curves,
            critical_probability_bounds=(0.38, 0.46),
            critical_exponent_bounds=(0.9, 1.6),
            grid_points=25,
            refinement_rounds=3,
        )
        self.assertAlmostEqual(fit.critical_probability, 0.42, delta=0.002)
        self.assertAlmostEqual(fit.critical_exponent, 1.25, delta=0.04)
        self.assertGreater(fit.comparisons, 0)
        self.assertFalse(fit.critical_probability_at_boundary)
        self.assertFalse(fit.critical_exponent_at_boundary)

    def test_subtracted_entropy_collapse_removes_size_offsets(self) -> None:
        curves = self.synthetic_curves(
            critical_probability=0.42,
            critical_exponent=1.25,
            subtract_offsets=True,
        )
        uncorrected, _ = collapse_cost(
            curves,
            critical_probability=0.42,
            critical_exponent=1.25,
        )
        corrected, comparisons = collapse_cost(
            curves,
            critical_probability=0.42,
            critical_exponent=1.25,
            subtract_at_critical_probability=True,
        )
        self.assertLess(corrected, uncorrected * 0.02)
        self.assertGreater(comparisons, 0)

    def test_leave_one_size_out_and_bootstrap_are_stable(self) -> None:
        curves = self.synthetic_curves(
            critical_probability=0.42,
            critical_exponent=1.25,
            subtract_offsets=False,
        )
        fit_kwargs = {
            "critical_probability_bounds": (0.38, 0.46),
            "critical_exponent_bounds": (0.9, 1.6),
            "grid_points": 17,
            "refinement_rounds": 2,
        }
        omitted = leave_one_size_out_fits(curves, **fit_kwargs)
        self.assertEqual(set(omitted), {12, 16, 24, 32, 48})
        self.assertLess(
            max(abs(fit.critical_probability - 0.42) for fit in omitted.values()),
            0.004,
        )
        bootstrap = bootstrap_measurement_fractions(
            curves,
            samples=5,
            sample_fraction=0.8,
            seed=19,
            **fit_kwargs,
        )
        self.assertAlmostEqual(
            float(np.mean(bootstrap.critical_probabilities)),
            0.42,
            delta=0.004,
        )
        self.assertAlmostEqual(
            float(np.mean(bootstrap.critical_exponents)),
            1.25,
            delta=0.06,
        )

    def test_search_reports_when_the_optimum_hits_a_bound(self) -> None:
        curves = self.synthetic_curves(
            critical_probability=0.42,
            critical_exponent=1.25,
            subtract_offsets=False,
        )
        fit = fit_data_collapse(
            curves,
            critical_probability_bounds=(0.44, 0.5),
            critical_exponent_bounds=(0.9, 1.6),
            grid_points=17,
            refinement_rounds=2,
        )
        self.assertTrue(fit.critical_probability_at_boundary)
        self.assertGreaterEqual(fit.critical_probability, 0.44)

    def test_weighted_logarithmic_entropy_fit_recovers_alpha(self) -> None:
        sizes = np.array([8, 12, 16, 24, 32, 48, 64])
        entropies = 1.23 * np.log(sizes) - 0.7
        fit = fit_log_entropy(sizes, entropies, np.full(len(sizes), 0.03))
        self.assertAlmostEqual(fit.alpha, 1.23, places=10)
        self.assertAlmostEqual(fit.intercept, -0.7, places=10)
        self.assertAlmostEqual(fit.r_squared, 1.0, places=12)

    def test_curve_contract_rejects_unsorted_measurement_fractions(self) -> None:
        with self.assertRaises(ValueError):
            ScalingCurve(
                size=12,
                measurement_fraction=np.array([0.2, 0.1, 0.3]),
                observable=np.zeros(3),
                standard_error=np.ones(3),
            )


if __name__ == "__main__":
    unittest.main()
