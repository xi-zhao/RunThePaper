"""Clean-room numerical realization of the printed distillation equations.

The closed forms generate the paper curves.  Two independent constructions
serve as falsification routes: an explicit five-qubit stabilizer projector and
an enumeration of the punctured Reed-Muller spaces used by the 15-qubit code.
No original figure coordinates or author numerical arrays are inputs.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]
BitArray = NDArray[np.uint8]

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def _return_scalar_if_scalar(
    source: ArrayLike, value: FloatArray
) -> float | FloatArray:
    return float(value) if np.ndim(source) == 0 else value


def t_type_success(epsilon: ArrayLike) -> float | FloatArray:
    """Eq. (22): probability to observe the trivial five-qubit syndrome."""

    e = np.asarray(epsilon, dtype=float)
    q = 1.0 - e
    value = (e**5 + 5.0 * e**2 * q**3 + 5.0 * e**3 * q**2 + q**5) / 6.0
    return _return_scalar_if_scalar(epsilon, value)


def t_type_output_error(epsilon: ArrayLike) -> float | FloatArray:
    """Eq. (23), evaluated in a cancellation-free epsilon polynomial form."""

    e = np.asarray(epsilon, dtype=float)
    q = 1.0 - e
    numerator = e**5 + 5.0 * e**2 * q**3
    denominator = e**5 + 5.0 * e**2 * q**3 + 5.0 * e**3 * q**2 + q**5
    value = numerator / denominator
    return _return_scalar_if_scalar(epsilon, value)


def _kron_all(operators: list[NDArray[np.complex128]]) -> NDArray[np.complex128]:
    result = np.array([[1.0 + 0.0j]])
    for operator in operators:
        result = np.kron(result, operator)
    return result


def five_qubit_projector() -> NDArray[np.complex128]:
    """Eq. (11): rank-two projector of the printed five-qubit code."""

    stabilizers = [
        _kron_all([X, Z, Z, X, I2]),
        _kron_all([I2, X, Z, Z, X]),
        _kron_all([X, I2, X, Z, Z]),
        _kron_all([Z, X, I2, X, Z]),
    ]
    projector = np.eye(32, dtype=complex)
    for stabilizer in stabilizers:
        projector = projector @ (np.eye(32, dtype=complex) + stabilizer) / 2.0
    return projector


def _t_basis() -> tuple[NDArray[np.complex128], NDArray[np.complex128]]:
    rho_t0 = (I2 + (X + Y + Z) / math.sqrt(3.0)) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(rho_t0)
    t1 = eigenvectors[:, int(np.argmin(eigenvalues))]
    t0 = eigenvectors[:, int(np.argmax(eigenvalues))]
    return t0, t1


def _tensor_state(states: list[NDArray[np.complex128]]) -> NDArray[np.complex128]:
    result = np.array([1.0 + 0.0j])
    for state in states:
        result = np.kron(result, state)
    return result


def t_type_projection_table() -> dict[str, FloatArray]:
    """Aggregate accepted, decoded-error and decoded-good norms by Hamming weight."""

    projector = five_qubit_projector()
    t0, t1 = _t_basis()
    state_00000 = _tensor_state([t0] * 5)
    state_11111 = _tensor_state([t1] * 5)
    logical_t1 = math.sqrt(6.0) * projector @ state_00000
    logical_t0 = math.sqrt(6.0) * projector @ state_11111
    logical_t0 /= np.linalg.norm(logical_t0)
    logical_t1 /= np.linalg.norm(logical_t1)

    accepted = np.zeros(6, dtype=float)
    decoded_error = np.zeros(6, dtype=float)
    decoded_good = np.zeros(6, dtype=float)
    for bits in itertools.product((0, 1), repeat=5):
        state = _tensor_state([t1 if bit else t0 for bit in bits])
        projected = projector @ state
        weight = sum(bits)
        accepted[weight] += float(np.vdot(projected, projected).real)
        decoded_error[weight] += float(abs(np.vdot(logical_t0, projected)) ** 2)
        decoded_good[weight] += float(abs(np.vdot(logical_t1, projected)) ** 2)
    return {
        "accepted": accepted,
        "decoded_error": decoded_error,
        "decoded_good": decoded_good,
    }


def t_type_projector_enumeration(
    epsilon: ArrayLike,
) -> tuple[float | FloatArray, float | FloatArray]:
    """Evaluate success and output error from the 32-state projector route."""

    table = t_type_projection_table()
    e = np.asarray(epsilon, dtype=float)
    success = np.zeros_like(e, dtype=float)
    error_mass = np.zeros_like(e, dtype=float)
    for weight in range(6):
        probability_per_string = e**weight * (1.0 - e) ** (5 - weight)
        success += table["accepted"][weight] * probability_per_string
        error_mass += table["decoded_error"][weight] * probability_per_string
    output_error = error_mass / success
    if np.ndim(epsilon) == 0:
        return float(success), float(output_error)
    return success, output_error


def _gf2_span(generators: BitArray) -> BitArray:
    words = []
    for coefficients in itertools.product((0, 1), repeat=len(generators)):
        word = np.zeros(generators.shape[1], dtype=np.uint8)
        for coefficient, generator in zip(coefficients, generators, strict=True):
            if coefficient:
                word ^= generator
        words.append(word)
    return np.unique(np.asarray(words, dtype=np.uint8), axis=0)


def reed_muller_spaces() -> tuple[BitArray, BitArray]:
    """Construct the paper's punctured L1 and L2 spaces from truth tables."""

    points = np.asarray(list(itertools.product((0, 1), repeat=4))[1:], dtype=np.uint8)
    linear = points.T.copy()
    quadratic = np.asarray(
        [
            points[:, left] * points[:, right]
            for left in range(4)
            for right in range(left + 1, 4)
        ],
        dtype=np.uint8,
    )
    l1 = _gf2_span(linear)
    l2 = _gf2_span(np.vstack([linear, quadratic]))
    return l1, l2


def h_type_weight_tables() -> dict[str, NDArray[np.int64]]:
    """Return exact weight histograms for L1, L2 and L1-perp."""

    l1, l2 = reed_muller_spaces()
    complement = l2 ^ np.ones(15, dtype=np.uint8)

    def histogram(words: BitArray) -> NDArray[np.int64]:
        return np.bincount(words.sum(axis=1).astype(int), minlength=16)

    return {
        "l1": histogram(l1),
        "l2": histogram(l2),
        "l1_perp": histogram(np.vstack([l2, complement])),
    }


def h_type_success(epsilon: ArrayLike) -> float | FloatArray:
    """Eq. (35): probability of the accepted 15-qubit syndrome."""

    e = np.asarray(epsilon, dtype=np.longdouble)
    q = 1.0 - 2.0 * e
    value = (1.0 + 15.0 * q**8) / 16.0
    result = np.asarray(value, dtype=float)
    return _return_scalar_if_scalar(epsilon, result)


def h_type_output_error(epsilon: ArrayLike) -> float | FloatArray:
    """Eq. (36), evaluated in extended precision to suppress cancellation."""

    e = np.asarray(epsilon, dtype=np.longdouble)
    q = 1.0 - 2.0 * e
    numerator = 1.0 - 15.0 * q**7 + 15.0 * q**8 - q**15
    denominator = 2.0 * (1.0 + 15.0 * q**8)
    value = np.clip(numerator / denominator, 0.0, 0.5)
    result = np.asarray(value, dtype=float)
    return _return_scalar_if_scalar(epsilon, result)


def h_type_enumeration(
    epsilon: ArrayLike,
) -> tuple[float | FloatArray, float | FloatArray]:
    """Evaluate Eq. (33) directly from independently enumerated codeword weights."""

    tables = h_type_weight_tables()
    e = np.asarray(epsilon, dtype=float)
    success = np.zeros_like(e, dtype=float)
    error_mass = np.zeros_like(e, dtype=float)
    for weight in range(16):
        term = e ** (15 - weight) * (1.0 - e) ** weight
        success += tables["l1_perp"][weight] * term
        error_mass += tables["l2"][weight] * term
    output_error = error_mass / success
    if np.ndim(epsilon) == 0:
        return float(success), float(output_error)
    return success, output_error


def _interior_fixed_point(
    function: Callable[[float], float], lower: float, upper: float
) -> float:
    def residual(value: float) -> float:
        return function(value) - value

    low, high = lower, upper
    f_low, f_high = residual(low), residual(high)
    if f_low * f_high >= 0:
        raise ValueError("Fixed-point bracket does not change sign")
    for _ in range(100):
        midpoint = (low + high) / 2.0
        f_mid = residual(midpoint)
        if abs(f_mid) < 1e-15 or high - low < 1e-15:
            return midpoint
        if f_low * f_mid <= 0:
            high, f_high = midpoint, f_mid
        else:
            low, f_low = midpoint, f_mid
    return (low + high) / 2.0


def threshold_summary() -> dict[str, float]:
    t_error = 0.5 * (1.0 - math.sqrt(3.0 / 7.0))
    h_error = _interior_fixed_point(
        lambda value: float(h_type_output_error(value)), 0.05, 0.3
    )
    return {
        "t_error_threshold": t_error,
        "t_fidelity_threshold": math.sqrt(1.0 - t_error),
        "t_polarization_threshold": 1.0 - 2.0 * t_error,
        "h_error_threshold": h_error,
        "h_fidelity_threshold": math.sqrt(1.0 - h_error),
        "h_polarization_threshold": 1.0 - 2.0 * h_error,
        "t_stabilizer_fidelity_bound": math.sqrt(0.5 * (1.0 + math.sqrt(1.0 / 3.0))),
        "h_stabilizer_fidelity_bound": math.sqrt(0.5 * (1.0 + math.sqrt(1.0 / 2.0))),
    }


def resource_summary() -> dict[str, float]:
    return {
        "t_success_at_zero": 1.0 / 6.0,
        "t_elementary_yield": 1.0 / 30.0,
        "h_success_at_zero": 1.0,
        "h_elementary_yield": 1.0 / 15.0,
        "t_small_error_coefficient": 5.0,
        "h_small_error_coefficient": 35.0,
        "xi_t": 1.0 / math.log2(30.0),
        "xi_h": math.log(3.0) / math.log(15.0),
        "gamma_h": math.log(15.0) / math.log(3.0),
        "circuit_log_exponent": math.log(15.0) / math.log(3.0) + 1.0,
    }
