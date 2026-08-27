"""Independent leading-order Kubo/relaxation-time quadrature."""

from __future__ import annotations

import numpy as np

from .kinetic import hole_mass_ratio, hole_scattering_rate, radial_grid
from .thermodynamics import HBAR_MEV_PS, EquilibriumState, ModelParameters, bose, fermi


def broadened_hole_rates(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    hole_nodes: np.ndarray,
    exciton_points: int,
    exciton_max_pf: float,
    angle_points: int,
    broadening_mev: float,
) -> np.ndarray:
    """Evaluate the imaginary self-energy without the analytic-delta kernel."""

    if angle_points < 8 or broadening_mev <= 0.0:
        raise ValueError("invalid Kubo quadrature")
    k_nodes, k_weights = radial_grid(exciton_points, exciton_max_pf)
    angles = (np.arange(angle_points, dtype=float) + 0.5) * (2.0 * np.pi / angle_points)
    angle_weight = 2.0 * np.pi / angle_points
    coupling_rate = 6.0 * tunnel_mev**2 / (abs(params.trion_binding_mev) * HBAR_MEV_PS)
    eta = broadening_mev / params.fermi_energy_mev
    detuning = equilibrium.detuning_mev / params.fermi_energy_mev
    output = np.empty_like(hole_nodes, dtype=float)
    for index, p in enumerate(hole_nodes):
        total = 0.0
        for k, wk in zip(k_nodes, k_weights, strict=True):
            r2 = p * p + k * k + 2.0 * p * k * np.cos(angles)
            mismatch = (
                p * p
                + hole_mass_ratio(params, "x") * k * k
                - hole_mass_ratio(params, "t") * r2
                - detuning
            )
            ex = (
                params.fermi_energy_mev * hole_mass_ratio(params, "x") * k * k
                - equilibrium.mu_x_mev
            )
            et = (
                params.fermi_energy_mev * hole_mass_ratio(params, "t") * r2
                - equilibrium.mu_t_mev
                + equilibrium.detuning_mev
            )
            population = bose(ex, equilibrium.temperature_k) + fermi(
                et, equilibrium.temperature_k
            )
            delta_eta = eta / (np.pi * (mismatch * mismatch + eta * eta))
            total += wk * angle_weight * float(np.sum(delta_eta * population))
        output[index] = 0.5 * coupling_rate * total
    return output


def kubo_resistivity(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    hole_points: int = 96,
    hole_max_pf: float = 3.5,
    exciton_points: int = 96,
    exciton_max_pf: float = 4.5,
    angle_points: int = 128,
    broadening_mev: float | None = None,
) -> float:
    """Return normalized dc resistivity from Supplement Eqs. (39)-(40)."""

    if broadening_mev is None:
        broadening_mev = HBAR_MEV_PS / params.relaxation_time_ps
    p, weights = radial_grid(hole_points, hole_max_pf)
    rates = broadened_hole_rates(
        params,
        equilibrium,
        tunnel_mev,
        p,
        exciton_points,
        exciton_max_pf,
        angle_points,
        broadening_mev,
    )
    return resistivity_from_hole_rates(params, equilibrium, p, weights, rates)


def resistivity_from_hole_rates(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hole_nodes: np.ndarray,
    hole_weights: np.ndarray,
    rates_ps_inverse: np.ndarray,
) -> float:
    """Evaluate the printed relaxation-time conductivity for supplied rates."""

    eh = params.fermi_energy_mev * hole_nodes * hole_nodes - equilibrium.mu_h_mev
    fh = fermi(eh, equilibrium.temperature_k)
    thermal = fh * (1.0 - fh)
    tau_total = 1.0 / (1.0 / params.relaxation_time_ps + rates_ps_inverse)
    numerator = float(
        np.sum(hole_weights * thermal * hole_nodes * hole_nodes * tau_total)
    )
    denominator = float(
        np.sum(
            hole_weights * thermal * hole_nodes * hole_nodes * params.relaxation_time_ps
        )
    )
    sigma = (
        equilibrium.n_h_cm2
        / params.hole_reference_density_cm2
        * numerator
        / denominator
    )
    return float(1.0 / sigma)


def leading_order_boltzmann_resistivity(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    hole_points: int = 96,
    hole_max_pf: float = 3.5,
    exciton_points: int = 240,
    exciton_max_pf: float = 4.5,
) -> float:
    """Leading-order relaxation-time lane using the analytic delta root.

    This is deliberately *not* the full coupled Boltzmann result.  It evaluates
    the same leading self-energy used by Kubo, but replaces the broadened delta
    quadrature with the analytic on-shell root from Main Eq. (2).  Agreement as
    the Kubo broadening is narrowed diagnoses the regularization independently
    of the higher-order/vertex terms in the full three-species solve.
    """

    nodes, weights = radial_grid(hole_points, hole_max_pf)
    rates = np.array(
        [
            hole_scattering_rate(
                params,
                equilibrium,
                tunnel_mev,
                float(momentum),
                exciton_points,
                exciton_max_pf,
            )
            for momentum in nodes
        ],
        dtype=float,
    )
    return resistivity_from_hole_rates(params, equilibrium, nodes, weights, rates)
