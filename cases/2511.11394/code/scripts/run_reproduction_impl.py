#!/usr/bin/env python3
"""Guarded, target-scoped reproduction of the three main paper figures."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.chern_jump_geometry import (  # noqa: E402
    extended_hubbard_lambda_d,
    geometry_observables,
    integrate_exact_extended_hubbard,
    integrate_extended_hubbard_comparison,
    integrate_llg,
    local_geometry,
    qwz_texture,
)


GUARDED_TARGET_ENV = "PRAGENT_GUARDED_TARGET_ID"
GUARDED_STAGE_ENV = "PRAGENT_GUARDED_STAGE"
DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"
TARGETS = ("T001", "T002", "T003", "T004")
plt: Any | None = None


def configure_rendering(enabled: bool) -> None:
    """Load plotting code only for the separate render path."""

    global plt
    if not enabled:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as pyplot

    plt = pyplot
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty dataset")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def geometry_fields(texture: np.ndarray) -> dict[str, np.ndarray]:
    """Return the paper's half-trace, half-curvature, and trace deviation."""

    fields = local_geometry(texture)
    half_trace = 0.5 * fields["metric_trace"]
    half_curvature = 0.5 * fields["curvature"]
    return {
        "half_trace": half_trace,
        "half_curvature": half_curvature,
        "trace_deviation": half_trace - np.abs(half_curvature),
    }


def zero_to_two_pi_field(field: np.ndarray) -> np.ndarray:
    """Reorder a [-pi, pi) field into the paper's [0, 2pi) display order."""

    return np.fft.ifftshift(field, axes=(0, 1))


def render_field_grid(
    fields_by_column: list[tuple[str, dict[str, np.ndarray]]],
    output_path: Path,
    title: str,
) -> None:
    """Render trace and curvature fields with shared row-wise color scales."""

    if plt is None:
        raise RuntimeError("rendering is disabled")

    figure, axes = plt.subplots(
        2,
        len(fields_by_column),
        figsize=(4.0 * len(fields_by_column), 7.0),
        constrained_layout=True,
        squeeze=False,
    )
    for column, (label, fields) in enumerate(fields_by_column):
        for row, (field_name, row_label) in enumerate(
            (("half_trace", r"$\mathrm{tr}\,g/2$"), ("half_curvature", r"$F_{12}/2$"))
        ):
            image = axes[row, column].imshow(
                zero_to_two_pi_field(fields[field_name]).T,
                origin="lower",
                extent=(0.0, 1.0, 0.0, 1.0),
                cmap="viridis" if row == 0 else "coolwarm",
                aspect="equal",
            )
            axes[row, column].set(
                xlabel=r"$k_x/2\pi$",
                ylabel=r"$k_y/2\pi$",
                title=f"{label}: {row_label}",
            )
            figure.colorbar(image, ax=axes[row, column], shrink=0.82)
    figure.suptitle(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def paper_flow_parameters(mode: str) -> dict[str, float | int]:
    if mode == "smoke":
        return {
            "grid_size": 31,
            "time_step": 0.02,
            "sample_interval": 0.1,
        }
    return {
        "grid_size": 81,
        "time_step": 0.01,
        "sample_interval": 0.05,
    }


def extended_flow_parameters(mode: str) -> dict[str, float | int]:
    if mode == "smoke":
        return {
            "grid_size": 31,
            "time_step": 0.02,
            "sample_interval": 0.1,
            "grid_offset_fraction": 0.5,
        }
    return {
        "grid_size": 141,
        "time_step": 0.01,
        "sample_interval": 0.04,
        "grid_offset_fraction": 0.5,
    }


def run_t001(mode: str) -> dict[str, object]:
    params = paper_flow_parameters(mode)
    time_max = 1.0 if mode == "smoke" else 15.0
    rows, final_texture = integrate_llg(
        size=int(params["grid_size"]),
        mass=-0.5,
        gamma=1.5,
        lambda_d=1.25,
        lambda_t=0.025,
        time_max=time_max,
        time_step=float(params["time_step"]),
        sample_interval=float(params["sample_interval"]),
        q_probe=0.15,
    )
    data_path = DATA_DIR / "fig1_small_q_energy.csv"
    figure_path = FIGURE_DIR / "fig1_small_q_energy.png"
    check_path = CHECK_DIR / "fig1_small_q_energy.json"
    supplemental_data_path = DATA_DIR / "sm_fig1_2_small_q_geometry.csv"
    supplemental_deviation_path = (
        FIGURE_DIR / "sm_fig1_trace_deviation_initial_final.png"
    )
    supplemental_profiles_path = (
        FIGURE_DIR / "sm_fig2_geometry_profiles_initial_final.png"
    )
    write_csv(data_path, rows)

    initial_texture = qwz_texture(int(params["grid_size"]), -0.5)
    initial_fields = geometry_fields(initial_texture)
    final_fields = geometry_fields(final_texture)
    grid_size = int(params["grid_size"])
    supplemental_rows: list[dict[str, object]] = []
    shifted_initial_fields = {
        key: zero_to_two_pi_field(value)
        for key, value in initial_fields.items()
    }
    shifted_final_fields = {
        key: zero_to_two_pi_field(value)
        for key, value in final_fields.items()
    }
    for i in range(grid_size):
        for j in range(grid_size):
            supplemental_rows.append(
                {
                    "kx_over_2pi_mod": float(i / grid_size),
                    "ky_over_2pi_mod": float(j / grid_size),
                    "initial_half_trace": float(
                        shifted_initial_fields["half_trace"][i, j]
                    ),
                    "initial_half_curvature": float(
                        shifted_initial_fields["half_curvature"][i, j]
                    ),
                    "initial_trace_deviation": float(
                        shifted_initial_fields["trace_deviation"][i, j]
                    ),
                    "final_half_trace": float(
                        shifted_final_fields["half_trace"][i, j]
                    ),
                    "final_half_curvature": float(
                        shifted_final_fields["half_curvature"][i, j]
                    ),
                    "final_trace_deviation": float(
                        shifted_final_fields["trace_deviation"][i, j]
                    ),
                }
            )
    write_csv(supplemental_data_path, supplemental_rows)

    if plt is not None:
        deviation_figure, deviation_axes = plt.subplots(
            1,
            2,
            figsize=(8.2, 3.7),
            constrained_layout=True,
        )
        deviation_limit = max(
            float(np.max(initial_fields["trace_deviation"])),
            float(np.max(final_fields["trace_deviation"])),
        )
        for axis, label, fields in zip(
            deviation_axes,
            ("initial", f"final, t={time_max:g}"),
            (initial_fields, final_fields),
            strict=True,
        ):
            image = axis.imshow(
                zero_to_two_pi_field(fields["trace_deviation"]).T,
                origin="lower",
                extent=(0.0, 1.0, 0.0, 1.0),
                cmap="viridis",
                vmin=0.0,
                vmax=deviation_limit,
                aspect="equal",
            )
            axis.set(
                xlabel=r"$k_x/2\pi$",
                ylabel=r"$k_y/2\pi$",
                title=label,
            )
        deviation_figure.colorbar(image, ax=deviation_axes, shrink=0.82)
        deviation_figure.suptitle("Supplemental Fig. 1 — trace-condition deviation")
        deviation_figure.savefig(supplemental_deviation_path, dpi=180)
        plt.close(deviation_figure)
        render_field_grid(
            [
                ("initial", initial_fields),
                (f"final, t={time_max:g}", final_fields),
            ],
            supplemental_profiles_path,
            "Supplemental Fig. 2 — small-q quantum geometry",
        )

    t = np.asarray([row["time"] for row in rows])
    e_d = np.asarray([row["dirichlet_energy"] for row in rows])
    e_t = np.asarray([row["hopping_component"] for row in rows])
    chern = np.asarray([row["chern"] for row in rows])
    if plt is not None:
        figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), constrained_layout=True)
        axes[0].plot(t, e_d, color="#2A7F3E", lw=2.4, label=r"$E_D$")
        axes[0].plot(t, e_t, color="#E67E22", lw=2.2, label=r"$\lambda_T E_T$")
        axes[0].axhline(np.pi, color="#6A51A3", ls="--", label=r"$\pi|C|$")
        axes[0].set(
            xlabel="time",
            ylabel="internally consistent energy",
            title="Small-q relaxation",
        )
        axes[0].legend(frameon=False)
        axes[1].plot(t, e_d / np.pi, color="#2A7F3E", label=r"$E_D/\pi$")
        axes[1].plot(t, chern, color="#1F77B4", label="solid-angle Chern")
        axes[1].axhline(1.0, color="black", ls=":")
        axes[1].set(
            xlabel="time",
            ylabel="normalized value",
            title="Geometry and topology",
        )
        axes[1].legend(frameon=False)
        figure.suptitle(
            "Feature-level reproduction; paper mesh and energy normalization are undisclosed"
        )
        figure.savefig(figure_path, dpi=200)
        plt.close(figure)
    increments = np.diff(e_d)
    checks = {
        "dirichlet_energy_nonincreasing": bool(
            np.max(increments, initial=0.0) < 2e-8
        ),
        "chern_sector_preserved": bool(np.max(np.abs(chern - 1.0)) < 1e-8),
        "unit_norm_preserved": bool(
            max(float(row["max_norm_error"]) for row in rows) < 1e-12
        ),
        "paper_axis_normalization_is_internally_inconsistent": True,
    }
    initial_deviation_mean = float(np.mean(initial_fields["trace_deviation"]))
    final_deviation_mean = float(np.mean(final_fields["trace_deviation"]))
    checks["trace_deviation_reduced"] = bool(
        final_deviation_mean < initial_deviation_mean
    )
    payload: dict[str, object] = {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "T001",
        "artifact_stage": "exploratory",
        "mode": mode,
        "parameters": {
            **params,
            "time_max": time_max,
            "mass": -0.5,
            "gamma": 1.5,
            "lambda_d": 1.25,
            "lambda_t": 0.025,
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "initial_dirichlet_energy": float(e_d[0]),
            "final_dirichlet_energy": float(e_d[-1]),
            "final_bound_ratio": float(e_d[-1] / np.pi),
            "source_label_claim": "lambda_D E_D with lower bound lambda_D*pi",
            "source_visible_lower_bound_approximately": float(4.0 * 1.25 * np.pi),
            "formula_implied_lower_bound": float(1.25 * np.pi),
            "normalization_ratio": 4.0,
            "initial_mean_trace_deviation": initial_deviation_mean,
            "final_mean_trace_deviation": final_deviation_mean,
            "paper_final_trace_deviation_scale": 0.005,
            "generated_final_max_trace_deviation": float(
                np.max(final_fields["trace_deviation"])
            ),
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "not_accessed_by_numerical_runner",
        "outputs": [
            str(data_path.relative_to(WORKSPACE)),
            str(supplemental_data_path.relative_to(WORKSPACE)),
            *(
                [
                    str(figure_path.relative_to(WORKSPACE)),
                    str(supplemental_deviation_path.relative_to(WORKSPACE)),
                    str(supplemental_profiles_path.relative_to(WORKSPACE)),
                ]
                if plt is not None
                else []
            ),
        ],
    }
    write_json(check_path, payload)
    return payload


def run_t002(mode: str) -> dict[str, object]:
    params = extended_flow_parameters(mode)
    time_max = 2.0 if mode == "smoke" else 10.0
    long_time = 8.0
    snapshot_times = (long_time,) if mode == "feature" else ()
    rows, snapshots = integrate_extended_hubbard_comparison(
        size=int(params["grid_size"]),
        mass=-0.5,
        gamma=1.5,
        onsite_u=8.0,
        nearest_v=0.75,
        lambda_t=0.025,
        cutoff_q=0.5 * np.pi,
        time_max=time_max,
        time_step=float(params["time_step"]),
        sample_interval=float(params["sample_interval"]),
        snapshot_times=snapshot_times,
        grid_offset_fraction=float(params["grid_offset_fraction"]),
    )
    data_path = DATA_DIR / "fig2_exact_vs_small_q.csv"
    figure_path = FIGURE_DIR / "fig2_exact_vs_small_q.png"
    check_path = CHECK_DIR / "fig2_exact_vs_small_q.json"
    long_time_data_path = DATA_DIR / "sm_fig5_long_time_geometry.csv"
    long_time_figure_path = FIGURE_DIR / "sm_fig5_long_time_geometry.png"
    write_csv(data_path, rows)

    t = np.asarray([row["time"] for row in rows])
    exact_e = np.asarray([row["exact_dirichlet_energy"] for row in rows])
    small_e = np.asarray([row["small_q_dirichlet_energy"] for row in rows])
    exact_chern_mesh = np.asarray(
        [row["exact_chern_mesh_integral"] for row in rows]
    )
    small_chern_mesh = np.asarray(
        [row["small_q_chern_mesh_integral"] for row in rows]
    )
    if plt is not None:
        figure, axes = plt.subplots(2, 1, figsize=(7.2, 7.0), constrained_layout=True)
        axes[0].plot(t, exact_e, color="#1F77B4", lw=2.5, label="exact")
        axes[0].plot(t, small_e, color="#FF7F0E", lw=2.5, ls="--", label="small-q")
        axes[0].axhline(np.pi, color="black", ls=":", label=r"$\pi$")
        if time_max >= 4.32:
            axes[0].axvline(4.32, color="0.45", ls=":")
        axes[0].set(xlabel="time", ylabel=r"$E_D(t)$")
        axes[0].legend(frameon=False)
        axes[1].plot(t, exact_chern_mesh, color="#1F77B4", label="exact")
        axes[1].plot(t, small_chern_mesh, color="#FF7F0E", ls="--", label="small-q")
        axes[1].axhline(1.0, color="black", ls=":")
        axes[1].axhline(0.0, color="black", ls=":", alpha=0.5)
        axes[1].set(xlabel="time", ylabel="mesh-integrated Chern")
        axes[1].legend(frameon=False)
        figure.suptitle(
            "Extended-Hubbard flow; physical parameters exact, numerical mesh reconstructed"
        )
        figure.savefig(figure_path, dpi=200)
        plt.close(figure)
    supplemental_outputs: list[str] = []
    if mode == "feature":
        exact_long = snapshots[long_time]["exact"]
        small_long = snapshots[long_time]["small_q"]
        exact_fields = geometry_fields(exact_long)
        small_fields = geometry_fields(small_long)
        grid_size = int(params["grid_size"])
        shifted_exact_fields = {
            key: zero_to_two_pi_field(value)
            for key, value in exact_fields.items()
        }
        shifted_small_fields = {
            key: zero_to_two_pi_field(value)
            for key, value in small_fields.items()
        }
        long_rows: list[dict[str, object]] = []
        for i in range(grid_size):
            for j in range(grid_size):
                long_rows.append(
                    {
                        "kx_over_2pi_mod": float(i / grid_size),
                        "ky_over_2pi_mod": float(j / grid_size),
                        "exact_half_trace": float(
                            shifted_exact_fields["half_trace"][i, j]
                        ),
                        "exact_half_curvature": float(
                            shifted_exact_fields["half_curvature"][i, j]
                        ),
                        "small_q_half_trace": float(
                            shifted_small_fields["half_trace"][i, j]
                        ),
                        "small_q_half_curvature": float(
                            shifted_small_fields["half_curvature"][i, j]
                        ),
                    }
                )
        write_csv(long_time_data_path, long_rows)
        if plt is not None:
            render_field_grid(
                [
                    (f"exact, t={long_time:g}", exact_fields),
                    (f"small-q, t={long_time:g}", small_fields),
                ],
                long_time_figure_path,
                "Supplemental Fig. 5 — long-time quantum geometry",
            )
        supplemental_outputs = [
            str(long_time_data_path.relative_to(WORKSPACE)),
            *(
                [str(long_time_figure_path.relative_to(WORKSPACE))]
                if plt is not None
                else []
            ),
        ]

    lambda_d = extended_hubbard_lambda_d(8.0, 0.75, 0.5 * np.pi)
    checks = {
        "lambda_d_matches_reported_rounding": bool(abs(lambda_d - 1.183) < 5e-4),
        "exact_energy_initially_decreases": bool(exact_e[-1] < exact_e[0]),
        "small_q_energy_initially_decreases": bool(small_e[-1] < small_e[0]),
        "unit_norm_preserved": bool(
            max(
                max(float(row["exact_max_norm_error"]), float(row["small_q_max_norm_error"]))
                for row in rows
            )
            < 1e-12
        ),
    }
    diagnostics: dict[str, float] = {
        "lambda_d": float(lambda_d),
        "initial_dirichlet_energy": float(exact_e[0]),
        "exact_final_dirichlet_energy": float(exact_e[-1]),
        "small_q_final_dirichlet_energy": float(small_e[-1]),
    }
    if time_max >= 4.32:
        short_index = int(np.argmin(np.abs(t - 4.32)))
        minimum_index = int(np.argmin(exact_e))
        checks.update(
            {
                "exact_near_bound_at_tshort": bool(
                    abs(exact_e[short_index] - np.pi) / np.pi < 0.15
                ),
                "exact_faster_than_small_q_at_tshort": bool(
                    exact_e[short_index] < small_e[short_index]
                ),
                "exact_topological_at_tshort_on_mesh": bool(
                    exact_chern_mesh[short_index] > 0.75
                ),
                "small_q_topology_preserved": bool(
                    np.min(small_chern_mesh) > 0.9
                ),
                "exact_trivial_by_t8": bool(
                    abs(
                        exact_chern_mesh[
                            int(np.argmin(np.abs(t - long_time)))
                        ]
                    )
                    < 0.05
                ),
            }
        )
        diagnostics.update(
            {
                "exact_dirichlet_at_tshort": float(exact_e[short_index]),
                "small_q_dirichlet_at_tshort": float(small_e[short_index]),
                "exact_mesh_chern_at_tshort": float(exact_chern_mesh[short_index]),
                "exact_minimum_time": float(t[minimum_index]),
                "exact_minimum_dirichlet_energy": float(exact_e[minimum_index]),
            }
        )
    payload: dict[str, object] = {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "T002",
        "artifact_stage": "exploratory",
        "mode": mode,
        "parameters": {
            **params,
            "time_max": time_max,
            "mass": -0.5,
            "gamma": 1.5,
            "onsite_u": 8.0,
            "nearest_v": 0.75,
            "lambda_t": 0.025,
            "cutoff_q": float(0.5 * np.pi),
            "lambda_d": float(lambda_d),
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": diagnostics,
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "not_accessed_by_numerical_runner",
        "outputs": [
            str(data_path.relative_to(WORKSPACE)),
            *(
                [str(figure_path.relative_to(WORKSPACE))]
                if plt is not None
                else []
            ),
            *supplemental_outputs,
        ],
    }
    write_json(check_path, payload)
    return payload


def trace_deviation(texture: np.ndarray) -> np.ndarray:
    fields = local_geometry(texture)
    return 0.5 * (fields["metric_trace"] - np.abs(fields["curvature"]))


def run_t003(mode: str) -> dict[str, object]:
    params = extended_flow_parameters(mode)
    short_time = 0.4 if mode == "smoke" else 4.32
    rows, snapshots = integrate_extended_hubbard_comparison(
        size=int(params["grid_size"]),
        mass=-0.5,
        gamma=1.5,
        onsite_u=8.0,
        nearest_v=0.75,
        lambda_t=0.025,
        cutoff_q=0.5 * np.pi,
        time_max=short_time,
        time_step=float(params["time_step"]),
        sample_interval=max(float(params["sample_interval"]), short_time),
        snapshot_times=(0.0, short_time),
        grid_offset_fraction=float(params["grid_offset_fraction"]),
    )
    initial = snapshots[0.0]["exact"]
    exact = snapshots[short_time]["exact"]
    small_q = snapshots[short_time]["small_q"]
    maps = {
        "initial": trace_deviation(initial),
        "exact": trace_deviation(exact),
        "small_q": trace_deviation(small_q),
    }
    profile_fields = {
        "initial": geometry_fields(initial),
        "exact": geometry_fields(exact),
        "small_q": geometry_fields(small_q),
    }
    grid_size = int(params["grid_size"])
    shifted_maps = {
        key: zero_to_two_pi_field(value)
        for key, value in maps.items()
    }
    shifted_profile_fields = {
        name: {
            key: zero_to_two_pi_field(value)
            for key, value in fields.items()
        }
        for name, fields in profile_fields.items()
    }
    data_rows: list[dict[str, object]] = []
    for i in range(grid_size):
        for j in range(grid_size):
            data_rows.append(
                {
                    "kx_over_2pi_mod": float(i / grid_size),
                    "ky_over_2pi_mod": float(j / grid_size),
                    "initial_trace_deviation": float(
                        shifted_maps["initial"][i, j]
                    ),
                    "exact_trace_deviation": float(
                        shifted_maps["exact"][i, j]
                    ),
                    "small_q_trace_deviation": float(
                        shifted_maps["small_q"][i, j]
                    ),
                    "initial_half_trace": float(
                        shifted_profile_fields["initial"]["half_trace"][i, j]
                    ),
                    "initial_half_curvature": float(
                        shifted_profile_fields["initial"]["half_curvature"][i, j]
                    ),
                    "exact_half_trace": float(
                        shifted_profile_fields["exact"]["half_trace"][i, j]
                    ),
                    "exact_half_curvature": float(
                        shifted_profile_fields["exact"]["half_curvature"][i, j]
                    ),
                    "small_q_half_trace": float(
                        shifted_profile_fields["small_q"]["half_trace"][i, j]
                    ),
                    "small_q_half_curvature": float(
                        shifted_profile_fields["small_q"]["half_curvature"][i, j]
                    ),
                }
            )
    data_path = DATA_DIR / "fig3_trace_deviation_maps.csv"
    figure_path = FIGURE_DIR / "fig3_trace_deviation_maps.png"
    check_path = CHECK_DIR / "fig3_trace_deviation_maps.json"
    supplemental_profiles_path = FIGURE_DIR / "sm_fig4_geometry_profiles.png"
    write_csv(data_path, data_rows)

    if plt is not None:
        figure, axes = plt.subplots(1, 3, figsize=(12.0, 3.7), constrained_layout=True)
        titles = (
            r"$t=0$",
            rf"exact, $t={short_time:g}$",
            rf"small-q, $t={short_time:g}$",
        )
        image = None
        for axis, key, title in zip(
            axes,
            ("initial", "exact", "small_q"),
            titles,
            strict=True,
        ):
            image = axis.imshow(
                shifted_maps[key].T,
                origin="lower",
                extent=(0.0, 1.0, 0.0, 1.0),
                cmap="viridis",
                vmin=0.0,
                vmax=0.1,
                interpolation="nearest",
                aspect="equal",
            )
            axis.set(
                xlabel=r"$k_x/2\pi$",
                ylabel=r"$k_y/2\pi$",
                title=title,
            )
        if image is None:
            raise RuntimeError("no map rendered")
        colorbar = figure.colorbar(image, ax=axes, shrink=0.88)
        colorbar.set_label(r"$[\mathrm{tr}\,g-|F_{12}|]/2$")
        figure.suptitle(
            "Trace-condition deviation; paper color range, reconstructed mesh"
        )
        figure.savefig(figure_path, dpi=200)
        plt.close(figure)
        render_field_grid(
            [
                ("initial", profile_fields["initial"]),
                (f"exact, t={short_time:g}", profile_fields["exact"]),
                (f"small-q, t={short_time:g}", profile_fields["small_q"]),
            ],
            supplemental_profiles_path,
            "Supplemental Fig. 4 — geometry at the near-ideal time",
        )

    initial_mean = float(np.mean(maps["initial"]))
    exact_mean = float(np.mean(maps["exact"]))
    small_mean = float(np.mean(maps["small_q"]))
    exact_geometry = geometry_observables(exact)
    checks = {
        "continuum_bound_respected_to_tolerance": bool(
            min(float(np.min(value)) for value in maps.values()) > -2e-8
        ),
        "exact_reduces_mean_trace_deviation": bool(exact_mean < initial_mean),
        "small_q_reduces_mean_trace_deviation": bool(small_mean < initial_mean),
        "unit_norm_preserved": bool(
            max(
                float(row["exact_max_norm_error"])
                for row in rows
            )
            < 1e-12
        ),
    }
    if mode == "feature":
        checks["exact_remains_topological_at_tshort"] = bool(
            exact_geometry.finite_difference_chern > 0.75
        )
        checks["exact_is_closer_than_small_q"] = bool(exact_mean < small_mean)
    payload: dict[str, object] = {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "T003",
        "artifact_stage": "exploratory",
        "mode": mode,
        "parameters": {
            **params,
            "time_max": short_time,
            "mass": -0.5,
            "gamma": 1.5,
            "onsite_u": 8.0,
            "nearest_v": 0.75,
            "lambda_t": 0.025,
            "cutoff_q": float(0.5 * np.pi),
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "initial_mean_trace_deviation": initial_mean,
            "exact_mean_trace_deviation": exact_mean,
            "small_q_mean_trace_deviation": small_mean,
            "initial_max_trace_deviation": float(np.max(maps["initial"])),
            "exact_max_trace_deviation": float(np.max(maps["exact"])),
            "small_q_max_trace_deviation": float(np.max(maps["small_q"])),
            "exact_mesh_chern": float(exact_geometry.finite_difference_chern),
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "not_accessed_by_numerical_runner",
        "outputs": [
            str(data_path.relative_to(WORKSPACE)),
            *(
                [
                    str(figure_path.relative_to(WORKSPACE)),
                    str(supplemental_profiles_path.relative_to(WORKSPACE)),
                ]
                if plt is not None
                else []
            ),
        ],
    }
    write_json(check_path, payload)
    return payload


def first_transition_time(
    rows: list[dict[str, float]],
    threshold: float = 0.5,
) -> float | None:
    """Return the first sampled time at which the mesh Chern crosses down."""

    for row in rows:
        if row["chern_mesh_integral"] < threshold:
            return float(row["time"])
    return None


def run_t004(mode: str) -> dict[str, object]:
    """Reproduce the extended-Hubbard robustness scan in Supplemental Fig. 6."""

    if mode == "smoke":
        grid_size = 31
        time_step = 0.04
        sample_interval = 0.2
        v_values = (0.0, 1.0, 4.75)
        u_values = (0.0, 3.0, 8.0)
        v_time_max = 2.0
        u_time_max = 2.0
    else:
        grid_size = 61
        time_step = 0.02
        sample_interval = 0.1
        v_values = (0.0, 0.5, 1.0, 1.75, 2.5, 3.25, 4.0, 4.75)
        u_values = (0.0, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0)
        v_time_max = 10.0
        u_time_max = 20.0

    all_rows: list[dict[str, object]] = []
    transition_times: dict[str, float | None] = {}
    maximum_norm_error = 0.0

    def run_curve(
        sweep: str,
        onsite_u: float,
        nearest_v: float,
        time_max: float,
    ) -> list[dict[str, float]]:
        nonlocal maximum_norm_error
        rows = integrate_exact_extended_hubbard(
            size=grid_size,
            mass=-0.5,
            gamma=1.5,
            onsite_u=onsite_u,
            nearest_v=nearest_v,
            lambda_t=0.025,
            time_max=time_max,
            time_step=time_step,
            sample_interval=sample_interval,
            grid_offset_fraction=0.5,
        )
        key = f"{sweep}:U={onsite_u:g}:V={nearest_v:g}"
        transition_times[key] = first_transition_time(rows)
        maximum_norm_error = max(
            maximum_norm_error,
            max(float(row["max_norm_error"]) for row in rows),
        )
        for row in rows:
            all_rows.append(
                {
                    "sweep": sweep,
                    "onsite_u": onsite_u,
                    "nearest_v": nearest_v,
                    **row,
                }
            )
        return rows

    curves_v = {
        value: run_curve("fixed_U", 8.0, value, v_time_max)
        for value in v_values
    }
    curves_u = {
        value: run_curve("fixed_V", value, 0.75, u_time_max)
        for value in u_values
    }

    data_path = DATA_DIR / "sm_fig6_parameter_sweeps.csv"
    figure_path = FIGURE_DIR / "sm_fig6_parameter_sweeps.png"
    check_path = CHECK_DIR / "sm_fig6_parameter_sweeps.json"
    write_csv(data_path, all_rows)

    if plt is not None:
        figure, axes = plt.subplots(2, 2, figsize=(11.0, 7.5), constrained_layout=True)
        for value, rows in curves_v.items():
            times = np.asarray([row["time"] for row in rows])
            energy = np.asarray([row["dirichlet_energy"] for row in rows]) - np.pi
            chern = np.asarray([row["chern_mesh_integral"] for row in rows])
            axes[0, 0].plot(times, energy, label=rf"$V={value:g}$")
            axes[0, 1].plot(times, chern, label=rf"$V={value:g}$")
        for value, rows in curves_u.items():
            times = np.asarray([row["time"] for row in rows])
            energy = np.asarray([row["dirichlet_energy"] for row in rows]) - np.pi
            chern = np.asarray([row["chern_mesh_integral"] for row in rows])
            axes[1, 0].plot(times, energy, label=rf"$U={value:g}$")
            axes[1, 1].plot(times, chern, label=rf"$U={value:g}$")
        axes[0, 0].set(title=r"fixed $U=8$", ylabel=r"$E_D-\pi$")
        axes[0, 1].set(title=r"fixed $U=8$", ylabel=r"$C_{\rm num}$")
        axes[1, 0].set(
            title=r"fixed $V=0.75$",
            xlabel="time",
            ylabel=r"$E_D-\pi$",
        )
        axes[1, 1].set(
            title=r"fixed $V=0.75$",
            xlabel="time",
            ylabel=r"$C_{\rm num}$",
        )
        for axis in axes.flat:
            axis.axhline(0.0, color="black", ls=":", lw=1.0)
            axis.legend(frameon=False, fontsize=7, ncol=2)
        figure.suptitle(
            "Supplemental Fig. 6 — interaction dependence "
            "(paper parameters, reconstructed mesh)"
        )
        figure.savefig(figure_path, dpi=180)
        plt.close(figure)

    def transition_or_after(key: str, end_time: float) -> float:
        value = transition_times[key]
        return end_time + sample_interval if value is None else value

    v0_transition = transition_or_after("fixed_U:U=8:V=0", v_time_max)
    vlast_transition = transition_or_after(
        f"fixed_U:U=8:V={v_values[-1]:g}",
        v_time_max,
    )
    u0_transition = transition_or_after("fixed_V:U=0:V=0.75", u_time_max)
    u8_transition = transition_or_after("fixed_V:U=8:V=0.75", u_time_max)
    checks = {
        "unit_norm_preserved": maximum_norm_error < 1e-12,
        "larger_v_delays_or_suppresses_transition": vlast_transition > v0_transition,
        "larger_u_accelerates_transition": u8_transition < u0_transition,
        "u8_v075_transitions_within_window": u8_transition <= u_time_max,
    }
    payload: dict[str, object] = {
        "status": "passed" if all(checks.values()) else "failed",
        "target_id": "T004",
        "artifact_stage": "exploratory",
        "mode": mode,
        "parameters": {
            "grid_size": grid_size,
            "time_step": time_step,
            "sample_interval": sample_interval,
            "grid_offset_fraction": 0.5,
            "mass": -0.5,
            "gamma": 1.5,
            "lambda_t": 0.025,
            "fixed_u": 8.0,
            "v_values": list(v_values),
            "v_time_max": v_time_max,
            "fixed_v": 0.75,
            "u_values": list(u_values),
            "u_time_max": u_time_max,
            "parameter_match": "paper_exact",
        },
        "checks": checks,
        "diagnostics": {
            "transition_times": transition_times,
            "maximum_norm_error": maximum_norm_error,
        },
        "generated_data_provenance": "independent_numerics",
        "reference_comparison": "source_figure_only",
        "outputs": [
            str(data_path.relative_to(WORKSPACE)),
            *(
                [str(figure_path.relative_to(WORKSPACE))]
                if plt is not None
                else []
            ),
        ],
    }
    write_json(check_path, payload)
    return payload


RUNNERS: dict[str, Callable[[str], dict[str, object]]] = {
    "T001": run_t001,
    "T002": run_t002,
    "T003": run_t003,
    "T004": run_t004,
}


def load_dispatch_config(path: Path, target_id: str, mode: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("paper_id") != "2511.11394":
        raise RuntimeError("config paper_id does not match this case")
    if payload.get("artifact_stage") != "exploratory":
        raise RuntimeError("only the exploratory artifact stage is authorized")
    target = (payload.get("targets") or {}).get(target_id)
    if not isinstance(target, dict) or target.get("mode") != mode:
        raise RuntimeError(f"config does not authorize {target_id} in {mode} mode")
    boundary = payload.get("source_boundary") or {}
    if any(
        boundary.get(key) is not False
        for key in (
            "source_pixels_used_as_scientific_input",
            "source_figure_directory_readable",
            "author_code_used",
            "author_numeric_arrays_used",
        )
    ):
        raise RuntimeError("config violates the isolated scientific source boundary")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=TARGETS)
    parser.add_argument("--mode", choices=("smoke", "feature"), default="feature")
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Generate only numerical data and checks for isolated attestation.",
    )
    parser.add_argument(
        "--attested-stage",
        choices=("exploratory",),
        help=(
            "Explicit stage for a run_contract invocation. Ordinary guarded runs "
            "continue to use PRAGENT_GUARDED_STAGE."
        ),
    )
    args = parser.parse_args()

    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    load_dispatch_config(config_path.resolve(), args.target, args.mode)

    guarded_target = os.environ.get(GUARDED_TARGET_ENV)
    if args.attested_stage is None and guarded_target != args.target:
        parser.error(
            f"{GUARDED_TARGET_ENV}={guarded_target!r} does not authorize "
            f"target {args.target!r}"
        )
    guarded_stage = args.attested_stage or os.environ.get(GUARDED_STAGE_ENV)
    if guarded_stage != "exploratory":
        parser.error(
            "This case has undisclosed paper mesh and integrator parameters; "
            "only the exploratory stage is authorized."
        )

    configure_rendering(not args.no_render)
    started = time.perf_counter()
    payload = RUNNERS[args.target](args.mode)
    payload["runtime_seconds"] = time.perf_counter() - started
    write_json(
        CHECK_DIR / f"{args.target.lower()}_paper_target_run.json",
        payload,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
