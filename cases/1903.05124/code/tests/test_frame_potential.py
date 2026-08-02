from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from frame_potential import (  # noqa: E402
    CliffordTableau,
    TWO_QUBIT_CLIFFORD_GROUP_SIZE,
    dense_trace_validation,
    result_from_q_samples,
    sample_frame_potentials,
    sample_frame_potentials_parallel,
    two_qubit_clifford_mappings,
)


class FramePotentialTests(unittest.TestCase):
    def test_known_clifford_trace_squares(self) -> None:
        identity = CliffordTableau.identity(1)
        self.assertEqual(identity.trace_square(), 4)

        hadamard = CliffordTableau.identity(1)
        hadamard.apply_h(0)
        self.assertEqual(hadamard.trace_square(), 0)

        phase = CliffordTableau.identity(1)
        phase.apply_s(0)
        self.assertEqual(phase.trace_square(), 2)

        cnot = CliffordTableau.identity(2)
        cnot.apply_cx(0, 1)
        self.assertEqual(cnot.trace_square(), 4)

    def test_dense_random_circuits_match_binary_trace(self) -> None:
        self.assertLess(dense_trace_validation(circuits=96, max_steps=30), 1e-10)

    def test_uniform_two_qubit_group_is_complete_and_unique(self) -> None:
        mappings = two_qubit_clifford_mappings()
        self.assertEqual(mappings.shape, (TWO_QUBIT_CLIFFORD_GROUP_SIZE, 16))
        self.assertEqual(len({row.tobytes() for row in mappings}), TWO_QUBIT_CLIFFORD_GROUP_SIZE)

    def test_local_lookup_matches_enumerated_primitive_identity(self) -> None:
        mappings = two_qubit_clifford_mappings()
        np.testing.assert_array_equal(mappings[0], np.arange(16, dtype=np.uint8))

    def test_sampling_is_seed_deterministic_and_moments_are_well_formed(self) -> None:
        first = sample_frame_potentials(n=4, depths=[2, 4], samples=12, seed=7)
        second = sample_frame_potentials(n=4, depths=[2, 4], samples=12, seed=7)
        np.testing.assert_array_equal(first.q_samples, second.q_samples)
        self.assertEqual(len(first.records), 8)
        values = first.q_samples.ravel()
        self.assertTrue(
            all(value == 0 or (int(value) & (int(value) - 1)) == 0 for value in values)
        )

    def test_parallel_sampling_is_deterministic_and_complete(self) -> None:
        first = sample_frame_potentials_parallel(
            n=4, depths=[2, 4], samples=17, seed=11, workers=2
        )
        second = sample_frame_potentials_parallel(
            n=4, depths=[2, 4], samples=17, seed=11, workers=2
        )
        np.testing.assert_array_equal(first.q_samples, second.q_samples)
        self.assertEqual(first.q_samples.shape, (2, 17))
        self.assertIn(first.workers, (1, 2))
        self.assertEqual(first.requested_workers, 2)
        self.assertEqual({int(row["samples"]) for row in first.records}, {17})

    def test_persisted_samples_rebuild_without_changing_values(self) -> None:
        q_samples = np.array([[0, 1, 2], [1, 2, 4]], dtype=np.uint64)
        result = result_from_q_samples(
            n=4,
            depths=[2, 4],
            q_samples=q_samples,
            seed=13,
            runtime_seconds=2.5,
            workers=2,
        )
        np.testing.assert_array_equal(result.q_samples, q_samples)
        self.assertEqual(result.records[0]["estimate"], 1.0)
        self.assertEqual(result.runtime_seconds, 2.5)
        self.assertEqual(result.workers, 2)


if __name__ == "__main__":
    unittest.main()
