"""Exact transfer-matrix contraction transcribed from the published equations.

This module deliberately has no file I/O.  It accepts only scalar physical
parameters and creates all scientific arrays from the paper's MPO amplitudes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ScaledVector:
    values: np.ndarray
    log_scale: float


@dataclass(frozen=True)
class SignedLogScalar:
    sign: float
    log_abs: float


def _generic_auxiliary_amplitudes_at(
    lam: complex,
    epsilon: float,
    r: int,
    *,
    c: complex = 1.0,
) -> tuple[complex, complex, complex, float]:
    """Evaluate one row of the generic Eq. (7) representation.

    Keeping the transcription in one function prevents scientific diagnostics
    from using a simplified expression that is not the one used by the MPO.
    The returned ``tau`` is the paper's nonsingular sign prescription.
    """

    if r < 1:
        raise ValueError("r must be positive")
    if c == 0:
        raise ValueError("c must be nonzero")
    sin_lam = np.sin(lam)
    if abs(sin_lam) < 1e-14:
        raise ValueError("singular anisotropy requires a separately derived limit")

    cosine = np.cos(r * lam)
    tau = 1.0 if np.real(cosine) >= 0.0 else -1.0
    a0 = cosine + 1j * epsilon * np.sin(r * lam) / (2.0 * sin_lam)
    denominator = 2.0 * (cosine + tau) * sin_lam
    if abs(denominator) < 1e-14:
        raise ValueError("stable tau prescription produced a singular denominator")

    if r % 2:
        k = (r + 1) // 2
        a_plus = c * np.sin(2 * k * lam) + (
            1j
            * epsilon
            * c
            * np.sin(r * lam)
            * np.sin(2 * k * lam)
            / denominator
        )
        a_minus = -np.sin(r * lam) / c + (
            1j * epsilon * (cosine + tau) / (2.0 * c * sin_lam)
        )
    else:
        k = r // 2
        a_plus = c * np.sin(r * lam) - (
            1j * epsilon * c * (cosine + tau) / (2.0 * sin_lam)
        )
        a_minus = -np.sin((2 * k + 1) * lam) / c - (
            1j
            * epsilon
            * np.sin(r * lam)
            * np.sin((2 * k + 1) * lam)
            / (2.0 * c * (cosine + tau) * sin_lam)
        )
    return complex(a0), complex(a_plus), complex(a_minus), tau


def auxiliary_dimension(size: int, delta: float) -> int:
    """Exact dimension needed by a length-``size`` return path.

    A path beginning and ending at auxiliary state zero cannot exceed
    ``floor(size / 2)``.  At Delta=1/2 the root-of-unity process additionally
    closes after auxiliary state two.
    """

    if size < 1:
        raise ValueError("size must be positive")
    dimension = size // 2 + 1
    if np.isclose(delta, 0.5, atol=1e-14, rtol=0.0):
        dimension = min(dimension, 3)
    return dimension


def auxiliary_amplitudes(
    delta: float, epsilon: float, dimension: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``a0, a_plus, a_minus`` from Eqs. (6)-(7).

    The isotropic point uses the regularized amplitudes printed after Main
    Figure 2.  For other anisotropies, the arbitrary gauge is fixed to ``c=1``
    and the paper's stable sign prescription is used.
    """

    if dimension < 1:
        raise ValueError("dimension must be positive")
    if epsilon < 0.0:
        raise ValueError("epsilon must be nonnegative")

    a0 = np.zeros(dimension, dtype=np.complex128)
    a_plus = np.zeros(dimension, dtype=np.complex128)
    a_minus = np.zeros(dimension, dtype=np.complex128)
    a0[0] = 1.0
    a_plus[0] = 1j * epsilon
    a_minus[0] = 1.0

    if np.isclose(delta, 1.0, atol=1e-14, rtol=0.0):
        for r in range(1, dimension):
            a0[r] = 1.0 + 0.5j * epsilon * r
            if r % 2:
                k = (r + 1) // 2
                a_plus[r] = 2.0 * k + 1j * epsilon * k * (k - 0.5)
                a_minus[r] = 1j * epsilon
            else:
                k = r // 2
                a_plus[r] = 2.0 * k + 1j * epsilon * k * k
                a_minus[r] = 1j * epsilon * (k + 0.5) / k
        return a0, a_plus, a_minus

    lam = np.arccos(complex(delta))
    for r in range(1, dimension):
        a0[r], a_plus[r], a_minus[r], _ = _generic_auxiliary_amplitudes_at(
            lam,
            epsilon,
            r,
        )
    return a0, a_plus, a_minus


def auxiliary_matrices(
    delta: float, epsilon: float, dimension: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the three near-diagonal MPO matrices in Eqs. (6)-(7).

    This is deliberately separate from the reduced transfer process below.
    It permits small-chain checks of the actual Cholesky factor ``S_n`` and
    therefore tests the theorem rather than only its longitudinal-observable
    corollary.
    """

    a0, a_plus, a_minus = auxiliary_amplitudes(delta, epsilon, dimension)
    matrix_0 = np.diag(a0)
    matrix_plus = np.zeros((dimension, dimension), dtype=np.complex128)
    matrix_minus = np.zeros((dimension, dimension), dtype=np.complex128)
    for r in range(dimension - 1):
        matrix_plus[r, r + 1] = a_plus[r]
        matrix_minus[r + 1, r] = a_minus[r]
    return matrix_0, matrix_plus, matrix_minus


def mpo_cholesky_operator(
    delta: float,
    epsilon: float,
    size: int,
    *,
    auxiliary_dimension_override: int | None = None,
) -> np.ndarray:
    """Contract the printed MPO to the finite many-body operator ``S_n``.

    The routine is intended for independent small-chain theorem checks.  It
    contracts physical operator blocks while retaining the auxiliary index;
    no dense Liouvillian information enters the construction.
    """

    if size < 1:
        raise ValueError("size must be positive")
    dimension = (
        auxiliary_dimension(size, delta)
        if auxiliary_dimension_override is None
        else int(auxiliary_dimension_override)
    )
    if dimension < auxiliary_dimension(size, delta):
        raise ValueError("auxiliary override is too small for an exact return path")
    matrix_0, matrix_plus, matrix_minus = auxiliary_matrices(delta, epsilon, dimension)
    identity = np.eye(2, dtype=np.complex128)
    sigma_plus = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    sigma_minus = sigma_plus.T
    physical = (
        (matrix_0, identity),
        (matrix_plus, sigma_plus),
        (matrix_minus, sigma_minus),
    )
    blocks: dict[int, np.ndarray] = {0: np.ones((1, 1), dtype=np.complex128)}
    for _ in range(size):
        next_blocks: dict[int, np.ndarray] = {}
        for left_index, block in blocks.items():
            for auxiliary, local_operator in physical:
                for right_index in np.flatnonzero(auxiliary[left_index]):
                    contribution = auxiliary[left_index, right_index] * np.kron(
                        block, local_operator
                    )
                    if int(right_index) in next_blocks:
                        next_blocks[int(right_index)] += contribution
                    else:
                        next_blocks[int(right_index)] = contribution
        blocks = next_blocks
    return blocks.get(0, np.zeros((2**size, 2**size), dtype=np.complex128))


def mpo_density_operator(delta: float, epsilon: float, size: int) -> np.ndarray:
    """Return the normalized finite-chain density matrix ``S_n S_n^dagger``."""

    cholesky = mpo_cholesky_operator(delta, epsilon, size)
    density = cholesky @ cholesky.conj().T
    return density / np.trace(density)


def hopping_vertex(delta: float, epsilon: float, size: int) -> np.ndarray:
    """Build the one-sided hopping vertex ``W`` printed in Eq. (17)."""

    dimension = auxiliary_dimension(size, delta)
    a0, a_plus, a_minus = auxiliary_amplitudes(delta, epsilon, dimension)
    vertex = np.zeros((dimension, dimension), dtype=np.complex128)
    for r in range(dimension - 1):
        vertex[r, r + 1] += a0[r] * np.conj(a0[r + 1]) * abs(a_plus[r]) ** 2 / 4.0
        vertex[r + 1, r] += a0[r] * np.conj(a0[r + 1]) * abs(a_minus[r]) ** 2 / 4.0
        vertex[r, r] += a0[r] ** 2 * np.conj(a_plus[r]) * np.conj(a_minus[r]) / 4.0
        vertex[r + 1, r + 1] += a_plus[r] * a_minus[r] * np.conj(a0[r + 1]) ** 2 / 4.0
    return vertex


def transfer_contraction_operation_count(size: int) -> int:
    """Count band multiplications for one length-``size`` local observable.

    The count mirrors ``_contract_sequence`` and makes the paper's O(n^2)
    arithmetic statement testable without relying on noisy wall-clock timing.
    """

    if size < 1:
        raise ValueError("size must be positive")
    dimension = size // 2 + 1
    operations = 0
    for completed in range(1, size + 1):
        reachable_height = min(completed, size - completed, dimension - 1)
        active_stop = min(reachable_height + 2, dimension)
        operations += active_stop + 2 * max(0, active_stop - 1)
    return operations


def root_of_unity_closure_diagnostic(
    m: int, numerator: int = 1, *, epsilon: float = 1.0
) -> dict[str, float | str]:
    """Audit the printed root-of-unity cutoff against the full Eq. (7).

    The prose claims a cutoff at ``r=m`` and hence an ``m+1`` dimensional
    auxiliary space.  Direct nonsingular substitution instead leaves that
    named component nonzero and cuts the opposite hopping at ``r=m-1``.  This
    matches the paper's own ``m=3`` example, which uses a three-state space.
    """

    if m < 2 or numerator < 1 or numerator >= m:
        raise ValueError("require m >= 2 and 1 <= numerator < m")
    if epsilon < 0.0:
        raise ValueError("epsilon must be nonnegative")
    lam = np.pi * numerator / m
    _, paper_plus, paper_minus, paper_tau = _generic_auxiliary_amplitudes_at(
        lam,
        epsilon,
        m,
    )
    actual_index = m - 1
    _, actual_plus, actual_minus, actual_tau = _generic_auxiliary_amplitudes_at(
        lam,
        epsilon,
        actual_index,
    )
    paper_component = paper_plus if m % 2 else paper_minus
    actual_component = actual_minus if m % 2 else actual_plus
    return {
        "m": float(m),
        "l": float(numerator),
        "paper_claimed_cutoff_index": float(m),
        "paper_named_component": "a_plus_m" if m % 2 else "a_minus_m",
        "paper_named_component_magnitude": float(abs(paper_component)),
        "stable_tau_at_paper_index": paper_tau,
        "actual_cutoff_index": float(actual_index),
        "actual_cutoff_component": (
            "a_minus_m_minus_1" if m % 2 else "a_plus_m_minus_1"
        ),
        "actual_cutoff_residual": float(abs(actual_component)),
        "stable_tau_at_actual_index": actual_tau,
        "paper_claimed_auxiliary_dimension": float(m + 1),
        "actual_auxiliary_dimension": float(m),
    }


def transfer_operators(
    delta: float, epsilon: float, size: int
) -> tuple[np.ndarray, np.ndarray]:
    """Build the finite exact transfer matrix ``T`` and vertex ``V``."""

    dimension = auxiliary_dimension(size, delta)
    a0, a_plus, a_minus = auxiliary_amplitudes(delta, epsilon, dimension)
    transfer = np.diag(np.abs(a0) ** 2).astype(np.float64)
    vertex = np.zeros((dimension, dimension), dtype=np.float64)
    for r in range(dimension - 1):
        hop_plus = float(abs(a_plus[r]) ** 2 / 2.0)
        hop_minus = float(abs(a_minus[r]) ** 2 / 2.0)
        transfer[r, r + 1] = hop_plus
        transfer[r + 1, r] = hop_minus
        vertex[r, r + 1] = hop_plus
        vertex[r + 1, r] = -hop_minus
    return transfer, vertex


def _normalized(values: np.ndarray, log_scale: float) -> ScaledVector:
    scale = float(np.max(np.abs(values)))
    if not np.isfinite(scale) or scale == 0.0:
        raise FloatingPointError(
            "transfer contraction produced a zero or nonfinite scale"
        )
    return ScaledVector(values / scale, log_scale + float(np.log(scale)))


def scaled_power_vector(
    transfer: np.ndarray, exponent: int, *, transpose: bool = False
) -> ScaledVector:
    """Evaluate ``T**exponent |0>`` with stepwise rescaling."""

    if exponent < 0:
        raise ValueError("exponent must be nonnegative")
    values = np.zeros(transfer.shape[0], dtype=np.float64)
    values[0] = 1.0
    state = ScaledVector(values, 0.0)
    operator = transfer.T if transpose else transfer
    for _ in range(exponent):
        state = _normalized(operator @ state.values, state.log_scale)
    return state


def _contract_sequence(operators: list[np.ndarray]) -> SignedLogScalar:
    """Contract ``<0| O_1 ... O_n |0>`` without unreachable states.

    A state at auxiliary height ``r`` after ``k`` operators can contribute to
    the final return only when ``r <= min(k, n-k)``.  Removing the other states
    is exact, and is essential in the easy-axis regime: exponentially large
    paths that cannot return would otherwise dominate a generic vector norm
    and erase the physically relevant component through floating underflow.
    """

    if not operators:
        return SignedLogScalar(1.0, 0.0)
    dimension = operators[0].shape[0]
    if any(operator.shape != (dimension, dimension) for operator in operators):
        raise ValueError("all operators must have a shared square dimension")
    values = np.zeros(dimension, dtype=np.float64)
    values[0] = 1.0
    log_scale = 0.0
    total = len(operators)
    bands: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for operator in operators:
        bands.setdefault(
            id(operator),
            (np.diag(operator), np.diag(operator, 1), np.diag(operator, -1)),
        )
    for completed, operator in enumerate(reversed(operators), start=1):
        reachable_height = min(completed, total - completed, dimension - 1)
        # T and V are tridiagonal.  Applying only their three populated bands
        # keeps the paper's O(n^2) arithmetic contract visible at n=400 rather
        # than paying for dense zeros.
        updated = np.zeros_like(values)
        active_stop = min(reachable_height + 2, dimension)
        diagonal, upper, lower = bands[id(operator)]
        updated[:active_stop] = diagonal[:active_stop] * values[:active_stop]
        if active_stop > 1:
            updated[: active_stop - 1] += (
                upper[: active_stop - 1] * values[1:active_stop]
            )
            updated[1:active_stop] += (
                lower[: active_stop - 1] * values[: active_stop - 1]
            )
        values = updated
        values[reachable_height + 1 :] = 0.0
        scale = float(np.max(np.abs(values[: reachable_height + 1])))
        if scale == 0.0:
            return SignedLogScalar(0.0, float("-inf"))
        if not np.isfinite(scale):
            raise FloatingPointError(
                "operator contraction vanished or became nonfinite"
            )
        values /= scale
        log_scale += float(np.log(scale))
    scalar = float(values[0])
    if scalar == 0.0 or not np.isfinite(scalar):
        raise FloatingPointError("final contraction vanished or became nonfinite")
    return SignedLogScalar(
        float(np.sign(scalar)), float(np.log(abs(scalar)) + log_scale)
    )


def _ratio(numerator: SignedLogScalar, denominator: SignedLogScalar) -> float:
    if numerator.sign == 0.0:
        return 0.0
    if denominator.sign == 0.0:
        raise ZeroDivisionError("zero denominator contraction")
    return float(
        numerator.sign
        * denominator.sign
        * np.exp(numerator.log_abs - denominator.log_abs)
    )


def spin_profile(delta: float, epsilon: float, size: int) -> np.ndarray:
    """Return all ``<sigma_j^z>`` using Eq. (15)."""

    transfer, vertex = transfer_operators(delta, epsilon, size)
    partition = _contract_sequence([transfer] * size)
    if partition.sign <= 0.0:
        raise FloatingPointError("partition contraction must be positive")
    profile = np.empty(size, dtype=np.float64)
    for j in range(1, size + 1):
        numerator = _contract_sequence(
            [transfer] * (j - 1) + [vertex] + [transfer] * (size - j)
        )
        profile[j - 1] = _ratio(numerator, partition)
    return profile


def spin_current(delta: float, epsilon: float, size: int) -> float:
    """Return the conserved current from the exact norm ratio."""

    if size < 2:
        raise ValueError("current requires at least two sites")
    transfer, _ = transfer_operators(delta, epsilon, size)
    partition_n = _contract_sequence([transfer] * size)
    partition_previous = _contract_sequence([transfer] * (size - 1))
    return float(0.5 * epsilon * _ratio(partition_previous, partition_n))


def connected_correlation(
    delta: float, epsilon: float, size: int, site_j: int, site_k: int
) -> float:
    """Return the connected ``sigma^z`` correlation for ``site_j < site_k``."""

    if not 1 <= site_j < site_k <= size:
        raise ValueError("sites must satisfy 1 <= site_j < site_k <= size")
    transfer, vertex = transfer_operators(delta, epsilon, size)
    partition = _contract_sequence([transfer] * size)
    numerator = _contract_sequence(
        [transfer] * (site_j - 1)
        + [vertex]
        + [transfer] * (site_k - site_j - 1)
        + [vertex]
        + [transfer] * (size - site_k)
    )
    two_point = _ratio(numerator, partition)
    profile = spin_profile(delta, epsilon, size)
    return float(two_point - profile[site_j - 1] * profile[site_k - 1])


def correlation_kernel(x: float, y: float) -> float:
    """Printed leading isotropic kernel ``f(min(x,y), max(x,y))``."""

    x0, y0 = sorted((float(x), float(y)))
    return float(
        2.0 * np.pi * x0 * (y0 - 1.0) * np.sin(np.pi * x0) * np.sin(np.pi * y0)
        + np.cos(np.pi * x0)
        * (
            (1.0 - 2.0 * y0) * np.sin(np.pi * y0)
            + np.pi * (y0 - 1.0) * y0 * np.cos(np.pi * y0)
        )
    )


def correlation_asymptote(x: float, y: float, size: int) -> float:
    return float(np.pi * correlation_kernel(x, y) / (4.0 * size))


def easy_plane_current_limit(epsilon: np.ndarray | float) -> np.ndarray | float:
    """Closed thermodynamic current for Delta=1/2."""

    value = np.asarray(epsilon, dtype=np.float64)
    result = (
        value
        * (np.sqrt(81.0 + 74.0 * value**2 + 9.0 * value**4) - 7.0 - 3.0 * value**2)
        / (4.0 * (1.0 + value**2))
    )
    if np.ndim(value) == 0:
        return float(result)
    return result


def easy_plane_convergence_diagnostic(
    epsilon: float, sizes: np.ndarray | list[int]
) -> dict[str, object]:
    """Test the printed ``Delta=1/2`` thermodynamic convergence claim.

    The paper states that observables converge exponentially at a rate fixed by
    the ratio of the two leading eigenvalues of its printed three-state
    transfer matrix, and that the bulk magnetization becomes flat.  This
    diagnostic compares that spectral prediction with independently contracted
    finite-chain currents and also evaluates the Perron-state magnetization.
    """

    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    size_values = np.asarray(sizes, dtype=np.int64)
    if size_values.ndim != 1 or len(size_values) < 3:
        raise ValueError("at least three convergence sizes are required")
    if np.any(size_values < 4) or np.any(np.diff(size_values) <= 0):
        raise ValueError("sizes must be strictly increasing and at least four")

    transfer, vertex = transfer_operators(0.5, epsilon, int(size_values[-1]))
    eigenvalues, right_vectors = np.linalg.eig(transfer)
    order = np.argsort(-np.abs(eigenvalues))
    leading_index, subleading_index = int(order[0]), int(order[1])
    leading = eigenvalues[leading_index]
    subleading = eigenvalues[subleading_index]
    spectral_ratio = float(abs(subleading / leading))

    left_values, left_vectors = np.linalg.eig(transfer.T)
    left_index = int(np.argmin(np.abs(left_values - leading)))
    right = right_vectors[:, leading_index]
    left = left_vectors[:, left_index]
    thermodynamic_magnetization = float(
        np.real_if_close((left @ vertex @ right) / (leading * (left @ right)))
    )

    limit = float(easy_plane_current_limit(epsilon))
    current_errors = np.asarray(
        [abs(spin_current(0.5, epsilon, int(size)) - limit) for size in size_values],
        dtype=np.float64,
    )
    if np.any(current_errors <= 0.0):
        raise FloatingPointError("convergence fit reached floating-point zero")
    fitted_log_rate, _ = np.polyfit(size_values, np.log(current_errors), 1)
    fitted_ratio = float(np.exp(fitted_log_rate))

    bulk_profile_maxima = []
    for size in size_values:
        profile = spin_profile(0.5, epsilon, int(size))
        start = int(size) // 3
        stop = int(size) - start
        bulk_profile_maxima.append(float(np.max(np.abs(profile[start:stop]))))

    return {
        "epsilon": float(epsilon),
        "sizes": [int(value) for value in size_values],
        "leading_eigenvalue": float(np.real_if_close(leading)),
        "subleading_eigenvalue": float(np.real_if_close(subleading)),
        "spectral_ratio": spectral_ratio,
        "fitted_current_error_ratio_per_site": fitted_ratio,
        "spectral_ratio_relative_error": float(
            abs(fitted_ratio / spectral_ratio - 1.0)
        ),
        "thermodynamic_magnetization": thermodynamic_magnetization,
        "current_absolute_errors": current_errors.tolist(),
        "bulk_profile_maxima": bulk_profile_maxima,
        "bulk_profile_monotone": bool(
            np.all(np.diff(np.asarray(bulk_profile_maxima)) < 0.0)
        ),
    }


def infinite_transfer_rank_certificate(
    delta: float, epsilon: float, max_rank: int
) -> dict[str, object]:
    """Return a finite certificate for the transfer operator's infinite rank.

    For every requested ``N``, rows ``0..N-1`` and columns ``1..N`` form a
    lower-triangular minor whose diagonal is ``|a_r^+|^2/2``.  At ``Delta=1``
    the printed regularized amplitudes have nonzero real part ``2k``; for
    ``Delta>1`` their imaginary part is a nonzero hyperbolic sine.  Hence such
    a nonsingular minor exists for arbitrary ``N``, proving unbounded rank
    rather than merely observing a large numerical matrix.
    """

    if delta < 1.0:
        raise ValueError("the certificate applies only to Delta >= 1")
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    if max_rank < 2:
        raise ValueError("max_rank must be at least two")

    _, a_plus, _ = auxiliary_amplitudes(delta, epsilon, max_rank + 1)
    upper_hops = 0.5 * np.abs(a_plus[:max_rank]) ** 2

    analytic_witness = np.empty(max_rank, dtype=np.float64)
    analytic_witness[0] = epsilon
    if np.isclose(delta, 1.0, atol=1e-14, rtol=0.0):
        for r in range(1, max_rank):
            analytic_witness[r] = 2.0 * ((r + 1) // 2 if r % 2 else r // 2)
        implemented_witness = np.empty(max_rank, dtype=np.float64)
        implemented_witness[0] = abs(np.imag(a_plus[0]))
        implemented_witness[1:] = np.abs(np.real(a_plus[1:max_rank]))
        witness_kind = "regularized_real_part"
    else:
        eta = float(np.arccosh(delta))
        for r in range(1, max_rank):
            even_height = r + 1 if r % 2 else r
            analytic_witness[r] = float(np.sinh(even_height * eta))
        implemented_witness = np.abs(np.imag(a_plus[:max_rank]))
        witness_kind = "hyperbolic_imaginary_part"

    transfer_dimension = 2 * max_rank
    transfer, _ = transfer_operators(delta, epsilon, transfer_dimension)
    shifted_minor = transfer[:max_rank, 1 : max_rank + 1]
    upper_triangle_residual = float(np.max(np.abs(np.triu(shifted_minor, 1))))
    diagonal_error = float(np.max(np.abs(np.diag(shifted_minor) - upper_hops)))
    witness_error = float(np.max(np.abs(implemented_witness - analytic_witness)))
    witness_scale = max(1.0, float(np.max(np.abs(analytic_witness))))
    diagonal_scale = max(1.0, float(np.max(np.abs(upper_hops))))

    return {
        "delta": float(delta),
        "epsilon": float(epsilon),
        "certified_rank_lower_bound": int(max_rank),
        "witness_kind": witness_kind,
        "minimum_nonzero_witness": float(np.min(analytic_witness)),
        "analytic_witness_maximum_error": witness_error,
        "analytic_witness_maximum_relative_error": witness_error / witness_scale,
        "minimum_shifted_minor_diagonal": float(np.min(upper_hops)),
        "shifted_minor_upper_triangle_residual": upper_triangle_residual,
        "shifted_minor_diagonal_error": diagonal_error,
        "shifted_minor_diagonal_relative_error": diagonal_error / diagonal_scale,
        "shifted_minor_log_abs_determinant": float(np.sum(np.log(upper_hops))),
        "all_diagonal_entries_nonzero": bool(np.all(upper_hops > 0.0)),
    }


def isotropic_profile_asymptote(size: int) -> np.ndarray:
    x = np.arange(size, dtype=np.float64) / (size - 1)
    return np.cos(np.pi * x)


def isotropic_current_asymptote(epsilon: float, size: np.ndarray | int) -> np.ndarray:
    values = np.asarray(size, dtype=np.float64)
    return np.pi**2 / (epsilon * values**2)


def easy_axis_decay_fit(sizes: np.ndarray, currents: np.ndarray) -> dict[str, float]:
    """Fit the source-independent slope of log current versus size."""

    x = np.asarray(sizes, dtype=np.float64)
    y = np.asarray(currents, dtype=np.float64)
    if np.any(y <= 0.0):
        raise ValueError("currents must be positive")
    slope, intercept = np.polyfit(x, np.log(y), 1)
    prediction = slope * x + intercept
    residual = np.log(y) - prediction
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((np.log(y) - np.mean(np.log(y))) ** 2))
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(1.0 - ss_res / ss_tot),
    }
