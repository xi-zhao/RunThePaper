"""Independent numerical model for Kane and Mele, PRL 95, 226801.

The implementation is derived from the printed nearest- and second-neighbour
Hamiltonian.  It does not consume author source code, author arrays, EPS paths,
or digitized figure points.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

import numpy as np
from numpy.typing import NDArray
from scipy import constants, optimize

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class Site:
    """One site in the Bloch unit cell of a zigzag ribbon."""

    index: int
    sublattice: str
    chain: int
    row: int
    x: float
    y: float


@dataclass(frozen=True)
class BlochTerm:
    """A hopping from a translated source cell into the reference cell."""

    target: int
    source: int
    translation: int
    kind: str
    nu: int = 0


@dataclass(frozen=True)
class RibbonGeometry:
    """Geometry and precomputed hopping graph for one ribbon width."""

    width_chains: int
    translation_length: float
    sites: tuple[Site, ...]
    nearest_terms: tuple[BlochTerm, ...]
    second_terms: tuple[BlochTerm, ...]
    nearest_coordination: tuple[int, ...]


def _row_position(sublattice: str, row: int) -> FloatArray:
    x = 0.0 if row % 2 == 0 else sqrt(3.0) / 2.0
    y = 1.5 * row + (1.0 if sublattice == "B" else 0.0)
    return np.asarray([x, y], dtype=float)


def _cross_z(first: FloatArray, second: FloatArray) -> float:
    return float(first[0] * second[1] - first[1] * second[0])


def build_ribbon_geometry(
    width_chains: int, *, distance_tolerance: float = 1e-8
) -> RibbonGeometry:
    """Construct a conventional zigzag strip with twofold-coordinated edges.

    The retained rows are B[-1..N-2] and A[0..N-1].  This cut is important:
    retaining A/B rows with the same row index would create bearded edges and
    put the flat edge band in the complementary Brillouin-zone interval.
    """

    if width_chains < 2:
        raise ValueError("width_chains must be at least 2")
    if distance_tolerance <= 0:
        raise ValueError("distance_tolerance must be positive")

    translation = np.asarray([sqrt(3.0), 0.0])
    site_rows: list[tuple[str, int, int, FloatArray]] = []
    for chain in range(width_chains):
        site_rows.append(("B", chain, chain - 1, _row_position("B", chain - 1)))
        site_rows.append(("A", chain, chain, _row_position("A", chain)))
    sites = tuple(
        Site(
            index=index,
            sublattice=sublattice,
            chain=chain,
            row=row,
            x=float(position[0]),
            y=float(position[1]),
        )
        for index, (sublattice, chain, row, position) in enumerate(site_rows)
    )

    candidates = [
        (
            source_index,
            source_sublattice,
            cell_shift,
            source_position + cell_shift * translation,
        )
        for cell_shift in range(-2, 3)
        for source_index, (
            source_sublattice,
            _chain,
            _row,
            source_position,
        ) in enumerate(site_rows)
    ]
    infinite_sites = [
        (
            sublattice,
            _row_position(sublattice, row) + cell_shift * translation,
        )
        for row in range(-3, width_chains + 2)
        for sublattice in ("A", "B")
        for cell_shift in range(-3, 4)
    ]

    nearest_terms: list[BlochTerm] = []
    second_terms: list[BlochTerm] = []
    for target, (target_sublattice, _chain, _row, target_position) in enumerate(
        site_rows
    ):
        for source, source_sublattice, cell_shift, source_position in candidates:
            distance = float(np.linalg.norm(target_position - source_position))
            if (
                target_sublattice != source_sublattice
                and abs(distance - 1.0) <= distance_tolerance
            ):
                nearest_terms.append(
                    BlochTerm(target, source, cell_shift, kind="nearest")
                )
                continue
            if target_sublattice != source_sublattice:
                continue
            if target == source and cell_shift == 0:
                continue
            if abs(distance - sqrt(3.0)) > distance_tolerance:
                continue

            common_positions: list[FloatArray] = []
            for common_sublattice, common_position in infinite_sites:
                if common_sublattice == target_sublattice:
                    continue
                if (
                    abs(float(np.linalg.norm(common_position - target_position)) - 1.0)
                    <= distance_tolerance
                    and abs(
                        float(np.linalg.norm(common_position - source_position)) - 1.0
                    )
                    <= distance_tolerance
                    and not any(
                        np.linalg.norm(common_position - existing) <= distance_tolerance
                        for existing in common_positions
                    )
                ):
                    common_positions.append(common_position)
            if len(common_positions) != 1:
                raise RuntimeError(
                    "second-neighbour path is not unique: "
                    f"target={target}, source={source}, shift={cell_shift}, "
                    f"common={len(common_positions)}"
                )
            common = common_positions[0]
            first_bond = common - source_position
            second_bond = target_position - common
            orientation = _cross_z(first_bond, second_bond)
            if abs(orientation) <= distance_tolerance:
                raise RuntimeError("second-neighbour orientation is singular")
            second_terms.append(
                BlochTerm(
                    target,
                    source,
                    cell_shift,
                    kind="intrinsic_spin_orbit",
                    nu=1 if orientation > 0 else -1,
                )
            )

    coordination = tuple(
        sum(term.target == index for term in nearest_terms)
        for index in range(len(sites))
    )
    expected = (2,) + (3,) * (len(sites) - 2) + (2,)
    if coordination != expected:
        raise RuntimeError(
            f"unexpected zigzag coordination {coordination}; expected {expected}"
        )
    return RibbonGeometry(
        width_chains=width_chains,
        translation_length=float(translation[0]),
        sites=sites,
        nearest_terms=tuple(nearest_terms),
        second_terms=tuple(second_terms),
        nearest_coordination=coordination,
    )


def ribbon_hamiltonian(
    geometry: RibbonGeometry,
    k_times_a: float,
    *,
    hopping_t: float = 1.0,
    spin_orbit_t2: float = 0.03,
    spin: int = 1,
) -> ComplexArray:
    """Return one conserved-spin block of the zigzag Bloch Hamiltonian."""

    if spin not in (-1, 1):
        raise ValueError("spin must be -1 or +1")
    size = len(geometry.sites)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for term in geometry.nearest_terms:
        phase = np.exp(1j * float(k_times_a) * term.translation)
        matrix[term.target, term.source] += hopping_t * phase
    for term in geometry.second_terms:
        phase = np.exp(1j * float(k_times_a) * term.translation)
        matrix[term.target, term.source] += 1j * spin_orbit_t2 * spin * term.nu * phase
    return matrix


def band_eigensystem(
    geometry: RibbonGeometry,
    k_times_a: float,
    *,
    hopping_t: float = 1.0,
    spin_orbit_t2: float = 0.03,
    spin: int = 1,
) -> tuple[FloatArray, ComplexArray]:
    matrix = ribbon_hamiltonian(
        geometry,
        k_times_a,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        spin=spin,
    )
    energies, vectors = np.linalg.eigh(matrix)
    return np.asarray(energies, dtype=float), np.asarray(vectors, dtype=np.complex128)


def edge_weights(
    geometry: RibbonGeometry, vectors: ComplexArray, *, chain_depth: int = 2
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Return total, bottom and top edge probabilities for eigenvector columns."""

    if chain_depth < 1 or 2 * chain_depth > geometry.width_chains:
        raise ValueError("chain_depth must select disjoint non-empty edges")
    chains = np.asarray([site.chain for site in geometry.sites], dtype=int)
    bottom = chains < chain_depth
    top = chains >= geometry.width_chains - chain_depth
    probabilities = np.abs(vectors) ** 2
    bottom_weights = np.asarray(probabilities[bottom, :].sum(axis=0), dtype=float)
    top_weights = np.asarray(probabilities[top, :].sum(axis=0), dtype=float)
    return bottom_weights + top_weights, bottom_weights, top_weights


def analytic_bulk_gap(spin_orbit_t2: float) -> float:
    """Full low-energy bulk gap 2 Delta_so in units of the hopping."""

    return 6.0 * sqrt(3.0) * abs(float(spin_orbit_t2))


def _pauli() -> tuple[ComplexArray, ComplexArray, ComplexArray, ComplexArray]:
    identity = np.eye(2, dtype=np.complex128)
    sigma_x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    sigma_y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    sigma_z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    return identity, sigma_x, sigma_y, sigma_z


def _operator(
    sublattice: ComplexArray, valley: ComplexArray, spin: ComplexArray
) -> ComplexArray:
    return np.kron(np.kron(sublattice, valley), spin)


def continuum_hamiltonian(
    qx: float,
    qy: float,
    *,
    hbar_vf: float = 1.0,
    delta_so: float = 0.2,
    lambda_r: float = 0.0,
) -> ComplexArray:
    """Eight-dimensional K/K' continuum Hamiltonian from Eqs. (2)-(4)."""

    identity, sigma_x, sigma_y, sigma_z = _pauli()
    kinetic = hbar_vf * (
        qx * _operator(sigma_x, sigma_z, identity)
        + qy * _operator(sigma_y, identity, identity)
    )
    intrinsic = delta_so * _operator(sigma_z, sigma_z, sigma_z)
    rashba = lambda_r * (
        _operator(sigma_x, sigma_z, sigma_y) - _operator(sigma_y, identity, sigma_x)
    )
    return kinetic + intrinsic + rashba


def continuum_energies(
    qx: float,
    qy: float,
    *,
    hbar_vf: float = 1.0,
    delta_so: float = 0.2,
    lambda_r: float = 0.0,
) -> FloatArray:
    return np.linalg.eigvalsh(
        continuum_hamiltonian(
            qx,
            qy,
            hbar_vf=hbar_vf,
            delta_so=delta_so,
            lambda_r=lambda_r,
        )
    )


def spin_chern_reference(spin: int, spin_orbit_t2: float) -> int:
    """Dirac-mass Chern number for a conserved-spin Haldane block."""

    if spin not in (-1, 1):
        raise ValueError("spin must be -1 or +1")
    if spin_orbit_t2 == 0:
        return 0
    return spin * (1 if spin_orbit_t2 > 0 else -1)


def transport_coefficients() -> dict[str, float]:
    """Dimensionless coefficients multiplying the units printed in the paper."""

    return {
        "charge_conductance_in_e2_over_h": 2.0,
        "spin_hall_conductivity_in_e": 1.0 / (2.0 * pi),
        "adjacent_spin_conductance_in_e": 1.0 / (4.0 * pi),
        "four_terminal_spin_current_in_eV": 1.0 / (4.0 * pi),
    }


def bare_gap_kelvin(lattice_constant_angstrom: float = 2.46) -> float:
    """Evaluate the paper's first-star full-gap estimate with SI constants."""

    lattice_constant = lattice_constant_angstrom * 1e-10
    coulomb_e_squared = constants.elementary_charge**2 / (
        4.0 * pi * constants.epsilon_0
    )
    gap_joule = (
        4.0
        * pi**2
        * coulomb_e_squared
        * constants.hbar**2
        / (3.0 * constants.m_e**2 * constants.c**2 * lattice_constant**3)
    )
    return float(gap_joule / constants.k)


def rashba_kelvin(
    *,
    fermi_velocity_m_per_s: float,
    electric_field_volts: float,
    electric_field_distance_nm: float,
) -> float:
    """Evaluate lambda_R/k_B for the printed perpendicular-field estimate."""

    electric_field = electric_field_volts / (electric_field_distance_nm * 1e-9)
    energy_joule = (
        constants.hbar
        * fermi_velocity_m_per_s
        * constants.elementary_charge
        * electric_field
        / (4.0 * constants.m_e * constants.c**2)
    )
    return float(energy_joule / constants.k)


def renormalized_gap_kelvin(
    *, bare_full_gap_kelvin: float, coulomb_g0: float, cutoff_ev: float
) -> float:
    """Solve the paper's self-consistency equation and return the full gap."""

    if bare_full_gap_kelvin <= 0 or coulomb_g0 <= 0 or cutoff_ev <= 0:
        raise ValueError("RG inputs must be positive")
    bare_half_gap = bare_full_gap_kelvin / 2.0
    cutoff_kelvin = cutoff_ev * constants.elementary_charge / constants.k

    def residual(half_gap: float) -> float:
        enhancement = 1.0 + coulomb_g0 * np.log(cutoff_kelvin / half_gap) / 4.0
        return float(half_gap - bare_half_gap * enhancement**2)

    renormalized_half_gap = optimize.brentq(
        residual, bare_half_gap, cutoff_kelvin, xtol=1e-13, rtol=1e-13
    )
    return float(2.0 * renormalized_half_gap)
