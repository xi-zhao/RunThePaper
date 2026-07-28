from __future__ import annotations

import unittest

import numpy as np
from scipy.linalg import expm

from src.programmable_lindbladian import (
    apply_choi,
    apply_superoperator,
    bell_dephase,
    channel_superoperator,
    computational_basis,
    contract_program_choi,
    map_to_choi,
    partial_trace_output,
    swap_dephasing_channel,
    swap_dephasing_liouvillian,
    swap_operator,
    swap_overlap_exact,
    swap_program_processor,
    swap_program_processor_choi,
    swap_program_state,
    superoperator_to_choi,
)


class SwapDephasingTests(unittest.TestCase):
    def test_factorized_channel_matches_full_liouvillian(self) -> None:
        random = np.random.default_rng(20260728)
        raw = random.normal(size=(4, 4)) + 1j * random.normal(size=(4, 4))
        state = raw @ raw.conj().T
        state /= np.trace(state)
        generator = swap_dephasing_liouvillian(0.5)
        for time_value in (0.0, 0.17, 1.3, 5.0, 10.0):
            direct = apply_superoperator(
                channel_superoperator(generator, time_value),
                state,
            )
            analytic = swap_dephasing_channel(state, time_value, 0.5)
            self.assertLess(np.linalg.norm(direct - analytic, ord="fro"), 2e-12)

    def test_overlap_formula_matches_both_channel_forms(self) -> None:
        state_vector = computational_basis(4, 1)
        state = np.outer(state_vector, state_vector.conj())
        generator = swap_dephasing_liouvillian(0.5)
        for time_value in np.linspace(0.0, 10.0, 21):
            direct_state = apply_superoperator(
                channel_superoperator(generator, float(time_value)),
                state,
            )
            factorized_state = swap_dephasing_channel(
                state,
                float(time_value),
                0.5,
            )
            expected = swap_overlap_exact(float(time_value), 0.5)
            self.assertAlmostEqual(float(np.trace(state @ direct_state).real), expected, 12)
            self.assertAlmostEqual(
                float(np.trace(state @ factorized_state).real),
                expected,
                12,
            )

    def test_minimal_processor_is_hptp(self) -> None:
        processor_choi = swap_program_processor_choi()
        self.assertLess(
            np.linalg.norm(
                partial_trace_output(processor_choi, 8, 4) - np.eye(8),
                ord="fro",
            ),
            2e-12,
        )
        self.assertLess(
            np.linalg.norm(processor_choi - processor_choi.conj().T, ord="fro"),
            2e-12,
        )

    def test_minimal_processor_programs_swap_unitary(self) -> None:
        random = np.random.default_rng(137040403)
        raw = random.normal(size=(4, 4)) + 1j * random.normal(size=(4, 4))
        state = raw @ raw.conj().T
        state /= np.trace(state)
        processor_choi = swap_program_processor_choi()
        for time_value in (0.0, 0.31, 1.2, 4.7):
            program = swap_program_state(time_value)
            direct = swap_program_processor(np.kron(state, program))
            unitary = expm(1j * time_value * swap_operator())
            expected = unitary @ state @ unitary.conj().T
            self.assertLess(np.linalg.norm(direct - expected, ord="fro"), 2e-12)

            effective_choi = contract_program_choi(
                processor_choi,
                program,
                system_dimension=4,
                program_dimension=2,
                output_dimension=4,
            )

            def unitary_map(operator):
                return unitary @ operator @ unitary.conj().T

            expected_choi = map_to_choi(unitary_map, 4, 4)
            self.assertLess(
                np.linalg.norm(effective_choi - expected_choi, ord="fro"),
                3e-12,
            )

    def test_bell_dephasing_is_idempotent(self) -> None:
        random = np.random.default_rng(40403)
        raw = random.normal(size=(4, 4)) + 1j * random.normal(size=(4, 4))
        self.assertLess(
            np.linalg.norm(
                bell_dephase(bell_dephase(raw)) - bell_dephase(raw),
                ord="fro",
            ),
            2e-12,
        )


if __name__ == "__main__":
    unittest.main()
