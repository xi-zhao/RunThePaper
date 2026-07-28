from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad

from src.wigner_gme import (
    SOURCE_PRINTED_GME_BOUND,
    STATE_DERIVED_GME_BOUND,
    W_STATE_GME_THRESHOLD,
    characteristic_witness_matrix,
    characteristic_witness_spectrum,
    convolve_with_gaussian_kernel,
    illustrative_com_density,
    illustrative_com_wigner,
    illustrative_relative_parity,
    illustrative_slice_metrics,
    illustrative_slice_signed_integral,
    illustrative_slice_wigner,
    illustrative_state_norm,
    illustrative_wigner_cut,
    smoothed_origin_exact,
    unique_pairwise_differences,
    w_state_characteristic_slice,
    w_state_critical_radius,
    w_state_disk_volume,
    w_state_wigner_slice,
    wigner_fock_element,
)


def test_fock_wigner_convention_and_hermiticity() -> None:
    alpha = np.asarray([0.0, 0.2 + 0.3j, -0.4 + 0.1j])
    vacuum = np.asarray(wigner_fock_element(0, 0, alpha))
    expected = (2.0 / np.pi) * np.exp(-2.0 * np.abs(alpha) ** 2)
    np.testing.assert_allclose(vacuum.real, expected, atol=1e-14)
    np.testing.assert_allclose(vacuum.imag, 0.0, atol=1e-14)

    forward = np.asarray(wigner_fock_element(4, 2, alpha))
    reverse = np.asarray(wigner_fock_element(2, 4, alpha))
    np.testing.assert_allclose(reverse, np.conjugate(forward), atol=1e-14)


def test_w_state_collective_formulas() -> None:
    alpha = np.asarray([0.0, 0.1 + 0.2j, 0.7j])
    gamma = np.sqrt(3.0) * alpha
    expected_wigner = (
        np.asarray(wigner_fock_element(1, 1, gamma)).real
        * (2.0 / np.pi) ** 2
    )
    np.testing.assert_allclose(
        w_state_wigner_slice(alpha),
        expected_wigner,
        atol=1e-14,
    )

    xi = np.asarray([0.0, 0.4 + 0.1j])
    expected_characteristic = (
        1.0 - 3.0 * np.abs(xi) ** 2
    ) * np.exp(-1.5 * np.abs(xi) ** 2)
    np.testing.assert_allclose(
        w_state_characteristic_slice(xi),
        expected_characteristic,
        atol=1e-14,
    )


def test_w_state_disk_volume_and_exact_threshold() -> None:
    for radius in (0.2, 0.7, 1.0):
        numeric, _ = quad(
            lambda value: 4.0
            * value
            * abs(12.0 * value**2 - 1.0)
            * math.exp(-6.0 * value**2),
            0.0,
            radius,
            epsabs=1e-13,
            epsrel=1e-13,
            points=[1.0 / (2.0 * math.sqrt(3.0))]
            if radius > 1.0 / (2.0 * math.sqrt(3.0))
            else None,
        )
        assert math.isclose(float(w_state_disk_volume(radius)), numeric, abs_tol=2e-12)

    critical = w_state_critical_radius()
    assert math.isclose(
        float(w_state_disk_volume(critical)),
        W_STATE_GME_THRESHOLD,
        abs_tol=2e-14,
    )
    assert critical < 0.7
    assert float(w_state_disk_volume(0.7)) > W_STATE_GME_THRESHOLD


def test_characteristic_witness_reproduces_paper_value() -> None:
    matrix = characteristic_witness_matrix()
    spectrum = characteristic_witness_spectrum()
    assert matrix.shape == (7, 7)
    np.testing.assert_allclose(matrix, matrix.T, atol=1e-15)
    assert math.isclose(float(np.trace(matrix)), 1.0, abs_tol=1e-14)
    assert len(unique_pairwise_differences()) == 19
    assert np.sum(spectrum < 0.0) == 1
    assert math.isclose(-float(spectrum[0]), 0.017580375648038153, abs_tol=2e-14)


def test_illustrative_state_normalization_and_reduction() -> None:
    assert math.isclose(illustrative_state_norm(), 1.0, abs_tol=1e-15)
    assert math.isclose(illustrative_relative_parity(), -13.0 / 25.0, abs_tol=1e-15)
    density = illustrative_com_density()
    np.testing.assert_allclose(density, density.conjugate().T, atol=1e-15)
    assert math.isclose(float(np.trace(density).real), 1.0, abs_tol=1e-15)
    np.testing.assert_allclose(
        np.linalg.eigvalsh(density),
        [0.0, 0.0, 0.0, 0.2, 0.8],
        atol=1e-14,
    )


def test_generic_cut_matches_derived_equal_slice_polynomial() -> None:
    alpha = np.asarray(
        [
            0.0,
            0.12 + 0.23j,
            -0.31 + 0.08j,
            0.6 - 0.2j,
        ]
    )
    generic = illustrative_wigner_cut(np.sqrt(3.0) * alpha, np.zeros_like(alpha))
    polynomial = illustrative_slice_wigner(alpha)
    np.testing.assert_allclose(generic, polynomial, atol=2e-14)


def test_illustrative_slice_integrals_expose_source_inconsistency() -> None:
    metrics = illustrative_slice_metrics(
        radial_order=240,
        angular_order=720,
        radial_cutoff=4.0,
    )
    assert math.isclose(
        float(metrics["signed_integral"]),
        illustrative_slice_signed_integral(),
        abs_tol=2e-12,
    )
    assert math.isclose(
        float(metrics["negativity_volume"]),
        0.263699,
        abs_tol=1e-4,
    )
    assert float(metrics["negativity_volume"]) > STATE_DERIVED_GME_BOUND
    assert float(metrics["negativity_volume"]) < SOURCE_PRINTED_GME_BOUND


def test_smoothed_origin_matches_exact_end_matter_value() -> None:
    exact = -7.0 / (16.0 * np.pi)
    assert math.isclose(smoothed_origin_exact(), exact, abs_tol=1e-15)

    axis = np.linspace(-4.0, 4.0, 601)
    x, y = np.meshgrid(axis, axis, indexing="xy")
    field = np.asarray(illustrative_com_wigner(x + 1.0j * y))
    smoothed = convolve_with_gaussian_kernel(field, axis)
    center = len(axis) // 2
    assert math.isclose(float(smoothed[center, center]), exact, abs_tol=2e-10)
