"""Formula-derived partial-wave recombination model and energy averaging."""

from __future__ import annotations

import numpy as np

from .polarization import CaptureTable
from .trap import (
    BA138_MASS_KG,
    BOLTZMANN_J_K,
    E_S_K,
    LI6_MASS_KG,
    energy_scale_frequency_hz,
)


def magnetic_detuning(
    magnetic_field_g: np.ndarray | float,
    resonance_field_g: float,
    relative_moment_mhz_g: float,
) -> np.ndarray:
    """Detuning energy in units of E_s from the printed delta-mu convention."""

    scale_mhz = energy_scale_frequency_hz(E_S_K) / 1.0e6
    return (
        relative_moment_mhz_g
        * (np.asarray(magnetic_field_g, dtype=float) - resonance_field_g)
        / scale_mhz
    )


def universal_rate_shape(
    energy_es: np.ndarray | float,
    table: CaptureTable,
    max_partial_wave: int | None = None,
) -> np.ndarray:
    """Dimensionless quantum-Langevin K(E), up to the unprinted absolute scale."""

    energy = np.asarray(energy_es, dtype=float)
    maximum = table.partial_waves - 1 if max_partial_wave is None else max_partial_wave
    if maximum >= table.partial_waves:
        raise ValueError("capture table lacks requested partial waves")
    total = np.zeros_like(energy)
    for partial_wave in range(maximum + 1):
        total += (2 * partial_wave + 1) * table.evaluate(energy, partial_wave)
    return total / np.sqrt(energy)


def normalized_universal_rate(
    energy_es: np.ndarray | float,
    table: CaptureTable,
    reference_energy_es: float = 1.0e-4,
) -> np.ndarray:
    reference = float(universal_rate_shape(reference_energy_es, table))
    return universal_rate_shape(energy_es, table) / reference


def resonant_cross_section_factor(
    energy_es: np.ndarray,
    detuning_es: np.ndarray,
    partial_wave: int,
    gamma_m_es_hbar: float,
    kn0_es_hbar: float,
    table: CaptureTable,
) -> np.ndarray:
    """Dimensionless sigma*n*v factor, preserving every term of the paper equation."""

    energy = np.asarray(energy_es, dtype=float)
    detuning = np.asarray(detuning_es, dtype=float)
    if np.any(energy <= 0) or gamma_m_es_hbar <= 0 or kn0_es_hbar <= 0:
        raise ValueError("energies and rates must be positive")
    gamma = gamma_m_es_hbar * table.evaluate(energy, partial_wave)
    kn = kn0_es_hbar * normalized_universal_rate(energy, table)
    denominator = (energy - detuning) ** 2 + 0.25 * (gamma + kn) ** 2
    return np.pi / np.sqrt(energy) * gamma * kn / denominator


def sample_three_body_energy(
    ion_velocities_m_s: np.ndarray,
    *,
    samples: int,
    seed: int,
    atom_temperature_k: float,
) -> np.ndarray:
    """Sample internal kinetic energy of one Ba+ and two independent Li atoms."""

    velocities = np.asarray(ion_velocities_m_s, dtype=float)
    if velocities.ndim != 2 or velocities.shape[1] != 3 or samples < 1:
        raise ValueError("ion velocities must be (N,3) and samples positive")
    rng = np.random.default_rng(seed)
    ion = velocities[rng.integers(0, velocities.shape[0], size=samples)]
    atom_sigma = np.sqrt(BOLTZMANN_J_K * atom_temperature_k / LI6_MASS_KG)
    atom_one = rng.normal(scale=atom_sigma, size=(samples, 3))
    atom_two = rng.normal(scale=atom_sigma, size=(samples, 3))
    total_mass = BA138_MASS_KG + 2.0 * LI6_MASS_KG
    center = (
        BA138_MASS_KG * ion + LI6_MASS_KG * atom_one + LI6_MASS_KG * atom_two
    ) / total_mass
    energy_j = (
        0.5 * BA138_MASS_KG * np.sum((ion - center) ** 2, axis=1)
        + 0.5 * LI6_MASS_KG * np.sum((atom_one - center) ** 2, axis=1)
        + 0.5 * LI6_MASS_KG * np.sum((atom_two - center) ** 2, axis=1)
    )
    return np.maximum(energy_j / (BOLTZMANN_J_K * E_S_K), 1.0e-12)


def average_loss_spectrum(
    energy_samples_es: np.ndarray,
    magnetic_field_g: np.ndarray,
    *,
    partial_wave: int,
    gamma_m_es_hbar: float,
    kn0_es_hbar: float,
    resonance_field_g: float,
    relative_moment_mhz_g: float,
    table: CaptureTable,
    rate_scale_s: float,
    chunk_size: int = 4096,
) -> np.ndarray:
    """Average the printed cross section over an independently sampled distribution."""

    energies = np.asarray(energy_samples_es, dtype=float)
    fields = np.asarray(magnetic_field_g, dtype=float)
    detuning = magnetic_detuning(fields, resonance_field_g, relative_moment_mhz_g)
    accumulated = np.zeros(fields.shape, dtype=float)
    for start in range(0, energies.size, chunk_size):
        current = energies[start : start + chunk_size, None]
        values = resonant_cross_section_factor(
            current,
            detuning[None, :],
            partial_wave,
            gamma_m_es_hbar,
            kn0_es_hbar,
            table,
        )
        accumulated += np.sum(values, axis=0)
    return rate_scale_s * accumulated / energies.size


def survival_from_rate(rate_s: np.ndarray, interaction_time_s: float) -> np.ndarray:
    return np.exp(
        -np.maximum(np.asarray(rate_s, dtype=float), 0.0) * interaction_time_s
    )


def peak_properties(
    magnetic_field_g: np.ndarray, rate_s: np.ndarray
) -> tuple[float, float]:
    fields = np.asarray(magnetic_field_g, dtype=float)
    rates = np.asarray(rate_s, dtype=float)
    index = int(np.argmax(rates))
    if 0 < index < rates.size - 1:
        x = fields[index - 1 : index + 2]
        y = rates[index - 1 : index + 2]
        coefficients = np.polyfit(x, y, 2)
        if coefficients[0] < 0:
            position = float(-coefficients[1] / (2.0 * coefficients[0]))
            peak = float(np.polyval(coefficients, position))
            return position, peak
    return float(fields[index]), float(rates[index])
