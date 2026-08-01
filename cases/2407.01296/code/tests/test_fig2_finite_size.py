from __future__ import annotations

import numpy as np

from src.fig2_finite_size import (
    FIG2_REGION_NAMES,
    fig2_energy_axes,
    fig2_probe_groups,
    flatten_probe_groups,
)


def test_fig2_probe_protocol_has_four_49_point_boxes_and_full_window() -> None:
    groups = fig2_probe_groups()
    assert tuple(group.name for group in groups[:-1]) == FIG2_REGION_NAMES
    assert all(group.energies.size == 49 for group in groups[:-1])
    assert groups[-1].name == "global_coarse"
    assert groups[-1].energies.size == 121


def test_fig2_probe_energies_are_exact_nodes_of_the_paper_grid() -> None:
    real_axis, imaginary_axis = fig2_energy_axes()
    for group in fig2_probe_groups():
        expected = (
            real_axis[group.indices_yx[:, 1]]
            + 1j * imaginary_axis[group.indices_yx[:, 0]]
        )
        np.testing.assert_array_equal(group.energies, expected)


def test_flattened_probe_slices_round_trip_without_reordering() -> None:
    groups = fig2_probe_groups()
    energies, slices = flatten_probe_groups(groups)
    assert energies.size == 4 * 49 + 121
    for group, selected in zip(groups, slices, strict=True):
        np.testing.assert_array_equal(energies[selected], group.energies)
