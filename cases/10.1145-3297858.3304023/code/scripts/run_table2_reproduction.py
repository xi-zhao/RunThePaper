from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import random
import sys
from concurrent.futures import ProcessPoolExecutor

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PILOT_ROOT = ROOT.parents[0]
sys.path.insert(0, str(ROOT / "src"))

from qasm_io import load_qasm_circuit
from sabre import random_layout, route_sabre, tokyo_20_graph


def run_single_attempt(args: tuple[list, int, int, bool]) -> dict:
    cx_gates, n_qubits, attempt_seed, use_decay = args
    graph = tokyo_20_graph()
    layout = random_layout(n_qubits, graph.number_of_nodes(), random.Random(attempt_seed))
    first = route_sabre(
        gates=cx_gates,
        graph=graph,
        initial_layout=list(layout),
        extended_size=20,
        lookahead_weight=0.5,
        decay_delta=0.001,
        use_decay=use_decay,
    )
    reverse = route_sabre(
        gates=list(reversed(cx_gates)),
        graph=graph,
        initial_layout=first.final_layout,
        extended_size=20,
        lookahead_weight=0.5,
        decay_delta=0.001,
        use_decay=use_decay,
    )
    final = route_sabre(
        gates=cx_gates,
        graph=graph,
        initial_layout=reverse.final_layout,
        extended_size=20,
        lookahead_weight=0.5,
        decay_delta=0.001,
        use_decay=use_decay,
    )
    return {
        "seed": attempt_seed,
        "g_la": first.additional_cnot_gates,
        "g_op": final.additional_cnot_gates,
        "first_depth": first.output_depth,
        "op_depth": final.output_depth,
        "first_compliant": first.hardware_compliant,
        "op_compliant": final.hardware_compliant,
    }


def read_expected() -> list[dict]:
    path = ROOT / "references" / "table2_expected.csv"
    with path.open() as file:
        return list(csv.DictReader(file))


def qasm_path(row: dict) -> Path:
    return PILOT_ROOT / "raw" / "benchmarks" / "table2" / row["type"] / f"{row['name']}.qasm"


def route_attempts(circuit, attempts: int, seed: int, use_decay: bool, workers: int) -> dict:
    task_args = [
        (circuit.cx_gates, circuit.n_qubits, seed + attempt, use_decay)
        for attempt in range(attempts)
    ]
    if workers <= 1:
        rows = [run_single_attempt(item) for item in task_args]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            rows = list(executor.map(run_single_attempt, task_args, chunksize=1))

    for attempt, row in enumerate(rows):
        row["attempt"] = attempt

    best_first = min(rows, key=lambda row: (row["g_la"], row["first_depth"], row["seed"]))
    best_op = min(rows, key=lambda row: (row["g_op"], row["op_depth"], row["seed"]))

    return {
        "best_g_la": best_first["g_la"],
        "best_g_op": best_op["g_op"],
        "best_first_depth": best_first["first_depth"],
        "best_op_depth": best_op["op_depth"],
        "all_compliant": all(row["first_compliant"] and row["op_compliant"] for row in rows),
        "attempt_rows": rows,
    }


def value_to_int(value: str) -> int | None:
    if value in {"OOM", "N/A", ""}:
        return None
    return int(value)


def compare_int(actual: int | None, expected: int | None) -> str:
    if expected is None:
        return "not_applicable"
    if actual is None:
        return "missing"
    return "exact" if actual == expected else "mismatch"


def plot_comparison(rows: list[dict], output_path: Path) -> None:
    runnable = [
        row
        for row in rows
        if row["status"] == "ran"
        and row["sabre_g_op"] not in {"OOM", "N/A", ""}
    ]
    if not runnable:
        return
    labels = [row["name"] for row in runnable]
    expected = [int(row["sabre_g_op"]) for row in runnable]
    actual = [int(row["actual_g_op"]) for row in runnable]
    x = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 0.46), 4.8))
    ax.bar([i - 0.18 for i in x], expected, width=0.36, label="paper Table II", color="#7b8794")
    ax.bar([i + 0.18 for i in x], actual, width=0.36, label="local reconstruction", color="#2f80ed")
    ax.set_ylabel("Additional CNOT-equivalent gates")
    ax.set_title("Table II g_op comparison")
    ax.set_xticks(x, labels, rotation=65, ha="right", fontsize=8)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--types", default="small,sim,qft,large")
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--use-decay", action="store_true")
    parser.add_argument("--max-cx", type=int, default=0, help="Skip circuits with more CX gates; 0 means no limit.")
    parser.add_argument("--workers", type=int, default=1, help="Parallel seed attempts per benchmark row.")
    args = parser.parse_args()
    workers = max(1, min(args.workers, os.cpu_count() or 1))

    selected_types = set(args.types.split(","))
    outputs = ROOT / "outputs"
    data_dir = outputs / "data"
    figure_dir = outputs / "figures"
    check_dir = outputs / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)

    expected_rows = [row for row in read_expected() if row["type"] in selected_types]
    result_rows: list[dict] = []
    attempt_rows: list[dict] = []

    for expected in expected_rows:
        path = qasm_path(expected)
        if not path.exists():
            result_rows.append(
                {
                    **expected,
                    "qasm_path": str(path),
                    "qasm_n": "",
                    "qasm_g_ori": "",
                    "qasm_cx": "",
                    "qasm_depth": "",
                    "n_match": False,
                    "g_ori_match": False,
                    "actual_g_la": "",
                    "actual_g_op": "",
                    "actual_first_depth": "",
                    "actual_op_depth": "",
                    "all_compliant": "",
                    "g_la_match": "missing",
                    "g_op_match": "missing",
                    "status": "missing_qasm",
                }
            )
            continue

        circuit = load_qasm_circuit(path)
        if args.max_cx and len(circuit.cx_gates) > args.max_cx:
            status = "skipped_max_cx"
            route = None
        else:
            status = "ran"
            route = route_attempts(circuit, args.attempts, args.seed, args.use_decay, workers)
            for attempt in route["attempt_rows"]:
                attempt_rows.append({"name": expected["name"], "type": expected["type"], **attempt})

        actual_g_la = route["best_g_la"] if route else None
        actual_g_op = route["best_g_op"] if route else None
        expected_g_la = value_to_int(expected["sabre_g_la"])
        expected_g_op = value_to_int(expected["sabre_g_op"])
        result_rows.append(
            {
                **expected,
                "qasm_path": str(path.relative_to(PILOT_ROOT)),
                "qasm_n": circuit.n_qubits,
                "qasm_g_ori": circuit.total_ops,
                "qasm_cx": len(circuit.cx_gates),
                "qasm_depth": circuit.original_depth,
                "n_match": circuit.n_qubits == value_to_int(expected["n"]),
                "g_ori_match": circuit.total_ops == value_to_int(expected["g_ori"]),
                "actual_g_la": "" if actual_g_la is None else actual_g_la,
                "actual_g_op": "" if actual_g_op is None else actual_g_op,
                "actual_first_depth": "" if route is None else route["best_first_depth"],
                "actual_op_depth": "" if route is None else route["best_op_depth"],
                "all_compliant": "" if route is None else route["all_compliant"],
                "g_la_match": compare_int(actual_g_la, expected_g_la),
                "g_op_match": compare_int(actual_g_op, expected_g_op),
                "status": status,
            }
        )

    result_csv = data_dir / "table2_reproduction.csv"
    with result_csv.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(result_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(result_rows)

    attempts_csv = data_dir / "table2_attempts.csv"
    if attempt_rows:
        with attempts_csv.open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(attempt_rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(attempt_rows)

    plot_comparison(result_rows, figure_dir / "table2_gop_comparison.png")

    ran_rows = [row for row in result_rows if row["status"] == "ran"]
    checks = {
        "target": "T004",
        "types": sorted(selected_types),
        "attempts": args.attempts,
        "seed": args.seed,
        "use_decay": args.use_decay,
        "workers": workers,
        "rows_total": len(result_rows),
        "rows_ran": len(ran_rows),
        "qasm_g_ori_matches": sum(row["g_ori_match"] in {True, "True"} for row in result_rows),
        "qasm_n_matches": sum(row["n_match"] in {True, "True"} for row in result_rows),
        "hardware_compliant_rows": sum(row["all_compliant"] in {True, "True"} for row in ran_rows),
        "g_la_exact_matches": sum(row["g_la_match"] == "exact" for row in ran_rows),
        "g_op_exact_matches": sum(row["g_op_match"] == "exact" for row in ran_rows),
        "mismatched_n": [
            {"name": row["name"], "paper_n": row["n"], "qasm_n": row["qasm_n"]}
            for row in result_rows
            if row["n_match"] in {False, "False"}
        ],
        "skipped": [
            {"name": row["name"], "status": row["status"], "qasm_cx": row["qasm_cx"]}
            for row in result_rows
            if row["status"] != "ran"
        ],
    }
    checks["status"] = (
        "passed_exact"
        if checks["rows_ran"] == checks["rows_total"]
        and checks["g_op_exact_matches"] == checks["rows_ran"]
        else "partial"
    )
    (check_dir / "table2_reproduction.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
