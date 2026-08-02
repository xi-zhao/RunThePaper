#!/usr/bin/env python3
"""Reproduce every theory-numerical panel in Main Figure 2(b--e).

Generation uses only the verified Clifford-stabilizer dynamics and finite-size
scaling implementations.  Source figures are not opened by this program.  The
published transition table is used only as an after-the-fit acceptance oracle;
it never selects a circuit parameter or fitting window.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Iterable


CODE = Path(__file__).resolve().parents[1]
CASE = CODE.parent
os.environ.setdefault("MPLCONFIGDIR", str(CASE / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(CODE / "src"))

from finite_size_scaling import (  # noqa: E402
    ScalingCurve,
    bootstrap_measurement_fractions,
    fit_data_collapse,
    leave_one_size_out_fits,
)
from stabilizer_dynamics import (  # noqa: E402
    DynamicsConfig,
    observable_worker_pool,
    run_observable_ensemble,
    run_trajectory_ensemble,
)


TARGET_ID = "T001"
MODEL_REVISION = "mth001-mth003-shared-observables-v1"
DEFAULT_SEED = 1_903_051_240
PAPER_REALIZATIONS = 240
PAPER_DYNAMICS_STEPS = 32
PAPER_TRANSITION_DEPTHS = (1, 3, 5, 7, 11, 15, 23, 31)

# Comparison-only values printed in Supplement Table SI.  They are referenced
# only in build_checks after every independent fit has completed.
PUBLISHED_ACCEPTANCE_PC = {
    1: 0.162,
    3: 0.412,
    5: 0.589,
    7: 0.707,
    11: 0.826,
    15: 0.862,
    23: 0.883,
    31: 0.886,
}


@dataclass(frozen=True)
class ScalePlan:
    scale: str
    dynamics_realizations: int
    steady_realizations: int
    phase_realizations: int
    transition_realizations: int
    steady_probabilities: tuple[float, ...]
    phase_depths: tuple[int, ...]
    phase_probabilities: tuple[float, ...]
    transition_depths: tuple[int, ...]
    transition_sizes: tuple[int, ...]
    transition_probability_points: int
    bootstrap_samples: int


@dataclass(frozen=True)
class DynamicsSetting:
    label: str
    blocks: int
    steps: int


@dataclass(frozen=True)
class DynamicsOutput:
    setting: DynamicsSetting
    seed: int
    entropy_after_measurement: np.ndarray
    entropy_before_measurement: np.ndarray
    measurement_entropy_change: np.ndarray
    runtime_seconds: float
    workers: int
    requested_workers: int

    @property
    def realizations(self) -> int:
        return int(self.entropy_after_measurement.shape[0])


@dataclass(frozen=True)
class ObservableSetting:
    campaign: str
    label: str
    blocks: int
    qubits_per_block: int
    depth: int
    measurement_fraction: float
    steps: int
    boundary: str
    sample_steps: tuple[int, ...]
    include_tripartite_information: bool = False

    @property
    def key(self) -> str:
        p = f"{self.measurement_fraction:.6f}".rstrip("0").rstrip(".")
        return (
            f"{self.campaign}_{self.label}_L{self.blocks}_m{self.qubits_per_block}"
            f"_d{self.depth}_p{p}_t{self.steps}"
        ).replace(".", "p")


@dataclass(frozen=True)
class ObservableOutput:
    setting: ObservableSetting
    seed: int
    half_chain_entropy: np.ndarray
    tripartite_mutual_information: np.ndarray | None
    runtime_seconds: float
    workers: int
    requested_workers: int

    @property
    def realizations(self) -> int:
        return int(self.half_chain_entropy.shape[0])


@dataclass(frozen=True)
class TransitionFit:
    depth: int
    critical_probability: float
    critical_exponent: float
    cost: float
    critical_probability_error: float
    critical_exponent_error: float
    probability_at_boundary: bool
    exponent_at_boundary: bool
    leave_one_size_out_probabilities: tuple[float, ...]
    bootstrap_probabilities: tuple[float, ...]
    bootstrap_exponents: tuple[float, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("smoke", "feature", "paper"), default="smoke")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def scale_plan(scale: str) -> ScalePlan:
    if scale == "smoke":
        return ScalePlan(
            scale=scale,
            dynamics_realizations=2,
            steady_realizations=2,
            phase_realizations=2,
            transition_realizations=2,
            steady_probabilities=(0.0, 0.5, 1.0),
            phase_depths=(1, 7, 31),
            phase_probabilities=(0.0, 0.25, 0.5, 0.75, 1.0),
            transition_depths=(1, 7, 31),
            transition_sizes=(4, 8, 12),
            transition_probability_points=5,
            bootstrap_samples=2,
        )
    if scale == "feature":
        return ScalePlan(
            scale=scale,
            dynamics_realizations=24,
            steady_realizations=12,
            phase_realizations=8,
            transition_realizations=8,
            steady_probabilities=tuple(float(value) for value in np.linspace(0.0, 1.0, 11)),
            phase_depths=(1, 2, 3, 4, 5, 7, 9, 11, 15, 23, 31, 44),
            phase_probabilities=tuple(float(value) for value in np.linspace(0.0, 1.0, 11)),
            transition_depths=PAPER_TRANSITION_DEPTHS,
            transition_sizes=(8, 12, 16, 24),
            transition_probability_points=9,
            bootstrap_samples=10,
        )
    return ScalePlan(
        scale=scale,
        dynamics_realizations=PAPER_REALIZATIONS,
        steady_realizations=PAPER_REALIZATIONS,
        phase_realizations=PAPER_REALIZATIONS,
        transition_realizations=PAPER_REALIZATIONS,
        steady_probabilities=tuple(float(value) for value in np.linspace(0.0, 1.0, 21)),
        phase_depths=tuple(range(1, 45)),
        phase_probabilities=tuple(float(value) for value in np.linspace(0.0, 1.0, 41)),
        transition_depths=PAPER_TRANSITION_DEPTHS,
        transition_sizes=(12, 16, 24, 32, 48, 64),
        transition_probability_points=41,
        bootstrap_samples=100,
    )


def odd_steps_ending_at(step: int, samples: int = 3) -> tuple[int, ...]:
    final = step if step % 2 else step - 1
    selected = tuple(range(final - 2 * (samples - 1), final + 1, 2))
    if selected[0] <= 0:
        raise ValueError("equilibration horizon is too short for requested samples")
    return selected


def equilibration_steps(blocks: int, depth: int, scale: str) -> int:
    if scale == "smoke":
        return 9
    if depth <= 3:
        estimate = max(101, 6 * blocks + 1)
    elif depth <= 7:
        estimate = max(65, 4 * blocks + 1)
    elif depth <= 15:
        estimate = max(49, 3 * blocks + 1)
    else:
        estimate = max(33, 2 * blocks + 1)
    return estimate if estimate % 2 else estimate + 1


def transition_probability_grid(
    probabilities: Iterable[float],
    density: Iterable[float],
    *,
    points: int,
    half_width: float,
    area_law_density_threshold: float = 0.05,
) -> tuple[float, ...]:
    """Choose a fit window from the generated volume-to-area crossover.

    For finite ``L``, the area-law entropy density is ``O(1/L)``.  The fixed
    threshold identifies the first coarse interval entering that regime.  A
    gradient fallback is used only if the generated grid never crosses it.
    """

    p = np.asarray(tuple(probabilities), dtype=float)
    values = np.asarray(tuple(density), dtype=float)
    if len(p) < 3 or len(p) != len(values) or np.any(np.diff(p) <= 0):
        raise ValueError("phase-grid probabilities must be aligned and increasing")
    if points < 3:
        raise ValueError("transition grid needs at least three points")
    if area_law_density_threshold <= 0:
        raise ValueError("area-law density threshold must be positive")
    below_threshold = np.flatnonzero(values <= area_law_density_threshold)
    if below_threshold.size and below_threshold[0] > 0:
        interval = int(below_threshold[0] - 1)
    else:
        smoothed = values
        if len(values) >= 5:
            padded = np.pad(values, 1, mode="edge")
            smoothed = np.convolve(padded, np.ones(3) / 3.0, mode="valid")
        slope = np.diff(smoothed) / np.diff(p)
        interval = int(np.argmin(slope))
    center = 0.5 * (p[interval] + p[interval + 1])
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    if upper - lower < half_width:
        if lower == 0.0:
            upper = min(1.0, 2.0 * half_width)
        else:
            lower = max(0.0, 1.0 - 2.0 * half_width)
    return tuple(float(value) for value in np.linspace(lower, upper, points))


def setting_seed(root_seed: int, campaign_code: int, index: int) -> int:
    sequence = np.random.SeedSequence([int(root_seed), int(campaign_code), int(index)])
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def checkpoint_directory() -> Path:
    path = CASE / ".checkpoints" / "t001"
    path.mkdir(parents=True, exist_ok=True)
    return path


def dynamics_checkpoint_path(
    *,
    scale: str,
    realizations: int,
    root_seed: int,
    setting: DynamicsSetting,
) -> Path:
    signature = f"{MODEL_REVISION}_{scale}_r{realizations}_seed{root_seed}"
    return checkpoint_directory() / (
        f"{signature}_dynamics_{setting.label}_L{setting.blocks}_t{setting.steps}.npz"
    )


def observable_checkpoint_path(
    *,
    scale: str,
    realizations: int,
    root_seed: int,
    setting: ObservableSetting,
) -> Path:
    signature = f"{MODEL_REVISION}_{scale}_r{realizations}_seed{root_seed}"
    return checkpoint_directory() / f"{signature}_{setting.key}.npz"


def save_dynamics_checkpoint(path: Path, output: DynamicsOutput) -> None:
    np.savez_compressed(
        path,
        seed=np.array(output.seed, dtype=np.uint64),
        entropy_after_measurement=output.entropy_after_measurement,
        entropy_before_measurement=output.entropy_before_measurement,
        measurement_entropy_change=output.measurement_entropy_change,
        runtime_seconds=np.array(output.runtime_seconds),
        workers=np.array(output.workers),
        requested_workers=np.array(output.requested_workers),
    )


def load_dynamics_checkpoint(
    path: Path,
    setting: DynamicsSetting,
    expected_realizations: int,
) -> DynamicsOutput:
    with np.load(path, allow_pickle=False) as payload:
        output = DynamicsOutput(
            setting=setting,
            seed=int(payload["seed"].item()),
            entropy_after_measurement=payload["entropy_after_measurement"].copy(),
            entropy_before_measurement=payload["entropy_before_measurement"].copy(),
            measurement_entropy_change=payload["measurement_entropy_change"].copy(),
            runtime_seconds=float(payload["runtime_seconds"].item()),
            workers=int(payload["workers"].item()),
            requested_workers=int(payload["requested_workers"].item()),
        )
    if output.realizations != expected_realizations:
        raise ValueError(f"dynamics checkpoint realization mismatch: {path}")
    return output


def save_observable_checkpoint(path: Path, output: ObservableOutput) -> None:
    arrays: dict[str, np.ndarray] = {
        "seed": np.array(output.seed, dtype=np.uint64),
        "half_chain_entropy": output.half_chain_entropy,
        "runtime_seconds": np.array(output.runtime_seconds),
        "workers": np.array(output.workers),
        "requested_workers": np.array(output.requested_workers),
    }
    if output.tripartite_mutual_information is not None:
        arrays["tripartite_mutual_information"] = output.tripartite_mutual_information
    np.savez_compressed(path, **arrays)


def load_observable_checkpoint(
    path: Path,
    setting: ObservableSetting,
    expected_realizations: int,
) -> ObservableOutput:
    with np.load(path, allow_pickle=False) as payload:
        tripartite = (
            payload["tripartite_mutual_information"].copy()
            if "tripartite_mutual_information" in payload.files
            else None
        )
        output = ObservableOutput(
            setting=setting,
            seed=int(payload["seed"].item()),
            half_chain_entropy=payload["half_chain_entropy"].copy(),
            tripartite_mutual_information=tripartite,
            runtime_seconds=float(payload["runtime_seconds"].item()),
            workers=int(payload["workers"].item()),
            requested_workers=int(payload["requested_workers"].item()),
        )
    if output.realizations != expected_realizations:
        raise ValueError(f"observable checkpoint realization mismatch: {path}")
    return output


def run_dynamics(
    plan: ScalePlan,
    *,
    root_seed: int,
    workers: int,
    resume: bool,
) -> tuple[DynamicsOutput, ...]:
    steps = 7 if plan.scale == "smoke" else PAPER_DYNAMICS_STEPS
    settings = (
        DynamicsSetting("L32", 32, steps),
        DynamicsSetting("L48", 48, steps),
    )
    outputs: list[DynamicsOutput] = []
    for index, setting in enumerate(settings):
        seed = setting_seed(root_seed, 1, index)
        path = dynamics_checkpoint_path(
            scale=plan.scale,
            realizations=plan.dynamics_realizations,
            root_seed=root_seed,
            setting=setting,
        )
        if resume and path.exists():
            output = load_dynamics_checkpoint(
                path,
                setting,
                plan.dynamics_realizations,
            )
            status = "resumed"
        else:
            result = run_trajectory_ensemble(
                DynamicsConfig(
                    blocks=setting.blocks,
                    qubits_per_block=11,
                    circuit_depth=44,
                    measurement_fraction=0.4,
                    steps=setting.steps,
                    boundary="open",
                ),
                realizations=plan.dynamics_realizations,
                seed=seed,
                workers=workers,
            )
            output = DynamicsOutput(
                setting=setting,
                seed=seed,
                entropy_after_measurement=result.entropy_after_measurement,
                entropy_before_measurement=result.entropy_before_measurement,
                measurement_entropy_change=result.measurement_entropy_change,
                runtime_seconds=result.runtime_seconds,
                workers=result.workers,
                requested_workers=result.requested_workers,
            )
            save_dynamics_checkpoint(path, output)
            status = "completed"
        outputs.append(output)
        print(
            json.dumps(
                {
                    "campaign": "dynamics",
                    "setting": setting.label,
                    "status": status,
                    "realizations": output.realizations,
                    "runtime_seconds": output.runtime_seconds,
                }
            ),
            flush=True,
        )
    return tuple(outputs)


def steady_settings(plan: ScalePlan) -> tuple[ObservableSetting, ...]:
    curves = (("d44_m11", 44, 11), ("d84_m21", 84, 21), ("d3_m11", 3, 11))
    settings: list[ObservableSetting] = []
    for label, depth, m in curves:
        steps = equilibration_steps(32, depth, plan.scale)
        for probability in plan.steady_probabilities:
            settings.append(
                ObservableSetting(
                    campaign="steady",
                    label=label,
                    blocks=32,
                    qubits_per_block=m,
                    depth=depth,
                    measurement_fraction=probability,
                    steps=steps,
                    boundary="open",
                    sample_steps=odd_steps_ending_at(steps),
                )
            )
    return tuple(settings)


def phase_settings(plan: ScalePlan) -> tuple[ObservableSetting, ...]:
    settings: list[ObservableSetting] = []
    for depth in plan.phase_depths:
        steps = equilibration_steps(32, depth, plan.scale)
        for probability in plan.phase_probabilities:
            settings.append(
                ObservableSetting(
                    campaign="phase",
                    label=f"d{depth}",
                    blocks=32,
                    qubits_per_block=11,
                    depth=depth,
                    measurement_fraction=probability,
                    steps=steps,
                    boundary="open",
                    sample_steps=odd_steps_ending_at(steps),
                )
            )
    return tuple(settings)


def run_observable_settings(
    settings: tuple[ObservableSetting, ...],
    *,
    campaign_code: int,
    scale: str,
    realizations: int,
    root_seed: int,
    workers: int,
    resume: bool,
    executor: ProcessPoolExecutor | None,
) -> tuple[ObservableOutput, ...]:
    outputs: list[ObservableOutput] = []
    total = len(settings)
    for index, setting in enumerate(settings):
        seed = setting_seed(root_seed, campaign_code, index)
        path = observable_checkpoint_path(
            scale=scale,
            realizations=realizations,
            root_seed=root_seed,
            setting=setting,
        )
        if resume and path.exists():
            output = load_observable_checkpoint(path, setting, realizations)
            status = "resumed"
        else:
            result = run_observable_ensemble(
                DynamicsConfig(
                    blocks=setting.blocks,
                    qubits_per_block=setting.qubits_per_block,
                    circuit_depth=setting.depth,
                    measurement_fraction=setting.measurement_fraction,
                    steps=setting.steps,
                    boundary=setting.boundary,
                ),
                realizations=realizations,
                seed=seed,
                sample_steps=setting.sample_steps,
                workers=workers,
                include_tripartite_information=setting.include_tripartite_information,
                executor=executor,
                create_executor=False,
            )
            output = ObservableOutput(
                setting=setting,
                seed=seed,
                half_chain_entropy=result.half_chain_entropy,
                tripartite_mutual_information=result.tripartite_mutual_information,
                runtime_seconds=result.runtime_seconds,
                workers=result.workers,
                requested_workers=result.requested_workers,
            )
            save_observable_checkpoint(path, output)
            status = "completed"
        outputs.append(output)
        print(
            json.dumps(
                {
                    "campaign": setting.campaign,
                    "progress": f"{index + 1}/{total}",
                    "setting": setting.key,
                    "status": status,
                    "realizations": output.realizations,
                    "runtime_seconds": output.runtime_seconds,
                }
            ),
            flush=True,
        )
    return tuple(outputs)


def observable_mean_and_error(values: np.ndarray) -> tuple[float, float, float]:
    per_trajectory = np.mean(values, axis=1)
    ddof = 1 if len(per_trajectory) > 1 else 0
    standard_deviation = float(np.std(per_trajectory, ddof=ddof))
    return (
        float(np.mean(per_trajectory)),
        standard_deviation,
        standard_deviation / np.sqrt(len(per_trajectory)),
    )


def density_mean(output: ObservableOutput) -> float:
    denominator = output.setting.blocks * output.setting.qubits_per_block / 2
    return observable_mean_and_error(output.half_chain_entropy / denominator)[0]


def phase_density_by_depth(
    plan: ScalePlan,
    outputs: tuple[ObservableOutput, ...],
) -> dict[int, tuple[float, ...]]:
    lookup = {
        (output.setting.depth, output.setting.measurement_fraction): density_mean(output)
        for output in outputs
    }
    return {
        depth: tuple(lookup[(depth, probability)] for probability in plan.phase_probabilities)
        for depth in plan.phase_depths
    }


def transition_settings(
    plan: ScalePlan,
    phase_outputs: tuple[ObservableOutput, ...],
) -> tuple[ObservableSetting, ...]:
    density_curves = phase_density_by_depth(plan, phase_outputs)
    settings: list[ObservableSetting] = []
    half_width = 0.22 if plan.scale == "smoke" else 0.14 if plan.scale == "feature" else 0.08
    for depth in plan.transition_depths:
        phase_depth = min(plan.phase_depths, key=lambda candidate: abs(candidate - depth))
        probabilities = transition_probability_grid(
            plan.phase_probabilities,
            density_curves[phase_depth],
            points=plan.transition_probability_points,
            half_width=half_width,
        )
        for blocks in plan.transition_sizes:
            steps = equilibration_steps(blocks, depth, plan.scale)
            for probability in probabilities:
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


def fit_transitions(
    plan: ScalePlan,
    outputs: tuple[ObservableOutput, ...],
    *,
    root_seed: int,
) -> tuple[TransitionFit, ...]:
    fits: list[TransitionFit] = []
    for depth_index, depth in enumerate(plan.transition_depths):
        selected = [output for output in outputs if output.setting.depth == depth]
        probabilities = sorted(
            {output.setting.measurement_fraction for output in selected}
        )
        curves: list[ScalingCurve] = []
        for blocks in plan.transition_sizes:
            means: list[float] = []
            errors: list[float] = []
            for probability in probabilities:
                output = next(
                    item
                    for item in selected
                    if item.setting.blocks == blocks
                    and np.isclose(item.setting.measurement_fraction, probability)
                )
                if output.tripartite_mutual_information is None:
                    raise AssertionError("transition output is missing I3")
                mean, _, standard_error = observable_mean_and_error(
                    output.tripartite_mutual_information
                )
                means.append(mean)
                errors.append(max(standard_error, 1.0 / np.sqrt(output.realizations)))
            curves.append(
                ScalingCurve(
                    size=blocks,
                    measurement_fraction=np.asarray(probabilities),
                    observable=np.asarray(means),
                    standard_error=np.asarray(errors),
                )
            )
        grid_points = 13 if plan.scale == "smoke" else 17 if plan.scale == "feature" else 31
        refinement_rounds = 2 if plan.scale != "paper" else 3
        fit_kwargs = {
            "critical_probability_bounds": (min(probabilities), max(probabilities)),
            "critical_exponent_bounds": (0.7, 1.8),
            "grid_points": grid_points,
            "refinement_rounds": refinement_rounds,
        }
        fit = fit_data_collapse(curves, **fit_kwargs)
        omitted = leave_one_size_out_fits(curves, **fit_kwargs)
        bootstrap = bootstrap_measurement_fractions(
            curves,
            samples=plan.bootstrap_samples,
            sample_fraction=0.8,
            seed=setting_seed(root_seed, 5, depth_index),
            **fit_kwargs,
        )
        omitted_probabilities = tuple(
            item.critical_probability for item in omitted.values()
        )
        probability_error = max(
            float(np.std(omitted_probabilities, ddof=1))
            if len(omitted_probabilities) > 1
            else 0.0,
            float(np.std(bootstrap.critical_probabilities, ddof=1))
            if len(bootstrap.critical_probabilities) > 1
            else 0.0,
            (probabilities[1] - probabilities[0]) / 2,
        )
        exponent_error = max(
            float(np.std(bootstrap.critical_exponents, ddof=1))
            if len(bootstrap.critical_exponents) > 1
            else 0.0,
            0.01,
        )
        fits.append(
            TransitionFit(
                depth=depth,
                critical_probability=fit.critical_probability,
                critical_exponent=fit.critical_exponent,
                cost=fit.cost,
                critical_probability_error=probability_error,
                critical_exponent_error=exponent_error,
                probability_at_boundary=fit.critical_probability_at_boundary,
                exponent_at_boundary=fit.critical_exponent_at_boundary,
                leave_one_size_out_probabilities=omitted_probabilities,
                bootstrap_probabilities=tuple(
                    float(value) for value in bootstrap.critical_probabilities
                ),
                bootstrap_exponents=tuple(
                    float(value) for value in bootstrap.critical_exponents
                ),
            )
        )
    return tuple(fits)


def save_raw(
    path: Path,
    dynamics: tuple[DynamicsOutput, ...],
    steady: tuple[ObservableOutput, ...],
    phase: tuple[ObservableOutput, ...],
    transition: tuple[ObservableOutput, ...],
) -> None:
    arrays: dict[str, np.ndarray] = {}
    for output in dynamics:
        prefix = f"dynamics_{output.setting.label.lower()}"
        arrays[f"{prefix}_entropy_after_measurement"] = output.entropy_after_measurement
        arrays[f"{prefix}_entropy_before_measurement"] = output.entropy_before_measurement
        arrays[f"{prefix}_measurement_entropy_change"] = output.measurement_entropy_change
    for output in (*steady, *phase, *transition):
        prefix = output.setting.key
        arrays[f"{prefix}_half_chain_entropy"] = output.half_chain_entropy
        if output.tripartite_mutual_information is not None:
            arrays[f"{prefix}_tripartite_mutual_information"] = (
                output.tripartite_mutual_information
            )
    np.savez_compressed(path, **arrays)


def write_csv(
    path: Path,
    dynamics: tuple[DynamicsOutput, ...],
    steady: tuple[ObservableOutput, ...],
    phase: tuple[ObservableOutput, ...],
    transition: tuple[ObservableOutput, ...],
) -> None:
    fieldnames = [
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for output in dynamics:
            denominator = output.setting.blocks * 11 / 2
            density = output.entropy_after_measurement / denominator
            density_mean = np.mean(density, axis=0)
            density_std = np.std(density, axis=0, ddof=1 if output.realizations > 1 else 0)
            density_se = density_std / np.sqrt(output.realizations)
            change_mean = np.mean(output.measurement_entropy_change, axis=0)
            change_std = np.std(
                output.measurement_entropy_change,
                axis=0,
                ddof=1 if output.realizations > 1 else 0,
            )
            change_se = change_std / np.sqrt(output.realizations)
            for time, value in enumerate(density_mean):
                writer.writerow(
                    {
                        "campaign": "dynamics",
                        "label": output.setting.label,
                        "L": output.setting.blocks,
                        "m": 11,
                        "d": 44,
                        "p": 0.4,
                        "time": time,
                        "observable": "half_chain_entropy_density",
                        "mean": float(value),
                        "standard_deviation": float(density_std[time]),
                        "standard_error": float(density_se[time]),
                        "realizations": output.realizations,
                    }
                )
                if time > 0:
                    writer.writerow(
                        {
                            "campaign": "dynamics",
                            "label": output.setting.label,
                            "L": output.setting.blocks,
                            "m": 11,
                            "d": 44,
                            "p": 0.4,
                            "time": time,
                            "observable": "measurement_entropy_change",
                            "mean": float(change_mean[time - 1]),
                            "standard_deviation": float(change_std[time - 1]),
                            "standard_error": float(change_se[time - 1]),
                            "realizations": output.realizations,
                        }
                    )
        for output in (*steady, *phase, *transition):
            half_mean, half_std, half_se = observable_mean_and_error(
                output.half_chain_entropy
            )
            writer.writerow(
                {
                    "campaign": output.setting.campaign,
                    "label": output.setting.label,
                    "L": output.setting.blocks,
                    "m": output.setting.qubits_per_block,
                    "d": output.setting.depth,
                    "p": output.setting.measurement_fraction,
                    "time": output.setting.sample_steps[-1],
                    "observable": "half_chain_entropy",
                    "mean": half_mean,
                    "standard_deviation": half_std,
                    "standard_error": half_se,
                    "realizations": output.realizations,
                }
            )
            if output.tripartite_mutual_information is not None:
                mean, standard_deviation, standard_error = observable_mean_and_error(
                    output.tripartite_mutual_information
                )
                writer.writerow(
                    {
                        "campaign": output.setting.campaign,
                        "label": output.setting.label,
                        "L": output.setting.blocks,
                        "m": output.setting.qubits_per_block,
                        "d": output.setting.depth,
                        "p": output.setting.measurement_fraction,
                        "time": output.setting.sample_steps[-1],
                        "observable": "tripartite_mutual_information",
                        "mean": mean,
                        "standard_deviation": standard_deviation,
                        "standard_error": standard_error,
                        "realizations": output.realizations,
                    }
                )


def write_fit_csv(path: Path, fits: tuple[TransitionFit, ...]) -> None:
    fieldnames = [
        "depth",
        "critical_probability",
        "critical_probability_error",
        "critical_exponent",
        "critical_exponent_error",
        "cost",
        "probability_at_boundary",
        "exponent_at_boundary",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for fit in fits:
            writer.writerow(
                {
                    field: getattr(fit, field)
                    for field in fieldnames
                }
            )


def render(
    path: Path,
    plan: ScalePlan,
    dynamics: tuple[DynamicsOutput, ...],
    steady: tuple[ObservableOutput, ...],
    phase: tuple[ObservableOutput, ...],
    fits: tuple[TransitionFit, ...],
) -> None:
    plt.rcParams.update({"font.size": 9.5, "axes.linewidth": 0.8})
    figure = plt.figure(figsize=(15.2, 5.2), constrained_layout=True)
    grid = figure.add_gridspec(2, 5, width_ratios=(1.2, 1.0, 1.0, 1.25, 1.25))
    entropy_axis = figure.add_subplot(grid[0, 0])
    change_axis = figure.add_subplot(grid[1, 0], sharex=entropy_axis)
    steady_axis = figure.add_subplot(grid[:, 1:3])
    phase_axis = figure.add_subplot(grid[:, 3:5])

    colors = {"L32": "#0879bd", "L48": "#9bcda8"}
    for output in dynamics:
        denominator = output.setting.blocks * 11 / 2
        times = np.arange(output.setting.steps + 1)
        indices = np.concatenate((np.array([0]), np.arange(1, output.setting.steps + 1, 2)))
        density = output.entropy_after_measurement / denominator
        entropy_axis.plot(
            times[indices],
            np.mean(density, axis=0)[indices],
            marker="o",
            markersize=2.4,
            linewidth=1.2,
            color=colors[output.setting.label],
            label=rf"$L={output.setting.blocks}$",
        )
        changes = output.measurement_entropy_change
        change_mean = np.mean(changes, axis=0)
        change_std = np.std(changes, axis=0, ddof=1 if output.realizations > 1 else 0)
        change_se = change_std / np.sqrt(output.realizations)
        change_indices = np.arange(0, output.setting.steps, 2)
        change_axis.errorbar(
            change_indices + 1,
            change_mean[change_indices],
            yerr=change_se[change_indices],
            marker="o",
            markersize=2.2,
            linewidth=1.0,
            elinewidth=0.7,
            capsize=1.8,
            color=colors[output.setting.label],
        )
    entropy_axis.axhline(0.6, color="black", linestyle="dashdot", linewidth=1.0)
    change_axis.axhline(0.0, color="black", linestyle=(0, (1, 4)), linewidth=0.8)
    entropy_axis.set_ylabel(r"$S/(Lm/2)$")
    change_axis.set_ylabel(r"$\Delta S_{\mathrm{meas}}$")
    change_axis.set_xlabel(r"$t$")
    entropy_axis.set_ylim(0, 0.68)
    change_axis.set_ylim(-1.1, 0.08)
    entropy_axis.legend(frameon=False, fontsize=8)
    plt.setp(entropy_axis.get_xticklabels(), visible=False)

    curve_specs = (
        ("d44_m11", "D", "#0879bd", r"$d=44,m=11$"),
        ("d84_m21", "s", "#74a62d", r"$d=84,m=21$"),
        ("d3_m11", ">", "#e75b16", r"$d=3,m=11$"),
    )
    for label, marker, color, display in curve_specs:
        selected = sorted(
            (output for output in steady if output.setting.label == label),
            key=lambda output: output.setting.measurement_fraction,
        )
        steady_axis.plot(
            [output.setting.measurement_fraction for output in selected],
            [density_mean(output) for output in selected],
            linestyle="none",
            marker=marker,
            markersize=5.0,
            color=color,
            label=display,
        )
    p_fill = np.linspace(0.0, 1.0, 200)
    steady_axis.fill_between(p_fill, 1.0 - p_fill, 1.0, color="#d8d8d8")
    steady_axis.plot(p_fill, 1.0 - p_fill, color="white", linestyle="--", linewidth=1.3)
    steady_axis.set_xlim(0, 1)
    steady_axis.set_ylim(0, 1)
    steady_axis.set_xlabel(r"$p$")
    steady_axis.set_ylabel(r"$S/(Lm/2)$")
    steady_axis.legend(frameon=False, fontsize=8, loc="upper right")

    density_curves = phase_density_by_depth(plan, phase)
    matrix = np.asarray([density_curves[depth] for depth in plan.phase_depths]).T
    image = phase_axis.pcolormesh(
        np.asarray(plan.phase_depths, dtype=float) / 11.0,
        np.asarray(plan.phase_probabilities, dtype=float),
        np.clip(matrix, 1e-3, 1.0),
        shading="auto",
        cmap="RdYlBu",
        norm=LogNorm(vmin=1e-3, vmax=1.0),
    )
    phase_axis.errorbar(
        [fit.depth / 11.0 for fit in fits],
        [fit.critical_probability for fit in fits],
        yerr=[fit.critical_probability_error for fit in fits],
        fmt="o",
        markersize=2.8,
        color="black",
        ecolor="black",
        capsize=2,
        linewidth=0.8,
    )
    phase_axis.set_xscale("log")
    phase_axis.set_xlim(min(plan.phase_depths) / 11.0, max(plan.phase_depths) / 11.0)
    phase_axis.set_ylim(0, 1)
    phase_axis.set_xlabel(r"$d/m$")
    phase_axis.set_ylabel(r"$p$")
    phase_axis.text(0.06, 0.88, "Area-law", color="white", fontsize=16, transform=phase_axis.transAxes)
    phase_axis.text(0.58, 0.12, "Volume-law", color="white", fontsize=15, transform=phase_axis.transAxes)
    colorbar = figure.colorbar(image, ax=phase_axis, pad=0.02)
    colorbar.set_label(r"$S/(Lm/2)$")

    entropy_axis.text(-0.25, 1.02, "(b)", transform=entropy_axis.transAxes, fontsize=13)
    change_axis.text(-0.25, 1.02, "(c)", transform=change_axis.transAxes, fontsize=13)
    steady_axis.text(-0.14, 1.02, "(d)", transform=steady_axis.transAxes, fontsize=13)
    phase_axis.text(-0.14, 1.02, "(e)", transform=phase_axis.transAxes, fontsize=13)
    for axis in (entropy_axis, change_axis, steady_axis, phase_axis):
        axis.tick_params(direction="in", top=True, right=True)
    figure.savefig(path, dpi=220, facecolor="white")
    plt.close(figure)


def build_checks(
    plan: ScalePlan,
    dynamics: tuple[DynamicsOutput, ...],
    steady: tuple[ObservableOutput, ...],
    phase: tuple[ObservableOutput, ...],
    transition: tuple[ObservableOutput, ...],
    fits: tuple[TransitionFit, ...],
) -> dict[str, object]:
    half_entropy_bounds = all(
        np.all(output.half_chain_entropy >= 0)
        and np.all(
            output.half_chain_entropy
            <= output.setting.blocks * output.setting.qubits_per_block // 2
        )
        for output in (*steady, *phase, *transition)
    )
    criteria = {
        "all_four_theory_numerical_panels_generated": bool(dynamics and steady and phase and fits),
        "two_paper_dynamics_geometries_present": {output.setting.blocks for output in dynamics} == {32, 48},
        "three_steady_state_parameter_families_present": {output.setting.label for output in steady} == {"d44_m11", "d84_m21", "d3_m11"},
        "phase_grid_uses_m11_L32": all(
            output.setting.qubits_per_block == 11 and output.setting.blocks == 32
            for output in phase
        ),
        "transition_grid_uses_periodic_I3": all(
            output.setting.boundary == "periodic"
            and output.tripartite_mutual_information is not None
            for output in transition
        ),
        "half_chain_entropy_bounds_pass": half_entropy_bounds,
        "measurement_change_is_nonpositive": all(
            np.all(output.measurement_entropy_change <= 0) for output in dynamics
        ),
        "integer_stabilizer_observables_persisted": all(
            np.issubdtype(output.half_chain_entropy.dtype, np.integer)
            for output in (*steady, *phase, *transition)
        ),
        "source_pixels_absent": True,
    }

    steady_lookup = {
        (output.setting.label, round(output.setting.measurement_fraction, 8)): density_mean(output)
        for output in steady
    }
    monotonic_curves: dict[str, bool] = {}
    for label in ("d44_m11", "d84_m21", "d3_m11"):
        values = [steady_lookup[(label, round(probability, 8))] for probability in plan.steady_probabilities]
        tolerance = 0.08 if plan.scale == "smoke" else 0.04
        monotonic_curves[label] = all(
            right <= left + tolerance for left, right in zip(values, values[1:])
        )

    density_curves = phase_density_by_depth(plan, phase)
    phase_monotonic_fraction = float(
        np.mean(
            [
                right <= left + (0.08 if plan.scale == "smoke" else 0.05)
                for values in density_curves.values()
                for left, right in zip(values, values[1:])
            ]
        )
    )
    fit_by_depth = {fit.depth: fit for fit in fits}
    published_errors = {
        depth: abs(fit_by_depth[depth].critical_probability - reference)
        for depth, reference in PUBLISHED_ACCEPTANCE_PC.items()
        if depth in fit_by_depth
    }
    ordered_probabilities = [fit.critical_probability for fit in sorted(fits, key=lambda item: item.depth)]
    feature_checks = {
        "dynamics_reaches_nonzero_volume_law_density": all(
            float(np.mean(output.entropy_after_measurement[:, -5:]))
            / (output.setting.blocks * 11 / 2)
            > 0.25
            for output in dynamics
        ),
        "early_measurements_are_protected_at_d44_p04": all(
            float(np.mean(output.measurement_entropy_change[:, :7:2])) > -0.12
            for output in dynamics
        ),
        "steady_curves_are_monotone_with_measurement_fraction": all(monotonic_curves.values()),
        "p_zero_is_volume_law_and_p_one_is_product": all(
            steady_lookup[(label, round(plan.steady_probabilities[0], 8))] > 0.65
            and steady_lookup[(label, round(plan.steady_probabilities[-1], 8))] < 0.02
            for label in ("d44_m11", "d84_m21", "d3_m11")
        ),
        "phase_grid_is_predominantly_monotone_in_p": phase_monotonic_fraction >= 0.9,
        "transition_probability_increases_with_depth": all(
            right >= left - 0.08
            for left, right in zip(ordered_probabilities, ordered_probabilities[1:])
        ),
        "independent_transition_markers_agree_with_published_values": (
            bool(published_errors) and float(np.mean(tuple(published_errors.values()))) < 0.12
        ),
        "transition_windows_contain_fit_optima": all(
            not fit.probability_at_boundary for fit in fits
        ),
    }
    paper_exact = (
        plan.scale == "paper"
        and plan.dynamics_realizations == PAPER_REALIZATIONS
        and plan.steady_realizations == PAPER_REALIZATIONS
        and plan.phase_realizations == PAPER_REALIZATIONS
        and plan.transition_realizations == PAPER_REALIZATIONS
        and max(plan.transition_sizes) == 64
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
            else "feature_reproduced"
            if all(feature_checks.values())
            else "mechanics_verified"
        ),
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "published_values_used_for_generation": False,
        "published_values_role": "post_fit_acceptance_only",
        "scale": plan.scale,
        "parameter_match": "paper_exact" if paper_exact else "paper_geometry_reduced_sampling_or_grid",
        "criteria": criteria,
        "feature_checks": feature_checks,
        "metrics": {
            "runtime_seconds": float(
                sum(output.runtime_seconds for output in (*dynamics, *steady, *phase, *transition))
            ),
            "phase_monotonic_fraction": phase_monotonic_fraction,
            "transition_fit": {
                str(fit.depth): {
                    "critical_probability": fit.critical_probability,
                    "critical_probability_error": fit.critical_probability_error,
                    "critical_exponent": fit.critical_exponent,
                    "critical_exponent_error": fit.critical_exponent_error,
                    "cost": fit.cost,
                    "probability_at_boundary": fit.probability_at_boundary,
                    "exponent_at_boundary": fit.exponent_at_boundary,
                }
                for fit in fits
            },
            "published_acceptance_pc": PUBLISHED_ACCEPTANCE_PC,
            "published_acceptance_absolute_error": published_errors,
            "mean_published_acceptance_absolute_error": (
                float(np.mean(tuple(published_errors.values()))) if published_errors else None
            ),
        },
    }


def metadata_payload(
    plan: ScalePlan,
    *,
    root_seed: int,
    dynamics: tuple[DynamicsOutput, ...],
    steady: tuple[ObservableOutput, ...],
    phase: tuple[ObservableOutput, ...],
    transition: tuple[ObservableOutput, ...],
    fits: tuple[TransitionFit, ...],
    checks: dict[str, object],
) -> dict[str, object]:
    return {
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "published_values_used_for_generation": False,
        "formula_refs": ["EQC002", "EQC005", "EQC006", "EQC008"],
        "method_refs": ["MTH001", "MTH003"],
        "model_revision": MODEL_REVISION,
        "scale": plan.scale,
        "parameter_match": checks["parameter_match"],
        "root_seed": root_seed,
        "plan": {
            **plan.__dict__,
            "steady_probabilities": list(plan.steady_probabilities),
            "phase_depths": list(plan.phase_depths),
            "phase_probabilities": list(plan.phase_probabilities),
            "transition_depths": list(plan.transition_depths),
            "transition_sizes": list(plan.transition_sizes),
        },
        "campaign_counts": {
            "dynamics_settings": len(dynamics),
            "steady_settings": len(steady),
            "phase_settings": len(phase),
            "transition_settings": len(transition),
            "transition_fits": len(fits),
            "trajectories_total": sum(output.realizations for output in dynamics)
            + sum(output.realizations for output in (*steady, *phase, *transition)),
        },
        "runtime_seconds": checks["metrics"]["runtime_seconds"],
        "files": [
            "main_fig2_numerical_data.csv",
            "main_fig2_raw.npz",
            "main_fig2_transition_fits.csv",
            "main_fig2_reproduction.png",
            "t001_scientific_checks.json",
        ],
    }


def main() -> int:
    args = parse_args()
    plan = scale_plan(args.scale)
    workers = args.workers if args.workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 0:
        raise ValueError("workers must be positive")
    resume = not args.no_resume
    started = perf_counter()

    dynamics = run_dynamics(
        plan,
        root_seed=args.seed,
        workers=workers,
        resume=resume,
    )
    with observable_worker_pool(workers) as executor:
        steady = run_observable_settings(
            steady_settings(plan),
            campaign_code=2,
            scale=plan.scale,
            realizations=plan.steady_realizations,
            root_seed=args.seed,
            workers=workers,
            resume=resume,
            executor=executor,
        )
        phase = run_observable_settings(
            phase_settings(plan),
            campaign_code=3,
            scale=plan.scale,
            realizations=plan.phase_realizations,
            root_seed=args.seed,
            workers=workers,
            resume=resume,
            executor=executor,
        )
        transition = run_observable_settings(
            transition_settings(plan, phase),
            campaign_code=4,
            scale=plan.scale,
            realizations=plan.transition_realizations,
            root_seed=args.seed,
            workers=workers,
            resume=resume,
            executor=executor,
        )
    fits = fit_transitions(plan, transition, root_seed=args.seed)

    data_dir = CASE / "outputs" / "data"
    figure_dir = CASE / "outputs" / "figures"
    check_dir = CASE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / "main_fig2_numerical_data.csv"
    raw_path = data_dir / "main_fig2_raw.npz"
    fit_path = data_dir / "main_fig2_transition_fits.csv"
    metadata_path = data_dir / "main_fig2_metadata.json"
    figure_path = figure_dir / "main_fig2_reproduction.png"
    check_path = check_dir / "t001_scientific_checks.json"

    write_csv(data_path, dynamics, steady, phase, transition)
    save_raw(raw_path, dynamics, steady, phase, transition)
    write_fit_csv(fit_path, fits)
    render(figure_path, plan, dynamics, steady, phase, fits)
    checks = build_checks(plan, dynamics, steady, phase, transition, fits)
    check_path.write_text(
        json.dumps(checks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    metadata = metadata_payload(
        plan,
        root_seed=args.seed,
        dynamics=dynamics,
        steady=steady,
        phase=phase,
        transition=transition,
        fits=fits,
        checks=checks,
    )
    metadata["wall_runtime_seconds"] = perf_counter() - started
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": checks["status"],
                "scientific_feature_status": checks["scientific_feature_status"],
                "completion_status": checks["completion_status"],
                "parameter_match": checks["parameter_match"],
                "trajectory_runtime_seconds": checks["metrics"]["runtime_seconds"],
                "wall_runtime_seconds": metadata["wall_runtime_seconds"],
                "outputs": [
                    str(data_path),
                    str(raw_path),
                    str(fit_path),
                    str(figure_path),
                    str(check_path),
                ],
            },
            indent=2,
        )
    )
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
