"""Paper-derived squeezing feature map and kernel.

This module contains no source-image, author-code, or author-array access.  The
only scientific inputs are equations (7)--(8) and the squeezed-vacuum expansion
printed in the paper.
"""

from __future__ import annotations

import numpy as np
from scipy.special import gammaln


def single_mode_overlap(phi: np.ndarray, phi_prime: np.ndarray, c: float) -> np.ndarray:
    """Return <(c,phi)|(c,phi')> from the paper's Eq. (8)."""

    phase_difference = np.asarray(phi_prime) - np.asarray(phi)
    return (1.0 / np.cosh(c)) / np.sqrt(
        1.0 - np.exp(1.0j * phase_difference) * np.tanh(c) ** 2
    )


def squeezing_kernel(first: np.ndarray, second: np.ndarray, c: float) -> np.ndarray:
    """Real PSD kernel |<phi(x)|phi(x')>|^2 for multidimensional inputs.

    The paper explicitly states that the absolute square must be taken when the
    feature-state inner product is complex.  This is the kernel accepted by a
    real-valued scikit-learn SVC.
    """

    first = np.atleast_2d(np.asarray(first, dtype=float))
    second = np.atleast_2d(np.asarray(second, dtype=float))
    differences = second[None, :, :] - first[:, None, :]
    denominator = np.abs(
        1.0 - np.exp(1.0j * differences) * np.tanh(c) ** 2
    )
    single_mode_fidelities = (1.0 / np.cosh(c) ** 2) / denominator
    return np.prod(single_mode_fidelities, axis=-1).real


def truncated_squeezed_state(
    phases: np.ndarray,
    c: float,
    even_terms: int,
    *,
    normalize: bool = False,
) -> np.ndarray:
    """Coefficients of |(c,phi)> on |0>,|2>,...,|2(even_terms-1)>.

    The returned last axis indexes the even Fock states only.  This compact
    representation is sufficient for the explicit real-subspace perceptron.
    """

    phases = np.asarray(phases, dtype=float)
    n = np.arange(even_terms, dtype=float)
    log_prefactor = (
        -0.5 * np.log(np.cosh(c))
        + 0.5 * gammaln(2.0 * n + 1.0)
        - n * np.log(2.0)
        - gammaln(n + 1.0)
        + n * np.log(np.tanh(c))
    )
    radial = np.exp(log_prefactor) * (-1.0) ** n
    state = radial * np.exp(1.0j * phases[..., None] * n)
    if normalize:
        norm = np.linalg.norm(state, axis=-1, keepdims=True)
        state = state / np.maximum(norm, np.finfo(float).tiny)
    return state


def real_fock_features(inputs: np.ndarray, c: float, even_terms: int) -> np.ndarray:
    """Map two-dimensional inputs to the real part of two-mode Fock space."""

    inputs = np.atleast_2d(np.asarray(inputs, dtype=float))
    if inputs.shape[1] != 2:
        raise ValueError("the reproduced classifiers use exactly two input modes")
    first = truncated_squeezed_state(inputs[:, 0], c, even_terms, normalize=True)
    second = truncated_squeezed_state(inputs[:, 1], c, even_terms, normalize=True)
    joint = np.einsum("bi,bj->bij", first, second).reshape(len(inputs), -1)
    return joint.real
