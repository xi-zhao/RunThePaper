from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from stabilizer_dynamics import (  # noqa: E402
    DynamicsConfig,
    StabilizerState,
    block_pairs,
    gf2_rank,
    run_observable_ensemble,
    run_trajectory_ensemble,
    simulate_observable_trajectory,
    simulate_trajectory,
    observable_worker_pool,
    tripartite_mutual_information,
    two_qubit_clifford_basis_mappings,
)


H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
S = np.diag([1.0, 1.0j]).astype(np.complex128)


def apply_one_qubit(vector: np.ndarray, gate: np.ndarray, qubit: int) -> np.ndarray:
    output = np.zeros_like(vector)
    for index, amplitude in enumerate(vector):
        bit = (index >> qubit) & 1
        base = index & ~(1 << qubit)
        output[base] += gate[0, bit] * amplitude
        output[base | (1 << qubit)] += gate[1, bit] * amplitude
    return output


def apply_cx(vector: np.ndarray, control: int, target: int) -> np.ndarray:
    output = np.zeros_like(vector)
    for index, amplitude in enumerate(vector):
        destination = index ^ (1 << target) if ((index >> control) & 1) else index
        output[destination] += amplitude
    return output


def measure_z_zero_if_possible(vector: np.ndarray, qubit: int) -> np.ndarray:
    probabilities = [
        float(sum(abs(vector[index]) ** 2 for index in range(len(vector)) if ((index >> qubit) & 1) == outcome))
        for outcome in (0, 1)
    ]
    outcome = 0 if probabilities[0] > 1e-12 else 1
    output = vector.copy()
    for index in range(len(output)):
        if ((index >> qubit) & 1) != outcome:
            output[index] = 0
    return output / np.linalg.norm(output)


def dense_entropy(vector: np.ndarray, n: int, qubits: tuple[int, ...]) -> float:
    selected = tuple(sorted(qubits))
    outside = tuple(qubit for qubit in range(n) if qubit not in selected)
    matrix = np.zeros((1 << len(selected), 1 << len(outside)), dtype=np.complex128)
    for index, amplitude in enumerate(vector):
        left = sum(((index >> qubit) & 1) << position for position, qubit in enumerate(selected))
        right = sum(((index >> qubit) & 1) << position for position, qubit in enumerate(outside))
        matrix[left, right] = amplitude
    probabilities = np.linalg.svd(matrix, compute_uv=False) ** 2
    probabilities = probabilities[probabilities > 1e-12]
    return float(-np.sum(probabilities * np.log2(probabilities)))


class StabilizerDynamicsTests(unittest.TestCase):
    def test_gf2_rank(self) -> None:
        self.assertEqual(gf2_rank([0b001, 0b010, 0b011, 0b100]), 3)
        self.assertEqual(gf2_rank([]), 0)

    def test_product_bell_and_measurement_entropies(self) -> None:
        state = StabilizerState.zero_product(2)
        self.assertEqual(state.entropy([0]), 0)
        state.apply_h(0)
        state.apply_cx(0, 1)
        state.assert_binary_invariants()
        self.assertEqual(state.entropy([0]), 1)
        self.assertTrue(state.measure_z(0))
        state.assert_binary_invariants()
        self.assertEqual(state.entropy([0]), 0)
        self.assertFalse(state.measure_z(0))

    def test_random_primitive_circuit_matches_dense_entropies(self) -> None:
        n = 5
        rng = np.random.default_rng(190305124)
        state = StabilizerState.zero_product(n)
        vector = np.zeros(1 << n, dtype=np.complex128)
        vector[0] = 1.0
        for _ in range(80):
            operation = int(rng.integers(4))
            first = int(rng.integers(n))
            if operation == 0:
                state.apply_h(first)
                vector = apply_one_qubit(vector, H, first)
            elif operation == 1:
                state.apply_s(first)
                vector = apply_one_qubit(vector, S, first)
            elif operation == 2:
                second = int(rng.integers(n - 1))
                if second >= first:
                    second += 1
                state.apply_cx(first, second)
                vector = apply_cx(vector, first, second)
            else:
                state.measure_z(first)
                vector = measure_z_zero_if_possible(vector, first)
            state.assert_binary_invariants()
            for subset in ((0,), (1, 3), (0, 1, 2)):
                self.assertAlmostEqual(state.entropy(subset), dense_entropy(vector, n, subset), places=9)

    def test_uniform_local_cliffords_preserve_binary_invariants(self) -> None:
        rng = np.random.default_rng(17)
        mappings = two_qubit_clifford_basis_mappings()
        state = StabilizerState.zero_product(8)
        for _ in range(100):
            first = int(rng.integers(7))
            mapping = mappings[int(rng.integers(len(mappings)))]
            state.apply_local_clifford(first, first + 1, mapping)
        state.assert_binary_invariants()

    def test_block_pair_schedule_keeps_half_cut_between_pairs_on_odd_steps(self) -> None:
        self.assertNotIn((3, 4), block_pairs(8, 1, "open"))
        self.assertIn((3, 4), block_pairs(8, 2, "open"))
        self.assertNotIn((7, 0), block_pairs(8, 1, "periodic"))
        self.assertIn((7, 0), block_pairs(8, 2, "periodic"))

    def test_ensemble_is_worker_count_deterministic(self) -> None:
        config = DynamicsConfig(
            blocks=4,
            qubits_per_block=2,
            circuit_depth=3,
            measurement_fraction=0.25,
            steps=5,
        )
        serial = run_trajectory_ensemble(config, realizations=5, seed=23, workers=1)
        parallel = run_trajectory_ensemble(config, realizations=5, seed=23, workers=2)
        np.testing.assert_array_equal(
            serial.entropy_after_measurement,
            parallel.entropy_after_measurement,
        )
        np.testing.assert_array_equal(
            serial.measurement_entropy_change,
            parallel.measurement_entropy_change,
        )

    def test_observable_samples_match_full_trajectory(self) -> None:
        config = DynamicsConfig(
            blocks=4,
            qubits_per_block=2,
            circuit_depth=3,
            measurement_fraction=0.25,
            steps=7,
        )
        full = simulate_trajectory(config, seed=37)
        sampled = simulate_observable_trajectory(
            config,
            seed=37,
            sample_steps=(3, 5, 7),
        )
        np.testing.assert_array_equal(
            sampled.half_chain_entropy,
            full.entropy_after_measurement[[3, 5, 7]],
        )

    def test_shared_observables_are_parallel_deterministic(self) -> None:
        config = DynamicsConfig(
            blocks=4,
            qubits_per_block=2,
            circuit_depth=2,
            measurement_fraction=0.5,
            steps=5,
            boundary="periodic",
        )
        serial = run_observable_ensemble(
            config,
            realizations=5,
            seed=41,
            sample_steps=(3, 5),
            workers=1,
            include_tripartite_information=True,
        )
        parallel = run_observable_ensemble(
            config,
            realizations=5,
            seed=41,
            sample_steps=(3, 5),
            workers=2,
            include_tripartite_information=True,
        )
        np.testing.assert_array_equal(
            serial.half_chain_entropy,
            parallel.half_chain_entropy,
        )
        np.testing.assert_array_equal(
            serial.tripartite_mutual_information,
            parallel.tripartite_mutual_information,
        )

    def test_observable_pool_can_be_reused_across_settings(self) -> None:
        config = DynamicsConfig(
            blocks=4,
            qubits_per_block=2,
            circuit_depth=2,
            measurement_fraction=0.25,
            steps=3,
        )
        with observable_worker_pool(2) as executor:
            first = run_observable_ensemble(
                config,
                realizations=4,
                seed=51,
                sample_steps=(3,),
                workers=2,
                executor=executor,
                create_executor=False,
            )
            second = run_observable_ensemble(
                config,
                realizations=4,
                seed=51,
                sample_steps=(3,),
                workers=2,
                executor=executor,
                create_executor=False,
            )
        np.testing.assert_array_equal(
            first.half_chain_entropy,
            second.half_chain_entropy,
        )

    def test_tripartite_information_known_states(self) -> None:
        product = StabilizerState.zero_product(4)
        self.assertEqual(tripartite_mutual_information(product, 4, 1), 0)

        ghz = StabilizerState.zero_product(4)
        ghz.apply_h(0)
        for target in (1, 2, 3):
            ghz.apply_cx(0, target)
        self.assertEqual(tripartite_mutual_information(ghz, 4, 1), 1)


if __name__ == "__main__":
    unittest.main()
