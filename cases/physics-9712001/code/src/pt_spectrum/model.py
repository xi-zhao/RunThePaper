"""Clean-room solvers for H=p^2+m^2 x^2-(i x)^N.

No routine in this module reads paper figures, author arrays, or raw sources.
The complex contour is derived directly from Eq. (3) of the paper.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.sparse import csc_matrix, diags
from scipy.sparse.linalg import ArpackNoConvergence, eigs
from scipy.special import gammaln


@dataclass(frozen=True)
class ContourGeometry:
    parameter: np.ndarray
    x: np.ndarray
    first_derivative: np.ndarray
    second_derivative: np.ndarray
    alpha: float


@dataclass(frozen=True)
class ShootingResult:
    energy: float
    residual: float
    bracket: tuple[float, float]
    evaluations: int


def contour_geometry(
    parameter: np.ndarray,
    exponent: float,
    *,
    bend_scale: float = 2.0,
    use_complex_contour: bool = True,
) -> ContourGeometry:
    """Return a smooth PT-symmetric contour and its derivatives.

    At large |t| the right and left endpoints approach the anti-Stokes ray
    centers printed in Eq. (3). The bend scale only changes the interpolation
    near the origin and is therefore a convergence parameter, not fitted
    physics.
    """

    t = np.asarray(parameter, dtype=float)
    if bend_scale <= 0:
        raise ValueError("bend_scale must be positive")
    alpha = (
        (float(exponent) - 2.0) * np.pi / (2.0 * (float(exponent) + 2.0))
        if use_complex_contour
        else 0.0
    )
    radius = np.sqrt(t * t + bend_scale * bend_scale)
    bend = radius - bend_scale
    bend_prime = t / radius
    bend_second = bend_scale * bend_scale / radius**3
    x = np.cos(alpha) * t - 1j * np.sin(alpha) * bend
    first = np.cos(alpha) - 1j * np.sin(alpha) * bend_prime
    second = -1j * np.sin(alpha) * bend_second
    return ContourGeometry(t, x, first, second, float(alpha))


def build_contour_hamiltonian(
    exponent: float,
    *,
    mass_squared: float = 0.0,
    half_width: float = 7.0,
    points: int = 1600,
    bend_scale: float = 2.0,
    use_complex_contour: bool | None = None,
) -> tuple[csc_matrix, ContourGeometry]:
    """Discretize the PT-symmetric Schrodinger operator.

    Massive targets use the real axis because m^2 x^2 controls their
    asymptotics. The massless problem uses the printed lower-half-plane
    anti-Stokes contour for N>2 and the real axis otherwise.
    """

    if points < 20:
        raise ValueError("points must be at least 20")
    if half_width <= 0:
        raise ValueError("half_width must be positive")
    if mass_squared < 0:
        raise ValueError("mass_squared must be nonnegative")
    if use_complex_contour is None:
        use_complex_contour = mass_squared == 0.0 and exponent > 2.0

    full_grid = np.linspace(-half_width, half_width, points + 2)
    t = full_grid[1:-1]
    step = full_grid[1] - full_grid[0]
    geometry = contour_geometry(
        t,
        exponent,
        bend_scale=bend_scale,
        use_complex_contour=use_complex_contour,
    )
    x = geometry.x
    xp = geometry.first_derivative
    xpp = geometry.second_derivative

    with np.errstate(divide="raise", invalid="raise", over="raise"):
        potential = mass_squared * x * x - np.power(1j * x, float(exponent))
        lower = -1.0 / (xp * xp * step * step) - xpp / (2.0 * xp**3 * step)
        diagonal = 2.0 / (xp * xp * step * step) + potential
        upper = -1.0 / (xp * xp * step * step) + xpp / (2.0 * xp**3 * step)
    matrix = diags(
        [lower[1:], diagonal, upper[:-1]],
        offsets=[-1, 0, 1],
        format="csc",
        dtype=np.complex128,
    )
    return matrix, geometry


def low_spectrum(
    exponent: float,
    *,
    mass_squared: float = 0.0,
    half_width: float = 7.0,
    points: int = 1600,
    bend_scale: float = 2.0,
    eigenvalues: int = 12,
    shift: float = 6.0,
    tolerance: float = 1e-10,
    max_iterations: int = 50_000,
    use_complex_contour: bool | None = None,
) -> np.ndarray:
    """Return deterministic low-energy eigenvalues sorted by real part."""

    matrix, _ = build_contour_hamiltonian(
        exponent,
        mass_squared=mass_squared,
        half_width=half_width,
        points=points,
        bend_scale=bend_scale,
        use_complex_contour=use_complex_contour,
    )
    count = min(int(eigenvalues), points - 3)
    ramp = np.linspace(-1.0, 1.0, points)
    initial = 1.0 + 0.17 * ramp + 0.11j * (ramp * ramp - 0.3)
    initial = initial.astype(np.complex128)
    initial /= np.linalg.norm(initial)
    try:
        values = eigs(
            matrix,
            k=count,
            sigma=complex(shift),
            which="LM",
            v0=initial,
            tol=tolerance,
            maxiter=max_iterations,
            return_eigenvectors=False,
        )
    except ArpackNoConvergence as exc:
        if exc.eigenvalues is None or len(exc.eigenvalues) < count // 2:
            raise
        values = exc.eigenvalues
    order = np.lexsort((np.abs(values.imag), values.real))
    return np.asarray(values[order], dtype=np.complex128)


def wkb_energy(exponent: float, level: int) -> float:
    """Leading complex-WKB energy from Eq. (5)."""

    if exponent <= 1:
        raise ValueError("the printed WKB branch requires N>1")
    if level < 0:
        raise ValueError("level must be nonnegative")
    log_base = (
        gammaln(1.5 + 1.0 / exponent)
        + 0.5 * np.log(np.pi)
        + np.log(level + 0.5)
        - np.log(np.sin(np.pi / exponent))
        - gammaln(1.0 + 1.0 / exponent)
    )
    return float(np.exp((2.0 * exponent / (exponent + 2.0)) * log_base))


def near_one_asymptotic_energy(epsilon: float) -> float:
    """Solve the implicit asymptotic equation (11) in the log domain."""

    if not 0 < epsilon < 1:
        raise ValueError("epsilon must lie in (0,1)")

    def residual(energy: float) -> float:
        bracket = (
            np.sqrt(3.0) * np.log(2.0 * np.sqrt(energy))
            + np.pi
            - (1.0 - np.euler_gamma) * np.sqrt(3.0)
        ) / 8.0
        if bracket <= 0:
            return -np.inf
        return float(
            np.log(epsilon)
            - 1.5 * np.log(energy)
            + (4.0 / 3.0) * energy**1.5
            + np.log(bracket)
        )

    return float(brentq(residual, 0.25, 100.0, xtol=1e-13, rtol=1e-13))


def shooting_patch_residual(
    energy: float,
    exponent: float,
    *,
    boundary: float = 40.0,
    relative_tolerance: float = 1e-11,
    absolute_tolerance: float = 1e-12,
    max_step: float = 0.03,
) -> float:
    """Evaluate Re[psi'(0)/psi(0)] for the decaying right solution."""

    if energy <= 0 or exponent <= 1 or boundary <= 0:
        raise ValueError("energy, N-1, and boundary must be positive")

    def potential(x: float) -> complex:
        return -complex(1j * x) ** exponent

    q = potential(boundary) - energy
    root = np.sqrt(q)
    if root.real < 0:
        root = -root
    derivative = -exponent * 1j * complex(1j * boundary) ** (exponent - 1.0)
    initial = -root - derivative / (4.0 * q)

    def rhs(x: float, vector: np.ndarray) -> np.ndarray:
        value = complex(vector[0], vector[1])
        slope = potential(x) - energy - value * value
        return np.array([slope.real, slope.imag], dtype=float)

    solution = solve_ivp(
        rhs,
        (boundary, 0.0),
        np.array([initial.real, initial.imag]),
        method="DOP853",
        rtol=relative_tolerance,
        atol=absolute_tolerance,
        max_step=max_step,
    )
    if not solution.success:
        raise RuntimeError(f"Riccati integration failed: {solution.message}")
    return float(solution.y[0, -1])


def ground_state_shooting(
    exponent: float,
    *,
    boundary: float = 40.0,
    relative_tolerance: float = 1e-11,
    absolute_tolerance: float = 1e-12,
    max_step: float = 0.03,
) -> ShootingResult:
    """Find the massless real ground state without paper table values."""

    epsilon = exponent - 1.0
    if not 0 < epsilon <= 0.5:
        raise ValueError("shooting helper is restricted to 1<N<=1.5")
    center = near_one_asymptotic_energy(epsilon)
    low = max(0.05, 0.45 * center)
    high = 1.35 * center
    evaluations = 0

    def residual(energy: float) -> float:
        nonlocal evaluations
        evaluations += 1
        return shooting_patch_residual(
            energy,
            exponent,
            boundary=boundary,
            relative_tolerance=relative_tolerance,
            absolute_tolerance=absolute_tolerance,
            max_step=max_step,
        )

    f_low = residual(low)
    f_high = residual(high)
    for _ in range(8):
        if f_low == 0 or f_high == 0 or np.signbit(f_low) != np.signbit(f_high):
            break
        low = max(0.02, 0.7 * low)
        high *= 1.3
        f_low = residual(low)
        f_high = residual(high)
    else:
        raise RuntimeError(
            f"could not bracket ground state for N={exponent}: "
            f"f({low})={f_low}, f({high})={f_high}"
        )
    energy = float(brentq(residual, low, high, xtol=1e-12, rtol=1e-12))
    final_residual = residual(energy)
    return ShootingResult(
        energy, final_residual, (float(low), float(high)), evaluations
    )


def massive_n1_energy(mass_squared: float, level: int) -> float:
    """Exact shifted-oscillator spectrum at N=1."""

    if mass_squared <= 0:
        raise ValueError("mass_squared must be positive")
    if level < 0:
        raise ValueError("level must be nonnegative")
    return float((2 * level + 1) * np.sqrt(mass_squared) + 1.0 / (4.0 * mass_squared))
