"""Vacuum scattering formulas from the supplement's microscopic model."""

from __future__ import annotations

import numpy as np


def scattering_amplitude(
    energy_mev: np.ndarray,
    detuning_mev: float,
    binding_energy_mev: float,
    tunnel_mev: float,
    convention: str = "logarithmic",
    linewidth_mev: float = 0.05,
) -> np.ndarray:
    """Return the dimensionless amplitude ``f(E)=-2 m_red T(E)``.

    The two available conventions are both printed in the paper but are not
    mutually sign-consistent for its declared negative binding energy.  They
    are therefore explicit API choices, never silently selected from a figure.
    """

    energy = np.asarray(energy_mev, dtype=float)
    if detuning_mev == 0.0:
        raise ValueError("detuning_mev must be nonzero")
    if linewidth_mev <= 0.0:
        raise ValueError("linewidth_mev must be positive")
    if convention == "logarithmic":
        ratio = (energy - detuning_mev + 1j * linewidth_mev) / binding_energy_mev
        return 4.0 * np.pi * tunnel_mev**2 / (detuning_mev**2 * np.log(ratio))
    if convention == "caption_pole":
        pole = binding_energy_mev + detuning_mev
        return (
            -4.0
            * np.pi
            * tunnel_mev**2
            / (abs(binding_energy_mev) * (energy - pole + 1j * linewidth_mev))
        )
    if convention == "printed_pole":
        pole = binding_energy_mev - detuning_mev
        return (
            -4.0
            * np.pi
            * tunnel_mev**2
            / (abs(binding_energy_mev) * (energy - pole + 1j * linewidth_mev))
        )
    raise ValueError(f"unknown scattering convention: {convention}")
