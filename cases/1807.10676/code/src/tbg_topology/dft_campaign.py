"""Code-ready paper-scale DFT campaign for arXiv:1807.10676.

The module has no access to ``raw/``, reference figures, or author numerical
arrays.  It turns the method printed in the paper into four explicit stages:

``config -> commensurate structures -> VASP decks -> structured acceptance``.

VASP and PAW data are licensed external assets.  They are deliberately not
bundled here: the runner validates and hashes them at the execution boundary.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
OUTCAR_COMPLETION_MARKER = "General timing and accounting informations for this job"


class CampaignError(RuntimeError):
    """Base error for an invalid or incomplete campaign."""


class ExternalAssetError(CampaignError):
    """Raised when a licensed executable, PAW asset, or machine is unavailable."""


class IncompleteResultError(CampaignError):
    """Raised when external VASP outputs are incomplete."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_config(payload)
    return payload


def _require_keys(mapping: dict[str, Any], keys: Iterable[str], context: str) -> None:
    missing = sorted(set(keys) - set(mapping))
    if missing:
        raise CampaignError(f"{context} is missing required keys: {', '.join(missing)}")


def validate_config(config: dict[str, Any]) -> None:
    _require_keys(
        config,
        [
            "paper_id",
            "implementation_id",
            "geometry",
            "vasp",
            "angle_jobs",
            "distance_jobs",
            "targets",
            "external_assets",
            "machine",
            "acceptance",
        ],
        "DFT config",
    )
    if config["paper_id"] != "1807.10676":
        raise CampaignError("DFT config paper_id must be 1807.10676")
    if config["implementation_id"] != "paper_scale_dft":
        raise CampaignError("implementation_id must be paper_scale_dft")

    geometry = config["geometry"]
    common_incar = config["vasp"]["incar_common"]
    method_checks = {
        "lattice constant": math.isclose(
            float(geometry["lattice_constant_angstrom"]), 2.456, abs_tol=1.0e-12
        ),
        "base interlayer distance": math.isclose(
            float(geometry["base_interlayer_distance_angstrom"]),
            3.35,
            abs_tol=1.0e-12,
        ),
        "unrelaxed geometry": geometry.get("relaxation") is False,
        "LDA": common_incar.get("GGA") == "CA",
        "300 eV cutoff": math.isclose(
            float(common_incar.get("ENCUT", 0.0)), 300.0, abs_tol=1.0e-12
        ),
        "no spin-orbit coupling": common_incar.get("LSORBIT") is False,
        "no ionic relaxation": int(common_incar.get("NSW", -1)) == 0
        and int(common_incar.get("IBRION", 0)) == -1,
    }
    failed_method = [name for name, passed in method_checks.items() if not passed]
    if failed_method:
        raise CampaignError(
            "config violates the paper DFT method: " + ", ".join(failed_method)
        )

    target_ids = set(config["targets"])
    expected_targets = {f"D{index:03d}" for index in range(1, 13)}
    if target_ids != expected_targets:
        raise CampaignError(
            "targets must be exactly D001-D012; got " + ", ".join(sorted(target_ids))
        )

    jobs = [*config["angle_jobs"], *config["distance_jobs"]]
    job_ids = [job["job_id"] for job in jobs]
    if len(job_ids) != len(set(job_ids)):
        raise CampaignError("job_id values must be unique")
    covered: set[str] = set()
    for job in jobs:
        _require_keys(
            job,
            ["job_id", "commensurate_index", "scf_mesh", "target_ids"],
            f"job {job.get('job_id', '<unknown>')}",
        )
        if int(job["commensurate_index"]) < 1:
            raise CampaignError(f"{job['job_id']}: commensurate_index must be positive")
        mesh = job["scf_mesh"]
        if len(mesh) != 3 or any(int(value) < 1 for value in mesh):
            raise CampaignError(
                f"{job['job_id']}: scf_mesh must contain 3 positive integers"
            )
        unknown = set(job["target_ids"]) - target_ids
        if unknown:
            raise CampaignError(f"{job['job_id']}: unknown targets {sorted(unknown)}")
        covered.update(job["target_ids"])
    if covered != expected_targets:
        raise CampaignError(
            f"jobs do not cover targets: {sorted(expected_targets - covered)}"
        )

    expected_angle_jobs = [
        ("angle_i06", 6, 10, ["D001", "D002", "D003"]),
        ("angle_i10", 10, 6, ["D001", "D002", "D004"]),
        ("angle_i16", 16, 4, ["D001", "D002", "D005"]),
        ("angle_i23", 23, 2, ["D001", "D002", "D006"]),
        ("angle_i27", 27, None, ["D001"]),
        ("angle_i30", 30, None, ["D001"]),
    ]
    actual_angle_jobs = [
        (
            str(job["job_id"]),
            int(job["commensurate_index"]),
            job.get("path_points_per_segment"),
            list(job["target_ids"]),
        )
        for job in config["angle_jobs"]
    ]
    if actual_angle_jobs != expected_angle_jobs:
        raise CampaignError(
            "angle jobs must encode the frozen D001-D006 paper campaign"
        )

    actual_z = [float(job["z_over_d0"]) for job in config["distance_jobs"]]
    expected_z = [1.0, 0.9, 0.86, 0.83, 0.8]
    if actual_z != expected_z:
        raise CampaignError(
            "Supplement Figure 12 z/d0 list must be exactly "
            f"{expected_z}; got {actual_z}"
        )
    if any(int(job["commensurate_index"]) != 10 for job in config["distance_jobs"]):
        raise CampaignError("all distance jobs must use commensurate index i=10")
    expected_distance_targets = [
        ["D007", "D012"],
        ["D008", "D012"],
        ["D009", "D012"],
        ["D010", "D012"],
        ["D011", "D012"],
    ]
    if [
        list(job["target_ids"]) for job in config["distance_jobs"]
    ] != expected_distance_targets:
        raise CampaignError("distance jobs must encode the frozen D007-D012 mapping")

    outputs = [str(details["output"]) for details in config["targets"].values()]
    if len(outputs) != len(set(outputs)) or any(
        not output.startswith("outputs/data/dft_paper_scale/") for output in outputs
    ):
        raise CampaignError(
            "every DFT target must have one unique campaign data output"
        )

    machine = config["machine"]
    if (
        machine.get("scheduler") != "slurm"
        or int(machine.get("cpus_per_task", 0)) < 72
        or int(machine.get("memory_gib", 0)) < 2048
    ):
        raise CampaignError(
            "paper-scale machine must provide Slurm, 72 CPU, and 2048 GiB"
        )

    path = config["vasp"]["band_path"]
    labels = [point["label"] for point in path]
    required_labels = config["acceptance"]["science"]["supplement_band_required_labels"]
    if labels != required_labels or labels != ["M", "Gamma", "K", "M"]:
        raise CampaignError("band path must be M-Gamma-K-M")
    expected_vertices = [
        [0.5, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [2.0 / 3.0, 1.0 / 3.0, 0.0],
        [0.5, 0.0, 0.0],
    ]
    if not np.allclose(
        np.asarray([point["fractional"] for point in path], dtype=float),
        np.asarray(expected_vertices, dtype=float),
        atol=1.0e-14,
        rtol=0.0,
    ):
        raise CampaignError(
            "band path vertices must be the hexagonal M-Gamma-K-M points"
        )


def commensurate_twist_angle(index: int) -> float:
    """Return the paper's commensurate twist angle in radians."""

    index = int(index)
    if index < 1:
        raise ValueError("commensurate index must be positive")
    numerator = 3.0 * index**2 + 3.0 * index + 0.5
    denominator = 3.0 * index**2 + 3.0 * index + 1.0
    return math.acos(numerator / denominator)


def commensurate_cell_count(index: int) -> int:
    """Number of graphene primitive cells in one layer."""

    index = int(index)
    return 3 * index**2 + 3 * index + 1


def expected_atom_count(index: int) -> int:
    """Two carbon sites times two layers times the supercell area."""

    return 4 * commensurate_cell_count(index)


@dataclass(frozen=True)
class Structure:
    """Unrelaxed commensurate twisted-bilayer graphene structure."""

    commensurate_index: int
    twist_angle_rad: float
    z_over_d0: float
    interlayer_distance_angstrom: float
    cell: FloatArray
    cartesian_positions: FloatArray
    layer_index: NDArray[np.int64]

    @property
    def fractional_positions(self) -> FloatArray:
        fractional = np.linalg.solve(self.cell.T, self.cartesian_positions.T).T
        fractional[:, :2] %= 1.0
        return fractional

    @property
    def atom_count(self) -> int:
        return int(self.cartesian_positions.shape[0])


def _rotation(angle: float) -> FloatArray:
    return np.array(
        [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]],
        dtype=float,
    )


def _points_in_cell(
    a1: FloatArray,
    a2: FloatArray,
    cell_2d: FloatArray,
    index: int,
) -> FloatArray:
    """Enumerate the two-site graphene basis in a half-open supercell."""

    basis = [np.zeros(2, dtype=float), (a1 + a2) / 3.0]
    # With A at zero and B=(a1+a2)/3, 2(a1+a2)/3 is a carbon-hexagon centre.
    hexagon_center = 2.0 * (a1 + a2) / 3.0
    # A common-cell vertex reaches lattice coordinate ``m+2n=3*i+1``.
    # Add a small margin for the shifted two-site basis.
    extent = 3 * int(index) + 5
    points: list[FloatArray] = []
    tolerance = 2.0e-11
    for u in range(-extent, extent + 1):
        for v in range(-extent, extent + 1):
            lattice_point = u * a1 + v * a2
            for offset in basis:
                point = lattice_point + offset - hexagon_center
                fractional = np.linalg.solve(cell_2d.T, point)
                if np.all(fractional >= -tolerance) and np.all(
                    fractional < 1.0 - tolerance
                ):
                    points.append(point)
    result = np.asarray(points, dtype=float)
    expected = 2 * commensurate_cell_count(index)
    if result.shape != (expected, 2):
        raise CampaignError(
            f"geometry enumeration produced {len(result)} sites; expected {expected} "
            f"for i={index}"
        )
    return result


def build_commensurate_structure(
    index: int,
    *,
    lattice_constant_angstrom: float,
    base_interlayer_distance_angstrom: float,
    z_over_d0: float,
    vacuum_angstrom: float,
) -> Structure:
    """Build an AA-centred, unrelaxed commensurate TBG cell.

    For ``m=i+1`` and ``n=i``, the common bottom-layer cell is
    ``T1=m*a1+n*a2`` and ``T2=-n*a1+(m+n)*a2``.  The top preimage vectors
    ``n*a1+m*a2`` and ``-m*a1+(m+n)*a2`` map onto this common cell under a
    rotation by ``-theta_i``.  This construction yields exactly
    ``4*(3*i^2+3*i+1)`` atoms and 11164 atoms at ``i=30``.
    """

    index = int(index)
    if lattice_constant_angstrom <= 0 or base_interlayer_distance_angstrom <= 0:
        raise ValueError("lattice and interlayer distances must be positive")
    if z_over_d0 <= 0 or vacuum_angstrom <= 0:
        raise ValueError("z_over_d0 and vacuum must be positive")

    m = index + 1
    n = index
    a0 = float(lattice_constant_angstrom)
    a1 = np.array([a0, 0.0], dtype=float)
    a2 = np.array([0.5 * a0, math.sqrt(3.0) * 0.5 * a0], dtype=float)
    common = np.array([m * a1 + n * a2, -n * a1 + (m + n) * a2])
    top_preimage = np.array([n * a1 + m * a2, -m * a1 + (m + n) * a2])
    theta = commensurate_twist_angle(index)
    top_rotation = _rotation(-theta)

    bottom_xy = _points_in_cell(a1, a2, common, index)
    top_unrotated_xy = _points_in_cell(a1, a2, top_preimage, index)
    top_xy = (top_rotation @ top_unrotated_xy.T).T

    # Numerical wrapping makes boundary representatives deterministic.
    bottom_frac = np.linalg.solve(common.T, bottom_xy.T).T % 1.0
    top_frac = np.linalg.solve(common.T, top_xy.T).T % 1.0
    bottom_xy = bottom_frac @ common
    top_xy = top_frac @ common

    interlayer = float(base_interlayer_distance_angstrom) * float(z_over_d0)
    height = interlayer + float(vacuum_angstrom)
    bottom_z = 0.5 * (height - interlayer)
    top_z = bottom_z + interlayer
    bottom = np.column_stack([bottom_xy, np.full(len(bottom_xy), bottom_z)])
    top = np.column_stack([top_xy, np.full(len(top_xy), top_z)])
    cell = np.array(
        [
            [common[0, 0], common[0, 1], 0.0],
            [common[1, 0], common[1, 1], 0.0],
            [0.0, 0.0, height],
        ],
        dtype=float,
    )
    structure = Structure(
        commensurate_index=index,
        twist_angle_rad=theta,
        z_over_d0=float(z_over_d0),
        interlayer_distance_angstrom=interlayer,
        cell=cell,
        cartesian_positions=np.vstack([bottom, top]),
        layer_index=np.concatenate(
            [np.zeros(len(bottom), dtype=np.int64), np.ones(len(top), dtype=np.int64)]
        ),
    )
    validate_structure(structure)
    return structure


def validate_structure(structure: Structure) -> dict[str, Any]:
    expected = expected_atom_count(structure.commensurate_index)
    fractional = structure.fractional_positions
    if structure.atom_count != expected:
        raise CampaignError(
            f"i={structure.commensurate_index}: {structure.atom_count} atoms, expected {expected}"
        )
    if not np.isfinite(fractional).all():
        raise CampaignError("structure contains non-finite fractional coordinates")
    if np.min(fractional) < -1.0e-12 or np.max(fractional) >= 1.0 + 1.0e-12:
        raise CampaignError("structure coordinates are outside the periodic cell")

    for layer in (0, 1):
        xy = fractional[structure.layer_index == layer, :2]
        rounded = {tuple(row) for row in np.round(xy, decimals=11)}
        if len(rounded) != len(xy):
            raise CampaignError(f"layer {layer} contains duplicate in-plane sites")
    layer_z = [
        float(np.mean(structure.cartesian_positions[structure.layer_index == layer, 2]))
        for layer in (0, 1)
    ]
    measured_interlayer = layer_z[1] - layer_z[0]
    if abs(measured_interlayer - structure.interlayer_distance_angstrom) > 1.0e-9:
        raise CampaignError("interlayer distance does not match the requested z/d0")
    return {
        "status": "passed",
        "commensurate_index": structure.commensurate_index,
        "twist_angle_deg": math.degrees(structure.twist_angle_rad),
        "z_over_d0": structure.z_over_d0,
        "interlayer_distance_angstrom": measured_interlayer,
        "atom_count": structure.atom_count,
        "expected_atom_count": expected,
        "cell_area_angstrom2": float(abs(np.linalg.det(structure.cell[:2, :2]))),
        "cell_height_angstrom": float(structure.cell[2, 2]),
    }


@dataclass(frozen=True)
class CampaignJob:
    job_id: str
    commensurate_index: int
    z_over_d0: float
    scf_mesh: tuple[int, int, int]
    path_points_per_segment: int | None
    target_ids: tuple[str, ...]
    family: str

    @property
    def has_band_stage(self) -> bool:
        return self.path_points_per_segment is not None


def campaign_jobs(config: dict[str, Any]) -> list[CampaignJob]:
    jobs: list[CampaignJob] = []
    for family, entries in (
        ("angle", config["angle_jobs"]),
        ("distance", config["distance_jobs"]),
    ):
        for entry in entries:
            jobs.append(
                CampaignJob(
                    job_id=str(entry["job_id"]),
                    commensurate_index=int(entry["commensurate_index"]),
                    z_over_d0=float(entry.get("z_over_d0", 1.0)),
                    scf_mesh=tuple(int(value) for value in entry["scf_mesh"]),
                    path_points_per_segment=(
                        None
                        if entry.get("path_points_per_segment") is None
                        else int(entry["path_points_per_segment"])
                    ),
                    target_ids=tuple(str(value) for value in entry["target_ids"]),
                    family=family,
                )
            )
    return jobs


def _format_incar_value(value: Any) -> str:
    if isinstance(value, bool):
        return ".TRUE." if value else ".FALSE."
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def render_incar(config: dict[str, Any], job: CampaignJob, stage: str) -> str:
    if stage not in {"scf", "bands"}:
        raise ValueError(f"unsupported VASP stage: {stage}")
    values = dict(config["vasp"]["incar_common"])
    values.update(config["vasp"][stage])
    values["SYSTEM"] = f"1807.10676 {job.job_id} {stage}"
    values["NCORE"] = 6
    # Standard carbon contributes four valence electrons.  Keep six occupied
    # and six empty states around neutrality available for the Gamma analysis.
    values["NBANDS"] = 2 * expected_atom_count(job.commensurate_index) + 12
    ordered = ["SYSTEM", *sorted(key for key in values if key != "SYSTEM")]
    return (
        "\n".join(f"{key} = {_format_incar_value(values[key])}" for key in ordered)
        + "\n"
    )


def render_poscar(structure: Structure, job_id: str) -> str:
    lines = [
        f"arXiv 1807.10676 {job_id}; independent commensurate TBG structure",
        "1.0",
    ]
    lines.extend(
        "  " + "  ".join(f"{value:.16f}" for value in vector)
        for vector in structure.cell
    )
    lines.extend(["C", str(structure.atom_count), "Direct"])
    lines.extend(
        "  " + "  ".join(f"{value:.16f}" for value in position)
        for position in structure.fractional_positions
    )
    return "\n".join(lines) + "\n"


def render_scf_kpoints(mesh: Sequence[int]) -> str:
    return (
        "Gamma-centered SCF mesh\n"
        "0\n"
        "Gamma\n"
        f"{int(mesh[0])} {int(mesh[1])} {int(mesh[2])}\n"
        "0 0 0\n"
    )


def render_band_kpoints(config: dict[str, Any], points_per_segment: int) -> str:
    path = config["vasp"]["band_path"]
    if len(path) < 2 or points_per_segment < 2:
        raise CampaignError(
            "band path needs at least two vertices and two points per segment"
        )
    lines = [
        "M-Gamma-K-M band path",
        str(int(points_per_segment)),
        "Line-mode",
        "Reciprocal",
    ]
    for start, stop in zip(path[:-1], path[1:]):
        for point in (start, stop):
            coordinates = " ".join(
                f"{float(value):.16f}" for value in point["fractional"]
            )
            lines.append(f"{coordinates}  ! {point['label']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _deck_file_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _job_deck_hashes(campaign_root: Path, job: dict[str, Any]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for stage_relative in job["stages"].values():
        stage = campaign_root / stage_relative
        for filename in ("INCAR", "KPOINTS", "POSCAR"):
            path = stage / filename
            if not path.is_file():
                raise CampaignError(f"prepared input deck is missing: {path}")
            hashes[str(path.relative_to(campaign_root))] = sha256_file(path)
    return hashes


def render_slurm_script(config: dict[str, Any], job_count: int) -> str:
    machine = config["machine"]
    return f"""#!/usr/bin/env bash
#SBATCH --job-name=tbg-dft-1807-10676
#SBATCH --array=0-{job_count - 1}
#SBATCH --cpus-per-task={int(machine["cpus_per_task"])}
#SBATCH --mem={int(machine["memory_gib"])}G
#SBATCH --time=30-00:00:00
#SBATCH --output=outputs/checks/dft_paper_scale/logs/slurm-%A_%a.out
#SBATCH --error=outputs/checks/dft_paper_scale/logs/slurm-%A_%a.err

set -euo pipefail

: "${{VASP_COMMAND:?Set VASP_COMMAND to the licensed VASP launch command}}"
: "${{VASP_C_POTCAR:?Set VASP_C_POTCAR to an external carbon LDA POTCAR}}"

mapfile -t DFT_JOB_IDS < outputs/checks/dft_paper_scale/slurm/job_ids.txt
DFT_JOB_ID="${{DFT_JOB_IDS[$SLURM_ARRAY_TASK_ID]}}"

python scripts/run_dft_campaign.py \\
  --config config/dft_paper_scale.json \\
  run-job \\
  --campaign-root outputs/checks/dft_paper_scale \\
  --job-id "$DFT_JOB_ID" \\
  --available-cpus "${{SLURM_CPUS_PER_TASK}}" \\
  --available-memory-gib {int(machine["memory_gib"])} \\
  --acknowledge-unpinned-potcar \\
  --resume
"""


def prepare_campaign(config: dict[str, Any], campaign_root: Path) -> dict[str, Any]:
    """Generate all structures and VASP decks without licensed external assets."""

    validate_config(config)
    campaign_root.mkdir(parents=True, exist_ok=True)
    geometry = config["geometry"]
    manifest_jobs: list[dict[str, Any]] = []
    structure_checks: list[dict[str, Any]] = []
    for job in campaign_jobs(config):
        structure = build_commensurate_structure(
            job.commensurate_index,
            lattice_constant_angstrom=float(geometry["lattice_constant_angstrom"]),
            base_interlayer_distance_angstrom=float(
                geometry["base_interlayer_distance_angstrom"]
            ),
            z_over_d0=job.z_over_d0,
            vacuum_angstrom=float(geometry["vacuum_angstrom"]),
        )
        check = validate_structure(structure)
        check["job_id"] = job.job_id
        structure_checks.append(check)
        job_root = campaign_root / "jobs" / job.job_id
        scf = job_root / "scf"
        scf.mkdir(parents=True, exist_ok=True)
        (scf / "POSCAR").write_text(
            render_poscar(structure, job.job_id), encoding="utf-8"
        )
        (scf / "INCAR").write_text(render_incar(config, job, "scf"), encoding="utf-8")
        (scf / "KPOINTS").write_text(render_scf_kpoints(job.scf_mesh), encoding="utf-8")
        stage_paths = {"scf": str(scf.relative_to(campaign_root))}
        if job.has_band_stage:
            bands = job_root / "bands"
            bands.mkdir(parents=True, exist_ok=True)
            (bands / "POSCAR").write_text(
                render_poscar(structure, job.job_id), encoding="utf-8"
            )
            (bands / "INCAR").write_text(
                render_incar(config, job, "bands"), encoding="utf-8"
            )
            (bands / "KPOINTS").write_text(
                render_band_kpoints(config, int(job.path_points_per_segment)),
                encoding="utf-8",
            )
            (bands / "CHGCAR.required").write_text(
                "Generated by the preceding SCF stage; the runner links it before execution.\n",
                encoding="utf-8",
            )
            stage_paths["bands"] = str(bands.relative_to(campaign_root))
        (job_root / "EXTERNAL_ASSETS_REQUIRED.json").write_text(
            json.dumps(config["external_assets"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest_job = {
            "job_id": job.job_id,
            "family": job.family,
            "commensurate_index": job.commensurate_index,
            "twist_angle_deg": math.degrees(structure.twist_angle_rad),
            "z_over_d0": job.z_over_d0,
            "interlayer_distance_angstrom": structure.interlayer_distance_angstrom,
            "atom_count": structure.atom_count,
            "scf_mesh": list(job.scf_mesh),
            "path_points_per_segment": job.path_points_per_segment,
            "target_ids": list(job.target_ids),
            "stages": stage_paths,
        }
        manifest_job["deck_input_hashes"] = _job_deck_hashes(
            campaign_root, manifest_job
        )
        manifest_jobs.append(manifest_job)

    job_ids = [job["job_id"] for job in manifest_jobs]
    slurm_root = campaign_root / "slurm"
    slurm_root.mkdir(parents=True, exist_ok=True)
    (slurm_root / "job_ids.txt").write_text("\n".join(job_ids) + "\n", encoding="utf-8")
    (slurm_root / "submit.slurm").write_text(
        render_slurm_script(config, len(job_ids)), encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "implementation_id": config["implementation_id"],
        "status": "code_ready_external_assets_required",
        "config_sha256": canonical_json_hash(config),
        "jobs": manifest_jobs,
        "target_ids": sorted(config["targets"]),
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numerical_arrays_used": False,
    }
    write_json(campaign_root / "campaign_manifest.json", manifest)
    readiness = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "job_count": len(manifest_jobs),
        "target_count": len(config["targets"]),
        "distance_z_over_d0": [job["z_over_d0"] for job in config["distance_jobs"]],
        "structures": structure_checks,
        "deck_hashes": _deck_file_hashes(campaign_root / "jobs"),
        "external_execution_status": "not_run_missing_licensed_assets_and_hpc",
    }
    write_json(campaign_root / "checks" / "deck_readiness.json", readiness)
    return readiness


def _resolve_executable(token: str) -> Path:
    if token.startswith("-"):
        raise ExternalAssetError(
            "the final VASP_COMMAND token must be the VASP executable, not an option"
        )
    candidate = Path(token).expanduser() if "/" in token else None
    if candidate is None:
        located = shutil.which(token)
        candidate = Path(located) if located else None
    if (
        candidate is None
        or not candidate.is_file()
        or not os.access(candidate, os.X_OK)
    ):
        raise ExternalAssetError(f"executable is unavailable: {token}")
    return candidate.resolve()


def _resolve_command(command_text: str) -> tuple[list[str], dict[str, Any]]:
    command = shlex.split(command_text)
    if not command:
        raise ExternalAssetError("VASP command is empty")
    try:
        launcher = _resolve_executable(command[0])
        vasp_executable = _resolve_executable(command[-1])
    except ExternalAssetError as error:
        raise ExternalAssetError(
            "licensed VASP launch command is unavailable: "
            f"{error}. Set VASP_COMMAND to a command such as "
            "'srun /path/to/vasp_std', with the VASP executable as the final token."
        ) from error
    return command, {
        "launcher_resolved_path": str(launcher),
        "launcher_sha256": sha256_file(launcher),
        "vasp_executable_resolved_path": str(vasp_executable),
        "vasp_executable_sha256": sha256_file(vasp_executable),
    }


def inspect_carbon_lda_potcar(path: Path) -> dict[str, Any]:
    """Verify the minimal metadata needed for the paper's carbon-LDA method."""

    text = path.read_text(encoding="utf-8", errors="replace")
    titles = re.findall(r"^\s*TITEL\s*=\s*(.+?)\s*$", text, flags=re.MULTILINE)
    lexch = re.findall(r"^\s*LEXCH\s*=\s*([A-Za-z0-9]+)", text, flags=re.MULTILINE)
    zvals = re.findall(
        r"^\s*POMASS\s*=.*?;\s*ZVAL\s*=\s*([-+0-9.Ee]+)",
        text,
        flags=re.MULTILINE,
    )
    if len(titles) != 1:
        raise ExternalAssetError(
            f"carbon POTCAR must contain exactly one TITEL dataset; found {len(titles)}"
        )
    title = titles[0].strip()
    if re.search(r"(?:^|[\s_])C(?:[\s_.]|$)", title, flags=re.IGNORECASE) is None:
        raise ExternalAssetError(f"POTCAR TITEL is not a carbon dataset: {title}")
    if not lexch or lexch[0].upper() != "CA":
        raise ExternalAssetError(
            "POTCAR is not marked as Ceperley-Alder LDA (expected LEXCH = CA)"
        )
    if not zvals or not math.isclose(float(zvals[0]), 4.0, abs_tol=1.0e-8):
        raise ExternalAssetError(
            "carbon POTCAR must report the standard four-electron valence (ZVAL = 4)"
        )
    return {
        "potcar_title": title,
        "potcar_lexch": lexch[0].upper(),
        "potcar_zval": float(zvals[0]),
    }


def preflight_external_assets(
    config: dict[str, Any],
    *,
    vasp_command: str | None,
    potcar_path: Path | None,
    acknowledge_unpinned_potcar: bool,
    available_cpus: int | None,
    available_memory_gib: int | None,
) -> dict[str, Any]:
    """Validate licensed assets and the paper-scale machine boundary."""

    external = config["external_assets"]
    command_text = vasp_command or os.environ.get(external["vasp_executable_env"])
    if not command_text:
        raise ExternalAssetError(
            f"missing licensed VASP executable: pass --vasp-command or set "
            f"{external['vasp_executable_env']}"
        )
    command, command_identity = _resolve_command(command_text)

    resolved_potcar = potcar_path
    if resolved_potcar is None:
        raw_path = os.environ.get(external["carbon_lda_potcar_env"])
        resolved_potcar = Path(raw_path).expanduser() if raw_path else None
    if resolved_potcar is None or not resolved_potcar.is_file():
        raise ExternalAssetError(
            "missing licensed carbon LDA POTCAR: pass --potcar or set "
            f"{external['carbon_lda_potcar_env']}; POTCAR must remain outside the repository"
        )
    potcar_metadata = inspect_carbon_lda_potcar(resolved_potcar)
    actual_hash = sha256_file(resolved_potcar)
    expected_hash = external.get("carbon_lda_potcar_expected_sha256")
    if expected_hash and actual_hash != expected_hash:
        raise ExternalAssetError(
            f"POTCAR SHA-256 mismatch: expected {expected_hash}, got {actual_hash}"
        )
    if expected_hash is None and not acknowledge_unpinned_potcar:
        raise ExternalAssetError(
            "the paper does not report the PAW/POTCAR identity. Re-run with "
            "--acknowledge-unpinned-potcar to make an explicit independent-reproduction "
            f"choice; the runner will record SHA-256 {actual_hash}"
        )

    machine = config["machine"]
    required_cpus = int(machine["cpus_per_task"])
    required_memory = int(machine["memory_gib"])
    if available_cpus is None or available_memory_gib is None:
        raise ExternalAssetError(
            "paper-scale machine declaration is required: pass --available-cpus and "
            "--available-memory-gib (configured minimum: "
            f"{required_cpus} CPU, {required_memory} GiB)"
        )
    if available_cpus < required_cpus or available_memory_gib < required_memory:
        raise ExternalAssetError(
            f"machine below paper-scale profile: have {available_cpus} CPU/"
            f"{available_memory_gib} GiB, require at least {required_cpus} CPU/"
            f"{required_memory} GiB"
        )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": (
            "passed_with_unpinned_author_paw" if expected_hash is None else "passed"
        ),
        "vasp_command": command,
        **command_identity,
        "potcar_path_recorded_as_external": str(resolved_potcar.resolve()),
        "potcar_sha256": actual_hash,
        **potcar_metadata,
        "paper_reported_potcar_sha256": expected_hash,
        "author_binary_equivalence": expected_hash is not None,
        "available_cpus": available_cpus,
        "available_memory_gib": available_memory_gib,
        "config_sha256": canonical_json_hash(config),
    }


def outcar_complete(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return any(OUTCAR_COMPLETION_MARKER in line for line in handle)


def _link_external_file(source: Path, destination: Path) -> None:
    if destination.is_symlink() and destination.resolve() == source.resolve():
        return
    if destination.exists() or destination.is_symlink():
        raise ExternalAssetError(
            f"refusing to replace existing external-asset path: {destination}"
        )
    destination.symlink_to(source.resolve())


def _run_stage(command: Sequence[str], stage: Path, *, resume: bool) -> None:
    if resume and outcar_complete(stage / "OUTCAR"):
        return
    stdout_path = stage / "vasp.stdout.log"
    stderr_path = stage / "vasp.stderr.log"
    with (
        stdout_path.open("a", encoding="utf-8") as stdout,
        stderr_path.open("a", encoding="utf-8") as stderr,
    ):
        result = subprocess.run(
            list(command),
            cwd=stage,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    if result.returncode != 0:
        raise CampaignError(
            f"VASP failed in {stage} with exit code {result.returncode}; "
            f"inspect {stdout_path.name} and {stderr_path.name}"
        )
    if not outcar_complete(stage / "OUTCAR"):
        raise CampaignError(
            f"VASP returned success but OUTCAR is incomplete in {stage}"
        )


def parse_vasp_version(outcar: Path) -> str:
    with outcar.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle):
            match = re.search(r"\bvasp\.([^\s]+)", line, flags=re.IGNORECASE)
            if match:
                return match.group(1)
            if line_number >= 200:
                break
    raise IncompleteResultError(f"OUTCAR has no VASP version banner: {outcar}")


def _job_result_hashes(campaign_root: Path, job: dict[str, Any]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for stage_relative in job["stages"].values():
        stage = campaign_root / stage_relative
        for filename in ("OUTCAR", "EIGENVAL"):
            path = stage / filename
            if not path.is_file():
                raise IncompleteResultError(
                    f"completed stage lacks {filename}: {stage}"
                )
            hashes[str(path.relative_to(campaign_root))] = sha256_file(path)
    return hashes


def run_campaign_job(
    config: dict[str, Any],
    campaign_root: Path,
    job_id: str,
    *,
    preflight: dict[str, Any],
    resume: bool,
) -> dict[str, Any]:
    manifest_path = campaign_root / "campaign_manifest.json"
    if not manifest_path.is_file():
        raise CampaignError(
            f"campaign is not prepared: missing {manifest_path}; run the prepare command first"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next((entry for entry in manifest["jobs"] if entry["job_id"] == job_id), None)
    if job is None:
        raise CampaignError(f"unknown job_id {job_id}")
    config_hash = canonical_json_hash(config)
    if manifest.get("config_sha256") != config_hash:
        raise CampaignError(
            "prepared campaign config hash does not match the active config"
        )
    if preflight.get("config_sha256") != config_hash:
        raise CampaignError(
            "external-asset preflight was produced for a different config"
        )
    for required_identity in ("vasp_executable_sha256", "potcar_sha256"):
        if not preflight.get(required_identity):
            raise CampaignError(
                f"preflight lacks required identity: {required_identity}"
            )
    current_deck_hashes = _job_deck_hashes(campaign_root, job)
    if current_deck_hashes != job.get("deck_input_hashes"):
        raise CampaignError(
            f"prepared input deck changed after manifest creation for {job_id}; run prepare again"
        )
    potcar = Path(preflight["potcar_path_recorded_as_external"])
    command = list(preflight["vasp_command"])
    completed_stages: list[str] = []
    scf = campaign_root / job["stages"]["scf"]
    _link_external_file(potcar, scf / "POTCAR")
    _run_stage(command, scf, resume=resume)
    completed_stages.append("scf")
    if "bands" in job["stages"]:
        chgcar = scf / "CHGCAR"
        if not chgcar.is_file():
            raise CampaignError(f"SCF completed without CHGCAR: {chgcar}")
        bands = campaign_root / job["stages"]["bands"]
        _link_external_file(potcar, bands / "POTCAR")
        _link_external_file(chgcar, bands / "CHGCAR")
        _run_stage(command, bands, resume=resume)
        completed_stages.append("bands")
    result_hashes = _job_result_hashes(campaign_root, job)
    vasp_versions = sorted(
        {
            parse_vasp_version(campaign_root / stage / "OUTCAR")
            for stage in job["stages"].values()
        }
    )
    result = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "job_id": job_id,
        "status": "completed",
        "completed_stages": completed_stages,
        "config_sha256": config_hash,
        "deck_input_hashes": current_deck_hashes,
        "result_hashes": result_hashes,
        "vasp_versions": vasp_versions,
        "vasp_executable_sha256": preflight["vasp_executable_sha256"],
        "potcar_sha256": preflight["potcar_sha256"],
        "author_binary_equivalence": preflight["author_binary_equivalence"],
        "machine": {
            "available_cpus": preflight["available_cpus"],
            "available_memory_gib": preflight["available_memory_gib"],
        },
    }
    write_json(campaign_root / "checks" / "jobs" / f"{job_id}.json", result)
    return result


@dataclass(frozen=True)
class EigenvalData:
    nelect: float
    kpoints: FloatArray
    weights: FloatArray
    energies: FloatArray
    occupations: FloatArray


def parse_eigenval(path: Path) -> EigenvalData:
    """Parse the ISPIN=1 subset of VASP's text EIGENVAL format."""

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 7:
        raise IncompleteResultError(f"EIGENVAL is truncated: {path}")
    try:
        header = lines[5].split()
        nelect = float(header[0])
        nkpoints = int(header[1])
        nbands = int(header[2])
    except (IndexError, ValueError) as error:
        raise IncompleteResultError(f"invalid EIGENVAL header in {path}") from error
    cursor = 6
    kpoints: list[list[float]] = []
    weights: list[float] = []
    energies: list[list[float]] = []
    occupations: list[list[float]] = []
    for _ in range(nkpoints):
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            raise IncompleteResultError(f"EIGENVAL lacks k-point rows in {path}")
        parts = lines[cursor].split()
        cursor += 1
        if len(parts) < 4:
            raise IncompleteResultError(f"invalid EIGENVAL k-point row in {path}")
        kpoints.append([float(value) for value in parts[:3]])
        weights.append(float(parts[3]))
        point_energies: list[float] = []
        point_occupations: list[float] = []
        for _band in range(nbands):
            if cursor >= len(lines):
                raise IncompleteResultError(f"EIGENVAL lacks band rows in {path}")
            band = lines[cursor].split()
            cursor += 1
            if len(band) < 3:
                raise IncompleteResultError(f"invalid EIGENVAL band row in {path}")
            point_energies.append(float(band[1]))
            point_occupations.append(float(band[2]))
        energies.append(point_energies)
        occupations.append(point_occupations)
    result = EigenvalData(
        nelect=nelect,
        kpoints=np.asarray(kpoints, dtype=float),
        weights=np.asarray(weights, dtype=float),
        energies=np.asarray(energies, dtype=float),
        occupations=np.asarray(occupations, dtype=float),
    )
    if not np.isfinite(result.energies).all():
        raise IncompleteResultError(f"EIGENVAL contains non-finite energies: {path}")
    return result


def parse_fermi_energy(outcar: Path) -> float:
    values: list[float] = []
    with outcar.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if "E-fermi" in line:
                try:
                    values.append(
                        float(line.split("E-fermi", 1)[1].split(":", 1)[1].split()[0])
                    )
                except (IndexError, ValueError):
                    continue
    if not values:
        raise IncompleteResultError(f"OUTCAR has no E-fermi value: {outcar}")
    return values[-1]


def occupied_band_count(nelect: float, nbands: int, minimum_each_side: int = 4) -> int:
    occupied = int(round(float(nelect) / 2.0))
    minimum = int(minimum_each_side)
    if occupied < minimum or occupied + minimum > nbands:
        raise IncompleteResultError(
            f"need at least {minimum} bands on each side of charge neutrality; "
            f"NELECT={nelect}, NBANDS={nbands}"
        )
    return occupied


def _path_vertex_indices(points_per_segment: int) -> dict[str, int]:
    points = int(points_per_segment)
    return {
        "M_start": 0,
        "Gamma": points - 1,
        "K": 2 * points - 1,
        "M_end": 3 * points - 1,
    }


def _write_band_csv(
    path: Path,
    data: EigenvalData,
    fermi: float,
    points_per_segment: int,
    bands_each_side: int,
) -> None:
    occupied = occupied_band_count(
        data.nelect, data.energies.shape[1], minimum_each_side=bands_each_side
    )
    lower = occupied - bands_each_side
    upper = occupied + bands_each_side
    vertices = _path_vertex_indices(points_per_segment)
    labels = {
        value: key.replace("_start", "").replace("_end", "")
        for key, value in vertices.items()
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "k_index",
                "kx_fractional",
                "ky_fractional",
                "label",
                "band_index",
                "energy_minus_fermi_ev",
            ]
        )
        for k_index, (kpoint, energies) in enumerate(
            zip(data.kpoints, data.energies, strict=True)
        ):
            for band_index in range(lower, upper):
                writer.writerow(
                    [
                        k_index,
                        f"{kpoint[0]:.16g}",
                        f"{kpoint[1]:.16g}",
                        labels.get(k_index, ""),
                        band_index + 1,
                        f"{energies[band_index] - fermi:.16g}",
                    ]
                )


def _neutrality_features(energies: FloatArray, nelect: float) -> dict[str, float]:
    occupied = occupied_band_count(nelect, len(energies))
    return {
        "lower_outer_ev": float(energies[occupied - 3]),
        "lower_middle_ev": float(energies[occupied - 2]),
        "valence_ev": float(energies[occupied - 1]),
        "conduction_ev": float(energies[occupied]),
        "upper_middle_ev": float(energies[occupied + 1]),
        "upper_outer_ev": float(energies[occupied + 2]),
        "lower_isolation_gap_ev": float(
            energies[occupied - 2] - energies[occupied - 3]
        ),
        "neutrality_gap_ev": float(energies[occupied] - energies[occupied - 1]),
        "upper_isolation_gap_ev": float(
            energies[occupied + 2] - energies[occupied + 1]
        ),
    }


def _i6_degeneracy_features(energies: FloatArray, nelect: float) -> dict[str, float]:
    """Return the 4-2-2-4 Gamma multiplet spreads reported for the gapped i=6 cell."""

    occupied = occupied_band_count(nelect, len(energies), minimum_each_side=6)
    groups = {
        "low56_fourfold_spread_ev": energies[occupied - 6 : occupied - 2],
        "gamma23_doublet_spread_ev": energies[occupied - 2 : occupied],
        "gamma14_doublet_spread_ev": energies[occupied : occupied + 2],
        "high56_fourfold_spread_ev": energies[occupied + 2 : occupied + 6],
    }
    return {
        name: float(np.max(values) - np.min(values)) for name, values in groups.items()
    }


def evaluate_science(
    config: dict[str, Any],
    gamma_rows: Sequence[dict[str, float]],
    angle_gap_rows: Sequence[dict[str, float]],
    distance_gap_rows: Sequence[dict[str, float]],
) -> dict[str, Any]:
    """Apply machine-readable paper feature checks to aggregate DFT results."""

    settings = config["acceptance"]["science"]
    tolerance = float(settings["trend_absolute_tolerance_ev"])
    gamma_by_i = {int(row["commensurate_index"]): row for row in gamma_rows}
    angle_by_i = {int(row["commensurate_index"]): row for row in angle_gap_rows}
    distance_sorted = sorted(
        distance_gap_rows, key=lambda row: -float(row["z_over_d0"])
    )
    checks: dict[str, dict[str, Any]] = {}

    required_gamma = [6, 10, 16, 23, 27, 30]
    gamma_complete = all(index in gamma_by_i for index in required_gamma)
    checks["gamma_indices_complete"] = {
        "passed": gamma_complete,
        "required": required_gamma,
        "actual": sorted(gamma_by_i),
    }
    if gamma_complete:
        lower_min = min(
            required_gamma,
            key=lambda index: abs(float(gamma_by_i[index]["lower_isolation_gap_ev"])),
        )
        upper_min = min(
            required_gamma,
            key=lambda index: abs(float(gamma_by_i[index]["upper_isolation_gap_ev"])),
        )
        index_tolerance = int(settings["gamma_minimum_index_tolerance"])
        checks["gamma_lower_gap_closes_at_i16"] = {
            "passed": abs(
                lower_min - int(settings["gamma_lower_gap_minimum_expected_i"])
            )
            <= index_tolerance,
            "minimum_index": lower_min,
        }
        checks["gamma_upper_gap_closes_at_i30"] = {
            "passed": abs(
                upper_min - int(settings["gamma_upper_gap_minimum_expected_i"])
            )
            <= index_tolerance,
            "minimum_index": upper_min,
        }
        degeneracy_keys = [
            "low56_fourfold_spread_ev",
            "gamma23_doublet_spread_ev",
            "gamma14_doublet_spread_ev",
            "high56_fourfold_spread_ev",
        ]
        degeneracy_tolerance = float(settings["degeneracy_tolerance_ev"])
        degeneracy_values = {key: float(gamma_by_i[6][key]) for key in degeneracy_keys}
        checks["gamma_i6_has_reported_4224_multiplets"] = {
            "passed": all(
                value <= degeneracy_tolerance for value in degeneracy_values.values()
            ),
            "spreads_ev": degeneracy_values,
            "tolerance_ev": degeneracy_tolerance,
        }
        fermi_window = float(settings["fermi_window_ev"])
        gamma_window_values = {
            index: float(gamma_by_i[index]["max_abs_selected_energy_minus_fermi_ev"])
            for index in required_gamma
        }
        checks["gamma_levels_within_declared_fermi_window"] = {
            "passed": all(
                value <= fermi_window for value in gamma_window_values.values()
            ),
            "max_abs_energy_minus_fermi_ev_by_i": gamma_window_values,
            "window_ev": fermi_window,
        }

    required_angle = [6, 10, 16, 23]
    angle_complete = all(index in angle_by_i for index in required_angle)
    angle_values = (
        [float(angle_by_i[index]["k_gap_ev"]) for index in required_angle]
        if angle_complete
        else []
    )
    checks["angle_k_gap_indices_complete"] = {
        "passed": angle_complete,
        "required": required_angle,
        "actual": sorted(angle_by_i),
    }
    if angle_complete:
        angle_trend = (
            angle_values[1] <= angle_values[0] + tolerance
            and angle_values[2] + tolerance >= angle_values[1]
            and angle_values[3] + tolerance >= angle_values[2]
        )
        checks["angle_k_gap_trend"] = {
            "passed": angle_trend,
            "values_ev_i6_i10_i16_i23": angle_values,
            "tolerance_ev": tolerance,
        }

    expected_z = [1.0, 0.9, 0.86, 0.83, 0.8]
    actual_z = [float(row["z_over_d0"]) for row in distance_sorted]
    distance_complete = actual_z == expected_z
    checks["distance_z_list_exact"] = {
        "passed": distance_complete,
        "required": expected_z,
        "actual": actual_z,
    }
    if distance_complete:
        values = [float(row["k_gap_ev"]) for row in distance_sorted]
        monotonic = all(
            next_value + tolerance >= value
            for value, next_value in zip(values[:-1], values[1:])
        )
        checks["distance_k_gap_nondecreasing_with_compression"] = {
            "passed": monotonic,
            "values_ev_descending_z": values,
            "tolerance_ev": tolerance,
        }

    status = (
        "passed"
        if checks and all(item["passed"] for item in checks.values())
        else "failed"
    )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "checks": checks,
    }


def _write_rows(
    path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def verify_execution_attestation(
    config: dict[str, Any], campaign_root: Path, manifest: dict[str, Any]
) -> dict[str, Any]:
    """Bind analysis to one config, deck set, VASP binary, POTCAR, and machine."""

    config_hash = canonical_json_hash(config)
    if manifest.get("config_sha256") != config_hash:
        raise IncompleteResultError(
            "campaign manifest does not match the active config"
        )
    preflight_path = campaign_root / "checks" / "external_asset_preflight.json"
    if not preflight_path.is_file():
        raise IncompleteResultError(
            "external asset preflight is missing; execute jobs through the campaign runner"
        )
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight.get("status") not in {"passed", "passed_with_unpinned_author_paw"}:
        raise IncompleteResultError("external asset preflight did not pass")
    if preflight.get("config_sha256") != config_hash:
        raise IncompleteResultError(
            "external asset preflight config hash does not match"
        )
    for identity in ("vasp_executable_sha256", "potcar_sha256"):
        if not preflight.get(identity):
            raise IncompleteResultError(f"external asset preflight lacks {identity}")
    machine = config["machine"]
    if int(preflight.get("available_cpus", 0)) < int(machine["cpus_per_task"]) or int(
        preflight.get("available_memory_gib", 0)
    ) < int(machine["memory_gib"]):
        raise IncompleteResultError(
            "recorded execution machine is below the paper-scale profile"
        )

    versions: set[str] = set()
    for job in manifest["jobs"]:
        check_path = campaign_root / "checks" / "jobs" / f"{job['job_id']}.json"
        if not check_path.is_file():
            raise IncompleteResultError(
                f"execution attestation is missing for {job['job_id']}: {check_path}"
            )
        check = json.loads(check_path.read_text(encoding="utf-8"))
        if check.get("status") != "completed":
            raise IncompleteResultError(
                f"job attestation is incomplete for {job['job_id']}"
            )
        if check.get("config_sha256") != config_hash:
            raise IncompleteResultError(f"job config hash mismatch for {job['job_id']}")
        if check.get("vasp_executable_sha256") != preflight["vasp_executable_sha256"]:
            raise IncompleteResultError(f"VASP executable changed for {job['job_id']}")
        if check.get("potcar_sha256") != preflight["potcar_sha256"]:
            raise IncompleteResultError(f"POTCAR changed for {job['job_id']}")
        current_decks = _job_deck_hashes(campaign_root, job)
        if current_decks != job.get("deck_input_hashes") or current_decks != check.get(
            "deck_input_hashes"
        ):
            raise IncompleteResultError(f"input deck hash mismatch for {job['job_id']}")
        if _job_result_hashes(campaign_root, job) != check.get("result_hashes"):
            raise IncompleteResultError(
                f"VASP result hash mismatch for {job['job_id']}"
            )
        versions.update(str(value) for value in check.get("vasp_versions", []))
    if len(versions) != 1:
        raise IncompleteResultError(
            f"campaign must use one recorded VASP version; got {sorted(versions)}"
        )
    return {
        "status": "passed",
        "config_sha256": config_hash,
        "vasp_executable_sha256": preflight["vasp_executable_sha256"],
        "vasp_version": next(iter(versions)),
        "potcar_sha256": preflight["potcar_sha256"],
        "potcar_title": preflight["potcar_title"],
        "author_binary_equivalence": preflight["author_binary_equivalence"],
        "job_attestations": len(manifest["jobs"]),
        "available_cpus": preflight["available_cpus"],
        "available_memory_gib": preflight["available_memory_gib"],
    }


def analyze_campaign(
    config: dict[str, Any], campaign_root: Path, workspace: Path
) -> dict[str, Any]:
    """Convert completed VASP text outputs into all D001-D012 data and checks."""

    manifest_path = campaign_root / "campaign_manifest.json"
    if not manifest_path.is_file():
        raise CampaignError("campaign_manifest.json is missing; run prepare first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    execution_attestation = verify_execution_attestation(
        config, campaign_root, manifest
    )
    jobs_by_id = {job.job_id: job for job in campaign_jobs(config)}
    target_output = {
        target_id: workspace / details["output"]
        for target_id, details in config["targets"].items()
    }
    gamma_rows: list[dict[str, Any]] = []
    gamma_level_rows: list[dict[str, Any]] = []
    angle_gap_rows: list[dict[str, Any]] = []
    distance_gap_rows: list[dict[str, Any]] = []
    target_status: dict[str, dict[str, Any]] = {}

    for entry in manifest["jobs"]:
        job = jobs_by_id[entry["job_id"]]
        stage_name = "bands" if job.has_band_stage else "scf"
        stage = campaign_root / entry["stages"][stage_name]
        if not outcar_complete(stage / "OUTCAR"):
            raise IncompleteResultError(
                f"{job.job_id} {stage_name} is incomplete; expected completed OUTCAR at {stage}"
            )
        data = parse_eigenval(stage / "EIGENVAL")
        fermi_source = campaign_root / entry["stages"]["scf"] / "OUTCAR"
        fermi = parse_fermi_energy(fermi_source)
        if job.has_band_stage:
            indices = _path_vertex_indices(int(job.path_points_per_segment))
            required_kpoints = 3 * int(job.path_points_per_segment)
            if len(data.kpoints) != required_kpoints:
                raise IncompleteResultError(
                    f"{job.job_id}: got {len(data.kpoints)} band k-points; expected {required_kpoints}"
                )
            gamma_index = indices["Gamma"]
            k_index = indices["K"]
        else:
            norms = np.linalg.norm(data.kpoints, axis=1)
            gamma_index = int(np.argmin(norms))
            k_index = -1
        if job.family == "angle":
            gamma_energies = data.energies[gamma_index]
            gamma = _neutrality_features(gamma_energies, data.nelect)
            if job.commensurate_index == 6:
                gamma.update(_i6_degeneracy_features(gamma_energies, data.nelect))
            twist_angle = math.degrees(commensurate_twist_angle(job.commensurate_index))
            gamma_rows.append(
                {
                    "commensurate_index": job.commensurate_index,
                    "twist_angle_deg": twist_angle,
                    **gamma,
                }
            )
            bands_each_side = int(
                config["acceptance"]["science"]["minimum_bands_each_side_of_fermi"]
            )
            occupied = occupied_band_count(
                data.nelect, len(gamma_energies), bands_each_side
            )
            selected_gamma = (
                gamma_energies[occupied - bands_each_side : occupied + bands_each_side]
                - fermi
            )
            gamma_rows[-1]["max_abs_selected_energy_minus_fermi_ev"] = float(
                np.max(np.abs(selected_gamma))
            )
            for band_index in range(
                occupied - bands_each_side, occupied + bands_each_side
            ):
                gamma_level_rows.append(
                    {
                        "commensurate_index": job.commensurate_index,
                        "twist_angle_deg": twist_angle,
                        "band_index": band_index + 1,
                        "band_offset_from_neutrality": band_index - occupied,
                        "energy_minus_fermi_ev": float(
                            gamma_energies[band_index] - fermi
                        ),
                        "fermi_ev": fermi,
                    }
                )

        if job.has_band_stage:
            k_features = _neutrality_features(data.energies[k_index], data.nelect)
            gap_row = {
                "commensurate_index": job.commensurate_index,
                "z_over_d0": job.z_over_d0,
                "k_gap_ev": k_features["neutrality_gap_ev"],
            }
            if job.family == "angle":
                angle_gap_rows.append(gap_row)
            else:
                distance_gap_rows.append(gap_row)
            for target_id in job.target_ids:
                if target_id in {"D001", "D002", "D012"}:
                    continue
                _write_band_csv(
                    target_output[target_id],
                    data,
                    fermi,
                    int(job.path_points_per_segment),
                    int(
                        config["acceptance"]["science"][
                            "minimum_bands_each_side_of_fermi"
                        ]
                    ),
                )
                target_status[target_id] = {
                    "status": "generated",
                    "output": str(target_output[target_id].relative_to(workspace)),
                    "job_id": job.job_id,
                    "kpoints": len(data.kpoints),
                }

    gamma_rows = sorted(
        {int(row["commensurate_index"]): row for row in gamma_rows}.values(),
        key=lambda row: int(row["commensurate_index"]),
    )
    gamma_level_rows = sorted(
        gamma_level_rows,
        key=lambda row: (
            int(row["commensurate_index"]),
            int(row["band_offset_from_neutrality"]),
        ),
    )
    angle_gap_rows = sorted(
        angle_gap_rows, key=lambda row: int(row["commensurate_index"])
    )
    distance_gap_rows = sorted(
        distance_gap_rows, key=lambda row: -float(row["z_over_d0"])
    )
    _write_rows(target_output["D001"], list(gamma_level_rows[0]), gamma_level_rows)
    _write_rows(target_output["D002"], list(angle_gap_rows[0]), angle_gap_rows)
    _write_rows(target_output["D012"], list(distance_gap_rows[0]), distance_gap_rows)
    for target_id in ("D001", "D002", "D012"):
        target_status[target_id] = {
            "status": "generated",
            "output": str(target_output[target_id].relative_to(workspace)),
        }
    target_status["D001"]["rows"] = len(gamma_level_rows)

    acceptance = evaluate_science(config, gamma_rows, angle_gap_rows, distance_gap_rows)
    acceptance["execution_attestation"] = execution_attestation
    acceptance["targets"] = target_status
    acceptance["config_sha256"] = canonical_json_hash(config)
    acceptance["generated_data_provenance"] = "independent_vasp_numerics"
    acceptance["source_pixels_used"] = False
    write_json(campaign_root / "checks" / "scientific_acceptance.json", acceptance)
    return acceptance
