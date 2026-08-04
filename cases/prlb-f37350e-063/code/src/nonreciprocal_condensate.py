"""Independent mean-field model for the nonreciprocal condensate paper.

The implementation follows Eqs. (1)--(5) of the paper and the PBC stability
matrix in the Supplemental Material.  It deliberately contains no routines
for reading paper figures or author-generated numerical data: structured
arrays produced here are the sole input to reproduction renderers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


Array = np.ndarray
Boundary = Literal["open", "periodic"]


@dataclass(frozen=True)
class ModelParameters:
    """Dimensionless parameters, with ``J`` setting the frequency scale."""

    kappa: float
    gamma: float
    theta: float = np.pi
    hopping: float = 1.0
    nonlinear_loss: float = 1.0

    def __post_init__(self) -> None:
        if self.kappa < 0.0:
            raise ValueError("kappa must be nonnegative")
        if self.gamma < 0.0:
            raise ValueError("gamma must be nonnegative")
        if self.hopping <= 0.0:
            raise ValueError("hopping must be positive")
        if self.nonlinear_loss <= 0.0:
            raise ValueError("nonlinear_loss must be positive")


def hatano_nelson_matrix(
    n: int, parameters: ModelParameters, *, boundary: Boundary = "open"
) -> Array:
    """Return the single-particle matrix in ``i d(alpha)/dt = H alpha``."""

    if n < 2:
        raise ValueError("n must be at least two")
    if boundary not in ("open", "periodic"):
        raise ValueError(f"unknown boundary: {boundary}")

    p = parameters
    diagonal = 1j * (p.kappa - 2.0 * p.gamma)
    upper = -(p.hopping + p.gamma * np.exp(1j * p.theta))
    lower = -(p.hopping - p.gamma * np.exp(-1j * p.theta))
    matrix = np.eye(n, dtype=np.complex128) * diagonal
    index = np.arange(n - 1)
    matrix[index, index + 1] = upper
    matrix[index + 1, index] = lower
    if boundary == "periodic":
        matrix[-1, 0] = upper
        matrix[0, -1] = lower
    return matrix


def pbc_decay_and_frequency(
    momentum: Array | float, parameters: ModelParameters
) -> tuple[Array, Array]:
    """Return ``gamma_q`` and ``omega_q`` from Eq. (3)."""

    q = np.asarray(momentum, dtype=float)
    p = parameters
    decay = 2.0 * p.gamma * (1.0 + np.sin(q + p.theta))
    frequency = -2.0 * p.hopping * np.cos(q)
    return decay, frequency


def pbc_amplitude(momentum: Array | float, parameters: ModelParameters) -> Array:
    """Return the plane-wave amplitude, with NaN where the branch is absent."""

    decay, _ = pbc_decay_and_frequency(momentum, parameters)
    density = (parameters.kappa - decay) / parameters.nonlinear_loss
    return np.where(density > 0.0, np.sqrt(np.maximum(density, 0.0)), np.nan)


def pbc_stability_matrix(
    condensate_q: float,
    perturbation_k: Array | float,
    parameters: ModelParameters,
) -> Array:
    """Return the Supplemental-Material 2x2 Bogoliubov matrix.

    The paper prints the corresponding closed-form eigenvalue with a
    ``Lambda**2`` term under the square root.  Direct diagonalization of this
    displayed matrix necessarily gives ``4*Lambda**2``.  We diagonalize the
    matrix itself so that the numerical result follows the stated dynamics.
    """

    k = np.asarray(perturbation_k, dtype=float)
    p = parameters
    decay_q, omega_q = pbc_decay_and_frequency(condensate_q, p)
    density = (p.kappa - float(decay_q)) / p.nonlinear_loss
    if density <= 0.0:
        raise ValueError("the condensate branch does not exist")
    lam = p.nonlinear_loss * density

    decay_k, omega_k = pbc_decay_and_frequency(k, p)
    partner_k = 2.0 * condensate_q - k
    decay_partner, omega_partner = pbc_decay_and_frequency(partner_k, p)
    beta_k = p.kappa - decay_k - 2.0 * lam - 1j * (omega_k - omega_q)
    beta_partner_conjugate = (
        p.kappa
        - decay_partner
        - 2.0 * lam
        + 1j * (omega_partner - omega_q)
    )

    matrix = np.empty(k.shape + (2, 2), dtype=np.complex128)
    matrix[..., 0, 0] = beta_k
    matrix[..., 0, 1] = -lam
    matrix[..., 1, 0] = -lam
    matrix[..., 1, 1] = beta_partner_conjugate
    return matrix


def pbc_max_growth_rate(
    condensate_q: float,
    parameters: ModelParameters,
    *,
    perturbation_count: int = 2048,
    finite_n: int | None = None,
) -> float:
    """Return the maximum real fluctuation eigenvalue for one PBC branch."""

    if finite_n is not None:
        if finite_n < 2:
            raise ValueError("finite_n must be at least two")
        k = 2.0 * np.pi * np.arange(finite_n) / finite_n
    else:
        if perturbation_count < 16:
            raise ValueError("perturbation_count must be at least 16")
        k = np.linspace(-np.pi, np.pi, perturbation_count, endpoint=False)
    eigenvalues = np.linalg.eigvals(
        pbc_stability_matrix(condensate_q, k, parameters)
    )
    return float(np.max(eigenvalues.real))


def complex_rhs(
    alpha: Array,
    parameters: ModelParameters,
    *,
    boundary: Boundary = "open",
) -> Array:
    """Return the mean-field vector field obtained from Eq. (2)."""

    state = np.asarray(alpha, dtype=np.complex128)
    if state.ndim < 1 or state.shape[-1] < 2:
        raise ValueError("alpha must end in a site axis of length at least two")
    if boundary not in ("open", "periodic"):
        raise ValueError(f"unknown boundary: {boundary}")

    p = parameters
    result = (
        p.kappa - 2.0 * p.gamma - p.nonlinear_loss * np.abs(state) ** 2
    ) * state
    upper = 1j * (p.hopping + p.gamma * np.exp(1j * p.theta))
    lower = 1j * (p.hopping - p.gamma * np.exp(-1j * p.theta))
    result[..., :-1] += upper * state[..., 1:]
    result[..., 1:] += lower * state[..., :-1]
    if boundary == "periodic":
        result[..., -1] += upper * state[..., 0]
        result[..., 0] += lower * state[..., -1]
    return result


def to_real(alpha: Array) -> Array:
    """Map a complex site vector to the real ordering ``(x_1..x_N,y_1..y_N)``."""

    state = np.asarray(alpha, dtype=np.complex128)
    if state.ndim != 1:
        raise ValueError("alpha must be one-dimensional")
    return np.concatenate((state.real, state.imag))


def from_real(state: Array) -> Array:
    """Inverse of :func:`to_real`."""

    values = np.asarray(state, dtype=float)
    if values.ndim != 1 or values.size % 2:
        raise ValueError("state must be a one-dimensional even-length vector")
    n = values.size // 2
    return values[:n] + 1j * values[n:]


def real_rhs(
    state: Array,
    parameters: ModelParameters,
    *,
    boundary: Boundary = "open",
) -> Array:
    """Return Eq. (2) as a real 2N-dimensional vector field."""

    return to_real(complex_rhs(from_real(state), parameters, boundary=boundary))


def real_jacobian(
    alpha: Array,
    parameters: ModelParameters,
    *,
    boundary: Boundary = "open",
) -> Array:
    """Return the exact real Jacobian of the mean-field vector field."""

    state = np.asarray(alpha, dtype=np.complex128)
    if state.ndim != 1 or state.size < 2:
        raise ValueError("alpha must be a one-dimensional site vector")
    if boundary not in ("open", "periodic"):
        raise ValueError(f"unknown boundary: {boundary}")

    p = parameters
    n = state.size
    jacobian = np.zeros((2 * n, 2 * n), dtype=float)

    def add_wirtinger(row: int, column: int, c: complex, d: complex = 0j) -> None:
        derivative_x = c + d
        derivative_y = 1j * (c - d)
        jacobian[row, column] += derivative_x.real
        jacobian[row + n, column] += derivative_x.imag
        jacobian[row, column + n] += derivative_y.real
        jacobian[row + n, column + n] += derivative_y.imag

    for site, value in enumerate(state):
        c = p.kappa - 2.0 * p.gamma - 2.0 * p.nonlinear_loss * abs(value) ** 2
        d = -p.nonlinear_loss * value**2
        add_wirtinger(site, site, c, d)

    upper = 1j * (p.hopping + p.gamma * np.exp(1j * p.theta))
    lower = 1j * (p.hopping - p.gamma * np.exp(-1j * p.theta))
    for site in range(n - 1):
        add_wirtinger(site, site + 1, upper)
        add_wirtinger(site + 1, site, lower)
    if boundary == "periodic":
        add_wirtinger(n - 1, 0, upper)
        add_wirtinger(0, n - 1, lower)
    return jacobian


def tangent_rhs(
    alpha: Array,
    perturbation: Array,
    parameters: ModelParameters,
    *,
    boundary: Boundary = "open",
) -> Array:
    """Apply the exact tangent dynamics to one or more complex perturbations.

    ``perturbation`` may have arbitrary leading axes and must end in the same
    site axis as ``alpha``.  Each complex vector represents one real tangent
    vector through its real and imaginary parts.
    """

    state = np.asarray(alpha, dtype=np.complex128)
    delta = np.asarray(perturbation, dtype=np.complex128)
    if state.ndim != 1 or delta.shape[-1] != state.size:
        raise ValueError("alpha must be 1D and perturbations must share its site axis")
    if boundary not in ("open", "periodic"):
        raise ValueError(f"unknown boundary: {boundary}")

    p = parameters
    onsite = p.kappa - 2.0 * p.gamma - 2.0 * p.nonlinear_loss * np.abs(state) ** 2
    result = onsite * delta - p.nonlinear_loss * state**2 * delta.conj()
    upper = 1j * (p.hopping + p.gamma * np.exp(1j * p.theta))
    lower = 1j * (p.hopping - p.gamma * np.exp(-1j * p.theta))
    result[..., :-1] += upper * delta[..., 1:]
    result[..., 1:] += lower * delta[..., :-1]
    if boundary == "periodic":
        result[..., -1] += upper * delta[..., 0]
        result[..., 0] += lower * delta[..., -1]
    return result


def rk4_state_tangent_step(
    alpha: Array,
    perturbation: Array,
    dt: float,
    parameters: ModelParameters,
    *,
    boundary: Boundary = "open",
) -> tuple[Array, Array]:
    """Advance Eq. (2) and its tangent flow with a shared RK4 step."""

    if dt <= 0.0:
        raise ValueError("dt must be positive")
    state = np.asarray(alpha, dtype=np.complex128)
    tangent = np.asarray(perturbation, dtype=np.complex128)
    k1_state = complex_rhs(state, parameters, boundary=boundary)
    k1_tangent = tangent_rhs(state, tangent, parameters, boundary=boundary)

    state_2 = state + 0.5 * dt * k1_state
    tangent_2 = tangent + 0.5 * dt * k1_tangent
    k2_state = complex_rhs(state_2, parameters, boundary=boundary)
    k2_tangent = tangent_rhs(state_2, tangent_2, parameters, boundary=boundary)

    state_3 = state + 0.5 * dt * k2_state
    tangent_3 = tangent + 0.5 * dt * k2_tangent
    k3_state = complex_rhs(state_3, parameters, boundary=boundary)
    k3_tangent = tangent_rhs(state_3, tangent_3, parameters, boundary=boundary)

    state_4 = state + dt * k3_state
    tangent_4 = tangent + dt * k3_tangent
    k4_state = complex_rhs(state_4, parameters, boundary=boundary)
    k4_tangent = tangent_rhs(state_4, tangent_4, parameters, boundary=boundary)

    next_state = state + (dt / 6.0) * (
        k1_state + 2.0 * k2_state + 2.0 * k3_state + k4_state
    )
    next_tangent = tangent + (dt / 6.0) * (
        k1_tangent + 2.0 * k2_tangent + 2.0 * k3_tangent + k4_tangent
    )
    return next_state, next_tangent


def rk4_step(
    alpha: Array,
    dt: float,
    parameters: ModelParameters,
    *,
    boundary: Boundary = "open",
) -> Array:
    """Advance one deterministic fourth-order Runge--Kutta step."""

    if dt <= 0.0:
        raise ValueError("dt must be positive")
    state = np.asarray(alpha, dtype=np.complex128)
    k1 = complex_rhs(state, parameters, boundary=boundary)
    k2 = complex_rhs(state + 0.5 * dt * k1, parameters, boundary=boundary)
    k3 = complex_rhs(state + 0.5 * dt * k2, parameters, boundary=boundary)
    k4 = complex_rhs(state + dt * k3, parameters, boundary=boundary)
    return state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate_trajectory(
    alpha_0: Array,
    parameters: ModelParameters,
    *,
    dt: float,
    steps: int,
    sample_every: int = 1,
    boundary: Boundary = "open",
) -> tuple[Array, Array]:
    """Integrate Eq. (2) and return sampled times and complex states."""

    if steps < 0:
        raise ValueError("steps must be nonnegative")
    if sample_every < 1:
        raise ValueError("sample_every must be positive")
    state = np.asarray(alpha_0, dtype=np.complex128).copy()
    times = [0.0]
    samples = [state.copy()]
    for step in range(1, steps + 1):
        state = rk4_step(state, dt, parameters, boundary=boundary)
        if step % sample_every == 0:
            times.append(step * dt)
            samples.append(state.copy())
    return np.asarray(times), np.asarray(samples)


def static_amplitude_residual(amplitude: Array, parameters: ModelParameters) -> Array:
    """Return the real static-state equations for ``alpha_j=i**(j+1) r_j``.

    This reduction is valid for open boundaries and ``theta=pi``.  It fixes
    the otherwise arbitrary global U(1) phase and exposes the paper's static
    kink as a real nonlinear boundary-value problem.
    """

    if not np.isclose(np.mod(parameters.theta, 2.0 * np.pi), np.pi):
        raise ValueError("the real static reduction requires theta=pi")
    r = np.asarray(amplitude, dtype=float)
    if r.ndim != 1 or r.size < 2:
        raise ValueError("amplitude must be a one-dimensional site vector")
    p = parameters
    result = (p.kappa - 2.0 * p.gamma - p.nonlinear_loss * r**2) * r
    result[:-1] -= (p.hopping - p.gamma) * r[1:]
    result[1:] += (p.hopping + p.gamma) * r[:-1]
    return result


def static_amplitude_jacobian(amplitude: Array, parameters: ModelParameters) -> Array:
    """Return the exact Jacobian of :func:`static_amplitude_residual`."""

    r = np.asarray(amplitude, dtype=float)
    p = parameters
    n = r.size
    matrix = np.diag(
        p.kappa - 2.0 * p.gamma - 3.0 * p.nonlinear_loss * r**2
    )
    index = np.arange(n - 1)
    matrix[index, index + 1] = -(p.hopping - p.gamma)
    matrix[index + 1, index] = p.hopping + p.gamma
    return matrix


def static_complex_state(amplitude: Array) -> Array:
    """Lift a real static amplitude profile into the complex OBC state."""

    r = np.asarray(amplitude, dtype=float)
    sites = np.arange(1, r.size + 1)
    return (1j**sites) * r


def finite_n_vacuum_threshold(n: int, gamma: float, *, hopping: float = 1.0) -> float:
    """Return the exact first OBC vacuum instability from Eq. (5)."""

    if n < 2 or gamma < 0.0 or hopping <= 0.0:
        raise ValueError("invalid n, gamma, or hopping")
    if gamma <= hopping:
        return 2.0 * gamma
    return float(
        2.0 * gamma
        - 2.0
        * np.sqrt(gamma**2 - hopping**2)
        * np.cos(np.pi / (n + 1))
    )


def thermodynamic_vacuum_threshold(gamma: Array | float, *, hopping: float = 1.0) -> Array:
    """Return the thermodynamic OBC vacuum boundary from Eq. (5)."""

    values = np.asarray(gamma, dtype=float)
    if np.any(values < 0.0) or hopping <= 0.0:
        raise ValueError("invalid gamma or hopping")
    return np.where(
        values <= hopping,
        2.0 * values,
        2.0 * values - 2.0 * np.sqrt(np.maximum(values**2 - hopping**2, 0.0)),
    )
