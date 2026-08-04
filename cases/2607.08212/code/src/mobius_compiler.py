"""Small, auditable core for the Möbius neutral-atom compiler case.

The module implements only paper-defined algebra and the Fig. 3 gate-accounting
mechanism.  The paper's unpublished benchmark generators and routed geometry do
not enter this baseline.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
import math
from typing import Iterable, Mapping, Sequence


Support = tuple[int, ...]
Gate = tuple[str, Support]


def canonical_support(values: Iterable[int]) -> Support:
    """Return one duplicate-free, sorted support tuple."""

    support = tuple(sorted(set(values)))
    if any(value < 0 for value in support):
        raise ValueError("qubit labels must be non-negative")
    return support


def subsets(support: Iterable[int]) -> list[Support]:
    """Enumerate subsets in degree-then-lexicographic order."""

    ordered = canonical_support(support)
    return [
        tuple(choice)
        for degree in range(len(ordered) + 1)
        for choice in combinations(ordered, degree)
    ]


def wrap_phase(value: float, *, tolerance: float = 1e-12) -> float:
    """Wrap a phase to [-pi, pi), treating numerical 0 and 2pi as zero."""

    wrapped = (value + math.pi) % (2.0 * math.pi) - math.pi
    if abs(wrapped) < tolerance:
        return 0.0
    return wrapped


def mobius_inversion(
    phase_table: Mapping[Support, float],
    variables: Iterable[int],
) -> dict[Support, float]:
    """Apply Eq. (7) on a complete local computational-basis phase table."""

    variables = canonical_support(variables)
    expected = set(subsets(variables))
    normalized = {canonical_support(key): float(value) for key, value in phase_table.items()}
    if set(normalized) != expected:
        missing = sorted(expected - set(normalized), key=lambda item: (len(item), item))
        extra = sorted(set(normalized) - expected, key=lambda item: (len(item), item))
        raise ValueError(f"phase table must cover every subset; missing={missing}, extra={extra}")

    coefficients: dict[Support, float] = {}
    for support in subsets(variables):
        value = sum(
            ((-1) ** (len(support) - len(subset))) * normalized[subset]
            for subset in subsets(support)
        )
        coefficients[support] = wrap_phase(value)
    return coefficients


def zeta_reconstruct(
    coefficients: Mapping[Support, float],
    variables: Iterable[int],
) -> dict[Support, float]:
    """Reconstruct Eq. (6) from projector-phase coefficients."""

    normalized = {canonical_support(key): float(value) for key, value in coefficients.items()}
    result: dict[Support, float] = {}
    for occupied in subsets(variables):
        occupied_set = set(occupied)
        result[occupied] = wrap_phase(
            sum(value for support, value in normalized.items() if set(support) <= occupied_set)
        )
    return result


def phase_distance(left: float, right: float) -> float:
    """Return the absolute circular distance between two phases."""

    return abs(wrap_phase(left - right))


def phase_tables_equal(
    left: Mapping[Support, float],
    right: Mapping[Support, float],
    *,
    tolerance: float = 1e-10,
) -> bool:
    """Check diagonal-unitary equality modulo 2pi, including global phase."""

    if set(left) != set(right):
        return False
    return all(phase_distance(float(left[key]), float(right[key])) <= tolerance for key in left)


def clause_phase_table(
    variables: Iterable[int],
    *,
    positive_literals: Iterable[int],
    negative_literals: Iterable[int],
    phase: float = math.pi,
) -> dict[Support, float]:
    """Build the violating-pattern phase table from Eq. (21).

    A positive literal is violated at x=0; a negative literal is violated at
    x=1.  The two literal sets must partition ``variables``.
    """

    variables = canonical_support(variables)
    positive = set(canonical_support(positive_literals))
    negative = set(canonical_support(negative_literals))
    if positive & negative or positive | negative != set(variables):
        raise ValueError("positive and negative literals must partition the clause variables")

    table: dict[Support, float] = {}
    for occupied in subsets(variables):
        occupied_set = set(occupied)
        violates = not (positive & occupied_set) and negative <= occupied_set
        table[occupied] = wrap_phase(phase if violates else 0.0)
    return table


def merge_projector_terms(
    term_sets: Iterable[Mapping[Support, float]],
) -> dict[Support, float]:
    """Merge equal supports, wrap phases, and discard zero terms (Eq. 14)."""

    merged: dict[Support, float] = {}
    for terms in term_sets:
        for support, value in terms.items():
            support = canonical_support(support)
            merged[support] = wrap_phase(merged.get(support, 0.0) + float(value))
    return {support: value for support, value in merged.items() if support and value != 0.0}


def asap_depth(gates: Sequence[Gate]) -> int:
    """Compute circuit-DAG ASAP depth while preserving per-qubit gate order."""

    last_layer: dict[int, int] = {}
    depth = 0
    for _, qubits in gates:
        qubits = canonical_support(qubits)
        if not qubits:
            raise ValueError("gates must act on at least one qubit")
        layer = max((last_layer.get(qubit, 0) for qubit in qubits), default=0) + 1
        for qubit in qubits:
            last_layer[qubit] = layer
        depth = max(depth, layer)
    return depth


def decompose_ccz_to_zap(qubits: Sequence[int]) -> list[Gate]:
    """Return one exact 6-CNOT/7-phase CCZ decomposition.

    The phase polynomial is the sign-reversed form of
    ``4abc = a+b+c-(a xor b)-(a xor c)-(b xor c)+(a xor b xor c)``.
    Reversing every sign leaves the CCZ phase unchanged modulo 2pi and gives
    the paper's per-block 3 T / 4 T-dagger census.  Each CNOT is lowered to
    H-CZ-H for the neutral-atom gate set used in Fig. 3.
    """

    a, b, c = canonical_support(qubits)
    logical: list[Gate] = [
        ("tdg", (a,)),
        ("tdg", (b,)),
        ("tdg", (c,)),
        ("cx", (a, b)),
        ("t", (b,)),
        ("cx", (a, b)),
        ("cx", (b, c)),
        ("t", (c,)),
        ("cx", (a, c)),
        ("tdg", (c,)),
        ("cx", (b, c)),
        ("t", (c,)),
        ("cx", (a, c)),
    ]
    elementary: list[Gate] = []
    for gate, support in logical:
        if gate == "cx":
            control, target = support
            elementary.extend([("h", (target,)), ("cz", (control, target)), ("h", (target,))])
        else:
            elementary.append((gate, support))
    return elementary


def decompose_native_stream_to_zap(gates: Sequence[Gate]) -> list[Gate]:
    """Lower every CCZ in a source stream with the paper's fixed template."""

    result: list[Gate] = []
    for gate, support in gates:
        support = canonical_support(support)
        if gate == "ccz":
            result.extend(decompose_ccz_to_zap(support))
        elif gate in {"z", "cz"}:
            result.append((gate, support))
        else:
            raise ValueError(f"unsupported native gate: {gate}")
    return result


def gate_counts(gates: Sequence[Gate]) -> dict[str, int]:
    """Count gate names in deterministic key order."""

    counts = Counter(gate for gate, _ in gates)
    return {gate: counts[gate] for gate in sorted(counts)}


def max_support_degree(supports: Iterable[Iterable[int]]) -> int:
    """Return the largest support degree, or zero for an empty stream."""

    return max((len(canonical_support(support)) for support in supports), default=0)
