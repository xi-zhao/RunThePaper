"""Printed three-fluid ac model and an independent direct matrix solution."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .thermodynamics import HBAR_MEV_PS, EquilibriumState, ModelParameters


@dataclass(frozen=True)
class HydroParameters:
    tau_h_ps: float = 9.4
    tau_x_ps: float = 10.0
    tau_t_ps: float = 2.9
    alpha_th: float = 0.64
    alpha_xh: float = -0.48
    alpha_tx: float = 0.50
    density_unit_cm2: float = 1.0e12
    mass_unit_me: float = 0.25
    time_unit_ps: float = 10.0


def _scaled_inputs(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hydro: HydroParameters,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    density = (
        np.array(
            [equilibrium.n_h_cm2, equilibrium.n_x_cm2, equilibrium.n_t_cm2], dtype=float
        )
        / hydro.density_unit_cm2
    )
    mass = (
        np.array(
            [params.hole_mass_me, params.exciton_mass_me, params.trion_mass_me],
            dtype=float,
        )
        / hydro.mass_unit_me
    )
    alpha = {
        "xh": hydro.alpha_xh / hydro.time_unit_ps,
        "th": hydro.alpha_th / hydro.time_unit_ps,
        "tx": hydro.alpha_tx / hydro.time_unit_ps,
    }
    return density, mass, alpha


def conductivities_direct(
    frequency_mev: np.ndarray,
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hydro: HydroParameters,
) -> np.ndarray:
    """Solve the three velocity equations as a complex 3x3 system."""

    frequencies = np.asarray(frequency_mev, dtype=float)
    density, mass, alpha = _scaled_inputs(params, equilibrium, hydro)
    nh, nx, nt = density
    mh, mx, mt = mass
    output = np.empty((len(frequencies), 3), dtype=complex)
    for index, energy in enumerate(frequencies):
        omega = energy / HBAR_MEV_PS
        matrix = np.array(
            [
                [
                    1.0 / hydro.tau_h_ps
                    + 1j * omega
                    + alpha["th"] * nt / mh
                    + alpha["xh"] * nx / mh,
                    -alpha["xh"] * nx / mh,
                    -alpha["th"] * nt / mh,
                ],
                [
                    -alpha["xh"] * nh / mx,
                    1.0 / hydro.tau_x_ps
                    + 1j * omega
                    + alpha["tx"] * nt / mx
                    + alpha["xh"] * nh / mx,
                    -alpha["tx"] * nt / mx,
                ],
                [
                    -alpha["th"] * nh / mt,
                    -alpha["tx"] * nx / mt,
                    1.0 / hydro.tau_t_ps
                    + 1j * omega
                    + alpha["th"] * nh / mt
                    + alpha["tx"] * nx / mt,
                ],
            ],
            dtype=complex,
        )
        velocities = np.linalg.solve(matrix, np.array([1.0 / mh, 0.0, 0.0]))
        output[index] = (
            density
            / (params.hole_reference_density_cm2 / hydro.density_unit_cm2)
            * velocities
            * mh
            / params.relaxation_time_ps
        )
    return output


def conductivities_closed(
    frequency_mev: np.ndarray,
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hydro: HydroParameters,
) -> np.ndarray:
    """Evaluate the dimensionally corrected elimination of the velocity system.

    The printed Supplement Eqs. (41)-(43) omit ``1/m_bar`` in the nested
    denominators.  Restoring those factors makes the closed form exactly equal
    to the main-text velocity equations.  ``conductivities_printed_closed``
    retains the literal source expression for falsification.
    """

    return _conductivities_closed_impl(
        frequency_mev,
        params,
        equilibrium,
        hydro,
        literal_printed_denominator=False,
    )


def conductivities_printed_closed(
    frequency_mev: np.ndarray,
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hydro: HydroParameters,
) -> np.ndarray:
    """Evaluate Supplement Eqs. (41)-(43) exactly as typeset."""

    return _conductivities_closed_impl(
        frequency_mev,
        params,
        equilibrium,
        hydro,
        literal_printed_denominator=True,
    )


def _conductivities_closed_impl(
    frequency_mev: np.ndarray,
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hydro: HydroParameters,
    literal_printed_denominator: bool,
) -> np.ndarray:

    frequencies = np.asarray(frequency_mev, dtype=float)
    density, mass, alpha = _scaled_inputs(params, equilibrium, hydro)
    nh, nx, nt = density
    mh, mx, mt = mass
    taus = {"h": hydro.tau_h_ps, "x": hydro.tau_x_ps, "t": hydro.tau_t_ps}
    ns = {"h": nh, "x": nx, "t": nt}
    ms = {"h": mh, "x": mx, "t": mt}
    alpha_ih = {"x": alpha["xh"], "t": alpha["th"]}
    other = {"x": "t", "t": "x"}
    alpha_other_h = {"x": alpha["th"], "t": alpha["xh"]}
    output = np.empty((len(frequencies), 3), dtype=complex)
    norm_density = params.hole_reference_density_cm2 / hydro.density_unit_cm2
    for index, energy in enumerate(frequencies):
        omega = energy / HBAR_MEV_PS
        a: dict[str, complex] = {}
        b: dict[str, complex] = {}
        c: dict[str, complex] = {}
        for species in ("x", "t"):
            partner = other[species]
            if literal_printed_denominator:
                shared = (
                    alpha_other_h[species] * nh
                    + alpha["tx"] * ns[species]
                    + 1j * omega
                    + 1.0 / taus[partner]
                )
                nested_mass = 1.0
            else:
                shared = (
                    alpha_other_h[species] * nh / ms[partner]
                    + alpha["tx"] * ns[species] / ms[partner]
                    + 1j * omega
                    + 1.0 / taus[partner]
                )
                nested_mass = ms[partner]
            a[species] = alpha_ih[species] * nh / ms[species] + (
                alpha_other_h[species]
                * alpha["tx"]
                * ns[partner]
                * nh
                / ms[species]
                / nested_mass
                / shared
            )
            b[species] = (
                alpha["tx"] * ns[partner] / ms[species]
                + alpha_ih[species] * nh / ms[species]
                - alpha["tx"] ** 2 * nx * nt / ms[species] / nested_mass / shared
            )
            c[species] = alpha_ih[species] * ns[species] / mh
        sigma_h = (
            (nh / norm_density)
            / params.relaxation_time_ps
            / (
                1.0 / hydro.tau_h_ps
                + 1j * omega
                + sum(
                    c[species]
                    * (
                        1.0
                        - a[species] / (1j * omega + 1.0 / taus[species] + b[species])
                    )
                    for species in ("x", "t")
                )
            )
        )
        sigma_x = a["x"] / (1j * omega + 1.0 / taus["x"] + b["x"]) * nx / nh * sigma_h
        sigma_t = a["t"] / (1j * omega + 1.0 / taus["t"] + b["t"]) * nt / nh * sigma_h
        output[index] = (sigma_h, sigma_x, sigma_t)
    return output
