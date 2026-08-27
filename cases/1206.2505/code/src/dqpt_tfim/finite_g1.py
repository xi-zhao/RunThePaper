"""Clean-room finite-``g1`` audit for the supplement's withheld expansion.

The publication gives only the ``g1 -> infinity`` formula and explicitly
defers finite-``g1`` corrections.  This module therefore computes a controlled
finite-chain reference directly from the printed Ising Hamiltonian; it does
not guess the unpublished expansion coefficients.
"""

from __future__ import annotations

import numpy as np

from .model import _evolve_states, extreme_quench_loschmidt_rates, spin_hamiltonian


def finite_g1_sector_rates(
    sites: int,
    g1: float,
    phases: np.ndarray,
    *,
    periodic: bool = True,
) -> dict[str, np.ndarray]:
    """Return exact finite-chain sector rates at fixed dimensionless phases.

    At ``g0=0`` the two symmetry-broken ground states are the all-up and
    all-down computational states.  ``phase=g1*t`` keeps the comparison window
    fixed while ``g1`` is increased toward the published extreme-quench limit.
    """

    if sites < 2:
        raise ValueError("sites must be at least two")
    if g1 <= 0.0:
        raise ValueError("g1 must be positive")
    phase = np.asarray(phases, dtype=float)
    if phase.ndim != 1 or phase.size < 2 or np.any(np.diff(phase) <= 0.0):
        raise ValueError("phases must be a strictly increasing vector")

    plus = np.zeros(1 << sites, dtype=complex)
    minus = np.zeros_like(plus)
    plus[0] = 1.0
    minus[-1] = 1.0
    times = phase / g1
    states = _evolve_states(plus, spin_hamiltonian(sites, g1, periodic), times)
    diagonal_amplitude = np.clip(np.abs(states @ plus.conj()), 1e-300, None)
    off_diagonal_amplitude = np.clip(np.abs(states @ minus.conj()), 1e-300, None)
    exact_diagonal = -np.log(diagonal_amplitude) / sites
    exact_off_diagonal = -np.log(off_diagonal_amplitude) / sites
    asymptotic = extreme_quench_loschmidt_rates(times, g1)
    return {
        "phase": phase,
        "time": times,
        "finite_diagonal_rate": exact_diagonal,
        "finite_off_diagonal_rate": exact_off_diagonal,
        "finite_dominant_rate": np.minimum(exact_diagonal, exact_off_diagonal),
        "asymptotic_diagonal_rate": asymptotic["physical_diagonal_rate"],
        "asymptotic_off_diagonal_rate": asymptotic["physical_off_diagonal_rate"],
        "asymptotic_dominant_rate": asymptotic["dominant_physical_rate"],
        "state_norm": np.linalg.norm(states, axis=1),
    }
