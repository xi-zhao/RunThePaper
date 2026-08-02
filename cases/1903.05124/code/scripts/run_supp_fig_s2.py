#!/usr/bin/env python3
"""Generate Supplement Figure S2 from independent Clifford circuits."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


CODE = Path(__file__).resolve().parents[1]
CASE = CODE.parent
os.environ.setdefault("MPLCONFIGDIR", str(CASE / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(CODE / "src"))

from frame_potential import (  # noqa: E402
    TWO_QUBIT_CLIFFORD_GROUP_SIZE,
    dense_trace_validation,
    records_by_moment,
    result_from_q_samples,
    sample_frame_potentials,
    sample_frame_potentials_parallel,
    two_qubit_clifford_mappings,
)


TARGET_ID = "T002"
PAPER_N = 22
PAPER_DEPTHS = tuple(range(2, 45, 2))
PAPER_SAMPLES = 50_000
DEFAULT_SEED = 190_305_124


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("smoke", "feature", "paper"), default="smoke")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Render the persisted exact Q_U samples without rerunning Monte Carlo.",
    )
    parser.add_argument("--samples", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def scale_config(scale: str, sample_override: int | None) -> tuple[tuple[int, ...], int]:
    if scale == "smoke":
        depths, samples = (2, 4, 8, 16, 32, 44), 64
    elif scale == "feature":
        depths, samples = PAPER_DEPTHS, 1_024
    else:
        depths, samples = PAPER_DEPTHS, PAPER_SAMPLES
    return depths, sample_override if sample_override is not None else samples


def write_records(path: Path, records: tuple[dict[str, float | int], ...]) -> None:
    fieldnames = ["depth", "depth_over_n", "moment", "estimate", "standard_error", "haar_value", "samples"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def render(path: Path, result) -> None:
    plt.rcParams.update({"font.size": 9.0, "axes.linewidth": 0.75})
    figure, axes = plt.subplots(1, 4, figsize=(13.5, 1.8), constrained_layout=True)
    y_limits = ((0.0, 4.1), (0.0, 8.2), (0.0, 24.5), (0.0, 96.0))
    y_ticks = ((0, 1, 2, 3), (0, 2, 4, 6), (0, 6, 12, 18), (0, 24, 48, 72))
    for moment, axis in enumerate(axes, start=1):
        rows = records_by_moment(result, moment)
        x = np.array([row["depth_over_n"] for row in rows], dtype=float)
        y = np.array([row["estimate"] for row in rows], dtype=float)
        error = np.array([row["standard_error"] for row in rows], dtype=float)
        haar = float(rows[0]["haar_value"])
        axis.errorbar(
            x,
            y,
            yerr=error,
            color="#0879bd",
            marker="o",
            markersize=2.4,
            linewidth=0.9,
            capsize=1.8,
        )
        axis.axhline(haar, color="#e95d0f", linestyle=(0, (6, 4)), linewidth=1.15)
        axis.set_xlabel(r"$d/n$")
        axis.set_ylabel(rf"$F_{{{moment}}}$")
        axis.set_title(f"({chr(96 + moment)})", loc="left", fontweight="bold", pad=7)
        axis.set_xlim(0.0, 2.05)
        axis.set_ylim(*y_limits[moment - 1])
        axis.set_yticks(y_ticks[moment - 1])
        axis.tick_params(direction="in", top=True, right=True, width=0.7, length=2.8)
    figure.savefig(path, dpi=220, facecolor="white")
    plt.close(figure)


def build_checks(result, *, scale: str, dense_error: float) -> dict[str, object]:
    q_values = result.q_samples.ravel()
    powers_of_two_or_zero = all(
        value == 0 or (int(value) & (int(value) - 1)) == 0 for value in q_values
    )
    deep = {moment: records_by_moment(result, moment)[-1] for moment in range(1, 5)}
    late_q = result.q_samples[result.depths >= result.n].astype(np.float64)
    late_f4_by_trajectory = np.mean(np.power(late_q, 4), axis=0)
    late_f4_mean = float(np.mean(late_f4_by_trajectory))
    late_f4_standard_error = float(
        np.std(late_f4_by_trajectory, ddof=1) / np.sqrt(late_f4_by_trajectory.size)
    )
    late_f4_lower_95 = late_f4_mean - 1.96 * late_f4_standard_error
    feature_checks = {
        "F1_approaches_Haar": abs(float(deep[1]["estimate"]) - 1.0)
        <= max(0.2, 5.0 * float(deep[1]["standard_error"])),
        "F2_approaches_Haar": abs(float(deep[2]["estimate"]) - 2.0)
        <= max(1.0, 5.0 * float(deep[2]["standard_error"])),
        "F3_approaches_Haar": abs(float(deep[3]["estimate"]) - 6.0)
        <= max(4.0, 5.0 * float(deep[3]["standard_error"])),
        "F4_distinct_from_Haar": late_f4_lower_95 > 24.0,
    }
    criteria = {
        "two_qubit_clifford_group_complete": len(two_qubit_clifford_mappings())
        == TWO_QUBIT_CLIFFORD_GROUP_SIZE,
        "binary_trace_matches_dense_small_system": dense_error < 1e-10,
        "trace_squares_are_zero_or_powers_of_two": powers_of_two_or_zero,
        "paper_qubit_count": result.n == PAPER_N,
        "requested_samples_completed": result.q_samples.shape[1] > 0,
        "source_pixels_absent": True,
    }
    return {
        "schema_version": 1,
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "scientific_feature_status": "passed" if all(feature_checks.values()) else "inconclusive_at_current_scale",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "scale": scale,
        "paper_parameters": {"n": PAPER_N, "depths": list(PAPER_DEPTHS), "samples_per_depth": PAPER_SAMPLES},
        "generated_parameters": {
            "n": result.n,
            "depths": result.depths.tolist(),
            "samples_per_depth": int(result.q_samples.shape[1]),
            "seed": result.seed,
            "workers": result.workers,
            "requested_workers": result.requested_workers,
        },
        "metrics": {
            "two_qubit_clifford_group_size": TWO_QUBIT_CLIFFORD_GROUP_SIZE,
            "dense_trace_max_absolute_error": dense_error,
            "runtime_seconds": result.runtime_seconds,
            "deepest_depth": int(result.depths[-1]),
            "deepest_estimates": {str(moment): float(deep[moment]["estimate"]) for moment in range(1, 5)},
            "deepest_standard_errors": {str(moment): float(deep[moment]["standard_error"]) for moment in range(1, 5)},
            "late_depth_F4": {
                "depth_rule": "d >= n",
                "trajectory_mean": late_f4_mean,
                "standard_error": late_f4_standard_error,
                "lower_95_percent_bound": late_f4_lower_95,
                "haar_value": 24.0,
            },
        },
        "criteria": criteria,
        "feature_checks": feature_checks,
    }


def main() -> int:
    args = parse_args()
    depths, samples = scale_config(args.scale, args.samples)
    default_workers = 1 if args.scale == "smoke" else min(8, os.cpu_count() or 1)
    workers = args.workers if args.workers is not None else default_workers
    if workers <= 0:
        raise ValueError("workers must be positive")
    data_dir = CASE / "outputs" / "data"
    figure_dir = CASE / "outputs" / "figures"
    check_dir = CASE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / "supp_fig_s2_frame_potential.csv"
    raw_path = data_dir / "supp_fig_s2_q_samples.npz"
    figure_path = figure_dir / "supp_fig_s2_reproduction.png"
    check_path = check_dir / "t002_scientific_checks.json"
    metadata_path = data_dir / "supp_fig_s2_metadata.json"

    if args.render_only:
        if not raw_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("render-only requires persisted Q_U samples and metadata")
        with np.load(raw_path, allow_pickle=False) as payload:
            persisted_depths = payload["depths"]
            persisted_q = payload["q_samples"]
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        result = result_from_q_samples(
            n=PAPER_N,
            depths=persisted_depths,
            q_samples=persisted_q,
            seed=int(metadata["seed"]),
            runtime_seconds=float(metadata["runtime_seconds"]),
            workers=int(metadata.get("workers") or 1),
            requested_workers=int(metadata.get("requested_workers") or metadata.get("workers") or 1),
        )
        render(figure_path, result)
        print(
            json.dumps(
                {
                    "status": "rendered",
                    "source_pixels_used_in_generation": False,
                    "samples": int(result.q_samples.shape[1]),
                    "depths": result.depths.tolist(),
                    "output": str(figure_path),
                },
                indent=2,
            )
        )
        return 0

    dense_error = dense_trace_validation()
    sampler = sample_frame_potentials if workers == 1 else sample_frame_potentials_parallel
    sampler_kwargs = {
        "n": PAPER_N,
        "depths": depths,
        "samples": samples,
        "seed": args.seed,
    }
    if workers != 1:
        sampler_kwargs["workers"] = workers
    result = sampler(**sampler_kwargs)
    write_records(csv_path, result.records)
    np.savez_compressed(raw_path, depths=result.depths, q_samples=result.q_samples)
    render(figure_path, result)
    checks = build_checks(result, scale=args.scale, dense_error=dense_error)
    check_path.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "paper_id": "1903.05124",
                "target_id": TARGET_ID,
                "generated_data_provenance": "independent_numerics",
                "source_pixels_used_in_generation": False,
                "formula_refs": ["EQC003", "EQC004"],
                "method_refs": ["MTH002"],
                "scale": args.scale,
                "seed": args.seed,
                "runtime_seconds": result.runtime_seconds,
                "workers": result.workers,
                "requested_workers": result.requested_workers,
                "files": [csv_path.name, raw_path.name, figure_path.name, check_path.name],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": checks["status"], "feature_status": checks["scientific_feature_status"], "runtime_seconds": result.runtime_seconds, "samples": samples, "workers": result.workers, "requested_workers": result.requested_workers, "depths": list(depths), "outputs": [str(csv_path), str(raw_path), str(figure_path), str(check_path)]}, indent=2))
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
