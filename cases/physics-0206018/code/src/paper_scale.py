"""Paper-scale geometry extensions for the coupled-hexagon BEM campaign.

The trusted feature runner uses uniform element counts.  The paper-scale
discretization needs exactly 1600 physical boundary elements, which is not
divisible by the twelve sides and twelve corner arcs.  This module therefore
accepts one explicit count per segment without changing the attested feature
implementation in :mod:`src.bem`.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.bem import BoundaryMesh

FloatArray = NDArray[np.float64]


def _positive_counts(values: Iterable[int], expected: int, label: str) -> list[int]:
    raw = list(values)
    if len(raw) != expected:
        raise ValueError(f"{label} must contain exactly {expected} counts")
    counts: list[int] = []
    for value in raw:
        numeric = float(value)
        integer = int(numeric)
        if not np.isfinite(numeric) or numeric != integer or integer < 1:
            raise ValueError(f"{label} counts must be positive finite integers")
        counts.append(integer)
    return counts


def _mesh_from_segments(
    starts: list[FloatArray],
    ends: list[FloatArray],
    cavity: list[int],
    curvature: list[float],
) -> BoundaryMesh:
    start = np.asarray(starts, dtype=float)
    end = np.asarray(ends, dtype=float)
    cavity_ids = np.asarray(cavity, dtype=np.int64)
    edge = end - start
    length = np.linalg.norm(edge, axis=1)
    if np.any(length <= 0):
        raise ValueError("boundary elements must have positive length")
    tangent = edge / length[:, None]
    normal = np.column_stack((tangent[:, 1], -tangent[:, 0]))
    return BoundaryMesh(
        start=start,
        end=end,
        midpoint=(start + end) / 2,
        tangent=tangent,
        normal=normal,
        length=length,
        curvature=np.asarray(curvature, dtype=float),
        cavity=cavity_ids,
    )


def coupled_explicit_rounded_hexagon_mesh(
    side_element_counts: Iterable[int],
    corner_element_counts: Iterable[int],
    corner_radius: float = 0.0205,
    *,
    side_length: float = 1.0,
    center_displacement: ArrayLike = (1.8, -0.5),
) -> BoundaryMesh:
    """Build two circular-fillet hexagons with explicit per-segment counts.

    Counts are ordered by cavity and then counter-clockwise segment index.  The
    same geometry formula as the independently derived feature implementation
    is used, but no author mesh, curve, code, data, or source pixels are read.
    """
    side_counts = _positive_counts(side_element_counts, 12, "side_element_counts")
    corner_counts = _positive_counts(corner_element_counts, 12, "corner_element_counts")
    if corner_radius <= 0 or side_length <= 0:
        raise ValueError("corner_radius and side_length must be positive")
    displacement = np.asarray(center_displacement, dtype=float)
    if displacement.shape != (2,) or not np.all(np.isfinite(displacement)):
        raise ValueError("center_displacement must contain two finite coordinates")
    centers = np.vstack((-displacement / 2, displacement / 2))
    sides = 6
    circumradius = side_length / (2 * np.sin(np.pi / sides))
    angles = 2 * np.pi * np.arange(sides) / sides
    base = circumradius * np.column_stack((np.cos(angles), np.sin(angles)))
    interior_angle = np.pi * (sides - 2) / sides
    tangent_offset = corner_radius / np.tan(interior_angle / 2)
    if 2 * tangent_offset >= side_length:
        raise ValueError("corner fillets consume the entire straight side")

    starts: list[FloatArray] = []
    ends: list[FloatArray] = []
    cavity_ids: list[int] = []
    curvatures: list[float] = []
    for cavity_id, center_shift in enumerate(centers):
        vertices = base + center_shift
        tangent_in = np.empty_like(vertices)
        tangent_out = np.empty_like(vertices)
        fillet_centers = np.empty_like(vertices)
        for index, vertex in enumerate(vertices):
            previous = vertices[(index - 1) % sides]
            following = vertices[(index + 1) % sides]
            incoming = (vertex - previous) / np.linalg.norm(vertex - previous)
            outgoing = (following - vertex) / np.linalg.norm(following - vertex)
            tangent_in[index] = vertex - tangent_offset * incoming
            tangent_out[index] = vertex + tangent_offset * outgoing
            left_normal = np.array([-incoming[1], incoming[0]])
            fillet_centers[index] = tangent_in[index] + corner_radius * left_normal

        for index in range(sides):
            segment_index = cavity_id * sides + index
            center = fillet_centers[index]
            start_angle = np.arctan2(
                tangent_in[index, 1] - center[1],
                tangent_in[index, 0] - center[0],
            )
            end_angle = np.arctan2(
                tangent_out[index, 1] - center[1],
                tangent_out[index, 0] - center[0],
            )
            while end_angle <= start_angle:
                end_angle += 2 * np.pi
            corner_count = corner_counts[segment_index]
            arc_angles = np.linspace(start_angle, end_angle, corner_count + 1)
            arc_points = center + corner_radius * np.column_stack(
                (np.cos(arc_angles), np.sin(arc_angles))
            )
            for element in range(corner_count):
                starts.append(arc_points[element])
                ends.append(arc_points[element + 1])
                cavity_ids.append(cavity_id)
                curvatures.append(1 / corner_radius)

            straight_start = tangent_out[index]
            straight_end = tangent_in[(index + 1) % sides]
            side_count = side_counts[segment_index]
            for element in range(side_count):
                lower = element / side_count
                upper = (element + 1) / side_count
                starts.append(straight_start + lower * (straight_end - straight_start))
                ends.append(straight_start + upper * (straight_end - straight_start))
                cavity_ids.append(cavity_id)
                curvatures.append(0.0)

    return _mesh_from_segments(starts, ends, cavity_ids, curvatures)
