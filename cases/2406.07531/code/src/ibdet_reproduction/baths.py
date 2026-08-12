"""Interacting-bath construction from independently supplied matrices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]
RealArray = NDArray[np.float64]


@dataclass(frozen=True)
class BathSelection:
    """Orthonormal bath orbitals represented in the full one-particle basis."""

    orbitals: ComplexArray
    strengths: RealArray
    label: str

    @property
    def size(self) -> int:
        return int(self.orbitals.shape[1])


def _environment_indices(
    size: int, impurity_indices: Iterable[int]
) -> NDArray[np.int64]:
    impurity = np.asarray(sorted(set(int(i) for i in impurity_indices)), dtype=int)
    if impurity.size == 0:
        raise ValueError("at least one impurity index is required")
    if impurity[0] < 0 or impurity[-1] >= size:
        raise ValueError("impurity index outside one-particle basis")
    mask = np.ones(size, dtype=bool)
    mask[impurity] = False
    return np.flatnonzero(mask)


def orthonormalize_candidates(
    candidates: ComplexArray,
    against: ComplexArray | None = None,
    *,
    threshold: float = 1e-10,
) -> ComplexArray:
    """Project candidates away from an existing basis and rank-reveal by SVD."""

    matrix = np.asarray(candidates, dtype=np.complex128)
    if matrix.ndim != 2:
        raise ValueError("candidates must be a matrix")
    if matrix.shape[1] == 0:
        return np.empty((matrix.shape[0], 0), dtype=np.complex128)
    if against is not None:
        fixed = np.asarray(against, dtype=np.complex128)
        if fixed.ndim != 2 or fixed.shape[0] != matrix.shape[0]:
            raise ValueError("against basis has incompatible shape")
        matrix = matrix - fixed @ (fixed.conj().T @ matrix)
    u, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
    keep = singular_values > threshold
    return np.asarray(u[:, keep], dtype=np.complex128)


def density_matrix_bath(
    density: ComplexArray,
    impurity_indices: Iterable[int],
    *,
    singular_value_threshold: float = 1e-10,
) -> BathSelection:
    """Construct B_DM from the environment-impurity 1-RDM block."""

    gamma = np.asarray(density, dtype=np.complex128)
    if gamma.ndim != 2 or gamma.shape[0] != gamma.shape[1]:
        raise ValueError("density must be square")
    impurity = np.asarray(sorted(set(int(i) for i in impurity_indices)), dtype=int)
    environment = _environment_indices(gamma.shape[0], impurity)
    block = gamma[np.ix_(environment, impurity)]
    u, singular_values, _ = np.linalg.svd(block, full_matrices=False)
    keep = singular_values > singular_value_threshold
    orbitals = np.zeros(
        (gamma.shape[0], int(np.count_nonzero(keep))), dtype=np.complex128
    )
    orbitals[environment, :] = u[:, keep]
    return BathSelection(
        orbitals=orbitals,
        strengths=np.asarray(singular_values[keep], dtype=float),
        label="B_DM",
    )


def mean_field_green_function(
    one_body_hamiltonian: ComplexArray,
    frequency: float,
    *,
    chemical_potential: float = 0.0,
    broadening: float = 0.05,
) -> ComplexArray:
    """Return the retarded noninteracting resolvent."""

    hamiltonian = np.asarray(one_body_hamiltonian, dtype=np.complex128)
    identity = np.eye(hamiltonian.shape[0], dtype=np.complex128)
    z = frequency + chemical_potential + 1j * broadening
    return np.linalg.inv(z * identity - hamiltonian)


def green_function_bath(
    one_body_hamiltonian: ComplexArray,
    impurity_indices: Iterable[int],
    frequencies: Iterable[float],
    *,
    chemical_potential: float = 0.0,
    broadening: float = 0.05,
    singular_value_threshold: float = 1e-7,
    against: ComplexArray | None = None,
) -> BathSelection:
    """Construct B_GF from SVDs of Im g_EI on a real-frequency grid."""

    hamiltonian = np.asarray(one_body_hamiltonian, dtype=np.complex128)
    impurity = np.asarray(sorted(set(int(i) for i in impurity_indices)), dtype=int)
    environment = _environment_indices(hamiltonian.shape[0], impurity)
    candidates: list[ComplexArray] = []
    strengths: list[float] = []
    for frequency in frequencies:
        green = mean_field_green_function(
            hamiltonian,
            float(frequency),
            chemical_potential=chemical_potential,
            broadening=broadening,
        )
        block = np.imag(green[np.ix_(environment, impurity)])
        u, singular_values, _ = np.linalg.svd(block, full_matrices=False)
        keep = singular_values > singular_value_threshold
        if not np.any(keep):
            continue
        full = np.zeros(
            (hamiltonian.shape[0], int(np.count_nonzero(keep))), dtype=np.complex128
        )
        full[environment, :] = u[:, keep]
        candidates.append(full)
        strengths.extend(float(value) for value in singular_values[keep])
    if not candidates:
        return BathSelection(
            orbitals=np.empty((hamiltonian.shape[0], 0), dtype=np.complex128),
            strengths=np.empty(0, dtype=float),
            label="B_GF",
        )
    orbitals = orthonormalize_candidates(
        np.concatenate(candidates, axis=1),
        against,
        threshold=singular_value_threshold,
    )
    return BathSelection(
        orbitals=orbitals,
        strengths=np.asarray(sorted(strengths, reverse=True)[: orbitals.shape[1]]),
        label="B_GF",
    )


def natural_orbital_bath(
    correlated_density: ComplexArray,
    impurity_indices: Iterable[int],
    *,
    occupation_threshold: float = 1e-5,
    maximum_orbitals: int | None = None,
    against: ComplexArray | None = None,
) -> BathSelection:
    """Select B_NO by fractional natural occupations in the environment."""

    density = np.asarray(correlated_density, dtype=np.complex128)
    impurity = np.asarray(sorted(set(int(i) for i in impurity_indices)), dtype=int)
    environment = _environment_indices(density.shape[0], impurity)
    block = 0.5 * (
        density[np.ix_(environment, environment)]
        + density[np.ix_(environment, environment)].conj().T
    )
    occupations, vectors = np.linalg.eigh(block)
    occupations = np.clip(np.real(occupations), 0.0, 1.0)
    strength = np.minimum(occupations, 1.0 - occupations)
    ordering = np.argsort(strength)[::-1]
    ordering = ordering[strength[ordering] > occupation_threshold]
    if maximum_orbitals is not None:
        ordering = ordering[: int(maximum_orbitals)]
    full = np.zeros((density.shape[0], ordering.size), dtype=np.complex128)
    full[environment, :] = vectors[:, ordering]
    orbitals = orthonormalize_candidates(full, against, threshold=1e-10)
    return BathSelection(
        orbitals=orbitals,
        strengths=np.asarray(strength[ordering][: orbitals.shape[1]], dtype=float),
        label="B_NO",
    )


def combine_embedding_basis(
    dimension: int,
    impurity_indices: Iterable[int],
    baths: Iterable[BathSelection],
    *,
    threshold: float = 1e-10,
) -> ComplexArray:
    """Build R=[I,B_DM,B_GF,B_NO] with explicit sequential orthogonalization."""

    impurity = np.asarray(sorted(set(int(i) for i in impurity_indices)), dtype=int)
    _environment_indices(dimension, impurity)
    basis = np.zeros((dimension, impurity.size), dtype=np.complex128)
    basis[impurity, np.arange(impurity.size)] = 1.0
    for bath in baths:
        addition = orthonormalize_candidates(bath.orbitals, basis, threshold=threshold)
        if addition.shape[1]:
            basis = np.concatenate([basis, addition], axis=1)
    error = np.max(np.abs(basis.conj().T @ basis - np.eye(basis.shape[1])))
    if error > 100 * threshold:
        raise RuntimeError(f"embedding basis lost orthonormality: {error:.3e}")
    return basis
