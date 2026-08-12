"""Authoritative paper-scale NiO DFT+DMFT campaign model."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cthyb import validate_solver_contract
from .qe import render_pw2wannier_input, render_pw_input, render_wannier_input
from .structure import build_rocksalt_slab

TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 19))
TARGET_MAP = {
    "slab-001-relaxed": tuple(f"T{index:03d}" for index in range(1, 6)),
    "slab-110-relaxed": tuple(f"T{index:03d}" for index in range(6, 12)),
    "slab-001-bulk-terminated": tuple(f"T{index:03d}" for index in range(12, 15)),
    "slab-110-bulk-terminated": tuple(f"T{index:03d}" for index in range(15, 19)),
}
STAGES = (
    "dft_scf",
    "wannier_projection",
    "multi_site_cthyb",
    "charge_feedback",
    "analytic_continuation",
    "observables",
)


class CampaignConfigError(ValueError):
    pass


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    orientation: str
    relaxed: bool
    targets: tuple[str, ...]
    stages: tuple[str, ...]
    layer_count: int
    resource_estimate: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "orientation": self.orientation,
            "relaxed": self.relaxed,
            "target_ids": list(self.targets),
            "stages": list(self.stages),
            "layer_count": self.layer_count,
            "resource_estimate": self.resource_estimate,
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def validate_config(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1 or payload.get("paper_id") != "2101.12558":
        raise CampaignConfigError("paper-scale schema or paper_id mismatch")
    if payload.get("boundaries") != {
        "source_pixels_used_by_numerics": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
    }:
        raise CampaignConfigError("scientific independence boundary is not fail-closed")
    if float(payload.get("temperature_k", 0.0)) != 390.0:
        raise CampaignConfigError("the printed temperature must be 390 K")
    if float(payload.get("beta_ev_inverse", 0.0)) != 30.0:
        raise CampaignConfigError("the printed beta must be 30 eV^-1")
    if (
        float(payload.get("u_ev", 0.0)) != 10.0
        or float(payload.get("j_ev", 0.0)) != 1.0
    ):
        raise CampaignConfigError("the printed U/J values must be preserved")
    if (
        "chemical_potential_ev" not in payload
        or float(payload.get("initial_d_occupancy", 0.0)) <= 0.0
    ):
        raise CampaignConfigError(
            "DMFT chemical potential and initial occupancy are required"
        )
    convergence = payload.get("dmft_convergence")
    if not isinstance(convergence, dict):
        raise CampaignConfigError("DMFT convergence controls are required")
    if (
        float(convergence.get("self_energy_max_tolerance_ev", 0.0)) <= 0.0
        or int(convergence.get("maximum_iterations", 0)) < 1
        or not 0.0 < float(convergence.get("mixing", 0.0)) <= 1.0
    ):
        raise CampaignConfigError("invalid DMFT fixed-point controls")
    slabs = payload.get("slabs")
    if not isinstance(slabs, dict) or set(slabs) != set(TARGET_MAP):
        raise CampaignConfigError("all four slab lanes are required")
    covered: set[str] = set()
    for unit_id, expected_targets in TARGET_MAP.items():
        slab = slabs[unit_id]
        if tuple(slab.get("target_ids", ())) != expected_targets:
            raise CampaignConfigError(f"target mapping mismatch for {unit_id}")
        covered.update(expected_targets)
        for key in (
            "orientation",
            "layers",
            "thickness_angstrom",
            "vacuum_angstrom",
            "cutoffs_ry",
            "kmesh",
        ):
            if key not in slab:
                raise CampaignConfigError(f"{unit_id} lacks {key}")
    if covered != set(TARGET_IDS):
        raise CampaignConfigError("target coverage is incomplete")
    validate_solver_contract(payload["cthyb"])
    missing = payload.get("missing_paper_inputs")
    if not isinstance(missing, list) or not missing:
        raise CampaignConfigError("missing production inputs must be explicit")


def resource_estimate(orientation: str, layer_count: int) -> dict[str, Any]:
    impurities = 3 if orientation == "001" else 4
    return {
        "layer_count": layer_count,
        "inequivalent_impurities": impurities,
        "recommended_cpu_cores": 256,
        "recommended_memory_gib": 512,
        "recommended_scratch_gib": 2000,
        "recommended_walltime_hours": 336,
        "recommended_mpi_ranks_per_impurity": 64,
        "a100_role": (
            "optional linear-algebra/continuation acceleration; CT-HYB sampling "
            "and QE MPI remain CPU-dominant"
        ),
    }


def reconstructed_correlated_groups(
    orientation: str,
    layer_count: int,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Map printed layer symmetries onto reconstructed Ni-d Wannier blocks.

    Each reconstructed layer contains five Ni-d followed by three O-p
    orbitals.  The paper explicitly uses three impurity sites for the 7-layer
    (001) slab and four for the 11-layer (110) slab.  Symmetry-related outer
    layers share an impurity; the central three/five layers share the printed
    quasi-bulk impurity.  Exact author projector indices remain unavailable,
    so this mapping is provenance-labelled rather than paper-exact.
    """

    if (orientation, layer_count) == ("001", 7):
        layer_groups = ((0, 6), (1, 5), (2, 3, 4))
    elif (orientation, layer_count) == ("110", 11):
        layer_groups = ((0, 10), (1, 9), (2, 8), (3, 4, 5, 6, 7))
    else:
        raise CampaignConfigError(
            f"unsupported printed slab symmetry: {orientation}/{layer_count}"
        )
    return tuple(
        tuple(tuple(range(8 * layer, 8 * layer + 5)) for layer in group)
        for group in layer_groups
    )


def build_plan(payload: dict[str, Any]) -> dict[str, Any]:
    validate_config(payload)
    units = []
    for unit_id, slab in payload["slabs"].items():
        units.append(
            WorkUnit(
                unit_id=unit_id,
                orientation=str(slab["orientation"]),
                relaxed=bool(slab["relaxed"]),
                targets=tuple(slab["target_ids"]),
                stages=STAGES,
                layer_count=int(slab["layers"]),
                resource_estimate=resource_estimate(
                    str(slab["orientation"]), int(slab["layers"])
                ),
            ).as_dict()
        )
    return {
        "schema_version": 1,
        "paper_id": "2101.12558",
        "execution_profile": "paper_scale_reconstructed_geometry",
        "paper_parameters_executed": False,
        "target_ids": list(TARGET_IDS),
        "work_units": units,
        "work_unit_count": len(units),
        "checkpoint_policy": {
            "unit_and_stage_atomicity": True,
            "resume": True,
            "config_hash_bound": True,
            "implementation_hash_bound": True,
            "output_hash_bound": True,
        },
        "boundary": {
            **payload["boundaries"],
            "promotion_allowed": False,
            "reason": (
                "full production run and indispensable unpublished inputs are absent"
            ),
            "missing_paper_inputs": payload["missing_paper_inputs"],
        },
    }


def select_shard(
    plan: dict[str, Any],
    shard_index: int,
    shard_count: int,
) -> list[dict[str, Any]]:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise CampaignConfigError("invalid shard")
    return [
        unit
        for index, unit in enumerate(plan["work_units"])
        if index % shard_count == shard_index
    ]


def prepare_decks(
    payload: dict[str, Any],
    output_root: Path,
) -> list[dict[str, Any]]:
    """Write deterministic public-backend decks without executing them."""

    validate_config(payload)
    records = []
    for unit_id, spec in payload["slabs"].items():
        layer_count = int(spec["layers"])
        orientation = str(spec["orientation"])
        expected_n_wann = 8 * layer_count
        if int(spec["wannier"]["n_wann"]) != expected_n_wann:
            raise CampaignConfigError(
                f"{unit_id} must use the reconstructed 5d+3p layer basis "
                f"({expected_n_wann} orbitals)"
            )
        correlated_groups = reconstructed_correlated_groups(
            orientation,
            layer_count,
        )
        structure = build_rocksalt_slab(
            orientation=orientation,
            lattice_angstrom=float(payload["lattice_angstrom"]),
            n_layers=layer_count,
            thickness_angstrom=float(spec["thickness_angstrom"]),
            vacuum_angstrom=float(spec["vacuum_angstrom"]),
            relaxed=bool(spec["relaxed"]),
            relaxation_percent=tuple(
                float(value) for value in spec["relaxation_percent"]
            ),
        )
        deck = output_root / unit_id
        deck.mkdir(parents=True, exist_ok=True)
        prefix = unit_id.replace("-", "_")
        pseudo_names = {
            species: str(
                payload["pseudopotentials"][species].get(
                    "filename", f"MISSING_{species}.UPF"
                )
            )
            for species in ("Ni", "O")
        }
        (deck / "pw.in").write_text(
            render_pw_input(
                structure,
                prefix=prefix,
                pseudo_names=pseudo_names,
                cutoffs_ry=tuple(float(value) for value in spec["cutoffs_ry"]),
                kmesh=tuple(int(value) for value in spec["kmesh"]),
                calculation="scf",
                convergence=payload["dft_convergence"],
            ),
            encoding="utf-8",
        )
        (deck / "pw2wannier90.in").write_text(
            render_pw2wannier_input(prefix), encoding="utf-8"
        )
        (deck / f"{prefix}.win").write_text(
            render_wannier_input(
                prefix=prefix,
                n_wann=int(spec["wannier"]["n_wann"]),
                n_bands=int(spec["wannier"]["n_bands"]),
                kmesh=tuple(int(value) for value in spec["kmesh"]),
                projection_lines=tuple(spec["wannier"]["projections"]),
                disentanglement_window_ev=tuple(
                    float(value)
                    for value in spec["wannier"]["disentanglement_window_ev"]
                ),
            ),
            encoding="utf-8",
        )
        dmft_contract = {
            "schema_version": 1,
            "unit_id": unit_id,
            "target_ids": spec["target_ids"],
            "cthyb": payload["cthyb"],
            "double_counting": payload["double_counting"],
            "chemical_potential_ev": payload["chemical_potential_ev"],
            "initial_d_occupancy": payload["initial_d_occupancy"],
            "dmft_convergence": payload["dmft_convergence"],
            "kmesh": spec["kmesh"],
            "wannier": spec["wannier"],
            "correlated_groups": [
                [list(block) for block in group] for group in correlated_groups
            ],
            "correlated_group_provenance": (
                "reconstructed_from_printed_layer_symmetry_and_5d_plus_3p_basis"
            ),
            "charge_feedback": payload["charge_feedback"],
            "continuation": payload["continuation"],
            "observables": spec["observables"],
            "geometry_provenance": structure.provenance,
        }
        write_json_atomic(deck / "dmft.json", dmft_contract)
        records.append(
            {
                "unit_id": unit_id,
                "target_ids": spec["target_ids"],
                "surface_area_angstrom2": structure.surface_area_angstrom2,
                "atom_count": len(structure.atoms),
                "deck_files": [
                    "pw.in",
                    "pw2wannier90.in",
                    f"{prefix}.win",
                    "dmft.json",
                ],
                "geometry_provenance": structure.provenance,
            }
        )
    return records
