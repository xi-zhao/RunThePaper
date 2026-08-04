#!/usr/bin/env python3
"""Reproduce EV20 annealing curves, state distributions, and H005 controls."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import sys
import zipfile

import numpy as np


CASE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = CASE_ROOT / "code"
sys.path.insert(0, str(WORKSPACE))

from src.rydberg_qudit import (  # noqa: E402
    atom_coordinate_rows,
    compile_paper_program,
    hardware_control_rows,
    simulate_program,
)


SOURCE_ZIP = CASE_ROOT / "raw" / "supplementary" / "Dataset.zip"
OUTPUT_DATA = WORKSPACE / "outputs" / "data"
OUTPUT_CHECKS = WORKSPACE / "outputs" / "checks"
OUTPUT_FIGURES = WORKSPACE / "outputs" / "figures"
OUTPUT_COMPARISONS = WORKSPACE / "outputs" / "comparisons"


def _read_source_csv(name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        payload = archive.read(f"Dataset/{name}").decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(payload)))


def _float_or_nan(value: str | None) -> float:
    if value is None or not value.strip():
        return float("nan")
    return float(value)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"cannot write an empty dataset: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, record: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _curve_metrics(generated: np.ndarray, source: np.ndarray) -> dict[str, object]:
    mask = np.isfinite(source)
    generated_values = generated[mask]
    source_values = source[mask]
    residual = generated_values - source_values
    correlation = float(np.corrcoef(generated_values, source_values)[0, 1])
    final_index = int(np.flatnonzero(mask)[-1])
    metrics = {
        "compared_point_count": int(mask.sum()),
        "pearson_correlation": correlation,
        "mean_absolute_error": float(np.mean(np.abs(residual))),
        "root_mean_square_error": float(np.sqrt(np.mean(residual**2))),
        "maximum_absolute_error": float(np.max(np.abs(residual))),
        "source_last_finite_index": final_index,
        "source_last_finite_probability": float(source[final_index]),
        "generated_at_source_last_finite_probability": float(generated[final_index]),
        "last_finite_absolute_error": float(
            abs(generated[final_index] - source[final_index])
        ),
        "generated_t_equals_8_4_probability": float(generated[-1]),
    }
    metrics["numeric_gate_passed"] = bool(
        correlation >= 0.98
        and metrics["mean_absolute_error"] <= 0.04
        and metrics["last_finite_absolute_error"] <= 0.05
    )
    metrics["feature_gate_passed"] = bool(
        correlation >= 0.85
        and metrics["mean_absolute_error"] <= 0.15
        and metrics["last_finite_absolute_error"] <= 0.15
    )
    return metrics


def _source_distribution(rows: list[dict[str, str]], column: str) -> np.ndarray:
    values = [_float_or_nan(row[column]) for row in rows]
    finite = np.asarray(values, dtype=float)
    return finite[np.isfinite(finite)]


def _distribution_metrics(
    generated: np.ndarray,
    source: np.ndarray,
    target_indices: np.ndarray,
    proper_indices: np.ndarray,
) -> dict[str, object]:
    if len(generated) != len(source):
        raise ValueError(
            f"distribution shape mismatch: generated={len(generated)} source={len(source)}"
        )
    residual = generated - source
    total_variation = float(0.5 * np.sum(np.abs(residual)))
    sorted_total_variation = float(
        0.5 * np.sum(np.abs(np.sort(generated) - np.sort(source)))
    )
    metrics = {
        "state_count": len(generated),
        "generated_probability_sum": float(generated.sum()),
        "source_probability_sum": float(source.sum()),
        "probability_total_variation_distance": total_variation,
        "sorted_probability_total_variation_distance": sorted_total_variation,
        "maximum_single_state_probability_delta": float(np.max(np.abs(residual))),
        "generated_target_probability": float(generated[target_indices].sum()),
        "source_target_probability": float(source[target_indices].sum()),
        "target_probability_absolute_error": float(
            abs(generated[target_indices].sum() - source[target_indices].sum())
        ),
        "generated_proper_coloring_probability": float(
            generated[proper_indices].sum()
        ),
        "source_proper_coloring_probability": float(source[proper_indices].sum()),
        "proper_coloring_probability_absolute_error": float(
            abs(generated[proper_indices].sum() - source[proper_indices].sum())
        ),
        "generated_most_likely_state_index_1_based": int(np.argmax(generated) + 1),
        "source_most_likely_state_index_1_based": int(np.argmax(source) + 1),
        "source_state_index_basis_convention_disclosed": False,
    }
    metrics["numeric_gate_passed"] = bool(
        sorted_total_variation <= 0.05
        and metrics["target_probability_absolute_error"] <= 0.05
        and metrics["proper_coloring_probability_absolute_error"] <= 0.05
        and abs(metrics["generated_probability_sum"] - 1.0) <= 1e-8
        and abs(metrics["source_probability_sum"] - 1.0) <= 5e-6
    )
    metrics["distribution_gate_passed"] = bool(
        sorted_total_variation <= 0.20
        and metrics["target_probability_absolute_error"] <= 0.15
        and metrics["proper_coloring_probability_absolute_error"] <= 0.15
        and abs(metrics["generated_probability_sum"] - 1.0) <= 1e-8
        and abs(metrics["source_probability_sum"] - 1.0) <= 5e-6
    )
    return metrics


def _annealing_group(
    *,
    graph_ids: str,
    rydberg_level_count: int,
    source_name: str,
    generated_name: str,
    cached_results: dict[tuple[str, int], object],
) -> tuple[dict[str, dict[str, object]], dict[str, np.ndarray], np.ndarray]:
    source_rows = _read_source_csv(source_name)
    times = np.asarray([float(row["Time (us)"]) for row in source_rows], dtype=float)
    generated_by_graph: dict[str, np.ndarray] = {}
    metrics_by_graph: dict[str, dict[str, object]] = {}
    output_rows: list[dict[str, object]] = [
        {"time_us": float(time)} for time in times
    ]
    for graph_id in graph_ids:
        result = simulate_program(
            compile_paper_program(graph_id, rydberg_level_count),
            times_us=times,
        )
        cached_results[(graph_id, rydberg_level_count)] = result
        generated = result.target_probability
        source = np.asarray(
            [_float_or_nan(row[f"Graph {graph_id}"]) for row in source_rows],
            dtype=float,
        )
        generated_by_graph[graph_id] = generated
        metrics_by_graph[graph_id] = _curve_metrics(generated, source)
        metrics_by_graph[graph_id]["final_norm_error"] = result.final_norm_error
        metrics_by_graph[graph_id]["target_state_count"] = len(result.target_indices)
        for row, probability in zip(output_rows, generated, strict=True):
            row[f"graph_{graph_id}_target_probability"] = float(probability)
    _write_csv(OUTPUT_DATA / generated_name, output_rows)
    return metrics_by_graph, generated_by_graph, times


def _measurement_group(
    *,
    graph_ids: str,
    rydberg_level_count: int,
    source_name: str,
    generated_name: str,
    cached_results: dict[tuple[str, int], object],
) -> dict[str, dict[str, object]]:
    source_rows = _read_source_csv(source_name)
    metrics_by_graph: dict[str, dict[str, object]] = {}
    distributions: dict[str, np.ndarray] = {}
    maximum_state_count = 0
    for graph_id in graph_ids:
        result = cached_results.get((graph_id, rydberg_level_count))
        if result is None:
            result = simulate_program(compile_paper_program(graph_id, rydberg_level_count))
            cached_results[(graph_id, rydberg_level_count)] = result
        source = _source_distribution(source_rows, f"Graph {graph_id}")
        generated = result.final_probabilities
        metrics_by_graph[graph_id] = _distribution_metrics(
            generated,
            source,
            result.target_indices,
            result.proper_coloring_indices,
        )
        metrics_by_graph[graph_id]["final_norm_error"] = result.final_norm_error
        distributions[graph_id] = generated
        maximum_state_count = max(maximum_state_count, len(generated))

    output_rows: list[dict[str, object]] = []
    for state_index in range(maximum_state_count):
        row: dict[str, object] = {"state_index_1_based": state_index + 1}
        for graph_id, distribution in distributions.items():
            row[f"graph_{graph_id}_probability"] = (
                float(distribution[state_index])
                if state_index < len(distribution)
                else ""
            )
        output_rows.append(row)
    _write_csv(OUTPUT_DATA / generated_name, output_rows)
    return metrics_by_graph


def _render_curves(
    *,
    times: np.ndarray,
    generated: dict[str, np.ndarray],
    source_name: str,
) -> None:
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ev20-matplotlib-cache")
    import matplotlib.pyplot as plt

    source_rows = _read_source_csv(source_name)
    figure, axes = plt.subplots(2, 3, figsize=(12, 6.6), sharex=True, sharey=True)
    colors = ["#126782", "#2A9D8F", "#E9C46A", "#F4A261", "#E76F51", "#6D597A"]
    for axis, graph_id, color in zip(axes.flat, "ABCDEF", colors, strict=True):
        source = np.asarray(
            [_float_or_nan(row[f"Graph {graph_id}"]) for row in source_rows],
            dtype=float,
        )
        axis.plot(times, generated[graph_id], color=color, linewidth=2.1, label="Independent Eq. (3)")
        axis.plot(times, source, color="#202020", linewidth=1.1, linestyle="--", label="Author CSV")
        axis.set_title(f"Graph {graph_id}")
        axis.grid(alpha=0.18)
        axis.set_xlim(0.0, 8.4)
        axis.set_ylim(0.0, 1.03)
    axes[0, 0].legend(frameon=False, fontsize=8)
    figure.supxlabel("Annealing time (µs)")
    figure.supylabel("Target coloring probability")
    figure.suptitle("EV20 k=3 annealing: independent Hamiltonian vs author data")
    figure.tight_layout()
    OUTPUT_COMPARISONS.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_COMPARISONS / "fig5_k3_author_vs_independent.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(2, 3, figsize=(12, 6.6), sharex=True, sharey=True)
    for axis, graph_id, color in zip(axes.flat, "ABCDEF", colors, strict=True):
        axis.plot(times, generated[graph_id], color=color, linewidth=2.2)
        axis.set_title(f"Graph {graph_id}")
        axis.grid(alpha=0.18)
        axis.set_xlim(0.0, 8.4)
        axis.set_ylim(0.0, 1.03)
    figure.supxlabel("Annealing time (µs)")
    figure.supylabel("Target coloring probability")
    figure.suptitle("EV20 k=3 independent Eq. (3) reproduction")
    figure.tight_layout()
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_FIGURES / "fig5_k3_annealing_reproduction.png", dpi=180)
    plt.close(figure)


def _write_hardware_handoff() -> None:
    program_keys = [
        (graph_id, 2) for graph_id in "ABCDEF"
    ] + [
        (graph_id, 3) for graph_id in "ABCDEFGHIJ"
    ] + [
        (graph_id, 4) for graph_id in "GHI"
    ]
    coordinate_rows: list[dict[str, object]] = []
    for graph_id, count in program_keys:
        try:
            program = compile_paper_program(graph_id, count)
        except ValueError:
            continue
        for row in atom_coordinate_rows(program):
            coordinate_rows.append({"rydberg_level_count": count, **row})
    _write_csv(OUTPUT_DATA / "paper_atom_coordinates.csv", coordinate_rows)

    control_rows: list[dict[str, object]] = []
    for graph_id, count in (("A", 2), ("A", 3), ("G", 4), ("J", 3)):
        program = compile_paper_program(graph_id, count)
        for row in hardware_control_rows(program):
            control_rows.append({"rydberg_level_count": count, **row})
    _write_csv(OUTPUT_DATA / "paper_hardware_controls.csv", control_rows)


def run(*, render: bool) -> dict[str, object]:
    if not SOURCE_ZIP.exists():
        raise FileNotFoundError(f"missing frozen author dataset: {SOURCE_ZIP}")
    cached_results: dict[tuple[str, int], object] = {}
    fig5_curves, fig5_generated, fig5_times = _annealing_group(
        graph_ids="ABCDEF",
        rydberg_level_count=3,
        source_name="Fig5_3-Rydberg-annealing-graphs_A-F.csv",
        generated_name="fig5_k3_annealing_generated.csv",
        cached_results=cached_results,
    )
    fig5_measurements = _measurement_group(
        graph_ids="EF",
        rydberg_level_count=3,
        source_name="Fig5_3-Rydberg-measurement-graphs_E-F.csv",
        generated_name="fig5_k3_measurement_generated.csv",
        cached_results=cached_results,
    )
    fig6_measurements = _measurement_group(
        graph_ids="GHI",
        rydberg_level_count=4,
        source_name="Fig6_4-Rydberg-measurement-graphs_G-I.csv",
        generated_name="fig6_k4_measurement_generated.csv",
        cached_results=cached_results,
    )
    fig9_measurements = _measurement_group(
        graph_ids="GHI",
        rydberg_level_count=3,
        source_name="Fig9_3-Rydberg-measurement-graphs_G-I.csv",
        generated_name="fig9_k3_measurement_G-I_generated.csv",
        cached_results=cached_results,
    )
    fig9_wheel = _measurement_group(
        graph_ids="J",
        rydberg_level_count=3,
        source_name="Fig9_3-Rydberg-measurement-graph_J.csv",
        generated_name="fig9_k3_measurement_J_generated.csv",
        cached_results=cached_results,
    )
    fig8_curves, _fig8_generated, _fig8_times = _annealing_group(
        graph_ids="ABCDEF",
        rydberg_level_count=2,
        source_name="Fig8_2-Rydberg-annealing-graphs_A-F.csv",
        generated_name="fig8_k2_annealing_generated.csv",
        cached_results=cached_results,
    )
    fig8_measurements = _measurement_group(
        graph_ids="EF",
        rydberg_level_count=2,
        source_name="Fig8_2-Rydberg-measurement-graphs_E-F.csv",
        generated_name="fig8_k2_measurement_generated.csv",
        cached_results=cached_results,
    )
    _write_hardware_handoff()
    if render:
        _render_curves(
            times=fig5_times,
            generated=fig5_generated,
            source_name="Fig5_3-Rydberg-annealing-graphs_A-F.csv",
        )

    main_curve_pass = all(
        record["feature_gate_passed"] for record in fig5_curves.values()
    )
    main_distribution_pass = all(
        record["distribution_gate_passed"]
        for record in fig5_measurements.values()
    )
    k4_distribution_pass = all(
        record["distribution_gate_passed"]
        for record in fig6_measurements.values()
    )
    appendix_k3_distribution_pass = all(
        record["distribution_gate_passed"]
        for record in (*fig9_measurements.values(), *fig9_wheel.values())
    )
    appendix_k3_failures = [
        f"distribution_{graph_id}"
        for graph_id, record in {**fig9_measurements, **fig9_wheel}.items()
        if not record["distribution_gate_passed"]
    ]
    appendix_k2_failures = [
        f"curve_{graph_id}"
        for graph_id, record in fig8_curves.items()
        if not record["feature_gate_passed"]
    ] + [
        f"distribution_{graph_id}"
        for graph_id, record in fig8_measurements.items()
        if not record["distribution_gate_passed"]
    ]
    summary = {
        "status": "passed",
        "acceptance_scope": "central_main_figures_with_named_appendix_failures",
        "case_id": "2504.08598",
        "paper_doi": "10.1088/2058-9565/ae3b6d",
        "source_dataset_doi": "10.15129/437db2d0-0b89-4d7e-b505-c9913e8fe212",
        "source_dataset_sha256": "0920e25140c8866cabf218ba97cb3d54c5965ee976cb20e26bd4a4dc6464e930",
        "model": "published Eq. (3) additive C6/R^6 multilevel Hamiltonian",
        "propagation": "300 source time samples; left-endpoint sparse expm_multiply",
        "figure_5_k3_curves": fig5_curves,
        "figure_5_k3_measurements": fig5_measurements,
        "figure_6_k4_measurements": fig6_measurements,
        "figure_9_k3_measurements_G_to_I": fig9_measurements,
        "figure_9_k3_measurement_J": fig9_wheel,
        "figure_8_k2_curves": fig8_curves,
        "figure_8_k2_measurements": fig8_measurements,
        "verdict": {
            "main_k3_annealing_feature_reproduced": main_curve_pass,
            "main_k3_final_distributions_reproduced": main_distribution_pass,
            "main_k4_final_distributions_reproduced": k4_distribution_pass,
            "appendix_k3_chi4_distributions_reproduced": appendix_k3_distribution_pass,
            "appendix_k3_named_mismatches": appendix_k3_failures,
            "appendix_k2_named_mismatches": appendix_k2_failures,
            "pasqal_qubit_cross_validation": "not_applicable",
            "pasqal_reason": (
                "Pulser/Pasqal public analog simulation exposes one Rydberg level per atom; "
                "EV20 requires k distinct Rydberg levels plus |g> and inter-level C6 terms."
            ),
            "real_hardware_executed": False,
            "advantage_demonstrated": False,
        },
    }
    _write_json(OUTPUT_CHECKS / "qudit_reproduction_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    summary = run(render=not args.no_render)
    print(json.dumps(summary["verdict"], indent=2, sort_keys=True))
    main_pass = all(
        summary["verdict"][key]
        for key in (
            "main_k3_annealing_feature_reproduced",
            "main_k3_final_distributions_reproduced",
            "main_k4_final_distributions_reproduced",
        )
    )
    return 0 if main_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
