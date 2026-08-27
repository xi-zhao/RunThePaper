#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CODE_ROOT = Path(__file__).resolve().parents[1]
# In the PRAgent master case the code root is ``workspace``; in the public
# RunThePaper projection it is ``code`` and generated artifacts belong beside
# that directory.  Keeping this path rule here makes the same scientific runner
# executable in both projections.
CASE_ROOT = CODE_ROOT if CODE_ROOT.name == "workspace" else CODE_ROOT.parent
sys.path.insert(0, str(CODE_ROOT))

from src.analytic_targets import (  # noqa: E402
    algorithm_lifecycles,
    lifecycle_curves,
    lifecycle_threshold_percent,
    table_i_analytic_rows,
)
from src.delayed_erasure_proxy import ProxyConfig, simulate_curve  # noqa: E402


DATA_DIR = CASE_ROOT / "outputs" / "data"
FIGURE_DIR = CASE_ROOT / "outputs" / "figures"
CHECK_DIR = CASE_ROOT / "outputs" / "checks"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def style_axis(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(direction="out", width=1.0)
    axis.grid(alpha=0.16, linewidth=0.6)


def target_fig2b_proxy() -> dict[str, Any]:
    config = ProxyConfig()
    rounds = [2, 4, 6, 8]
    rows = simulate_curve(config, rounds)
    for row in rows:
        row["distance"] = config.distance
        row["p_loss_per_opportunity"] = config.p_loss
        row["partner_flip_probability"] = config.partner_flip_probability
        row["seed"] = config.seed
        row["generated_data_provenance"] = "independent_numerics"
        row["parameter_match"] = "proxy_model"
    write_csv(DATA_DIR / "fig2b_proxy.csv", rows)

    x = np.asarray([row["rounds"] for row in rows], dtype=float)
    no_info = np.asarray([row["no_information_plot_rate"] for row in rows], dtype=float)
    delayed = np.asarray([row["delayed_erasure_plot_rate"] for row in rows], dtype=float)
    perfect = np.asarray([row["perfect_time_plot_rate"] for row in rows], dtype=float)

    figure, axis = plt.subplots(figsize=(6.1, 4.4), constrained_layout=True)
    axis.semilogy(x, no_info, "o-", color="#222222", linewidth=2.0, markersize=4.5, label="Loss, no SSR info")
    axis.semilogy(x, delayed, "o-", color="#E85A9D", linewidth=2.2, markersize=4.5, label="Loss, delayed-erasure")
    axis.semilogy(x, perfect, "--", color="#888888", linewidth=2.0, label="Perfect loss time")
    axis.set_xlabel("Number of SE rounds")
    axis.set_ylabel("Logical error rate")
    axis.set_title("Fig. 2(b) mechanism proxy: distance-five repetition code", loc="left", fontsize=10)
    axis.legend(frameon=False, fontsize=8)
    style_axis(axis)
    figure.savefig(FIGURE_DIR / "fig2b_proxy.png", dpi=240, bbox_inches="tight")
    plt.close(figure)

    improvement = float(np.median(no_info / delayed))
    check = {
        "status": "physically_consistent" if improvement > 1.0 else "failed",
        "target_id": "T001",
        "paper_item": "Fig. 2(b)",
        "artifact_stage": "exploratory",
        "parameter_match": "proxy_model",
        "paper_parameters": {"distance": 5, "p_loss_per_entangling_gate": 0.01, "model": "surface-code logical memory + delayed-erasure/MLE"},
        "generated_parameters": {"distance": 5, "p_loss_per_opportunity": 0.01, "shots": config.shots, "seed": config.seed, "model": "classical repetition-code analogue"},
        "feature_checks": {
            "median_improvement_over_paper_round_range": improvement,
            "delayed_matches_perfect_time_in_timing_marginalized_proxy": bool(np.array_equal(delayed, perfect)),
            "absolute_curve_claimed": False,
        },
        "blocker": "The author surface-code circuit generator, correlated MLE decoder, raw samples, shot count, and seeds are not public.",
        "data": "outputs/data/fig2b_proxy.csv",
        "figure": "outputs/figures/fig2b_proxy.png",
    }
    write_json(CHECK_DIR / "fig2b_proxy.json", check)
    return check


def target_fig4b() -> dict[str, Any]:
    lifecycle = np.linspace(1.0, 16.0, 151)
    threshold = np.asarray([lifecycle_threshold_percent(value) for value in lifecycle])
    rows = [
        {
            "lifecycle_length": float(x),
            "loss_only_threshold_percent": float(y),
            "generated_data_provenance": "analytic_reference",
            "parameter_match": "paper_exact",
            "source": "Appendix H.2: 7/(lifecycle length)^(1/3)",
        }
        for x, y in zip(lifecycle, threshold, strict=True)
    ]
    write_csv(DATA_DIR / "fig4b_lifecycle_threshold.csv", rows)

    figure, axis = plt.subplots(figsize=(5.6, 4.1), constrained_layout=True)
    axis.plot(lifecycle, threshold, color="#D98900", linewidth=2.2, label=r"$7/\ell^{1/3}$")
    anchors = np.asarray([1.0, 4.0, 8.0, 12.0, 16.0])
    axis.scatter(anchors, [lifecycle_threshold_percent(x) for x in anchors], marker=">", s=45, facecolors="white", edgecolors="#B44236", zorder=3)
    axis.set_xlabel("Lifecycle length")
    axis.set_ylabel("Loss-only threshold [%]")
    axis.set_xlim(0.5, 16.5)
    axis.set_ylim(2.4, 7.4)
    axis.set_title("Fig. 4(b): printed lifecycle-threshold trend", loc="left", fontsize=10)
    axis.legend(frameon=False)
    style_axis(axis)
    figure.savefig(FIGURE_DIR / "fig4b_lifecycle_threshold.png", dpi=240, bbox_inches="tight")
    plt.close(figure)

    monotonic = bool(np.all(np.diff(threshold) < 0.0))
    check = {
        "status": "passed" if monotonic else "failed",
        "target_id": "T002",
        "paper_item": "Fig. 4(b)",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "paper_parameters": {"lifecycle_domain": [1.0, 16.0], "fit": "7/lifecycle^(1/3) percent"},
        "generated_parameters": {"lifecycle_domain": [1.0, 16.0], "grid_points": 151, "fit": "7/lifecycle^(1/3) percent"},
        "feature_checks": {"strictly_decreasing": monotonic, "ell_1_percent": float(threshold[0]), "ell_16_percent": float(threshold[-1])},
        "scope_note": "This reproduces the printed analytic trend, not the unavailable finite-size simulation markers.",
        "data": "outputs/data/fig4b_lifecycle_threshold.csv",
        "figure": "outputs/figures/fig4b_lifecycle_threshold.png",
    }
    write_json(CHECK_DIR / "fig4b_lifecycle_threshold.json", check)
    return check


def target_fig6b() -> dict[str, Any]:
    rows = algorithm_lifecycles(ghz_qubits=16)
    for row in rows:
        row["generated_data_provenance"] = "analytic_reference"
        row["parameter_match"] = "paper_exact"
    write_csv(DATA_DIR / "fig6b_algorithm_lifecycles.csv", rows)

    labels = [str(row["algorithm"]) for row in rows]
    average = np.asarray([row["average"] for row in rows], dtype=float)
    maximum = np.asarray([row["maximum"] for row in rows], dtype=float)
    x = np.arange(len(rows))
    figure, axis = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    width = 0.34
    axis.bar(x - width / 2, average, width, color="#DDE6F5", edgecolor="#365B8C", label="Average")
    axis.bar(x + width / 2, maximum, width, color="#F4DE78", edgecolor="#8A6A00", label="Maximum")
    axis.set_xticks(x, labels, rotation=12, ha="right")
    axis.set_ylabel("SE rounds per logical qubit")
    axis.set_ylim(0.0, 14.0)
    axis.set_title("Fig. 6(b): algorithmic qubit lifecycles", loc="left", fontsize=10)
    axis.legend(frameon=False)
    style_axis(axis)
    figure.savefig(FIGURE_DIR / "fig6b_algorithm_lifecycles.png", dpi=240, bbox_inches="tight")
    plt.close(figure)

    expected = [(2.0, 4.0), (4.0, 5.0), (7.0, 8.0), (9.0, 13.0)]
    exact = all((float(row["average"]), float(row["maximum"])) == pair for row, pair in zip(rows, expected, strict=True))
    check = {
        "status": "passed" if exact else "failed",
        "target_id": "T003",
        "paper_item": "Fig. 6(b)",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "paper_parameters": {"GHZ_N": 16, "algorithms": labels},
        "generated_parameters": {"GHZ_N": 16, "algorithms": labels},
        "feature_checks": {"all_printed_counts_exact": exact, "values": expected},
        "data": "outputs/data/fig6b_algorithm_lifecycles.csv",
        "figure": "outputs/figures/fig6b_algorithm_lifecycles.png",
    }
    write_json(CHECK_DIR / "fig6b_algorithm_lifecycles.json", check)
    return check


def target_lifecycle_figures() -> tuple[dict[str, Any], dict[str, Any]]:
    distance = 9
    rows = lifecycle_curves(distance, range(2, 21))
    for row in rows:
        row["distance"] = distance
        row["generated_data_provenance"] = "analytic_reference"
        row["parameter_match"] = "paper_subset"
    write_csv(DATA_DIR / "fig14c_swap_lifecycles.csv", rows)
    write_csv(DATA_DIR / "fig16a_lifecycle_comparison.csv", rows)

    x = np.asarray([row["displayed_se_rounds"] for row in rows], dtype=float)
    all_curve = np.asarray([row["conventional_all_lifecycle"] for row in rows], dtype=float)
    data_curve = np.asarray([row["conventional_data_lifecycle"] for row in rows], dtype=float)
    measure_curve = np.asarray([row["conventional_measure_lifecycle"] for row in rows], dtype=float)

    figure, axis = plt.subplots(figsize=(5.8, 4.2), constrained_layout=True)
    axis.plot(x, all_curve, "o-", color="#4568B2", markersize=4.2, linewidth=1.9, label="SWAP SE period 1")
    axis.plot(x, all_curve, "o", markerfacecolor="white", markeredgecolor="#6846A5", markersize=5.5, label="SWAP SE period 2")
    axis.set_xlabel("Number of SE rounds")
    axis.set_ylabel("Average lifecycle length")
    axis.set_ylim(3.0, 8.0)
    axis.set_title("Fig. 14(c): SWAP all-qubit lifecycle invariant", loc="left", fontsize=10)
    axis.legend(frameon=False, fontsize=8)
    style_axis(axis)
    figure.savefig(FIGURE_DIR / "fig14c_swap_lifecycles.png", dpi=240, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6.3, 4.5), constrained_layout=True)
    axis.semilogy(x, all_curve, "o-", color="#4568B2", linewidth=2.0, markersize=4.2, label="SWAP: all qubits")
    axis.semilogy(x, all_curve, "o-", color="#EE63A7", linewidth=1.3, markersize=4.0, label="Conventional: all qubits")
    axis.semilogy(x, data_curve, "s--", color="#EE63A7", linewidth=1.5, markersize=4.0, label="Conventional: data")
    axis.semilogy(x, measure_curve, "D:", color="#C13C8A", linewidth=1.5, markersize=3.8, label="Conventional: measure")
    axis.set_xlabel("Number of SE rounds")
    axis.set_ylabel("Average lifecycle length")
    axis.set_title("Fig. 16(a): lifecycle counting", loc="left", fontsize=10)
    axis.legend(frameon=False, fontsize=7.5, ncol=2)
    style_axis(axis)
    figure.savefig(FIGURE_DIR / "fig16a_lifecycle_comparison.png", dpi=240, bbox_inches="tight")
    plt.close(figure)

    invariant = bool(np.allclose(all_curve, [row["swap_period_1_all_lifecycle"] for row in rows]) and np.allclose(all_curve, [row["swap_period_2_all_lifecycle"] for row in rows]))
    asymptotic_d9 = 8.0 * distance / (distance + 1.0)
    fig14_check = {
        "status": "passed" if invariant and np.all(np.diff(all_curve) > 0.0) else "failed",
        "target_id": "T004",
        "paper_item": "Fig. 14(c)",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_subset",
        "paper_parameters": {"distance": 9, "displayed_rounds": [2, 20], "curves": ["SWAP period 1 all", "SWAP period 2 all"]},
        "generated_parameters": {"distance": 9, "displayed_rounds": [2, 20], "noisy_rounds_convention": "displayed_rounds - 1"},
        "feature_checks": {"period_1_equals_period_2": invariant, "monotonic_to_finite_d_limit": bool(np.all(np.diff(all_curve) > 0.0)), "finite_d_deep_limit": asymptotic_d9, "large_d_limit": 8.0},
        "data": "outputs/data/fig14c_swap_lifecycles.csv",
        "figure": "outputs/figures/fig14c_swap_lifecycles.png",
    }
    fig16_check = {
        "status": "physically_consistent" if invariant and np.all(np.diff(data_curve) > 0.0) and np.allclose(measure_curve, measure_curve[0]) else "failed",
        "target_id": "T005",
        "paper_item": "Fig. 16(a)",
        "artifact_stage": "exploratory",
        "parameter_match": "paper_subset",
        "paper_parameters": {"distance": 9, "displayed_rounds": [2, 18], "role_resolved": True},
        "generated_parameters": {"distance": 9, "displayed_rounds": [2, 20], "role_resolved": "conventional only; SWAP all-qubit invariant"},
        "feature_checks": {"swap_and_conventional_all_equal": invariant, "conventional_data_grows": bool(np.all(np.diff(data_curve) > 0.0)), "conventional_measure_constant": bool(np.allclose(measure_curve, measure_curve[0]))},
        "remaining_gap": "The SWAP data/measure role-resolved subcurves require the author's exact boundary pairing schedule.",
        "data": "outputs/data/fig16a_lifecycle_comparison.csv",
        "figure": "outputs/figures/fig16a_lifecycle_comparison.png",
    }
    write_json(CHECK_DIR / "fig14c_swap_lifecycles.json", fig14_check)
    write_json(CHECK_DIR / "fig16a_lifecycle_comparison.json", fig16_check)
    return fig14_check, fig16_check


def target_table_i() -> dict[str, Any]:
    rows = table_i_analytic_rows(distance=7)
    for row in rows:
        row["distance_for_numeric_evaluation"] = "7"
        row["generated_data_provenance"] = "analytic_reference"
        row["parameter_match"] = "paper_exact"
    write_csv(DATA_DIR / "table_i_analytic_rows.csv", rows)
    expected_overhead = str(8 * 7**3 - 4 * 7)
    exact = len(rows) == 7 and rows[0]["data_lifecycle"] == "28" and rows[0]["space_time_overhead"] == expected_overhead and rows[3]["space_time_overhead"] == str(18 * 7**3 - 6 * 7)
    check = {
        "status": "passed" if exact else "failed",
        "target_id": "T006",
        "paper_item": "Table I analytic rows",
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "paper_parameters": {"methods": 7, "rows": ["average data lifecycle", "average measure lifecycle", "space-time overhead"]},
        "generated_parameters": {"methods": 7, "distance_for_polynomial_evaluation": 7},
        "feature_checks": {"method_count": len(rows), "conventional_data_lifecycle_at_d7": rows[0]["data_lifecycle"], "conventional_space_time_at_d7": expected_overhead, "all_exact": exact},
        "scope_note": "Threshold and effective-distance rows are simulation outputs and remain separately deferred.",
        "data": "outputs/data/table_i_analytic_rows.csv",
    }
    write_json(CHECK_DIR / "table_i_analytic_rows.json", check)
    return check


def main() -> int:
    started = time.perf_counter()
    for directory in (DATA_DIR, FIGURE_DIR, CHECK_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    checks = [target_fig2b_proxy(), target_fig4b(), target_fig6b()]
    checks.extend(target_lifecycle_figures())
    checks.append(target_table_i())
    elapsed = time.perf_counter() - started
    failed = [check["target_id"] for check in checks if check["status"] == "failed"]
    summary = {
        "status": "passed" if not failed else "failed",
        "paper_id": "2502.20558",
        "runtime_seconds": elapsed,
        "targets_run": [check["target_id"] for check in checks],
        "failed_targets": failed,
        "exact_or_analytic_targets": ["T002", "T003", "T004", "T005", "T006"],
        "proxy_targets": ["T001"],
        "note": "No source-figure pixels or digitized curves are computational inputs.",
    }
    write_json(CHECK_DIR / "reproduction_run.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
