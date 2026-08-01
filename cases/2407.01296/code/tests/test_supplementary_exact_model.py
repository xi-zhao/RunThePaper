from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from src.geometry_adaptive import (
    build_obc_hamiltonian,
    full_spectrum,
    ronkin_potential,
    sparse_spectral_potential,
    square_sites,
)
from src.supplementary_exact_model import (
    amoeba_potential_grid,
    bloch_s17,
    classify_amoeba_holes,
    exact_tdl_potential,
    hx,
    hy,
    jensen_ronkin_potential,
    model_s17,
    separable_square_spectrum,
    x_root_potential,
)


def test_s17_laurent_expansion_matches_printed_trigonometric_equation() -> None:
    momentum_x = np.linspace(-2.7, 2.5, 17)
    momentum_y = np.linspace(-2.2, 2.8, 17)
    beta_x = np.exp(1j * momentum_x)
    beta_y = np.exp(1j * momentum_y)

    assert np.allclose(
        bloch_s17(momentum_x, momentum_y),
        hx(beta_x) + hy(beta_y),
        rtol=1e-13,
        atol=1e-13,
    )


def test_separable_spectrum_matches_full_small_square_diagonalization() -> None:
    length = 7
    separable = separable_square_spectrum(length).eigenvalues
    direct = full_spectrum(
        build_obc_hamiltonian(square_sites(length), model_s17())
    )
    rows, columns = linear_sum_assignment(np.abs(separable[:, None] - direct[None, :]))

    assert len(rows) == length**2
    assert float(np.max(np.abs(separable[rows] - direct[columns]))) < 1e-9


def test_y_chain_obc_spectrum_matches_the_analytic_gbz_interval() -> None:
    length = 19
    y_values = separable_square_spectrum(length).y_eigenvalues
    indices = np.arange(1, length + 1, dtype=np.float64)
    analytic = np.sqrt(6.0) * np.cos(indices * np.pi / (length + 1))
    assert np.allclose(
        np.sort(y_values.real),
        np.sort(analytic),
        rtol=1e-11,
        atol=1e-11,
    )
    assert float(np.max(np.abs(y_values.imag))) < 1e-12


def test_s20_root_potential_matches_a_large_finite_chain_log_determinant() -> None:
    energy = 3.7 + 0.41j
    length = 180
    sites = square_sites(length, 1)
    x_hoppings = {
        (1, 0): 1.0,
        (-1, 0): 1.5,
        (2, 0): 0.5,
        (-2, 0): 2.0,
    }
    matrix = build_obc_hamiltonian(sites, x_hoppings)
    finite_chain_potential = sparse_spectral_potential(matrix, energy)

    assert abs(float(x_root_potential(energy)) - finite_chain_potential) < 0.03


def test_jensen_reduction_matches_direct_two_dimensional_ronkin_sum() -> None:
    energy = 2.2 + 0.03j
    deformation_x = 0.31
    deformation_y = -0.27
    direct = ronkin_potential(
        energy,
        model_s17(),
        deformation_x=deformation_x,
        deformation_y=deformation_y,
        momentum_samples=384,
    )
    reduced = jensen_ronkin_potential(
        energy,
        deformation_x=deformation_x,
        deformation_y=deformation_y,
        momentum_samples=384,
    )

    assert abs(reduced - direct) < 0.015


def test_amoeba_potential_obeys_the_paper_inequality_s16() -> None:
    energies = np.asarray((2.2 + 0.03j, 6.0 - 0.3j, -3.0 + 0.2j))
    exact = exact_tdl_potential(energies, quadrature_samples=192)
    amoeba = amoeba_potential_grid(
        energies,
        momentum_samples=192,
        coarse_samples=49,
        refinement_steps=22,
    )

    assert amoeba.boundary_hits == 0
    assert np.all(amoeba.potential + 5e-4 >= exact)


def test_s2d_distinguishes_the_noncentral_and_central_holes() -> None:
    first = classify_amoeba_holes(2.2 + 0.03j)
    second = classify_amoeba_holes(6.0 - 0.3j)

    assert len(first.holes) == 1
    assert not first.holes[0].is_central
    assert (first.holes[0].order.winding_x, first.holes[0].order.winding_y) == (
        1,
        0,
    )
    assert any(hole.is_central for hole in second.holes)
