"""Executable boundary for the paper's zero-discord hardness assertion."""

from __future__ import annotations

from dataclasses import dataclass
import cmath

import numpy as np


@dataclass(frozen=True)
class PhaseInvolutionTrace:
    dimension: int
    phase_radians: float
    positive_eigenvalues: int
    negative_eigenvalues: int
    normalized_trace_real: float
    normalized_trace_imag: float


def phase_involution_normalized_trace(
    phase_radians: float,
    positive_eigenvalues: int,
    negative_eigenvalues: int,
) -> PhaseInvolutionTrace:
    """Evaluate Tr(exp(i phi) A)/d for a Hermitian involution A."""

    positive = int(positive_eigenvalues)
    negative = int(negative_eigenvalues)
    if positive < 0 or negative < 0 or positive + negative < 1:
        raise ValueError("eigenvalue multiplicities must be non-negative and nonempty")
    dimension = positive + negative
    value = cmath.exp(1.0j * float(phase_radians)) * (positive - negative) / dimension
    return PhaseInvolutionTrace(
        dimension=dimension,
        phase_radians=float(phase_radians),
        positive_eigenvalues=positive,
        negative_eigenvalues=negative,
        normalized_trace_real=float(value.real),
        normalized_trace_imag=float(value.imag),
    )


def explicit_phase_involution(
    phase_radians: float,
    positive_eigenvalues: int,
    negative_eigenvalues: int,
) -> np.ndarray:
    """Construct a diagonal representative for formula-level cross-checks."""

    record = phase_involution_normalized_trace(
        phase_radians, positive_eigenvalues, negative_eigenvalues
    )
    eigenvalues = np.concatenate(
        (
            np.ones(record.positive_eigenvalues),
            -np.ones(record.negative_eigenvalues),
        )
    )
    return cmath.exp(1.0j * record.phase_radians) * np.diag(eigenvalues)


def hardness_contract_boundary() -> dict[str, object]:
    """State exactly why the publication's complexity claim is undecidable.

    An explicit matrix has an input length exponential in qubit count and its
    trace is directly readable.  A succinct circuit may define a hard counting
    problem, but the paper gives no circuit family, approximation promise,
    classical model, or reduction for the phase-times-involution subset.
    """

    return {
        "adjudication": "inconclusive",
        "explicit_matrix_input": {
            "normalized_trace_algorithm": "sum diagonal entries and divide by d",
            "arithmetic_operations": "O(d)",
            "hardness_in_qubit_count_established": False,
            "reason": "The explicit input itself has size at least d=2^n.",
        },
        "succinct_circuit_input": {
            "hardness_established": False,
            "missing_contract_fields": [
                "encoded zero-discord unitary family",
                "uniform circuit-generation rule",
                "additive or multiplicative approximation tolerance",
                "success probability",
                "classical computational model",
                "reduction or counter-algorithm",
            ],
        },
        "resource_conclusion_available": False,
        "reason": (
            "The algebraic zero-discord condition is executable, but it does "
            "not by itself prove classical hardness or exclude discord as a resource."
        ),
    }
