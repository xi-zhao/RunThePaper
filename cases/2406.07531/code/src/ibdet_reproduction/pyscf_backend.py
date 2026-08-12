"""Independent PySCF mean-field entrypoint for paper-scale work units.

This module intentionally imports PySCF only inside execution functions. The
local verification lane can validate plans without installing a large
production dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


class BackendUnavailable(RuntimeError):
    """A production dependency or algorithmic backend is unavailable."""


def _imports() -> tuple[Any, Any, Any]:
    try:
        from pyscf.pbc import dft, gto, scf
    except ImportError as exc:
        raise BackendUnavailable(
            "PySCF periodic modules are required for paper-scale mean-field execution"
        ) from exc
    return gto, scf, dft


def build_cell(material: dict[str, Any]) -> Any:
    """Build an independent periodic Gaussian cell from the frozen config."""

    gto, _, _ = _imports()
    cell = gto.Cell()
    cell.unit = "Angstrom"
    cell.a = np.asarray(material["structure"]["lattice_angstrom"], dtype=float)
    cell.atom = [
        [entry["element"], tuple(float(value) for value in entry["cartesian_angstrom"])]
        for entry in material["structure"]["atoms"]
    ]
    cell.basis = material["basis"]
    if material.get("pseudopotential"):
        cell.pseudo = material["pseudopotential"]
    cell.precision = float(material.get("integral_precision", 1e-9))
    cell.mesh = [int(value) for value in material.get("fft_mesh", [60, 60, 60])]
    cell.verbose = 4
    cell.build()
    return cell


def run_mean_field(
    material: dict[str, Any],
    reference: str,
    output_path: Path,
) -> dict[str, Any]:
    """Execute KRKS(PBE) or KRHF and freeze one-particle tensors."""

    _, scf, dft = _imports()
    cell = build_cell(material)
    kpoints = cell.make_kpts([int(value) for value in material["kmesh"]])
    if reference == "PBE":
        solver = dft.KRKS(cell, kpts=kpoints)
        solver.xc = "PBE"
    elif reference == "HF":
        solver = scf.KRHF(cell, kpts=kpoints)
    else:
        raise ValueError(f"unsupported mean-field reference: {reference}")
    solver.conv_tol = float(material.get("scf_tolerance", 1e-9))
    solver.max_cycle = int(material.get("scf_max_cycles", 100))
    solver.chkfile = str(output_path.with_suffix(".chk"))
    energy = float(solver.kernel())
    if not solver.converged:
        raise RuntimeError("periodic mean-field solver did not converge")
    overlap = np.asarray(solver.get_ovlp(), dtype=np.complex128)
    density = np.asarray(solver.make_rdm1(), dtype=np.complex128)
    fock = np.asarray(solver.get_fock(dm_kpts=density), dtype=np.complex128)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        total_energy_hartree=energy,
        kpoints=np.asarray(kpoints),
        overlap=overlap,
        density=density,
        fock=fock,
        mo_energy=np.asarray(solver.mo_energy),
        mo_occ=np.asarray(solver.mo_occ),
        mo_coeff=np.asarray(solver.mo_coeff),
    )
    return {
        "converged": True,
        "total_energy_hartree": energy,
        "kpoint_count": int(len(kpoints)),
        "output": output_path.as_posix(),
    }


def correlated_solver_boundary(embedding_orbitals: int) -> None:
    """Fail before accidentally treating a missing CCGF implementation as a result."""

    raise BackendUnavailable(
        "The paper-scale real-axis EOM-CCSD Green-function solve requires an "
        f"independently implemented production backend for {embedding_orbitals} "
        "embedding orbitals. The case supplies and tests the defining algebra, "
        "Hamiltonian decks, resource plan, and exact small-system cross-check, "
        "but it does not substitute author code, digitized spectra, or a proxy "
        "self-energy for this production result."
    )
