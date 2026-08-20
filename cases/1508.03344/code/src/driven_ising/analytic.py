"""Analytic free-drive phase boundaries used by Main Fig. 2(a)."""

from __future__ import annotations

import numpy as np

PHASE_TO_CODE = {"PM": 0, "0": 1, "pi": 2, "0pi": 3}


def free_phase_label(h_t1: float, j_t2: float) -> str:
    """Classify the four free uniform phases in the printed first quadrant."""
    if not (0.0 <= h_t1 <= np.pi / 2 and 0.0 <= j_t2 <= np.pi / 2):
        raise ValueError("h*T1 and J*T2 must lie in [0, pi/2]")
    lower = min(h_t1, np.pi / 2 - h_t1)
    upper = max(h_t1, np.pi / 2 - h_t1)
    if j_t2 < lower:
        return "PM"
    if j_t2 > upper:
        return "0pi"
    return "0" if h_t1 < np.pi / 4 else "pi"


def free_phase_map(points: int) -> dict[str, np.ndarray]:
    """Return the analytic phase grid and both exact gap-closing lines."""
    if points < 3:
        raise ValueError("points must be at least 3")
    axis = np.linspace(0.0, np.pi / 2, points)
    phase = np.empty((points, points), dtype=np.int8)
    for row, j_t2 in enumerate(axis):
        for column, h_t1 in enumerate(axis):
            phase[row, column] = PHASE_TO_CODE[free_phase_label(h_t1, j_t2)]
    return {
        "h_t1": axis,
        "j_t2": axis,
        "phase_code": phase,
        "zero_gap_boundary": axis.copy(),
        "pi_gap_boundary": np.pi / 2 - axis,
    }
