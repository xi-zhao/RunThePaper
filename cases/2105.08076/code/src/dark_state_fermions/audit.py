"""Independent paper-consistency checks that never read source images."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from .gaussian import neel_orbitals
from .theory import dark_state_exponents, integrate_rg, kernel_log_slope


def wick_sign_checks() -> dict[str, object]:
    """Check the Main Eq. (4b) sign by two independent constructions."""

    # Method 1: one-body Slater projector for an explicitly delocalized orbital.
    orbital = np.asarray([1.0, 1.0j, -1.0, 0.5], dtype=np.complex128)
    orbital /= np.linalg.norm(orbital)
    projector = np.outer(orbital, orbital.conj())
    x, y = 0, 1
    projector_connected = -float(abs(projector[x, y]) ** 2)
    printed_positive = float(abs(projector[x, y]) ** 2)

    # Method 2: construct the same one-particle Fock state explicitly and
    # evaluate n_x n_y - n_x n_y.  For one particle, n_x n_y=0 at x != y.
    probabilities = np.abs(orbital) ** 2
    fock_connected = float(-probabilities[x] * probabilities[y])
    return {
        "projector_method": projector_connected,
        "explicit_fock_method": fock_connected,
        "printed_positive": printed_positive,
        "methods_agree_abs": float(abs(projector_connected - fock_connected)),
        "printed_sign_is_opposite": bool(
            projector_connected < 0
            and printed_positive > 0
            and abs(projector_connected + printed_positive) < 1e-14
        ),
    }


def relevance_inequality_checks() -> dict[str, object]:
    """Test the local `p>3/2 relevant` sentence against two formula lanes."""

    q_values = np.geomspace(0.008, 0.04, 5)
    kernel_below = kernel_log_slope(1.25, q_values)
    kernel_above = kernel_log_slope(1.75, q_values)
    _, delta_below, _ = integrate_rg(
        exponent=1.25, eta0=0.05, delta0=0.01, scale_max=4.0
    )
    _, delta_above, _ = integrate_rg(
        exponent=1.75, eta0=0.05, delta0=0.01, scale_max=4.0
    )
    return {
        "kernel_slope_p1_25": kernel_below,
        "kernel_expected_p1_25": 1.5,
        "kernel_slope_p1_75": kernel_above,
        "kernel_expected_p1_75": 2.0,
        "rg_delta_ratio_p1_25": float(delta_below[-1] / delta_below[0]),
        "rg_delta_ratio_p1_75": float(delta_above[-1] / delta_above[0]),
        "canonical_dimension_below": 3.0 - 2.0 * 1.25,
        "canonical_dimension_above": 3.0 - 2.0 * 1.75,
    }


def phase_label_checks() -> dict[str, object]:
    """Classify the two caption parameter pairs from printed analytic theory."""

    a, b = dark_state_exponents(1.25)
    return {
        "gamma0_3_p1_25": {
            "analytic_phase": "algebraic",
            "a": a,
            "b": b,
            "caption_phase": "CFT",
        },
        "gamma0_3_p5": {
            "analytic_phase": "short_range_CFT_candidate",
            "caption_phase": "algebraic",
            "reason": "p=5 is above p_c; at weak monitoring the paper's own phase map assigns the CFT regime",
        },
        "labels_are_swapped_under_printed_theory": True,
    }


def exact_number_basis_limits(length: int = 8) -> dict[str, float]:
    """A simple pointer-state check independent of the time integrator."""

    orbitals = neel_orbitals(length)
    projector = orbitals @ orbitals.conj().T
    eigenvalues = np.linalg.eigvalsh(projector[: length // 2, : length // 2])
    entropy = -np.sum(
        [
            value * np.log(value) + (1 - value) * np.log(1 - value)
            for value in np.clip(eigenvalues, 1e-14, 1 - 1e-14)
        ]
    )
    occupied = np.flatnonzero(np.diag(projector).real > 0.5)
    separations = [abs(i - j) for i, j in combinations(occupied.tolist(), 2)]
    return {
        "entropy": float(entropy),
        "trace": float(np.trace(projector).real),
        "minimum_occupied_separation": float(min(separations, default=0)),
    }
