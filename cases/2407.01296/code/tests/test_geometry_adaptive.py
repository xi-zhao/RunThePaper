from __future__ import annotations

import numpy as np

from src.geometry_adaptive import (
    aggregate_right_density,
    amoeba_potential,
    basis_hopping_model,
    build_obc_hamiltonian,
    cut_coordinate_interval_sites,
    cut_coordinate_sites,
    diamond_sites,
    eigensystem_residuals,
    full_spectrum,
    full_right_eigensystem,
    fit_gaussian_profile,
    geometry_adaptive_potential,
    linear_fit_with_confidence,
    model_eq11,
    model_eq15,
    reflection_symmetrized_density,
    rhombus_edge_profile,
    rhombus_localization_metrics,
    ronkin_potential,
    sparse_spectral_potential,
    sparse_spectral_potential_consensus,
    spectral_potential,
    spectral_density_from_potential,
    square_sites,
    symmetric_cloud_distance,
    target_right_eigenstate,
)
from src.gbz import laurent_energy, solve_gbz_for_energy


def test_paper_geometry_site_counts() -> None:
    assert len(square_sites(40)) == 1600
    assert len(diamond_sites(30)) == 1861
    assert len(diamond_sites(30)) == 1 + 2 * 30 * 31
    assert len(diamond_sites(42)) == 3613


def test_equal_cut_bounds_are_the_integer_diamond() -> None:
    assert cut_coordinate_sites(5, 5) == diamond_sites(5)


def test_reconstructed_fig4_intervals_match_paper_site_counts() -> None:
    assert len(cut_coordinate_interval_sites((-69, 69), (-23, 23))) == 3267
    assert len(cut_coordinate_interval_sites((-57, 57), (-29, 27))) == 3278


def test_eq11_hopping_entries_match_the_laurent_terms() -> None:
    sites = square_sites(3)
    matrix = build_obc_hamiltonian(sites, model_eq11()).toarray()
    index = {site: i for i, site in enumerate(sites)}
    origin = index[(1, 1)]
    assert matrix[origin, index[(0, 1)]] == 2.0
    assert matrix[origin, index[(2, 0)]] == 0.5
    assert matrix[origin, index[(1, 2)]] == 1.5
    assert matrix[origin, index[(0, 2)]] == 0.9
    assert set(np.unique(matrix)) <= {0.0, 0.5, 0.9, 1.5, 2.0}


def test_eq15_is_complex_symmetric_on_an_open_rhombus() -> None:
    matrix = build_obc_hamiltonian(diamond_sites(4), model_eq15()).toarray()
    np.testing.assert_allclose(matrix, matrix.T)


def test_one_site_has_zero_hamiltonian_and_density_normalization() -> None:
    matrix = build_obc_hamiltonian(((0, 0),), model_eq11())
    eigensystem = full_right_eigensystem(matrix)
    np.testing.assert_allclose(eigensystem.eigenvalues, [0.0])
    np.testing.assert_allclose(aggregate_right_density(eigensystem.right_eigenvectors), [1.0])


def test_full_eigensystem_residuals_are_small() -> None:
    matrix = build_obc_hamiltonian(diamond_sites(4), model_eq15())
    eigensystem = full_right_eigensystem(matrix)
    assert np.max(eigensystem_residuals(matrix, eigensystem, batch_size=7)) < 1e-12


def test_reflection_symmetrization_preserves_mass_and_symmetry() -> None:
    sites = diamond_sites(3)
    density = np.arange(1.0, len(sites) + 1.0)
    symmetrized = reflection_symmetrized_density(sites, density)
    index = {site: position for position, site in enumerate(sites)}
    assert np.isclose(symmetrized.sum(), density.sum())
    for (x, y), value in zip(sites, symmetrized, strict=True):
        assert np.isclose(value, symmetrized[index[(-x, y)]])
        assert np.isclose(value, symmetrized[index[(x, -y)]])


def test_rhombus_localization_metrics_detect_boundary_not_corner_weight() -> None:
    sites = diamond_sites(10)
    coordinates = np.asarray(sites)
    radial = np.abs(coordinates[:, 0]) + np.abs(coordinates[:, 1])
    density = np.exp(-0.8 * (10 - radial))
    density *= np.exp(-0.02 * (coordinates[:, 0] - coordinates[:, 1]) ** 2)
    metrics = rhombus_localization_metrics(sites, density)
    assert metrics["boundary_enrichment"] > 1.5
    assert (
        metrics["corner_fraction_of_boundary_mass"]
        < metrics["corner_fraction_of_boundary_sites"]
    )


def test_spectral_potential_is_jointly_translation_invariant() -> None:
    eigenvalues = np.array([-1 + 0.2j, 0.4 - 0.7j, 2.1 + 0.5j])
    probe = 0.3 + 0.1j
    shift = -0.8 + 1.4j
    assert np.isclose(
        spectral_potential(eigenvalues, probe),
        spectral_potential(eigenvalues + shift, probe + shift),
    )


def test_sparse_log_determinant_matches_eigenvalue_potential() -> None:
    matrix = build_obc_hamiltonian(diamond_sites(4), model_eq15())
    eigenvalues = full_spectrum(matrix)
    probe = 0.17 + 0.23j
    assert np.isclose(
        sparse_spectral_potential(matrix, probe),
        spectral_potential(eigenvalues, probe),
        rtol=1e-11,
        atol=1e-11,
    )


def test_sparse_log_determinant_is_invariant_under_lu_ordering() -> None:
    matrix = build_obc_hamiltonian(square_sites(5), model_eq11())
    consensus = sparse_spectral_potential_consensus(matrix, 0.31 + 0.27j)
    assert consensus.ordering_spread < 1e-12
    assert len(consensus.estimates) == 3
    assert np.isclose(consensus.potential, np.median(consensus.estimates))


def test_eq15_ronkin_minimum_is_not_above_zero_deformation() -> None:
    energy = 0.1 + 0.1j
    zero = ronkin_potential(
        energy,
        model_eq15(),
        deformation_x=0.0,
        deformation_y=0.0,
        momentum_samples=32,
    )
    minimum = amoeba_potential(energy, model_eq15(), momentum_samples=32)
    assert minimum.potential <= zero + 1e-8


def test_rhombus_basis_transform_preserves_eq11_energy() -> None:
    beta_1 = 1.13 * np.exp(0.2j)
    beta_2 = 0.87 * np.exp(-0.4j)
    beta_x = beta_1 / beta_2
    beta_y = beta_1 * beta_2
    original = sum(
        amplitude * beta_x**dx * beta_y**dy
        for (dx, dy), amplitude in model_eq11().items()
    )
    transformed = sum(
        amplitude * beta_1**d1 * beta_2**d2
        for (d1, d2), amplitude in basis_hopping_model(
            model_eq11(), "rhombus"
        ).items()
    )
    assert np.allclose(original, transformed, rtol=1e-13, atol=1e-13)


def test_geometry_potential_respects_complex_conjugation() -> None:
    energy = 0.4 + 0.6j
    upper = geometry_adaptive_potential(
        energy,
        model_eq11(),
        basis="square",
        momentum_samples=32,
        tolerance=1e-3,
    )
    lower = geometry_adaptive_potential(
        energy.conjugate(),
        model_eq11(),
        basis="square",
        momentum_samples=32,
        tolerance=1e-3,
    )
    assert np.isclose(upper.potential, lower.potential, rtol=2e-4, atol=2e-4)


def test_constant_potential_has_zero_spectral_density() -> None:
    density = spectral_density_from_potential(
        np.ones((5, 5), dtype=float),
        real_step=0.2,
        imaginary_step=0.3,
    )
    assert np.allclose(density, 0.0, atol=1e-12)


def test_three_point_laplacian_matches_quadratic_potential() -> None:
    real_axis = np.linspace(-1.0, 1.0, 7)
    imaginary_axis = np.linspace(-1.5, 1.5, 7)
    real_grid, imaginary_grid = np.meshgrid(real_axis, imaginary_axis)
    density = spectral_density_from_potential(
        real_grid**2 + imaginary_grid**2,
        real_step=float(real_axis[1] - real_axis[0]),
        imaginary_step=float(imaginary_axis[1] - imaginary_axis[0]),
        trim_boundary=True,
    )
    assert density.shape == (5, 5)
    np.testing.assert_allclose(density, 2.0 / np.pi, rtol=1e-13, atol=1e-13)


def test_transpose_preserves_spectrum_but_changes_right_density() -> None:
    matrix = build_obc_hamiltonian(square_sites(5), model_eq11()).toarray()
    forward = full_right_eigensystem(matrix)
    transposed = full_right_eigensystem(matrix.T)
    assert symmetric_cloud_distance(
        forward.eigenvalues, transposed.eigenvalues
    )["max"] < 1e-8
    forward_density = aggregate_right_density(forward.right_eigenvectors)
    transposed_density = aggregate_right_density(transposed.right_eigenvectors)
    assert not np.allclose(forward_density, transposed_density)


def test_eq15_reciprocal_boundary_ratios_are_reflection_equivalent() -> None:
    first = build_obc_hamiltonian(cut_coordinate_sites(8, 4), model_eq15())
    reflected = build_obc_hamiltonian(cut_coordinate_sites(4, 8), model_eq15())
    assert symmetric_cloud_distance(
        full_spectrum(first), full_spectrum(reflected)
    )["max"] < 1e-8


def test_gaussian_profile_recovers_curvature_and_center() -> None:
    coordinate = np.linspace(-12.0, 12.0, 97)
    expected_kappa = 0.08
    expected_center = -1.75
    probability = 0.63 * np.exp(-expected_kappa * (coordinate - expected_center) ** 2)
    fit = fit_gaussian_profile(coordinate, probability, relative_floor=1e-8)
    assert np.isclose(fit.kappa, expected_kappa, rtol=1e-12, atol=1e-12)
    assert np.isclose(fit.center, expected_center, rtol=1e-12, atol=1e-12)
    assert fit.r_squared > 1.0 - 1e-12


def test_target_state_and_edge_profile_have_small_residual() -> None:
    sites = diamond_sites(5)
    matrix = build_obc_hamiltonian(sites, model_eq15())
    state = target_right_eigenstate(matrix, 1.0 + 0.2j, candidate_count=6)
    coordinate, probability, boundary_length = rhombus_edge_profile(
        sites, state.right_eigenvector
    )
    assert state.normalized_residual < 1e-10
    assert boundary_length == 5
    assert np.all(np.diff(coordinate) > 0)
    assert probability.size == 6
    assert np.all(probability >= 0.0)


def test_linear_fit_reports_zero_compatible_intercept() -> None:
    inverse_length = np.linspace(0.01, 0.04, 12)
    kappa = 0.7 * inverse_length + 2e-5 * np.sin(np.arange(inverse_length.size))
    fit = linear_fit_with_confidence(inverse_length, kappa)
    assert fit.slope > 0.0
    assert fit.r_squared > 0.999
    assert fit.intercept_confidence_interval[0] <= 0.0 <= fit.intercept_confidence_interval[1]


def test_gbz_points_solve_the_continued_characteristic_equation() -> None:
    energy = -1.2 + 1.1j
    points = solve_gbz_for_energy(
        energy,
        model_eq11(),
        basis="square",
        momentum_samples=32,
        minimization_tolerance=5e-4,
        seed_count=4,
    )
    assert points
    for point in points:
        assert point.residual < 1e-7
        assert abs(laurent_energy(point.beta_1, point.beta_2, model_eq11()) - energy) < 1e-7
        assert point.mu_1 > 0
        assert point.mu_2 < 0
