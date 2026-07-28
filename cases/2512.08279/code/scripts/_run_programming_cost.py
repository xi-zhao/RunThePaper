from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import resource
import time
from pathlib import Path

import cvxpy as cp
import numpy as np
import scipy

from src.programmable_lindbladian import (
    ProgrammingCostProblem,
    ProgrammingCostSolution,
    choi_absolute_diamond_upper_bound,
    contract_program_choi,
    diamond_norm_hp,
    diamond_norms_hp_batch,
    fig3_model,
)


WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "outputs" / "data"
CHECK_DIR = WORKSPACE / "outputs" / "checks"
BRANCHES = {
    "pure_damping": False,
    "damping_plus_z": True,
}


def _require_guard(stage: str) -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID") != "T002":
        raise SystemExit("run_programming_cost.py must be called through run_target.py for T002")
    if os.environ.get("PRAGENT_GUARDED_STAGE") != stage:
        raise SystemExit("script --stage must match PRAGENT_GUARDED_STAGE")


def _solution_row(
    branch: str,
    solution: ProgrammingCostSolution,
    *,
    time_points: int,
    time_grid: str,
    endpoint_half_diamond: float | None,
    full_grid_certificate: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "branch": branch,
        "epsilon": solution.epsilon,
        "kappa": solution.kappa,
        "gamma_log2": solution.gamma_log2,
        "p_plus": solution.p_plus,
        "p_minus": solution.p_minus,
        "status": solution.status,
        "solver": solution.solver,
        "iterations": solution.iterations,
        "solve_time_seconds": solution.solve_time_seconds,
        "solver_setup_time_seconds": solution.setup_time_seconds,
        "solver_internal_time_seconds": solution.solver_time_seconds,
        "trace_residual": solution.trace_residual,
        "signed_weight_residual": solution.signed_weight_residual,
        "minimum_eigenvalue_plus": solution.minimum_eigenvalue_plus,
        "minimum_eigenvalue_minus": solution.minimum_eigenvalue_minus,
        "worst_diamond_psd_violation": solution.worst_diamond_psd_violation,
        "worst_diamond_trace_violation": solution.worst_diamond_trace_violation,
        "endpoint_t10_half_diamond": endpoint_half_diamond,
        "time_points": time_points,
        "time_grid": time_grid,
        "full_grid_points": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["full_grid_points"]
        ),
        "unconstrained_grid_points": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["unconstrained_grid_points"]
        ),
        "unconstrained_max_half_diamond_upper_bound": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["maximum_half_diamond_upper_bound"]
        ),
        "unconstrained_max_upper_bound_excess": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["maximum_upper_bound_excess"]
        ),
        "unconstrained_worst_time": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["worst_time"]
        ),
        "full_source_grid_certified": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["certified"]
        ),
        "fast_certificate_points": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["fast_certificate_points"]
        ),
        "batch_exact_certificate_points": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["batch_exact_certificate_points"]
        ),
        "batch_diamond_seconds": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["batch_diamond_seconds"]
        ),
        "batch_diamond_status": (
            None
            if full_grid_certificate is None
            else full_grid_certificate["batch_diamond_status"]
        ),
    }


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (str(item["branch"]), float(item["epsilon"]))):
            writer.writerow(row)


def _serialize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    serializable: list[dict[str, object]] = []
    for row in rows:
        serializable.append(
            {
                key: (
                    None
                    if value is None
                    else bool(value)
                    if isinstance(value, np.bool_)
                    else int(value)
                    if isinstance(value, np.integer)
                    else float(value)
                    if isinstance(value, np.floating)
                    else value
                )
                for key, value in row.items()
            }
        )
    return serializable


def _run_branch(
    branch: str,
    times: np.ndarray,
    epsilons: list[float],
    *,
    solver_epsilon: float,
    max_iterations: int,
    evaluate_endpoint: bool,
    verification_times: np.ndarray | None,
    verification_tolerance: float,
) -> tuple[list[dict[str, object]], list[np.ndarray], dict[str, object]]:
    with_z = BRANCHES[branch]
    target_choi, programs = fig3_model(times, with_z_hamiltonian=with_z)
    build_start = time.perf_counter()
    problem = ProgrammingCostProblem(target_choi, programs)
    build_seconds = time.perf_counter() - build_start
    endpoint_targets, endpoint_programs = fig3_model(
        [10.0],
        with_z_hamiltonian=with_z,
    )
    verification_targets: list[np.ndarray] = []
    verification_programs: list[np.ndarray] = []
    active_verification_indices: set[int] = set()
    if verification_times is not None:
        verification_targets, verification_programs = fig3_model(
            verification_times,
            with_z_hamiltonian=with_z,
        )
        for active_time in times:
            matches = np.flatnonzero(
                np.isclose(verification_times, active_time, atol=1e-12, rtol=0.0)
            )
            if len(matches) != 1:
                raise RuntimeError(
                    f"active time {active_time} is not a unique verification-grid point"
                )
            active_verification_indices.add(int(matches[0]))
    rows: list[dict[str, object]] = []
    retrieval_matrices: list[np.ndarray] = []
    solve_order = sorted(epsilons, reverse=True)
    for epsilon in solve_order:
        solution = problem.solve(
            epsilon,
            solver_epsilon=solver_epsilon,
            max_iterations=max_iterations,
            warm_start=True,
        )
        endpoint_half_diamond = None
        if evaluate_endpoint:
            effective_endpoint = contract_program_choi(
                solution.retrieval_choi,
                endpoint_programs[0],
                system_dimension=2,
                program_dimension=4,
                output_dimension=2,
            )
            endpoint_result = diamond_norm_hp(
                effective_endpoint - endpoint_targets[0],
                input_dimension=2,
                output_dimension=2,
                solver_epsilon=max(2e-7, solver_epsilon / 10.0),
                max_iterations=max_iterations,
            )
            endpoint_half_diamond = 0.5 * endpoint_result.value
        full_grid_certificate = None
        if verification_times is not None:
            certified_values: list[float] = []
            certified_times: list[float] = []
            unresolved_differences: list[np.ndarray] = []
            unresolved_times: list[float] = []
            unconstrained_count = 0
            for index, (
                verification_time,
                verification_target,
                verification_program,
            ) in enumerate(
                zip(
                    verification_times,
                    verification_targets,
                    verification_programs,
                    strict=True,
                )
            ):
                if index in active_verification_indices:
                    continue
                unconstrained_count += 1
                effective = contract_program_choi(
                    solution.retrieval_choi,
                    verification_program,
                    system_dimension=2,
                    program_dimension=4,
                    output_dimension=2,
                )
                half_upper_bound = 0.5 * choi_absolute_diamond_upper_bound(
                    effective - verification_target,
                    input_dimension=2,
                    output_dimension=2,
                )
                if half_upper_bound <= float(epsilon) + verification_tolerance:
                    certified_values.append(half_upper_bound)
                    certified_times.append(float(verification_time))
                else:
                    unresolved_differences.append(effective - verification_target)
                    unresolved_times.append(float(verification_time))
            batch_result = diamond_norms_hp_batch(
                unresolved_differences,
                input_dimension=2,
                output_dimension=2,
                solver_epsilon=max(2e-6, solver_epsilon / 2.0),
                max_iterations=max_iterations,
            )
            batch_half_values = 0.5 * batch_result.values
            certified_values.extend(float(value) for value in batch_half_values)
            certified_times.extend(unresolved_times)
            if certified_values:
                worst_index = int(np.argmax(certified_values))
                worst_bound = float(certified_values[worst_index])
                worst_time = float(certified_times[worst_index])
            else:
                worst_bound = 0.0
                worst_time = None
            worst_excess = worst_bound - float(epsilon)
            batch_residual_ok = (
                batch_result.worst_psd_violation <= verification_tolerance
                and batch_result.worst_partial_trace_violation
                <= verification_tolerance
            )
            full_grid_certificate = {
                "full_grid_points": len(verification_times),
                "unconstrained_grid_points": unconstrained_count,
                "maximum_half_diamond_upper_bound": worst_bound,
                "maximum_upper_bound_excess": max(0.0, worst_excess),
                "worst_time": worst_time,
                "certified": bool(
                    worst_excess <= verification_tolerance
                    and batch_residual_ok
                    and batch_result.status
                    in {"optimal", "optimal_inaccurate", "not_needed"}
                ),
                "certificate": (
                    "Z=abs(J_delta) where sufficient; separable exact "
                    "Watrous SDPs for remaining times"
                ),
                "tolerance": verification_tolerance,
                "fast_certificate_points": len(certified_values)
                - len(batch_half_values),
                "batch_exact_certificate_points": len(batch_half_values),
                "batch_diamond_status": batch_result.status,
                "batch_diamond_seconds": batch_result.solve_time_seconds,
                "batch_diamond_iterations": batch_result.iterations,
                "batch_worst_psd_violation": batch_result.worst_psd_violation,
                "batch_worst_partial_trace_violation": (
                    batch_result.worst_partial_trace_violation
                ),
            }
        rows.append(
            _solution_row(
                branch,
                solution,
                time_points=len(times),
                time_grid=(
                    "0:0.01:9.99 (1000 direct constraints)"
                    if len(times) == 1000 and np.allclose(np.diff(times), 0.01)
                    else (
                        f"{len(times)} active source-grid constraints; "
                        f"all {len(verification_times)} source points certified"
                        if verification_times is not None
                        else f"linspace(0,9.99,{len(times)})"
                    )
                ),
                endpoint_half_diamond=endpoint_half_diamond,
                full_grid_certificate=full_grid_certificate,
            )
        )
        retrieval_matrices.append(solution.retrieval_choi)
        print(
            json.dumps(
                {
                    "branch": branch,
                    "epsilon": epsilon,
                    "kappa": solution.kappa,
                    "status": solution.status,
                    "seconds": solution.solve_time_seconds,
                    "iterations": solution.iterations,
                    "trace_residual": solution.trace_residual,
                    "worst_psd_violation": solution.worst_diamond_psd_violation,
                    "worst_trace_violation": solution.worst_diamond_trace_violation,
                    "endpoint_half_diamond": endpoint_half_diamond,
                    "full_grid_certificate": full_grid_certificate,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    metadata = {
        "branch": branch,
        "problem_build_seconds": build_seconds,
        "time_points": len(times),
        "scalar_variables": problem.problem.size_metrics.num_scalar_variables,
        "scalar_equalities": problem.problem.size_metrics.num_scalar_eq_constr,
        "scalar_inequalities": problem.problem.size_metrics.num_scalar_leq_constr,
        "max_data_dimension": problem.problem.size_metrics.max_data_dimension,
        "verification_time_points": (
            len(verification_times) if verification_times is not None else 0
        ),
        "verification_certificate": (
            "Z=abs(J_delta) plus separable exact Watrous SDPs"
            if verification_times is not None
            else None
        ),
    }
    return rows, retrieval_matrices, metadata


def _checks(rows: list[dict[str, object]], solver_epsilon: float) -> dict[str, object]:
    allowed_residual = max(5e-4, 25.0 * solver_epsilon)
    branches = {
        branch: sorted(
            [row for row in rows if row["branch"] == branch],
            key=lambda item: float(item["epsilon"]),
        )
        for branch in BRANCHES
    }
    status_ok = all(
        row["status"] in {"optimal", "optimal_inaccurate"}
        for row in rows
    )
    lower_bound_ok = all(float(row["kappa"]) >= 1.0 - allowed_residual for row in rows)
    trace_ok = all(float(row["trace_residual"]) <= allowed_residual for row in rows)
    weight_ok = all(
        float(row["signed_weight_residual"]) <= allowed_residual for row in rows
    )
    psd_ok = all(
        float(row["worst_diamond_psd_violation"]) <= allowed_residual for row in rows
    )
    diamond_trace_ok = all(
        float(row["worst_diamond_trace_violation"]) <= allowed_residual
        for row in rows
    )
    monotonicity_by_branch = {}
    for branch, branch_rows in branches.items():
        values = np.asarray([float(row["kappa"]) for row in branch_rows])
        monotonicity_by_branch[branch] = bool(
            np.all(np.diff(values) <= allowed_residual)
        )
    coherent_harder = True
    if branches["pure_damping"] and branches["damping_plus_z"]:
        blue = {
            round(float(row["epsilon"]), 12): float(row["kappa"])
            for row in branches["pure_damping"]
        }
        red = {
            round(float(row["epsilon"]), 12): float(row["kappa"])
            for row in branches["damping_plus_z"]
        }
        shared = sorted(set(blue) & set(red))
        coherent_harder = bool(
            shared
            and all(red[key] + allowed_residual >= blue[key] for key in shared)
        )
    endpoint_rows = [
        row for row in rows if row["endpoint_t10_half_diamond"] is not None
    ]
    endpoint_feasible = all(
        float(row["endpoint_t10_half_diamond"])
        <= float(row["epsilon"]) + allowed_residual
        for row in endpoint_rows
    )
    full_grid_rows = [
        row for row in rows if row["full_source_grid_certified"] is not None
    ]
    full_grid_certified = all(
        bool(row["full_source_grid_certified"]) for row in full_grid_rows
    )
    checks = {
        "solver_status_accepted": status_ok,
        "physical_lower_bound": lower_bound_ok,
        "trace_constraints_accepted": trace_ok,
        "signed_weight_identity_accepted": weight_ok,
        "diamond_psd_constraints_accepted": psd_ok,
        "diamond_trace_constraints_accepted": diamond_trace_ok,
        "monotonicity_by_branch": monotonicity_by_branch,
        "coherent_branch_not_easier": coherent_harder,
        "t10_endpoint_feasible_for_source_grid_solutions": endpoint_feasible,
        "all_1000_source_grid_points_certified": full_grid_certified,
        "allowed_residual": allowed_residual,
    }
    checks["all_required_passed"] = bool(
        status_ok
        and lower_bound_ok
        and trace_ok
        and weight_ok
        and psd_ok
        and diamond_trace_ok
        and all(monotonicity_by_branch.values())
        and coherent_harder
        and endpoint_feasible
        and full_grid_certified
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["exploratory", "final_reproduction"],
        required=True,
    )
    parser.add_argument(
        "--mode",
        choices=["profile", "final"],
        required=True,
    )
    parser.add_argument(
        "--branch",
        choices=["both", *BRANCHES],
        default="both",
    )
    parser.add_argument("--time-points", type=int, default=11)
    parser.add_argument(
        "--epsilons",
        default="0,0.1,0.2",
        help="Comma-separated exploratory epsilon values; final mode always uses 41 paper points.",
    )
    parser.add_argument("--solver-epsilon", type=float, default=2e-5)
    parser.add_argument("--max-iterations", type=int, default=100_000)
    parser.add_argument(
        "--verify-full-grid",
        action="store_true",
        help="For a profile, constrain a source-grid subset and certify all 1000 source points.",
    )
    args = parser.parse_args()
    _require_guard(args.stage)
    if args.mode == "final" and args.stage != "final_reproduction":
        raise SystemExit("final mode requires --stage final_reproduction")
    if args.mode == "profile" and args.stage != "exploratory":
        raise SystemExit("profile mode requires --stage exploratory")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if args.mode == "final":
        verification_times = np.arange(1000, dtype=float) * 0.01
        active_indices = np.unique(
            np.concatenate((np.arange(0, 1000, 10), np.array([999])))
        )
        times = verification_times[active_indices]
        epsilons = [index * 0.005 for index in range(41)]
        branches = list(BRANCHES)
        csv_path = DATA_DIR / "programming_cost.csv"
        summary_path = DATA_DIR / "programming_cost_summary.json"
        matrices_path = DATA_DIR / "programming_cost_retrieval_choi.npz"
        check_path = CHECK_DIR / "t002_final_run.json"
    else:
        if args.time_points < 2:
            raise SystemExit("--time-points must be at least 2")
        if args.verify_full_grid:
            verification_times = np.arange(1000, dtype=float) * 0.01
            active_indices = np.unique(
                np.rint(np.linspace(0, 999, args.time_points)).astype(int)
            )
            times = verification_times[active_indices]
        else:
            verification_times = None
            times = np.linspace(0.0, 9.99, args.time_points)
        epsilons = [float(value) for value in args.epsilons.split(",")]
        branches = list(BRANCHES) if args.branch == "both" else [args.branch]
        suffix = f"{'-'.join(branches)}_{len(times)}t"
        csv_path = DATA_DIR / f"exploratory_programming_cost_{suffix}.csv"
        summary_path = DATA_DIR / f"exploratory_programming_cost_{suffix}.json"
        matrices_path = DATA_DIR / f"exploratory_programming_cost_{suffix}.npz"
        check_path = CHECK_DIR / f"t002_profile_{suffix}.json"

    start = time.perf_counter()
    rows: list[dict[str, object]] = []
    matrices: dict[str, np.ndarray] = {}
    branch_metadata: list[dict[str, object]] = []
    for branch in branches:
        verification_tolerance = max(5e-4, 25.0 * args.solver_epsilon)
        branch_rows, retrievals, metadata = _run_branch(
            branch,
            times,
            epsilons,
            solver_epsilon=args.solver_epsilon,
            max_iterations=args.max_iterations,
            evaluate_endpoint=True,
            verification_times=verification_times,
            verification_tolerance=verification_tolerance,
        )
        rows.extend(branch_rows)
        branch_metadata.append(metadata)
        for row, retrieval in zip(branch_rows, retrievals, strict=True):
            key = f"{branch}_eps_{float(row['epsilon']):.3f}".replace(".", "p")
            matrices[key] = retrieval
        _write_rows(csv_path, rows)
    total_seconds = time.perf_counter() - start
    np.savez_compressed(matrices_path, **matrices)
    checks = _checks(rows, args.solver_epsilon)
    status = "passed" if checks["all_required_passed"] else "failed"
    max_rss_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    max_rss_bytes = (
        int(max_rss_raw)
        if platform.system() == "Darwin"
        else int(max_rss_raw * 1024)
    )
    profile_scale_estimate = None
    if args.mode == "profile":
        solve_seconds = sum(float(row["solve_time_seconds"]) for row in rows)
        solves = max(len(rows), 1)
        mean_solve = solve_seconds / solves
        profile_scale_estimate = {
            "measured_time_points": len(times),
            "measured_solves": solves,
            "mean_solve_seconds": mean_solve,
            "naive_82_solve_seconds_at_same_problem_size": mean_solve * 82.0,
            "warning": (
                "Canonicalization and cone size grow with time points; this is not "
                "the final estimate until a larger-grid profile is measured."
            ),
        }
    summary = {
        "schema_version": 1,
        "paper_id": "2512.08279",
        "target_id": "T002",
        "stage": args.stage,
        "mode": args.mode,
        "status": status,
        "generated_data_provenance": "independent_numerics",
        "source_arrays_used": False,
        "paper_parameters": {
            "system_dimension": 2,
            "damping_rate": 0.1,
            "hamiltonians": ["0", "Z"],
            "program_choi_copies": 1,
            "nominal_time_interval": [0.0, 10.0],
            "source_script_time_grid": "0:0.01:9.99 (1000 points)",
            "epsilon_grid": "0:0.005:0.2 (41 points)",
        },
        "run_parameters": {
            "branches": branches,
            "time_points": len(times),
            "time_min": float(times[0]),
            "time_max": float(times[-1]),
            "active_time_points": len(times),
            "full_source_grid_points_certified": (
                len(verification_times) if verification_times is not None else 0
            ),
            "epsilons": sorted(epsilons),
            "solver": "SCS",
            "solver_epsilon": args.solver_epsilon,
            "max_iterations": args.max_iterations,
        },
        "branch_problem_metadata": branch_metadata,
        "checks": checks,
        "rows": _serialize_rows(rows),
        "performance": {
            "total_seconds": total_seconds,
            "maximum_resident_set_bytes": max_rss_bytes,
            "profile_scale_estimate": profile_scale_estimate,
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "cvxpy": cp.__version__,
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "artifacts": {
            "csv": str(csv_path.relative_to(WORKSPACE)),
            "summary": str(summary_path.relative_to(WORKSPACE)),
            "retrieval_choi": str(matrices_path.relative_to(WORKSPACE)),
            "check": str(check_path.relative_to(WORKSPACE)),
        },
    }
    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    summary_path.write_text(text, encoding="utf-8")
    check_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
