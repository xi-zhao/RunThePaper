"""Scientific evidence selectors over frozen PXP overlap arrays."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np


def consecutive_negative_tower(
    data: Mapping[str, np.ndarray], *, prefix: str, count: int
) -> list[dict[str, float | int | str]]:
    """Match n-particle trials to consecutive negative-energy scar states.

    The paper states that high-particle MMA trials can carry weight on two primary
    scar states. Therefore a global overlap maximum is not the target definition.
    Starting below zero, the n-th trial is matched to its largest-overlap state
    strictly below the energy selected for the (n-1)-th trial.
    """

    ceiling = 0.0
    selected: list[dict[str, float | int | str]] = []
    for particles in range(1, count + 1):
        overlap = data[f"overlap_{prefix}_{particles}"]
        if len(overlap) == len(data["energy_plus"]):
            sector = "plus"
        elif len(overlap) == len(data["energy_minus"]):
            sector = "minus"
        else:
            raise ValueError("overlap length does not match either symmetry sector")
        energy = data[f"energy_{sector}"]
        candidates = np.flatnonzero(energy < ceiling - 1.0e-10)
        if not len(candidates):
            raise ValueError(f"no lower-energy state remains for {prefix}_{particles}")
        index = int(candidates[np.argmax(overlap[candidates])])
        ceiling = float(energy[index])
        selected.append(
            {
                "particles": particles,
                "sector": sector,
                "index": index,
                "energy": ceiling,
                "overlap": float(overlap[index]),
                "global_maximum_overlap": float(np.max(overlap)),
            }
        )
    return selected


def fsa_primary_overlaps(
    data: Mapping[str, np.ndarray], *, zero_tolerance: float = 1.0e-10
) -> list[dict[str, float | int | str]]:
    """Return basis-invariant FSA overlap with each matched primary scar state.

    At the central FSA state, the exact PXP spectrum has a degenerate zero-energy
    subspace. Individual eigenvector overlaps depend on the diagonalizer's basis,
    while their sum over that subspace is invariant and is the paper's 87% feature.
    """

    results: list[dict[str, float | int | str]] = []
    for state_index in range(27):
        sector_totals = {
            suffix: float(np.sum(data[f"fsa_{state_index}_{suffix}"]))
            for suffix in ("plus", "minus")
        }
        sector = max(sector_totals, key=sector_totals.get)
        energy = data[f"energy_{sector}"]
        overlap = data[f"fsa_{state_index}_{sector}"]
        if state_index == 13:
            zero = np.abs(energy) < zero_tolerance
            value = float(np.sum(overlap[zero]))
            matched_energy = 0.0
            aggregation = "zero_energy_subspace_sum"
        else:
            index = int(np.argmax(overlap))
            value = float(overlap[index])
            matched_energy = float(energy[index])
            aggregation = "individual_eigenstate"
        results.append(
            {
                "state_index": state_index,
                "sector": sector,
                "energy": matched_energy,
                "overlap": value,
                "aggregation": aggregation,
            }
        )
    return results
