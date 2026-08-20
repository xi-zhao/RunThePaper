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
from scipy import constants

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
    displacement_x: float = 0.0
    displacement_y: float = 0.0


@dataclass(frozen=True)
class RibbonGeometry:
    """Geometry and precomputed hopping graph for one ribbon width."""

    width_chains: int
    edge_orientation: str
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


def _build_periodic_ribbon_geometry(
    *,
    width_chains: int,
    edge_orientation: str,
    translation: FloatArray,
    site_rows: list[tuple[str, int, int, FloatArray]],
    infinite_sites: list[tuple[str, FloatArray]],
    expected_coordination: tuple[int, ...],
    distance_tolerance: float,
) -> RibbonGeometry:
    """Build NN/NNN Bloch terms for a periodic honeycomb strip.

    Zigzag and armchair strips differ only in the retained sites and periodic
    translation.  Keeping the graph construction in one implementation makes
    the bond-vector Rashba term and the oriented intrinsic-SO sign obey the
    same convention for both boundaries.
    """

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
                displacement = target_position - source_position
                nearest_terms.append(
                    BlochTerm(
                        target,
                        source,
                        cell_shift,
                        kind="nearest",
                        displacement_x=float(displacement[0]),
                        displacement_y=float(displacement[1]),
                    )
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
                    f"orientation={edge_orientation}, target={target}, "
                    f"source={source}, shift={cell_shift}, "
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
    if coordination != expected_coordination:
        raise RuntimeError(
            f"unexpected {edge_orientation} coordination {coordination}; "
            f"expected {expected_coordination}"
        )
    return RibbonGeometry(
        width_chains=width_chains,
        edge_orientation=edge_orientation,
        translation_length=float(np.linalg.norm(translation)),
        sites=sites,
        nearest_terms=tuple(nearest_terms),
        second_terms=tuple(second_terms),
        nearest_coordination=coordination,
    )


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
    infinite_sites = [
        (
            sublattice,
            _row_position(sublattice, row) + cell_shift * translation,
        )
        for row in range(-3, width_chains + 2)
        for sublattice in ("A", "B")
        for cell_shift in range(-3, 4)
    ]

    expected = (2,) + (3,) * (len(site_rows) - 2) + (2,)
    return _build_periodic_ribbon_geometry(
        width_chains=width_chains,
        edge_orientation="zigzag",
        translation=translation,
        site_rows=site_rows,
        infinite_sites=infinite_sites,
        expected_coordination=expected,
        distance_tolerance=distance_tolerance,
    )


def build_armchair_geometry(
    width_chains: int, *, distance_tolerance: float = 1e-8
) -> RibbonGeometry:
    """Construct an armchair strip periodic along ``a1+a2``.

    ``chain = n1-n2`` labels the finite coordinate.  Both A and B sites on
    each outer armchair dimer have coordination two, while all retained
    interior sites have coordination three.
    """

    if width_chains < 3:
        raise ValueError("width_chains must be at least 3")
    if distance_tolerance <= 0:
        raise ValueError("distance_tolerance must be positive")

    translation = np.asarray([0.0, 3.0], dtype=float)

    def armchair_positions(chain: int) -> tuple[FloatArray, FloatArray]:
        a_position = np.asarray(
            [sqrt(3.0) * chain / 2.0, 1.5 * (chain % 2)], dtype=float
        )
        return a_position, a_position + np.asarray([0.0, 1.0], dtype=float)

    site_rows: list[tuple[str, int, int, FloatArray]] = []
    for chain in range(width_chains):
        a_position, b_position = armchair_positions(chain)
        site_rows.append(("A", chain, chain % 2, a_position))
        site_rows.append(("B", chain, chain % 2, b_position))
    infinite_sites = [
        (sublattice, position + cell_shift * translation)
        for chain in range(-3, width_chains + 3)
        for sublattice, position in zip(("A", "B"), armchair_positions(chain))
        for cell_shift in range(-3, 4)
    ]
    expected = (2, 2) + (3,) * (2 * width_chains - 4) + (2, 2)
    return _build_periodic_ribbon_geometry(
        width_chains=width_chains,
        edge_orientation="armchair",
        translation=translation,
        site_rows=site_rows,
        infinite_sites=infinite_sites,
        expected_coordination=expected,
        distance_tolerance=distance_tolerance,
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


def spinful_ribbon_hamiltonian(
    geometry: RibbonGeometry,
    k_times_a: float,
    *,
    hopping_t: float = 1.0,
    spin_orbit_t2: float = 0.03,
    rashba_lambda: float = 0.0,
) -> ComplexArray:
    """Return the full spinful zigzag Hamiltonian including NN Rashba SO.

    The basis is ``(site, spin_z)``.  For a directed nearest-neighbour bond
    from source ``j`` to target ``i``, the printed lattice term is

    ``i lambda_R z . (s x d_ij) = i lambda_R (s_x d_y - s_y d_x)``.

    Keeping the bond displacement in :class:`BlochTerm` makes the Rashba
    parameter an actual input to the numerical Hamiltonian rather than a
    metadata-only value.
    """

    identity, spin_x, spin_y, spin_z = _pauli()
    size = 2 * len(geometry.sites)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for term in geometry.nearest_terms:
        phase = np.exp(1j * float(k_times_a) * term.translation)
        rashba = (
            1j
            * rashba_lambda
            * (spin_x * term.displacement_y - spin_y * term.displacement_x)
        )
        block = (hopping_t * identity + rashba) * phase
        target = slice(2 * term.target, 2 * term.target + 2)
        source = slice(2 * term.source, 2 * term.source + 2)
        matrix[target, source] += block
    for term in geometry.second_terms:
        phase = np.exp(1j * float(k_times_a) * term.translation)
        block = 1j * spin_orbit_t2 * term.nu * spin_z * phase
        target = slice(2 * term.target, 2 * term.target + 2)
        source = slice(2 * term.source, 2 * term.source + 2)
        matrix[target, source] += block
    return matrix


def spinful_band_eigensystem(
    geometry: RibbonGeometry,
    k_times_a: float,
    *,
    hopping_t: float = 1.0,
    spin_orbit_t2: float = 0.03,
    rashba_lambda: float = 0.0,
) -> tuple[FloatArray, ComplexArray]:
    matrix = spinful_ribbon_hamiltonian(
        geometry,
        k_times_a,
        hopping_t=hopping_t,
        spin_orbit_t2=spin_orbit_t2,
        rashba_lambda=rashba_lambda,
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
    if vectors.shape[0] == 2 * len(geometry.sites):
        chains = np.repeat(chains, 2)
    elif vectors.shape[0] != len(geometry.sites):
        raise ValueError("vectors do not match the spinless or spinful ribbon basis")
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


def honeycomb_bulk_hamiltonian(
    reciprocal_u: float,
    reciprocal_v: float,
    *,
    hopping_t: float = 1.0,
    spin_orbit_t2: float = 0.03,
    spin: int = 1,
) -> ComplexArray:
    """Two-band periodic Haldane block in reciprocal-lattice coordinates."""

    if spin not in (-1, 1):
        raise ValueError("spin must be -1 or +1")
    delta = np.asarray(
        [[0.0, -1.0], [sqrt(3.0) / 2.0, 0.5], [-sqrt(3.0) / 2.0, 0.5]],
        dtype=float,
    )
    lattice = np.column_stack((delta[1] - delta[0], delta[2] - delta[0]))
    reciprocal = 2.0 * pi * np.linalg.inv(lattice).T
    momentum = reciprocal @ np.asarray([reciprocal_u, reciprocal_v], dtype=float)
    nearest_structure = np.sum(np.exp(1j * delta @ momentum))
    second = np.asarray(
        [delta[1] - delta[2], delta[2] - delta[0], delta[0] - delta[1]],
        dtype=float,
    )
    mass = 2.0 * spin * spin_orbit_t2 * float(np.sum(np.sin(second @ momentum)))
    return np.asarray(
        [
            [mass, hopping_t * nearest_structure],
            [hopping_t * nearest_structure.conjugate(), -mass],
        ],
        dtype=np.complex128,
    )


def fukui_chern_number(
    spin: int,
    spin_orbit_t2: float,
    *,
    hopping_t: float = 1.0,
    grid_size: int = 31,
) -> float:
    """Compute the occupied-band Chern number on a periodic Fukui grid."""

    if grid_size < 5:
        raise ValueError("grid_size must be at least 5")
    if spin_orbit_t2 == 0:
        return 0.0
    states = np.empty((grid_size, grid_size, 2), dtype=np.complex128)
    for first in range(grid_size):
        for second in range(grid_size):
            matrix = honeycomb_bulk_hamiltonian(
                first / grid_size,
                second / grid_size,
                hopping_t=hopping_t,
                spin_orbit_t2=spin_orbit_t2,
                spin=spin,
            )
            _energies, vectors = np.linalg.eigh(matrix)
            states[first, second] = vectors[:, 0]

    flux = 0.0
    for first in range(grid_size):
        for second in range(grid_size):
            state = states[first, second]
            next_first = states[(first + 1) % grid_size, second]
            next_second = states[first, (second + 1) % grid_size]
            diagonal = states[(first + 1) % grid_size, (second + 1) % grid_size]
            link_first = np.vdot(state, next_first)
            link_second = np.vdot(state, next_second)
            shifted_second = np.vdot(next_first, diagonal)
            shifted_first = np.vdot(next_second, diagonal)
            plaquette = (
                link_first
                * shifted_second
                * np.conjugate(shifted_first)
                * np.conjugate(link_second)
            )
            flux += float(np.angle(plaquette))
    return flux / (2.0 * pi)


def spin_chern_numbers(
    spin_orbit_t2: float, *, hopping_t: float = 1.0, grid_size: int = 31
) -> dict[str, float]:
    """Numerically evaluate both conserved-spin Chern sectors."""

    return {
        "up": fukui_chern_number(
            1,
            spin_orbit_t2,
            hopping_t=hopping_t,
            grid_size=grid_size,
        ),
        "down": fukui_chern_number(
            -1,
            spin_orbit_t2,
            hopping_t=hopping_t,
            grid_size=grid_size,
        ),
    }


def helical_transmission_tensor(contact_count: int) -> FloatArray:
    """Return ideal clockwise/up and counter-clockwise/down transmissions."""

    if contact_count < 2:
        raise ValueError("contact_count must be at least 2")
    transmission = np.zeros((2, contact_count, contact_count), dtype=float)
    for source in range(contact_count):
        transmission[0, (source + 1) % contact_count, source] += 1.0
        transmission[1, (source - 1) % contact_count, source] += 1.0
    return transmission


def landauer_buttiker_currents(
    transmission: FloatArray, voltages: FloatArray
) -> FloatArray:
    """Compute spin-resolved terminal currents in units of e^2/h."""

    if transmission.ndim != 3 or transmission.shape[0] != 2:
        raise ValueError("transmission must have shape (2, contacts, contacts)")
    contacts = transmission.shape[1]
    if transmission.shape[2] != contacts or voltages.shape != (contacts,):
        raise ValueError("transmission and voltage dimensions do not agree")
    currents = np.zeros((2, contacts), dtype=float)
    for spin_index in range(2):
        for terminal in range(contacts):
            outgoing = float(np.sum(transmission[spin_index, :, terminal]))
            incoming = float(np.dot(transmission[spin_index, terminal, :], voltages))
            currents[spin_index, terminal] = outgoing * voltages[terminal] - incoming
    return currents


def transport_coefficients(chern_numbers: dict[str, float]) -> dict[str, float]:
    """Derive Fig. 2 coefficients from explicit helical transmission graphs."""

    two_terminal = helical_transmission_tensor(2)
    two_currents = landauer_buttiker_currents(
        two_terminal, np.asarray([1.0, 0.0], dtype=float)
    )
    four_terminal = helical_transmission_tensor(4)
    # Contact order is top, right, bottom, left, matching Fig. 2(b).
    four_currents = landauer_buttiker_currents(
        four_terminal, np.asarray([0.5, 0.0, -0.5, 0.0], dtype=float)
    )
    right_spin_in_e_over_4pi = float(four_currents[1, 1] - four_currents[0, 1])
    spin_hall = abs(chern_numbers["up"] - chern_numbers["down"]) / (4.0 * pi)
    return {
        "charge_conductance_in_e2_over_h": float(np.sum(two_currents[:, 0])),
        "spin_hall_conductivity_in_e": spin_hall,
        "adjacent_spin_conductance_in_e": abs(right_spin_in_e_over_4pi) / (4.0 * pi),
        "four_terminal_spin_current_in_eV": abs(right_spin_in_e_over_4pi) / (4.0 * pi),
        "four_terminal_charge_current_in_e2_over_h": float(np.sum(four_currents[:, 1])),
    }


def time_reversal_scattering_basis() -> ComplexArray:
    """Numerically find matrices satisfying S = s_y S^T s_y."""

    _identity, _spin_x, spin_y, _spin_z = _pauli()
    elementary = []
    for row in range(2):
        for column in range(2):
            matrix = np.zeros((2, 2), dtype=np.complex128)
            matrix[row, column] = 1.0
            elementary.append(matrix)
    constraint = np.column_stack(
        [(matrix - spin_y @ matrix.T @ spin_y).reshape(-1) for matrix in elementary]
    )
    _left, singular_values, right = np.linalg.svd(constraint)
    rank = int(np.sum(singular_values > 1e-12))
    null_vectors = right.conj().T[:, rank:]
    return np.asarray(
        [
            sum(
                (
                    coefficient * matrix
                    for coefficient, matrix in zip(vector, elementary)
                ),
                start=np.zeros((2, 2), dtype=np.complex128),
            )
            for vector in null_vectors.T
        ],
        dtype=np.complex128,
    )


def flux_pumped_spin_in_hbar(chern_numbers: dict[str, float]) -> float:
    """Spin transferred by one h/e flux insertion in units of hbar."""

    return abs(chern_numbers["up"] - chern_numbers["down"]) / 2.0


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
