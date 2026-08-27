#!/usr/bin/env python3
"""Independently audit the printed operator orientation and theta step.

The audit transcribes Eqs. (1)--(8) into local functions instead of calling the
reproduction implementation.  Production functions are imported only after
the independent results exist, so agreement is a cross-check rather than a
shared implementation.  No source image, author code, or author array is read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT = WORKSPACE / "outputs/checks/operator_and_step_alignment_review.json"


def rho_encoded(p: float, theta: float) -> np.ndarray:
    coherence = (2.0 * p - 1.0) / 2.0
    return np.array(
        [
            [0.5, coherence * np.exp(1j * theta)],
            [coherence * np.exp(-1j * theta), 0.5],
        ],
        dtype=complex,
    )


def printed_nonhermitian(p: float, theta: float) -> np.ndarray:
    return np.array(
        [
            [
                1.0 / (2.0 * (p - 1.0)) + 1.0 / (2.0 * p),
                np.exp(1j * theta) / (2.0 * p * (p - 1.0)),
            ],
            [
                np.exp(-1j * theta) / (2.0 * p * (1.0 - p)),
                1.0 / (2.0 * (1.0 - p)) - 1.0 / (2.0 * p),
            ],
        ],
        dtype=complex,
    )


def printed_hermitian(p: float, theta: float) -> np.ndarray:
    scale = (2.0 * p - 1.0) / 2.0
    return np.array(
        [
            [0.0, -1j * np.exp(1j * theta) * scale],
            [1j * np.exp(-1j * theta) * scale, 0.0],
        ],
        dtype=complex,
    )


def mean(rho: np.ndarray, observable: np.ndarray) -> complex:
    return complex(np.trace(rho @ observable))


def normalized_fringe_baseline(
    rho: np.ndarray,
    observable: np.ndarray,
) -> float:
    gram = observable.conjugate().T @ observable
    eigenvalues = np.linalg.eigvalsh(gram).real
    scale_squared = float(eigenvalues.max())
    return float((1.0 + mean(rho, gram).real / scale_squared) / 4.0)


def finite_step_variance(
    p: float,
    theta: float,
    observable: np.ndarray,
    *,
    step: float,
    product_order: str,
) -> float:
    rho = rho_encoded(p, theta)
    observable_mean = mean(rho, observable)
    if product_order == "printed_A_dagger_A":
        product = observable.conjugate().T @ observable
    elif product_order == "reversed_A_A_dagger":
        product = observable @ observable.conjugate().T
    else:
        raise ValueError(product_order)
    numerator = mean(rho, product).real - abs(observable_mean) ** 2
    plus = mean(rho_encoded(p, theta + step), observable)
    minus = mean(rho_encoded(p, theta - step), observable)
    derivative = (plus - minus) / (2.0 * step)
    return float(numerator / abs(derivative) ** 2)


def reciprocal_fisher_nonhermitian(p: float) -> float:
    return float(4.0 * p * (1.0 - p) / (2.0 * p - 1.0) ** 2)


def reciprocal_fisher_hermitian(p: float) -> float:
    return float(1.0 / (2.0 * p - 1.0) ** 2)


def main() -> int:
    theta = 0.3 * np.pi
    audit_p = (0.01, 0.15, 0.25, 0.75)
    steps = (0.1, 0.05, 0.01, 0.001, 0.00001)

    fringe_rows: list[dict[str, float]] = []
    for p in (0.75, 0.15):
        rho = rho_encoded(p, theta)
        printed = printed_nonhermitian(p, theta)
        fringe_rows.append(
            {
                "p": p,
                "printed_eq5_baseline": normalized_fringe_baseline(rho, printed),
                "adjoint_eq5_baseline": normalized_fringe_baseline(
                    rho,
                    printed.conjugate().T,
                ),
                "hermitian_baseline": normalized_fringe_baseline(
                    rho,
                    printed_hermitian(p, theta),
                ),
            }
        )

    variance_rows: list[dict[str, float]] = []
    maximum_identity_error = 0.0
    for p in audit_p:
        observable = printed_nonhermitian(p, theta)
        hermitian = printed_hermitian(p, theta)
        bound_nonhermitian = reciprocal_fisher_nonhermitian(p)
        bound_hermitian = reciprocal_fisher_hermitian(p)
        for step in steps:
            finite_step_factor = float((step / np.sin(step)) ** 2)
            literal = finite_step_variance(
                p,
                theta,
                observable,
                step=step,
                product_order="printed_A_dagger_A",
            )
            reversed_order = finite_step_variance(
                p,
                theta,
                observable,
                step=step,
                product_order="reversed_A_A_dagger",
            )
            hermitian_value = finite_step_variance(
                p,
                theta,
                hermitian,
                step=step,
                product_order="printed_A_dagger_A",
            )
            expected_literal = (bound_nonhermitian + 4.0) * finite_step_factor
            expected_reversed = bound_nonhermitian * finite_step_factor
            expected_hermitian = bound_hermitian * finite_step_factor
            identity_error = max(
                abs(literal - expected_literal),
                abs(reversed_order - expected_reversed),
                abs(hermitian_value - expected_hermitian),
            )
            maximum_identity_error = max(maximum_identity_error, identity_error)
            variance_rows.append(
                {
                    "p": p,
                    "theta_step": step,
                    "finite_step_factor": finite_step_factor,
                    "printed_order_variance": literal,
                    "reversed_order_variance": reversed_order,
                    "hermitian_variance": hermitian_value,
                    "maximum_identity_error": identity_error,
                }
            )

    sys.path.insert(0, str(WORKSPACE))
    from src.sensing import (  # noqa: PLC0415
        encoded_state,
        error_propagation_variance,
        optimal_hermitian,
        optimal_nonhermitian,
    )

    maximum_implementation_error = 0.0
    for p in audit_p:
        maximum_implementation_error = max(
            maximum_implementation_error,
            float(np.max(np.abs(rho_encoded(p, theta) - encoded_state(p, theta)))),
            float(
                np.max(
                    np.abs(
                        printed_nonhermitian(p, theta)
                        - optimal_nonhermitian(p, theta)
                    )
                )
            ),
            float(
                np.max(
                    np.abs(
                        printed_hermitian(p, theta)
                        - optimal_hermitian(p, theta)
                    )
                )
            ),
        )
        for step in steps:
            independent = finite_step_variance(
                p,
                theta,
                printed_nonhermitian(p, theta),
                step=step,
                product_order="printed_A_dagger_A",
            )
            production = error_propagation_variance(
                p,
                theta,
                optimal_nonhermitian(p, theta),
                theta_step=step,
                ordering="literal",
            )
            maximum_implementation_error = max(
                maximum_implementation_error,
                abs(independent - production),
            )

    paper_step_factor = float((0.1 / np.sin(0.1)) ** 2)
    converged_step_factor = float((1e-5 / np.sin(1e-5)) ** 2)
    passed = maximum_identity_error < 1e-10 and maximum_implementation_error < 1e-10
    payload = {
        "schema_version": 1,
        "paper_id": "2607.23978",
        "status": "passed" if passed else "failed",
        "scope": ["T001", "T003"],
        "scientific_input_boundary": {
            "paper_equations_transcribed": ["Eq. (1)", "Eq. (2)", "Eq. (3)", "Eq. (5)", "Eq. (8)"],
            "paper_parameters": {"p": list(audit_p), "theta_over_pi": 0.3, "theta_step": 0.1},
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_scientific_input": False,
        },
        "findings": {
            "t001_fringe_orientation": fringe_rows,
            "t003_variance_identity": (
                "With the printed Eq. (3) order, Eq. (5) gives "
                "(1/F_nH+4)*(h/sin(h))^2. Reversing the product order gives "
                "(1/F_nH)*(h/sin(h))^2."
            ),
            "paper_step_factor": paper_step_factor,
            "converged_step_factor": converged_step_factor,
            "paper_step_relative_shift": paper_step_factor - 1.0,
        },
        "checks": {
            "maximum_exact_identity_error": maximum_identity_error,
            "maximum_independent_vs_production_error": maximum_implementation_error,
            "all_finite": bool(
                np.isfinite(
                    [row["printed_order_variance"] for row in variance_rows]
                ).all()
            ),
        },
        "variance_rows": variance_rows,
        "interpretation_boundary": (
            "This audit excludes the tested algebra, parameter transcription, "
            "finite-difference, and implementation alternatives. A fresh-context "
            "reviewer must still decide whether the source inconsistency is a "
            "paper-error candidate or is resolved by another documented convention."
        ),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
