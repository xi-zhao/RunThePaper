"""Freeze auxiliary paper-scope targets that sit on top of generated numerics."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .analysis import (
    fit_vft,
    green_kubo_viscosity,
    linear_fit_through_origin,
    power_law_fit,
    threshold_crossing,
)

AUX_TARGET_FILENAMES = {
    "T018": "T018_fig2a_newtonian_fits.png",
    "T019": "T019_fig2b_newtonian_fits.png",
    "T020": "T020_fig3a_fit_families.png",
    "T021": "T021_fig3b_vc_boundary.png",
    "T022": "T022_fig5_power_law_fits.png",
    "T023": "T023_fig6_top_thickening_loss.png",
    "T024": "T024_fig7b_linear_guide.png",
    "T029": "T029_green_kubo_vs_rheology.png",
    "T030": "T030_p0_double_star_scan.png",
}


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


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def _cubic_hermite_segments(
    x: np.ndarray,
    y: np.ndarray,
    samples_per_segment: int = 32,
) -> tuple[np.ndarray, np.ndarray]:
    if len(x) < 2:
        raise ValueError("at least two knots are required")
    slopes = np.empty_like(y)
    slopes[0] = (y[1] - y[0]) / (x[1] - x[0])
    slopes[-1] = (y[-1] - y[-2]) / (x[-1] - x[-2])
    if len(x) > 2:
        slopes[1:-1] = (y[2:] - y[:-2]) / (x[2:] - x[:-2])
    pieces_x: list[np.ndarray] = []
    pieces_y: list[np.ndarray] = []
    for index in range(len(x) - 1):
        left = x[index]
        right = x[index + 1]
        interval = right - left
        grid = np.linspace(0.0, 1.0, samples_per_segment, endpoint=index == len(x) - 2)
        h00 = 2.0 * grid**3 - 3.0 * grid**2 + 1.0
        h10 = grid**3 - 2.0 * grid**2 + grid
        h01 = -2.0 * grid**3 + 3.0 * grid**2
        h11 = grid**3 - grid**2
        values = (
            h00 * y[index]
            + h10 * interval * slopes[index]
            + h01 * y[index + 1]
            + h11 * interval * slopes[index + 1]
        )
        pieces_x.append(left + interval * grid)
        pieces_y.append(values)
    return np.concatenate(pieces_x), np.concatenate(pieces_y)


def _build_newtonian_rows(
    curves: list[dict[str, Any]],
    *,
    target_id: str,
    p0: float,
    activities: tuple[float, ...],
) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for activity in activities:
        selected = next(
            (
                curve
                for curve in curves
                if abs(float(curve["p0"]) - p0) <= 1e-8
                and abs(float(curve["activity"]) - activity) <= 1e-8
            ),
            None,
        )
        if selected is None:
            continue
        eta = float(selected["viscosity"])
        residual = float(selected["viscosity_relative_rms"])
        for shear_rate in np.asarray(selected["shear_rate"], dtype=float):
            rows.append(
                {
                    "target_id": target_id,
                    "p0": p0,
                    "activity": activity,
                    "shear_rate": float(shear_rate),
                    "fit_stress": float(eta * shear_rate),
                    "newtonian_viscosity": eta,
                    "relative_rms": residual,
                }
            )
    return rows


def _plot_newtonian_family(
    curves: list[dict[str, Any]],
    rows: list[dict[str, float | str]],
    *,
    path: Path,
    p0: float,
    title: str,
) -> None:
    fig, axis = plt.subplots(figsize=(3.35, 3.0))
    selected = _matching_curves(curves, p0=p0)
    by_activity: dict[float, list[dict[str, float | str]]] = {}
    for row in rows:
        by_activity.setdefault(float(row["activity"]), []).append(row)
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, max(len(selected), 1)))
    for curve, color in zip(selected, colors, strict=True):
        activity = float(curve["activity"])
        axis.loglog(
            curve["shear_rate"],
            curve["stress"],
            "o-",
            ms=3,
            lw=1.0,
            color=color,
            alpha=0.9,
        )
        fit_rows = sorted(
            by_activity.get(activity, []),
            key=lambda item: float(item["shear_rate"]),
        )
        if fit_rows:
            axis.loglog(
                [float(item["shear_rate"]) for item in fit_rows],
                [float(item["fit_stress"]) for item in fit_rows],
                "--",
                lw=0.9,
                color=color,
            )
    axis.set_xlabel(r"shear rate $\dot\gamma$")
    axis.set_ylabel(r"stress $\sigma$")
    axis.set_title(title)
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _build_vft_rows(
    curves: list[dict[str, Any]],
) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    low_p0 = (3.5, 3.575, 3.65, 3.725, 3.76, 3.8)
    high_p0 = (3.825, 3.85, 3.875, 3.9, 3.95, 4.0)
    fit_rows: list[dict[str, float | str]] = []
    vc_rows: list[dict[str, float | str]] = []
    for p0 in low_p0:
        selected = _matching_curves(curves, p0=p0)
        if len(selected) < 3:
            continue
        activity = np.asarray([curve["activity"] for curve in selected], dtype=float)
        viscosity = np.asarray([curve["viscosity"] for curve in selected], dtype=float)
        fit = fit_vft(activity, viscosity)
        grid = np.geomspace(max(fit["critical_activity"] + 1e-4, np.min(activity)), np.max(activity), 48)
        fitted = np.exp(fit["log_prefactor"] + fit["activation_scale"] / (grid - fit["critical_activity"]))
        for value, eta in zip(grid, fitted, strict=True):
            fit_rows.append(
                {
                    "target_id": "T020",
                    "p0": p0,
                    "activity": float(value),
                    "fitted_viscosity": float(eta),
                    "fit_family": "vft",
                }
            )
        vc_rows.append(
            {
                "target_id": "T021",
                "p0": p0,
                "critical_activity": float(fit["critical_activity"]),
                "fit_family": "vft",
            }
        )
    for p0 in high_p0:
        selected = _matching_curves(curves, p0=p0)
        if len(selected) < 2:
            continue
        activity = np.asarray([curve["activity"] for curve in selected], dtype=float)
        viscosity = np.asarray([curve["viscosity"] for curve in selected], dtype=float)
        grid, values = _cubic_hermite_segments(activity, np.log(viscosity))
        for value, eta in zip(grid, np.exp(values), strict=True):
            fit_rows.append(
                {
                    "target_id": "T020",
                    "p0": p0,
                    "activity": float(value),
                    "fitted_viscosity": float(eta),
                    "fit_family": "spline",
                }
            )
    return fit_rows, vc_rows


def _plot_viscosity_fits(
    curves: list[dict[str, Any]],
    fit_rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(3.6, 3.0))
    p0_values = sorted({float(curve["p0"]) for curve in curves})
    colors = plt.cm.Spectral(np.linspace(0.05, 0.95, len(p0_values))) if p0_values else []
    for color, p0 in zip(colors, p0_values, strict=True):
        selected = _matching_curves(curves, p0=p0)
        if not selected:
            continue
        activity = np.asarray([curve["activity"] for curve in selected], dtype=float)
        viscosity = np.asarray([curve["viscosity"] for curve in selected], dtype=float)
        axis.loglog(activity, viscosity, "o", ms=2.6, color=color)
        subset = sorted(
            [row for row in fit_rows if abs(float(row["p0"]) - p0) <= 1e-8],
            key=lambda item: float(item["activity"]),
        )
        if subset:
            style = "-" if subset[0]["fit_family"] == "vft" else "--"
            axis.loglog(
                [float(row["activity"]) for row in subset],
                [float(row["fitted_viscosity"]) for row in subset],
                style,
                lw=0.9,
                color=color,
                label=f"{p0:.3f}",
            )
    axis.set_xlabel(r"activity $v$")
    axis.set_ylabel(r"Newtonian viscosity $\eta$")
    axis.set_title("Frozen viscosity fits")
    axis.grid(alpha=0.15, which="both")
    if p0_values:
        axis.legend(title=r"$p_0$", fontsize=6, title_fontsize=7, frameon=False, ncol=2)
    _save(fig, path)


def _plot_vc_boundary(
    vc_rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> list[dict[str, float | str]]:
    line_rows: list[dict[str, float | str]] = []
    fig, axis = plt.subplots(figsize=(3.2, 2.9))
    if len(vc_rows) >= 2:
        x = np.asarray([float(row["p0"]) for row in vc_rows], dtype=float)
        y = np.asarray([float(row["critical_activity"]) for row in vc_rows], dtype=float)
        slope, intercept, r_squared = linear_fit_through_origin(x - np.min(x), y)
        grid = np.linspace(np.min(x), np.max(x), 64)
        values = intercept + slope * (grid - np.min(x))
        axis.plot(x, y, "^", color="black", ms=4)
        axis.plot(grid, values, color="#c2185b", lw=1.0)
        for p0, value in zip(grid, values, strict=True):
            line_rows.append(
                {
                    "target_id": "T021",
                    "p0": float(p0),
                    "critical_activity": float(value),
                    "fit_family": "linear",
                    "r_squared": float(r_squared),
                }
            )
    elif vc_rows:
        x = np.asarray([float(row["p0"]) for row in vc_rows], dtype=float)
        y = np.asarray([float(row["critical_activity"]) for row in vc_rows], dtype=float)
        axis.plot(x, y, "^", color="black", ms=4)
    else:
        axis.text(0.5, 0.5, "No VFT critical activities available", ha="center", va="center", transform=axis.transAxes)
    axis.set_xlabel(r"target shape $p_0$")
    axis.set_ylabel(r"critical activity $v_c$")
    axis.set_title("Frozen $v_c(p_0)$ fit")
    axis.grid(alpha=0.15)
    _save(fig, path)
    return line_rows


def _build_onset_rows(
    curves: list[dict[str, Any]],
) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    fit_rows: list[dict[str, float | str]] = []
    data_rows: list[dict[str, float | str]] = []
    all_x: list[float] = []
    all_y: list[float] = []
    for p0 in (3.76, 3.8, 3.825, 3.85, 3.875, 3.9, 3.95, 4.0):
        selected = [
            curve
            for curve in _matching_curves(curves, p0=p0)
            if curve["thickening_rate"] is not None and float(curve["activity"]) > 0.0
        ]
        if not selected:
            continue
        x = np.asarray([curve["activity"] for curve in selected], dtype=float)
        y = np.asarray([curve["thickening_rate"] for curve in selected], dtype=float)
        for activity, onset in zip(x, y, strict=True):
            data_rows.append(
                {
                    "target_id": "T022",
                    "p0": p0,
                    "activity": float(activity),
                    "thickening_rate": float(onset),
                    "fit_family": "data",
                }
            )
        all_x.extend(x.tolist())
        all_y.extend(y.tolist())
        if len(x) >= 2:
            fit = power_law_fit(x, y)
            grid = np.geomspace(np.min(x), np.max(x), 40)
            for activity, onset in zip(grid, fit["prefactor"] * grid ** fit["exponent"], strict=True):
                fit_rows.append(
                    {
                        "target_id": "T022",
                        "p0": p0,
                        "activity": float(activity),
                        "thickening_rate": float(onset),
                        "fit_family": "power_law",
                        "exponent": float(fit["exponent"]),
                    }
                )
    if all_x and all_y:
        x = np.asarray(all_x, dtype=float)
        y = np.asarray(all_y, dtype=float)
        prefactor = float(np.exp(np.mean(np.log(y) - 2.0 * np.log(x))))
        grid = np.geomspace(np.min(x), np.max(x), 80)
        for activity, onset in zip(grid, prefactor * grid**2, strict=True):
            fit_rows.append(
                {
                    "target_id": "T022",
                    "p0": -1.0,
                    "activity": float(activity),
                    "thickening_rate": float(onset),
                    "fit_family": "alpha2_guide",
                    "exponent": 2.0,
                }
            )
    return fit_rows, data_rows


def _plot_onset_fits(
    fit_rows: list[dict[str, float | str]],
    data_rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(3.35, 2.95))
    p0_values = sorted({float(row["p0"]) for row in data_rows})
    colors = plt.cm.Spectral(np.linspace(0.05, 0.95, len(p0_values))) if p0_values else []
    for color, p0 in zip(colors, p0_values, strict=True):
        selected = [row for row in data_rows if abs(float(row["p0"]) - p0) <= 1e-8]
        if not selected:
            continue
        axis.loglog(
            [float(row["activity"]) for row in selected],
            [float(row["thickening_rate"]) for row in selected],
            "o",
            ms=3,
            color=color,
        )
        fitted = sorted(
            [
                row
                for row in fit_rows
                if abs(float(row["p0"]) - p0) <= 1e-8
                and row["fit_family"] == "power_law"
            ],
            key=lambda item: float(item["activity"]),
        )
        if fitted:
            axis.loglog(
                [float(row["activity"]) for row in fitted],
                [float(row["thickening_rate"]) for row in fitted],
                "-",
                lw=1.0,
                color=color,
            )
    guide = sorted(
        [row for row in fit_rows if row["fit_family"] == "alpha2_guide"],
        key=lambda item: float(item["activity"]),
    )
    if guide:
        axis.loglog(
            [float(row["activity"]) for row in guide],
            [float(row["thickening_rate"]) for row in guide],
            "k:",
            lw=1.0,
            label=r"$\alpha=2$ guide",
        )
        axis.legend(frameon=False, fontsize=7)
    axis.set_xlabel(r"activity $v$")
    axis.set_ylabel(r"onset $\dot\gamma_{thick}$")
    axis.set_title("Frozen onset fits")
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _build_thickening_loss_rows(
    curves: list[dict[str, Any]],
) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for p0 in sorted({float(curve["p0"]) for curve in curves}):
        selected = _matching_curves(curves, p0=p0)
        if len(selected) < 2:
            continue
        activity = np.asarray([curve["activity"] for curve in selected], dtype=float)
        maximum = np.asarray([curve["maximum_slope"] for curve in selected], dtype=float)
        crossing = threshold_crossing(activity, maximum, threshold=1.2, rising=False)
        if crossing is None:
            continue
        rows.append(
            {
                "target_id": "T023",
                "p0": p0,
                "activity": float(crossing),
                "criterion": "Gmax=1.2",
            }
        )
    return rows


def _plot_thickening_loss(
    rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(3.3, 2.9))
    if len(rows) >= 2:
        x = np.asarray([float(row["p0"]) for row in rows], dtype=float)
        y = np.asarray([float(row["activity"]) for row in rows], dtype=float)
        slope, intercept, _ = linear_fit_through_origin(x - np.min(x), y)
        grid = np.linspace(np.min(x), np.max(x), 64)
        axis.plot(x, y, "o", color="black", ms=4)
        axis.plot(grid, intercept + slope * (grid - np.min(x)), color="black", lw=1.0)
    elif rows:
        x = np.asarray([float(row["p0"]) for row in rows], dtype=float)
        y = np.asarray([float(row["activity"]) for row in rows], dtype=float)
        axis.plot(x, y, "o", color="black", ms=4)
    else:
        axis.text(0.5, 0.5, "No thickening-loss crossing resolved", ha="center", va="center", transform=axis.transAxes)
    axis.set_xlabel(r"target shape $p_0$")
    axis.set_ylabel(r"activity $v$")
    axis.set_title("Frozen thickening-loss boundary")
    axis.grid(alpha=0.15)
    _save(fig, path)


def _build_peclet_rows(
    curves: list[dict[str, Any]],
) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]]]:
    data_rows: list[dict[str, float | str]] = []
    line_rows: list[dict[str, float | str]] = []
    x_values: list[float] = []
    y_values: list[float] = []
    for curve in curves:
        if float(curve["activity"]) <= 0.0 or curve["thickening_rate"] is None:
            continue
        x = float(curve["viscosity"] / curve["activity"] ** 2)
        y = float(1.0 / curve["thickening_rate"])
        x_values.append(x)
        y_values.append(y)
        data_rows.append(
            {
                "target_id": "T024",
                "p0": float(curve["p0"]),
                "activity": float(curve["activity"]),
                "scaled_viscosity": x,
                "inverse_onset": y,
                "fit_family": "data",
            }
        )
    if len(x_values) >= 2:
        slope, _, r_squared = linear_fit_through_origin(
            np.asarray(x_values, dtype=float),
            np.asarray(y_values, dtype=float),
        )
        grid = np.geomspace(min(x_values), max(x_values), 80)
        for value in grid:
            line_rows.append(
                {
                    "target_id": "T024",
                    "scaled_viscosity": float(value),
                    "inverse_onset": float(slope * value),
                    "fit_family": "linear_guide",
                    "r_squared": float(r_squared),
                }
            )
    return data_rows, line_rows


def _plot_peclet_relation(
    data_rows: list[dict[str, float | str]],
    line_rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(3.15, 2.8))
    if data_rows:
        axis.loglog(
            [float(row["scaled_viscosity"]) for row in data_rows],
            [float(row["inverse_onset"]) for row in data_rows],
            "o",
            color="#4c78a8",
            ms=3,
        )
    if line_rows:
        axis.loglog(
            [float(row["scaled_viscosity"]) for row in line_rows],
            [float(row["inverse_onset"]) for row in line_rows],
            "k--",
            lw=1.0,
        )
    else:
        axis.text(0.5, 0.5, "No onset-collapse relation resolved", ha="center", va="center", transform=axis.transAxes)
    axis.set_xlabel(r"$\eta/v^2$")
    axis.set_ylabel(r"$1/\dot\gamma_{thick}$")
    axis.set_title("Frozen Peclet guide")
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _build_green_kubo_rows(
    curves: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> list[dict[str, float | str]]:
    rheology = {
        (float(curve["p0"]), float(curve["activity"])): float(curve["viscosity"])
        for curve in curves
        if float(np.min(np.asarray(curve["shear_rate"], dtype=float))) > 0.0
    }
    grouped: dict[tuple[float, float], list[float]] = {}
    for item in results:
        condition = item["condition"]
        if abs(float(condition.shear_rate)) > 1e-14:
            continue
        if "stress" not in item or "time" not in item:
            with np.load(item["result_path"], allow_pickle=False) as payload:
                item["stress"] = np.asarray(payload["stress"], dtype=np.float64)
                item["time"] = np.asarray(payload["time"], dtype=np.float64)
        time = np.asarray(item["time"], dtype=np.float64)
        time_step = float(np.median(np.diff(time))) if len(time) >= 2 else 1.0
        grouped.setdefault((float(condition.p0), float(condition.activity)), []).append(
            green_kubo_viscosity(np.asarray(item["stress"], dtype=float), time_step)
        )
    rows: list[dict[str, float | str]] = []
    for (p0, activity), values in sorted(grouped.items()):
        if not values:
            continue
        mean = float(np.mean(values))
        sem = float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0
        rows.append(
            {
                "target_id": "T029",
                "p0": p0,
                "activity": activity,
                "green_kubo_viscosity": mean,
                "green_kubo_sem": sem,
                "rheology_viscosity": rheology.get((p0, activity)),
            }
        )
    return rows


def _plot_green_kubo(
    rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(3.2, 2.8))
    valid = [
        row
        for row in rows
        if row.get("rheology_viscosity") is not None
        and float(row["green_kubo_viscosity"]) > 0.0
        and float(row["rheology_viscosity"]) > 0.0
    ]
    if valid:
        x = np.asarray([float(row["rheology_viscosity"]) for row in valid], dtype=float)
        y = np.asarray([float(row["green_kubo_viscosity"]) for row in valid], dtype=float)
        axis.loglog(x, y, "o", ms=3, color="#4c78a8")
        guide = np.geomspace(min(np.min(x), np.min(y)), max(np.max(x), np.max(y)), 80)
        axis.loglog(guide, guide, "k--", lw=0.9)
    else:
        axis.text(0.5, 0.5, "Need matched zero-shear and low-rate samples", ha="center", va="center", transform=axis.transAxes)
    axis.set_xlabel(r"rheology $\eta$")
    axis.set_ylabel(r"Green-Kubo $\eta$")
    axis.set_title("Green-Kubo comparison")
    axis.grid(alpha=0.15, which="both")
    _save(fig, path)


def _build_p0_double_star_rows(
    curves: list[dict[str, Any]],
) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for curve in [curve for curve in curves if abs(float(curve["activity"])) <= 1e-14]:
        slope = np.asarray(curve["slope"], dtype=float)
        quasistatic = float(np.mean(slope[: min(2, len(slope))]))
        rows.append(
            {
                "target_id": "T030",
                "p0": float(curve["p0"]),
                "quasistatic_slope": quasistatic,
                "newtonian_viscosity": float(curve["viscosity"]),
                "fit_family": "zero_activity_scan",
            }
        )
    rows.sort(key=lambda item: float(item["p0"]))
    return rows


def _plot_p0_double_star(
    rows: list[dict[str, float | str]],
    *,
    path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(3.2, 2.8))
    if rows:
        x = np.asarray([float(row["p0"]) for row in rows], dtype=float)
        y = np.asarray([float(row["quasistatic_slope"]) for row in rows], dtype=float)
        axis.plot(x, y, "o-", color="#4c78a8", lw=1.0, ms=3)
        crossing = threshold_crossing(x, y, threshold=0.95, rising=True)
        axis.axhline(0.95, color="0.4", lw=0.8, ls=":")
        if crossing is not None:
            axis.axvline(crossing, color="black", lw=0.9, ls="--")
    else:
        axis.text(0.5, 0.5, "No zero-activity p0 scan available", ha="center", va="center", transform=axis.transAxes)
    axis.set_xlabel(r"target shape $p_0$")
    axis.set_ylabel(r"low-rate log slope")
    axis.set_title(r"Exploratory $p_0^{**}$ scan")
    axis.grid(alpha=0.15)
    _save(fig, path)


def write_scope_target_artifacts(
    curves: list[dict[str, Any]],
    results: list[dict[str, Any]],
    *,
    workspace: Path,
    data_root: Path,
    figures_root: Path,
    checks_root: Path,
    profile: str,
    target_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    _style()
    selected = set(AUX_TARGET_FILENAMES) if target_ids is None else set(target_ids)
    data_dir = data_root / "auxiliary"
    figures_dir = figures_root
    checks_dir = checks_root

    if "T018" in selected:
        newtonian_solid = _build_newtonian_rows(
            curves,
            target_id="T018",
            p0=3.65,
            activities=(0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5),
        )
        _write_csv(
            data_dir / "T018_newtonian_fits.csv",
            ["target_id", "p0", "activity", "shear_rate", "fit_stress", "newtonian_viscosity", "relative_rms"],
            newtonian_solid,
        )
        _plot_newtonian_family(
            curves,
            newtonian_solid,
            path=figures_dir / AUX_TARGET_FILENAMES["T018"],
            p0=3.65,
            title="Frozen Fig. 2(a) Newtonian fits",
        )
    if "T019" in selected:
        newtonian_liquid = _build_newtonian_rows(
            curves,
            target_id="T019",
            p0=3.9,
            activities=(0.08, 0.10, 0.12, 0.14, 0.16, 0.20, 0.25, 0.30, 0.35, 0.40),
        )
        _write_csv(
            data_dir / "T019_newtonian_fits.csv",
            ["target_id", "p0", "activity", "shear_rate", "fit_stress", "newtonian_viscosity", "relative_rms"],
            newtonian_liquid,
        )
        _plot_newtonian_family(
            curves,
            newtonian_liquid,
            path=figures_dir / AUX_TARGET_FILENAMES["T019"],
            p0=3.9,
            title="Frozen Fig. 2(b) Newtonian fits",
        )

    vft_rows: list[dict[str, float | str]] = []
    vc_rows: list[dict[str, float | str]] = []
    if selected & {"T020", "T021"}:
        vft_rows, vc_rows = _build_vft_rows(curves)
    if "T020" in selected:
        _write_csv(
            data_dir / "T020_viscosity_fit_families.csv",
            ["target_id", "p0", "activity", "fitted_viscosity", "fit_family"],
            vft_rows,
        )
        _plot_viscosity_fits(curves, vft_rows, path=figures_dir / AUX_TARGET_FILENAMES["T020"])
    if "T021" in selected:
        vc_line = _plot_vc_boundary(vc_rows, path=figures_dir / AUX_TARGET_FILENAMES["T021"])
        _write_csv(
            data_dir / "T021_critical_activity_boundary.csv",
            ["target_id", "p0", "critical_activity", "fit_family", "r_squared"],
            [*vc_rows, *vc_line],
        )

    onset_fit_rows: list[dict[str, float | str]] = []
    onset_data_rows: list[dict[str, float | str]] = []
    if selected & {"T022", "T024"}:
        onset_fit_rows, onset_data_rows = _build_onset_rows(curves)
    if "T022" in selected:
        _write_csv(
            data_dir / "T022_onset_power_laws.csv",
            ["target_id", "p0", "activity", "thickening_rate", "fit_family", "exponent"],
            onset_fit_rows,
        )
        _plot_onset_fits(
            onset_fit_rows,
            onset_data_rows,
            path=figures_dir / AUX_TARGET_FILENAMES["T022"],
        )

    if "T023" in selected:
        thickening_loss_rows = _build_thickening_loss_rows(curves)
        _write_csv(
            data_dir / "T023_thickening_loss_boundary.csv",
            ["target_id", "p0", "activity", "criterion"],
            thickening_loss_rows,
        )
        _plot_thickening_loss(
            thickening_loss_rows,
            path=figures_dir / AUX_TARGET_FILENAMES["T023"],
        )

    if "T024" in selected:
        peclet_data, peclet_line = _build_peclet_rows(curves)
        _write_csv(
            data_dir / "T024_peclet_linear_guide.csv",
            ["target_id", "p0", "activity", "scaled_viscosity", "inverse_onset", "fit_family", "r_squared"],
            [*peclet_data, *peclet_line],
        )
        _plot_peclet_relation(
            peclet_data,
            peclet_line,
            path=figures_dir / AUX_TARGET_FILENAMES["T024"],
        )

    if "T029" in selected:
        green_kubo_rows = _build_green_kubo_rows(curves, results)
        _write_csv(
            data_dir / "T029_green_kubo_comparison.csv",
            ["target_id", "p0", "activity", "green_kubo_viscosity", "green_kubo_sem", "rheology_viscosity"],
            green_kubo_rows,
        )
        _plot_green_kubo(green_kubo_rows, path=figures_dir / AUX_TARGET_FILENAMES["T029"])

    if "T030" in selected:
        p0_rows = _build_p0_double_star_rows(curves)
        _write_csv(
            data_dir / "T030_p0_double_star_scan.csv",
            ["target_id", "p0", "quasistatic_slope", "newtonian_viscosity", "fit_family"],
            p0_rows,
        )
        _plot_p0_double_star(p0_rows, path=figures_dir / AUX_TARGET_FILENAMES["T030"])

    target_checks = []
    for target_id in sorted(selected):
        figure_path = figures_dir / AUX_TARGET_FILENAMES[target_id]
        data_path = next(
            data_dir.glob(f"{target_id}_*.csv"),
            None,
        )
        output_exists = figure_path.exists() and data_path is not None and data_path.exists()
        target_checks.append(
            {
                "target_id": target_id,
                "artifact_stage": "exploratory" if profile != "paper_scale" else "final_reproduction",
                "parameter_match": "reduced_scale" if profile != "paper_scale" else "reconstructed_paper_scale",
                "output_path": figure_path.relative_to(workspace).as_posix(),
                "data_path": data_path.relative_to(workspace).as_posix() if data_path else None,
                "output_exists": output_exists,
                "artifact_status": "passed" if output_exists else "failed",
                "science_status": "pending_paper_scale" if profile != "paper_scale" else "evaluated",
                "status": "partial",
                "reason": (
                    "The auxiliary target is now generated and hash-bound, but this profile still lacks paper-exact evidence."
                    if output_exists
                    else "The target-specific auxiliary artifact is missing."
                ),
            }
        )
    summary = {
        "schema_version": 1,
        "profile": profile,
        "target_checks": target_checks,
    }
    checks_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "auxiliary_target_checks.json").write_text(
        json_dumps(summary),
        encoding="utf-8",
    )
    return target_checks


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
