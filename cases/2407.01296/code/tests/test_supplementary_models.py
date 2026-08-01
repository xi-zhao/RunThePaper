from __future__ import annotations

import numpy as np

from src.geometry_adaptive import (
    basis_hopping_model,
    build_obc_hamiltonian,
    diamond_sites,
    full_right_eigensystem,
    model_eq11,
    model_eq15,
    square_sites,
)
from src.supplementary_models import (
    biorthogonal_diagonal_response,
    double_chain_characteristic_coefficients,
    double_chain_hamiltonian,
    double_chain_tdl_spectrum,
    find_fermi_points,
    fit_boundary_exponential,
    laurent_bloch_value,
    mean_absolute_first_order_shift,
    model_s27,
    select_target_spatial_eigenstate,
    site_probability,
    spatial_profile_metrics,
    winding_sweep,
)


def test_s27_hoppings_match_the_printed_bloch_formula() -> None:
    momentum_x = np.asarray((-1.2, -0.1, 0.7))
    momentum_y = np.asarray((0.3, -0.9, 1.4))
    beta_x = np.exp(1j * momentum_x)
    beta_y = np.exp(1j * momentum_y)
    expected = (
        6.0 * beta_x
        - 4.0 / beta_x
        + 6.0 * beta_y
        - 4.0 / beta_y
        + 0.5
        * (
            beta_x * beta_y
            + beta_x / beta_y
            + beta_y / beta_x
            + 1.0 / (beta_x * beta_y)
        )
    )

    np.testing.assert_allclose(
        laurent_bloch_value(momentum_x, momentum_y, model_s27()),
        expected,
        rtol=1e-13,
        atol=1e-13,
    )


def test_s5_paper_geometries_have_the_caption_site_counts() -> None:
    assert len(square_sites(80)) == 6400
    assert len(diamond_sites(56)) == 6385


def test_s5_spatial_state_selection_is_deterministic_and_rule_based() -> None:
    sites = square_sites(12)
    matrix = build_obc_hamiltonian(sites, model_s27())
    narrowest = select_target_spatial_eigenstate(
        sites,
        matrix,
        1.5 + 8.0j,
        selection="narrowest",
        candidate_count=8,
    )
    widest = select_target_spatial_eigenstate(
        sites,
        matrix,
        -1.0 + 10.0j,
        selection="widest",
        candidate_count=8,
    )
    narrowest_metrics = spatial_profile_metrics(sites, narrowest.right_eigenvector)
    widest_metrics = spatial_profile_metrics(sites, widest.right_eigenvector)

    assert narrowest.normalized_residual < 1e-9
    assert widest.normalized_residual < 1e-9
    assert 0.0 < narrowest_metrics.boundary_mass <= 1.0
    assert widest_metrics.rms_width > narrowest_metrics.rms_width
    assert widest_metrics.effective_site_count > narrowest_metrics.effective_site_count


def test_s24_matrix_matches_the_two_laurent_chains() -> None:
    matrix = double_chain_hamiltonian(4).toarray()
    assert matrix[0, 0] == 0.5
    assert matrix[1, 1] == -0.5
    assert matrix[0, 1] == matrix[1, 0] == 0.01
    assert matrix[0, 2] == 1.0
    assert matrix[2, 0] == 0.5
    assert matrix[1, 3] == 0.5
    assert matrix[3, 1] == 1.0


def test_s24_characteristic_quartic_matches_direct_bloch_determinant() -> None:
    energy = 0.37 + 0.19j
    beta = 0.83 * np.exp(0.71j)
    bloch = np.asarray(
        (
            (0.5 / beta + beta + 0.5, 0.01),
            (0.01, 1.0 / beta + 0.5 * beta - 0.5),
        ),
        dtype=np.complex128,
    )
    direct = np.linalg.det(bloch - energy * np.eye(2))
    quartic = np.polyval(double_chain_characteristic_coefficients(energy), beta)

    np.testing.assert_allclose(quartic / beta**2, direct, rtol=1e-13, atol=1e-13)


def test_s24_tdl_is_traced_from_the_middle_root_condition() -> None:
    spectrum = double_chain_tdl_spectrum(
        real_samples=121,
        imaginary_samples=61,
        root_gap_tolerance=2e-7,
    )

    assert spectrum.energies.size > 100
    assert float(np.max(spectrum.root_gaps)) <= spectrum.root_gap_tolerance
    rounded = {
        (round(float(value.real), 12), round(float(value.imag), 12))
        for value in spectrum.energies
    }
    assert all((real, round(-imaginary, 12)) in rounded for real, imaginary in rounded)


def test_s24_central_state_localization_scales_with_inverse_length() -> None:
    lengths = np.asarray((20, 40, 60), dtype=np.float64)
    kappas: list[float] = []
    for length in lengths.astype(int):
        eigensystem = full_right_eigensystem(double_chain_hamiltonian(length))
        selected = int(np.argmax(eigensystem.eigenvalues.imag))
        fit = fit_boundary_exponential(
            site_probability(eigensystem.right_eigenvectors[:, selected])
        )
        kappas.append(fit.kappa)
        assert fit.r_squared > 0.88

    assert kappas[0] > kappas[1] > kappas[2]
    coefficients = np.polyfit(1.0 / lengths, np.asarray(kappas), 1)
    prediction = np.polyval(coefficients, 1.0 / lengths)
    r_squared = 1.0 - np.sum((kappas - prediction) ** 2) / np.sum(
        (kappas - np.mean(kappas)) ** 2
    )
    assert coefficients[0] > 0.0
    assert abs(coefficients[1]) < 0.02
    assert r_squared > 0.99


def test_s28_winding_distinguishes_normal_and_critical_models() -> None:
    fixed = (np.arange(121, dtype=np.float64) + 0.5) * (2.0 * np.pi / 121) - np.pi
    normal = winding_sweep(
        model_eq11(), fixed, integration_axis=1, momentum_samples=1024
    )
    critical = winding_sweep(
        basis_hopping_model(model_eq15(), "rhombus"),
        fixed,
        integration_axis=1,
        momentum_samples=1024,
    )

    assert set(normal.tolist()) == {0, 1}
    assert set(critical.tolist()) == {-1, 1}


def test_fermi_point_charges_are_balanced() -> None:
    normal = find_fermi_points(model_eq11())
    critical = find_fermi_points(model_eq15())

    assert len(normal) == 2
    assert len(critical) == 4
    assert sum(point.charge for point in normal) == 0
    assert sum(point.charge for point in critical) == 0
    assert max(point.residual for point in (*normal, *critical)) < 1e-9


def test_s29_biorthogonal_weights_reproduce_a_uniform_shift() -> None:
    matrix = build_obc_hamiltonian(square_sites(4), model_eq11())
    response = biorthogonal_diagonal_response(matrix)
    samples = np.full((3, matrix.shape[0]), 0.125)

    assert response.maximum_uniform_shift_error < 1e-10
    assert response.maximum_sampled_eigenpair_residual < 1e-10
    assert abs(mean_absolute_first_order_shift(response, samples) - 0.125) < 1e-10


def test_s29_common_random_samples_scale_exactly_with_disorder_strength() -> None:
    matrix = build_obc_hamiltonian(diamond_sites(3), model_eq15())
    response = biorthogonal_diagonal_response(matrix)
    unit_samples = np.random.default_rng(240701296).random((8, matrix.shape[0]))
    unit_shift = mean_absolute_first_order_shift(response, unit_samples)

    assert np.isclose(
        mean_absolute_first_order_shift(response, 0.2 * unit_samples),
        0.2 * unit_shift,
        rtol=1e-12,
    )


def test_s7_rhombus_counts_expose_the_middle_caption_typo() -> None:
    counts = [len(diamond_sites(radius)) for radius in (14, 21, 28)]
    assert counts == [421, 925, 1625]
    assert counts[1] != 935
