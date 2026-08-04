"""Independent numerical implementation for the frozen Fig. 2/3 targets.

The module implements the four precision functions in Table 1, the sufficient
analytic bounds in Eqs. (14), (20), (22), and (24), and a lower-bound binary
search for the smallest integer N satisfying the requested precision.

No source-figure pixels, digitized values, or author-generated result files are
read here.  The only inputs are the equations and paper parameters recorded in
``TARGET_SPECS``.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from scipy.special import lambertw


METHODS = ("det1", "ran1", "det2", "ran2")


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    t: float
    lam: float
    epsilon: float
    m_values: tuple[int, ...]
    size_name: str
    size_values: tuple[int, ...]
    extra_parameters: dict[str, float]


@dataclass(frozen=True)
class TargetSpec:
    target_id: str
    figure_id: str
    panel: str
    model: ModelSpec
    method: str
    title: str


XX_MODEL = ModelSpec(
    model_id="xx_spin_chain",
    t=2.0,
    # Section 5.4 reports lambda=7.071.  The literal reported value is used so
    # the paper-to-generated parameter map is auditable.
    lam=7.071,
    epsilon=1.0e-3,
    m_values=(7, 9, 11, 13, 15, 17, 19),
    size_name="P",
    size_values=(2, 3, 4, 5, 6, 7, 8),
    extra_parameters={"Omega": 3.94, "gamma": 0.31},
)

TFIM_MODEL = ModelSpec(
    model_id="tfim_lattice",
    t=5.0,
    lam=8.0,
    epsilon=1.0e-5,
    m_values=(5, 8, 12, 15, 19),
    size_name="n_spins",
    size_values=(2, 3, 4, 5, 6),
    extra_parameters={"J": 1.0, "h": 0.5, "gamma": 0.1},
)


def _target(
    target_id: str,
    figure_id: str,
    panel: str,
    model: ModelSpec,
    method: str,
    title: str,
) -> TargetSpec:
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    return TargetSpec(target_id, figure_id, panel, model, method, title)


TARGET_SPECS: dict[str, TargetSpec] = {
    "T-FIG002A": _target(
        "T-FIG002A", "FIG002A", "a", XX_MODEL, "det1", "First Order Deterministic"
    ),
    "T-FIG002B": _target(
        "T-FIG002B", "FIG002B", "b", XX_MODEL, "ran1", "First Order Randomised"
    ),
    "T-FIG002C": _target(
        "T-FIG002C", "FIG002C", "c", XX_MODEL, "det2", "Second Order Deterministic"
    ),
    "T-FIG002D": _target(
        "T-FIG002D", "FIG002D", "d", XX_MODEL, "ran2", "Second Order Randomised"
    ),
    "T-FIG003A": _target(
        "T-FIG003A", "FIG003A", "a", TFIM_MODEL, "det1", "First Order Deterministic"
    ),
    "T-FIG003B": _target(
        "T-FIG003B", "FIG003B", "b", TFIM_MODEL, "ran1", "First Order Randomised"
    ),
    "T-FIG003C": _target(
        "T-FIG003C", "FIG003C", "c", TFIM_MODEL, "det2", "Second Order Deterministic"
    ),
    "T-FIG003D": _target(
        "T-FIG003D", "FIG003D", "d", TFIM_MODEL, "ran2", "Second Order Randomised"
    ),
}


def target_slug(target_id: str) -> str:
    return target_id.removeprefix("T-").lower()


def _validate_inputs(t: float, lam: float, m_terms: int, n_steps: int) -> None:
    if t <= 0 or lam <= 0 or m_terms <= 0 or n_steps <= 0:
        raise ValueError("t, lambda, M, and N must all be positive")


def log_precision_error(
    method: str,
    t: float,
    lam: float,
    m_terms: int,
    n_steps: int,
) -> float:
    """Return log(epsilon_hat) without overflowing at small N."""

    _validate_inputs(t, lam, m_terms, n_steps)
    x = t * lam * m_terms
    if method == "det1":
        return 2.0 * math.log(x) - math.log(n_steps) + x / n_steps
    if method in {"ran1", "det2"}:
        return (
            3.0 * math.log(x)
            - math.log(3.0)
            - 2.0 * math.log(n_steps)
            + x / n_steps
        )
    if method == "ran2":
        return (
            3.0 * math.log(t * lam)
            + 2.0 * math.log(m_terms)
            - 2.0 * math.log(n_steps)
            + x / n_steps
        )
    raise ValueError(f"unknown method: {method}")


def precision_error(
    method: str,
    t: float,
    lam: float,
    m_terms: int,
    n_steps: int,
) -> float:
    """Evaluate epsilon_hat, returning infinity rather than overflowing."""

    log_value = log_precision_error(method, t, lam, m_terms, n_steps)
    return math.inf if log_value > math.log(float.fromhex("0x1.fffffffffffffp+1023")) else math.exp(log_value)


def analytic_bound(
    method: str,
    t: float,
    lam: float,
    m_terms: int,
    epsilon: float,
) -> int:
    """Evaluate the paper's sufficient analytic integer bound."""

    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    x = t * lam * m_terms
    if method == "det1":
        sufficient = math.e * x**2 / epsilon
    elif method in {"ran1", "det2"}:
        sufficient = math.sqrt(math.e * x**3 / (3.0 * epsilon))
    elif method == "ran2":
        sufficient = math.sqrt(
            math.e * (t * lam) ** 3 * m_terms**2 / epsilon
        )
    else:
        raise ValueError(f"unknown method: {method}")
    return math.ceil(max(x, sufficient))


def minimum_steps(
    method: str,
    t: float,
    lam: float,
    m_terms: int,
    epsilon: float,
) -> tuple[int, int]:
    """Return the minimum valid integer N and precision-function evaluations."""

    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    log_epsilon = math.log(epsilon)
    evaluations = 0

    def exceeds(n_steps: int) -> bool:
        nonlocal evaluations
        evaluations += 1
        return log_precision_error(method, t, lam, m_terms, n_steps) > log_epsilon

    lower = 1
    upper = 1
    while exceeds(upper):
        upper *= 2

    while lower < upper:
        middle = (lower + upper) // 2
        if exceeds(middle):
            lower = middle + 1
        else:
            upper = middle
    return lower, evaluations


def continuous_threshold(
    method: str,
    t: float,
    lam: float,
    m_terms: int,
    epsilon: float,
) -> float:
    """Solve epsilon_hat(N)=epsilon analytically with Lambert W.

    This is an independent cross-check of the discrete binary search, not an
    input to it.
    """

    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    x = t * lam * m_terms
    if method == "det1":
        root = x / lambertw(epsilon / x).real
    elif method in {"ran1", "det2"}:
        coefficient = x**3 / 3.0
        argument = 0.5 * x * math.sqrt(epsilon / coefficient)
        root = x / (2.0 * lambertw(argument).real)
    elif method == "ran2":
        coefficient = (t * lam) ** 3 * m_terms**2
        argument = 0.5 * x * math.sqrt(epsilon / coefficient)
        root = x / (2.0 * lambertw(argument).real)
    else:
        raise ValueError(f"unknown method: {method}")
    return float(root)


def gate_complexity(method: str, m_terms: int, n_steps: int) -> int:
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    multiplier = 2 if method in {"det2", "ran2"} else 1
    return multiplier * m_terms * n_steps


def generate_rows(spec: TargetSpec) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    model = spec.model
    for size, m_terms in zip(model.size_values, model.m_values, strict=True):
        n_analytic = analytic_bound(
            spec.method, model.t, model.lam, m_terms, model.epsilon
        )
        n_min, evaluations = minimum_steps(
            spec.method, model.t, model.lam, m_terms, model.epsilon
        )
        continuous = continuous_threshold(
            spec.method, model.t, model.lam, m_terms, model.epsilon
        )
        rows.append(
            {
                model.size_name: size,
                "M": m_terms,
                "N_analytic": n_analytic,
                "N_min": n_min,
                "g_analytic": gate_complexity(spec.method, m_terms, n_analytic),
                "g_min": gate_complexity(spec.method, m_terms, n_min),
                "epsilon_at_N_analytic": precision_error(
                    spec.method, model.t, model.lam, m_terms, n_analytic
                ),
                "epsilon_at_N_min": precision_error(
                    spec.method, model.t, model.lam, m_terms, n_min
                ),
                "epsilon_at_N_min_minus_1": precision_error(
                    spec.method, model.t, model.lam, m_terms, n_min - 1
                )
                if n_min > 1
                else math.inf,
                "continuous_threshold": continuous,
                "binary_search_evaluations": evaluations,
            }
        )
    return rows


def scientific_checks(spec: TargetSpec, rows: list[dict[str, Any]]) -> dict[str, Any]:
    epsilon = spec.model.epsilon
    gate_multiplier = 2 if spec.method in {"det2", "ran2"} else 1
    checks = {
        "analytic_bound_sufficient": all(
            row["epsilon_at_N_analytic"] <= epsilon for row in rows
        ),
        "binary_search_threshold_satisfied": all(
            row["epsilon_at_N_min"] <= epsilon for row in rows
        ),
        "binary_search_minimal": all(
            row["epsilon_at_N_min_minus_1"] > epsilon for row in rows
        ),
        "lambert_w_crosscheck": all(
            row["N_min"] == math.ceil(row["continuous_threshold"]) for row in rows
        ),
        "gate_count_identity": all(
            row["g_analytic"] == gate_multiplier * row["M"] * row["N_analytic"]
            and row["g_min"] == gate_multiplier * row["M"] * row["N_min"]
            for row in rows
        ),
        "analytic_not_below_optimised": all(
            row["N_analytic"] >= row["N_min"] for row in rows
        ),
        "monotone_with_M": all(
            left["N_analytic"] < right["N_analytic"]
            and left["N_min"] < right["N_min"]
            and left["g_analytic"] < right["g_analytic"]
            and left["g_min"] < right["g_min"]
            for left, right in zip(rows, rows[1:])
        ),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "all_passed": all(checks.values()),
    }


def write_rows_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows_list = list(rows)
    if not rows_list:
        raise ValueError("cannot write an empty dataset")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows_list[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_list)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
