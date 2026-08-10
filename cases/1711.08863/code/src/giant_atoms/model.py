"""Waveguide-QED coefficients derived from the paper's master equation.

No source-figure data enter this module.  The connection-point summation is an
independent implementation of the general coefficients printed after Eq. (2),
while :func:`table_coefficients` implements the closed forms in Table I.  Their
agreement is used as a formula-level cross-check before Main Fig. 2 is drawn.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]
SETUPS = ("ab", "aabb", "abab", "abba")


@dataclass(frozen=True)
class Coefficients:
    """Dimensionful coefficients for one connection-point geometry."""

    exchange: FloatArray
    individual_a: FloatArray
    individual_b: FloatArray
    collective: FloatArray
    shift_a: FloatArray
    shift_b: FloatArray

    def plotted(self) -> dict[str, FloatArray]:
        return {
            "g": self.exchange,
            "gamma_a": self.individual_a,
            "gamma_b": self.individual_b,
            "gamma_coll": self.collective,
        }


def _as_float_array(phi: ArrayLike) -> FloatArray:
    return np.asarray(phi, dtype=np.float64)


def _pair_sum(
    point_indices_left: NDArray[np.int64],
    point_indices_right: NDArray[np.int64],
    phi: FloatArray,
    function,
) -> FloatArray:
    distances = np.abs(
        point_indices_left[:, None] - point_indices_right[None, :]
    ).astype(np.float64)
    phases = distances[(...,) + (None,) * phi.ndim] * phi
    return np.sum(function(phases), axis=(0, 1), dtype=np.float64)


def _self_shift(point_indices: NDArray[np.int64], phi: FloatArray) -> FloatArray:
    total = np.zeros_like(phi, dtype=np.float64)
    for left_index, left in enumerate(point_indices):
        for right in point_indices[left_index + 1 :]:
            total = total + np.sin(abs(int(right) - int(left)) * phi)
    return total


def coefficients_from_ordering(
    ordering: str,
    phi: ArrayLike,
    *,
    gamma: float = 1.0,
) -> Coefficients:
    """Evaluate Eq. (2)'s coefficient sums for equally spaced connections.

    ``ordering`` records the atom label at consecutive waveguide connection
    points.  For example, ``abab`` is the braided geometry.  Every connection
    point has the same bare relaxation rate ``gamma`` and adjacent points are
    separated by phase ``phi``.
    """

    if ordering not in SETUPS:
        raise ValueError(f"unsupported ordering {ordering!r}; expected one of {SETUPS}")
    if not np.isfinite(gamma) or gamma <= 0.0:
        raise ValueError("gamma must be finite and positive")

    phi_array = _as_float_array(phi)
    point_indices = np.arange(len(ordering), dtype=np.int64)
    a_points = point_indices[np.fromiter((label == "a" for label in ordering), bool)]
    b_points = point_indices[np.fromiter((label == "b" for label in ordering), bool)]

    exchange = 0.5 * gamma * _pair_sum(a_points, b_points, phi_array, np.sin)
    collective = gamma * _pair_sum(a_points, b_points, phi_array, np.cos)
    individual_a = gamma * _pair_sum(a_points, a_points, phi_array, np.cos)
    individual_b = gamma * _pair_sum(b_points, b_points, phi_array, np.cos)
    shift_a = gamma * _self_shift(a_points, phi_array)
    shift_b = gamma * _self_shift(b_points, phi_array)
    return Coefficients(
        exchange=np.asarray(exchange, dtype=np.float64),
        individual_a=np.asarray(individual_a, dtype=np.float64),
        individual_b=np.asarray(individual_b, dtype=np.float64),
        collective=np.asarray(collective, dtype=np.float64),
        shift_a=np.asarray(shift_a, dtype=np.float64),
        shift_b=np.asarray(shift_b, dtype=np.float64),
    )


def table_coefficients(
    ordering: str,
    phi: ArrayLike,
    *,
    gamma: float = 1.0,
) -> Coefficients:
    """Evaluate the equal-spacing closed forms printed in Table I."""

    if ordering not in SETUPS:
        raise ValueError(f"unsupported ordering {ordering!r}; expected one of {SETUPS}")
    if not np.isfinite(gamma) or gamma <= 0.0:
        raise ValueError("gamma must be finite and positive")
    p = _as_float_array(phi)

    if ordering == "ab":
        zeros = np.zeros_like(p)
        ones = np.ones_like(p) * gamma
        return Coefficients(
            exchange=0.5 * gamma * np.sin(p),
            individual_a=ones,
            individual_b=ones.copy(),
            collective=gamma * np.cos(p),
            shift_a=zeros,
            shift_b=zeros.copy(),
        )

    if ordering == "aabb":
        individual = 2.0 * gamma * (1.0 + np.cos(p))
        shift = gamma * np.sin(p)
        return Coefficients(
            exchange=0.5
            * gamma
            * (np.sin(p) + 2.0 * np.sin(2.0 * p) + np.sin(3.0 * p)),
            individual_a=individual,
            individual_b=individual.copy(),
            collective=gamma
            * (np.cos(p) + 2.0 * np.cos(2.0 * p) + np.cos(3.0 * p)),
            shift_a=shift,
            shift_b=shift.copy(),
        )

    if ordering == "abab":
        individual = 2.0 * gamma * (1.0 + np.cos(2.0 * p))
        shift = gamma * np.sin(2.0 * p)
        return Coefficients(
            exchange=0.5 * gamma * (3.0 * np.sin(p) + np.sin(3.0 * p)),
            individual_a=individual,
            individual_b=individual.copy(),
            collective=gamma * (3.0 * np.cos(p) + np.cos(3.0 * p)),
            shift_a=shift,
            shift_b=shift.copy(),
        )

    return Coefficients(
        exchange=gamma * (np.sin(p) + np.sin(2.0 * p)),
        individual_a=2.0 * gamma * (1.0 + np.cos(3.0 * p)),
        individual_b=2.0 * gamma * (1.0 + np.cos(p)),
        collective=2.0 * gamma * (np.cos(p) + np.cos(2.0 * p)),
        shift_a=gamma * np.sin(3.0 * p),
        shift_b=gamma * np.sin(p),
    )


def maximum_table_residual(phi: ArrayLike, *, gamma: float = 1.0) -> float:
    """Maximum residual between the general sum and all Table-I expressions."""

    residual = 0.0
    for ordering in SETUPS:
        general = coefficients_from_ordering(ordering, phi, gamma=gamma)
        closed = table_coefficients(ordering, phi, gamma=gamma)
        for field in Coefficients.__dataclass_fields__:
            residual = max(
                residual,
                float(np.max(np.abs(getattr(general, field) - getattr(closed, field)))),
            )
    return residual
