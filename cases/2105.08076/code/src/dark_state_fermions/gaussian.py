"""Gaussian trajectory solver for continuously monitored free fermions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

from .observables import density_correlations, entropy_profile

ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]


def periodic_distances(length: int) -> FloatArray:
    """Return distances from site zero using the minimum ring convention."""

    if length < 2 or length % 2:
        raise ValueError("length must be an even integer >= 2")
    offsets = np.arange(length, dtype=float)
    return np.minimum(offsets, length - offsets)


def long_range_hamiltonian(length: int, exponent: float) -> FloatArray:
    """Construct Main Eq. (2) on a finite periodic ring.

    The paper specifies a ring but does not spell out the finite-size distance.
    We use the minimum periodic distance and expose that choice in provenance.
    """

    if exponent <= 1.0:
        raise ValueError("the paper requires exponent p > 1")
    distance = periodic_distances(length)
    first_row = np.zeros(length, dtype=float)
    first_row[1:] = -(distance[1:] ** (-exponent))
    indices = (np.arange(length)[:, None] - np.arange(length)[None, :]) % length
    hamiltonian = first_row[indices]
    return np.asarray(hamiltonian, dtype=float)


def hopping_dispersion(length: int, exponent: float) -> FloatArray:
    """Eigenvalues of the circulant hopping matrix in FFT ordering."""

    first_column = long_range_hamiltonian(length, exponent)[:, 0]
    dispersion = np.fft.fft(first_column)
    if np.max(np.abs(dispersion.imag)) > 1e-12:
        raise RuntimeError("circulant hopping spectrum is unexpectedly complex")
    return np.asarray(dispersion.real, dtype=float)


def neel_orbitals(length: int, offset: int = 0) -> ComplexArray:
    """Half-filled Neel product state as occupied single-particle orbitals."""

    if offset not in (0, 1):
        raise ValueError("Neel offset must be zero or one")
    occupied = np.arange(offset, length, 2)
    orbitals = np.zeros((length, length // 2), dtype=np.complex128)
    orbitals[occupied, np.arange(length // 2)] = 1.0
    return orbitals


def _canonical_qr(matrix: ComplexArray) -> ComplexArray:
    """Reduced QR with deterministic column phases."""

    q, r = np.linalg.qr(matrix, mode="reduced")
    diagonal = np.diag(r)
    phases = np.ones_like(diagonal, dtype=np.complex128)
    nonzero = np.abs(diagonal) > 1e-15
    phases[nonzero] = diagonal[nonzero] / np.abs(diagonal[nonzero])
    return np.asarray(q * phases.conj()[None, :], dtype=np.complex128)


@dataclass
class GaussianTrajectory:
    """One number-conserving pure Gaussian monitored trajectory."""

    length: int
    exponent: float
    gamma: float
    dt: float
    seed: int
    neel_offset: int = 0

    def __post_init__(self) -> None:
        if self.gamma < 0:
            raise ValueError("gamma must be nonnegative")
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        self._dispersion = hopping_dispersion(self.length, self.exponent)
        self._half_phase = np.exp(-0.5j * self.dt * self._dispersion)
        self._rng = np.random.default_rng(self.seed)
        self.orbitals = neel_orbitals(self.length, self.neel_offset)
        self.time = 0.0

    def _unitary_half_step(self) -> None:
        momentum = np.fft.fft(self.orbitals, axis=0)
        momentum *= self._half_phase[:, None]
        self.orbitals = np.asarray(np.fft.ifft(momentum, axis=0), dtype=np.complex128)

    def _measurement_step(self) -> None:
        if self.gamma == 0.0:
            return
        occupation = np.sum(np.abs(self.orbitals) ** 2, axis=1).real
        innovation = self._rng.normal(
            loc=0.0,
            scale=np.sqrt(self.gamma * self.dt),
            size=self.length,
        )
        # Derived from Main Eq. (1).  The extra -gamma/2 in the exponential
        # cancels the Ito square of the stochastic one-body coefficient.
        log_weight = innovation - self.gamma * (1.0 - occupation) * self.dt
        log_weight -= np.max(log_weight)
        weighted = np.exp(log_weight)[:, None] * self.orbitals
        self.orbitals = _canonical_qr(weighted)

    def step(self) -> None:
        """Advance by one symmetric split step."""

        self._unitary_half_step()
        self._measurement_step()
        self._unitary_half_step()
        self.time += self.dt

    def advance(self, steps: int) -> None:
        if steps < 0:
            raise ValueError("steps must be nonnegative")
        for _ in range(steps):
            self.step()

    @property
    def projector(self) -> ComplexArray:
        return np.asarray(self.orbitals @ self.orbitals.conj().T, dtype=np.complex128)

    def invariant_residuals(self) -> dict[str, float]:
        projector = self.projector
        hermitian = np.linalg.norm(projector - projector.conj().T)
        idempotent = np.linalg.norm(projector @ projector - projector)
        trace_error = abs(float(np.trace(projector).real) - self.length / 2)
        orbital_error = np.linalg.norm(
            self.orbitals.conj().T @ self.orbitals - np.eye(self.length // 2)
        )
        return {
            "hermitian": float(hermitian),
            "idempotent": float(idempotent),
            "trace_error": float(trace_error),
            "orbital_orthonormality": float(orbital_error),
        }


@dataclass(frozen=True)
class EnsembleResult:
    length: int
    exponent: float
    gamma: float
    ell: FloatArray
    entropy_mean: FloatArray
    entropy_sem: FloatArray
    correlation_positive_mean: FloatArray
    correlation_positive_sem: FloatArray
    correlation_connected_mean: FloatArray
    trajectories: int
    samples_per_trajectory: int
    max_invariant_residual: float
    stationary_relative_drift: float

    def half_chain(self) -> dict[str, float]:
        index = int(np.argmin(np.abs(self.ell - self.length / 2)))
        return {
            "entropy": float(self.entropy_mean[index]),
            "entropy_sem": float(self.entropy_sem[index]),
            "correlation_positive": float(self.correlation_positive_mean[index]),
            "correlation_positive_sem": float(self.correlation_positive_sem[index]),
            "correlation_connected": float(self.correlation_connected_mean[index]),
        }


def default_ell_values(length: int, points: int = 15) -> NDArray[np.int64]:
    """Log/linear hybrid subsystem grid including L/2 exactly."""

    upper = length // 2
    if upper <= 2:
        return np.asarray([1], dtype=np.int64)
    logarithmic = np.geomspace(1, upper, num=max(4, points))
    central = np.linspace(max(1, length // 4), upper, num=max(4, points // 2))
    values = np.unique(
        np.rint(np.concatenate([logarithmic, central, [upper]])).astype(int)
    )
    return values[(values >= 1) & (values <= upper)]


def _sem(values: FloatArray, axis: int = 0) -> FloatArray:
    count = values.shape[axis]
    if count <= 1:
        shape = list(values.shape)
        shape.pop(axis)
        return np.zeros(shape, dtype=float)
    return np.std(values, axis=axis, ddof=1) / np.sqrt(count)


def simulate_ensemble(
    *,
    length: int,
    exponent: float,
    gamma: float,
    dt: float,
    burn_time: float,
    sample_time: float,
    sample_interval: float,
    trajectories: int,
    seed_base: int,
    ell_values: Iterable[int] | None = None,
    entropy_origins: int = 1,
) -> EnsembleResult:
    """Run a trajectory ensemble and average nonlinear observables correctly."""

    if trajectories < 1:
        raise ValueError("trajectories must be >= 1")
    if burn_time < 0 or sample_time < 0 or sample_interval <= 0:
        raise ValueError("invalid time window")
    ell = np.asarray(
        list(ell_values) if ell_values is not None else default_ell_values(length),
        dtype=np.int64,
    )
    if ell.size == 0 or np.any(ell < 1) or np.any(ell > length // 2):
        raise ValueError("ell_values must lie between 1 and L/2")

    burn_steps = int(np.ceil(burn_time / dt))
    interval_steps = max(1, int(np.ceil(sample_interval / dt)))
    sample_count = max(1, int(np.floor(sample_time / (interval_steps * dt))) + 1)

    trajectory_entropy: list[FloatArray] = []
    trajectory_positive: list[FloatArray] = []
    trajectory_connected: list[FloatArray] = []
    invariant_max = 0.0
    drift_values: list[float] = []

    for trajectory_index in range(trajectories):
        trajectory = GaussianTrajectory(
            length=length,
            exponent=exponent,
            gamma=gamma,
            dt=dt,
            seed=seed_base + trajectory_index,
            neel_offset=trajectory_index % 2,
        )
        trajectory.advance(burn_steps)
        entropy_samples: list[FloatArray] = []
        positive_samples: list[FloatArray] = []
        connected_samples: list[FloatArray] = []

        for sample_index in range(sample_count):
            if sample_index:
                trajectory.advance(interval_steps)
            projector = trajectory.projector
            origins = np.linspace(
                0,
                length - 1,
                num=min(entropy_origins, length),
                endpoint=False,
                dtype=int,
            )
            entropy_samples.append(entropy_profile(projector, ell, origins=origins))
            positive, connected = density_correlations(projector, ell)
            positive_samples.append(positive)
            connected_samples.append(connected)

        entropy_array = np.asarray(entropy_samples, dtype=float)
        positive_array = np.asarray(positive_samples, dtype=float)
        connected_array = np.asarray(connected_samples, dtype=float)
        trajectory_entropy.append(np.mean(entropy_array, axis=0))
        trajectory_positive.append(np.mean(positive_array, axis=0))
        trajectory_connected.append(np.mean(connected_array, axis=0))

        if entropy_array.shape[0] > 1:
            start = float(np.mean(entropy_array[0]))
            end = float(np.mean(entropy_array[-1]))
            drift_values.append(abs(end - start) / max(abs(start), 1e-12))
        residuals = trajectory.invariant_residuals()
        invariant_max = max(invariant_max, max(residuals.values()))

    entropy_stack = np.asarray(trajectory_entropy, dtype=float)
    positive_stack = np.asarray(trajectory_positive, dtype=float)
    connected_stack = np.asarray(trajectory_connected, dtype=float)
    return EnsembleResult(
        length=length,
        exponent=exponent,
        gamma=gamma,
        ell=ell.astype(float),
        entropy_mean=np.mean(entropy_stack, axis=0),
        entropy_sem=_sem(entropy_stack),
        correlation_positive_mean=np.mean(positive_stack, axis=0),
        correlation_positive_sem=_sem(positive_stack),
        correlation_connected_mean=np.mean(connected_stack, axis=0),
        trajectories=trajectories,
        samples_per_trajectory=sample_count,
        max_invariant_residual=float(invariant_max),
        stationary_relative_drift=float(max(drift_values, default=0.0)),
    )
