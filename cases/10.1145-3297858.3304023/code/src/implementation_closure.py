from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any

from benchmarks import paper_swap_example, qft_cnot_dependencies
from sabre import (
    Gate,
    identity_layout,
    random_layout,
    route_sabre,
    sabre_forward_backward_forward,
    square_4_graph,
    tokyo_20_graph,
)


ITEMS_BY_TARGET = {
    "T001": ("fig3d_routed_circuit",),
    "T002": ("fig4_dag_front_layer", "fig5_reverse_traversal", "fig6_swap_heuristic_search"),
    "T003": ("fig7_optimization_objectives", "fig8_gate_depth_tradeoff"),
    "T004": ("table2_benchmark_results",),
}

REQUIRED_TABLE2_INPUTS = (
    "benchmark_manifest",
    "qasm_corpus",
    "seed_and_attempt_policy",
    "tie_break_policy",
    "reverse_traversal_policy",
    "bka_baseline_definition",
)


def _attest_exact_swap(config: dict[str, Any]) -> dict[str, Any]:
    result = route_sabre(
        gates=paper_swap_example(),
        graph=square_4_graph(),
        initial_layout=identity_layout(4),
        extended_size=int(config["extended_size"]),
        lookahead_weight=float(config["lookahead_weight"]),
        use_decay=False,
    )
    passed = (
        result.hardware_compliant
        and len(result.swaps) == 1
        and result.additional_cnot_gates == 3
        and result.output_depth == 8
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "paper_text_exact_small_example",
        "paper_scale_executed": True,
        "inserted_swaps": len(result.swaps),
        "additional_cnot_equivalent_gates": result.additional_cnot_gates,
        "output_depth": result.output_depth,
        "hardware_compliant": result.hardware_compliant,
    }


def _attest_search_and_reverse(config: dict[str, Any]) -> dict[str, Any]:
    graph = tokyo_20_graph()
    gates = qft_cnot_dependencies(int(config["logical_qubits"]))
    initial_layout = random_layout(
        int(config["logical_qubits"]),
        graph.number_of_nodes(),
        random.Random(int(config["seed"])),
    )
    first = route_sabre(
        gates,
        graph,
        initial_layout,
        extended_size=int(config["extended_size"]),
        lookahead_weight=float(config["lookahead_weight"]),
        decay_delta=float(config["decay_delta"]),
        use_decay=True,
    )
    reverse = sabre_forward_backward_forward(
        gates,
        graph,
        attempts=int(config["attempts"]),
        seed=int(config["seed"]),
        extended_size=int(config["extended_size"]),
        lookahead_weight=float(config["lookahead_weight"]),
        decay_delta=float(config["decay_delta"]),
        use_decay=True,
    )
    passed = (
        first.hardware_compliant
        and reverse.hardware_compliant
        and reverse.additional_cnot_gates <= first.additional_cnot_gates
        and reverse.output_depth <= first.output_depth
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "logical_qubits": int(config["logical_qubits"]),
        "two_qubit_dependencies": len(gates),
        "first_traversal": {
            "additional_cnot_equivalent_gates": first.additional_cnot_gates,
            "output_depth": first.output_depth,
        },
        "forward_backward_forward": {
            "additional_cnot_equivalent_gates": reverse.additional_cnot_gates,
            "output_depth": reverse.output_depth,
        },
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _attest_decay_tradeoff(config: dict[str, Any]) -> dict[str, Any]:
    graph = tokyo_20_graph()
    rng = random.Random(int(config["circuit_seed"]))
    gates = [
        Gate(*rng.sample(range(int(config["logical_qubits"])), 2))
        for _ in range(int(config["two_qubit_gates"]))
    ]
    initial_layout = random_layout(
        int(config["logical_qubits"]),
        graph.number_of_nodes(),
        random.Random(int(config["layout_seed"])),
    )
    rows = []
    for delta in config["decay_deltas"]:
        result = route_sabre(
            gates,
            graph,
            list(initial_layout),
            extended_size=int(config["extended_size"]),
            lookahead_weight=float(config["lookahead_weight"]),
            decay_delta=float(delta),
            use_decay=float(delta) > 0.0,
        )
        rows.append(
            {
                "decay_delta": float(delta),
                "additional_cnot_equivalent_gates": result.additional_cnot_gates,
                "output_depth": result.output_depth,
                "hardware_compliant": result.hardware_compliant,
            }
        )
    baseline = rows[0]
    operating_points = {
        (row["additional_cnot_equivalent_gates"], row["output_depth"])
        for row in rows
    }
    strict_tradeoff = any(
        row["output_depth"] < baseline["output_depth"]
        and row["additional_cnot_equivalent_gates"]
        > baseline["additional_cnot_equivalent_gates"]
        for row in rows[1:]
    )
    passed = (
        all(row["hardware_compliant"] for row in rows)
        and len(operating_points) >= 2
        and strict_tradeoff
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "operating_points": rows,
        "unique_operating_points": len(operating_points),
        "strict_gate_depth_tradeoff_observed": strict_tradeoff,
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _validate_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == hashlib.sha256().digest_size * 2
        and all(character in "0123456789abcdef" for character in value.lower())
    )


def _attest_table2_input_boundary(config: dict[str, Any]) -> dict[str, Any]:
    declared = config.get("required_inputs")
    if not isinstance(declared, dict) or set(declared) != set(REQUIRED_TABLE2_INPUTS):
        raise ValueError("Table II required_inputs must declare the frozen six-field schema")
    missing = []
    invalid = []
    for name in REQUIRED_TABLE2_INPUTS:
        record = declared[name]
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "source_requirement"}:
            raise ValueError(f"{name} must contain path, sha256, and source_requirement")
        if not isinstance(record["source_requirement"], str) or not record["source_requirement"].strip():
            raise ValueError(f"{name}.source_requirement must be non-empty")
        path = record["path"]
        digest = record["sha256"]
        if path is None and digest is None:
            missing.append(name)
        elif not isinstance(path, str) or not path.strip() or not _validate_sha256(digest):
            invalid.append(name)
    if invalid:
        raise ValueError(f"invalid Table II input records: {', '.join(invalid)}")
    if not missing:
        raise ValueError(
            "All Table II inputs are populated; use a dedicated paper-scale contract rather than this blocker attestation"
        )
    return {
        "status": "input_blocked",
        "profile": "strict_input_boundary",
        "paper_scale_executed": False,
        "missing_indispensable_inputs": missing,
        "blocked_artifact_valid": True,
        "scientific_coverage_changed": False,
        "boundary": config["boundary"],
    }


def run_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if config.get("paper_id") != "10.1145-3297858.3304023":
        raise ValueError("paper_id must be 10.1145-3297858.3304023")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    target_checks = {
        "T001": _attest_exact_swap(parameters["T001"]),
        "T002": _attest_search_and_reverse(parameters["T002"]),
        "T003": _attest_decay_tradeoff(parameters["T003"]),
        "T004": _attest_table2_input_boundary(parameters["T004"]),
    }
    accepted_statuses = {"passed", "input_blocked"}
    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": (
                "attested"
                if target_checks[target_id]["status"] in accepted_statuses
                else "failed"
            ),
            "scientific_coverage_changed": False,
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    status = (
        "passed"
        if all(check["status"] in accepted_statuses for check in target_checks.values())
        else "failed"
    )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "profile": "mixed_exact_reduced_and_blocked_attestation",
        "fixed_item_denominator": len(item_results),
        "item_results": item_results,
        "target_checks": target_checks,
        "scientific_coverage_changed": False,
        "numerical_input_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "reference_pixels_read": False,
        },
    }
