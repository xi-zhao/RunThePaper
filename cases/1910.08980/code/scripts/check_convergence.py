"""Post-run refinement check on frozen representative instances."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rqaoa import optimize_qaoa1, run_rqaoa1  # noqa: E402


def main() -> int:
    checks: list[dict[str, object]] = []
    specifications = [(32, 8, [0, 7, 15]), (100, 30, [0, 7, 15])]
    for n, cutoff, indices in specifications:
        data_path = WORKSPACE / "outputs" / "data" / f"main_fig1_n{n}.csv"
        matrix_path = WORKSPACE / "outputs" / "data" / f"main_fig1_n{n}_instances.npz"
        with data_path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        matrices = np.load(matrix_path)["couplings"]
        for index in indices:
            matrix = matrices[index]
            qaoa = optimize_qaoa1(
                matrix, gamma_grid_points=257, local_candidates=8
            )
            rqaoa = run_rqaoa1(
                matrix,
                cutoff=cutoff,
                gamma_grid_points=257,
                local_candidates=8,
                exact_time_limit_seconds=300.0,
            )
            baseline_qaoa = float(rows[index]["qaoa_expected_energy"])
            baseline_rqaoa = float(rows[index]["rqaoa_energy"])
            checks.append(
                {
                    "n": n,
                    "instance": index + 1,
                    "baseline_gamma_grid_points": 129,
                    "refined_gamma_grid_points": 257,
                    "qaoa_energy_absolute_difference": abs(
                        qaoa.expected_energy - baseline_qaoa
                    ),
                    "rqaoa_energy_difference": rqaoa.energy - baseline_rqaoa,
                    "passed": (
                        abs(qaoa.expected_energy - baseline_qaoa) <= 1e-8
                        and rqaoa.energy == baseline_rqaoa
                    ),
                }
            )
            print(
                f"n={n} instance={index + 1}: "
                f"dQAOA={checks[-1]['qaoa_energy_absolute_difference']:.3e}, "
                f"dRQAOA={checks[-1]['rqaoa_energy_difference']}",
                flush=True,
            )
    payload = {
        "schema_version": 1,
        "paper_id": "1910.08980",
        "status": "passed" if all(bool(item["passed"]) for item in checks) else "failed",
        "frozen_input_role": "post_run_convergence_check_only",
        "checks": checks,
    }
    output = WORKSPACE / "outputs" / "checks" / "convergence.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
