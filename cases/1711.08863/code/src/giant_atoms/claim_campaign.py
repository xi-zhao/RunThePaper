"""Reduced clean-room checks for the paper's three analytic claim families.

The implementation starts from the coefficient sums and phase constraints in
the paper.  It never reads the paper, reference figures, author code, author
arrays, or an earlier reproduction output at runtime.  The resulting artifacts
attest that claim-specific code exists and runs; they are not a fresh-context
review and therefore do not promote scientific coverage by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


@dataclass(frozen=True)
class Atom:
    """One giant atom represented by ordered waveguide connection points."""

    label: str
    positions: np.ndarray
    rates: np.ndarray


def _atom(label: str, positions: Iterable[float], rates: Iterable[float] | None = None) -> Atom:
    x = np.asarray(tuple(positions), dtype=np.float64)
    if x.ndim != 1 or x.size < 1 or not np.all(np.isfinite(x)):
        raise ValueError("positions must be a non-empty finite vector")
    if np.any(np.diff(x) <= 0.0):
        raise ValueError("connection positions must be strictly increasing")
    gamma = np.ones_like(x) if rates is None else np.asarray(tuple(rates), dtype=np.float64)
    if gamma.shape != x.shape or not np.all(np.isfinite(gamma)) or np.any(gamma <= 0.0):
        raise ValueError("rates must be finite, positive, and match positions")
    return Atom(label=label, positions=x, rates=gamma)


def individual_decay(atom: Atom) -> float:
    """Evaluate Eq. (S135) as the squared connection-phasor norm."""

    amplitude = np.sum(np.sqrt(atom.rates) * np.exp(1j * atom.positions))
    return float(abs(amplitude) ** 2)


def emission_amplitude(atom: Atom) -> complex:
    """Return the complex connection-point amplitude used in Eq. (S135)."""

    return complex(np.sum(np.sqrt(atom.rates) * np.exp(1j * atom.positions)))


def pair_coefficients(left: Atom, right: Atom) -> dict[str, float]:
    """Evaluate Eq. (2)'s exchange and collective-decay point-pair sums."""

    distance = np.abs(left.positions[:, None] - right.positions[None, :])
    weights = np.sqrt(left.rates[:, None] * right.rates[None, :])
    return {
        "exchange": float(0.5 * np.sum(weights * np.sin(distance))),
        "collective_decay": float(np.sum(weights * np.cos(distance))),
    }


def collective_decay_factorized(left: Atom, right: Atom) -> float:
    """Evaluate the factorized collective decay in Eqs. (S135)--(S137)."""

    return float(np.real(emission_amplitude(left) * np.conj(emission_amplitude(right))))


def topology(left: Atom, right: Atom) -> str:
    """Classify two connection-point sets as separate, nested, or braided."""

    if left.positions[-1] < right.positions[0] or right.positions[-1] < left.positions[0]:
        return "separate"

    def is_nested(inner: np.ndarray, outer: np.ndarray) -> bool:
        return any(
            outer[index] < inner[0] and inner[-1] < outer[index + 1]
            for index in range(len(outer) - 1)
        )

    if is_nested(left.positions, right.positions) or is_nested(right.positions, left.positions):
        return "nested"
    return "braided"


def chain_constraint_matrix(atom_count: int) -> np.ndarray:
    """Return Eqs. (S122)--(S127) for an N-atom protected chain."""

    if atom_count < 2:
        raise ValueError("atom_count must be at least two")
    matrix = np.zeros((atom_count, 2 * atom_count - 1), dtype=np.float64)
    matrix[0, 0:2] = 1.0
    matrix[-1, -2:] = 1.0
    for atom_index in range(1, atom_count - 1):
        start = 2 * atom_index - 1
        matrix[atom_index, start : start + 3] = 1.0
    return matrix


def all_to_all_constraint_matrix(atom_count: int) -> np.ndarray:
    """Return the zero-decay constraints for ordering 1..N,1..N."""

    if atom_count < 2:
        raise ValueError("atom_count must be at least two")
    matrix = np.zeros((atom_count, 2 * atom_count - 1), dtype=np.float64)
    for atom_index in range(atom_count):
        matrix[atom_index, atom_index : atom_index + atom_count] = 1.0
    return matrix


def _solve_chain_phases(atom_count: int, controls: np.ndarray) -> np.ndarray:
    matrix = chain_constraint_matrix(atom_count)
    control_columns = np.arange(1, 2 * atom_count - 2, 2)
    dependent_columns = np.arange(0, 2 * atom_count - 1, 2)
    if controls.shape != (atom_count - 1,):
        raise ValueError("controls must contain N-1 phases")
    rhs = np.full(atom_count, np.pi) - matrix[:, control_columns] @ controls
    phases = np.zeros(2 * atom_count - 1, dtype=np.float64)
    phases[control_columns] = controls
    phases[dependent_columns] = np.linalg.solve(matrix[:, dependent_columns], rhs)
    return phases


def _atoms_from_order(order: list[int], phases: np.ndarray) -> list[Atom]:
    positions = np.concatenate(([0.0], np.cumsum(phases)))
    atoms = []
    for atom_index in sorted(set(order)):
        atoms.append(_atom(str(atom_index), positions[np.asarray(order) == atom_index]))
    return atoms


def _chain_order(atom_count: int) -> list[int]:
    order = [0, 1, 0]
    for atom_index in range(2, atom_count):
        order.extend([atom_index, atom_index - 1])
    order.append(atom_count - 1)
    return order


def general_topology_result(tolerance: float) -> dict[str, Any]:
    """Exercise arbitrary connection counts and the topology implication."""

    cases = {
        "separate_three_point": (
            _atom("a", [0.0, 2.0 * np.pi / 3.0, 4.0 * np.pi / 3.0]),
            _atom("b", [2.0 * np.pi, 8.0 * np.pi / 3.0, 10.0 * np.pi / 3.0]),
        ),
        "nested_two_point": (
            _atom("a", [0.0, 3.0 * np.pi]),
            _atom("b", [np.pi, 2.0 * np.pi]),
        ),
        "braided_two_point": (
            _atom("a", [0.0, np.pi]),
            _atom("b", [np.pi / 2.0, 3.0 * np.pi / 2.0]),
        ),
    }
    rows = []
    for case_id, (left, right) in cases.items():
        coefficients = pair_coefficients(left, right)
        factorized = collective_decay_factorized(left, right)
        rows.append(
            {
                "case_id": case_id,
                "topology": topology(left, right),
                "left_points": int(left.positions.size),
                "right_points": int(right.positions.size),
                "individual_decay_left": individual_decay(left),
                "individual_decay_right": individual_decay(right),
                "collective_decay_factorized": factorized,
                "collective_factorization_residual": abs(
                    coefficients["collective_decay"] - factorized
                ),
                **coefficients,
            }
        )
    checks = {
        "arbitrary_connection_counts_exercised": any(
            row["left_points"] > 2 and row["right_points"] > 2 for row in rows
        ),
        "zero_individual_implies_zero_collective": all(
            abs(row["individual_decay_left"]) <= tolerance
            and abs(row["individual_decay_right"]) <= tolerance
            and abs(row["collective_decay"]) <= tolerance
            for row in rows
        ),
        "collective_decay_factorization": all(
            row["collective_factorization_residual"] <= tolerance for row in rows
        ),
        "separate_and_nested_exchange_vanish": all(
            abs(row["exchange"]) <= tolerance
            for row in rows
            if row["topology"] in {"separate", "nested"}
        ),
        "braided_exchange_can_survive": any(
            row["topology"] == "braided" and abs(row["exchange"]) > 0.5
            for row in rows
        ),
    }
    return {"target_id": "T002", "checks": checks, "cases": rows}


def chain_tunability_result(atom_counts: Iterable[int], tolerance: float) -> dict[str, Any]:
    """Check the N constraints and N-1 independent chain controls."""

    rows = []
    for atom_count in atom_counts:
        controls = np.linspace(0.23, 0.83, atom_count - 1, dtype=np.float64)
        matrix = chain_constraint_matrix(atom_count)
        dependent_columns = np.arange(0, 2 * atom_count - 1, 2)
        rank_witness = matrix[:, dependent_columns]
        phases = _solve_chain_phases(atom_count, controls)
        atoms = _atoms_from_order(_chain_order(atom_count), phases)
        coupling_jacobian = np.diag(np.cos(controls))
        pair_rows = []
        for left_index in range(atom_count):
            for right_index in range(left_index + 1, atom_count):
                values = pair_coefficients(atoms[left_index], atoms[right_index])
                pair_rows.append(
                    {
                        "pair": [left_index, right_index],
                        "topology": topology(atoms[left_index], atoms[right_index]),
                        **values,
                    }
                )
        rows.append(
            {
                "atom_count": atom_count,
                "phase_count": int(matrix.shape[1]),
                "constraint_rank": int(np.linalg.matrix_rank(matrix)),
                "rank_witness_is_identity": bool(
                    np.array_equal(rank_witness, np.eye(atom_count))
                ),
                "free_phase_count": int(matrix.shape[1] - np.linalg.matrix_rank(matrix)),
                "coupling_jacobian_rank": int(np.linalg.matrix_rank(coupling_jacobian)),
                "constraint_residual": float(np.max(np.abs(matrix @ phases - np.pi))),
                "maximum_individual_decay": float(max(individual_decay(atom) for atom in atoms)),
                "maximum_non_neighbor_exchange": float(
                    max(
                        [
                            abs(row["exchange"])
                            for row in pair_rows
                            if row["pair"][1] - row["pair"][0] > 1
                        ]
                        or [0.0]
                    )
                ),
            }
        )
    checks = {
        "constraint_rank_is_n": all(row["constraint_rank"] == row["atom_count"] for row in rows),
        "exact_rank_witness_is_identity": all(
            row["rank_witness_is_identity"] for row in rows
        ),
        "free_phase_count_is_n_minus_one": all(
            row["free_phase_count"] == row["atom_count"] - 1 for row in rows
        ),
        "coupling_jacobian_rank_is_n_minus_one": all(
            row["coupling_jacobian_rank"] == row["atom_count"] - 1 for row in rows
        ),
        "constructed_chains_are_decoherence_free": all(
            row["constraint_residual"] <= tolerance
            and row["maximum_individual_decay"] <= tolerance
            for row in rows
        ),
        "only_nearest_neighbors_exchange": all(
            row["maximum_non_neighbor_exchange"] <= tolerance for row in rows
        ),
    }
    return {"target_id": "T003", "checks": checks, "systems": rows}


def all_to_all_result(atom_counts: Iterable[int], tolerance: float) -> dict[str, Any]:
    """Check control counting and the two explicit N=3 constructions."""

    rank_rows = []
    for atom_count in atom_counts:
        matrix = all_to_all_constraint_matrix(atom_count)
        rank_witness = matrix[:, :atom_count]
        rank = int(np.linalg.matrix_rank(matrix))
        rank_rows.append(
            {
                "atom_count": atom_count,
                "phase_count": int(matrix.shape[1]),
                "constraint_rank": rank,
                "rank_witness_is_upper_triangular_unit_diagonal": bool(
                    np.array_equal(rank_witness, np.triu(np.ones_like(rank_witness)))
                ),
                "free_phase_count": int(matrix.shape[1] - rank),
                "pairwise_coupling_count": atom_count * (atom_count - 1) // 2,
            }
        )

    constructions = []
    for construction_id, interior, zero_decay_phase in (
        ("equal_positive", np.array([np.pi / 3.0] * 3), np.pi),
        (
            "signed",
            np.array([4.0 * np.pi / 3.0, np.pi / 3.0, 4.0 * np.pi / 3.0]),
            3.0 * np.pi,
        ),
    ):
        phases = np.empty(5, dtype=np.float64)
        phases[1:4] = interior
        phases[0] = zero_decay_phase - phases[1] - phases[2]
        phases[4] = zero_decay_phase - phases[2] - phases[3]
        atoms = _atoms_from_order([0, 1, 2, 0, 1, 2], phases)
        couplings = {
            "g12": pair_coefficients(atoms[0], atoms[1])["exchange"],
            "g13": pair_coefficients(atoms[0], atoms[2])["exchange"],
            "g23": pair_coefficients(atoms[1], atoms[2])["exchange"],
        }
        constructions.append(
            {
                "construction_id": construction_id,
                "maximum_individual_decay": float(max(individual_decay(atom) for atom in atoms)),
                "couplings": couplings,
            }
        )

    equal = constructions[0]["couplings"]
    signed = constructions[1]["couplings"]
    checks = {
        "constraint_rank_is_n": all(row["constraint_rank"] == row["atom_count"] for row in rank_rows),
        "exact_rank_witness_is_unit_upper_triangular": all(
            row["rank_witness_is_upper_triangular_unit_diagonal"]
            for row in rank_rows
        ),
        "free_phase_count_is_n_minus_one": all(
            row["free_phase_count"] == row["atom_count"] - 1 for row in rank_rows
        ),
        "n3_equal_construction": max(equal.values()) - min(equal.values()) <= tolerance,
        "n3_signed_construction": abs(signed["g12"] - signed["g23"]) <= tolerance
        and abs(signed["g12"] + signed["g13"]) <= tolerance,
        "n3_constructions_are_decoherence_free": all(
            row["maximum_individual_decay"] <= tolerance for row in constructions
        ),
    }
    return {
        "target_id": "T004",
        "checks": checks,
        "rank_systems": rank_rows,
        "constructions": constructions,
    }


def run_claim_campaign(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Run the frozen analytic campaign and return one artifact per target."""

    closure = config.get("implementation_closure")
    if not isinstance(closure, dict):
        raise ValueError("implementation_closure must be an object")
    target_items = closure.get("target_items")
    expected_targets = {"T002", "T003", "T004"}
    if not isinstance(target_items, dict) or set(target_items) != expected_targets:
        raise ValueError("target_items must contain exactly T002, T003, and T004")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != 3 or len(set(flattened)) != 3:
        raise ValueError("each of the three fixed-denominator claims must map once")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    tolerance = float(parameters["tolerance"])
    results = {
        "T002": general_topology_result(tolerance),
        "T003": chain_tunability_result(parameters["chain_atom_counts"], tolerance),
        "T004": all_to_all_result(parameters["all_to_all_atom_counts"], tolerance),
    }
    for target_id, result in results.items():
        result.update(
            {
                "schema_version": 1,
                "item_ids": target_items[target_id],
                "status": "implementation_attested"
                if all(result["checks"].values())
                else "implementation_check_failed",
                "scientific_promotion": bool(closure["scientific_promotion"]),
                "profile": str(closure["profile"]),
            }
        )
    return results
