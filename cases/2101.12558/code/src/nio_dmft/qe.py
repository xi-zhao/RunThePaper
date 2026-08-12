"""Quantum ESPRESSO/Wannier90 input and Hamiltonian interfaces.

Only public scientific backends are supported. Pseudopotential identity and
hashes are mandatory for execution, preventing an apparently successful run
with silently different material inputs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .structure import SlabStructure


class ExternalInputError(RuntimeError):
    """A required external scientific input is absent or inconsistent."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pseudopotentials(
    specifications: dict[str, dict[str, Any]],
    root: Path,
) -> dict[str, dict[str, str]]:
    resolved: dict[str, dict[str, str]] = {}
    for species in ("Ni", "O"):
        item = specifications.get(species, {})
        relative = item.get("path")
        expected = item.get("sha256")
        if (
            not isinstance(relative, str)
            or not relative
            or not isinstance(expected, str)
            or not expected
        ):
            raise ExternalInputError(f"{species} pseudopotential path/hash is required")
        candidate = (root / relative).resolve()
        candidate.relative_to(root.resolve())
        if not candidate.is_file():
            raise ExternalInputError(f"missing {species} pseudopotential: {relative}")
        actual = sha256(candidate)
        if actual != expected:
            raise ExternalInputError(f"{species} pseudopotential hash mismatch")
        resolved[species] = {"path": str(candidate), "sha256": actual}
    return resolved


def render_pw_input(
    structure: SlabStructure,
    *,
    prefix: str,
    pseudo_names: dict[str, str],
    cutoffs_ry: tuple[float, float],
    kmesh: tuple[int, int, int],
    calculation: str,
    convergence: dict[str, float],
) -> str:
    if calculation not in {"scf", "relax"}:
        raise ValueError("calculation must be scf or relax")
    ecutwfc, ecutrho = cutoffs_ry
    if ecutwfc <= 0.0 or ecutrho < ecutwfc:
        raise ValueError("invalid plane-wave cutoffs")
    if len(kmesh) != 3 or any(int(value) <= 0 for value in kmesh):
        raise ValueError("kmesh requires three positive integers")
    lines = [
        "&CONTROL",
        f"  calculation = '{calculation}'",
        f"  prefix = '{prefix}'",
        "  pseudo_dir = './pseudo'",
        "  outdir = './scratch'",
        "/",
        "&SYSTEM",
        "  ibrav = 0",
        f"  nat = {len(structure.atoms)}",
        "  ntyp = 2",
        f"  ecutwfc = {ecutwfc:.8f}",
        f"  ecutrho = {ecutrho:.8f}",
        "  occupations = 'fixed'",
        "  nspin = 1",
        "/",
        "&ELECTRONS",
        f"  conv_thr = {float(convergence['scf_energy_ry']):.12e}",
        f"  mixing_beta = {float(convergence['mixing_beta']):.8f}",
        f"  electron_maxstep = {int(convergence['electron_maxstep'])}",
        "/",
    ]
    if calculation == "relax":
        lines.extend(["&IONS", "  ion_dynamics = 'bfgs'", "/"])
    lines.extend(
        [
            "ATOMIC_SPECIES",
            f"Ni 58.6934 {pseudo_names['Ni']}",
            f"O  15.9990 {pseudo_names['O']}",
            "CELL_PARAMETERS angstrom",
        ]
    )
    lines.extend(
        "  " + " ".join(f"{value:.12f}" for value in vector)
        for vector in structure.cell_angstrom
    )
    lines.append("ATOMIC_POSITIONS angstrom")
    lines.extend(
        f"{atom.species}  "
        + " ".join(f"{value:.12f}" for value in atom.position_angstrom)
        for atom in structure.atoms
    )
    lines.extend(
        [
            "K_POINTS automatic",
            f"{kmesh[0]} {kmesh[1]} {kmesh[2]} 0 0 0",
        ]
    )
    return "\n".join(lines) + "\n"


def render_wannier_input(
    *,
    prefix: str,
    n_wann: int,
    n_bands: int,
    kmesh: tuple[int, int, int],
    projection_lines: tuple[str, ...],
    disentanglement_window_ev: tuple[float, float],
) -> str:
    if n_wann < 1 or n_bands < n_wann:
        raise ValueError("n_bands must be at least n_wann")
    lower, upper = disentanglement_window_ev
    if not lower < upper:
        raise ValueError("invalid disentanglement window")
    return "\n".join(
        [
            f"num_wann = {n_wann}",
            f"num_bands = {n_bands}",
            f"mp_grid = {kmesh[0]} {kmesh[1]} {kmesh[2]}",
            f"dis_win_min = {lower:.8f}",
            f"dis_win_max = {upper:.8f}",
            "begin projections",
            *projection_lines,
            "end projections",
            "bands_plot = true",
            "write_hr = true",
            f"seedname = {prefix}",
            "",
        ]
    )


def render_pw2wannier_input(prefix: str) -> str:
    return (
        "&INPUTPP\n"
        f"  outdir = './scratch'\n  prefix = '{prefix}'\n"
        f"  seedname = '{prefix}'\n  write_mmn = .true.\n"
        "  write_amn = .true.\n/\n"
    )


def parse_wannier_hr(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parse a standard Wannier90 ``*_hr.dat`` file."""

    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 4:
        raise ExternalInputError("Wannier Hamiltonian file is truncated")
    n_wann = int(lines[1].strip())
    n_r = int(lines[2].strip())
    cursor = 3
    degeneracies: list[int] = []
    while len(degeneracies) < n_r:
        degeneracies.extend(int(value) for value in lines[cursor].split())
        cursor += 1
    matrices: dict[tuple[int, int, int], np.ndarray] = {}
    for line in lines[cursor:]:
        fields = line.split()
        if len(fields) != 7:
            continue
        translation = tuple(int(value) for value in fields[:3])
        row, column = int(fields[3]) - 1, int(fields[4]) - 1
        matrix = matrices.setdefault(
            translation,
            np.zeros((n_wann, n_wann), dtype=np.complex128),
        )
        matrix[row, column] = float(fields[5]) + 1j * float(fields[6])
    if len(matrices) != n_r:
        raise ExternalInputError("Wannier Hamiltonian translation count mismatch")
    translations = np.asarray(list(matrices), dtype=int)
    values = np.stack([matrices[tuple(row)] for row in translations])
    return translations, np.asarray(degeneracies[:n_r], dtype=int), values


def hamiltonian_from_hr(
    translations: np.ndarray,
    degeneracies: np.ndarray,
    values: np.ndarray,
    fractional_kpoints: np.ndarray,
) -> np.ndarray:
    kpoints = np.asarray(fractional_kpoints, dtype=float)
    phase = np.exp(2j * np.pi * kpoints @ np.asarray(translations, dtype=float).T)
    weighted = values / np.asarray(degeneracies, dtype=float)[:, None, None]
    hamiltonian = np.einsum("kr,rij->kij", phase, weighted, optimize=True)
    hermiticity = float(
        np.max(np.abs(hamiltonian - hamiltonian.swapaxes(-1, -2).conj()))
    )
    if hermiticity > 1e-7:
        raise ExternalInputError(
            f"interpolated Hamiltonian is non-Hermitian: {hermiticity:.3e}"
        )
    return hamiltonian


def write_deck_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
