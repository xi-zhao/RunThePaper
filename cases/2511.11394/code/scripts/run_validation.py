#!/usr/bin/env python3
"""Run the static and dynamical go/no-go validation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.chern_jump_geometry import (  # noqa: E402
    TWO_PI,
    constant_texture,
    geometry_observables,
    integrate_llg,
    jump_metric_estimator,
    qwz_texture,
)


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def static_validation(mode: str) -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int | str]], dict]:
    sizes = [31, 51] if mode == "smoke" else [41, 81, 121]
    models = [("paper_topological", -0.5), ("trivial_control", -3.0)]
    static_rows: list[dict[str, float | int | str]] = []
    for model, mass in models:
        for size in sizes:
            geometry = geometry_observables(qwz_texture(size, mass))
            bound = TWO_PI * abs(geometry.chern)
            static_rows.append(
                {
                    "model": model,
                    "mass": mass,
                    "grid_size": size,
                    "chern": geometry.chern,
                    "metric_integral": geometry.metric_integral,
                    "dirichlet_energy": geometry.dirichlet_energy,
                    "topological_bound": bound,
                    "bound_ratio": geometry.metric_integral / bound if bound > 1e-12 else np.nan,
                    "absolute_curvature_integral": geometry.absolute_curvature_integral,
                    "finite_difference_chern": geometry.finite_difference_chern,
                    "opposite_curvature_fraction": geometry.opposite_curvature_fraction,
                    "max_norm_error": geometry.max_norm_error,
                }
            )

    size = sizes[-1]
    q_values = (
        np.array([0.36, 0.26, 0.18, 0.12])
        if mode == "smoke"
        else np.array([0.40, 0.32, 0.25, 0.19, 0.14, 0.10, 0.07])
    )
    convergence_rows: list[dict[str, float | int | str]] = []
    fit_results: dict[str, dict[str, float]] = {}
    for model, mass in models:
        texture = qwz_texture(size, mass)
        exact = geometry_observables(texture).metric_integral
        estimates = np.asarray([jump_metric_estimator(texture, q) for q in q_values])
        slope, intercept = np.polyfit(q_values * q_values, estimates, deg=1)
        fit_results[model] = {
            "slope": float(slope),
            "intercept": float(intercept),
            "exact_metric_integral": float(exact),
            "intercept_relative_error": float(abs(intercept - exact) / max(abs(exact), 1e-15)),
        }
        for q, estimate in zip(q_values, estimates, strict=True):
            convergence_rows.append(
                {
                    "model": model,
                    "mass": mass,
                    "grid_size": size,
                    "q": float(q),
                    "q_squared": float(q * q),
                    "jump_metric_estimator": float(estimate),
                    "metric_integral": float(exact),
                    "relative_error": float((estimate - exact) / exact),
                }
            )

    dark = constant_texture(size)
    dark_estimator = jump_metric_estimator(dark, float(q_values[-1]))
    top_final = next(
        row
        for row in static_rows
        if row["model"] == "paper_topological" and row["grid_size"] == size
    )
    trivial_final = next(
        row
        for row in static_rows
        if row["model"] == "trivial_control" and row["grid_size"] == size
    )
    checks = {
        "paper_chern_is_one": abs(float(top_final["chern"]) - 1.0) < 1e-10,
        "trivial_chern_is_zero": abs(float(trivial_final["chern"])) < 1e-10,
        "topological_bound_holds": float(top_final["bound_ratio"]) >= 1.0 - 2e-3,
        "constant_texture_is_dark": abs(dark_estimator) < 1e-12,
        "topological_q_extrapolation": fit_results["paper_topological"]["intercept_relative_error"] < 5e-3,
        "trivial_q_extrapolation": fit_results["trivial_control"]["intercept_relative_error"] < 5e-3,
    }
    result = {
        "status": "passed" if all(checks.values()) else "failed",
        "mode": mode,
        "checks": checks,
        "fit_results": fit_results,
        "constant_texture_estimator": dark_estimator,
        "interpretation": {
            "geometric_claim": "supported" if all(checks.values()) else "not_supported",
            "raw_total_jump_claim": "not_tested_detector_model_required",
        },
    }
    return static_rows, convergence_rows, result


def dynamic_validation(mode: str) -> tuple[list[dict[str, float]], dict]:
    if mode == "smoke":
        size, time_max, time_step, sample_interval = 31, 1.0, 0.02, 0.1
    else:
        size, time_max, time_step, sample_interval = 61, 15.0, 0.01, 0.1
    q_probe = 0.15
    rows, final_texture = integrate_llg(
        size=size,
        mass=-0.5,
        gamma=1.5,
        lambda_d=1.25,
        lambda_t=0.025,
        time_max=time_max,
        time_step=time_step,
        sample_interval=sample_interval,
        q_probe=q_probe,
    )
    convergence_diagnostics: dict[str, float] = {}
    convergence_checks: dict[str, bool] = {}
    if mode == "feature":
        coarse_step_rows, _ = integrate_llg(
            size=41,
            mass=-0.5,
            gamma=1.5,
            lambda_d=1.25,
            lambda_t=0.025,
            time_max=3.0,
            time_step=0.02,
            sample_interval=3.0,
            q_probe=q_probe,
        )
        fine_step_rows, _ = integrate_llg(
            size=41,
            mass=-0.5,
            gamma=1.5,
            lambda_d=1.25,
            lambda_t=0.025,
            time_max=3.0,
            time_step=0.01,
            sample_interval=3.0,
            q_probe=q_probe,
        )
        coarse_grid_rows, _ = integrate_llg(
            size=41,
            mass=-0.5,
            gamma=1.5,
            lambda_d=1.25,
            lambda_t=0.025,
            time_max=15.0,
            time_step=0.01,
            sample_interval=15.0,
            q_probe=q_probe,
        )
        step_relative_difference = abs(
            coarse_step_rows[-1]["dirichlet_energy"]
            - fine_step_rows[-1]["dirichlet_energy"]
        ) / fine_step_rows[-1]["dirichlet_energy"]
        grid_relative_difference = abs(
            coarse_grid_rows[-1]["dirichlet_energy"]
            - rows[-1]["dirichlet_energy"]
        ) / rows[-1]["dirichlet_energy"]
        convergence_diagnostics = {
            "step_halving_relative_difference_at_t3": step_relative_difference,
            "grid_41_vs_61_relative_difference_at_t15": grid_relative_difference,
        }
        convergence_checks = {
            "time_step_converged": step_relative_difference < 1e-6,
            "grid_converged": grid_relative_difference < 2e-3,
        }
    energies = np.asarray([row["total_energy"] for row in rows])
    energy_steps = np.diff(energies)
    cherns = np.asarray([row["chern"] for row in rows])
    metrics = np.asarray([row["metric_integral"] for row in rows])
    jump_metrics = np.asarray([row["jump_metric_estimator"] for row in rows])
    correlation = float(np.corrcoef(metrics, jump_metrics)[0, 1])
    relative_tracking_error = float(
        np.max(np.abs(jump_metrics - metrics) / np.maximum(metrics, 1e-15))
    )
    checks = {
        "total_energy_nonincreasing": float(np.max(energy_steps, initial=0.0)) < 2e-8,
        "chern_sector_preserved": float(np.max(np.abs(cherns - 1.0))) < 1e-8,
        "unit_norm_preserved": max(row["max_norm_error"] for row in rows) < 1e-12,
        "dirichlet_energy_decreases": rows[-1]["dirichlet_energy"] < rows[0]["dirichlet_energy"],
        "jump_estimator_tracks_metric": correlation > 0.999 and relative_tracking_error < 0.02,
        **convergence_checks,
    }
    result = {
        "status": "passed" if all(checks.values()) else "failed",
        "mode": mode,
        "parameters": {
            "grid_size": size,
            "time_max": time_max,
            "time_step": time_step,
            "sample_interval": sample_interval,
            "q_probe": q_probe,
            "mass": -0.5,
            "gamma": 1.5,
            "lambda_d": 1.25,
            "lambda_t": 0.025,
        },
        "checks": checks,
        "diagnostics": {
            "largest_positive_energy_step": float(np.max(energy_steps, initial=0.0)),
            "metric_jump_correlation": correlation,
            "maximum_relative_tracking_error": relative_tracking_error,
            "initial_dirichlet_energy": rows[0]["dirichlet_energy"],
            "final_dirichlet_energy": rows[-1]["dirichlet_energy"],
            "initial_bound_ratio": rows[0]["metric_integral"] / TWO_PI,
            "final_bound_ratio": rows[-1]["metric_integral"] / TWO_PI,
            "final_chern": geometry_observables(final_texture).chern,
            **convergence_diagnostics,
        },
    }
    return rows, result


def plot_static(convergence_rows: list[dict[str, float | int | str]], output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0), constrained_layout=True)
    colors = {"paper_topological": "#0072B2", "trivial_control": "#D55E00"}
    labels = {"paper_topological": "Chern band (M=-0.5)", "trivial_control": "Trivial band (M=-3)"}
    for model in colors:
        selected = [row for row in convergence_rows if row["model"] == model]
        x = np.asarray([float(row["q_squared"]) for row in selected])
        y = np.asarray([float(row["jump_metric_estimator"]) for row in selected])
        exact = float(selected[0]["metric_integral"])
        order = np.argsort(x)
        axes[0].plot(x[order], y[order], "o-", color=colors[model], label=labels[model])
        axes[0].axhline(exact, color=colors[model], linestyle="--", alpha=0.65)
        axes[1].plot(
            x[order],
            np.abs(y[order] - exact) / exact,
            "o-",
            color=colors[model],
            label=labels[model],
        )
    axes[0].axhline(TWO_PI, color="black", linestyle=":", label=r"$2\pi|C|$ (Chern)")
    axes[0].set(xlabel=r"$q^2$", ylabel=r"$K_{\rm jump}(q)$", title="Finite-q geometric jump moment")
    axes[1].set(
        xlabel=r"$q^2$",
        ylabel=r"$|K_{\rm jump}-K|/K$",
        title="Convergence to integrated quantum metric",
        yscale="log",
    )
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].legend(frameon=False, fontsize=8)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def plot_dynamic(rows: list[dict[str, float]], output: Path) -> None:
    time_values = np.asarray([row["time"] for row in rows])
    dirichlet = np.asarray([row["dirichlet_energy"] for row in rows])
    jump = np.asarray([row["jump_metric_estimator"] for row in rows])
    chern = np.asarray([row["chern"] for row in rows])
    opposite = np.asarray([row["opposite_curvature_fraction"] for row in rows])
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0), constrained_layout=True)
    axes[0].plot(time_values, dirichlet / np.pi, color="#0072B2", label=r"$E_D/\pi$")
    axes[0].plot(time_values, jump / TWO_PI, "--", color="#E69F00", label=r"$K_{\rm jump}/2\pi$")
    axes[0].axhline(1.0, color="black", linestyle=":", label="topological bound")
    axes[0].set(ylabel="normalized geometry", title="Dissipative approach to the bound")
    axes[0].legend(frameon=False)
    axes[1].plot(time_values, chern, color="#009E73", label="Chern number")
    axes[1].plot(time_values, opposite, color="#CC79A7", label="opposite-curvature area")
    axes[1].set(ylabel="topology / fraction", title="Topology and curvature sign")
    axes[1].legend(frameon=False)
    fig.supxlabel("time")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "feature"), default="feature")
    args = parser.parse_args()
    data_dir = WORKSPACE / "outputs" / "data"
    checks_dir = WORKSPACE / "outputs" / "checks"
    figures_dir = WORKSPACE / "outputs" / "figures"
    checks_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    static_rows, convergence_rows, static_result = static_validation(args.mode)
    dynamic_rows, dynamic_result = dynamic_validation(args.mode)
    runtime = time.perf_counter() - started
    write_csv(data_dir / "static_geometry.csv", static_rows)
    write_csv(data_dir / "finite_q_convergence.csv", convergence_rows)
    write_csv(data_dir / "llg_trajectory.csv", dynamic_rows)
    plot_static(convergence_rows, figures_dir / "jump_sum_rule.png")
    plot_dynamic(dynamic_rows, figures_dir / "llg_geometry_flow.png")

    static_result["runtime_seconds"] = runtime
    dynamic_result["runtime_seconds"] = runtime
    (checks_dir / "jump_sum_rule_validation.json").write_text(
        json.dumps(static_result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (checks_dir / "llg_validation.json").write_text(
        json.dumps(dynamic_result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    combined = {
        "status": "passed"
        if static_result["status"] == dynamic_result["status"] == "passed"
        else "failed",
        "mode": args.mode,
        "runtime_seconds": runtime,
        "static": static_result,
        "dynamic": dynamic_result,
    }
    (checks_dir / "validation_summary.json").write_text(
        json.dumps(combined, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(combined, indent=2, ensure_ascii=False))
    return 0 if combined["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
