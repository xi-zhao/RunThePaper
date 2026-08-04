"""Exact identities for the synthetic Bayesian scar-weight benchmark extension."""

from __future__ import annotations

import math
from typing import Iterable


def binary_relative_entropy(p: float, q: float) -> float:
    if p == q:
        return 0.0
    return p * math.log(p / q) + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))


def safe_count_log(count: int, value: float) -> float:
    """Return log(value**count), including the 0**0 convention."""

    if count == 0:
        return 0.0
    if value == 0.0:
        return -math.inf
    return count * math.log(value)


def fixed_word_log_survival(
    bullet_weights: Iterable[float], bullet_count: int, word_length: int
) -> float:
    """Best squared norm of the diagonal conditioned product."""

    circle_count = word_length - bullet_count
    sector_logs = [
        safe_count_log(bullet_count, mu) + safe_count_log(circle_count, 1.0 - mu)
        for mu in bullet_weights
    ]
    return 2.0 * max(sector_logs)


def sector_growth(empirical_bullet_rate: float, mu: float, q: float) -> float:
    return empirical_bullet_rate * math.log(mu / q) + (
        1.0 - empirical_bullet_rate
    ) * math.log((1.0 - mu) / (1.0 - q))


def zero_growth_frequency(mu: float, q: float) -> float:
    """Unique empirical outcome rate at which one sector has zero growth."""

    if mu == q:
        return q
    bullet_log = math.log(mu / q)
    circle_log = math.log((1.0 - mu) / (1.0 - q))
    return -circle_log / (bullet_log - circle_log)


def exact_ldp_rate(a: float, b: float, q: float) -> dict[str, float | str]:
    """Exact asymptotic no-decay rate for the frozen Bayesian update equations.

    The Bayesian evidence telescopes to a two-component mixture. Each component
    supplies one Bernoulli large-deviation boundary; the cheaper boundary wins.
    """

    candidates: list[tuple[float, float, str]] = []
    for mu, sector in ((a, "a"), (b, "b")):
        root = zero_growth_frequency(mu, q)
        rate = binary_relative_entropy(root, q)
        candidates.append((rate, root, sector))
    rate, root, sector = min(candidates)
    return {
        "Gamma": rate,
        "p_star": root,
        "selected_sector": sector,
        "a_root": candidates[0][1],
        "a_rate": candidates[0][0],
        "b_root": candidates[1][1],
        "b_rate": candidates[1][0],
    }


def frozen_regime_flags(a: float, b: float, q: float) -> dict[str, bool | float]:
    alpha = math.log(a / q)
    beta = math.log((1.0 - b) / (1.0 - q))
    best_bullet = math.log(b / q)
    best_circle = math.log((1.0 - a) / (1.0 - q))
    return {
        "alpha": alpha,
        "beta": beta,
        "best_bullet": best_bullet,
        "best_circle": best_circle,
        "infinite_branch": max(alpha, beta) < 0.0,
        "zero_branch": min(best_bullet, best_circle) > 0.0,
    }


def bayesian_path(
    outcomes: Iterable[bool], a: float, b: float, q: float
) -> dict[str, float | int]:
    """Execute the frozen full Bayesian update and accumulated log increments."""

    nu_a = 0.5
    nu_b = 0.5
    accumulated = 0.0
    bullet_count = 0
    step_count = 0
    for is_bullet in outcomes:
        step_count += 1
        if is_bullet:
            bullet_count += 1
            weight_a, weight_b, baseline = a, b, q
        else:
            weight_a, weight_b, baseline = 1.0 - a, 1.0 - b, 1.0 - q
        evidence = nu_a * weight_a + nu_b * weight_b
        accumulated += math.log(evidence) - math.log(baseline)
        nu_a = nu_a * weight_a / evidence
        nu_b = nu_b * weight_b / evidence

    circle_count = step_count - bullet_count
    sector_a = safe_count_log(bullet_count, a) + safe_count_log(circle_count, 1.0 - a)
    sector_b = safe_count_log(bullet_count, b) + safe_count_log(circle_count, 1.0 - b)
    baseline = safe_count_log(bullet_count, q) + safe_count_log(circle_count, 1.0 - q)
    maximum = max(sector_a, sector_b)
    log_mixture = maximum + math.log(
        0.5 * math.exp(sector_a - maximum) + 0.5 * math.exp(sector_b - maximum)
    )
    return {
        "steps": step_count,
        "bullet_count": bullet_count,
        "accumulated_log_growth": accumulated,
        "telescoped_log_growth": log_mixture - baseline,
        "posterior_a": nu_a,
        "posterior_b": nu_b,
    }


def is_projector_eigenvalue(value: float, tolerance: float = 1e-12) -> bool:
    return abs(value) <= tolerance or abs(value - 1.0) <= tolerance


def fibonacci(index: int) -> int:
    previous, current = 0, 1
    for _ in range(index):
        previous, current = current, previous + current
    return previous


def constrained_ring_dimension(length: int) -> int:
    return fibonacci(length - 1) + fibonacci(length + 1)
