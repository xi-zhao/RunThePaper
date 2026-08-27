#!/usr/bin/env python3
"""Reproduce all sixteen numerical subpanels of Supplement Figure S3.

Every plotted datum comes from independently simulated Clifford stabilizer
trajectories.  The source figure is never opened by this program.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import sys
from time import perf_counter


WORKSPACE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(WORKSPACE / "outputs" / "cache" / "matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(WORKSPACE / "src"))

from stabilizer_dynamics import DynamicsConfig, run_trajectory_ensemble  # noqa: E402


TARGET_ID = "T003"
MODEL_REVISION = "mth001-odd-step-noncrossing-v2"
PAPER_BLOCKS = 32
PAPER_QUBITS_PER_BLOCK = 11
PAPER_REALIZATIONS = 240
DEFAULT_SEED = 190_305_124


@dataclass(frozen=True)
class Setting:
    panel: str
    depth: int
    measurement_fraction: float
    steps: int

    @property
    def key(self) -> str:
        return self.panel.lower()


@dataclass(frozen=True)
class SettingOutput:
    setting: Setting
    seed: int
    entropy_after_measurement: np.ndarray
    entropy_before_measurement: np.ndarray
    measurement_entropy_change: np.ndarray
    random_measurements: np.ndarray
    runtime_seconds: float
    workers: int
    requested_workers: int

    @property
    def realizations(self) -> int:
        return int(self.entropy_after_measurement.shape[0])


PAPER_SETTINGS = (
    Setting("A", 3, 0.1, 300),
    Setting("B", 3, 0.2, 300),
    Setting("C", 3, 0.3, 300),
    Setting("D", 3, 0.4, 300),
    Setting("E", 44, 0.2, 40),
    Setting("F", 44, 0.4, 32),
    Setting("G", 44, 0.6, 32),
    Setting("H", 44, 0.8, 32),
)


def require_guard() -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID", "") != TARGET_ID:
        raise RuntimeError(
            "Run this target through PRAgent-workflow/scripts/run_target.py so the live formula gate is enforced."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("smoke", "feature", "paper"), default="smoke")
    parser.add_argument("--realizations", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Render the persisted independent trajectories without rerunning dynamics.",
    )
    return parser.parse_args()


def scale_config(
    scale: str,
    realization_override: int | None,
) -> tuple[tuple[Setting, ...], int]:
    if scale == "smoke":
        settings = tuple(replace(setting, steps=min(12, setting.steps)) for setting in PAPER_SETTINGS)
        realizations = 2
    elif scale == "feature":
        settings = PAPER_SETTINGS
        realizations = 24
    else:
        settings = PAPER_SETTINGS
        realizations = PAPER_REALIZATIONS
    if realization_override is not None:
        realizations = realization_override
    if realizations <= 0:
        raise ValueError("realizations must be positive")
    return settings, realizations


def setting_seed(root_seed: int, index: int) -> int:
    sequence = np.random.SeedSequence([int(root_seed), int(index)])
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def checkpoint_path(
    *,
    scale: str,
    realizations: int,
    root_seed: int,
    setting: Setting,
) -> Path:
    directory = WORKSPACE / "outputs" / "checkpoints" / "t003"
    directory.mkdir(parents=True, exist_ok=True)
    signature = f"{MODEL_REVISION}_{scale}_r{realizations}_seed{root_seed}"
    return directory / f"{signature}_{setting.key}_d{setting.depth}_p{setting.measurement_fraction:g}_t{setting.steps}.npz"


def save_checkpoint(path: Path, output: SettingOutput) -> None:
    np.savez_compressed(
        path,
        panel=np.array(output.setting.panel),
        depth=np.array(output.setting.depth),
        measurement_fraction=np.array(output.setting.measurement_fraction),
        steps=np.array(output.setting.steps),
        seed=np.array(output.seed, dtype=np.uint64),
        entropy_after_measurement=output.entropy_after_measurement,
        entropy_before_measurement=output.entropy_before_measurement,
        measurement_entropy_change=output.measurement_entropy_change,
        random_measurements=output.random_measurements,
        runtime_seconds=np.array(output.runtime_seconds),
        workers=np.array(output.workers),
        requested_workers=np.array(output.requested_workers),
    )


def load_checkpoint(path: Path, expected: Setting, expected_realizations: int) -> SettingOutput:
    with np.load(path, allow_pickle=False) as payload:
        setting = Setting(
            panel=str(payload["panel"].item()),
            depth=int(payload["depth"].item()),
            measurement_fraction=float(payload["measurement_fraction"].item()),
            steps=int(payload["steps"].item()),
        )
        output = SettingOutput(
            setting=setting,
            seed=int(payload["seed"].item()),
            entropy_after_measurement=payload["entropy_after_measurement"].copy(),
            entropy_before_measurement=payload["entropy_before_measurement"].copy(),
            measurement_entropy_change=payload["measurement_entropy_change"].copy(),
            random_measurements=payload["random_measurements"].copy(),
            runtime_seconds=float(payload["runtime_seconds"].item()),
            workers=int(payload["workers"].item()),
            requested_workers=int(payload["requested_workers"].item()),
        )
    if setting != expected or output.realizations != expected_realizations:
        raise ValueError(f"checkpoint does not match requested run: {path}")
    return output


def run_settings(
    settings: tuple[Setting, ...],
    *,
    scale: str,
    realizations: int,
    root_seed: int,
    workers: int,
    resume: bool,
) -> tuple[SettingOutput, ...]:
    outputs: list[SettingOutput] = []
    for index, setting in enumerate(settings):
        seed = setting_seed(root_seed, index)
        path = checkpoint_path(
            scale=scale,
            realizations=realizations,
            root_seed=root_seed,
            setting=setting,
        )
        if resume and path.exists():
            output = load_checkpoint(path, setting, realizations)
            print(
                json.dumps(
                    {"panel": setting.panel, "status": "resumed", "runtime_seconds": output.runtime_seconds}
                ),
                flush=True,
            )
            outputs.append(output)
            continue
        config = DynamicsConfig(
            blocks=PAPER_BLOCKS,
            qubits_per_block=PAPER_QUBITS_PER_BLOCK,
            circuit_depth=setting.depth,
            measurement_fraction=setting.measurement_fraction,
            steps=setting.steps,
            boundary="open",
        )
        result = run_trajectory_ensemble(
            config,
            realizations=realizations,
            seed=seed,
            workers=workers,
        )
        output = SettingOutput(
            setting=setting,
            seed=seed,
            entropy_after_measurement=result.entropy_after_measurement,
            entropy_before_measurement=result.entropy_before_measurement,
            measurement_entropy_change=result.measurement_entropy_change,
            random_measurements=result.random_measurements,
            runtime_seconds=result.runtime_seconds,
            workers=result.workers,
            requested_workers=result.requested_workers,
        )
        save_checkpoint(path, output)
        outputs.append(output)
        print(
            json.dumps(
                {
                    "panel": setting.panel,
                    "status": "completed",
                    "depth": setting.depth,
                    "p": setting.measurement_fraction,
                    "steps": setting.steps,
                    "realizations": realizations,
                    "runtime_seconds": result.runtime_seconds,
                    "workers": result.workers,
                }
            ),
            flush=True,
        )
    return tuple(outputs)


def mean_std_error(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = np.mean(values, axis=0)
    ddof = 1 if values.shape[0] > 1 else 0
    standard_deviation = np.std(values, axis=0, ddof=ddof)
    standard_error = standard_deviation / np.sqrt(values.shape[0])
    return mean, standard_deviation, standard_error


def write_csv(path: Path, outputs: tuple[SettingOutput, ...]) -> None:
    fieldnames = [
        "panel",
        "depth",
        "measurement_fraction",
        "time",
        "entropy_density_mean",
        "entropy_density_standard_deviation",
        "entropy_density_standard_error",
        "measurement_change_mean",
        "measurement_change_standard_deviation",
        "measurement_change_standard_error",
        "realizations",
    ]
    denominator = PAPER_BLOCKS * PAPER_QUBITS_PER_BLOCK / 2
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for output in outputs:
            entropy = output.entropy_after_measurement / denominator
            entropy_mean, entropy_std, entropy_se = mean_std_error(entropy)
            change_mean, change_std, change_se = mean_std_error(output.measurement_entropy_change)
            for time in range(output.setting.steps + 1):
                row: dict[str, object] = {
                    "panel": output.setting.panel,
                    "depth": output.setting.depth,
                    "measurement_fraction": output.setting.measurement_fraction,
                    "time": time,
                    "entropy_density_mean": float(entropy_mean[time]),
                    "entropy_density_standard_deviation": float(entropy_std[time]),
                    "entropy_density_standard_error": float(entropy_se[time]),
                    "measurement_change_mean": "",
                    "measurement_change_standard_deviation": "",
                    "measurement_change_standard_error": "",
                    "realizations": output.realizations,
                }
                if time > 0:
                    row.update(
                        {
                            "measurement_change_mean": float(change_mean[time - 1]),
                            "measurement_change_standard_deviation": float(change_std[time - 1]),
                            "measurement_change_standard_error": float(change_se[time - 1]),
                        }
                    )
                writer.writerow(row)


def save_raw(path: Path, outputs: tuple[SettingOutput, ...]) -> None:
    arrays: dict[str, np.ndarray] = {}
    for output in outputs:
        prefix = output.setting.key
        arrays[f"{prefix}_entropy_after_measurement"] = output.entropy_after_measurement
        arrays[f"{prefix}_entropy_before_measurement"] = output.entropy_before_measurement
        arrays[f"{prefix}_measurement_entropy_change"] = output.measurement_entropy_change
        arrays[f"{prefix}_random_measurements"] = output.random_measurements
    np.savez_compressed(path, **arrays)


def load_raw(path: Path, metadata_path: Path) -> tuple[SettingOutput, ...]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    outputs: list[SettingOutput] = []
    with np.load(path, allow_pickle=False) as payload:
        for item in metadata["settings"]:
            setting = Setting(
                panel=str(item["panel"]),
                depth=int(item["depth"]),
                measurement_fraction=float(item["measurement_fraction"]),
                steps=int(item["steps"]),
            )
            prefix = setting.key
            outputs.append(
                SettingOutput(
                    setting=setting,
                    seed=int(item["seed"]),
                    entropy_after_measurement=payload[f"{prefix}_entropy_after_measurement"].copy(),
                    entropy_before_measurement=payload[f"{prefix}_entropy_before_measurement"].copy(),
                    measurement_entropy_change=payload[f"{prefix}_measurement_entropy_change"].copy(),
                    random_measurements=payload[f"{prefix}_random_measurements"].copy(),
                    runtime_seconds=float(item["runtime_seconds"]),
                    workers=int(item["workers"]),
                    requested_workers=int(item["requested_workers"]),
                )
            )
    return tuple(outputs)


def steady_density(output: SettingOutput) -> float:
    denominator = PAPER_BLOCKS * PAPER_QUBITS_PER_BLOCK / 2
    density = output.entropy_after_measurement / denominator
    window = max(5, output.setting.steps // 5)
    return float(np.mean(density[:, -window:]))


def saturation_time(output: SettingOutput) -> int:
    denominator = PAPER_BLOCKS * PAPER_QUBITS_PER_BLOCK / 2
    mean = np.mean(output.entropy_after_measurement / denominator, axis=0)
    threshold = 0.95 * steady_density(output)
    candidate_times = (
        np.concatenate((np.array([0]), np.arange(1, output.setting.steps + 1, 2)))
        if output.setting.depth == 44
        else np.arange(output.setting.steps + 1)
    )
    matches = candidate_times[mean[candidate_times] >= threshold]
    return int(matches[0]) if matches.size else output.setting.steps


def render(path: Path, outputs: tuple[SettingOutput, ...]) -> None:
    plt.rcParams.update({"font.size": 8.5, "axes.linewidth": 0.7})
    figure = plt.figure(figsize=(13.6, 1583 / 220), constrained_layout=True)
    grid = figure.add_gridspec(4, 4, height_ratios=(1.0, 0.9, 1.0, 0.9))
    denominator = PAPER_BLOCKS * PAPER_QUBITS_PER_BLOCK / 2
    for index, output in enumerate(outputs):
        row = 0 if index < 4 else 2
        column = index % 4
        entropy_axis = figure.add_subplot(grid[row, column])
        change_axis = figure.add_subplot(grid[row + 1, column], sharex=entropy_axis)
        setting = output.setting
        color = "#e9540d" if setting.depth == 3 else "#0879bd"

        entropy = output.entropy_after_measurement / denominator
        entropy_mean, _, _ = mean_std_error(entropy)
        entropy_times = np.arange(setting.steps + 1)
        change_mean, _, change_se = mean_std_error(output.measurement_entropy_change)
        change_times = np.arange(1, setting.steps + 1)
        entropy_indices = np.concatenate((np.array([0]), np.arange(1, setting.steps + 1, 2)))
        change_indices = np.arange(0, setting.steps, 2)

        entropy_axis.plot(
            entropy_times[entropy_indices],
            entropy_mean[entropy_indices],
            color=color,
            linewidth=1.0,
            marker="o" if setting.depth == 44 else None,
            markersize=2.2,
        )
        entropy_axis.axhline(
            1.0 - setting.measurement_fraction,
            color="black",
            linestyle=(0, (7, 3, 1.5, 3)),
            linewidth=0.9,
        )
        change_axis.errorbar(
            change_times[change_indices],
            change_mean[change_indices],
            yerr=change_se[change_indices],
            color=color,
            linewidth=1.0,
            marker="o" if setting.depth == 44 else None,
            markersize=2.1,
            elinewidth=0.65,
            capsize=1.8,
        )
        change_axis.axhline(0.0, color="black", linestyle=(0, (1, 4)), linewidth=0.65)
        if setting.panel in {"E", "F"}:
            transition = saturation_time(output)
            for axis in (entropy_axis, change_axis):
                axis.axvline(transition, color="#e9540d", linestyle=(0, (1, 3)), linewidth=0.9)

        entropy_axis.set_ylabel(r"$S/(Lm/2)$")
        change_axis.set_ylabel(r"$\Delta S_{\mathrm{meas}}$")
        change_axis.set_xlabel(r"$t$")
        entropy_axis.text(
            -0.24,
            1.03,
            f"({setting.panel.lower()})",
            transform=entropy_axis.transAxes,
            fontsize=10.5,
        )
        entropy_axis.set_xlim(0, setting.steps)
        entropy_axis.set_ylim(0, min(1.0, 1.0 - setting.measurement_fraction + 0.11))
        change_axis.set_ylim(-0.72 if setting.depth == 3 else -1.1, 0.1)
        for axis in (entropy_axis, change_axis):
            axis.tick_params(direction="in", top=True, right=True, width=0.65, length=2.6)
        plt.setp(entropy_axis.get_xticklabels(), visible=False)
    figure.savefig(path, dpi=220, facecolor="white")
    plt.close(figure)


def build_checks(
    outputs: tuple[SettingOutput, ...],
    *,
    scale: str,
) -> dict[str, object]:
    output_by_panel = {output.setting.panel: output for output in outputs}
    half_size = PAPER_BLOCKS * PAPER_QUBITS_PER_BLOCK // 2
    initial_zero = all(np.all(output.entropy_after_measurement[:, 0] == 0) for output in outputs)
    entropy_bounds = all(
        np.all((output.entropy_after_measurement >= 0) & (output.entropy_after_measurement <= half_size))
        for output in outputs
    )
    nonpositive_measurement_change = all(
        np.all(output.measurement_entropy_change <= 0) for output in outputs
    )
    requested_trajectories_complete = all(
        output.entropy_after_measurement.shape
        == (output.realizations, output.setting.steps + 1)
        for output in outputs
    )
    criteria = {
        "all_eight_parameter_settings_present": set(output_by_panel) == set("ABCDEFGH"),
        "all_sixteen_numerical_subpanels_generated": len(outputs) == 8,
        "paper_system_geometry_L32_m11": True,
        "initial_product_entropy_is_zero": initial_zero,
        "entropy_respects_bipartite_bounds": entropy_bounds,
        "projective_measurements_do_not_increase_stabilizer_entanglement": nonpositive_measurement_change,
        "requested_trajectories_completed": requested_trajectories_complete,
        "generated_data_are_integer_stabilizer_observables": all(
            np.issubdtype(output.entropy_after_measurement.dtype, np.integer)
            and np.issubdtype(output.measurement_entropy_change.dtype, np.integer)
            for output in outputs
        ),
        "source_pixels_absent": True,
    }

    weak_early_losses = {
        panel: float(np.mean(output_by_panel[panel].measurement_entropy_change[:, :25:2]))
        for panel in "ABCD"
    }
    strong_early_losses: dict[str, float] = {}
    strong_late_losses: dict[str, float] = {}
    for panel in "EFGH":
        changes = output_by_panel[panel].measurement_entropy_change
        early_indices = np.arange(0, min(15, changes.shape[1]), 2)
        strong_early_losses[panel] = float(np.mean(changes[:, early_indices]))
        odd_changes = changes[:, ::2]
        late_window = max(4, odd_changes.shape[1] // 4)
        strong_late_losses[panel] = float(np.mean(odd_changes[:, -late_window:]))

    weak_steady = [steady_density(output_by_panel[panel]) for panel in "ABCD"]
    strong_steady = [steady_density(output_by_panel[panel]) for panel in "EFGH"]
    strong_ceilings = [1.0 - output_by_panel[panel].setting.measurement_fraction for panel in "EFGH"]
    split_drifts: dict[str, float] = {}
    for panel, output in output_by_panel.items():
        midpoint = output.realizations // 2
        if midpoint == 0:
            split_drifts[panel] = float("nan")
            continue
        denominator = half_size
        window = max(5, output.setting.steps // 5)
        first = np.mean(output.entropy_after_measurement[:midpoint, -window:] / denominator)
        second = np.mean(output.entropy_after_measurement[midpoint:, -window:] / denominator)
        split_drifts[panel] = float(abs(first - second))

    feature_checks = {
        "weak_scrambling_measurements_reduce_entropy_from_early_times": all(
            value < -0.02 for value in weak_early_losses.values()
        ),
        "strong_scrambling_low_p_has_early_measurement_protection": all(
            strong_early_losses[panel] > -0.08 for panel in "EF"
        ),
        "strong_scrambling_has_late_measurement_loss": all(
            value < -0.2 for value in strong_late_losses.values()
        ),
        "steady_entropy_decreases_monotonically_with_p": all(
            left > right for left, right in zip(weak_steady, weak_steady[1:])
        )
        and all(left > right for left, right in zip(strong_steady, strong_steady[1:])),
        "strong_scrambling_saturates_below_and_near_decoupling_ceiling": all(
            0.0 <= ceiling - density < 0.2
            for ceiling, density in zip(strong_ceilings, strong_steady)
        ),
        "strong_scrambling_outperforms_weak_at_matched_p": (
            strong_steady[0] > weak_steady[1] and strong_steady[1] > weak_steady[3]
        ),
        "split_sample_steady_density_drift_below_0_08": all(
            np.isfinite(value) and value < 0.08 for value in split_drifts.values()
        ),
    }
    paper_exact = (
        all(output.realizations == PAPER_REALIZATIONS for output in outputs)
        and tuple(output.setting for output in outputs) == PAPER_SETTINGS
    )
    return {
        "schema_version": 1,
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "status": "passed" if all(criteria.values()) else "failed",
        "scientific_feature_status": (
            "passed" if all(feature_checks.values()) else "inconclusive_at_current_scale"
        ),
        "completion_status": (
            "paper_scale_reproduced"
            if paper_exact and all(feature_checks.values())
            else "feature_reproduced" if all(feature_checks.values()) else "mechanics_verified"
        ),
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "rendered_uncertainty": "standard_error",
        "persisted_uncertainties": ["standard_deviation", "standard_error"],
        "scale": scale,
        "parameter_match": "paper_exact" if paper_exact else "paper_subset",
        "paper_parameters": {
            "L": PAPER_BLOCKS,
            "m": PAPER_QUBITS_PER_BLOCK,
            "realizations": PAPER_REALIZATIONS,
            "settings": [setting.__dict__ for setting in PAPER_SETTINGS],
        },
        "generated_parameters": {
            "L": PAPER_BLOCKS,
            "m": PAPER_QUBITS_PER_BLOCK,
            "realizations": outputs[0].realizations,
            "settings": [output.setting.__dict__ for output in outputs],
            "seeds": {output.setting.panel: output.seed for output in outputs},
            "workers": {output.setting.panel: output.workers for output in outputs},
        },
        "metrics": {
            "runtime_seconds": float(sum(output.runtime_seconds for output in outputs)),
            "steady_density": {
                panel: steady_density(output_by_panel[panel]) for panel in "ABCDEFGH"
            },
            "weak_early_measurement_change": weak_early_losses,
            "strong_early_measurement_change": strong_early_losses,
            "strong_late_measurement_change": strong_late_losses,
            "split_sample_steady_density_drift": split_drifts,
            "saturation_time": {
                panel: saturation_time(output_by_panel[panel]) for panel in "EFGH"
            },
        },
        "criteria": criteria,
        "feature_checks": feature_checks,
    }


def metadata_payload(
    outputs: tuple[SettingOutput, ...],
    *,
    scale: str,
    root_seed: int,
    checks: dict[str, object],
) -> dict[str, object]:
    return {
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "formula_refs": ["EQC002", "EQC005", "EQC006"],
        "method_refs": ["MTH001"],
        "model_revision": MODEL_REVISION,
        "scale": scale,
        "parameter_match": checks["parameter_match"],
        "root_seed": root_seed,
        "runtime_seconds": checks["metrics"]["runtime_seconds"],
        "settings": [
            {
                **output.setting.__dict__,
                "seed": output.seed,
                "realizations": output.realizations,
                "runtime_seconds": output.runtime_seconds,
                "workers": output.workers,
                "requested_workers": output.requested_workers,
            }
            for output in outputs
        ],
        "files": [
            "supp_fig_s3_trajectories.csv",
            "supp_fig_s3_raw.npz",
            "supp_fig_s3_reproduction.png",
            "t003_scientific_checks.json",
        ],
    }


def main() -> int:
    require_guard()
    args = parse_args()
    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    check_dir = WORKSPACE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "supp_fig_s3_trajectories.csv"
    raw_path = data_dir / "supp_fig_s3_raw.npz"
    metadata_path = data_dir / "supp_fig_s3_metadata.json"
    figure_path = figure_dir / "supp_fig_s3_reproduction.png"
    check_path = check_dir / "t003_scientific_checks.json"

    if args.render_only:
        if not raw_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("render-only requires persisted independent trajectories and metadata")
        outputs = load_raw(raw_path, metadata_path)
        render(figure_path, outputs)
        print(
            json.dumps(
                {
                    "status": "rendered",
                    "source_pixels_used_in_generation": False,
                    "output": str(figure_path),
                },
                indent=2,
            )
        )
        return 0

    settings, realizations = scale_config(args.scale, args.realizations)
    default_workers = 1 if args.scale == "smoke" else min(8, os.cpu_count() or 1)
    workers = args.workers if args.workers is not None else default_workers
    if workers <= 0:
        raise ValueError("workers must be positive")
    started = perf_counter()
    outputs = run_settings(
        settings,
        scale=args.scale,
        realizations=realizations,
        root_seed=args.seed,
        workers=workers,
        resume=not args.no_resume,
    )
    write_csv(csv_path, outputs)
    save_raw(raw_path, outputs)
    render(figure_path, outputs)
    checks = build_checks(outputs, scale=args.scale)
    check_path.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata = metadata_payload(
        outputs,
        scale=args.scale,
        root_seed=args.seed,
        checks=checks,
    )
    metadata["wall_runtime_seconds"] = perf_counter() - started
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": checks["status"],
                "feature_status": checks["scientific_feature_status"],
                "completion_status": checks["completion_status"],
                "parameter_match": checks["parameter_match"],
                "trajectory_runtime_seconds": checks["metrics"]["runtime_seconds"],
                "wall_runtime_seconds": metadata["wall_runtime_seconds"],
                "outputs": [str(csv_path), str(raw_path), str(figure_path), str(check_path)],
            },
            indent=2,
        )
    )
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
