"""Clifford frame-potential numerics for arXiv:1903.05124.

The source figures are not inputs to this module.  A Clifford is represented
by the signed images of the ``X_i`` and ``Z_i`` Pauli generators.  The trace
algorithm follows Supplement Eqs. (S4)-(S10): fixed Paulis are the binary
kernel of the symplectic action minus the identity, and a negative fixed
generator makes the signed sum vanish.
"""

from __future__ import annotations

from collections import deque
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from math import sqrt
import multiprocessing as mp
from time import perf_counter
from typing import Iterable, Sequence

import numpy as np


TWO_QUBIT_CLIFFORD_GROUP_SIZE = 11_520


def _gf2_nullspace(rows: Sequence[int], variables: int) -> list[int]:
    """Return an RREF nullspace basis for a binary matrix stored as bit rows."""

    work = [int(row) for row in rows]
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(variables):
        selected = next(
            (index for index in range(pivot_row, len(work)) if (work[index] >> column) & 1),
            None,
        )
        if selected is None:
            continue
        work[pivot_row], work[selected] = work[selected], work[pivot_row]
        for index in range(len(work)):
            if index != pivot_row and ((work[index] >> column) & 1):
                work[index] ^= work[pivot_row]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(work):
            break

    free_columns = [column for column in range(variables) if column not in pivot_columns]
    basis: list[int] = []
    for free_column in free_columns:
        vector = 1 << free_column
        for row_index, column in enumerate(pivot_columns):
            if (work[row_index] >> free_column) & 1:
                vector |= 1 << column
        basis.append(vector)
    return basis


def _pauli_product(
    left_x: np.ndarray,
    left_z: np.ndarray,
    left_phase: int,
    right_x: np.ndarray,
    right_z: np.ndarray,
    right_phase: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Multiply ``i^phase P(x,z)`` Pauli operators.

    ``P(x,z)=i^(x.z) X^x Z^z`` is Hermitian.  Intermediate products may carry
    odd powers of ``i`` even though Clifford images of Hermitian Paulis finish
    with phase 0 or 2.
    """

    output_x = np.bitwise_xor(left_x, right_x)
    output_z = np.bitwise_xor(left_z, right_z)
    correction = (
        int(np.dot(left_x, left_z))
        + int(np.dot(right_x, right_z))
        + 2 * int(np.dot(left_z, right_x))
        - int(np.dot(output_x, output_z))
    )
    return output_x, output_z, (left_phase + right_phase + correction) % 4


@dataclass
class CliffordTableau:
    """Signed conjugation action on the Hermitian Pauli generators."""

    n: int
    x: np.ndarray
    z: np.ndarray
    phase: np.ndarray

    @classmethod
    def identity(cls, n: int) -> "CliffordTableau":
        if n <= 0:
            raise ValueError("n must be positive")
        x = np.zeros((2 * n, n), dtype=np.uint8)
        z = np.zeros((2 * n, n), dtype=np.uint8)
        x[np.arange(n), np.arange(n)] = 1
        z[n + np.arange(n), np.arange(n)] = 1
        return cls(n=n, x=x, z=z, phase=np.zeros(2 * n, dtype=np.uint8))

    def copy(self) -> "CliffordTableau":
        return CliffordTableau(self.n, self.x.copy(), self.z.copy(), self.phase.copy())

    def key(self) -> bytes:
        return self.x.tobytes() + self.z.tobytes() + self.phase.tobytes()

    def apply_h(self, qubit: int) -> None:
        self._check_qubit(qubit)
        x = self.x[:, qubit].copy()
        z = self.z[:, qubit].copy()
        self.phase ^= x & z
        self.x[:, qubit] = z
        self.z[:, qubit] = x

    def apply_s(self, qubit: int) -> None:
        self._check_qubit(qubit)
        x = self.x[:, qubit].copy()
        z = self.z[:, qubit].copy()
        self.phase ^= x & z
        self.z[:, qubit] = z ^ x

    def apply_cx(self, control: int, target: int) -> None:
        self._check_qubit(control)
        self._check_qubit(target)
        if control == target:
            raise ValueError("control and target must differ")
        x_control = self.x[:, control].copy()
        x_target = self.x[:, target].copy()
        z_control = self.z[:, control].copy()
        z_target = self.z[:, target].copy()
        self.phase ^= x_control & z_target & (x_target ^ z_control ^ 1)
        self.x[:, target] = x_target ^ x_control
        self.z[:, control] = z_control ^ z_target

    def apply_local_mapping(self, first: int, second: int, mapping: np.ndarray) -> None:
        """Apply a signed two-qubit Clifford Pauli lookup to every generator."""

        self._check_qubit(first)
        self._check_qubit(second)
        if first == second:
            raise ValueError("local Clifford needs two distinct qubits")
        if mapping.shape != (16,):
            raise ValueError("mapping must contain all 16 two-qubit Paulis")
        labels = (
            self.x[:, first]
            | (self.x[:, second] << 1)
            | (self.z[:, first] << 2)
            | (self.z[:, second] << 3)
        )
        codes = mapping[labels]
        self.x[:, first] = codes & 1
        self.x[:, second] = (codes >> 1) & 1
        self.z[:, first] = (codes >> 2) & 1
        self.z[:, second] = (codes >> 3) & 1
        self.phase ^= (codes >> 4) & 1

    def transform_pauli(self, input_bits: int) -> tuple[int, int]:
        """Return output binary Pauli and phase in ``i^phase P(output)`` form."""

        variables = 2 * self.n
        if input_bits < 0 or input_bits >= (1 << variables):
            raise ValueError("input Pauli is outside this tableau")
        input_x = np.fromiter(
            ((input_bits >> index) & 1 for index in range(self.n)),
            dtype=np.uint8,
            count=self.n,
        )
        input_z = np.fromiter(
            ((input_bits >> (self.n + index)) & 1 for index in range(self.n)),
            dtype=np.uint8,
            count=self.n,
        )
        output_x = np.zeros(self.n, dtype=np.uint8)
        output_z = np.zeros(self.n, dtype=np.uint8)
        output_phase = int(np.dot(input_x, input_z)) % 4
        for row in range(variables):
            if not ((input_bits >> row) & 1):
                continue
            output_x, output_z, output_phase = _pauli_product(
                output_x,
                output_z,
                output_phase,
                self.x[row],
                self.z[row],
                2 * int(self.phase[row]),
            )
        output_bits = 0
        for qubit in range(self.n):
            output_bits |= int(output_x[qubit]) << qubit
            output_bits |= int(output_z[qubit]) << (self.n + qubit)
        return output_bits, output_phase

    def trace_square(self) -> int:
        """Compute ``|Tr U|^2`` from fixed Pauli generators exactly."""

        variables = 2 * self.n
        output_rows: list[int] = []
        for row in range(variables):
            bits = 0
            for qubit in range(self.n):
                bits |= int(self.x[row, qubit]) << qubit
                bits |= int(self.z[row, qubit]) << (self.n + qubit)
            output_rows.append(bits)

        # Fixed input coefficients v obey v(S-I)=0, equivalently
        # (S-I)^T v^T=0.  Store each transposed equation as an integer row.
        equations: list[int] = []
        for output_column in range(variables):
            equation = 0
            for input_row, output_bits in enumerate(output_rows):
                equation |= ((output_bits >> output_column) & 1) << input_row
            equation ^= 1 << output_column
            equations.append(equation)

        fixed_basis = _gf2_nullspace(equations, variables)
        for fixed_pauli in fixed_basis:
            output_bits, phase = self.transform_pauli(fixed_pauli)
            if output_bits != fixed_pauli:
                raise AssertionError("nullspace produced a non-fixed Pauli")
            if phase not in (0, 2):
                raise AssertionError("fixed Hermitian Pauli acquired a non-real phase")
            if phase == 2:
                return 0
        return 1 << len(fixed_basis)

    def _check_qubit(self, qubit: int) -> None:
        if not 0 <= qubit < self.n:
            raise IndexError(f"qubit {qubit} outside 0..{self.n - 1}")


def _apply_generator(tableau: CliffordTableau, generator: tuple[str, int, int]) -> None:
    name, first, second = generator
    if name == "h":
        tableau.apply_h(first)
    elif name == "s":
        tableau.apply_s(first)
    elif name == "cx":
        tableau.apply_cx(first, second)
    else:  # pragma: no cover - internal invariant
        raise ValueError(name)


def _local_mapping(tableau: CliffordTableau) -> np.ndarray:
    if tableau.n != 2:
        raise ValueError("local mappings are defined for two qubits")
    mapping = np.empty(16, dtype=np.uint8)
    for label in range(16):
        output, phase = tableau.transform_pauli(label)
        if phase not in (0, 2):
            raise AssertionError("Clifford maps a Hermitian Pauli to a non-Hermitian one")
        mapping[label] = output | ((phase // 2) << 4)
    return mapping


@lru_cache(maxsize=1)
def two_qubit_clifford_mappings() -> np.ndarray:
    """Enumerate the 11,520 signed two-qubit Clifford conjugation actions."""

    generators = (
        ("h", 0, -1),
        ("h", 1, -1),
        ("s", 0, -1),
        ("s", 1, -1),
        ("cx", 0, 1),
        ("cx", 1, 0),
    )
    identity = CliffordTableau.identity(2)
    queue: deque[CliffordTableau] = deque([identity])
    seen = {identity.key()}
    tableaus: list[CliffordTableau] = []
    while queue:
        current = queue.popleft()
        tableaus.append(current)
        for generator in generators:
            candidate = current.copy()
            _apply_generator(candidate, generator)
            key = candidate.key()
            if key in seen:
                continue
            seen.add(key)
            queue.append(candidate)

    if len(tableaus) != TWO_QUBIT_CLIFFORD_GROUP_SIZE:
        raise AssertionError(
            f"expected {TWO_QUBIT_CLIFFORD_GROUP_SIZE} two-qubit Cliffords, got {len(tableaus)}"
        )
    mappings = np.stack([_local_mapping(tableau) for tableau in tableaus])
    mappings.setflags(write=False)
    return mappings


def _dense_gate(name: str, first: int, second: int = -1) -> np.ndarray:
    identity = np.eye(2, dtype=np.complex128)
    hadamard = np.array([[1, 1], [1, -1]], dtype=np.complex128) / sqrt(2.0)
    phase = np.diag([1.0, 1.0j]).astype(np.complex128)
    if name == "h":
        return np.kron(hadamard, identity) if first == 0 else np.kron(identity, hadamard)
    if name == "s":
        return np.kron(phase, identity) if first == 0 else np.kron(identity, phase)
    if name == "cx" and (first, second) == (0, 1):
        return np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
            dtype=np.complex128,
        )
    if name == "cx" and (first, second) == (1, 0):
        return np.array(
            [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]],
            dtype=np.complex128,
        )
    raise ValueError((name, first, second))


def dense_trace_validation(seed: int = 190305124, circuits: int = 64, max_steps: int = 24) -> float:
    """Cross-check the binary trace algorithm against independent 4x4 matrices."""

    rng = np.random.default_rng(seed)
    generators = (
        ("h", 0, -1), ("h", 1, -1), ("s", 0, -1),
        ("s", 1, -1), ("cx", 0, 1), ("cx", 1, 0),
    )
    max_error = 0.0
    for _ in range(circuits):
        tableau = CliffordTableau.identity(2)
        unitary = np.eye(4, dtype=np.complex128)
        for _ in range(int(rng.integers(1, max_steps + 1))):
            generator = generators[int(rng.integers(len(generators)))]
            _apply_generator(tableau, generator)
            unitary = _dense_gate(*generator) @ unitary
        expected = float(abs(np.trace(unitary)) ** 2)
        actual = float(tableau.trace_square())
        max_error = max(max_error, abs(expected - actual))
    return max_error


@dataclass(frozen=True)
class FramePotentialResult:
    n: int
    depths: np.ndarray
    q_samples: np.ndarray
    records: tuple[dict[str, float | int], ...]
    runtime_seconds: float
    seed: int
    workers: int = 1
    requested_workers: int = 1


def result_from_q_samples(
    *,
    n: int,
    depths: Iterable[int],
    q_samples: np.ndarray,
    seed: int,
    runtime_seconds: float = 0.0,
    workers: int = 1,
    requested_workers: int | None = None,
) -> FramePotentialResult:
    """Rebuild derived moments from persisted exact trace samples."""

    depth_values = np.asarray(tuple(int(value) for value in depths), dtype=np.int64)
    samples = np.asarray(q_samples)
    if n < 2:
        raise ValueError("n must be at least two")
    if depth_values.ndim != 1 or depth_values.size == 0 or np.any(depth_values < 1):
        raise ValueError("depths must be a non-empty one-dimensional positive sequence")
    if samples.ndim != 2 or samples.shape[0] != depth_values.size or samples.shape[1] == 0:
        raise ValueError("q_samples must have shape (len(depths), positive sample count)")
    if not np.issubdtype(samples.dtype, np.integer) or np.any(samples < 0):
        raise ValueError("q_samples must contain non-negative exact integers")
    exact_samples = samples.astype(np.uint64, copy=False)
    return FramePotentialResult(
        n=n,
        depths=depth_values,
        q_samples=exact_samples,
        records=_records_from_samples(
            n=n,
            depth_values=depth_values,
            q_samples=exact_samples,
        ),
        runtime_seconds=float(runtime_seconds),
        seed=int(seed),
        workers=int(workers),
        requested_workers=int(requested_workers if requested_workers is not None else workers),
    )


def _records_from_samples(
    *,
    n: int,
    depth_values: np.ndarray,
    q_samples: np.ndarray,
) -> tuple[dict[str, float | int], ...]:
    samples = q_samples.shape[1]
    records: list[dict[str, float | int]] = []
    haar_values = (1, 2, 6, 24)
    for depth_index, depth in enumerate(depth_values):
        q_float = q_samples[depth_index].astype(np.float64)
        for moment in range(1, 5):
            values = np.power(q_float, moment)
            estimate = float(np.mean(values))
            standard_error = (
                float(np.std(values, ddof=1) / np.sqrt(samples)) if samples > 1 else 0.0
            )
            records.append(
                {
                    "depth": int(depth),
                    "depth_over_n": float(depth / n),
                    "moment": moment,
                    "estimate": estimate,
                    "standard_error": standard_error,
                    "haar_value": haar_values[moment - 1],
                    "samples": samples,
                }
            )
    return tuple(records)


def _sample_q_values(
    *,
    n: int,
    depth_values: np.ndarray,
    samples: int,
    seed: int,
) -> np.ndarray:
    mappings = two_qubit_clifford_mappings()
    rng = np.random.default_rng(seed)
    milestones = {2 * int(depth) - 1: index for index, depth in enumerate(depth_values)}
    q_samples = np.empty((len(depth_values), samples), dtype=np.uint64)
    max_layers = max(milestones)

    for sample_index in range(samples):
        tableau = CliffordTableau.identity(n)
        for layer_index in range(max_layers):
            offset = layer_index % 2
            for first in range(offset, n - 1, 2):
                mapping = mappings[int(rng.integers(len(mappings)))]
                tableau.apply_local_mapping(first, first + 1, mapping)
            completed_layers = layer_index + 1
            if completed_layers in milestones:
                q_samples[milestones[completed_layers], sample_index] = tableau.trace_square()
    return q_samples


def _sample_q_chunk(payload: tuple[int, tuple[int, ...], int, int]) -> np.ndarray:
    n, depths, samples, seed = payload
    return _sample_q_values(
        n=n,
        depth_values=np.asarray(depths, dtype=np.int64),
        samples=samples,
        seed=seed,
    )


def sample_frame_potentials(
    *,
    n: int,
    depths: Iterable[int],
    samples: int,
    seed: int,
) -> FramePotentialResult:
    """Sample all requested depths from independently generated circuits."""

    if n < 2:
        raise ValueError("n must be at least two")
    depth_values = np.array(sorted(set(int(value) for value in depths)), dtype=np.int64)
    if depth_values.size == 0 or np.any(depth_values < 1):
        raise ValueError("depths must contain positive integers")
    if samples <= 0:
        raise ValueError("samples must be positive")

    started = perf_counter()
    q_samples = _sample_q_values(
        n=n,
        depth_values=depth_values,
        samples=samples,
        seed=seed,
    )
    return result_from_q_samples(
        n=n,
        depths=depth_values,
        q_samples=q_samples,
        runtime_seconds=perf_counter() - started,
        seed=seed,
    )


def sample_frame_potentials_parallel(
    *,
    n: int,
    depths: Iterable[int],
    samples: int,
    seed: int,
    workers: int,
) -> FramePotentialResult:
    """Sample independent circuit trajectories across multiple processes.

    Each worker receives a deterministic child seed.  Concatenation happens in
    worker-index order, so a fixed ``(seed, workers)`` pair is reproducible.
    """

    if workers <= 1:
        return sample_frame_potentials(n=n, depths=depths, samples=samples, seed=seed)
    if n < 2:
        raise ValueError("n must be at least two")
    depth_values = np.array(sorted(set(int(value) for value in depths)), dtype=np.int64)
    if depth_values.size == 0 or np.any(depth_values < 1):
        raise ValueError("depths must contain positive integers")
    if samples <= 0:
        raise ValueError("samples must be positive")

    worker_count = min(int(workers), samples)
    quotient, remainder = divmod(samples, worker_count)
    chunk_sizes = [quotient + (index < remainder) for index in range(worker_count)]
    child_sequences = np.random.SeedSequence(seed).spawn(worker_count)
    child_seeds = [
        int(sequence.generate_state(1, dtype=np.uint64)[0]) for sequence in child_sequences
    ]
    payloads = [
        (n, tuple(int(value) for value in depth_values), chunk_size, child_seed)
        for chunk_size, child_seed in zip(chunk_sizes, child_seeds, strict=True)
    ]

    # Fork shares the immutable 11,520-element Clifford lookup through copy-on-write
    # on POSIX.  Spawn remains a safe fallback on platforms without fork.
    two_qubit_clifford_mappings()
    start_method = "fork" if "fork" in mp.get_all_start_methods() else "spawn"
    started = perf_counter()
    actual_workers = worker_count
    try:
        with ProcessPoolExecutor(
            max_workers=worker_count,
            mp_context=mp.get_context(start_method),
        ) as executor:
            chunks = list(executor.map(_sample_q_chunk, payloads))
    except PermissionError:
        # Some constrained runners deny semaphore/sysconf access required by
        # ProcessPoolExecutor.  Preserve correctness and provenance by falling
        # back to serial chunk execution and reporting one actual worker.
        chunks = [_sample_q_chunk(payload) for payload in payloads]
        actual_workers = 1
    q_samples = np.concatenate(chunks, axis=1)
    return result_from_q_samples(
        n=n,
        depths=depth_values,
        q_samples=q_samples,
        runtime_seconds=perf_counter() - started,
        seed=seed,
        workers=actual_workers,
        requested_workers=worker_count,
    )


def records_by_moment(result: FramePotentialResult, moment: int) -> list[dict[str, float | int]]:
    return [record for record in result.records if int(record["moment"]) == moment]
