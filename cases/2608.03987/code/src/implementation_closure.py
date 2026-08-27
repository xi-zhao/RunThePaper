"""Independent table emitters for the RealifyTN complexity claims.

The campaign consumes only the frozen clean circuit-input archive.  Author
trees, code, table arrays, source pixels, PDFs, and historical outputs are not
numerical inputs.
"""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path
from typing import Any

from benchmark_release import RANDOM_PANEL_ORDER
from independent_tn import ContractionTree, TensorNetwork


ITEMS_BY_TARGET = {
    "T010": ("Table 1 core",),
    "T011": ("Table 1 extension",),
    "T012": ("Table 5",),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _qubit_count(network: TensorNetwork) -> int:
    return sum(leaf.label.startswith("ket0[") for leaf in network.leaves)


def _step_dimensions(tree: ContractionTree, node: int) -> tuple[int, int, int, int]:
    left = tree.left[node]
    right = tree.right[node]
    left_boundary = tree.boundary[left]
    right_boundary = tree.boundary[right]
    contracted = left_boundary & right_boundary
    left_free = left_boundary - contracted
    right_free = right_boundary - contracted
    d_i = 1 << len(left_free)
    d_j = 1 << len(right_free)
    d_k = 1 << len(contracted)
    core_volume = d_i * d_j * d_k
    if core_volume != tree.volume[node]:
        raise ValueError("binary-index loop dimensions disagree with tree volume")
    return d_i, d_j, d_k, 1 << len(tree.boundary[node])


def independent_loop_complexity(tree: ContractionTree) -> dict[str, float]:
    """Accumulate the appendix loop-volume convention from tree primitives.

    The time path implements the printed merge factor
    ``kappa=3+6(1/Di+1/Dj+1/Dk)``.  Space and read/write are explicit
    independently declared working-set/touch conventions; they remain
    comparison-pending rather than being treated as paper-exact evidence.
    """

    time_real = 0
    time_oracle = 0
    real_touch_bytes = 0
    complex_touch_bytes = 0
    peak_real_elements = 0
    for node in range(tree.nleaves, len(tree.left)):
        left = tree.left[node]
        right = tree.right[node]
        d_i, d_j, d_k, output_size = _step_dimensions(tree, node)
        core = tree.volume[node]
        factor = tree.factor[node]
        left_size = 1 << len(tree.boundary[left])
        right_size = 1 << len(tree.boundary[right])
        base_touch = left_size + right_size + output_size
        complex_touch_bytes += 8 * base_touch
        if factor == 1:
            step_time = core
            oracle_time = core
            lane_touch = base_touch
            working = base_touch
        elif factor == 2:
            step_time = 2 * core
            oracle_time = 2 * core
            lane_touch = 2 * base_touch
            working = 2 * base_touch
        else:
            step_time = 3 * core + 6 * (
                d_i * d_j + d_i * d_k + d_j * d_k
            )
            kappa = 3.0 + 6.0 * (1.0 / d_i + 1.0 / d_j + 1.0 / d_k)
            oracle_time = int(round(core * kappa))
            lane_touch = 3 * base_touch + 2 * (d_i + d_j + d_k)
            working = 3 * output_size + 2 * (left_size + right_size)
        time_real += step_time
        time_oracle += oracle_time
        real_touch_bytes += 4 * lane_touch
        peak_real_elements = max(peak_real_elements, working)

    same_tree_law = tree.statistics().real_volume
    delta_time = math.log2(time_real) - math.log2(same_tree_law)
    return {
        "tc_R": math.log2(time_real),
        "sc_R": math.log2(peak_real_elements),
        "rwc_R": math.log2(real_touch_bytes),
        "delta_tc": delta_time,
        "delta_tc_excess": 2.0**delta_time - 1.0,
        "rwc_R_minus_rwc_C": math.log2(real_touch_bytes)
        - math.log2(complex_touch_bytes),
        "time_volume": float(time_real),
        "same_tree_law_volume": float(same_tree_law),
        "time_oracle_residual": float(abs(time_real - time_oracle)),
    }


def _table1_row(network: TensorNetwork, tree: ContractionTree, group: str) -> dict[str, Any]:
    statistics = tree.statistics()
    return {
        "group": group,
        "circuit": network.name,
        "qubits": _qubit_count(network),
        "complex_leaves": network.green_leaves,
        "total_leaves": len(network.leaves),
        "log2_real_cost": statistics.as_dict()["log2_real_volume"],
        "m": statistics.m,
        "r": statistics.r,
        "overhead": statistics.overhead,
        "law_value": statistics.law_value,
        "law_residual": abs(statistics.overhead - statistics.law_value),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def contraction_tree_from_plan(
    network: TensorNetwork, plan: dict[str, Any]
) -> ContractionTree:
    """Rebuild one independently generated tree from its frozen child pairs."""

    nleaves = len(network.leaves)
    children = plan.get("children")
    root = int(plan.get("root", -1))
    if plan.get("format") != "binary-tree-child-pairs-v1":
        raise ValueError("unsupported contraction-plan format")
    if int(plan.get("leaf_count", -1)) != nleaves:
        raise ValueError("plan leaf count does not match the clean circuit")
    if not isinstance(children, list) or len(children) != nleaves - 1:
        raise ValueError("a binary contraction plan needs exactly n-1 child pairs")

    node_count = 2 * nleaves - 1
    left = [-1] * node_count
    right = [-1] * node_count
    parent = [-1] * node_count
    for offset, pair in enumerate(children):
        node = nleaves + offset
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("every contraction-plan row must contain two children")
        a, b = map(int, pair)
        if not 0 <= a < node or not 0 <= b < node or a == b:
            raise ValueError("contraction-plan children must precede their parent")
        if parent[a] != -1 or parent[b] != -1:
            raise ValueError("a contraction-plan node cannot have two parents")
        left[node], right[node] = a, b
        parent[a] = parent[b] = node
    if root != node_count - 1 or parent[root] != -1:
        raise ValueError("contraction-plan root is not the final parentless node")
    return ContractionTree(network, left, right, parent, root)


def emit_paper_scale_table_outputs(
    records: list[dict[str, Any]],
    networks: dict[str, TensorNetwork],
    output_root: Path,
) -> dict[str, Any]:
    """Emit Table 1/5 values from the best full-search plan per declared circuit.

    Selection uses only independently generated records. Paper table values
    remain a post-hoc comparison source and never steer tree selection.
    """

    best: dict[str, dict[str, Any]] = {}
    for record in records:
        name = str(record["network"]["name"])
        prior = best.get(name)
        if prior is None or float(record["full_anneal"]["real_volume"]) < float(
            prior["full_anneal"]["real_volume"]
        ):
            best[name] = record

    missing = [
        name
        for name in RANDOM_PANEL_ORDER
        if name not in best or name not in networks
    ]
    if missing:
        raise ValueError(f"paper-scale table records are incomplete: {missing}")

    core = set(RANDOM_PANEL_ORDER[:9])
    table1_rows: list[dict[str, Any]] = []
    table5_rows: list[dict[str, Any]] = []
    selected_records: list[dict[str, Any]] = []
    for name in RANDOM_PANEL_ORDER:
        record = best[name]
        network = networks[name]
        tree = contraction_tree_from_plan(network, record["plans"]["full_anneal"])
        group = "core" if name in core else "extension"
        table1_rows.append(_table1_row(network, tree, group))
        table5_rows.append(
            {"group": group, "circuit": name, **independent_loop_complexity(tree)}
        )
        selected_records.append(
            {
                "circuit": name,
                "seed": int(record["search"]["seed"]),
                "plan_sha256": str(record["plans"]["full_anneal"]["sha256"]),
            }
        )

    table1_path = output_root / "table1_paper_scale.csv"
    table5_path = output_root / "table5_paper_scale.csv"
    _write_csv(table1_path, table1_rows)
    _write_csv(table5_path, table5_rows)
    return {
        "status": "ready_for_posthoc_paper_comparison",
        "T010_rows": 9,
        "T011_rows": 3,
        "T012_rows": 12,
        "table1_path": str(table1_path),
        "table5_path": str(table5_path),
        "selected_records": selected_records,
        "paper_values_used_for_selection": False,
    }


def run_campaign(
    config: dict[str, Any],
    output_root: Path,
    *,
    workspace: Path,
) -> dict[str, Any]:
    if config.get("paper_id") != "2608.03987":
        raise ValueError("paper_id must be 2608.03987")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if parameters.get("profile") != "reduced_greedy_attestation":
        raise ValueError("only the frozen reduced greedy profile is accepted")
    input_contract = parameters["input"]
    archive_relative = Path(input_contract["archive"])
    if (
        archive_relative.is_absolute()
        or ".." in archive_relative.parts
        or archive_relative.parts[:1] != ("inputs",)
    ):
        raise ValueError("input archive must be workspace-relative under inputs/")
    archive = workspace / archive_relative
    observed_hash = _sha256(archive)
    if observed_hash != input_contract["sha256"]:
        raise ValueError("clean circuit archive hash mismatch")

    # Imported lazily so the scientific module itself never reaches outside
    # the contract-declared clean input path.
    from run_independent_reimplementation import load_networks

    member_audit: list[str] = []
    networks = {network.name: network for network in load_networks(archive, member_audit=member_audit)}
    core = tuple(parameters["table1"]["core_circuits"])
    extension = tuple(parameters["table1"]["extension_circuits"])
    declared = core + extension
    if len(core) != 9 or len(extension) != 3 or declared != RANDOM_PANEL_ORDER:
        raise ValueError("the frozen 9+3 Table 1 boundary must equal RANDOM_PANEL_ORDER")
    if set(networks) & set(declared) != set(declared):
        raise ValueError("clean archive is missing one or more Table 1 circuits")

    table1_rows: list[dict[str, Any]] = []
    table5_rows: list[dict[str, Any]] = []
    seed = int(parameters["optimizer"]["seed"])
    for position, circuit in enumerate(declared):
        network = networks[circuit]
        tree = ContractionTree.greedy(network, "real", seed=seed + position)
        group = "core" if circuit in core else "extension"
        table1 = _table1_row(network, tree, group)
        table1_rows.append(table1)
        table5_rows.append(
            {
                "group": group,
                "circuit": circuit,
                **independent_loop_complexity(tree),
            }
        )

    _write_csv(output_root / "table1_random_complexity_audit.csv", table1_rows)
    _write_csv(output_root / "table5_independent_complexity_audit.csv", table5_rows)
    tolerance = float(parameters["acceptance"]["tolerance"])
    core_rows = [row for row in table1_rows if row["group"] == "core"]
    extension_rows = [row for row in table1_rows if row["group"] == "extension"]
    maximum_law_residual = max(float(row["law_residual"]) for row in table1_rows)
    maximum_oracle_residual = max(
        float(row["time_oracle_residual"]) for row in table5_rows
    )
    clean_member_boundary = (
        len(member_audit) == 122
        and all(
            "/circuits/" in member
            or "/experiments/structured-v1/formal-inputs/" in member
            for member in member_audit
        )
    )
    target_checks = {
        "T010": {
            "status": (
                "passed"
                if len(core_rows) == 9 and maximum_law_residual <= tolerance
                else "failed"
            ),
            "rows_emitted": len(core_rows),
            "maximum_cost_law_residual": maximum_law_residual,
            "independent_checks": ["tree_statistics_identity", "nine_row_partition"],
        },
        "T011": {
            "status": (
                "passed"
                if len(extension_rows) == 3 and maximum_law_residual <= tolerance
                else "failed"
            ),
            "rows_emitted": len(extension_rows),
            "maximum_cost_law_residual": maximum_law_residual,
            "independent_checks": ["tree_statistics_identity", "three_row_partition"],
        },
        "T012": {
            "status": (
                "passed"
                if len(table5_rows) == 12
                and maximum_oracle_residual <= tolerance
                and clean_member_boundary
                else "failed"
            ),
            "rows_emitted": len(table5_rows),
            "maximum_kappa_oracle_residual": maximum_oracle_residual,
            "clean_input_payloads_read": len(member_audit),
            "independent_checks": ["kappa_closed_form_oracle", "clean_input_member_audit"],
            "paper_table_comparison_executed": False,
        },
    }
    for check in target_checks.values():
        check["profile"] = parameters["profile"]
        check["paper_scale_executed"] = False

    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": (
                "attested" if target_checks[target_id]["status"] == "passed" else "failed"
            ),
            "scientific_coverage_changed": False,
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    status = (
        "passed"
        if all(check["status"] == "passed" for check in target_checks.values())
        else "failed"
    )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "profile": parameters["profile"],
        "fixed_item_denominator": len(item_results),
        "item_results": item_results,
        "target_checks": target_checks,
        "generated_outputs": [
            "outputs/checks/implementation_closure/table1_random_complexity_audit.csv",
            "outputs/checks/implementation_closure/table5_independent_complexity_audit.csv",
        ],
        "scientific_coverage_changed": False,
        "scientific_boundary": (
            "All 9+3 rows and the appendix accumulator are executable on a reduced "
            "independent greedy tree ensemble. Paper optimizer parity and post-hoc table "
            "comparison remain outside this attestation."
        ),
        "numerical_input_boundary": {
            "clean_circuit_archive_sha256": observed_hash,
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "author_trees_or_plans_read": False,
            "reference_pixels_read": False,
            "historical_outputs_read": False,
        },
    }
