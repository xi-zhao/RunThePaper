"""Independent numerical model for arXiv:2401.05830.

The package implements only equations derived from the paper text.  It does
not read author code, author arrays, PDFs, reference figures, or pixel data.
"""

from .model import (
    bifurcation_temperature,
    crossing_metrics,
    distance_to_final,
    modal_coefficients,
    preparation_parameters,
    propagate_bloch,
    relaxation_rates,
    slow_mode_coefficient,
    steady_state,
    strong_initial_temperature,
)

__all__ = [
    "bifurcation_temperature",
    "crossing_metrics",
    "distance_to_final",
    "modal_coefficients",
    "preparation_parameters",
    "propagate_bloch",
    "relaxation_rates",
    "slow_mode_coefficient",
    "steady_state",
    "strong_initial_temperature",
]
