"""Independent analytic checks for PRL-Bench record 051.

The benchmark is a synthetic extension of the Wang--Teter kernel lineage.  This
module keeps three contracts distinct: the frozen prompt, its supplied gold,
and the sign convention in the recoverable 1992 PRB source.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp


@dataclass(frozen=True)
class ResponseAudit:
    lindhard_magnitude: mp.mpf
    frozen_G: mp.mpf
    frozen_response_coefficient: mp.mpf
    hessian_required_by_frozen_relation: mp.mpf
    gold_hessian: mp.mpf
    response_implied_by_gold_hessian: mp.mpf
    source_G: mp.mpf
    source_response_coefficient: mp.mpf


def lindhard(x: mp.mpf | float | str) -> mp.mpf:
    """Dimensionless static Lindhard factor l(x)."""

    x = mp.mpf(x)
    if x == 0:
        return mp.mpf(1)
    if x == 1:
        return mp.mpf("0.5")
    if x > 1:
        log_ratio = mp.log1p(2 / (x - 1))
    else:
        log_ratio = mp.log1p(2 * x / (1 - x))
    return mp.mpf("0.5") * (
        1 + (1 - x**2) / (2 * x) * log_ratio
    )


def l1(x: mp.mpf | float | str) -> mp.mpf:
    """Contact-subtracted frozen kernel shape."""

    x = mp.mpf(x)
    return mp.mpf(5) / 8 * (1 / lindhard(x) - 3 * x**2 + mp.mpf(3) / 5)


def bisect_root(low: mp.mpf, high: mp.mpf, iterations: int = 300) -> mp.mpf:
    """Deterministic high-precision bisection for a sign-changing interval."""

    low = mp.mpf(low)
    high = mp.mpf(high)
    f_low = l1(low)
    f_high = l1(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if mp.sign(f_low) == mp.sign(f_high):
        raise ValueError("root interval does not bracket a sign change")
    for _ in range(iterations):
        mid = (low + high) / 2
        f_mid = l1(mid)
        if f_mid == 0:
            return mid
        if mp.sign(f_mid) == mp.sign(f_low):
            low, f_low = mid, f_mid
        else:
            high = mid
    return (low + high) / 2


def smallest_positive_root() -> mp.mpf:
    """Return the first positive root, bracketed after a deterministic scan."""

    previous_x = mp.mpf("1e-6")
    previous_y = l1(previous_x)
    for index in range(1, 10_000):
        x = mp.mpf(index) / 10_000
        y = l1(x)
        if mp.sign(y) != mp.sign(previous_y):
            return bisect_root(previous_x, x)
        previous_x, previous_y = x, y
    raise RuntimeError("no positive root found below the Lindhard cusp")


def response_audit(x: mp.mpf | float | str) -> ResponseAudit:
    """Expose the frozen sign contradiction in common positive units.

    The frozen prompt states ``-G = l > 0`` and ``delta_rho = -G delta_V``.
    Therefore G is negative and the stated response coefficient is positive.
    A variational Hessian K instead obeys ``delta_rho = -K^-1 delta_V``.
    """

    magnitude = lindhard(x)
    frozen_g = -magnitude
    frozen_response = -frozen_g
    required_hessian = 1 / frozen_g
    gold_hessian = 1 / magnitude
    gold_response = -1 / gold_hessian
    source_g = magnitude
    source_response = -source_g
    return ResponseAudit(
        lindhard_magnitude=magnitude,
        frozen_G=frozen_g,
        frozen_response_coefficient=frozen_response,
        hessian_required_by_frozen_relation=required_hessian,
        gold_hessian=gold_hessian,
        response_implied_by_gold_hessian=gold_response,
        source_G=source_g,
        source_response_coefficient=source_response,
    )


def asymptotic_coefficient(x: mp.mpf | float | str) -> mp.mpf:
    """Return x^2*l1(x), which tends to -3/35."""

    x = mp.mpf(x)
    return x**2 * l1(x)


def yukawa_second_moment() -> mp.mpf:
    """Second radial moment of exp(-r)/(4*pi*r), inverse FT of 1/(q^2+1)."""

    return mp.factorial(3)


def decomposition_coefficients() -> dict[str, mp.mpf]:
    """Conditional algebraic coefficients in frozen Task 3."""

    scale = mp.mpf(12) / 25 * (3 * mp.pi**2) ** (mp.mpf(2) / 3)
    return {
        "A": scale,
        "B": mp.mpf(3) / 4,
        "C": -mp.mpf(7) / 20,
        "nonlocal_inside_bracket": mp.mpf(8) / 5,
        "laplacian_delta_inside_bracket": -mp.mpf(3) / 4,
        "delta_inside_bracket": -mp.mpf(7) / 20,
    }
