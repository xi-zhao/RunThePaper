"""Clean-room exact-diagonalization tools for arXiv:cond-mat/0610854."""

from .hamiltonian import FermionChain, fixed_particle_basis
from .statistics import adjacent_gap_ratios, crossing_estimates, poisson_density

__all__ = [
    "FermionChain",
    "adjacent_gap_ratios",
    "crossing_estimates",
    "fixed_particle_basis",
    "poisson_density",
]
