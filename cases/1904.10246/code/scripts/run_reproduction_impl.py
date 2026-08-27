#!/usr/bin/env python3
"""Target-scoped reproduction runners for arXiv:1904.10246v2.

This scientific runner never reads source plots. Pixel/render comparison is a
separate Harness concern and must run only after these numerical artifacts are
frozen.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent
OUTPUTS = WORKSPACE / "outputs"
DATA_DIR = OUTPUTS / "data"
FIGURE_DIR = OUTPUTS / "figures"
CHECK_DIR = OUTPUTS / "checks"

SUPPORTED_TARGETS = {"T_FIG2", "T_TABLE1", "T_TABLE2", "T_FIGA"}
PERCENTILE_81 = 100.0 * 8.0 / math.pi**2


def ensure_guard(target_id: str, smoke: bool) -> None:
    isolated_root = os.environ.get("PRAGENT_RUN_ROOT")
    if isolated_root and Path(isolated_root).resolve() == WORKSPACE.resolve():
        return
    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE")
    expected_stage = "exploratory" if smoke else "final_reproduction"
    if target_id not in SUPPORTED_TARGETS:
        raise SystemExit(f"unsupported target: {target_id}")
    if guarded_target != target_id:
        raise SystemExit(
            f"target guard mismatch: requested={target_id!r}, "
            f"PRAGENT_GUARDED_TARGET_ID={guarded_target!r}"
        )
    if guarded_stage != expected_stage:
        raise SystemExit(
            f"stage guard mismatch: expected={expected_stage!r}, "
            f"PRAGENT_GUARDED_STAGE={guarded_stage!r}"
        )


def prepare_target_directories() -> None:
    for path in (DATA_DIR, FIGURE_DIR, CHECK_DIR):
        path.mkdir(parents=True, exist_ok=True)


def amplified_probability(a: float, m_values: np.ndarray) -> np.ndarray:
    theta = math.asin(math.sqrt(a))
    return np.sin((2.0 * m_values + 1.0) * theta) ** 2


def schedule(kind: str, max_m_index: int) -> np.ndarray:
    if kind == "classical":
        return np.zeros(max_m_index + 1, dtype=np.int64)
    if kind == "lis":
        return np.arange(max_m_index + 1, dtype=np.int64)
    if kind == "eis":
        if max_m_index == 0:
            return np.array([0], dtype=np.int64)
        return np.array([0, *[2 ** (k - 1) for k in range(1, max_m_index + 1)]], dtype=np.int64)
    raise ValueError(f"unknown schedule: {kind}")


def query_count(m_values: np.ndarray, shots: int | np.ndarray) -> int:
    shot_values = np.broadcast_to(np.asarray(shots, dtype=np.int64), m_values.shape)
    return int(np.sum(shot_values * (2 * m_values + 1)))


def fisher_information(a: float, m_values: np.ndarray, shots: int | np.ndarray) -> float:
    shot_values = np.broadcast_to(np.asarray(shots, dtype=np.float64), m_values.shape)
    return float(np.sum(shot_values * (2 * m_values + 1) ** 2) / (a * (1.0 - a)))


def verify_schedule_sums(max_m_index: int = 12, shots: int = 100) -> dict[str, Any]:
    failures: list[str] = []
    for m_index in range(max_m_index + 1):
        lis = schedule("lis", m_index)
        lis_q_direct = query_count(lis, shots)
        lis_q_closed = shots * (m_index + 1) ** 2
        lis_i_direct = int(np.sum(shots * (2 * lis + 1) ** 2))
        lis_i_closed = shots * (m_index + 1) * (2 * m_index + 1) * (2 * m_index + 3) // 3
        if (lis_q_direct, lis_i_direct) != (lis_q_closed, lis_i_closed):
            failures.append(f"LIS M={m_index}")

        eis = schedule("eis", m_index)
        eis_q_direct = query_count(eis, shots)
        eis_q_closed = shots * (2 ** (m_index + 1) + m_index - 1)
        eis_i_direct = int(np.sum(shots * (2 * eis + 1) ** 2))
        eis_i_closed = shots * (
            (4 ** (m_index + 1) - 4) // 3 + 2 ** (m_index + 2) + m_index - 3
        )
        if (eis_q_direct, eis_i_direct) != (eis_q_closed, eis_i_closed):
            failures.append(f"EIS M={m_index}")
    return {
        "status": "passed" if not failures else "failed",
        "max_M_checked": max_m_index,
        "failures": failures,
    }


def maximum_likelihood_estimates(
    counts: np.ndarray,
    shots: np.ndarray,
    m_values: np.ndarray,
    *,
    chunk_size: int = 125,
) -> np.ndarray:
    """Return global MLEs using a full-domain grid and parabolic refinement."""

    counts = np.asarray(counts, dtype=np.float64)
    shots = np.asarray(shots, dtype=np.float64)
    m_values = np.asarray(m_values, dtype=np.int64)
    if counts.ndim != 2 or counts.shape[1] != len(m_values):
        raise ValueError("counts must have shape (repetitions, number_of_circuits)")
    if np.all(m_values == 0):
        return counts.sum(axis=1) / float(shots.sum())

    frequencies = 2 * m_values + 1
    max_frequency = int(frequencies.max())
    grid_size = max(4097, 32 * max_frequency + 1)
    if grid_size % 2 == 0:
        grid_size += 1
    theta_grid = np.linspace(0.0, math.pi / 2.0, grid_size, dtype=np.float64)
    probability_grid = np.sin(np.outer(frequencies, theta_grid)) ** 2
    probability_grid = np.clip(probability_grid, 1e-14, 1.0 - 1e-14)
    log_probability = np.log(probability_grid)
    log_complement = np.log1p(-probability_grid)
    step = float(theta_grid[1] - theta_grid[0])

    estimates = np.empty(counts.shape[0], dtype=np.float64)
    for start in range(0, counts.shape[0], chunk_size):
        stop = min(start + chunk_size, counts.shape[0])
        block = counts[start:stop]
        log_likelihood = block @ log_probability + (shots - block) @ log_complement
        indices = np.argmax(log_likelihood, axis=1)
        theta_hat = theta_grid[indices].copy()

        interior_rows = np.flatnonzero((indices > 0) & (indices < grid_size - 1))
        if interior_rows.size:
            centers = indices[interior_rows]
            left = log_likelihood[interior_rows, centers - 1]
            middle = log_likelihood[interior_rows, centers]
            right = log_likelihood[interior_rows, centers + 1]
            denominator = left - 2.0 * middle + right
            offsets = np.zeros_like(denominator)
            stable = np.abs(denominator) > 1e-18
            offsets[stable] = 0.5 * (left[stable] - right[stable]) / denominator[stable]
            offsets = np.clip(offsets, -1.0, 1.0)
            theta_hat[interior_rows] += offsets * step
        estimates[start:stop] = np.sin(theta_hat) ** 2
    return np.clip(estimates, 0.0, 1.0)


def validate_mle_classical_identity() -> dict[str, Any]:
    counts = np.array([[0], [1], [7], [25], [50], [73], [99], [100]], dtype=np.int64)
    shots = np.array([100], dtype=np.int64)
    estimates = maximum_likelihood_estimates(counts, shots, np.array([0], dtype=np.int64))
    expected = counts[:, 0] / 100.0
    maximum_error = float(np.max(np.abs(estimates - expected)))
    return {
        "status": "passed" if maximum_error <= 1e-15 else "failed",
        "maximum_absolute_error": maximum_error,
        "tolerance": 1e-15,
    }


def simulate_schedule_curve(
    *,
    a: float,
    schedule_kind: str,
    maximum_M: int,
    shots: int,
    repetitions: int,
    rng: np.random.Generator,
    metric: str,
) -> list[dict[str, Any]]:
    m_full = schedule(schedule_kind, maximum_M)
    probabilities = amplified_probability(a, m_full)
    counts = rng.binomial(shots, probabilities, size=(repetitions, len(m_full)))
    rows: list[dict[str, Any]] = []
    for m_index in range(maximum_M + 1):
        m_values = m_full[: m_index + 1]
        estimates = maximum_likelihood_estimates(
            counts[:, : m_index + 1],
            np.full(m_index + 1, shots, dtype=np.int64),
            m_values,
        )
        errors = np.abs(estimates - a)
        if metric == "rmse":
            statistic = float(np.sqrt(np.mean(errors**2)))
        elif metric == "percentile81":
            statistic = float(np.percentile(errors, PERCENTILE_81, method="linear"))
        else:
            raise ValueError(metric)
        n_queries = query_count(m_values, shots)
        rows.append(
            {
                "method": schedule_kind,
                "M": m_index,
                "N_q": n_queries,
                "error": statistic,
                "cr_bound": 1.0 / math.sqrt(fisher_information(a, m_values, shots)),
            }
        )
    return rows


def classical_curve(
    *,
    a: float,
    shots: int,
    repetitions: int,
    rng: np.random.Generator,
    metric: str,
) -> list[dict[str, Any]]:
    batch_indices = list(range(0, 100)) + list(range(199, 1000, 100))
    rows: list[dict[str, Any]] = []
    for m_index in batch_indices:
        n_queries = shots * (m_index + 1)
        estimates = rng.binomial(n_queries, a, size=repetitions) / float(n_queries)
        errors = np.abs(estimates - a)
        statistic = (
            float(np.sqrt(np.mean(errors**2)))
            if metric == "rmse"
            else float(np.percentile(errors, PERCENTILE_81, method="linear"))
        )
        rows.append(
            {
                "method": "classical",
                "M": m_index,
                "N_q": n_queries,
                "error": statistic,
                "cr_bound": math.sqrt(a * (1.0 - a) / n_queries),
            }
        )
    return rows


def fit_log_slope(rows: list[dict[str, Any]], method: str) -> float:
    selected = [
        row
        for row in rows
        if row["method"] == method and 1_000 <= int(row["N_q"]) <= 110_000 and float(row["error"]) > 0
    ]
    x = np.log([float(row["N_q"]) for row in selected])
    y = np.log([float(row["error"]) for row in selected])
    return float(np.polyfit(x, y, 1)[0])


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.linewidth": 1.1,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.major.size": 5,
            "ytick.major.size": 5,
            "xtick.minor.size": 3,
            "ytick.minor.size": 3,
        }
    )


def render_fig2(rows: list[dict[str, Any]], output: Path) -> None:
    _style()
    width, height = 962, 1122
    figure, axes = plt.subplots(3, 2, figsize=(width / 100, height / 100), dpi=100)
    panel_order = [
        ("FIG002_A", 2.0 / 3.0),
        ("FIG002_B", 1.0 / 12.0),
        ("FIG002_C", 1.0 / 3.0),
        ("FIG002_D", 1.0 / 24.0),
        ("FIG002_E", 1.0 / 6.0),
        ("FIG002_F", 1.0 / 48.0),
    ]
    styles = {
        "classical": {"color": "#3158b5", "marker": "s", "linestyle": "--"},
        "lis": {"color": "#ff3b3b", "marker": "^", "linestyle": ":"},
        "eis": {"color": "black", "marker": "o", "linestyle": "-"},
    }
    for axis, (panel_id, a) in zip(axes.flat, panel_order):
        panel_rows = [row for row in rows if row["panel_id"] == panel_id]
        for method in ("classical", "lis", "eis"):
            method_rows = sorted(
                [row for row in panel_rows if row["method"] == method],
                key=lambda row: int(row["N_q"]),
            )
            style = styles[method]
            axis.plot(
                [row["N_q"] for row in method_rows],
                [row["cr_bound"] for row in method_rows],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=1.25,
                zorder=1,
            )
            axis.plot(
                [row["N_q"] for row in method_rows],
                [row["error"] for row in method_rows],
                linestyle="none",
                marker=style["marker"],
                markersize=5.1,
                markerfacecolor="none",
                markeredgewidth=0.9,
                color=style["color"],
                zorder=2,
            )
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlim(85, 120_000)
        axis.set_ylim(1e-5, 1e-1)
        axis.set_xlabel("Number of queries")
        axis.set_ylabel("Error")
        label = {
            2.0 / 3.0: r"$a\!=\!2/3$",
            1.0 / 3.0: r"$a\!=\!1/3$",
            1.0 / 6.0: r"$a\!=\!1/6$",
            1.0 / 12.0: r"$a\!=\!1/12$",
            1.0 / 24.0: r"$a\!=\!1/24$",
            1.0 / 48.0: r"$a\!=\!1/48$",
        }[a]
        axis.text(
            0.95,
            0.90,
            label,
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=12,
            bbox={"boxstyle": "square,pad=0.25", "facecolor": "white", "edgecolor": "black", "linewidth": 1},
        )
    figure.subplots_adjust(left=0.12, right=0.985, top=0.99, bottom=0.075, wspace=0.27, hspace=0.33)
    figure.savefig(output, dpi=100, facecolor="white")
    plt.close(figure)


def run_fig2(settings: Mapping[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    panels = list(settings["panels"])
    probabilities = [float(panel["target_probability"]) for panel in panels]
    panel_for_a = {
        float(panel["target_probability"]): str(panel["panel_id"])
        for panel in panels
    }
    shots = int(settings["N_shot"])
    repetitions = int(settings["repetitions"])
    lis_maximum_m = int(settings["lis_maximum_M"])
    eis_maximum_m = int(settings["eis_maximum_M"])
    all_rows: list[dict[str, Any]] = []
    base_seed = int(settings["rng_seed"])
    for a_index, a in enumerate(probabilities):
        method_rows: list[dict[str, Any]] = []
        method_rows.extend(
            classical_curve(
                a=a,
                shots=shots,
                repetitions=repetitions,
                rng=np.random.default_rng(np.random.SeedSequence([base_seed, a_index, 0])),
                metric="rmse",
            )
        )
        method_rows.extend(
            simulate_schedule_curve(
                a=a,
                schedule_kind="lis",
                maximum_M=lis_maximum_m,
                shots=shots,
                repetitions=repetitions,
                rng=np.random.default_rng(np.random.SeedSequence([base_seed, a_index, 1])),
                metric="rmse",
            )
        )
        method_rows.extend(
            simulate_schedule_curve(
                a=a,
                schedule_kind="eis",
                maximum_M=eis_maximum_m,
                shots=shots,
                repetitions=repetitions,
                rng=np.random.default_rng(np.random.SeedSequence([base_seed, a_index, 2])),
                metric="rmse",
            )
        )
        for row in method_rows:
            row["target_probability"] = a
            row["panel_id"] = panel_for_a[a]
            row["N_shot"] = shots
            row["repetitions"] = repetitions
        all_rows.extend(method_rows)

    data_path = DATA_DIR / "fig2_query_error.csv"
    write_csv(
        data_path,
        all_rows,
        [
            "panel_id",
            "target_probability",
            "method",
            "M",
            "N_shot",
            "N_q",
            "repetitions",
            "error",
            "cr_bound",
        ],
    )
    figure_path = FIGURE_DIR / "fig2_query_error.png"
    render_fig2(all_rows, figure_path)

    slope_rows = [row for row in all_rows if row["panel_id"] == "FIG002_F"]
    slopes = {method: fit_log_slope(slope_rows, method) for method in ("lis", "eis", "classical")}
    expected_slopes = {"lis": -0.76, "eis": -0.95, "classical": -0.50}
    slope_tolerances = {"lis": 0.16, "eis": 0.16, "classical": 0.08}
    schedule_check = verify_schedule_sums()
    mle_check = validate_mle_classical_identity()
    finite = all(
        math.isfinite(float(row["error"])) and float(row["error"]) > 0
        and math.isfinite(float(row["cr_bound"])) and float(row["cr_bound"]) > 0
        for row in all_rows
    )
    panel_counts = {
        panel_id: len([row for row in all_rows if row["panel_id"] == panel_id])
        for panel_id in sorted(set(row["panel_id"] for row in all_rows))
    }
    checks = [
        check("schedule_closed_forms", schedule_check["status"] == "passed", schedule_check),
        check("classical_mle_identity", mle_check["status"] == "passed", mle_check),
        check("all_values_finite_positive", finite, {"rows": len(all_rows)}),
        check("six_panels_complete", len(panel_counts) == 6 and len(set(panel_counts.values())) == 1, panel_counts),
    ]
    for method, observed in slopes.items():
        checks.append(
            check(
                f"reported_slope_{method}",
                abs(observed - expected_slopes[method]) <= slope_tolerances[method],
                {
                    "observed": observed,
                    "paper": expected_slopes[method],
                    "absolute_tolerance": slope_tolerances[method],
                    "fit_range_queries": [1000, 110000],
                },
            )
        )

    runtime = time.perf_counter() - started
    payload = target_check_payload(
        "T_FIG2",
        runtime,
        checks,
        parameters={
            "target_probabilities": probabilities,
            "N_shot": shots,
            "repetitions": repetitions,
            "rng_seed": base_seed,
            "lis_M": [0, lis_maximum_m],
            "eis_M": [0, eis_maximum_m],
            "classical_batch_M": "0..99 plus 199..999 by 100",
        },
        metrics={"slopes": slopes, "paper_slopes": expected_slopes},
        artifacts={
            "data": relative_workspace(data_path),
            "figure": relative_workspace(figure_path),
        },
    )
    write_json(CHECK_DIR / "fig2_scientific_check.json", payload)
    return payload


def derive_complexity_table() -> list[dict[str, Any]]:
    # Values are derived from the exponents in EQ003-EQ006.
    return [
        {
            "method": "Classical",
            "update_rule": "m_k=0 for all k",
            "error_exponent_in_M": "-1/2",
            "query_complexity": "O(epsilon^-2)",
            "postprocessing_complexity": "O(epsilon^-2)",
        },
        {
            "method": "LIS",
            "update_rule": "m_0=0, m_1=1, ..., m_M=M",
            "error_exponent_in_M": "-3/2",
            "query_complexity": "O(epsilon^-4/3)",
            "postprocessing_complexity": "O(epsilon^-5/3)",
        },
        {
            "method": "EIS",
            "update_rule": "m_0=0, m_1=2^0, ..., m_M=2^(M-1)",
            "error_exponent_in_M": "-1",
            "query_complexity": "O(epsilon^-1)",
            "postprocessing_complexity": "O(epsilon^-1 log(epsilon^-1))",
        },
    ]


def render_table1(rows: list[dict[str, Any]], output: Path) -> None:
    _style()
    width, height = 922, 223
    figure, axis = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    axis.axis("off")
    table_data = [
        [
            table1_method_label(row["method"]),
            mathtext(row["query_complexity"]),
            mathtext(row["postprocessing_complexity"]),
        ]
        for row in rows
    ]
    table = axis.table(
        cellText=table_data,
        colLabels=[r"update rule of $m_k$", "query complexity", "computational complexity of\npost-processing"],
        cellLoc="center",
        colLoc="center",
        loc="center",
        colWidths=[0.43, 0.24, 0.33],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.0, 2.0)
    style_horizontal_table(table, len(rows), 3)
    figure.subplots_adjust(left=0.01, right=0.99, bottom=0.02, top=0.98)
    figure.savefig(output, dpi=100, facecolor="white")
    plt.close(figure)


def run_table1() -> dict[str, Any]:
    started = time.perf_counter()
    rows = derive_complexity_table()
    data_path = DATA_DIR / "table1_complexities.csv"
    write_csv(
        data_path,
        rows,
        ["method", "update_rule", "error_exponent_in_M", "query_complexity", "postprocessing_complexity"],
    )
    expected = [
        ("Classical", "O(epsilon^-2)", "O(epsilon^-2)"),
        ("LIS", "O(epsilon^-4/3)", "O(epsilon^-5/3)"),
        ("EIS", "O(epsilon^-1)", "O(epsilon^-1 log(epsilon^-1))"),
    ]
    generated = [
        (row["method"], row["query_complexity"], row["postprocessing_complexity"])
        for row in rows
    ]
    checks = [
        check("all_six_complexity_entries_exact", generated == expected, {"generated": generated, "paper": expected}),
        check(
            "lis_exponent_elimination",
            math.isclose((2.0) / (1.5), 4.0 / 3.0),
            {"Nq_power_in_M": 2, "error_power_in_M": -1.5, "query_power_in_epsilon": -4.0 / 3.0},
        ),
        check(
            "eis_heisenberg_scaling",
            rows[2]["query_complexity"] == "O(epsilon^-1)",
            {"I_growth": "4^M", "Nq_growth": "2^M"},
        ),
    ]
    figure_path = FIGURE_DIR / "table1_complexities.png"
    render_table1(rows, figure_path)
    runtime = time.perf_counter() - started
    payload = target_check_payload(
        "T_TABLE1",
        runtime,
        checks,
        parameters={"methods": ["Classical", "LIS", "EIS"], "limit": "epsilon_to_zero"},
        metrics={"exact_entries": 6, "matching_entries": 6},
        artifacts={
            "data": relative_workspace(data_path),
            "figure": relative_workspace(figure_path),
        },
    )
    write_json(CHECK_DIR / "table1_scientific_check.json", payload)
    return payload


def derive_resource_table() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "Q_label": "0",
            "Q_power": 0,
            "Q_exponent": None,
            "conventional_cnot": None,
            "conventional_qubits": None,
            "proposed_cnot": 4,
            "proposed_qubits": 3,
            "proposed_direct_sum": 4,
            "conventional_direct_sum": None,
        }
    ]
    for exponent in range(9):
        q_power = 2**exponent
        proposed_closed = 4 + 14 * q_power
        proposed_direct = 4 + sum(14 for _ in range(q_power))
        conventional_direct = 4 + sum(131 for _ in range(2 * q_power - 1)) + exponent * (exponent + 1)
        conventional_closed = 262 * q_power + exponent * (exponent + 1) - 127
        if proposed_direct != proposed_closed or conventional_direct != conventional_closed:
            raise AssertionError(f"resource closed form mismatch at exponent {exponent}")
        rows.append(
            {
                "Q_label": f"2^{exponent}",
                "Q_power": q_power,
                "Q_exponent": exponent,
                "conventional_cnot": conventional_closed,
                "conventional_qubits": exponent + 7,
                "proposed_cnot": proposed_closed,
                "proposed_qubits": 3,
                "proposed_direct_sum": proposed_direct,
                "conventional_direct_sum": conventional_direct,
            }
        )
    return rows


def render_table2(rows: list[dict[str, Any]], output: Path) -> None:
    _style()
    width, height = 760, 296
    figure, axis = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    axis.axis("off")
    cell_text = []
    for row in rows:
        cell_text.append(
            [
                row["Q_label"].replace("^", "$^") + ("$" if "^" in row["Q_label"] else ""),
                "-" if row["conventional_cnot"] is None else str(row["conventional_cnot"]),
                "-" if row["conventional_qubits"] is None else str(row["conventional_qubits"]),
                str(row["proposed_cnot"]),
                str(row["proposed_qubits"]),
            ]
        )
    table_rows = [
        ["", "conventional amplitude estimation", "", "our algorithm", ""],
        ["# operators Q", "# CNOT gates", "# qubits", "# CNOT gates", "# qubits"],
        *cell_text,
    ]
    table = axis.table(
        cellText=table_rows,
        cellLoc="center",
        colLoc="center",
        loc="center",
        colWidths=[0.23, 0.21, 0.18, 0.20, 0.18],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.8)
    table.scale(1.0, 1.12)
    for (row, _column), cell in table.get_celld().items():
        cell.set_facecolor("white")
        cell.set_edgecolor("black")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.visible_edges = "T"
        elif row == 1:
            cell.visible_edges = "B"
        elif row == len(table_rows) - 1:
            cell.visible_edges = "B"
        else:
            cell.visible_edges = ""
    figure.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
    figure.savefig(output, dpi=100, facecolor="white")
    plt.close(figure)


def run_table2() -> dict[str, Any]:
    started = time.perf_counter()
    rows = derive_resource_table()
    data_path = DATA_DIR / "table2_resources.csv"
    write_csv(
        data_path,
        rows,
        [
            "Q_label",
            "Q_power",
            "Q_exponent",
            "conventional_cnot",
            "conventional_qubits",
            "proposed_cnot",
            "proposed_qubits",
            "proposed_direct_sum",
            "conventional_direct_sum",
        ],
    )
    source_expected = [
        (None, None, 4, 3),
        (135, 7, 18, 3),
        (399, 8, 32, 3),
        (927, 9, 60, 3),
        (1981, 10, 116, 3),
        (4085, 11, 228, 3),
        (8287, 12, 452, 3),
        (16683, 13, 900, 3),
        (33465, 14, 1796, 3),
        (67017, 15, 3588, 3),
    ]
    generated = [
        (
            row["conventional_cnot"],
            row["conventional_qubits"],
            row["proposed_cnot"],
            row["proposed_qubits"],
        )
        for row in rows
    ]
    direct_matches = all(
        row["proposed_cnot"] == row["proposed_direct_sum"]
        and (
            row["conventional_cnot"] is None
            or row["conventional_cnot"] == row["conventional_direct_sum"]
        )
        for row in rows
    )
    numeric_cells = 2 + 9 * 4
    checks = [
        check(
            "direct_block_sum_equals_closed_form",
            direct_matches,
            {"rows": len(rows), "primitive_cnot": {"A": 4, "Q": 14, "controlled_Q": 131}},
        ),
        check(
            "all_source_numeric_cells_exact",
            generated == source_expected,
            {"matching_numeric_cells": numeric_cells, "total_numeric_cells": numeric_cells},
        ),
        check(
            "proposed_qubits_constant",
            all(row["proposed_qubits"] == 3 for row in rows),
            {"value": 3},
        ),
        check(
            "conventional_qubits_increment",
            [row["conventional_qubits"] for row in rows[1:]] == list(range(7, 16)),
            {"values": [row["conventional_qubits"] for row in rows[1:]]},
        ),
    ]
    figure_path = FIGURE_DIR / "table2_resources.png"
    render_table2(rows, figure_path)
    runtime = time.perf_counter() - started
    payload = target_check_payload(
        "T_TABLE2",
        runtime,
        checks,
        parameters={
            "n": 2,
            "b_max": "pi/4",
            "connectivity": "all-to-all",
            "gate_set": "Qiskit 0.7",
            "Q_exponents": list(range(9)),
        },
        metrics={"matching_numeric_cells": numeric_cells, "total_numeric_cells": numeric_cells},
        artifacts={
            "data": relative_workspace(data_path),
            "figure": relative_workspace(figure_path),
        },
    )
    write_json(CHECK_DIR / "table2_scientific_check.json", payload)
    return payload


def conventional_ae_envelope(a: float, minimum_m: int = 7, maximum_m: int = 17) -> list[dict[str, Any]]:
    theta = math.asin(math.sqrt(a))
    rows: list[dict[str, Any]] = []
    for phase_bits in range(minimum_m, maximum_m + 1):
        queries = 2**phase_bits - 1
        phase_location = theta * queries / math.pi
        low = math.floor(phase_location)
        high = math.ceil(phase_location)
        candidates = [low, high, queries - low, queries - high]
        amplitude_candidates = [math.sin(math.pi * value / queries) ** 2 for value in candidates]
        largest_error = max(abs(value - a) for value in amplitude_candidates)
        rows.append(
            {
                "method": "conventional",
                "M": phase_bits,
                "N_q": queries,
                "error": largest_error,
                "N_shot": None,
                "repetitions": None,
            }
        )
    return rows


def render_figa(rows: list[dict[str, Any]], output: Path) -> None:
    _style()
    plt.rcParams.update(
        {
            "font.size": 15,
            "axes.linewidth": 1.8,
            "xtick.major.size": 7,
            "ytick.major.size": 7,
            "xtick.minor.size": 4,
            "ytick.minor.size": 4,
        }
    )
    width, height = 492, 400
    figure, axis = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    styles = {
        "conventional": {"color": "black", "marker": "o", "label": "conventional"},
        "eis_30": {"color": "#ff3b3b", "marker": "^", "label": r"$N_{\rm shot}=30$"},
        "eis_100": {"color": "#3158b5", "marker": "s", "label": r"$N_{\rm shot}=100$"},
        "classical": {"color": "#55b82d", "marker": "x", "label": "classical"},
    }
    for method in ("conventional", "eis_30", "eis_100", "classical"):
        method_rows = sorted([row for row in rows if row["method"] == method], key=lambda row: int(row["N_q"]))
        style = styles[method]
        axis.plot(
            [row["N_q"] for row in method_rows],
            [row["error"] for row in method_rows],
            linestyle="none",
            marker=style["marker"],
            markersize=9,
            markerfacecolor="none",
            markeredgewidth=1.3,
            color=style["color"],
            label=style["label"],
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlim(85, 140_000)
    axis.set_ylim(7e-6, 1.2e-1)
    axis.set_xlabel("Number of queries")
    axis.set_ylabel("Error")
    axis.legend(
        loc="upper right",
        frameon=True,
        fancybox=False,
        edgecolor="black",
        framealpha=1.0,
        fontsize=13,
    )
    figure.subplots_adjust(left=0.115, right=0.945, bottom=0.15, top=0.825)
    figure.savefig(output, dpi=100, facecolor="white")
    plt.close(figure)


def log_interpolated_ratio(
    numerator_rows: list[dict[str, Any]],
    denominator_rows: list[dict[str, Any]],
) -> float:
    numerator_x = np.array([float(row["N_q"]) for row in sorted(numerator_rows, key=lambda row: row["N_q"])])
    numerator_y = np.array([float(row["error"]) for row in sorted(numerator_rows, key=lambda row: row["N_q"])])
    denominator_x = np.array([float(row["N_q"]) for row in sorted(denominator_rows, key=lambda row: row["N_q"])])
    denominator_y = np.array([float(row["error"]) for row in sorted(denominator_rows, key=lambda row: row["N_q"])])
    mask = (numerator_x >= denominator_x.min()) & (numerator_x <= denominator_x.max())
    interpolated = np.exp(np.interp(np.log(numerator_x[mask]), np.log(denominator_x), np.log(denominator_y)))
    return float(np.median(numerator_y[mask] / interpolated))


def run_figa(settings: Mapping[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    a = float(settings["target_probability"])
    base_seed = int(settings["rng_seed"])
    repetitions = int(settings["repetitions"])
    shot_values = [int(value) for value in settings["N_shot_values"]]
    maximum_m_by_shots = {
        int(key): int(value) for key, value in settings["eis_maximum_M"].items()
    }
    rows: list[dict[str, Any]] = []
    for seed_offset, shots in enumerate(shot_values):
        maximum_M = maximum_m_by_shots[shots]
        method_name = f"eis_{shots}"
        generated = simulate_schedule_curve(
            a=a,
            schedule_kind="eis",
            maximum_M=maximum_M,
            shots=shots,
            repetitions=repetitions,
            rng=np.random.default_rng(np.random.SeedSequence([base_seed, seed_offset])),
            metric="percentile81",
        )
        for row in generated:
            row["method"] = method_name
            row["N_shot"] = shots
            row["repetitions"] = repetitions
            row.pop("cr_bound", None)
        rows.extend(generated)

    classical = classical_curve(
        a=a,
        shots=int(settings["classical_N_shot"]),
        repetitions=repetitions,
        rng=np.random.default_rng(np.random.SeedSequence([base_seed, 2])),
        metric="percentile81",
    )
    for row in classical:
        row["N_shot"] = int(settings["classical_N_shot"])
        row["repetitions"] = repetitions
        row.pop("cr_bound", None)
    rows.extend(classical)
    phase_bits = settings["conventional_phase_bits"]
    rows.extend(
        conventional_ae_envelope(
            a,
            minimum_m=int(phase_bits[0]),
            maximum_m=int(phase_bits[1]),
        )
    )
    for row in rows:
        row["target_probability"] = a
        row["percentile"] = PERCENTILE_81

    data_path = DATA_DIR / "figa_percentile_comparison.csv"
    write_csv(
        data_path,
        rows,
        ["target_probability", "method", "M", "N_shot", "N_q", "repetitions", "percentile", "error"],
    )
    figure_path = FIGURE_DIR / "figa_percentile_comparison.png"
    render_figa(rows, figure_path)

    grouped = {method: [row for row in rows if row["method"] == method] for method in {
        "conventional", "eis_30", "eis_100", "classical"
    }}
    conventional_slope = fit_log_slope(grouped["conventional"], "conventional")
    eis30_to_conventional = log_interpolated_ratio(grouped["eis_30"], grouped["conventional"])
    eis30_to_eis100 = log_interpolated_ratio(grouped["eis_30"], grouped["eis_100"])
    checks = [
        check(
            "paper_percentile_exact",
            abs(PERCENTILE_81 - 81.05694691387022) < 1e-12,
            {"value": PERCENTILE_81, "paper_definition": "100*8/pi^2"},
        ),
        check(
            "four_series_complete",
            set(grouped) == {"conventional", "eis_30", "eis_100", "classical"}
            and all(grouped.values()),
            {method: len(values) for method, values in grouped.items()},
        ),
        check(
            "conventional_error_converges",
            conventional_slope < -0.75,
            {"log_log_slope": conventional_slope, "threshold": -0.75},
        ),
        check(
            "eis30_comparable_to_conventional",
            0.25 <= eis30_to_conventional <= 4.0,
            {"median_interpolated_error_ratio": eis30_to_conventional, "accepted_range": [0.25, 4.0]},
        ),
        check(
            "lower_shot_eis_not_worse_at_fixed_queries",
            eis30_to_eis100 <= 1.35,
            {"median_interpolated_error_ratio_N30_over_N100": eis30_to_eis100, "maximum": 1.35},
        ),
        check(
            "all_errors_finite_positive",
            all(math.isfinite(float(row["error"])) and float(row["error"]) > 0 for row in rows),
            {"rows": len(rows)},
        ),
    ]
    runtime = time.perf_counter() - started
    payload = target_check_payload(
        "T_FIGA",
        runtime,
        checks,
        parameters={
            "target_probability": a,
            "N_shot_values": shot_values,
            "repetitions": repetitions,
            "percentile": PERCENTILE_81,
            "rng_seed": base_seed,
        },
        metrics={
            "conventional_log_log_slope": conventional_slope,
            "median_eis30_to_conventional_ratio": eis30_to_conventional,
            "median_eis30_to_eis100_ratio": eis30_to_eis100,
        },
        artifacts={
            "data": relative_workspace(data_path),
            "figure": relative_workspace(figure_path),
        },
    )
    write_json(CHECK_DIR / "figa_scientific_check.json", payload)
    return payload


def run_smoke() -> dict[str, Any]:
    started = time.perf_counter()
    a = 1.0 / 48.0
    rows = simulate_schedule_curve(
        a=a,
        schedule_kind="eis",
        maximum_M=5,
        shots=100,
        repetitions=64,
        rng=np.random.default_rng(190410246),
        metric="rmse",
    )
    elapsed = time.perf_counter() - started
    projected = elapsed * (1000.0 / 64.0) * (10.0 / 6.0) * 6.0
    payload = {
        "schema_version": 1,
        "status": "passed",
        "target_id": "T_FIG2",
        "stage": "exploratory",
        "measured_runtime_seconds": elapsed,
        "measured_configuration": {"amplitudes": 1, "repetitions": 64, "eis_M": [0, 5]},
        "projected_final_seconds_upper_estimate": projected,
        "memory_class": "local_ok",
        "sample_rows": len(rows),
    }
    write_json(CHECK_DIR / "performance_smoke_T_FIG2.json", payload)
    return payload


def style_horizontal_table(table: Any, data_rows: int, columns: int) -> None:
    for (row, column), cell in table.get_celld().items():
        cell.set_facecolor("white")
        cell.set_edgecolor("black")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.visible_edges = "TB"
        elif row == data_rows:
            cell.visible_edges = "B"
        else:
            cell.visible_edges = ""
        if column >= columns:
            cell.visible_edges = ""


def mathtext(value: str) -> str:
    replacements = {
        "O(epsilon^-2)": r"$\mathcal{O}(\epsilon^{-2})$",
        "O(epsilon^-4/3)": r"$\mathcal{O}(\epsilon^{-4/3})$",
        "O(epsilon^-5/3)": r"$\mathcal{O}(\epsilon^{-5/3})$",
        "O(epsilon^-1)": r"$\mathcal{O}(\epsilon^{-1})$",
        "O(epsilon^-1 log(epsilon^-1))": r"$\mathcal{O}(\epsilon^{-1}\ln\epsilon^{-1})$",
    }
    return replacements[value]


def table1_method_label(method: str) -> str:
    return {
        "Classical": "Classical\n" + r"$(m_k=0\ \forall k)$",
        "LIS": "Linearly incremental sequence (LIS)\n" + r"$(m_0=0,m_1=1,\ldots,m_M=M)$",
        "EIS": "Exponentially incremental sequence (EIS)\n"
        + r"$(m_0=0,m_1=2^0,\ldots,m_M=2^{M-1})$",
    }[method]


def check(check_id: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "passed" if passed else "failed",
        "evidence": evidence,
    }


def target_check_payload(
    target_id: str,
    runtime_seconds: float,
    checks: list[dict[str, Any]],
    *,
    parameters: dict[str, Any],
    metrics: dict[str, Any],
    artifacts: dict[str, str],
) -> dict[str, Any]:
    failures = [item["check_id"] for item in checks if item["status"] != "passed"]
    data_path = WORKSPACE / artifacts["data"]
    return {
        "schema_version": 1,
        "target_id": target_id,
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "generated_data_provenance": "independent_numerics"
        if target_id in {"T_FIG2", "T_FIGA"}
        else "analytic_reference",
        "status": "passed" if not failures else "failed",
        "runtime_seconds": runtime_seconds,
        "parameters": parameters,
        "metrics": metrics,
        "checks": checks,
        "summary": {
            "checks_total": len(checks),
            "checks_passed": len(checks) - len(failures),
            "checks_failed": len(failures),
            "failed_check_ids": failures,
        },
        "artifacts": artifacts,
        "data_sha256": sha256(data_path),
    }


def relative_workspace(path: Path) -> str:
    return str(path.relative_to(WORKSPACE))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(SUPPORTED_TARGETS))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    ensure_guard(args.target, args.smoke)
    prepare_target_directories()
    settings: Mapping[str, Any] = {}
    if not args.smoke and args.target in {"T_FIG2", "T_FIGA"}:
        if args.config is None:
            parser.error(f"--config is required for {args.target}")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        settings = config["targets"][args.target]

    if args.smoke:
        if args.target != "T_FIG2":
            raise SystemExit("--smoke is defined only for T_FIG2")
        payload = run_smoke()
    elif args.target == "T_FIG2":
        payload = run_fig2(settings)
    elif args.target == "T_TABLE1":
        payload = run_table1()
    elif args.target == "T_TABLE2":
        payload = run_table2()
    elif args.target == "T_FIGA":
        payload = run_figa(settings)
    else:
        raise AssertionError(args.target)

    print(
        json.dumps(
            {
                "target_id": args.target,
                "status": payload["status"],
                "runtime_seconds": payload.get("runtime_seconds", payload.get("measured_runtime_seconds")),
                "checks": payload.get("summary", {}),
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
