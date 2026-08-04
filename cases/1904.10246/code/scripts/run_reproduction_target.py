#!/usr/bin/env python3
"""Guarded, one-target-at-a-time reproduction runner for 1904.10246."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Iterable

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.amplitude_estimation import (  # noqa: E402
    PAPER_AMPLITUDES,
    PAPER_FIG2_REPETITIONS,
    PAPER_FIG2_SHOTS,
    PAPER_PERCENTILE,
    PAPER_RESOURCE_REFERENCE,
    SchedulePoint,
    classical_curve,
    complexity_rows,
    conventional_qae_error,
    eis_schedule,
    fitted_log_slope,
    lis_schedule,
    resource_rows,
    simulate_schedule_curve,
)


TARGETS = {"T_FIG2", "T_TABLE1", "T_TABLE2", "T_FIGA"}


def _ensure_guard(target_id: str) -> None:
    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE")
    if guarded_target != target_id:
        raise SystemExit(
            f"guard mismatch: --target-id={target_id!r}, "
            f"PRAGENT_GUARDED_TARGET_ID={guarded_target!r}"
        )
    if guarded_stage != "final_reproduction":
        raise SystemExit(
            "paper-facing outputs require PRAGENT_GUARDED_STAGE=final_reproduction"
        )


def _output_paths(target_id: str) -> dict[str, Path]:
    names = {
        "T_FIG2": (
            "fig2_error_curves.csv",
            "fig2_error_curves.png",
            "fig2_scientific_checks.json",
        ),
        "T_TABLE1": (
            "table1_complexities.csv",
            "table1_complexities.png",
            "table1_scientific_checks.json",
        ),
        "T_TABLE2": (
            "table2_resource_counts.csv",
            "table2_resource_counts.png",
            "table2_scientific_checks.json",
        ),
        "T_FIGA": (
            "figa_percentile_curves.csv",
            "figa_percentile_curves.png",
            "figa_scientific_checks.json",
        ),
    }
    data_name, figure_name, check_name = names[target_id]
    return {
        "data": WORKSPACE / "outputs" / "data" / data_name,
        "figure": WORKSPACE / "outputs" / "figures" / figure_name,
        "check": WORKSPACE / "outputs" / "checks" / check_name,
    }


def _prepare_matplotlib(target_id: str) -> Any:
    cache = WORKSPACE / "outputs" / "cache" / target_id
    cache.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(cache)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 8,
            "axes.linewidth": 1.0,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "savefig.facecolor": "white",
        }
    )
    return plt


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write an empty data file")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_check(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _point_rows(
    *,
    target_id: str,
    panel_label: str,
    a: float,
    schedule_name: str,
    simulation_series: str,
    bound_series: str,
    points: Iterable[SchedulePoint],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for point in points:
        rows.append(
            {
                "target_id": target_id,
                "panel": panel_label,
                "a": f"{a:.16g}",
                "series_id": simulation_series,
                "schedule": schedule_name,
                "stage_M": point.stage,
                "n_query": point.n_query,
                "error": f"{point.error:.16g}",
                "evidence_kind": "independent_numerics",
            }
        )
        rows.append(
            {
                "target_id": target_id,
                "panel": panel_label,
                "a": f"{a:.16g}",
                "series_id": bound_series,
                "schedule": schedule_name,
                "stage_M": point.stage,
                "n_query": point.n_query,
                "error": f"{point.cramer_rao:.16g}",
                "evidence_kind": "analytic_reference",
            }
        )
    return rows


def run_fig2(paths: dict[str, Path]) -> dict[str, Any]:
    started = time.perf_counter()
    base_seed = 190410246
    lis = lis_schedule(31)
    eis = eis_schedule(9)
    lis_query_grid = [PAPER_FIG2_SHOTS * (stage + 1) ** 2 for stage in range(32)]
    panel_fraction_labels = {
        2 / 3: "2/3",
        1 / 3: "1/3",
        1 / 6: "1/6",
        1 / 12: "1/12",
        1 / 24: "1/24",
        1 / 48: "1/48",
    }
    all_rows: list[dict[str, Any]] = []
    plot_data: dict[float, dict[str, list[SchedulePoint]]] = {}
    slope_checks: dict[str, float] = {}

    for panel_index, a in enumerate(PAPER_AMPLITUDES):
        seed_sequence = np.random.SeedSequence([base_seed, panel_index])
        lis_seed, eis_seed, classical_seed = seed_sequence.spawn(3)
        lis_points = simulate_schedule_curve(
            a=a,
            schedule=lis,
            shots=PAPER_FIG2_SHOTS,
            repetitions=PAPER_FIG2_REPETITIONS,
            rng=np.random.default_rng(lis_seed),
            grid_size=32769,
            statistic="rmse",
        )
        eis_points = simulate_schedule_curve(
            a=a,
            schedule=eis,
            shots=PAPER_FIG2_SHOTS,
            repetitions=PAPER_FIG2_REPETITIONS,
            rng=np.random.default_rng(eis_seed),
            grid_size=65537,
            statistic="rmse",
        )
        classical_points = classical_curve(
            a=a,
            query_counts=lis_query_grid,
            repetitions=PAPER_FIG2_REPETITIONS,
            rng=np.random.default_rng(classical_seed),
            statistic="rmse",
        )
        panel_label = f"a={panel_fraction_labels[a]}"
        all_rows.extend(
            _point_rows(
                target_id="T_FIG2",
                panel_label=panel_label,
                a=a,
                schedule_name="Classical",
                simulation_series="CLASSICAL_SIM",
                bound_series="CLASSICAL_CRB",
                points=classical_points,
            )
        )
        all_rows.extend(
            _point_rows(
                target_id="T_FIG2",
                panel_label=panel_label,
                a=a,
                schedule_name="LIS",
                simulation_series="LIS_SIM",
                bound_series="LIS_CRB",
                points=lis_points,
            )
        )
        all_rows.extend(
            _point_rows(
                target_id="T_FIG2",
                panel_label=panel_label,
                a=a,
                schedule_name="EIS",
                simulation_series="EIS_SIM",
                bound_series="EIS_CRB",
                points=eis_points,
            )
        )
        plot_data[a] = {
            "classical": classical_points,
            "lis": lis_points,
            "eis": eis_points,
        }
        if math.isclose(a, 1 / 48):
            slope_checks = {
                "classical": fitted_log_slope(classical_points, 1e3, 1e5),
                "lis": fitted_log_slope(lis_points, 1e3, 1e5),
                "eis": fitted_log_slope(eis_points, 1e3, 1.1e5),
            }

    _write_csv(paths["data"], all_rows)
    _render_fig2(paths["figure"], plot_data, panel_fraction_labels)

    reported = {"classical": -0.50, "lis": -0.76, "eis": -0.95}
    tolerances = {"classical": 0.07, "lis": 0.13, "eis": 0.13}
    assertions = [
        {
            "assertion_id": f"FIG2_SLOPE_{name.upper()}",
            "tier": "numeric",
            "essential": True,
            "status": (
                "passed"
                if abs(slope_checks[name] - reported[name]) <= tolerances[name]
                else "failed"
            ),
            "observed": slope_checks[name],
            "expected": reported[name],
            "tolerance": tolerances[name],
            "claim": f"The a=1/48 {name} log-log error slope matches the paper.",
        }
        for name in ("classical", "lis", "eis")
    ]
    final_panel = plot_data[1 / 48]
    assertions.extend(
        [
            {
                "assertion_id": "FIG2_EIS_BEATS_CLASSICAL",
                "tier": "numeric",
                "essential": True,
                "status": (
                    "passed"
                    if final_panel["eis"][-1].error < final_panel["classical"][-1].error
                    else "failed"
                ),
                "observed": final_panel["eis"][-1].error / final_panel["classical"][-1].error,
                "expected": "ratio < 1",
                "claim": "EIS beats classical sampling at the high-query end.",
            },
            {
                "assertion_id": "FIG2_LIS_EXACT_QUERY_SUM",
                "tier": "analytic",
                "essential": True,
                "status": (
                    "passed"
                    if all(point.n_query == 100 * (point.stage + 1) ** 2 for point in final_panel["lis"])
                    else "failed"
                ),
                "observed": final_panel["lis"][-1].n_query,
                "expected": 102400,
                "claim": "The LIS query axis obeys N_shot(M+1)^2.",
            },
        ]
    )
    status = "passed" if all(item["status"] == "passed" for item in assertions) else "failed"
    payload = {
        "schema_version": 1,
        "paper_id": "1904.10246",
        "target_id": "T_FIG2",
        "status": status,
        "artifact_stage": "final_reproduction",
        "generated_data_provenance": "independent_numerics",
        "parameters": {
            "a_values": [panel_fraction_labels[a] for a in PAPER_AMPLITUDES],
            "N_shot": PAPER_FIG2_SHOTS,
            "repetitions": PAPER_FIG2_REPETITIONS,
            "lis_M": [0, 31],
            "eis_M": [0, 9],
            "seed": base_seed,
            "mle_domain": [0, "pi/2"],
        },
        "reference_contract": {
            "reported_slopes_at_a_1_over_48": reported,
            "analytic_bounds": "Eqs. (10)-(13)",
            "author_seed_available": False,
        },
        "summary": {
            "rows": len(all_rows),
            "panels": 6,
            "runtime_seconds": time.perf_counter() - started,
            "fitted_slopes": slope_checks,
        },
        "physics_assertions": assertions,
        "outputs": {
            "data": str(paths["data"].relative_to(WORKSPACE)),
            "figure": str(paths["figure"].relative_to(WORKSPACE)),
        },
    }
    _write_check(paths["check"], payload)
    return payload


def _render_fig2(
    path: Path,
    plot_data: dict[float, dict[str, list[SchedulePoint]]],
    labels: dict[float, str],
) -> None:
    plt = _prepare_matplotlib("T_FIG2")
    figure, axes = plt.subplots(3, 2, figsize=(7.65, 8.80), dpi=100)
    panel_order = (2 / 3, 1 / 12, 1 / 3, 1 / 24, 1 / 6, 1 / 48)
    for axis, a in zip(axes.flat, panel_order):
        panel = plot_data[a]
        styles = {
            "classical": ("#3569c8", "s", "--"),
            "lis": ("#f05050", "^", ":"),
            "eis": ("#202020", "o", "-"),
        }
        for name in ("classical", "lis", "eis"):
            points = panel[name]
            x = [point.n_query for point in points]
            error = [point.error for point in points]
            bound = [point.cramer_rao for point in points]
            color, marker, line_style = styles[name]
            axis.plot(x, bound, linestyle=line_style, color=color, linewidth=1.2, zorder=1)
            axis.plot(
                x,
                error,
                linestyle="none",
                marker=marker,
                markerfacecolor="none",
                markeredgecolor=color,
                markeredgewidth=0.7,
                markersize=3.4,
                zorder=2,
            )
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlim(1e2, 1e5)
        axis.set_ylim(1e-5, 1e-1)
        axis.set_xlabel("Number of queries")
        axis.set_ylabel("Error")
        axis.text(
            0.96,
            0.95,
            f"$a={labels[a]}$",
            transform=axis.transAxes,
            ha="right",
            va="top",
            bbox={"boxstyle": "square,pad=0.18", "facecolor": "white", "edgecolor": "black"},
        )
        axis.tick_params(which="both", width=0.8, length=3)
        axis.tick_params(which="minor", length=2)
    figure.subplots_adjust(left=0.105, right=0.985, bottom=0.065, top=0.965, wspace=0.27, hspace=0.31)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=100, metadata={"Software": "PRAgent independent reproduction"})
    plt.close(figure)


def run_table1(paths: dict[str, Path]) -> dict[str, Any]:
    started = time.perf_counter()
    rows = complexity_rows()
    _write_csv(paths["data"], rows)
    expected = [
        ("O(epsilon^-2)", "O(epsilon^-2)"),
        ("O(epsilon^-4/3)", "O(epsilon^-5/3)"),
        ("O(epsilon^-1)", "O(epsilon^-1 log(epsilon^-1))"),
    ]
    observed = [(row["query_complexity"], row["postprocessing_complexity"]) for row in rows]
    assertion = {
        "assertion_id": "TABLE1_ALL_COMPLEXITIES_EXACT",
        "tier": "analytic",
        "essential": True,
        "status": "passed" if observed == expected else "failed",
        "observed": observed,
        "expected": expected,
        "claim": "All six asymptotic complexity entries equal Table 1.",
    }
    _render_table1(paths["figure"], rows)
    payload = {
        "schema_version": 1,
        "paper_id": "1904.10246",
        "target_id": "T_TABLE1",
        "status": assertion["status"],
        "artifact_stage": "final_reproduction",
        "generated_data_provenance": "analytic_reference",
        "parameters": {
            "methods": ["Classical", "LIS", "EIS"],
            "asymptotic_variable": "epsilon",
        },
        "summary": {
            "rows": 3,
            "numeric_cells_checked": 6,
            "runtime_seconds": time.perf_counter() - started,
        },
        "physics_assertions": [assertion],
        "outputs": {
            "data": str(paths["data"].relative_to(WORKSPACE)),
            "figure": str(paths["figure"].relative_to(WORKSPACE)),
        },
    }
    _write_check(paths["check"], payload)
    return payload


def _render_table1(path: Path, rows: list[dict[str, str]]) -> None:
    plt = _prepare_matplotlib("T_TABLE1")
    figure, axis = plt.subplots(figsize=(8.8, 2.35), dpi=100)
    figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
    axis.axis("off")
    axis.text(
        0.0,
        0.95,
        "Table 1  The summary of the complexities for estimating target value with given error $\\epsilon$.\n"
        "The query complexity and computational complexity of post-processing are listed.",
        ha="left",
        va="top",
        fontsize=7.2,
    )
    cell_text = [
        ["Classical\n($m_k=0\\ \\forall k$)", "$\\mathcal{O}(\\epsilon^{-2})$", "$\\mathcal{O}(\\epsilon^{-2})$"],
        [
            "Linearly incremental sequence (LIS)\n($m_0=0,m_1=1,\\ldots,m_M=M$)",
            "$\\mathcal{O}(\\epsilon^{-4/3})$",
            "$\\mathcal{O}(\\epsilon^{-5/3})$",
        ],
        [
            "Exponentially incremental sequence (EIS)\n($m_0=0,m_1=2^0,\\ldots,m_M=2^{M-1}$)",
            "$\\mathcal{O}(\\epsilon^{-1})$",
            "$\\mathcal{O}(\\epsilon^{-1}\\ln\\epsilon^{-1})$",
        ],
    ]
    table = axis.table(
        cellText=cell_text,
        colLabels=[
            "update rule of $m_k$",
            "query complexity",
            "computational complexity of\npost-processing",
        ],
        cellLoc="center",
        colLoc="center",
        bbox=[0.10, 0.035, 0.79, 0.69],
        colWidths=[0.50, 0.22, 0.28],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6.8)
    last_row = len(rows)
    for (row, _column), cell in table.get_celld().items():
        cell.set_facecolor("white")
        cell.set_edgecolor("black")
        cell.set_linewidth(0.7)
        if row == 0:
            cell.visible_edges = "TB"
        elif row == last_row:
            cell.visible_edges = "B"
        else:
            cell.visible_edges = ""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=100, metadata={"Software": "PRAgent independent reproduction"})
    plt.close(figure)


def run_table2(paths: dict[str, Path]) -> dict[str, Any]:
    started = time.perf_counter()
    generated = resource_rows()
    rows = [
        {
            key: ("" if value is None else value)
            for key, value in row.items()
        }
        for row in generated
    ]
    _write_csv(paths["data"], rows)
    observed = tuple(
        (
            int(row["q_operators"]),
            row["conventional_cnot"],
            row["conventional_qubits"],
            int(row["proposed_cnot"]),
            int(row["proposed_qubits"]),
        )
        for row in generated
    )
    ratios = [
        float(row["conventional_cnot"]) / float(row["proposed_cnot"])
        for row in generated[1:]
    ]
    assertions = [
        {
            "assertion_id": "TABLE2_ALL_CELLS_EXACT",
            "tier": "numeric",
            "essential": True,
            "status": "passed" if observed == PAPER_RESOURCE_REFERENCE else "failed",
            "observed": observed,
            "expected": PAPER_RESOURCE_REFERENCE,
            "claim": "All 37 published numeric resource cells are exact.",
        },
        {
            "assertion_id": "TABLE2_CONSTANT_PROPOSED_QUBITS",
            "tier": "analytic",
            "essential": True,
            "status": "passed" if all(row["proposed_qubits"] == 3 for row in generated) else "failed",
            "observed": [row["proposed_qubits"] for row in generated],
            "expected": 3,
            "claim": "The proposed method keeps a constant three-qubit footprint.",
        },
        {
            "assertion_id": "TABLE2_CNOT_REDUCTION",
            "tier": "numeric",
            "essential": True,
            "status": "passed" if min(ratios) > 7.0 and max(ratios) < 19.0 else "failed",
            "observed": {"minimum_ratio": min(ratios), "maximum_ratio": max(ratios)},
            "expected": "7 < conventional/proposed < 19",
            "claim": "The CNOT reduction agrees with the reported about 7-18 times range.",
        },
    ]
    _render_table2(paths["figure"], generated)
    status = "passed" if all(item["status"] == "passed" for item in assertions) else "failed"
    payload = {
        "schema_version": 1,
        "paper_id": "1904.10246",
        "target_id": "T_TABLE2",
        "status": status,
        "artifact_stage": "final_reproduction",
        "generated_data_provenance": "analytic_reference",
        "parameters": {
            "n": 2,
            "b_max": "pi/4",
            "connectivity": "all_to_all",
            "gate_set": "Qiskit 0.7 frozen convention",
        },
        "summary": {
            "rows": 10,
            "numeric_cells_checked": 37,
            "runtime_seconds": time.perf_counter() - started,
        },
        "physics_assertions": assertions,
        "outputs": {
            "data": str(paths["data"].relative_to(WORKSPACE)),
            "figure": str(paths["figure"].relative_to(WORKSPACE)),
        },
    }
    _write_check(paths["check"], payload)
    return payload


def _render_table2(path: Path, rows: list[dict[str, int | None]]) -> None:
    plt = _prepare_matplotlib("T_TABLE2")
    figure, axis = plt.subplots(figsize=(8.3, 3.0), dpi=100)
    figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
    axis.axis("off")
    axis.text(
        0.0,
        0.94,
        "Table 2  Number of CNOT gates and qubits to calculate the sine integral as a function of $\\mathbf{Q}$ operations.",
        ha="left",
        va="top",
        fontsize=7.2,
    )
    cell_text = []
    for row_index, row in enumerate(rows):
        q_label: Any = row["q_operators"] if row_index == 0 else f"$2^{{{row_index - 1}}}$"
        cell_text.append(
          [
            q_label,
            "-" if row["conventional_cnot"] is None else row["conventional_cnot"],
            "-" if row["conventional_qubits"] is None else row["conventional_qubits"],
            row["proposed_cnot"],
            row["proposed_qubits"],
          ]
        )
    axis.text(0.455, 0.80, "conventional amplitude estimation", ha="center", va="center", fontsize=6.8)
    axis.text(0.742, 0.80, "our algorithm", ha="center", va="center", fontsize=6.8)
    table = axis.table(
        cellText=cell_text,
        colLabels=[
            "# operators Q",
            "# CNOT gates",
            "# qubits",
            "# CNOT gates",
            "# qubits",
        ],
        cellLoc="center",
        colLoc="center",
        bbox=[0.18, 0.01, 0.69, 0.74],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6.6)
    last_row = len(rows)
    for (row, _column), cell in table.get_celld().items():
        cell.set_facecolor("white")
        cell.set_edgecolor("black")
        cell.set_linewidth(0.65)
        if row == 0:
            cell.visible_edges = "TB"
        elif row == last_row:
            cell.visible_edges = "B"
        else:
            cell.visible_edges = ""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=100, metadata={"Software": "PRAgent independent reproduction"})
    plt.close(figure)


def run_figa(paths: dict[str, Path]) -> dict[str, Any]:
    started = time.perf_counter()
    a = 1 / 48
    base_seed = 190410247
    series: dict[str, list[SchedulePoint]] = {}

    schedule_30 = eis_schedule(10)
    schedule_100 = eis_schedule(9)
    seed_30, seed_100, seed_classical = np.random.SeedSequence(base_seed).spawn(3)
    points_30_all = simulate_schedule_curve(
        a=a,
        schedule=schedule_30,
        shots=30,
        repetitions=1000,
        rng=np.random.default_rng(seed_30),
        grid_size=131073,
        statistic="percentile",
        percentile=PAPER_PERCENTILE,
    )
    points_100_all = simulate_schedule_curve(
        a=a,
        schedule=schedule_100,
        shots=100,
        repetitions=1000,
        rng=np.random.default_rng(seed_100),
        grid_size=65537,
        statistic="percentile",
        percentile=PAPER_PERCENTILE,
    )
    points_30 = [point for point in points_30_all if 100 <= point.n_query <= 110000]
    points_100 = [point for point in points_100_all if 100 <= point.n_query <= 110000]
    conventional = [
        SchedulePoint(stage=phase_bits, n_query=n_query, error=error, cramer_rao=math.nan)
        for phase_bits in range(7, 18)
        for n_query, error in [conventional_qae_error(a, phase_bits)]
        if n_query <= 110000
    ]
    classical_queries = np.unique(np.rint(np.logspace(2, 5, 32)).astype(int)).tolist()
    classical = classical_curve(
        a=a,
        query_counts=classical_queries,
        repetitions=1000,
        rng=np.random.default_rng(seed_classical),
        statistic="percentile",
        percentile=PAPER_PERCENTILE,
    )
    series.update(
        {
            "EIS_N30": points_30,
            "EIS_N100": points_100,
            "CONVENTIONAL_QAE": conventional,
            "CLASSICAL": classical,
        }
    )

    rows: list[dict[str, Any]] = []
    for series_id, points in series.items():
        for point in points:
            rows.append(
                {
                    "target_id": "T_FIGA",
                    "a": "1/48",
                    "series_id": series_id,
                    "stage": point.stage,
                    "n_query": point.n_query,
                    "error_percentile": f"{point.error:.16g}",
                    "percentile": f"{PAPER_PERCENTILE:.16g}",
                    "evidence_kind": (
                        "analytic_reference"
                        if series_id == "CONVENTIONAL_QAE"
                        else "independent_numerics"
                    ),
                }
            )
    _write_csv(paths["data"], rows)
    _render_figa(paths["figure"], series)

    conventional_x = np.log([point.n_query for point in conventional])
    conventional_y = np.log([point.error for point in conventional])

    def comparable_ratios(points: list[SchedulePoint]) -> list[float]:
        ratios: list[float] = []
        for point in points:
            if conventional[0].n_query <= point.n_query <= conventional[-1].n_query:
                reference = float(np.exp(np.interp(math.log(point.n_query), conventional_x, conventional_y)))
                ratios.append(point.error / reference)
        return ratios

    ratios_30 = comparable_ratios(points_30)
    ratios_100 = comparable_ratios(points_100)
    classical_slope = fitted_log_slope(classical, 1e2, 1e5)
    assertions = [
        {
            "assertion_id": "FIGA_CONVENTIONAL_DECREASES",
            "tier": "analytic",
            "essential": True,
            "status": (
                "passed"
                if all(
                    later.error < earlier.error
                    for earlier, later in zip(conventional, conventional[1:])
                )
                else "failed"
            ),
            "observed": [conventional[0].error, conventional[-1].error],
            "expected": "strict decrease",
            "claim": "Conventional-QAE phase-grid error decreases with query count.",
        },
        {
            "assertion_id": "FIGA_EIS30_COMPARABLE",
            "tier": "numeric",
            "essential": True,
            "status": (
                "passed"
                if ratios_30 and 0.25 <= float(np.median(ratios_30)) <= 4.0
                else "failed"
            ),
            "observed": float(np.median(ratios_30)) if ratios_30 else None,
            "expected": "median EIS30/conventional ratio in [0.25, 4]",
            "claim": "EIS with N_shot=30 is comparable to conventional QAE.",
        },
        {
            "assertion_id": "FIGA_SMALLER_SHOT_ADVANTAGE",
            "tier": "numeric",
            "essential": True,
            "status": (
                "passed"
                if ratios_30 and ratios_100 and np.median(ratios_30) < np.median(ratios_100)
                else "failed"
            ),
            "observed": {
                "median_N30_ratio": float(np.median(ratios_30)) if ratios_30 else None,
                "median_N100_ratio": float(np.median(ratios_100)) if ratios_100 else None,
            },
            "expected": "N30 ratio < N100 ratio",
            "claim": "At fixed query scale, fewer shots allocate more queries to amplification.",
        },
        {
            "assertion_id": "FIGA_CLASSICAL_SLOPE",
            "tier": "numeric",
            "essential": True,
            "status": "passed" if abs(classical_slope + 0.5) <= 0.08 else "failed",
            "observed": classical_slope,
            "expected": -0.5,
            "tolerance": 0.08,
            "claim": "The classical percentile error follows N_q^-1/2.",
        },
    ]
    status = "passed" if all(item["status"] == "passed" for item in assertions) else "failed"
    payload = {
        "schema_version": 1,
        "paper_id": "1904.10246",
        "target_id": "T_FIGA",
        "status": status,
        "artifact_stage": "final_reproduction",
        "generated_data_provenance": "independent_numerics",
        "parameters": {
            "a": "1/48",
            "N_shot": [30, 100],
            "repetitions": 1000,
            "percentile": PAPER_PERCENTILE,
            "seed": base_seed,
        },
        "summary": {
            "rows": len(rows),
            "runtime_seconds": time.perf_counter() - started,
            "classical_slope": classical_slope,
            "median_EIS30_to_conventional": float(np.median(ratios_30)),
            "median_EIS100_to_conventional": float(np.median(ratios_100)),
        },
        "physics_assertions": assertions,
        "outputs": {
            "data": str(paths["data"].relative_to(WORKSPACE)),
            "figure": str(paths["figure"].relative_to(WORKSPACE)),
        },
    }
    _write_check(paths["check"], payload)
    return payload


def _render_figa(path: Path, series: dict[str, list[SchedulePoint]]) -> None:
    plt = _prepare_matplotlib("T_FIGA")
    figure, axis = plt.subplots(figsize=(3.90, 3.40), dpi=100)
    styles = {
        "CONVENTIONAL_QAE": ("#202020", "o", "conventional"),
        "EIS_N30": ("#f05050", "^", "$N_{shot}=30$"),
        "EIS_N100": ("#3569c8", "s", "$N_{shot}=100$"),
        "CLASSICAL": ("#58b927", "x", "classical"),
    }
    for series_id in ("CONVENTIONAL_QAE", "EIS_N30", "EIS_N100", "CLASSICAL"):
        points = series[series_id]
        color, marker, label = styles[series_id]
        axis.plot(
            [point.n_query for point in points],
            [point.error for point in points],
            linestyle="none",
            marker=marker,
            markerfacecolor="none",
            markeredgecolor=color,
            color=color,
            markeredgewidth=0.7,
            markersize=4.0,
            label=label,
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlim(1e2, 1.3e5)
    axis.set_ylim(1e-5, 1e-1)
    axis.set_xlabel("Number of queries")
    axis.set_ylabel("Error")
    axis.legend(loc="upper right", fontsize=6.2, frameon=True, fancybox=False, framealpha=1)
    axis.tick_params(which="both", width=0.8, length=3)
    axis.tick_params(which="minor", length=2)
    figure.subplots_adjust(left=0.17, right=0.97, bottom=0.17, top=0.96)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=100, metadata={"Software": "PRAgent independent reproduction"})
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-id", required=True, choices=sorted(TARGETS))
    args = parser.parse_args()
    _ensure_guard(args.target_id)
    paths = _output_paths(args.target_id)
    runners = {
        "T_FIG2": run_fig2,
        "T_TABLE1": run_table1,
        "T_TABLE2": run_table2,
        "T_FIGA": run_figa,
    }
    payload = runners[args.target_id](paths)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
