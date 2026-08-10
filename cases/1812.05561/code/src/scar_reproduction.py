r"""Independent numerics for arXiv:1812.05561.

The implementation follows the Hamiltonians and algorithms printed in the
paper and its supplement.  It deliberately contains no reader for paper PDFs,
source figures, digitized curves, or author data.

Spin convention
---------------
``1`` is :math:`|\uparrow\rangle` (sigma-z eigenvalue +1) and ``0`` is
:math:`|\downarrow\rangle` (sigma-z eigenvalue -1).  Constrained bases contain
no adjacent ``1`` bits.  Site labels are zero based in code.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy import sparse
from scipy.linalg import eigh
from scipy.optimize import brentq
from scipy.sparse.linalg import eigsh


PHI = (1.0 + math.sqrt(5.0)) / 2.0


def spin_z(state: int, site: int) -> int:
    """Return the sigma-z eigenvalue at ``site``."""

    return 1 if (state >> site) & 1 else -1


@lru_cache(maxsize=None)
def constrained_basis(n_sites: int, periodic: bool = True) -> tuple[int, ...]:
    """Enumerate blockade-allowed bit strings without scanning ``2**N``."""

    if n_sites < 2:
        raise ValueError("n_sites must be at least two")
    states: list[int] = []

    def visit(site: int, previous_up: bool, state: int) -> None:
        if site == n_sites:
            if not periodic or not ((state & 1) and ((state >> (n_sites - 1)) & 1)):
                states.append(state)
            return
        visit(site + 1, False, state)
        if not previous_up:
            visit(site + 1, True, state | (1 << site))

    visit(0, False, 0)
    return tuple(states)


def neel_state(n_sites: int, shift: int = 0) -> int:
    """Return one of the two period-two product states."""

    if n_sites % 2:
        raise ValueError("the periodic Neel state requires even n_sites")
    return sum(1 << site for site in range(shift, n_sites, 2))


def ansatz_couplings(h0: float, max_range: int) -> dict[int, float]:
    """Main-text Eq. (4), for distances 2 through ``max_range``."""

    return {
        distance: h0
        / (PHI ** (distance - 1) - PHI ** (-(distance - 1))) ** 2
        for distance in range(2, max_range + 1)
    }


def su2_constraint(h0: float, truncation: int = 200) -> float:
    """Residual of main-text Eq. (6) for the infinite ansatz hierarchy."""

    couplings = ansatz_couplings(h0, truncation)
    alternating = 2.0 * sum(value * ((-1) ** distance) for distance, value in couplings.items())
    even = [value for distance, value in couplings.items() if distance % 2 == 0]
    return (1.0 - alternating) * (1.0 - alternating - 16.0 * sum(even)) - 16.0 * sum(
        value * value for value in even
    )


def solve_h0() -> float:
    """Solve Eq. (6) without importing the paper's quoted decimal value."""

    return float(brentq(lambda value: su2_constraint(value), 0.01, 0.1, xtol=1e-14))


def harmonic_gap_and_period(h0: float) -> tuple[float, float]:
    """Return Delta=(1-h)^2 and tau=2*pi/sqrt(2*Delta)."""

    couplings = ansatz_couplings(h0, 200)
    h_value = 2.0 * sum(value * ((-1) ** distance) for distance, value in couplings.items())
    delta = (1.0 - h_value) ** 2
    tau = 2.0 * math.pi / math.sqrt(2.0 * delta)
    return float(delta), float(tau)


@dataclass(frozen=True)
class HamiltonianFamily:
    """A shared-sparsity representation of the deformed PXP Hamiltonian."""

    n_sites: int
    periodic: bool
    basis: np.ndarray
    indices: Mapping[int, int]
    rows: np.ndarray
    cols: np.ndarray
    distance_modifiers: np.ndarray
    distances: tuple[int, ...]

    @classmethod
    def build(
        cls,
        n_sites: int,
        *,
        periodic: bool = True,
        max_range: int | None = None,
    ) -> "HamiltonianFamily":
        basis = np.asarray(constrained_basis(n_sites, periodic), dtype=np.int64)
        indices = {int(state): index for index, state in enumerate(basis)}
        if max_range is None:
            max_range = n_sites // 2 if periodic else n_sites - 1
        distances = tuple(range(2, max_range + 1))
        rows: list[int] = []
        cols: list[int] = []
        modifiers: list[list[float]] = []

        for col, raw_state in enumerate(basis):
            state = int(raw_state)
            for site in range(n_sites):
                left = (site - 1) % n_sites
                right = (site + 1) % n_sites
                if not periodic:
                    left_down = site == 0 or not ((state >> left) & 1)
                    right_down = site == n_sites - 1 or not ((state >> right) & 1)
                else:
                    left_down = not ((state >> left) & 1)
                    right_down = not ((state >> right) & 1)
                if not (left_down and right_down):
                    continue
                target = state ^ (1 << site)
                rows.append(indices[target])
                cols.append(col)
                distance_row: list[float] = []
                for distance in distances:
                    z_sum = 0
                    for direction in (-1, 1):
                        neighbor = site + direction * distance
                        if periodic:
                            z_sum += spin_z(state, neighbor % n_sites)
                        elif 0 <= neighbor < n_sites:
                            z_sum += spin_z(state, neighbor)
                    # H=H0-sum_d h_d X_i(Z_{i-d}+Z_{i+d}), main Eqs. (2)-(3).
                    distance_row.append(float(-z_sum))
                modifiers.append(distance_row)

        return cls(
            n_sites=n_sites,
            periodic=periodic,
            basis=basis,
            indices=indices,
            rows=np.asarray(rows, dtype=np.int64),
            cols=np.asarray(cols, dtype=np.int64),
            distance_modifiers=np.asarray(modifiers, dtype=np.float64),
            distances=distances,
        )

    def matrix(self, couplings: Mapping[int, float] | None = None) -> sparse.csr_matrix:
        coupling_vector = np.asarray(
            [float((couplings or {}).get(distance, 0.0)) for distance in self.distances],
            dtype=np.float64,
        )
        data = np.ones(len(self.rows), dtype=np.float64)
        if coupling_vector.size:
            data += self.distance_modifiers @ coupling_vector
        matrix = sparse.coo_matrix(
            (data, (self.rows, self.cols)),
            shape=(len(self.basis), len(self.basis)),
            dtype=np.float64,
        ).tocsr()
        matrix.sum_duplicates()
        return matrix

    def plus_matrix(
        self,
        couplings: Mapping[int, float] | None = None,
        *,
        origin: int | None = None,
    ) -> sparse.csr_matrix:
        """Return the FSA raising part, defined by distance from Z2."""

        if origin is None:
            origin = neel_state(self.n_sites)
        distances_from_origin = np.fromiter(
            (int(int(state) ^ origin).bit_count() for state in self.basis),
            dtype=np.int16,
            count=len(self.basis),
        )
        mask = distances_from_origin[self.rows] == distances_from_origin[self.cols] + 1
        coupling_vector = np.asarray(
            [float((couplings or {}).get(distance, 0.0)) for distance in self.distances],
            dtype=np.float64,
        )
        data = np.ones(len(self.rows), dtype=np.float64)
        if coupling_vector.size:
            data += self.distance_modifiers @ coupling_vector
        return sparse.coo_matrix(
            (data[mask], (self.rows[mask], self.cols[mask])),
            shape=(len(self.basis), len(self.basis)),
            dtype=np.float64,
        ).tocsr()


def fsa_basis(
    family: HamiltonianFamily,
    couplings: Mapping[int, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, sparse.csr_matrix]:
    """Construct |k> recursively and return columns, beta values, and H+."""

    plus = family.plus_matrix(couplings)
    vectors = np.zeros((len(family.basis), family.n_sites + 1), dtype=np.float64)
    vectors[family.indices[neel_state(family.n_sites)], 0] = 1.0
    beta = np.zeros(family.n_sites + 1, dtype=np.float64)
    for k in range(family.n_sites):
        candidate = plus @ vectors[:, k]
        beta[k + 1] = np.linalg.norm(candidate)
        if beta[k + 1] <= 1e-14:
            break
        vectors[:, k + 1] = candidate / beta[k + 1]
    return vectors, beta, plus


def fsa_diagnostics(
    family: HamiltonianFamily,
    couplings: Mapping[int, float] | None = None,
) -> dict[str, np.ndarray | float]:
    """Compute the two panels of main Figure 3 from independent FSA states."""

    vectors, beta, plus = fsa_basis(family, couplings)
    minus = plus.transpose().tocsr()
    hz_expectation = np.zeros(family.n_sites + 1)
    hz_sigma = np.zeros(family.n_sites + 1)
    for k in range(family.n_sites + 1):
        vector = vectors[:, k]
        hz_vector = plus @ (minus @ vector) - minus @ (plus @ vector)
        expectation = float(vector @ hz_vector)
        hz_expectation[k] = expectation
        hz_sigma[k] = float(np.linalg.norm(hz_vector - expectation * vector))
    k = np.arange(family.n_sites, dtype=np.float64)
    su2_shape = np.sqrt((family.n_sites - k) * (k + 1.0))
    scale = float(np.dot(beta[1:], su2_shape) / np.dot(su2_shape, su2_shape))
    spacing = np.diff(hz_expectation)
    return {
        "k": np.arange(family.n_sites + 1),
        "beta": beta,
        "su2_beta": np.concatenate(([0.0], scale * su2_shape)),
        "su2_scale": scale,
        "hz_expectation": hz_expectation,
        "hz_sigma": hz_sigma,
        "hz_spacing": spacing,
        "spacing_mean": float(np.mean(spacing)),
        "spacing_relative_std": float(np.std(spacing) / abs(np.mean(spacing))),
        "beta_relative_rms": float(
            np.linalg.norm(beta[1:] - scale * su2_shape) / np.linalg.norm(scale * su2_shape)
        ),
    }


def rotate_left(state: int, n_sites: int, shift: int = 1) -> int:
    shift %= n_sites
    mask = (1 << n_sites) - 1
    if not shift:
        return state & mask
    return ((state << shift) & mask) | (state >> (n_sites - shift))


def reflect_state(state: int, n_sites: int) -> int:
    """Bond-centred inversion i -> N-1-i."""

    reflected = 0
    for site in range(n_sites):
        if (state >> site) & 1:
            reflected |= 1 << (n_sites - 1 - site)
    return reflected


def translation_orbit(state: int, n_sites: int) -> tuple[int, ...]:
    orbit: list[int] = []
    current = state
    while current not in orbit:
        orbit.append(current)
        current = rotate_left(current, n_sites)
    canonical = min(orbit)
    start = orbit.index(canonical)
    return tuple(orbit[start:] + orbit[:start])


def symmetry_basis(
    family: HamiltonianFamily,
    *,
    momentum: int = 0,
    inversion: int = 1,
) -> sparse.csr_matrix:
    """Build a real translation/inversion symmetry basis for k=0 or pi.

    ``momentum`` is 0 or 1, denoting phase +1 or -1 under one-site
    translation. ``inversion`` is +1 or -1.
    """

    if not family.periodic:
        raise ValueError("translation sectors require periodic boundaries")
    if momentum not in (0, 1) or inversion not in (-1, 1):
        raise ValueError("supported sectors are momentum 0/pi and inversion +/-")
    phase_step = 1 if momentum == 0 else -1
    basis_set = set(int(state) for state in family.basis)
    seen: set[int] = set()
    orbits: dict[int, tuple[int, ...]] = {}
    for state in sorted(basis_set):
        if state in seen:
            continue
        orbit = translation_orbit(state, family.n_sites)
        seen.update(orbit)
        if phase_step == -1 and len(orbit) % 2:
            continue
        orbits[orbit[0]] = orbit

    reflection_map: dict[int, tuple[int, int]] = {}
    for canonical, orbit in orbits.items():
        reflected = reflect_state(canonical, family.n_sites)
        target_orbit = translation_orbit(reflected, family.n_sites)
        target = target_orbit[0]
        if target not in orbits:
            raise RuntimeError("reflection left the selected momentum sector")
        shift = target_orbit.index(reflected)
        reflection_map[canonical] = (target, phase_step**shift)

    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    completed: set[int] = set()
    column = 0

    def append_orbit(canonical: int, coefficient: float) -> None:
        orbit = orbits[canonical]
        normalization = math.sqrt(len(orbit))
        for shift, state in enumerate(orbit):
            rows.append(family.indices[state])
            cols.append(column)
            values.append(coefficient * (phase_step**shift) / normalization)

    for canonical in sorted(orbits):
        if canonical in completed:
            continue
        partner, reflection_phase = reflection_map[canonical]
        if partner == canonical:
            completed.add(canonical)
            if reflection_phase != inversion:
                continue
            append_orbit(canonical, 1.0)
        else:
            completed.update((canonical, partner))
            append_orbit(canonical, 1.0 / math.sqrt(2.0))
            append_orbit(partner, inversion * reflection_phase / math.sqrt(2.0))
        column += 1

    return sparse.coo_matrix(
        (values, (rows, cols)),
        shape=(len(family.basis), column),
        dtype=np.float64,
    ).tocsr()


def sector_hamiltonian(
    family: HamiltonianFamily,
    couplings: Mapping[int, float] | None = None,
    *,
    momentum: int = 0,
    inversion: int = 1,
) -> tuple[np.ndarray, sparse.csr_matrix]:
    transform = symmetry_basis(family, momentum=momentum, inversion=inversion)
    projected = transform.transpose() @ family.matrix(couplings) @ transform
    return np.asarray(projected.toarray()), transform


def sector_hamiltonian_sparse(
    family: HamiltonianFamily,
    couplings: Mapping[int, float] | None = None,
    *,
    momentum: int = 0,
    inversion: int = 1,
) -> tuple[sparse.csr_matrix, sparse.csr_matrix]:
    """Project into a symmetry sector without materializing a dense block.

    Paper-size ``N=30`` and ``N=32`` sectors are too large for the reduced-run
    dense path.  Keeping the projected operator sparse makes shift-invert
    spectrum slicing and targeted interior eigensolves possible on a
    high-memory CPU node.
    """

    transform = symmetry_basis(family, momentum=momentum, inversion=inversion)
    projected = transform.transpose() @ family.matrix(couplings) @ transform
    projected = projected.tocsr()
    projected.sum_duplicates()
    projected.eliminate_zeros()
    return projected, transform


def sector_neel_vector(transform: sparse.csr_matrix, family: HamiltonianFamily) -> np.ndarray:
    """Normalize the symmetry projection of one Neel product state."""

    row = family.indices[neel_state(family.n_sites)]
    projected = np.asarray(transform.getrow(row).toarray()).ravel()
    norm = np.linalg.norm(projected)
    if norm <= 1e-14:
        raise ValueError("the chosen Neel state has no weight in this sector")
    return projected / norm


def level_statistics(eigenvalues: Sequence[float]) -> tuple[np.ndarray, np.ndarray, float]:
    """Return unfolded spacings, adjacent ratios, and mean r.

    Exact zero modes and the outer five percent of the spectrum are removed,
    matching the paper's instruction to avoid symmetry-protected degeneracies
    while retaining the bulk spectrum.
    """

    energies = np.sort(np.asarray(eigenvalues, dtype=np.float64))
    energies = energies[np.abs(energies) > 1e-9]
    trim = max(1, int(0.05 * len(energies)))
    if len(energies) > 2 * trim + 4:
        energies = energies[trim:-trim]
    spacings = np.diff(energies)
    spacings = spacings[spacings > 1e-10]
    unfolded = spacings / np.mean(spacings)
    ratios = np.minimum(spacings[:-1], spacings[1:]) / np.maximum(spacings[:-1], spacings[1:])
    return unfolded, ratios, float(np.mean(ratios))


@dataclass(frozen=True)
class Bipartition:
    row_index: np.ndarray
    col_index: np.ndarray
    n_rows: int
    n_cols: int

    @classmethod
    def from_basis(cls, basis: Sequence[int], n_sites: int) -> "Bipartition":
        cut = n_sites // 2
        lower_mask = (1 << cut) - 1
        lower = np.asarray([int(state) & lower_mask for state in basis], dtype=np.int64)
        upper = np.asarray([int(state) >> cut for state in basis], dtype=np.int64)
        lower_values = {int(value): index for index, value in enumerate(sorted(set(lower.tolist())))}
        upper_values = {int(value): index for index, value in enumerate(sorted(set(upper.tolist())))}
        return cls(
            row_index=np.asarray([lower_values[int(value)] for value in lower], dtype=np.int64),
            col_index=np.asarray([upper_values[int(value)] for value in upper], dtype=np.int64),
            n_rows=len(lower_values),
            n_cols=len(upper_values),
        )

    def schmidt_probabilities(self, state_vector: np.ndarray) -> np.ndarray:
        coefficient = np.zeros((self.n_rows, self.n_cols), dtype=np.complex128)
        coefficient[self.row_index, self.col_index] = state_vector
        singular = np.linalg.svd(coefficient, compute_uv=False)
        probabilities = np.maximum(np.real(singular * singular.conjugate()), 0.0)
        probabilities /= probabilities.sum()
        return probabilities

    def entropy(self, state_vector: np.ndarray) -> float:
        probabilities = self.schmidt_probabilities(state_vector)
        positive = probabilities[probabilities > 1e-15]
        return float(-np.sum(positive * np.log(positive)))


def low_energy_schmidt_scan(
    n_sites: int,
    ranges: Iterable[int],
    h0: float,
) -> dict[str, np.ndarray]:
    """Reduced-scale version of Supplementary Figure S1."""

    family = HamiltonianFamily.build(n_sites, periodic=False, max_range=max(ranges))
    partition = Bipartition.from_basis(family.basis, n_sites)
    range_values: list[int] = []
    ground_singular: list[np.ndarray] = []
    first_singular: list[np.ndarray] = []
    gaps: list[float] = []
    residuals: list[float] = []
    for max_range in ranges:
        couplings = {} if max_range <= 1 else ansatz_couplings(h0, max_range)
        matrix = family.matrix(couplings)
        values, vectors = eigsh(matrix, k=2, which="SA", tol=1e-11, maxiter=5000)
        order = np.argsort(values)
        values = values[order]
        vectors = vectors[:, order]
        range_values.append(max_range)
        ground_singular.append(np.sqrt(partition.schmidt_probabilities(vectors[:, 0]))[:12])
        first_singular.append(np.sqrt(partition.schmidt_probabilities(vectors[:, 1]))[:12])
        gaps.append(float(values[1] - values[0]))
        residuals.append(
            float(
                max(
                    np.linalg.norm(matrix @ vectors[:, index] - values[index] * vectors[:, index])
                    for index in (0, 1)
                )
            )
        )
    return {
        "ranges": np.asarray(range_values),
        "ground_singular": np.asarray(ground_singular),
        "first_singular": np.asarray(first_singular),
        "gaps": np.asarray(gaps),
        "eigensolver_residual": np.asarray(residuals),
    }


def pauli_string_action(state: int, operators: Mapping[int, str]) -> tuple[int, complex]:
    """Apply a Pauli string in the bit convention documented above."""

    target = state
    phase: complex = 1.0 + 0.0j
    for site, operator in operators.items():
        up = bool((state >> site) & 1)
        if operator == "x":
            target ^= 1 << site
        elif operator == "y":
            target ^= 1 << site
            phase *= 1j if up else -1j
        elif operator == "z":
            phase *= 1.0 if up else -1.0
        else:
            raise ValueError(f"unknown Pauli operator: {operator}")
    return target, phase


def toy_hamiltonian_sparse(
    n_sites: int,
    seed: int,
    omega: float = 1.0,
) -> tuple[sparse.csr_matrix, np.ndarray]:
    """Construct main Eq. (7) sparsely for a disclosed Gaussian realization.

    The paper does not disclose its random realization.  The returned coupling
    tensor therefore belongs to the explicitly supplied seed and is part of the
    generated evidence, never an author-provided numerical input.
    """

    dimension = 1 << n_sites
    rng = np.random.default_rng(seed)
    couplings = rng.normal(0.0, 0.25, size=(n_sites, 3, 3))
    paulis = ("x", "y", "z")
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []

    def add_string(coefficient: complex, operators: Mapping[int, str]) -> None:
        for state in range(dimension):
            target, phase = pauli_string_action(state, operators)
            rows.append(target)
            cols.append(state)
            data.append(coefficient * phase)

    for site in range(n_sites):
        add_string(omega / 2.0, {site: "x"})
    for site in range(n_sites):
        outer_left = (site - 1) % n_sites
        pair_left = site
        pair_right = (site + 1) % n_sites
        outer_right = (site + 2) % n_sites
        for mu_index, mu in enumerate(paulis):
            for nu_index, nu in enumerate(paulis):
                coefficient = couplings[site, mu_index, nu_index] / 4.0
                add_string(coefficient, {outer_left: mu, outer_right: nu})
                for pair_pauli in paulis:
                    add_string(
                        -coefficient,
                        {
                            outer_left: mu,
                            pair_left: pair_pauli,
                            pair_right: pair_pauli,
                            outer_right: nu,
                        },
                    )
    matrix = sparse.coo_matrix((data, (rows, cols)), shape=(dimension, dimension)).tocsr()
    matrix.sum_duplicates()
    return matrix, couplings


def toy_hamiltonian(n_sites: int, seed: int, omega: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Dense compatibility wrapper used by the reduced-scale eigensolver."""

    matrix, couplings = toy_hamiltonian_sparse(n_sites, seed, omega)
    return np.asarray(matrix.toarray()), couplings


def toy_diagnostics(n_sites: int, seed: int, omega: float = 1.0) -> dict[str, np.ndarray | float]:
    matrix, couplings = toy_hamiltonian(n_sites, seed, omega)
    hermiticity_error = float(np.max(np.abs(matrix - matrix.conjugate().T)))
    energies, eigenvectors = eigh(matrix, overwrite_a=True, check_finite=False)
    polarized_index = (1 << n_sites) - 1
    overlaps = np.abs(eigenvectors[polarized_index, :]) ** 2
    times = np.linspace(0.0, 4.0, 401)
    amplitude = np.exp(-2j * math.pi * np.outer(times, energies)) @ overlaps
    fidelity = np.abs(amplitude) ** 2
    partition = Bipartition.from_basis(tuple(range(1 << n_sites)), n_sites)
    entropy = np.asarray([partition.entropy(eigenvectors[:, index]) for index in range(len(energies))])
    return {
        "energies": energies,
        "overlaps": overlaps,
        "times": times,
        "fidelity": fidelity,
        "entropy": entropy,
        "couplings": couplings,
        "hermiticity_error": hermiticity_error,
    }


def dense_lowest_states(matrix: sparse.spmatrix, k: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """Small helper used in tests; keeps solver choice explicit."""

    dense = np.asarray(matrix.toarray())
    values, vectors = eigh(dense, subset_by_index=(0, k - 1))
    return values, vectors
