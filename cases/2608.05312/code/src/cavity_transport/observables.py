"""Bright/dark projectors and transport observables."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ManifoldProjectors:
    bright: NDArray[np.complex128]
    dark: NDArray[np.complex128]
    cavity_weights: NDArray[np.float64]
    bright_indices: NDArray[np.int64]
    dark_indices: NDArray[np.int64]
    eigenvectors: NDArray[np.complex128]


def manifold_projectors(h: NDArray[np.complex128]) -> ManifoldProjectors:
    """Implement SM Appendix E: two largest cavity weights are bright."""

    dimension = h.shape[0]
    if h.shape != (dimension, dimension) or dimension < 3:
        raise ValueError("h must be a square extended-space Hamiltonian")

    system_h = h[:-1, :-1]
    _, eigenvectors = np.linalg.eigh(system_h)
    weights = np.abs(eigenvectors[0, :]) ** 2
    order = np.argsort(weights)
    bright_indices = np.sort(order[-2:]).astype(np.int64)
    dark_indices = np.sort(order[:-2]).astype(np.int64)

    bright_system = eigenvectors[:, bright_indices] @ eigenvectors[:, bright_indices].conj().T
    dark_system = eigenvectors[:, dark_indices] @ eigenvectors[:, dark_indices].conj().T
    bright = np.zeros_like(h)
    dark = np.zeros_like(h)
    bright[:-1, :-1] = bright_system
    dark[:-1, :-1] = dark_system
    return ManifoldProjectors(
        bright=bright,
        dark=dark,
        cavity_weights=weights.astype(float),
        bright_indices=bright_indices,
        dark_indices=dark_indices,
        eigenvectors=eigenvectors,
    )


def expectation(
    operator: NDArray[np.complex128],
    rho: NDArray[np.complex128],
) -> float:
    return float(np.real(np.trace(operator @ rho)))


def populations(
    rho: NDArray[np.complex128],
    projectors: ManifoldProjectors,
) -> dict[str, float]:
    return {
        "bright": expectation(projectors.bright, rho),
        "dark": expectation(projectors.dark, rho),
        "cavity": float(np.real(rho[0, 0])),
        "sink": float(np.real(rho[-1, -1])),
        "trace": float(np.real(np.trace(rho))),
    }


def population_series(
    rhos: NDArray[np.complex128],
    projectors: ManifoldProjectors,
) -> dict[str, NDArray[np.float64]]:
    names = ("bright", "dark", "cavity", "sink", "trace")
    rows = [populations(rho, projectors) for rho in rhos]
    return {
        name: np.asarray([row[name] for row in rows], dtype=float) for name in names
    }


def rescue_rate_matrix(
    cavity_weights: NDArray[np.float64],
    gamma_rec: float,
) -> NDArray[np.float64]:
    weights = np.asarray(cavity_weights, dtype=float)
    return gamma_rec * np.outer(weights, 1.0 - weights)


def dephasing_rate_matrix(
    eigenvectors: NDArray[np.complex128],
    gamma_deph: float,
) -> NDArray[np.float64]:
    """Secular dephasing rates from the equation following Main Eq. (4)."""

    emitter_probabilities = np.abs(eigenvectors[1:, :]) ** 2
    return gamma_deph * emitter_probabilities.T @ emitter_probabilities
