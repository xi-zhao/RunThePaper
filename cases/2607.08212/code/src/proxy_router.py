"""Deterministic proxy router for the Möbius neutral-atom compiler case.

The paper does not publish enough geometry or benchmark metadata to reproduce
Figs. 4--8 exactly.  This module therefore implements the explicitly approved
toy zoned architecture in ``config/routing_benchmark_contract.json``.  It uses
the paper's Table-I timing/fidelity values but never presents proxy outputs as
author-exact routed data.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import math
import random
from typing import Mapping, Sequence

from mobius_compiler import (
    Gate,
    Support,
    clause_phase_table,
    decompose_ccz_to_zap,
    merge_projector_terms,
    mobius_inversion,
)


MANY_BODY_FAMILIES = (
    "synthetic_3sat",
    "qaoa_3local",
    "p_spin_ising",
    "hypergraph_4local",
    "qram_oracle",
    "multiplier_oracle",
)
CONTROL_FAMILIES = ("qft_pairs", "ghz_chain")
PROXY_FAMILIES = (*MANY_BODY_FAMILIES, *CONTROL_FAMILIES)


@dataclass(frozen=True)
class ArchitectureParameters:
    t_1q_us: float
    t_2q_us: float
    t_multiq_us: float
    t_transfer_us: float
    f_1q: float
    f_2q: float
    f_transfer: float
    f_idle: float
    f_native_3: float
    f_native_4: float
    t2_us: float
    native_cutoff: int
    native_radius_um: float
    partition_capacity_atoms: int
    storage_partition_spacing_um: float
    storage_origin_distance_um: float
    storage_slot_spacing_um: float
    shared_zone_capacity_atoms: int
    concurrent_entangling_operations: int
    movement_throughput_atoms_per_layer: int

    @classmethod
    def from_contract(cls, contract: Mapping[str, object]) -> "ArchitectureParameters":
        paper = _mapping(contract.get("paper_table_i"))
        run = _mapping(contract.get("generated_run"))
        toy = _mapping(contract.get("toy_zoned_architecture"))
        return cls(
            t_1q_us=float(paper["t_1q_us"]),
            t_2q_us=float(paper["t_2q_us"]),
            t_multiq_us=float(paper["t_multiq_us"]),
            t_transfer_us=float(paper["t_transfer_us"]),
            f_1q=float(paper["f_1q"]),
            f_2q=float(paper["f_2q"]),
            f_transfer=float(paper["f_transfer"]),
            f_idle=float(paper["f_idle"]),
            f_native_3=float(paper["f_native_3"]),
            f_native_4=float(paper["f_native_4"]),
            t2_us=float(paper["t2_us"]),
            native_cutoff=int(paper["native_cutoff"]),
            native_radius_um=float(paper["native_radius_um"]),
            partition_capacity_atoms=int(run["partition_capacity_atoms"]),
            storage_partition_spacing_um=float(toy["storage_partition_spacing_um"]),
            storage_origin_distance_um=float(toy["storage_origin_distance_um"]),
            storage_slot_spacing_um=float(toy["storage_slot_spacing_um"]),
            shared_zone_capacity_atoms=int(toy["shared_zone_capacity_atoms"]),
            concurrent_entangling_operations=int(toy["concurrent_entangling_operations"]),
            movement_throughput_atoms_per_layer=int(toy["movement_throughput_atoms_per_layer"]),
        )


@dataclass(frozen=True)
class RoutedMetrics:
    qubits: int
    gate_count: int
    one_qubit_gates: int
    two_qubit_gates: int
    native_three_qubit_gates: int
    native_four_qubit_gates: int
    scheduled_stages: int
    movement_events: int
    movement_distance_um: float
    movement_duration_us: float
    transfer_events: int
    idle_exposure: int
    total_duration_us: float
    idle_coherence_us: float
    log_no_fault: float
    no_fault: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def storage_coordinates(qubits: int, architecture: ArchitectureParameters) -> dict[int, tuple[float, float]]:
    """Place qubits in declared five-atom storage partitions."""

    if qubits < 1:
        raise ValueError("qubits must be positive")
    result: dict[int, tuple[float, float]] = {}
    for qubit in range(qubits):
        partition, slot = divmod(qubit, architecture.partition_capacity_atoms)
        x = architecture.storage_origin_distance_um + partition * architecture.storage_partition_spacing_um
        centered_slot = slot - (architecture.partition_capacity_atoms - 1) / 2.0
        y = centered_slot * architecture.storage_slot_spacing_um
        result[qubit] = (x, y)
    return result


def movement_duration_us(distance_um: float) -> float:
    """Evaluate the Table-I BigMove/Park timing model."""

    if distance_um < 0:
        raise ValueError("movement distance must be non-negative")
    return 200.0 * math.sqrt(distance_um / 110.0)


def native_support_is_feasible(support: Sequence[int], architecture: ArchitectureParameters) -> bool:
    """Check the declared shared-zone capacity and clique placement."""

    degree = len(tuple(dict.fromkeys(support)))
    if degree < 3 or degree > architecture.native_cutoff:
        return False
    if degree > architecture.shared_zone_capacity_atoms:
        return False
    # The toy shared zone places active atoms on a radius-3 um ring.  Its
    # maximum pair separation is 6 um, below the paper's 8 um predicate.
    return 6.0 <= architecture.native_radius_um


def synthetic_3sat_terms(qubits: int, seed: int, clauses_per_qubit: int = 2) -> dict[Support, float]:
    """Generate a deterministic disclosed 3-SAT phase-hypergraph proxy."""

    if qubits < 3:
        raise ValueError("3-SAT proxy needs at least three qubits")
    if clauses_per_qubit < 1:
        raise ValueError("clauses_per_qubit must be positive")
    rng = random.Random((qubits << 32) ^ seed)
    clauses: list[dict[Support, float]] = []
    for _ in range(clauses_per_qubit * qubits):
        support = tuple(sorted(rng.sample(range(qubits), 3)))
        positive = tuple(qubit for qubit in support if rng.randrange(2) == 0)
        negative = tuple(qubit for qubit in support if qubit not in positive)
        table = clause_phase_table(
            support,
            positive_literals=positive,
            negative_literals=negative,
        )
        clauses.append(mobius_inversion(table, support))
    return merge_projector_terms(clauses)


def compile_projector_terms(terms: Mapping[Support, float], *, keep_native: bool) -> list[Gate]:
    """Compile proxy terms into native or fixed ZAP-decomposed streams."""

    stream: list[Gate] = []
    for support in sorted(terms, key=lambda item: (len(item), item)):
        degree = len(support)
        if degree == 1:
            stream.append(("phase", support))
        elif degree == 2:
            stream.append(("cz", support))
        elif degree == 3 and keep_native:
            stream.append(("ccz", support))
        elif degree == 3:
            stream.extend(decompose_ccz_to_zap(support))
        elif degree == 4 and keep_native:
            stream.append(("c3z", support))
        elif degree == 4:
            stream.extend(decompose_projector_to_zap(support))
        else:
            raise ValueError(f"proxy compiler supports only degree 1--4, got {degree}")
    return stream


def decompose_projector_to_zap(support: Sequence[int]) -> list[Gate]:
    """Lower a four-body pi projector with an exact Gray-code phase gadget.

    The identity ``2^(k-1) prod(x_i) = sum (-1)^(|T|-1) xor(T)`` over all
    nonempty subsets gives an exact diagonal phase polynomial.  Parities are
    grouped by their largest qubit and traversed with a cyclic Gray code, so
    intermediate parities are reused: 14 CNOTs and 15 phase rotations instead
    of independently computing every parity.  Angles are not needed by the
    proxy cost model, so every rotation is represented as a generic one-qubit
    ``phase`` gate.  CNOTs are lowered as H-CZ-H.
    """

    ordered = tuple(sorted(set(support)))
    if len(ordered) != 4:
        raise ValueError("generic proxy phase gadget is declared only for four-body supports")
    stream: list[Gate] = []
    for target_index, target in enumerate(ordered):
        controls = ordered[:target_index]
        gray_masks = [value ^ (value >> 1) for value in range(1 << len(controls))]
        current_mask = 0
        for mask in gray_masks:
            if mask != current_mask:
                changed_bit = (mask ^ current_mask).bit_length() - 1
                stream.extend(_lower_cx(controls[changed_bit], target))
            stream.append(("phase", (target,)))
            current_mask = mask
        if current_mask:
            changed_bit = current_mask.bit_length() - 1
            stream.extend(_lower_cx(controls[changed_bit], target))
    return stream


def _lower_cx(control: int, target: int) -> list[Gate]:
    return [("h", (target,)), ("cz", (control, target)), ("h", (target,))]


def benchmark_projector_terms(
    family: str,
    qubits: int,
    seed: int,
    clauses_per_qubit: int = 2,
) -> dict[Support, float]:
    """Generate one disclosed proxy family matching the paper's degree class."""

    if family == "synthetic_3sat":
        return synthetic_3sat_terms(qubits, seed, clauses_per_qubit)
    rng = random.Random(hashless_seed(family, qubits, seed))
    degree_counts = {
        "qaoa_3local": ((3, 2 * qubits),),
        "p_spin_ising": ((3, qubits), (4, qubits)),
        "hypergraph_4local": ((4, 2 * qubits),),
        "qram_oracle": ((3, qubits), (4, 2 * qubits)),
        "multiplier_oracle": ((2, qubits), (3, qubits), (4, max(1, qubits // 2))),
    }.get(family)
    if degree_counts is None:
        raise ValueError(f"family has no many-body projector generator: {family}")
    supports: dict[Support, float] = {}
    for degree, count in degree_counts:
        for support in _unique_random_supports(qubits, degree, count, rng):
            supports[support] = math.pi
    return supports


def benchmark_gate_streams(
    family: str,
    qubits: int,
    seed: int,
    clauses_per_qubit: int = 2,
) -> dict[str, list[Gate]]:
    """Return native and ZAP streams for one proxy benchmark instance."""

    if family == "qft_pairs":
        stream = qft_pair_stream(qubits)
        return {"mobius_native": stream, "zap_decomposed": list(stream)}
    if family == "ghz_chain":
        stream = ghz_chain_stream(qubits)
        return {"mobius_native": stream, "zap_decomposed": list(stream)}
    terms = benchmark_projector_terms(family, qubits, seed, clauses_per_qubit)
    return {
        "mobius_native": compile_projector_terms(terms, keep_native=True),
        "zap_decomposed": compile_projector_terms(terms, keep_native=False),
    }


def hashless_seed(family: str, qubits: int, seed: int) -> int:
    """Build a stable integer seed without Python's randomized string hash."""

    family_code = sum((index + 1) * ord(character) for index, character in enumerate(family))
    return (family_code << 40) ^ (qubits << 24) ^ seed


def _unique_random_supports(
    qubits: int,
    degree: int,
    count: int,
    rng: random.Random,
) -> list[Support]:
    if qubits < degree:
        raise ValueError(f"{degree}-body proxy needs at least {degree} qubits")
    maximum = math.comb(qubits, degree)
    target = min(count, maximum)
    supports: set[Support] = set()
    while len(supports) < target:
        supports.add(tuple(sorted(rng.sample(range(qubits), degree))))
    return sorted(supports)


def qft_pair_stream(qubits: int) -> list[Gate]:
    """Return a pairwise QFT phase layer used as a negative control."""

    return [("cz", (left, right)) for left in range(qubits) for right in range(left + 1, qubits)]


def ghz_chain_stream(qubits: int) -> list[Gate]:
    """Return H plus nearest-neighbour H-CZ-H blocks for a GHZ chain."""

    stream: list[Gate] = [("h", (0,))]
    for control in range(qubits - 1):
        target = control + 1
        stream.extend([("h", (target,)), ("cz", (control, target)), ("h", (target,))])
    return stream


def schedule_gate_stream(gates: Sequence[Gate], architecture: ArchitectureParameters) -> list[list[Gate]]:
    """Greedily schedule while preserving per-qubit order and zone capacity."""

    if architecture.concurrent_entangling_operations != 1:
        return _schedule_gate_stream_general(gates, architecture)
    stages: list[list[Gate]] = []
    last_stage: dict[int, int] = {}
    next_occupied_zone_stage: dict[int, int] = {}

    def first_free_zone_stage(stage: int) -> int:
        path: list[int] = []
        current = stage
        while current in next_occupied_zone_stage:
            path.append(current)
            current = next_occupied_zone_stage[current]
        for occupied in path:
            next_occupied_zone_stage[occupied] = current
        return current

    for gate in gates:
        _, support = gate
        earliest = max((last_stage.get(qubit, -1) for qubit in support), default=-1) + 1
        stage_index = first_free_zone_stage(earliest) if len(support) > 1 else earliest
        while len(stages) <= stage_index:
            stages.append([])
        stages[stage_index].append(gate)
        for qubit in support:
            last_stage[qubit] = stage_index
        if len(support) > 1:
            next_occupied_zone_stage[stage_index] = first_free_zone_stage(stage_index + 1)
    return stages


def _schedule_gate_stream_general(
    gates: Sequence[Gate],
    architecture: ArchitectureParameters,
) -> list[list[Gate]]:
    stages: list[list[Gate]] = []
    last_stage: dict[int, int] = {}
    for gate in gates:
        _, support = gate
        stage_index = max((last_stage.get(qubit, -1) for qubit in support), default=-1) + 1
        while True:
            if stage_index == len(stages):
                stages.append([])
            occupied = {qubit for _, placed_support in stages[stage_index] for qubit in placed_support}
            entanglers = sum(len(placed_support) > 1 for _, placed_support in stages[stage_index])
            if not (occupied & set(support)) and (
                len(support) == 1 or entanglers < architecture.concurrent_entangling_operations
            ):
                stages[stage_index].append(gate)
                for qubit in support:
                    last_stage[qubit] = stage_index
                break
            stage_index += 1
    return stages


def route_gate_stream(
    gates: Sequence[Gate],
    *,
    qubits: int,
    architecture: ArchitectureParameters,
) -> RoutedMetrics:
    """Route a gate stream and evaluate the paper's no-fault roll-up."""

    if any(qubit < 0 or qubit >= qubits for _, support in gates for qubit in support):
        raise ValueError("gate support exceeds declared qubit count")
    for gate, support in gates:
        if gate in {"ccz", "c3z"} and not native_support_is_feasible(support, architecture):
            raise ValueError(f"native support is infeasible under proxy architecture: {support}")

    coordinates = storage_coordinates(qubits, architecture)
    stages = schedule_gate_stream(gates, architecture)
    busy_time = [0.0 for _ in range(qubits)]
    movement_events = 0
    movement_distance = 0.0
    movement_duration = 0.0
    transfer_events = 0
    idle_exposure = 0
    total_duration = 0.0
    gate_names = Counter(gate for gate, _ in gates)

    for stage in stages:
        durations: list[float] = []
        for gate, support in stage:
            if len(support) == 1:
                duration = architecture.t_1q_us
            else:
                distances = [math.hypot(*coordinates[qubit]) for qubit in support]
                one_way_duration = max(movement_duration_us(distance) for distance in distances)
                move_layers = math.ceil(len(support) / architecture.movement_throughput_atoms_per_layer)
                route_move_duration = 2.0 * move_layers * one_way_duration
                gate_duration = architecture.t_multiq_us if len(support) >= 3 else architecture.t_2q_us
                duration = 2.0 * architecture.t_transfer_us + route_move_duration + gate_duration
                movement_events += 2 * len(support)
                movement_distance += 2.0 * sum(distances)
                movement_duration += route_move_duration
                transfer_events += 2 * len(support)
                idle_exposure += qubits - len(support)
            durations.append(duration)
            for qubit in support:
                busy_time[qubit] += duration
        total_duration += max(durations, default=0.0)

    one_qubit = sum(count for gate, count in gate_names.items() if gate in {"phase", "h", "t", "tdg", "z"})
    two_qubit = sum(count for gate, count in gate_names.items() if gate in {"cz"})
    native_three = gate_names["ccz"]
    native_four = gate_names["c3z"]
    idle_coherence = max(0.0, qubits * total_duration - sum(busy_time))
    log_no_fault = (
        one_qubit * math.log(architecture.f_1q)
        + two_qubit * math.log(architecture.f_2q)
        + native_three * math.log(architecture.f_native_3)
        + native_four * math.log(architecture.f_native_4)
        + transfer_events * math.log(architecture.f_transfer)
        + idle_exposure * math.log(architecture.f_idle)
        - idle_coherence / architecture.t2_us
    )
    return RoutedMetrics(
        qubits=qubits,
        gate_count=len(gates),
        one_qubit_gates=one_qubit,
        two_qubit_gates=two_qubit,
        native_three_qubit_gates=native_three,
        native_four_qubit_gates=native_four,
        scheduled_stages=len(stages),
        movement_events=movement_events,
        movement_distance_um=movement_distance,
        movement_duration_us=movement_duration,
        transfer_events=transfer_events,
        idle_exposure=idle_exposure,
        total_duration_us=total_duration,
        idle_coherence_us=idle_coherence,
        log_no_fault=log_no_fault,
        no_fault=math.exp(log_no_fault) if log_no_fault > -745.0 else 0.0,
    )


def log_no_fault_with_native_fidelities(
    metrics: RoutedMetrics,
    architecture: ArchitectureParameters,
    *,
    f_native_3: float,
    f_native_4: float,
) -> float:
    """Re-evaluate Eq. (23) on a fixed routed stream for Fig. 7 proxies."""

    if not 0.0 < f_native_3 <= 1.0 or not 0.0 < f_native_4 <= 1.0:
        raise ValueError("native fidelities must lie in (0, 1]")
    return (
        metrics.one_qubit_gates * math.log(architecture.f_1q)
        + metrics.two_qubit_gates * math.log(architecture.f_2q)
        + metrics.native_three_qubit_gates * math.log(f_native_3)
        + metrics.native_four_qubit_gates * math.log(f_native_4)
        + metrics.transfer_events * math.log(architecture.f_transfer)
        + metrics.idle_exposure * math.log(architecture.f_idle)
        - metrics.idle_coherence_us / architecture.t2_us
    )


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("routing contract section must be an object")
    return value
