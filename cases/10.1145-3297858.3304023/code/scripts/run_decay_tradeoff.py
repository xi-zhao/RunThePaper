from __future__ import annotations

import csv
import json
from pathlib import Path
import random
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sabre import Gate, Operation, compute_depth, random_layout, route_sabre, tokyo_20_graph


def random_interaction_circuit(n_qubits: int, n_gates: int, seed: int) -> list[Gate]:
    rng = random.Random(seed)
    return [Gate(*rng.sample(range(n_qubits), 2)) for _ in range(n_gates)]


def original_depth(gates: list[Gate]) -> int:
    return compute_depth([Operation("cx", gate.q1, gate.q2) for gate in gates])


def plot_tradeoff(rows: list[dict], output_path: Path) -> None:
    grouped: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        key = (row["normalized_cnot_count"], row["normalized_depth"])
        grouped.setdefault(key, []).append(row["decay_delta"])
    points = [
        (float(key[0]), float(key[1]), labels)
        for key, labels in grouped.items()
    ]
    points.sort(key=lambda item: item[0])

    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    ax.plot([item[0] for item in points], [item[1] for item in points], marker="o", color="#2f80ed", lw=2)
    for index, (xi, yi, labels) in enumerate(points):
        if len(labels) == 1:
            label = f"delta={labels[0]}"
        else:
            label = f"delta={labels[0]}..{labels[-1]}"
        if index == len(points) - 1:
            ax.text(xi - 0.002, yi - 0.012, label, fontsize=8, va="center", ha="right")
        else:
            ax.text(xi + 0.002, yi + 0.014, label, fontsize=8, va="center")
    ax.set_title("Decay heuristic changes the gate-count/depth operating point")
    ax.set_xlabel("Normalized CNOT-equivalent count")
    ax.set_ylabel("Normalized depth")
    ax.grid(alpha=0.25)
    ax.margins(x=0.08, y=0.12)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    outputs = ROOT / "outputs"
    data_dir = outputs / "data"
    figure_dir = outputs / "figures"
    check_dir = outputs / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)

    graph = tokyo_20_graph()
    n_qubits = 14
    n_gates = 100
    gates = random_interaction_circuit(n_qubits=n_qubits, n_gates=n_gates, seed=1)
    initial_layout = random_layout(n_qubits, graph.number_of_nodes(), random.Random(1001))
    base_depth = original_depth(gates)
    rows: list[dict] = []

    for delta in [0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]:
        result = route_sabre(
            gates=gates,
            graph=graph,
            initial_layout=list(initial_layout),
            extended_size=20,
            lookahead_weight=0.5,
            decay_delta=delta,
            use_decay=delta > 0,
        )
        total_cnot_equivalent = len(gates) + result.additional_cnot_gates
        rows.append(
            {
                "decay_delta": f"{delta:g}",
                "inserted_swaps": len(result.swaps),
                "additional_cnot_equivalent_gates": result.additional_cnot_gates,
                "output_cnot_equivalent_count": total_cnot_equivalent,
                "output_depth": result.output_depth,
                "normalized_cnot_count": f"{total_cnot_equivalent / len(gates):.6f}",
                "normalized_depth": f"{result.output_depth / base_depth:.6f}",
                "runtime_sec": f"{result.runtime_sec:.6f}",
                "hardware_compliant": result.hardware_compliant,
            }
        )

    csv_path = data_dir / "decay_tradeoff.csv"
    with csv_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    plot_tradeoff(rows, figure_dir / "decay_tradeoff.png")

    baseline = rows[0]
    changed_points = {
        (row["additional_cnot_equivalent_gates"], row["output_depth"]) for row in rows
    }
    depth_improvements = [
        row
        for row in rows[1:]
        if row["output_depth"] < baseline["output_depth"]
    ]
    strict_tradeoffs = [
        row
        for row in depth_improvements
        if row["additional_cnot_equivalent_gates"]
        > baseline["additional_cnot_equivalent_gates"]
    ]
    checks = {
        "target": "T003",
        "source": "decay heuristic section and Fig. 8 operating-point idea",
        "benchmark_note": "Seeded local random-interaction circuit, not the paper's hidden benchmark corpus.",
        "logical_qubits": n_qubits,
        "two_qubit_gates": n_gates,
        "original_depth": base_depth,
        "all_hardware_compliant": all(row["hardware_compliant"] for row in rows),
        "unique_operating_points": len(changed_points),
        "baseline_additional_cnot": baseline["additional_cnot_equivalent_gates"],
        "baseline_depth": baseline["output_depth"],
        "best_depth": min(row["output_depth"] for row in rows),
        "has_decay_depth_improvement": bool(depth_improvements),
        "has_gate_depth_tradeoff": bool(strict_tradeoffs),
    }
    checks["status"] = (
        "passed"
        if checks["all_hardware_compliant"]
        and checks["unique_operating_points"] >= 2
        and checks["has_gate_depth_tradeoff"]
        else "failed"
    )
    (check_dir / "decay_tradeoff.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
