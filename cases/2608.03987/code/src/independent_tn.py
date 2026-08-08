"""Independent tensor-network model and contraction-tree optimizer.

This module deliberately does not import or execute the authors' Rust crates.  It
implements the model described in arXiv:2608.03987 directly:

* quantum circuits are lowered to a closed binary-index tensor hypergraph;
* leaves are marked green exactly when their tensor has an imaginary entry;
* a contraction step is a pass, ride, or merge according to its two children;
* skeleton and realified objectives are evaluated as ``sum(v)`` and
  ``sum(factor * v)`` with factors 1, 2, and 3;
* binary trees are searched with greedy initialization and NNI simulated
  annealing.

Only circuit inputs from the public benchmark archive are consumed.  Published
plans, optimizer studies, and Rust-generated contraction orders are not inputs to
the optimizer.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping, Sequence


Objective = Literal["skeleton", "real"]


@dataclass(frozen=True)
class TensorLeaf:
    indices: frozenset[int]
    green: bool
    label: str


@dataclass(frozen=True)
class TensorNetwork:
    name: str
    family: str
    leaves: tuple[TensorLeaf, ...]
    index_incidence: Mapping[int, int]
    source_kind: str

    def validate(self) -> None:
        if len(self.leaves) < 2:
            raise ValueError(f"{self.name}: a contraction network needs at least two leaves")
        observed: Counter[int] = Counter()
        for leaf in self.leaves:
            if not leaf.indices:
                raise ValueError(f"{self.name}: scalar leaf is unsupported ({leaf.label})")
            observed.update(leaf.indices)
        if dict(observed) != dict(self.index_incidence):
            raise ValueError(f"{self.name}: index-incidence table is inconsistent")
        dangling = sorted(index for index, degree in observed.items() if degree < 2)
        if dangling:
            raise ValueError(f"{self.name}: closed network has dangling indices {dangling[:8]}")

    @property
    def green_leaves(self) -> int:
        return sum(leaf.green for leaf in self.leaves)

    @property
    def topology_sha256(self) -> str:
        payload = {
            "name": self.name,
            "family": self.family,
            "leaves": [
                {"indices": sorted(leaf.indices), "green": leaf.green, "label": leaf.label}
                for leaf in self.leaves
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


class _CircuitBuilder:
    def __init__(self, name: str, family: str, num_qubits: int, source_kind: str) -> None:
        self.name = name
        self.family = family
        self.num_qubits = num_qubits
        self.source_kind = source_kind
        self.next_index = num_qubits
        self.current = list(range(num_qubits))
        self.leaves = [
            TensorLeaf(frozenset((qubit,)), False, f"ket0[{qubit}]")
            for qubit in range(num_qubits)
        ]

    def apply(self, targets: Sequence[int], *, diagonal: bool, green: bool, label: str) -> None:
        if not targets:
            raise ValueError(f"{self.name}: gate {label!r} has no targets")
        if len(set(targets)) != len(targets):
            raise ValueError(f"{self.name}: gate {label!r} repeats a target")
        old_indices = [self.current[target] for target in targets]
        if diagonal:
            indices = old_indices
        else:
            new_indices = list(range(self.next_index, self.next_index + len(targets)))
            self.next_index += len(targets)
            indices = old_indices + new_indices
            for target, new_index in zip(targets, new_indices, strict=True):
                self.current[target] = new_index
        self.leaves.append(TensorLeaf(frozenset(indices), green, label))

    def add_observable(self, paulis: Mapping[int, str]) -> None:
        for qubit in range(self.num_qubits):
            pauli = paulis.get(qubit, "I")
            self.apply(
                (qubit,),
                # The expectation-value construction places one rank-2
                # operator tensor on every wire, including I and Z.  Unlike
                # circuit diagonal gates, this middle layer separates ket and
                # bra networks explicitly.
                diagonal=False,
                green=pauli == "Y",
                label=f"observable:{pauli}[{qubit}]",
            )

    def close(self) -> TensorNetwork:
        for qubit, index in enumerate(self.current):
            self.leaves.append(TensorLeaf(frozenset((index,)), False, f"bra0[{qubit}]"))
        incidence: Counter[int] = Counter()
        for leaf in self.leaves:
            incidence.update(leaf.indices)
        network = TensorNetwork(
            name=self.name,
            family=self.family,
            leaves=tuple(self.leaves),
            index_incidence=dict(incidence),
            source_kind=self.source_kind,
        )
        network.validate()
        return network


_QSIM_LINE = re.compile(r"^\s*(\d+)\s+(.+?)\s+((?:\d+\s*)+)$")
_GATE_BASE = re.compile(r"^([A-Za-z0-9_]+)")
_PAULI = re.compile(r"([IXYZ])\((\d+)\)")


def _qsim_gate_properties(expression: str) -> tuple[bool, bool]:
    match = _GATE_BASE.match(expression)
    if match is None:
        raise ValueError(f"Unsupported qsim gate expression: {expression!r}")
    gate = match.group(1).lower()
    if gate in {"h", "x", "cx", "cz"}:
        return gate == "cz", False
    if gate == "t":
        return True, True
    if gate == "rz":
        return True, True
    # qsim's sqrt(Y) is real: (I - iY)/sqrt(2).  sqrt(X), sqrt(W),
    # and fSim retain nonzero imaginary entries.
    if gate == "y_1_2":
        return False, False
    if gate in {"x_1_2", "hz_1_2", "fsim"}:
        return False, True
    raise ValueError(f"Unsupported qsim gate {gate!r} in {expression!r}")


def build_qsim_network(name: str, family: str, text: str) -> TensorNetwork:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"{name}: empty qsim circuit")
    num_qubits = int(lines[0])
    parsed_lines: list[tuple[str, tuple[int, ...]]] = []
    for line in lines[1:]:
        match = _QSIM_LINE.match(line)
        if match is None:
            raise ValueError(f"{name}: cannot parse qsim line {line!r}")
        expression = match.group(2).strip()
        targets = tuple(int(value) for value in match.group(3).split())
        parsed_lines.append((expression, targets))
    physical_qubits = sorted({target for _, targets in parsed_lines for target in targets})
    if len(physical_qubits) != num_qubits:
        raise ValueError(
            f"{name}: header declares {num_qubits} qubits but gates address "
            f"{len(physical_qubits)} labels"
        )
    # qsim files may use sparse hardware labels (the five-qubit validation
    # circuit addresses 0,1,2,3,5).  Tensor topology is invariant under this
    # explicit dense relabeling.
    dense_label = {physical: dense for dense, physical in enumerate(physical_qubits)}
    builder = _CircuitBuilder(name, family, num_qubits, "qsim-text")
    for expression, physical_targets in parsed_lines:
        targets = tuple(dense_label[target] for target in physical_targets)
        diagonal, green = _qsim_gate_properties(expression)
        builder.apply(targets, diagonal=diagonal, green=green, label=expression)
    return builder.close()


def _has_nonzero_imaginary(value: Any) -> bool:
    if isinstance(value, list):
        if len(value) == 2 and all(isinstance(part, (int, float)) for part in value):
            return float(value[1]) != 0.0
        return any(_has_nonzero_imaginary(part) for part in value)
    return False


def _structured_gate_properties(element: Mapping[str, Any]) -> tuple[tuple[int, ...], bool, bool, str]:
    gate = str(element["gate"])
    controls = tuple(int(value) for value in element.get("controls", ()))
    targets = tuple(int(value) for value in element.get("targets", ()))
    wires = controls + targets
    if gate == "Custom":
        diagonal = bool(element.get("is_diagonal", False))
        green = _has_nonzero_imaginary(element.get("matrix", []))
        return wires, diagonal, green, str(element.get("label", "Custom"))
    if gate in {"H", "X", "Ry"}:
        return wires, False, False, gate
    if gate == "Z":
        return wires, True, False, "CZ" if controls else "Z"
    if gate == "T":
        return wires, True, True, gate
    if gate == "Rz":
        return wires, True, True, gate
    if gate == "Rx":
        return wires, False, True, gate
    raise ValueError(f"Unsupported structured gate {gate!r}")


def _parse_observable(text: str, num_qubits: int) -> dict[int, str] | None:
    stripped = text.strip()
    if stripped == "OVERLAP":
        return None
    matches = list(_PAULI.finditer(stripped))
    if not matches or "".join(match.group(0) for match in matches) != stripped:
        raise ValueError(f"Unsupported observable expression: {stripped!r}")
    paulis: dict[int, str] = {}
    for match in matches:
        pauli = match.group(1)
        qubit = int(match.group(2))
        if qubit >= num_qubits:
            raise ValueError(f"Observable qubit {qubit} is outside a {num_qubits}-qubit circuit")
        if qubit in paulis:
            raise ValueError(f"Observable repeats qubit {qubit}")
        paulis[qubit] = pauli
    return paulis


def build_structured_network(
    name: str,
    family: str,
    circuit_payload: Mapping[str, Any],
    observable_text: str,
) -> TensorNetwork:
    num_qubits = int(circuit_payload["num_qubits"])
    elements = tuple(circuit_payload["elements"])
    builder = _CircuitBuilder(name, family, num_qubits, "structured-circuit-json")
    parsed: list[tuple[tuple[int, ...], bool, bool, str]] = []
    for element in elements:
        if element.get("type") != "gate":
            raise ValueError(f"{name}: unsupported circuit element {element.get('type')!r}")
        properties = _structured_gate_properties(element)
        parsed.append(properties)
        wires, diagonal, green, label = properties
        builder.apply(wires, diagonal=diagonal, green=green, label=label)

    observable = _parse_observable(observable_text, num_qubits)
    if observable is not None:
        builder.add_observable(observable)
        for wires, diagonal, green, label in reversed(parsed):
            builder.apply(wires, diagonal=diagonal, green=green, label=f"adjoint:{label}")
    return builder.close()


@dataclass(frozen=True)
class TreeStatistics:
    base_volume: int
    real_volume: int
    pass_volume: int
    ride_volume: int
    merge_volume: int
    pass_nodes: int
    ride_nodes: int
    merge_nodes: int
    peak_rank: int

    @property
    def m(self) -> float:
        return self.merge_volume / self.base_volume

    @property
    def r(self) -> float:
        return self.ride_volume / self.base_volume

    @property
    def overhead(self) -> float:
        return self.real_volume / self.base_volume

    @property
    def law_value(self) -> float:
        return 1.0 + 2.0 * self.m + self.r

    def as_dict(self) -> dict[str, int | float]:
        return {
            "base_volume": self.base_volume,
            "real_volume": self.real_volume,
            "pass_volume": self.pass_volume,
            "ride_volume": self.ride_volume,
            "merge_volume": self.merge_volume,
            "pass_nodes": self.pass_nodes,
            "ride_nodes": self.ride_nodes,
            "merge_nodes": self.merge_nodes,
            "peak_rank": self.peak_rank,
            "m": self.m,
            "r": self.r,
            "overhead": self.overhead,
            "law_value": self.law_value,
            "law_residual": abs(self.overhead - self.law_value),
            "log2_base_volume": math.log2(self.base_volume),
            "log2_real_volume": math.log2(self.real_volume),
        }


class ContractionTree:
    """A mutable rooted binary tree with O(boundary-rank) NNI updates."""

    def __init__(
        self,
        network: TensorNetwork,
        left: list[int],
        right: list[int],
        parent: list[int],
        root: int,
    ) -> None:
        self.network = network
        self.nleaves = len(network.leaves)
        self.left = left
        self.right = right
        self.parent = parent
        self.root = root
        nnodes = len(left)
        self.leaf_mask = [0] * nnodes
        self.boundary: list[frozenset[int]] = [frozenset() for _ in range(nnodes)]
        self.green = [False] * nnodes
        self.volume = [0] * nnodes
        self.factor = [0] * nnodes
        self.rank = [0] * nnodes
        index_masks: dict[int, int] = defaultdict(int)
        for leaf_id, leaf in enumerate(network.leaves):
            bit = 1 << leaf_id
            self.leaf_mask[leaf_id] = bit
            self.boundary[leaf_id] = leaf.indices
            self.green[leaf_id] = leaf.green
            for index in leaf.indices:
                index_masks[index] |= bit
        self.index_masks = dict(index_masks)
        self.recompute_all()

    @classmethod
    def greedy(cls, network: TensorNetwork, objective: Objective, seed: int) -> "ContractionTree":
        import heapq

        network.validate()
        rng = random.Random(seed)
        nleaves = len(network.leaves)
        left = [-1] * (2 * nleaves - 1)
        right = [-1] * (2 * nleaves - 1)
        parent = [-1] * (2 * nleaves - 1)

        incidence_masks: dict[int, int] = defaultdict(int)
        for leaf_id, leaf in enumerate(network.leaves):
            for index in leaf.indices:
                incidence_masks[index] |= 1 << leaf_id

        active: set[int] = set(range(nleaves))
        masks: dict[int, int] = {leaf_id: 1 << leaf_id for leaf_id in active}
        boundaries: dict[int, frozenset[int]] = {
            leaf_id: leaf.indices for leaf_id, leaf in enumerate(network.leaves)
        }
        greens: dict[int, bool] = {
            leaf_id: leaf.green for leaf_id, leaf in enumerate(network.leaves)
        }
        by_index: dict[int, set[int]] = defaultdict(set)
        for leaf_id, boundary in boundaries.items():
            for index in boundary:
                by_index[index].add(leaf_id)

        heap: list[tuple[float, int, int, int, int]] = []
        queued: set[tuple[int, int]] = set()

        def result_boundary(a: int, b: int) -> frozenset[int]:
            mask = masks[a] | masks[b]
            return frozenset(
                index
                for index in boundaries[a] | boundaries[b]
                if incidence_masks[index] & mask != incidence_masks[index]
            )

        def queue_pair(a: int, b: int) -> None:
            if a == b:
                return
            if a > b:
                a, b = b, a
            key = (a, b)
            if key in queued:
                return
            queued.add(key)
            union_rank = len(boundaries[a] | boundaries[b])
            out_rank = len(result_boundary(a, b))
            factor = 1
            if objective == "real":
                factor = 3 if greens[a] and greens[b] else 2 if greens[a] or greens[b] else 1
            # A randomized memory-removed score is a transparent independent
            # analogue of common greedy einsum heuristics.  Raw element counts
            # matter here: a one-rank reduction at rank 20 should dominate many
            # low-rank conveniences.  A small local arithmetic term lets the
            # real-aware initializer distinguish pass/ride/merge ties.
            output_size = 1 << out_rank
            input_size = (1 << len(boundaries[a])) + (1 << len(boundaries[b]))
            step_size = factor * (1 << union_rank)
            memory_weight = 0.8 + 0.4 * rng.random()
            score = output_size - memory_weight * input_size + 0.02 * step_size
            score *= 1.0 + rng.uniform(-0.01, 0.01)
            heapq.heappush(heap, (score, union_rank, out_rank, a, b))

        for members in by_index.values():
            ordered = sorted(members)
            for position, a in enumerate(ordered):
                for b in ordered[position + 1 :]:
                    queue_pair(a, b)

        next_node = nleaves
        while len(active) > 1:
            pair: tuple[int, int] | None = None
            while heap:
                _, _, _, a, b = heapq.heappop(heap)
                if a in active and b in active:
                    pair = (a, b)
                    break
            if pair is None:
                # Disconnected scalar factors are legal.  Keep the outer
                # product deterministic apart from the trial seed.
                choices = sorted(active, key=lambda node: (len(boundaries[node]), rng.random()))
                pair = (choices[0], choices[1])
            a, b = pair
            node = next_node
            next_node += 1
            left[node], right[node] = a, b
            parent[a] = parent[b] = node
            new_mask = masks[a] | masks[b]
            new_boundary = result_boundary(a, b)
            new_green = greens[a] or greens[b]

            active.remove(a)
            active.remove(b)
            for index in boundaries[a]:
                by_index[index].discard(a)
            for index in boundaries[b]:
                by_index[index].discard(b)
            active.add(node)
            masks[node] = new_mask
            boundaries[node] = new_boundary
            greens[node] = new_green
            neighbors: set[int] = set()
            for index in new_boundary:
                neighbors.update(by_index[index])
                by_index[index].add(node)
            for other in neighbors:
                if other != node:
                    queue_pair(node, other)

        root = next(iter(active))
        return cls(network, left, right, parent, root)

    @classmethod
    def einsum_greedy(
        cls,
        network: TensorNetwork,
        *,
        seed: int,
        jitter: bool,
    ) -> "ContractionTree":
        """Build a generic einsum path without using any paper-author code.

        ``opt_einsum`` supplies only the standard memory-removed initializer.
        The physical cost evaluator and all subsequent NNI optimization remain
        in this module.
        """

        from opt_einsum import paths

        rng = random.Random(seed)

        def jittered_memory_removed(
            size12: int,
            size1: int,
            size2: int,
            _k12: int,
            _k1: int,
            _k2: int,
        ) -> float:
            base = size12 - size1 - size2
            return rng.gauss(1.0, 0.01) * base

        inputs = [frozenset(leaf.indices) for leaf in network.leaves]
        sizes = {index: 2 for index in network.index_incidence}
        ssa_path = paths.ssa_greedy_optimize(
            inputs,
            frozenset(),
            sizes,
            cost_fn=jittered_memory_removed if jitter else "memory-removed",
        )
        nleaves = len(network.leaves)
        if len(ssa_path) != nleaves - 1 or any(len(step) != 2 for step in ssa_path):
            raise ValueError("Generic einsum initializer did not return a full binary SSA path")
        left = [-1] * (2 * nleaves - 1)
        right = [-1] * (2 * nleaves - 1)
        parent = [-1] * (2 * nleaves - 1)
        for offset, (a, b) in enumerate(ssa_path):
            node = nleaves + offset
            left[node], right[node] = a, b
            parent[a] = parent[b] = node
        return cls(network, left, right, parent, 2 * nleaves - 2)

    @classmethod
    def cotengra_initialized(
        cls,
        network: TensorNetwork,
        *,
        seed: int,
        repeats: int,
        subtree_size: int = 8,
    ) -> "ContractionTree":
        """Generate a high-quality generic contraction tree.

        Cotengra is an unrelated, general-purpose tensor-network optimizer.  It
        sees only index sets and dimensions, never green labels or author plans.
        We use its FLOP-minimized tree as an initializer, then independently
        evaluate and optimize the paper's realification objective.
        """

        import cotengra as ctg

        optimizer = ctg.HyperOptimizer(
            methods=["greedy"],
            minimize="flops",
            max_repeats=repeats,
            parallel=False,
            progbar=False,
            reconf_opts={"subtree_size": subtree_size},
            optlib="random",
            seed=seed,
            on_trial_error="raise",
        )
        tree = optimizer.search(
            [tuple(sorted(leaf.indices)) for leaf in network.leaves],
            (),
            {index: 2 for index in network.index_incidence},
        )
        ssa_path = tree.get_ssa_path()
        nleaves = len(network.leaves)
        if len(ssa_path) != nleaves - 1:
            raise ValueError("Cotengra initializer did not return a full binary SSA path")
        left = [-1] * (2 * nleaves - 1)
        right = [-1] * (2 * nleaves - 1)
        parent = [-1] * (2 * nleaves - 1)
        for offset, (a, b) in enumerate(ssa_path):
            node = nleaves + offset
            left[node], right[node] = a, b
            parent[a] = parent[b] = node
        result = cls(network, left, right, parent, 2 * nleaves - 2)
        # This equality is an independent cross-check of our hyperedge boundary
        # and loop-volume evaluator against a general einsum implementation.
        if result.skeleton_total != int(tree.total_flops()):
            raise ValueError(
                "Independent skeleton evaluator disagrees with cotengra: "
                f"{result.skeleton_total} != {tree.total_flops()}"
            )
        return result

    def clone(self) -> "ContractionTree":
        return ContractionTree(
            self.network,
            self.left.copy(),
            self.right.copy(),
            self.parent.copy(),
            self.root,
        )

    def _recompute_node(self, node: int) -> None:
        a, b = self.left[node], self.right[node]
        mask = self.leaf_mask[a] | self.leaf_mask[b]
        candidate_indices = self.boundary[a] | self.boundary[b]
        self.leaf_mask[node] = mask
        self.boundary[node] = frozenset(
            index
            for index in candidate_indices
            if self.index_masks[index] & mask != self.index_masks[index]
        )
        self.green[node] = self.green[a] or self.green[b]
        self.rank[node] = len(candidate_indices)
        self.volume[node] = 1 << self.rank[node]
        self.factor[node] = 3 if self.green[a] and self.green[b] else 2 if self.green[a] or self.green[b] else 1

    def recompute_all(self) -> None:
        # Contraction trees can be much deeper than Python's recursion limit
        # (Sycamore has 1764 leaves), so all production traversals are explicit.
        stack: list[tuple[int, bool]] = [(self.root, False)]
        while stack:
            node, expanded = stack.pop()
            if node < self.nleaves:
                continue
            if expanded:
                self._recompute_node(node)
            else:
                stack.append((node, True))
                stack.append((self.right[node], False))
                stack.append((self.left[node], False))
        self.skeleton_total = sum(self.volume[self.nleaves :])
        self.real_total = sum(
            self.volume[node] * self.factor[node]
            for node in range(self.nleaves, len(self.left))
        )
        self.validate()

    def validate(self) -> None:
        if self.parent[self.root] != -1:
            raise ValueError("Contraction-tree root has a parent")
        seen: set[int] = set()
        leaves = 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node in seen:
                raise ValueError("Contraction tree contains a cycle")
            seen.add(node)
            if node < self.nleaves:
                leaves += 1
                continue
            a, b = self.left[node], self.right[node]
            if a < 0 or b < 0 or self.parent[a] != node or self.parent[b] != node:
                raise ValueError(f"Invalid child/parent relation at node {node}")
            stack.append(b)
            stack.append(a)
        if leaves != self.nleaves or len(seen) != 2 * self.nleaves - 1:
            raise ValueError("Contraction tree does not span every leaf exactly once")
        if self.boundary[self.root]:
            raise ValueError(f"Closed contraction root has boundary {sorted(self.boundary[self.root])[:8]}")

    def objective(self, objective: Objective) -> int:
        return self.skeleton_total if objective == "skeleton" else self.real_total

    def statistics(self) -> TreeStatistics:
        pass_volume = ride_volume = merge_volume = 0
        pass_nodes = ride_nodes = merge_nodes = 0
        peak_rank = 0
        for node in range(self.nleaves, len(self.left)):
            volume = self.volume[node]
            peak_rank = max(peak_rank, len(self.boundary[node]))
            factor = self.factor[node]
            if factor == 1:
                pass_nodes += 1
                pass_volume += volume
            elif factor == 2:
                ride_nodes += 1
                ride_volume += volume
            else:
                merge_nodes += 1
                merge_volume += volume
        return TreeStatistics(
            base_volume=self.skeleton_total,
            real_volume=self.real_total,
            pass_volume=pass_volume,
            ride_volume=ride_volume,
            merge_volume=merge_volume,
            pass_nodes=pass_nodes,
            ride_nodes=ride_nodes,
            merge_nodes=merge_nodes,
            peak_rank=peak_rank,
        )

    def plan_record(self) -> dict[str, Any]:
        children = [
            [self.left[node], self.right[node]]
            for node in range(self.nleaves, len(self.left))
        ]
        canonical = json.dumps(
            {"root": self.root, "children": children},
            separators=(",", ":"),
        ).encode()
        maximum_depth = 0
        stack = [(self.root, 0)]
        while stack:
            node, depth = stack.pop()
            maximum_depth = max(maximum_depth, depth)
            if node >= self.nleaves:
                stack.append((self.left[node], depth + 1))
                stack.append((self.right[node], depth + 1))
        return {
            "format": "binary-tree-child-pairs-v1",
            "leaf_count": self.nleaves,
            "root": self.root,
            "children": children,
            "maximum_depth": maximum_depth,
            "sha256": hashlib.sha256(canonical).hexdigest(),
        }

    def anneal(
        self,
        objective: Objective,
        *,
        steps: int,
        seed: int,
        temperature_start: float = 1.0,
        temperature_end: float = 0.005,
    ) -> dict[str, int | float]:
        if steps < 0:
            raise ValueError("Annealing steps must be nonnegative")
        if temperature_start <= 0 or temperature_end <= 0:
            raise ValueError("Annealing temperatures must be positive")
        if steps == 0:
            value = self.objective(objective)
            return {"initial": value, "best": value, "accepted": 0, "improved": 0}

        rng = random.Random(seed)
        eligible = tuple(node for node in range(self.nleaves, len(self.left)) if node != self.root)
        initial = current = self.objective(objective)
        best = current
        best_left = self.left.copy()
        best_right = self.right.copy()
        best_parent = self.parent.copy()
        accepted = improved = 0
        log_ratio = math.log(temperature_end / temperature_start)

        for step in range(steps):
            child = eligible[rng.randrange(len(eligible))]
            parent = self.parent[child]
            if parent < self.nleaves:
                raise RuntimeError("An internal node cannot have a leaf parent")
            if self.left[parent] == child:
                sibling = self.right[parent]
                child_on_left = True
            elif self.right[parent] == child:
                sibling = self.left[parent]
                child_on_left = False
            else:
                raise RuntimeError("Broken parent relation during NNI")
            a, b = self.left[child], self.right[child]
            swapped, retained = (a, b) if rng.random() < 0.5 else (b, a)

            snapshot = (
                self.left[child], self.right[child], self.left[parent], self.right[parent],
                self.parent[sibling], self.parent[swapped],
                self.leaf_mask[child], self.boundary[child], self.green[child],
                self.volume[child], self.factor[child], self.rank[child],
                self.leaf_mask[parent], self.boundary[parent], self.green[parent],
                self.volume[parent], self.factor[parent], self.rank[parent],
                self.skeleton_total, self.real_total,
            )
            old_local_skeleton = self.volume[child] + self.volume[parent]
            old_local_real = (
                self.volume[child] * self.factor[child]
                + self.volume[parent] * self.factor[parent]
            )

            self.left[child], self.right[child] = sibling, retained
            self.parent[sibling] = child
            if child_on_left:
                self.left[parent], self.right[parent] = swapped, child
            else:
                self.left[parent], self.right[parent] = child, swapped
            self.parent[swapped] = parent
            self._recompute_node(child)
            self._recompute_node(parent)
            new_local_skeleton = self.volume[child] + self.volume[parent]
            new_local_real = (
                self.volume[child] * self.factor[child]
                + self.volume[parent] * self.factor[parent]
            )
            proposed_skeleton = self.skeleton_total - old_local_skeleton + new_local_skeleton
            proposed_real = self.real_total - old_local_real + new_local_real
            proposed = proposed_skeleton if objective == "skeleton" else proposed_real

            temperature = temperature_start * math.exp(log_ratio * step / max(1, steps - 1))
            log_delta = math.log2(proposed) - math.log2(current)
            accept = log_delta <= 0 or rng.random() < math.exp(-log_delta / temperature)
            if accept:
                accepted += 1
                self.skeleton_total = proposed_skeleton
                self.real_total = proposed_real
                current = proposed
                if current < best:
                    improved += 1
                    best = current
                    best_left = self.left.copy()
                    best_right = self.right.copy()
                    best_parent = self.parent.copy()
            else:
                (
                    self.left[child], self.right[child], self.left[parent], self.right[parent],
                    self.parent[sibling], self.parent[swapped],
                    self.leaf_mask[child], self.boundary[child], self.green[child],
                    self.volume[child], self.factor[child], self.rank[child],
                    self.leaf_mask[parent], self.boundary[parent], self.green[parent],
                    self.volume[parent], self.factor[parent], self.rank[parent],
                    self.skeleton_total, self.real_total,
                ) = snapshot

        self.left = best_left
        self.right = best_right
        self.parent = best_parent
        self.recompute_all()
        return {
            "initial": initial,
            "best": best,
            "accepted": accepted,
            "improved": improved,
            "steps": steps,
            "seed": seed,
            "temperature_start": temperature_start,
            "temperature_end": temperature_end,
        }


def _cotengra_candidate_trees(
    network: TensorNetwork,
    *,
    trials: int,
    seed_base: int,
) -> list[ContractionTree]:
    if trials < 1:
        raise ValueError("At least one greedy trial is required")
    import cotengra as ctg

    class RecordingOptimizer(ctg.HyperOptimizer):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.ssa_paths: list[tuple[tuple[int, int], ...]] = []

        def _maybe_report_result(self, setting: Any, trial: dict[str, Any]) -> None:
            if "tree" in trial:
                self.ssa_paths.append(tuple(trial["tree"].get_ssa_path()))
            super()._maybe_report_result(setting, trial)

    optimizer = RecordingOptimizer(
        methods=["greedy"],
        minimize="flops",
        max_repeats=trials,
        parallel=False,
        progbar=False,
        reconf_opts={"subtree_size": 8},
        optlib="random",
        seed=seed_base,
        on_trial_error="raise",
    )
    global_random_state = random.getstate()
    random.seed(seed_base)
    try:
        optimizer.search(
            [tuple(sorted(leaf.indices)) for leaf in network.leaves],
            (),
            {index: 2 for index in network.index_incidence},
        )
    finally:
        random.setstate(global_random_state)

    nleaves = len(network.leaves)
    candidates: list[ContractionTree] = []
    for trial, path in enumerate(optimizer.ssa_paths):
        if len(path) != nleaves - 1:
            raise ValueError("Cotengra initializer did not return a full binary SSA path")
        left = [-1] * (2 * nleaves - 1)
        right = [-1] * (2 * nleaves - 1)
        parent = [-1] * (2 * nleaves - 1)
        for offset, (a, b) in enumerate(path):
            node = nleaves + offset
            left[node], right[node] = a, b
            parent[a] = parent[b] = node
        tree = ContractionTree(network, left, right, parent, 2 * nleaves - 2)
        candidates.append(tree)
    if len(candidates) != trials:
        raise ValueError(f"Cotengra returned {len(candidates)} successful trials, expected {trials}")
    return candidates


def best_greedy_tree(
    network: TensorNetwork,
    objective: Objective,
    *,
    trials: int,
    seed_base: int,
) -> tuple[ContractionTree, list[dict[str, int]]]:
    candidates = _cotengra_candidate_trees(
        network,
        trials=trials,
        seed_base=seed_base,
    )
    records = [
        {
            "trial": trial,
            "seed": seed_base,
            "objective": tree.objective(objective),
            "skeleton_volume": tree.skeleton_total,
            "real_volume": tree.real_total,
            "cotengra_repeats": trials,
        }
        for trial, tree in enumerate(candidates)
    ]
    best = min(candidates, key=lambda tree: tree.objective(objective))
    return best, records


def optimize_network(
    network: TensorNetwork,
    *,
    greedy_trials: int,
    anneal_steps: int,
    polish_steps: int,
    seed: int,
) -> dict[str, Any]:
    candidates = _cotengra_candidate_trees(
        network,
        trials=greedy_trials,
        seed_base=seed,
    )
    candidate_records = [
        {
            "trial": trial,
            "seed": seed,
            "skeleton_volume": tree.skeleton_total,
            "real_volume": tree.real_total,
            "cotengra_repeats": greedy_trials,
        }
        for trial, tree in enumerate(candidates)
    ]
    skeleton = min(candidates, key=lambda tree: tree.skeleton_total).clone()
    full = min(candidates, key=lambda tree: tree.real_total).clone()
    skeleton_anneal = skeleton.anneal(
        "skeleton", steps=anneal_steps, seed=seed + 1
    )
    convert_only = skeleton.statistics()

    polished = skeleton.clone()
    polish_anneal = polished.anneal(
        "real",
        steps=polish_steps,
        seed=seed + 2,
        temperature_start=0.02,
        temperature_end=0.0002,
    )

    full_anneal = full.anneal("real", steps=anneal_steps, seed=seed + 3)

    return {
        "network": {
            "name": network.name,
            "family": network.family,
            "source_kind": network.source_kind,
            "leaves": len(network.leaves),
            "green_leaves": network.green_leaves,
            "indices": len(network.index_incidence),
            "topology_sha256": network.topology_sha256,
        },
        "search": {
            "algorithm": "independent-python-greedy+nni-sa",
            "greedy_trials": greedy_trials,
            "anneal_steps": anneal_steps,
            "polish_steps": polish_steps,
            "seed": seed,
            "candidate_pool": candidate_records,
            "candidate_pool_shared_between_objectives": True,
            "skeleton_anneal": skeleton_anneal,
            "polish_anneal": polish_anneal,
            "full_anneal": full_anneal,
        },
        "convert_only": convert_only.as_dict(),
        "polished": polished.statistics().as_dict(),
        "full_anneal": full.statistics().as_dict(),
        "plans": {
            "convert_only": skeleton.plan_record(),
            "polished": polished.plan_record(),
            "full_anneal": full.plan_record(),
        },
    }


def exact_optimum(network: TensorNetwork, objective: Objective) -> tuple[int, ContractionTree]:
    """Enumerate every labeled binary-tree split for tiny validation networks.

    The dynamic program is exponential and intentionally restricted to at most
    14 leaves.  It provides an optimizer-independent oracle for unit tests.
    """

    nleaves = len(network.leaves)
    if nleaves > 14:
        raise ValueError("Exact tree optimization is limited to 14 leaves")
    full = (1 << nleaves) - 1
    index_masks: dict[int, int] = defaultdict(int)
    for leaf_id, leaf in enumerate(network.leaves):
        for index in leaf.indices:
            index_masks[index] |= 1 << leaf_id

    boundary_cache: dict[int, frozenset[int]] = {}
    green_cache: dict[int, bool] = {}
    for subset in range(1, full + 1):
        boundary_cache[subset] = frozenset(
            index
            for index, incident in index_masks.items()
            if incident & subset and incident & subset != incident
        )
        green_cache[subset] = any(
            network.leaves[leaf].green for leaf in range(nleaves) if subset & (1 << leaf)
        )

    costs: dict[int, int] = {1 << leaf: 0 for leaf in range(nleaves)}
    splits: dict[int, tuple[int, int]] = {}
    for size in range(2, nleaves + 1):
        for subset in range(1, full + 1):
            if subset.bit_count() != size:
                continue
            anchor = subset & -subset
            best_cost: int | None = None
            best_split: tuple[int, int] | None = None
            left_subset = (subset - 1) & subset
            while left_subset:
                right_subset = subset ^ left_subset
                if left_subset & anchor and right_subset and left_subset in costs and right_subset in costs:
                    rank = len(boundary_cache[left_subset] | boundary_cache[right_subset])
                    factor = 1
                    if objective == "real":
                        factor = (
                            3
                            if green_cache[left_subset] and green_cache[right_subset]
                            else 2
                            if green_cache[left_subset] or green_cache[right_subset]
                            else 1
                        )
                    candidate = costs[left_subset] + costs[right_subset] + factor * (1 << rank)
                    if best_cost is None or candidate < best_cost:
                        best_cost = candidate
                        best_split = (left_subset, right_subset)
                left_subset = (left_subset - 1) & subset
            assert best_cost is not None and best_split is not None
            costs[subset] = best_cost
            splits[subset] = best_split

    left = [-1] * (2 * nleaves - 1)
    right = [-1] * (2 * nleaves - 1)
    parent = [-1] * (2 * nleaves - 1)
    next_node = nleaves

    def materialize(subset: int) -> int:
        nonlocal next_node
        if subset.bit_count() == 1:
            return subset.bit_length() - 1
        a_subset, b_subset = splits[subset]
        a, b = materialize(a_subset), materialize(b_subset)
        node = next_node
        next_node += 1
        left[node], right[node] = a, b
        parent[a] = parent[b] = node
        return node

    root = materialize(full)
    tree = ContractionTree(network, left, right, parent, root)
    return costs[full], tree
