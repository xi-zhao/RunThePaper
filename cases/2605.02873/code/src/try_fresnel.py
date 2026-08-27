"""Independent finite-width TRY numerics for arXiv:2605.02873v1.

Only formulas transcribed and independently checked in EQC001-EQC008 enter
this module. Original figure pixels and tabulated paper values are deliberately
absent; those belong to the comparison lane in ``scripts/run_target.py``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class Geometry:
    wavelength_m: float = 633e-9
    L1_m: float = 0.35
    L2_m: float = 0.35
    slit_separation_m: float = 500e-6
    slit_width_m: float = 250e-6
    detector_x_m: float = -110.775e-6
    y_min_m: float = -1.5e-3
    y_max_m: float = 1.5e-3
    noise_floor_fraction: float = 0.02

    @property
    def wave_number_per_m(self) -> float:
        return 2.0 * np.pi / self.wavelength_m

    @property
    def half_separation_m(self) -> float:
        return self.slit_separation_m / 2.0


@dataclass(frozen=True)
class FresnelObservables:
    y_m: FloatArray
    E0: ComplexArray
    R0: FloatArray
    M_t: ComplexArray
    M_f: ComplexArray
    g_t: FloatArray
    g_f: FloatArray


@dataclass(frozen=True)
class MainSolution:
    geometry: Geometry
    quadrature_order: int
    y_points: int
    observables: FresnelObservables
    noise_weight: FloatArray
    optimized_codes: FloatArray
    toy_codes: FloatArray
    full_fisher: FloatArray
    optimized_fisher: FloatArray
    toy_fisher: FloatArray
    optimized_retention: FloatArray
    toy_retention: FloatArray


def source_grid(geometry: Geometry, points: int) -> FloatArray:
    if points < 3:
        raise ValueError("source grid requires at least three points")
    return np.linspace(geometry.y_min_m, geometry.y_max_m, points, dtype=np.float64)


def integration_weights(coordinate: FloatArray) -> FloatArray:
    """Trapezoidal weights for a strictly increasing, possibly nonuniform grid."""

    if coordinate.ndim != 1 or coordinate.size < 2:
        raise ValueError("coordinate must be a one-dimensional grid")
    spacing = np.diff(coordinate)
    if np.any(spacing <= 0.0):
        raise ValueError("coordinate must be strictly increasing")
    weights = np.empty_like(coordinate)
    weights[0] = spacing[0] / 2.0
    weights[-1] = spacing[-1] / 2.0
    weights[1:-1] = (spacing[:-1] + spacing[1:]) / 2.0
    return weights


def slit_quadrature(geometry: Geometry, order: int) -> tuple[FloatArray, FloatArray]:
    """Gauss--Legendre nodes and weights on the two exact slit intervals."""

    if order < 8:
        raise ValueError("slit quadrature order must be at least eight")
    canonical_nodes, canonical_weights = np.polynomial.legendre.leggauss(order)
    nodes: list[FloatArray] = []
    weights: list[FloatArray] = []
    half_width = geometry.slit_width_m / 2.0
    for sign in (-1.0, 1.0):
        center = sign * geometry.slit_separation_m / 2.0
        nodes.append(center + half_width * canonical_nodes)
        weights.append(half_width * canonical_weights)
    return np.concatenate(nodes), np.concatenate(weights)


def fresnel_field(
    geometry: Geometry,
    y_m: FloatArray,
    quadrature_order: int,
    *,
    theta_t: float = 0.0,
    theta_f: float = 0.0,
) -> ComplexArray:
    """Evaluate Eq. (2)/(S1) without source-side image information."""

    x_m, x_weights = slit_quadrature(geometry, quadrature_order)
    W_m = geometry.half_separation_m
    propagation_phase = geometry.wave_number_per_m * (
        (x_m[np.newaxis, :] - y_m[:, np.newaxis]) ** 2 / (2.0 * geometry.L1_m)
        + (geometry.detector_x_m - x_m[np.newaxis, :]) ** 2
        / (2.0 * geometry.L2_m)
    )
    aberration_phase = (
        theta_t * x_m[np.newaxis, :] / W_m
        + theta_f * (x_m[np.newaxis, :] / W_m) ** 2
    )
    return np.exp(1j * (propagation_phase + aberration_phase)) @ x_weights


def fresnel_observables(
    geometry: Geometry,
    y_m: FloatArray,
    quadrature_order: int,
) -> FresnelObservables:
    """Evaluate E0, R0, weighted moments, and analytic local derivatives."""

    x_m, x_weights = slit_quadrature(geometry, quadrature_order)
    W_m = geometry.half_separation_m
    phase = geometry.wave_number_per_m * (
        (x_m[np.newaxis, :] - y_m[:, np.newaxis]) ** 2 / (2.0 * geometry.L1_m)
        + (geometry.detector_x_m - x_m[np.newaxis, :]) ** 2
        / (2.0 * geometry.L2_m)
    )
    kernel = np.exp(1j * phase)
    E0 = kernel @ x_weights
    M_t = kernel @ (x_weights * (x_m / W_m))
    M_f = kernel @ (x_weights * (x_m / W_m) ** 2)
    R0 = np.real(np.conjugate(E0) * E0)
    g_t = -2.0 * np.imag(np.conjugate(E0) * M_t)
    g_f = -2.0 * np.imag(np.conjugate(E0) * M_f)
    return FresnelObservables(y_m, E0, R0, M_t, M_f, g_t, g_f)


def noise_inner(
    left: FloatArray,
    right: FloatArray,
    noise_weight: FloatArray,
    y_m: FloatArray,
) -> float:
    weights = integration_weights(y_m)
    return float(np.sum(weights * noise_weight * left * right))


def _orthonormalize_pair(
    raw_first: FloatArray,
    raw_second: FloatArray,
    noise_weight: FloatArray,
    y_m: FloatArray,
) -> FloatArray:
    constant = np.ones_like(y_m)
    constant_norm = noise_inner(constant, constant, noise_weight, y_m)
    first = raw_first - (
        noise_inner(raw_first, constant, noise_weight, y_m) / constant_norm
    )
    first_norm = np.sqrt(noise_inner(first, first, noise_weight, y_m))
    if first_norm <= 0.0:
        raise ValueError("first code is null after nuisance projection")
    first = first / first_norm

    second = raw_second - (
        noise_inner(raw_second, constant, noise_weight, y_m) / constant_norm
    )
    second = second - noise_inner(second, first, noise_weight, y_m) * first
    second_norm = np.sqrt(noise_inner(second, second, noise_weight, y_m))
    if second_norm <= 0.0:
        raise ValueError("second code is null after nuisance projection")
    second = second / second_norm
    return np.vstack((first, second))


def optimized_codes(
    g_t: FloatArray,
    g_f: FloatArray,
    noise_weight: FloatArray,
    y_m: FloatArray,
) -> FloatArray:
    codes = _orthonormalize_pair(
        g_t / noise_weight,
        g_f / noise_weight,
        noise_weight,
        y_m,
    )
    # Fix the otherwise arbitrary signs by positive same-parameter response.
    weights = integration_weights(y_m)
    if np.sum(weights * codes[0] * g_t) < 0.0:
        codes[0] *= -1.0
    if np.sum(weights * codes[1] * g_f) < 0.0:
        codes[1] *= -1.0
    return codes


def toy_codes(
    R0: FloatArray,
    noise_weight: FloatArray,
    y_m: FloatArray,
) -> FloatArray:
    weights = integration_weights(y_m)
    response_integral = float(np.sum(weights * R0))
    mean_y = float(np.sum(weights * y_m * R0) / response_integral)
    variance_y = float(
        np.sum(weights * (y_m - mean_y) ** 2 * R0) / response_integral
    )
    xi = (y_m - mean_y) / np.sqrt(variance_y)
    raw_tilt = xi
    raw_defocus = (xi**2 - 1.0) / np.sqrt(2.0)
    return _orthonormalize_pair(
        raw_tilt,
        raw_defocus,
        noise_weight,
        y_m,
    )


def full_fisher(
    g_t: FloatArray,
    g_f: FloatArray,
    noise_weight: FloatArray,
    y_m: FloatArray,
) -> FloatArray:
    weights = integration_weights(y_m)
    scores = np.vstack((g_t, g_f))
    weighted_scores = scores * (weights / noise_weight)[np.newaxis, :]
    return weighted_scores @ scores.T


def coded_fisher(
    codes: FloatArray,
    g_t: FloatArray,
    g_f: FloatArray,
    noise_weight: FloatArray,
    y_m: FloatArray,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    weights = integration_weights(y_m)
    scores = np.vstack((g_t, g_f))
    transfer = (codes * weights[np.newaxis, :]) @ scores.T
    covariance = (
        codes * (weights * noise_weight)[np.newaxis, :]
    ) @ codes.T
    fisher = transfer.T @ np.linalg.solve(covariance, transfer)
    return fisher, transfer, covariance


def retention_eigenvalues(
    full_matrix: FloatArray,
    coded_matrix: FloatArray,
) -> FloatArray:
    values, vectors = np.linalg.eigh(full_matrix)
    if np.any(values <= 0.0):
        raise ValueError("full Fisher matrix must be positive definite")
    inverse_sqrt = (vectors * (1.0 / np.sqrt(values))[np.newaxis, :]) @ vectors.T
    whitened = inverse_sqrt @ coded_matrix @ inverse_sqrt
    whitened = (whitened + whitened.T) / 2.0
    return np.linalg.eigvalsh(whitened)


def solve_main(
    *,
    y_points: int = 1201,
    quadrature_order: int = 192,
    geometry: Geometry | None = None,
) -> MainSolution:
    geometry = geometry or Geometry()
    y_m = source_grid(geometry, y_points)
    observables = fresnel_observables(geometry, y_m, quadrature_order)
    noise_weight = (
        observables.R0
        + geometry.noise_floor_fraction * float(np.max(observables.R0))
    )
    opt_codes = optimized_codes(
        observables.g_t,
        observables.g_f,
        noise_weight,
        y_m,
    )
    parity_codes = toy_codes(observables.R0, noise_weight, y_m)
    F_full = full_fisher(
        observables.g_t,
        observables.g_f,
        noise_weight,
        y_m,
    )
    F_opt, _, _ = coded_fisher(
        opt_codes,
        observables.g_t,
        observables.g_f,
        noise_weight,
        y_m,
    )
    F_toy, _, _ = coded_fisher(
        parity_codes,
        observables.g_t,
        observables.g_f,
        noise_weight,
        y_m,
    )
    return MainSolution(
        geometry=geometry,
        quadrature_order=quadrature_order,
        y_points=y_points,
        observables=observables,
        noise_weight=noise_weight,
        optimized_codes=opt_codes,
        toy_codes=parity_codes,
        full_fisher=F_full,
        optimized_fisher=F_opt,
        toy_fisher=F_toy,
        optimized_retention=retention_eigenvalues(F_full, F_opt),
        toy_retention=retention_eigenvalues(F_full, F_toy),
    )


def width_scan(
    widths_m: FloatArray,
    *,
    y_points: int = 1201,
    quadrature_order: int = 192,
    base_geometry: Geometry | None = None,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    geometry = base_geometry or Geometry()
    ratios: list[float] = []
    fisher_tt: list[float] = []
    fisher_ff: list[float] = []
    for width_m in widths_m:
        width_geometry = Geometry(
            wavelength_m=geometry.wavelength_m,
            L1_m=geometry.L1_m,
            L2_m=geometry.L2_m,
            slit_separation_m=geometry.slit_separation_m,
            slit_width_m=float(width_m),
            detector_x_m=geometry.detector_x_m,
            y_min_m=geometry.y_min_m,
            y_max_m=geometry.y_max_m,
            noise_floor_fraction=geometry.noise_floor_fraction,
        )
        y_m = source_grid(width_geometry, y_points)
        observables = fresnel_observables(
            width_geometry,
            y_m,
            quadrature_order,
        )
        noise_weight = (
            observables.R0
            + width_geometry.noise_floor_fraction * float(np.max(observables.R0))
        )
        fisher = full_fisher(
            observables.g_t,
            observables.g_f,
            noise_weight,
            y_m,
        )
        fisher_tt.append(float(fisher[0, 0]))
        fisher_ff.append(float(fisher[1, 1]))
        ratios.append(float(fisher[1, 1] / fisher[0, 0]))
    return (
        np.asarray(ratios, dtype=np.float64),
        np.asarray(fisher_tt, dtype=np.float64),
        np.asarray(fisher_ff, dtype=np.float64),
    )
