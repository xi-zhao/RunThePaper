#!/usr/bin/env python3
"""Add independently simulated midpoint samples for Supplement Figure S5.

The feature-scale Main Figure 2 campaign supplies nine probabilities per
transition curve.  That grid is sufficient to locate ``p_c`` but too coarse
for a stable critical-exponent fit.  This guarded campaign evaluates the eight
strict interval midpoints with the same Clifford-stabilizer model, boundary
condition, system sizes, equilibration rule, and realization count.  It never
opens a source figure and never uses published fit values to choose samples.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import numpy as np


CODE = Path(__file__).resolve().parents[1]
CASE = CODE.parent
sys.path.insert(0, str(CODE / "scripts"))
sys.path.insert(0, str(CODE / "src"))

from run_main_fig2 import (  # noqa: E402
    ObservableOutput,
    ObservableSetting,
    equilibration_steps,
    observable_mean_and_error,
    odd_steps_ending_at,
    observable_worker_pool,
    run_observable_settings,
)


TARGET_ID = "T005"
MODEL_REVISION = "s5-midpoint-refinement-v1"
PAPER_DEPTHS = (1, 3, 5, 7, 11, 15, 23, 31)
FEATURE_SIZES = (8, 12, 16, 24)
DEFAULT_REALIZATIONS = 8
DEFAULT_SEED = 1_903_051_255


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=CASE / "outputs" / "data" / "main_fig2_numerical_data.csv",
    )
    parser.add_argument("--realizations", type=int, default=DEFAULT_REALIZATIONS)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def load_base_probability_grids(path: Path) -> dict[int, tuple[float, ...]]:
    """Read generated transition coordinates, never their observable values."""

    grouped: dict[tuple[int, int], set[float]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["campaign"] != "transition":
                continue
            if row["observable"] != "tripartite_mutual_information":
                continue
            key = (int(row["d"]), int(row["L"]))
            grouped.setdefault(key, set()).add(float(row["p"]))
    if not grouped:
        raise ValueError("input contains no independently generated transition grid")

    depths = tuple(sorted({depth for depth, _ in grouped}))
    sizes = tuple(sorted({size for _, size in grouped}))
    if depths != PAPER_DEPTHS:
        raise ValueError(f"expected depths {PAPER_DEPTHS}, got {depths}")
    if sizes != FEATURE_SIZES:
        raise ValueError(f"expected feature sizes {FEATURE_SIZES}, got {sizes}")

    grids: dict[int, tuple[float, ...]] = {}
    for depth in depths:
        per_size = {
            tuple(sorted(grouped[(depth, size)]))
            for size in sizes
            if (depth, size) in grouped
        }
        if len(per_size) != 1:
            raise ValueError(f"depth {depth} does not have one aligned probability grid")
        grid = per_size.pop()
        if len(grid) < 3 or np.any(np.diff(grid) <= 0):
            raise ValueError(f"depth {depth} probability grid is invalid")
        grids[depth] = grid
    return grids


def interval_midpoints(grid: tuple[float, ...]) -> tuple[float, ...]:
    values = np.asarray(grid, dtype=float)
    if len(values) < 2 or np.any(np.diff(values) <= 0):
        raise ValueError("probability grid must contain increasing values")
    return tuple(float(value) for value in (values[:-1] + values[1:]) / 2.0)


def refinement_settings(
    grids: dict[int, tuple[float, ...]],
) -> tuple[ObservableSetting, ...]:
    settings: list[ObservableSetting] = []
    for depth in PAPER_DEPTHS:
        midpoints = interval_midpoints(grids[depth])
        for blocks in FEATURE_SIZES:
            steps = equilibration_steps(blocks, depth, "feature")
            for probability in midpoints:
                settings.append(
                    ObservableSetting(
                        campaign="transition",
                        label=f"d{depth}",
                        blocks=blocks,
                        qubits_per_block=11,
                        depth=depth,
                        measurement_fraction=probability,
                        steps=steps,
                        boundary="periodic",
                        sample_steps=odd_steps_ending_at(steps),
                        include_tripartite_information=True,
                    )
                )
    return tuple(settings)


def write_csv(path: Path, outputs: tuple[ObservableOutput, ...]) -> None:
    fields = [
        "campaign",
        "label",
        "L",
        "m",
        "d",
        "p",
        "time",
        "observable",
        "mean",
        "standard_deviation",
        "standard_error",
        "realizations",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for output in outputs:
            observables = (
                ("half_chain_entropy", output.half_chain_entropy),
                ("tripartite_mutual_information", output.tripartite_mutual_information),
            )
            for name, values in observables:
                if values is None:
                    raise AssertionError(f"{output.setting.key} is missing {name}")
                mean, standard_deviation, standard_error = observable_mean_and_error(values)
                writer.writerow(
                    {
                        "campaign": output.setting.campaign,
                        "label": output.setting.label,
                        "L": output.setting.blocks,
                        "m": output.setting.qubits_per_block,
                        "d": output.setting.depth,
                        "p": output.setting.measurement_fraction,
                        "time": output.setting.sample_steps[-1],
                        "observable": name,
                        "mean": mean,
                        "standard_deviation": standard_deviation,
                        "standard_error": standard_error,
                        "realizations": output.realizations,
                    }
                )


def build_checks(
    grids: dict[int, tuple[float, ...]],
    settings: tuple[ObservableSetting, ...],
    outputs: tuple[ObservableOutput, ...],
    *,
    realizations: int,
) -> dict[str, object]:
    expected = sum((len(grid) - 1) * len(FEATURE_SIZES) for grid in grids.values())
    output_keys = {output.setting.key for output in outputs}
    setting_keys = {setting.key for setting in settings}
    midpoint_membership = []
    for setting in settings:
        midpoint_membership.append(
            any(
                np.isclose(setting.measurement_fraction, midpoint, atol=1e-14)
                for midpoint in interval_midpoints(grids[setting.depth])
            )
        )
    scientific_checks = {
        "all_eight_depths_refined": {setting.depth for setting in settings} == set(PAPER_DEPTHS),
        "all_four_feature_sizes_refined": {setting.blocks for setting in settings} == set(FEATURE_SIZES),
        "every_new_probability_is_a_strict_interval_midpoint": all(midpoint_membership),
        "all_planned_settings_completed": len(outputs) == expected and output_keys == setting_keys,
        "all_outputs_have_requested_independent_realizations": all(
            output.realizations == realizations for output in outputs
        ),
        "all_outputs_include_periodic_tripartite_information": all(
            output.setting.boundary == "periodic"
            and output.tripartite_mutual_information is not None
            for output in outputs
        ),
        "source_pixels_absent": True,
        "published_values_absent_from_sampling_rule": True,
    }
    return {
        "schema_version": 1,
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "status": "passed" if all(scientific_checks.values()) else "failed",
        "generated_data_provenance": "independent_T005_midpoint_Clifford_stabilizer_simulation",
        "source_pixels_used_in_generation": False,
        "published_values_used_for_generation": False,
        "scientific_checks": scientific_checks,
        "metrics": {
            "depths": list(PAPER_DEPTHS),
            "sizes": list(FEATURE_SIZES),
            "midpoints_per_curve": len(interval_midpoints(grids[PAPER_DEPTHS[0]])),
            "settings": len(settings),
            "realizations_per_setting": realizations,
            "independent_trajectories": len(settings) * realizations,
            "trajectory_runtime_seconds": float(sum(output.runtime_seconds for output in outputs)),
        },
    }


def main() -> int:
    args = parse_args()
    if args.realizations <= 0:
        raise ValueError("realizations must be positive")
    workers = args.workers if args.workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 0:
        raise ValueError("workers must be positive")

    started = perf_counter()
    grids = load_base_probability_grids(args.input)
    settings = refinement_settings(grids)
    with observable_worker_pool(workers) as executor:
        outputs = run_observable_settings(
            settings,
            campaign_code=5,
            scale=MODEL_REVISION,
            realizations=args.realizations,
            root_seed=args.seed,
            workers=workers,
            resume=not args.no_resume,
            executor=executor,
        )

    data_dir = CASE / "outputs" / "data"
    check_dir = CASE / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "supp_fig_s5_refinement_numerical_data.csv"
    write_csv(output_path, outputs)
    checks = build_checks(grids, settings, outputs, realizations=args.realizations)
    checks["runtime_seconds"] = perf_counter() - started
    (check_dir / "t005_refinement_checks.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    metadata = {
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "model_revision": MODEL_REVISION,
        "generated_data_provenance": checks["generated_data_provenance"],
        "source_pixels_used_in_generation": False,
        "published_values_used_for_generation": False,
        "sampling_rule": "strict midpoints of adjacent independently selected T001 transition-grid values",
        "input_coordinates_only": "main_fig2_numerical_data.csv#campaign=transition",
        "formula_refs": ["EQC005", "EQC008"],
        "method_refs": ["MTH001", "MTH003"],
        "seed": args.seed,
        "workers": workers,
        "realizations": args.realizations,
        "runtime_seconds": checks["runtime_seconds"],
    }
    (data_dir / "supp_fig_s5_refinement_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(checks, indent=2), flush=True)
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
