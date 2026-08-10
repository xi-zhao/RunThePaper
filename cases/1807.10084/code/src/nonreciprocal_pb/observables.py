"""Paper observables, analytic references, and scientific diagnostics."""

from __future__ import annotations

from math import factorial

import numpy as np

from .liouvillian import steady_state
from .model import (
    PaperParameters,
    PhysicalScales,
    delta_l_from_k,
    fizeau_shift,
    hamiltonian,
)


def photon_statistics(rho: np.ndarray, max_order: int = 4) -> dict:
    probabilities = np.real(np.diag(rho)).copy()
    probabilities[np.abs(probabilities) < 1e-15] = 0.0
    if np.min(probabilities) < -1e-10:
        raise ValueError("steady state has a materially negative Fock probability")
    probabilities = np.maximum(probabilities, 0.0)
    probabilities /= probabilities.sum()
    photon_numbers = np.arange(probabilities.size, dtype=float)
    mean = float(np.dot(photon_numbers, probabilities))
    correlations: dict[str, float] = {}
    for order in range(1, max_order + 1):
        falling = np.ones_like(photon_numbers)
        for offset in range(order):
            falling *= np.maximum(photon_numbers - offset, 0.0)
        numerator = float(np.dot(falling, probabilities))
        correlations[f"g{order}"] = numerator / mean**order if mean > 0.0 else float("nan")
    return {
        "probabilities": probabilities,
        "mean_n": mean,
        **correlations,
    }


def analytic_correlations(delta: np.ndarray | float, kerr_u: float, gamma: float) -> tuple[np.ndarray, np.ndarray]:
    delta_array = np.asarray(delta, dtype=float)
    linewidth = gamma**2 / 4.0
    g2 = (delta_array**2 + linewidth) / ((delta_array + kerr_u) ** 2 + linewidth)
    g3 = (delta_array**2 + linewidth) ** 2 / (
        (((delta_array + kerr_u) ** 2 + linewidth) * ((delta_array + 2.0 * kerr_u) ** 2 + linewidth))
    )
    return g2, g3


def poisson_probabilities(mean_n: float, count: int) -> np.ndarray:
    return np.asarray(
        [np.exp(-mean_n) * mean_n**number / factorial(number) for number in range(count)],
        dtype=float,
    )


def blockade_diagnostics(statistics: dict, count: int = 5) -> dict:
    probabilities = np.asarray(statistics["probabilities"], dtype=float)[:count]
    poisson = poisson_probabilities(float(statistics["mean_n"]), count)
    relative = np.divide(
        probabilities - poisson,
        poisson,
        out=np.zeros_like(probabilities),
        where=poisson > 0.0,
    )
    threshold = float(np.exp(-float(statistics["mean_n"])))
    threshold_two = threshold + float(statistics["mean_n"]) * float(statistics["g3"])
    return {
        "poisson": poisson,
        "relative_poisson_deviation": relative,
        "f": threshold,
        "f2": threshold_two,
        "one_photon_blockade": bool(float(statistics["g2"]) < threshold),
        "two_photon_blockade": bool(
            float(statistics["g3"]) < threshold and float(statistics["g2"]) >= threshold_two
        ),
        "pit_2_to_4": bool(
            float(statistics["g2"]) > 1.0
            and float(statistics["g3"]) > 1.0
            and float(statistics["g4"]) > 1.0
        ),
    }


def solve_observables(
    parameters: PaperParameters,
    scales: PhysicalScales,
    *,
    k: float,
    direction: int,
    omega_khz: float,
    input_power_w: float,
    cutoff: int | None = None,
) -> dict:
    selected_cutoff = int(cutoff or parameters.fock_cutoff)
    hamiltonian_matrix, annihilation = hamiltonian(
        parameters,
        scales,
        k=k,
        direction=direction,
        omega_khz=omega_khz,
        input_power_w=input_power_w,
        cutoff=selected_cutoff,
    )
    result = steady_state(hamiltonian_matrix, annihilation)
    statistics = photon_statistics(result.rho)
    diagnostics = blockade_diagnostics(statistics)
    delta_l = delta_l_from_k(scales, k)
    delta_f = fizeau_shift(scales, direction, omega_khz)
    analytic_g2, analytic_g3 = analytic_correlations(
        delta_l + delta_f,
        scales.kerr_u_rad_s,
        scales.gamma_rad_s,
    )
    return {
        "k": float(k),
        "direction": int(direction),
        "omega_khz": float(omega_khz),
        "input_power_w": float(input_power_w),
        "cutoff": selected_cutoff,
        "delta_l_over_u": float(delta_l / scales.kerr_u_rad_s),
        "delta_f_over_u": float(delta_f / scales.kerr_u_rad_s),
        "analytic_g2": float(analytic_g2),
        "analytic_g3": float(analytic_g3),
        "residual_norm": result.residual_norm,
        "trace_error": result.trace_error,
        "hermiticity_error": result.hermiticity_error,
        "minimum_eigenvalue": result.minimum_eigenvalue,
        "tail_probability": float(statistics["probabilities"][-1]),
        **{key: value for key, value in statistics.items() if key != "probabilities"},
        "probabilities": statistics["probabilities"],
        **diagnostics,
    }


def fock_energies_over_u(
    scales: PhysicalScales,
    *,
    k: float,
    direction: int,
    omega_khz: float,
    maximum_n: int,
) -> np.ndarray:
    photon_number = np.arange(maximum_n + 1, dtype=float)
    delta = delta_l_from_k(scales, k) + fizeau_shift(scales, direction, omega_khz)
    return photon_number * delta / scales.kerr_u_rad_s + photon_number * (photon_number - 1.0)


def fock_energies_from_ratios(
    *,
    k: float,
    direction: int,
    fizeau_over_u: float,
    maximum_n: int,
) -> np.ndarray:
    """Evaluate the paper's idealized level diagrams in units of ``U``.

    The numerical curves use the physical rotation frequencies printed in the
    paper.  The level schematics instead state the rounded identities
    ``|Delta_F| = U/2`` and ``|Delta_F| = U``.  Keeping this idealized helper
    separate prevents a rounded 29/58 kHz mapping from masquerading as an
    exact resonance condition.
    """

    photon_number = np.arange(maximum_n + 1, dtype=float)
    detuning_over_u = 1.0 - float(k) + int(direction) * float(fizeau_over_u)
    return photon_number * detuning_over_u + photon_number * (photon_number - 1.0)


def required_k_for_resonance(*, direction: int, fizeau_over_u: float, photon_order: int) -> float:
    """Return the tuning ``k`` required for an ``n``-photon resonance.

    From ``E_n/U = n(1-k+s f)+n(n-1)=0`` follows ``k=n+s f``, where
    ``s`` is the propagation direction and ``f=|Delta_F|/U``.  This is the
    invariant behind Supplement Fig. S3 and Table S2.
    """

    if direction not in {-1, 1}:
        raise ValueError("direction must be +1 or -1 for a directional resonance")
    if photon_order < 1:
        raise ValueError("photon_order must be at least one")
    if fizeau_over_u < 0.0:
        raise ValueError("fizeau_over_u is an unsigned magnitude")
    return float(photon_order + direction * fizeau_over_u)
