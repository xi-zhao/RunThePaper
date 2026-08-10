"""Formula-only implementation of the collective-spin Lindblad model.

The module deliberately has no PDF, image, raw-source, or reference-file inputs.
Every numerical object is constructed from the equations recorded in
``EQUATION_CARDS.json``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import comb

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csc_matrix, csr_matrix, diags, eye, kron
from scipy.sparse.linalg import ArpackNoConvergence, eigs, expm_multiply, spsolve


@dataclass(frozen=True)
class SpinOperators:
    sx: csr_matrix
    sy: csr_matrix
    sz: csr_matrix
    sm: csr_matrix
    sp: csr_matrix


@lru_cache(maxsize=None)
def spin_operators(number_spins: int) -> SpinOperators:
    """Collective spin matrices in the fully symmetric S=N/2 sector."""

    if number_spins < 1:
        raise ValueError("number_spins must be positive")
    spin = number_spins / 2.0
    magnetic = np.arange(spin, -spin - 1.0, -1.0, dtype=np.float64)
    lowering = np.sqrt(spin * (spin + 1.0) - magnetic[:-1] * (magnetic[:-1] - 1.0))
    sm = diags(lowering, offsets=-1, shape=(number_spins + 1, number_spins + 1), dtype=np.complex128).tocsr()
    sp = sm.getH().tocsr()
    sx = ((sp + sm) * 0.5).tocsr()
    sy = ((sp - sm) * (-0.5j)).tocsr()
    sz = diags(magnetic, offsets=0, dtype=np.complex128).tocsr()
    return SpinOperators(sx=sx, sy=sy, sz=sz, sm=sm, sp=sp)


def liouvillian(
    number_spins: int,
    omega_0: float,
    kappa: float = 1.0,
    *,
    omega_x: float = 0.0,
    omega_z: float = 0.0,
) -> csc_matrix:
    """Return the column-vectorized Liouvillian from the paper master equation."""

    if kappa <= 0:
        raise ValueError("kappa must be positive")
    ops = spin_operators(number_spins)
    spin = number_spins / 2.0
    dimension = number_spins + 1
    identity = eye(dimension, dtype=np.complex128, format="csc")
    hamiltonian = (
        omega_0 * ops.sx
        + (omega_x / spin) * (ops.sx @ ops.sx)
        + (omega_z / spin) * (ops.sz @ ops.sz)
    ).tocsc()
    jump_norm = (ops.sp @ ops.sm).tocsc()

    # vec(A X B) = (B^T kron A) vec(X), using Fortran/column ordering.
    coherent = -1j * (
        kron(identity, hamiltonian, format="csc")
        - kron(hamiltonian.transpose(), identity, format="csc")
    )
    dissipative = (kappa / spin) * (
        kron(ops.sp.transpose(), ops.sm, format="csc")
        - 0.5 * kron(identity, jump_norm, format="csc")
        - 0.5 * kron(jump_norm.transpose(), identity, format="csc")
    )
    return (coherent + dissipative).tocsc()


def spin_x_coherent_density(number_spins: int) -> np.ndarray:
    """Density matrix for all spins polarized along +x in the symmetric basis."""

    amplitudes = np.asarray(
        [np.sqrt(comb(number_spins, index)) for index in range(number_spins + 1)],
        dtype=np.complex128,
    )
    amplitudes /= 2.0 ** (number_spins / 2.0)
    amplitudes /= np.linalg.norm(amplitudes)
    return np.outer(amplitudes, amplitudes.conj())


def vectorize_density(density: np.ndarray) -> np.ndarray:
    return np.asarray(density, dtype=np.complex128).reshape(-1, order="F")


def density_from_vector(vector: np.ndarray, dimension: int) -> np.ndarray:
    density = np.asarray(vector, dtype=np.complex128).reshape((dimension, dimension), order="F")
    density = 0.5 * (density + density.conj().T)
    trace = np.trace(density)
    if abs(trace) == 0:
        raise ValueError("density vector has zero trace")
    return density / trace


def steady_state(
    number_spins: int,
    omega_0: float,
    kappa: float = 1.0,
) -> tuple[np.ndarray, float]:
    """Solve L rho=0 with one row replaced by the trace constraint."""

    operator = liouvillian(number_spins, omega_0, kappa).tolil(copy=True)
    dimension = number_spins + 1
    size = dimension * dimension
    trace_row = np.zeros(size, dtype=np.complex128)
    trace_row[np.arange(dimension) * (dimension + 1)] = 1.0
    operator[0, :] = trace_row
    right_hand_side = np.zeros(size, dtype=np.complex128)
    right_hand_side[0] = 1.0
    vector = spsolve(operator.tocsc(), right_hand_side)
    density = density_from_vector(vector, dimension)
    residual = float(
        np.linalg.norm(liouvillian(number_spins, omega_0, kappa) @ vectorize_density(density))
    )
    return density, residual


def expectation(operator: csr_matrix, density: np.ndarray) -> float:
    value = np.trace(operator.toarray() @ density)
    return float(np.real_if_close(value).real)


def variance(operator: csr_matrix, density: np.ndarray) -> float:
    mean = expectation(operator, density)
    second = expectation((operator @ operator).tocsr(), density)
    return float(max(second - mean * mean, 0.0))


def full_spectrum(number_spins: int, omega_0: float, kappa: float = 1.0) -> np.ndarray:
    """Dense finite-N spectrum, reserved for the reduced-scale full-cloud target."""

    values = np.linalg.eigvals(liouvillian(number_spins, omega_0, kappa).toarray())
    return values[np.argsort(values.real)[::-1]]


def leading_spectrum(
    number_spins: int,
    omega_0: float,
    kappa: float = 1.0,
    *,
    count: int = 16,
    tolerance: float = 1e-9,
) -> tuple[np.ndarray, float, bool]:
    """Eigenvalues with largest real part plus an explicit residual audit."""

    operator = liouvillian(number_spins, omega_0, kappa)
    size = operator.shape[0]
    requested = min(max(count, 3), size - 2)
    converged = True
    try:
        values, vectors = eigs(
            operator,
            k=requested,
            which="LR",
            tol=tolerance,
            maxiter=50000,
            v0=np.random.default_rng(number_spins * 1009 + int(round(omega_0 * 1000))).normal(size=size),
        )
    except ArpackNoConvergence as exc:
        values = exc.eigenvalues
        vectors = exc.eigenvectors
        converged = False
        if values is None or vectors is None or len(values) < 3:
            raise
    ordering = np.argsort(values.real)[::-1]
    values = values[ordering]
    vectors = vectors[:, ordering]
    residuals = [
        np.linalg.norm(operator @ vectors[:, index] - values[index] * vectors[:, index])
        / max(np.linalg.norm(vectors[:, index]), 1e-15)
        for index in range(values.size)
    ]
    return values, float(max(residuals, default=np.inf)), converged


def magnetization_dynamics(
    number_spins: int,
    omega_0: float,
    times: np.ndarray,
    kappa: float = 1.0,
) -> np.ndarray:
    """Return <Sz>/N from exact finite-N Lindblad evolution."""

    times = np.asarray(times, dtype=np.float64)
    if times.ndim != 1 or times.size < 2 or times[0] != 0 or np.any(np.diff(times) <= 0):
        raise ValueError("times must be a strictly increasing one-dimensional grid starting at zero")
    density = spin_x_coherent_density(number_spins)
    vectors = expm_multiply(
        liouvillian(number_spins, omega_0, kappa),
        vectorize_density(density),
        start=float(times[0]),
        stop=float(times[-1]),
        num=int(times.size),
        endpoint=True,
    )
    sz_vector = spin_operators(number_spins).sz.toarray().T.reshape(-1, order="F")
    return np.real(vectors @ sz_vector) / number_spins


def semiclassical_rhs(
    _time: float,
    magnetization: np.ndarray,
    *,
    omega_0: float,
    kappa: float,
    omega_x: float = 0.0,
    omega_z: float = 0.0,
) -> np.ndarray:
    """Supplement Eq. (S7) for (m_x,m_y,m_z)."""

    mx, my, mz = magnetization
    return np.asarray(
        [
            -2.0 * omega_z * my * mz + kappa * mx * mz,
            2.0 * (omega_z - omega_x) * mx * mz - omega_0 * mz + kappa * my * mz,
            omega_0 * my - kappa * (mx * mx + my * my) + 2.0 * omega_x * mx * my,
        ],
        dtype=np.float64,
    )


def semiclassical_trajectory(
    initial: np.ndarray,
    times: np.ndarray,
    *,
    omega_0: float,
    kappa: float,
    omega_x: float = 0.0,
    omega_z: float = 0.0,
) -> tuple[np.ndarray, float]:
    """Integrate the semiclassical equations and report maximum norm drift."""

    initial = np.asarray(initial, dtype=np.float64)
    initial /= np.linalg.norm(initial)
    times = np.asarray(times, dtype=np.float64)
    solution = solve_ivp(
        lambda time, state: semiclassical_rhs(
            time,
            state,
            omega_0=omega_0,
            kappa=kappa,
            omega_x=omega_x,
            omega_z=omega_z,
        ),
        (float(times[0]), float(times[-1])),
        initial,
        t_eval=times,
        rtol=2e-9,
        atol=2e-11,
        method="DOP853",
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    trajectory = solution.y.T
    drift = float(np.max(np.abs(np.sum(trajectory * trajectory, axis=1) - 1.0)))
    return trajectory, drift


def qp_coordinates(trajectory: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map (mx,my,mz) to paper coordinates Q=mz and P=atan2(my,mx)/2."""

    trajectory = np.asarray(trajectory, dtype=np.float64)
    q_coordinate = trajectory[:, 2]
    p_coordinate = 0.5 * np.arctan2(trajectory[:, 1], trajectory[:, 0])
    return q_coordinate, p_coordinate


def conserved_r_omega_z(
    mx: np.ndarray,
    my: np.ndarray,
    *,
    omega_0: float,
    kappa: float,
    omega_z: float,
) -> np.ndarray:
    """Principal-branch value of the supplement conserved quantity R_{omega_z}."""

    real_part = kappa * my + 2.0 * omega_z * mx - omega_0
    imag_part = kappa * mx - 2.0 * omega_z * my
    radius_squared = real_part * real_part + imag_part * imag_part
    return 2.0 * omega_z * np.log(np.maximum(radius_squared, 1e-15)) + 2.0 * kappa * np.arctan2(
        imag_part, real_part
    )
