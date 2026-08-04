"""Exact identities for the PRL-Bench idx64 waveguide-QED gold audit."""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np


def transmission_components(
    delta_1: float, delta_2: float, phi: float
) -> dict[str, float]:
    """Return the components of the two-qubit expression printed in the source.

    The printed formula contains ``f_minus - cos(phi)``.  This is intentionally
    not silently changed to ``cos(2 phi)``: the benchmark copied that exact
    expression, and the audit must test the frozen contract as written.
    """

    sin_2phi = math.sin(2.0 * phi)
    cos_2phi = math.cos(2.0 * phi)
    total = delta_1 + delta_2
    product = delta_1 * delta_2
    f_plus = (
        1.0
        + 2.0 * delta_1**2
        + 2.0 * delta_2**2
        + 4.0 * product * cos_2phi
        - 2.0 * total * sin_2phi
    )
    f_minus = (
        1.0
        + 2.0 * delta_1**2
        + 2.0 * delta_2**2
        - 4.0 * product * cos_2phi
        - 2.0 * total * sin_2phi
    )
    q = 8.0 * product**2 + f_plus - cos_2phi
    p = (
        8.0 * product**2 * (1.0 + total**2)
        + 4.0 * product * total * sin_2phi
    )
    second_factor = total**2 * (f_minus - math.cos(phi)) + p
    denominator = 64.0 * delta_1**4 * delta_2**4 * (1.0 + total**2)
    return {
        "f_plus": f_plus,
        "f_minus": f_minus,
        "q": q,
        "p": p,
        "second_factor": second_factor,
        "denominator": denominator,
    }


def transmission_g(delta_1: float, delta_2: float, phi: float) -> float:
    if delta_1 == 0.0 or delta_2 == 0.0:
        raise ValueError("the frozen transmission formula excludes zero detuning")
    parts = transmission_components(delta_1, delta_2, phi)
    return parts["q"] * parts["second_factor"] / parts["denominator"]


def task1_divergent_path(epsilon: float) -> tuple[float, float, float]:
    """Counterexample path at phi=pi/6 where the printed g_T tends to -inf."""

    delta_1 = epsilon
    delta_2 = -epsilon + 12.0 * epsilon**2
    return delta_1, delta_2, transmission_g(delta_1, delta_2, math.pi / 6.0)


def reflection_g(delta_1: float, delta_2: float) -> float:
    total = delta_1 + delta_2
    numerator = total**2 + 4.0 * delta_1**2 * delta_2**2
    denominator = total**2 + total**4
    if denominator == 0.0:
        raise ValueError("reflection expression is undefined on delta_1=-delta_2")
    return numerator / denominator


def reflection_tail_asymptotic(s: float, width: float) -> float:
    """Source Eq. (S15): leading small-s probability-density asymptotic."""

    return (
        math.exp(-1.0 / (2.0 * width**2 * s))
        / (math.sqrt(2.0 * math.pi) * width * s)
    )


def z_values(detunings: Iterable[float]) -> np.ndarray:
    values = np.asarray(tuple(detunings), dtype=float)
    return 1.0 / (values - 0.5j)


def path_amplitude(
    detunings: Iterable[float], *, single_path_coefficient: float
) -> complex:
    """Strong-disorder transmission numerator for a selected sum coefficient."""

    z = z_values(detunings)
    pair_sum = sum(z[left] * z[right] for left in range(len(z)) for right in range(left))
    return 1.0 + 1j * single_path_coefficient * z.sum() - 0.5 * pair_sum


def frozen_f(detunings: Iterable[float]) -> complex:
    """The benchmark's mistyped amplitude, with i/2 multiplying sum(z)."""

    return path_amplitude(detunings, single_path_coefficient=0.5)


def source_f(detunings: Iterable[float]) -> complex:
    """The source Eq. (S30) numerator, with i multiplying sum(z)."""

    return path_amplitude(detunings, single_path_coefficient=1.0)


def symmetric_polynomials_n3(detunings: Iterable[float]) -> tuple[float, float, float]:
    d1, d2, d3 = tuple(float(value) for value in detunings)
    return d1 + d2 + d3, d1 * d2 + d1 * d3 + d2 * d3, d1 * d2 * d3


def frozen_numerator_n3(detunings: Iterable[float]) -> complex:
    """Polynomial numerator H where frozen_f = H / prod(delta_j-i/2)."""

    s1, _, s3 = symmetric_polynomials_n3(detunings)
    return s3 - 0.25 * s1 + 0.5j


def source_numerator_n3(detunings: Iterable[float]) -> complex:
    """Polynomial numerator of the correctly transcribed source amplitude."""

    s1, s2, s3 = symmetric_polynomials_n3(detunings)
    return s3 + 0.25 * s1 + 1j * (0.5 * s2 + 0.125)


def denominator_n3(detunings: Iterable[float]) -> complex:
    values = np.asarray(tuple(detunings), dtype=float)
    if values.shape != (3,):
        raise ValueError("N=3 requires exactly three detunings")
    return complex(np.prod(values - 0.5j))


def source_ppb_family(parameter: float) -> tuple[float, float, float]:
    """One ordered branch of the complete source-formula N=3 PPB family."""

    return float(parameter), 0.5, -0.5


def amplitude_jacobian(
    detunings: Iterable[float], *, single_path_coefficient: float
) -> np.ndarray:
    values = np.asarray(tuple(detunings), dtype=float)
    z = z_values(values)
    derivatives: list[complex] = []
    for index, z_value in enumerate(z):
        other_sum = z.sum() - z_value
        derivatives.append(
            z_value**2 * (-1j * single_path_coefficient + 0.5 * other_sum)
        )
    complex_gradient = np.asarray(derivatives)
    return np.vstack((complex_gradient.real, complex_gradient.imag))


def source_jacobian_singular_values(detunings: Iterable[float]) -> np.ndarray:
    return np.linalg.svd(
        amplitude_jacobian(detunings, single_path_coefficient=1.0),
        compute_uv=False,
    )


def source_closest_radius() -> float:
    """Minimum of sqrt(a^2+1/2) over the complete source PPB family."""

    return 1.0 / math.sqrt(2.0)
