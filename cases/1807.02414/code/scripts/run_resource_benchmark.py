#!/usr/bin/env python3
"""Measure the local host against the two immutable paper-scale contracts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]


def _workspace_path(value: str, *, allowed_roots: tuple[str, ...]) -> Path:
    relative = Path(value)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.parts[:1] not in {(root,) for root in allowed_roots}
    ):
        raise ValueError(f"path must be workspace-relative under {allowed_roots}")
    return WORKSPACE / relative


def _read_json(value: str, *, allowed_roots: tuple[str, ...]) -> dict[str, Any]:
    return json.loads(
        _workspace_path(value, allowed_roots=allowed_roots).read_text(encoding="utf-8")
    )


def _physical_memory_bytes() -> int | None:
    try:
        return int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
    except (ValueError, OSError, AttributeError):
        return None


def _mps_tensor_lower_bound_gib(config: dict[str, Any]) -> float:
    variants = config["profiles"]["final"]["variants"]
    return max(
        int(variant["chain_length"])
        * 4
        * int(variant["max_bond"]) ** 2
        * 16
        / 1024**3
        for variant in variants
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = _read_json(args.config, allowed_roots=("config",))
    boundary = config["scientific_boundary"]
    if any(boundary.values()):
        raise RuntimeError("resource benchmark must not consume source/review inputs")
    parameters = config["parameters"]
    full_config = _read_json(
        parameters["full_ghd_config"], allowed_roots=("config",)
    )
    tdmrg_config = _read_json(
        parameters["tdmrg_config"], allowed_roots=("config",)
    )
    full_contract = _read_json(
        parameters["full_ghd_contract"], allowed_roots=("run_contract_full_ghd.json",)
    )
    tdmrg_contract = _read_json(
        parameters["tdmrg_contract"], allowed_roots=("run_contract_tdmrg.json",)
    )
    full_variants = full_config["profiles"]["final"]["variants"]
    tdmrg_variants = tdmrg_config["profiles"]["final"]["variants"]
    physical_bytes = _physical_memory_bytes()
    local_memory_gib = physical_bytes / 1024**3 if physical_bytes else None
    cupy_available = importlib.util.find_spec("cupy") is not None
    nvidia_smi_available = shutil.which("nvidia-smi") is not None
    required_memory = float(parameters["required_accelerator_memory_gib"])
    checks = {
        "full_ghd_all_final_variants_require_cupy": all(
            variant["backend"] == "cupy" for variant in full_variants
        ),
        "tdmrg_all_final_variants_require_cupy": all(
            variant["backend"] == "cupy" for variant in tdmrg_variants
        ),
        "full_ghd_contract_requests_a100_80g": (
            full_contract["resource_request"]["accelerator"] == parameters["required_accelerator"]
            and float(full_contract["resource_request"]["gpu_memory_gb"]) == required_memory
        ),
        "tdmrg_contract_requests_a100_80g": (
            tdmrg_contract["resource_request"]["accelerator"] == parameters["required_accelerator"]
            and float(tdmrg_contract["resource_request"]["gpu_memory_gb"]) == required_memory
        ),
        "local_cupy_unavailable": not cupy_available,
        "local_nvidia_smi_unavailable": not nvidia_smi_available,
        "local_memory_below_declared_accelerator_memory": (
            local_memory_gib is not None and local_memory_gib < required_memory
        ),
    }
    maximum_time = max(float(value) for value in tdmrg_config["paper_parameters"]["times"])
    payload = {
        "schema_version": 1,
        "status": "passed" if all(checks.values()) else "failed",
        "paper_id": "1807.02414",
        "target_ids": ["T001-DIFFUSIVE", "T003"],
        "host": {
            "operating_system": sys.platform,
            "release": platform.release(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "physical_memory_bytes": physical_bytes,
            "physical_memory_gib": local_memory_gib,
            "cupy_available": cupy_available,
            "nvidia_smi_available": nvidia_smi_available,
        },
        "declared_resource": {
            "accelerator": parameters["required_accelerator"],
            "accelerator_memory_gib": required_memory,
            "full_ghd_cpu_cores": full_contract["resource_request"]["cpu_cores"],
            "tdmrg_cpu_cores": tdmrg_contract["resource_request"]["cpu_cores"],
            "tdmrg_checkpoint_storage_gib": tdmrg_contract["resource_request"]["checkpoint_storage_gb"],
        },
        "workload_projection": {
            "full_ghd_variants": len(full_variants),
            "full_ghd_max_rapidity_points": max(int(v["rapidity_points"]) for v in full_variants),
            "full_ghd_max_spatial_points": max(int(v["x_points"]) for v in full_variants),
            "full_ghd_max_time_steps": max(
                int(round(max(full_config["paper_parameters"]["times"]) / float(v["time_step"])))
                for v in full_variants
            ),
            "tdmrg_variants": len(tdmrg_variants),
            "tdmrg_total_time_steps": sum(
                int(round(maximum_time / float(v["time_step"]))) for v in tdmrg_variants
            ),
            "tdmrg_max_bond": max(int(v["max_bond"]) for v in tdmrg_variants),
            "tdmrg_max_chain_length": max(int(v["chain_length"]) for v in tdmrg_variants),
            "tdmrg_mps_tensor_storage_lower_bound_gib": _mps_tensor_lower_bound_gib(tdmrg_config),
        },
        "checks": checks,
        "conclusion": (
            "Both immutable final campaigns select CuPy and request an A100 80 GB lane; "
            "the measured local host has neither CuPy nor an NVIDIA device."
        ),
        "scientific_boundary": boundary,
    }
    output = _workspace_path(args.output, allowed_roots=("outputs",))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
