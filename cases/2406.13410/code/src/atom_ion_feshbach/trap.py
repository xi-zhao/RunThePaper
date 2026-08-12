"""Printed trap relations and physical constants."""

from __future__ import annotations

import numpy as np

ELEMENTARY_CHARGE_C = 1.602176634e-19
ATOMIC_MASS_KG = 1.66053906660e-27
BOLTZMANN_J_K = 1.380649e-23
PLANCK_J_S = 6.62607015e-34
HBAR_J_S = PLANCK_J_S / (2.0 * np.pi)

LI6_MASS_KG = 6.0 * ATOMIC_MASS_KG
BA138_MASS_KG = 138.0 * ATOMIC_MASS_KG
E_S_K = 8.8e-6
ION_S_WAVE_EXCESS_K = 195.0e-6


def quadratic_energy(
    field_v_m: np.ndarray | float,
    minimum_temperature_k: float,
    alpha_k_per_v_m2: float,
) -> np.ndarray:
    """Return E_ion/(3 k_B/2), expressed as an effective temperature."""

    field = np.asarray(field_v_m, dtype=float)
    return minimum_temperature_k + alpha_k_per_v_m2 * field**2


def field_to_displacement(
    field_v_m: np.ndarray | float,
    secular_frequency_hz: float,
    ion_mass_kg: float = BA138_MASS_KG,
) -> np.ndarray:
    """Static equilibrium displacement of a singly charged harmonic ion."""

    if secular_frequency_hz <= 0 or ion_mass_kg <= 0:
        raise ValueError("frequency and mass must be positive")
    omega = 2.0 * np.pi * secular_frequency_hz
    return (
        ELEMENTARY_CHARGE_C
        * np.asarray(field_v_m, dtype=float)
        / (ion_mass_kg * omega**2)
    )


def displacement_to_field(
    displacement_m: np.ndarray | float,
    secular_frequency_hz: float,
    ion_mass_kg: float = BA138_MASS_KG,
) -> np.ndarray:
    omega = 2.0 * np.pi * secular_frequency_hz
    return (
        np.asarray(displacement_m, dtype=float)
        * ion_mass_kg
        * omega**2
        / ELEMENTARY_CHARGE_C
    )


def micromotion_alpha(
    mathieu_a: float,
    mathieu_q: float,
    drive_frequency_hz: float,
    ion_mass_kg: float = BA138_MASS_KG,
) -> float:
    """Appendix isolated-ion coefficient in joule per (V/m)^2."""

    omega_rf = 2.0 * np.pi * drive_frequency_hz
    denominator = (2.0 * mathieu_a + mathieu_q**2) * omega_rf
    if denominator == 0:
        raise ValueError("Mathieu response denominator is zero")
    return 4.0 / ion_mass_kg * (ELEMENTARY_CHARGE_C * mathieu_q / denominator) ** 2


def energy_scale_frequency_hz(energy_temperature_k: float = E_S_K) -> float:
    return BOLTZMANN_J_K * energy_temperature_k / PLANCK_J_S
