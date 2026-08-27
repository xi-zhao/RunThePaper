#!/usr/bin/env python3
"""Run author-side falsification and local-resource checks without paper inputs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from kicked_ising.iid_universality import iid_transfer_spectrum  # noqa: E402
from kicked_ising.paper_scale import paper_scale_preflight  # noqa: E402


def _safe_path(value: str, *, root: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != (root,):
        raise ValueError(f"path must be workspace-relative under {root}/")
    return WORKSPACE / relative


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _physical_memory_bytes() -> int | None:
    try:
        return int(os.sysconf("SC_PAGE_SIZE")) * int(os.sysconf("SC_PHYS_PAGES"))
    except (ValueError, OSError, AttributeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    config = json.loads(_safe_path(args.config, root="config").read_text(encoding="utf-8"))
    parameters = config["parameters"]
    boundary = config["scientific_boundary"]
    if any(
        boundary[key]
        for key in (
            "paper_or_source_read_by_numeric_runner",
            "author_code_used",
            "author_numeric_arrays_used",
            "source_pixels_used_as_numerical_inputs",
            "fresh_review_claimed",
        )
    ):
        raise RuntimeError("forbidden source or review input declared")

    rows = []
    for label, standard_deviation in (
        ("generic", float(parameters["generic_standard_deviation"])),
        ("resonant", float(parameters["resonant_standard_deviation"])),
    ):
        for time_value in parameters["times"]:
            rows.append(
                {
                    "regime": label,
                    "standard_deviation": standard_deviation,
                    **iid_transfer_spectrum(
                        int(time_value),
                        h_mean=float(parameters["h_mean"]),
                        standard_deviation=standard_deviation,
                        distribution=str(parameters["distribution"]),
                    ),
                }
            )
    generic_rows = [row for row in rows if row["regime"] == "generic"]
    resonant_rows = [row for row in rows if row["regime"] == "resonant"]
    iid_checks = {
        "generic_unit_multiplicities_match": all(
            row["unit_modulus_count"] == row["expected_unit_modulus_count"]
            for row in generic_rows
        ),
        "resonant_unit_multiplicities_exceed_protected_counts": all(
            row["unit_modulus_count"] > row["expected_unit_modulus_count"]
            for row in resonant_rows
        ),
        "resonant_full_transfer_spectrum_is_unit_modulus": all(
            row["unit_modulus_count"] == 4 ** int(row["time"])
            for row in resonant_rows
        ),
    }
    iid_payload = {
        "schema_version": 1,
        "status": "passed" if all(iid_checks.values()) else "failed",
        "paper_id": "1805.00931",
        "target_id": "T006",
        "checks": iid_checks,
        "rows": rows,
        "interpretation": (
            "For an IID symmetric-binary field with nonzero width pi/2, all allowed "
            "magnetization differences have unit-modulus characteristic function. "
            "The unrestricted IID statement therefore needs an explicit non-resonance condition."
        ),
        "scientific_boundary": boundary,
    }

    paper_scale_path = _safe_path(str(parameters["paper_scale_config"]), root="config")
    paper_scale = json.loads(paper_scale_path.read_text(encoding="utf-8"))
    preflight = paper_scale_preflight(paper_scale)
    physical_bytes = _physical_memory_bytes()
    cupy_available = importlib.util.find_spec("cupy") is not None
    cuda_tool_available = shutil.which("nvidia-smi") is not None
    required_memory = float(parameters["required_accelerator_memory_gib"])
    local_memory_gib = physical_bytes / 1024**3 if physical_bytes else None
    resource_checks = {
        "paper_scale_preflight_passed": preflight["status"] == "passed",
        "paper_scale_requires_cupy_for_sff": paper_scale["parameters"]["fig2"]["trace_estimator"]["backend"] == "cupy",
        "paper_scale_requires_cupy_for_gap": paper_scale["parameters"]["solver"]["backend"] == "cupy",
        "local_cupy_unavailable": not cupy_available,
        "local_cuda_tool_unavailable": not cuda_tool_available,
        "local_memory_below_declared_accelerator_memory": (
            local_memory_gib is not None and local_memory_gib < required_memory
        ),
        "largest_gap_projection_exceeds_local_memory": (
            local_memory_gib is not None
            and max(float(row["estimated_peak_gib"]) for row in preflight["memory"])
            > local_memory_gib
        ),
    }
    resource_payload = {
        "schema_version": 1,
        "status": "passed" if all(resource_checks.values()) else "failed",
        "paper_id": "1805.00931",
        "target_ids": [f"T003-T{time_value}" for time_value in range(10, 16)],
        "host": {
            "operating_system": sys.platform,
            "release": platform.release(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "physical_memory_bytes": physical_bytes,
            "physical_memory_gib": local_memory_gib,
            "cupy_available": cupy_available,
            "nvidia_smi_available": cuda_tool_available,
        },
        "declared_paper_scale_requirement": {
            "accelerator": parameters["required_accelerator"],
            "accelerator_memory_gib": required_memory,
            "gap_vector_scaling": "4^t",
            "two_seed_acceptance": True,
            "nine_sigma_points_per_time": True,
        },
        "paper_scale_preflight": preflight,
        "checks": resource_checks,
        "conclusion": (
            "The exact campaign is runnable only on the declared external CUDA lane: "
            "the local host has neither CuPy/CUDA nor enough RAM for the t=15 projected peak."
        ),
    }

    output_root = _safe_path(args.output_root, root="outputs")
    _write_json(output_root / "iid_resonant_counterexample.json", iid_payload)
    _write_json(output_root / "resource_benchmark.json", resource_payload)
    return 0 if iid_payload["status"] == resource_payload["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
