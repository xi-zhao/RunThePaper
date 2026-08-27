"""Strict scientific-input boundary for the unpublished Fig. 3/9 inputs.

The paper's six-clause 3-SAT instance and ZX transformation contract are not
published.  This module makes the missing boundary executable without guessing
either input.  A complete external package can compile the clause Hamiltonian
through the independently implemented Möbius algebra; the ZX path produces a
normalized backend request because the publication does not identify an
extractor algorithm that can honestly be hard-coded in advance.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import mobius_compiler as mobius


class ScientificInputError(ValueError):
    """Raised when an external scientific package is incomplete or ambiguous."""


def _clauses(package: dict[str, Any]) -> list[dict[str, Any]]:
    raw = package.get("clauses")
    if not isinstance(raw, list) or not raw:
        raise ScientificInputError("clauses must be a non-empty list")
    clauses = []
    for index, clause in enumerate(raw):
        if not isinstance(clause, dict):
            raise ScientificInputError(f"clauses[{index}] must be an object")
        variables = clause.get("variables")
        negative = clause.get("negative_literals")
        if (
            not isinstance(variables, list)
            or len(variables) != 3
            or not all(isinstance(value, int) and not isinstance(value, bool) for value in variables)
            or len(set(variables)) != 3
            or any(value < 0 for value in variables)
        ):
            raise ScientificInputError(
                f"clauses[{index}].variables must contain three unique nonnegative integers"
            )
        if (
            not isinstance(negative, list)
            or not all(isinstance(value, int) and not isinstance(value, bool) for value in negative)
            or len(set(negative)) != len(negative)
            or not set(negative) <= set(variables)
        ):
            raise ScientificInputError(
                f"clauses[{index}].negative_literals must be a unique subset of variables"
            )
        clauses.append({"variables": sorted(variables), "negative_literals": sorted(negative)})
    return clauses


def _derived_terms(clauses: list[dict[str, Any]]) -> dict[mobius.Support, float]:
    term_sets = []
    for clause in clauses:
        variables = tuple(clause["variables"])
        negative = tuple(clause["negative_literals"])
        positive = tuple(value for value in variables if value not in set(negative))
        table = mobius.clause_phase_table(
            variables,
            positive_literals=positive,
            negative_literals=negative,
            phase=math.pi,
        )
        term_sets.append(mobius.mobius_inversion(table, variables))
    terms = mobius.merge_projector_terms(term_sets)
    for support, phase in terms.items():
        if len(support) > 3:
            raise ScientificInputError(f"unsupported derived support degree: {support}")
        if abs(abs(phase) - math.pi) > 1e-10:
            raise ScientificInputError(
                f"derived support {support} has non-Pauli phase {phase}; the declared compiler only accepts pi phases"
            )
    return terms


def _declared_order(package: dict[str, Any], supports: set[mobius.Support]) -> list[mobius.Support]:
    raw = package.get("native_gate_order")
    if not isinstance(raw, list) or not raw:
        raise ScientificInputError(
            "native_gate_order is required because the publication's within-block ordering is unpublished"
        )
    order = []
    for index, row in enumerate(raw):
        if (
            not isinstance(row, list)
            or not row
            or not all(isinstance(value, int) and not isinstance(value, bool) for value in row)
            or len(set(row)) != len(row)
            or any(value < 0 for value in row)
        ):
            raise ScientificInputError(
                f"native_gate_order[{index}] must be a non-empty list of unique nonnegative integers"
            )
        order.append(mobius.canonical_support(row))
    if len(order) != len(set(order)) or set(order) != supports:
        raise ScientificInputError(
            "native_gate_order must contain every independently derived nonzero support exactly once"
        )
    return order


def compile_three_sat_package(package: dict[str, Any]) -> dict[str, Any]:
    """Compile an explicit clause package to native and ZAP gate accounting."""

    clauses = _clauses(package)
    terms = _derived_terms(clauses)
    order = _declared_order(package, set(terms))
    name_by_degree = {1: "z", 2: "cz", 3: "ccz"}
    native = [(name_by_degree[len(support)], support) for support in order]
    zap = mobius.decompose_native_stream_to_zap(native)
    return {
        "model": "three_sat_mobius_compilation",
        "clause_count": len(clauses),
        "qubit_count": 1 + max(value for clause in clauses for value in clause["variables"]),
        "derived_support_count": len(terms),
        "native_gate_counts": mobius.gate_counts(native),
        "native_depth": mobius.asap_depth(native),
        "zap_gate_counts": mobius.gate_counts(zap),
        "zap_depth": mobius.asap_depth(zap),
        "native_gate_stream": [
            {"gate": gate, "support": list(support)} for gate, support in native
        ],
    }


def build_zx_backend_request(package: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize the external ZX transformation boundary."""

    compiled = compile_three_sat_package(package)
    extractor = package.get("extractor")
    if not isinstance(extractor, dict):
        raise ScientificInputError("extractor must be an object")
    required = ("tool_name", "version", "algorithm", "options")
    for field in required:
        value = extractor.get(field)
        if field == "options":
            if not isinstance(value, dict):
                raise ScientificInputError("extractor.options must be an object")
        elif not isinstance(value, str) or not value.strip():
            raise ScientificInputError(f"extractor.{field} must be a non-empty string")
    variants = package.get("variants")
    expected_items = {"fig3b_zx_no_insert", "fig9_zx_insert_diagnostic"}
    if not isinstance(variants, list) or {
        str(row.get("item_id") or "") for row in variants if isinstance(row, dict)
    } != expected_items:
        raise ScientificInputError("variants must declare exactly the Fig. 3(b) and Fig. 9 item ids")
    normalized = {
        "source_circuit": compiled["native_gate_stream"],
        "extractor": extractor,
        "variants": variants,
    }
    fingerprint = hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "model": "declared_external_zx_backend_request",
        "status": "ready_for_declared_external_backend",
        "request_sha256": fingerprint,
        "request": normalized,
        "scientific_result_present": False,
        "remaining_boundary": (
            "Execute the declared, independently sourced ZX backend and attest its version and options; "
            "the request itself is not a scientific result."
        ),
    }


def required_schema(target_id: str) -> list[str]:
    common = [
        "clauses[].variables",
        "clauses[].negative_literals",
        "native_gate_order[]",
    ]
    if target_id == "ZX_EXTRACTOR_INPUT_GAP":
        return common + [
            "extractor.tool_name",
            "extractor.version",
            "extractor.algorithm",
            "extractor.options",
            "variants[].item_id",
        ]
    if target_id in {"FIG3A_ZAP", "FIG3C_NATIVE"}:
        return common
    raise ScientificInputError(f"unsupported target_id: {target_id}")
