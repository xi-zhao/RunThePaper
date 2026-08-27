"""Formula limit for the far-detuned total-resistivity lane in Main Fig. 3."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .phonons import phonon_resistivity


@dataclass(frozen=True)
class FarDetunedResistivity:
    """Dimensionless resistivity components in the ``Delta/Delta_* -> infinity`` limit."""

    temperature_k: np.ndarray
    background_over_rho0: np.ndarray
    many_body_over_rho0: np.ndarray
    phonon_over_rho0: np.ndarray
    total_over_rho0: np.ndarray


def asymptotic_far_detuned_resistivity(
    temperature_k: np.ndarray,
    *,
    background_over_rho0: float,
    bloch_gruneisen_k: float,
    high_temperature_slope_per_k: float,
    crossover_power: float,
) -> FarDetunedResistivity:
    """Evaluate the paper-derived far-detuned limit without guessing a detuning.

    Main-text transport vanishes as ``Delta >> Delta_*``.  The remaining total
    resistivity is therefore the Drude background plus the explicitly declared
    acoustic-phonon proxy.  No value is inferred from the source figure.
    """

    temperature = np.asarray(temperature_k, dtype=float)
    if temperature.ndim != 1 or temperature.size < 2:
        raise ValueError("temperature_k must be a one-dimensional grid")
    if not np.isfinite(temperature).all() or np.any(temperature < 0.0):
        raise ValueError("temperature_k must contain finite non-negative values")
    if np.any(np.diff(temperature) <= 0.0):
        raise ValueError("temperature_k must be strictly increasing")
    if not np.isfinite(background_over_rho0) or background_over_rho0 <= 0.0:
        raise ValueError("background_over_rho0 must be finite and positive")

    phonon = phonon_resistivity(
        temperature,
        bloch_gruneisen_k,
        high_temperature_slope_per_k,
        crossover_power,
    )
    background = np.full_like(temperature, float(background_over_rho0))
    many_body = np.zeros_like(temperature)
    total = background + many_body + phonon
    return FarDetunedResistivity(
        temperature_k=temperature,
        background_over_rho0=background,
        many_body_over_rho0=many_body,
        phonon_over_rho0=phonon,
        total_over_rho0=total,
    )


def check_far_detuned_resistivity(
    result: FarDetunedResistivity,
) -> dict[str, float | bool | str]:
    """Return executable physical invariants for the asymptotic lane."""

    arrays = (
        result.temperature_k,
        result.background_over_rho0,
        result.many_body_over_rho0,
        result.phonon_over_rho0,
        result.total_over_rho0,
    )
    finite = bool(all(np.isfinite(values).all() for values in arrays))
    identity_error = float(
        np.max(
            np.abs(
                result.total_over_rho0
                - result.background_over_rho0
                - result.many_body_over_rho0
                - result.phonon_over_rho0
            )
        )
    )
    many_body_limit = float(np.max(np.abs(result.many_body_over_rho0)))
    phonon_nonnegative = bool(np.all(result.phonon_over_rho0 >= 0.0))
    phonon_monotone = bool(np.all(np.diff(result.phonon_over_rho0) >= -1.0e-14))
    passed = bool(
        finite
        and identity_error <= 1.0e-13
        and many_body_limit <= 1.0e-15
        and phonon_nonnegative
        and phonon_monotone
    )
    return {
        "passed": passed,
        "limit_definition": "Delta/Delta_star -> infinity",
        "finite": finite,
        "total_identity_max_abs": identity_error,
        "many_body_limit_max_abs": many_body_limit,
        "phonon_nonnegative": phonon_nonnegative,
        "phonon_monotone": phonon_monotone,
        "minimum_total_over_rho0": float(np.min(result.total_over_rho0)),
        "maximum_total_over_rho0": float(np.max(result.total_over_rho0)),
    }
