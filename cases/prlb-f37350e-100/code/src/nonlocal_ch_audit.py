"""Independent analytic and discrete checks for PRL-Bench record idx100.

The module keeps three layers separate:

* the exact nonlocal linear dispersion printed in the PRL supplement;
* the discrete two-dimensional torus search requested by the benchmark; and
* the long-wave coefficients obtained by Taylor expanding that exact result.

That separation is important because the frozen answer mixes the continuum
and discrete optima and changes signs while passing from the exact dispersion
to its conserved Swift--Hohenberg truncation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


RHO_STAR = 0.5
GAMMA = 1.5


@dataclass(frozen=True)
class ModeSearchResult:
    """Result and proof-carrying domain for a two-dimensional mode search."""

    critical_temperature: float
    k_squared: float
    shell: int
    representative_mode: tuple[int, int]
    degeneracy: int
    continuum_shell: float
    maximum_shell_searched: int


@dataclass(frozen=True)
class GradientCoefficients:
    """Coefficients in -s[A0 + A2 s + A4 s^2], with s=|k|^2."""

    a0: float
    a2: float
    a4: float


def utility_derivatives(rho: float) -> tuple[float, float, float]:
    """Return u', u'', u''' for u=-|rho-1/2|^(3/2)."""

    if not 0.0 < rho < 1.0:
        raise ValueError("rho must lie in (0, 1)")
    delta = rho - RHO_STAR
    if delta == 0.0:
        raise ValueError("the cusped utility is not C3 at rho=1/2")
    sign = 1.0 if delta > 0.0 else -1.0
    magnitude = abs(delta)
    u1 = -1.5 * sign * math.sqrt(magnitude)
    u2 = -0.75 / math.sqrt(magnitude)
    u3 = 0.375 * sign / (magnitude ** 1.5)
    return u1, u2, u3


def gaussian_hat_from_k2(k_squared: float, sigma: float) -> float:
    """Return exp(-sigma^2 |k|^2 / 2)."""

    if k_squared < 0.0 or sigma <= 0.0:
        raise ValueError("k_squared must be nonnegative and sigma positive")
    return math.exp(-0.5 * sigma * sigma * k_squared)


def destabilizing_contribution(
    q: float, *, alpha: float, rho: float
) -> float:
    """Return M[(1+alpha)u' q + alpha rho u'' q^2]."""

    if not 0.0 <= q <= 1.0:
        raise ValueError("q must lie in [0, 1]")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must lie in [0, 1]")
    u1, u2, _ = utility_derivatives(rho)
    mobility = rho * (1.0 - rho)
    return mobility * ((1.0 + alpha) * u1 * q + alpha * rho * u2 * q * q)


def continuum_q_vertex(*, alpha: float, rho: float) -> float:
    """Return the unconstrained vertex of the concave quadratic D(q)."""

    if alpha <= 0.0:
        return math.inf
    u1, u2, _ = utility_derivatives(rho)
    return -((1.0 + alpha) * u1) / (2.0 * alpha * rho * u2)


def continuum_spinodal_temperature(*, alpha: float, rho: float) -> float:
    """Return max_{q in [0,1]} D(q), clipped below at zero."""

    if alpha == 0.0:
        q = 1.0
    else:
        q = min(1.0, max(0.0, continuum_q_vertex(alpha=alpha, rho=rho)))
    return max(0.0, destabilizing_contribution(q, alpha=alpha, rho=rho))


def rigorous_shell_bound_2d(
    *, alpha: float, rho: float, sigma: float, length: float
) -> tuple[float, int]:
    """Return the continuum optimum shell and a sufficient finite bound.

    When the vertex lies inside q in (0,1), D is monotone on either side of
    the corresponding real-valued shell m_cont.  Hence the discrete optimum
    is bracketed by the last sum-of-two-squares shell below m_cont and the
    first one above it.  The axis shell ceil(sqrt(m_cont))^2 is guaranteed to
    be representable and supplies a simple proof-carrying upper bound.
    """

    if sigma <= 0.0 or length <= 0.0:
        raise ValueError("sigma and length must be positive")
    q_vertex = continuum_q_vertex(alpha=alpha, rho=rho)
    if q_vertex >= 1.0:
        return 0.0, 1
    if q_vertex <= 0.0:
        raise ValueError("D(q) has no attained maximum on the infinite torus spectrum")
    shell_decay = 0.5 * sigma * sigma * (2.0 * math.pi / length) ** 2
    continuum_shell = -math.log(q_vertex) / shell_decay
    maximum_shell = math.ceil(math.sqrt(continuum_shell)) ** 2
    return continuum_shell, maximum_shell


def search_discrete_modes_2d(
    *, alpha: float, rho: float, sigma: float, length: float
) -> ModeSearchResult:
    """Exactly search the sufficient finite set of two-dimensional shells."""

    continuum_shell, maximum_shell = rigorous_shell_bound_2d(
        alpha=alpha, rho=rho, sigma=sigma, length=length
    )
    radius = math.isqrt(maximum_shell)
    fundamental_k2 = (2.0 * math.pi / length) ** 2
    best_value = -math.inf
    best_shell: int | None = None
    best_mode: tuple[int, int] | None = None
    best_degeneracy = 0
    tolerance = 1.0e-15

    shell_values: dict[int, float] = {}
    shell_modes: dict[int, list[tuple[int, int]]] = {}
    for nx in range(-radius, radius + 1):
        for ny in range(-radius, radius + 1):
            shell = nx * nx + ny * ny
            if shell == 0 or shell > maximum_shell:
                continue
            shell_modes.setdefault(shell, []).append((nx, ny))
            if shell not in shell_values:
                q = gaussian_hat_from_k2(shell * fundamental_k2, sigma)
                shell_values[shell] = destabilizing_contribution(
                    q, alpha=alpha, rho=rho
                )

    for shell in sorted(shell_values):
        value = shell_values[shell]
        if value > best_value + tolerance:
            best_value = value
            best_shell = shell
            best_mode = min(shell_modes[shell])
            best_degeneracy = len(shell_modes[shell])
        elif abs(value - best_value) <= tolerance and best_shell is not None:
            if shell < best_shell:
                best_shell = shell
                best_mode = min(shell_modes[shell])
                best_degeneracy = len(shell_modes[shell])

    if best_shell is None or best_mode is None:
        raise RuntimeError("the finite search domain unexpectedly contained no modes")
    return ModeSearchResult(
        critical_temperature=best_value,
        k_squared=best_shell * fundamental_k2,
        shell=best_shell,
        representative_mode=best_mode,
        degeneracy=best_degeneracy,
        continuum_shell=continuum_shell,
        maximum_shell_searched=maximum_shell,
    )


def finite_wavenumber_threshold(alpha: float) -> float:
    """Correct rho threshold for an interior q vertex below the cusp."""

    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must lie in (0, 1]")
    return (1.0 + alpha) / (2.0 + 4.0 * alpha)


def frozen_threshold(alpha: float) -> float:
    """Return the incompatible threshold printed in the benchmark gold."""

    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must lie in (0, 1]")
    return (1.0 + alpha) / (2.0 + 3.0 * alpha)


def mapping_denominator(*, alpha: float, rho: float) -> float:
    """Return (1+alpha)u' + 2 alpha rho u'' from the mapping ODE."""

    u1, u2, _ = utility_derivatives(rho)
    return (1.0 + alpha) * u1 + 2.0 * alpha * rho * u2


def mapping_singular_density(alpha: float) -> float:
    """Return the PRL supplement's rho_m for gamma=3/2, rho*=1/2."""

    return finite_wavenumber_threshold(alpha)


def mapping_exponent(alpha: float) -> float:
    """Return the indicial exponent xi at rho_m."""

    if not 0.0 < alpha < 1.0:
        raise ValueError("the singular mapping task assumes alpha in (0, 1)")
    return (1.0 + 5.0 * alpha) / (2.0 + 4.0 * alpha)


def gradient_coefficients(
    *, temperature: float, alpha: float, rho: float, sigma: float
) -> GradientCoefficients:
    """Expand the exact conserved dispersion through O(|k|^6)."""

    u1, u2, _ = utility_derivatives(rho)
    mobility = rho * (1.0 - rho)
    linear = (1.0 + alpha) * u1
    quadratic = alpha * rho * u2
    return GradientCoefficients(
        a0=temperature - mobility * (linear + quadratic),
        a2=mobility * sigma * sigma * (linear + 2.0 * quadratic) / 2.0,
        a4=-mobility * sigma**4 * (linear + 4.0 * quadratic) / 8.0,
    )


def frozen_a4(*, alpha: float, rho: float, sigma: float) -> float:
    """Return the sign-flipped A4 printed in the frozen answer."""

    return -gradient_coefficients(
        temperature=0.0, alpha=alpha, rho=rho, sigma=sigma
    ).a4


def selected_wavenumber(a2: float, a4: float) -> float:
    """Maximize -A2 s^2-A4 s^3 for A2<0<A4 and return sqrt(s)."""

    if not a2 < 0.0 < a4:
        raise ValueError("selected_wavenumber requires A2<0<A4")
    return math.sqrt(-2.0 * a2 / (3.0 * a4))


def frozen_selected_wavenumber_with_repaired_sign(a2: float, a4: float) -> float:
    """Evaluate the frozen 1/2 factor after repairing its A4 sign."""

    if not a2 < 0.0 < a4:
        raise ValueError("comparison requires A2<0<A4")
    return math.sqrt(-a2 / (2.0 * a4))


def exact_growth_rate(
    k_squared: float,
    *,
    temperature: float,
    alpha: float,
    rho: float,
    sigma: float,
) -> float:
    """Return the exact linear growth rate from the nonlocal PRL dispersion."""

    q = gaussian_hat_from_k2(k_squared, sigma)
    bracket = temperature - destabilizing_contribution(q, alpha=alpha, rho=rho)
    return -k_squared * bracket
