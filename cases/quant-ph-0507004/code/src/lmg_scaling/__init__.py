"""Independent numerical model for the LMG large-N scaling paper."""

from .model import (
    SectorSpectrum,
    classical_ground_energy,
    classical_minimum_mu,
    critical_excitation_spectrum,
    exceptional_point_certificate,
    lmg_sector,
    separatrix_action,
    separatrix_spacing,
    super_scar_record,
    theory_separatrix_coefficient,
    wkb_separatrix_index,
)

__all__ = [
    "SectorSpectrum",
    "classical_ground_energy",
    "classical_minimum_mu",
    "critical_excitation_spectrum",
    "exceptional_point_certificate",
    "lmg_sector",
    "separatrix_spacing",
    "separatrix_action",
    "super_scar_record",
    "theory_separatrix_coefficient",
    "wkb_separatrix_index",
]
