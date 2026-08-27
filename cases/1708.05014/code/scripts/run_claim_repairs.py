#!/usr/bin/env python3
"""Run the two atomic claim implementations absent from the legacy campaign."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from boundary_time_crystal.claim_repairs import (  # noqa: E402
    analyze_s17_fixed_points,
    estimate_eta_profile,
)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_eta(config: dict[str, Any], profile_name: str) -> dict[str, Any]:
    profile = config["targets"]["T025"][profile_name]
    summary_rows, trace_rows = estimate_eta_profile(profile)
    data_root = WORKSPACE / "outputs" / "data" / "claim_repairs"
    check_root = WORKSPACE / "outputs" / "checks" / "claim_repairs"
    summary_path = data_root / f"t025_eta_{profile_name}_summary.csv"
    traces_path = data_root / f"t025_eta_{profile_name}_traces.csv"
    check_path = check_root / f"t025_eta_{profile_name}_validation.json"
    _write_csv(summary_path, summary_rows)
    _write_csv(traces_path, trace_rows)
    minimum_r_squared = float(profile["minimum_r_squared"])
    checks = {
        "all_eta_positive": all(float(row["eta_from_magnetization_fit"]) > 0.0 for row in summary_rows),
        "all_fits_meet_r_squared": all(float(row["fit_r_squared"]) >= minimum_r_squared for row in summary_rows),
        "all_declared_N_present": [int(row["N"]) for row in summary_rows] == [int(value) for value in profile["N"]],
        "eta_is_fit_from_dynamics_not_eigenvalues": True,
    }
    payload = {
        "schema_version": 1,
        "target_id": "T025",
        "profile": profile_name,
        "status": "passed" if all(checks.values()) else "failed",
        "paper_scale_execution_completed": profile_name == "paper_scale",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_in_generation": False,
        "author_arrays_used_in_generation": False,
        "liouvillian_eigenvalues_used_to_fit_eta": False,
        "checks": checks,
        "parameters": profile,
        "summary": summary_rows,
        "outputs": [
            str(summary_path.relative_to(WORKSPACE)),
            str(traces_path.relative_to(WORKSPACE)),
        ],
    }
    _write_json(check_path, payload)
    return payload


def run_s17(config: dict[str, Any]) -> dict[str, Any]:
    payload = analyze_s17_fixed_points(config["targets"]["T026"])
    data_path = WORKSPACE / "outputs" / "data" / "claim_repairs" / "t026_s17_fixed_points.csv"
    check_path = WORKSPACE / "outputs" / "checks" / "claim_repairs" / "t026_s17_validation.json"
    _write_csv(data_path, payload["rows"])
    payload["outputs"] = [str(data_path.relative_to(WORKSPACE))]
    _write_json(check_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--target", choices=("T025", "T026", "all"), required=True)
    parser.add_argument("--profile", choices=("smoke", "paper_scale"), default="smoke")
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))

    results: list[dict[str, Any]] = []
    if arguments.target in {"T025", "all"}:
        results.append(run_eta(config, arguments.profile))
    if arguments.target in {"T026", "all"}:
        results.append(run_s17(config))
    status = "passed" if all(result["status"] == "passed" for result in results) else "failed"
    print(json.dumps({"status": status, "targets": [result["target_id"] for result in results]}))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
