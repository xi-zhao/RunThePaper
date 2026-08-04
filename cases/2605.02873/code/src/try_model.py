"""Independent finite-width Fresnel numerics for the frozen TRY targets.

This module implements only equations transcribed and independently verified in
EQUATION_CARDS.json. It never reads source figures or reference pixels.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
from numpy.polynomial.legendre import leggauss


@dataclass(frozen=True)
class ModelParameters:
    wavelength_m: float = 633e-9
    L1_m: float = 0.35
    L2_m: float = 0.35
    d_m: float = 500e-6
    a_m: float = 250e-6
    detector_x_m: float = -0.35 * 633e-9 / (4.0 * 500e-6)
    y_min_m: float = -1.5e-3
    y_max_m: float = 1.5e-3
    noise_floor_fraction: float = 0.02
    y_points: int = 3001
    slit_quadrature_order: int = 256
    source_chunk_size: int = 256

    @property
    def k_per_m(self) -> float:
        return 2.0 * np.pi / self.wavelength_m

    @property
    def W_m(self) -> float:
        return self.d_m / 2.0

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class ResponseState:
    y_m: np.ndarray
    E0: np.ndarray
    Mt: np.ndarray
    Mf: np.ndarray
    R0: np.ndarray
    gt: np.ndarray
    gf: np.ndarray


@dataclass(frozen=True)
class ReceiverState:
    response: ResponseState
    noise: np.ndarray
    full_fisher: np.ndarray
    optimized_codes: np.ndarray
    optimized_transfer: np.ndarray
    optimized_covariance: np.ndarray
    optimized_fisher: np.ndarray
    optimized_retention: np.ndarray
    toy_codes: np.ndarray
    toy_transfer: np.ndarray
    toy_covariance: np.ndarray
    toy_fisher: np.ndarray
    toy_retention: np.ndarray


def source_grid(parameters: ModelParameters, *, points: int | None = None) -> np.ndarray:
    count = parameters.y_points if points is None else int(points)
    if count < 3 or count % 2 == 0:
        raise ValueError("source-grid point count must be odd and at least 3")
    return np.linspace(parameters.y_min_m, parameters.y_max_m, count)


def slit_quadrature(
    parameters: ModelParameters,
    *,
    slit_width_m: float | None = None,
    order: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return nodes and weights on the two exact finite slit intervals."""
    width = parameters.a_m if slit_width_m is None else float(slit_width_m)
    quadrature_order = (
        parameters.slit_quadrature_order if order is None else int(order)
    )
    if not (0.0 < width <= parameters.d_m):
        raise ValueError("slit width must be positive and no larger than d")
    if quadrature_order < 16:
        raise ValueError("quadrature order must be at least 16")
    canonical_nodes, canonical_weights = leggauss(quadrature_order)
    half_width = width / 2.0
    all_nodes: list[np.ndarray] = []
    all_weights: list[np.ndarray] = []
    for sign in (-1.0, 1.0):
        center = sign * parameters.d_m / 2.0
        all_nodes.append(center + half_width * canonical_nodes)
        all_weights.append(half_width * canonical_weights)
    return np.concatenate(all_nodes), np.concatenate(all_weights)


def compute_field(
    y_m: np.ndarray,
    parameters: ModelParameters,
    *,
    slit_width_m: float | None = None,
    order: int | None = None,
    theta_t: float = 0.0,
    theta_f: float = 0.0,
) -> np.ndarray:
    x_m, x_weights = slit_quadrature(
        parameters, slit_width_m=slit_width_m, order=order
    )
    q_t = x_m / parameters.W_m
    q_f = q_t**2
    aberration_phase = theta_t * q_t + theta_f * q_f
    detector_phase = (
        parameters.k_per_m
        * (parameters.detector_x_m - x_m) ** 2
        / (2.0 * parameters.L2_m)
    )
    field = np.empty(y_m.size, dtype=np.complex128)
    chunk = parameters.source_chunk_size
    for start in range(0, y_m.size, chunk):
        stop = min(start + chunk, y_m.size)
        source_phase = (
            parameters.k_per_m
            * (x_m[None, :] - y_m[start:stop, None]) ** 2
            / (2.0 * parameters.L1_m)
        )
        kernel = np.exp(
            1j
            * (
                source_phase
                + detector_phase[None, :]
                + aberration_phase[None, :]
            )
        )
        field[start:stop] = kernel @ x_weights
    return field


def compute_response(
    parameters: ModelParameters,
    *,
    y_m: np.ndarray | None = None,
    slit_width_m: float | None = None,
    order: int | None = None,
) -> ResponseState:
    """Evaluate E0, weighted moments, response, and exact local scores."""
    source = source_grid(parameters) if y_m is None else np.asarray(y_m, dtype=float)
    x_m, x_weights = slit_quadrature(
        parameters, slit_width_m=slit_width_m, order=order
    )
    q_t = x_m / parameters.W_m
    q_f = q_t**2
    detector_phase = (
        parameters.k_per_m
        * (parameters.detector_x_m - x_m) ** 2
        / (2.0 * parameters.L2_m)
    )
    E0 = np.empty(source.size, dtype=np.complex128)
    Mt = np.empty(source.size, dtype=np.complex128)
    Mf = np.empty(source.size, dtype=np.complex128)
    chunk = parameters.source_chunk_size
    for start in range(0, source.size, chunk):
        stop = min(start + chunk, source.size)
        source_phase = (
            parameters.k_per_m
            * (x_m[None, :] - source[start:stop, None]) ** 2
            / (2.0 * parameters.L1_m)
        )
        kernel = np.exp(1j * (source_phase + detector_phase[None, :]))
        weighted = kernel * x_weights[None, :]
        E0[start:stop] = np.sum(weighted, axis=1)
        Mt[start:stop] = weighted @ q_t
        Mf[start:stop] = weighted @ q_f
    R0 = np.abs(E0) ** 2
    gt = -2.0 * np.imag(np.conjugate(E0) * Mt)
    gf = -2.0 * np.imag(np.conjugate(E0) * Mf)
    return ResponseState(source, E0, Mt, Mf, R0, gt, gf)


def integrate(y_m: np.ndarray, values: np.ndarray) -> float:
    return float(np.trapezoid(values, x=y_m))


def weighted_inner(
    y_m: np.ndarray, noise: np.ndarray, left: np.ndarray, right: np.ndarray
) -> float:
    return integrate(y_m, noise * left * right)


def noise_weight(
    response: ResponseState, parameters: ModelParameters
) -> np.ndarray:
    return response.R0 + parameters.noise_floor_fraction * np.max(response.R0)


def full_fisher(
    response: ResponseState, noise: np.ndarray
) -> np.ndarray:
    scores = np.stack([response.gt, response.gf], axis=0)
    fisher = np.empty((2, 2), dtype=float)
    for row in range(2):
        for col in range(2):
            fisher[row, col] = integrate(
                response.y_m, scores[row] * scores[col] / noise
            )
    return fisher


def _orthonormalize_pair(
    y_m: np.ndarray,
    noise: np.ndarray,
    first_raw: np.ndarray,
    second_raw: np.ndarray,
) -> np.ndarray:
    constant = np.ones_like(y_m)
    constant_norm = weighted_inner(y_m, noise, constant, constant)
    first = first_raw - (
        weighted_inner(y_m, noise, first_raw, constant) / constant_norm
    )
    first /= np.sqrt(weighted_inner(y_m, noise, first, first))
    second = second_raw - (
        weighted_inner(y_m, noise, second_raw, constant) / constant_norm
    ) * constant
    second -= weighted_inner(y_m, noise, second, first) * first
    second /= np.sqrt(weighted_inner(y_m, noise, second, second))
    return np.stack([first, second], axis=0)


def optimized_codes(
    response: ResponseState, noise: np.ndarray
) -> np.ndarray:
    codes = _orthonormalize_pair(
        response.y_m, noise, response.gt / noise, response.gf / noise
    )
    if integrate(response.y_m, codes[0] * response.gt) < 0.0:
        codes[0] *= -1.0
    if integrate(response.y_m, codes[1] * response.gf) < 0.0:
        codes[1] *= -1.0
    return codes


def toy_codes(response: ResponseState, noise: np.ndarray) -> np.ndarray:
    normalization = integrate(response.y_m, response.R0)
    centroid = integrate(response.y_m, response.y_m * response.R0) / normalization
    variance = (
        integrate(
            response.y_m, (response.y_m - centroid) ** 2 * response.R0
        )
        / normalization
    )
    xi = (response.y_m - centroid) / np.sqrt(variance)
    codes = _orthonormalize_pair(
        response.y_m, noise, xi, (xi**2 - 1.0) / np.sqrt(2.0)
    )
    if integrate(response.y_m, codes[0] * response.gt) < 0.0:
        codes[0] *= -1.0
    if integrate(response.y_m, codes[1] * response.gf) < 0.0:
        codes[1] *= -1.0
    return codes


def coded_fisher(
    response: ResponseState,
    noise: np.ndarray,
    codes: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    scores = np.stack([response.gt, response.gf], axis=0)
    transfer = np.empty((codes.shape[0], 2), dtype=float)
    covariance = np.empty((codes.shape[0], codes.shape[0]), dtype=float)
    for channel in range(codes.shape[0]):
        for parameter in range(2):
            transfer[channel, parameter] = integrate(
                response.y_m, codes[channel] * scores[parameter]
            )
        for other in range(codes.shape[0]):
            covariance[channel, other] = weighted_inner(
                response.y_m, noise, codes[channel], codes[other]
            )
    fisher = transfer.T @ np.linalg.solve(covariance, transfer)
    return fisher, transfer, covariance


def retention_eigenvalues(
    full_matrix: np.ndarray, coded_matrix: np.ndarray
) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(full_matrix)
    if np.min(eigenvalues) <= 0.0:
        raise ValueError("full Fisher matrix must be positive definite")
    inverse_sqrt = (
        eigenvectors
        @ np.diag(eigenvalues ** -0.5)
        @ eigenvectors.T
    )
    whitened = inverse_sqrt @ coded_matrix @ inverse_sqrt
    return np.linalg.eigvalsh((whitened + whitened.T) / 2.0)


def compute_receiver(
    parameters: ModelParameters,
    *,
    y_m: np.ndarray | None = None,
    slit_width_m: float | None = None,
    order: int | None = None,
) -> ReceiverState:
    response = compute_response(
        parameters, y_m=y_m, slit_width_m=slit_width_m, order=order
    )
    noise = noise_weight(response, parameters)
    full = full_fisher(response, noise)
    optimized = optimized_codes(response, noise)
    optimized_fisher_matrix, optimized_transfer, optimized_covariance = (
        coded_fisher(response, noise, optimized)
    )
    toy = toy_codes(response, noise)
    toy_fisher_matrix, toy_transfer, toy_covariance = coded_fisher(
        response, noise, toy
    )
    return ReceiverState(
        response=response,
        noise=noise,
        full_fisher=full,
        optimized_codes=optimized,
        optimized_transfer=optimized_transfer,
        optimized_covariance=optimized_covariance,
        optimized_fisher=optimized_fisher_matrix,
        optimized_retention=retention_eigenvalues(
            full, optimized_fisher_matrix
        ),
        toy_codes=toy,
        toy_transfer=toy_transfer,
        toy_covariance=toy_covariance,
        toy_fisher=toy_fisher_matrix,
        toy_retention=retention_eigenvalues(full, toy_fisher_matrix),
    )


def finite_difference_scores(
    parameters: ModelParameters,
    y_m: np.ndarray,
    *,
    epsilon: float = 1e-6,
    slit_width_m: float | None = None,
    order: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    tilt_plus = np.abs(
        compute_field(
            y_m,
            parameters,
            slit_width_m=slit_width_m,
            order=order,
            theta_t=epsilon,
        )
    ) ** 2
    tilt_minus = np.abs(
        compute_field(
            y_m,
            parameters,
            slit_width_m=slit_width_m,
            order=order,
            theta_t=-epsilon,
        )
    ) ** 2
    defocus_plus = np.abs(
        compute_field(
            y_m,
            parameters,
            slit_width_m=slit_width_m,
            order=order,
            theta_f=epsilon,
        )
    ) ** 2
    defocus_minus = np.abs(
        compute_field(
            y_m,
            parameters,
            slit_width_m=slit_width_m,
            order=order,
            theta_f=-epsilon,
        )
    ) ** 2
    return (
        (tilt_plus - tilt_minus) / (2.0 * epsilon),
        (defocus_plus - defocus_minus) / (2.0 * epsilon),
    )


def width_scan(
    parameters: ModelParameters, widths_um: Iterable[float]
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for width_um in widths_um:
        response = compute_response(
            parameters, slit_width_m=float(width_um) * 1e-6
        )
        noise = noise_weight(response, parameters)
        fisher = full_fisher(response, noise)
        rows.append(
            {
                "slit_width_um": float(width_um),
                "Ftt": float(fisher[0, 0]),
                "Ftf": float(fisher[0, 1]),
                "Fff": float(fisher[1, 1]),
                "rho_Fff_over_Ftt": float(fisher[1, 1] / fisher[0, 0]),
            }
        )
    return rows


def relative_l2(candidate: np.ndarray, reference: np.ndarray) -> float:
    denominator = np.linalg.norm(reference.ravel())
    if denominator == 0.0:
        return float(np.linalg.norm(candidate.ravel()))
    return float(np.linalg.norm((candidate - reference).ravel()) / denominator)


def max_scaled_error(candidate: np.ndarray, reference: np.ndarray) -> float:
    scale = max(float(np.max(np.abs(reference))), np.finfo(float).tiny)
    return float(np.max(np.abs(candidate - reference)) / scale)


def zero_crossings(values: np.ndarray) -> int:
    signs = np.sign(values)
    nonzero = signs[signs != 0]
    if nonzero.size < 2:
        return 0
    return int(np.count_nonzero(nonzero[1:] != nonzero[:-1]))
