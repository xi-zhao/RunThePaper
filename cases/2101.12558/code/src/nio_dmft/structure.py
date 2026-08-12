"""Independent rocksalt NiO slab construction.

The paper does not publish relaxed Cartesian coordinates. This module turns
the printed lattice constant, slab thickness, vacuum, layer count, and
inter-layer relaxations into an explicit *reconstructed* geometry. The
result is suitable for a convergence campaign, but is never paper-exact.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Atom:
    species: str
    position_angstrom: tuple[float, float, float]


@dataclass(frozen=True)
class SlabStructure:
    orientation: str
    cell_angstrom: np.ndarray
    atoms: tuple[Atom, ...]
    layer_z_angstrom: np.ndarray
    relaxed: bool
    provenance: str

    @property
    def surface_area_angstrom2(self) -> float:
        return float(
            np.linalg.norm(np.cross(self.cell_angstrom[0], self.cell_angstrom[1]))
        )

    def validate(self, *, tolerance: float = 1e-9) -> None:
        cell = np.asarray(self.cell_angstrom, dtype=float)
        if cell.shape != (3, 3) or abs(float(np.linalg.det(cell))) < tolerance:
            raise ValueError("slab cell must be a nonsingular 3x3 matrix")
        if self.orientation not in {"001", "110"}:
            raise ValueError("orientation must be 001 or 110")
        if len(self.atoms) != 2 * self.layer_z_angstrom.size:
            raise ValueError("each reconstructed layer must contain one Ni and one O")
        if np.any(np.diff(self.layer_z_angstrom) <= 0.0):
            raise ValueError("layer positions must be strictly ordered")
        z_max = float(cell[2, 2])
        if any(not 0.0 < atom.position_angstrom[2] < z_max for atom in self.atoms):
            raise ValueError("all atoms must lie inside the slab cell")


def _symmetric_spacings(
    n_layers: int,
    thickness_angstrom: float,
    relaxation_percent: tuple[float, ...],
) -> np.ndarray:
    """Return symmetric spacings while preserving the printed total thickness."""

    if n_layers < 3 or n_layers % 2 == 0:
        raise ValueError("the symmetric slab requires an odd number of layers")
    if thickness_angstrom <= 0.0:
        raise ValueError("thickness must be positive")
    n_spacing = n_layers - 1
    factors = np.ones(n_spacing, dtype=float)
    for depth, percent in enumerate(relaxation_percent):
        if depth >= n_spacing // 2:
            break
        factor = 1.0 + float(percent) / 100.0
        if factor <= 0.0:
            raise ValueError("a layer relaxation collapses the slab")
        factors[depth] = factor
        factors[-depth - 1] = factor
    return thickness_angstrom * factors / float(np.sum(factors))


def build_rocksalt_slab(
    *,
    orientation: str,
    lattice_angstrom: float,
    n_layers: int,
    thickness_angstrom: float,
    vacuum_angstrom: float,
    relaxed: bool,
    relaxation_percent: tuple[float, ...],
) -> SlabStructure:
    """Construct a charge-neutral, inversion-symmetric NiO slab.

    In-plane primitive cells are selected independently from rocksalt lattice
    vectors. Exact relaxed coordinates are unavailable, so only the printed
    normal separations are imposed. Both surfaces are related by inversion.
    """

    if lattice_angstrom <= 0.0 or vacuum_angstrom <= 0.0:
        raise ValueError("lattice constant and vacuum must be positive")
    if orientation == "001":
        a1 = 0.5 * lattice_angstrom * np.array([1.0, 1.0, 0.0])
        a2 = 0.5 * lattice_angstrom * np.array([-1.0, 1.0, 0.0])
    elif orientation == "110":
        # Local Cartesian axes represent crystallographic [001], [1 -1 0],
        # and the surface-normal [110], respectively.
        a1 = lattice_angstrom * np.array([1.0, 0.0, 0.0])
        a2 = (lattice_angstrom / np.sqrt(2.0)) * np.array([0.0, 1.0, 0.0])
    else:
        raise ValueError("orientation must be 001 or 110")

    spacing = _symmetric_spacings(
        n_layers,
        thickness_angstrom,
        relaxation_percent if relaxed else (),
    )
    layer_z = np.concatenate(([0.0], np.cumsum(spacing))) + vacuum_angstrom / 2.0
    cell_height = thickness_angstrom + vacuum_angstrom
    cell = np.vstack([a1, a2, np.array([0.0, 0.0, cell_height])])
    atoms: list[Atom] = []
    for layer, z_value in enumerate(layer_z):
        parity = layer % 2
        ni_fractional = np.array([0.0, 0.0]) if parity == 0 else np.array([0.5, 0.5])
        o_fractional = np.array([0.5, 0.5]) if parity == 0 else np.array([0.0, 0.0])
        for species, fractional in (("Ni", ni_fractional), ("O", o_fractional)):
            xy = fractional[0] * a1 + fractional[1] * a2
            atoms.append(Atom(species, (float(xy[0]), float(xy[1]), float(z_value))))

    structure = SlabStructure(
        orientation=orientation,
        cell_angstrom=cell,
        atoms=tuple(atoms),
        layer_z_angstrom=layer_z,
        relaxed=relaxed,
        provenance="reconstructed_from_printed_scalar_geometry_not_author_coordinates",
    )
    structure.validate()
    return structure
