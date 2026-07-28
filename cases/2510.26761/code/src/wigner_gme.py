"""Derivation-backed Wigner-function calculations for arXiv:2510.26761.

The module follows the paper's convention

    W(alpha) = (2/pi)^M Tr[rho exp(i pi |a-alpha|^2)].

Every production function maps to a verified card in ``EQUATION_CARDS.json``.
No source figure pixels enter these calculations.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import brentq
from scipy.signal import fftconvolve
from scipy.special import eval_genlaguerre


PI = math.pi
WIGNER_PREFAC_3 = (2.0 / PI) ** 3
W_STATE_GME_THRESHOLD = 1.0 / (2.0 * math.sqrt(2.0))
SOURCE_PRINTED_GME_BOUND = (75.0 * math.sqrt(2.0) + 56.0) / 600.0
STATE_DERIVED_GME_BOUND = (75.0 * math.sqrt(2.0) + 52.0) / 600.0


def _scalar_or_array(value: NDArray[np.generic]) -> float | complex | NDArray[np.generic]:
    if value.ndim == 0:
        return value.item()
    return value


def wigner_fock_element(
    ket_number: int,
    bra_number: int,
    alpha: ArrayLike,
) -> complex | NDArray[np.complex128]:
    """Return the Wigner transform of ``|ket><bra|``.

    For ``ket_number >= bra_number`` this is the associated-Laguerre expression
    derived in ``DERIVATION_TRACE.md``. The reversed ordering follows by
    Hermitian conjugation.
    """

    if ket_number < 0 or bra_number < 0:
        raise ValueError("Fock indices must be nonnegative")
    coordinate = np.asarray(alpha, dtype=np.complex128)
    if ket_number < bra_number:
        reversed_element = np.asarray(
            wigner_fock_element(bra_number, ket_number, coordinate),
            dtype=np.complex128,
        )
        return _scalar_or_array(np.conjugate(reversed_element))

    order = ket_number - bra_number
    radial_argument = 4.0 * np.abs(coordinate) ** 2
    coefficient = (
        (2.0 / PI)
        * ((-1.0) ** bra_number)
        * math.sqrt(math.factorial(bra_number) / math.factorial(ket_number))
    )
    result = (
        coefficient
        * np.power(2.0 * np.conjugate(coordinate), order)
        * eval_genlaguerre(bra_number, order, radial_argument)
        * np.exp(-0.5 * radial_argument)
    )
    return _scalar_or_array(np.asarray(result, dtype=np.complex128))


def wigner_from_density(
    density: ArrayLike,
    alpha: ArrayLike,
    *,
    reality_tolerance: float = 1e-11,
) -> float | NDArray[np.float64]:
    """Evaluate a finite single-mode density operator in phase space."""

    rho = np.asarray(density, dtype=np.complex128)
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("density must be a square matrix")
    coordinate = np.asarray(alpha, dtype=np.complex128)
    result = np.zeros(coordinate.shape, dtype=np.complex128)
    for ket_number, bra_number in zip(*np.nonzero(np.abs(rho) > 0.0), strict=True):
        result += rho[ket_number, bra_number] * np.asarray(
            wigner_fock_element(ket_number, bra_number, coordinate)
        )
    maximum_imaginary = float(np.max(np.abs(result.imag), initial=0.0))
    if maximum_imaginary > reality_tolerance:
        raise ValueError(
            f"Hermitian density produced imaginary Wigner residue {maximum_imaginary:.3e}"
        )
    return _scalar_or_array(np.asarray(result.real, dtype=np.float64))


def w_state_wigner_slice(alpha: ArrayLike) -> float | NDArray[np.float64]:
    """Tripartite W-state Wigner function on ``alpha_1=alpha_2=alpha_3``."""

    coordinate = np.asarray(alpha, dtype=np.complex128)
    radius_squared = np.abs(coordinate) ** 2
    result = WIGNER_PREFAC_3 * (12.0 * radius_squared - 1.0) * np.exp(
        -6.0 * radius_squared
    )
    return _scalar_or_array(np.asarray(result, dtype=np.float64))


def w_state_disk_volume(radius: ArrayLike) -> float | NDArray[np.float64]:
    """Closed-form finite-disk absolute volume from the paper's End Matter."""

    r = np.asarray(radius, dtype=np.float64)
    if np.any(r < 0.0):
        raise ValueError("radius must be nonnegative")
    common = (1.0 + 12.0 * r**2) * np.exp(-6.0 * r**2)
    zero_radius = 1.0 / (2.0 * math.sqrt(3.0))
    result = np.where(
        r < zero_radius,
        (common - 1.0) / 3.0,
        (4.0 * math.exp(-0.5) - common - 1.0) / 3.0,
    )
    return _scalar_or_array(np.asarray(result, dtype=np.float64))


def w_state_critical_radius() -> float:
    """Solve the exact finite-region GME threshold crossing."""

    return float(
        brentq(
            lambda radius: float(w_state_disk_volume(radius))
            - W_STATE_GME_THRESHOLD,
            0.6,
            0.8,
            xtol=1e-14,
            rtol=1e-14,
        )
    )


def w_state_characteristic_slice(xi: ArrayLike) -> float | NDArray[np.float64]:
    """Tripartite W-state characteristic function on the equal slice."""

    coordinate = np.asarray(xi, dtype=np.complex128)
    radius_squared = np.abs(coordinate) ** 2
    result = (1.0 - 3.0 * radius_squared) * np.exp(-1.5 * radius_squared)
    return _scalar_or_array(np.asarray(result, dtype=np.float64))


def witness_points() -> NDArray[np.complex128]:
    """Return the paper's seven-point set Xi in a deterministic order."""

    xi0 = complex(85.0, 147.0) / 200.0
    real_sum = xi0 + xi0.conjugate()
    return np.asarray(
        [0.0j, real_sum, -real_sum, xi0, -xi0, xi0.conjugate(), -xi0.conjugate()],
        dtype=np.complex128,
    )


def unique_pairwise_differences(
    points: ArrayLike | None = None,
    *,
    decimals: int = 12,
) -> NDArray[np.complex128]:
    """Return the unique pairwise differences in display-stable order."""

    values = witness_points() if points is None else np.asarray(points, dtype=np.complex128)
    differences = values[:, None] - values[None, :]
    keys: dict[tuple[float, float], complex] = {}
    for value in differences.ravel():
        key = (round(float(value.real), decimals), round(float(value.imag), decimals))
        keys[key] = complex(key[0], key[1])
    ordered = sorted(keys.values(), key=lambda value: (value.imag, value.real))
    return np.asarray(ordered, dtype=np.complex128)


def characteristic_witness_matrix(
    points: ArrayLike | None = None,
) -> NDArray[np.float64]:
    """Build ``C circle K`` for the W state with a vacuum filter."""

    values = witness_points() if points is None else np.asarray(points, dtype=np.complex128)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("points must be a nonempty one-dimensional array")
    delta = values[:, None] - values[None, :]
    radius_squared = np.abs(delta) ** 2
    matrix = (
        (1.0 / len(values))
        * (1.0 - 3.0 * radius_squared)
        * np.exp(-2.0 * radius_squared)
    )
    return np.asarray(matrix, dtype=np.float64)


def characteristic_witness_spectrum() -> NDArray[np.float64]:
    """Return the sorted Hermitian eigenspectrum of the seven-point witness."""

    return np.linalg.eigvalsh(characteristic_witness_matrix())


def illustrative_state_amplitudes() -> dict[tuple[int, int], float]:
    """Sparse amplitudes ``(n_plus, n_minus) -> coefficient`` for Fig. 1."""

    small = 1.0 / (5.0 * math.sqrt(2.0))
    large = math.sqrt(19.0) * small
    even = 1.0 / math.sqrt(10.0)
    return {
        (1, 0): small,
        (3, 0): small,
        (1, 1): large,
        (3, 1): large,
        (2, 2): even,
        (4, 2): even,
    }


def illustrative_state_norm(
    amplitudes: Mapping[tuple[int, int], complex] | None = None,
) -> float:
    """Return the squared norm of the sparse collective-Fock state."""

    values = illustrative_state_amplitudes() if amplitudes is None else amplitudes
    return float(sum(abs(coefficient) ** 2 for coefficient in values.values()))


def illustrative_relative_parity(
    amplitudes: Mapping[tuple[int, int], complex] | None = None,
) -> float:
    """Expectation of parity on both relative modes (the third is vacuum)."""

    values = illustrative_state_amplitudes() if amplitudes is None else amplitudes
    return float(
        sum(
            ((-1.0) ** relative_number) * abs(coefficient) ** 2
            for (_, relative_number), coefficient in values.items()
        )
    )


def illustrative_com_density() -> NDArray[np.complex128]:
    """Reduced center-of-mass density matrix in the n=0,...,4 basis."""

    density = np.zeros((5, 5), dtype=np.complex128)
    for left in (1, 3):
        for right in (1, 3):
            density[left, right] = 0.4
    for left in (2, 4):
        for right in (2, 4):
            density[left, right] = 0.1
    return density


def illustrative_com_wigner(alpha: ArrayLike) -> float | NDArray[np.float64]:
    """Wigner function of the reduced center-of-mass state."""

    return wigner_from_density(illustrative_com_density(), alpha)


def illustrative_wigner_cut(
    alpha_plus: ArrayLike,
    alpha_minus: ArrayLike,
    *,
    reality_tolerance: float = 1e-10,
) -> float | NDArray[np.float64]:
    """Evaluate the Fig. 1 cut ``W(alpha_plus, alpha_minus, 0)``."""

    plus = np.asarray(alpha_plus, dtype=np.complex128)
    minus = np.asarray(alpha_minus, dtype=np.complex128)
    plus, minus = np.broadcast_arrays(plus, minus)
    result = np.zeros(plus.shape, dtype=np.complex128)
    amplitudes = illustrative_state_amplitudes()
    for (plus_ket, minus_ket), coefficient_ket in amplitudes.items():
        for (plus_bra, minus_bra), coefficient_bra in amplitudes.items():
            result += (
                coefficient_ket
                * np.conjugate(coefficient_bra)
                * np.asarray(wigner_fock_element(plus_ket, plus_bra, plus))
                * np.asarray(wigner_fock_element(minus_ket, minus_bra, minus))
            )
    result *= 2.0 / PI  # the unused relative mode is vacuum at the origin
    maximum_imaginary = float(np.max(np.abs(result.imag), initial=0.0))
    if maximum_imaginary > reality_tolerance:
        raise ValueError(
            f"illustrative cut has imaginary residue {maximum_imaginary:.3e}"
        )
    return _scalar_or_array(np.asarray(result.real, dtype=np.float64))


def illustrative_slice_polynomials(
    alpha: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return the unnormalized odd/even cat polynomials on the equal slice."""

    coordinate = np.asarray(alpha, dtype=np.complex128)
    gamma = math.sqrt(3.0) * coordinate
    t = 4.0 * np.abs(gamma) ** 2
    real_gamma_squared = np.real(gamma**2)
    p13 = (
        -2.0
        + 4.0 * t
        - 1.5 * t**2
        + t**3 / 6.0
        - (8.0 / math.sqrt(6.0)) * real_gamma_squared * (3.0 - t)
    )
    p24 = (
        2.0
        - 6.0 * t
        + 3.5 * t**2
        - (2.0 / 3.0) * t**3
        + t**4 / 24.0
        + (4.0 / math.sqrt(3.0))
        * real_gamma_squared
        * (6.0 - 4.0 * t + 0.5 * t**2)
    )
    return np.asarray(p13, dtype=np.float64), np.asarray(p24, dtype=np.float64)


def illustrative_slice_wigner(alpha: ArrayLike) -> float | NDArray[np.float64]:
    """Evaluate ``W_psi(alpha,alpha,alpha)`` using the derived polynomial."""

    coordinate = np.asarray(alpha, dtype=np.complex128)
    gamma = math.sqrt(3.0) * coordinate
    p13, p24 = illustrative_slice_polynomials(coordinate)
    polynomial = -(9.0 / 25.0) * p13 + 0.1 * p24
    result = WIGNER_PREFAC_3 * np.exp(-2.0 * np.abs(gamma) ** 2) * polynomial
    return _scalar_or_array(np.asarray(result, dtype=np.float64))


def illustrative_slice_signed_integral() -> float:
    """Exact signed equal-slice integral derived from relative parity."""

    return -52.0 / (75.0 * PI**2)


def illustrative_slice_metrics(
    *,
    radial_order: int = 640,
    angular_order: int = 2048,
    radial_cutoff: float = 4.0,
) -> dict[str, float | int]:
    """Deterministically integrate the illustrative equal-slice Wigner field."""

    if radial_order < 2 or angular_order < 4 or radial_cutoff <= 0.0:
        raise ValueError("invalid quadrature specification")
    nodes, weights = np.polynomial.legendre.leggauss(radial_order)
    radii = 0.5 * radial_cutoff * (nodes + 1.0)
    radial_weights = 0.5 * radial_cutoff * weights
    angles = np.arange(angular_order, dtype=np.float64) * (
        2.0 * PI / angular_order
    )
    coordinates = radii[:, None] * np.exp(1.0j * angles[None, :])
    field = np.asarray(illustrative_slice_wigner(coordinates))
    measure = radial_weights[:, None] * radii[:, None] * (2.0 * PI / angular_order)
    signed_integral = float(np.sum(field * measure))
    negative_integral = float(np.sum(np.maximum(-field, 0.0) * measure))
    negativity_volume = (PI / 2.0) ** 2 * negative_integral
    return {
        "radial_order": radial_order,
        "angular_order": angular_order,
        "radial_cutoff": radial_cutoff,
        "signed_integral": signed_integral,
        "signed_integral_exact": illustrative_slice_signed_integral(),
        "negative_integral": negative_integral,
        "negativity_volume": negativity_volume,
        "state_derived_gme_bound": STATE_DERIVED_GME_BOUND,
        "source_printed_gme_bound": SOURCE_PRINTED_GME_BOUND,
        "corrected_margin": negativity_volume - STATE_DERIVED_GME_BOUND,
        "printed_margin": negativity_volume - SOURCE_PRINTED_GME_BOUND,
    }


def gaussian_kernel(alpha: ArrayLike) -> float | NDArray[np.float64]:
    """The three-mode minimum-width Gaussian kernel used in Fig. 1."""

    coordinate = np.asarray(alpha, dtype=np.complex128)
    result = (8.0 / PI) * np.exp(-6.0 * np.abs(coordinate) ** 2)
    return _scalar_or_array(np.asarray(result, dtype=np.float64))


def fock_kernel_integral(number: int) -> float:
    """Analytic convolution of ``W_n`` with the Fig. 1 kernel at the origin."""

    if number < 0:
        raise ValueError("Fock number must be nonnegative")
    return ((-1.0) ** number) * (2.0 ** (1 - number)) / PI


def smoothed_origin_exact() -> float:
    """Exact smoothed center-of-mass Wigner value at the origin."""

    populations = {1: 0.4, 2: 0.1, 3: 0.4, 4: 0.1}
    return float(
        sum(weight * fock_kernel_integral(number) for number, weight in populations.items())
    )


def convolve_with_gaussian_kernel(
    field: ArrayLike,
    axis: ArrayLike,
) -> NDArray[np.float64]:
    """Convolve a square Cartesian field with the paper's Gaussian kernel."""

    values = np.asarray(field, dtype=np.float64)
    coordinates = np.asarray(axis, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != values.shape[1]:
        raise ValueError("field must be a square two-dimensional array")
    if coordinates.ndim != 1 or len(coordinates) != values.shape[0]:
        raise ValueError("axis length must match the field")
    if len(coordinates) < 3 or len(coordinates) % 2 == 0:
        raise ValueError("axis must contain an odd number of points")
    steps = np.diff(coordinates)
    if not np.allclose(steps, steps[0], rtol=1e-12, atol=1e-14):
        raise ValueError("axis must be uniformly spaced")
    if not np.isclose(coordinates[len(coordinates) // 2], 0.0, atol=1e-14):
        raise ValueError("axis must be centered at zero")
    x, y = np.meshgrid(coordinates, coordinates, indexing="xy")
    kernel = np.asarray(gaussian_kernel(x + 1.0j * y))
    return np.asarray(
        fftconvolve(values, kernel, mode="same") * float(steps[0]) ** 2,
        dtype=np.float64,
    )
