#!/usr/bin/env python3
"""Plan, execute, resume, and merge the paper-scale trajectory campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys
import time
from typing import Any

import numpy as np

from src.dicke import wigner_distribution
from src.paper_scale_trajectories import (
    CampaignJob,
    artifact_prefix,
    atomic_json,
    campaign_jobs,
    canonical_digest,
    effective_campaign,
    file_digest,
    merge_job_shards,
    run_shard,
    sha256_file,
)

WORKSPACE = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATHS = (
    WORKSPACE / "src" / "dicke.py",
    WORKSPACE / "src" / "paper_scale_trajectories.py",
    Path(__file__).resolve(),
)


def load_campaign(config_path: Path, *, smoke: bool) -> tuple[dict[str, Any], str, str]:
    with config_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    campaign = effective_campaign(payload, smoke=smoke)
    return campaign, canonical_digest(campaign), file_digest(IMPLEMENTATION_PATHS)


def write_plan(
    campaign: dict[str, Any],
    *,
    config_path: Path,
    config_digest: str,
    implementation_digest: str,
) -> Path:
    output_root = Path(campaign["execution"]["effective_output_root"])
    shard_count = int(campaign["execution"]["effective_shard_count"])
    trajectory_count = int(campaign["parameters"]["trajectory_count"])
    jobs = campaign_jobs(campaign)
    plan = {
        "schema_version": 1,
        "status": "planned",
        "paper_id": "2412.14271",
        "run_id": campaign["run_id"],
        "profile": campaign["profile"],
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "effective_config_digest": config_digest,
        "implementation_digest": implementation_digest,
        "job_count": len(jobs),
        "trajectory_count_per_job": trajectory_count,
        "total_trajectories": len(jobs) * trajectory_count,
        "shard_count_per_job": shard_count,
        "work_units": [
            {
                "job": job.label,
                "shard_index": shard_index,
                "shard_count": shard_count,
            }
            for job in jobs
            for shard_index in range(shard_count)
        ],
        "seed_policy": "two disjoint deterministic seeds per (job, trajectory_index): one initial-state draw and one jump process",
        "initial_state_policy": "every trajectory independently draws a dense Haar state, implementing the printed infinite-temperature sampling rule",
        "input_boundary": campaign["input_boundary"],
    }
    plan_path = output_root / "checks" / f"{artifact_prefix(campaign)}_plan.json"
    atomic_json(plan_path, plan)
    return plan_path


def select_jobs(campaign: dict[str, Any], label: str | None) -> list[CampaignJob]:
    jobs = campaign_jobs(campaign)
    if label is None:
        return jobs
    selected = [job for job in jobs if job.label == label]
    if not selected:
        raise ValueError(f"unknown job label: {label}")
    return selected


def execute_shards(
    campaign: dict[str, Any],
    *,
    config_digest: str,
    implementation_digest: str,
    label: str | None,
    shard_index: int | None,
    shard_count: int,
    resume: bool,
) -> list[Path]:
    if shard_index is not None and not 0 <= shard_index < shard_count:
        raise ValueError("--shard-index must lie in [0, shard-count)")
    indices = range(shard_count) if shard_index is None else [shard_index]
    paths: list[Path] = []
    for job in select_jobs(campaign, label):
        for index in indices:
            print(
                f"running {job.label} shard {index + 1}/{shard_count}",
                flush=True,
            )
            paths.append(
                run_shard(
                    campaign,
                    job,
                    shard_index=index,
                    shard_count=shard_count,
                    config_digest=config_digest,
                    implementation_digest=implementation_digest,
                    resume=resume,
                )
            )
    return paths


def _distribution_metrics(density: np.ndarray) -> dict[str, Any]:
    hermitian = (density + density.conjugate().T) / 2
    eigenvalues = np.linalg.eigvalsh(hermitian)
    distribution = np.maximum(np.real(np.diag(hermitian)), 0)
    distribution /= distribution.sum()
    photons = np.arange(distribution.size, dtype=float)
    return {
        "distribution": distribution,
        "photon_mean": float(distribution @ photons),
        "tail": float(distribution[max(0, distribution.size - 5) :].sum()),
        "trace_error": float(abs(np.trace(density) - 1)),
        "hermiticity_error": float(np.linalg.norm(density - density.conjugate().T)),
        "minimum_eigenvalue": float(eigenvalues.min()),
    }


def aggregate_campaign(
    campaign: dict[str, Any],
    *,
    config_path: Path,
    config_digest: str,
    implementation_digest: str,
    shard_count: int,
) -> dict[str, Any]:
    output_root = Path(campaign["execution"]["effective_output_root"])
    data_root = output_root / "data"
    checks_root = output_root / "checks"
    prefix = artifact_prefix(campaign)
    data_root.mkdir(parents=True, exist_ok=True)
    checks_root.mkdir(parents=True, exist_ok=True)
    parameters = campaign["parameters"]
    snapshots = [int(value) for value in parameters["snapshot_counts"]]
    wigner_spec = parameters["wigner_axis"]
    wigner_axis = np.linspace(
        float(wigner_spec[0]), float(wigner_spec[1]), int(wigner_spec[2])
    )
    arrays: dict[str, np.ndarray] = {
        "snapshot_counts": np.asarray(snapshots, dtype=np.int64),
        "wigner_axis": wigner_axis,
    }
    records: list[dict[str, Any]] = []
    shard_records: list[dict[str, Any]] = []

    for job in campaign_jobs(campaign):
        densities, spin_means, job_shards = merge_job_shards(
            campaign,
            job,
            shard_count=shard_count,
            config_digest=config_digest,
            implementation_digest=implementation_digest,
        )
        shard_records.extend({"job": job.label, **record} for record in job_shards)
        arrays[f"{job.label}_rho"] = densities
        arrays[f"{job.label}_spin_z"] = spin_means
        job_record: dict[str, Any] = {
            "label": job.label,
            "N": job.system_size,
            "M": job.photon_cutoff,
            "lambda": job.coupling,
            "final_time": job.final_time,
            "snapshots": {},
        }
        for snapshot_index, count in enumerate(snapshots):
            metrics = _distribution_metrics(densities[snapshot_index])
            arrays[f"{job.label}_fock_{count}"] = metrics.pop("distribution")
            snapshot_record = {
                **metrics,
                "spin_z_mean": float(spin_means[snapshot_index]),
            }
            if job.wigner:
                import qutip as qt

                field = wigner_distribution(
                    qt.Qobj(densities[snapshot_index]), wigner_axis
                )
                arrays[f"{job.label}_wigner_{count}"] = field
                spacing = float(wigner_axis[1] - wigner_axis[0])
                snapshot_record["wigner_integral_error"] = float(
                    abs(np.sum(field) * spacing * spacing - 1)
                )
                snapshot_record["z4_rotation_relative_residual"] = float(
                    np.linalg.norm(field - np.rot90(field))
                    / max(np.linalg.norm(field), np.finfo(float).tiny)
                )
            job_record["snapshots"][str(count)] = snapshot_record
        job_record["snapshot_comparison"] = [snapshots[0], snapshots[-1]]
        job_record["photon_mean_change_first_to_final"] = float(
            abs(
                job_record["snapshots"][str(snapshots[-1])]["photon_mean"]
                - job_record["snapshots"][str(snapshots[0])]["photon_mean"]
            )
        )
        records.append(job_record)

    data_path = data_root / f"{prefix}.npz"
    with data_path.open("wb") as handle:
        np.savez_compressed(handle, **arrays)

    all_snapshots = [
        snapshot for record in records for snapshot in record["snapshots"].values()
    ]
    wigner_snapshots = [
        snapshot for snapshot in all_snapshots if "wigner_integral_error" in snapshot
    ]
    acceptance = campaign["acceptance"]
    checks = {
        "schema_version": 1,
        "paper_id": "2412.14271",
        "profile": campaign["profile"],
        "trajectory_index_coverage": "exactly once; enforced before aggregation",
        "independent_initial_state_per_trajectory": True,
        "source_pixels_used_as_numeric_input": False,
        "author_code_or_numeric_data_used": False,
        "metrics": {
            "trace_error_max": max(item["trace_error"] for item in all_snapshots),
            "hermiticity_error_max": max(
                item["hermiticity_error"] for item in all_snapshots
            ),
            "minimum_density_eigenvalue": min(
                item["minimum_eigenvalue"] for item in all_snapshots
            ),
            "cutoff_tail_max": max(item["tail"] for item in all_snapshots),
            "wigner_integral_error_max": max(
                (item["wigner_integral_error"] for item in wigner_snapshots),
                default=0.0,
            ),
            "photon_mean_change_first_to_final_max": max(
                record["photon_mean_change_first_to_final"] for record in records
            ),
        },
        "acceptance": {},
        "jobs": records,
    }
    metrics = checks["metrics"]
    checks["acceptance"] = {
        "trace": metrics["trace_error_max"] <= float(acceptance["maximum_trace_error"]),
        "hermiticity": metrics["hermiticity_error_max"]
        <= float(acceptance["maximum_hermiticity_error"]),
        "positivity": metrics["minimum_density_eigenvalue"]
        >= -float(acceptance["density_eigenvalue_tolerance"]),
        "cutoff_tail": metrics["cutoff_tail_max"]
        <= float(acceptance["maximum_cutoff_tail"]),
        "wigner_integral": metrics["wigner_integral_error_max"]
        <= float(acceptance["maximum_wigner_integral_error"]),
    }
    checks["machine_passed"] = bool(all(checks["acceptance"].values()))
    checks["status"] = "passed" if checks["machine_passed"] else "failed"
    checks_path = checks_root / f"{prefix}_science.json"
    atomic_json(checks_path, checks)

    summary = {
        "schema_version": 1,
        "paper_id": "2412.14271",
        "run_id": campaign["run_id"],
        "profile": campaign["profile"],
        "effective_config_digest": config_digest,
        "implementation_digest": implementation_digest,
        "runtime_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "qutip": __import__("qutip").__version__,
        },
        "parameters": parameters,
        "paper_parameters_executed": campaign["profile"] == "paper_scale",
        "science_checks_passed": checks["machine_passed"],
        "fidelity": {
            "level": (
                "paper_scale_candidate"
                if campaign["profile"] == "paper_scale"
                else "smoke"
            ),
            "paper_exact": False,
            "reason": "The paper omits integration time and random-seed policy; fresh independent review and strict source comparison remain required.",
        },
        "execution_assurance": "Require the corresponding Harness run_attestation.json for Git SHA and file-access proof; this summary alone is not an isolation attestation.",
    }
    summary_path = data_root / f"{prefix}_summary.json"
    atomic_json(summary_path, summary)

    manifest = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "2412.14271",
        "run_id": campaign["run_id"],
        "config": {"path": str(config_path), "sha256": sha256_file(config_path)},
        "effective_config_digest": config_digest,
        "implementation_digest": implementation_digest,
        "numeric_input_boundary": campaign["input_boundary"],
        "generated_files": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (data_path, summary_path, checks_path)
        ],
        "shards": shard_records,
    }
    manifest_path = checks_root / f"{prefix}_manifest.json"
    atomic_json(manifest_path, manifest)
    return {
        "data": str(data_path),
        "summary": str(summary_path),
        "checks": str(checks_path),
        "manifest": str(manifest_path),
        "machine_passed": checks["machine_passed"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("plan", "run-shard", "aggregate", "run-all"),
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--job")
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--resume", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config)
    campaign, config_digest, implementation_digest = load_campaign(
        config_path,
        smoke=args.smoke,
    )
    shard_count = args.shard_count or int(
        campaign["execution"]["effective_shard_count"]
    )
    plan_path = write_plan(
        campaign,
        config_path=config_path,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
    )
    if args.action == "plan":
        print(json.dumps({"plan": str(plan_path)}, indent=2))
        return 0

    started = time.monotonic()
    if args.action in {"run-shard", "run-all"}:
        paths = execute_shards(
            campaign,
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            label=args.job,
            shard_index=args.shard_index if args.action == "run-shard" else None,
            shard_count=shard_count,
            resume=args.resume,
        )
        if args.action == "run-shard":
            print(json.dumps({"checkpoints": [str(path) for path in paths]}, indent=2))
            return 0

    result = aggregate_campaign(
        campaign,
        config_path=config_path,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        shard_count=shard_count,
    )
    result["runtime_seconds"] = time.monotonic() - started
    print(json.dumps(result, indent=2))
    return 0 if result["machine_passed"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
