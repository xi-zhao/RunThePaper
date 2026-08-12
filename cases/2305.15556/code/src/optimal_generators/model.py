"""Physics model for the SU(2) and SU(4) QFIM examples."""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, pi, sqrt
from typing import Sequence

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import expm_multiply

from .bosons import FixedNBosons

Array = np.ndarray
Sparse = sparse.csr_matrix


@dataclass(frozen=True)
class OperatorBasis:
    names: tuple[str, ...]
    operators: tuple[Sparse, ...]
    space: FixedNBosons


def spin_operator_basis(particles: int) -> OperatorBasis:
    space = FixedNBosons(particles, ("u", "d"))
    raising = space.bilinear("u", "d")
    lowering = raising.getH().tocsr()
    jx = ((raising + lowering) / 2).tocsr()
    jy = ((raising - lowering) / (2j)).tocsr()
    jz = ((space.number("u") - space.number("d")) / 2).tocsr()
    return OperatorBasis(("Jx", "Jy", "Jz"), (jx, jy, jz), space)


def oat_state(particles: int, tau: float) -> Array:
    basis = spin_operator_basis(particles)
    initial = basis.space.coherent_state((1 / sqrt(2), 1 / sqrt(2)))
    magnetic = np.asarray(
        [(occupation[0] - occupation[1]) / 2 for occupation in basis.space.basis],
        dtype=float,
    )
    state = initial * np.exp(-1j * float(tau) * magnetic**2)
    return state / np.linalg.norm(state)


def husimi_q(
    state: Array,
    particles: int,
    theta: Sequence[float],
    phi: Sequence[float],
) -> Array:
    """Evaluate |<theta,phi|state>|^2 on a tensor-product sphere grid."""

    theta_values = np.asarray(theta, dtype=float)
    phi_values = np.asarray(phi, dtype=float)
    if state.shape != (particles + 1,):
        raise ValueError("state does not match the symmetric SU(2) dimension")

    cos_half = np.cos(theta_values / 2)[:, None]
    sin_half = np.sin(theta_values / 2)[:, None]
    overlap = np.zeros((theta_values.size, phi_values.size), dtype=np.complex128)
    # FixedNBosons orders states as (N-k, k), k=0,...,N.
    for k in range(particles + 1):
        coherent_bra = (
            sqrt(comb(particles, k))
            * cos_half ** (particles - k)
            * sin_half**k
            * np.exp(-1j * k * phi_values[None, :])
        )
        overlap += coherent_bra * state[k]
    probability = np.abs(overlap) ** 2
    return np.clip(probability.real, 0.0, 1.0)


def qfim(state: Array, operators: Sequence[sparse.spmatrix]) -> Array:
    vector = np.asarray(state, dtype=np.complex128)
    norm = float(np.vdot(vector, vector).real)
    if not np.isclose(norm, 1.0, rtol=0.0, atol=2e-11):
        raise ValueError(f"state is not normalized: {norm}")
    acted = np.column_stack([operator @ vector for operator in operators])
    means = np.real(np.conjugate(vector) @ acted)
    gram = np.conjugate(acted).T @ acted
    matrix = 4.0 * np.real(gram - np.outer(means, means))
    return (matrix + matrix.T) / 2


def qfim_eigensystem(matrix: Array) -> tuple[Array, Array]:
    values, vectors = np.linalg.eigh(np.asarray(matrix, dtype=float))
    order = np.argsort(values)[::-1]
    return values[order], vectors[:, order]


def leading_projector(
    matrix: Array, relative_tolerance: float = 2e-8
) -> tuple[float, Array, int, Array]:
    values, vectors = qfim_eigensystem(matrix)
    threshold = relative_tolerance * max(1.0, abs(float(values[0])))
    rank = int(np.count_nonzero(values[0] - values <= threshold))
    leading = vectors[:, :rank]
    projector = leading @ leading.T
    return float(values[0]), projector, rank, values


def tracked_optimal_generator(
    matrices: Sequence[Array],
    seed: Sequence[float],
    relative_tolerance: float = 2e-8,
) -> tuple[Array, Array, Array, Array]:
    """Choose a deterministic continuous representative of each leading space."""

    reference = np.asarray(seed, dtype=float)
    reference /= np.linalg.norm(reference)
    coefficients: list[Array] = []
    projectors: list[Array] = []
    ranks: list[int] = []
    residuals: list[float] = []

    for matrix in matrices:
        leading_value, projector, rank, _ = leading_projector(
            matrix, relative_tolerance=relative_tolerance
        )
        candidate = projector @ reference
        norm = np.linalg.norm(candidate)
        if norm < 1e-10:
            _, vectors = qfim_eigensystem(matrix)
            candidate = vectors[:, 0]
            pivot = int(np.argmax(np.abs(candidate)))
            if candidate[pivot] < 0:
                candidate = -candidate
        else:
            candidate /= norm
        residual = float(np.linalg.norm(matrix @ candidate - leading_value * candidate))
        coefficients.append(candidate.copy())
        projectors.append(projector)
        ranks.append(rank)
        residuals.append(residual)
        reference = candidate

    return (
        np.asarray(coefficients),
        np.asarray(projectors),
        np.asarray(ranks, dtype=int),
        np.asarray(residuals),
    )


def oat_analytic_qfi(particles: int, tau: Array | float) -> Array:
    values = np.asarray(tau, dtype=float)
    a_term = 1.0 - np.cos(2.0 * values) ** (particles - 2)
    b_term = 4.0 * np.sin(values) * np.cos(values) ** (particles - 2)
    return particles + particles * (particles - 1) / 4 * (
        a_term + np.sqrt(a_term**2 + b_term**2)
    )


def oat_analytic_axis(particles: int, tau: Array | float) -> Array:
    values = np.asarray(tau, dtype=float)
    a_term = 1.0 - np.cos(2.0 * values) ** (particles - 2)
    b_term = 4.0 * np.sin(values) * np.cos(values) ** (particles - 2)
    delta = np.arctan2(b_term, a_term) / 2.0
    return np.stack([np.zeros_like(delta), np.cos(delta), np.sin(delta)], axis=-1)


def _xy(raising: Sparse) -> tuple[Sparse, Sparse]:
    lowering = raising.getH().tocsr()
    return (
        ((raising + lowering) / 2).tocsr(),
        ((raising - lowering) / (2j)).tocsr(),
    )


def su4_operator_basis(particles: int) -> OperatorBasis:
    space = FixedNBosons(particles, ("u", "d", "s", "c"))
    q_plus = space.bilinear("u", "d")
    sigma_plus = space.bilinear("s", "c")
    m_plus = space.bilinear("u", "c")
    n_plus = space.bilinear("s", "d")
    u_plus = space.bilinear("u", "s")
    v_plus = space.bilinear("c", "d")

    qx, qy = _xy(q_plus)
    sx, sy = _xy(sigma_plus)
    mx, my = _xy(m_plus)
    nx, ny = _xy(n_plus)
    ux, uy = _xy(u_plus)
    vx, vy = _xy(v_plus)

    qz = ((space.number("u") - space.number("d")) / 2).tocsr()
    sz = ((space.number("s") - space.number("c")) / 2).tocsr()
    mz = ((space.number("u") - space.number("c")) / 2).tocsr()
    nz = ((space.number("s") - space.number("d")) / 2).tocsr()
    pz = ((mz - nz) / sqrt(2)).tocsr()

    names = (
        "Qx",
        "Qy",
        "Qz",
        "Sigma_x",
        "Sigma_y",
        "Sigma_z",
        "M_x",
        "M_y",
        "N_x",
        "N_y",
        "P_z",
        "U_x",
        "U_y",
        "V_x",
        "V_y",
    )
    operators = (qx, qy, qz, sx, sy, sz, mx, my, nx, ny, pz, ux, uy, vx, vy)
    return OperatorBasis(names, operators, space)


def su4_hamiltonian(particles: int) -> tuple[Sparse, OperatorBasis]:
    basis = su4_operator_basis(particles)
    space = basis.space
    raising = space.bilinear("u", "d") + space.bilinear("s", "c")
    hamiltonian = (raising @ raising.getH()).tocsr()
    hamiltonian = ((hamiltonian + hamiltonian.getH()) / 2).tocsr()
    return hamiltonian, basis


def su4_initial_state(particles: int, space: FixedNBosons | None = None) -> Array:
    target = space or FixedNBosons(particles, ("u", "d", "s", "c"))
    return target.coherent_state((1 / sqrt(2), 0.0, 0.0, 1 / sqrt(2)))


def evolve_su4(hamiltonian: Sparse, initial: Array, times: Sequence[float]) -> Array:
    points = np.asarray(times, dtype=float)
    if points.ndim != 1 or points.size < 2 or not np.all(np.diff(points) > 0):
        raise ValueError("times must be a strictly increasing one-dimensional grid")
    spacing = np.diff(points)
    if not np.allclose(spacing, spacing[0], rtol=1e-12, atol=1e-14):
        raise ValueError("expm_multiply campaign requires an equally spaced grid")
    states = expm_multiply(
        -1j * hamiltonian,
        np.asarray(initial, dtype=np.complex128),
        start=float(points[0]),
        stop=float(points[-1]),
        num=points.size,
        endpoint=True,
    )
    return np.asarray(states, dtype=np.complex128)


def subgroup_coefficient_bases() -> tuple[Array, Array, Array]:
    """Return orthonormal coefficient bases for the printed J, K, E subgroups."""

    def vector(**entries: float) -> Array:
        names = su4_operator_names()
        result = np.zeros(len(names), dtype=float)
        for name, value in entries.items():
            result[names.index(name)] = value
        result /= np.linalg.norm(result)
        return result

    inv = 1 / sqrt(2)
    j_basis = np.column_stack(
        [
            vector(M_x=inv, N_x=inv),
            vector(M_y=inv, N_y=inv),
            vector(Qz=inv, Sigma_z=inv),
        ]
    )
    k_basis = np.column_stack(
        [
            vector(U_x=inv, V_x=inv),
            vector(U_y=inv, V_y=inv),
            vector(Qz=inv, Sigma_z=-inv),
        ]
    )
    e_basis = np.column_stack(
        [
            vector(Qx=inv, Sigma_x=inv),
            vector(Qy=inv, Sigma_y=inv),
            vector(Qz=inv, Sigma_z=inv),
        ]
    )
    return j_basis, k_basis, e_basis


def su4_operator_names() -> tuple[str, ...]:
    return (
        "Qx",
        "Qy",
        "Qz",
        "Sigma_x",
        "Sigma_y",
        "Sigma_z",
        "M_x",
        "M_y",
        "N_x",
        "N_y",
        "P_z",
        "U_x",
        "U_y",
        "V_x",
        "V_y",
    )


def maximum_subgroup_qfi(matrix: Array) -> float:
    maxima = []
    for coefficients in subgroup_coefficient_bases():
        restricted = coefficients.T @ matrix @ coefficients
        maxima.append(float(np.linalg.eigvalsh(restricted)[-1]))
    return max(maxima)


def generator_qfi(matrix: Array, coefficients: Sequence[float]) -> float:
    vector = np.asarray(coefficients, dtype=float)
    vector /= np.linalg.norm(vector)
    return float(vector @ matrix @ vector)


def normalized_time(tau: Array | float) -> Array:
    return 2 * np.asarray(tau, dtype=float) / pi
