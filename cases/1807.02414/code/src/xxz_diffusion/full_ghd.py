"""Full spectral diffusion operator and linearized GHD evolution.

This module implements the non-diagonal operator printed around Eqs. (9),
(12), and (13).  It advances the complete rapidity/species perturbation rather
than replacing the operator by a fitted scalar spin diffusivity.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .backend import array_module, to_numpy
from .tba import StationaryState


def spectral_diffusion_operator(state: StationaryState) -> np.ndarray:
    """Discretize the paper's full ``D_tilde(theta, alpha)`` operator.

    With midpoint weight ``dλ``, the integral operator is

    ``D_ij = [w_i δ_ij - dλ W_ij] / rho_s(i)^2``

    where ``W_ij = rho_p(i) f(i) Tdr_ij^2 |v_i-v_j|`` and
    ``w_i = dλ sum_j W_ji``.  Species are folded into the mode index.
    """

    points = state.rapidity.size
    fillings = np.repeat(state.fillings, points)
    thermal = 1.0 - fillings
    velocity_difference = np.abs(state.velocity[:, None] - state.velocity[None, :])
    w_kernel = (
        (state.particle_density * thermal)[:, None]
        * np.square(state.dressed_scattering)
        * velocity_difference
    )
    integrated_incoming = state.quadrature_weight * np.sum(w_kernel, axis=0)
    numerator = np.diag(integrated_incoming) - state.quadrature_weight * w_kernel
    return numerator / np.square(state.total_density)[:, None]


def magnetic_linear_response_vectors(
    state: StationaryState,
) -> tuple[np.ndarray, np.ndarray]:
    """Return initial occupation response and magnetization readout vectors."""

    points = state.rapidity.size
    fillings = np.repeat(state.fillings, points)
    occupation_response = fillings * (1.0 - fillings) * state.dressed_spin
    magnetization_readout = (
        state.total_density * state.dressed_spin * state.quadrature_weight
    )
    return occupation_response, magnetization_readout


def evolve_linearized_full_ghd(
    state: StationaryState,
    *,
    x: np.ndarray,
    times: list[float],
    time_step: float,
    backend: str = "numpy",
) -> dict[str, Any]:
    """Solve Eq. (13) by Fourier-space Strang splitting.

    Advection is diagonal in quasiparticle mode and the full diffusion operator
    is diagonalized once.  The evolution retains only requested magnetization
    snapshots and works with NumPy or optional CuPy.
    """

    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or x.size < 16:
        raise ValueError("x must be a one-dimensional grid with at least 16 points")
    spacing = np.diff(x)
    if not np.allclose(spacing, spacing[0], rtol=1.0e-12, atol=1.0e-14):
        raise ValueError("x must be uniformly spaced")
    if time_step <= 0.0:
        raise ValueError("time_step must be positive")
    sorted_times = sorted(float(value) for value in times)
    target_steps: dict[int, float] = {}
    for target_time in sorted_times:
        step_float = target_time / float(time_step)
        step = int(round(step_float))
        if target_time <= 0.0 or abs(step_float - step) > 1.0e-9:
            raise ValueError("each positive target time must be an integer multiple of dt")
        target_steps[step] = target_time

    diffusion = spectral_diffusion_operator(state)
    occupation_response, readout = magnetic_linear_response_vectors(state)
    xp = array_module(backend)
    diffusion_xp = xp.asarray(diffusion)
    eigenvalues, eigenvectors = xp.linalg.eig(diffusion_xp)
    inverse_eigenvectors = xp.linalg.inv(eigenvectors)
    wavenumbers = 2.0 * np.pi * np.fft.fftfreq(x.size, d=float(spacing[0]))
    k_xp = xp.asarray(wavenumbers)
    initial_sign = np.where(x < 0.0, 1.0, -1.0)
    modes = xp.asarray(occupation_response[:, None] * initial_sign[None, :])
    fourier_modes = xp.fft.fft(modes, axis=1)
    velocity = xp.asarray(state.velocity[:, None])
    half_diffusion_factor = xp.exp(
        -0.25 * float(time_step) * eigenvalues[:, None] * xp.square(k_xp)[None, :]
    )
    advection_factor = xp.exp(
        -1j * float(time_step) * velocity * k_xp[None, :]
    )
    readout_xp = xp.asarray(readout)

    profiles: dict[float, np.ndarray] = {}
    maximum_imaginary_residual = 0.0
    for step in range(1, max(target_steps) + 1):
        eigen_coordinates = inverse_eigenvectors @ fourier_modes
        fourier_modes = eigenvectors @ (half_diffusion_factor * eigen_coordinates)
        fourier_modes *= advection_factor
        eigen_coordinates = inverse_eigenvectors @ fourier_modes
        fourier_modes = eigenvectors @ (half_diffusion_factor * eigen_coordinates)
        if step in target_steps:
            mode_snapshot = xp.fft.ifft(fourier_modes, axis=1)
            magnetization = readout_xp @ mode_snapshot
            host = to_numpy(magnetization)
            maximum_imaginary_residual = max(
                maximum_imaginary_residual, float(np.max(np.abs(host.imag)))
            )
            profiles[target_steps[step]] = np.asarray(host.real)

    eigenvalues_host = to_numpy(eigenvalues)
    plateau = float(readout @ occupation_response)
    return {
        "times": np.asarray(sorted_times),
        "magnetization_over_mu": np.stack([profiles[time] for time in sorted_times]),
        "susceptibility_plateau": plateau,
        "diffusion_operator": diffusion,
        "diffusion_eigenvalue_real_min": float(np.min(eigenvalues_host.real)),
        "diffusion_eigenvalue_imag_max": float(np.max(np.abs(eigenvalues_host.imag))),
        "maximum_profile_imaginary_residual": maximum_imaginary_residual,
    }
