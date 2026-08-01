from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from squeezing_nonreciprocity import (  # noqa: E402
    closed_charger_squeezed_energy_dynamics,
    effective_enhancement,
    forward_transmission,
    forward_transmission_zero_squeezed_frequency,
    gaussian_battery_energy_dynamics,
    gaussian_master_equation_energy_dynamics,
    gaussian_invariant,
    optimal_transmission_coupling,
    passive_state_energy,
    steady_state_energy,
    steady_state_energy_derivative,
    steady_state_ergotropy,
    steady_state_energy_nonsqueezed,
)


def test_symmetric_squeezing_leaves_effective_coupling_unchanged() -> None:
    r = np.linspace(0.0, 2.0, 21)
    actual = effective_enhancement(r, r, 0.0)
    np.testing.assert_allclose(actual, 1.0, rtol=0.0, atol=1e-12)


def test_pi_phase_or_single_mode_squeezing_reaches_cosh_2r() -> None:
    r = 1.2
    delta_r = np.linspace(0.0, 2.0 * r, 31)
    r_a = r + delta_r / 2.0
    r_b = r - delta_r / 2.0
    np.testing.assert_allclose(
        effective_enhancement(r_a, r_b, np.pi),
        np.cosh(2.0 * r),
        rtol=1e-12,
        atol=1e-12,
    )
    phase = np.linspace(0.0, 2.0 * np.pi, 51)
    np.testing.assert_allclose(
        effective_enhancement(2.0 * r, 0.0, phase),
        np.cosh(2.0 * r),
        rtol=1e-12,
        atol=1e-12,
    )


def test_energy_identity_holds_for_broadcast_grids() -> None:
    coupling = np.logspace(-6, -3, 30)[:, None]
    squeezing = np.linspace(0.0, 2.0, 20)[None, :]
    kappa = 8e-5
    drive = 1e-4
    baseline = steady_state_energy_nonsqueezed(coupling, kappa, drive)
    energy_a = steady_state_energy("a", coupling, squeezing, kappa, drive)
    energy_b = steady_state_energy("b", coupling, squeezing, kappa, drive)
    energy_c = steady_state_energy("c", coupling, squeezing, kappa, drive)
    np.testing.assert_allclose(
        energy_a + energy_b - baseline,
        energy_c,
        rtol=5e-13,
        atol=1e-13,
    )


def test_closed_derivatives_match_centered_finite_differences() -> None:
    kappa = 8e-5
    drive = 1e-4
    coupling = 2.5e-4
    squeezing = 1.1
    step = coupling * 1e-5
    for case in ("a", "b", "c"):
        finite_difference = (
            steady_state_energy(case, coupling + step, squeezing, kappa, drive)
            - steady_state_energy(case, coupling - step, squeezing, kappa, drive)
        ) / (2.0 * step)
        analytic = steady_state_energy_derivative(
            case, coupling, squeezing, kappa, drive
        )
        np.testing.assert_allclose(analytic, finite_difference, rtol=2e-8, atol=1e-8)


def test_general_transmission_reduces_to_main_text_formula() -> None:
    kappa_a = 8e-5
    kappa_b = 8e-5
    coupling = optimal_transmission_coupling(kappa_a, kappa_b)
    collective_decay = 2.0 * coupling
    omega = np.linspace(-5.0, 5.0, 401) * collective_decay
    configurations = [
        (1.0, 1.0, np.pi),
        (0.2, 1.8, np.pi / 2.0),
        (1.0, 1.0, np.pi / 2.0),
        (0.0, 0.0, 0.0),
    ]
    for r_a, r_b, delta_theta in configurations:
        general = forward_transmission(
            omega,
            0.0,
            r_a,
            r_b,
            delta_theta,
            coupling,
            kappa_a,
            kappa_b,
            collective_decay,
        )
        reduced = forward_transmission_zero_squeezed_frequency(
            omega,
            r_a,
            r_b,
            delta_theta,
            coupling,
            kappa_a,
            kappa_b,
            collective_decay,
        )
        np.testing.assert_allclose(general, reduced, rtol=2e-14, atol=1e-13)


def test_optimal_transmission_coupling_is_local_maximum() -> None:
    kappa = 8e-5
    optimum = optimal_transmission_coupling(kappa, kappa)

    def peak(coupling: float) -> float:
        return float(
            forward_transmission_zero_squeezed_frequency(
                0.0,
                1.0,
                1.0,
                np.pi,
                coupling,
                kappa,
                kappa,
                2.0 * coupling,
            )
        )

    assert peak(optimum) > peak(0.9 * optimum)
    assert peak(optimum) > peak(1.1 * optimum)


def test_passive_energy_vanishes_without_squeezing() -> None:
    coupling = 1e-3
    kappa = 8e-5
    drive = 1e-4
    baseline = float(steady_state_energy_nonsqueezed(coupling, kappa, drive))
    for case in ("a", "b", "c"):
        np.testing.assert_allclose(
            gaussian_invariant(case, coupling, 0.0, kappa, drive),
            1.0,
            rtol=0.0,
            atol=2e-12,
        )
        np.testing.assert_allclose(
            passive_state_energy(case, coupling, 0.0, kappa, drive),
            0.0,
            rtol=0.0,
            atol=2e-12,
        )
        np.testing.assert_allclose(
            steady_state_ergotropy(case, coupling, 0.0, kappa, drive),
            baseline,
            rtol=2e-12,
            atol=2e-12,
        )


def test_gaussian_dynamics_recovers_steady_energy_and_initial_reservoir_slope() -> None:
    coupling = 1e-3
    kappa = 8e-5
    drive = 1e-4
    squeezing = 1.5
    times = np.linspace(0.0, 10000.0, 1001)
    expected_slope = 2.0 * coupling * np.sinh(squeezing) ** 2
    for case in ("b", "c"):
        energy = gaussian_battery_energy_dynamics(
            case,
            times,
            coupling,
            kappa,
            kappa,
            drive,
            squeezing,
        )
        observed_slope = (energy[1] - energy[0]) / (times[1] - times[0])
        np.testing.assert_allclose(observed_slope, expected_slope, rtol=3e-2)
        np.testing.assert_allclose(
            energy[-1],
            steady_state_energy(case, coupling, squeezing, kappa, drive),
            rtol=2e-3,
            atol=1e-8,
        )


def test_master_equation_gaussianization_recovers_all_steady_energies() -> None:
    coupling = 1e-3
    kappa = 8e-5
    drive = 1e-4
    squeezing = 1.0
    times = np.linspace(0.0, 10000.0, 1001)
    expected = {
        "baseline": steady_state_energy_nonsqueezed(coupling, kappa, drive),
        **{
            case: steady_state_energy(case, coupling, squeezing, kappa, drive)
            for case in ("a", "b", "c")
        },
    }
    for case in ("baseline", "a", "b", "c"):
        energy = gaussian_master_equation_energy_dynamics(
            case,
            times,
            coupling,
            kappa,
            kappa,
            drive,
            squeezing,
        )
        assert energy[0] == 0.0
        np.testing.assert_allclose(
            energy[-1],
            expected[case],
            rtol=2e-3,
            atol=1e-8,
        )


def test_closed_charger_dynamics_reaches_published_steady_energy() -> None:
    coupling = 1e-3
    kappa_a = 8e-5
    kappa_b = kappa_a + 1e-7
    drive = 1e-4
    squeezing = 1.5
    energy = closed_charger_squeezed_energy_dynamics(
        np.linspace(0.0, 10000.0, 1001),
        coupling,
        2.0 * coupling + kappa_a,
        2.0 * coupling + kappa_b,
        drive,
        squeezing,
    )
    assert energy[0] == 0.0
    assert np.all(energy >= 0.0)
    np.testing.assert_allclose(
        energy[-1],
        steady_state_energy("a", coupling, squeezing, kappa_a, drive),
        rtol=1e-3,
        atol=1e-8,
    )


def test_charger_phase_pi_implements_enhanced_classical_drive() -> None:
    times = np.linspace(0.0, 1200.0, 61)
    phase_pi = gaussian_battery_energy_dynamics(
        "a",
        times,
        1e-3,
        8e-5,
        8e-5,
        1e-4,
        1.5,
        charger_phase=np.pi,
        reservoir_phase=np.pi,
    )
    phase_zero = gaussian_battery_energy_dynamics(
        "a",
        times,
        1e-3,
        8e-5,
        8e-5,
        1e-4,
        1.5,
        charger_phase=0.0,
        reservoir_phase=0.0,
    )
    assert phase_pi[20] > phase_zero[20]
