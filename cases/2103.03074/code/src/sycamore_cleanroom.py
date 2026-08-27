"""Independent Sycamore circuit ingestion and falsification helpers.

The only paper-specific numerical inputs accepted by this module are the
frozen QSIM text files declared in ``config/scientific_closure.json``.  It
never reads the paper, source figures, author code, or author result arrays.

The 53-qubit contractions are deliberately resource guarded.  We build and
simplify the exact tensor networks and run a bounded, independent path search,
but do not start a contraction whose estimated memory or work exceeds the
declared local budget.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
import random
import resource
import shutil
import sys
import time
from typing import Any, Iterable, Sequence

import numpy as np


ONE_QUBIT_GATES = frozenset({"x_1_2", "y_1_2", "hz_1_2", "rz"})
TWO_QUBIT_GATES = frozenset({"fs"})
SUPPORTED_GATES = ONE_QUBIT_GATES | TWO_QUBIT_GATES


@dataclass(frozen=True)
class Gate:
    moment: int
    name: str
    qubits: tuple[int, ...]
    parameters: tuple[float, ...] = ()


@dataclass(frozen=True)
class CircuitSpec:
    source_path: Path
    sha256: str
    n_qubits: int
    gates: tuple[Gate, ...]

    @property
    def moments(self) -> int:
        return max((gate.moment for gate in self.gates), default=-1) + 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_qsim(path: Path, *, expected_sha256: str | None = None) -> CircuitSpec:
    """Parse the public QSIM format with a strict, small gate vocabulary."""

    actual_sha256 = sha256_file(path)
    if expected_sha256 and actual_sha256 != expected_sha256:
        raise ValueError(
            f"QSIM digest mismatch for {path}: {actual_sha256} != {expected_sha256}"
        )
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"empty QSIM file: {path}")
    try:
        n_qubits = int(lines[0].strip())
    except ValueError as exc:
        raise ValueError(f"invalid QSIM qubit-count line in {path}") from exc
    if n_qubits <= 0:
        raise ValueError("QSIM qubit count must be positive")

    gates: list[Gate] = []
    previous_moment = -1
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split()
        if len(fields) < 3:
            raise ValueError(f"{path}:{line_number}: incomplete gate line")
        try:
            moment = int(fields[0])
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: invalid moment") from exc
        if moment < previous_moment:
            raise ValueError(f"{path}:{line_number}: moments are not monotonic")
        previous_moment = moment
        name = fields[1]
        if name not in SUPPORTED_GATES:
            raise ValueError(f"{path}:{line_number}: unsupported gate {name!r}")
        try:
            if name in {"x_1_2", "y_1_2", "hz_1_2"}:
                if len(fields) != 3:
                    raise ValueError("one-qubit gate must have three fields")
                qubits = (int(fields[2]),)
                parameters: tuple[float, ...] = ()
            elif name == "rz":
                if len(fields) != 4:
                    raise ValueError("rz gate must have four fields")
                qubits = (int(fields[2]),)
                parameters = (float(fields[3]),)
            else:
                if len(fields) != 6:
                    raise ValueError("fs gate must have six fields")
                qubits = (int(fields[2]), int(fields[3]))
                parameters = (float(fields[4]), float(fields[5]))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: invalid gate fields") from exc
        if len(set(qubits)) != len(qubits):
            raise ValueError(f"{path}:{line_number}: repeated qubit")
        if any(qubit < 0 or qubit >= n_qubits for qubit in qubits):
            raise ValueError(f"{path}:{line_number}: qubit outside 0..{n_qubits - 1}")
        gates.append(Gate(moment, name, qubits, parameters))

    return CircuitSpec(path, actual_sha256, n_qubits, tuple(gates))


def gate_matrix(
    gate: Gate, *, dtype: np.dtype[Any] = np.dtype(np.complex128)
) -> np.ndarray:
    """Return the qsim gate matrix using the public qsim conventions."""

    # qsim's ``h_double`` is 0.5 for the pi/2 rotations.  HZ additionally
    # uses ``is2_double = 1/sqrt(2)`` in its off-diagonal entries.
    half = 0.5
    inverse_sqrt_two = 1.0 / math.sqrt(2.0)
    if gate.name == "x_1_2":
        matrix = np.array(
            [
                [half + 1j * half, half - 1j * half],
                [half - 1j * half, half + 1j * half],
            ]
        )
    elif gate.name == "y_1_2":
        matrix = np.array(
            [
                [half + 1j * half, -half - 1j * half],
                [half + 1j * half, half + 1j * half],
            ]
        )
    elif gate.name == "hz_1_2":
        matrix = np.array(
            [
                [half + 1j * half, -1j * inverse_sqrt_two],
                [inverse_sqrt_two, half + 1j * half],
            ]
        )
    elif gate.name == "rz":
        (angle,) = gate.parameters
        matrix = np.diag([np.exp(-0.5j * angle), np.exp(0.5j * angle)])
    elif gate.name == "fs":
        theta, phi = gate.parameters
        cosine = math.cos(theta)
        sine = -1j * math.sin(theta)
        matrix = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, cosine, sine, 0.0],
                [0.0, sine, cosine, 0.0],
                [0.0, 0.0, 0.0, np.exp(-1j * phi)],
            ]
        )
    else:  # pragma: no cover - parser closes this branch
        raise ValueError(f"unsupported gate {gate.name!r}")
    return matrix.astype(dtype)


def gate_unitarity_residual(gate: Gate) -> float:
    matrix = gate_matrix(gate)
    identity = np.eye(matrix.shape[0], dtype=np.complex128)
    return float(np.max(np.abs(matrix.conj().T @ matrix - identity)))


def circuit_inventory(spec: CircuitSpec) -> dict[str, Any]:
    gate_counts = {
        name: sum(gate.name == name for gate in spec.gates)
        for name in sorted(SUPPORTED_GATES)
    }
    representative: dict[str, Gate] = {}
    for gate in spec.gates:
        representative.setdefault(gate.name, gate)
    return {
        "sha256": spec.sha256,
        "n_qubits": spec.n_qubits,
        "gate_lines": len(spec.gates),
        "moments": spec.moments,
        "gate_counts": gate_counts,
        "max_representative_unitarity_residual": max(
            gate_unitarity_residual(gate) for gate in representative.values()
        ),
    }


def _build_quimb_circuit(spec: CircuitSpec, *, dtype: np.dtype[Any]) -> Any:
    import quimb.tensor as qtn

    circuit = qtn.Circuit(spec.n_qubits)
    for gate in spec.gates:
        circuit.apply_gate(gate_matrix(gate, dtype=dtype), *gate.qubits)
    return circuit


def simplified_network(
    spec: CircuitSpec,
    *,
    open_qubits: Sequence[int] = (),
    dtype: np.dtype[Any] = np.dtype(np.complex128),
) -> tuple[Any, dict[str, Any]]:
    """Build an exact-circuit TN and perform value-preserving simplification."""

    start = time.perf_counter()
    circuit = _build_quimb_circuit(spec, dtype=dtype)
    build_seconds = time.perf_counter() - start
    open_set = set(open_qubits)
    if any(qubit < 0 or qubit >= spec.n_qubits for qubit in open_set):
        raise ValueError("open-qubit id outside circuit")

    start = time.perf_counter()
    if open_qubits:
        closed_qubits = [q for q in range(spec.n_qubits) if q not in open_set]
        output_inds = [circuit.psi.site_ind(q) for q in open_qubits]
        network = circuit.psi.isel({circuit.psi.site_ind(q): 0 for q in closed_qubits})
        network.full_simplify_(
            seq="ADCRS",
            output_inds=output_inds,
            atol=1e-12,
            equalize_norms=True,
        )
    else:
        network = circuit.amplitude_tn(
            "0" * spec.n_qubits,
            simplify_sequence="ADCRS",
            simplify_atol=1e-12,
            simplify_equalize_norms=True,
            rehearse="tn",
        )
    simplify_seconds = time.perf_counter() - start
    return network, {
        "build_seconds": build_seconds,
        "simplify_seconds": simplify_seconds,
        "simplified_tensors": int(network.num_tensors),
        "simplified_indices": int(network.num_indices),
        "outer_indices": int(len(network.outer_inds())),
        "maximum_bond_dimension": int(network.max_bond()),
    }


def bounded_path_search(
    network: Any,
    *,
    max_time_seconds: float,
    max_repeats: int,
    target_size_exponent: int,
    seed: int,
) -> dict[str, Any]:
    """Run a real path search, then slice only the symbolic contraction tree."""

    import cotengra as ctg

    inputs, output, size_dict = network.get_inputs_output_size_dict()
    random.seed(seed)
    np.random.seed(seed)
    start = time.perf_counter()
    optimizer = ctg.HyperOptimizer(
        methods=["random-greedy"],
        minimize="combo-64",
        max_repeats=max_repeats,
        max_time=max_time_seconds,
        parallel=False,
        progbar=False,
    )
    tree = optimizer.search(inputs, output, size_dict)
    search_seconds = time.perf_counter() - start
    start = time.perf_counter()
    sliced = tree.slice(target_size=2**target_size_exponent, seed=seed)
    slicing_seconds = time.perf_counter() - start
    return {
        "method": "cotengra_random_greedy_combo64",
        "max_time_seconds": max_time_seconds,
        "max_repeats": max_repeats,
        "search_seconds": search_seconds,
        "unsliced_log10_complexity": float(tree.contraction_cost(log=10)),
        "unsliced_log2_max_tensor_elements": float(tree.max_size(log=2)),
        "target_log2_max_tensor_elements": target_size_exponent,
        "slicing_seconds": slicing_seconds,
        "sliced_log10_complexity": float(sliced.contraction_cost(log=10)),
        "sliced_log2_max_tensor_elements": float(sliced.max_size(log=2)),
        "sliced_indices": int(len(sliced.sliced_inds)),
        "log2_subtasks": float(math.log2(sliced.nslices)),
        "subtasks": int(sliced.nslices),
        "full_contraction_started": False,
        "resource_guard": "symbolic_path_only_when_estimate_exceeds_local_budget",
    }


def paper_scale_attempt(
    spec: CircuitSpec,
    *,
    open_qubits: Sequence[int],
    expected_fixed_amplitude_nodes: int,
    path_settings: dict[str, Any],
) -> dict[str, Any]:
    inventory = circuit_inventory(spec)
    fixed_network, fixed_stats = simplified_network(spec)
    batch_network, batch_stats = simplified_network(spec, open_qubits=open_qubits)
    path = bounded_path_search(
        batch_network,
        max_time_seconds=float(path_settings["max_time_seconds"]),
        max_repeats=int(path_settings["max_repeats"]),
        target_size_exponent=int(path_settings["target_size_exponent"]),
        seed=int(path_settings["seed"]),
    )
    node_count_matches = (
        fixed_stats["simplified_tensors"] == expected_fixed_amplitude_nodes
    )
    return {
        "circuit": inventory,
        "open_qubits": list(open_qubits),
        "closed_qubits": [q for q in range(spec.n_qubits) if q not in open_qubits],
        "batch_size": 2 ** len(open_qubits),
        "fixed_amplitude_network": fixed_stats,
        "expected_fixed_amplitude_nodes": expected_fixed_amplitude_nodes,
        "fixed_amplitude_node_count_matches": node_count_matches,
        "batch_network": batch_stats,
        "bounded_path_attempt": path,
        "scientific_result_status": "paper_scale_network_and_path_attempted_no_amplitudes_contracted",
    }


def _apply_gate_dense(
    state: np.ndarray,
    matrix: np.ndarray,
    qubits: Sequence[int],
    n_qubits: int,
) -> np.ndarray:
    tensor = state.reshape((2,) * n_qubits)
    front = tuple(qubits)
    rest = tuple(q for q in range(n_qubits) if q not in front)
    permutation = front + rest
    inverse = np.argsort(permutation)
    front_tensor = np.transpose(tensor, permutation).reshape(2 ** len(front), -1)
    updated = (matrix @ front_tensor).reshape(
        (2,) * len(front) + (2,) * (n_qubits - len(front))
    )
    return np.transpose(updated, inverse).reshape(-1)


def remapped_subcircuit(spec: CircuitSpec, qubits: Sequence[int]) -> tuple[Gate, ...]:
    """Select only gates wholly inside a declared reduced subsystem."""

    mapping = {qubit: index for index, qubit in enumerate(qubits)}
    return tuple(
        Gate(
            gate.moment,
            gate.name,
            tuple(mapping[q] for q in gate.qubits),
            gate.parameters,
        )
        for gate in spec.gates
        if all(q in mapping for q in gate.qubits)
    )


def simulate_gates(
    gates: Iterable[Gate],
    *,
    n_qubits: int,
    dtype: np.dtype[Any],
    initial: np.ndarray | None = None,
) -> np.ndarray:
    if initial is None:
        state = np.zeros(2**n_qubits, dtype=dtype)
        state[0] = 1.0
    else:
        state = np.asarray(initial, dtype=dtype).copy()
    for gate in gates:
        state = _apply_gate_dense(
            state,
            gate_matrix(gate, dtype=dtype),
            gate.qubits,
            n_qubits,
        ).astype(dtype, copy=False)
    return state


def reduced_precision_check(
    spec: CircuitSpec, *, qubits: Sequence[int]
) -> dict[str, Any]:
    gates = remapped_subcircuit(spec, qubits)
    state128 = simulate_gates(
        gates, n_qubits=len(qubits), dtype=np.dtype(np.complex128)
    )
    state64 = simulate_gates(
        gates, n_qubits=len(qubits), dtype=np.dtype(np.complex64)
    ).astype(np.complex128)
    probability128 = np.abs(state128) ** 2
    probability64 = np.abs(state64) ** 2
    norm128 = float(np.vdot(state128, state128).real)
    norm64 = float(np.vdot(state64, state64).real)
    overlap = np.vdot(state128, state64)
    normalized_state_fidelity = float(abs(overlap) ** 2 / (norm128 * norm64))
    return {
        "subsystem_qubits": list(qubits),
        "retained_gate_count": len(gates),
        "discarded_cross_boundary_or_outside_gate_count": len(spec.gates) - len(gates),
        "maximum_amplitude_error": float(np.max(np.abs(state128 - state64))),
        "l2_state_error": float(np.linalg.norm(state128 - state64)),
        "relative_l2_state_error": float(
            np.linalg.norm(state128 - state64) / np.linalg.norm(state128)
        ),
        "maximum_probability_error": float(
            np.max(np.abs(probability128 - probability64))
        ),
        "l1_probability_error": float(np.sum(np.abs(probability128 - probability64))),
        "complex128_norm": norm128,
        "complex64_norm": norm64,
        "normalized_state_fidelity": normalized_state_fidelity,
        "complex64_itemsize_bytes": int(np.dtype(np.complex64).itemsize),
        "complex128_itemsize_bytes": int(np.dtype(np.complex128).itemsize),
        "scope": "official_gate_reduced_subsystem_not_paper_scale_precision_proof",
    }


def head_tail_factorization_check(
    spec: CircuitSpec, *, qubits: Sequence[int], output_index: int
) -> dict[str, Any]:
    gates = remapped_subcircuit(spec, qubits)
    split = len(gates) // 2
    head_gates = gates[:split]
    tail_gates = gates[split:]
    n_qubits = len(qubits)
    head = simulate_gates(head_gates, n_qubits=n_qubits, dtype=np.dtype(np.complex128))
    tail_row = np.empty(2**n_qubits, dtype=np.complex128)
    for basis_index in range(2**n_qubits):
        basis = np.zeros(2**n_qubits, dtype=np.complex128)
        basis[basis_index] = 1.0
        tail_row[basis_index] = simulate_gates(
            tail_gates,
            n_qubits=n_qubits,
            dtype=np.dtype(np.complex128),
            initial=basis,
        )[output_index]
    direct = simulate_gates(gates, n_qubits=n_qubits, dtype=np.dtype(np.complex128))[
        output_index
    ]
    factorized = np.dot(tail_row, head)
    return {
        "subsystem_qubits": list(qubits),
        "retained_gate_count": len(gates),
        "cut_dimension": int(head.size),
        "output_index": output_index,
        "direct_amplitude": [float(direct.real), float(direct.imag)],
        "factorized_amplitude": [float(factorized.real), float(factorized.imag)],
        "absolute_error": float(abs(direct - factorized)),
        "scope": "exact_identity_on_official_gate_reduced_subsystem",
    }


def head_tail_batch_reuse_check(
    spec: CircuitSpec, *, qubits: Sequence[int], output_indices: Sequence[int]
) -> dict[str, Any]:
    """Verify several amplitudes while constructing the head vector only once."""

    gates = remapped_subcircuit(spec, qubits)
    split = len(gates) // 2
    head_gates = gates[:split]
    tail_gates = gates[split:]
    n_qubits = len(qubits)
    dimension = 2**n_qubits
    selected = [int(index) for index in output_indices]
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("output_indices must be a non-empty unique sequence")
    if any(index < 0 or index >= dimension for index in selected):
        raise ValueError("output index outside the reduced state dimension")

    head = simulate_gates(head_gates, n_qubits=n_qubits, dtype=np.dtype(np.complex128))
    direct_state = simulate_gates(
        gates, n_qubits=n_qubits, dtype=np.dtype(np.complex128)
    )
    amplitudes: list[dict[str, Any]] = []
    for output_index in selected:
        tail_row = np.empty(dimension, dtype=np.complex128)
        for basis_index in range(dimension):
            basis = np.zeros(dimension, dtype=np.complex128)
            basis[basis_index] = 1.0
            tail_row[basis_index] = simulate_gates(
                tail_gates,
                n_qubits=n_qubits,
                dtype=np.dtype(np.complex128),
                initial=basis,
            )[output_index]
        direct = direct_state[output_index]
        factorized = np.dot(tail_row, head)
        amplitudes.append(
            {
                "output_index": output_index,
                "direct_amplitude": [float(direct.real), float(direct.imag)],
                "factorized_amplitude": [
                    float(factorized.real),
                    float(factorized.imag),
                ],
                "absolute_error": float(abs(direct - factorized)),
            }
        )
    return {
        "subsystem_qubits": list(qubits),
        "retained_gate_count": len(gates),
        "cut_dimension": dimension,
        "shared_head_contractions": 1,
        "tail_rows_contracted": len(selected),
        "amplitudes": amplitudes,
        "maximum_absolute_error": max(row["absolute_error"] for row in amplitudes),
        "scope": "exact_multi_amplitude_identity_on_official_gate_reduced_subsystem",
    }


def complex64_gemm_benchmark(*, size: int, repeats: int, seed: int) -> dict[str, Any]:
    """Measure a local dense complex64 kernel as an optimistic throughput bound."""

    rng = np.random.default_rng(seed)
    left = (
        rng.standard_normal((size, size), dtype=np.float32)
        + 1j * rng.standard_normal((size, size), dtype=np.float32)
    ).astype(np.complex64)
    right = (
        rng.standard_normal((size, size), dtype=np.float32)
        + 1j * rng.standard_normal((size, size), dtype=np.float32)
    ).astype(np.complex64)
    _ = left @ right
    durations: list[float] = []
    checksum = 0.0
    for _ in range(repeats):
        start = time.perf_counter()
        product = left @ right
        durations.append(time.perf_counter() - start)
        checksum += float(abs(product[0, 0]))
    median_seconds = float(np.median(durations))
    complex_flops = 8.0 * size**3
    peak_rss_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mib = (
        peak_rss_raw / 1024.0**2 if sys.platform == "darwin" else peak_rss_raw / 1024.0
    )
    return {
        "kernel": "numpy_complex64_square_gemm",
        "matrix_size": size,
        "repeats": repeats,
        "durations_seconds": durations,
        "median_seconds": median_seconds,
        "complex_flop_convention": "8*N^3_matching_paper_complex_multiply_add_count",
        "measured_flops_per_second": complex_flops / median_seconds,
        "checksum": checksum,
        "peak_rss_mib": peak_rss_mib,
        "platform": sys.platform,
        "machine": os.uname().machine,
        "os_release": os.uname().release,
        "interpretation": "optimistic_local_dense_kernel_bound_not_A100_or_V100_measurement",
    }


def gpu_efficiency(
    time_complexity: float, capacity_flops: float, seconds: float
) -> float:
    return 8.0 * time_complexity / (capacity_flops * seconds)


def one_device_days(subtasks: int, seconds_per_subtask: float) -> float:
    return subtasks * seconds_per_subtask / 86400.0


def heterogeneous_cluster_days(
    subtasks: int,
    *,
    a100_count: int,
    a100_seconds: float,
    v100_count: int,
    v100_seconds: float,
) -> float:
    aggregate_rate = a100_count / a100_seconds + v100_count / v100_seconds
    return subtasks / aggregate_rate / 86400.0


def marginal_xeb_relation(
    *, marginal_probability: float, n_closed: int, n_open: int
) -> dict[str, Any]:
    total_qubits = n_closed + n_open
    batch_size = 2**n_open
    xeb_plus_one_from_equation_1 = (2**total_qubits) / batch_size * marginal_probability
    scaled_marginal = (2**n_closed) * marginal_probability
    return {
        "marginal_probability": marginal_probability,
        "n_closed": n_closed,
        "n_open": n_open,
        "total_qubits": total_qubits,
        "batch_size": batch_size,
        "equation_1_xeb_plus_one": xeb_plus_one_from_equation_1,
        "scaled_marginal": scaled_marginal,
        "equation_1_scaling_residual": xeb_plus_one_from_equation_1 - scaled_marginal,
        "equation_1_recovered_marginal": xeb_plus_one_from_equation_1 / (2**n_closed),
        "printed_prose_unscaled_residual": marginal_probability
        - xeb_plus_one_from_equation_1,
        "derived_identity": "F_XEB + 1 = 2^n_closed * P(s_closed)",
        "printed_prose_identity": "P(s_closed) = F_XEB + 1",
        "derivation": (
            "For L=2^n_open complete suffixes, Eq.(1) gives "
            "F_XEB+1=(2^(n_closed+n_open)/L)*sum_s_open P(s_closed,s_open)"
        ),
        "author_disposition": "evidence_only_fresh_review_required",
    }


def marginal_xeb_toy_check() -> dict[str, Any]:
    """Independent normalized example for the marginal/XEB scaling identity."""

    joint = np.asarray(
        [[0.05, 0.08, 0.12, 0.15], [0.07, 0.13, 0.18, 0.22]],
        dtype=np.float64,
    )
    n_closed = 1
    n_open = 2
    selected_prefix = 0
    marginal = float(np.sum(joint[selected_prefix]))
    conditional = joint[selected_prefix] / marginal
    relation = marginal_xeb_relation(
        marginal_probability=marginal,
        n_closed=n_closed,
        n_open=n_open,
    )
    return {
        "joint_normalization": float(np.sum(joint)),
        "selected_prefix": selected_prefix,
        "marginal_probability": marginal,
        "conditional_normalization": float(np.sum(conditional)),
        "equation_1_xeb_plus_one": relation["equation_1_xeb_plus_one"],
        "scaled_marginal": relation["scaled_marginal"],
        "scaling_residual": relation["equation_1_scaling_residual"],
        "unscaled_identity_residual": relation["printed_prose_unscaled_residual"],
        "input_origin": "deterministic_synthetic_distribution_not_author_data",
    }


def memory_arithmetic(
    *, rank: int, bytes_per_element: int, printed_tb: float
) -> dict[str, Any]:
    elements = 2**rank
    runtime_complex64_bytes = int(np.dtype(np.complex64).itemsize)
    bytes_total = elements * runtime_complex64_bytes
    decimal_tb = bytes_total / 1e12
    tib = bytes_total / 2**40
    return {
        "rank": rank,
        "elements": elements,
        "configured_bytes_per_element": bytes_per_element,
        "runtime_complex64_bytes_per_element": runtime_complex64_bytes,
        "dtype_definition_matches_config": runtime_complex64_bytes == bytes_per_element,
        "bytes_total": bytes_total,
        "decimal_tb": decimal_tb,
        "tebibytes": tib,
        "paper_printed_tb": printed_tb,
        "printed_to_decimal_ratio": printed_tb / decimal_tb,
        "printed_decimal_tb_residual": printed_tb - decimal_tb,
        "printed_binary_tib_residual": printed_tb - tib,
        "implied_decimal_bytes_per_element": printed_tb * 1e12 / elements,
        "implied_binary_bytes_per_element": printed_tb * 2**40 / elements,
        "rank_implied_by_printed_decimal_tb_at_complex64": float(
            np.log2(printed_tb * 1e12 / runtime_complex64_bytes)
        ),
        "identity": "memory_bytes = 2^rank * complex64_itemsize_bytes",
        "author_disposition": "evidence_only_fresh_review_required",
    }


def table3_square_check(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    checked: list[dict[str, Any]] = []
    for row in rows:
        amplitude_magnitude = float(row["amplitude_magnitude"])
        probability = float(row["probability"])
        squared = amplitude_magnitude**2
        checked.append(
            {
                **row,
                "amplitude_magnitude_squared": squared,
                "relative_residual": abs(squared - probability) / probability,
                "bitstring_length": len(str(row["bitstring"])),
            }
        )
    return {
        "rows": checked,
        "maximum_relative_rounding_residual": max(
            row["relative_residual"] for row in checked
        ),
        "phase_information_published": False,
        "exact_amplitudes_contracted": False,
        "scope": "printed_pair_internal_arithmetic_only_with_paper_scale_path_attempt_separate",
    }


def mixed_xeb_identity(
    *, top_count: int, random_count: int, target_xeb: float
) -> dict[str, Any]:
    total = top_count + random_count
    top_weight = top_count / total
    required_top_xeb = target_xeb / top_weight
    return {
        "top_count": top_count,
        "random_count": random_count,
        "total_count": total,
        "top_weight": top_weight,
        "target_mixture_xeb": target_xeb,
        "uniform_random_expected_xeb": 0.0,
        "required_top_subset_xeb": required_top_xeb,
        "required_top_mean_scaled_probability": required_top_xeb + 1.0,
        "identity": "F_mix = w_top * F_top when the random component has expected XEB zero",
        "exact_top_probabilities_available": False,
    }


def reduced_full_state_streaming_smoke(
    spec: CircuitSpec,
    *,
    qubits: Sequence[int],
    closed_qubits_count: int,
    histogram_bins: int,
    histogram_scaled_max: float,
    sample_count: int,
    seed: int,
) -> dict[str, Any]:
    """Exercise the complete streaming/full-state contract at a safe scale.

    The smoke uses only gates induced by a declared subsystem of a frozen public
    QSIM circuit.  It writes no source-derived arrays: amplitudes are generated
    independently, consumed once in deterministic batches, and represented by
    hashes plus numerical invariants.
    """

    selected_qubits = [int(qubit) for qubit in qubits]
    n_qubits = len(selected_qubits)
    if not selected_qubits or len(set(selected_qubits)) != n_qubits:
        raise ValueError("qubits must be a non-empty unique sequence")
    if closed_qubits_count <= 0 or closed_qubits_count >= n_qubits:
        raise ValueError("closed_qubits_count must split the reduced subsystem")
    if histogram_bins <= 1 or histogram_scaled_max <= 0.0:
        raise ValueError("histogram contract must have positive extent and bins")
    if sample_count < 2:
        raise ValueError("sample_count must be at least two")

    gates = remapped_subcircuit(spec, selected_qubits)
    started = time.perf_counter()
    state = simulate_gates(
        gates,
        n_qubits=n_qubits,
        dtype=np.dtype(np.complex64),
    )
    simulation_seconds = time.perf_counter() - started
    probabilities = np.abs(state.astype(np.complex128)) ** 2
    dimension = int(state.size)
    open_qubits_count = n_qubits - closed_qubits_count
    batch_count = 2**closed_qubits_count
    amplitudes_per_batch = 2**open_qubits_count

    stream_hash = hashlib.sha256()
    ledger: list[dict[str, Any]] = []
    for batch_index in range(batch_count):
        start = batch_index * amplitudes_per_batch
        stop = start + amplitudes_per_batch
        batch = np.asarray(state[start:stop], dtype="<c8")
        raw = batch.tobytes(order="C")
        batch_hash = hashlib.sha256(raw).hexdigest()
        stream_hash.update(raw)
        ledger.append(
            {
                "batch_index": batch_index,
                "start_amplitude": start,
                "stop_amplitude_exclusive": stop,
                "amplitude_count": amplitudes_per_batch,
                "sha256": batch_hash,
            }
        )

    scaled = dimension * probabilities
    edges = np.linspace(0.0, histogram_scaled_max, histogram_bins + 1)
    counts, _ = np.histogram(scaled, bins=edges)
    overflow = int(np.count_nonzero(scaled >= histogram_scaled_max))
    expected = dimension * (np.exp(-edges[:-1]) - np.exp(-edges[1:]))
    expected_overflow = float(dimension * np.exp(-histogram_scaled_max))
    ordered = np.sort(scaled)
    empirical_upper = np.arange(1, dimension + 1, dtype=np.float64) / dimension
    empirical_lower = np.arange(0, dimension, dtype=np.float64) / dimension
    theoretical = 1.0 - np.exp(-ordered)
    ks_distance = float(
        max(
            np.max(np.abs(empirical_upper - theoretical)),
            np.max(np.abs(empirical_lower - theoretical)),
        )
    )

    rng = np.random.default_rng(seed)
    normalized = probabilities / probabilities.sum()
    samples = rng.choice(dimension, size=sample_count, replace=True, p=normalized)
    lag_one_correlation = float(np.corrcoef(samples[:-1], samples[1:])[0, 1])
    correlation_limit = 4.0 / math.sqrt(sample_count - 1)
    sampled_xeb = float(dimension * np.mean(normalized[samples]) - 1.0)
    normalization = float(probabilities.sum())

    return {
        "scope": "official_qsim_reduced_subsystem_streaming_contract_smoke",
        "subsystem_qubits": selected_qubits,
        "retained_gate_count": len(gates),
        "n_qubits": n_qubits,
        "closed_qubits_count": closed_qubits_count,
        "open_qubits_count": open_qubits_count,
        "batch_count": batch_count,
        "amplitudes_per_batch": amplitudes_per_batch,
        "amplitudes_streamed": dimension,
        "simulation_seconds": simulation_seconds,
        "amplitudes_per_second": dimension / simulation_seconds,
        "complex64_stream_sha256": stream_hash.hexdigest(),
        "batch_ledger": ledger,
        "normalization": normalization,
        "normalization_error": abs(normalization - 1.0),
        "histogram": {
            "scaled_probability": "x=2^n*P(s)",
            "edges": edges.tolist(),
            "counts": counts.tolist(),
            "overflow_count": overflow,
            "porter_thomas_expected_counts": expected.tolist(),
            "porter_thomas_expected_overflow": expected_overflow,
            "kolmogorov_smirnov_distance": ks_distance,
            "interpretation": "diagnostic_only_at_reduced_scale",
        },
        "sampling": {
            "sample_count": sample_count,
            "seed": seed,
            "lag_one_index_correlation": lag_one_correlation,
            "predeclared_absolute_correlation_limit": correlation_limit,
            "correlation_check_passed": abs(lag_one_correlation)
            <= correlation_limit,
            "sampled_xeb": sampled_xeb,
        },
        "checks": {
            "batch_ledger_complete": sum(
                row["amplitude_count"] for row in ledger
            )
            == dimension,
            "normalization_passed": abs(normalization - 1.0) <= 2e-6,
            "sampling_correlation_passed": abs(lag_one_correlation)
            <= correlation_limit,
        },
    }


def noisy_fidelity_projection_smoke(
    spec: CircuitSpec,
    *,
    qubits: Sequence[int],
    target_fidelities: Sequence[float],
) -> dict[str, Any]:
    """Show why target fidelity alone does not determine a unique work law."""

    selected_qubits = [int(qubit) for qubit in qubits]
    gates = remapped_subcircuit(spec, selected_qubits)
    state = simulate_gates(
        gates,
        n_qubits=len(selected_qubits),
        dtype=np.dtype(np.complex128),
    )
    probabilities = np.abs(state) ** 2
    order = np.argsort(probabilities)[::-1]
    cumulative = np.cumsum(probabilities[order])
    rows: list[dict[str, Any]] = []
    for raw_fidelity in target_fidelities:
        fidelity = float(raw_fidelity)
        if not 0.0 < fidelity <= 1.0:
            raise ValueError("target fidelities must lie in (0, 1]")
        retained_count = int(np.searchsorted(cumulative, fidelity, side="left") + 1)
        achieved = float(cumulative[retained_count - 1])
        work_fraction = retained_count / state.size
        rows.append(
            {
                "target_fidelity": fidelity,
                "retained_amplitudes": retained_count,
                "total_amplitudes": int(state.size),
                "work_fraction_for_largest_mass_projection": work_fraction,
                "achieved_projective_fidelity": achieved,
                "fidelity_residual": achieved - fidelity,
            }
        )
    return {
        "scope": "independent_reduced_projection_counterexample_not_paper_method",
        "subsystem_qubits": selected_qubits,
        "retained_gate_count": len(gates),
        "rows": rows,
        "identity": "For a normalized projection, fidelity equals retained probability mass.",
        "paper_cost_law_uniquely_testable": False,
        "missing_method_contract": [
            "which amplitudes or tensor-network paths are discarded",
            "whether fidelity is state overlap, XEB fidelity, or another estimator",
            "how work is counted after approximation",
            "the meaning of the printed phrase reduced by a factor 1/f",
        ],
    }


def full_state_resource_contract(
    *,
    n_qubits: int,
    n_closed: int,
    n_open: int,
    bytes_per_amplitude: int,
    paper_gpu_count: int,
    paper_runtime_seconds: float,
    measured_local_flops_per_second: float,
    time_complexity_per_batch: float | None = None,
) -> dict[str, Any]:
    """Return the executable partition contract and fail-closed resource gate."""

    if n_closed + n_open != n_qubits:
        raise ValueError("closed/open partition must cover every qubit")
    if min(n_qubits, n_closed, n_open, bytes_per_amplitude, paper_gpu_count) <= 0:
        raise ValueError("resource-contract integers must be positive")
    batch_count = 2**n_closed
    amplitudes_per_batch = 2**n_open
    amplitudes_total = 2**n_qubits
    logical_output_bytes = amplitudes_total * bytes_per_amplitude
    disk = shutil.disk_usage(Path.cwd())
    total_time_complexity = (
        None
        if time_complexity_per_batch is None
        else batch_count * float(time_complexity_per_batch)
    )
    optimistic_local_days = (
        None
        if total_time_complexity is None
        else 8.0
        * total_time_complexity
        / measured_local_flops_per_second
        / 86400.0
    )
    return {
        "n_qubits": n_qubits,
        "n_closed": n_closed,
        "n_open": n_open,
        "batch_count": batch_count,
        "amplitudes_per_batch": amplitudes_per_batch,
        "amplitudes_total": amplitudes_total,
        "bytes_per_amplitude": bytes_per_amplitude,
        "logical_output_bytes": logical_output_bytes,
        "logical_output_tib": logical_output_bytes / 2**40,
        "streaming_manifest": {
            "one_ledger_row_per_closed_configuration": True,
            "one_hash_per_batch": True,
            "rolling_full_stream_sha256": True,
            "normalization_accumulator": True,
            "histogram_accumulator": True,
            "persistent_full_vector_required": False,
        },
        "paper_hardware": {
            "gpu_count": paper_gpu_count,
            "runtime_seconds": paper_runtime_seconds,
            "gpu_days": paper_gpu_count * paper_runtime_seconds / 86400.0,
        },
        "time_complexity_per_batch": time_complexity_per_batch,
        "total_time_complexity": total_time_complexity,
        "complex_flop_convention": "8*paper_time_complexity",
        "optimistic_local_dense_kernel_days": optimistic_local_days,
        "measured_local_flops_per_second": measured_local_flops_per_second,
        "local_disk_free_bytes_at_run": int(disk.free),
        "logical_output_to_local_free_disk_ratio": logical_output_bytes / disk.free,
        "paper_scale_execution_started": False,
        "paper_scale_guard": (
            "requires exact EFGH circuit parameters plus the declared GPU budget; "
            "the current isolated host is resource-incompatible"
        ),
    }
