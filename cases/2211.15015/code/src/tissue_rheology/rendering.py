"""Render frozen generated arrays for all 17 numerical figure targets."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .analysis import peclet_collapse, power_law_fit
from .campaign import Condition, aggregate_flow_curves, atomic_json
from .geometry import edge_displacement
from .scope_targets import write_scope_target_artifacts
from .target_selection import select_condition_results, select_curve

TARGET_FILENAMES = {
    "T001": "T001_main_fig2a_flow_solid.png",
    "T002": "T002_main_fig2b_flow_liquid.png",
    "T003": "T003_main_fig3a_viscosity_activity.png",
    "T004": "T004_main_fig3b_viscosity_map.png",
    "T005": "T005_main_fig4a_dst_curve.png",
    "T006": "T006_main_fig4b_stress_strain.png",
    "T007": "T007_main_fig4c_stress_distribution.png",
    "T008": "T008_main_fig4d_low_tension_network.png",
    "T009": "T009_main_fig4e_high_tension_network.png",
    "T010": "T010_main_fig5_onset_scaling.png",
    "T011": "T011_main_fig6_phase_map.png",
    "T012": "T012_main_fig6i_yield.png",
    "T013": "T013_main_fig6ii_cst.png",
    "T014": "T014_main_fig6iii_dst.png",
    "T015": "T015_main_fig6iv_newtonian.png",
    "T016": "T016_main_fig7a_scaled_curves.png",
    "T017": "T017_main_fig7b_peclet_relation.png",
}

FEATURE_SCOPE_TARGET_IDS = {f"T{value:03d}" for value in range(18, 25)}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "figure.dpi": 150,
            "savefig.dpi": 180,
        }
    )


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.{os.getpid()}.tmp{path.suffix}")
    fig.savefig(temporary, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    os.replace(temporary, path)


def _matching_curves(
    curves: list[dict[str, Any]],
    *,
    p0: float,
    tolerance: float = 1e-8,
) -> list[dict[str, Any]]:
    return sorted(
        [curve for curve in curves if abs(float(curve["p0"]) - p0) <= tolerance],
        key=lambda item: float(item["activity"]),
    )


def _plot_flow_family(
    curves: list[dict[str, Any]],
    path: Path,
    *,
    p0: float,
    title: str,
) -> None:
    selected = _matching_curves(curves, p0=p0)
    fig, axis = plt.subplots(figsize=(3.25, 3.0))
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, max(len(selected), 1)))
    for color, curve in zip(colors, selected, strict=True):
        axis.loglog(
            curve["shear_rate"],
            curve["stress"],
            marker="o",
            ms=3,
            lw=1.1,
            color=color,
            label=f"v={float(curve['activity']):g}",
        )
        if curve["thickening_rate"] is not None:
            rate = float(curve["thickening_rate"])
            stress = float(np.interp(rate, curve["shear_rate"], curve["stress"]))
            axis.scatter(rate, stress, marker="s", s=18, color="black", zorder=4)
        if curve["thinning_rate"] is not None:
            rate = float(curve["thinning_rate"])
            stress = float(np.interp(rate, curve["shear_rate"], curve["stress"]))
            axis.scatter(rate, stress, marker="v", s=20, color="black", zorder=4)
    axis.set_xlabel(r"shear rate $\dot\gamma$")
    axis.set_ylabel(r"stress $\sigma$")
    axis.set_title(title)
    if selected:
        axis.legend(fontsize=6, ncol=2, frameon=False)
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _plot_viscosity_activity(curves: list[dict[str, Any]], path: Path) -> None:
    fig, axis = plt.subplots(figsize=(3.55, 3.0))
    p0_values = sorted({float(curve["p0"]) for curve in curves})
    colors = plt.cm.Spectral(np.linspace(0.05, 0.95, max(len(p0_values), 1)))
    for color, p0 in zip(colors, p0_values, strict=True):
        selected = _matching_curves(curves, p0=p0)
        activity = np.asarray([curve["activity"] for curve in selected], dtype=float)
        viscosity = np.asarray([curve["viscosity"] for curve in selected], dtype=float)
        valid = (activity > 0.0) & (viscosity > 0.0)
        if np.any(valid):
            axis.loglog(
                activity[valid],
                viscosity[valid],
                "o-",
                ms=3,
                lw=1,
                color=color,
                label=f"{p0:.3g}",
            )
    axis.set_xlabel(r"activity $v$")
    axis.set_ylabel(r"Newtonian estimate $\eta$")
    axis.set_title("Reduced-scale viscosity scan")
    axis.legend(title=r"$p_0$", fontsize=6, title_fontsize=7, ncol=2, frameon=False)
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _plot_viscosity_map(curves: list[dict[str, Any]], path: Path) -> None:
    fig, axis = plt.subplots(figsize=(3.5, 3.0))
    p0 = np.asarray([curve["p0"] for curve in curves], dtype=float)
    activity = np.asarray([curve["activity"] for curve in curves], dtype=float)
    viscosity = np.asarray([curve["viscosity"] for curve in curves], dtype=float)
    scatter = axis.scatter(
        p0, activity, c=np.log10(np.maximum(viscosity, 1e-14)), cmap="viridis", s=45
    )
    axis.set_xlabel(r"target shape $p_0$")
    axis.set_ylabel(r"activity $v$")
    axis.set_title("Generated viscosity map")
    fig.colorbar(scatter, ax=axis, label=r"$\log_{10}\eta$")
    _save(fig, path)


def _plot_single_curve(curve: dict[str, Any], path: Path, title: str) -> None:
    fig, axis = plt.subplots(figsize=(2.8, 2.55))
    axis.loglog(
        curve["shear_rate"], curve["stress"], "o-", color="#2b6cb0", ms=3, lw=1.3
    )
    reference = curve["shear_rate"] * curve["viscosity"]
    axis.loglog(
        curve["shear_rate"], reference, "k--", lw=0.9, label="low-rate Newtonian fit"
    )
    axis.set_xlabel(r"$\dot\gamma$")
    axis.set_ylabel(r"$\sigma$")
    axis.set_title(title)
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _condition_results(
    results: list[dict[str, Any]],
    *,
    p0: float,
    activity: float,
) -> list[dict[str, Any]]:
    selected = [
        item
        for item in results
        if abs(item["condition"].p0 - p0) < 1e-8
        and abs(item["condition"].activity - activity) < 1e-8
    ]
    selected.sort(key=lambda item: item["condition"].shear_rate)
    return selected


def _materialize(item: dict[str, Any]) -> dict[str, Any]:
    """Load one condition lazily; paper-scale aggregation stays bounded-memory."""

    if "stress" in item and "fractional" in item:
        return item
    with np.load(item["result_path"], allow_pickle=False) as payload:
        for key in payload.files:
            if not key.endswith("_json"):
                item[key] = np.asarray(payload[key])
    return item


def _plot_stress_diagnostics(
    results: list[dict[str, Any]],
    time_path: Path,
    distribution_path: Path,
    *,
    selector: dict[str, Any],
    strict: bool,
) -> list[dict[str, Any]]:
    selected = select_condition_results(results, selector, strict=strict)
    selected = [_materialize(item) for item in selected]
    colors = ["#4c78a8", "#e45756", "#54a24b"]
    fig, axis = plt.subplots(figsize=(3.5, 2.75))
    for color, item in zip(colors, selected, strict=False):
        axis.plot(
            item["strain"],
            item["stress"],
            color=color,
            lw=1.0,
            label=f"{item['condition'].shear_rate:g}",
        )
    axis.set_xlabel(r"strain $\gamma$")
    axis.set_ylabel(r"stress $\sigma$")
    axis.set_title("Generated stress histories")
    axis.legend(title=r"$\dot\gamma$", fontsize=7, frameon=False)
    _save(fig, time_path)

    fig, axis = plt.subplots(figsize=(3.2, 2.75))
    for color, item in zip(colors, selected, strict=False):
        values = np.log10(np.maximum(item["stress"], 1e-14))
        axis.hist(
            values,
            bins=max(6, min(24, len(values) // 3)),
            density=True,
            histtype="step",
            lw=1.5,
            color=color,
            label=f"{item['condition'].shear_rate:g}",
        )
    axis.set_xlabel(r"$\log_{10}\sigma$")
    axis.set_ylabel("probability density")
    axis.set_title("Generated stress distributions")
    axis.legend(title=r"$\dot\gamma$", fontsize=7, frameon=False)
    _save(fig, distribution_path)
    return selected


def _cycles_from_result(item: dict[str, Any]) -> list[list[int]]:
    flat = item["cell_flat"].astype(int)
    offsets = item["cell_offsets"].astype(int)
    return [
        flat[offsets[index] : offsets[index + 1]].tolist()
        for index in range(len(offsets) - 1)
    ]


def _plot_network(item: dict[str, Any], path: Path, title: str) -> None:
    item = _materialize(item)
    fractional = item["fractional"]
    lattice = item["lattice"]
    cells = _cycles_from_result(item)
    tension_lookup = {
        (min(int(first), int(second)), max(int(first), int(second))): float(tension)
        for first, second, tension in zip(
            item["network_first"],
            item["network_second"],
            item["network_tension"],
            strict=True,
        )
    }
    positive = np.asarray([value for value in tension_lookup.values() if value > 0.0])
    scale = float(np.quantile(positive, 0.9)) if len(positive) else 1.0
    fig, axis = plt.subplots(figsize=(4.2, 3.2))
    drawn: set[tuple[int, int]] = set()
    for cycle in cells:
        for index, first in enumerate(cycle):
            second = cycle[(index + 1) % len(cycle)]
            key = (min(first, second), max(first, second))
            if key in drawn:
                continue
            drawn.add(key)
            start = lattice @ fractional[first]
            stop = start + edge_displacement(fractional, first, second, lattice)
            tension = tension_lookup.get(key, 0.0)
            width = 0.35 + 3.0 * min(tension / max(scale, 1e-12), 2.0)
            axis.plot(
                [start[0], stop[0]],
                [start[1], stop[1]],
                color="black",
                lw=width,
                solid_capstyle="round",
            )
    axis.set_xlim(0.0, lattice[0, 0])
    axis.set_ylim(0.0, lattice[1, 1])
    axis.set_aspect("equal")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(title)
    _save(fig, path)


def _plot_onsets(curves: list[dict[str, Any]], path: Path) -> None:
    fig, axis = plt.subplots(figsize=(3.35, 2.9))
    p0_values = sorted({float(curve["p0"]) for curve in curves})
    colors = plt.cm.Spectral(np.linspace(0.05, 0.95, max(len(p0_values), 1)))
    plotted = 0
    for color, p0 in zip(colors, p0_values, strict=True):
        selected = [
            curve
            for curve in _matching_curves(curves, p0=p0)
            if curve["thickening_rate"] is not None and curve["activity"] > 0.0
        ]
        if not selected:
            continue
        x = np.asarray([curve["activity"] for curve in selected])
        y = np.asarray([curve["thickening_rate"] for curve in selected])
        axis.loglog(x, y, "o-", ms=3, lw=1, color=color, label=f"{p0:.3g}")
        if len(x) >= 2:
            fit = power_law_fit(x, y)
            grid = np.geomspace(np.min(x), np.max(x), 40)
            axis.loglog(
                grid,
                fit["prefactor"] * grid ** fit["exponent"],
                color=color,
                lw=0.8,
                alpha=0.7,
            )
        plotted += 1
    if not plotted:
        axis.text(
            0.5,
            0.5,
            "No G>1.2 crossing at this reduced scale",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
    axis.set_xlabel(r"activity $v$")
    axis.set_ylabel(r"onset $\dot\gamma_{thick}$")
    axis.set_title("Generated onset-rate scaling")
    if plotted:
        axis.legend(title=r"$p_0$", fontsize=6, frameon=False)
    _save(fig, path)


def _plot_phase(curves: list[dict[str, Any]], path: Path) -> None:
    fig, axis = plt.subplots(figsize=(3.45, 3.0))
    p0 = np.asarray([curve["p0"] for curve in curves])
    activity = np.asarray([curve["activity"] for curve in curves])
    maximum = np.asarray([curve["maximum_slope"] for curve in curves])
    thickening = maximum > 1.2
    if np.any(thickening):
        scatter = axis.scatter(
            p0[thickening],
            activity[thickening],
            c=maximum[thickening],
            cmap="viridis",
            s=50,
            vmin=1.2,
        )
        fig.colorbar(scatter, ax=axis, label=r"$G_{max}$")
    axis.scatter(
        p0[~thickening],
        activity[~thickening],
        facecolors="none",
        edgecolors="0.4",
        s=40,
    )
    axis.set_xlabel(r"target shape $p_0$")
    axis.set_ylabel(r"activity $v$")
    axis.set_title("Generated rheology phase map")
    _save(fig, path)


def _plot_scaled(curves: list[dict[str, Any]], path: Path) -> None:
    selected = [
        curve for curve in _matching_curves(curves, p0=3.9) if curve["activity"] > 0.0
    ]
    fig, axis = plt.subplots(figsize=(3.45, 3.0))
    colors = plt.cm.viridis(np.linspace(0.05, 0.95, max(len(selected), 1)))
    for color, curve in zip(colors, selected, strict=True):
        scaled = (
            curve["shear_rate"] * curve["viscosity"] / float(curve["activity"]) ** 2
        )
        axis.loglog(
            scaled,
            curve["stress"],
            "o-",
            ms=3,
            lw=1,
            color=color,
            label=f"{float(curve['activity']):g}",
        )
    axis.set_xlabel(r"$\dot\gamma\eta/v^2$")
    axis.set_ylabel(r"$\sigma$")
    axis.set_title("Printed Peclet rescaling")
    if selected:
        axis.legend(title=r"$v$", fontsize=6, frameon=False)
    _save(fig, path)


def _plot_peclet(curves: list[dict[str, Any]], path: Path) -> None:
    x: list[float] = []
    y: list[float] = []
    for curve in curves:
        if curve["activity"] > 0.0 and curve["thickening_rate"] is not None:
            x.append(float(curve["viscosity"] / curve["activity"] ** 2))
            y.append(float(1.0 / curve["thickening_rate"]))
    fig, axis = plt.subplots(figsize=(3.15, 2.8))
    if len(x):
        axis.loglog(x, y, "o", color="#4c78a8")
        if len(x) >= 2:
            fit = power_law_fit(np.asarray(x), np.asarray(y))
            grid = np.geomspace(min(x), max(x), 80)
            axis.loglog(
                grid,
                fit["prefactor"] * grid ** fit["exponent"],
                "k--",
                lw=1,
                label=f"slope={fit['exponent']:.2f}",
            )
            axis.legend(frameon=False)
    else:
        axis.text(
            0.5,
            0.5,
            "No resolved onset at this reduced scale",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
    axis.set_xlabel(r"$\eta/v^2$")
    axis.set_ylabel(r"$1/\dot\gamma_{thick}$")
    axis.set_title("Generated onset collapse")
    _save(fig, path)


def _write_data_tables(
    curves: list[dict[str, Any]],
    results: list[dict[str, Any]],
    data_dir: Path,
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    flow_path = data_dir / "flow_curves.csv"
    with flow_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "p0",
                "activity",
                "shear_rate",
                "stress",
                "stress_sem",
                "viscosity",
                "maximum_slope",
                "thickening_rate",
                "thinning_rate",
            ]
        )
        for curve in curves:
            for rate, stress, sem in zip(
                curve["shear_rate"], curve["stress"], curve["stress_sem"], strict=True
            ):
                writer.writerow(
                    [
                        curve["p0"],
                        curve["activity"],
                        rate,
                        stress,
                        sem,
                        curve["viscosity"],
                        curve["maximum_slope"],
                        curve["thickening_rate"],
                        curve["thinning_rate"],
                    ]
                )
    condition_path = data_dir / "condition_summary.csv"
    with condition_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "condition_id",
                "p0",
                "activity",
                "shear_rate",
                "seed",
                "mean_stress",
                "stress_std",
                "bimodality",
                "t1_count",
                "tension_component_fraction",
            ]
        )
        for item in results:
            condition: Condition = item["condition"]
            summary = item["record"]["summary"]
            writer.writerow(
                [
                    condition.condition_id,
                    condition.p0,
                    condition.activity,
                    condition.shear_rate,
                    condition.seed,
                    summary["mean_stress"],
                    summary["stress_std"],
                    summary["log_stress_bimodality"],
                    summary["t1_count"],
                    summary["largest_tension_component_fraction"],
                ]
            )


def render_all_targets(
    results: list[dict[str, Any]],
    *,
    workspace: Path,
    data_root: Path,
    figures_root: Path,
    checks_root: Path,
    profile: str,
    target_selectors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    _style()
    figures = figures_root
    figures.mkdir(parents=True, exist_ok=True)
    curves = aggregate_flow_curves(results)
    _write_data_tables(curves, results, data_root)

    _plot_flow_family(
        curves,
        figures / TARGET_FILENAMES["T001"],
        p0=3.65,
        title="Solid-side flow curves",
    )
    _plot_flow_family(
        curves,
        figures / TARGET_FILENAMES["T002"],
        p0=3.9,
        title="Liquid-side flow curves",
    )
    _plot_viscosity_activity(curves, figures / TARGET_FILENAMES["T003"])
    _plot_viscosity_map(curves, figures / TARGET_FILENAMES["T004"])
    strict_selection = profile == "paper_scale"
    dst_curve = select_curve(
        curves,
        target_selectors["T005"],
        strict=strict_selection,
    )
    _plot_single_curve(
        dst_curve, figures / TARGET_FILENAMES["T005"], "DST diagnostic curve"
    )
    _plot_stress_diagnostics(
        results,
        figures / TARGET_FILENAMES["T006"],
        figures / TARGET_FILENAMES["T007"],
        selector=target_selectors["T006"],
        strict=strict_selection,
    )
    low_network = select_condition_results(
        results,
        target_selectors["T008"],
        strict=strict_selection,
    )
    high_network = select_condition_results(
        results,
        target_selectors["T009"],
        strict=strict_selection,
    )
    if low_network:
        _plot_network(
            low_network[0],
            figures / TARGET_FILENAMES["T008"],
            "Low-rate generated tension network",
        )
    if high_network:
        _plot_network(
            high_network[0],
            figures / TARGET_FILENAMES["T009"],
            "High-rate generated tension network",
        )
    _plot_onsets(curves, figures / TARGET_FILENAMES["T010"])
    _plot_phase(curves, figures / TARGET_FILENAMES["T011"])
    for target, title in [
        ("T012", "Yield diagnostic"),
        ("T013", "CST diagnostic"),
        ("T014", "DST diagnostic"),
        ("T015", "Newtonian diagnostic"),
    ]:
        _plot_single_curve(
            select_curve(
                curves,
                target_selectors[target],
                strict=strict_selection,
            ),
            figures / TARGET_FILENAMES[target],
            title,
        )
    _plot_scaled(curves, figures / TARGET_FILENAMES["T016"])
    _plot_peclet(curves, figures / TARGET_FILENAMES["T017"])

    collapse = peclet_collapse(curves)
    target_checks: list[dict[str, Any]] = []
    for target_id, filename in TARGET_FILENAMES.items():
        path = figures / filename
        artifact_ok = path.exists()
        science_status = (
            "pending_paper_scale" if profile != "paper_scale" else "evaluated"
        )
        target_checks.append(
            {
                "target_id": target_id,
                "artifact_stage": (
                    "final_reproduction" if profile == "paper_scale" else "exploratory"
                ),
                "parameter_match": (
                    "reconstructed_paper_scale"
                    if profile == "paper_scale"
                    else "reduced_scale"
                ),
                "output_path": path.relative_to(workspace).as_posix(),
                "output_exists": artifact_ok,
                "artifact_status": "passed" if artifact_ok else "failed",
                "science_status": science_status,
                "status": (
                    "passed" if artifact_ok and profile == "paper_scale" else "partial"
                ),
                "reason": (
                    "The reduced/smoke run proves the independent model and target wiring, not the long-time rheological claim."
                    if profile != "paper_scale"
                    else "Paper-scale arrays are present; downstream claim-specific checks still govern authoritative completion."
                ),
            }
        )
    if results:
        target_checks.extend(
            write_scope_target_artifacts(
                curves,
                results,
                workspace=workspace,
                data_root=data_root,
                figures_root=figures_root,
                checks_root=checks_root,
                profile=profile,
                target_ids=FEATURE_SCOPE_TARGET_IDS,
            )
        )
    scientific = {
        "schema_version": 1,
        "paper_id": "2211.15015",
        "profile": profile,
        "conditions": len(results),
        "flow_curves": len(curves),
        "peclet_collapse": collapse,
        "resolved_thickening_curves": sum(
            curve["thickening_rate"] is not None for curve in curves
        ),
        "target_checks": target_checks,
        "paper_error_candidates": [],
        "artifact_status": (
            "passed"
            if all(item["artifact_status"] == "passed" for item in target_checks)
            else "failed"
        ),
        "science_status": (
            "pending_paper_scale" if profile != "paper_scale" else "evaluated"
        ),
        "status": (
            "partial"
            if profile != "paper_scale"
            else (
                "passed"
                if all(item["status"] == "passed" for item in target_checks)
                else "failed"
            )
        ),
    }
    atomic_json(checks_root / "target_checks.json", scientific)
    return scientific
