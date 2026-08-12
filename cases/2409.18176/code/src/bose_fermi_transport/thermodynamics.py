"""Ideal-gas thermodynamics for the effective hole/exciton/trion model.

All public energies use meV, temperatures use kelvin, masses are multiples of
the electron mass, and areal densities use cm^-2.  The numerical implementation
is derived from the quadratic dispersions printed around main Eq. (1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

KB_MEV_PER_K = 8.617333262e-2
HBAR_MEV_PS = 0.6582119569
HBAR_SI = 1.054571817e-34
ELECTRON_MASS_KG = 9.1093837015e-31
MEV_J = 1.602176634e-22


@dataclass(frozen=True)
class ModelParameters:
    """Paper parameters needed by all numerical lanes."""

    fermi_energy_mev: float = 5.0
    trion_binding_mev: float = -10.0
    hole_mass_me: float = 0.5
    exciton_mass_ratio_to_hole: float = 2.0
    exciton_density_cm2: float = 2.0e11
    relaxation_time_ps: float = 10.0

    @property
    def exciton_mass_me(self) -> float:
        return self.hole_mass_me * self.exciton_mass_ratio_to_hole

    @property
    def trion_mass_me(self) -> float:
        return self.hole_mass_me + self.exciton_mass_me

    @property
    def hole_reference_density_cm2(self) -> float:
        """Zero-temperature density associated with the printed Fermi energy."""

        mass_kg = self.hole_mass_me * ELECTRON_MASS_KG
        return (
            mass_kg * self.fermi_energy_mev * MEV_J / (2.0 * np.pi * HBAR_SI**2) / 1.0e4
        )


@dataclass(frozen=True)
class EquilibriumState:
    temperature_k: float
    detuning_mev: float
    mu_h_mev: float
    mu_x_mev: float
    mu_t_mev: float
    n_h_cm2: float
    n_x_cm2: float
    n_t_cm2: float
    closure: str
    residual_max: float


def _thermal_prefactor_cm2(mass_me: float, temperature_k: float) -> float:
    mass_kg = mass_me * ELECTRON_MASS_KG
    kt_mev = KB_MEV_PER_K * temperature_k
    return mass_kg * kt_mev * MEV_J / (2.0 * np.pi * HBAR_SI**2) / 1.0e4


def fermi_density_cm2(mass_me: float, mu_mev: float, temperature_k: float) -> float:
    """Density of one nondegenerate two-dimensional Fermi species."""

    kt = KB_MEV_PER_K * temperature_k
    return float(
        _thermal_prefactor_cm2(mass_me, temperature_k) * np.logaddexp(0.0, mu_mev / kt)
    )


def bose_density_cm2(mass_me: float, mu_mev: float, temperature_k: float) -> float:
    """Density of a normal ideal two-dimensional Bose gas (mu < 0)."""

    kt = KB_MEV_PER_K * temperature_k
    scaled_mu = min(mu_mev / kt, -1.0e-14)
    return float(
        -_thermal_prefactor_cm2(mass_me, temperature_k) * np.log1p(-np.exp(scaled_mu))
    )


def bose_chemical_potential_mev(
    mass_me: float, density_cm2: float, temperature_k: float
) -> float:
    """Analytic inversion of the two-dimensional Bose density."""

    prefactor = _thermal_prefactor_cm2(mass_me, temperature_k)
    argument = -density_cm2 / prefactor
    return float(KB_MEV_PER_K * temperature_k * np.log(-np.expm1(argument)))


def fermi(energy_mev: np.ndarray | float, temperature_k: float) -> np.ndarray:
    scaled = np.asarray(energy_mev, dtype=float) / (KB_MEV_PER_K * temperature_k)
    scaled = np.clip(scaled, -700.0, 700.0)
    return 1.0 / (np.exp(scaled) + 1.0)


def bose(energy_mev: np.ndarray | float, temperature_k: float) -> np.ndarray:
    scaled = np.asarray(energy_mev, dtype=float) / (KB_MEV_PER_K * temperature_k)
    scaled = np.maximum(scaled, 1.0e-12)
    return 1.0 / np.expm1(np.minimum(scaled, 700.0))


def solve_equilibrium(
    params: ModelParameters,
    temperature_k: float,
    detuning_mev: float,
    closure: str = "fixed_free",
) -> EquilibriumState:
    """Close the three chemical potentials without author data.

    ``fixed_free`` is the primary interpretation: the printed hole Fermi energy
    fixes ``mu_h`` and the printed exciton density fixes ``mu_x``.  The trion
    chemical potential then follows from chemical equilibrium.  ``conserved``
    is retained as a sensitivity lane in which total hole and exciton
    constituents are fixed instead.
    """

    if temperature_k <= 0.0:
        raise ValueError("temperature_k must be positive")
    mu_h = params.fermi_energy_mev
    mu_x = bose_chemical_potential_mev(
        params.exciton_mass_me, params.exciton_density_cm2, temperature_k
    )

    if closure == "fixed_free":
        mu_t = mu_h + mu_x
        n_h = fermi_density_cm2(params.hole_mass_me, mu_h, temperature_k)
        n_x = bose_density_cm2(params.exciton_mass_me, mu_x, temperature_k)
        n_t = fermi_density_cm2(
            params.trion_mass_me, mu_t - detuning_mev, temperature_k
        )
        residual = max(
            abs((mu_h + mu_x) - mu_t),
            abs(n_x - params.exciton_density_cm2) / params.exciton_density_cm2,
        )
    elif closure == "conserved":
        target_h = params.hole_reference_density_cm2
        target_x = params.exciton_density_cm2

        def residuals(mus: np.ndarray) -> np.ndarray:
            trial_h, trial_x = (float(mus[0]), float(mus[1]))
            trial_t = fermi_density_cm2(
                params.trion_mass_me,
                trial_h + trial_x - detuning_mev,
                temperature_k,
            )
            return np.array(
                [
                    (
                        fermi_density_cm2(params.hole_mass_me, trial_h, temperature_k)
                        + trial_t
                        - target_h
                    )
                    / target_h,
                    (
                        bose_density_cm2(params.exciton_mass_me, trial_x, temperature_k)
                        + trial_t
                        - target_x
                    )
                    / target_x,
                ]
            )

        result = least_squares(
            residuals,
            np.array([mu_h, mu_x]),
            bounds=(np.array([-50.0, -50.0]), np.array([50.0, -1.0e-12])),
            xtol=1.0e-13,
            ftol=1.0e-13,
            gtol=1.0e-13,
            max_nfev=1000,
        )
        if not result.success:
            raise RuntimeError(f"equilibrium solve failed: {result.message}")
        mu_h, mu_x = (float(result.x[0]), float(result.x[1]))
        mu_t = mu_h + mu_x
        n_t = fermi_density_cm2(
            params.trion_mass_me, mu_t - detuning_mev, temperature_k
        )
        n_h = fermi_density_cm2(params.hole_mass_me, mu_h, temperature_k)
        n_x = bose_density_cm2(params.exciton_mass_me, mu_x, temperature_k)
        residual = float(np.max(np.abs(residuals(result.x))))
    else:
        raise ValueError(f"unknown closure: {closure}")

    return EquilibriumState(
        temperature_k=float(temperature_k),
        detuning_mev=float(detuning_mev),
        mu_h_mev=float(mu_h),
        mu_x_mev=float(mu_x),
        mu_t_mev=float(mu_t),
        n_h_cm2=float(n_h),
        n_x_cm2=float(n_x),
        n_t_cm2=float(n_t),
        closure=closure,
        residual_max=float(residual),
    )
