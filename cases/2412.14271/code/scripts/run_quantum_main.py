#!/usr/bin/env python3
"""Finite-size reproduction via an independent Monte-Carlo unraveling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from src.dicke import trajectory_density, wigner_distribution


def cumulative_mean(result: dict[str, object], count: int) -> float:
    rho = result["cumulative_rho_photon"][count]
    distribution = np.maximum(np.real(np.diag(rho.full())), 0)
    distribution /= distribution.sum()
    return float(distribution @ np.arange(distribution.size))


def run_job(job: dict[str, object], parameters: dict[str, object]) -> dict[str, object]:
    return trajectory_density(
        int(job["N"]),
        int(job["M"]),
        float(job["lambda"]),
        omega_c=float(parameters["omega_c"]),
        omega_a=float(parameters["omega_a"]),
        kappa1=float(parameters["kappa1"]),
        kappa2=float(parameters["kappa2"]),
        final_time=float(job["final_time"]),
        trajectories=int(job["trajectories"]),
        seed=int(job["seed"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        parameters = json.load(handle)["parameters"]

    started = time.monotonic()
    wspec = parameters["wigner_axis"]
    wigner_axis = np.linspace(float(wspec[0]), float(wspec[1]), int(wspec[2]))
    arrays: dict[str, np.ndarray] = {"wigner_axis": wigner_axis}
    records: list[dict[str, object]] = []
    result_by_label: dict[str, dict[str, object]] = {}

    jobs = list(parameters["distribution_jobs"]) + list(parameters["branch_jobs"])
    for job_index, job in enumerate(jobs):
        job_started = time.monotonic()
        result = run_job(job, parameters)
        label = str(job["label"])
        result_by_label[label] = result
        rho = result["rho_photon"]
        matrix = rho.full()
        eigenvalues = np.linalg.eigvalsh((matrix + matrix.conjugate().T) / 2)
        counts = sorted(result["cumulative_rho_photon"])
        record = {
            **job,
            "runtime_seconds": time.monotonic() - job_started,
            "photon_mean": float(result["photon_mean"]),
            "spin_z_mean": float(result["spin_z_mean"]),
            "photon_tail": float(result["photon_tail"]),
            "trace_error": float(result["trace_error"]),
            "minimum_density_eigenvalue": float(eigenvalues.min()),
            "cumulative_photon_mean": {
                str(count): cumulative_mean(result, count) for count in counts
            },
        }
        records.append(record)
        arrays[f"{label}_fock"] = np.asarray(result["fock_distribution"])
        arrays[f"{label}_rho"] = matrix
        arrays[f"{label}_spin_z_runs"] = np.asarray(result["spin_z_runs"])
        if job in parameters["distribution_jobs"]:
            wigner = wigner_distribution(rho, wigner_axis)
            arrays[f"{label}_wigner"] = wigner
            dx = float(wigner_axis[1] - wigner_axis[0])
            record["wigner_integral"] = float(np.sum(wigner) * dx * dx)
            record["z4_rotation_relative_residual"] = float(
                np.linalg.norm(wigner - np.rot90(wigner))
                / max(np.linalg.norm(wigner), np.finfo(float).tiny)
            )
        print(
            f"[{job_index + 1}/{len(jobs)}] {label}: "
            f"n={record['photon_mean']:.4g}, tail={record['photon_tail']:.3g}, "
            f"seconds={record['runtime_seconds']:.1f}",
            flush=True,
        )

    # The six main distribution jobs are also the anchor points of Fig. 3(g).
    branch_records = records
    arrays["branch_N"] = np.asarray([record["N"] for record in branch_records], dtype=int)
    arrays["branch_lambda"] = np.asarray([record["lambda"] for record in branch_records], dtype=float)
    arrays["branch_photon_mean"] = np.asarray([record["photon_mean"] for record in branch_records])
    arrays["branch_photon_mean_4"] = np.asarray(
        [record["cumulative_photon_mean"]["4"] for record in branch_records]
    )
    arrays["branch_cutoff"] = np.asarray([record["M"] for record in branch_records], dtype=int)
    arrays["branch_tail"] = np.asarray([record["photon_tail"] for record in branch_records])

    output_data = Path("outputs/data")
    output_checks = Path("outputs/checks")
    output_data.mkdir(parents=True, exist_ok=True)
    output_checks.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_data / "main_quantum.npz", **arrays)

    distribution_records = records[: len(parameters["distribution_jobs"])]
    trace_max = max(float(record["trace_error"]) for record in records)
    tail_max = max(float(record["photon_tail"]) for record in distribution_records)
    wigner_integral_error = max(abs(float(record["wigner_integral"]) - 1) for record in distribution_records)
    convergence_deltas = [
        abs(float(record["photon_mean"]) - float(record["cumulative_photon_mean"]["4"]))
        for record in records
    ]
    checks = {
        "fig3_science.json": {
            "trace_error_max": trace_max,
            "cutoff_tail_max": tail_max,
            "all_density_matrices_positive_within_sampling_tolerance": bool(
                min(float(record["minimum_density_eigenvalue"]) for record in records) >= -1e-10
            ),
            "stabilized_distributions_resolved_from_cutoff": bool(tail_max < 0.02),
            "method_variant": "quantum trajectories for all N; paper uses ED for N=5 and trajectories for larger N",
        },
        "fig4_science.json": {
            "wigner_integral_error_max": wigner_integral_error,
            "z4_rotation_relative_residual_by_job": {
                str(record["label"]): float(record["z4_rotation_relative_residual"])
                for record in distribution_records
            },
            "wigner_input": "generated reduced photon density matrices only",
        },
        "figS5_science.json": {
            "paper_trajectory_counts": [500, 3000],
            "reproduced_trajectory_counts": [4, "job final count (6-16)"],
            "absolute_mean_change_max": max(convergence_deltas),
            "fidelity": "reduced convergence diagnostic; paper-scale trajectory counts deferred by compute budget",
        },
    }
    for filename, content in checks.items():
        with (output_checks / filename).open("w", encoding="utf-8") as handle:
            json.dump(content, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    summary = {
        "schema_version": 1,
        "paper_id": "2412.14271",
        "method": "QuTiP Monte-Carlo unraveling from dense Haar initial states",
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_numeric_data_used": False,
        "parameters": parameters,
        "runtime_seconds": time.monotonic() - started,
        "jobs": records,
        "fidelity": {
            "level": "feature_reproduced_candidate",
            "paper_exact": False,
            "reason": "independent reduced-count trajectories replace 3000-trajectory and small-N ED production runs",
        },
    }
    with (output_data / "main_quantum_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"runtime_seconds": summary["runtime_seconds"], "jobs": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
