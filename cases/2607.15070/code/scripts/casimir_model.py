"""Independent numerical model for arXiv:2607.15070.

The production evaluator uses positive Bessel-K series derived from the
paper's proper-time integrals.  Direct adaptive quadrature of the original
integrals is retained as a structurally independent check.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import quad
from scipy.special import kv, zeta


DEFAULT_BESSEL_ARGUMENT_CUTOFF = 42.0
TIGHT_BESSEL_ARGUMENT_CUTOFF = 46.0


@dataclass(frozen=True)
class DirectQuadratureResult:
    value: float
    estimated_error: float
    image_terms: int


def landau_zero_coupling(m0: float, *, argument_cutoff: float = 44.0) -> float:
    """Return ``S_L=-Y_L`` at alpha0=0."""

    _validate_mass(m0)
    if m0 == 0.0:
        return float(zeta(4.0, 1.0) / 2.0)
    j_max = max(1, int(math.ceil(argument_cutoff / (2.0 * m0))))
    j = np.arange(1, j_max + 1, dtype=float)
    return float(np.sum((m0 * m0) * kv(2, 2.0 * j * m0) / (j * j)))


def correction_small_coupling_coefficient(
    m0: float,
    *,
    argument_cutoff: float = 44.0,
) -> float:
    """Return ``lim(alpha0*S_c)`` from the corrected small-alpha expansion."""

    _validate_mass(m0)
    if m0 == 0.0:
        return float(2.0 * zeta(6.0, 1.0))
    j_max = max(1, int(math.ceil(argument_cutoff / (2.0 * m0))))
    j = np.arange(1, j_max + 1, dtype=float)
    return float(2.0 * np.sum((m0**3) * kv(3, 2.0 * j * m0) / (j**3)))


def landau_magnitude(
    alpha0: float,
    m0: float,
    *,
    argument_cutoff: float = DEFAULT_BESSEL_ARGUMENT_CUTOFF,
) -> float:
    """Evaluate the positive magnitude ``S_L=-Y_L``."""

    _validate_parameters(alpha0, m0, allow_zero_alpha=True)
    if alpha0 == 0.0:
        return landau_zero_coupling(m0, argument_cutoff=argument_cutoff)

    q_min = math.sqrt(m0 * m0 + alpha0)
    j_max = max(1, int(math.floor(argument_cutoff / (2.0 * q_min))))
    total = 0.0
    for image_index in range(1, j_max + 1):
        q_max = argument_cutoff / (2.0 * image_index)
        raw_r_max = ((q_max * q_max - m0 * m0) / alpha0 - 1.0) / 2.0
        r_max = int(math.floor(raw_r_max))
        if r_max < 0:
            continue
        radial_index = np.arange(r_max + 1, dtype=float)
        q = np.sqrt(m0 * m0 + (2.0 * radial_index + 1.0) * alpha0)
        total += float(
            np.sum(q * kv(1, 2.0 * image_index * q) / image_index)
        )
    return 2.0 * alpha0 * total


def correction_magnitude(
    alpha0: float,
    m0: float,
    *,
    argument_cutoff: float = DEFAULT_BESSEL_ARGUMENT_CUTOFF,
) -> float:
    """Evaluate the positive magnitude ``S_c=-Y_c``."""

    _validate_parameters(alpha0, m0, allow_zero_alpha=False)
    q_min = math.sqrt(m0 * m0 + 2.0 * alpha0)
    j_max = max(1, int(math.floor(argument_cutoff / (2.0 * q_min))))
    total = 0.0
    for image_index in range(1, j_max + 1):
        q_max = argument_cutoff / (2.0 * image_index)
        k_max = int(math.floor((q_max * q_max - m0 * m0) / alpha0))
        if k_max < 2:
            continue
        grouped_level = np.arange(2, k_max + 1, dtype=float)
        multiplicity = np.floor(grouped_level / 2.0)
        q = np.sqrt(m0 * m0 + grouped_level * alpha0)
        total += float(
            np.sum(
                multiplicity
                * q
                * kv(1, 2.0 * image_index * q)
                / image_index
            )
        )
    return 4.0 * alpha0 * total


def energy_ratio(
    alpha0: float,
    m0: float,
    *,
    argument_cutoff: float = DEFAULT_BESSEL_ARGUMENT_CUTOFF,
) -> float:
    """Return ``E_0^ren/E_L^ren = 1 + S_c/S_L``."""

    landau = landau_magnitude(
        alpha0,
        m0,
        argument_cutoff=argument_cutoff,
    )
    correction = correction_magnitude(
        alpha0,
        m0,
        argument_cutoff=argument_cutoff,
    )
    return 1.0 + correction / landau


def large_coupling_leading(alpha0: float, m0: float, sector_factor: int) -> float:
    """Leading j=1 term of the corrected large-coupling expression."""

    _validate_parameters(alpha0, m0, allow_zero_alpha=False)
    if sector_factor not in {1, 2}:
        raise ValueError("sector_factor must be 1 (Landau) or 2 (correction)")
    q = math.sqrt(m0 * m0 + sector_factor * alpha0)
    return float(
        2.0
        * sector_factor
        * alpha0
        * q
        * kv(1, 2.0 * q)
    )


def direct_proper_time_magnitude(
    alpha0: float,
    m0: float,
    *,
    sector: str,
    image_terms: int = 14,
    relative_tolerance: float = 2.0e-9,
) -> DirectQuadratureResult:
    """Integrate the original proper-time expression in ``u=log(tau)``."""

    _validate_parameters(alpha0, m0, allow_zero_alpha=False)
    if sector not in {"landau", "correction"}:
        raise ValueError("sector must be 'landau' or 'correction'")
    if image_terms < 1:
        raise ValueError("image_terms must be positive")

    value = 0.0
    error = 0.0
    for image_index in range(1, image_terms + 1):
        integral, estimate = quad(
            _log_tau_integrand,
            -12.0,
            12.0,
            args=(alpha0, m0, image_index, sector),
            epsabs=1.0e-13,
            epsrel=relative_tolerance,
            limit=250,
        )
        value += integral
        error += estimate
    prefactor = alpha0 if sector == "landau" else 2.0 * alpha0
    return DirectQuadratureResult(
        value=float(prefactor * value),
        estimated_error=float(prefactor * error),
        image_terms=image_terms,
    )


def _log_tau_integrand(
    u: float,
    alpha0: float,
    m0: float,
    image_index: int,
    sector: str,
) -> float:
    tau_squared = math.exp(2.0 * u)
    inverse_tau_squared = 1.0 / tau_squared
    x = alpha0 * tau_squared
    log_value = (
        -2.0 * u
        - m0 * m0 * tau_squared
        - image_index * image_index * inverse_tau_squared
        + _log_inverse_sinh(x)
    )
    if sector == "correction":
        log_value += _log_inverse_expm1(x)
    if log_value < -745.0:
        return 0.0
    return math.exp(log_value)


def _log_inverse_sinh(x: float) -> float:
    if x > 40.0:
        return math.log(2.0) - x
    return -math.log(math.sinh(x))


def _log_inverse_expm1(x: float) -> float:
    if x > 40.0:
        return -x
    return -math.log(math.expm1(x))


def _validate_mass(m0: float) -> None:
    if not math.isfinite(m0) or m0 < 0.0:
        raise ValueError("m0 must be finite and nonnegative")


def _validate_parameters(
    alpha0: float,
    m0: float,
    *,
    allow_zero_alpha: bool,
) -> None:
    _validate_mass(m0)
    lower_ok = alpha0 >= 0.0 if allow_zero_alpha else alpha0 > 0.0
    if not math.isfinite(alpha0) or not lower_ok:
        relation = "nonnegative" if allow_zero_alpha else "positive"
        raise ValueError(f"alpha0 must be finite and {relation}")
