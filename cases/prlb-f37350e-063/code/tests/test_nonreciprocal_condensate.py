"""Scientific unit tests for the full-paper independent model."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nonreciprocal_condensate import (  # noqa: E402
    ModelParameters,
    complex_rhs,
    finite_n_vacuum_threshold,
    from_real,
    hatano_nelson_matrix,
    pbc_decay_and_frequency,
    pbc_stability_matrix,
    real_jacobian,
    real_rhs,
    static_amplitude_jacobian,
    static_amplitude_residual,
    static_complex_state,
    tangent_rhs,
    thermodynamic_vacuum_threshold,
    to_real,
)


def central_difference_jacobian(function, state: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    columns = []
    for index in range(state.size):
        shift = np.zeros_like(state)
        shift[index] = epsilon
        columns.append((function(state + shift) - function(state - shift)) / (2 * epsilon))
    return np.stack(columns, axis=1)


def test_hatano_nelson_pbc_eigenvalues_match_dispersion() -> None:
    n = 17
    p = ModelParameters(kappa=0.4, gamma=0.7, theta=np.pi)
    matrix = hatano_nelson_matrix(n, p, boundary="periodic")
    actual = np.linalg.eigvals(matrix)
    q = 2.0 * np.pi * np.arange(n) / n
    decay, frequency = pbc_decay_and_frequency(q, p)
    expected = frequency + 1j * (p.kappa - decay)
    for value in expected:
        assert np.min(np.abs(actual - value)) < 2e-12


def test_pbc_bogoliubov_matrix_requires_factor_four_in_closed_form() -> None:
    p = ModelParameters(kappa=3.0, gamma=0.5, theta=np.pi)
    q = 1.1
    k = 0.4
    matrix = pbc_stability_matrix(q, k, p)
    direct = np.linalg.eigvals(matrix)
    a, d = matrix[0, 0], matrix[1, 1]
    lam = -matrix[0, 1]
    derived = np.asarray(
        [
            0.5 * (a + d) + 0.5 * np.sqrt((a - d) ** 2 + 4.0 * lam**2),
            0.5 * (a + d) - 0.5 * np.sqrt((a - d) ** 2 + 4.0 * lam**2),
        ]
    )
    printed = np.asarray(
        [
            0.5 * (a + d) + 0.5 * np.sqrt((a - d) ** 2 + lam**2),
            0.5 * (a + d) - 0.5 * np.sqrt((a - d) ** 2 + lam**2),
        ]
    )
    assert max(min(abs(value - candidate) for candidate in direct) for value in derived) < 1e-12
    assert max(min(abs(value - candidate) for candidate in direct) for value in printed) > 1e-3


def test_exact_real_jacobian_matches_central_difference() -> None:
    rng = np.random.default_rng(9)
    alpha = 0.2 * (rng.normal(size=6) + 1j * rng.normal(size=6))
    p = ModelParameters(kappa=1.7, gamma=0.4, theta=np.pi)
    state = to_real(alpha)
    numeric = central_difference_jacobian(lambda x: real_rhs(x, p), state)
    analytic = real_jacobian(alpha, p)
    assert np.allclose(analytic, numeric, atol=2e-9, rtol=2e-9)
    assert np.allclose(from_real(to_real(alpha)), alpha)


def test_static_real_reduction_solves_full_complex_equation() -> None:
    rng = np.random.default_rng(4)
    amplitude = rng.uniform(0.1, 0.8, size=8)
    p = ModelParameters(kappa=2.1, gamma=1.6, theta=np.pi)
    reduced = static_amplitude_residual(amplitude, p)
    lifted = complex_rhs(static_complex_state(amplitude), p)
    sites = np.arange(1, amplitude.size + 1)
    assert np.allclose(lifted / (1j**sites), reduced, atol=1e-14)


def test_static_reduced_jacobian_matches_central_difference() -> None:
    amplitude = np.linspace(0.1, 0.8, 8)
    p = ModelParameters(kappa=1.3, gamma=2.0, theta=np.pi)
    numeric = central_difference_jacobian(
        lambda x: static_amplitude_residual(x, p), amplitude
    )
    analytic = static_amplitude_jacobian(amplitude, p)
    assert np.allclose(analytic, numeric, atol=2e-9, rtol=2e-9)


def test_complex_tangent_rhs_matches_real_jacobian_action() -> None:
    rng = np.random.default_rng(21)
    alpha = 0.3 * (rng.normal(size=7) + 1j * rng.normal(size=7))
    perturbations = rng.normal(size=(3, 7)) + 1j * rng.normal(size=(3, 7))
    p = ModelParameters(kappa=2.2, gamma=0.35, theta=np.pi)
    jacobian = real_jacobian(alpha, p)
    for perturbation in perturbations:
        expected = jacobian @ to_real(perturbation)
        actual = to_real(tangent_rhs(alpha, perturbation, p))
        assert np.allclose(actual, expected, atol=2e-13, rtol=2e-13)


def test_uniform_bulk_static_state_and_vacuum_thresholds() -> None:
    p = ModelParameters(kappa=1.7, gamma=1.4, theta=np.pi)
    amplitude = np.full(32, np.sqrt(p.kappa / p.nonlinear_loss))
    residual = static_amplitude_residual(amplitude, p)
    assert np.max(np.abs(residual[1:-1])) < 1e-13
    assert finite_n_vacuum_threshold(200, 0.3) == 0.6
    expected = 4.0 - 2.0 * np.sqrt(3.0) * np.cos(np.pi / 201.0)
    assert np.isclose(finite_n_vacuum_threshold(200, 2.0), expected)
    assert np.isclose(thermodynamic_vacuum_threshold(2.0), 4.0 - 2.0 * np.sqrt(3.0))
