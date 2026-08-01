"""Finite-size protocol for the independently generated Fig. 2(d).

The paper samples four 7 x 7 energy boxes and a coarse grid over the full
displayed complex-energy window.  This module makes that scientific protocol
explicit and testable.  It contains no author eigenvalue tables or digitized
figure coordinates: the box centers are the grid indices recorded by the
authors' public calculation script, while every potential value is generated
from the paper equations by the runner.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


FIG2_REAL_WINDOW = (-2.0, 4.0)
FIG2_IMAGINARY_WINDOW = (-3.0, 3.0)
FIG2_GRID_SIZE = 101
FIG2_REGION_RADIUS = 3
FIG2_GLOBAL_STRIDE = 10
FIG2_REGION_NAMES = ("red", "yellow", "green", "cyan")
FIG2_REGION_CENTERS_YX = ((61, 59), (50, 22), (14, 5), (69, 19))


@dataclass(frozen=True)
class EnergyProbeGroup:
    """One declared group of complex energies used in the scaling test."""

    name: str
    indices_yx: np.ndarray
    energies: np.ndarray


def fig2_energy_axes() -> tuple[np.ndarray, np.ndarray]:
    """Return the formal 101 x 101 complex-energy axes used for Fig. 2."""

    return (
        np.linspace(*FIG2_REAL_WINDOW, FIG2_GRID_SIZE),
        np.linspace(*FIG2_IMAGINARY_WINDOW, FIG2_GRID_SIZE),
    )


def fig2_probe_groups() -> tuple[EnergyProbeGroup, ...]:
    """Build the four 49-point boxes and the 121-point full-window sample."""

    real_axis, imaginary_axis = fig2_energy_axes()
    groups: list[EnergyProbeGroup] = []
    for name, (center_y, center_x) in zip(
        FIG2_REGION_NAMES,
        FIG2_REGION_CENTERS_YX,
        strict=True,
    ):
        indices = np.asarray(
            [
                (center_y + offset_y, center_x + offset_x)
                for offset_y in range(-FIG2_REGION_RADIUS, FIG2_REGION_RADIUS + 1)
                for offset_x in range(-FIG2_REGION_RADIUS, FIG2_REGION_RADIUS + 1)
            ],
            dtype=np.int64,
        )
        groups.append(
            EnergyProbeGroup(
                name=name,
                indices_yx=indices,
                energies=np.asarray(
                    real_axis[indices[:, 1]]
                    + 1j * imaginary_axis[indices[:, 0]],
                    dtype=np.complex128,
                ),
            )
        )

    global_indices = np.asarray(
        [
            (row, column)
            for row in range(0, FIG2_GRID_SIZE, FIG2_GLOBAL_STRIDE)
            for column in range(0, FIG2_GRID_SIZE, FIG2_GLOBAL_STRIDE)
        ],
        dtype=np.int64,
    )
    groups.append(
        EnergyProbeGroup(
            name="global_coarse",
            indices_yx=global_indices,
            energies=np.asarray(
                real_axis[global_indices[:, 1]]
                + 1j * imaginary_axis[global_indices[:, 0]],
                dtype=np.complex128,
            ),
        )
    )
    return tuple(groups)


def flatten_probe_groups(
    groups: tuple[EnergyProbeGroup, ...],
) -> tuple[np.ndarray, tuple[slice, ...]]:
    """Flatten probe energies while retaining deterministic group slices."""

    if not groups:
        raise ValueError("at least one energy probe group is required")
    slices: list[slice] = []
    start = 0
    for group in groups:
        stop = start + group.energies.size
        slices.append(slice(start, stop))
        start = stop
    return np.concatenate([group.energies for group in groups]), tuple(slices)
