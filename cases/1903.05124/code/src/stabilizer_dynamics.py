"""Binary stabilizer dynamics for the monitored Clifford block chain.

This module implements the scientific state transition behind Main Fig. 2 and
Supplement Figs. S3--S6 of arXiv:1903.05124.  Stabilizer signs are deliberately
omitted: Clifford conjugation, measurement (anti)commutation, and subsystem
entropy depend only on the binary symplectic generators.  Source figures are
not inputs.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
import multiprocessing as mp
from time import perf_counter
from typing import Iterable, Iterator, Sequence

import numpy as np

from frame_potential import two_qubit_clifford_mappings


def gf2_rank(vectors: Iterable[int]) -> int:
    """Rank of binary column vectors represented by Python integers."""

    pivots: dict[int, int] = {}
    for raw_vector in vectors:
        vector = int(raw_vector)
        if vector < 0:
            raise ValueError("GF(2) vectors must be non-negative")
        while vector:
            pivot = vector.bit_length() - 1
            if pivot in pivots:
                vector ^= pivots[pivot]
            else:
                pivots[pivot] = vector
                break
    return len(pivots)


@lru_cache(maxsize=1)
def two_qubit_clifford_basis_mappings() -> np.ndarray:
    """Return the unsigned symplectic images of X0, X1, Z0, and Z1."""

    mappings = two_qubit_clifford_mappings()
    basis = np.asarray(mappings[:, (1, 2, 4, 8)] & 0x0F, dtype=np.uint8)
    basis.setflags(write=False)
    return basis


class StabilizerState:
    """Pure stabilizer state stored as Pauli columns over generator rows.

    ``x_columns[q]`` is an integer bit mask: bit ``r`` is one when generator
    ``r`` has X support on qubit ``q``.  Column storage makes both local
    Clifford updates and projective-measurement row operations inexpensive.
    """

    def __init__(self, n: int, x_columns: Sequence[int], z_columns: Sequence[int]) -> None:
        if n <= 0:
            raise ValueError("n must be positive")
        if len(x_columns) != n or len(z_columns) != n:
            raise ValueError("x_columns and z_columns must each have length n")
        row_mask = (1 << n) - 1
        self.n = int(n)
        self.x_columns = [int(value) & row_mask for value in x_columns]
        self.z_columns = [int(value) & row_mask for value in z_columns]

    @classmethod
    def zero_product(cls, n: int) -> "StabilizerState":
        """Construct ``|0>^n`` with generators ``Z_0,...,Z_(n-1)``."""

        return cls(n, [0] * n, [1 << row for row in range(n)])

    def copy(self) -> "StabilizerState":
        return StabilizerState(self.n, self.x_columns, self.z_columns)

    def apply_h(self, qubit: int) -> None:
        self._check_qubit(qubit)
        self.x_columns[qubit], self.z_columns[qubit] = (
            self.z_columns[qubit],
            self.x_columns[qubit],
        )

    def apply_s(self, qubit: int) -> None:
        self._check_qubit(qubit)
        self.z_columns[qubit] ^= self.x_columns[qubit]

    def apply_cx(self, control: int, target: int) -> None:
        self._check_qubit(control)
        self._check_qubit(target)
        if control == target:
            raise ValueError("control and target must differ")
        self.x_columns[target] ^= self.x_columns[control]
        self.z_columns[control] ^= self.z_columns[target]

    def apply_local_clifford(
        self,
        first: int,
        second: int,
        basis_mapping: Sequence[int],
    ) -> None:
        """Apply one unsigned two-qubit Clifford symplectic map."""

        self._check_qubit(first)
        self._check_qubit(second)
        if first == second:
            raise ValueError("a two-qubit Clifford needs distinct qubits")
        if len(basis_mapping) != 4:
            raise ValueError("basis_mapping must contain X0, X1, Z0, Z1 images")
        inputs = (
            self.x_columns[first],
            self.x_columns[second],
            self.z_columns[first],
            self.z_columns[second],
        )
        outputs = [0, 0, 0, 0]
        for input_index, raw_image in enumerate(basis_mapping):
            image = int(raw_image)
            if image < 0 or image >= 16:
                raise ValueError("basis images must be unsigned two-qubit Pauli labels")
            input_column = inputs[input_index]
            for output_index in range(4):
                if (image >> output_index) & 1:
                    outputs[output_index] ^= input_column
        (
            self.x_columns[first],
            self.x_columns[second],
            self.z_columns[first],
            self.z_columns[second],
        ) = outputs

    def measure_z(self, qubit: int) -> bool:
        """Projectively measure Z and return whether the outcome was random.

        Outcome signs are irrelevant to every entropy observable in this case.
        If Z anticommutes with a stabilizer generator, the other anticommuting
        rows are multiplied by a pivot row and that pivot is replaced by Z.
        """

        self._check_qubit(qubit)
        anticommuting = self.x_columns[qubit]
        if anticommuting == 0:
            return False
        pivot = anticommuting & -anticommuting
        rows_to_update = anticommuting ^ pivot
        clear_pivot = ~pivot
        for column_index in range(self.n):
            x_column = self.x_columns[column_index]
            z_column = self.z_columns[column_index]
            if x_column & pivot:
                x_column ^= rows_to_update
            if z_column & pivot:
                z_column ^= rows_to_update
            self.x_columns[column_index] = x_column & clear_pivot
            self.z_columns[column_index] = z_column & clear_pivot
        self.z_columns[qubit] |= pivot
        return True

    def entropy(self, qubits: Iterable[int]) -> int:
        """Exact stabilizer entropy (bits) of an arbitrary subsystem."""

        subsystem = frozenset(int(qubit) for qubit in qubits)
        if any(qubit < 0 or qubit >= self.n for qubit in subsystem):
            raise IndexError("subsystem contains a qubit outside the state")
        outside = [qubit for qubit in range(self.n) if qubit not in subsystem]
        restricted_columns = [
            column
            for qubit in outside
            for column in (self.x_columns[qubit], self.z_columns[qubit])
        ]
        entropy = gf2_rank(restricted_columns) - len(outside)
        maximum = min(len(subsystem), len(outside))
        if entropy < 0 or entropy > maximum:
            raise AssertionError(
                f"invalid pure-state stabilizer entropy {entropy}, expected 0..{maximum}"
            )
        return entropy

    def generator_rows(self) -> tuple[tuple[int, int], ...]:
        """Return unsigned (X,Z) row bit sets for independent checks."""

        rows: list[tuple[int, int]] = []
        for row in range(self.n):
            x_bits = 0
            z_bits = 0
            for qubit in range(self.n):
                x_bits |= ((self.x_columns[qubit] >> row) & 1) << qubit
                z_bits |= ((self.z_columns[qubit] >> row) & 1) << qubit
            rows.append((x_bits, z_bits))
        return tuple(rows)

    def assert_binary_invariants(self) -> None:
        rows = self.generator_rows()
        combined = [x_bits | (z_bits << self.n) for x_bits, z_bits in rows]
        if gf2_rank(combined) != self.n:
            raise AssertionError("stabilizer generators lost independence")
        for first in range(self.n):
            x_first, z_first = rows[first]
            for second in range(first + 1, self.n):
                x_second, z_second = rows[second]
                parity = ((x_first & z_second).bit_count() + (z_first & x_second).bit_count()) & 1
                if parity:
                    raise AssertionError("stabilizer generators do not commute")

    def _check_qubit(self, qubit: int) -> None:
        if not 0 <= qubit < self.n:
            raise IndexError(f"qubit {qubit} outside 0..{self.n - 1}")


@dataclass(frozen=True)
class DynamicsConfig:
    blocks: int
    qubits_per_block: int
    circuit_depth: int
    measurement_fraction: float
    steps: int
    boundary: str = "open"

    def __post_init__(self) -> None:
        if self.blocks <= 1 or self.blocks % 2:
            raise ValueError("blocks must be an even integer greater than one")
        if self.qubits_per_block <= 0:
            raise ValueError("qubits_per_block must be positive")
        if self.circuit_depth <= 0:
            raise ValueError("circuit_depth must be positive")
        if not 0.0 <= self.measurement_fraction <= 1.0:
            raise ValueError("measurement_fraction must be between zero and one")
        if self.steps <= 0:
            raise ValueError("steps must be positive")
        if self.boundary not in {"open", "periodic"}:
            raise ValueError("boundary must be open or periodic")

    @property
    def qubits(self) -> int:
        return self.blocks * self.qubits_per_block


@dataclass(frozen=True)
class TrajectoryResult:
    entropy_after_measurement: np.ndarray
    entropy_before_measurement: np.ndarray
    measurement_entropy_change: np.ndarray
    random_measurements: np.ndarray


@dataclass(frozen=True)
class EnsembleResult:
    config: DynamicsConfig
    entropy_after_measurement: np.ndarray
    entropy_before_measurement: np.ndarray
    measurement_entropy_change: np.ndarray
    random_measurements: np.ndarray
    seed: int
    runtime_seconds: float
    workers: int
    requested_workers: int


@dataclass(frozen=True)
class ObservableTrajectoryResult:
    sample_steps: np.ndarray
    half_chain_entropy: np.ndarray
    tripartite_mutual_information: np.ndarray | None


@dataclass(frozen=True)
class ObservableEnsembleResult:
    config: DynamicsConfig
    sample_steps: np.ndarray
    half_chain_entropy: np.ndarray
    tripartite_mutual_information: np.ndarray | None
    seed: int
    runtime_seconds: float
    workers: int
    requested_workers: int


def block_pairs(blocks: int, step: int, boundary: str) -> tuple[tuple[int, int], ...]:
    """Brick-wall pairs with odd physical steps not crossing the half-chain cut.

    The paper evaluates measurement protection on odd steps.  For even ``L``,
    those layers must pair ``(0,1),(2,3),...`` so the half-chain cut lies
    between pairs; the alternate layer creates local entanglement directly
    across that cut and is intentionally excluded from that analysis.
    """

    if step <= 0:
        raise ValueError("step is one-indexed and must be positive")
    offset = (step - 1) % 2
    pairs = [(left, left + 1) for left in range(offset, blocks - 1, 2)]
    if boundary == "periodic" and offset == 1:
        pairs.append((blocks - 1, 0))
    return tuple(pairs)


def apply_block_pair_unitary(
    state: StabilizerState,
    *,
    left_block: int,
    right_block: int,
    qubits_per_block: int,
    circuit_depth: int,
    rng: np.random.Generator,
) -> None:
    """Apply the paper's depth-d brick-wall circuit on two adjacent blocks."""

    local_qubits = tuple(
        list(range(left_block * qubits_per_block, (left_block + 1) * qubits_per_block))
        + list(range(right_block * qubits_per_block, (right_block + 1) * qubits_per_block))
    )
    basis_mappings = two_qubit_clifford_basis_mappings()
    for layer in range(circuit_depth):
        for local_first in range(layer % 2, 2 * qubits_per_block - 1, 2):
            mapping = basis_mappings[int(rng.integers(len(basis_mappings)))]
            state.apply_local_clifford(
                local_qubits[local_first],
                local_qubits[local_first + 1],
                mapping,
            )


def apply_unitary_step(
    state: StabilizerState,
    config: DynamicsConfig,
    step: int,
    rng: np.random.Generator,
) -> None:
    for left_block, right_block in block_pairs(config.blocks, step, config.boundary):
        apply_block_pair_unitary(
            state,
            left_block=left_block,
            right_block=right_block,
            qubits_per_block=config.qubits_per_block,
            circuit_depth=config.circuit_depth,
            rng=rng,
        )


def apply_measurement_step(
    state: StabilizerState,
    config: DynamicsConfig,
    rng: np.random.Generator,
) -> int:
    """Measure floor/ceil(pm) distinct qubits per block with mean pm."""

    expected = config.measurement_fraction * config.qubits_per_block
    lower = int(np.floor(expected))
    fractional = expected - lower
    random_measurements = 0
    for block in range(config.blocks):
        count = lower + int(rng.random() < fractional)
        if count == 0:
            continue
        local_positions = rng.choice(config.qubits_per_block, size=count, replace=False)
        for local_position in local_positions:
            qubit = block * config.qubits_per_block + int(local_position)
            random_measurements += int(state.measure_z(qubit))
    return random_measurements


def simulate_trajectory(
    config: DynamicsConfig,
    *,
    seed: int,
    subsystem: Iterable[int] | None = None,
) -> TrajectoryResult:
    rng = np.random.default_rng(seed)
    state = StabilizerState.zero_product(config.qubits)
    selected = tuple(range(config.qubits // 2)) if subsystem is None else tuple(subsystem)
    after = np.empty(config.steps + 1, dtype=np.int32)
    before = np.empty(config.steps, dtype=np.int32)
    changes = np.empty(config.steps, dtype=np.int32)
    random_counts = np.empty(config.steps, dtype=np.int32)
    after[0] = state.entropy(selected)
    for index in range(config.steps):
        step = index + 1
        apply_unitary_step(state, config, step, rng)
        before[index] = state.entropy(selected)
        random_counts[index] = apply_measurement_step(state, config, rng)
        after[index + 1] = state.entropy(selected)
        changes[index] = after[index + 1] - before[index]
    return TrajectoryResult(after, before, changes, random_counts)


def simulate_observable_trajectory(
    config: DynamicsConfig,
    *,
    seed: int,
    sample_steps: Iterable[int],
    include_tripartite_information: bool = False,
) -> ObservableTrajectoryResult:
    """Evolve once and sample steady-state observables at selected steps.

    This is the shared numerical primitive for the phase-transition targets.
    It avoids rerunning the same circuit separately for half-chain entropy and
    tripartite mutual information.
    """

    selected_steps = tuple(int(step) for step in sample_steps)
    if not selected_steps:
        raise ValueError("sample_steps must not be empty")
    if selected_steps != tuple(sorted(set(selected_steps))):
        raise ValueError("sample_steps must be strictly increasing and unique")
    if selected_steps[0] <= 0 or selected_steps[-1] > config.steps:
        raise ValueError("sample_steps must lie between 1 and config.steps")
    if include_tripartite_information and (
        config.boundary != "periodic" or config.blocks % 4
    ):
        raise ValueError(
            "tripartite mutual information requires periodic boundaries and blocks divisible by four"
        )

    rng = np.random.default_rng(seed)
    state = StabilizerState.zero_product(config.qubits)
    half_chain = tuple(range(config.qubits // 2))
    sample_index = {step: index for index, step in enumerate(selected_steps)}
    half_entropy = np.empty(len(selected_steps), dtype=np.int32)
    tripartite = (
        np.empty(len(selected_steps), dtype=np.int32)
        if include_tripartite_information
        else None
    )
    for step in range(1, config.steps + 1):
        apply_unitary_step(state, config, step, rng)
        apply_measurement_step(state, config, rng)
        index = sample_index.get(step)
        if index is None:
            continue
        half_entropy[index] = state.entropy(half_chain)
        if tripartite is not None:
            tripartite[index] = tripartite_mutual_information(
                state,
                config.blocks,
                config.qubits_per_block,
            )
    return ObservableTrajectoryResult(
        sample_steps=np.asarray(selected_steps, dtype=np.int32),
        half_chain_entropy=half_entropy,
        tripartite_mutual_information=tripartite,
    )


def _simulate_seed_chunk(
    payload: tuple[DynamicsConfig, tuple[int, ...], tuple[int, ...] | None],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    config, seeds, subsystem = payload
    trajectories = [
        simulate_trajectory(config, seed=seed, subsystem=subsystem) for seed in seeds
    ]
    return (
        np.stack([item.entropy_after_measurement for item in trajectories]),
        np.stack([item.entropy_before_measurement for item in trajectories]),
        np.stack([item.measurement_entropy_change for item in trajectories]),
        np.stack([item.random_measurements for item in trajectories]),
    )


def _simulate_observable_seed_chunk(
    payload: tuple[DynamicsConfig, tuple[int, ...], tuple[int, ...], bool],
) -> tuple[np.ndarray, np.ndarray | None]:
    config, seeds, sample_steps, include_tripartite_information = payload
    trajectories = [
        simulate_observable_trajectory(
            config,
            seed=seed,
            sample_steps=sample_steps,
            include_tripartite_information=include_tripartite_information,
        )
        for seed in seeds
    ]
    half_entropy = np.stack([item.half_chain_entropy for item in trajectories])
    if include_tripartite_information:
        tripartite = np.stack(
            [item.tripartite_mutual_information for item in trajectories]
        )
    else:
        tripartite = None
    return half_entropy, tripartite


def _trajectory_seed_chunks(
    *,
    realizations: int,
    seed: int,
    workers: int,
) -> tuple[tuple[tuple[int, ...], ...], int]:
    if realizations <= 0:
        raise ValueError("realizations must be positive")
    if workers <= 0:
        raise ValueError("workers must be positive")
    child_sequences = np.random.SeedSequence(seed).spawn(realizations)
    trajectory_seeds = tuple(
        int(sequence.generate_state(1, dtype=np.uint64)[0])
        for sequence in child_sequences
    )
    requested_workers = min(int(workers), realizations)
    chunk_size, extra = divmod(realizations, requested_workers)
    chunks: list[tuple[int, ...]] = []
    cursor = 0
    for worker_index in range(requested_workers):
        next_cursor = cursor + chunk_size + int(worker_index < extra)
        chunks.append(trajectory_seeds[cursor:next_cursor])
        cursor = next_cursor
    return tuple(chunk for chunk in chunks if chunk), requested_workers


def run_trajectory_ensemble(
    config: DynamicsConfig,
    *,
    realizations: int,
    seed: int,
    workers: int = 1,
    subsystem: Iterable[int] | None = None,
) -> EnsembleResult:
    """Run deterministic independent trajectories, optionally in processes."""

    selected = None if subsystem is None else tuple(int(qubit) for qubit in subsystem)
    chunks, requested_workers = _trajectory_seed_chunks(
        realizations=realizations,
        seed=seed,
        workers=workers,
    )
    payloads = [(config, chunk, selected) for chunk in chunks if chunk]
    started = perf_counter()
    actual_workers = requested_workers
    if requested_workers == 1:
        results = [_simulate_seed_chunk(payloads[0])]
    else:
        two_qubit_clifford_basis_mappings()
        start_method = "fork" if "fork" in mp.get_all_start_methods() else "spawn"
        try:
            with ProcessPoolExecutor(
                max_workers=requested_workers,
                mp_context=mp.get_context(start_method),
            ) as executor:
                results = list(executor.map(_simulate_seed_chunk, payloads))
        except PermissionError:
            results = [_simulate_seed_chunk(payload) for payload in payloads]
            actual_workers = 1
    after = np.concatenate([item[0] for item in results], axis=0)
    before = np.concatenate([item[1] for item in results], axis=0)
    changes = np.concatenate([item[2] for item in results], axis=0)
    random_counts = np.concatenate([item[3] for item in results], axis=0)
    return EnsembleResult(
        config=config,
        entropy_after_measurement=after,
        entropy_before_measurement=before,
        measurement_entropy_change=changes,
        random_measurements=random_counts,
        seed=int(seed),
        runtime_seconds=perf_counter() - started,
        workers=actual_workers,
        requested_workers=requested_workers,
    )


def run_observable_ensemble(
    config: DynamicsConfig,
    *,
    realizations: int,
    seed: int,
    sample_steps: Iterable[int],
    workers: int = 1,
    include_tripartite_information: bool = False,
    executor: ProcessPoolExecutor | None = None,
    create_executor: bool = True,
) -> ObservableEnsembleResult:
    """Run deterministic trajectories and collect shared steady observables."""

    selected_steps = tuple(int(step) for step in sample_steps)
    chunks, requested_workers = _trajectory_seed_chunks(
        realizations=realizations,
        seed=seed,
        workers=workers,
    )
    payloads = [
        (config, chunk, selected_steps, include_tripartite_information)
        for chunk in chunks
    ]
    started = perf_counter()
    actual_workers = requested_workers
    if requested_workers == 1:
        results = [_simulate_observable_seed_chunk(payloads[0])]
    elif executor is not None:
        results = list(executor.map(_simulate_observable_seed_chunk, payloads))
    elif not create_executor:
        results = [_simulate_observable_seed_chunk(payload) for payload in payloads]
        actual_workers = 1
    else:
        two_qubit_clifford_basis_mappings()
        start_method = "fork" if "fork" in mp.get_all_start_methods() else "spawn"
        try:
            with ProcessPoolExecutor(
                max_workers=requested_workers,
                mp_context=mp.get_context(start_method),
            ) as executor:
                results = list(executor.map(_simulate_observable_seed_chunk, payloads))
        except PermissionError:
            results = [
                _simulate_observable_seed_chunk(payload) for payload in payloads
            ]
            actual_workers = 1
    half_entropy = np.concatenate([item[0] for item in results], axis=0)
    if include_tripartite_information:
        tripartite = np.concatenate(
            [item[1] for item in results if item[1] is not None],
            axis=0,
        )
    else:
        tripartite = None
    return ObservableEnsembleResult(
        config=config,
        sample_steps=np.asarray(selected_steps, dtype=np.int32),
        half_chain_entropy=half_entropy,
        tripartite_mutual_information=tripartite,
        seed=int(seed),
        runtime_seconds=perf_counter() - started,
        workers=actual_workers,
        requested_workers=requested_workers,
    )


@contextmanager
def observable_worker_pool(
    workers: int,
) -> Iterator[ProcessPoolExecutor | None]:
    """Reuse one worker pool across a checkpointed parameter campaign.

    Creating hundreds of short-lived process pools can exhaust semaphore
    resources on macOS.  A failed pool allocation degrades explicitly to the
    serial path while preserving deterministic trajectory seeds.
    """

    if workers <= 1:
        yield None
        return
    two_qubit_clifford_basis_mappings()
    start_method = "fork" if "fork" in mp.get_all_start_methods() else "spawn"
    try:
        with ProcessPoolExecutor(
            max_workers=int(workers),
            mp_context=mp.get_context(start_method),
        ) as executor:
            yield executor
    except PermissionError:
        yield None


def tripartite_mutual_information(state: StabilizerState, blocks: int, qubits_per_block: int) -> int:
    """I3 for four equal contiguous block partitions with periodic geometry."""

    if blocks % 4:
        raise ValueError("blocks must be divisible by four for the I3 partition")
    if state.n != blocks * qubits_per_block:
        raise ValueError("state size does not match the block partition")
    quarter = blocks // 4

    def block_qubits(block_ids: Iterable[int]) -> tuple[int, ...]:
        return tuple(
            qubit
            for block in block_ids
            for qubit in range(block * qubits_per_block, (block + 1) * qubits_per_block)
        )

    a_blocks = range(0, quarter)
    b_blocks = range(quarter, 2 * quarter)
    c_blocks = range(2 * quarter, 3 * quarter)
    a = block_qubits(a_blocks)
    b = block_qubits(b_blocks)
    c = block_qubits(c_blocks)
    return (
        state.entropy(a)
        + state.entropy(b)
        + state.entropy(c)
        - state.entropy((*a, *b))
        - state.entropy((*b, *c))
        - state.entropy((*a, *c))
        + state.entropy((*a, *b, *c))
    )
