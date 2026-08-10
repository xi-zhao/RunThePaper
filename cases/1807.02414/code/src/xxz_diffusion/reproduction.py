"""Scientific observables built from the independently solved XXZ TBA state."""

from __future__ import annotations

from math import erf

import numpy as np

from .tba import StationaryState


def _erf_array(values: np.ndarray) -> np.ndarray:
    return np.fromiter((erf(float(value)) for value in values.ravel()), dtype=float).reshape(
        values.shape
    )


def euler_profile(state: StationaryState, x: np.ndarray, time: float) -> np.ndarray:
    """Weak-wall Euler profile normalized by the wall chemical potential."""

    arguments = state.velocity[:, None] * float(time) - np.asarray(x)[None, :]
    return 0.5 * np.sum(
        state.susceptibility_weights[:, None] * np.sign(arguments), axis=0
    )


def projected_diffusive_profile(
    state: StationaryState, x: np.ndarray, time: float
) -> np.ndarray:
    """Collective-spin projection of the full non-diagonal Eq. (13) operator.

    The paper's PDE is d_t n = (1/2) D d_x^2 n.  Hence a step transported by
    one mode has the denominator sqrt(2 D t), not sqrt(4 D t).
    """

    spin_diffusivity = state.spin_onsager / state.susceptibility
    denominator = np.sqrt(2.0 * spin_diffusivity * float(time))
    arguments = (
        state.velocity[:, None] * float(time) - np.asarray(x)[None, :]
    ) / denominator
    return 0.5 * np.sum(
        state.susceptibility_weights[:, None] * _erf_array(arguments), axis=0
    )


def build_domain_wall_profiles(
    state: StationaryState, x: np.ndarray, times: list[float]
) -> dict[str, np.ndarray]:
    """Build all six formula-derived curves in Main Fig. 1."""

    return {
        "euler": np.stack([euler_profile(state, x, time) for time in times]),
        "diffusive_projected": np.stack(
            [projected_diffusive_profile(state, x, time) for time in times]
        ),
    }
