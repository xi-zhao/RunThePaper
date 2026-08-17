"""Bit-basis Hamiltonians and Floquet eigensystems.

This module is a clean-room implementation derived from the manuscript. It
does not read files and has no access to paper figures or author artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import scipy.linalg

Array = np.ndarray


@dataclass(frozen=True)
class FloquetEigensystem:
    """Sorted dimensionless quasienergy angles and optional eigenvectors."""

    angles: Array
    vectors: Array | None
    unitary_residual: float
    total_period: float


def parity_basis(system_size: int, parity: int | None = 1) -> Array:
    """Return z-basis states in the requested global-Ising-parity sector."""
    if system_size < 2:
        raise ValueError("system_size must be at least 2")
    if parity not in {-1, 1, None}:
        raise ValueError("parity must be -1, +1 or None")
    states = np.arange(1 << system_size, dtype=np.int64)
    if parity is None:
        return states
    keep = np.fromiter(
        ((1 if int(state).bit_count() % 2 == 0 else -1) == parity for state in states),
        dtype=bool,
        count=states.size,
    )
    return states[keep]


def _as_bond_array(value: float | Sequence[float], bonds: int, name: str) -> Array:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        return np.full(bonds, float(array))
    if array.shape != (bonds,):
        raise ValueError(f"{name} must contain {bonds} bonds")
    return array


def build_ising_hamiltonian(
    system_size: int,
    *,
    xx_couplings: float | Sequence[float],
    z_fields: float | Sequence[float],
    zz_couplings: float | Sequence[float],
    parity: int | None = 1,
    periodic: bool = False,
) -> tuple[Array, Array]:
    """Build sum J_i X_iX_j + h_i Z_i + K_i Z_iZ_j."""
    basis = parity_basis(system_size, parity)
    dimension = basis.size
    index = {int(state): row for row, state in enumerate(basis)}
    bond_count = system_size if periodic else system_size - 1
    j_values = _as_bond_array(xx_couplings, bond_count, "xx_couplings")
    k_values = _as_bond_array(zz_couplings, bond_count, "zz_couplings")
    h_values = np.asarray(z_fields, dtype=float)
    if h_values.ndim == 0:
        h_values = np.full(system_size, float(h_values))
    if h_values.shape != (system_size,):
        raise ValueError(f"z_fields must contain {system_size} sites")

    hamiltonian = np.zeros((dimension, dimension), dtype=float)
    bonds = [(site, (site + 1) % system_size) for site in range(bond_count)]
    for row, raw_state in enumerate(basis):
        state = int(raw_state)
        z = np.fromiter(
            (
                1.0 if ((state >> site) & 1) == 0 else -1.0
                for site in range(system_size)
            ),
            dtype=float,
            count=system_size,
        )
        diagonal = float(np.dot(h_values, z))
        for bond, (left, right) in enumerate(bonds):
            diagonal += k_values[bond] * z[left] * z[right]
            coupling = j_values[bond]
            if coupling:
                flipped = state ^ (1 << left) ^ (1 << right)
                hamiltonian[row, index[flipped]] += coupling
        hamiltonian[row, row] += diagonal
    return hamiltonian, basis


def _numpy_exponential(hamiltonian: Array, duration: float) -> Array:
    eigenvalues, eigenvectors = scipy.linalg.eigh(
        hamiltonian, overwrite_a=False, check_finite=True
    )
    phases = np.exp(-1j * duration * eigenvalues)
    return (eigenvectors * phases) @ eigenvectors.conj().T


def _backend_eigensystem(
    stages: Sequence[tuple[Array, float]], backend: str
) -> tuple[Array, Array]:
    if backend == "numpy":
        dimension = stages[0][0].shape[0]
        unitary = np.eye(dimension, dtype=complex)
        for hamiltonian, duration in stages:
            unitary = _numpy_exponential(hamiltonian, duration) @ unitary
        triangular, vectors = scipy.linalg.schur(unitary, output="complex")
        eigenvalues = np.diag(triangular)
        return unitary, (eigenvalues, vectors)
    if backend != "cupy":
        raise ValueError("backend must be numpy or cupy")
    try:
        import cupy as cp
    except ImportError as exc:  # pragma: no cover - depends on A100 environment
        raise RuntimeError("CuPy backend requested but cupy is unavailable") from exc
    dimension = stages[0][0].shape[0]
    unitary_gpu = cp.eye(dimension, dtype=cp.complex128)
    for hamiltonian, duration in stages:
        values, vectors = cp.linalg.eigh(cp.asarray(hamiltonian))
        exponential = (vectors * cp.exp(-1j * duration * values)) @ vectors.conj().T
        unitary_gpu = exponential @ unitary_gpu
    eigenvalues_gpu, vectors_gpu = cp.linalg.eig(unitary_gpu)
    return cp.asnumpy(unitary_gpu), (
        cp.asnumpy(eigenvalues_gpu),
        cp.asnumpy(vectors_gpu),
    )


def floquet_eigensystem(
    stages: Sequence[tuple[Array, float]],
    *,
    backend: str = "numpy",
    return_vectors: bool = True,
) -> FloquetEigensystem:
    """Diagonalize the chronological Floquet product for declared stages."""
    if not stages:
        raise ValueError("at least one stage is required")
    dimension = stages[0][0].shape[0]
    if any(matrix.shape != (dimension, dimension) for matrix, _ in stages):
        raise ValueError("all stage Hamiltonians must have equal square shape")
    if any(duration <= 0 for _, duration in stages):
        raise ValueError("stage durations must be positive")
    unitary, (eigenvalues, vectors) = _backend_eigensystem(stages, backend)
    residual = float(
        np.linalg.norm(unitary.conj().T @ unitary - np.eye(dimension), ord=np.inf)
    )
    angles = np.mod(-np.angle(eigenvalues), 2 * np.pi)
    order = np.argsort(angles)
    vectors_out = vectors[:, order] if return_vectors else None
    if vectors_out is not None:
        vectors_out /= np.linalg.norm(vectors_out, axis=0, keepdims=True)
    return FloquetEigensystem(
        angles=angles[order],
        vectors=vectors_out,
        unitary_residual=residual,
        total_period=float(sum(duration for _, duration in stages)),
    )


def lognormal_standard_deviation(log_mean: float, log_sigma: float = 1.0) -> float:
    variance = (np.exp(log_sigma**2) - 1.0) * np.exp(2.0 * log_mean + log_sigma**2)
    return float(np.sqrt(variance))


def log_drive_stages(
    *,
    system_size: int,
    mean_log_j: float,
    interaction: float,
    rng: np.random.Generator,
    parity: int | None = 1,
    periodic: bool = False,
) -> tuple[list[tuple[Array, float]], Array]:
    """Sample and assemble the three-stage drive behind Main Fig. 1."""
    bond_count = system_size if periodic else system_size - 1
    fields = np.exp(rng.normal(0.0, 1.0, size=system_size))
    couplings = np.exp(rng.normal(mean_log_j, 1.0, size=bond_count))
    bandwidth = max(
        lognormal_standard_deviation(0.0),
        lognormal_standard_deviation(mean_log_j),
    )
    period = np.pi / bandwidth
    low, basis = build_ising_hamiltonian(
        system_size,
        xx_couplings=couplings,
        z_fields=fields,
        zz_couplings=interaction,
        parity=parity,
        periodic=periodic,
    )
    high, _ = build_ising_hamiltonian(
        system_size,
        xx_couplings=np.e * couplings,
        z_fields=fields,
        zz_couplings=interaction,
        parity=parity,
        periodic=periodic,
    )
    return [(low, period / 4), (high, period / 2), (low, period / 4)], basis


def pi_drive_stages(
    *,
    system_size: int,
    interaction: float,
    h_t1: Sequence[float],
    j_t2: Sequence[float],
    t1: float = 1.0,
    t2: float = np.pi / 2,
    parity: int | None = 1,
) -> tuple[list[tuple[Array, float]], Array]:
    """Assemble the open binary drive from dimensionless disorder angles."""
    h_angles = np.asarray(h_t1, dtype=float)
    j_angles = np.asarray(j_t2, dtype=float)
    if h_angles.shape != (system_size,):
        raise ValueError(f"h_t1 must contain {system_size} sites")
    if j_angles.shape != (system_size - 1,):
        raise ValueError(f"j_t2 must contain {system_size - 1} bonds")
    hz, basis = build_ising_hamiltonian(
        system_size,
        xx_couplings=0.0,
        z_fields=h_angles / t1,
        zz_couplings=interaction,
        parity=parity,
        periodic=False,
    )
    hx, _ = build_ising_hamiltonian(
        system_size,
        xx_couplings=j_angles / t2,
        z_fields=0.0,
        zz_couplings=interaction,
        parity=parity,
        periodic=False,
    )
    return [(hz, t1), (hx, t2)], basis


def sample_pi_angles(
    system_size: int,
    rng: np.random.Generator,
    *,
    phase: str = "pi",
) -> tuple[Array, Array]:
    """Draw the printed pi-SG ensemble or its explicitly reconstructed dual."""
    narrow = (1.512, 1.551)
    broad = (0.393, 1.492)
    if phase == "pi":
        h_interval, j_interval = narrow, broad
    elif phase == "zero":
        # The paper does not print the dashed 0-SG ensemble. Reflecting the
        # narrow h*T1 interval about pi/2 moves the same disorder width from
        # the pi triangle to the 0 triangle of Fig. 2(a), while leaving the
        # broad spin-glass coupling interval unchanged.
        h_interval = (np.pi / 2 - narrow[1], np.pi / 2 - narrow[0])
        j_interval = broad
    else:
        raise ValueError("phase must be pi or zero")
    return (
        rng.uniform(*h_interval, size=system_size),
        rng.uniform(*j_interval, size=system_size - 1),
    )


def apply_hermitian_stage(hamiltonian: Array, duration: float, state: Array) -> Array:
    """Apply one exact time-independent stage to a state vector."""
    eigenvalues, eigenvectors = scipy.linalg.eigh(hamiltonian)
    coefficients = eigenvectors.conj().T @ state
    return eigenvectors @ (np.exp(-1j * duration * eigenvalues) * coefficients)


def micromotion_states(
    stages: Sequence[tuple[Array, float]], state: Array, times: Iterable[float]
) -> list[Array]:
    """Propagate a state to arbitrary times in one piecewise-constant period."""
    decompositions = [scipy.linalg.eigh(matrix) for matrix, _ in stages]
    boundaries = np.cumsum([0.0, *[duration for _, duration in stages]])
    output: list[Array] = []
    for raw_time in times:
        time = float(raw_time)
        if not (0.0 <= time <= boundaries[-1] + 1e-12):
            raise ValueError("micromotion time lies outside one period")
        current = np.asarray(state, dtype=complex)
        for stage_index, (_, duration) in enumerate(stages):
            elapsed = min(max(time - boundaries[stage_index], 0.0), duration)
            if elapsed <= 0:
                break
            values, vectors = decompositions[stage_index]
            coefficients = vectors.conj().T @ current
            current = vectors @ (np.exp(-1j * elapsed * values) * coefficients)
            if elapsed < duration:
                break
        output.append(current)
    return output
