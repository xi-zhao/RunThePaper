"""Independent event-driven atom-ion collision ensemble.

The paper's Julia trajectory code and microscopic launch parameters are not
public.  This module implements the declared physical invariants without using
author code or arrays: thermal Li atoms, 3D elastic COM scattering, random rf
phase, radial excess micromotion, and a stationary median ion energy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import kurtosis

from .trap import BA138_MASS_KG, BOLTZMANN_J_K, LI6_MASS_KG


@dataclass(frozen=True)
class MDSamples:
    field_v_m: float
    velocities_m_s: np.ndarray
    effective_temperature_k: np.ndarray
    median_temperature_k: float
    radial_kurtosis: float
    axial_kurtosis: float
    stationary_relative_drift: float


def _unit_vectors(rng: np.random.Generator, count: int) -> np.ndarray:
    directions = rng.normal(size=(count, 3))
    norms = np.linalg.norm(directions, axis=1)
    while np.any(norms == 0):
        directions[norms == 0] = rng.normal(size=(int(np.sum(norms == 0)), 3))
        norms = np.linalg.norm(directions, axis=1)
    return directions / norms[:, None]


def elastic_collision_update(
    ion_velocity: np.ndarray,
    atom_velocity: np.ndarray,
    outgoing_direction: np.ndarray,
    ion_mass_kg: float = BA138_MASS_KG,
    atom_mass_kg: float = LI6_MASS_KG,
) -> np.ndarray:
    """Isotropic elastic scattering in the two-body center-of-mass frame."""

    ion = np.asarray(ion_velocity, dtype=float)
    atom = np.asarray(atom_velocity, dtype=float)
    direction = np.asarray(outgoing_direction, dtype=float)
    if ion.shape != atom.shape or ion.shape != direction.shape or ion.shape[-1] != 3:
        raise ValueError("velocity and direction arrays must share shape (..., 3)")
    direction_norm = np.linalg.norm(direction, axis=-1)
    if np.any(direction_norm == 0):
        raise ValueError("outgoing directions must be nonzero")
    direction = direction / direction_norm[..., None]
    center = (ion_mass_kg * ion + atom_mass_kg * atom) / (ion_mass_kg + atom_mass_kg)
    relative_speed = np.linalg.norm(ion - atom, axis=-1)
    return center + atom_mass_kg / (ion_mass_kg + atom_mass_kg) * (
        relative_speed[..., None] * direction
    )


def collision_conservation_residual(
    ion_velocity: np.ndarray,
    atom_velocity: np.ndarray,
    outgoing_direction: np.ndarray,
) -> float:
    """Maximum relative momentum/energy residual for the full two-body update."""

    ion = np.asarray(ion_velocity, dtype=float)
    atom = np.asarray(atom_velocity, dtype=float)
    direction = np.asarray(outgoing_direction, dtype=float)
    direction /= np.linalg.norm(direction, axis=-1)[..., None]
    center = (BA138_MASS_KG * ion + LI6_MASS_KG * atom) / (BA138_MASS_KG + LI6_MASS_KG)
    relative_speed = np.linalg.norm(ion - atom, axis=-1)
    ion_after = center + LI6_MASS_KG / (BA138_MASS_KG + LI6_MASS_KG) * (
        relative_speed[..., None] * direction
    )
    atom_after = center - BA138_MASS_KG / (BA138_MASS_KG + LI6_MASS_KG) * (
        relative_speed[..., None] * direction
    )
    momentum_before = BA138_MASS_KG * ion + LI6_MASS_KG * atom
    momentum_after = BA138_MASS_KG * ion_after + LI6_MASS_KG * atom_after
    energy_before = 0.5 * BA138_MASS_KG * np.sum(
        ion**2, axis=-1
    ) + 0.5 * LI6_MASS_KG * np.sum(atom**2, axis=-1)
    energy_after = 0.5 * BA138_MASS_KG * np.sum(
        ion_after**2, axis=-1
    ) + 0.5 * LI6_MASS_KG * np.sum(atom_after**2, axis=-1)
    momentum_scale = np.maximum(np.linalg.norm(momentum_before, axis=-1), 1e-30)
    energy_scale = np.maximum(np.abs(energy_before), 1e-30)
    momentum_residual = (
        np.linalg.norm(momentum_after - momentum_before, axis=-1) / momentum_scale
    )
    energy_residual = np.abs(energy_after - energy_before) / energy_scale
    return float(max(np.max(momentum_residual), np.max(energy_residual)))


def _median_secular_temperature(velocity: np.ndarray) -> float:
    temperature = BA138_MASS_KG * np.sum(velocity**2, axis=1) / (3.0 * BOLTZMANN_J_K)
    return float(np.median(temperature))


def simulate_collision_ensemble(
    *,
    field_v_m: float,
    trajectories: int,
    collisions: int,
    seed: int,
    bath_temperature_k: float,
    background_temperature_k: float,
    drive_alpha_k_per_v_m2: float,
) -> MDSamples:
    """Generate one stationary ion ensemble at a declared displacement field."""

    if trajectories < 128 or collisions < 8:
        raise ValueError("at least 128 trajectories and 8 collisions are required")
    if min(bath_temperature_k, background_temperature_k, drive_alpha_k_per_v_m2) < 0:
        raise ValueError("temperatures and drive coefficient must be nonnegative")
    rng = np.random.default_rng(seed)
    atom_sigma = np.sqrt(BOLTZMANN_J_K * bath_temperature_k / LI6_MASS_KG)
    ion_sigma = np.sqrt(BOLTZMANN_J_K * bath_temperature_k / BA138_MASS_KG)
    background_sigma = np.sqrt(BOLTZMANN_J_K * background_temperature_k / BA138_MASS_KG)
    # For a sinusoid the median of sin^2 is 1/2.  This amplitude therefore
    # maps the quoted effective-temperature coefficient onto E/(3 k_B/2).
    drive_amplitude_per_field = np.sqrt(
        6.0 * BOLTZMANN_J_K * drive_alpha_k_per_v_m2 / BA138_MASS_KG
    )
    secular = rng.normal(scale=ion_sigma, size=(trajectories, 3))
    checkpoint_temperature = np.nan
    checkpoint_step = max(1, int(0.8 * collisions))
    for step in range(collisions):
        phase = rng.uniform(0.0, 2.0 * np.pi, trajectories)
        micromotion = drive_amplitude_per_field * field_v_m * np.sin(phase)
        instantaneous = secular.copy()
        instantaneous[:, 0] += micromotion
        atom = rng.normal(scale=atom_sigma, size=(trajectories, 3))
        instantaneous_after = elastic_collision_update(
            instantaneous, atom, _unit_vectors(rng, trajectories)
        )
        secular = instantaneous_after
        secular[:, 0] -= micromotion
        if step + 1 == checkpoint_step:
            checkpoint_temperature = _median_secular_temperature(secular)

    observation_phase = rng.uniform(0.0, 2.0 * np.pi, trajectories)
    observed = secular + rng.normal(scale=background_sigma, size=(trajectories, 3))
    observed[:, 0] += drive_amplitude_per_field * field_v_m * np.sin(observation_phase)
    temperature = BA138_MASS_KG * np.sum(observed**2, axis=1) / (3.0 * BOLTZMANN_J_K)
    final_secular_temperature = _median_secular_temperature(secular)
    drift = abs(final_secular_temperature - checkpoint_temperature) / max(
        final_secular_temperature, 1e-30
    )
    return MDSamples(
        field_v_m=float(field_v_m),
        velocities_m_s=observed,
        effective_temperature_k=temperature,
        median_temperature_k=float(np.median(temperature)),
        radial_kurtosis=float(kurtosis(observed[:, 0], fisher=False, bias=False)),
        axial_kurtosis=float(kurtosis(observed[:, 2], fisher=False, bias=False)),
        stationary_relative_drift=float(drift),
    )


def fit_energy_scaling(ensembles: list[MDSamples]) -> tuple[float, float, float]:
    """Fit median effective temperature = intercept + alpha * field^2."""

    if len(ensembles) < 3:
        raise ValueError("at least three fields are required")
    fields = np.asarray([item.field_v_m for item in ensembles], dtype=float)
    medians = np.asarray([item.median_temperature_k for item in ensembles], dtype=float)
    design = np.column_stack([np.ones_like(fields), fields**2])
    coefficients, _, _, _ = np.linalg.lstsq(design, medians, rcond=None)
    prediction = design @ coefficients
    relative_rms = float(
        np.sqrt(np.mean((prediction - medians) ** 2)) / max(np.ptp(medians), 1e-30)
    )
    return float(coefficients[0]), float(coefficients[1]), relative_rms


def velocity_histogram(
    velocities_m_s: np.ndarray,
    component: int,
    bins: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    velocity = np.asarray(velocities_m_s, dtype=float)
    edges = np.asarray(bins, dtype=float)
    density, edges = np.histogram(velocity[:, component], bins=edges, density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return centers, density


def gaussian_velocity_density(grid: np.ndarray, samples: np.ndarray) -> np.ndarray:
    sigma = float(np.std(samples, ddof=1))
    if sigma <= 0:
        raise ValueError("velocity sample has zero variance")
    return np.exp(-0.5 * (np.asarray(grid) / sigma) ** 2) / (
        np.sqrt(2.0 * np.pi) * sigma
    )
