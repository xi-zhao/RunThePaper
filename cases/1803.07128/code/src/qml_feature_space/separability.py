"""Independent checks for the phase-squeezing separability theorem.

The paper's displayed Fock coefficients define the feature vectors.  This
module checks their finite-set rank and the affine classifier claim without
using the paper's simulation code or numerical arrays.
"""

from __future__ import annotations

from itertools import product

import numpy as np
from scipy.optimize import linprog

from .model import single_mode_overlap, truncated_squeezed_state


def multimode_fock_states(
    phases: np.ndarray,
    c: float,
    even_terms: int,
    *,
    normalize: bool = False,
) -> np.ndarray:
    """Return tensor-product squeezed states for arbitrary input dimension."""

    points = np.atleast_2d(np.asarray(phases, dtype=float))
    if c <= 0:
        raise ValueError("the theorem requires c > 0")
    if even_terms <= 0:
        raise ValueError("even_terms must be positive")
    states = np.ones((len(points), 1), dtype=np.complex128)
    for axis in range(points.shape[1]):
        mode = truncated_squeezed_state(
            points[:, axis], c, even_terms, normalize=normalize
        )
        states = np.einsum("bi,bj->bij", states, mode).reshape(len(points), -1)
    if normalize:
        norms = np.linalg.norm(states, axis=1, keepdims=True)
        states = states / np.maximum(norms, np.finfo(float).tiny)
    return states


def analytic_multimode_gram(phases: np.ndarray, c: float) -> np.ndarray:
    """Return the complex Gram matrix from the printed overlap formula."""

    points = np.atleast_2d(np.asarray(phases, dtype=float))
    gram = np.ones((len(points), len(points)), dtype=np.complex128)
    for axis in range(points.shape[1]):
        gram *= single_mode_overlap(
            points[:, axis, None], points[None, :, axis], c
        )
    return gram


def realify(states: np.ndarray) -> np.ndarray:
    """Embed complex feature rows in the equivalent real vector space."""

    array = np.atleast_2d(np.asarray(states, dtype=np.complex128))
    return np.concatenate((array.real, array.imag), axis=1)


def numerical_rank(matrix: np.ndarray, relative_tolerance: float = 1e-10) -> int:
    singular_values = np.linalg.svd(np.asarray(matrix), compute_uv=False)
    if not len(singular_values):
        return 0
    return int(np.count_nonzero(singular_values > relative_tolerance * singular_values[0]))


def all_binary_affine_interpolation(features: np.ndarray) -> dict[str, object]:
    """Try every binary labelling through the stronger equality criterion."""

    rows = np.atleast_2d(np.asarray(features, dtype=float))
    design = np.column_stack((rows, np.ones(len(rows))))
    worst_residual = -1.0
    worst_labels: list[int] = []
    for labels_tuple in product((-1.0, 1.0), repeat=len(rows)):
        labels = np.asarray(labels_tuple)
        weights, *_ = np.linalg.lstsq(design, labels, rcond=None)
        residual = float(np.max(np.abs(design @ weights - labels)))
        if residual > worst_residual:
            worst_residual = residual
            worst_labels = [int(value) for value in labels]
    return {
        "labelings_tested": 2 ** len(rows),
        "design_rank": numerical_rank(design),
        "worst_absolute_residual": worst_residual,
        "worst_labels": worst_labels,
    }


def strict_affine_separation_feasible(
    points: np.ndarray, labels: np.ndarray
) -> bool:
    """Check whether one affine hyperplane separates labels with unit margin."""

    rows = np.atleast_2d(np.asarray(points, dtype=float))
    signs = np.asarray(labels, dtype=float)
    if signs.shape != (len(rows),) or not np.all(np.isin(signs, (-1.0, 1.0))):
        raise ValueError("labels must contain one +/-1 value per point")
    design = np.column_stack((rows, np.ones(len(rows))))
    result = linprog(
        np.zeros(design.shape[1]),
        A_ub=-signs[:, None] * design,
        b_ub=-np.ones(len(rows)),
        bounds=[(None, None)] * design.shape[1],
        method="highs",
    )
    return bool(result.success)
