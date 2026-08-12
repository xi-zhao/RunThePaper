"""Physical constants used by the independent hydrogen model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalConstants:
    """Small, explicit constant set with units in field names."""

    fine_structure: float
    rydberg_frequency_hz: float
    electron_proton_mass_ratio: float
    hartree_over_h_hz: float
    atomic_field_v_per_cm: float
    ground_hyperfine_hz: float
    speed_of_light_m_per_s: float

    @property
    def hydrogen_rydberg_frequency_hz(self) -> float:
        """Reduced-mass Rydberg frequency for ordinary hydrogen."""

        return self.rydberg_frequency_hz / (1.0 + self.electron_proton_mass_ratio)


CODATA2018 = PhysicalConstants(
    fine_structure=7.297_352_569_3e-3,
    rydberg_frequency_hz=3.289_841_960_250_8e15,
    electron_proton_mass_ratio=1.0 / 1836.152_673_43,
    hartree_over_h_hz=6.579_683_920_499e15,
    atomic_field_v_per_cm=5.142_206_747_63e9,
    ground_hyperfine_hz=1_420_405_751.768,
    speed_of_light_m_per_s=299_792_458.0,
)
