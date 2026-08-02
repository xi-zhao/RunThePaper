from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from nonhermitian_topology import (  # noqa: E402
    DiracDomain,
    SIGMA_PLUS,
    cylinder_blocks,
    cylinder_boundary_weights,
    cylinder_hamiltonian,
    dirac_eigenvalues,
    energy_difference_vorticity,
    exceptional_eigenvalues,
    exceptional_point_hamiltonian,
    exceptional_points,
    exceptional_trajectory,
    hybrid_eigenvalues,
    hybrid_hamiltonian,
    lattice_bloch_hamiltonian,
    solve_domain_wall_edge,
    symmetric_domain_wall_energy,
    tracked_hybrid_loop,
    tracked_exceptional_loop,
    unordered_pair_error,
)


class NonHermitianTopologyTests(unittest.TestCase):
    def test_paper_sigma_plus_convention_has_no_half(self) -> None:
        np.testing.assert_allclose(SIGMA_PLUS, np.array([[0.0, 2.0], [0.0, 0.0]]))

    def test_exceptional_formula_matches_direct_diagonalization(self) -> None:
        for kx, ky in [(-0.8, -0.3), (0.2, 0.7), (1.1, -0.4), (0.0, 0.0)]:
            plus, minus = exceptional_eigenvalues(kx, ky)
            direct = np.linalg.eigvals(exceptional_point_hamiltonian(kx, ky))
            self.assertLess(unordered_pair_error([plus, minus], direct), 1e-12)

    def test_loop_swaps_branches_and_has_half_winding_magnitude(self) -> None:
        loop = tracked_exceptional_loop(np.linspace(0.0, 2.0 * np.pi, 721))
        plus = loop["e_plus"]
        self.assertLess(abs(plus[-1] + plus[0]), 1e-12)
        vorticity = energy_difference_vorticity(2.0 * plus)
        self.assertAlmostEqual(abs(vorticity), 0.5, places=12)

    def test_origin_is_nonzero_nilpotent_rank_one(self) -> None:
        matrix = exceptional_point_hamiltonian(0.0, 0.0)
        self.assertEqual(np.linalg.matrix_rank(matrix), 1)
        np.testing.assert_allclose(matrix @ matrix, np.zeros((2, 2)), atol=1e-14)

    def test_dirac_formula_matches_direct_pauli_matrix(self) -> None:
        kx, ky = 0.37, -0.61
        kappa_x, kappa_y, mass, delta = 0.2, 0.3, 1.0, 0.4
        sigma_x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        sigma_y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
        sigma_z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
        matrix = (
            (kx + 1.0j * kappa_x) * sigma_x
            + (ky + 1.0j * kappa_y) * sigma_y
            + (mass + 1.0j * delta) * sigma_z
        )
        plus, minus = dirac_eigenvalues(
            kx,
            ky,
            kappa_x=kappa_x,
            kappa_y=kappa_y,
            mass=mass,
            delta=delta,
        )
        self.assertLess(unordered_pair_error([plus, minus], np.linalg.eigvals(matrix)), 1e-12)

    def test_closed_form_exceptional_points_zero_the_dirac_radicand(self) -> None:
        points = exceptional_points(kappa_x=1.0, kappa_y=0.0, mass=0.35, delta=0.7)
        for kx, ky in points:
            plus, minus = dirac_eigenvalues(
                kx,
                ky,
                kappa_x=1.0,
                kappa_y=0.0,
                mass=0.35,
                delta=0.7,
            )
            self.assertLess(max(abs(plus), abs(minus)), 1e-7)

    def test_ep_trajectory_is_ellipse_and_merges_at_hybrid_points(self) -> None:
        masses = np.linspace(-1.0, 1.0, 101)
        points = exceptional_trajectory(
            masses, kappa_x=1.0, kappa_y=0.0, delta=1.0
        )
        ellipse = points[..., 0] ** 2 + points[..., 1] ** 2 / 2.0
        np.testing.assert_allclose(ellipse, np.ones_like(ellipse), atol=1e-13)
        np.testing.assert_allclose(points[0, 0], points[0, 1], atol=1e-13)
        np.testing.assert_allclose(points[-1, 0], points[-1, 1], atol=1e-13)

    def test_hybrid_point_has_half_and_linear_directional_exponents(self) -> None:
        scale = np.logspace(-8, -3, 120)
        along_x, _ = hybrid_eigenvalues(scale, np.zeros_like(scale))
        along_y, _ = hybrid_eigenvalues(np.zeros_like(scale), scale)
        slope_x = np.polyfit(np.log(scale), np.log(np.abs(along_x)), 1)[0]
        slope_y = np.polyfit(np.log(scale), np.log(np.abs(along_y)), 1)[0]
        self.assertAlmostEqual(slope_x, 0.5, delta=0.002)
        self.assertAlmostEqual(slope_y, 1.0, delta=1e-10)

    def test_hybrid_formula_matches_direct_diagonalization(self) -> None:
        for kx, ky in [(-0.8, -0.3), (0.2, 0.7), (0.0, 0.0), (1.1, -0.4)]:
            plus, minus = hybrid_eigenvalues(kx, ky)
            direct = np.linalg.eigvals(hybrid_hamiltonian(kx, ky))
            # A generic eigensolver is ill-conditioned at the defective origin;
            # rank and nilpotency are checked independently and exactly.
            self.assertLess(unordered_pair_error([plus, minus], direct), 5e-12)

    def test_hybrid_loop_returns_to_same_sheet_with_zero_vorticity(self) -> None:
        loop = tracked_hybrid_loop(np.linspace(0.0, 2.0 * np.pi, 721))
        plus = loop["e_plus"]
        self.assertLess(abs(plus[-1] - plus[0]), 1e-12)
        self.assertAlmostEqual(energy_difference_vorticity(2.0 * plus), 0.0, places=12)

    def test_cylinder_blocks_fourier_transform_to_supplement_equation_13(self) -> None:
        parameters = {
            "kappa_x": 0.13,
            "kappa_y": -0.07,
            "mass": -0.5,
            "delta": 0.04,
        }
        kx, ky = 0.37, -0.81
        onsite, forward, reverse = cylinder_blocks(ky, **parameters)
        reconstructed = onsite + forward * np.exp(1.0j * kx) + reverse * np.exp(-1.0j * kx)
        np.testing.assert_allclose(
            reconstructed,
            lattice_bloch_hamiltonian(kx, ky, **parameters),
            atol=1e-14,
        )

    def test_cylinder_is_hermitian_in_hermitian_limit(self) -> None:
        matrix = cylinder_hamiltonian(
            8,
            0.41,
            kappa_x=0.0,
            kappa_y=0.0,
            mass=-0.5,
            delta=0.0,
        )
        np.testing.assert_allclose(matrix, matrix.conj().T, atol=1e-14)

    def test_boundary_weights_normalize_column_eigenvectors(self) -> None:
        matrix = cylinder_hamiltonian(
            8,
            0.0,
            kappa_x=0.1,
            kappa_y=0.0,
            mass=-0.5,
            delta=0.0,
        )
        _, eigenvectors = np.linalg.eig(matrix)
        left, right = cylinder_boundary_weights(eigenvectors, sites=8, edge_sites=2)
        self.assertEqual(left.shape, (16,))
        self.assertEqual(right.shape, (16,))
        self.assertTrue(np.all(left >= 0.0))
        self.assertTrue(np.all(right >= 0.0))
        self.assertTrue(np.all(left + right <= 1.0 + 1e-12))

    def test_hermitian_domain_wall_reduces_to_chiral_edge_dispersion(self) -> None:
        left = DiracDomain(kappa_x=0.0, kappa_y=0.0, mass=-1.0, delta=0.0)
        right = DiracDomain(kappa_x=0.0, kappa_y=0.0, mass=1.0, delta=0.0)
        for ky in (-0.8, -0.2, 0.4, 0.9):
            solution = solve_domain_wall_edge(ky, left, right)
            self.assertLess(abs(solution.energy - ky), 1e-12)
            self.assertGreater(solution.inverse_length_left.real, 0.0)
            self.assertLess(solution.inverse_length_right.real, 0.0)
            self.assertLess(solution.equation_residual, 1e-12)

    def test_symmetric_domain_wall_surface_matches_full_matching_solution(self) -> None:
        for kappa_left, kappa_right in [(-0.7, -0.2), (-0.4, 0.3), (0.2, -0.5), (0.6, 0.8)]:
            left = DiracDomain(
                kappa_x=0.0,
                kappa_y=kappa_left,
                mass=-1.0,
                delta=0.0,
            )
            right = DiracDomain(
                kappa_x=0.0,
                kappa_y=kappa_right,
                mass=1.0,
                delta=0.0,
            )
            expected = symmetric_domain_wall_energy(kappa_left, kappa_right).item()
            solution = solve_domain_wall_edge(0.0, left, right)
            self.assertLess(abs(solution.energy - expected), 1e-12)

    def test_main_figure_1_domain_wall_solution_is_localized_and_exact(self) -> None:
        bulk = DiracDomain(kappa_x=0.2, kappa_y=0.3, mass=1.0, delta=0.4)
        vacuum = DiracDomain(kappa_x=0.0, kappa_y=0.0, mass=-1.0, delta=0.0)
        for ky in (-2.0, -0.5, 0.0, 1.0, 2.0):
            solution = solve_domain_wall_edge(ky, bulk, vacuum)
            self.assertGreater(solution.localization_margin, 0.8)
            self.assertLess(solution.equation_residual, 2e-12)


if __name__ == "__main__":
    unittest.main()
