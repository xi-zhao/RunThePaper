#!/usr/bin/env python3
"""Reproduce all three theory-numerical panels in Supplement Figure S6.

The campaign fixes the paper's relative circuit depth ``d/m=3`` and varies
the qubit-block size.  It first simulates a source-independent coarse
probability grid, chooses extra midpoint samples from a preliminary fit to
those generated values, and finally simulates the fitted critical points for
an independent ``S(p_c,L)=alpha log(L)+c`` regression.  Source pixels and
published plotted values are never numerical inputs.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
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

sys.path.insert(0, str(WORKSPACE / "scripts"))
sys.path.insert(0, str(WORKSPACE / "src"))

from finite_size_scaling import (  # noqa: E402
    ScalingCurve,
    bootstrap_measurement_fractions,
    collapse_cost,
    fit_data_collapse,
    fit_log_entropy,
    leave_one_size_out_fits,
)
from run_main_fig2 import (  # noqa: E402
    ObservableOutput,
    ObservableSetting,
    equilibration_steps,
    observable_mean_and_error,
    observable_worker_pool,
    odd_steps_ending_at,
    run_observable_settings,
    setting_seed,
)


TARGET_ID = "T006"
MODEL_REVISION = "s6-block-size-scaling-v1"
PAPER_BLOCK_SIZES = (3, 5, 7, 9, 11, 13)
RELATIVE_DEPTH = 3
FEATURE_SIZES = (8, 12, 16, 24)
SMOKE_SIZES = (8, 12, 16)
FEATURE_BASE_PROBABILITIES = tuple(float(value) for value in np.linspace(0.2, 0.98, 9))
SMOKE_BASE_PROBABILITIES = tuple(float(value) for value in np.linspace(0.2, 0.98, 5))
DEFAULT_SEED = 1_903_051_266


@dataclass(frozen=True)
class ScaleSpec:
    scale: str
    sizes: tuple[int, ...]
    base_probabilities: tuple[float, ...]
    transition_realizations: int
    refinement_points: int
    critical_realizations: int
    bootstrap_samples: int


@dataclass(frozen=True)
class BlockFit:
    m: int
    d: int
    critical_probability: float
    critical_probability_error: float
    critical_exponent: float
    critical_exponent_error: float
    collapse_cost: float
    unscaled_cost: float
    probability_at_boundary: bool
    exponent_at_boundary: bool
    leave_one_size_out_probability_span: float
    alpha: float
    alpha_error: float
    alpha_intercept: float
    alpha_r_squared: float


def require_guard() -> None:
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID", "") != TARGET_ID:
        raise RuntimeError(
            "Run this target through PRAgent-workflow/scripts/run_target.py so the live formula gate is enforced."
        )


def scale_spec(scale: str) -> ScaleSpec:
    if scale == "smoke":
        return ScaleSpec(
            scale=scale,
            sizes=SMOKE_SIZES,
            base_probabilities=SMOKE_BASE_PROBABILITIES,
            transition_realizations=2,
            refinement_points=2,
            critical_realizations=4,
            bootstrap_samples=5,
        )
    if scale == "feature":
        return ScaleSpec(
            scale=scale,
            sizes=FEATURE_SIZES,
            base_probabilities=FEATURE_BASE_PROBABILITIES,
            transition_realizations=8,
            refinement_points=4,
            critical_realizations=16,
            bootstrap_samples=100,
        )
    raise ValueError(f"unsupported scale: {scale}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=("smoke", "feature"), default="smoke")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--bootstrap-samples", type=int)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def transition_settings(
    spec: ScaleSpec,
    probabilities_by_m: dict[int, tuple[float, ...]],
    *,
    stage: str,
) -> tuple[ObservableSetting, ...]:
    settings: list[ObservableSetting] = []
    dynamics_scale = "feature" if spec.scale == "feature" else "smoke"
    for m in PAPER_BLOCK_SIZES:
        depth = RELATIVE_DEPTH * m
        probabilities = probabilities_by_m[m]
        for blocks in spec.sizes:
            steps = equilibration_steps(blocks, depth, dynamics_scale)
            for probability in probabilities:
                settings.append(
                    ObservableSetting(
                        campaign=f"s6_{stage}",
                        label=f"m{m}",
                        blocks=blocks,
                        qubits_per_block=m,
                        depth=depth,
                        measurement_fraction=probability,
                        steps=steps,
                        boundary="periodic",
                        sample_steps=odd_steps_ending_at(steps),
                        include_tripartite_information=True,
                    )
                )
    return tuple(settings)


def output_lookup(
    outputs: tuple[ObservableOutput, ...],
) -> dict[tuple[int, int, float], ObservableOutput]:
    lookup: dict[tuple[int, int, float], ObservableOutput] = {}
    for output in outputs:
        key = (
            output.setting.qubits_per_block,
            output.setting.blocks,
            round(output.setting.measurement_fraction, 14),
        )
        if key in lookup:
            raise ValueError(f"duplicate generated coordinate: {key}")
        lookup[key] = output
    return lookup


def i3_curves(
    outputs: tuple[ObservableOutput, ...],
    *,
    m: int,
    sizes: tuple[int, ...],
) -> tuple[ScalingCurve, ...]:
    lookup = output_lookup(outputs)
    probabilities = tuple(
        sorted(
            {
                output.setting.measurement_fraction
                for output in outputs
                if output.setting.qubits_per_block == m
            }
        )
    )
    curves: list[ScalingCurve] = []
    for blocks in sizes:
        means: list[float] = []
        errors: list[float] = []
        for probability in probabilities:
            output = lookup[(m, blocks, round(probability, 14))]
            if output.tripartite_mutual_information is None:
                raise AssertionError(f"{output.setting.key} is missing I3")
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
    return tuple(curves)


def preliminary_probabilities(
    base_outputs: tuple[ObservableOutput, ...],
    spec: ScaleSpec,
) -> dict[int, float]:
    fitted: dict[int, float] = {}
    for m in PAPER_BLOCK_SIZES:
        curves = i3_curves(base_outputs, m=m, sizes=spec.sizes)
        fit = fit_data_collapse(
            curves,
            critical_probability_bounds=(
                spec.base_probabilities[0],
                spec.base_probabilities[-1],
            ),
            critical_exponent_bounds=(0.7, 1.8),
            grid_points=13,
            refinement_rounds=2,
        )
        fitted[m] = fit.critical_probability
    return fitted


def select_refinement_probabilities(
    base_probabilities: tuple[float, ...],
    preliminary_probability: float,
    *,
    count: int,
) -> tuple[float, ...]:
    values = np.asarray(base_probabilities, dtype=float)
    if len(values) < 3 or np.any(np.diff(values) <= 0):
        raise ValueError("base probabilities must be strictly increasing")
    midpoints = (values[:-1] + values[1:]) / 2.0
    selected = np.argsort(np.abs(midpoints - preliminary_probability))[:count]
    return tuple(float(value) for value in np.sort(midpoints[selected]))


def final_transition_fit(
    curves: tuple[ScalingCurve, ...],
    *,
    m_index: int,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, float | bool]:
    probabilities = curves[0].measurement_fraction
    fit_kwargs = {
        "critical_probability_bounds": (
            float(probabilities[0]),
            float(probabilities[-1]),
        ),
        "critical_exponent_bounds": (0.7, 1.8),
        "grid_points": 17,
        "refinement_rounds": 2,
    }
    fit = fit_data_collapse(curves, **fit_kwargs)
    omitted = leave_one_size_out_fits(curves, **fit_kwargs)
    bootstrap = bootstrap_measurement_fractions(
        curves,
        samples=bootstrap_samples,
        sample_fraction=0.8,
        seed=setting_seed(seed, 9, m_index),
        **fit_kwargs,
    )
    omitted_pc = np.asarray([item.critical_probability for item in omitted.values()])
    local_spacing = float(np.min(np.diff(probabilities)))
    probability_error = max(
        float(np.std(omitted_pc, ddof=1)),
        float(np.std(bootstrap.critical_probabilities, ddof=1)),
        local_spacing / 2,
    )
    exponent_error = max(float(np.std(bootstrap.critical_exponents, ddof=1)), 0.01)
    unscaled_cost, _ = collapse_cost(
        curves,
        critical_probability=fit.critical_probability,
        critical_exponent=100.0,
    )
    return {
        "critical_probability": fit.critical_probability,
        "critical_probability_error": probability_error,
        "critical_exponent": fit.critical_exponent,
        "critical_exponent_error": exponent_error,
        "collapse_cost": fit.cost,
        "unscaled_cost": unscaled_cost,
        "probability_at_boundary": fit.critical_probability_at_boundary,
        "exponent_at_boundary": fit.critical_exponent_at_boundary,
        "leave_one_size_out_probability_span": float(np.ptp(omitted_pc)),
    }


def critical_settings(
    spec: ScaleSpec,
    fitted_probabilities: dict[int, float],
) -> tuple[ObservableSetting, ...]:
    return transition_settings(
        spec,
        {m: (fitted_probabilities[m],) for m in PAPER_BLOCK_SIZES},
        stage="critical_entropy",
    )


def fit_alpha(
    outputs: tuple[ObservableOutput, ...],
    *,
    m: int,
    sizes: tuple[int, ...],
) -> dict[str, float]:
    selected = {
        output.setting.blocks: output
        for output in outputs
        if output.setting.qubits_per_block == m
    }
    if set(selected) != set(sizes):
        raise ValueError(f"critical entropy outputs for m={m} are incomplete")
    entropies: list[float] = []
    errors: list[float] = []
    for size in sizes:
        mean, _, standard_error = observable_mean_and_error(
            selected[size].half_chain_entropy
        )
        entropies.append(mean)
        errors.append(max(standard_error, 1e-3))
    fit = fit_log_entropy(sizes, entropies, errors)
    return {
        "alpha": fit.alpha,
        "alpha_error": fit.alpha_standard_error,
        "alpha_intercept": fit.intercept,
        "alpha_r_squared": fit.r_squared,
    }


def write_numerical_data(
    path: Path,
    staged_outputs: tuple[tuple[str, ObservableOutput], ...],
) -> None:
    fields = [
        "stage", "m", "d", "L", "p", "time", "observable", "mean",
        "standard_deviation", "standard_error", "realizations",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for stage, output in staged_outputs:
            observables = (
                ("half_chain_entropy", output.half_chain_entropy),
                ("tripartite_mutual_information", output.tripartite_mutual_information),
            )
            for observable, values in observables:
                if values is None:
                    raise AssertionError(f"{output.setting.key} is missing {observable}")
                mean, standard_deviation, standard_error = observable_mean_and_error(values)
                writer.writerow(
                    {
                        "stage": stage,
                        "m": output.setting.qubits_per_block,
                        "d": output.setting.depth,
                        "L": output.setting.blocks,
                        "p": output.setting.measurement_fraction,
                        "time": output.setting.sample_steps[-1],
                        "observable": observable,
                        "mean": mean,
                        "standard_deviation": standard_deviation,
                        "standard_error": standard_error,
                        "realizations": output.realizations,
                    }
                )


def write_fit_data(path: Path, fits: tuple[BlockFit, ...]) -> None:
    fields = list(asdict(fits[0]))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for fit in fits:
            writer.writerow(asdict(fit))


def render(path: Path, fits: tuple[BlockFit, ...]) -> None:
    plt.rcParams.update({"font.size": 12, "axes.linewidth": 0.8})
    figure, axes = plt.subplots(1, 3, figsize=(12, 3), constrained_layout=True)
    block_sizes = np.asarray([fit.m for fit in fits])
    probabilities = np.asarray([fit.critical_probability for fit in fits])
    probability_errors = np.asarray([fit.critical_probability_error for fit in fits])
    exponents = np.asarray([fit.critical_exponent for fit in fits])
    exponent_errors = np.asarray([fit.critical_exponent_error for fit in fits])
    alphas = np.asarray([fit.alpha for fit in fits])
    alpha_errors = np.asarray([fit.alpha_error for fit in fits])

    axes[0].errorbar(
        block_sizes, probabilities, yerr=probability_errors,
        fmt="D", color="#0879bd", ecolor="#0879bd", markersize=4, capsize=2,
        linestyle="none",
    )
    axes[1].errorbar(
        block_sizes, exponents, yerr=exponent_errors,
        fmt=">", fillstyle="none", color="#e64a19", ecolor="#e64a19",
        markersize=5, capsize=3, linestyle="none",
    )
    axes[2].errorbar(
        block_sizes, alphas, yerr=alpha_errors,
        fmt="s", fillstyle="none", color="#e6a100", ecolor="#e6a100",
        markersize=4, capsize=3, linestyle="none",
    )
    labels = (r"$p_c$", r"$\nu$", r"$\alpha$")
    panel_labels = ("(a)", "(b)", "(c)")
    for axis, y_label, panel_label in zip(axes, labels, panel_labels):
        axis.set_xlim(0, 14)
        axis.set_xticks((0, 5, 10))
        axis.set_xlabel(r"$m$")
        axis.set_ylabel(y_label)
        axis.tick_params(direction="in", top=True, right=True)
        axis.text(-0.23, 1.02, panel_label, transform=axis.transAxes, fontsize=14)
    axes[0].set_ylim(0.45, 1.0)
    axes[1].set_ylim(0.0, 2.0)
    axes[2].set_ylim(0.0, 2.0)
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def constant_compatibility(
    values: np.ndarray,
    standard_errors: np.ndarray,
) -> dict[str, float]:
    """Measure whether noisy estimates are statistically compatible with one constant."""

    values = np.asarray(values, dtype=float)
    standard_errors = np.asarray(standard_errors, dtype=float)
    if (
        values.ndim != 1
        or len(values) < 3
        or values.shape != standard_errors.shape
        or np.any(standard_errors <= 0)
    ):
        raise ValueError("constant compatibility needs aligned positive uncertainties")
    weights = 1.0 / standard_errors**2
    weighted_mean = float(np.sum(weights * values) / np.sum(weights))
    chi_square = float(np.sum(((values - weighted_mean) / standard_errors) ** 2))
    reduced_chi_square = chi_square / (len(values) - 1)
    maximum_pairwise_sigma = max(
        abs(float(values[left] - values[right]))
        / float(np.hypot(standard_errors[left], standard_errors[right]))
        for left in range(len(values))
        for right in range(left)
    )
    return {
        "weighted_mean": weighted_mean,
        "reduced_chi_square": reduced_chi_square,
        "maximum_pairwise_sigma": maximum_pairwise_sigma,
    }


def build_checks(
    spec: ScaleSpec,
    fits: tuple[BlockFit, ...],
    base_outputs: tuple[ObservableOutput, ...],
    refinement_outputs: tuple[ObservableOutput, ...],
    critical_outputs: tuple[ObservableOutput, ...],
) -> dict[str, object]:
    probabilities = np.asarray([fit.critical_probability for fit in fits])
    exponents = np.asarray([fit.critical_exponent for fit in fits])
    alphas = np.asarray([fit.alpha for fit in fits])
    alpha_errors = np.asarray([fit.alpha_error for fit in fits])
    alpha_r_squared = np.asarray([fit.alpha_r_squared for fit in fits])
    alpha_compatibility = constant_compatibility(alphas, alpha_errors)
    alpha_m_correlation = float(np.corrcoef(PAPER_BLOCK_SIZES, alphas)[0, 1])
    pc_differences = np.diff(probabilities)
    pc_monotonic_fraction = float(np.mean(pc_differences >= -0.03))
    pc_m_correlation = float(np.corrcoef(PAPER_BLOCK_SIZES, probabilities)[0, 1])
    core_checks = {
        "all_three_theory_numerical_panels_generated": True,
        "all_six_paper_block_sizes_present": tuple(fit.m for fit in fits) == PAPER_BLOCK_SIZES,
        "relative_depth_is_exactly_three": all(fit.d == RELATIVE_DEPTH * fit.m for fit in fits),
        "all_transition_settings_completed": len(base_outputs) == (
            len(PAPER_BLOCK_SIZES) * len(spec.sizes) * len(spec.base_probabilities)
        ),
        "all_adaptive_refinement_settings_completed": len(refinement_outputs) == (
            len(PAPER_BLOCK_SIZES) * len(spec.sizes) * spec.refinement_points
        ),
        "all_critical_entropy_settings_completed": len(critical_outputs) == (
            len(PAPER_BLOCK_SIZES) * len(spec.sizes)
        ),
        "all_fits_are_interior": all(
            not fit.probability_at_boundary and not fit.exponent_at_boundary
            for fit in fits
        ),
        "I3_collapse_improves_over_no_size_scaling": all(
            fit.collapse_cost < fit.unscaled_cost for fit in fits
        ),
        "critical_probability_grows_with_block_size": bool(
            pc_monotonic_fraction >= 0.8
            and pc_m_correlation > 0.85
            and probabilities[-1] - probabilities[0] > 0.2
            and probabilities[-1] > 0.8
        ),
        "critical_entropy_grows_with_log_size": float(np.mean(alpha_r_squared > 0.5)) >= 2 / 3,
        "source_pixels_absent": True,
        "published_plot_values_absent_from_generation": True,
    }
    universality_checks = {
        "mean_I3_exponent_is_near_1p25": abs(float(np.mean(exponents)) - 1.25) < 0.35,
        "I3_exponent_has_no_large_block_size_dependence": float(np.ptp(exponents)) < 0.7,
        "log_entropy_coefficient_is_positive": bool(np.all(alphas > 0)),
        "log_entropy_coefficient_is_constant_within_uncertainty": (
            alpha_compatibility["reduced_chi_square"] < 2.5
            and alpha_compatibility["maximum_pairwise_sigma"] < 3.0
            and abs(alpha_m_correlation) < 0.6
        ),
    }
    core_pass = all(core_checks.values())
    universality_pass = all(universality_checks.values())
    return {
        "schema_version": 1,
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "status": (
            "passed"
            if core_pass and universality_pass
            else "passed_with_warnings"
            if core_pass
            else "failed"
        ),
        "scientific_feature_status": (
            "passed"
            if core_pass and universality_pass
            else "partial"
            if core_pass
            else "failed"
        ),
        "completion_status": (
            "feature_reproduced"
            if core_pass and universality_pass
            else "partial_reproduction"
        ),
        "generated_data_provenance": "independent_adaptive_Clifford_stabilizer_simulation",
        "source_pixels_used_in_generation": False,
        "published_values_used_for_generation": False,
        "adaptive_sampling_inputs": "generated_I3_values_and_base_grid_coordinates_only",
        "parameter_match": "paper_subset",
        "core_checks": core_checks,
        "universality_checks": universality_checks,
        "metrics": {
            "block_sizes": list(PAPER_BLOCK_SIZES),
            "relative_depth": RELATIVE_DEPTH,
            "sizes": list(spec.sizes),
            "base_probability_points": len(spec.base_probabilities),
            "adaptive_probability_points": spec.refinement_points,
            "transition_realizations_per_cell": spec.transition_realizations,
            "critical_entropy_realizations_per_cell": spec.critical_realizations,
            "independent_trajectories": (
                len(base_outputs) * spec.transition_realizations
                + len(refinement_outputs) * spec.transition_realizations
                + len(critical_outputs) * spec.critical_realizations
            ),
            "pc_monotonic_fraction": pc_monotonic_fraction,
            "pc_m_correlation": pc_m_correlation,
            "pc_growth": float(probabilities[-1] - probabilities[0]),
            "mean_nu": float(np.mean(exponents)),
            "nu_span": float(np.ptp(exponents)),
            "mean_alpha": float(np.mean(alphas)),
            "alpha_span": float(np.ptp(alphas)),
            "alpha_weighted_constant": alpha_compatibility["weighted_mean"],
            "alpha_constant_reduced_chi_square": alpha_compatibility["reduced_chi_square"],
            "alpha_maximum_pairwise_sigma": alpha_compatibility["maximum_pairwise_sigma"],
            "alpha_m_correlation": alpha_m_correlation,
            "alpha_r_squared_pass_fraction": float(np.mean(alpha_r_squared > 0.5)),
            "fits": {str(fit.m): asdict(fit) for fit in fits},
        },
    }


def main() -> int:
    require_guard()
    args = parse_args()
    spec = scale_spec(args.scale)
    bootstrap_samples = args.bootstrap_samples or spec.bootstrap_samples
    workers = args.workers if args.workers is not None else min(8, os.cpu_count() or 1)
    if workers <= 0 or bootstrap_samples < 2:
        raise ValueError("workers must be positive and bootstrap samples must be at least two")
    started = perf_counter()

    base_probability_map = {m: spec.base_probabilities for m in PAPER_BLOCK_SIZES}
    base_settings = transition_settings(spec, base_probability_map, stage="base")
    with observable_worker_pool(workers) as executor:
        base_outputs = run_observable_settings(
            base_settings,
            campaign_code=6,
            scale=f"{MODEL_REVISION}-{spec.scale}-base",
            realizations=spec.transition_realizations,
            root_seed=args.seed,
            workers=workers,
            resume=not args.no_resume,
            executor=executor,
        )
        preliminary = preliminary_probabilities(base_outputs, spec)
        refinement_probability_map = {
            m: select_refinement_probabilities(
                spec.base_probabilities,
                preliminary[m],
                count=spec.refinement_points,
            )
            for m in PAPER_BLOCK_SIZES
        }
        refinement_settings = transition_settings(
            spec,
            refinement_probability_map,
            stage="refinement",
        )
        refinement_outputs = run_observable_settings(
            refinement_settings,
            campaign_code=7,
            scale=f"{MODEL_REVISION}-{spec.scale}-refinement",
            realizations=spec.transition_realizations,
            root_seed=args.seed,
            workers=workers,
            resume=not args.no_resume,
            executor=executor,
        )

        transition_outputs = (*base_outputs, *refinement_outputs)
        transition_fit_payloads: dict[int, dict[str, float | bool]] = {}
        for m_index, m in enumerate(PAPER_BLOCK_SIZES):
            curves = i3_curves(transition_outputs, m=m, sizes=spec.sizes)
            transition_fit_payloads[m] = final_transition_fit(
                curves,
                m_index=m_index,
                bootstrap_samples=bootstrap_samples,
                seed=args.seed,
            )
        fitted_probabilities = {
            m: float(transition_fit_payloads[m]["critical_probability"])
            for m in PAPER_BLOCK_SIZES
        }
        entropy_settings = critical_settings(spec, fitted_probabilities)
        critical_outputs = run_observable_settings(
            entropy_settings,
            campaign_code=8,
            scale=f"{MODEL_REVISION}-{spec.scale}-critical",
            realizations=spec.critical_realizations,
            root_seed=args.seed,
            workers=workers,
            resume=not args.no_resume,
            executor=executor,
        )

    fits: list[BlockFit] = []
    for m in PAPER_BLOCK_SIZES:
        payload = transition_fit_payloads[m]
        alpha_payload = fit_alpha(critical_outputs, m=m, sizes=spec.sizes)
        fits.append(
            BlockFit(
                m=m,
                d=RELATIVE_DEPTH * m,
                **payload,
                **alpha_payload,
            )
        )
    fit_records = tuple(fits)

    data_dir = WORKSPACE / "outputs" / "data"
    figure_dir = WORKSPACE / "outputs" / "figures"
    check_dir = WORKSPACE / "outputs" / "checks"
    for directory in (data_dir, figure_dir, check_dir):
        directory.mkdir(parents=True, exist_ok=True)
    staged_outputs = tuple(
        [("base", output) for output in base_outputs]
        + [("adaptive_refinement", output) for output in refinement_outputs]
        + [("critical_entropy", output) for output in critical_outputs]
    )
    write_numerical_data(data_dir / "supp_fig_s6_numerical_data.csv", staged_outputs)
    write_fit_data(data_dir / "supp_fig_s6_block_size_fits.csv", fit_records)
    render(figure_dir / "supp_fig_s6_reproduction.png", fit_records)
    checks = build_checks(
        spec,
        fit_records,
        base_outputs,
        refinement_outputs,
        critical_outputs,
    )
    checks["runtime_seconds"] = perf_counter() - started
    checks["trajectory_runtime_seconds"] = float(
        sum(
            output.runtime_seconds
            for output in (*base_outputs, *refinement_outputs, *critical_outputs)
        )
    )
    (check_dir / "t006_scientific_checks.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    metadata = {
        "paper_id": "1903.05124",
        "target_id": TARGET_ID,
        "model_revision": MODEL_REVISION,
        "generated_data_provenance": checks["generated_data_provenance"],
        "source_pixels_used_in_generation": False,
        "published_values_used_for_generation": False,
        "sampling_rule": "fixed full-range base grid plus midpoints nearest preliminary generated-I3 collapse",
        "critical_entropy_sampling_rule": "new trajectories at independently fitted p_c(m)",
        "formula_refs": ["EQC005", "EQC008", "EQC010"],
        "method_refs": ["MTH001", "MTH003"],
        "scale": spec.scale,
        "seed": args.seed,
        "workers": workers,
        "bootstrap_samples": bootstrap_samples,
        "runtime_seconds": checks["runtime_seconds"],
    }
    (data_dir / "supp_fig_s6_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(checks, indent=2), flush=True)
    return 0 if checks["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
