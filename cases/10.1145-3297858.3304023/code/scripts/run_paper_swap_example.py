from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from benchmarks import paper_swap_example
from sabre import identity_layout, route_sabre, square_4_graph


def annotated_rows(result):
    layout = list(result.initial_layout)
    rows = []
    for index, op in enumerate(result.routed_ops):
        if op.name == "cx":
            p1, p2 = layout[op.q1], layout[op.q2]
        elif op.name == "swap":
            p1, p2 = op.p1, op.p2
            if op.q1 is not None:
                layout[op.q1] = p2
            if op.q2 is not None:
                layout[op.q2] = p1
        else:
            p1, p2 = None, None
        rows.append(
            {
                "index": index,
                "name": op.name,
                "logical_q1": op.q1,
                "logical_q2": op.q2,
                "physical_q1": p1,
                "physical_q2": p2,
            }
        )
    return rows


def plot_trace(rows, output_path: Path) -> None:
    colors = {"cx": "#2f80ed", "swap": "#eb5757"}
    fig, ax = plt.subplots(figsize=(8.0, 3.2))
    for row in rows:
        x = row["index"]
        y1 = row["logical_q1"]
        y2 = row["logical_q2"]
        label = "SWAP" if row["name"] == "swap" else "CX"
        ax.plot([x, x], [y1, y2], color=colors[row["name"]], lw=3, solid_capstyle="round")
        ax.scatter([x, x], [y1, y2], s=90, color=colors[row["name"]], zorder=3)
        ax.text(x, max(y1, y2) + 0.22, label, ha="center", va="bottom", fontsize=8)
    ax.set_title("Paper Fig. 3 routing trace: one inserted SWAP")
    ax.set_xlabel("Routed operation order")
    ax.set_ylabel("Logical qubit")
    ax.set_yticks([0, 1, 2, 3])
    ax.set_ylim(-0.5, 3.8)
    ax.set_xlim(-0.6, len(rows) - 0.4)
    ax.grid(axis="x", alpha=0.2)
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

    result = route_sabre(
        gates=paper_swap_example(),
        graph=square_4_graph(),
        initial_layout=identity_layout(4),
        extended_size=4,
        lookahead_weight=0.5,
        use_decay=False,
    )
    rows = annotated_rows(result)

    csv_path = data_dir / "paper_swap_example_ops.csv"
    with csv_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    plot_path = figure_dir / "paper_swap_example_trace.png"
    plot_trace(rows, plot_path)

    checks = {
        "target": "T001",
        "source": "paper Fig. 3 and Problem Analysis text",
        "hardware_compliant": result.hardware_compliant,
        "original_two_qubit_gates": result.original_two_qubit_gates,
        "inserted_swaps": len(result.swaps),
        "additional_cnot_equivalent_gates": result.additional_cnot_gates,
        "output_depth": result.output_depth,
        "expected_inserted_swaps": 1,
        "expected_additional_cnot_equivalent_gates": 3,
        "expected_output_depth": 8,
        "first_swap_logical_pair": result.swaps[0] if result.swaps else None,
    }
    checks["status"] = (
        "passed"
        if checks["hardware_compliant"]
        and checks["inserted_swaps"] == checks["expected_inserted_swaps"]
        and checks["additional_cnot_equivalent_gates"]
        == checks["expected_additional_cnot_equivalent_gates"]
        and checks["output_depth"] == checks["expected_output_depth"]
        else "failed"
    )

    check_path = check_dir / "paper_swap_example.json"
    check_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
