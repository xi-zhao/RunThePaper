"""Two-mode and two-photon interferometer algebra.

The implementation starts from Eqs. (1)-(4) of the paper.  It does not use
author code, author numerical arrays, or values extracted from figure pixels.
"""

from __future__ import annotations

import numpy as np

FOCK_LABELS = ("20", "11", "02")


def mzi_unitary(theta: float) -> np.ndarray:
    """Return the paper's H' R(theta) H' single-photon unitary."""

    coupler = np.asarray([[1.0, 1.0j], [1.0j, 1.0]], dtype=complex) / np.sqrt(2.0)
    phase = np.diag([1.0, np.exp(1.0j * float(theta))])
    return coupler @ phase @ coupler


def two_photon_lift(unitary: np.ndarray) -> np.ndarray:
    """Lift a two-mode single-photon unitary to {|20>, |11>, |02>}.

    Columns are input Fock states and rows are output Fock states.  The square
    roots of two are the normalized bosonic occupation factors.
    """

    unitary = np.asarray(unitary, dtype=complex)
    if unitary.shape != (2, 2):
        raise ValueError("unitary must be 2x2")
    a, b = unitary[0, 0], unitary[0, 1]
    c, d = unitary[1, 0], unitary[1, 1]
    root_two = np.sqrt(2.0)
    return np.asarray(
        [
            [a * a, root_two * a * b, b * b],
            [root_two * a * c, a * d + b * c, root_two * b * d],
            [c * c, root_two * c * d, d * d],
        ],
        dtype=complex,
    )


def noon_state(phi: float, balance: float = 0.5) -> np.ndarray:
    """Return sqrt(b)|20> + exp(2i phi)sqrt(1-b)|02>."""

    if not 0.0 <= balance <= 1.0:
        raise ValueError("balance must lie in [0, 1]")
    return np.asarray(
        [
            np.sqrt(balance),
            0.0,
            np.exp(2.0j * float(phi)) * np.sqrt(1.0 - balance),
        ],
        dtype=complex,
    )


def noon_density(phi: float, purity: float = 1.0) -> np.ndarray:
    """Return the balanced partially coherent state from Supplement Eq. (2)."""

    if not 0.0 <= purity <= 1.0:
        raise ValueError("purity must lie in [0, 1]")
    coherence = 0.5 * purity * np.exp(-2.0j * float(phi))
    density = np.asarray(
        [[0.5, 0.0, coherence], [0.0, 0.0, 0.0], [coherence.conjugate(), 0.0, 0.5]],
        dtype=complex,
    )
    return density


def output_probabilities(
    theta: float,
    phi: float,
    *,
    balance: float = 0.5,
    purity: float = 1.0,
) -> np.ndarray:
    """Return output probabilities in the {|20>, |11>, |02>} order."""

    lifted = two_photon_lift(mzi_unitary(theta))
    if purity == 1.0:
        state = lifted @ noon_state(phi, balance)
        probabilities = np.abs(state) ** 2
    else:
        if balance != 0.5:
            raise ValueError("the paper's partial-purity model assumes balance=0.5")
        density = lifted @ noon_density(phi, purity) @ lifted.conjugate().T
        probabilities = np.real(np.diag(density)).copy()
    probabilities[np.abs(probabilities) < 1e-15] = 0.0
    return probabilities


def probability_grid(
    theta: np.ndarray,
    phi: np.ndarray,
    *,
    balance: float = 0.5,
    purity: float = 1.0,
) -> np.ndarray:
    """Evaluate all three probabilities on a theta-by-phi mesh."""

    theta = np.asarray(theta, dtype=float)
    phi = np.asarray(phi, dtype=float)
    output = np.empty((3, theta.size, phi.size), dtype=float)
    for theta_index, theta_value in enumerate(theta):
        for phi_index, phi_value in enumerate(phi):
            output[:, theta_index, phi_index] = output_probabilities(
                theta_value,
                phi_value,
                balance=balance,
                purity=purity,
            )
    return output


def classical_transfer(theta: np.ndarray) -> np.ndarray:
    """Return P(output|input) for both inputs over the phase scan."""

    theta = np.asarray(theta, dtype=float)
    output = np.empty((2, 2, theta.size), dtype=float)
    for index, phase in enumerate(theta):
        output[:, :, index] = np.abs(mzi_unitary(float(phase))) ** 2
    return output


def hom_visibility(reflectivity: np.ndarray | float) -> np.ndarray:
    """HOM visibility for a wavelength-independent beam splitter."""

    reflectivity = np.asarray(reflectivity, dtype=float)
    if np.any((reflectivity < 0.0) | (reflectivity > 1.0)):
        raise ValueError("reflectivity must lie in [0, 1]")
    distinguishable = reflectivity**2 + (1.0 - reflectivity) ** 2
    indistinguishable = (2.0 * reflectivity - 1.0) ** 2
    return 1.0 - indistinguishable / distinguishable


def spectrum_weighted_hom_visibility(
    reflectivity_signal: np.ndarray,
    reflectivity_idler: np.ndarray,
    weights: np.ndarray,
) -> float:
    """Integrate two-color coincidence probabilities over a pair spectrum."""

    signal = np.asarray(reflectivity_signal, dtype=float)
    idler = np.asarray(reflectivity_idler, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if not (signal.shape == idler.shape == weights.shape):
        raise ValueError("reflectivities and weights must have equal shapes")
    if np.any(weights < 0.0) or not np.any(weights > 0.0):
        raise ValueError("weights must be nonnegative and nonzero")
    if np.any((signal < 0.0) | (signal > 1.0)) or np.any((idler < 0.0) | (idler > 1.0)):
        raise ValueError("reflectivities must lie in [0, 1]")
    transmission_signal = 1.0 - signal
    transmission_idler = 1.0 - idler
    distinguishable = signal * idler + transmission_signal * transmission_idler
    indistinguishable = (
        np.sqrt(signal * idler) - np.sqrt(transmission_signal * transmission_idler)
    ) ** 2
    return float(
        1.0 - np.sum(weights * indistinguishable) / np.sum(weights * distinguishable)
    )
