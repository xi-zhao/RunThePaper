"""Independent numerics for arXiv:2607.15070.

The primary implementation evaluates the paper's displayed proper-time
integrals after a logarithmic change of variable and a Poisson-resummed plate
sum.  Positive Bessel-series representations provide an independent numerical
cross-check.  Source-figure pixels and paths are never numerical inputs.
"""
from __future__ import annotations

import math
import os
from collections.abc import Iterable

import numpy as np
from scipy.integrate import quad_vec
from scipy.special import kv


DEFAULT_EPSABS = 2.0e-10
DEFAULT_EPSREL = 2.0e-9
LOG_TAU_MIN = -9.0
LOG_TAU_MAX = 6.0
SERIES_TOL = 2.0e-13
_SERIES_LOG_CUTOFF = -math.log(SERIES_TOL)


def require_guarded_target(expected_target: str, *, allowed_stages: Iterable[str]) -> str:
    """Fail closed unless run_target.py authorized this exact target and stage."""

    guarded_target = os.environ.get("PRAGENT_GUARDED_TARGET_ID", "")
    guarded_stage = os.environ.get("PRAGENT_GUARDED_STAGE", "")
    if guarded_target != expected_target:
        raise RuntimeError(
            f"target guard mismatch: expected {expected_target}, got "
            f"{guarded_target or '<missing>'}"
        )
    allowed = set(allowed_stages)
    if guarded_stage not in allowed:
        raise RuntimeError(
            f"stage guard mismatch for {expected_target}: expected one of "
            f"{sorted(allowed)}, got {guarded_stage or '<missing>'}"
        )
    return guarded_stage


def radial_ground_eigenvalue(alpha: float) -> float:
    """Ground eigenvalue of -Δ_r + alpha² rho² for l=0."""

    if alpha <= 0:
        raise ValueError("alpha must be positive")
    return 2.0 * float(alpha)


def _theta_plate_sum(tau: float) -> float:
    """Return sum_{j>=1} exp(-j²/tau²) with a direct/Poisson dual form."""

    if tau <= 0:
        raise ValueError("tau must be positive")
    if tau < 1.0:
        j_max = max(1, int(math.ceil(tau * math.sqrt(_SERIES_LOG_CUTOFF))))
        j = np.arange(1, j_max + 1, dtype=np.float64)
        return float(np.exp(-(j / tau) ** 2).sum())

    k_max = max(
        1,
        int(math.ceil(math.sqrt(_SERIES_LOG_CUTOFF) / (math.pi * tau))),
    )
    k = np.arange(1, k_max + 1, dtype=np.float64)
    correction = float(np.exp(-(math.pi * k * tau) ** 2).sum())
    return (
        0.5 * (math.sqrt(math.pi) * tau - 1.0)
        + math.sqrt(math.pi) * tau * correction
    )


def _landau_factor(alpha0: np.ndarray, tau_squared: float) -> np.ndarray:
    """Stable alpha0/sinh(alpha0*tau²), including the alpha0=0 limit."""

    alpha0 = np.asarray(alpha0, dtype=np.float64)
    x = alpha0 * tau_squared
    result = np.empty_like(x)
    zero = alpha0 == 0.0
    result[zero] = 1.0 / tau_squared

    positive = ~zero
    small = positive & (x < 1.0e-4)
    if np.any(small):
        xs = x[small]
        result[small] = (1.0 / tau_squared) * (xs / np.sinh(xs))

    regular = positive & ~small
    if np.any(regular):
        xr = x[regular]
        ar = alpha0[regular]
        result[regular] = (
            2.0 * ar * np.exp(-xr) / (-np.expm1(-2.0 * xr))
        )
    return result


def _correction_factor(alpha0: np.ndarray, tau_squared: float) -> np.ndarray:
    """Stable 2 alpha0/[sinh(x)(exp(x)-1)] for positive alpha0."""

    alpha0 = np.asarray(alpha0, dtype=np.float64)
    if np.any(alpha0 <= 0):
        raise ValueError("the additional contribution requires alpha0 > 0")
    x = alpha0 * tau_squared
    denominator = (-np.expm1(-2.0 * x)) * (-np.expm1(-x))
    return 4.0 * alpha0 * np.exp(-2.0 * x) / denominator


def _integrate_energy_vector(
    alpha0_values: np.ndarray,
    m0: float,
    *,
    sector: str,
    epsabs: float = DEFAULT_EPSABS,
    epsrel: float = DEFAULT_EPSREL,
) -> tuple[np.ndarray, float]:
    alpha0_values = np.asarray(alpha0_values, dtype=np.float64)
    if alpha0_values.ndim != 1 or alpha0_values.size == 0:
        raise ValueError("alpha0_values must be a non-empty one-dimensional array")
    if m0 < 0:
        raise ValueError("m0 must be non-negative")
    if sector not in {"landau", "correction"}:
        raise ValueError(f"unsupported sector: {sector}")
    if sector == "correction" and np.any(alpha0_values <= 0):
        raise ValueError("correction alpha0 values must be positive")

    def integrand(log_tau: float) -> np.ndarray:
        tau = math.exp(log_tau)
        tau_squared = tau * tau
        plate_sum = _theta_plate_sum(tau)
        if plate_sum == 0.0:
            return np.zeros_like(alpha0_values)
        exponent = -2.0 * log_tau - (m0 * m0) * tau_squared
        common = math.exp(exponent) * plate_sum
        factor = (
            _landau_factor(alpha0_values, tau_squared)
            if sector == "landau"
            else _correction_factor(alpha0_values, tau_squared)
        )
        return -common * factor

    values, error = quad_vec(
        integrand,
        LOG_TAU_MIN,
        LOG_TAU_MAX,
        epsabs=epsabs,
        epsrel=epsrel,
        limit=500,
        quadrature="gk21",
    )
    return np.asarray(values, dtype=np.float64), float(error)


def dimensionless_landau_energy(
    alpha0_values: Iterable[float],
    m0: float,
    *,
    epsabs: float = DEFAULT_EPSABS,
    epsrel: float = DEFAULT_EPSREL,
) -> tuple[np.ndarray, float]:
    """Compute 8π²L³ E_L^ren/A for one mass and many alpha0 values."""

    alpha0 = np.asarray(list(alpha0_values), dtype=np.float64)
    zero = alpha0 == 0.0
    result = np.empty_like(alpha0)
    integration_error = 0.0
    if np.any(~zero):
        positive_values, integration_error = _integrate_energy_vector(
            alpha0[~zero],
            m0,
            sector="landau",
            epsabs=epsabs,
            epsrel=epsrel,
        )
        result[~zero] = positive_values
    if np.any(zero):
        result[zero] = standard_landau_limit(m0)
    return result, integration_error


def dimensionless_correction_energy(
    alpha0_values: Iterable[float],
    m0: float,
    *,
    epsabs: float = DEFAULT_EPSABS,
    epsrel: float = DEFAULT_EPSREL,
) -> tuple[np.ndarray, float]:
    """Compute 8π²L³ E_c^ren/A for one mass and many positive alpha0."""

    alpha0 = np.asarray(list(alpha0_values), dtype=np.float64)
    return _integrate_energy_vector(
        alpha0,
        m0,
        sector="correction",
        epsabs=epsabs,
        epsrel=epsrel,
    )


def energy_ratio(landau: np.ndarray, correction: np.ndarray) -> np.ndarray:
    landau = np.asarray(landau, dtype=np.float64)
    correction = np.asarray(correction, dtype=np.float64)
    if landau.shape != correction.shape:
        raise ValueError("landau and correction arrays must have the same shape")
    if np.any(landau == 0.0):
        raise ZeroDivisionError("landau energy contains zero")
    return 1.0 + correction / landau


def _bessel_j_sum(root: float, *, tolerance: float) -> float:
    total = 0.0
    small_count = 0
    for j in range(1, 100_001):
        term = root * float(kv(1, 2.0 * j * root)) / j
        total += term
        if abs(term) <= tolerance * max(1.0, abs(total)):
            small_count += 1
            if small_count >= 8:
                return total
        else:
            small_count = 0
    raise RuntimeError("Bessel j sum failed to converge")


def landau_energy_bessel(
    alpha0: float,
    m0: float,
    *,
    tolerance: float = 2.0e-12,
) -> float:
    """Independent EQC004 sum for the Landau-like contribution."""

    if alpha0 <= 0 or m0 < 0:
        raise ValueError("alpha0 must be positive and m0 non-negative")
    total = 0.0
    small_count = 0
    for n in range(200_000):
        root = math.sqrt(m0 * m0 + (2 * n + 1) * alpha0)
        level = 2.0 * alpha0 * _bessel_j_sum(
            root,
            tolerance=tolerance * 0.1,
        )
        total += level
        if abs(level) <= tolerance * max(1.0, abs(total)):
            small_count += 1
            if small_count >= 10:
                return -total
        else:
            small_count = 0
    raise RuntimeError("Landau Bessel level sum failed to converge")


def correction_energy_bessel(
    alpha0: float,
    m0: float,
    *,
    tolerance: float = 2.0e-12,
) -> float:
    """Independent EQC004 sum for the additional contribution."""

    if alpha0 <= 0 or m0 < 0:
        raise ValueError("alpha0 must be positive and m0 non-negative")
    total = 0.0
    small_count = 0
    for r in range(2, 200_000):
        root = math.sqrt(m0 * m0 + r * alpha0)
        multiplicity = r // 2
        level = (
            4.0
            * alpha0
            * multiplicity
            * _bessel_j_sum(root, tolerance=tolerance * 0.05)
        )
        total += level
        if abs(level) <= tolerance * max(1.0, abs(total)):
            small_count += 1
            if small_count >= 12:
                return -total
        else:
            small_count = 0
    raise RuntimeError("Correction Bessel level sum failed to converge")


def standard_landau_limit(m0: float, *, tolerance: float = 1.0e-14) -> float:
    """Small-alpha0 limit of the dimensionless Landau-like energy."""

    if m0 < 0:
        raise ValueError("m0 must be non-negative")
    if m0 == 0.0:
        return -(math.pi**4) / 180.0
    total = 0.0
    small_count = 0
    for j in range(1, 100_001):
        term = (m0 * m0) * float(kv(2, 2.0 * j * m0)) / (j * j)
        total += term
        if abs(term) <= tolerance * max(1.0, abs(total)):
            small_count += 1
            if small_count >= 8:
                return -total
        else:
            small_count = 0
    raise RuntimeError("standard Landau limit failed to converge")


def correction_small_alpha_leading(
    alpha0: float,
    m0: float,
    *,
    tolerance: float = 1.0e-14,
) -> float:
    """Correct leading weak-coupling term (K3, not the paper's K2)."""

    if alpha0 <= 0 or m0 < 0:
        raise ValueError("alpha0 must be positive and m0 non-negative")
    if m0 == 0.0:
        return -2.0 * (math.pi**6 / 945.0) / alpha0
    total = 0.0
    small_count = 0
    for j in range(1, 100_001):
        term = (m0**3) * float(kv(3, 2.0 * j * m0)) / (j**3)
        total += term
        if abs(term) <= tolerance * max(1.0, abs(total)):
            small_count += 1
            if small_count >= 8:
                return -2.0 * total / alpha0
        else:
            small_count = 0
    raise RuntimeError("correction small-alpha limit failed to converge")


def paper_printed_correction_small_alpha(alpha0: float, m0: float) -> float:
    """Literal paper Eq. (36), retained only for discrepancy quantification."""

    return (2.0 / alpha0) * standard_landau_limit(m0)


def strong_coupling_leading(
    alpha0: float,
    m0: float,
    *,
    f: int,
    j: int = 1,
) -> float:
    """Correct large-alpha0 K1 asymptotic for the leading f=1 or f=2 level."""

    if alpha0 <= 0 or m0 < 0 or f not in {1, 2} or j < 1:
        raise ValueError("invalid strong-coupling arguments")
    squared_mass = m0 * m0 + f * alpha0
    return (
        -math.sqrt(math.pi)
        * f
        * alpha0
        * squared_mass**0.25
        * math.exp(-2.0 * j * math.sqrt(squared_mass))
        / (j**1.5)
    )


def paper_printed_strong_coupling(alpha0: float, *, f: int, j: int = 1) -> float:
    """Literal final line of paper Eq. (31), for numerical discrepancy checks."""

    if alpha0 <= 0 or f not in {1, 2} or j < 1:
        raise ValueError("invalid paper-asymptotic arguments")
    return (
        -math.sqrt(2.0 * math.pi * (f**3) * (alpha0**3) / (j * j))
        * math.exp(-2.0 * j * f * alpha0)
    )
