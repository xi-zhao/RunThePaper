from __future__ import annotations

import unittest

import numpy as np

from src.programmable_lindbladian import (
    amplitude_damping_choi,
    channel_superoperator,
    contract_program_choi,
    diamond_norm_hp,
    diamond_norms_hp_batch,
    fig3_model,
    liouvillian,
    partial_trace_output,
    partial_trace_output_linear_map,
    program_contraction_linear_map,
    superoperator_to_choi,
)


class ProgrammingCostTests(unittest.TestCase):
    def test_identity_choi_normalization(self) -> None:
        identity_choi = superoperator_to_choi(np.eye(4), 2)
        self.assertAlmostEqual(float(np.trace(identity_choi).real), 2.0, 12)
        self.assertLess(
            np.linalg.norm(
                partial_trace_output(identity_choi, 2, 2) - np.eye(2),
                ord="fro",
            ),
            1e-13,
        )

    def test_amplitude_damping_matches_analytic_channel(self) -> None:
        jump = np.sqrt(0.1) * np.array([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
        z = np.diag([1.0, -1.0]).astype(complex)
        for with_z, hamiltonian in (
            (False, np.zeros((2, 2), dtype=complex)),
            (True, z),
        ):
            generator = liouvillian(hamiltonian, [jump])
            for time_value in (0.0, 0.13, 1.0, 4.2, 10.0):
                numeric = superoperator_to_choi(
                    channel_superoperator(generator, time_value),
                    2,
                )
                analytic = amplitude_damping_choi(
                    time_value,
                    gamma=0.1,
                    with_z_hamiltonian=with_z,
                )
                self.assertLess(np.linalg.norm(numeric - analytic, ord="fro"), 3e-12)

    def test_sparse_partial_trace_map_matches_numpy(self) -> None:
        random = np.random.default_rng(251208279)
        raw = random.normal(size=(16, 16)) + 1j * random.normal(size=(16, 16))
        linear_map = partial_trace_output_linear_map(8, 2)
        mapped = (linear_map @ raw.reshape(-1, order="C")).reshape((8, 8), order="C")
        expected = partial_trace_output(raw, 8, 2)
        self.assertLess(np.linalg.norm(mapped - expected, ord="fro"), 1e-13)

    def test_sparse_program_contraction_matches_explicit_sum(self) -> None:
        random = np.random.default_rng(137046601)
        raw = random.normal(size=(16, 16)) + 1j * random.normal(size=(16, 16))
        retrieval = 0.5 * (raw + raw.conj().T)
        program_raw = random.normal(size=(4, 4)) + 1j * random.normal(size=(4, 4))
        program = program_raw @ program_raw.conj().T
        program /= np.trace(program)
        mapped = contract_program_choi(
            retrieval,
            program,
            system_dimension=2,
            program_dimension=4,
            output_dimension=2,
        )
        tensor = retrieval.reshape((2, 4, 2, 2, 4, 2), order="C")
        expected_tensor = np.einsum("pq,ipajqb->iajb", program, tensor, optimize=True)
        expected = expected_tensor.reshape((4, 4), order="C")
        self.assertLess(np.linalg.norm(mapped - expected, ord="fro"), 1e-12)

        linear_map = program_contraction_linear_map(program, 2, 4, 2)
        sparse_value = (linear_map @ retrieval.reshape(-1, order="C")).reshape(
            (4, 4),
            order="C",
        )
        self.assertLess(np.linalg.norm(sparse_value - expected, ord="fro"), 1e-12)

    def test_diamond_norm_known_channels(self) -> None:
        identity_choi = superoperator_to_choi(np.eye(4), 2)
        identity_result = diamond_norm_hp(
            identity_choi,
            input_dimension=2,
            output_dimension=2,
            solver_epsilon=2e-7,
        )
        self.assertAlmostEqual(identity_result.value, 1.0, delta=5e-6)

        x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        x_superoperator = np.kron(x, x.conj())
        x_choi = superoperator_to_choi(x_superoperator, 2)
        difference_result = diamond_norm_hp(
            identity_choi - x_choi,
            input_dimension=2,
            output_dimension=2,
            solver_epsilon=2e-7,
        )
        self.assertAlmostEqual(difference_result.value, 2.0, delta=1e-5)
        batch = diamond_norms_hp_batch(
            [identity_choi, identity_choi - x_choi],
            input_dimension=2,
            output_dimension=2,
            solver_epsilon=2e-7,
        )
        self.assertEqual(batch.status, "optimal")
        self.assertTrue(np.allclose(batch.values, [1.0, 2.0], atol=1e-5))

    def test_fig3_programs_are_normalized_choi_states(self) -> None:
        for with_z in (False, True):
            targets, programs = fig3_model([0.0, 0.37, 10.0], with_z_hamiltonian=with_z)
            for target, program in zip(targets, programs, strict=True):
                self.assertAlmostEqual(float(np.trace(target).real), 2.0, 11)
                self.assertAlmostEqual(float(np.trace(program).real), 1.0, 11)
                self.assertGreaterEqual(float(np.min(np.linalg.eigvalsh(program))), -1e-11)
                self.assertLess(
                    np.linalg.norm(partial_trace_output(target, 2, 2) - np.eye(2)),
                    2e-11,
                )


if __name__ == "__main__":
    unittest.main()
