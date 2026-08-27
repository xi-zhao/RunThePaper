"""Clean-room optical analogue Hawking-radiation model."""

from .analysis import (
    conjugated_spm_contribution,
    figure2_landmarks,
    phase_matching_from_angular_frequencies,
    phase_matching_markers,
    stimulated_signal,
)
from .model import PropagationConfig, PulseSpec, SimulationGrid
from .physical_dispersion import CleanRoomPCFDispersion, PCFGeometry
from .solver import AnalyticSignalUPPE, PropagationResult, build_counterfactual_batch
from .theory import (
    SidebandFit,
    SidebandParameters,
    fit_sideband_spectrum,
    hawking_peak_profile,
    sideband_spectrum,
    thermal_line_fit,
)

__all__ = [
    "AnalyticSignalUPPE",
    "CleanRoomPCFDispersion",
    "PCFGeometry",
    "PropagationConfig",
    "PropagationResult",
    "PulseSpec",
    "SimulationGrid",
    "SidebandFit",
    "SidebandParameters",
    "build_counterfactual_batch",
    "conjugated_spm_contribution",
    "figure2_landmarks",
    "phase_matching_from_angular_frequencies",
    "fit_sideband_spectrum",
    "hawking_peak_profile",
    "phase_matching_markers",
    "sideband_spectrum",
    "stimulated_signal",
    "thermal_line_fit",
]
