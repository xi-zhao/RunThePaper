"""Trivalent torus topology and T1 neighbor exchanges."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
from numpy.typing import NDArray

from .geometry import box_matrix, edge_displacement, edge_length, wrap_fractional

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class EdgeRecord:
    cell: int
    first: int
    second: int
    index: int


def build_hexagonal_tiling(
    nx: int,
    ny: int,
) -> tuple[FloatArray, FloatArray, list[list[int]]]:
    """Construct an exact periodic honeycomb with ``nx*ny`` cells.

    ``nx`` must be even so the staggered rows close periodically.
    """

    if nx < 2 or ny < 2 or nx % 2:
        raise ValueError("nx must be even and nx, ny must both be at least two")
    lx = 1.5 * nx
    ly = sqrt(3.0) * ny
    lattice = box_matrix(lx, ly)
    vertex_ids: dict[tuple[float, float], int] = {}
    positions: list[tuple[float, float]] = []
    cells: list[list[int]] = []

    for column in range(nx):
        for row in range(ny):
            center_x = 1.5 * column
            center_y = sqrt(3.0) * (row + 0.5 * (column % 2))
            cycle: list[int] = []
            for corner in range(6):
                angle = corner * np.pi / 3.0
                x = (center_x + np.cos(angle)) % lx
                y = (center_y + np.sin(angle)) % ly
                key = (round(float(x), 10), round(float(y), 10))
                if key not in vertex_ids:
                    vertex_ids[key] = len(positions)
                    positions.append((x / lx, y / ly))
                cycle.append(vertex_ids[key])
            cells.append(cycle)

    fractional = np.asarray(positions, dtype=np.float64)
    validate_topology(cells, len(fractional))
    return lattice, fractional, cells


def edge_map(cells: list[list[int]]) -> dict[tuple[int, int], list[EdgeRecord]]:
    mapping: dict[tuple[int, int], list[EdgeRecord]] = {}
    for cell_index, cycle in enumerate(cells):
        for index, first in enumerate(cycle):
            second = cycle[(index + 1) % len(cycle)]
            key = (min(first, second), max(first, second))
            mapping.setdefault(key, []).append(
                EdgeRecord(cell=cell_index, first=first, second=second, index=index)
            )
    return mapping


def vertex_cells(cells: list[list[int]], vertex_count: int) -> list[list[int]]:
    incidence: list[list[int]] = [[] for _ in range(vertex_count)]
    for cell_index, cycle in enumerate(cells):
        for vertex in cycle:
            incidence[vertex].append(cell_index)
    return incidence


def topology_report(cells: list[list[int]], vertex_count: int) -> dict[str, object]:
    edges = edge_map(cells)
    incidence = vertex_cells(cells, vertex_count)
    duplicate_vertices = [
        index for index, cycle in enumerate(cells) if len(cycle) != len(set(cycle))
    ]
    short_cells = [index for index, cycle in enumerate(cells) if len(cycle) < 3]
    bad_edges = [key for key, records in edges.items() if len(records) != 2]
    same_orientation = [
        key
        for key, records in edges.items()
        if len(records) == 2
        and not (
            records[0].first == records[1].second
            and records[0].second == records[1].first
        )
    ]
    bad_vertices = [index for index, owners in enumerate(incidence) if len(owners) != 3]
    euler = vertex_count - len(edges) + len(cells)
    return {
        "vertices": vertex_count,
        "edges": len(edges),
        "cells": len(cells),
        "euler_characteristic": euler,
        "duplicate_vertices_in_cells": duplicate_vertices,
        "short_cells": short_cells,
        "bad_edges": bad_edges,
        "same_orientation_edges": same_orientation,
        "bad_vertices": bad_vertices,
        "valid": not duplicate_vertices
        and not short_cells
        and not bad_edges
        and not same_orientation
        and not bad_vertices
        and euler == 0,
    }


def validate_topology(cells: list[list[int]], vertex_count: int) -> None:
    report = topology_report(cells, vertex_count)
    if not report["valid"]:
        raise ValueError(f"invalid torus topology: {report}")


def _remove_consecutive(cycle: list[int], first: int, second: int) -> list[int]:
    index = cycle.index(first)
    if cycle[(index + 1) % len(cycle)] != second:
        raise ValueError(f"{first}->{second} is not an oriented cell edge")
    output = cycle.copy()
    del output[(index + 1) % len(output)]
    return output


def _insert_before(cycle: list[int], existing: int, inserted: int) -> list[int]:
    if inserted in cycle:
        raise ValueError("T1 insertion would duplicate a cell vertex")
    index = cycle.index(existing)
    output = cycle.copy()
    output.insert(index, inserted)
    return output


def perform_t1(
    cells: list[list[int]],
    fractional: FloatArray,
    lattice: FloatArray,
    edge: tuple[int, int],
    new_length: float,
) -> tuple[list[list[int]], FloatArray, dict[str, int]]:
    """Flip one short edge using the four-cell incidence rule in the paper."""

    if new_length <= 0.0:
        raise ValueError("new T1 edge length must be positive")
    mapping = edge_map(cells)
    key = (min(edge), max(edge))
    records = mapping.get(key)
    if records is None or len(records) != 2:
        raise ValueError("T1 edge must be shared by exactly two cells")

    alpha_record = records[0]
    beta_record = records[1]
    u = alpha_record.first
    v = alpha_record.second
    if beta_record.first != v or beta_record.second != u:
        raise ValueError("T1 cells do not carry opposite edge orientations")
    alpha = alpha_record.cell
    beta = beta_record.cell

    incidence = vertex_cells(cells, len(fractional))
    gamma_set = set(incidence[u]) - {alpha, beta}
    delta_set = set(incidence[v]) - {alpha, beta}
    if len(gamma_set) != 1 or len(delta_set) != 1:
        raise ValueError("T1 endpoints must each have exactly one third cell")
    gamma = gamma_set.pop()
    delta = delta_set.pop()
    if gamma == delta or len({alpha, beta, gamma, delta}) != 4:
        raise ValueError("degenerate T1 requires four distinct cells")

    updated = [cycle.copy() for cycle in cells]
    updated[alpha] = _remove_consecutive(updated[alpha], u, v)
    updated[beta] = _remove_consecutive(updated[beta], v, u)
    updated[gamma] = _insert_before(updated[gamma], u, v)
    updated[delta] = _insert_before(updated[delta], v, u)

    displacement = edge_displacement(fractional, u, v, lattice)
    old_length = float(np.linalg.norm(displacement))
    if old_length <= 1e-14:
        raise ValueError("cannot orient a zero-length T1 edge")
    midpoint = lattice @ fractional[u] + 0.5 * displacement
    perpendicular = (
        np.array([-displacement[1], displacement[0]], dtype=np.float64) / old_length
    )
    physical_u = midpoint + 0.5 * new_length * perpendicular
    physical_v = midpoint - 0.5 * new_length * perpendicular
    inverse_lattice = np.linalg.inv(lattice)
    positions = fractional.copy()
    positions[u] = inverse_lattice @ physical_u
    positions[v] = inverse_lattice @ physical_v
    positions = wrap_fractional(positions)

    validate_topology(updated, len(positions))
    return (
        updated,
        positions,
        {
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "delta": delta,
            "first": u,
            "second": v,
        },
    )


def shortest_edges(
    cells: list[list[int]],
    fractional: FloatArray,
    lattice: FloatArray,
) -> list[tuple[float, tuple[int, int]]]:
    output = [
        (edge_length(fractional, key[0], key[1], lattice), key)
        for key in edge_map(cells)
    ]
    output.sort(key=lambda item: (item[0], item[1]))
    return output


def perform_short_edge_t1s(
    cells: list[list[int]],
    fractional: FloatArray,
    lattice: FloatArray,
    threshold: float,
    reset_factor: float,
    max_events: int,
) -> tuple[list[list[int]], FloatArray, list[dict[str, int]]]:
    """Resolve short edges one at a time, recomputing topology after each flip."""

    updated_cells = [cycle.copy() for cycle in cells]
    updated_positions = fractional.copy()
    events: list[dict[str, int]] = []
    for _ in range(max_events):
        candidates = shortest_edges(updated_cells, updated_positions, lattice)
        if not candidates or candidates[0][0] >= threshold:
            break
        _, key = candidates[0]
        try:
            updated_cells, updated_positions, event = perform_t1(
                updated_cells,
                updated_positions,
                lattice,
                key,
                reset_factor * threshold,
            )
        except ValueError:
            # A four-cell degeneracy can occur in very small periodic systems.
            # It is reported by the caller through the unresolved-short-edge count.
            break
        events.append(event)
    return updated_cells, updated_positions, events
