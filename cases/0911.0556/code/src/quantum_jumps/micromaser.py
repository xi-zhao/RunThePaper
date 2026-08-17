"""Diagonal micromaser tilted generator derived from the printed jumps."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.linalg


@dataclass(frozen=True)
class MicromaserParameters:
    excitation_number: float = 100.0
    thermal_occupation: float = 0.15
    alpha: float = 2.0 * np.pi
    cutoff: int = 250

    @property
    def r(self) -> float:
        return self.excitation_number

    @property
    def lambda_rate(self) -> float:
        return self.thermal_occupation

    @property
    def kappa(self) -> float:
        return 1.0 + self.thermal_occupation

    @property
    def phi(self) -> float:
        return self.alpha / np.sqrt(self.excitation_number)


def tilted_birth_death(
    parameters: MicromaserParameters,
    s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return diagonal, lower and upper diagonals of the tilted generator."""

    if parameters.cutoff < 3:
        raise ValueError("cutoff must be at least three")
    n = np.arange(parameters.cutoff, dtype=np.float64)
    atomic_birth = parameters.r * np.sin(parameters.phi * np.sqrt(n + 1.0)) ** 2
    thermal_birth = parameters.lambda_rate * (n + 1.0)
    death = parameters.kappa * n
    diagonal = -(atomic_birth + thermal_birth + death)
    lower = np.exp(-float(s)) * atomic_birth[:-1] + thermal_birth[:-1]
    upper = death[1:]
    return diagonal, lower, upper


def dominant_eigenvalue(parameters: MicromaserParameters, s: float) -> float:
    diagonal, lower, upper = tilted_birth_death(parameters, s)
    symmetric_offdiagonal = np.sqrt(lower * upper)
    value = scipy.linalg.eigh_tridiagonal(
        diagonal,
        symmetric_offdiagonal,
        select="i",
        select_range=(parameters.cutoff - 1, parameters.cutoff - 1),
        eigvals_only=True,
        check_finite=True,
    )[0]
    return float(value)


def dominant_distribution(
    parameters: MicromaserParameters,
    s: float,
) -> tuple[float, np.ndarray]:
    """Return theta and the normalized right eigenvector over photon number."""

    diagonal, lower, upper = tilted_birth_death(parameters, s)
    symmetric_offdiagonal = np.sqrt(lower * upper)
    values, vectors = scipy.linalg.eigh_tridiagonal(
        diagonal,
        symmetric_offdiagonal,
        select="i",
        select_range=(parameters.cutoff - 1, parameters.cutoff - 1),
        eigvals_only=False,
        check_finite=True,
    )
    symmetric_vector = vectors[:, 0]
    if np.sum(symmetric_vector) < 0:
        symmetric_vector = -symmetric_vector

    log_scale = np.zeros(parameters.cutoff, dtype=np.float64)
    log_scale[1:] = 0.5 * np.cumsum(np.log(lower) - np.log(upper))
    log_scale -= np.max(log_scale)
    distribution = np.exp(log_scale) * symmetric_vector
    distribution = np.maximum(distribution, 0.0)
    distribution /= np.sum(distribution)
    return float(values[0]), distribution


def direct_generator(parameters: MicromaserParameters, s: float) -> np.ndarray:
    diagonal, lower, upper = tilted_birth_death(parameters, s)
    matrix = np.diag(diagonal)
    matrix += np.diag(lower, k=-1)
    matrix += np.diag(upper, k=1)
    return matrix
