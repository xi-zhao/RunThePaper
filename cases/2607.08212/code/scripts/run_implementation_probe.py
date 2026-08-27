"""Source-blind execution proof for every locally implementable target.

The probe exercises the paper-derived algebra and the disclosed routing proxy
at reduced cost. It proves that the implementation is runnable; it does not
replace the frozen proxy campaign or turn proxy curves into paper-exact data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
import time
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
SRC = WORKSPACE / "src"
sys.path.insert(0, str(SRC))

import mobius_compiler as mobius  # noqa: E402
import proxy_router as router  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty probe output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _algebra_probe(variable_count: int) -> tuple[list[dict[str, Any]], bool]:
    if variable_count != 3:
        raise ValueError("the bounded exhaustive probe is declared for three variables")
    variables = tuple(range(variable_count))
    basis = mobius.subsets(variables)
    roundtrip_failures = 0
    maximum_error = 0.0
    for phase_mask in range(1 << len(basis)):
        table = {
            occupied: math.pi if phase_mask & (1 << index) else 0.0
            for index, occupied in enumerate(basis)
        }
        reconstructed = mobius.zeta_reconstruct(
            mobius.mobius_inversion(table, variables), variables
        )
        error = max(
            mobius.phase_distance(table[key], reconstructed[key]) for key in basis
        )
        maximum_error = max(maximum_error, error)
        roundtrip_failures += int(
            not mobius.phase_tables_equal(table, reconstructed)
        )

    polarity_failures = 0
    degree_three_terms = 0
    for negative_mask in range(1 << variable_count):
        negative = tuple(
            variable
            for index, variable in enumerate(variables)
            if negative_mask & (1 << index)
        )
        positive = tuple(variable for variable in variables if variable not in negative)
        table = mobius.clause_phase_table(
            variables,
            positive_literals=positive,
            negative_literals=negative,
        )
        terms = mobius.mobius_inversion(table, variables)
        reconstructed = mobius.zeta_reconstruct(terms, variables)
        polarity_failures += int(
            not mobius.phase_tables_equal(table, reconstructed)
        )
        degree_three_terms += int(terms[variables] != 0.0)

    rows = [
        {
            "suite": "boolean_phase_roundtrip",
            "cases": 1 << len(basis),
            "failures": roundtrip_failures,
            "maximum_phase_error": maximum_error,
        },
        {
            "suite": "three_sat_clause_polarities",
            "cases": 1 << variable_count,
            "failures": polarity_failures,
            "maximum_phase_error": 0.0,
        },
    ]
    passed = (
        roundtrip_failures == 0
        and polarity_failures == 0
        and degree_three_terms == 1 << variable_count
    )
    return rows, passed


def _routing_probe(
    config: dict[str, Any], architecture: router.ArchitectureParameters
) -> tuple[list[dict[str, Any]], bool]:
    qubits = int(config["qubits"])
    seed = int(config["seed"])
    clauses_per_qubit = int(config["clauses_per_qubit"])
    rows: list[dict[str, Any]] = []
    by_family: dict[str, dict[str, router.RoutedMetrics]] = {}
    for family in config["families"]:
        streams = router.benchmark_gate_streams(
            str(family), qubits, seed, clauses_per_qubit
        )
        by_family[str(family)] = {}
        for strategy, stream in streams.items():
            metrics = router.route_gate_stream(
                stream, qubits=qubits, architecture=architecture
            )
            by_family[str(family)][strategy] = metrics
            rows.append(
                {
                    "family": family,
                    "strategy": strategy,
                    "qubits": qubits,
                    "gate_count": metrics.gate_count,
                    "scheduled_stages": metrics.scheduled_stages,
                    "movement_events": metrics.movement_events,
                    "total_duration_us": metrics.total_duration_us,
                    "log_no_fault": metrics.log_no_fault,
                    "no_fault": metrics.no_fault,
                }
            )

    controls_equal = all(
        by_family[family]["mobius_native"]
        == by_family[family]["zap_decomposed"]
        for family in router.CONTROL_FAMILIES
    )
    many_body_advantage = all(
        by_family[family]["mobius_native"].log_no_fault
        > by_family[family]["zap_decomposed"].log_no_fault
        for family in router.MANY_BODY_FAMILIES
    )
    values_bounded = all(
        int(row["gate_count"]) > 0
        and 0.0 <= float(row["no_fault"]) <= 1.0
        and float(row["log_no_fault"]) <= 1e-12
        for row in rows
    )
    return rows, controls_equal and many_body_advantage and values_bounded


def _scaling_probe(
    config: dict[str, Any],
    architecture: router.ArchitectureParameters,
    clauses_per_qubit: int,
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    for family in config["families"]:
        for qubits in config["qubit_counts"]:
            for strategy, keep_native in (
                ("mobius_native", True),
                ("zap_decomposed", False),
            ):
                elapsed: list[float] = []
                metrics = None
                for _ in range(int(config["repetitions"])):
                    started = time.perf_counter()
                    terms = router.benchmark_projector_terms(
                        str(family),
                        int(qubits),
                        int(config["seed"]),
                        clauses_per_qubit,
                    )
                    stream = router.compile_projector_terms(
                        terms, keep_native=keep_native
                    )
                    metrics = router.route_gate_stream(
                        stream, qubits=int(qubits), architecture=architecture
                    )
                    elapsed.append(time.perf_counter() - started)
                assert metrics is not None
                rows.append(
                    {
                        "family": family,
                        "strategy": strategy,
                        "qubits": qubits,
                        "median_compile_route_seconds": sorted(elapsed)[
                            len(elapsed) // 2
                        ],
                        "gate_count": metrics.gate_count,
                        "total_duration_us": metrics.total_duration_us,
                    }
                )

    lookup = {
        (str(row["family"]), str(row["strategy"]), int(row["qubits"])): row
        for row in rows
    }
    duration_advantage = all(
        float(
            lookup[(str(family), "mobius_native", int(qubits))][
                "total_duration_us"
            ]
        )
        < float(
            lookup[(str(family), "zap_decomposed", int(qubits))][
                "total_duration_us"
            ]
        )
        for family in config["families"]
        for qubits in config["qubit_counts"]
    )
    timings_valid = all(
        float(row["median_compile_route_seconds"]) > 0.0 for row in rows
    )
    return rows, duration_advantage and timings_valid


def _sensitivity_probe(
    config: dict[str, Any],
    architecture: router.ArchitectureParameters,
    clauses_per_qubit: int,
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    for family in config["families"]:
        streams = router.benchmark_gate_streams(
            str(family),
            int(config["qubits"]),
            int(config["seed"]),
            clauses_per_qubit,
        )
        native = router.route_gate_stream(
            streams["mobius_native"],
            qubits=int(config["qubits"]),
            architecture=architecture,
        )
        baseline = router.route_gate_stream(
            streams["zap_decomposed"],
            qubits=int(config["qubits"]),
            architecture=architecture,
        )
        for p3 in config["p3_values"]:
            for p4 in config["p4_values"]:
                native_log = router.log_no_fault_with_native_fidelities(
                    native,
                    architecture,
                    f_native_3=1.0 - float(p3),
                    f_native_4=1.0 - float(p4),
                )
                rows.append(
                    {
                        "family": family,
                        "p3": p3,
                        "p4": p4,
                        "native_log_no_fault": native_log,
                        "zap_log_no_fault": baseline.log_no_fault,
                        "delta_log_no_fault": native_log - baseline.log_no_fault,
                    }
                )

    finite = all(
        math.isfinite(float(row[key]))
        for row in rows
        for key in (
            "native_log_no_fault",
            "zap_log_no_fault",
            "delta_log_no_fault",
        )
    )
    three_sat_p4_independent = all(
        len(
            {
                round(float(row["delta_log_no_fault"]), 12)
                for row in rows
                if row["family"] == "synthetic_3sat" and row["p3"] == p3
            }
        )
        == 1
        for p3 in config["p3_values"]
    )
    return rows, finite and three_sat_p4_independent


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.config.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    proxy_contract = json.loads(
        (WORKSPACE / "config" / "routing_benchmark_contract.json").read_text(
            encoding="utf-8"
        )
    )
    architecture = router.ArchitectureParameters.from_contract(proxy_contract)
    clauses_per_qubit = int(parameters["routing"]["clauses_per_qubit"])

    algebra_rows, algebra_ok = _algebra_probe(int(parameters["algebra_variables"]))
    routing_rows, routing_ok = _routing_probe(parameters["routing"], architecture)
    scaling_rows, scaling_ok = _scaling_probe(
        parameters["scaling"], architecture, clauses_per_qubit
    )
    sensitivity_rows, sensitivity_ok = _sensitivity_probe(
        parameters["sensitivity"], architecture, clauses_per_qubit
    )

    output_root = WORKSPACE / "outputs"
    data_dir = output_root / "data" / "implementation_probe"
    checks_dir = output_root / "checks" / "implementation_probe"
    _write_csv(data_dir / "algebra_smoke.csv", algebra_rows)
    _write_csv(data_dir / "routing_smoke.csv", routing_rows)
    _write_csv(data_dir / "scaling_smoke.csv", scaling_rows)
    _write_csv(data_dir / "sensitivity_smoke.csv", sensitivity_rows)

    target_results = {
        "ALGEBRA_CORE": {"status": "passed" if algebra_ok else "failed"},
        "ROUTING_PROXY": {"status": "passed" if routing_ok else "failed"},
        "ROUTING_PROXY_SCALING": {
            "status": "passed" if scaling_ok else "failed"
        },
        "ROUTING_PROXY_SENSITIVITY": {
            "status": "passed" if sensitivity_ok else "failed"
        },
    }
    summary = {
        "schema_version": 1,
        "paper_id": payload["paper_id"],
        "profile": parameters["profile"],
        "status": (
            "passed"
            if all(
                result["status"] == "passed"
                for result in target_results.values()
            )
            else "failed"
        ),
        "target_results": target_results,
        "generated_data_provenance": "independent_numerics",
        "scientific_role": "implementation_smoke_only",
        "paper_scale_outputs_replaced": False,
        "claim_boundary": (
            "The probe validates runnable algebra and the disclosed proxy model. "
            "It does not reconstruct unpublished benchmark circuits, ZX routes, "
            "or paper-exact curves."
        ),
    }
    checks_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "implementation_probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
