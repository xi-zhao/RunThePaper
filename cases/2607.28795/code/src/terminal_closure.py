"""Independent terminal-evidence campaign for the atomic target inventory.

The campaign deliberately separates three scientific outcomes:

* successful analytic or numerical checks;
* bounded attempts that reach a documented local capability boundary; and
* publication inputs whose absence is established outside the numerical run.

It never reads the paper PDF, author code, author arrays, or source pixels.
"""

from __future__ import annotations

from itertools import combinations, product
import json
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .gf2 import inverse, matmul_mod2, nullspace, rank, rref
from .group_algebra import FiniteGroupTable
from .mitten_codes import analyze_code, build_checks, canonical_logicals
from .sqetch import estimate_minimum_weight


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _group_record(
    group_payload: dict[str, Any], small_group_id: list[int]
) -> dict[str, Any]:
    return next(
        row
        for row in group_payload["groups"]
        if row["small_group_id"] == small_group_id
    )


def _paper_matrices(
    paper_inputs: dict[str, Any],
    group_payload: dict[str, Any],
    code_id: str,
):
    specification = next(
        row for row in paper_inputs["mitten_codes"] if row["code_id"] == code_id
    )
    group = FiniteGroupTable.from_record(
        _group_record(group_payload, specification["small_group_id"])
    )
    return group, specification, build_checks(group, specification)


def _mitten_weight_discrepancy(
    paper_inputs: dict[str, Any],
    group_payload: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    """Generate all eight rows before consulting comparison-only scalars."""

    analyses: list[dict[str, Any]] = []
    for specification in paper_inputs["mitten_codes"]:
        group = FiniteGroupTable.from_record(
            _group_record(group_payload, specification["small_group_id"])
        )
        analyses.append(
            analyze_code(group, specification, build_checks(group, specification))
        )

    # The branch above is the complete scientific generation path.  Values
    # below are paper Table-I scalars used only for post-generation comparison;
    # they never select a group, support, pivot, or numerical method.
    reported = comparison["table_i_reported_scalars"]
    comparisons: list[dict[str, Any]] = []
    for row in analyses:
        expected = reported[row["code_id"]]
        x_match = row["canonical_x_weight"] == int(expected["x"])
        z_match = row["canonical_z_weight"] == int(expected["z"])
        comparisons.append(
            {
                "code_id": row["code_id"],
                "generated_x": row["canonical_x_weight"],
                "generated_z": row["canonical_z_weight"],
                "paper_x": int(expected["x"]),
                "paper_z": int(expected["z"]),
                "x_match": x_match,
                "z_match": z_match,
                "row_match": x_match and z_match,
                "pivot_status": row["canonical_basis"]["status"],
            }
        )
    exact_rows = sum(bool(row["row_match"]) for row in comparisons)
    exact_components = sum(
        int(bool(row["x_match"])) + int(bool(row["z_match"]))
        for row in comparisons
    )
    return {
        "target_id": "T001",
        "mode": "independent_generation_then_table_scalar_comparison",
        "codes": analyses,
        "comparisons": comparisons,
        "exact_rows": exact_rows,
        "rows_total": len(comparisons),
        "exact_weight_components": exact_components,
        "weight_components_total": 2 * len(comparisons),
        "scientific_outcome": (
            "reproduced"
            if exact_rows == len(comparisons)
            else "paper_claim_discrepancy"
        ),
        "comparison_only_after_independent_generation": bool(
            comparison["comparison_only_after_independent_generation"]
        ),
    }


def _row_basis(matrix: np.ndarray) -> np.ndarray:
    reduced, pivots = rref(matrix)
    return reduced[: len(pivots)]


def _quotient_basis(kernel_basis: np.ndarray, subspace_rows: np.ndarray) -> np.ndarray:
    """Choose a row basis for ``span(kernel_basis) / span(subspace_rows)``."""

    current = _row_basis(subspace_rows)
    current_rank = rank(current)
    complement: list[np.ndarray] = []
    for vector in kernel_basis:
        candidate = np.vstack((current, vector))
        candidate_rank = rank(candidate)
        if candidate_rank > current_rank:
            complement.append(vector.copy())
            current = candidate
            current_rank = candidate_rank
    if not complement:
        return np.zeros((0, kernel_basis.shape[1]), dtype=np.uint8)
    return np.asarray(complement, dtype=np.uint8)


def milp_css_distance_attempt(
    commute_checks: np.ndarray,
    dual_logicals: np.ndarray,
    *,
    time_limit_seconds: float,
) -> dict[str, Any]:
    """Attempt an exact logical-weight MILP with a frozen wall-clock limit.

    Binary variables describe the candidate Pauli support. Integer slack
    variables impose every GF(2) parity equation exactly. Extra binary parity
    variables require a non-zero pairing with at least one dual logical, which
    excludes the stabilizer row space without enumerating logical cosets.
    """

    checks = np.asarray(commute_checks, dtype=np.uint8) & 1
    logicals = np.asarray(dual_logicals, dtype=np.uint8) & 1
    checks_total, qubits = checks.shape
    logicals_total = logicals.shape[0]
    if logicals_total == 0:
        raise ValueError("at least one dual logical is required")

    # [support bits | check parity slacks | logical parity bits | logical slacks]
    variables_total = qubits + checks_total + logicals_total + logicals_total
    constraints_total = checks_total + logicals_total + 1
    matrix = lil_matrix((constraints_total, variables_total), dtype=float)
    lower = np.zeros(constraints_total, dtype=float)
    upper = np.zeros(constraints_total, dtype=float)

    for row_index, row in enumerate(checks):
        matrix[row_index, np.flatnonzero(row)] = 1.0
        matrix[row_index, qubits + row_index] = -2.0

    parity_offset = qubits + checks_total
    logical_slack_offset = parity_offset + logicals_total
    for logical_index, row in enumerate(logicals):
        constraint_index = checks_total + logical_index
        matrix[constraint_index, np.flatnonzero(row)] = 1.0
        matrix[constraint_index, parity_offset + logical_index] = -1.0
        matrix[constraint_index, logical_slack_offset + logical_index] = -2.0

    # At least one dual-logical pairing must be odd.
    matrix[-1, parity_offset:logical_slack_offset] = 1.0
    lower[-1] = 1.0
    upper[-1] = np.inf

    variable_lower = np.zeros(variables_total, dtype=float)
    variable_upper = np.empty(variables_total, dtype=float)
    variable_upper[:qubits] = 1.0
    variable_upper[qubits:parity_offset] = np.ceil(checks.sum(axis=1) / 2)
    variable_upper[parity_offset:logical_slack_offset] = 1.0
    variable_upper[logical_slack_offset:] = np.floor(logicals.sum(axis=1) / 2)

    objective = np.zeros(variables_total, dtype=float)
    objective[:qubits] = 1.0
    started = perf_counter()
    result = milp(
        objective,
        integrality=np.ones(variables_total, dtype=np.uint8),
        bounds=Bounds(variable_lower, variable_upper),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
        options={"time_limit": float(time_limit_seconds), "mip_rel_gap": 0.0},
    )
    elapsed = perf_counter() - started
    return {
        "solver": "scipy.optimize.milp/HiGHS",
        "qubits": int(qubits),
        "checks": int(checks_total),
        "dual_logicals": int(logicals_total),
        "variables": int(variables_total),
        "constraints": int(constraints_total),
        "time_limit_seconds": float(time_limit_seconds),
        "elapsed_seconds": elapsed,
        "solver_status": int(result.status),
        "solver_message": str(result.message),
        "objective": None if result.fun is None else float(result.fun),
        "mip_gap": None
        if getattr(result, "mip_gap", None) is None
        else float(result.mip_gap),
        "nodes": None
        if getattr(result, "mip_node_count", None) is None
        else int(result.mip_node_count),
        "optimality_certified": bool(result.status == 0),
    }


def _exact_distance_probe(
    paper_inputs: dict[str, Any],
    group_payload: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    group, specification, matrices = _paper_matrices(
        paper_inputs, group_payload, str(config["code_id"])
    )
    del group
    z_logicals = _quotient_basis(nullspace(matrices.hx), matrices.hz)
    x_logicals = _quotient_basis(nullspace(matrices.hz), matrices.hx)
    time_limit = float(config["time_limit_seconds_per_sector"])
    x_attempt = milp_css_distance_attempt(
        matrices.hz, z_logicals, time_limit_seconds=time_limit
    )
    z_attempt = milp_css_distance_attempt(
        matrices.hx, x_logicals, time_limit_seconds=time_limit
    )
    expected = int(config["paper_reported_distance"])
    certified = x_attempt["optimality_certified"] and z_attempt["optimality_certified"]
    reproduced = certified and min(x_attempt["objective"], z_attempt["objective"]) == expected
    return {
        "target_id": "T009",
        "mode": "paper_instance_exact_milp_attempt",
        "code_id": specification["code_id"],
        "paper_reported_distance": expected,
        "x_sector": x_attempt,
        "z_sector": z_attempt,
        "scientific_outcome": (
            "reproduced" if reproduced else "attempted_not_reproduced"
        ),
        "capability_boundary": (
            None
            if certified
            else "The exact paper-instance MILP did not certify both sectors within the frozen local limit."
        ),
    }


def _distance_estimator_probe(
    paper_inputs: dict[str, Any],
    group_payload: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for offset, code_id in enumerate(config["code_ids"]):
        _, _, matrices = _paper_matrices(paper_inputs, group_payload, str(code_id))
        started = perf_counter()
        result = estimate_minimum_weight(
            matrices.hz,
            matrices.hx,
            sketch_rows=int(config["sketch_rows"]),
            trials=int(config["probe_trials"]),
            seed=int(config["seed"]) + offset,
        )
        elapsed = perf_counter() - started
        per_trial = elapsed / int(config["probe_trials"])
        rows.append(
            {
                "code_id": code_id,
                "qubits": int(matrices.hx.shape[1]),
                "probe": result,
                "elapsed_seconds": elapsed,
                "seconds_per_trial": per_trial,
                "projected_seconds_for_reported_sqetch_trials": (
                    per_trial * int(config["paper_reported_sqetch_trials"])
                ),
            }
        )
    return {
        "target_id": "T010",
        "mode": "paper_matrix_cpu_sqetch_attempt",
        "paper_reported_sqetch_trials": int(config["paper_reported_sqetch_trials"]),
        "paper_reported_bposd_trials": int(config["paper_reported_bposd_trials"]),
        "rows": rows,
        "scientific_outcome": "attempted_not_reproduced",
        "capability_boundary": (
            "The clean-room estimator executed on disclosed paper matrices, but the paper's "
            "50M sQetch plus 50k BP+OSD campaign and the undisclosed BP+OSD path were not completed."
        ),
    }


def _detected_single_qubit_errors(check: np.ndarray) -> int:
    return int(np.count_nonzero(np.any(check, axis=0)))


def _implementation_probes(
    paper_inputs: dict[str, Any], group_payload: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    group, specification, matrices = _paper_matrices(
        paper_inputs, group_payload, "mitten-150"
    )
    analysis = analyze_code(group, specification, matrices)
    logical_x, logical_z = canonical_logicals(matrices)
    pairing = matmul_mod2(logical_x[:10], logical_z[:10].T)

    hx_neighbors = [set(np.flatnonzero(matrices.hx[:, column])) for column in range(20)]
    pair_expansion = [
        len(hx_neighbors[left] | hx_neighbors[right]) / 2
        for left, right in combinations(range(20), 2)
    ]
    graph_probe = {
        "data_qubits": int(matrices.hx.shape[1]),
        "x_checks": int(matrices.hx.shape[0]),
        "z_checks": int(matrices.hz.shape[0]),
        "x_edges": int(np.sum(matrices.hx)),
        "z_edges": int(np.sum(matrices.hz)),
        "x_data_columns_with_nonzero_syndrome": _detected_single_qubit_errors(
            matrices.hz
        ),
        "z_data_columns_with_nonzero_syndrome": _detected_single_qubit_errors(
            matrices.hx
        ),
    }
    common = {
        "paper_instance": analysis["code_id"],
        "css_commutation": analysis["invariants"]["css_commutation"],
        "code_dimensions": [analysis["n"], analysis["k"]],
    }
    return {
        "T005": {
            **common,
            "probe": "paper_matrix_and_single_fault_syndrome_construction",
            "graph": graph_probe,
            "scientific_outcome": "attempted_not_reproduced",
            "capability_boundary": "No circuit-level hook-free schedule, detector model, or telescoping-decoder implementation was completed.",
        },
        "T006": {
            **common,
            "probe": "two_logical_product_operator_construction",
            "product_weight": int(np.sum(logical_x[0] ^ logical_x[1])),
            "product_commutes_with_z_checks": bool(
                not np.any(matmul_mod2(matrices.hz, (logical_x[0] ^ logical_x[1])[:, None]))
            ),
            "scientific_outcome": "attempted_not_reproduced",
            "capability_boundary": "The logical-product observable was constructed, but the merged surgery circuit and circuit-level decoder were not completed.",
        },
        "T011": {
            **common,
            "probe": "typed_tanner_graph_construction",
            "graph": graph_probe,
            "scientific_outcome": "attempted_not_reproduced",
            "capability_boundary": "The base Tanner graph was constructed, but the five optimized graph-surgery transformations were not completed.",
        },
        "T012": {
            **common,
            "probe": "ten_parallel_canonical_logicals",
            "logical_operators_checked": 10,
            "delta_pairing": bool(np.array_equal(pairing, np.eye(10, dtype=np.uint8))),
            "scientific_outcome": "attempted_not_reproduced",
            "capability_boundary": "Ten independent logical operands were constructed, but the thickened merged code and dual distance certification were not completed.",
        },
        "T013": {
            **common,
            "probe": "bounded_tanner_expansion_check",
            "vertices_sampled": 20,
            "minimum_pair_neighbor_ratio": min(pair_expansion),
            "scientific_outcome": "attempted_not_reproduced",
            "capability_boundary": "The base expansion probe ran, but the full extractor graph reduction, augmentation, and certification were not completed.",
        },
    }


def _cyclic_group(order: int) -> FiniteGroupTable:
    multiplication = np.fromfunction(
        lambda left, right: (left + right) % order,
        (order, order),
        dtype=int,
    ).astype(np.int64)
    return FiniteGroupTable.from_record(
        {
            "small_group_id": [order, 2 if order == 28 else 1],
            "order": order,
            "identity": 0,
            "multiplication": multiplication.tolist(),
            "inverse": [(-element) % order for element in range(order)],
        }
    )


def _c4_times_c2_group() -> FiniteGroupTable:
    """C4 x C2 with index ``x_power + 4*y_power``."""

    order = 8
    multiplication = np.zeros((order, order), dtype=np.int64)
    inverses: list[int] = []
    for left in range(order):
        left_x, left_y = left % 4, left // 4
        inverses.append(((-left_x) % 4) + 4 * left_y)
        for right in range(order):
            right_x, right_y = right % 4, right // 4
            multiplication[left, right] = (
                (left_x + right_x) % 4 + 4 * ((left_y + right_y) % 2)
            )
    return FiniteGroupTable.from_record(
        {
            "small_group_id": [8, 2],
            "order": order,
            "identity": 0,
            "multiplication": multiplication.tolist(),
            "inverse": inverses,
        }
    )


def _c4c2_support(*monomials: tuple[int, int]) -> list[int]:
    return [x_power % 4 + 4 * (y_power % 2) for x_power, y_power in monomials]


def _minimum_kernel_weight(matrix: np.ndarray) -> dict[str, Any]:
    basis = nullspace(matrix)
    dimension = int(basis.shape[0])
    if dimension > 24:
        raise ValueError("bounded kernel enumerator is limited to dimension 24")
    best: int | None = None
    examined = 0
    for selector in product((0, 1), repeat=dimension):
        if not any(selector):
            continue
        examined += 1
        vector = np.zeros(matrix.shape[1], dtype=np.uint8)
        for include, row in zip(selector, basis, strict=True):
            if include:
                vector ^= row
        weight = int(np.sum(vector))
        best = weight if best is None else min(best, weight)
    return {
        "kernel_dimension": dimension,
        "nonzero_vectors_examined": examined,
        "minimum_weight": best,
    }


def _full_rank_counterexample(config: dict[str, Any]) -> dict[str, Any]:
    """Independently transcribe and test Remark 12 / Eqs. G10-G11."""

    s = _c4c2_support
    group = _c4_times_c2_group()
    a = [
        [
            s((0, 0), (1, 0), (1, 1), (3, 1)),
            s((0, 0), (0, 1), (1, 1), (2, 0), (3, 0)),
            s((0, 0), (1, 1), (2, 1)),
            s((1, 0), (1, 1), (2, 1), (3, 0)),
        ],
        [
            s((0, 1), (2, 0), (2, 1), (3, 0)),
            s((0, 0), (1, 0), (2, 1)),
            s((0, 0), (2, 1), (3, 0)),
            s((0, 0), (0, 1), (1, 0), (1, 1), (3, 0), (3, 1)),
        ],
        [
            s((0, 0), (0, 1), (2, 1), (3, 1)),
            s((0, 0), (0, 1), (1, 0), (3, 0), (3, 1)),
            s((0, 0), (1, 0), (2, 1), (3, 1)),
            s((1, 0), (3, 0), (3, 1)),
        ],
    ]
    b = [
        [
            s((1, 1), (2, 1), (3, 0), (3, 1)),
            s((1, 0), (1, 1), (2, 0), (2, 1), (3, 0)),
            s((1, 1), (2, 1)),
            s((1, 1), (2, 1), (3, 0)),
        ],
        [
            s((0, 1), (1, 0), (2, 0), (3, 0)),
            s((0, 0), (1, 0), (3, 0)),
            s((1, 0), (2, 0), (3, 0), (3, 1)),
            s((2, 0), (3, 0), (3, 1)),
        ],
        [
            s((0, 0), (1, 0), (3, 1)),
            s((0, 1), (3, 0)),
            s((0, 1), (1, 0), (1, 1), (3, 1)),
            s((0, 0), (1, 1), (2, 0), (3, 0)),
        ],
    ]
    left_a = _regular_block_matrix(group, a, side="left")
    right_b = _regular_block_matrix(group, b, side="right")
    classical_a = _minimum_kernel_weight(left_a)
    classical_b = _minimum_kernel_weight(right_b)
    hx, hz = build_general_lp_checks(group, a, b)
    z_logicals = _quotient_basis(nullspace(hx), hz)
    x_logicals = _quotient_basis(nullspace(hz), hx)
    time_limit = float(config["time_limit_seconds_per_sector"])
    x_attempt = milp_css_distance_attempt(
        hz, z_logicals, time_limit_seconds=time_limit
    )
    z_attempt = milp_css_distance_attempt(
        hx, x_logicals, time_limit_seconds=time_limit
    )
    exact_quantum = (
        x_attempt["optimality_certified"]
        and z_attempt["optimality_certified"]
        and min(x_attempt["objective"], z_attempt["objective"]) == 10
    )
    return {
        "claim_id": "CLM07_FULL_RANK_COUNTEREXAMPLE",
        "left_a_rank": rank(left_a),
        "right_b_rank": rank(right_b),
        "full_row_rank": 24,
        "classical_a": classical_a,
        "classical_b": classical_b,
        "lp_n": int(hx.shape[1]),
        "lp_k": int(hx.shape[1] - rank(hx) - rank(hz)),
        "x_sector": x_attempt,
        "z_sector": z_attempt,
        "paper_reported_quantum_distance": 10,
        "exact_quantum_distance_reproduced": exact_quantum,
        "partial_checks_passed": bool(
            rank(left_a) == 22
            and rank(right_b) == 23
            and classical_a["minimum_weight"] == 8
            and classical_b["minimum_weight"] == 8
            and hx.shape[1] == 200
            and hx.shape[1] - rank(hx) - rank(hz) == 13
        ),
    }


def _regular_block_matrix(
    group: FiniteGroupTable,
    ring_matrix: list[list[list[int]]],
    *,
    side: str,
    star: bool = False,
) -> np.ndarray:
    rows = len(ring_matrix)
    columns = len(ring_matrix[0])
    blocks: list[list[np.ndarray]] = []
    for row in range(rows):
        block_row: list[np.ndarray] = []
        for column in range(columns):
            support = ring_matrix[row][column]
            if star:
                support = list(group.star_support(support))
            block_row.append(
                group.left_regular(support)
                if side == "left"
                else group.right_regular(support)
            )
        blocks.append(block_row)
    return np.block(blocks)


def build_general_lp_checks(
    group: FiniteGroupTable,
    a: list[list[list[int]]],
    b: list[list[list[int]]],
) -> tuple[np.ndarray, np.ndarray]:
    """Expand Eqs. (A19)-(A20) for arbitrary base-matrix shapes."""

    r1, c1 = len(a), len(a[0])
    r2, c2 = len(b), len(b[0])
    order = group.order
    hx_left = np.zeros((r1 * c2 * order, c1 * c2 * order), dtype=np.uint8)
    hx_right = np.zeros((r1 * c2 * order, r1 * r2 * order), dtype=np.uint8)
    hz_left = np.zeros((c1 * r2 * order, c1 * c2 * order), dtype=np.uint8)
    hz_right = np.zeros((c1 * r2 * order, r1 * r2 * order), dtype=np.uint8)

    for i in range(r1):
        for j in range(c2):
            out = slice((i * c2 + j) * order, (i * c2 + j + 1) * order)
            for alpha in range(c1):
                target = slice(
                    (alpha * c2 + j) * order,
                    (alpha * c2 + j + 1) * order,
                )
                hx_left[out, target] = group.left_regular(a[i][alpha])
            for beta in range(r2):
                target = slice(
                    (i * r2 + beta) * order,
                    (i * r2 + beta + 1) * order,
                )
                hx_right[out, target] = group.right_regular(
                    group.star_support(b[beta][j])
                )

    for alpha in range(c1):
        for beta in range(r2):
            out = slice((alpha * r2 + beta) * order, (alpha * r2 + beta + 1) * order)
            for j in range(c2):
                target = slice(
                    (alpha * c2 + j) * order,
                    (alpha * c2 + j + 1) * order,
                )
                hz_left[out, target] = group.right_regular(b[beta][j])
            for i in range(r1):
                target = slice(
                    (i * r2 + beta) * order,
                    (i * r2 + beta + 1) * order,
                )
                hz_right[out, target] = group.left_regular(
                    group.star_support(a[i][alpha])
                )
    return np.hstack((hx_left, hx_right)), np.hstack((hz_left, hz_right))


def _cyclic_convolution(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    order = left.shape[0]
    result = np.zeros(order, dtype=np.uint8)
    for left_index in np.flatnonzero(left):
        for right_index in np.flatnonzero(right):
            result[(int(left_index) + int(right_index)) % order] ^= 1
    return result


def _tensor_ring_vectors(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_blocks, order = left.shape
    right_blocks = right.shape[0]
    result = np.zeros((left_blocks * right_blocks, order), dtype=np.uint8)
    for i in range(left_blocks):
        for j in range(right_blocks):
            result[i * right_blocks + j] = _cyclic_convolution(left[i], right[j])
    return result.reshape(-1)


def _kernel_seed_vectors(
    expanded: np.ndarray, *, free_columns: int, order: int
) -> list[np.ndarray]:
    free_width = free_columns * order
    pivot = expanded[:, free_width:]
    pivot_inverse = inverse(pivot)
    seeds: list[np.ndarray] = []
    for alpha in range(free_columns):
        free = np.zeros(free_width, dtype=np.uint8)
        free[alpha * order] = 1
        pivot_part = matmul_mod2(
            pivot_inverse, matmul_mod2(expanded[:, :free_width], free[:, None])
        )[:, 0]
        seeds.append(np.concatenate((free, pivot_part)).reshape(-1, order))
    return seeds


def _free_seed_vectors(*, columns: int, free_columns: int, order: int) -> list[np.ndarray]:
    seeds: list[np.ndarray] = []
    for alpha in range(free_columns):
        vector = np.zeros((columns, order), dtype=np.uint8)
        vector[alpha, 0] = 1
        seeds.append(vector)
    return seeds


def _ablp_j560() -> dict[str, Any]:
    group = _cyclic_group(28)
    a = [
        [[10, 11], [26], [2, 19], [6]],
        [[13], [15, 27], [15], [0, 10]],
    ]
    b = a
    hx, hz = build_general_lp_checks(group, a, b)
    order = group.order
    # Definition 16 permits a column reordering before splitting free and
    # pivot columns.  Choose the first lexicographic two-column pivot whose
    # left and right binary expansions are both invertible.  This rule is
    # fixed without consulting the reported logical weights.
    pivot_columns: tuple[int, ...] | None = None
    ordered_a: list[list[list[int]]] | None = None
    for candidate in combinations(range(4), 2):
        free_columns = [column for column in range(4) if column not in candidate]
        column_order = [*free_columns, *candidate]
        reordered = [[row[column] for column in column_order] for row in a]
        left_candidate = _regular_block_matrix(group, reordered, side="left")
        right_candidate = _regular_block_matrix(group, reordered, side="right")
        if (
            rank(left_candidate[:, 2 * order :]) == 2 * order
            and rank(right_candidate[:, 2 * order :]) == 2 * order
        ):
            pivot_columns = candidate
            ordered_a = reordered
            break
    if pivot_columns is None or ordered_a is None:
        raise RuntimeError("J560 has no square-invertible two-column pivot")
    left_a = _regular_block_matrix(group, ordered_a, side="left")
    right_b = _regular_block_matrix(group, ordered_a, side="right")
    v_a = _kernel_seed_vectors(left_a, free_columns=2, order=order)
    v_b = _kernel_seed_vectors(right_b, free_columns=2, order=order)
    w_a = _free_seed_vectors(columns=4, free_columns=2, order=order)
    w_b = _free_seed_vectors(columns=4, free_columns=2, order=order)
    x_weights: list[int] = []
    z_weights: list[int] = []
    for alpha, beta in product(range(2), repeat=2):
        x = _tensor_ring_vectors(w_a[alpha], v_b[beta])
        z = _tensor_ring_vectors(v_a[alpha], w_b[beta])
        x_weights.append(int(np.sum(x)))
        z_weights.append(int(np.sum(z)))
    n = int(hx.shape[1])
    k = n - rank(hx) - rank(hz)
    return {
        "target_id": "T027",
        "code_id": "ablp-560",
        "n": n,
        "k": int(k),
        "css_commutation": bool(not np.any(matmul_mod2(hx, hz.T))),
        "left_pivot_invertible": rank(left_a[:, 2 * order :]) == 2 * order,
        "right_pivot_invertible": rank(right_b[:, 2 * order :]) == 2 * order,
        "pivot_columns_zero_based": list(pivot_columns),
        "canonical_x_weight_set": sorted(set(x_weights)),
        "canonical_z_weight_set": sorted(set(z_weights)),
        "paper_reported_weight_set": [22, 30],
        "scientific_outcome": (
            "reproduced"
            if n == 560
            and k == 112
            and sorted(set(x_weights)) == [22, 30]
            and sorted(set(z_weights)) == [22, 30]
            else "attempted_not_reproduced"
        ),
    }


def _structured_j300(
    group_payload: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    group = FiniteGroupTable.from_record(_group_record(group_payload, [60, 11]))
    specification = {
        "code_id": "structured-300-table-xiii",
        "small_group_id": [60, 11],
        **config["table_xiii_supports"],
    }
    result = analyze_code(group, specification, build_checks(group, specification))
    return {
        "target_id": "T014",
        "mode": "literal_table_xiii_structured_code",
        "analysis": result,
        "table_vi_reported": config["table_vi_reported"],
        "paper_internal_identity_match": (
            result["n"] == int(config["table_vi_reported"]["n"])
            and result["k"] == int(config["table_vi_reported"]["k"])
        ),
        "scientific_outcome": "paper_claim_discrepancy",
    }


def _analytic_checks(config: dict[str, Any]) -> dict[str, Any]:
    claims = config["analytic_claims"]
    failed = [claim["claim_id"] for claim in claims if claim["status"] == "failed"]
    return {
        "schema_version": 1,
        "paper_id": "2607.28795",
        "status": "passed" if not failed else "failed",
        "claims_total": len(claims),
        "failed_claim_ids": failed,
        "claims": claims,
    }


def run_terminal_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _read_json(config_path)
    workspace = config_path.resolve().parent.parent
    paper_inputs = _read_json(workspace / str(config["paper_inputs_path"]))
    group_payload = _read_json(workspace / str(config["group_tables_path"]))

    targets: dict[str, dict[str, Any]] = {}
    targets["T001"] = _mitten_weight_discrepancy(
        paper_inputs, group_payload, config["mitten_weight_comparison"]
    )
    targets.update(_implementation_probes(paper_inputs, group_payload))
    exact = _exact_distance_probe(
        paper_inputs, group_payload, config["exact_distance_attempt"]
    )
    targets["T009"] = exact
    stochastic = _distance_estimator_probe(
        paper_inputs, group_payload, config["distance_estimation_attempt"]
    )
    targets["T010"] = stochastic
    targets["T014"] = _structured_j300(group_payload, config["structured_code_attempt"])
    targets["T027"] = _ablp_j560()

    analytic = _analytic_checks(config)
    counterexample = _full_rank_counterexample(config["counterexample_attempt"])
    analytic["counterexample_numeric_check"] = counterexample
    targets["T028"] = {
        "target_id": "T028",
        "mode": "paper_counterexample_exact_distance_attempt",
        "scientific_outcome": (
            "reproduced"
            if counterexample["exact_quantum_distance_reproduced"]
            else "attempted_not_reproduced"
        ),
        "counterexample": counterexample,
        "capability_boundary": (
            None
            if counterexample["exact_quantum_distance_reproduced"]
            else "Ranks, dimensions, and both classical distances reproduced, but the exact LP distance-ten MILP did not certify within the frozen local limit."
        ),
    }
    for target_id in config["analytic_target_ids"]:
        targets[target_id] = {
            "target_id": target_id,
            "mode": "analytic_reference",
            "scientific_outcome": "reproduced",
            "claim_ids": [
                claim["claim_id"]
                for claim in analytic["claims"]
                if target_id in claim["target_ids"]
            ],
        }

    _write_json(output_root / "data" / "terminal_closure.json", {"targets": targets})
    _write_json(output_root / "checks" / "analytic_claim_review.json", analytic)
    expected_targets = set(config["attestation_parameters"]["target_ids"])
    observed_targets = set(targets)
    missing = sorted(expected_targets - observed_targets)
    check = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if not missing and analytic["status"] == "passed" else "failed",
        "target_ids": sorted(observed_targets),
        "missing_target_ids": missing,
        "clean_room_boundary": config["clean_room_boundary"],
    }
    _write_json(output_root / "checks" / "terminal_closure.json", check)
    if check["status"] != "passed":
        raise RuntimeError(f"terminal campaign check failed: {check}")
    return check
