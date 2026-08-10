"""Paper-derived Hamiltonian and physical parameter mapping.

This module intentionally has no path or file access. All values enter through
the explicit run configuration copied into the isolated numerical bundle.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


HBAR = 1.054571817e-34
LIGHT_SPEED = 299_792_458.0


@dataclass(frozen=True)
class PaperParameters:
    wavelength_m: float
    radius_m: float
    refractive_index: float
    nonlinear_index_m2_per_w: float
    effective_volume_m3: float
    quality_factor: float
    weak_power_w: float
    strong_power_w: float
    dispersion_correction: float
    fock_cutoff: int

    @classmethod
    def from_mapping(cls, values: dict) -> "PaperParameters":
        parameters = cls(
            wavelength_m=float(values["wavelength_m"]),
            radius_m=float(values["radius_m"]),
            refractive_index=float(values["refractive_index"]),
            nonlinear_index_m2_per_w=float(values["nonlinear_index_m2_per_w"]),
            effective_volume_m3=float(values["effective_volume_m3"]),
            quality_factor=float(values["quality_factor"]),
            weak_power_w=float(values["weak_power_w"]),
            strong_power_w=float(values["strong_power_w"]),
            dispersion_correction=float(values["dispersion_correction"]),
            fock_cutoff=int(values["fock_cutoff"]),
        )
        parameters.validate()
        return parameters

    def validate(self) -> None:
        positive = {
            "wavelength_m": self.wavelength_m,
            "radius_m": self.radius_m,
            "refractive_index": self.refractive_index,
            "nonlinear_index_m2_per_w": self.nonlinear_index_m2_per_w,
            "effective_volume_m3": self.effective_volume_m3,
            "quality_factor": self.quality_factor,
            "weak_power_w": self.weak_power_w,
            "strong_power_w": self.strong_power_w,
        }
        invalid = [name for name, value in positive.items() if value <= 0.0]
        if invalid:
            raise ValueError(f"paper parameters must be positive: {invalid}")
        if not 0.0 <= self.dispersion_correction < 1.0:
            raise ValueError("dispersion_correction must lie in [0, 1)")
        if self.fock_cutoff < 6:
            raise ValueError("fock_cutoff must retain at least six Fock states")


@dataclass(frozen=True)
class PhysicalScales:
    omega0_rad_s: float
    gamma_rad_s: float
    kerr_u_rad_s: float
    fizeau_eta: float

    @property
    def u_over_gamma(self) -> float:
        return self.kerr_u_rad_s / self.gamma_rad_s


def physical_scales(parameters: PaperParameters) -> PhysicalScales:
    omega0 = 2.0 * np.pi * LIGHT_SPEED / parameters.wavelength_m
    gamma = omega0 / parameters.quality_factor
    kerr_u = (
        HBAR
        * omega0**2
        * LIGHT_SPEED
        * parameters.nonlinear_index_m2_per_w
        / (parameters.refractive_index**2 * parameters.effective_volume_m3)
    )
    fizeau_eta = (
        parameters.refractive_index
        * parameters.radius_m
        * omega0
        / LIGHT_SPEED
        * (1.0 - 1.0 / parameters.refractive_index**2 - parameters.dispersion_correction)
    )
    return PhysicalScales(
        omega0_rad_s=float(omega0),
        gamma_rad_s=float(gamma),
        kerr_u_rad_s=float(kerr_u),
        fizeau_eta=float(fizeau_eta),
    )


def operators(cutoff: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if cutoff < 2:
        raise ValueError("cutoff must be at least two")
    annihilation = np.diag(np.sqrt(np.arange(1, cutoff, dtype=float)), 1).astype(complex)
    creation = annihilation.conj().T
    number = creation @ annihilation
    return annihilation, creation, number


def delta_l_from_k(scales: PhysicalScales, k: float) -> float:
    return scales.kerr_u_rad_s * (1.0 - float(k))


def fizeau_shift(scales: PhysicalScales, direction: int, omega_khz: float) -> float:
    if direction not in {-1, 0, 1}:
        raise ValueError("direction must be -1, 0, or 1")
    return float(direction) * scales.fizeau_eta * float(omega_khz) * 1_000.0


def drive_amplitude(
    scales: PhysicalScales,
    k: float,
    input_power_w: float,
) -> float:
    delta_l = delta_l_from_k(scales, k)
    omega_l = scales.omega0_rad_s - delta_l
    if omega_l <= 0.0:
        raise ValueError("drive frequency must remain positive")
    return float(np.sqrt(scales.gamma_rad_s * input_power_w / (HBAR * omega_l)))


def hamiltonian(
    parameters: PaperParameters,
    scales: PhysicalScales,
    *,
    k: float,
    direction: int,
    omega_khz: float,
    input_power_w: float,
    cutoff: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return H/(hbar*gamma) and the dimensionless loss operator a."""

    dimension = int(cutoff or parameters.fock_cutoff)
    annihilation, creation, number = operators(dimension)
    detuning = delta_l_from_k(scales, k) + fizeau_shift(scales, direction, omega_khz)
    drive = drive_amplitude(scales, k, input_power_w)
    h_over_gamma = (
        (detuning / scales.gamma_rad_s) * number
        + (scales.kerr_u_rad_s / scales.gamma_rad_s) * (creation @ creation @ annihilation @ annihilation)
        + (drive / scales.gamma_rad_s) * (creation + annihilation)
    )
    return h_over_gamma, annihilation
