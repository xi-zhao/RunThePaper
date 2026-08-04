#!/usr/bin/env python3
"""Run Fig. 6-style duration and classical compile-time proxy scaling."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_PATH = WORKSPACE.parent
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from proxy_router import (  # noqa: E402
    ArchitectureParameters,
    benchmark_projector_terms,
    compile_projector_terms,
    route_gate_stream,
)


CONTRACT_PATH = WORKSPACE / "config" / "routing_benchmark_contract.json"
DATA_PATH = WORKSPACE / "outputs" / "data" / "proxy_duration_compile_scaling.csv"
CHECK_PATH = WORKSPACE / "outputs" / "checks" / "proxy_scaling_result.json"
FIGURE_PATH = WORKSPACE / "outputs" / "figures" / "proxy_duration_compile_scaling.png"


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    run = contract["generated_run"]
    architecture = ArchitectureParameters.from_contract(contract)
    families = [str(value) for value in run["duration_scaling_families"]]
    sizes = [int(value) for value in run["duration_scaling_qubit_counts"]]
    seed = int(run["duration_scaling_seed"])
    repetitions = int(run["compile_time_repetitions"])
    clauses_per_qubit = int(run["synthetic_3sat_clauses_per_qubit"])

    rows: list[dict[str, Any]] = []
    for family in families:
        for qubits in sizes:
            for strategy, keep_native in (("mobius_native", True), ("zap_decomposed", False)):
                elapsed: list[float] = []
                metrics = None
                for _ in range(repetitions):
                    started = time.perf_counter()
                    terms = benchmark_projector_terms(family, qubits, seed, clauses_per_qubit)
                    stream = compile_projector_terms(terms, keep_native=keep_native)
                    metrics = route_gate_stream(stream, qubits=qubits, architecture=architecture)
                    elapsed.append(time.perf_counter() - started)
                if metrics is None:
                    raise RuntimeError("scaling loop produced no metrics")
                rows.append(
                    {
                        "family": family,
                        "strategy": strategy,
                        "qubits": qubits,
                        "seed": seed,
                        "repetitions": repetitions,
                        "median_compile_route_seconds": statistics.median(elapsed),
                        "min_compile_route_seconds": min(elapsed),
                        "gate_count": metrics.gate_count,
                        "scheduled_stages": metrics.scheduled_stages,
                        "total_duration_us": metrics.total_duration_us,
                    }
                )

    lookup = {(row["family"], row["strategy"], row["qubits"]): row for row in rows}
    duration_shorter = all(
        lookup[(family, "mobius_native", qubits)]["total_duration_us"]
        < lookup[(family, "zap_decomposed", qubits)]["total_duration_us"]
        for family in families
        for qubits in sizes
    )
    compile_faster = all(
        lookup[(family, "mobius_native", qubits)]["median_compile_route_seconds"]
        < lookup[(family, "zap_decomposed", qubits)]["median_compile_route_seconds"]
        for family in families
        for qubits in sizes
    )
    checks = {
        "three_declared_many_body_families_present": len(families) == 3,
        "paper_fig6_size_range_reaches_100": sizes[0] == 20 and sizes[-1] == 100,
        "native_total_duration_shorter_at_every_point": duration_shorter,
        "native_median_compile_route_time_faster_at_every_point": compile_faster,
        "all_timings_positive": all(float(row["median_compile_route_seconds"]) > 0.0 for row in rows),
    }
    payload = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "passed_with_warnings",
        "paper_id": CASE_PATH.name,
        "target_id": "ROUTING_PROXY_SCALING",
        "scope": "proxy_model",
        "run_shape": {"families": families, "qubit_counts": sizes, "seed": seed, "repetitions": repetitions},
        "checks": checks,
        "boundary": "Classical timings are local Apple-M4 measurements for the disclosed proxy, not Fig. 6 author timings.",
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_rows(DATA_PATH, rows)
    _plot(rows, families, sizes, FIGURE_PATH)
    CHECK_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _plot(rows: list[dict[str, Any]], families: list[str], sizes: list[int], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = {"synthetic_3sat": "3-SAT oracle", "p_spin_ising": "p-spin Ising", "qram_oracle": "QRAM oracle"}
    colors = {"mobius_native": "#1f77b4", "zap_decomposed": "#d95f02"}
    strategy_labels = {"mobius_native": "Möbius native", "zap_decomposed": "ZAP decomposed"}
    lookup = {(row["family"], row["strategy"], row["qubits"]): row for row in rows}
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2), constrained_layout=True)
    for column, family in enumerate(families):
        for strategy in colors:
            duration = [lookup[(family, strategy, size)]["total_duration_us"] / 1e6 for size in sizes]
            compile_time = [lookup[(family, strategy, size)]["median_compile_route_seconds"] for size in sizes]
            axes[0, column].plot(sizes, duration, marker="o", color=colors[strategy], label=strategy_labels[strategy])
            axes[1, column].plot(sizes, compile_time, marker="o", color=colors[strategy], label=strategy_labels[strategy])
        axes[0, column].set_title(labels[family], fontweight="bold")
        axes[0, column].set_ylabel("routed duration (s)")
        axes[1, column].set_ylabel("local compile + route (s)")
        axes[1, column].set_xlabel("qubits")
        axes[1, column].set_yscale("log")
        axes[0, column].grid(alpha=0.25)
        axes[1, column].grid(alpha=0.25)
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.suptitle("Fig. 6 proxy — duration and local compile-time scaling\nproxy_model, not author timing data", fontsize=13)
    fig.savefig(path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
