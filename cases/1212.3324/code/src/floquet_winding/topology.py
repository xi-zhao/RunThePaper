"""Gauge-aware Chern and full-evolution winding calculations."""

from __future__ import annotations

import numpy as np

from .model import (
    IDENTITY_2,
    SIGMA_Z,
    square_bloch_evolution,
    square_floquet_bloch,
    weak_bloch_hamiltonian,
    weak_floquet_bloch,
)


def _normalized_overlap(left: np.ndarray, right: np.ndarray) -> complex:
    value = np.vdot(left, right)
    magnitude = abs(value)
    if magnitude < 1e-14:
        raise ValueError("neighboring eigenvectors have vanishing overlap")
    return value / magnitude


def fukui_chern(
    states: np.ndarray,
    *,
    seam_gauge_x: np.ndarray | None = None,
    seam_gauge_y: np.ndarray | None = None,
    orientation: float = 1.0,
) -> float:
    """Calculate a one-band Chern number on a periodic two-dimensional mesh."""

    nx, ny, _ = states.shape
    link_x = np.empty((nx, ny), dtype=complex)
    link_y = np.empty((nx, ny), dtype=complex)
    for ix in range(nx):
        for iy in range(ny):
            state_x = states[(ix + 1) % nx, iy]
            state_y = states[ix, (iy + 1) % ny]
            if ix == nx - 1 and seam_gauge_x is not None:
                state_x = seam_gauge_x @ state_x
            if iy == ny - 1 and seam_gauge_y is not None:
                state_y = seam_gauge_y @ state_y
            link_x[ix, iy] = _normalized_overlap(states[ix, iy], state_x)
            link_y[ix, iy] = _normalized_overlap(states[ix, iy], state_y)
    plaquette = (
        link_x
        * np.roll(link_y, -1, axis=0)
        / (np.roll(link_x, -1, axis=1) * link_y)
    )
    return float(orientation * np.angle(plaquette).sum() / (2.0 * np.pi))


def square_floquet_chern(
    hopping: float,
    sublattice: float,
    *,
    grid_points: int,
    period: float = 1.0,
) -> float:
    coordinates = np.linspace(-np.pi, np.pi, grid_points, endpoint=False)
    states = np.empty((grid_points, grid_points, 2), dtype=complex)
    for ix, q1 in enumerate(coordinates):
        for iy, q2 in enumerate(coordinates):
            operator = square_floquet_bloch(
                q1, q2, hopping, sublattice, period=period
            )
            values, vectors = np.linalg.eig(operator)
            energies = -np.angle(values) / period
            upper = int(np.argmax(energies))
            states[ix, iy] = vectors[:, upper] / np.linalg.norm(vectors[:, upper])
    # q1,q2 have the opposite orientation to kx,ky, and a 2pi seam flips
    # the off-diagonal Bloch elements.  Both facts are part of the Bloch gauge.
    return fukui_chern(
        states,
        seam_gauge_x=SIGMA_Z,
        seam_gauge_y=SIGMA_Z,
        orientation=-1.0,
    )


def square_bulk_gaps(
    hopping: float,
    sublattice: float,
    *,
    grid_points: int,
    period: float = 1.0,
) -> tuple[float, float]:
    coordinates = np.linspace(-np.pi, np.pi, grid_points, endpoint=False)
    gap_zero = np.inf
    gap_pi = np.inf
    for q1 in coordinates:
        for q2 in coordinates:
            values = np.linalg.eigvals(
                square_floquet_bloch(q1, q2, hopping, sublattice, period=period)
            )
            energies = np.sort(-np.angle(values) / period)
            half_separation = 0.5 * float(energies[1] - energies[0])
            gap_zero = min(gap_zero, half_separation)
            gap_pi = min(gap_pi, np.pi / period - half_separation)
    return float(gap_zero), float(gap_pi)


def _effective_hamiltonian(
    operator: np.ndarray, gap_energy: float, period: float
) -> np.ndarray:
    values, vectors = np.linalg.eig(operator)
    energies = -np.angle(values) / period
    lower_boundary = gap_energy - 2.0 * np.pi / period
    energies = np.where(energies >= gap_energy - 1e-10, energies - 2.0 * np.pi / period, energies)
    if np.any(energies < lower_boundary - 1e-8):
        raise ValueError("branch-cut energy left the selected quasienergy zone")
    result = vectors @ np.diag(energies) @ np.linalg.inv(vectors)
    return 0.5 * (result + result.conjugate().T)


def _gauge_periodic_centered_difference(
    values: np.ndarray,
    *,
    axis: int,
    spacing: float,
    seam_gauge: np.ndarray,
) -> np.ndarray:
    """Differentiate a matrix field across a gauge-periodic torus seam.

    The square-lattice Bloch basis changes by ``seam_gauge`` after either
    primitive reciprocal coordinate advances by ``2*pi``.  Consequently a
    matrix sampled on the opposite edge must be transported into the local
    basis before a finite difference is formed.  Treating the array as simply
    periodic compares matrices written in different bases and produces a
    spurious boundary contribution to the winding integral.
    """

    forward = np.roll(values, -1, axis=axis).copy()
    backward = np.roll(values, 1, axis=axis).copy()
    high = [slice(None)] * values.ndim
    low = [slice(None)] * values.ndim
    high[axis] = -1
    low[axis] = 0
    gauge_dagger = seam_gauge.conjugate().T
    forward[tuple(high)] = (
        seam_gauge @ forward[tuple(high)] @ gauge_dagger
    )
    backward[tuple(low)] = (
        seam_gauge @ backward[tuple(low)] @ gauge_dagger
    )
    return (forward - backward) / (2.0 * spacing)


def square_winding_number(
    hopping: float,
    sublattice: float,
    gap_energy: float,
    *,
    momentum_points: int,
    time_points: int,
    period: float = 1.0,
) -> float:
    """Discretize Eq. (4) for the closed return-map evolution."""

    coordinates = np.linspace(-np.pi, np.pi, momentum_points, endpoint=False)
    times = np.linspace(0.0, period, time_points, endpoint=False)
    evolution = np.empty(
        (time_points, momentum_points, momentum_points, 2, 2), dtype=complex
    )
    effective = np.empty((momentum_points, momentum_points, 2, 2), dtype=complex)
    for ix, q1 in enumerate(coordinates):
        for iy, q2 in enumerate(coordinates):
            floquet = square_floquet_bloch(
                q1, q2, hopping, sublattice, period=period
            )
            effective[ix, iy] = _effective_hamiltonian(
                floquet, gap_energy, period
            )
    for it, time in enumerate(times):
        if time <= period / 2.0:
            for ix, q1 in enumerate(coordinates):
                for iy, q2 in enumerate(coordinates):
                    evolution[it, ix, iy] = square_bloch_evolution(
                        q1,
                        q2,
                        hopping,
                        sublattice,
                        2.0 * time,
                        period=period,
                    )
        else:
            return_time = 2.0 * period - 2.0 * time
            for ix in range(momentum_points):
                for iy in range(momentum_points):
                    values, vectors = np.linalg.eigh(effective[ix, iy])
                    evolution[it, ix, iy] = vectors @ np.diag(
                        np.exp(-1.0j * values * return_time)
                    ) @ vectors.conjugate().T

    dt = period / time_points
    dq = 2.0 * np.pi / momentum_points
    derivative_t = (np.roll(evolution, -1, axis=0) - np.roll(evolution, 1, axis=0)) / (2.0 * dt)
    derivative_x = _gauge_periodic_centered_difference(
        evolution,
        axis=1,
        spacing=dq,
        seam_gauge=SIGMA_Z,
    )
    derivative_y = _gauge_periodic_centered_difference(
        evolution,
        axis=2,
        spacing=dq,
        seam_gauge=SIGMA_Z,
    )
    inverse = evolution.conjugate().swapaxes(-1, -2)
    a_t = inverse @ derivative_t
    a_x = inverse @ derivative_x
    a_y = inverse @ derivative_y
    commutator = a_x @ a_y - a_y @ a_x
    integrand = np.trace(a_t @ commutator, axis1=-2, axis2=-1)
    raw = float((integrand.sum() * dt * dq * dq / (8.0 * np.pi**2)).real)
    # The primitive q torus has the opposite orientation to Cartesian k.
    return -raw


def weak_static_chern(
    *,
    mu: float,
    hopping: float,
    mass_curvature: float,
    spin_orbit: float,
    grid_points: int,
) -> float:
    coordinates = np.linspace(-np.pi, np.pi, grid_points, endpoint=False)
    states = np.empty((grid_points, grid_points, 2), dtype=complex)
    for ix, kx in enumerate(coordinates):
        for iy, ky in enumerate(coordinates):
            _, vectors = np.linalg.eigh(
                weak_bloch_hamiltonian(
                    kx,
                    ky,
                    mu=mu,
                    hopping=hopping,
                    mass_curvature=mass_curvature,
                    spin_orbit=spin_orbit,
                )
            )
            states[ix, iy] = vectors[:, 1]
    return fukui_chern(states)


def weak_floquet_chern(
    *,
    mu: float,
    hopping: float,
    mass_curvature: float,
    spin_orbit: float,
    drive_amplitude: float,
    drive_frequency: float,
    time_steps: int,
    grid_points: int,
) -> float:
    coordinates = np.linspace(-np.pi, np.pi, grid_points, endpoint=False)
    states = np.empty((grid_points, grid_points, 2), dtype=complex)
    for ix, kx in enumerate(coordinates):
        for iy, ky in enumerate(coordinates):
            operator = weak_floquet_bloch(
                kx,
                ky,
                mu=mu,
                hopping=hopping,
                mass_curvature=mass_curvature,
                spin_orbit=spin_orbit,
                drive_amplitude=drive_amplitude,
                drive_frequency=drive_frequency,
                time_steps=time_steps,
            )
            values, vectors = np.linalg.eig(operator)
            energies = -np.angle(values)
            states[ix, iy] = vectors[:, int(np.argmax(energies))]
    return fukui_chern(states)


def unitarity_residual(operator: np.ndarray) -> float:
    return float(
        np.linalg.norm(operator.conjugate().T @ operator - IDENTITY_2, ord=np.inf)
    )
