"""Public-equation targets that do not require the commercial Plaquette code.

The routines in this module are derived from the paper's printed channels.
They do not import Plaquette, author code, author arrays, or source pixels.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm


def _dissipator_superoperator(operator: np.ndarray) -> np.ndarray:
    """Return the column-vectorized Lindblad dissipator D[operator]."""

    dimension = operator.shape[0]
    identity = np.eye(dimension, dtype=complex)
    gram = operator.conj().T @ operator
    return (
        np.kron(operator.conj(), operator)
        - 0.5 * np.kron(identity, gram)
        - 0.5 * np.kron(gram.T, identity)
    )


def heating_transition_matrix(
    *, levels: int, gamma_h: float, n_thermal: float, interval: float
) -> np.ndarray:
    """Reproduce Fig. 10 from Eq. (20) by independent Lindblad propagation."""

    if levels < 2:
        raise ValueError("levels must be at least two")
    if gamma_h < 0 or n_thermal < 0 or interval < 0:
        raise ValueError("rates and interval must be nonnegative")

    annihilation = np.zeros((levels, levels), dtype=complex)
    for number in range(1, levels):
        annihilation[number - 1, number] = np.sqrt(number)
    creation = annihilation.conj().T
    liouvillian = gamma_h * (
        n_thermal * _dissipator_superoperator(creation)
        + (n_thermal + 1.0) * _dissipator_superoperator(annihilation)
    )
    channel = expm(liouvillian * interval)

    transition = np.empty((levels, levels), dtype=float)
    for initial in range(levels):
        state = np.zeros((levels, levels), dtype=complex)
        state[initial, initial] = 1.0
        evolved = (channel @ state.reshape(-1, order="F")).reshape(
            (levels, levels), order="F"
        )
        transition[:, initial] = np.real(np.diag(evolved))
    return transition


@dataclass(frozen=True)
class TwirlTransition:
    source_sector: str
    destination_sector: str
    transition_probability: float
    error_weights: dict[str, float]

    @property
    def conditional_error_probabilities(self) -> dict[str, float]:
        return {
            error: weight / self.transition_probability
            for error, weight in self.error_weights.items()
        }


def leakage_generalized_pauli_twirl(p_transfer: float) -> list[TwirlTransition]:
    """Derive Table III weights for the two-Kraus leakage channel, Eq. (12).

    ``error_weights`` are joint transition-and-Pauli weights.  Dividing them by
    ``transition_probability`` gives the actual conditional probabilities.
    This distinction exposes a stable header/value inconsistency in Table III.
    """

    if not 0.0 <= p_transfer <= 1.0:
        raise ValueError("p_transfer must lie in [0, 1]")
    survival_amplitude = np.sqrt(1.0 - p_transfer)
    weak_z_weight = ((1.0 - survival_amplitude) / 4.0) ** 2
    leaked_z_weight = ((1.0 - survival_amplitude) / 2.0) ** 2
    return [
        TwirlTransition(
            "(comp,comp)",
            "(comp,comp)",
            1.0 - p_transfer / 4.0,
            {"IZ": weak_z_weight, "ZI": weak_z_weight, "ZZ": weak_z_weight},
        ),
        TwirlTransition(
            "(comp,comp)",
            "(comp,2)",
            p_transfer / 4.0,
            {"X·": p_transfer / 8.0, "Y·": p_transfer / 8.0},
        ),
        TwirlTransition(
            "(comp,2)",
            "(comp,comp)",
            p_transfer / 2.0,
            {"X·": p_transfer / 4.0, "Y·": p_transfer / 4.0},
        ),
        TwirlTransition(
            "(comp,2)",
            "(comp,2)",
            1.0 - p_transfer / 2.0,
            {"Z·": leaked_z_weight},
        ),
    ]


def printed_fig10_matrix() -> np.ndarray:
    """Return only the paper's rounded values for post-compute validation."""

    return np.array(
        [
            [0.84660, 0.25980, 0.07970, 0.02460, 0.00860],
            [0.12990, 0.53660, 0.31730, 0.14560, 0.06850],
            [0.01990, 0.15860, 0.38790, 0.31980, 0.22070],
            [0.00310, 0.03640, 0.15990, 0.32660, 0.36670],
            [0.00050, 0.00860, 0.05520, 0.18340, 0.33550],
        ],
        dtype=float,
    )
