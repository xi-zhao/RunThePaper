"""Damped Jaynes--Cummings formulas derived independently from the paper.

The scientific generator uses only printed equations and parameters.  In
particular, it never reads a source figure.  The survival amplitude is written
with a regularized ``sinh(z)/z`` so the critical point ``gamma0=lambda/2`` is
well conditioned and the non-Markovian regime is evaluated without integrating
the singular time-local decay rate through its poles.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def _sinhc(value: np.ndarray | complex) -> np.ndarray:
    z = np.asarray(value, dtype=complex)
    out = np.empty_like(z)
    small = np.abs(z) < 1.0e-7
    z2 = z[small] * z[small]
    out[small] = 1.0 + z2 / 6.0 + z2 * z2 / 120.0
    out[~small] = np.sinh(z[~small]) / z[~small]
    return out


def survival_amplitude(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return the exact excited-state amplitude G(t).

    It solves ``G'' + lambda G' + gamma0*lambda*G/2 = 0`` with
    ``G(0)=1`` and ``G'(0)=0``.
    """

    if gamma0 < 0.0 or spectral_width <= 0.0:
        raise ValueError("gamma0 must be nonnegative and spectral_width positive")
    t = np.asarray(time, dtype=float)
    d = np.sqrt(complex(spectral_width**2 - 2.0 * gamma0 * spectral_width))
    z = d * t / 2.0
    value = np.exp(-spectral_width * t / 2.0) * (
        np.cosh(z) + spectral_width * t * _sinhc(z) / 2.0
    )
    return np.real_if_close(value, tol=1000)


def survival_amplitude_derivative(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return dG/dt in a form regular at the critical coupling."""

    if gamma0 < 0.0 or spectral_width <= 0.0:
        raise ValueError("gamma0 must be nonnegative and spectral_width positive")
    t = np.asarray(time, dtype=float)
    d = np.sqrt(complex(spectral_width**2 - 2.0 * gamma0 * spectral_width))
    z = d * t / 2.0
    value = (
        -gamma0
        * spectral_width
        * t
        * np.exp(-spectral_width * t / 2.0)
        * _sinhc(z)
        / 2.0
    )
    return np.real_if_close(value, tol=1000)


def survival_probability(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    amplitude = survival_amplitude(time, gamma0, spectral_width)
    return np.abs(amplitude) ** 2


def population_derivative(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    amplitude = survival_amplitude(time, gamma0, spectral_width)
    derivative = survival_amplitude_derivative(time, gamma0, spectral_width)
    return 2.0 * np.real(np.conjugate(amplitude) * derivative)


def decay_rate(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return the time-local rate away from zeros of the amplitude."""

    amplitude = survival_amplitude(time, gamma0, spectral_width)
    derivative = survival_amplitude_derivative(time, gamma0, spectral_width)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.real(-2.0 * derivative / amplitude)


def density_derivative(time: float, gamma0: float, spectral_width: float) -> np.ndarray:
    derivative = float(population_derivative(time, gamma0, spectral_width))
    return np.diag([derivative, -derivative])


def averaged_norms(
    gamma0: float,
    spectral_width: float,
    duration: float,
    *,
    integration_points: int,
) -> dict[str, float]:
    """Time-average the three Schatten norms of dot(rho)."""

    if duration <= 0.0 or integration_points < 3:
        raise ValueError("duration and integration_points must be positive")
    time = np.linspace(0.0, duration, integration_points)
    speed = np.abs(population_derivative(time, gamma0, spectral_width))
    total_variation = float(np.trapezoid(speed, time))
    operator = total_variation / duration
    return {
        "operator": operator,
        "hilbert_schmidt": np.sqrt(2.0) * operator,
        "trace": 2.0 * operator,
        "total_variation": total_variation,
    }


def markovian_averaged_norms(gamma0: float, duration: float) -> dict[str, float]:
    if gamma0 < 0.0 or duration <= 0.0:
        raise ValueError("gamma0 must be nonnegative and duration positive")
    operator = -np.expm1(-gamma0 * duration) / duration
    return {
        "operator": float(operator),
        "hilbert_schmidt": float(np.sqrt(2.0) * operator),
        "trace": float(2.0 * operator),
    }


def qsl_bounds(
    gamma0: float,
    spectral_width: float,
    duration: float,
    *,
    integration_points: int,
) -> dict[str, float]:
    """Return Eq. (21) resolved into operator/HS/trace contributions."""

    probability = float(survival_probability(duration, gamma0, spectral_width))
    numerator = max(0.0, 1.0 - probability)
    norms = averaged_norms(
        gamma0, spectral_width, duration, integration_points=integration_points
    )
    if gamma0 == 0.0:
        # Continuous gamma0 -> 0+ limit.  The state is stationary exactly at
        # zero coupling, so a 0/0 ratio has no operational QSL value.
        operator = duration
    else:
        operator = numerator / norms["operator"]
    return {
        "operator": float(operator),
        "hilbert_schmidt": float(operator / np.sqrt(2.0)),
        "trace": float(operator / 2.0),
        "survival_probability": probability,
        "total_variation": norms["total_variation"],
    }


def fidelity_amplitude(
    time: float | np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Return cos(Bures angle)=sqrt(<e|rho(t)|e>)=|G(t)|."""

    return np.sqrt(survival_probability(time, gamma0, spectral_width))


def pseudomode_survival_amplitude(
    time: np.ndarray, gamma0: float, spectral_width: float
) -> np.ndarray:
    """Independent Markovian-embedding integration of the Lorentzian bath."""

    grid = np.asarray(time, dtype=float)
    if grid.ndim != 1 or len(grid) < 2 or np.any(np.diff(grid) <= 0.0):
        raise ValueError("time must be a strictly increasing one-dimensional grid")
    coupling = np.sqrt(gamma0 * spectral_width / 2.0)

    def rhs(_: float, state: np.ndarray) -> np.ndarray:
        excited, cavity = state
        return np.array(
            [
                -1.0j * coupling * cavity,
                -spectral_width * cavity - 1.0j * coupling * excited,
            ],
            dtype=complex,
        )

    result = solve_ivp(
        rhs,
        (float(grid[0]), float(grid[-1])),
        np.array([1.0 + 0.0j, 0.0 + 0.0j]),
        t_eval=grid,
        rtol=2.0e-11,
        atol=2.0e-13,
        method="DOP853",
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result.y[0]


def pure_state_unitary_speed(
    hamiltonian: np.ndarray,
    state: np.ndarray,
    *,
    hbar: float = 1.0,
) -> dict[str, float]:
    """Audit the norm of ``rho_dot=-i[H,rho]/hbar`` for a pure state.

    This is deliberately independent of the open-system specialization used
    for the paper figures.  It exposes every normalization factor in the
    sentence following Eq. (20).
    """

    h = np.asarray(hamiltonian, dtype=complex)
    psi = np.asarray(state, dtype=complex)
    if h.ndim != 2 or h.shape[0] != h.shape[1]:
        raise ValueError("hamiltonian must be a square matrix")
    if psi.shape != (h.shape[0],):
        raise ValueError("state dimension must match hamiltonian")
    if hbar <= 0.0:
        raise ValueError("hbar must be positive")
    if not np.allclose(h, h.conjugate().T, rtol=0.0, atol=1.0e-13):
        raise ValueError("hamiltonian must be Hermitian")
    norm = float(np.linalg.norm(psi))
    if not np.isclose(norm, 1.0, rtol=0.0, atol=1.0e-13):
        raise ValueError("state must be normalized")

    rho = np.outer(psi, psi.conjugate())
    rho_dot = -1.0j * (h @ rho - rho @ h) / hbar
    mean_energy = float(np.real(np.vdot(psi, h @ psi)))
    mean_energy_squared = float(np.real(np.vdot(psi, h @ h @ psi)))
    variance = max(0.0, mean_energy_squared - mean_energy**2)
    energy_std = float(np.sqrt(variance))
    operator = float(np.linalg.norm(rho_dot, ord=2))
    hilbert_schmidt = float(np.linalg.norm(rho_dot, ord="fro"))
    trace = float(np.linalg.norm(rho_dot, ord="nuc"))
    expected_hs = np.sqrt(2.0) * energy_std / hbar
    return {
        "mean_energy": mean_energy,
        "energy_variance": variance,
        "energy_standard_deviation": energy_std,
        "operator_speed": operator,
        "hilbert_schmidt_speed": hilbert_schmidt,
        "trace_speed": trace,
        "expected_hilbert_schmidt_speed": float(expected_hs),
        "hilbert_schmidt_identity_error": float(abs(hilbert_schmidt - expected_hs)),
    }


def closed_two_level_qsl_audit(
    duration: float,
    *,
    angular_frequency: float = 1.0,
    hbar: float = 1.0,
) -> dict[str, float]:
    """Compare Eq. (21) with standard closed-system bounds.

    The independently chosen test system is ``H=diag(0,hbar*omega)`` with
    initial state ``(|0>+|1>)/sqrt(2)``.  For ``0 <= omega*t <= pi`` it follows
    a geodesic and reaches an orthogonal state at ``t=pi/omega``.
    """

    if duration < 0.0 or angular_frequency <= 0.0 or hbar <= 0.0:
        raise ValueError("duration must be nonnegative and scales positive")
    phase = angular_frequency * duration
    if phase > np.pi + 1.0e-13:
        raise ValueError("audit is restricted to the first orthogonalization")
    h = np.diag([0.0, hbar * angular_frequency])
    psi = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2.0)
    speed = pure_state_unitary_speed(h, psi, hbar=hbar)
    overlap = float(abs((1.0 + np.exp(-1.0j * phase)) / 2.0))
    bures_angle = float(np.arccos(np.clip(overlap, 0.0, 1.0)))
    numerator = float(np.sin(bures_angle) ** 2)
    equation_21_operator = numerator / speed["operator_speed"]
    equation_21_hs = numerator / speed["hilbert_schmidt_speed"]
    equation_21_trace = numerator / speed["trace_speed"]
    standard_mt_geometric = hbar * bures_angle / speed["energy_standard_deviation"]
    standard_mt_orthogonal = (
        np.pi * hbar / (2.0 * speed["energy_standard_deviation"])
    )
    standard_ml_orthogonal = np.pi * hbar / (2.0 * speed["mean_energy"])
    return {
        "duration": float(duration),
        "bures_angle": bures_angle,
        "endpoint_overlap": overlap,
        "mean_energy": speed["mean_energy"],
        "energy_standard_deviation": speed["energy_standard_deviation"],
        "equation_21_operator": float(equation_21_operator),
        "equation_21_hilbert_schmidt": float(equation_21_hs),
        "equation_21_trace": float(equation_21_trace),
        "standard_mt_geometric": float(standard_mt_geometric),
        "standard_mt_orthogonal": float(standard_mt_orthogonal),
        "standard_ml_orthogonal": float(standard_ml_orthogonal),
    }


def lorentzian_spectral_density(
    detuning: float | np.ndarray,
    gamma0: float,
    spectral_width: float,
    *,
    convention: str = "printed_eq24",
) -> np.ndarray:
    """Evaluate literal Eq. (24) or the density required by Eqs. (25)--(26).

    ``printed_eq24`` uses a numerator ``gamma0*lambda``.  Fourier transforming
    it gives ``gamma0*exp(-lambda*|t|)/2``.  The later amplitude equation needs
    ``gamma0*lambda*exp(-lambda*|t|)/2``, corresponding to a numerator
    ``gamma0*lambda**2`` under the same transform convention.
    """

    if gamma0 < 0.0 or spectral_width <= 0.0:
        raise ValueError("gamma0 must be nonnegative and spectral_width positive")
    if convention not in {"printed_eq24", "eq25_dynamics"}:
        raise ValueError("unknown Lorentzian convention")
    delta = np.asarray(detuning, dtype=float)
    width_power = 1 if convention == "printed_eq24" else 2
    numerator = gamma0 * spectral_width**width_power
    return numerator / (2.0 * np.pi * (delta**2 + spectral_width**2))


def lorentzian_kernel_scale(
    gamma0: float,
    spectral_width: float,
    *,
    convention: str = "printed_eq24",
) -> float:
    """Return ``integral J(omega) d omega``, the zero-time bath kernel."""

    # Route validation through the public density function.
    lorentzian_spectral_density(
        0.0, gamma0, spectral_width, convention=convention
    )
    if convention == "printed_eq24":
        return float(gamma0 / 2.0)
    return float(gamma0 * spectral_width / 2.0)


def amplitude_damping_trace_distance(
    amplitude: float | np.ndarray,
    polar_angle: float | np.ndarray,
) -> np.ndarray:
    """Trace distance for antipodal pure inputs under amplitude damping.

    Every difference of two qubit states has Bloch length at most two.  The
    channel acts linearly on that difference, so homogeneity reduces the global
    state-pair optimization to antipodal pure states.  Axial symmetry leaves
    only the polar angle used here.
    """

    g = np.abs(np.asarray(amplitude, dtype=complex)).astype(float)
    theta = np.asarray(polar_angle, dtype=float)
    sin2 = np.sin(theta) ** 2
    cos2 = np.cos(theta) ** 2
    return g * np.sqrt(sin2 + g**2 * cos2)


def optimize_blp_state_pair(
    amplitude: np.ndarray,
    *,
    angle_points: int,
    rise_tolerance: float = 1.0e-13,
) -> dict[str, float | int]:
    """Maximize BLP trace-distance backflow over all qubit-state pairs."""

    if angle_points < 3:
        raise ValueError("angle_points must be at least three")
    g = np.abs(np.asarray(amplitude, dtype=complex)).astype(float)
    if g.ndim != 1 or len(g) < 2:
        raise ValueError("amplitude must be a one-dimensional trajectory")
    if np.any(g > 1.0 + 1.0e-10):
        raise ValueError("amplitude-damping trajectory is not contractive")

    rising = np.diff(g) > rise_tolerance
    starts = np.flatnonzero(rising & np.r_[True, ~rising[:-1]])
    ends = np.flatnonzero(rising & np.r_[~rising[1:], True]) + 1
    angles = np.linspace(0.0, np.pi / 2.0, angle_points)
    if len(starts) == 0:
        measures = np.zeros_like(angles)
    else:
        low = g[starts][None, :]
        high = g[ends][None, :]
        theta = angles[:, None]
        measures = np.sum(
            amplitude_damping_trace_distance(high, theta)
            - amplitude_damping_trace_distance(low, theta),
            axis=1,
        )
    best = int(np.argmax(measures))
    return {
        "optimal_polar_angle": float(angles[best]),
        "optimal_measure": float(measures[best]),
        "excited_ground_measure": float(measures[0]),
        "equatorial_measure": float(measures[-1]),
        "revival_segments": int(len(starts)),
        "angle_points": int(angle_points),
    }
