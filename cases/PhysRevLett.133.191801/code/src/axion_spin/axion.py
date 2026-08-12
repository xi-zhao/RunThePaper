"""Independent Eq. (1) kernels and result-normalized constraint curves."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

HBAR_C_EV_M = 1.973269804e-7


def dimensionless_range(
    mass_ev: ArrayLike, distance_m: ArrayLike
) -> NDArray[np.float64]:
    mass = np.asarray(mass_ev, dtype=float)
    distance = np.asarray(distance_m, dtype=float)
    if np.any(mass < 0) or np.any(distance <= 0):
        raise ValueError("mass must be nonnegative and distance positive")
    return mass * distance / HBAR_C_EV_M


def transverse_kernel(mass_ev: ArrayLike, distance_m: float) -> NDArray[np.float64]:
    """Eq. (1) mass/range factor for parallel spins transverse to separation.

    Overall coupling and neutron-mass constants are omitted.  The returned
    relative kernel has units m^-3 and is sufficient for the curve shape and
    normalized constraints.
    """

    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    x = dimensionless_range(mass_ev, distance_m)
    return np.exp(-x) * (1.0 + x) / distance_m**3


def tensor_kernel(
    mass_ev: ArrayLike,
    displacement_m: ArrayLike,
    *,
    sensor_spin: ArrayLike = (1.0, 0.0, 0.0),
    source_spin: ArrayLike = (1.0, 0.0, 0.0),
) -> NDArray[np.float64]:
    """Full orientation-dependent bracket of Eq. (1), without constants."""

    mass = np.atleast_1d(np.asarray(mass_ev, dtype=float))
    displacement = np.asarray(displacement_m, dtype=float)
    if displacement.shape[-1:] != (3,):
        raise ValueError("displacement_m must end in a three-vector axis")
    flat = displacement.reshape(-1, 3)
    radius = np.linalg.norm(flat, axis=1)
    if np.any(radius <= 0):
        raise ValueError("source and sensor points must not coincide")
    rhat = flat / radius[:, None]
    spin_i = np.asarray(sensor_spin, dtype=float)
    spin_ii = np.asarray(source_spin, dtype=float)
    if spin_i.shape != (3,) or spin_ii.shape != (3,):
        raise ValueError("spin vectors must have length three")
    dot_spin = float(np.dot(spin_i, spin_ii))
    projection = (rhat @ spin_i) * (rhat @ spin_ii)
    x = dimensionless_range(mass[:, None], radius[None, :])
    bracket = dot_spin * (1.0 + x) - projection[None, :] * (x**2 + 3.0 * x + 3.0)
    values = np.exp(-x) * bracket / radius[None, :] ** 3
    return values.reshape((mass.size,) + displacement.shape[:-1])


def normalized_constraint_curve(
    mass_ev: ArrayLike,
    *,
    distance_m: float,
    anchor_mass_ev: float,
    anchor_coupling_product_over_four: float,
) -> NDArray[np.float64]:
    """Convert Eq. (1) kernel shape to a result-normalized coupling limit."""

    mass = np.asarray(mass_ev, dtype=float)
    if anchor_mass_ev <= 0 or anchor_coupling_product_over_four <= 0:
        raise ValueError("anchor mass and coupling must be positive")
    anchor = float(transverse_kernel(anchor_mass_ev, distance_m))
    kernel = transverse_kernel(mass, distance_m)
    return anchor_coupling_product_over_four * anchor / kernel


def finite_volume_kernel(
    mass_ev: ArrayLike,
    source_points_m: ArrayLike,
    sensor_points_m: ArrayLike,
    *,
    sensor_spin: ArrayLike = (1.0, 0.0, 0.0),
    source_spin: ArrayLike = (1.0, 0.0, 0.0),
    block_size: int = 16384,
) -> NDArray[np.float64]:
    """Average paired quasi-Monte-Carlo geometry samples in bounded blocks."""

    source = np.asarray(source_points_m, dtype=float)
    sensor = np.asarray(sensor_points_m, dtype=float)
    if source.ndim != 2 or source.shape[1] != 3 or sensor.shape != source.shape:
        raise ValueError("source and sensor samples must have equal shape (N, 3)")
    if source.shape[0] == 0 or block_size <= 0:
        raise ValueError(
            "at least one paired sample and positive block_size are required"
        )
    masses = np.atleast_1d(np.asarray(mass_ev, dtype=float))
    total = np.zeros(masses.size, dtype=float)
    count = 0
    for start in range(0, source.shape[0], block_size):
        stop = min(start + block_size, source.shape[0])
        values = tensor_kernel(
            masses,
            sensor[start:stop] - source[start:stop],
            sensor_spin=sensor_spin,
            source_spin=source_spin,
        )
        total += np.sum(values, axis=1)
        count += stop - start
    return total / count
