"""Phase-free binary stabilizer algebra used by the numerical runner.

Only stabilizer support is required for the entropies in this paper.  Pauli
phases and sampled measurement signs cannot change those supports, so omitting
them is an exact reduction for every observable implemented in this case.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import numpy as np


def gf2_rank(matrix: np.ndarray) -> int:
    """Return the rank of a binary matrix over GF(2)."""

    work = np.asarray(matrix, dtype=np.uint8).copy() & 1
    rows, columns = work.shape
    rank = 0
    for column in range(columns):
        pivots = np.flatnonzero(work[rank:, column])
        if not len(pivots):
            continue
        pivot = rank + int(pivots[0])
        if pivot != rank:
            work[[rank, pivot]] = work[[pivot, rank]]
        active = np.flatnonzero(work[:, column])
        active = active[active != rank]
        if len(active):
            work[active] ^= work[rank]
        rank += 1
        if rank == rows:
            break
    return rank


def gf2_rank_packed(matrix: np.ndarray) -> int:
    """Return GF(2) rank using Python's packed arbitrary-width bit vectors.

    This is mathematically identical to :func:`gf2_rank`, but is much faster
    for the wide complement restrictions that occur in an incomplete-record
    mixed stabilizer.  It is kept as an independent implementation path and is
    parity-tested against the transparent byte-matrix elimination above.
    """

    work = np.asarray(matrix, dtype=np.uint8) & 1
    if work.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    if work.shape[0] == 0 or work.shape[1] == 0:
        return 0
    packed = np.packbits(work, axis=1, bitorder="little")
    basis: dict[int, int] = {}
    for row in packed:
        value = int.from_bytes(row.tobytes(), "little")
        while value:
            pivot = value.bit_length() - 1
            existing = basis.get(pivot)
            if existing is None:
                basis[pivot] = value
                break
            value ^= existing
    return len(basis)


def _elementary_symplectic(gate: str) -> np.ndarray:
    """Matrix for a two-qubit Clifford generator in [x0,x1,z0,z1]."""

    matrix = np.eye(4, dtype=np.uint8)
    if gate == "H0":
        matrix[:, [0, 2]] = matrix[:, [2, 0]]
    elif gate == "H1":
        matrix[:, [1, 3]] = matrix[:, [3, 1]]
    elif gate == "S0":
        matrix[:, 2] ^= matrix[:, 0]
    elif gate == "S1":
        matrix[:, 3] ^= matrix[:, 1]
    elif gate == "CX01":
        matrix[:, 1] ^= matrix[:, 0]
        matrix[:, 2] ^= matrix[:, 3]
    elif gate == "CX10":
        matrix[:, 0] ^= matrix[:, 1]
        matrix[:, 3] ^= matrix[:, 2]
    else:
        raise ValueError(f"unknown Clifford generator: {gate}")
    return matrix


@lru_cache(maxsize=1)
def two_qubit_symplectic_group() -> tuple[np.ndarray, ...]:
    """Enumerate all 720 elements of Sp(4,2).

    Sampling this group uniformly is equivalent to sampling the two-qubit
    Clifford group modulo Pauli phases.  Those phases are immaterial for the
    stabilizer entropies and purification events studied here.
    """

    generators = tuple(
        _elementary_symplectic(name)
        for name in ("H0", "H1", "S0", "S1", "CX01", "CX10")
    )
    identity = np.eye(4, dtype=np.uint8)
    group: list[np.ndarray] = [identity]
    seen = {identity.tobytes()}
    cursor = 0
    while cursor < len(group):
        current = group[cursor]
        cursor += 1
        for generator in generators:
            candidate = (current @ generator) & 1
            key = candidate.tobytes()
            if key not in seen:
                seen.add(key)
                group.append(candidate)
    if len(group) != 720:
        raise RuntimeError(f"expected |Sp(4,2)|=720, obtained {len(group)}")
    return tuple(group)


class StabilizerState:
    """Pure stabilizer state represented by n independent binary generators."""

    def __init__(self, tableau: np.ndarray):
        tableau = np.asarray(tableau, dtype=np.uint8) & 1
        if tableau.ndim != 2 or tableau.shape[1] != 2 * tableau.shape[0]:
            raise ValueError("tableau must have shape (n, 2n)")
        self.tableau = tableau.copy()

    @classmethod
    def product_zero(cls, qubits: int) -> "StabilizerState":
        tableau = np.zeros((qubits, 2 * qubits), dtype=np.uint8)
        tableau[np.arange(qubits), qubits + np.arange(qubits)] = 1
        return cls(tableau)

    @property
    def qubits(self) -> int:
        return self.tableau.shape[0]

    def copy(self) -> "StabilizerState":
        return StabilizerState(self.tableau)

    def apply_h(self, qubit: int) -> None:
        n = self.qubits
        self.tableau[:, [qubit, n + qubit]] = self.tableau[:, [n + qubit, qubit]]

    def apply_s(self, qubit: int) -> None:
        n = self.qubits
        self.tableau[:, n + qubit] ^= self.tableau[:, qubit]

    def apply_cnot(self, control: int, target: int) -> None:
        n = self.qubits
        self.tableau[:, target] ^= self.tableau[:, control]
        self.tableau[:, n + control] ^= self.tableau[:, n + target]

    def apply_two_qubit(self, first: int, second: int, matrix: np.ndarray) -> None:
        n = self.qubits
        columns = [first, second, n + first, n + second]
        local = self.tableau[:, columns]
        self.tableau[:, columns] = (local @ matrix) & 1

    def measure_z(self, qubit: int) -> bool:
        """Projectively measure Z and return whether the support changed."""

        anticommuting = np.flatnonzero(self.tableau[:, qubit])
        if not len(anticommuting):
            return False
        pivot = int(anticommuting[0])
        others = anticommuting[1:]
        if len(others):
            self.tableau[others] ^= self.tableau[pivot]
        self.tableau[pivot] = 0
        self.tableau[pivot, self.qubits + qubit] = 1
        return True

    def entropy(self, qubits: Iterable[int]) -> int:
        """Von Neumann entropy in bits of a subsystem of a pure state."""

        subset = tuple(sorted(set(int(qubit) for qubit in qubits)))
        if not subset:
            return 0
        n = self.qubits
        columns = list(subset) + [n + qubit for qubit in subset]
        return gf2_rank(self.tableau[:, columns]) - len(subset)

    def mutual_information(self, first: Iterable[int], second: Iterable[int]) -> int:
        a = tuple(first)
        b = tuple(second)
        return self.entropy(a) + self.entropy(b) - self.entropy(a + b)

    def is_valid(self) -> bool:
        """Check independence and pairwise commutation of the generators."""

        n = self.qubits
        x = self.tableau[:, :n]
        z = self.tableau[:, n:]
        commutator = ((x @ z.T) ^ (z @ x.T)) & 1
        return gf2_rank(self.tableau) == n and not np.any(commutator)


class MixedStabilizerState:
    """Possibly mixed stabilizer state with a variable-rank generator group.

    This representation is needed when a physical measurement is performed but
    its outcome is not present in the decoder record.  Averaging over that
    unknown outcome is a dephasing channel: anticommuting stabilizers are
    removed instead of replacing one of them with the measured Pauli.  The
    resulting density operator is therefore mixed even though every fully
    conditioned trajectory remains pure.

    Pauli signs are still unnecessary for the entropies used here.  Conditioning
    on a recorded outcome changes signs but not the support or rank of the
    stabilizer group.
    """

    def __init__(self, tableau: np.ndarray, qubits: int):
        tableau = np.asarray(tableau, dtype=np.uint8) & 1
        if tableau.ndim != 2 or tableau.shape[1] != 2 * qubits:
            raise ValueError("tableau must have shape (rank, 2 * qubits)")
        if tableau.shape[0] > qubits:
            raise ValueError("a stabilizer group cannot have rank above qubit count")
        self.tableau = tableau.copy()
        self._qubits = int(qubits)
        if not self.is_valid():
            raise ValueError("tableau generators must be independent and commuting")

    @classmethod
    def product_zero(cls, qubits: int) -> "MixedStabilizerState":
        tableau = np.zeros((qubits, 2 * qubits), dtype=np.uint8)
        tableau[np.arange(qubits), qubits + np.arange(qubits)] = 1
        return cls(tableau, qubits)

    @classmethod
    def from_pure(cls, state: StabilizerState) -> "MixedStabilizerState":
        return cls(state.tableau, state.qubits)

    @property
    def qubits(self) -> int:
        return self._qubits

    @property
    def stabilizer_rank(self) -> int:
        return int(self.tableau.shape[0])

    def copy(self) -> "MixedStabilizerState":
        return MixedStabilizerState(self.tableau, self.qubits)

    def apply_h(self, qubit: int) -> None:
        n = self.qubits
        self.tableau[:, [qubit, n + qubit]] = self.tableau[:, [n + qubit, qubit]]

    def apply_s(self, qubit: int) -> None:
        n = self.qubits
        self.tableau[:, n + qubit] ^= self.tableau[:, qubit]

    def apply_cnot(self, control: int, target: int) -> None:
        n = self.qubits
        self.tableau[:, target] ^= self.tableau[:, control]
        self.tableau[:, n + control] ^= self.tableau[:, n + target]

    def apply_two_qubit(self, first: int, second: int, matrix: np.ndarray) -> None:
        n = self.qubits
        columns = [first, second, n + first, n + second]
        local = self.tableau[:, columns]
        self.tableau[:, columns] = (local @ matrix) & 1

    def measure_z(self, qubit: int, *, record_outcome: bool) -> bool:
        """Apply a recorded projection or an unrecorded dephasing channel.

        Returns whether the stabilizer group changed.  A recorded measurement
        conditions the state on its outcome.  An unrecorded measurement applies
        ``rho -> (rho + Z rho Z) / 2`` and therefore removes one anticommuting
        generator.  This distinction is the scientific content of Main Fig.
        2(b); skipping unrecorded measurements would simulate a different
        physical circuit.
        """

        anticommuting = np.flatnonzero(self.tableau[:, qubit])
        if len(anticommuting):
            pivot = int(anticommuting[0])
            others = anticommuting[1:]
            if len(others):
                self.tableau[others] ^= self.tableau[pivot]
            if record_outcome:
                self.tableau[pivot] = 0
                self.tableau[pivot, self.qubits + qubit] = 1
            else:
                self.tableau = np.delete(self.tableau, pivot, axis=0)
            return True

        if not record_outcome:
            return False

        measured = np.zeros((1, 2 * self.qubits), dtype=np.uint8)
        measured[0, self.qubits + qubit] = 1
        old_rank = self.stabilizer_rank
        augmented = np.concatenate((self.tableau, measured), axis=0)
        if gf2_rank_packed(augmented) == old_rank:
            return False
        self.tableau = augmented
        return True

    def entropy(self, qubits: Iterable[int]) -> int:
        """Von Neumann entropy in bits of a mixed stabilizer subsystem.

        For a rank-r stabilizer group, the reduced state on A has entropy
        ``|A| - dim(S_A)``, where ``S_A`` is the subgroup supported entirely in
        A.  ``dim(S_A)`` is the nullity of the restriction map to A's
        complement.  The formula reduces to the familiar pure-state rank
        identity used by :class:`StabilizerState`.
        """

        subset = tuple(sorted(set(int(qubit) for qubit in qubits)))
        if not subset:
            return 0
        subset_set = set(subset)
        outside = [qubit for qubit in range(self.qubits) if qubit not in subset_set]
        outside_columns = outside + [self.qubits + qubit for qubit in outside]
        restricted_rank = (
            gf2_rank_packed(self.tableau[:, outside_columns]) if outside_columns else 0
        )
        local_stabilizers = self.stabilizer_rank - restricted_rank
        entropy = len(subset) - local_stabilizers
        if not 0 <= entropy <= len(subset):
            raise RuntimeError("mixed stabilizer entropy fell outside physical bounds")
        return int(entropy)

    def is_valid(self) -> bool:
        n = self.qubits
        x = self.tableau[:, :n]
        z = self.tableau[:, n:]
        commutator = ((x @ z.T) ^ (z @ x.T)) & 1
        return gf2_rank(self.tableau) == self.stabilizer_rank and not np.any(commutator)


def insert_bell_pair(
    state: StabilizerState | MixedStabilizerState,
    reference: int,
    system_site: int,
) -> None:
    """Reset one system site and create a Bell pair with a fresh |0> reference."""

    if isinstance(state, MixedStabilizerState):
        state.measure_z(system_site, record_outcome=True)
    else:
        state.measure_z(system_site)
    state.apply_h(reference)
    state.apply_cnot(reference, system_site)
