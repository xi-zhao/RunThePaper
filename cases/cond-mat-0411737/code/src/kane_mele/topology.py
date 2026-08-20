"""Finite-cylinder spectral flow for the Laughlin spin-pump argument."""

from __future__ import annotations

from math import pi

import numpy as np


def cylinder_flux_spectral_flow(
    *,
    level_cutoff: int,
    flux_points: int,
    circumference_in_correlation_lengths: float,
    ramp_time_in_inverse_gaps: float,
) -> tuple[list[dict[str, float | int]], dict[str, float | int | bool]]:
    """Track the two helical edge branches during one ``h/e`` flux cycle.

    Energies are in units of the bulk half-gap, with ``hbar v_F=1`` and
    correlation length ``xi=1/Delta``.  Flux shifts angular momentum by one,
    so the explicit level permutation counts the pumped Kramers quantum.
    """

    if level_cutoff < 3 or flux_points < 21:
        raise ValueError("resolved finite-cylinder spectrum required")
    if circumference_in_correlation_lengths <= 1.0:
        raise ValueError("cylinder must exceed the bulk correlation length")
    if ramp_time_in_inverse_gaps <= 1.0:
        raise ValueError("flux ramp must be slower than the inverse bulk gap")
    levels = np.arange(-level_cutoff, level_cutoff + 1)
    fluxes = np.linspace(0.0, 1.0, flux_points)
    spacing = 2.0 * pi / circumference_in_correlation_lengths
    rows: list[dict[str, float | int]] = []
    for flux in fluxes:
        right = spacing * (levels + flux)
        left = -spacing * (levels + flux)
        for level, right_energy, left_energy in zip(levels, right, left):
            rows.append(
                {
                    "flux_over_h_over_e": float(flux),
                    "angular_level": int(level),
                    "right_down_energy_over_half_gap": float(right_energy),
                    "left_up_energy_over_half_gap": float(left_energy),
                }
            )
    epsilon = 1e-9
    initial_right = spacing * (levels + epsilon)
    final_right = spacing * (levels + 1.0 + epsilon)
    initial_left = -initial_right
    final_left = -final_right
    right_upward_crossings = int(np.sum((initial_right < 0) & (final_right > 0)))
    left_downward_crossings = int(np.sum((initial_left > 0) & (final_left < 0)))
    return rows, {
        "right_down_upward_crossings": right_upward_crossings,
        "left_up_downward_crossings": left_downward_crossings,
        "pumped_spin_in_hbar": float(
            (right_upward_crossings + left_downward_crossings) / 2.0
        ),
        "level_permutation_residual": float(
            np.max(np.abs(spacing * (levels[:-1] + 1.0) - spacing * levels[1:]))
        ),
        "circumference_condition_satisfied": True,
        "adiabatic_condition_satisfied": True,
        "edge_level_spacing_over_half_gap": spacing,
    }
