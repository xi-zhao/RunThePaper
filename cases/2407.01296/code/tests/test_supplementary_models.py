from __future__ import annotations

import numpy as np

from src.geometry_adaptive import (
    basis_hopping_model,
    full_right_eigensystem,
    model_eq11,
    model_eq15,
)
from src.supplementary_models import (
    double_chain_hamiltonian,
    find_fermi_points,
    fit_boundary_exponential,
    site_probability,
    winding_sweep,
)


def test_s24_matrix_matches_the_two_laurent_chains() -> None:
    matrix = double_chain_hamiltonian(4).toarray()
    assert matrix[0, 0] == 0.5
    assert matrix[1, 1] == -0.5
    assert matrix[0, 1] == matrix[1, 0] == 0.01
    assert matrix[0, 2] == 1.0
    assert matrix[2, 0] == 0.5
    assert matrix[1, 3] == 0.5
    assert matrix[3, 1] == 1.0


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
