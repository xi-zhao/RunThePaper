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
from scipy.sparse.linalg import ArpackNoConvergence, eigs, eigsh
from scipy.special import airy, eval_hermite, gammaln, roots_hermite


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


@dataclass(frozen=True)
class ClassicalTrajectory:
    """A continuously unwrapped classical orbit on the Riemann surface."""

    time: np.ndarray
    position: np.ndarray
    momentum: np.ndarray
    unwrapped_z_angle: np.ndarray
    energy_max_abs_error: float


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
    linear_coefficient: complex = 0.0,
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
        potential = (
            mass_squared * x * x
            - np.power(1j * x, float(exponent))
            + complex(linear_coefficient) * x
        )
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
    linear_coefficient: complex = 0.0,
) -> np.ndarray:
    """Return deterministic low-energy eigenvalues sorted by real part."""

    matrix, _ = build_contour_hamiltonian(
        exponent,
        mass_squared=mass_squared,
        half_width=half_width,
        points=points,
        bend_scale=bend_scale,
        use_complex_contour=use_complex_contour,
        linear_coefficient=linear_coefficient,
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


def complex_wkb_turning_points(
    exponent: float, energy: float
) -> tuple[complex, complex]:
    """Return the analytically continued turning points printed in Eq. (4)."""

    if exponent <= 0:
        raise ValueError("exponent must be positive")
    if energy <= 0:
        raise ValueError("energy must be positive")
    radius = float(energy) ** (1.0 / float(exponent))
    left = radius * np.exp(1j * np.pi * (1.5 - 1.0 / float(exponent)))
    right = radius * np.exp(-1j * np.pi * (0.5 - 1.0 / float(exponent)))
    return complex(left), complex(right)


def wkb_branch_cut_intersection_imag(exponent: float, energy: float) -> float:
    """Imaginary coordinate where the straight WKB segment meets Re(x)=0.

    For the principal continuation of ``(i x)^N``, the branch cut in the
    x-plane is the positive imaginary axis.  Thus a positive return value is a
    direct geometric obstruction, rather than a restatement of ``N < 2``.
    """

    left, right = complex_wkb_turning_points(exponent, energy)
    denominator = right.real - left.real
    if abs(denominator) < 1e-15:
        raise RuntimeError("turning-point segment does not cross the imaginary axis")
    fraction = -left.real / denominator
    if not 0.0 <= fraction <= 1.0:
        raise RuntimeError("imaginary-axis crossing lies outside the WKB segment")
    crossing = left + fraction * (right - left)
    return float(crossing.imag)


def exceptional_point_discriminant(
    exponent: float,
    *,
    half_width: float,
    points: int,
    eigenvalues: int,
    shift: float,
    tolerance: float,
) -> float:
    """Signed first-excited-pair discriminant for the massless transition.

    Below the exceptional point the pair is complex conjugate and
    ``Re[(E_2-E_1)^2] < 0``; above it both levels are real and the same
    discriminant is positive.  No printed threshold enters this observable.
    """

    values = low_spectrum(
        exponent,
        half_width=half_width,
        points=points,
        eigenvalues=max(4, eigenvalues),
        shift=shift,
        tolerance=tolerance,
        use_complex_contour=False,
    )
    pair_gap_squared = (values[2] - values[1]) ** 2
    return float(pair_gap_squared.real)


def locate_exceptional_point(
    lower: float,
    upper: float,
    *,
    half_width: float,
    points: int,
    eigenvalues: int,
    shift: float,
    tolerance: float,
    root_tolerance: float = 1e-10,
) -> float:
    """Locate the first excited-pair exceptional point by sign bracketing."""

    if not 1.0 < lower < upper < 2.0:
        raise ValueError("exceptional-point bracket must lie inside 1<N<2")

    def discriminant(exponent: float) -> float:
        return exceptional_point_discriminant(
            exponent,
            half_width=half_width,
            points=points,
            eigenvalues=eigenvalues,
            shift=shift,
            tolerance=tolerance,
        )

    return float(
        brentq(
            discriminant,
            lower,
            upper,
            xtol=root_tolerance,
            rtol=max(4.0 * np.finfo(float).eps, root_tolerance),
        )
    )


def hermitian_wkb_energy(exponent: float, level: int) -> float:
    """Leading WKB energy for ``p^2 + |x|^N`` stated after Eq. (5)."""

    if exponent <= 0:
        raise ValueError("exponent must be positive")
    if level < 0:
        raise ValueError("level must be nonnegative")
    log_base = (
        gammaln(1.5 + 1.0 / exponent)
        + 0.5 * np.log(np.pi)
        + np.log(level + 0.5)
        - gammaln(1.0 + 1.0 / exponent)
    )
    return float(np.exp((2.0 * exponent / (exponent + 2.0)) * log_base))


def square_well_energy(level: int) -> float:
    """Energy of the width-two infinite square well used in the paper."""

    if level < 0:
        raise ValueError("level must be nonnegative")
    return float((level + 1) ** 2 * np.pi**2 / 4.0)


def hermitian_low_spectrum(
    exponent: float,
    *,
    half_width: float = 1.5,
    points: int = 2400,
    eigenvalues: int = 4,
    tolerance: float = 1e-11,
) -> np.ndarray:
    """Independently diagonalize ``p^2 + |x|^N`` on the real axis."""

    if exponent <= 0:
        raise ValueError("exponent must be positive")
    if half_width <= 1.0:
        raise ValueError("half_width must extend beyond the limiting well")
    if points < 20:
        raise ValueError("points must be at least 20")
    full_grid = np.linspace(-half_width, half_width, points + 2)
    x = full_grid[1:-1]
    step = full_grid[1] - full_grid[0]
    off_diagonal = np.full(points - 1, -1.0 / step**2)
    diagonal = 2.0 / step**2 + np.abs(x) ** float(exponent)
    matrix = diags(
        [off_diagonal, diagonal, off_diagonal],
        offsets=[-1, 0, 1],
        format="csc",
        dtype=float,
    )
    count = min(int(eigenvalues), points - 3)
    values = eigsh(
        matrix,
        k=count,
        sigma=0.0,
        which="LM",
        tol=tolerance,
        return_eigenvectors=False,
    )
    return np.sort(np.asarray(values, dtype=float))


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


def massive_n0_energy(mass_squared: float, level: int) -> float:
    """Exact massive spectrum at N=0: ``p^2 + m^2 x^2 - 1``."""

    if mass_squared <= 0:
        raise ValueError("mass_squared must be positive")
    if level < 0:
        raise ValueError("level must be nonnegative")
    return float((2 * level + 1) * np.sqrt(mass_squared) - 1.0)


def massive_n2_energy(mass_squared: float, level: int) -> float:
    """Exact massive spectrum at N=2: ``p^2 + (m^2+1) x^2``."""

    if mass_squared < 0:
        raise ValueError("mass_squared must be nonnegative")
    if level < 0:
        raise ValueError("level must be nonnegative")
    return float((2 * level + 1) * np.sqrt(mass_squared + 1.0))


def near_n2_two_level_merger(
    level: int, *, quadrature_order: int = 256
) -> dict[str, float]:
    """First-order two-level discriminant for ``N=2-epsilon``.

    Expanding the printed Hamiltonian gives

    ``H = H_osc - epsilon*x^2*(log|x| + i*pi*sgn(x)/2)``.

    The even real term is diagonal within an adjacent parity pair, while the
    odd imaginary term produces a complex-symmetric off-diagonal coupling.
    Consequently the level-splitting discriminant contains ``-4 c^2`` rather
    than the ``+4 c^2`` of a Hermitian avoided crossing.  Its positive zero is
    a clean, source-pixel-free diagnostic of level coalescence.
    """

    if level < 0:
        raise ValueError("level must be nonnegative")
    if quadrature_order < 32:
        raise ValueError("quadrature_order must be at least 32")

    nodes, weights = roots_hermite(int(quadrature_order))

    def normalization(index: int) -> float:
        log_norm_squared = (
            index * np.log(2.0) + gammaln(index + 1.0) + 0.5 * np.log(np.pi)
        )
        return float(np.exp(-0.5 * log_norm_squared))

    def matrix_element(left: int, right: int, operator_values: np.ndarray) -> float:
        value = (
            normalization(left)
            * normalization(right)
            * np.sum(
                weights
                * eval_hermite(left, nodes)
                * eval_hermite(right, nodes)
                * operator_values
            )
        )
        return float(value)

    with np.errstate(divide="ignore", invalid="raise"):
        even_operator = nodes * nodes * np.log(np.abs(nodes))
    odd_operator = nodes * nodes * np.sign(nodes)
    diagonal_lower = -matrix_element(level, level, even_operator)
    diagonal_upper = -matrix_element(level + 1, level + 1, even_operator)
    imaginary_coupling = -0.5 * np.pi * matrix_element(level, level + 1, odd_operator)
    diagonal_difference = diagonal_upper - diagonal_lower
    denominator = 2.0 * abs(imaginary_coupling) - diagonal_difference
    if denominator <= 0:
        raise RuntimeError("two-level approximation has no positive merger")
    epsilon_merger = 2.0 / denominator
    return {
        "level_lower": float(level),
        "diagonal_lower": diagonal_lower,
        "diagonal_upper": diagonal_upper,
        "imaginary_coupling": imaginary_coupling,
        "epsilon_merger": float(epsilon_merger),
    }


def shifted_oscillator_energy(linear_coefficient: complex, level: int) -> complex:
    """Exact spectrum of ``p^2+x^2+b x`` by completing the square."""

    if level < 0:
        raise ValueError("level must be nonnegative")
    coefficient = complex(linear_coefficient)
    return complex(2 * level + 1) - coefficient**2 / 4.0


def stokes_wedge_angles(exponent: float) -> dict[str, float]:
    """Return the two wedge centers and opening printed in Eq. (3)."""

    if exponent <= 0:
        raise ValueError("exponent must be positive")
    offset = (exponent - 2.0) * np.pi / (2.0 * (exponent + 2.0))
    return {
        "left_center": float(-np.pi + offset),
        "right_center": float(-offset),
        "opening": float(2.0 * np.pi / (exponent + 2.0)),
    }


def airy_matching_derivative(energy: float) -> float:
    """Evaluate the N=1 matching derivative in Eq. (7) directly."""

    if not np.isfinite(energy):
        raise ValueError("energy must be finite")
    argument = float(energy) * np.exp(-2j * np.pi / 3.0)
    ai_value, ai_derivative, _, _ = airy(argument)
    direction = np.exp(-1j * np.pi / 6.0)
    return float(2.0 * np.real(np.conj(ai_value) * ai_derivative * direction))


def classical_period(energy: float, exponent: float) -> float:
    """Real classical period for the periodic N>=2 branch, Eq. (12)."""

    if energy <= 0 or exponent < 2:
        raise ValueError("the printed finite-period branch requires E>0 and N>=2")
    prefactor = 2.0 * energy ** ((2.0 - exponent) / (2.0 * exponent))
    angle = np.cos((exponent - 2.0) * np.pi / (2.0 * exponent))
    gamma_ratio = np.exp(gammaln(1.0 + 1.0 / exponent) - gammaln(0.5 + 1.0 / exponent))
    return float(prefactor * angle * gamma_ratio * np.sqrt(np.pi))


def classical_escape_angle(exponent: float) -> float:
    """Asymptotic escape angle of the N<2 classical spiral."""

    if not 0 < exponent < 2:
        raise ValueError("escape-angle branch requires 0<N<2")
    return float(exponent * np.pi / (2.0 - exponent))


def turning_point_angle(exponent: float, index: int) -> float:
    """Angle of the indexed turning point quoted below Eq. (12)."""

    if exponent <= 0 or index < 0:
        raise ValueError("exponent must be positive and index nonnegative")
    return float((4 * index - exponent + 2.0) * np.pi / (2.0 * exponent))


def classical_spiral_trajectory(
    exponent: float,
    energy: float,
    *,
    maximum_time: float,
    samples: int,
    maximum_step: float,
    relative_tolerance: float = 1e-11,
    absolute_tolerance: float = 1e-13,
) -> ClassicalTrajectory:
    """Integrate the subcritical orbit with a continuously unwrapped phase.

    Writing ``z=i*x=exp(q+i*theta)`` keeps ``z**N`` on the continuously
    followed Riemann sheet.  Integrating ``q, theta, p`` therefore avoids the
    principal-branch reset that would erase the sheet-to-sheet spiral.
    """

    if not 0.0 < exponent < 2.0:
        raise ValueError("the spiral trajectory requires 0<N<2")
    if energy <= 0.0 or maximum_time <= 0.0 or maximum_step <= 0.0:
        raise ValueError("energy, maximum_time, and maximum_step must be positive")
    if samples < 3:
        raise ValueError("samples must be at least three")

    log_radius = np.log(energy) / exponent
    initial_angle = np.pi / exponent

    def rhs(_time: float, state: np.ndarray) -> np.ndarray:
        q, theta, momentum_real, momentum_imag = state
        z = np.exp(q + 1j * theta)
        position = -1j * z
        momentum = complex(momentum_real, momentum_imag)
        logarithmic_velocity = 2.0 * momentum / position
        force = exponent * 1j * np.exp((exponent - 1.0) * (q + 1j * theta))
        return np.array(
            [
                logarithmic_velocity.real,
                logarithmic_velocity.imag,
                force.real,
                force.imag,
            ],
            dtype=float,
        )

    times = np.linspace(0.0, maximum_time, int(samples))
    solution = solve_ivp(
        rhs,
        (0.0, maximum_time),
        np.array([log_radius, initial_angle, 0.0, 0.0]),
        t_eval=times,
        method="DOP853",
        rtol=relative_tolerance,
        atol=absolute_tolerance,
        max_step=maximum_step,
    )
    if not solution.success or len(solution.t) != len(times):
        raise RuntimeError(f"classical spiral integration failed: {solution.message}")

    q, theta, momentum_real, momentum_imag = solution.y
    z = np.exp(q + 1j * theta)
    position = -1j * z
    momentum = momentum_real + 1j * momentum_imag
    continuous_potential = np.exp(exponent * (q + 1j * theta))
    hamiltonian = momentum * momentum - continuous_potential
    energy_error = float(np.max(np.abs(hamiltonian - energy)))
    return ClassicalTrajectory(
        time=np.asarray(solution.t),
        position=np.asarray(position),
        momentum=np.asarray(momentum),
        unwrapped_z_angle=np.asarray(theta),
        energy_max_abs_error=energy_error,
    )


def turning_point_passages(
    trajectory: ClassicalTrajectory,
    exponent: float,
    energy: float,
) -> list[dict[str, float]]:
    """Interpolate every new turning-point angle passed by one orbit."""

    angles = np.asarray(trajectory.unwrapped_z_angle, dtype=float)
    if np.any(np.diff(angles) < -1e-9):
        raise RuntimeError("turning-point passage extraction requires monotone angle")
    log_radius = np.log(energy) / exponent
    radii = np.abs(trajectory.position)
    passages: list[dict[str, float]] = []
    index = 1  # n=0 is the initial turning point.
    while True:
        z_angle = (2 * index + 1) * np.pi / exponent
        if z_angle > angles[-1]:
            break
        passage_time = float(np.interp(z_angle, angles, trajectory.time))
        passage_radius = float(np.interp(passage_time, trajectory.time, radii))
        passages.append(
            {
                "turning_point_index": float(index),
                "time": passage_time,
                "x_angle": turning_point_angle(exponent, index),
                "radial_miss_distance": abs(passage_radius - np.exp(log_radius)),
            }
        )
        index += 1
    return passages


def turning_points_before_escape(exponent: float) -> int:
    """Count printed turning-point angles reached before the escape ray."""

    if not 0.0 < exponent < 2.0:
        raise ValueError("escape counting requires 0<N<2")
    escape = classical_escape_angle(exponent)
    count = 0
    while turning_point_angle(exponent, count) <= escape + 1e-12:
        count += 1
        if count > 1_000_000:
            raise RuntimeError("turning-point count did not terminate")
    return count
