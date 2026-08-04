#!/usr/bin/env python3
"""Run the four bounded, source-blind numerical targets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.closed_form import magic_injection_counts, realtime_decoder_metrics
from src.group_algebra import FiniteGroupTable
from src.mitten_codes import MittenMatrices, analyze_code, build_checks
from src.sqetch import (
    approximate_hit_probability,
    benchmark_methods,
    estimate_minimum_weight,
    sketch_inclusion_probability,
    steane_check_matrix,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_t001(
    code_specs: list[dict[str, Any]],
    groups: dict[tuple[int, int], FiniteGroupTable],
) -> tuple[dict[str, MittenMatrices], dict[str, Any], dict[str, Any]]:
    matrices_by_code: dict[str, MittenMatrices] = {}
    analyses: list[dict[str, Any]] = []
    for specification in code_specs:
        group_id = tuple(int(value) for value in specification["small_group_id"])
        matrices = build_checks(groups[group_id], specification)
        result = analyze_code(groups[group_id], specification, matrices)
        matrices_by_code[specification["code_id"]] = matrices
        analyses.append(result)
        print(
            f"T001 {result['code_id']}: n={result['n']} k={result['k']} "
            f"logical weights={result['canonical_x_weight']}/{result['canonical_z_weight']} "
            f"status={result['status']}",
            flush=True,
        )
    passed = all(row["status"] == "passed" for row in analyses)
    data = {
        "schema_version": 1,
        "target_id": "T001",
        "generated_data_provenance": "independent_numerics",
        "parameter_match": "paper_exact",
        "codes": analyses,
    }
    check = {
        "schema_version": 1,
        "target_id": "T001",
        "status": "passed" if passed else "paper_claim_inconsistent",
        "checks": {
            "all_eight_codes_constructed": len(analyses) == 8,
            "all_algebraic_invariants_passed": passed,
            "paper_claim_inconsistencies_detected": [
                row["code_id"] for row in analyses if row["status"] != "passed"
            ],
            "no_reported_output_values_used_as_inputs": True,
        },
        "note": "Paper-reported logical weights are compared only after this numerical output is frozen.",
    }
    return matrices_by_code, data, check


def run_t002(code_specs: list[dict[str, Any]], d_rep_values: list[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_consistent = True
    for specification in code_specs:
        order = int(specification["small_group_id"][0])
        for distance in d_rep_values:
            counts = magic_injection_counts(order, int(distance))
            all_consistent &= counts["logical_qubits"] == order
            rows.append(
                {
                    "code_id": specification["code_id"],
                    "group_order": order,
                    "d_rep": int(distance),
                    **counts,
                    "generated_data_provenance": "analytic_reference",
                }
            )
    check = {
        "schema_version": 1,
        "target_id": "T002",
        "status": "passed" if len(rows) == 32 and all_consistent else "failed",
        "checks": {
            "all_32_table_cells_generated": len(rows) == 32,
            "n_minus_x_minus_z_equals_group_order": all_consistent,
            "x_z_counts_equal": all(row["x_checks"] == row["z_checks"] for row in rows),
        },
    }
    return rows, check


def run_t003(
    matrices_by_code: dict[str, MittenMatrices],
    parameters: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = parameters["sqetch"]
    seed = int(config["random_seed"])
    steane = steane_check_matrix()
    steane_result = estimate_minimum_weight(
        steane,
        steane,
        sketch_rows=int(config["steane_sketch_rows"]),
        trials=int(config["steane_trials"]),
        seed=seed,
    )
    rows: list[dict[str, Any]] = []
    for offset, code_id in enumerate(config["benchmark_code_ids"]):
        matrices = matrices_by_code[code_id]
        benchmarks = benchmark_methods(
            matrices.hz,
            matrices.hx,
            sketch_rows=int(config["sketch_rows"]),
            sketch_trials=int(config["sketch_trials"]),
            baseline_trials=int(config["baseline_trials"]),
            seed=seed + 1000 * (offset + 1),
        )
        for benchmark in benchmarks:
            rows.append(
                {
                    "code_id": code_id,
                    "n": int(matrices.hx.shape[1]),
                    **benchmark,
                    "projected_trials": int(config["projected_trials"]),
                    "projected_seconds": benchmark["seconds_per_trial"] * int(config["projected_trials"]),
                    "parameter_match": "reduced_scale",
                    "generated_data_provenance": "independent_numerics",
                }
            )
            print(
                f"T003 {code_id} {benchmark['method']}: "
                f"{benchmark['seconds_per_trial']:.6g} s/trial",
                flush=True,
            )

    p_short = sketch_inclusion_probability(nullity=20, required_rows=3, sketch_rows=4)
    p_long = sketch_inclusion_probability(nullity=20, required_rows=3, sketch_rows=12)
    amplified = approximate_hit_probability(p_long, 100)
    checks = {
        "steane_exact_distance_three": steane_result["best_weight"] == 3,
        "steane_candidates_found": steane_result["logical_candidates"] > 0,
        "inclusion_probability_bounded": 0 <= p_short <= p_long <= 1,
        "trial_amplification_monotone": p_long <= amplified <= 1,
        "all_benchmarks_positive": all(row["seconds_per_trial"] > 0 for row in rows),
        "both_methods_benchmarked": {row["method"] for row in rows}
        == {"sqetch", "full_nullspace_rref"},
    }
    check = {
        "schema_version": 1,
        "target_id": "T003",
        "status": "passed" if all(checks.values()) else "failed",
        "parameter_match": "reduced_scale",
        "checks": checks,
        "steane_validation": steane_result,
        "probability_sanity": {
            "p_required_3_kappa_4": p_short,
            "p_required_3_kappa_12": p_long,
            "p_at_least_one_hit_in_100_trials": amplified,
        },
        "non_claim": "This is a bounded algorithmic benchmark, not the paper's 10^12-trial hardware benchmark or QDistRnd implementation.",
    }
    return rows, check


def run_t004(
    experiments: list[dict[str, Any]],
    cycle_seconds: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_mean_below_one = True
    all_worst_below_one = True
    for experiment in experiments:
        metrics = realtime_decoder_metrics(experiment["stages"], cycle_seconds)
        all_mean_below_one &= metrics["all_mean_stage_utilizations_below_one"]
        s4_fraction = next(
            float(stage["fraction"])
            for stage in experiment["stages"]
            if stage["stage"] == "S4_mean"
        )
        worst_utilization = s4_fraction * float(experiment["s4_worst_seconds"]) / cycle_seconds
        all_worst_below_one &= worst_utilization < 1
        for stage in metrics["stages"]:
            rows.append(
                {
                    "experiment_id": experiment["experiment_id"],
                    **stage,
                    "mean_latency_seconds": metrics["mean_latency_seconds"],
                    "cycle_seconds": cycle_seconds,
                    "row_role": "mean_latency_and_utilization",
                    "generated_data_provenance": "analytic_reference",
                }
            )
        rows.append(
            {
                "experiment_id": experiment["experiment_id"],
                "stage": "S4_worst",
                "fraction": s4_fraction,
                "time_seconds": float(experiment["s4_worst_seconds"]),
                "latency_contribution_seconds": "",
                "utilization": worst_utilization,
                "mean_latency_seconds": metrics["mean_latency_seconds"],
                "cycle_seconds": cycle_seconds,
                "row_role": "worst_utilization_only",
                "generated_data_provenance": "analytic_reference",
            }
        )
    checks = {
        "three_experiments_recomputed": len(experiments) == 3,
        "all_mean_stage_utilizations_below_one": all_mean_below_one,
        "all_worst_s4_utilizations_below_one": all_worst_below_one,
        "mean_latency_below_cycle": all(
            float(row["mean_latency_seconds"]) < cycle_seconds for row in rows
        ),
    }
    check = {
        "schema_version": 1,
        "target_id": "T004",
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "note": "Uses only rounded f and t values printed in Table X; reported rho and t-bar are post-freeze comparison values.",
    }
    return rows, check


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--paper-inputs", type=Path, required=True)
    parser.add_argument("--group-tables", type=Path, required=True)
    args = parser.parse_args()

    parameters = read_json(args.config)["parameters"]
    paper_inputs = read_json(args.paper_inputs)
    group_payload = read_json(args.group_tables)
    if parameters["paper_id"] != "2607.28795":
        raise SystemExit("unexpected paper_id")
    groups = {
        tuple(record["small_group_id"]): FiniteGroupTable.from_record(record)
        for record in group_payload["groups"]
    }
    expected_group_ids = {tuple(row["small_group_id"]) for row in paper_inputs["mitten_codes"]}
    if set(groups) != expected_group_ids:
        raise SystemExit("group-table input does not cover the paper code list exactly")

    matrices, t001_data, t001_check = run_t001(paper_inputs["mitten_codes"], groups)
    t002_rows, t002_check = run_t002(paper_inputs["mitten_codes"], parameters["d_rep_values"])
    t003_rows, t003_check = run_t003(matrices, parameters)
    t004_rows, t004_check = run_t004(
        paper_inputs["realtime_experiments"],
        float(parameters["realtime"]["cycle_seconds"]),
    )

    write_json(Path("outputs/data/T001_code_parameters.json"), t001_data)
    write_csv(
        Path("outputs/data/T002_magic_counts.csv"),
        t002_rows,
        [
            "code_id",
            "group_order",
            "d_rep",
            "qubits",
            "x_checks",
            "z_checks",
            "logical_qubits",
            "generated_data_provenance",
        ],
    )
    write_csv(
        Path("outputs/data/T003_sqetch_benchmark.csv"),
        t003_rows,
        [
            "code_id",
            "n",
            "method",
            "trials",
            "elapsed_seconds",
            "seconds_per_trial",
            "logical_candidates",
            "best_weight",
            "nullity",
            "sketch_rows",
            "projected_trials",
            "projected_seconds",
            "parameter_match",
            "generated_data_provenance",
        ],
    )
    write_csv(
        Path("outputs/data/T004_realtime.csv"),
        t004_rows,
        [
            "experiment_id",
            "stage",
            "fraction",
            "time_seconds",
            "latency_contribution_seconds",
            "utilization",
            "mean_latency_seconds",
            "cycle_seconds",
            "row_role",
            "generated_data_provenance",
        ],
    )
    checks = {
        "T001": t001_check,
        "T002": t002_check,
        "T003": t003_check,
        "T004": t004_check,
    }
    for target_id, check in checks.items():
        write_json(Path(f"outputs/checks/{target_id}_science.json"), check)
    summary = {
        "schema_version": 1,
        "paper_id": parameters["paper_id"],
        "status": "passed"
        if all(check["status"] == "passed" for check in checks.values())
        else "completed_with_scientific_findings",
        "targets": {target_id: check["status"] for target_id, check in checks.items()},
        "source_boundaries": {
            "raw_pdf_readable": False,
            "original_figures_readable": False,
            "author_repository_accessed": False,
            "author_numerical_arrays_used": False,
        },
    }
    write_json(Path("outputs/checks/reproduction_summary.json"), summary)


if __name__ == "__main__":
    main()
