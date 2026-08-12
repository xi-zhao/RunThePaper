"""Spectral, layer-character, continuation, and surface-energy observables."""

from __future__ import annotations

import numpy as np

from .lattice import LayeredPDModel, lattice_green_function, layer_diagonal


def spectral_observables(
    model: LayeredPDModel,
    omega: np.ndarray,
    layer_sigma: np.ndarray,
    *,
    chemical_potential: float,
    broadening: float,
) -> dict[str, np.ndarray]:
    """Evaluate k-resolved and orbital-resolved retarded spectral functions."""

    energies = np.asarray(omega, dtype=float)
    if broadening <= 0.0:
        raise ValueError("broadening must be positive")
    green_k, local_matrix = lattice_green_function(
        model,
        energies + 1j * broadening,
        layer_sigma,
        chemical_potential=chemical_potential,
    )
    d_green, p_green = layer_diagonal(model, local_matrix)
    return {
        "omega": energies,
        "kpoints": model.kpoints,
        "a_k": -np.imag(np.trace(green_k, axis1=-2, axis2=-1)) / np.pi,
        "d_dos": -np.imag(d_green) / np.pi,
        "p_dos": -np.imag(p_green) / np.pi,
        "total_dos": -np.imag(np.trace(local_matrix, axis1=-2, axis2=-1)) / np.pi,
    }


def integrated_spectral_weight(omega: np.ndarray, spectral: np.ndarray) -> np.ndarray:
    return np.trapezoid(np.asarray(spectral), np.asarray(omega), axis=0)


def band_gap(
    omega: np.ndarray,
    density: np.ndarray,
    *,
    threshold_fraction: float = 0.02,
) -> float:
    """Extract a thresholded gap around zero from a nonnegative spectrum."""

    energies = np.asarray(omega, dtype=float)
    dos = np.asarray(density, dtype=float)
    if energies.ndim != 1 or dos.shape != energies.shape:
        raise ValueError("omega and density must be one-dimensional and aligned")
    threshold = threshold_fraction * float(np.max(dos))
    occupied = energies[(energies < 0.0) & (dos > threshold)]
    empty = energies[(energies > 0.0) & (dos > threshold)]
    if occupied.size == 0 or empty.size == 0:
        return float("nan")
    return float(np.min(empty) - np.max(occupied))


def layer_character_fraction(
    omega: np.ndarray,
    d_dos: np.ndarray,
    p_dos: np.ndarray,
    *,
    window: tuple[float, float],
) -> np.ndarray:
    """Return the O-p fraction of spectral weight in an energy window."""

    energies = np.asarray(omega, dtype=float)
    d_values = np.asarray(d_dos, dtype=float)
    p_values = np.asarray(p_dos, dtype=float)
    if d_values.shape != p_values.shape or d_values.shape[0] != energies.size:
        raise ValueError("orbital spectra are not aligned")
    mask = (energies >= window[0]) & (energies <= window[1])
    if np.count_nonzero(mask) < 2:
        raise ValueError("character window contains fewer than two samples")
    d_weight = np.trapezoid(d_values[mask], energies[mask], axis=0)
    p_weight = np.trapezoid(p_values[mask], energies[mask], axis=0)
    return p_weight / np.maximum(d_weight + p_weight, 1e-14)


def surface_energy(
    slab_energy_ev: float,
    *,
    formula_units: int,
    bulk_energy_ev_per_formula: float,
    surface_area_angstrom2: float,
    equivalent_surfaces: int = 2,
) -> float:
    """Return gamma in meV/Angstrom^2 from the paper's slab formula."""

    if formula_units < 1 or surface_area_angstrom2 <= 0.0:
        raise ValueError("formula_units and surface area must be positive")
    if equivalent_surfaces not in {1, 2}:
        raise ValueError("equivalent_surfaces must be one or two")
    excess_ev = slab_energy_ev - formula_units * bulk_energy_ev_per_formula
    return 1000.0 * excess_ev / (equivalent_surfaces * surface_area_angstrom2)


def imaginary_time_symmetry_error(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    return float(np.max(np.abs(array - array[::-1])))


def rational_continue(
    z_input: np.ndarray,
    values: np.ndarray,
    z_output: np.ndarray,
    *,
    numerator_degree: int,
    denominator_degree: int,
    regularization: float = 1e-12,
) -> np.ndarray:
    """Least-squares rational continuation used as a Pade-style cross-check.

    The function rescales the complex frequency before solving
    ``f(z) Q(z) = P(z)`` with ``Q(0)=1``. It is an independent diagnostic; the
    paper-scale contract still requires MaxEnt/Pade agreement and uncertainty.
    """

    z_in = np.asarray(z_input, dtype=np.complex128)
    f_in = np.asarray(values, dtype=np.complex128)
    z_out = np.asarray(z_output, dtype=np.complex128)
    if z_in.ndim != 1 or f_in.shape != z_in.shape:
        raise ValueError("input frequencies and values must be aligned vectors")
    if numerator_degree < 0 or denominator_degree < 0:
        raise ValueError("rational degrees must be nonnegative")
    unknowns = numerator_degree + 1 + denominator_degree
    if z_in.size < unknowns:
        raise ValueError("insufficient samples for requested rational degrees")
    scale = max(float(np.max(np.abs(z_in))), 1.0)
    x = z_in / scale
    numerator = np.column_stack([x**power for power in range(numerator_degree + 1)])
    denominator = np.column_stack(
        [-f_in * x**power for power in range(1, denominator_degree + 1)]
    )
    design = np.column_stack([numerator, denominator])
    gram = design.conj().T @ design + regularization * np.eye(unknowns)
    coefficients = np.linalg.solve(gram, design.conj().T @ f_in)
    x_out = z_out / scale
    p = sum(coefficients[power] * x_out**power for power in range(numerator_degree + 1))
    q = np.ones_like(x_out)
    offset = numerator_degree + 1
    for power in range(1, denominator_degree + 1):
        q += coefficients[offset + power - 1] * x_out**power
    return p / q
