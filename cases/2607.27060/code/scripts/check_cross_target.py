#!/usr/bin/env python3
"""Check claims that couple multiple frozen figure targets."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from trotter_bounds import write_json  # noqa: E402


def load_target(slug: str) -> dict[str, object]:
    path = WORKSPACE / "outputs" / "checks" / "targets" / f"{slug}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def series(rows: list[dict[str, object]], key: str) -> list[int]:
    return [int(row[key]) for row in rows]


def main() -> int:
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    records = {
        slug: load_target(slug)
        for slug in (
            "fig002a",
            "fig002b",
            "fig002c",
            "fig002d",
            "fig003a",
            "fig003b",
            "fig003c",
            "fig003d",
        )
    }
    checks: dict[str, bool] = {}
    crossover_evidence: dict[str, dict[str, list[int]]] = {}

    checks["all_target_checks_passed"] = all(
        record["status"] == "passed"
        and record["scientific_checks"]["all_passed"] is True
        for record in records.values()
    )

    for figure in ("fig002", "fig003"):
        det1 = records[f"{figure}a"]["rows"]
        ran1 = records[f"{figure}b"]["rows"]
        det2 = records[f"{figure}c"]["rows"]
        ran2 = records[f"{figure}d"]["rows"]
        suffix = figure[-3:]

        checks[f"{suffix}_shared_M_grid"] = (
            series(det1, "M")
            == series(ran1, "M")
            == series(det2, "M")
            == series(ran2, "M")
        )
        checks[f"{suffix}_ran1_det2_equal_N_analytic"] = (
            series(ran1, "N_analytic") == series(det2, "N_analytic")
        )
        checks[f"{suffix}_ran1_det2_equal_N_min"] = (
            series(ran1, "N_min") == series(det2, "N_min")
        )
        checks[f"{suffix}_det2_gate_factor_two_analytic"] = all(
            int(right["g_analytic"]) == 2 * int(left["g_analytic"])
            for left, right in zip(ran1, det2, strict=True)
        )
        checks[f"{suffix}_det2_gate_factor_two_min"] = all(
            int(right["g_min"]) == 2 * int(left["g_min"])
            for left, right in zip(ran1, det2, strict=True)
        )
        checks[f"{suffix}_ran2_lowest_N_analytic"] = all(
            int(row_d["N_analytic"])
            < min(int(row["N_analytic"]) for row in (row_a, row_b, row_c))
            for row_a, row_b, row_c, row_d in zip(
                det1, ran1, det2, ran2, strict=True
            )
        )
        checks[f"{suffix}_ran2_lowest_N_min"] = all(
            int(row_d["N_min"])
            < min(int(row["N_min"]) for row in (row_a, row_b, row_c))
            for row_a, row_b, row_c, row_d in zip(
                det1, ran1, det2, ran2, strict=True
            )
        )
        checks[f"{suffix}_ran2_lowest_g_analytic"] = all(
            int(row_d["g_analytic"])
            < min(int(row["g_analytic"]) for row in (row_a, row_b, row_c))
            for row_a, row_b, row_c, row_d in zip(
                det1, ran1, det2, ran2, strict=True
            )
        )
        checks[f"{suffix}_ran2_lowest_g_min"] = all(
            int(row_d["g_min"])
            < min(int(row["g_min"]) for row in (row_a, row_b, row_c))
            for row_a, row_b, row_c, row_d in zip(
                det1, ran1, det2, ran2, strict=True
            )
        )
        crossover_evidence[suffix] = {
            "M_where_ran2_has_lowest_g_analytic": [
                int(row_d["M"])
                for row_a, row_b, row_c, row_d in zip(
                    det1, ran1, det2, ran2, strict=True
                )
                if int(row_d["g_analytic"])
                < min(
                    int(row["g_analytic"])
                    for row in (row_a, row_b, row_c)
                )
            ],
            "M_where_ran2_has_lowest_g_min": [
                int(row_d["M"])
                for row_a, row_b, row_c, row_d in zip(
                    det1, ran1, det2, ran2, strict=True
                )
                if int(row_d["g_min"])
                < min(int(row["g_min"]) for row in (row_a, row_b, row_c))
            ],
        }

    checks["analytic_bounds_not_below_optimised"] = all(
        int(row["N_analytic"]) >= int(row["N_min"])
        and int(row["g_analytic"]) >= int(row["g_min"])
        for record in records.values()
        for row in record["rows"]
    )
    tfim_largest = records["fig003a"]["rows"][-1]
    tfim_gate_gap = int(tfim_largest["g_analytic"]) - int(
        tfim_largest["g_min"]
    )
    checks["tfim_reported_gate_gap_rounds_to_1_89e12"] = (
        round(tfim_gate_gap / 1.0e12, 2) == 1.89
    )

    reproduction_checks = {
        key: value
        for key, value in checks.items()
        if "ran2_lowest_g_" not in key
    }
    narrative_gate_checks = {
        key: value
        for key, value in checks.items()
        if "ran2_lowest_g_" in key
    }
    if not all(reproduction_checks.values()):
        status = "failed"
    elif all(narrative_gate_checks.values()):
        status = "passed"
    else:
        status = "passed_with_findings"
    payload = {
        "schema_version": 1,
        "status": status,
        "scope": [
            "T-FIG002A",
            "T-FIG002B",
            "T-FIG002C",
            "T-FIG002D",
            "T-FIG003A",
            "T-FIG003B",
            "T-FIG003C",
            "T-FIG003D",
        ],
        "generated_data_provenance": "independent_numerics",
        "checks": checks,
        "claim_results": {
            "CLM-ANALYTIC-CONSERVATIVE": {
                "status": "verified",
                "passed": checks["analytic_bounds_not_below_optimised"],
            },
            "CLM-RAN1-DET2-EQUAL-N": {
                "status": "verified",
                "passed": all(
                    value
                    for key, value in checks.items()
                    if "ran1_det2" in key or "det2_gate_factor_two" in key
                ),
            },
            "CLM-RAN2-LOWEST-REPORTED": {
                "status": "partially_supported",
                "fewest_Trotter_steps_on_full_grid": all(
                    value
                    for key, value in checks.items()
                    if "ran2_lowest_N_" in key
                ),
                "lowest_gate_complexity_on_full_grid": all(
                    narrative_gate_checks.values()
                ),
                "crossover_evidence": crossover_evidence,
            },
        },
        "reported_narrative_check": {
            "model": "tfim_lattice",
            "M": int(tfim_largest["M"]),
            "analytic_minus_optimised_gate_count": tfim_gate_gap,
            "in_trillions": tfim_gate_gap / 1.0e12,
        },
        "findings": (
            []
            if all(narrative_gate_checks.values())
            else [
                {
                    "severity": "warning",
                    "code": "paper_ran2_gate_claim_not_uniform_on_frozen_grids",
                    "message": (
                        "The second-order randomised formula has the fewest "
                        "Trotter steps everywhere, but its 2MN per-step factor "
                        "means it does not have the lowest gate complexity at "
                        "every small-M point. It becomes lowest only after the "
                        "crossovers recorded above."
                    ),
                }
            ]
        ),
        "timing": {
            "wall_seconds": time.perf_counter() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu,
        },
    }
    output = (
        WORKSPACE / "outputs" / "checks" / "cross_target_consistency.json"
    )
    write_json(output, payload)
    print(json.dumps(payload, indent=2))
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
