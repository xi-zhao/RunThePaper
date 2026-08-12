#!/usr/bin/env python3
"""Validate, shard, and optionally start the independent paper-scale campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from ibdet_reproduction.campaign import (  # noqa: E402
    build_plan,
    select_shard,
    sha256,
    write_json_atomic,
)
from ibdet_reproduction.pyscf_backend import (  # noqa: E402
    BackendUnavailable,
    correlated_solver_boundary,
    run_mean_field,
)


def implementation_digest() -> str:
    digest = hashlib.sha256()
    files = [
        WORKSPACE / "src" / "ibdet_reproduction" / name
        for name in (
            "baths.py",
            "embedding.py",
            "spectra.py",
            "ed.py",
            "campaign.py",
            "pyscf_backend.py",
        )
    ]
    files.append(Path(__file__).resolve())
    for path in sorted(files):
        digest.update(path.relative_to(WORKSPACE).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def input_inventory(config_path: Path, config: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "paper_id": "2406.07531",
        "config": {
            "path": config_path.relative_to(WORKSPACE).as_posix(),
            "sha256": sha256(config_path),
        },
        "implementation_sha256": implementation_digest(),
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "missing_inputs": config["missing_inputs"],
    }


def execute_mean_field_units(
    config: dict[str, object],
    units: list[dict[str, object]],
    config_hash: str,
    implementation_hash: str,
) -> list[dict[str, object]]:
    records = []
    for unit in units:
        material_name = str(unit["material"])
        reference = str(unit["reference"])
        unit_id = str(unit["unit_id"])
        root = WORKSPACE / "outputs" / "paper_scale" / unit_id
        marker = root / "mean_field.json"
        if marker.exists():
            existing = json.loads(marker.read_text(encoding="utf-8"))
            if (
                existing.get("config_sha256") == config_hash
                and existing.get("implementation_sha256") == implementation_hash
            ):
                records.append(existing)
                continue
        result = run_mean_field(
            config["materials"][material_name],
            reference,
            root / "mean_field.npz",
        )
        record = {
            "schema_version": 1,
            "unit_id": unit_id,
            "stage": "mean_field",
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "result": result,
            "status": "completed",
        }
        write_json_atomic(marker, record)
        records.append(record)
        correlated_solver_boundary(int(unit["embedding_orbitals"]))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--execute-mean-field", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    arguments = parser.parse_args()
    config_path = (WORKSPACE / arguments.config).resolve()
    config_path.relative_to(WORKSPACE)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = build_plan(config)
    units = select_shard(plan, arguments.shard_index, arguments.shard_count)
    plan["selected_shard"] = {
        "index": arguments.shard_index,
        "count": arguments.shard_count,
        "unit_ids": [unit["unit_id"] for unit in units],
    }
    plan_path = WORKSPACE / "outputs" / "checks" / "paper_scale" / "plan.json"
    inventory_path = (
        WORKSPACE / "outputs" / "checks" / "paper_scale" / "input_inventory.json"
    )
    inventory = input_inventory(config_path, config)
    write_json_atomic(plan_path, plan)
    write_json_atomic(inventory_path, inventory)
    if arguments.execute_mean_field:
        try:
            execute_mean_field_units(
                config,
                units,
                str(inventory["config"]["sha256"]),
                str(inventory["implementation_sha256"]),
            )
        except BackendUnavailable as exc:
            write_json_atomic(
                WORKSPACE
                / "outputs"
                / "checks"
                / "paper_scale"
                / "backend_boundary.json",
                {
                    "schema_version": 1,
                    "status": "compute_or_backend_deferred",
                    "reason": str(exc),
                    "paper_targets_completed": [],
                },
            )
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
