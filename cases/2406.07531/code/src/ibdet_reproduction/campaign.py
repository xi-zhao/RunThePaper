"""Paper-scale campaign planning with fail-closed resource and input gates."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 10))
MATERIAL_TARGETS = {
    "Si": ("T001", "T002"),
    "BN": ("T003",),
    "MgO": ("T004",),
    "SrTiO3": ("T005",),
    "Na": ("T006", "T007", "T008", "T009"),
}


class CampaignConfigError(ValueError):
    """The paper-scale configuration is incomplete or inconsistent."""


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    material: str
    reference: str
    embedding_orbitals: int
    target_ids: tuple[str, ...]
    stages: tuple[str, ...]
    resource_estimate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "material": self.material,
            "reference": self.reference,
            "embedding_orbitals": self.embedding_orbitals,
            "target_ids": list(self.target_ids),
            "stages": list(self.stages),
            "resource_estimate": self.resource_estimate,
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_fci_log10_dimension(n_spatial_orbitals: int, filling: float = 1.0) -> float:
    """Estimate the central spin-orbital determinant dimension in log10."""

    n_spin = 2 * int(n_spatial_orbitals)
    n_electrons = min(max(int(round(filling * n_spatial_orbitals)), 1), n_spin - 1)
    log_dimension = (
        math.lgamma(n_spin + 1)
        - math.lgamma(n_electrons + 1)
        - math.lgamma(n_spin - n_electrons + 1)
    )
    return float(log_dimension / math.log(10.0))


def validate_config(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise CampaignConfigError("schema_version must be 1")
    if payload.get("paper_id") != "2406.07531":
        raise CampaignConfigError("paper_id mismatch")
    materials = payload.get("materials")
    if not isinstance(materials, dict) or set(materials) != set(MATERIAL_TARGETS):
        raise CampaignConfigError("materials must contain Si, BN, MgO, SrTiO3, and Na")
    covered: set[str] = set()
    for name, expected_targets in MATERIAL_TARGETS.items():
        material = materials[name]
        if tuple(material.get("target_ids", ())) != expected_targets:
            raise CampaignConfigError(f"{name} target mapping mismatch")
        covered.update(expected_targets)
        if not material.get("structure", {}).get("lattice_angstrom"):
            raise CampaignConfigError(f"{name} lattice is missing")
        if not material.get("structure", {}).get("atoms"):
            raise CampaignConfigError(f"{name} atoms are missing")
        kmesh = material.get("kmesh")
        if (
            not isinstance(kmesh, list)
            or len(kmesh) != 3
            or any(int(v) <= 0 for v in kmesh)
        ):
            raise CampaignConfigError(f"{name} kmesh is invalid")
        sizes = material.get("embedding_orbitals")
        if not isinstance(sizes, list) or not sizes or any(int(v) <= 0 for v in sizes):
            raise CampaignConfigError(f"{name} embedding sizes are invalid")
        if not material.get("references"):
            raise CampaignConfigError(f"{name} mean-field references are missing")
    if covered != set(TARGET_IDS):
        raise CampaignConfigError("paper-scale target coverage is incomplete")
    solver = payload.get("solver_contract", {})
    if solver.get("many_body_method") != "EOM-CCSD real-axis Green function":
        raise CampaignConfigError("solver contract must name the paper method")
    if solver.get("author_code_allowed") is not False:
        raise CampaignConfigError("author code boundary must fail closed")
    if solver.get("source_pixels_allowed") is not False:
        raise CampaignConfigError("source pixel boundary must fail closed")


def resource_estimate(embedding_orbitals: int) -> dict[str, Any]:
    """Return an auditable order-of-growth estimate, not a runtime promise."""

    n = int(embedding_orbitals)
    return {
        "embedding_spatial_orbitals": n,
        "ccsd_amplitude_elements_order": n**4,
        "ccgf_linear_system_order": n**6,
        "exact_crosscheck_log10_determinants": exact_fci_log10_dimension(n),
        "recommended_cpu_cores": 64 if n >= 200 else 32,
        "recommended_memory_gib": 512 if n >= 200 else 256,
        "recommended_scratch_gib": 2000,
        "recommended_walltime_hours": 168,
        "gpu_role": "optional tensor acceleration; A100 does not remove the CPU-memory and scaling bottleneck",
    }


def build_plan(payload: dict[str, Any]) -> dict[str, Any]:
    validate_config(payload)
    stages = tuple(payload["solver_contract"]["stages"])
    units: list[WorkUnit] = []
    for material_name, material in payload["materials"].items():
        for reference in material["references"]:
            for size in material["embedding_orbitals"]:
                unit_id = f"{material_name.lower()}-{reference.lower()}-nemb{int(size)}"
                units.append(
                    WorkUnit(
                        unit_id=unit_id,
                        material=material_name,
                        reference=reference,
                        embedding_orbitals=int(size),
                        target_ids=MATERIAL_TARGETS[material_name],
                        stages=stages,
                        resource_estimate=resource_estimate(int(size)),
                    )
                )
    return {
        "schema_version": 1,
        "paper_id": "2406.07531",
        "execution_profile": "paper_scale_reconstructed_inputs",
        "paper_parameters_executed": False,
        "target_ids": list(TARGET_IDS),
        "work_units": [unit.to_dict() for unit in units],
        "work_unit_count": len(units),
        "stage_count": len(stages),
        "checkpoint_policy": {
            "unit_atomicity": "one material/reference/embedding-size unit",
            "stage_markers": True,
            "resume": True,
            "config_hash_bound": True,
            "implementation_hash_bound": True,
            "result_hash_bound": True,
        },
        "boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "supplement_available": False,
            "missing_inputs": payload["missing_inputs"],
            "promotion_allowed": False,
        },
    }


def select_shard(
    plan: dict[str, Any], shard_index: int, shard_count: int
) -> list[dict[str, Any]]:
    if shard_count <= 0 or not 0 <= shard_index < shard_count:
        raise CampaignConfigError("invalid shard index/count")
    return [
        unit
        for index, unit in enumerate(plan["work_units"])
        if index % shard_count == shard_index
    ]


def write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
