"""Declared scalar reconstructions of Fig. 1(c) and Supplement Fig. S7."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh


@dataclass(frozen=True)
class ModeResult:
    wavelength_um: float
    x_um: np.ndarray
    y_um: np.ndarray
    refractive_index: np.ndarray
    intensity: np.ndarray
    effective_index: float


def lnoi_extraordinary_index(wavelength_um: float) -> float:
    """Room-temperature extraordinary-index Sellmeier approximation."""

    wavelength_squared = float(wavelength_um) ** 2
    index_squared = (
        5.35583
        + 0.100473 / (wavelength_squared - 0.20692**2)
        + 100.0 / (wavelength_squared - 11.34927**2)
    )
    return float(np.sqrt(index_squared))


def silica_index(wavelength_um: float) -> float:
    """Fused-silica Sellmeier equation with wavelength in micrometres."""

    wavelength_squared = float(wavelength_um) ** 2
    terms = (
        0.6961663 * wavelength_squared / (wavelength_squared - 0.0684043**2)
        + 0.4079426 * wavelength_squared / (wavelength_squared - 0.1162414**2)
        + 0.8974794 * wavelength_squared / (wavelength_squared - 9.896161**2)
    )
    return float(np.sqrt(1.0 + terms))


def cross_section_index(
    wavelength_um: float,
    x_um: np.ndarray,
    y_um: np.ndarray,
    *,
    film_height_um: float,
    top_width_um: float,
    sidewall_angle_deg: float,
) -> np.ndarray:
    """Build an x-cut LNOI trapezoid on silica with air above."""

    x_mesh, y_mesh = np.meshgrid(x_um, y_um)
    indices = np.where(y_mesh < 0.0, silica_index(wavelength_um), 1.0)
    sidewall_expansion = film_height_um / np.tan(np.deg2rad(sidewall_angle_deg))
    normalized_height = np.clip(y_mesh / film_height_um, 0.0, 1.0)
    local_half_width = 0.5 * top_width_um + sidewall_expansion * (
        1.0 - normalized_height
    )
    lithium_niobate = (
        (y_mesh >= 0.0)
        & (y_mesh <= film_height_um)
        & (np.abs(x_mesh) <= local_half_width)
    )
    indices[lithium_niobate] = lnoi_extraordinary_index(wavelength_um)
    return indices


def solve_scalar_mode(
    wavelength_um: float,
    *,
    x_extent_um: float = 2.8,
    y_min_um: float = -1.0,
    y_max_um: float = 1.4,
    nx: int = 121,
    ny: int = 81,
    film_height_um: float = 0.3,
    top_width_um: float = 1.2,
    sidewall_angle_deg: float = 70.0,
) -> ModeResult:
    """Solve the fundamental scalar Helmholtz mode by finite differences."""

    if nx < 41 or ny < 41:
        raise ValueError("mode grid is too small")
    x_um = np.linspace(-x_extent_um, x_extent_um, nx)
    y_um = np.linspace(y_min_um, y_max_um, ny)
    dx = float(x_um[1] - x_um[0])
    dy = float(y_um[1] - y_um[0])
    indices = cross_section_index(
        wavelength_um,
        x_um,
        y_um,
        film_height_um=film_height_um,
        top_width_um=top_width_um,
        sidewall_angle_deg=sidewall_angle_deg,
    )
    d2x = (
        sparse.diags(
            [np.ones(nx - 1), -2.0 * np.ones(nx), np.ones(nx - 1)],
            offsets=[-1, 0, 1],
            format="csr",
        )
        / dx**2
    )
    d2y = (
        sparse.diags(
            [np.ones(ny - 1), -2.0 * np.ones(ny), np.ones(ny - 1)],
            offsets=[-1, 0, 1],
            format="csr",
        )
        / dy**2
    )
    laplacian = sparse.kron(sparse.eye(ny), d2x) + sparse.kron(d2y, sparse.eye(nx))
    vacuum_wave_number = 2.0 * np.pi / float(wavelength_um)
    operator = laplacian + sparse.diags(
        (vacuum_wave_number * indices.ravel()) ** 2,
        format="csr",
    )
    eigenvalues, eigenvectors = eigsh(operator, k=1, which="LA", tol=1e-9)
    beta_squared = float(eigenvalues[-1])
    if beta_squared <= 0.0:
        raise RuntimeError("mode solve returned nonphysical beta squared")
    field = eigenvectors[:, -1].reshape(ny, nx)
    intensity = np.abs(field) ** 2
    intensity /= float(np.sum(intensity) * dx * dy)
    effective_index = float(np.sqrt(beta_squared) / vacuum_wave_number)
    return ModeResult(
        wavelength_um=float(wavelength_um),
        x_um=x_um,
        y_um=y_um,
        refractive_index=indices,
        intensity=intensity,
        effective_index=effective_index,
    )


def electrode_loss_curve(
    mode: ModeResult,
    gaps_um: np.ndarray,
    *,
    top_width_um: float = 1.2,
    electrode_width_um: float = 1.0,
    electrode_height_um: float = 0.12,
    gold_n: float = 0.55,
    gold_k: float = 11.5,
) -> np.ndarray:
    """Estimate loss from modal overlap with a lateral gold electrode.

    This is a transparent perturbative reconstruction, not the paper's
    unpublished vector finite-element model.
    """

    gaps_um = np.asarray(gaps_um, dtype=float)
    if np.any(gaps_um <= 0.0):
        raise ValueError("electrode gaps must be positive")
    x_mesh, y_mesh = np.meshgrid(mode.x_um, mode.y_um)
    dx = float(mode.x_um[1] - mode.x_um[0])
    dy = float(mode.y_um[1] - mode.y_um[0])
    imaginary_permittivity = 2.0 * gold_n * gold_k
    vacuum_wave_number_per_m = 2.0 * np.pi / (mode.wavelength_um * 1e-6)
    absorption_scale_per_m = (
        vacuum_wave_number_per_m * imaginary_permittivity / (2.0 * mode.effective_index)
    )
    losses: list[float] = []
    for gap in gaps_um:
        inner_edge = 0.5 * top_width_um + float(gap)
        metal = (
            (x_mesh >= inner_edge)
            & (x_mesh <= inner_edge + electrode_width_um)
            & (y_mesh >= 0.3)
            & (y_mesh <= 0.3 + electrode_height_um)
        )
        overlap = float(np.sum(mode.intensity[metal]) * dx * dy)
        alpha_per_m = absorption_scale_per_m * overlap
        losses.append(4.343 * alpha_per_m / 1000.0)
    return np.asarray(losses)
