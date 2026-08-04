"""Independent analytic/numeric helpers for PRL-Bench record idx10.

The benchmark mixes a real harmonic normalization with a complex conjugate
mode pair.  This module keeps the physical inverse-propagator coefficient
explicit: for V(phi)=lambda*phi**4/4 it is V''=3*lambda*phi_bar**2.
"""

from __future__ import annotations

import math
from typing import Callable


def quartic_moment(power: int, coupling: float, volume: float) -> float:
    """Return <phi0**power> for exp[-lambda phi0^4/(4 V)]."""

    if power < 0 or power % 2:
        raise ValueError("power must be a non-negative even integer")
    if coupling <= 0.0 or volume <= 0.0:
        raise ValueError("coupling and volume must be positive")
    a = coupling / (4.0 * volume)
    return a ** (-power / 4.0) * math.gamma((power + 1.0) / 4.0) / math.gamma(0.25)


def zero_mode_spatial_variance(coupling: float, volume: float) -> float:
    """Return <phi(x)^2> from the constant harmonic alone."""

    return quartic_moment(2, coupling, volume) / volume


def physical_mass_squared(phi0: float, coupling: float, volume: float) -> float:
    """Hessian mass V'' evaluated on phi_bar=phi0/sqrt(V)."""

    return 3.0 * coupling * phi0 * phi0 / volume


def frozen_mass_squared(phi0: float, coupling: float, volume: float) -> float:
    """The factor-six expression printed in frozen Tasks 2-3."""

    return 6.0 * coupling * phi0 * phi0 / volume


def propagator_expansion_coefficients(
    coupling: float, volume: float, mass_prefactor: float = 3.0
) -> tuple[float, float]:
    """Return A=<M^2> and B=<M^4> for M^2=c lambda phi0^2/V."""

    scale = mass_prefactor * coupling / volume
    return (
        scale * quartic_moment(2, coupling, volume),
        scale * scale * quartic_moment(4, coupling, volume),
    )


def exact_propagator(
    k_squared: float,
    coupling: float,
    volume: float,
    *,
    mass_prefactor: float = 3.0,
    quad: Callable[..., tuple[float, float]],
) -> float:
    """Quadrature of <1/(K^2+c lambda phi0^2/V)>.

    A dimensionless integration variable u=(lambda/(4V))**(1/4) phi0
    avoids poorly scaled tails.
    """

    if k_squared <= 0.0:
        raise ValueError("k_squared must be positive")
    a = coupling / (4.0 * volume)
    phi_scale_squared = a ** -0.5
    mass_scale = mass_prefactor * coupling * phi_scale_squared / volume
    numerator = quad(
        lambda u: math.exp(-(u**4)) / (k_squared + mass_scale * u * u),
        0.0,
        math.inf,
        epsabs=1e-12,
        epsrel=1e-12,
        limit=250,
    )[0]
    normalization = math.gamma(0.25) / 4.0
    return numerator / normalization


def weak_mass_expansion(
    k_squared: float, coupling: float, volume: float, mass_prefactor: float = 3.0
) -> float:
    """Return 1/K^2-A/K^4+B/K^6 using K^2 as the input variable."""

    a_coefficient, b_coefficient = propagator_expansion_coefficients(
        coupling, volume, mass_prefactor
    )
    return (
        1.0 / k_squared
        - a_coefficient / (k_squared**2)
        + b_coefficient / (k_squared**3)
    )


def diffusion_constant(dimension: float) -> float:
    """Return D=Gamma((d+2)/2)/(2 d pi^((d+2)/2))."""

    return math.gamma((dimension + 2.0) / 2.0) / (
        2.0 * dimension * math.pi ** ((dimension + 2.0) / 2.0)
    )


def large_n_asymptotics(
    dimension: float, coupling: float, mass_squared: float
) -> dict[str, float]:
    """Source-traced saddle and vector/singlet eigenvalue expansions."""

    d_const = diffusion_constant(dimension)
    rho0 = (
        math.sqrt(dimension * d_const / coupling)
        - 3.0 * d_const / dimension
        - mass_squared / (2.0 * coupling)
    )
    lambda_v = math.sqrt(d_const * coupling / dimension) + (
        6.0 * d_const * coupling + dimension * mass_squared
    ) / (2.0 * dimension**2)
    lambda_s = 4.0 * math.sqrt(d_const * coupling / dimension) + (
        12.0 * d_const * coupling / dimension**2
    )
    return {"D": d_const, "rho0": rho0, "lambda_v": lambda_v, "lambda_s": lambda_s}


def fp_coefficients(
    coupling: float, hubble: float, mass_squared: float, epsilon: float
) -> dict[str, float]:
    """NLO one-point Fokker-Planck coefficients from source Eq. (8.14)."""

    if min(coupling, hubble, epsilon) <= 0.0:
        raise ValueError("coupling, hubble, and epsilon must be positive")
    bracket = math.log(epsilon / 2.0) - _digamma_three_halves()
    return {
        "a": 2.0 * coupling * bracket / hubble**2,
        "b": mass_squared / (3.0 * hubble)
        - coupling * hubble * bracket / (4.0 * math.pi**2),
        "c": coupling**2 / (9.0 * hubble**3),
    }


def _digamma_three_halves() -> float:
    # psi(1/2)=-gamma-2 log 2 and psi(x+1)=psi(x)+1/x.
    euler_mascheroni = 0.5772156649015328606
    return -euler_mascheroni - 2.0 * math.log(2.0) + 2.0
