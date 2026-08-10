"""Formula-derived PXP, MPS, SMA/MMA, and FSA implementation.

This module is intentionally self-contained.  It does not read the paper's
figure assets, digitized curves, author code, or author numerical arrays.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product

import numpy as np
import scipy.linalg
import scipy.sparse as sp


@dataclass(frozen=True)
class PXPBasis:
    """Rydberg-blockaded computational basis."""

    length: int
    periodic: bool
    states: np.ndarray
    index: dict[int, int]


@dataclass(frozen=True)
class SectorSpectrum:
    """Exact spectrum and full-to-sector isometry for a one-dimensional irrep."""

    energies: np.ndarray
    vectors: np.ndarray
    projector: sp.csc_matrix
    k_sign: int | None
    parity: int


def bit(state: int, site: int) -> int:
    return (state >> site) & 1


def build_basis(length: int, periodic: bool) -> PXPBasis:
    """Enumerate legal strings without scanning the full 2**L space."""

    if length < 2:
        raise ValueError("length must be at least two")
    states = [0]
    for site in range(length):
        next_states: list[int] = []
        for state in states:
            next_states.append(state)
            if site == 0 or not bit(state, site - 1):
                next_states.append(state | (1 << site))
        states = next_states
    if periodic:
        states = [
            state for state in states if not (bit(state, 0) and bit(state, length - 1))
        ]
    array = np.asarray(sorted(states), dtype=np.int64)
    return PXPBasis(
        length=length,
        periodic=periodic,
        states=array,
        index={int(state): index for index, state in enumerate(array)},
    )


def valid_flip(state: int, length: int, site: int, periodic: bool) -> bool:
    left_ok = site == 0 and not periodic
    right_ok = site == length - 1 and not periodic
    if not left_ok:
        left_ok = bit(state, (site - 1) % length) == 0
    if not right_ok:
        right_ok = bit(state, (site + 1) % length) == 0
    return left_ok and right_ok


def build_hamiltonian(basis: PXPBasis) -> sp.csr_matrix:
    """Construct H=sum_j P_(j-1) X_j P_(j+1) in the constrained basis."""

    rows: list[int] = []
    cols: list[int] = []
    for col, state_value in enumerate(basis.states):
        state = int(state_value)
        for site in range(basis.length):
            if not valid_flip(state, basis.length, site, basis.periodic):
                continue
            target = state ^ (1 << site)
            row = basis.index.get(target)
            if row is not None:
                rows.append(row)
                cols.append(col)
    data = np.ones(len(rows), dtype=np.float64)
    dimension = len(basis.states)
    matrix = sp.csr_matrix(
        (data, (rows, cols)), shape=(dimension, dimension), dtype=np.float64
    )
    matrix.sum_duplicates()
    return matrix


def translate_state(state: int, length: int) -> int:
    mask = (1 << length) - 1
    return ((state << 1) & mask) | (state >> (length - 1))


def invert_state(state: int, length: int) -> int:
    result = 0
    for site in range(length):
        result |= bit(state, site) << (length - 1 - site)
    return result


def _dihedral_orbit(state: int, length: int) -> set[int]:
    orbit: set[int] = set()
    translated = state
    for _ in range(length):
        orbit.add(translated)
        orbit.add(invert_state(translated, length))
        translated = translate_state(translated, length)
    return orbit


def build_dihedral_projector(
    basis: PXPBasis, *, k_sign: int, parity: int
) -> sp.csc_matrix:
    """Build a normalized projector for k=0/pi and inversion +/- sectors.

    ``k_sign`` is +1 for k=0 and -1 for k=pi.  The construction applies the
    one-dimensional dihedral-group character directly to each disjoint orbit,
    so short-period or reflection-fixed orbits are handled without special
    cases: incompatible orbits cancel exactly and are omitted.
    """

    if not basis.periodic:
        raise ValueError("dihedral projector requires periodic boundary conditions")
    if k_sign not in (-1, 1) or parity not in (-1, 1):
        raise ValueError("k_sign and parity must be +/-1")

    seen: set[int] = set()
    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    column = 0
    for state_value in basis.states:
        state = int(state_value)
        if state in seen:
            continue
        orbit = _dihedral_orbit(state, basis.length)
        seen.update(orbit)
        representative = min(orbit)
        coefficients: defaultdict[int, float] = defaultdict(float)
        translated = representative
        phase = 1
        for _ in range(basis.length):
            coefficients[translated] += phase
            coefficients[invert_state(translated, basis.length)] += parity * phase
            translated = translate_state(translated, basis.length)
            phase *= k_sign
        norm = float(np.sqrt(sum(value * value for value in coefficients.values())))
        if norm < 1e-12:
            continue
        for member, value in coefficients.items():
            if abs(value) < 1e-14:
                continue
            rows.append(basis.index[member])
            cols.append(column)
            values.append(value / norm)
        column += 1
    return sp.csc_matrix(
        (values, (rows, cols)), shape=(len(basis.states), column), dtype=np.float64
    )


def build_inversion_projector(basis: PXPBasis, *, parity: int) -> sp.csc_matrix:
    """Build the open-chain inversion +/- isometry."""

    if basis.periodic:
        raise ValueError("open-chain inversion projector requires OBC")
    if parity not in (-1, 1):
        raise ValueError("parity must be +/-1")
    seen: set[int] = set()
    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    column = 0
    for state_value in basis.states:
        state = int(state_value)
        if state in seen:
            continue
        reflected = invert_state(state, basis.length)
        seen.update((state, reflected))
        if reflected == state:
            if parity == 1:
                rows.append(basis.index[state])
                cols.append(column)
                values.append(1.0)
                column += 1
            continue
        norm = np.sqrt(2.0)
        rows.extend((basis.index[state], basis.index[reflected]))
        cols.extend((column, column))
        values.extend((1.0 / norm, parity / norm))
        column += 1
    return sp.csc_matrix(
        (values, (rows, cols)), shape=(len(basis.states), column), dtype=np.float64
    )


def sector_spectrum(
    basis: PXPBasis,
    hamiltonian: sp.csr_matrix,
    *,
    parity: int,
    k_sign: int | None = None,
) -> SectorSpectrum:
    """Exactly diagonalize one symmetry block."""

    if basis.periodic:
        if k_sign is None:
            raise ValueError("periodic sector requires k_sign")
        projector = build_dihedral_projector(basis, k_sign=k_sign, parity=parity)
    else:
        if k_sign is not None:
            raise ValueError("open sector does not have momentum")
        projector = build_inversion_projector(basis, parity=parity)
    sector = (projector.T @ hamiltonian @ projector).toarray()
    sector = 0.5 * (sector + sector.T)
    energies, vectors = scipy.linalg.eigh(sector, overwrite_a=True, check_finite=False)
    return SectorSpectrum(
        energies=energies,
        vectors=vectors,
        projector=projector,
        k_sign=k_sign,
        parity=parity,
    )


def pattern_state(length: int, name: str) -> int:
    if name == "z2":
        return sum(1 << site for site in range(0, length, 2))
    if name == "z2_shift":
        return sum(1 << site for site in range(1, length, 2))
    if name == "vacuum":
        return 0
    raise ValueError(f"unknown pattern state: {name}")


def computational_vector(basis: PXPBasis, state: int) -> np.ndarray:
    vector = np.zeros(len(basis.states), dtype=np.float64)
    vector[basis.index[state]] = 1.0
    return vector


def z2_momentum_vector(basis: PXPBasis, k_sign: int) -> np.ndarray:
    vector = computational_vector(basis, pattern_state(basis.length, "z2"))
    shifted = computational_vector(basis, pattern_state(basis.length, "z2_shift"))
    return (vector + k_sign * shifted) / np.sqrt(2.0)


def mps_matrices() -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """Return the B and C matrices printed in main-text Eqs. (2)-(3)."""

    root_two = np.sqrt(2.0)
    b = {
        0: np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        1: root_two * np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 1.0]]),
    }
    c = {
        0: np.asarray([[0.0, -1.0], [1.0, 0.0], [0.0, 0.0]]),
        1: root_two * np.asarray([[1.0, 0.0], [0.0, 0.0], [-1.0, 0.0]]),
    }
    return b, c


def gamma_state(basis: PXPBasis, alpha: int, beta: int) -> np.ndarray:
    """Construct the exact OBC |Gamma_(alpha,beta)> from Eq. (7)."""

    if basis.periodic:
        raise ValueError("Gamma states require OBC")
    if alpha not in (1, 2) or beta not in (1, 2):
        raise ValueError("alpha and beta must be 1 or 2")
    b_matrices, c_matrices = mps_matrices()
    boundaries = {
        1: np.asarray([1.0, 1.0]),
        2: np.asarray([1.0, -1.0]),
    }
    vector = np.empty(len(basis.states), dtype=np.float64)
    for index, state_value in enumerate(basis.states):
        state = int(state_value)
        matrix = np.eye(2)
        for site in range(basis.length):
            local = bit(state, site)
            matrix = matrix @ (
                b_matrices[local] if site % 2 == 0 else c_matrices[local]
            )
        vector[index] = boundaries[alpha] @ matrix @ boundaries[beta]
    norm = float(np.linalg.norm(vector))
    if norm < 1e-14:
        raise RuntimeError("constructed zero Gamma state")
    return vector / norm


def local_x_profile(basis: PXPBasis, state_vector: np.ndarray) -> np.ndarray:
    """Numerically evaluate each constrained local X_j expectation value."""

    result = np.zeros(basis.length, dtype=np.float64)
    for col, state_value in enumerate(basis.states):
        state = int(state_value)
        amplitude = state_vector[col]
        for site in range(basis.length):
            if not valid_flip(state, basis.length, site, basis.periodic):
                continue
            target = state ^ (1 << site)
            row = basis.index.get(target)
            if row is not None:
                result[site] += amplitude * state_vector[row]
    return result


def local_x_profile_formula(length: int, alpha: int, beta: int) -> np.ndarray:
    """Supplement Eq. for the exact OBC energy-density profile."""

    if length % 2:
        raise ValueError("the paper assumes even length")
    blocks = length // 2
    denominator = 1.0 + ((-1) ** (blocks + alpha + beta)) * 3.0 ** (-blocks)
    result = np.empty(length, dtype=np.float64)
    for block_zero in range(blocks):
        block = block_zero + 1
        value = (
            np.sqrt(2.0)
            / denominator
            * (
                ((-1) ** alpha) * ((-1) ** block) * 3.0 ** (-block)
                + ((-1) ** beta)
                * ((-1) ** (blocks - block))
                * 3.0 ** (-blocks + block - 1)
            )
        )
        result[2 * block_zero : 2 * block_zero + 2] = value
    return result


def _block2_matrices(
    family: str,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray]]:
    b, c = mps_matrices()
    base = {pair: b[pair[0]] @ c[pair[1]] for pair in product((0, 1), repeat=2)}
    if family == "xi":
        mu1, mu2 = -1.0876, -0.6344
        excitation = {
            (0, 0): np.eye(2),
            (0, 1): np.asarray([[mu1, 0.0], [mu2, 0.0]]),
            (1, 0): np.asarray([[0.0, 0.0], [-mu2, mu1]]),
            (1, 1): np.zeros((2, 2)),
        }
    elif family == "xi_tilde":
        mu = 0.89285
        root_two = np.sqrt(2.0)
        excitation = {
            (0, 0): root_two * np.asarray([[1.0, -mu], [mu, -1.0]]),
            (0, 1): np.asarray([[-mu, 0.0], [-1.0, 0.0]]),
            (1, 0): np.asarray([[0.0, 0.0], [-1.0, mu]]),
            (1, 1): np.zeros((2, 2)),
        }
    else:
        raise ValueError(f"unknown block-dimension-2 family: {family}")
    return base, excitation


def _block3_matrices(
    family: str,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray]]:
    b, c = mps_matrices()
    base = {pair: c[pair[0]] @ b[pair[1]] for pair in product((0, 1), repeat=2)}
    root_two = np.sqrt(2.0)
    if family == "upsilon":
        nu1, nu2, nu3, nu4 = 0.507183, 0.60202, 0.625366, 0.264115
        nu5, nu6, nu7 = -0.00128607, 0.0228075, 0.42342
        excitation = {
            (0, 0): np.asarray(
                [
                    [1 + root_two * nu7, 0, 2 * root_two * nu6],
                    [0, 1 - root_two * nu7, 2 * root_two * nu5],
                    [-2 * root_two * nu6, 2 * root_two * nu5, nu1],
                ]
            ),
            (0, 1): np.asarray(
                [
                    [nu2, 2 * nu6, nu2],
                    [nu6 + nu7, nu3, nu6 + nu7],
                    [nu2 - nu5, nu4, nu2 - nu5],
                ]
            ),
            (1, 0): np.asarray(
                [
                    [nu2, nu6 + nu7, -nu2 - nu5],
                    [2 * nu6, nu3, -nu4],
                    [-nu2, -nu6 - nu7, nu2 + nu5],
                ]
            ),
            (1, 1): np.zeros((3, 3)),
        }
    elif family == "upsilon_tilde":
        nu1, nu2, nu3, nu4 = 2.59334, 1.48065, 0.0615383, -0.992914
        excitation = {
            (0, 0): np.asarray(
                [
                    [0, 2 * root_two, 2 * root_two * nu4],
                    [-2 * root_two, 0, 2 * root_two * nu3],
                    [2 * root_two * nu4, -2 * root_two * nu3, 0],
                ]
            ),
            (0, 1): np.asarray(
                [
                    [-1, -2 * nu4, -1],
                    [nu4, nu1, nu4],
                    [-1 + nu3, nu2, -1 + nu3],
                ]
            ),
            (1, 0): np.asarray(
                [
                    [1, -nu4, -1 - nu3],
                    [2 * nu4, -nu1, nu2],
                    [-1, nu4, 1 + nu3],
                ]
            ),
            (1, 1): np.zeros((3, 3)),
        }
    else:
        raise ValueError(f"unknown block-dimension-3 family: {family}")
    return base, excitation


def _batch_polynomial_coefficients(
    basis: PXPBasis,
    *,
    family: str,
    maximum_particles: int,
    batch_size: int,
) -> np.ndarray:
    if not basis.periodic or basis.length % 2:
        raise ValueError("trial families require an even periodic chain")
    if family in ("xi", "xi_tilde"):
        base, excitation = _block2_matrices(family)
        dimension = 2
        offset = 0
    elif family in ("upsilon", "upsilon_tilde"):
        base, excitation = _block3_matrices(family)
        dimension = 3
        offset = 1
    else:
        raise ValueError(f"unknown trial family: {family}")

    blocks = basis.length // 2
    maximum_particles = min(maximum_particles, blocks)
    coefficients = np.empty(
        (maximum_particles + 1, len(basis.states)), dtype=np.float64
    )
    for start in range(0, len(basis.states), batch_size):
        stop = min(start + batch_size, len(basis.states))
        states = basis.states[start:stop]
        polynomial = np.zeros(
            (len(states), maximum_particles + 1, dimension, dimension),
            dtype=np.float64,
        )
        polynomial[:, 0] = np.eye(dimension)
        for block_index in range(blocks):
            if offset == 0:
                first_site = 2 * block_index
                second_site = first_site + 1
            else:
                first_site = 2 * block_index + 1
                second_site = (first_site + 1) % basis.length
            first = ((states >> first_site) & 1).astype(np.int8)
            second = ((states >> second_site) & 1).astype(np.int8)
            base_batch = np.stack(
                [base[(int(a), int(b))] for a, b in zip(first, second)]
            )
            excitation_batch = np.stack(
                [excitation[(int(a), int(b))] for a, b in zip(first, second)]
            )
            updated = np.einsum("bqij,bjk->bqik", polynomial, base_batch, optimize=True)
            updated[:, 1:] += np.einsum(
                "bqij,bjk->bqik",
                polynomial[:, :-1],
                excitation_batch,
                optimize=True,
            )
            polynomial = updated
        coefficients[:, start:stop] = np.trace(polynomial, axis1=-2, axis2=-1).T
    return coefficients


def _translate_vector(basis: PXPBasis, vector: np.ndarray) -> np.ndarray:
    result = np.empty_like(vector)
    for source_index, state_value in enumerate(basis.states):
        target = translate_state(int(state_value), basis.length)
        result[basis.index[target]] = vector[source_index]
    return result


def build_trial_family(
    basis: PXPBasis,
    *,
    family: str,
    maximum_particles: int,
    batch_size: int = 4096,
) -> dict[int, np.ndarray]:
    """Construct normalized Xi/Upsilon SMA and MMA states from printed matrices."""

    coefficients = _batch_polynomial_coefficients(
        basis,
        family=family,
        maximum_particles=maximum_particles,
        batch_size=batch_size,
    )
    blocks = basis.length // 2
    result: dict[int, np.ndarray] = {}
    for particles in range(maximum_particles + 1):
        raw = coefficients[particles]
        if family in ("xi_tilde", "upsilon_tilde"):
            if particles > 1:
                raise ValueError(
                    "the paper defines tilde families only for one particle"
                )
            sign = (-1) ** blocks
        else:
            sign = (-1) ** (blocks + particles)
        vector = raw + sign * _translate_vector(basis, raw)
        norm = float(np.linalg.norm(vector))
        if norm > 1e-12:
            result[particles] = vector / norm
    return result


def build_hplus(basis: PXPBasis, reference_state: int) -> sp.csr_matrix:
    """FSA forward operator: retain flips increasing Z2 Hamming distance."""

    rows: list[int] = []
    cols: list[int] = []
    for col, state_value in enumerate(basis.states):
        state = int(state_value)
        distance = (state ^ reference_state).bit_count()
        for site in range(basis.length):
            if not valid_flip(state, basis.length, site, basis.periodic):
                continue
            target = state ^ (1 << site)
            if (target ^ reference_state).bit_count() != distance + 1:
                continue
            row = basis.index.get(target)
            if row is not None:
                rows.append(row)
                cols.append(col)
    data = np.ones(len(rows), dtype=np.float64)
    dimension = len(basis.states)
    return sp.csr_matrix(
        (data, (rows, cols)), shape=(dimension, dimension), dtype=np.float64
    )


def fsa_states(
    basis: PXPBasis, hamiltonian: sp.csr_matrix
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return FSA energies, full-basis states, and backward-leakage errors."""

    reference = pattern_state(basis.length, "z2")
    hplus = build_hplus(basis, reference)
    hminus = hplus.T.tocsr()
    vectors = [computational_vector(basis, reference)]
    betas: list[float] = []
    errors: list[float] = []
    for _ in range(basis.length):
        proposal = np.asarray(hplus @ vectors[-1]).reshape(-1)
        beta = float(np.linalg.norm(proposal))
        if beta < 1e-13:
            break
        following = proposal / beta
        backward = np.asarray(hminus @ following).reshape(-1)
        errors.append(
            float(np.linalg.norm(backward - beta * vectors[-1]) / max(beta, 1e-15))
        )
        betas.append(beta)
        vectors.append(following)
    fsa_basis = np.stack(vectors)
    projected = np.asarray(fsa_basis @ (hamiltonian @ fsa_basis.T))
    projected = 0.5 * (projected + projected.T)
    energies, coefficients = scipy.linalg.eigh(projected)
    full_states = coefficients.T @ fsa_basis
    return energies, full_states, np.asarray(errors)


def entanglement_entropy(
    state_vector: np.ndarray, basis: PXPBasis, cut: int | None = None
) -> float:
    """Half-chain von Neumann entropy using a compressed allowed-state matrix."""

    cut = basis.length // 2 if cut is None else cut
    if not (0 < cut < basis.length):
        raise ValueError("cut must lie inside the chain")
    mask = (1 << cut) - 1
    left_states = np.asarray([int(state) & mask for state in basis.states])
    right_states = np.asarray([int(state) >> cut for state in basis.states])
    left_values, left_inverse = np.unique(left_states, return_inverse=True)
    right_values, right_inverse = np.unique(right_states, return_inverse=True)
    amplitude = np.zeros((len(left_values), len(right_values)), dtype=np.float64)
    amplitude[left_inverse, right_inverse] = state_vector
    singular_values = scipy.linalg.svdvals(amplitude, overwrite_a=True)
    probabilities = singular_values**2
    probabilities = probabilities[probabilities > 1e-14]
    probabilities /= probabilities.sum()
    return float(-np.sum(probabilities * np.log(probabilities)))


def overlap_distribution(
    full_state: np.ndarray, spectrum: SectorSpectrum
) -> np.ndarray:
    coordinates = np.asarray(spectrum.projector.T @ full_state).reshape(-1)
    return np.abs(coordinates @ spectrum.vectors) ** 2


def reconstruct_eigenstate(spectrum: SectorSpectrum, index: int) -> np.ndarray:
    return np.asarray(spectrum.projector @ spectrum.vectors[:, index]).reshape(-1)


def projected_variational_diagonalization(
    trials: list[np.ndarray], hamiltonian: sp.csr_matrix
) -> tuple[np.ndarray, np.ndarray]:
    """Solve H_eff v=lambda B v and return energies/full normalized states."""

    trial_matrix = np.stack(trials, axis=1)
    overlap = trial_matrix.T @ trial_matrix
    effective = trial_matrix.T @ (hamiltonian @ trial_matrix)
    eigenvalues, coefficients = scipy.linalg.eigh(effective, overlap)
    states = trial_matrix @ coefficients
    states /= np.linalg.norm(states, axis=0, keepdims=True)
    return eigenvalues, states.T
