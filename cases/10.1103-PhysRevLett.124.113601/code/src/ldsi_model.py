"""Numerical core for localization-driven superradiant instability.

All public functions operate in units of the nearest-neighbor hopping ``J``.
The module contains no plotting or paper-reference data.  It generates only
independent AA/GAA eigenstates and mean-field observables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.linalg import eigh, eigh_tridiagonal


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]
GOLDEN_GAMMA = (np.sqrt(5.0) - 1.0) / 2.0


def _sites(length: int) -> FloatArray:
    if length < 2:
        raise ValueError("length must be at least two")
    return np.arange(length, dtype=float)


def aa_diagonals(
    length: int,
    chi: float,
    *,
    gamma: float = GOLDEN_GAMMA,
    hopping: float = 1.0,
    phase: float = 0.0,
    harmonic_trap: float = 0.0,
) -> tuple[FloatArray, FloatArray]:
    """Return the diagonal and off-diagonal of the open AA chain."""

    sites = _sites(length)
    diagonal = chi * np.cos(2.0 * np.pi * gamma * sites + phase)
    if harmonic_trap:
        centered = sites - 0.5 * (length - 1)
        diagonal = diagonal + harmonic_trap * centered**2
    off_diagonal = np.full(length - 1, -hopping, dtype=float)
    return diagonal, off_diagonal


def aa_hamiltonian(
    length: int,
    chi: float,
    *,
    gamma: float = GOLDEN_GAMMA,
    hopping: float = 1.0,
    phase: float = 0.0,
    harmonic_trap: float = 0.0,
    periodic: bool = False,
) -> FloatArray:
    """Construct the dense AA Hamiltonian for the selected boundary."""

    diagonal, off_diagonal = aa_diagonals(
        length,
        chi,
        gamma=gamma,
        hopping=hopping,
        phase=phase,
        harmonic_trap=harmonic_trap,
    )
    matrix = (
        np.diag(diagonal)
        + np.diag(off_diagonal, k=1)
        + np.diag(off_diagonal, k=-1)
    )
    if periodic:
        matrix[0, -1] = -hopping
        matrix[-1, 0] = -hopping
    return matrix


def aa_eigensystem(
    length: int,
    chi: float,
    *,
    gamma: float = GOLDEN_GAMMA,
    hopping: float = 1.0,
    phase: float = 0.0,
    harmonic_trap: float = 0.0,
    periodic: bool = False,
) -> tuple[FloatArray, FloatArray]:
    """Diagonalize the AA chain using its tridiagonal structure."""

    if periodic:
        return eigh(
            aa_hamiltonian(
                length,
                chi,
                gamma=gamma,
                hopping=hopping,
                phase=phase,
                harmonic_trap=harmonic_trap,
                periodic=True,
            ),
            check_finite=False,
        )
    diagonal, off_diagonal = aa_diagonals(
        length,
        chi,
        gamma=gamma,
        hopping=hopping,
        phase=phase,
        harmonic_trap=harmonic_trap,
    )
    return eigh_tridiagonal(diagonal, off_diagonal, check_finite=False)


def gaa_hamiltonian(
    length: int,
    chi: float,
    *,
    gamma: float,
    hopping: float = 1.0,
    phase: float = 0.0,
    next_nearest: float = 0.072,
    hopping_correction: float = -0.23,
    disorder_correction: float = -0.016,
    periodic: bool = False,
) -> FloatArray:
    """Construct the GAA Hamiltonian in published Eq. (2)."""

    sites = _sites(length)
    matrix = aa_hamiltonian(
        length,
        chi,
        gamma=gamma,
        hopping=hopping,
        phase=phase,
        periodic=periodic,
    )
    matrix[np.diag_indices(length)] += disorder_correction * np.cos(
        4.0 * np.pi * gamma * sites + 2.0 * phase
    )
    bonds = np.arange(length - 1, dtype=float)
    corrected_hopping = hopping_correction * np.cos(
        2.0 * np.pi * gamma * (bonds + 0.5) + phase
    )
    matrix += np.diag(corrected_hopping, k=1)
    matrix += np.diag(corrected_hopping, k=-1)
    nnn = np.full(length - 2, next_nearest, dtype=float)
    matrix += np.diag(nnn, k=2)
    matrix += np.diag(nnn, k=-2)
    if periodic:
        closing_hop = hopping_correction * np.cos(
            2.0 * np.pi * gamma * (length - 0.5) + phase
        )
        matrix[-1, 0] += closing_hop
        matrix[0, -1] += closing_hop
        for source in (length - 2, length - 1):
            target = (source + 2) % length
            matrix[source, target] += next_nearest
            matrix[target, source] += next_nearest
    return matrix


def gaa_eigensystem(
    length: int,
    chi: float,
    *,
    gamma: float,
    hopping: float = 1.0,
    phase: float = 0.0,
    next_nearest: float = 0.072,
    hopping_correction: float = -0.23,
    disorder_correction: float = -0.016,
    periodic: bool = False,
) -> tuple[FloatArray, FloatArray]:
    """Diagonalize the dense pentadiagonal GAA Hamiltonian."""

    matrix = gaa_hamiltonian(
        length,
        chi,
        gamma=gamma,
        hopping=hopping,
        phase=phase,
        next_nearest=next_nearest,
        hopping_correction=hopping_correction,
        disorder_correction=disorder_correction,
        periodic=periodic,
    )
    return eigh(matrix, check_finite=False)


def inverse_participation_ratio(eigenvectors: ArrayLike) -> FloatArray:
    """Return IPR for column-wise normalized eigenvectors."""

    vectors = np.asarray(eigenvectors)
    return np.sum(np.abs(vectors) ** 4, axis=0).real


def cavity_profile(length: int, gamma_c: float, phase_c: float = 0.0) -> FloatArray:
    """Return the diagonal cavity-mode profile C_j."""

    return np.cos(2.0 * np.pi * gamma_c * _sites(length) + phase_c)


def scattering_matrix(eigenvectors: ArrayLike, gamma_c: float) -> FloatArray:
    """Return S_{alpha,beta}=<alpha|C|beta>."""

    vectors = np.asarray(eigenvectors, dtype=float)
    profile = cavity_profile(vectors.shape[0], gamma_c)
    return vectors.T @ (profile[:, None] * vectors)


def scattering_response(
    energies: ArrayLike,
    eigenvectors: ArrayLike,
    gamma_c: float,
    *,
    state_index: int = 0,
    absolute_denominators: bool = False,
    degeneracy_tolerance: float = 1e-13,
) -> tuple[FloatArray, float, FloatArray]:
    """Return per-channel response, its signed sum, and the overlap row.

    Ground-state response uses positive excitation energies.  For an excited
    initial state, signed denominators are retained unless the caller requests
    absolute denominators explicitly.
    """

    values = np.asarray(energies, dtype=float)
    if not 0 <= state_index < values.size:
        raise IndexError("state_index outside eigensystem")
    overlaps = scattering_matrix(eigenvectors, gamma_c)[state_index]
    denominators = values - values[state_index]
    if absolute_denominators:
        denominators = np.abs(denominators)
    channels = np.zeros_like(values)
    valid = np.abs(denominators) > degeneracy_tolerance
    channels[valid] = overlaps[valid] ** 2 / denominators[valid]
    return channels, float(np.sum(channels)), overlaps


def effective_detuning(
    *,
    delta_c: float,
    atom_number: float,
    dispersive_coupling: float,
    h0: float = 0.5,
    shift_factor: float = 1.0,
) -> float:
    """Return the literal published detuning convention from Eq. (3)."""

    return delta_c - shift_factor * dispersive_coupling * atom_number * h0


def critical_pump(
    susceptibility: ArrayLike,
    *,
    atom_number: float = 100.0,
    delta_c: float = -1.0,
    kappa: float = 1.0,
    dispersive_coupling: float = 0.1,
    h0: float = 0.5,
    shift_factor: float = 1.0,
) -> FloatArray | float:
    """Evaluate the linear critical pump from EQ005."""

    response = np.asarray(susceptibility, dtype=float)
    detuning = effective_detuning(
        delta_c=delta_c,
        atom_number=atom_number,
        dispersive_coupling=dispersive_coupling,
        h0=h0,
        shift_factor=shift_factor,
    )
    result = np.full(response.shape, np.inf, dtype=float)
    valid = (response > 0.0) & (detuning < 0.0)
    result[valid] = np.sqrt(
        (kappa**2 + detuning**2)
        / (-4.0 * atom_number * response[valid] * detuning)
    )
    if result.ndim == 0:
        return float(result)
    return result


def ground_state_response(
    length: int,
    chi: float,
    *,
    gamma: float = GOLDEN_GAMMA,
    gamma_c: float = 0.8,
) -> tuple[float, FloatArray, FloatArray, FloatArray]:
    """Return f1 and the AA eigensystem for a ground-state target."""

    energies, vectors = aa_eigensystem(length, chi, gamma=gamma)
    channels, response, _ = scattering_response(energies, vectors, gamma_c)
    return response, channels, energies, vectors


def state_resolved_thresholds(
    energies: ArrayLike,
    eigenvectors: ArrayLike,
    gamma_c: float,
    *,
    ipr_cutoff: float = 0.05,
    atom_number: float = 100.0,
    delta_c: float = -1.0,
    kappa: float = 1.0,
    dispersive_coupling: float = 0.1,
    shift_factor: float = 1.0,
) -> dict[str, FloatArray]:
    """Calculate finite-L state thresholds for Fig. 2.

    The paper does not print the excited-state response convention.  The
    reconstruction retains signed energy denominators, takes the magnitude of
    the total static response, and applies the source-consistent IPR classifier
    before assigning the localized self-channel threshold.
    """

    values = np.asarray(energies, dtype=float)
    vectors = np.asarray(eigenvectors, dtype=float)
    ipr = inverse_participation_ratio(vectors)
    localized = ipr >= ipr_cutoff
    overlap = scattering_matrix(vectors, gamma_c)
    denominator = values[None, :] - values[:, None]
    valid = np.abs(denominator) > 1e-13
    terms = np.zeros_like(denominator)
    terms[valid] = overlap[valid] ** 2 / denominator[valid]
    response = np.abs(np.sum(terms, axis=1))
    eta = np.asarray(
        critical_pump(
            response,
            atom_number=atom_number,
            delta_c=delta_c,
            kappa=kappa,
            dispersive_coupling=dispersive_coupling,
            shift_factor=shift_factor,
        )
    )
    eta[localized] = 0.0
    return {
        "ipr": ipr,
        "localized": localized,
        "response": response,
        "eta_c": eta,
        "diagonal_overlap": np.diag(overlap),
    }


def momentum_distribution(
    state: ArrayLike,
    q_values: ArrayLike,
) -> FloatArray:
    """Evaluate P(k/k1) using the paper's direct Fourier convention."""

    vector = np.asarray(state)
    q = np.asarray(q_values, dtype=float)
    phases = np.exp(1j * np.pi * np.outer(q, np.arange(vector.size)))
    return (np.abs(phases @ vector) ** 2 / vector.size).real


def steady_cavity_field(
    state: ArrayLike,
    eta: float,
    gamma_c: float,
    *,
    atom_number: float = 100.0,
    delta_c: float = -1.0,
    kappa: float = 1.0,
    dispersive_coupling: float = 0.1,
    shift_factor: float = 1.0,
) -> complex:
    """Evaluate the steady cavity field for one normalized orbital."""

    vector = np.asarray(state)
    probability = np.abs(vector) ** 2
    profile = cavity_profile(vector.size, gamma_c)
    theta = float(probability @ profile)
    bunching = float(probability @ (profile**2))
    denominator = (
        -delta_c
        - 1j * kappa
        + shift_factor * dispersive_coupling * atom_number * bunching
    )
    return complex(-eta * atom_number * theta / denominator)


@dataclass(frozen=True)
class SelfConsistentResult:
    state: FloatArray
    field: complex
    iterations: int
    converged: bool
    density_error: float
    field_error: float

    @property
    def photon_number(self) -> float:
        return float(abs(self.field) ** 2)

    @property
    def ipr(self) -> float:
        return float(np.sum(np.abs(self.state) ** 4))


def solve_self_consistent_state(
    length: int,
    chi: float,
    eta: float,
    *,
    gamma: float = GOLDEN_GAMMA,
    gamma_c: float = 0.8,
    hopping: float = 1.0,
    atom_number: float = 100.0,
    delta_c: float = -1.0,
    kappa: float = 1.0,
    dispersive_coupling: float = 0.1,
    shift_factor: float = 1.0,
    phase: float = 0.0,
    initial_state: ArrayLike | None = None,
    initial_field: complex | None = None,
    mixing: float = 0.35,
    tolerance: float = 1e-11,
    max_iterations: int = 1000,
) -> SelfConsistentResult:
    """Solve the nonlinear mean-field fixed point by damped continuation."""

    if not 0.0 < mixing <= 1.0:
        raise ValueError("mixing must lie in (0, 1]")
    base_diagonal, off_diagonal = aa_diagonals(
        length,
        chi,
        gamma=gamma,
        hopping=hopping,
        phase=phase,
    )
    if initial_state is None:
        _, eigvec = eigh_tridiagonal(
            base_diagonal,
            off_diagonal,
            select="i",
            select_range=(0, 0),
            check_finite=False,
        )
        state = eigvec[:, 0]
    else:
        state = np.asarray(initial_state, dtype=float).copy()
        state /= np.linalg.norm(state)
    field = (
        complex(initial_field)
        if initial_field is not None
        else steady_cavity_field(
            state,
            eta,
            gamma_c,
            atom_number=atom_number,
            delta_c=delta_c,
            kappa=kappa,
            dispersive_coupling=dispersive_coupling,
            shift_factor=shift_factor,
        )
    )
    profile = cavity_profile(length, gamma_c)
    density_error = np.inf
    field_error = np.inf

    for iteration in range(1, max_iterations + 1):
        effective_diagonal = (
            base_diagonal
            + 2.0 * eta * field.real * profile
            + dispersive_coupling * abs(field) ** 2 * profile**2
        )
        _, eigvec = eigh_tridiagonal(
            effective_diagonal,
            off_diagonal,
            select="i",
            select_range=(0, 0),
            check_finite=False,
        )
        candidate = eigvec[:, 0]
        if float(candidate @ state) < 0.0:
            candidate = -candidate
        mixed_state = (1.0 - mixing) * state + mixing * candidate
        mixed_state /= np.linalg.norm(mixed_state)
        candidate_field = steady_cavity_field(
            mixed_state,
            eta,
            gamma_c,
            atom_number=atom_number,
            delta_c=delta_c,
            kappa=kappa,
            dispersive_coupling=dispersive_coupling,
            shift_factor=shift_factor,
        )
        mixed_field = (1.0 - mixing) * field + mixing * candidate_field
        density_error = float(
            np.max(np.abs(np.abs(mixed_state) ** 2 - np.abs(state) ** 2))
        )
        field_error = float(abs(mixed_field - field))
        state = mixed_state
        field = mixed_field
        if max(density_error, field_error) < tolerance:
            return SelfConsistentResult(
                state=state,
                field=field,
                iterations=iteration,
                converged=True,
                density_error=density_error,
                field_error=field_error,
            )

    return SelfConsistentResult(
        state=state,
        field=field,
        iterations=max_iterations,
        converged=False,
        density_error=density_error,
        field_error=field_error,
    )


def continue_self_consistent_branch(
    eta_values: Iterable[float],
    *,
    length: int,
    chi: float,
    gamma: float = GOLDEN_GAMMA,
    gamma_c: float = 0.8,
    seed_field: complex = 0.5 + 0.0j,
    **solver_kwargs: object,
) -> list[tuple[float, SelfConsistentResult]]:
    """Follow a fixed-point branch in the supplied eta order."""

    state: FloatArray | None = None
    field: complex | None = seed_field
    results: list[tuple[float, SelfConsistentResult]] = []
    for eta in eta_values:
        result = solve_self_consistent_state(
            length,
            chi,
            float(eta),
            gamma=gamma,
            gamma_c=gamma_c,
            initial_state=state,
            initial_field=field,
            **solver_kwargs,
        )
        results.append((float(eta), result))
        state = result.state
        field = result.field
    return results
