"""Clean-room orchestration boundary for the missing DFT displacement map."""

from __future__ import annotations

import re
from typing import Any

import numpy as np


_HIGHEST_OCCUPIED_PATTERNS = (
    re.compile(r"highest occupied level \(ev\):\s*([-+0-9.eEdD]+)", re.I),
    re.compile(
        r"highest occupied, lowest unoccupied level \(ev\):\s*"
        r"([-+0-9.eEdD]+)\s+([-+0-9.eEdD]+)",
        re.I,
    ),
)


def parse_qe_highest_occupied_energy(output: str) -> float:
    """Extract the final highest occupied Kohn-Sham energy from QE stdout."""

    matches: list[float] = []
    for pattern in _HIGHEST_OCCUPIED_PATTERNS:
        matches.extend(
            float(match.group(1).replace("D", "E").replace("d", "e"))
            for match in pattern.finditer(output)
        )
    if not matches:
        raise ValueError("QE output has no highest-occupied-level record")
    return matches[-1]


def assemble_periodic_displacement_map(
    samples: list[dict[str, Any]],
    *,
    u_points: int,
    v_points: int,
) -> dict[str, Any]:
    """Validate and assemble one independently generated rectangular map."""

    if u_points < 2 or v_points < 2:
        raise ValueError("displacement grid needs at least 2x2 points")
    if len(samples) != u_points * v_points:
        raise ValueError("sample count does not fill the declared grid")
    values = np.full((u_points, v_points), np.nan, dtype=float)
    for sample in samples:
        if sample.get("data_provenance") != "independent_qe_run":
            raise ValueError("every DFT sample must come from an independent_qe_run")
        if any(
            bool(sample.get(flag))
            for flag in ("source_pixels_used", "author_code_used", "author_numeric_arrays_used")
        ):
            raise ValueError("source pixels, author code, and author arrays are forbidden")
        i = int(sample["u_index"])
        j = int(sample["v_index"])
        if not (0 <= i < u_points and 0 <= j < v_points) or np.isfinite(values[i, j]):
            raise ValueError("displacement sample index is invalid or duplicated")
        values[i, j] = float(sample["valence_max_ev"])
    if np.any(~np.isfinite(values)):
        raise ValueError("displacement map contains a missing or non-finite sample")
    shifted = values - float(np.max(values))
    return {
        "u_points": u_points,
        "v_points": v_points,
        "valence_max_ev": values.tolist(),
        "relative_valence_max_ev": shifted.tolist(),
        "energy_span_ev": float(np.ptp(values)),
    }
