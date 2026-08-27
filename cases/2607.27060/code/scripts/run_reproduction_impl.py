#!/usr/bin/env python3
"""Guard-aware, one-target final numerical runner for Figures 2 and 3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.trotter_bounds import TARGET_SPECS, compute_rows, target_slug  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest_target(target_id: str) -> dict[str, Any]:
    manifest_path = WORKSPACE / "physics_reproduction_project.json"
    project = json.loads(manifest_path.read_text(encoding="utf-8"))
    matches = [item for item in project["figure_targets"] if item.get("target_id") == target_id]
    if len(matches) != 1:
        raise RuntimeError(f"manifest must declare exactly one {target_id} target")
    return matches[0]


def _load_config(path: Path, target_id: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("paper_id") != "2607.27060":
        raise RuntimeError("config paper_id does not match this case")
    targets = payload.get("targets")
    if not isinstance(targets, dict) or not isinstance(targets.get(target_id), dict):
        raise RuntimeError(f"config does not declare {target_id}")
    boundary = payload.get("source_boundary") or {}
    if any(boundary.get(key) is not False for key in (
        "source_pixels_used_as_scientific_input",
        "author_code_used",
        "author_numeric_arrays_used",
    )):
        raise RuntimeError("config violates the independent-numerics source boundary")
    return targets[target_id]


def _validate_guard(target_id: str, attested_stage: str | None = None) -> str:
    if attested_stage is not None:
        if attested_stage != "final_reproduction":
            raise RuntimeError("attested stage must be final_reproduction")
        return attested_stage
    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE")
    if guarded_target != target_id:
        raise RuntimeError(
            f"guard mismatch: requested {target_id}, PRAGENT_GUARDED_TARGET_ID={guarded_target!r}"
        )
    if guarded_stage != "final_reproduction":
        raise RuntimeError(
            "this reader-facing runner requires PRAGENT_GUARDED_STAGE=final_reproduction"
        )
    return guarded_stage


def _validate_parameter_contract(
    target: dict[str, Any], target_id: str, config: dict[str, Any]
) -> dict[str, Any]:
    spec = TARGET_SPECS[target_id]
    parameter_set = target.get("parameter_set") or {}
    paper = parameter_set.get("paper") or {}
    generated = parameter_set.get("generated") or {}
    if parameter_set.get("parameter_match") != "paper_exact" or paper != generated:
        raise RuntimeError("final target parameters are not an exact paper/generated match")
    expected = {
        "model": spec.model,
        "method": spec.method,
        "M_values": list(spec.m_values),
        "t": spec.t,
        "lambda": spec.lam,
        "epsilon": spec.epsilon,
    }
    mismatches = {
        key: {"expected": value, "manifest": generated.get(key)}
        for key, value in expected.items()
        if generated.get(key) != value
    }
    if mismatches:
        raise RuntimeError(f"target spec differs from frozen paper parameters: {mismatches}")
    if config != expected:
        raise RuntimeError(
            f"config differs from frozen target parameters: expected={expected}, config={config}"
        )
    return generated


def _evaluate_checks(rows: list[dict[str, Any]], target_id: str) -> list[dict[str, Any]]:
    spec = TARGET_SPECS[target_id]
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, evidence: Any) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "passed" if passed else "failed",
                "evidence": evidence,
            }
        )

    add("complete_M_grid", [row["M"] for row in rows] == list(spec.m_values), [row["M"] for row in rows])
    add("all_four_visible_series", all(all(key in row for key in ("N_analytic", "N_min", "g_analytic", "g_min")) for row in rows), {"series": 4, "rows": len(rows)})
    add("analytic_bound_sufficient", all(row["epsilon_at_N_analytic"] <= spec.epsilon for row in rows), {"max_error": max(row["epsilon_at_N_analytic"] for row in rows), "epsilon": spec.epsilon})
    add("minimum_current_passes", all(row["epsilon_at_N_min"] <= spec.epsilon for row in rows), {"max_error": max(row["epsilon_at_N_min"] for row in rows), "epsilon": spec.epsilon})
    add("minimum_predecessor_fails", all(row["N_min"] == 1 or row["epsilon_at_predecessor"] > spec.epsilon for row in rows), {"min_predecessor_error": min(row["epsilon_at_predecessor"] for row in rows if row["epsilon_at_predecessor"] is not None), "epsilon": spec.epsilon})
    gate_factor = 2 if spec.second_order else 1
    add("gate_count_identity", all(row["g_analytic"] == gate_factor * row["M"] * row["N_analytic"] and row["g_min"] == gate_factor * row["M"] * row["N_min"] for row in rows), {"gate_factor": gate_factor})
    add("analytic_not_below_minimum", all(row["N_analytic"] >= row["N_min"] for row in rows), {"minimum_ratio": min(row["N_analytic"] / row["N_min"] for row in rows)})
    add("positive_monotone_series", all(all(rows[index][key] < rows[index + 1][key] for index in range(len(rows) - 1)) for key in ("N_analytic", "N_min", "g_analytic", "g_min")), {"sort_key": "M"})
    return checks


def _write_outputs(
    target_id: str, stage: str, config_path: Path
) -> tuple[Path, Path, Path]:
    spec = TARGET_SPECS[target_id]
    target = _load_manifest_target(target_id)
    config = _load_config(config_path, target_id)
    parameters = _validate_parameter_contract(target, target_id, config)
    rows = compute_rows(spec)
    checks = _evaluate_checks(rows, target_id)
    if any(item["status"] != "passed" for item in checks):
        failed = [item["check_id"] for item in checks if item["status"] != "passed"]
        raise RuntimeError(f"scientific checks failed: {failed}")

    slug = target_slug(target_id)
    data_dir = WORKSPACE / "outputs" / "data"
    check_dir = WORKSPACE / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / f"{slug}.json"
    csv_path = data_dir / f"{slug}.csv"
    check_path = check_dir / f"{slug}_scientific.json"
    run_id = f"RUN-{target_id}-FINAL"

    data_payload = {
        "schema_version": 1,
        "target_id": target_id,
        "figure_id": spec.figure_id,
        "scientific_role": "theory_numerical",
        "generated_data_provenance": "independent_numerics",
        "created_by_run": run_id,
        "method": spec.method,
        "model": spec.model,
        "parameters": parameters,
        "series": ["N_analytic", "N_min", "g_analytic", "g_min"],
        "rows": rows,
    }
    json_path.write_text(json.dumps(data_payload, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "M",
            "N_analytic",
            "N_min",
            "g_analytic",
            "g_min",
            "epsilon_at_N_analytic",
            "epsilon_at_N_min",
            "epsilon_at_predecessor",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    check_payload = {
        "schema_version": 1,
        "status": "passed",
        "target_id": target_id,
        "figure_id": spec.figure_id,
        "run_id": run_id,
        "requested_stage": stage,
        "artifact_stage": "final_reproduction",
        "parameter_match": "paper_exact",
        "scientific_role": "theory_numerical",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used_for_generated_data": False,
        "author_modules_imported": False,
        "formula_dependencies": target["formula_refs"],
        "method_dependencies": target["method_refs"],
        "formula_gate": "verified",
        "checks": checks,
        "summary": {
            "visible_series_total": 4,
            "points_per_series": len(rows),
            "checks_passed": len(checks),
            "checks_failed": 0,
        },
        "artifacts": {
            "json_data": str(json_path.relative_to(WORKSPACE)),
            "csv_data": str(csv_path.relative_to(WORKSPACE)),
        },
        "input_fingerprints": {
            str(config_path.relative_to(WORKSPACE)): _sha256(config_path),
            "physics_reproduction_project.json": _sha256(WORKSPACE / "physics_reproduction_project.json"),
            "src/trotter_bounds.py": _sha256(WORKSPACE / "src" / "trotter_bounds.py"),
            "scripts/run_target.py": _sha256(Path(__file__)),
        },
    }
    check_path.write_text(json.dumps(check_payload, indent=2) + "\n", encoding="utf-8")
    return json_path, csv_path, check_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=sorted(TARGET_SPECS))
    parser.add_argument(
        "--attested-stage",
        choices=("final_reproduction",),
        help="Explicit stage used only by an isolated run contract.",
    )
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    stage = _validate_guard(args.target, args.attested_stage)
    json_path, csv_path, check_path = _write_outputs(
        args.target, stage, config_path.resolve()
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "target_id": args.target,
                "data": str(json_path.relative_to(WORKSPACE)),
                "csv": str(csv_path.relative_to(WORKSPACE)),
                "check": str(check_path.relative_to(WORKSPACE)),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
