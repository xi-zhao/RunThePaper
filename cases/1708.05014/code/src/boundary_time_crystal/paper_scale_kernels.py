"""Paper-scale-only kernels that do not mutate the attested feature-run model."""

from __future__ import annotations

import numpy as np
from scipy.sparse.linalg import expm_multiply
from scipy.special import logsumexp

from .model import (
    liouvillian,
    spin_operators,
    spin_x_coherent_density,
    vectorize_density,
)


def steady_state_shifted_jump(
    number_spins: int,
    omega_0: float,
    kappa: float = 1.0,
) -> tuple[np.ndarray, dict[str, float | str]]:
    r"""Construct the exact finite-N steady state without a Liouville-space LU.

    Completing the dissipator gives

    ``L rho = (kappa/S) D[S_- + i omega_0 S/kappa] rho``.

    For nonzero ``omega_0`` the shifted jump ``J`` is invertible, and
    ``rho_ss`` is proportional to ``(J^\dagger J)^-1``.  The inverse of the
    lower-bidiagonal ``J`` is accumulated column by column in logarithmic
    scale.  This avoids overflow in the strong-dissipation regime and reduces
    the paper ``N_b=600`` problem from a sparse factorization on ``(N+1)^2``
    unknowns to dense linear algebra on ``N+1`` states.

    The returned residual is still evaluated against the independently
    assembled Liouvillian from :func:`liouvillian`; the algebraic construction
    is therefore not accepted on identity alone.
    """

    if number_spins < 1:
        raise ValueError("number_spins must be positive")
    if kappa <= 0:
        raise ValueError("kappa must be positive")

    dimension = number_spins + 1
    if omega_0 == 0.0:
        density = np.zeros((dimension, dimension), dtype=np.complex128)
        density[-1, -1] = 1.0
        residual = float(
            np.linalg.norm(
                liouvillian(number_spins, omega_0, kappa) @ vectorize_density(density)
            )
        )
        return density, {
            "method": "shifted_jump_zero_drive_limit",
            "liouvillian_residual": residual,
            "trace_error": 0.0,
            "hermiticity_error": 0.0,
            "minimum_gram_weight": 1.0,
        }

    spin = number_spins / 2.0
    shift = abs(omega_0 * spin / kappa)
    shift_phase = np.sign(omega_0)
    logarithm_shift = np.log(shift)
    lowering = np.asarray(spin_operators(number_spins).sm.diagonal(-1).real)

    normalized_columns = np.zeros((dimension, dimension), dtype=np.complex128)
    logarithmic_weights = np.empty(dimension, dtype=np.float64)
    for column in range(dimension):
        length = dimension - column
        logarithmic_magnitude = np.empty(length, dtype=np.float64)
        phase = np.empty(length, dtype=np.float64)
        logarithmic_magnitude[0] = -logarithm_shift
        phase[0] = -shift_phase * np.pi / 2.0
        if length > 1:
            logarithmic_magnitude[1:] = logarithmic_magnitude[0] + np.cumsum(
                np.log(lowering[column:]) - logarithm_shift
            )
            phase[1:] = phase[0] + shift_phase * np.arange(1, length) * np.pi / 2.0

        column_scale = float(np.max(logarithmic_magnitude))
        scaled = np.exp(logarithmic_magnitude - column_scale) * np.exp(1j * phase)
        scaled_norm = float(np.linalg.norm(scaled))
        normalized_columns[column:, column] = scaled / scaled_norm
        logarithmic_weights[column] = 2.0 * (column_scale + np.log(scaled_norm))

    gram_weights = np.exp(logarithmic_weights - logsumexp(logarithmic_weights))
    gram_factor = normalized_columns * np.sqrt(gram_weights)[None, :]
    density = gram_factor @ gram_factor.conj().T
    density /= np.trace(density)

    residual = float(
        np.linalg.norm(
            liouvillian(number_spins, omega_0, kappa) @ vectorize_density(density)
        )
    )
    return density, {
        "method": "shifted_jump_gram",
        "liouvillian_residual": residual,
        "trace_error": float(abs(np.trace(density) - 1.0)),
        "hermiticity_error": float(np.linalg.norm(density - density.conj().T)),
        "minimum_gram_weight": float(np.min(gram_weights)),
    }


def magnetization_dynamics_chunk(
    number_spins: int,
    omega_0: float,
    elapsed_times: np.ndarray,
    kappa: float = 1.0,
    *,
    initial_vector: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Propagate one resumable time block and return ``<Sz>/N``.

    ``elapsed_times`` is local to the block and must start at zero.  Passing
    the returned final vector into the next block gives the same numerical
    object as a monolithic exponential action while retaining only one density
    vector at a checkpoint boundary.
    """

    elapsed_times = np.asarray(elapsed_times, dtype=np.float64)
    if (
        elapsed_times.ndim != 1
        or elapsed_times.size < 2
        or elapsed_times[0] != 0.0
        or np.any(np.diff(elapsed_times) <= 0.0)
    ):
        raise ValueError(
            "elapsed_times must be strictly increasing, one-dimensional, and start at zero"
        )
    if initial_vector is None:
        initial_vector = vectorize_density(spin_x_coherent_density(number_spins))
    initial_vector = np.asarray(initial_vector, dtype=np.complex128)
    expected_size = (number_spins + 1) ** 2
    if initial_vector.shape != (expected_size,):
        raise ValueError(f"initial_vector must have shape ({expected_size},)")

    vectors = expm_multiply(
        liouvillian(number_spins, omega_0, kappa),
        initial_vector,
        start=0.0,
        stop=float(elapsed_times[-1]),
        num=int(elapsed_times.size),
        endpoint=True,
    )
    operators = spin_operators(number_spins)
    sz_vector = operators.sz.toarray().T.reshape(-1, order="F")
    trace_vector = np.eye(number_spins + 1, dtype=np.complex128).reshape(-1, order="F")
    raw_magnetization = vectors @ sz_vector / number_spins
    traces = vectors @ trace_vector
    return (
        np.real(raw_magnetization),
        np.asarray(vectors[-1], dtype=np.complex128),
        {
            "maximum_trace_error": float(np.max(np.abs(traces - 1.0))),
            "maximum_imaginary_magnetization": float(
                np.max(np.abs(np.imag(raw_magnetization)))
            ),
        },
    )
