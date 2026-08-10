"""Independent Gaussian-fermion solvers for arXiv:2005.09722.

The implementation follows the stochastic equations and numerical appendix in
the paper.  It does not read author code, author arrays, or source-figure
pixels.  A trajectory is represented by an ``L x (L/2)`` orthonormal orbital
matrix whose Slater determinant defines the many-body state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import qr


ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]
SnapshotCallback = Callable[[float, ComplexArray], None]


@dataclass(frozen=True)
class QSDConfig:
    length: int
    gamma: float
    dt: float = 0.05
    t_final: float = 20.0
    protocol: str = "qsd"

    def validate(self) -> None:
        if self.length < 4 or self.length % 2:
            raise ValueError("length must be an even integer >= 4")
        if self.gamma < 0.0:
            raise ValueError("gamma must be non-negative")
        if self.dt <= 0.0 or self.t_final < 0.0:
            raise ValueError("dt must be positive and t_final non-negative")
        if self.protocol not in {"qsd", "qsdc"}:
            raise ValueError("protocol must be 'qsd' or 'qsdc'")


def neel_orbitals(length: int) -> ComplexArray:
    """Return the half-filled ``|0101...01>`` Slater determinant."""

    if length < 2 or length % 2:
        raise ValueError("length must be positive and even")
    orbitals = np.zeros((length, length // 2), dtype=np.complex128)
    orbitals[np.arange(1, length, 2), np.arange(length // 2)] = 1.0
    return orbitals


def correlation_matrix(orbitals: ComplexArray) -> ComplexArray:
    """Equal-time one-body correlation matrix ``U U^dagger``."""

    return orbitals @ orbitals.conj().T


def apply_uniform_hopping(
    orbitals: ComplexArray,
    duration: float,
) -> ComplexArray:
    """Apply ``exp(-i h duration)`` for unit periodic nearest-neighbor hopping.

    The hopping matrix is circulant with eigenvalues ``2 cos(2 pi k/L)``;
    applying it by FFT is algebraically equivalent to a dense exponential.
    """

    length = orbitals.shape[0]
    momenta = 2.0 * np.pi * np.arange(length) / length
    phases = np.exp(-2.0j * np.cos(momenta) * duration)
    transformed = np.fft.fft(orbitals, axis=0)
    return np.fft.ifft(phases[:, None] * transformed, axis=0)


def random_hopping_propagator(
    couplings: FloatArray,
    duration: float,
) -> ComplexArray:
    """Dense propagator for Eq. (A1), including the periodic boundary bond."""

    weights = np.asarray(couplings, dtype=np.float64)
    length = len(weights)
    if weights.shape != (length,):
        raise ValueError("couplings must be one-dimensional")
    hopping = np.zeros((length, length), dtype=np.float64)
    sites = np.arange(length)
    neighbors = (sites + 1) % length
    hopping[sites, neighbors] = weights
    hopping[neighbors, sites] = weights
    eigenvalues, eigenvectors = np.linalg.eigh(hopping)
    return (eigenvectors * np.exp(-1.0j * eigenvalues * duration)) @ eigenvectors.T


def qsd_step(
    orbitals: ComplexArray,
    *,
    gamma: float,
    dt: float,
    generator: np.random.Generator,
    protocol: str = "qsd",
    hopping: Callable[[ComplexArray], ComplexArray] | None = None,
) -> ComplexArray:
    """Apply one first-order Trotter step from the numerical appendix."""

    if protocol not in {"qsd", "qsdc"}:
        raise ValueError("protocol must be 'qsd' or 'qsdc'")
    densities = np.sum(np.abs(orbitals) ** 2, axis=1).real
    evolved = (
        apply_uniform_hopping(orbitals, dt)
        if hopping is None
        else hopping(orbitals)
    )
    if gamma > 0.0:
        noise = np.sqrt(gamma * dt) * generator.normal(size=orbitals.shape[0])
        sigma = 1.0 if protocol == "qsd" else 0.0
        exponent = noise + gamma * sigma * (2.0 * densities - 1.0) * dt
        evolved = np.exp(exponent)[:, None] * evolved
    orthonormal, triangular = np.linalg.qr(evolved, mode="reduced")
    diagonal = np.diag(triangular)
    phases = np.ones_like(diagonal)
    nonzero = np.abs(diagonal) > 1e-15
    phases[nonzero] = diagonal[nonzero] / np.abs(diagonal[nonzero])
    # Fix the otherwise arbitrary orbital phases by requiring a positive-real
    # diagonal in R.  Equal-time observables are gauge invariant, while this
    # deterministic convention is needed for the two-time product U(t')U†(t)
    # used in the paper's autocorrelation definition.
    orthonormal = orthonormal * phases[None, :]
    return np.asarray(orthonormal, dtype=np.complex128)


def evolve_qsd(
    config: QSDConfig,
    *,
    seed: int,
    initial: ComplexArray | None = None,
    sample_times: Iterable[float] = (),
    callback: SnapshotCallback | None = None,
) -> ComplexArray:
    """Evolve one QSD or QSDc trajectory and optionally expose snapshots."""

    config.validate()
    generator = np.random.default_rng(seed)
    orbitals = (
        neel_orbitals(config.length)
        if initial is None
        else np.asarray(initial, dtype=np.complex128).copy()
    )
    requested = sorted(float(value) for value in sample_times if value >= 0.0)
    sample_index = 0
    if callback is not None:
        while sample_index < len(requested) and requested[sample_index] <= 1e-12:
            callback(0.0, orbitals)
            sample_index += 1

    steps = int(np.ceil(config.t_final / config.dt - 1e-12))
    for step in range(1, steps + 1):
        orbitals = qsd_step(
            orbitals,
            gamma=config.gamma,
            dt=config.dt,
            generator=generator,
            protocol=config.protocol,
        )
        time = min(step * config.dt, config.t_final)
        if callback is not None:
            while sample_index < len(requested) and requested[sample_index] <= time + 1e-12:
                callback(requested[sample_index], orbitals)
                sample_index += 1
    return orbitals


def evolve_random_hopping_qsd(
    config: QSDConfig,
    *,
    seed: int,
    update_interval: float = 1.0,
) -> ComplexArray:
    """Evolve QSD with the binary spatiotemporal hopping in Eq. (A1)."""

    config.validate()
    if config.protocol != "qsd":
        raise ValueError("the random-hopping appendix target uses QSD")
    if update_interval <= 0.0:
        raise ValueError("update_interval must be positive")
    generator = np.random.default_rng(seed)
    orbitals = neel_orbitals(config.length)
    steps = int(np.ceil(config.t_final / config.dt - 1e-12))
    steps_per_block = max(1, int(round(update_interval / config.dt)))
    propagator: ComplexArray | None = None

    for step in range(steps):
        if step % steps_per_block == 0:
            couplings = generator.choice(np.array([-1.0, 1.0]), size=config.length)
            propagator = random_hopping_propagator(couplings, config.dt)
        assert propagator is not None
        orbitals = qsd_step(
            orbitals,
            gamma=config.gamma,
            dt=config.dt,
            generator=generator,
            protocol="qsd",
            hopping=lambda state, matrix=propagator: matrix @ state,
        )
    return orbitals


def _apply_occupied_jump(orbitals: ComplexArray, site: int) -> ComplexArray:
    """Condition a Slater determinant on an occupied-site quantum jump.

    A unitary rotation of occupied orbitals aligns one orbital with the selected
    row.  Replacing that orbital by ``|site>`` implements ``n_site |psi>``
    while retaining an orthonormal Slater basis, without using author code.
    """

    row = orbitals[site]
    probability = float(np.vdot(row, row).real)
    if probability <= 1e-14:
        raise RuntimeError("selected a zero-probability jump")
    rotation, _ = qr(row.conj()[:, None], mode="full")
    rotated = orbitals @ rotation
    rotated[:, 0] = 0.0
    rotated[site, 0] = 1.0
    rotated[site, 1:] = 0.0
    return np.asarray(rotated, dtype=np.complex128)


def evolve_quantum_jumps(
    *,
    length: int,
    gamma: float,
    t_final: float,
    seed: int,
) -> ComplexArray:
    """Event-driven quantum-jump trajectory from the paper's appendix."""

    if length < 4 or length % 2:
        raise ValueError("length must be even and >= 4")
    if gamma < 0.0 or t_final < 0.0:
        raise ValueError("gamma and t_final must be non-negative")
    generator = np.random.default_rng(seed)
    orbitals = neel_orbitals(length)
    if gamma == 0.0:
        return apply_uniform_hopping(orbitals, t_final)

    particle_number = length // 2
    time = 0.0
    while time < t_final - 1e-14:
        waiting = float(generator.exponential(1.0 / (gamma * particle_number)))
        duration = min(waiting, t_final - time)
        orbitals = apply_uniform_hopping(orbitals, duration)
        time += duration
        if waiting > duration + 1e-14:
            break
        densities = np.sum(np.abs(orbitals) ** 2, axis=1).real
        probabilities = np.maximum(densities, 0.0)
        probabilities /= np.sum(probabilities)
        site = int(generator.choice(length, p=probabilities))
        orbitals = _apply_occupied_jump(orbitals, site)
    return orbitals


def subsystem_entropy(orbitals: ComplexArray, sites: Iterable[int]) -> float:
    """Von Neumann entropy in bits from Eq. (6)."""

    indices = np.asarray(list(sites), dtype=np.int64)
    if indices.size == 0:
        return 0.0
    reduced_orbitals = orbitals[indices]
    reduced = reduced_orbitals @ reduced_orbitals.conj().T
    eigenvalues = np.linalg.eigvalsh(reduced).real
    clipped = np.clip(eigenvalues, 1e-14, 1.0 - 1e-14)
    entropy = -np.sum(
        clipped * np.log2(clipped)
        + (1.0 - clipped) * np.log2(1.0 - clipped)
    )
    return float(entropy)


def interval_entropy(orbitals: ComplexArray, start: int, length: int) -> float:
    """Entropy of a periodic contiguous interval."""

    system_size = orbitals.shape[0]
    sites = (start + np.arange(length)) % system_size
    return subsystem_entropy(orbitals, sites)


def mutual_information(
    orbitals: ComplexArray,
    interval_a: Iterable[int],
    interval_b: Iterable[int],
) -> float:
    """Mutual information ``S(A)+S(B)-S(A union B)`` in bits."""

    sites_a = np.asarray(list(interval_a), dtype=np.int64)
    sites_b = np.asarray(list(interval_b), dtype=np.int64)
    if np.intersect1d(sites_a, sites_b).size:
        raise ValueError("mutual-information intervals must be disjoint")
    return float(
        subsystem_entropy(orbitals, sites_a)
        + subsystem_entropy(orbitals, sites_b)
        - subsystem_entropy(orbitals, np.concatenate((sites_a, sites_b)))
    )


def fixed_separation_mutual_information(orbitals: ComplexArray) -> float:
    """Paper geometry: two ``L/8`` intervals whose centers differ by ``L/2``."""

    length = orbitals.shape[0]
    block = max(1, length // 8)
    interval_a = np.arange(block)
    interval_b = (length // 2 + np.arange(block)) % length
    return mutual_information(orbitals, interval_a, interval_b)


def cross_ratio(
    endpoints: tuple[int, int, int, int],
    length: int,
) -> float:
    """Periodic CFT cross ratio used in Fig. 3(b,c)."""

    m1, m2, m3, m4 = endpoints

    def chord(left: int, right: int) -> float:
        return float(np.sin(np.pi * abs(left - right) / length))

    denominator = chord(m1, m3) * chord(m2, m4)
    if denominator <= 0.0:
        raise ValueError("degenerate interval endpoints")
    return chord(m1, m2) * chord(m3, m4) / denominator


def spatial_correlations(orbitals: ComplexArray, distances: Iterable[int]) -> FloatArray:
    """Translation average of ``|<c_i^dagger c_(i+l)>|^2``."""

    matrix = correlation_matrix(orbitals)
    length = orbitals.shape[0]
    values = []
    sites = np.arange(length)
    for distance in distances:
        shifted = (sites + int(distance)) % length
        values.append(float(np.mean(np.abs(matrix[shifted, sites]) ** 2)))
    return np.asarray(values, dtype=np.float64)


def density_correlation_components(
    orbitals: ComplexArray,
    distances: Iterable[int],
) -> tuple[FloatArray, FloatArray]:
    """Return ``<n_i><n_i+l>`` and ``<n_i n_i+l>`` translation averages.

    Wick's theorem for a number-conserving Gaussian state gives the second
    component.  Their difference is the direct Fock correlation plotted in the
    appendix measurement check.
    """

    matrix = correlation_matrix(orbitals)
    densities = np.diag(matrix).real
    length = orbitals.shape[0]
    sites = np.arange(length)
    products = []
    density_density = []
    for distance in distances:
        shifted = (sites + int(distance)) % length
        product = densities[sites] * densities[shifted]
        exchange = np.abs(matrix[shifted, sites]) ** 2
        products.append(float(np.mean(product)))
        density_density.append(float(np.mean(product - exchange)))
    return (
        np.asarray(products, dtype=np.float64),
        np.asarray(density_density, dtype=np.float64),
    )


def two_time_on_site_correlation(
    reference_orbitals: ComplexArray,
    later_orbitals: ComplexArray,
) -> float:
    """Translation average of the paper's ``|D_jj(t+tau,t)|^2``."""

    if reference_orbitals.shape != later_orbitals.shape:
        raise ValueError("reference and later orbital matrices must have equal shape")
    unequal_time = later_orbitals @ reference_orbitals.conj().T
    return float(np.mean(np.abs(np.diag(unequal_time)) ** 2))


def cft_fit(
    lengths: FloatArray,
    entropies: FloatArray,
    system_size: int,
) -> tuple[float, float, float]:
    """Fit Eq. (8), returning effective central charge, intercept and R^2."""

    sizes = np.asarray(lengths, dtype=np.float64)
    values = np.asarray(entropies, dtype=np.float64)
    coordinate = np.log2(system_size / np.pi * np.sin(np.pi * sizes / system_size))
    design = np.column_stack((coordinate, np.ones_like(coordinate)))
    slope, intercept = np.linalg.lstsq(design, values, rcond=None)[0]
    predicted = design @ np.array([slope, intercept])
    residual = float(np.sum((values - predicted) ** 2))
    total = float(np.sum((values - np.mean(values)) ** 2))
    r_squared = 1.0 - residual / total if total > 0.0 else 1.0
    return float(3.0 * slope), float(intercept), float(r_squared)


def orthonormality_residual(orbitals: ComplexArray) -> float:
    """Maximum absolute violation of ``U^dagger U = I``."""

    identity = np.eye(orbitals.shape[1], dtype=np.complex128)
    return float(np.max(np.abs(orbitals.conj().T @ orbitals - identity)))
