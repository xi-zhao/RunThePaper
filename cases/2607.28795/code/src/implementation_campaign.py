"""Clean-room implementation closure for all reproduction targets.

This module proves that every target has either an executable scientific path
or a fail-closed, machine-readable input boundary.  Reduced validations do not
promote scientific coverage, and the runner never reads the paper PDF, source
figures, author arrays, or author code.
"""

from __future__ import annotations

from itertools import permutations, product
import json
from math import comb, ceil
from pathlib import Path
from typing import Any

import numpy as np

from .closed_form import magic_injection_counts, realtime_decoder_metrics
from .gf2 import matmul_mod2, rank
from .group_algebra import FiniteGroupTable
from .mitten_codes import analyze_code, build_checks
from .sqetch import (
    approximate_hit_probability,
    estimate_minimum_weight,
    sketch_inclusion_probability,
    steane_check_matrix,
)


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 25))


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _resolve_input(workspace: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else workspace / path


def _cyclic_group(order: int) -> FiniteGroupTable:
    multiplication = np.fromfunction(
        lambda left, right: (left + right) % order,
        (order, order),
        dtype=int,
    ).astype(np.int64)
    return FiniteGroupTable.from_record(
        {
            "small_group_id": [order, 1],
            "order": order,
            "identity": 0,
            "multiplication": multiplication.tolist(),
            "inverse": [(-element) % order for element in range(order)],
        }
    )


def _paper_code_subset(params: dict[str, Any], workspace: Path) -> dict[str, Any]:
    paper_inputs = _read_json(
        _resolve_input(workspace, str(params["paper_inputs_path"]))
    )
    group_payload = _read_json(
        _resolve_input(workspace, str(params["group_tables_path"]))
    )
    code_id = str(params["code_id"])
    specification = next(
        row for row in paper_inputs["mitten_codes"] if row["code_id"] == code_id
    )
    group_id = list(specification["small_group_id"])
    record = next(
        row for row in group_payload["groups"] if row["small_group_id"] == group_id
    )
    group = FiniteGroupTable.from_record(record)
    result = analyze_code(group, specification, build_checks(group, specification))
    return {
        "mode": "paper_exact_subset_validation",
        "paper_exact_scope": code_id,
        "analysis": result,
        "passed": result["status"] == "passed",
        "scope_boundary": (
            "This attests the clean-room algebra path on one frozen paper row; "
            "it does not replace the existing eight-row scientific assessment."
        ),
    }


def _magic_counts(params: dict[str, Any]) -> dict[str, Any]:
    result = magic_injection_counts(
        int(params["group_order"]), int(params["repetition_distance"])
    )
    return {
        "mode": "analytic_validation",
        "counts": result,
        "passed": result["logical_qubits"] == int(params["group_order"]),
    }


def _sqetch_reduced(params: dict[str, Any]) -> dict[str, Any]:
    check = steane_check_matrix()
    result = estimate_minimum_weight(
        check,
        check,
        sketch_rows=int(params["sketch_rows"]),
        trials=int(params["trials"]),
        seed=int(params["seed"]),
    )
    return {
        "mode": "reduced_validation",
        "known_code": "Steane [[7,1,3]]",
        "result": result,
        "passed": result["best_weight"] == 3,
    }


def _realtime_arithmetic(params: dict[str, Any], workspace: Path) -> dict[str, Any]:
    paper_inputs = _read_json(
        _resolve_input(workspace, str(params["paper_inputs_path"]))
    )
    experiment_id = str(params["experiment_id"])
    experiment = next(
        row
        for row in paper_inputs["realtime_experiments"]
        if row["experiment_id"] == experiment_id
    )
    result = realtime_decoder_metrics(
        experiment["stages"], float(params["cycle_seconds"])
    )
    return {
        "mode": "paper_exact_analytic_validation",
        "experiment_id": experiment_id,
        "result": result,
        "passed": bool(result["all_mean_stage_utilizations_below_one"]),
    }


def _input_boundary(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    schema = params.get("required_input_schema")
    supplied = params.get("supplied_inputs", [])
    if not isinstance(schema, dict) or not schema:
        raise ValueError(f"{target_id}: required_input_schema must be non-empty")
    if not isinstance(supplied, list):
        raise ValueError(f"{target_id}: supplied_inputs must be a list")
    missing = [name for name in schema if name not in supplied]
    if not missing:
        raise ValueError(
            f"{target_id}: all inputs are supplied; use an executable scientific mode"
        )
    return {
        "mode": "input_boundary",
        "status": "input_blocked",
        "target_id": target_id,
        "input_schema_version": 1,
        "required_input_schema": schema,
        "supplied_inputs": supplied,
        "missing_inputs": missing,
        "forbidden_substitutions": [
            "author numerical code",
            "author numerical arrays",
            "digitized paper curves",
            "source-figure pixels",
            "guessed circuits, schedules, layouts, or benchmark metadata",
        ],
        "acceptance_boundary": str(params["acceptance_boundary"]),
    }


def _vector_is_in_rowspan(vector: np.ndarray, rows: np.ndarray) -> bool:
    return rank(np.vstack((rows, vector))) == rank(rows)


def exact_css_distance(
    hx: np.ndarray,
    hz: np.ndarray,
    *,
    max_enumerated_vectors: int,
) -> dict[str, Any]:
    """Return an exact CSS distance certificate by exhaustive enumeration.

    The implementation is matrix-generic.  The explicit enumeration limit is
    part of the run contract so a large paper instance fails before consuming
    unbounded resources rather than silently switching algorithms.
    """

    hx = np.asarray(hx, dtype=np.uint8)
    hz = np.asarray(hz, dtype=np.uint8)
    if hx.ndim != 2 or hz.ndim != 2 or hx.shape[1] != hz.shape[1]:
        raise ValueError("H_X and H_Z must be binary matrices with equal width")
    if np.any(matmul_mod2(hx, hz.T)):
        raise ValueError("H_X and H_Z do not define a commuting CSS code")
    required_vectors = 2 ** int(hx.shape[1]) - 1
    if required_vectors > max_enumerated_vectors:
        raise ValueError(
            "exact enumeration exceeds frozen max_enumerated_vectors: "
            f"required={required_vectors}, limit={max_enumerated_vectors}"
        )
    best_x: int | None = None
    best_z: int | None = None
    examined = 0
    for bits in product((0, 1), repeat=hx.shape[1]):
        vector = np.asarray(bits, dtype=np.uint8)
        if not np.any(vector):
            continue
        examined += 1
        weight = int(np.sum(vector))
        if not np.any(matmul_mod2(hz, vector[:, None])) and not _vector_is_in_rowspan(
            vector, hx
        ):
            best_x = weight if best_x is None else min(best_x, weight)
        if not np.any(matmul_mod2(hx, vector[:, None])) and not _vector_is_in_rowspan(
            vector, hz
        ):
            best_z = weight if best_z is None else min(best_z, weight)
    return {
        "examined_nonzero_vectors": examined,
        "x_distance": best_x,
        "z_distance": best_z,
    }


def _exact_css_distance(params: dict[str, Any]) -> dict[str, Any]:
    if params.get("matrix_source") == "steane_validation":
        hx = steane_check_matrix()
        hz = steane_check_matrix()
        known_code = "Steane [[7,1,3]]"
    else:
        hx = np.asarray(params["hx"], dtype=np.uint8)
        hz = np.asarray(params["hz"], dtype=np.uint8)
        known_code = str(params.get("code_id", "configured_css_code"))
    certificate = exact_css_distance(
        hx,
        hz,
        max_enumerated_vectors=int(params["max_enumerated_vectors"]),
    )
    expected = int(params["expected_distance"])
    return {
        "mode": "reduced_exact_validation",
        "known_code": known_code,
        **certificate,
        "passed": (
            certificate["x_distance"] == expected
            and certificate["z_distance"] == expected
        ),
        "paper_scale_boundary": (
            "The exact enumerator is validated here; the five paper code sizes "
            "require a scalable search and are not claimed as executed."
        ),
    }


def _stochastic_distance(params: dict[str, Any]) -> dict[str, Any]:
    result = _sqetch_reduced(params)
    result["mode"] = "reduced_stochastic_validation"
    result["frozen_seed"] = int(params["seed"])
    return result


def _general_css_identity(params: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for order in params["cyclic_group_orders"]:
        order = int(order)
        group = _cyclic_group(order)
        specification = {
            "code_id": f"cyclic-{order}",
            "a0": [0],
            "a1": [0],
            "b0": [0],
            "b1": [0],
        }
        matrices = build_checks(group, specification)
        commutator = matmul_mod2(matrices.hx, matrices.hz.T)
        k = matrices.hx.shape[1] - rank(matrices.hx) - rank(matrices.hz)
        rows.append(
            {
                "group_order": order,
                "css_commutes": bool(not np.any(commutator)),
                "n": int(matrices.hx.shape[1]),
                "k": int(k),
                "rate": float(k / matrices.hx.shape[1]),
                "expected_lower_bound": order,
            }
        )
    passed = all(row["css_commutes"] and row["k"] >= row["expected_lower_bound"] for row in rows)
    return {
        "mode": "independent_property_validation",
        "instances": rows,
        "passed": passed,
        "claim_boundary": "Finite instances test the identity; they are not a formal proof of the general proposition.",
    }


def _generic_pivot_hit(params: dict[str, Any]) -> dict[str, Any]:
    columns = int(params["columns"])
    pivots = int(params["pivots"])
    required = int(params["required_pivots"])
    if not 0 <= required <= pivots <= columns:
        raise ValueError("invalid generic-pivot parameters")
    exact_pivot_probability = comb(columns - required, pivots - required) / comb(
        columns, pivots
    )
    sketch_probability = sketch_inclusion_probability(
        int(params["nullity"]), required, int(params["sketch_rows"])
    )
    single_trial = exact_pivot_probability * sketch_probability
    amplified = approximate_hit_probability(single_trial, int(params["trials"]))
    rng = np.random.default_rng(int(params["seed"]))
    hits = 0
    required_set = set(range(required))
    samples = int(params["monte_carlo_samples"])
    for _ in range(samples):
        selected = set(rng.choice(columns, size=pivots, replace=False).tolist())
        hits += required_set <= selected
    empirical = hits / samples
    tolerance = float(params["tolerance"])
    return {
        "mode": "generic_pivot_model_validation",
        "exact_pivot_probability": exact_pivot_probability,
        "empirical_pivot_probability": empirical,
        "sketch_inclusion_probability": sketch_probability,
        "single_trial_hit_probability": single_trial,
        "amplified_hit_probability": amplified,
        "passed": abs(empirical - exact_pivot_probability) <= tolerance,
        "assumption_boundary": (
            "This validates the uniform-pivot approximation under its stated "
            "sampling assumption; it does not assert that every code instance has uniform pivots."
        ),
    }


def _relative_group_permutation(params: dict[str, Any]) -> dict[str, Any]:
    group = _cyclic_group(int(params["order"]))
    gi = int(params["g_i"])
    gj = int(params["g_j"])
    relative = int(group.multiplication[int(group.inverses[gj]), gi])
    left_composed = matmul_mod2(group.left_regular([gj]).T, group.left_regular([gi]))
    right_composed = matmul_mod2(group.right_regular([gj]).T, group.right_regular([gi]))
    left_expected = group.left_regular([relative])
    right_expected = group.right_regular([relative])
    return {
        "mode": "exact_group_property_validation",
        "group_order": group.order,
        "relative_element": relative,
        "left_identity_holds": bool(np.array_equal(left_composed, left_expected)),
        "right_identity_holds": bool(np.array_equal(right_composed, right_expected)),
        "passed": bool(
            np.array_equal(left_composed, left_expected)
            and np.array_equal(right_composed, right_expected)
        ),
    }


def _tanner_thickness_bound(params: dict[str, Any]) -> dict[str, Any]:
    vertices = int(params["vertices"])
    edges = int(params["edges"])
    if vertices < 3 or edges <= 0:
        raise ValueError("invalid bipartite graph counts")
    planar_edge_capacity = 2 * vertices - 4
    lower_bound = ceil(edges / planar_edge_capacity)
    return {
        "mode": "analytic_lower_bound_validation",
        "graph": str(params["graph"]),
        "vertices": vertices,
        "edges": edges,
        "bipartite_planar_edge_capacity": planar_edge_capacity,
        "thickness_lower_bound": lower_bound,
        "passed": lower_bound == int(params["expected_lower_bound"]),
        "paper_exact_boundary": (
            "The Euler lower-bound code path is independently checked. Exact "
            "mitten thickness three still requires the paper-instance Tanner graph "
            "and a machine-checkable three-layer planar decomposition."
        ),
    }


def _spectral_placement(params: dict[str, Any]) -> dict[str, Any]:
    adjacency = np.asarray(params["adjacency"], dtype=float)
    if adjacency.ndim != 2 or adjacency.shape[0] != adjacency.shape[1]:
        raise ValueError("adjacency must be square")
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    embedding = eigenvectors[:, 1:3]
    grid = np.asarray(params["grid"], dtype=float)
    if grid.shape != embedding.shape:
        raise ValueError("grid and two-dimensional embedding shapes must match")
    costs: list[tuple[float, tuple[int, ...]]] = []
    for assignment in permutations(range(grid.shape[0])):
        assigned = grid[np.asarray(assignment)]
        cost = float(np.sum((embedding - assigned) ** 2))
        costs.append((cost, assignment))
    optimum_cost, optimum_assignment = min(costs, key=lambda row: row[0])
    return {
        "mode": "reduced_spectral_assignment_validation",
        "laplacian_eigenvalues": eigenvalues.tolist(),
        "embedding": embedding.tolist(),
        "assignment": list(optimum_assignment),
        "assignment_cost": optimum_cost,
        "assignments_exhausted": len(costs),
        "passed": len(costs) == int(params["expected_assignments"]),
        "paper_exact_boundary": (
            "This validates the eigensolver and discrete assignment objective on "
            "a small graph; the unpublished optimized paper layouts remain unavailable."
        ),
    }


def _run_target(
    target_id: str,
    params: dict[str, Any],
    workspace: Path,
) -> dict[str, Any]:
    mode = str(params["mode"])
    if mode == "paper_code_subset":
        return _paper_code_subset(params, workspace)
    if mode == "magic_counts":
        return _magic_counts(params)
    if mode == "sqetch_reduced":
        return _sqetch_reduced(params)
    if mode == "realtime_arithmetic":
        return _realtime_arithmetic(params, workspace)
    if mode == "input_boundary":
        return _input_boundary(target_id, params)
    if mode == "exact_css_distance":
        return _exact_css_distance(params)
    if mode == "stochastic_distance":
        return _stochastic_distance(params)
    if mode == "general_css_identity":
        return _general_css_identity(params)
    if mode == "generic_pivot_hit":
        return _generic_pivot_hit(params)
    if mode == "relative_group_permutation":
        return _relative_group_permutation(params)
    if mode == "tanner_thickness_bound":
        return _tanner_thickness_bound(params)
    if mode == "spectral_placement":
        return _spectral_placement(params)
    raise ValueError(f"{target_id}: unsupported campaign mode {mode!r}")


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _read_json(config_path)
    targets = config.get("targets")
    if not isinstance(targets, dict) or tuple(sorted(targets)) != TARGET_IDS:
        raise ValueError("config must declare exactly T001-T024")
    workspace = config_path.resolve().parent.parent

    results: dict[str, dict[str, Any]] = {}
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id], workspace)
        result.update(
            {
                "schema_version": 1,
                "paper_id": config["paper_id"],
                "target_id": target_id,
                "campaign_scale": config["campaign_scale"],
                "scientific_coverage_promoted": False,
            }
        )
        passed = result.get("status") == "input_blocked" or bool(
            result.get("passed", False)
        )
        check = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "status": "passed" if passed else "failed",
            "implementation_attestation_only": True,
            "scientific_coverage_promoted": False,
            "result_mode": result["mode"],
        }
        _write_json(
            output_root / "data" / "implementation_closure" / f"{target_id}.json",
            result,
        )
        _write_json(
            output_root / "checks" / "implementation_closure" / f"{target_id}.json",
            check,
        )
        if not passed:
            raise RuntimeError(f"{target_id}: implementation validation failed")
        results[target_id] = result

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "campaign_scale": config["campaign_scale"],
        "target_ids": list(TARGET_IDS),
        "targets_attested": len(results),
        "input_blocked_targets": [
            target_id
            for target_id, result in results.items()
            if result.get("status") == "input_blocked"
        ],
        "scientific_coverage_promoted": False,
        "clean_room_boundary": config["clean_room_boundary"],
    }
    _write_json(output_root / "checks" / "implementation_closure" / "manifest.json", manifest)
    return manifest
