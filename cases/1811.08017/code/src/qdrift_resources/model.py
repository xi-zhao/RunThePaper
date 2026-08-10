"""Formula-level gate-count bounds from Campbell, PRL 123, 070503."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
import math
from typing import Callable


@dataclass(frozen=True)
class Molecule:
    """The three resource parameters printed above each paper panel."""

    name: str
    qubits: int
    lambda_one: float
    lambda_max: float
    terms: int


def _logsumexp_pair(left: float, right: float) -> float:
    peak = max(left, right)
    return peak + math.log(math.exp(left - peak) + math.exp(right - peak))


def _minimum_integer(log_error: Callable[[int], float], epsilon: float) -> int:
    """Find a floating-point candidate for a monotone integer bound."""

    target = math.log(epsilon)
    lower = 0
    upper = 1
    while log_error(upper) > target:
        lower = upper
        upper *= 2
    while lower + 1 < upper:
        midpoint = (lower + upper) // 2
        if log_error(midpoint) <= target:
            upper = midpoint
        else:
            lower = midpoint
    return upper


DECIMAL_PRECISION = 60


def _decimal(value: int | float) -> Decimal:
    """Convert paper parameters without importing their binary representation."""

    return Decimal(str(value))


def _decimal_logsumexp_pair(left: Decimal, right: Decimal) -> Decimal:
    peak = max(left, right)
    return peak + ((left - peak).exp() + (right - peak).exp()).ln()


def _refine_minimum_integer(
    candidate: int,
    decimal_log_error: Callable[[int], Decimal],
    epsilon: float,
) -> int:
    """Refine a fast candidate to the exact high-precision integer boundary.

    Paper-scale gate counts reach roughly 10^25. At that scale adjacent Python
    integers map to the same IEEE-754 float, so a float-only binary search
    cannot establish that ``N`` passes while ``N-1`` fails. We use the fast
    search only to get close, then bracket and bisect with Decimal logarithms.
    """

    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        target = _decimal(epsilon).ln()

        def passes(value: int) -> bool:
            return decimal_log_error(value) <= target

        if passes(candidate):
            if candidate == 1 or not passes(candidate - 1):
                return candidate
            upper = candidate
            step = 1
            lower = max(0, candidate - step)
            while lower > 0 and passes(lower):
                upper = lower
                step *= 2
                lower = max(0, candidate - step)
        else:
            lower = candidate
            step = 1
            upper = candidate + step
            while not passes(upper):
                lower = upper
                step *= 2
                upper = candidate + step

        while lower + 1 < upper:
            midpoint = (lower + upper) // 2
            if passes(midpoint):
                upper = midpoint
            else:
                lower = midpoint
        return upper


def _decimal_boundary_is_minimal(
    candidate: int,
    decimal_log_error: Callable[[int], Decimal],
    epsilon: float,
) -> bool:
    """Return whether ``candidate`` passes and its predecessor fails."""

    if candidate < 1:
        return False
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        target = _decimal(epsilon).ln()
        return decimal_log_error(candidate) <= target and (
            candidate == 1 or decimal_log_error(candidate - 1) > target
        )


def qdrift_log_error(gates: int, lambda_one: float, time: float) -> float:
    """Appendix qDRIFT channel bound after N compositions."""

    return (
        math.log(2.0)
        + 2.0 * math.log(lambda_one * time)
        - math.log(gates)
        + 2.0 * lambda_one * time / gates
    )


def _qdrift_decimal_log_error(
    gates: int,
    lambda_one: float,
    time: float,
) -> Decimal:
    gates_decimal = _decimal(gates)
    scale = _decimal(lambda_one) * _decimal(time)
    return (
        Decimal(2).ln()
        + 2 * scale.ln()
        - gates_decimal.ln()
        + 2 * scale / gates_decimal
    )


def qdrift_gate_count(lambda_one: float, time: float, epsilon: float) -> int:
    candidate = _minimum_integer(
        lambda gates: qdrift_log_error(gates, lambda_one, time),
        epsilon,
    )
    return _refine_minimum_integer(
        candidate,
        lambda gates: _qdrift_decimal_log_error(gates, lambda_one, time),
        epsilon,
    )


def _first_order_log_error(
    segments: int,
    lambda_max: float,
    terms: int,
    time: float,
    randomized: bool,
) -> float:
    log_r = math.log(segments)
    scale = terms * lambda_max * time
    exponential = lambda_max * time / segments
    log_a = 2.0 * math.log(scale) - 2.0 * log_r + exponential
    log_b = 3.0 * math.log(scale) - math.log(3.0) - 3.0 * log_r + exponential
    local = _logsumexp_pair(2.0 * log_a, math.log(2.0) + log_b) if randomized else log_a
    return log_r - math.log(2.0) + local


def _first_order_decimal_log_error(
    segments: int,
    lambda_max: float,
    terms: int,
    time: float,
    randomized: bool,
) -> Decimal:
    log_r = _decimal(segments).ln()
    scale = _decimal(terms) * _decimal(lambda_max) * _decimal(time)
    exponential = _decimal(lambda_max) * _decimal(time) / _decimal(segments)
    log_a = 2 * scale.ln() - 2 * log_r + exponential
    log_b = 3 * scale.ln() - Decimal(3).ln() - 3 * log_r + exponential
    local = (
        _decimal_logsumexp_pair(2 * log_a, Decimal(2).ln() + log_b)
        if randomized
        else log_a
    )
    return log_r - Decimal(2).ln() + local


def first_order_gate_count(
    lambda_max: float,
    terms: int,
    time: float,
    epsilon: float,
    randomized: bool,
) -> int:
    candidate = _minimum_integer(
        lambda r: _first_order_log_error(r, lambda_max, terms, time, randomized),
        epsilon,
    )
    segments = _refine_minimum_integer(
        candidate,
        lambda r: _first_order_decimal_log_error(
            r,
            lambda_max,
            terms,
            time,
            randomized,
        ),
        epsilon,
    )
    return terms * segments


def _suzuki_log_error(
    segments: int,
    lambda_max: float,
    terms: int,
    time: float,
    order_index: int,
    randomized: bool,
) -> float:
    """Exact appendix bound for the order 2k Suzuki formula."""

    k = order_index
    factor = 2 * 5 ** (k - 1)
    power = 2 * k + 1
    log_r = math.log(segments)
    exponential = factor * lambda_max * time / segments
    log_a = (
        math.log(2.0)
        + power * math.log(factor * lambda_max * time * terms)
        - math.lgamma(power + 1)
        - power * log_r
        + exponential
    )
    log_b = (
        power * math.log(factor * lambda_max * time)
        + 2.0 * k * math.log(terms)
        - math.lgamma(2 * k)
        - power * log_r
        + exponential
    )
    local = _logsumexp_pair(2.0 * log_a, math.log(2.0) + log_b) if randomized else log_a
    return log_r - math.log(2.0) + local


def _suzuki_decimal_log_error(
    segments: int,
    lambda_max: float,
    terms: int,
    time: float,
    order_index: int,
    randomized: bool,
) -> Decimal:
    k = order_index
    factor = 2 * 5 ** (k - 1)
    power = 2 * k + 1
    log_r = _decimal(segments).ln()
    exponential = (
        _decimal(factor) * _decimal(lambda_max) * _decimal(time) / _decimal(segments)
    )
    log_a = (
        Decimal(2).ln()
        + _decimal(power)
        * (
            _decimal(factor) * _decimal(lambda_max) * _decimal(time) * _decimal(terms)
        ).ln()
        - _decimal(math.factorial(power)).ln()
        - _decimal(power) * log_r
        + exponential
    )
    log_b = (
        _decimal(power)
        * (_decimal(factor) * _decimal(lambda_max) * _decimal(time)).ln()
        + _decimal(2 * k) * _decimal(terms).ln()
        - _decimal(math.factorial(2 * k - 1)).ln()
        - _decimal(power) * log_r
        + exponential
    )
    local = (
        _decimal_logsumexp_pair(2 * log_a, Decimal(2).ln() + log_b)
        if randomized
        else log_a
    )
    return log_r - Decimal(2).ln() + local


def suzuki_gate_count(
    lambda_max: float,
    terms: int,
    time: float,
    epsilon: float,
    order_index: int,
    randomized: bool,
) -> int:
    candidate = _minimum_integer(
        lambda r: _suzuki_log_error(
            r,
            lambda_max,
            terms,
            time,
            order_index,
            randomized,
        ),
        epsilon,
    )
    segments = _refine_minimum_integer(
        candidate,
        lambda r: _suzuki_decimal_log_error(
            r,
            lambda_max,
            terms,
            time,
            order_index,
            randomized,
        ),
        epsilon,
    )
    gates_per_segment = 2 * 5 ** (order_index - 1) * terms
    return gates_per_segment * segments


def higher_order_gate_count(
    lambda_max: float,
    terms: int,
    time: float,
    epsilon: float,
    randomized: bool,
    max_order_index: int = 4,
) -> tuple[int, int]:
    candidates = {
        k: suzuki_gate_count(
            lambda_max,
            terms,
            time,
            epsilon,
            order_index=k,
            randomized=randomized,
        )
        for k in range(1, max_order_index + 1)
    }
    best_k = min(candidates, key=candidates.__getitem__)
    return candidates[best_k], best_k


def phase_estimation_counts(
    molecule: Molecule,
    failure_probability: float,
    energy_precision: float,
) -> tuple[float, float]:
    """Main Appendix Eqs. (E14) and (E28), including control overhead."""

    qdrift = (
        133.0 * molecule.lambda_one**2 / (energy_precision**2 * failure_probability**3)
    )
    random_trotter = (
        69.0
        * molecule.terms**2
        * molecule.lambda_max**1.5
        / (energy_precision**1.5 * failure_probability**2)
    )
    return qdrift, random_trotter
