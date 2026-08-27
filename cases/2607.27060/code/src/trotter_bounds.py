"""Paper-derived Trotter-step and gate-count calculations.

This module evaluates only formulas and parameter grids transcribed and
verified from the paper. The separately published author code is outside the
input and evidence boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, e, exp, inf, log, sqrt


METHODS = ("det1", "ran1", "det2", "ran2")


@dataclass(frozen=True)
class TargetSpec:
    target_id: str
    figure_id: str
    model: str
    method: str
    title: str
    m_values: tuple[int, ...]
    t: float
    lam: float
    epsilon: float
    second_order: bool


_XX_M = (7, 9, 11, 13, 15, 17, 19)
_TFIM_M = (5, 8, 12, 15, 19)


TARGET_SPECS: dict[str, TargetSpec] = {
    "T-FIG002A": TargetSpec("T-FIG002A", "FIG002A", "xx_spin_chain", "det1", "First Order Deterministic", _XX_M, 2.0, 7.071, 1e-3, False),
    "T-FIG002B": TargetSpec("T-FIG002B", "FIG002B", "xx_spin_chain", "ran1", "First Order Randomised", _XX_M, 2.0, 7.071, 1e-3, False),
    "T-FIG002C": TargetSpec("T-FIG002C", "FIG002C", "xx_spin_chain", "det2", "Second Order Deterministic", _XX_M, 2.0, 7.071, 1e-3, True),
    "T-FIG002D": TargetSpec("T-FIG002D", "FIG002D", "xx_spin_chain", "ran2", "Second Order Randomised", _XX_M, 2.0, 7.071, 1e-3, True),
    "T-FIG003A": TargetSpec("T-FIG003A", "FIG003A", "tfim_lattice", "det1", "First Order Deterministic", _TFIM_M, 5.0, 8.0, 1e-5, False),
    "T-FIG003B": TargetSpec("T-FIG003B", "FIG003B", "tfim_lattice", "ran1", "First Order Randomised", _TFIM_M, 5.0, 8.0, 1e-5, False),
    "T-FIG003C": TargetSpec("T-FIG003C", "FIG003C", "tfim_lattice", "det2", "Second Order Deterministic", _TFIM_M, 5.0, 8.0, 1e-5, True),
    "T-FIG003D": TargetSpec("T-FIG003D", "FIG003D", "tfim_lattice", "ran2", "Second Order Randomised", _TFIM_M, 5.0, 8.0, 1e-5, True),
}


def _validate_inputs(t: float, lam: float, m_terms: int, n_steps: int | None = None) -> None:
    if t <= 0 or lam <= 0 or m_terms <= 0:
        raise ValueError("t, lambda, and M must be positive")
    if n_steps is not None and n_steps <= 0:
        raise ValueError("N must be a positive integer")


def log_epsilon_hat(method: str, t: float, lam: float, m_terms: int, n_steps: int) -> float:
    """Return log(epsilon_hat) without overflow during the doubling search."""
    _validate_inputs(t, lam, m_terms, n_steps)
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    a = t * lam * m_terms
    if method == "det1":
        return 2.0 * log(a) - log(n_steps) + a / n_steps
    if method in {"ran1", "det2"}:
        return 3.0 * log(a) - log(3.0) - 2.0 * log(n_steps) + a / n_steps
    return 3.0 * log(t * lam) + 2.0 * log(m_terms) - 2.0 * log(n_steps) + a / n_steps


def epsilon_hat(method: str, t: float, lam: float, m_terms: int, n_steps: int) -> float:
    """Evaluate the paper's precision function, returning infinity on overflow."""
    value_log = log_epsilon_hat(method, t, lam, m_terms, n_steps)
    if value_log > 709.0:
        return inf
    return exp(value_log)


def epsilon_hat_det1(t: float, lam: float, m_terms: int, n_steps: int) -> float:
    return epsilon_hat("det1", t, lam, m_terms, n_steps)


def epsilon_hat_ran1(t: float, lam: float, m_terms: int, n_steps: int) -> float:
    return epsilon_hat("ran1", t, lam, m_terms, n_steps)


def epsilon_hat_det2(t: float, lam: float, m_terms: int, n_steps: int) -> float:
    return epsilon_hat("det2", t, lam, m_terms, n_steps)


def epsilon_hat_ran2(t: float, lam: float, m_terms: int, n_steps: int) -> float:
    return epsilon_hat("ran2", t, lam, m_terms, n_steps)


def analytic_steps(method: str, t: float, lam: float, m_terms: int, epsilon: float) -> int:
    """Evaluate the verified sufficient integer bound from Section 3."""
    _validate_inputs(t, lam, m_terms)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    a = t * lam * m_terms
    if method == "det1":
        sufficient = e * a**2 / epsilon
    elif method in {"ran1", "det2"}:
        sufficient = sqrt(e * a**3 / (3.0 * epsilon))
    else:
        sufficient = sqrt(e * (t * lam) ** 3 * m_terms**2 / epsilon)
    return ceil(max(a, sufficient))


def minimum_steps(method: str, t: float, lam: float, m_terms: int, epsilon: float) -> int:
    """Return the least positive integer satisfying epsilon_hat <= epsilon."""
    _validate_inputs(t, lam, m_terms)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    threshold = log(epsilon)

    def passes(n_steps: int) -> bool:
        return log_epsilon_hat(method, t, lam, m_terms, n_steps) <= threshold

    lower = 1
    upper = 1
    while not passes(upper):
        upper *= 2

    while lower < upper:
        middle = (lower + upper) // 2
        if passes(middle):
            upper = middle
        else:
            lower = middle + 1
    return lower


def gate_complexity(m_terms: int, n_steps: int, *, second_order: bool) -> int:
    _validate_inputs(1.0, 1.0, m_terms, n_steps)
    return (2 if second_order else 1) * m_terms * n_steps


def compute_rows(spec: TargetSpec) -> list[dict[str, int | float | None]]:
    """Generate all four visible series and threshold certificates for one target."""
    rows: list[dict[str, int | float | None]] = []
    for m_terms in spec.m_values:
        n_analytic = analytic_steps(spec.method, spec.t, spec.lam, m_terms, spec.epsilon)
        n_min = minimum_steps(spec.method, spec.t, spec.lam, m_terms, spec.epsilon)
        rows.append(
            {
                "M": m_terms,
                "N_analytic": n_analytic,
                "N_min": n_min,
                "g_analytic": gate_complexity(m_terms, n_analytic, second_order=spec.second_order),
                "g_min": gate_complexity(m_terms, n_min, second_order=spec.second_order),
                "epsilon_at_N_analytic": epsilon_hat(spec.method, spec.t, spec.lam, m_terms, n_analytic),
                "epsilon_at_N_min": epsilon_hat(spec.method, spec.t, spec.lam, m_terms, n_min),
                "epsilon_at_predecessor": (
                    epsilon_hat(spec.method, spec.t, spec.lam, m_terms, n_min - 1)
                    if n_min > 1
                    else None
                ),
            }
        )
    return rows


def target_slug(target_id: str) -> str:
    if target_id not in TARGET_SPECS:
        raise ValueError(f"unknown frozen target: {target_id}")
    return TARGET_SPECS[target_id].figure_id.lower()
