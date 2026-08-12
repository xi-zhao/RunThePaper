"""Independent scientific implementation for arXiv:2406.07531."""

from .baths import (
    combine_embedding_basis,
    density_matrix_bath,
    green_function_bath,
    natural_orbital_bath,
)
from .embedding import (
    combine_gw_ibdet,
    democratic_assembly,
    local_only_correction,
    project_hamiltonian,
    rotate_self_energy,
)
from .spectra import density_of_states, spectral_function

__all__ = [
    "combine_embedding_basis",
    "combine_gw_ibdet",
    "democratic_assembly",
    "density_matrix_bath",
    "density_of_states",
    "green_function_bath",
    "local_only_correction",
    "natural_orbital_bath",
    "project_hamiltonian",
    "rotate_self_energy",
    "spectral_function",
]
