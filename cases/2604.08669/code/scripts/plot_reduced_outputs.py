#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from p2wgs_potential import pipelined_assembly_time_ms  # noqa: E402


def main() -> int:
    figures_dir = ROOT / "outputs" / "figures"
    checks_dir = ROOT / "outputs" / "checks"
    data_dir = ROOT / "outputs" / "data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "timing_model").mkdir(parents=True, exist_ok=True)

    gnn_metrics_path = checks_dir / "retrained_gnn_model" / "metrics.json"
    if not gnn_metrics_path.exists():
        gnn_metrics_path = checks_dir / "reduced_gnn_pilot" / "metrics.json"
    p2wgs_metrics_path = checks_dir / "reduced_p2wgs_pilot" / "metrics.json"
    plot_gnn_distance_comparison(gnn_metrics_path, figures_dir / "fig3_reduced_gnn_metrics.png")
    plot_p2wgs_continuity(p2wgs_metrics_path, figures_dir / "fig4_reduced_p2wgs_continuity.png")
    timing_metrics = build_timing_model(checks_dir / "timing_model" / "metrics.json")
    plot_timing_model(timing_metrics, figures_dir / "fig5_reduced_timing_model.png")
    export_gnn_rows(gnn_metrics_path, data_dir / "fig3_reduced_gnn_eval_rows.csv")
    export_p2wgs_rows(p2wgs_metrics_path, data_dir / "fig4_reduced_p2wgs_rows.csv")
    write_csv(data_dir / "fig5_timing_model_rows.csv", timing_metrics["rows"])
    print(json.dumps({"figures_dir": "outputs/figures", "timing_metrics": timing_metrics["summary"]}, indent=2))
    return 0


def plot_gnn_distance_comparison(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    rows = metrics["eval_rows"]
    x = np.arange(len(rows))
    width = 0.36

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.2), constrained_layout=True)
    for ax, key, title in [
        (axes[0], "max_distance", "Maximum move distance"),
        (axes[1], "average_distance", "Mean move distance"),
    ]:
        optimal = np.asarray([row[f"optimal_{key}"] for row in rows], dtype=float)
        predicted = np.asarray([row[f"predicted_{key}"] for row in rows], dtype=float)
        ax.bar(x - width / 2, optimal, width, label="Hungarian", color="#c44e52")
        ax.bar(x + width / 2, predicted, width, label="GNN decoder", color="#55a868")
        ax.set_title(title)
        ax.set_xlabel("eval instance")
        ax.set_ylabel("lattice units")
        ax.set_xticks(x)
        ax.grid(axis="y", alpha=0.25)
    axes[0].legend(frameon=False)
    fig.suptitle("Fig. 3 reproduction: retrained GNN assignment distances", fontsize=12)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_p2wgs_continuity(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    summary = metrics["summary"]
    iterations = np.asarray(summary["iteration_counts"], dtype=int)
    intensity = np.asarray(
        [summary["mean_intensity_continuity_by_iteration"][str(value)] for value in iterations],
        dtype=float,
    )
    phase = np.asarray(
        [summary["mean_phase_continuity_by_iteration"][str(value)] for value in iterations],
        dtype=float,
    )

    fig, ax1 = plt.subplots(figsize=(5.2, 3.4), constrained_layout=True)
    ax1.plot(iterations, intensity, marker="o", color="#dd8452", label="Intensity continuity")
    ax1.set_xlabel("P2WGS iterations")
    ax1.set_ylabel("mean relative intensity change")
    ax1.grid(alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(iterations, phase, marker="s", color="#4c72b0", label="Phase continuity")
    ax2.set_ylabel("mean wrapped phase change / 2pi")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], frameon=False, loc="upper right")
    fig.suptitle("Reduced Fig. 4 reproduction: P2WGS continuity", fontsize=12)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_timing_model(output_path: Path) -> dict[str, object]:
    refresh_values = np.linspace(0.2, 1.4, 25)
    iteration_models = {
        "iter5": 0.5,
        "iter8": 0.8,
        "iter10": 1.0,
    }
    rows = []
    for label, generation_ms in iteration_models.items():
        for refresh_ms in refresh_values:
            rows.append(
                {
                    "iteration_label": label,
                    "per_frame_generation_ms": generation_ms,
                    "slm_refresh_ms": float(refresh_ms),
                    "total_assembly_time_ms": pipelined_assembly_time_ms(
                        path_planning_ms=5.0,
                        per_frame_generation_ms=generation_ms,
                        slm_refresh_ms=float(refresh_ms),
                        frames=20,
                        transfer_delay_ms=3.0,
                    ),
                }
            )
    metrics: dict[str, object] = {
        "status": "completed",
        "paper_id": "2604.08669",
        "target": "pipelined_timing_model",
        "config": {
            "path_planning_ms": 5.0,
            "frames": 20,
            "transfer_delay_ms": 3.0,
            "iteration_generation_ms": iteration_models,
        },
        "summary": {
            "refresh_min_ms": float(refresh_values.min()),
            "refresh_max_ms": float(refresh_values.max()),
            "rows": len(rows),
        },
        "rows": rows,
    }
    output_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def plot_timing_model(metrics: dict[str, object], output_path: Path) -> None:
    rows = metrics["rows"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    for label, color in [("iter5", "#55a868"), ("iter8", "#dd8452"), ("iter10", "#c44e52")]:
        subset = [row for row in rows if row["iteration_label"] == label]
        x = [row["slm_refresh_ms"] for row in subset]
        y = [row["total_assembly_time_ms"] for row in subset]
        ax.plot(x, y, label=label, color=color)
    ax.set_xlabel("SLM refresh time (ms/frame)")
    ax.set_ylabel("total assembly time (ms)")
    ax.set_title("Reduced Fig. 5 reproduction: pipeline timing model")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    fig.text(
        0.5,
        0.025,
        "Difference reason: analytic pipeline model only; no measured RTX 5090 or A100 hardware benchmark.",
        ha="center",
        va="bottom",
        fontsize=7.5,
        wrap=True,
    )
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def export_gnn_rows(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    rows = []
    for idx, row in enumerate(metrics["eval_rows"]):
        rows.append({"eval_instance": idx, **row})
    write_csv(output_path, rows)


def export_p2wgs_rows(metrics_path: Path, output_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    write_csv(output_path, metrics["rows"])


def write_csv(output_path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
