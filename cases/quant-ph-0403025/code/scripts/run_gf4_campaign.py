#!/usr/bin/env python3
"""Validate or execute the code-ready GF(4) threshold campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from magic_distillation.gf4_codes import (  # noqa: E402
    StabilizerCode,
    evaluate_t_axis_code,
    interior_threshold,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    config_path = (WORKSPACE / args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    codes = parameters.get("codes")
    if not isinstance(codes, list):
        raise ValueError("config.codes must be an array")
    required_sizes = {int(value) for value in parameters["required_n_qubits"]}
    output_root = (WORKSPACE / args.output_root).resolve()
    checks = output_root / "checks"
    data = output_root / "data"
    checks.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)

    plan = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_id": config["target_id"],
        "config_sha256": sha256_file(config_path),
        "code_entries": len(codes),
        "input_status": config["input_status"],
        "required_code_schema": config["required_code_schema"],
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "source_pixels_used_as_numeric_input": False,
        "status": "ready" if codes else "blocked_missing_source_input",
    }
    plan_path = checks / "gf4_campaign_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if not codes:
        blocked_payload = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": config["target_id"],
            "status": "blocked_missing_source_input",
            "results": [],
            "required_n_qubits": sorted(required_sizes),
            "required_code_schema": config["required_code_schema"],
            "scientific_boundary": {
                "source_pixels_used": False,
                "author_code_used": False,
                "author_numeric_arrays_used": False,
                "code_generators_guessed": False,
            },
        }
        blocked_path = data / "gf4_threshold_campaign.json"
        blocked_path.write_text(
            json.dumps(blocked_payload, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(plan, indent=2))
        return 0
    if args.validate_only:
        print(json.dumps(plan, indent=2))
        return 0

    epsilon = np.linspace(
        float(parameters["epsilon_grid"]["minimum"]),
        float(parameters["epsilon_grid"]["maximum"]),
        int(parameters["epsilon_grid"]["points"]),
    )
    results = []
    for raw_code in codes:
        code = StabilizerCode.from_mapping(raw_code)
        if code.n_qubits not in required_sizes:
            raise ValueError(
                f"{code.name}: n_qubits={code.n_qubits} is outside "
                f"the declared campaign sizes {sorted(required_sizes)}"
            )
        success, output_error = evaluate_t_axis_code(code, epsilon)
        results.append(
            {
                "name": code.name,
                "n_qubits": code.n_qubits,
                "threshold_error": interior_threshold(code),
                "epsilon": epsilon.tolist(),
                "success": np.asarray(success).tolist(),
                "output_error": np.asarray(output_error).tolist(),
            }
        )
    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_id": config["target_id"],
        "results": results,
        "status": "generated",
    }
    output_path = data / "gf4_threshold_campaign.json"
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "generated", "output": str(output_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
