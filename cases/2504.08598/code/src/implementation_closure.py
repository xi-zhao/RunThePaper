"""Clean-room implementation closure for the EV20 Rydberg-qudit targets.

The runner exercises the independently derived Hamiltonian without opening the
paper dataset, original figures, author arrays, or legacy outputs. Successful
execution proves code readiness only; it never promotes scientific coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from src.rydberg_qudit import compile_paper_program, simulate_program


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"configuration must be a JSON object: {path}")
    return payload


def _formula_smoke(target_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    program = compile_paper_program(
        str(spec["graph_id"]), int(spec["rydberg_level_count"])
    )
    point_count = int(spec["time_points"])
    if point_count < 5:
        raise ValueError(f"{target_id}: time_points must be at least five")
    times = np.linspace(0.0, program.schedule.duration_us, point_count)
    result = simulate_program(program, times_us=times)
    probability_sum = float(result.final_probabilities.sum())
    checks = {
        "finite_probabilities": bool(np.isfinite(result.final_probabilities).all()),
        "normalization": bool(abs(probability_sum - 1.0) <= 1e-10),
        "target_indices_nonempty": bool(len(result.target_indices) > 0),
        "proper_coloring_indices_nonempty": bool(
            len(result.proper_coloring_indices) > 0
        ),
        "target_probability_bounded": bool(
            np.all(
                (result.target_probability >= -1e-12)
                & (result.target_probability <= 1.0 + 1e-12)
            )
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"{target_id}: clean-room invariant failed: {checks}")
    return {
        "target_id": target_id,
        "mode": "formula_smoke",
        "status": "code_attested_reduced_scale",
        "scientific_coverage_promoted": False,
        "graph_id": result.graph_id,
        "profile_id": result.profile_id,
        "basis_state_count": int(len(result.basis)),
        "time_point_count": point_count,
        "final_probability_sum": probability_sum,
        "final_target_probability": result.final_target_probability,
        "final_norm_error": result.final_norm_error,
        "checks": checks,
    }


def _input_boundary(target_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    required = spec.get("required_input_schema")
    supplied = spec.get("supplied_inputs")
    if not isinstance(required, dict) or not required:
        raise ValueError(f"{target_id}: required_input_schema must be non-empty")
    if not isinstance(supplied, list):
        raise TypeError(f"{target_id}: supplied_inputs must be a list")
    missing = sorted(set(required) - {str(value) for value in supplied})
    if not missing:
        raise RuntimeError(
            f"{target_id}: inputs were declared complete but no numerical protocol is configured"
        )
    return {
        "target_id": target_id,
        "mode": "input_boundary",
        "status": "blocked_missing_source_input",
        "scientific_coverage_promoted": False,
        "required_input_schema": required,
        "missing_inputs": missing,
        "acceptance_boundary": str(spec["acceptance_boundary"]),
    }


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _read_object(config_path)
    targets = config.get("targets")
    if not isinstance(targets, dict) or not targets:
        raise ValueError("targets must be a non-empty object")
    output_dir = output_root / "data" / "implementation_closure"
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for target_id, raw_spec in targets.items():
        if not isinstance(raw_spec, dict):
            raise TypeError(f"{target_id}: target specification must be an object")
        mode = raw_spec.get("mode")
        if mode == "formula_smoke":
            record = _formula_smoke(str(target_id), raw_spec)
        elif mode == "input_boundary":
            record = _input_boundary(str(target_id), raw_spec)
        else:
            raise ValueError(f"{target_id}: unsupported mode {mode!r}")
        (output_dir / f"{target_id}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        records.append(record)
    summary = {
        "schema_version": 1,
        "paper_id": config.get("paper_id"),
        "target_count": len(records),
        "code_attested_count": len(records),
        "input_blocked_count": sum(
            row["status"] == "blocked_missing_source_input" for row in records
        ),
        "scientific_coverage_promoted": False,
    }
    (output_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary
