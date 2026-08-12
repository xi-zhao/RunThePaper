"""Independent numerics for arXiv:2105.08076.

The package is intentionally self-contained: it implements the printed model
and analysis contracts without author code, author arrays, or source images.
"""

from .gaussian import EnsembleResult, GaussianTrajectory, simulate_ensemble
from .theory import dark_state_exponents, infrared_kernel

__all__ = [
    "EnsembleResult",
    "GaussianTrajectory",
    "dark_state_exponents",
    "infrared_kernel",
    "simulate_ensemble",
]
