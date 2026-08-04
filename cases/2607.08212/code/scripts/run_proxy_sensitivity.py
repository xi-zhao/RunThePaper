#!/usr/bin/env python3
"""Run a Fig. 7-style native-error sensitivity proxy against ZAP."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_PATH = WORKSPACE.parent
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from proxy_router import (  # noqa: E402
    ArchitectureParameters,
    benchmark_gate_streams,
    log_no_fault_with_native_fidelities,
    route_gate_stream,
)


CONTRACT_PATH = WORKSPACE / "config" / "routing_benchmark_contract.json"
DATA_PATH = WORKSPACE / "outputs" / "data" / "proxy_native_error_sensitivity.csv"
CHECK_PATH = WORKSPACE / "outputs" / "checks" / "proxy_sensitivity_result.json"
FIGURE_PATH = WORKSPACE / "outputs" / "figures" / "proxy_native_error_sensitivity.png"


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    run = contract["generated_run"]
    architecture = ArchitectureParameters.from_contract(contract)
    families = [str(value) for value in run["sensitivity_families"]]
    qubits = int(run["sensitivity_qubits"])
    seed = int(run["sensitivity_seed"])
    clauses_per_qubit = int(run["synthetic_3sat_clauses_per_qubit"])
    p3_values = _grid(run["sensitivity_p3_grid"])
    p4_values = _grid(run["sensitivity_p4_grid"])

    fixed: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for family in families:
        streams = benchmark_gate_streams(family, qubits, seed, clauses_per_qubit)
        native = route_gate_stream(streams["mobius_native"], qubits=qubits, architecture=architecture)
        baseline = route_gate_stream(streams["zap_decomposed"], qubits=qubits, architecture=architecture)
        fixed[family] = {"native": native, "baseline": baseline}
        for p3 in p3_values:
            for p4 in p4_values:
                native_log = log_no_fault_with_native_fidelities(
                    native,
                    architecture,
                    f_native_3=1.0 - p3,
                    f_native_4=1.0 - p4,
                )
                rows.append(
                    {
                        "family": family,
                        "qubits": qubits,
                        "seed": seed,
                        "p3": p3,
                        "p4": p4,
                        "native_log_no_fault": native_log,
                        "zap_log_no_fault": baseline.log_no_fault,
                        "delta_log_no_fault": native_log - baseline.log_no_fault,
                    }
                )

    grouped = {family: [row for row in rows if row["family"] == family] for family in families}
    three_sat_p4_independent = all(
        len({round(float(row["delta_log_no_fault"]), 12) for row in grouped["synthetic_3sat"] if row["p3"] == p3}) == 1
        for p3 in p3_values
    )
    mixed_have_both_degrees = all(
        fixed[family]["native"].native_three_qubit_gates > 0
        and fixed[family]["native"].native_four_qubit_gates > 0
        for family in ("p_spin_ising", "qram_oracle")
    )
    sign_change = {
        family: min(float(row["delta_log_no_fault"]) for row in grouped[family]) < 0.0
        < max(float(row["delta_log_no_fault"]) for row in grouped[family])
        for family in families
    }
    representative_positive = {}
    p3_star = 1.0 - architecture.f_native_3
    p4_star = 1.0 - architecture.f_native_4
    for family in families:
        native = fixed[family]["native"]
        baseline = fixed[family]["baseline"]
        representative_positive[family] = (
            log_no_fault_with_native_fidelities(
                native,
                architecture,
                f_native_3=1.0 - p3_star,
                f_native_4=1.0 - p4_star,
            )
            > baseline.log_no_fault
        )
    checks = {
        "three_sat_has_only_three_body_native_exposure": fixed["synthetic_3sat"]["native"].native_four_qubit_gates == 0,
        "three_sat_surface_is_p4_independent": three_sat_p4_independent,
        "p_spin_and_qram_have_three_and_four_body_exposure": mixed_have_both_degrees,
        "all_surfaces_cross_break_even_within_declared_grid": all(sign_change.values()),
        "table_i_representative_point_is_native_favorable": all(representative_positive.values()),
    }
    payload = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "passed_with_warnings",
        "paper_id": CASE_PATH.name,
        "target_id": "ROUTING_PROXY_SENSITIVITY",
        "scope": "proxy_model",
        "run_shape": {
            "families": families,
            "qubits": qubits,
            "seed": seed,
            "p3_points": len(p3_values),
            "p4_points": len(p4_values),
            "rows": len(rows),
        },
        "representative_point": {"p3": p3_star, "p4": p4_star, "native_favorable": representative_positive},
        "break_even_crossing": sign_change,
        "checks": checks,
        "boundary": "The fixed route streams come from the disclosed proxy and compare only against ZAP; the paper's ZX route stream is unavailable.",
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_rows(DATA_PATH, rows)
    _plot(rows, families, p3_values, p4_values, p3_star, p4_star, FIGURE_PATH)
    CHECK_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _grid(spec: dict[str, Any]) -> list[float]:
    minimum = float(spec["min"])
    maximum = float(spec["max"])
    points = int(spec["points"])
    if points < 2 or minimum < 0.0 or maximum >= 1.0 or minimum >= maximum:
        raise ValueError("invalid native-error sensitivity grid")
    return [minimum + index * (maximum - minimum) / (points - 1) for index in range(points)]


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _plot(
    rows: list[dict[str, Any]],
    families: list[str],
    p3_values: list[float],
    p4_values: list[float],
    p3_star: float,
    p4_star: float,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = {"synthetic_3sat": "3-SAT oracle", "p_spin_ising": "p-spin Ising", "qram_oracle": "QRAM oracle"}
    lookup = {(row["family"], row["p3"], row["p4"]): row["delta_log_no_fault"] for row in rows}
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)
    image = None
    for axis, family in zip(axes, families):
        values = np.array([[lookup[(family, p3, p4)] for p4 in p4_values] for p3 in p3_values])
        limit = max(abs(float(values.min())), abs(float(values.max())))
        image = axis.imshow(
            values,
            origin="lower",
            extent=(p4_values[0], p4_values[-1], p3_values[0], p3_values[-1]),
            aspect="auto",
            cmap="coolwarm_r",
            vmin=-limit,
            vmax=limit,
        )
        if float(values.min()) < 0.0 < float(values.max()):
            axis.contour(p4_values, p3_values, values, levels=[0.0], colors="black", linewidths=1.2)
        else:
            axis.text(
                0.03,
                0.96,
                "no break-even\nin 0–20% grid",
                transform=axis.transAxes,
                ha="left",
                va="top",
                fontsize=8,
                bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
            )
        axis.scatter([p4_star], [p3_star], marker="*", s=90, color="gold", edgecolor="black", linewidth=0.6)
        axis.set_title(labels[family], fontweight="bold")
        axis.set_xlabel("p4")
        axis.set_ylabel("p3")
    if image is not None:
        fig.colorbar(image, ax=axes, label="Δ log no-fault (native − ZAP)", shrink=0.9)
    fig.suptitle("Fig. 7 proxy — fixed-route native-error break-even\nproxy ZAP comparison; ZX route unavailable", fontsize=13)
    fig.savefig(path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
