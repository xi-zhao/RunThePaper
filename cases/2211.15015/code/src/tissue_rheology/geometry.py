"""Periodic polygon geometry used by the independent vertex model.

All physical polygons are reconstructed locally from reduced torus coordinates.
No source-figure geometry enters this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PolygonObservables:
    """Area, perimeter, centroid, and analytic coordinate derivatives."""

    vertices: FloatArray
    area: float
    perimeter: float
    centroid: FloatArray
    grad_area: FloatArray
    grad_perimeter: FloatArray


def box_matrix(lx: float, ly: float, tilt: float = 0.0) -> FloatArray:
    """Return the two-dimensional Lees--Edwards lattice matrix."""

    if lx <= 0.0 or ly <= 0.0:
        raise ValueError("box lengths must be positive")
    return np.array([[lx, tilt], [0.0, ly]], dtype=np.float64)


def minimum_image(delta_fractional: FloatArray) -> FloatArray:
    """Apply the nearest-image convention in reduced lattice coordinates."""

    delta = np.asarray(delta_fractional, dtype=np.float64)
    return delta - np.rint(delta)


def edge_displacement(
    fractional: FloatArray,
    first: int,
    second: int,
    lattice: FloatArray,
) -> FloatArray:
    """Physical nearest-image displacement from ``first`` to ``second``."""

    return lattice @ minimum_image(fractional[second] - fractional[first])


def edge_length(
    fractional: FloatArray,
    first: int,
    second: int,
    lattice: FloatArray,
) -> float:
    return float(np.linalg.norm(edge_displacement(fractional, first, second, lattice)))


def unwrap_cycle(
    fractional: FloatArray,
    cycle: list[int] | NDArray[np.int64],
    lattice: FloatArray,
) -> FloatArray:
    """Unwrap one ordered periodic polygon into a contiguous physical frame."""

    ids = [int(value) for value in cycle]
    if len(ids) < 3:
        raise ValueError("a cell polygon needs at least three vertices")
    output = np.empty((len(ids), 2), dtype=np.float64)
    output[0] = lattice @ fractional[ids[0]]
    for index in range(1, len(ids)):
        output[index] = output[index - 1] + edge_displacement(
            fractional,
            ids[index - 1],
            ids[index],
            lattice,
        )
    closing = output[-1] + edge_displacement(fractional, ids[-1], ids[0], lattice)
    if np.linalg.norm(closing - output[0]) > 1e-7:
        raise ValueError(
            "polygon cycle does not close under the nearest-image convention"
        )
    return output


def signed_area(vertices: FloatArray) -> float:
    x = vertices[:, 0]
    y = vertices[:, 1]
    return float(0.5 * np.sum(x * np.roll(y, -1) - y * np.roll(x, -1)))


def polygon_observables(vertices: FloatArray) -> PolygonObservables:
    """Evaluate a counterclockwise polygon and the derivatives in Eq. (1)."""

    points = np.asarray(vertices, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3:
        raise ValueError("vertices must have shape (n>=3, 2)")

    x = points[:, 0]
    y = points[:, 1]
    cross = x * np.roll(y, -1) - y * np.roll(x, -1)
    area = float(0.5 * np.sum(cross))
    if not np.isfinite(area) or area <= 1e-12:
        raise ValueError(f"cell polygon has nonpositive signed area: {area}")

    edges = points - np.roll(points, 1, axis=0)
    lengths = np.linalg.norm(edges, axis=1)
    if np.any(lengths <= 1e-12):
        raise ValueError("cell polygon contains a zero-length edge")
    perimeter = float(np.sum(lengths))

    centroid = np.array(
        [
            np.sum((x + np.roll(x, -1)) * cross),
            np.sum((y + np.roll(y, -1)) * cross),
        ],
        dtype=np.float64,
    ) / (6.0 * area)

    grad_area = 0.5 * np.column_stack(
        [
            np.roll(y, -1) - np.roll(y, 1),
            np.roll(x, 1) - np.roll(x, -1),
        ]
    )
    to_previous = points - np.roll(points, 1, axis=0)
    to_next = points - np.roll(points, -1, axis=0)
    grad_perimeter = to_previous / np.linalg.norm(to_previous, axis=1)[:, None]
    grad_perimeter += to_next / np.linalg.norm(to_next, axis=1)[:, None]

    return PolygonObservables(
        vertices=points,
        area=area,
        perimeter=perimeter,
        centroid=centroid,
        grad_area=grad_area,
        grad_perimeter=grad_perimeter,
    )


def wrap_fractional(fractional: FloatArray) -> FloatArray:
    """Wrap reduced coordinates into the half-open unit square."""

    return np.mod(np.asarray(fractional, dtype=np.float64), 1.0)


def remap_tilt(
    fractional: FloatArray,
    lattice: FloatArray,
) -> tuple[FloatArray, FloatArray, int]:
    """Keep the shear tilt within half a horizontal lattice vector.

    The simultaneous reduced-coordinate transform leaves all physical positions
    exactly unchanged up to an integer lattice translation.
    """

    coordinates = np.asarray(fractional, dtype=np.float64).copy()
    matrix = np.asarray(lattice, dtype=np.float64).copy()
    lx = float(matrix[0, 0])
    shift = int(np.rint(matrix[0, 1] / lx))
    if shift:
        matrix[0, 1] -= shift * lx
        coordinates[:, 0] += shift * coordinates[:, 1]
        coordinates = wrap_fractional(coordinates)
    return coordinates, matrix, shift
