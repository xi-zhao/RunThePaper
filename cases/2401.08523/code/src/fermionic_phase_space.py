"""Closed-form science model for a physical single fermionic mode.

This module implements equations from arXiv:2401.08523v2.  It deliberately
contains no plotting code and never reads paper figures or digitized data.
Every generated curve is therefore determined only by the formulas and the
explicit numerical grid supplied by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]
Distribution = Literal["P", "W", "Q"]


@dataclass(frozen=True)
class PhaseSpaceBodies:
    """Complex bodies of the three Grassmann-valued distributions.

    Their common nilpotent soul is ``alpha alpha*`` and is represented in the
    derivation documents rather than as an ordinary floating-point number.
    """

    glauber_p: FloatArray
    wigner_w: FloatArray
    husimi_q: FloatArray


def _occupation_array(occupation: ArrayLike) -> FloatArray:
    values = np.asarray(occupation, dtype=float)
    if np.any(~np.isfinite(values)) or np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("occupation must be finite and lie in [0, 1]")
    return values


def fermi_dirac_occupation(energy_over_temperature: ArrayLike) -> FloatArray:
    """Return ``<n> = 1 / (1 + exp(epsilon/T))`` stably."""

    x = np.asarray(energy_over_temperature, dtype=float)
    if np.any(~np.isfinite(x)):
        raise ValueError("energy_over_temperature must be finite")
    result = np.empty_like(x, dtype=float)
    nonnegative = x >= 0.0
    exp_minus = np.exp(-x[nonnegative])
    result[nonnegative] = exp_minus / (1.0 + exp_minus)
    exp_plus = np.exp(x[~nonnegative])
    result[~nonnegative] = 1.0 / (1.0 + exp_plus)
    return result


def phase_space_bodies(occupation: ArrayLike) -> PhaseSpaceBodies:
    """Return the bodies ``P_B=-n``, ``W_B=1/2-n``, ``Q_B=1-n``."""

    n = _occupation_array(occupation)
    return PhaseSpaceBodies(glauber_p=-n, wigner_w=0.5 - n, husimi_q=1.0 - n)


def covariance_determinants(occupation: ArrayLike) -> PhaseSpaceBodies:
    """Return ``det gamma(z) = -z_B**2`` for ``P``, ``W``, and ``Q``."""

    bodies = phase_space_bodies(occupation)
    return PhaseSpaceBodies(
        glauber_p=-(bodies.glauber_p**2),
        wigner_w=-(bodies.wigner_w**2),
        husimi_q=-(bodies.husimi_q**2),
    )


def renyi_offset(order: float) -> float:
    """Return ``ln(r)/(1-r)``, including its continuous value ``-1`` at r=1."""

    if not np.isfinite(order) or order <= 0.0:
        raise ValueError("Renyi order must be finite and positive")
    if order == 1.0:
        return -1.0
    return float(np.log(order) / (1.0 - order))


def renyi_entropy(
    occupation: ArrayLike,
    order: float,
    distribution: Distribution,
) -> FloatArray:
    """Evaluate the paper's real-valued phase-space Rényi entropy.

    A zero body gives ``+inf``.  This is a physical singularity, not a missing
    value, and rendering code may clip it at the visible plot boundary.
    """

    bodies = phase_space_bodies(occupation)
    body = {
        "P": bodies.glauber_p,
        "W": bodies.wigner_w,
        "Q": bodies.husimi_q,
    }.get(distribution)
    if body is None:
        raise ValueError(f"unknown distribution: {distribution}")
    with np.errstate(divide="ignore"):
        return renyi_offset(order) - np.log(np.abs(body))


def entropy_lower_bound(order: float, distribution: Distribution) -> float:
    """Return the exact uncertainty lower bound for the selected distribution."""

    base = renyi_offset(order)
    if distribution == "W":
        return base + float(np.log(2.0))
    if distribution in {"P", "Q"}:
        return base
    raise ValueError(f"unknown distribution: {distribution}")


def thermal_loss_output_occupation(
    input_occupation: float,
    environment_occupation: float,
    transmissivity: float,
) -> float:
    """Return the output occupation of the single-mode thermal loss channel."""

    n_in = float(_occupation_array(input_occupation))
    n_env = float(_occupation_array(environment_occupation))
    if not np.isfinite(transmissivity) or not 0.0 <= transmissivity <= 1.0:
        raise ValueError("transmissivity must lie in [0, 1]")
    return transmissivity * n_in + (1.0 - transmissivity) * n_env


def crossing_points() -> dict[str, tuple[float, float]]:
    """Return exact occupation/value crossings used by main Figure 2."""

    return {
        "P_equals_W": (0.25, -0.0625),
        "P_equals_Q": (0.5, -0.25),
        "W_equals_Q": (0.75, -0.0625),
    }
