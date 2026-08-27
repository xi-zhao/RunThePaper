from __future__ import annotations

import csv
import json
from pathlib import Path
import random
import sys
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from benchmarks import path_ising, qft_cnot_dependencies
from sabre import (
    Operation,
    check_hardware_compliance,
    compute_depth,
    random_layout,
    route_sabre,
    sabre_forward_backward_forward,
    tokyo_20_graph,
)


warnings.filterwarnings("ignore")


def original_depth(gates) -> int:
    return compute_depth([Operation("cx", gate.q1, gate.q2) for gate in gates])


def result_row(benchmark: str, mode: str, gates, result) -> dict:
    return {
        "benchmark": benchmark,
        "mode": mode,
        "logical_qubits": 1 + max(max(g.q1, g.q2) for g in gates),
        "original_two_qubit_gates": len(gates),
        "original_depth": original_depth(gates),
        "inserted_swaps": len(result.swaps),
        "additional_cnot_equivalent_gates": result.additional_cnot_gates,
        "output_depth": result.output_depth,
        "runtime_sec": f"{result.runtime_sec:.6f}",
        "hardware_compliant": result.hardware_compliant,
    }


def plot_qft(rows: list[dict], output_path: Path) -> None:
    qft_rows = [row for row in rows if row["benchmark"].startswith("qft")]
    names = sorted({row["benchmark"] for row in qft_rows}, key=lambda name: int(name[3:]))
    first_add = [int(next(row for row in qft_rows if row["benchmark"] == name and row["mode"] == "first")["additional_cnot_equivalent_gates"]) for name in names]
    fbf_add = [int(next(row for row in qft_rows if row["benchmark"] == name and row["mode"] == "forward_backward_forward")["additional_cnot_equivalent_gates"]) for name in names]
    first_depth = [int(next(row for row in qft_rows if row["benchmark"] == name and row["mode"] == "first")["output_depth"]) for name in names]
    fbf_depth = [int(next(row for row in qft_rows if row["benchmark"] == name and row["mode"] == "forward_backward_forward")["output_depth"]) for name in names]

    x = range(len(names))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    axes[0].bar([i - width / 2 for i in x], first_add, width=width, label="first traversal", color="#7b8794")
    axes[0].bar([i + width / 2 for i in x], fbf_add, width=width, label="forward-backward-forward", color="#2f80ed")
    axes[0].set_title("Additional CNOT-equivalent gates")
    axes[0].set_xticks(list(x), names)
    axes[0].set_ylabel("Count")

    axes[1].bar([i - width / 2 for i in x], first_depth, width=width, label="first traversal", color="#7b8794")
    axes[1].bar([i + width / 2 for i in x], fbf_depth, width=width, label="forward-backward-forward", color="#27ae60")
    axes[1].set_title("Output depth")
    axes[1].set_xticks(list(x), names)
    axes[1].set_ylabel("Depth")

    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
        ax.legend(frameon=False)
    fig.suptitle("Reverse traversal improves the initial mapping on QFT-style circuits")
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
    rows: list[dict] = []

    ising_layout = [0, 1, 2, 3, 4, 9, 14, 19, 18, 17]
    ising_gates = path_ising(10, rounds=8)
    ising = route_sabre(ising_gates, graph, ising_layout, use_decay=False)
    rows.append(result_row("ising10_topology_aligned", "single_forward", ising_gates, ising))

    qft_checks = {}
    for n_qubits in [6, 8, 10]:
        gates = qft_cnot_dependencies(n_qubits)
        first_layout = random_layout(n_qubits, graph.number_of_nodes(), random.Random(3))
        first = route_sabre(
            gates=gates,
            graph=graph,
            initial_layout=first_layout,
            extended_size=20,
            lookahead_weight=0.5,
            decay_delta=0.001,
            use_decay=True,
        )
        fbf = sabre_forward_backward_forward(
            gates=gates,
            graph=graph,
            attempts=3,
            seed=3,
            extended_size=20,
            lookahead_weight=0.5,
            decay_delta=0.001,
            use_decay=True,
        )
        name = f"qft{n_qubits}"
        rows.append(result_row(name, "first", gates, first))
        rows.append(result_row(name, "forward_backward_forward", gates, fbf))
        qft_checks[name] = {
            "first_additional_cnot": first.additional_cnot_gates,
            "fbf_additional_cnot": fbf.additional_cnot_gates,
            "first_depth": first.output_depth,
            "fbf_depth": fbf.output_depth,
            "fbf_not_worse_on_additional_gates": fbf.additional_cnot_gates <= first.additional_cnot_gates,
            "fbf_not_worse_on_depth": fbf.output_depth <= first.output_depth,
            "hardware_compliant": first.hardware_compliant and fbf.hardware_compliant,
        }

    csv_path = data_dir / "core_benchmarks.csv"
    with csv_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    plot_qft(rows, figure_dir / "core_benchmarks_qft.png")

    checks = {
        "target": "T002",
        "source": "Algorithm 1, reverse traversal section, and evaluation metrics",
        "all_hardware_compliant": all(row["hardware_compliant"] for row in rows),
        "ising_topology_aligned_additional_cnot": ising.additional_cnot_gates,
        "qft_checks": qft_checks,
    }
    checks["status"] = (
        "passed"
        if checks["all_hardware_compliant"]
        and checks["ising_topology_aligned_additional_cnot"] == 0
        and all(item["fbf_not_worse_on_additional_gates"] for item in qft_checks.values())
        and all(item["fbf_not_worse_on_depth"] for item in qft_checks.values())
        else "failed"
    )
    (check_dir / "core_benchmarks.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
