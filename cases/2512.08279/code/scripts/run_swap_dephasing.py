from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import cvxpy as cp
import numpy as np
import scipy

from src.programmable_lindbladian import (
    decompose_hptp_processor,
    quasi_sample_swap_dephasing,
    swap_program_processor_choi,
)


WORKSPACE = Path(__file__).resolve().parents[1]
DATA_DIR = WORKSPACE / "outputs" / "data"
CHECK_DIR = WORKSPACE / "outputs" / "checks"


def _require_guard(stage: str) -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID") != "T001":
        raise SystemExit("run_swap_dephasing.py must be called through run_target.py for T001")
    if os.environ.get("PRAGENT_GUARDED_STAGE") != stage:
        raise SystemExit("script --stage must match PRAGENT_GUARDED_STAGE")


def _write_csv(path: Path, result: dict[str, np.ndarray]) -> None:
    fieldnames = [
        "time",
        "exact_overlap",
        "direct_liouvillian_overlap",
        "quasi_sampled_overlap",
        "standard_error",
        "confidence_low_95",
        "confidence_high_95",
        "coherent_branch_count",
        "plus_inner_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for index in range(len(result["time"])):
            sampled = float(result["quasi_sampled_overlap"][index])
            standard_error = float(result["standard_error"][index])
            writer.writerow(
                {
                    "time": f"{float(result['time'][index]):.10g}",
                    "exact_overlap": f"{float(result['exact_overlap'][index]):.15g}",
                    "direct_liouvillian_overlap": (
                        f"{float(result['direct_liouvillian_overlap'][index]):.15g}"
                    ),
                    "quasi_sampled_overlap": f"{sampled:.15g}",
                    "standard_error": f"{standard_error:.15g}",
                    "confidence_low_95": f"{sampled - 1.96 * standard_error:.15g}",
                    "confidence_high_95": f"{sampled + 1.96 * standard_error:.15g}",
                    "coherent_branch_count": int(result["coherent_branch_count"][index]),
                    "plus_inner_count": int(result["plus_inner_count"][index]),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["exploratory", "final_reproduction"],
        required=True,
    )
    parser.add_argument("--solver-epsilon", type=float, default=1e-7)
    args = parser.parse_args()
    _require_guard(args.stage)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    processor_choi = swap_program_processor_choi()
    decomposition = decompose_hptp_processor(
        processor_choi,
        input_dimension=8,
        output_dimension=4,
        solver_epsilon=args.solver_epsilon,
    )
    times = np.linspace(0.0, 10.0, 101)
    sampled = quasi_sample_swap_dephasing(
        times,
        decomposition,
        lambda_value=0.5,
        outer_cycles=1000,
        inner_samples=200,
        seed=251208279,
    )
    runtime = time.perf_counter() - start

    prefix = "" if args.stage == "final_reproduction" else "exploratory_"
    csv_path = DATA_DIR / f"{prefix}swap_dephasing.csv"
    summary_path = DATA_DIR / f"{prefix}swap_dephasing_summary.json"
    npz_path = DATA_DIR / f"{prefix}swap_processor_decomposition.npz"
    check_path = CHECK_DIR / (
        "t001_final_run.json"
        if args.stage == "final_reproduction"
        else "t001_exploratory_run.json"
    )

    _write_csv(csv_path, sampled)
    np.savez_compressed(
        npz_path,
        processor_choi=processor_choi,
        choi_plus_subnormalized=decomposition.choi_plus_subnormalized,
        choi_minus_subnormalized=decomposition.choi_minus_subnormalized,
        choi_plus_channel=decomposition.choi_plus_channel,
        choi_minus_channel=decomposition.choi_minus_channel,
    )

    analytic_liouvillian_error = float(
        np.max(
            np.abs(
                sampled["exact_overlap"]
                - sampled["direct_liouvillian_overlap"]
            )
        )
    )
    residual = sampled["quasi_sampled_overlap"] - sampled["exact_overlap"]
    rmse = float(np.sqrt(np.mean(residual**2)))
    mean_bias = float(np.mean(residual))
    max_abs_residual = float(np.max(np.abs(residual)))
    nonzero_error = sampled["standard_error"] > 0
    normalized = np.abs(residual[nonzero_error]) / sampled["standard_error"][nonzero_error]
    maximum_standardized_residual = (
        float(np.max(normalized)) if len(normalized) else 0.0
    )
    within_three_standard_errors = (
        float(np.mean(normalized <= 3.0)) if len(normalized) else 1.0
    )
    checks = {
        "analytic_liouvillian_match": analytic_liouvillian_error <= 1e-11,
        "decomposition_status_accepted": decomposition.status
        in {"optimal", "optimal_inaccurate"},
        "processor_overhead_matches_two": abs(decomposition.objective - 2.0) <= 1e-4,
        "signed_weights_trace_preserving": (
            abs((decomposition.p_plus - decomposition.p_minus) - 1.0) <= 1e-6
        ),
        "decomposition_residual_accepted": decomposition.decomposition_residual <= 1e-5,
        "trace_residual_accepted": decomposition.primal_trace_residual <= 1e-5,
        "branch_positivity_accepted": min(
            decomposition.minimum_eigenvalue_plus,
            decomposition.minimum_eigenvalue_minus,
        )
        >= -1e-5,
        "sampling_bias_accepted": abs(mean_bias) <= max(
            3.0 * float(np.mean(sampled["standard_error"])),
            0.003,
        ),
        "sampling_coverage_accepted": within_three_standard_errors >= 0.95,
    }
    status = "passed" if all(checks.values()) else "failed"
    summary = {
        "schema_version": 1,
        "paper_id": "2512.08279",
        "target_id": "T001",
        "stage": args.stage,
        "status": status,
        "generated_data_provenance": "independent_numerics",
        "source_arrays_used": False,
        "paper_parameters": {
            "lambda": 0.5,
            "time_interval": [0.0, 10.0],
            "time_points": 101,
            "outer_cycles": 1000,
            "inner_hptp_samples": 200,
            "initial_state": "|01>",
            "observable": "|01><01|",
        },
        "generated_controls": {
            "random_seed": 251208279,
            "solver_epsilon": args.solver_epsilon,
        },
        "decomposition": {
            "program_dimension": 2,
            "processor_choi_shape": list(processor_choi.shape),
            "p_plus": decomposition.p_plus,
            "p_minus": decomposition.p_minus,
            "kappa": decomposition.objective,
            "status": decomposition.status,
            "solver": decomposition.solver,
            "iterations": decomposition.iterations,
            "solve_time_seconds": decomposition.solve_time_seconds,
            "trace_residual": decomposition.primal_trace_residual,
            "decomposition_residual": decomposition.decomposition_residual,
            "minimum_eigenvalue_plus": decomposition.minimum_eigenvalue_plus,
            "minimum_eigenvalue_minus": decomposition.minimum_eigenvalue_minus,
        },
        "metrics": {
            "analytic_liouvillian_max_abs_error": analytic_liouvillian_error,
            "quasi_sampling_rmse": rmse,
            "quasi_sampling_mean_bias": mean_bias,
            "quasi_sampling_max_abs_residual": max_abs_residual,
            "maximum_standardized_residual": maximum_standardized_residual,
            "fraction_within_three_standard_errors": within_three_standard_errors,
            "mean_standard_error": float(np.mean(sampled["standard_error"])),
        },
        "checks": checks,
        "runtime": {
            "total_seconds": runtime,
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "cvxpy": cp.__version__,
            "machine": os.uname().machine if hasattr(os, "uname") else "unknown",
        },
        "artifacts": {
            "csv": str(csv_path.relative_to(WORKSPACE)),
            "summary": str(summary_path.relative_to(WORKSPACE)),
            "decomposition": str(npz_path.relative_to(WORKSPACE)),
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
