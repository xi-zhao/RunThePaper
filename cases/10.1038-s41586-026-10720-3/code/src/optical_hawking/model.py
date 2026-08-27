"""Domain objects and paper presets for the reproduction.

The core state is the positive-laboratory-frequency analytic signal.  A
propagation step is the only state transition.  Grid, pulse, and solver
parameters are immutable so a run can be audited from its serialized config.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import torch


C_NM_PER_FS = 299.792458
C_MM_PER_FS = C_NM_PER_FS * 1.0e-6


def angular_frequency_from_wavelength_nm(wavelength_nm: float) -> float:
    """Return angular frequency in rad/fs."""

    return 2.0 * torch.pi * C_NM_PER_FS / wavelength_nm


def wavelength_nm_from_angular_frequency(omega_rad_fs: float) -> float:
    """Return vacuum wavelength in nm."""

    return 2.0 * torch.pi * C_NM_PER_FS / omega_rad_fs


@dataclass(frozen=True)
class PulseSpec:
    wavelength_nm: float
    intensity_fwhm_fs: float
    average_power_w: float
    repetition_rate_hz: float = 80.0e6
    delay_fs: float = 0.0
    phase_rad: float = 0.0

    @property
    def omega_rad_fs(self) -> float:
        return angular_frequency_from_wavelength_nm(self.wavelength_nm)

    @property
    def sech_width_fs(self) -> float:
        # I(t) = P0 sech^2(t/T0), whose intensity FWHM is 1.76275 T0.
        return self.intensity_fwhm_fs / 1.762747174

    @property
    def pulse_energy_w_fs(self) -> float:
        return self.average_power_w * 1.0e15 / self.repetition_rate_hz

    @property
    def peak_power_w(self) -> float:
        return self.pulse_energy_w_fs / (2.0 * self.sech_width_fs)

    def field(self, time_fs: torch.Tensor, complex_dtype: torch.dtype) -> torch.Tensor:
        shifted = time_fs - self.delay_fs
        envelope = torch.sqrt(
            torch.as_tensor(self.peak_power_w, device=time_fs.device, dtype=time_fs.dtype)
        ) / torch.cosh(shifted / self.sech_width_fs)
        phase = self.omega_rad_fs * shifted + self.phase_rad
        return envelope.to(complex_dtype) * torch.exp(1j * phase.to(complex_dtype))


@dataclass(frozen=True)
class SimulationGrid:
    points: int
    omega_max_rad_fs: float = 16.2

    def validate(self) -> None:
        if self.points < 64 or self.points & (self.points - 1):
            raise ValueError("points must be a power of two and at least 64")
        if self.omega_max_rad_fs <= 0:
            raise ValueError("omega_max_rad_fs must be positive")

    @property
    def dt_fs(self) -> float:
        return float(torch.pi / self.omega_max_rad_fs)

    @property
    def time_window_fs(self) -> float:
        return self.points * self.dt_fs

    def tensors(
        self, device: torch.device, real_dtype: torch.dtype
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        self.validate()
        dt = self.dt_fs
        time = (
            torch.arange(self.points, device=device, dtype=real_dtype) - self.points // 2
        ) * dt
        omega = 2.0 * torch.pi * torch.fft.fftfreq(
            self.points, d=dt, device=device, dtype=real_dtype
        )
        return time, omega, omega > 0


@dataclass(frozen=True)
class PropagationConfig:
    length_mm: float
    step_mm: float
    integrator: str = "ifrk4"
    gamma_spm_w_inv_mm: float = 1.0e-4
    frame_velocity_over_c: float = 0.665
    precision: str = "complex64"
    compile_step: bool = False
    record_snapshots: int = 5

    def validate(self) -> None:
        if self.length_mm <= 0 or self.step_mm <= 0:
            raise ValueError("length_mm and step_mm must be positive")
        ratio = self.length_mm / self.step_mm
        if abs(ratio - round(ratio)) > 1.0e-9:
            raise ValueError("length_mm must be an integer multiple of step_mm")
        if self.integrator not in {"ifrk4", "dopri5"}:
            raise ValueError("integrator must be 'ifrk4' or 'dopri5'")
        if self.precision not in {"complex64", "complex128"}:
            raise ValueError("precision must be complex64 or complex128")
        if not 0 < self.frame_velocity_over_c < 1:
            raise ValueError("frame_velocity_over_c must lie between zero and one")

    @property
    def steps(self) -> int:
        return round(self.length_mm / self.step_mm)

    @property
    def complex_dtype(self) -> torch.dtype:
        return torch.complex64 if self.precision == "complex64" else torch.complex128

    @property
    def real_dtype(self) -> torch.dtype:
        return torch.float32 if self.precision == "complex64" else torch.float64

    @property
    def frame_velocity_mm_fs(self) -> float:
        return self.frame_velocity_over_c * C_MM_PER_FS

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


PAPER_PUMP = PulseSpec(
    wavelength_nm=800.0,
    intensity_fwhm_fs=8.0,
    average_power_w=45.0e-3,
)

PAPER_PROBE_1400 = PulseSpec(
    wavelength_nm=1400.0,
    intensity_fwhm_fs=30.0,
    average_power_w=4.0e-3,
)

PAPER_GRID = SimulationGrid(points=2**16, omega_max_rad_fs=16.2)

PAPER_PROPAGATION = PropagationConfig(
    length_mm=7.0,
    step_mm=0.0005,
    integrator="dopri5",
    precision="complex64",
)

A100_FAST_PROPAGATION = PropagationConfig(
    length_mm=7.0,
    step_mm=0.001,
    integrator="ifrk4",
    precision="complex64",
    compile_step=True,
)
