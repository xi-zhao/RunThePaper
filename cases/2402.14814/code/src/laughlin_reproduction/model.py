"""Formula-derived model for the two-fermion Laughlin state.

This module never reads paper figures, author code, or author numerical arrays.
The density and correlation routines follow the printed wavefunction exactly.
The interaction-spectrum routine is a documented reconstruction because the
paper does not print the full coupled-channel map or drive calibration.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.constants import hbar, physical_constants, pi
from scipy.linalg import eigh
from scipy.optimize import brentq
from scipy.special import factorial, gamma


@dataclass(frozen=True)
class TrapParameters:
    radial_frequency_khz: float
    axial_frequency_khz: float
    lithium_mass_u: float
    tweezer_waist_um: float
    background_scattering_length_a0: float
    resonance_field_g: float
    width_g: float
    confinement_constant: float = 1.4603

    @property
    def aspect_ratio(self) -> float:
        return self.axial_frequency_khz / self.radial_frequency_khz

    @property
    def radial_oscillator_length_um(self) -> float:
        atomic_mass = physical_constants["atomic mass constant"][0]
        mass = self.lithium_mass_u * atomic_mass
        omega = 2.0 * pi * self.radial_frequency_khz * 1.0e3
        return float(np.sqrt(hbar / (mass * omega)) * 1.0e6)

    @property
    def quartic_alpha(self) -> float:
        """Paper's dimensionless single-particle quartic coefficient."""

        ratio = self.radial_oscillator_length_um / self.tweezer_waist_um
        return -0.5 * ratio**2


def ho_energy(n: int, m: int, rotation_ratio: float) -> float:
    """Return E/(hbar*omega) for the rotating 2D harmonic oscillator."""

    if n < 0 or abs(m) > n or (n - abs(m)) % 2:
        raise ValueError("m must be an allowed angular momentum in shell n")
    return float(n + 1 - m * rotation_ratio)


def ho_spectrum(n_max: int, rotation_ratio: float) -> list[tuple[int, int, float]]:
    rows: list[tuple[int, int, float]] = []
    for n in range(n_max + 1):
        for m in range(-n, n + 1, 2):
            rows.append((n, m, ho_energy(n, m, rotation_ratio)))
    return rows


def ho_density_2d(m: int, px: np.ndarray, py: np.ndarray) -> np.ndarray:
    """Normalized lowest-Landau-level |m> probability density."""

    if m < 0:
        raise ValueError("This LLL density implementation requires m >= 0")
    radius2 = np.asarray(px) ** 2 + np.asarray(py) ** 2
    return radius2**m * np.exp(-radius2) / (np.pi * factorial(m, exact=False))


def laughlin_single_particle_density(px: np.ndarray, py: np.ndarray) -> np.ndarray:
    """One-particle marginal from Eq. (2b): weights 1/4, 1/2, 1/4."""

    return (
        0.25 * ho_density_2d(0, px, py)
        + 0.50 * ho_density_2d(1, px, py)
        + 0.25 * ho_density_2d(2, px, py)
    )


def radial_density_units(m: int, radius: np.ndarray) -> np.ndarray:
    """2D density in the paper's units 1/(2*pi*p_HO^2)."""

    radius = np.asarray(radius, dtype=float)
    return 2.0 * radius ** (2 * m) * np.exp(-(radius**2)) / factorial(m, exact=False)


def laughlin_single_particle_radial(radius: np.ndarray) -> np.ndarray:
    return (
        0.25 * radial_density_units(0, radius)
        + 0.50 * radial_density_units(1, radius)
        + 0.25 * radial_density_units(2, radius)
    )


def angle_correlation(phi: np.ndarray) -> np.ndarray:
    """Printed m=2 relative-angle correlation g_{1/2}(phi)."""

    phi = np.asarray(phi, dtype=float)
    return (6.0 - 3.0 * np.pi * np.cos(phi) + 4.0 * np.cos(phi) ** 2) / (16.0 * np.pi)


def rabi_occupation(
    time_ms: np.ndarray,
    rabi_rate_khz: float,
    observable_min: float = 0.5,
    observable_max: float = 2.0,
) -> np.ndarray:
    """Ideal resonant Rabi prediction for the measured ground occupation."""

    time_ms = np.asarray(time_ms, dtype=float)
    midpoint = 0.5 * (observable_max + observable_min)
    amplitude = 0.5 * (observable_max - observable_min)
    return midpoint + amplitude * np.cos(2.0 * np.pi * rabi_rate_khz * time_ms)


def ramsey_occupation(
    time_ms: np.ndarray,
    frequency_hz: float,
    coherence_ms: float,
    contrast: float = 1.0,
) -> np.ndarray:
    """Unit-contrast damped two-level Ramsey prediction."""

    time_ms = np.asarray(time_ms, dtype=float)
    phase = 2.0 * np.pi * frequency_hz * time_ms * 1.0e-3
    return 1.0 + contrast * np.exp(-time_ms / coherence_ms) * np.cos(phase)


def evolving_relative_density(
    px: np.ndarray,
    py: np.ndarray,
    fraction_of_period: float,
) -> np.ndarray:
    """Density of coherent |+2> <-> |-2> evolution at a period fraction."""

    px = np.asarray(px, dtype=float)
    py = np.asarray(py, dtype=float)
    radius2 = px**2 + py**2
    phi = np.arctan2(py, px)
    theta = 2.0 * np.pi * fraction_of_period
    coefficient_plus = np.cos(0.5 * theta)
    coefficient_minus = -1j * np.sin(0.5 * theta)
    radial_amplitude = radius2 * np.exp(-0.5 * radius2) / np.sqrt(2.0 * np.pi)
    angular_amplitude = coefficient_plus * np.exp(
        2j * phi
    ) + coefficient_minus * np.exp(-2j * phi)
    return np.abs(radial_amplitude * angular_amplitude) ** 2


def feshbach_scattering_length_um(field_g: float, trap: TrapParameters) -> float:
    """Broad 6Li |1>-|2> resonance parameterization from published constants."""

    bohr_radius_um = physical_constants["Bohr radius"][0] * 1.0e6
    factor = 1.0 + trap.width_g / (field_g - trap.resonance_field_g)
    return trap.background_scattering_length_a0 * factor * bohr_radius_um


def effective_1d_coupling(field_g: float, trap: TrapParameters) -> float:
    """Dimensionless Olshanii coupling for the reconstructed axial problem."""

    atomic_mass = physical_constants["atomic mass constant"][0]
    mass = trap.lithium_mass_u * atomic_mass
    omega_r = 2.0 * pi * trap.radial_frequency_khz * 1.0e3
    omega_z = 2.0 * pi * trap.axial_frequency_khz * 1.0e3
    a_perp_um = np.sqrt(2.0 * hbar / (mass * omega_r)) * 1.0e6
    a_z_um = np.sqrt(2.0 * hbar / (mass * omega_z)) * 1.0e6
    scattering_length = feshbach_scattering_length_um(field_g, trap)
    denominator = 1.0 - trap.confinement_constant * scattering_length / a_perp_um
    return float(2.0 * scattering_length * a_z_um / (a_perp_um**2 * denominator))


def _even_1d_energy(coupling: float) -> float:
    if abs(coupling) < 1.0e-12:
        return 0.5

    def equation(energy: float) -> float:
        ratio = -2.0 * gamma(0.75 - 0.5 * energy) / gamma(0.25 - 0.5 * energy)
        return float(ratio - coupling)

    if coupling > 0.0:
        return float(brentq(equation, 0.500000001, 1.499999999))
    return float(brentq(equation, -40.0, 0.499999999))


def interaction_shift(field_g: float, trap: TrapParameters) -> float:
    """Reconstructed repulsive-branch shift in units of hbar*omega_radial."""

    coupling = effective_1d_coupling(field_g, trap)
    axial_energy = _even_1d_energy(coupling)
    return trap.aspect_ratio * (axial_energy - 0.5)


def two_particle_spectrum(
    field_g: float,
    trap: TrapParameters,
    *,
    anharmonic: bool,
) -> dict[str, np.ndarray | float]:
    """Lowest M=0,2,4 levels in harmonic or quartic Gaussian model."""

    interaction = interaction_shift(field_g, trap)
    if not anharmonic:
        return {
            "m0": interaction,
            "m2": np.sort(np.array([2.0, 2.0 + interaction])),
            "m4": np.sort(np.array([4.0, 4.0, 4.0 + interaction])),
        }

    alpha = trap.quartic_alpha
    ground = interaction + 4.0 * alpha

    h2 = np.array(
        [
            [2.0 + 13.0 * alpha, alpha],
            [alpha, 2.0 + 13.0 * alpha + interaction],
        ]
    )

    transform = np.array(
        [
            [np.sqrt(1.0 / 8.0), np.sqrt(3.0) / 2.0, np.sqrt(1.0 / 8.0)],
            [1.0 / np.sqrt(2.0), 0.0, -1.0 / np.sqrt(2.0)],
            [np.sqrt(3.0 / 8.0), -0.5, np.sqrt(3.0 / 8.0)],
        ]
    )
    h4_quartic = transform.T @ np.diag([32.0, 26.0, 24.0]) @ transform * alpha
    h4 = 4.0 * np.eye(3) + h4_quartic + np.diag([0.0, 0.0, interaction])
    return {"m0": ground, "m2": eigvalsh(h2), "m4": eigvalsh(h4)}


def eigvalsh(matrix: np.ndarray) -> np.ndarray:
    return np.linalg.eigvalsh(np.asarray(matrix, dtype=float))


def driven_occupation(
    field_g: float,
    excitation_frequency_ratio: float,
    duration_ms: float,
    rabi_rate_khz: float,
    trap: TrapParameters,
) -> float:
    """Three-state rotating-frame prediction for Supplement Fig. S2(c)."""

    spectrum = two_particle_spectrum(field_g, trap, anharmonic=True)
    ground = float(spectrum["m0"])
    alpha = trap.quartic_alpha
    interaction = interaction_shift(field_g, trap)
    excited = np.array(
        [
            [2.0 + 13.0 * alpha - ground, alpha],
            [alpha, 2.0 + 13.0 * alpha + interaction - ground],
        ]
    )
    excited -= excitation_frequency_ratio * np.eye(2)
    coupling = rabi_rate_khz / (2.0 * trap.radial_frequency_khz)
    hamiltonian = np.zeros((3, 3), dtype=float)
    hamiltonian[1:, 1:] = excited
    hamiltonian[0, 1:] = coupling / np.sqrt(2.0)
    hamiltonian[1:, 0] = coupling / np.sqrt(2.0)
    values, vectors = eigh(hamiltonian)
    time_dimensionless = 2.0 * np.pi * trap.radial_frequency_khz * duration_ms
    initial = np.array([1.0, 0.0, 0.0], dtype=complex)
    amplitudes = vectors.T.conj() @ initial
    evolved = vectors @ (np.exp(-1j * values * time_dimensionless) * amplitudes)
    observable = np.diag([2.0, 0.5, 1.0])
    return float(np.real(evolved.conj() @ observable @ evolved))


def gaussian_profile(coordinate_um: np.ndarray, sigma_um: float) -> np.ndarray:
    coordinate_um = np.asarray(coordinate_um, dtype=float)
    return np.exp(-0.5 * (coordinate_um / sigma_um) ** 2)
