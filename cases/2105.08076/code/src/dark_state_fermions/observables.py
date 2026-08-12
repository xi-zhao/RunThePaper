"""Nonlinear observables evaluated before trajectory averaging."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]


def subsystem_entropy(projector: ComplexArray, sites: NDArray[np.int64]) -> float:
    """Von Neumann entropy of a number-conserving Gaussian subsystem."""

    block = projector[np.ix_(sites, sites)]
    eigenvalues = np.linalg.eigvalsh(block).real
    eigenvalues = np.clip(eigenvalues, 1e-14, 1.0 - 1e-14)
    entropy = -np.sum(
        eigenvalues * np.log(eigenvalues)
        + (1.0 - eigenvalues) * np.log(1.0 - eigenvalues)
    )
    return float(entropy)


def entropy_profile(
    projector: ComplexArray,
    ell_values: Iterable[int],
    *,
    origins: Iterable[int] = (0,),
) -> FloatArray:
    """Average contiguous-block entropy over declared ring origins."""

    length = projector.shape[0]
    values: list[float] = []
    origin_array = np.asarray(list(origins), dtype=int)
    for ell in ell_values:
        samples = []
        for origin in origin_array:
            sites = (origin + np.arange(int(ell), dtype=int)) % length
            samples.append(subsystem_entropy(projector, sites))
        values.append(float(np.mean(samples)))
    return np.asarray(values, dtype=float)


def density_correlations(
    projector: ComplexArray,
    ell_values: Iterable[int],
) -> tuple[FloatArray, FloatArray]:
    """Return the paper's positive magnitude and literal connected covariance.

    For x != y, fermionic Wick contraction gives
    ``<n_x n_y>_c = -|<c_x^dagger c_y>|^2``.  Main Eq. (4b) prints the positive
    expression.  Both are retained so the reproduction and audit cannot be
    conflated.
    """

    length = projector.shape[0]
    sites = np.arange(length, dtype=int)
    positive: list[float] = []
    for ell in ell_values:
        partners = (sites + int(ell)) % length
        positive.append(float(np.mean(np.abs(projector[sites, partners]) ** 2)))
    positive_array = np.asarray(positive, dtype=float)
    return positive_array, -positive_array


def chord_length(length: int, ell: NDArray[np.float64] | FloatArray) -> FloatArray:
    values = np.asarray(ell, dtype=float)
    return np.asarray((length / np.pi) * np.sin(np.pi * values / length), dtype=float)
