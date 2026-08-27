"""Ion-chain normal modes and piecewise toggle closure for Fig. S1."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares, root


@dataclass(frozen=True)
class ToggleSchedule:
    boundaries: np.ndarray
    amplitudes: np.ndarray
    residuals: np.ndarray
    cost: float


def _equilibrium_gradient(positions: np.ndarray) -> np.ndarray:
    delta = positions[:, None] - positions[None, :]
    mask = ~np.eye(len(positions), dtype=bool)
    inverse_cube = np.zeros_like(delta)
    inverse_cube[mask] = np.abs(delta[mask]) ** -3
    return positions - np.sum(delta * inverse_cube, axis=1)


def equilibrium_positions(number_of_ions: int) -> np.ndarray:
    """Dimensionless equilibrium positions in a 1D harmonic trap."""

    if number_of_ions < 1:
        raise ValueError("number_of_ions must be positive")
    if number_of_ions == 1:
        return np.zeros(1)
    extent = 0.8 * number_of_ions ** 0.65
    initial = np.linspace(-extent, extent, number_of_ions)
    solution = root(_equilibrium_gradient, initial, method="lm")
    residual = float(np.max(np.abs(_equilibrium_gradient(solution.x))))
    if not solution.success or residual > 1e-10:
        refinement = least_squares(
            _equilibrium_gradient,
            solution.x,
            xtol=1e-14,
            ftol=1e-14,
            gtol=1e-14,
            max_nfev=10_000,
        )
        residual = float(np.max(np.abs(_equilibrium_gradient(refinement.x))))
        if not refinement.success or residual > 1e-8:
            raise RuntimeError(
                f"ion equilibrium did not converge: {refinement.message}; "
                f"max residual={residual:.3e}"
            )
        positions = np.sort(refinement.x)
    else:
        positions = np.sort(solution.x)
    positions -= np.mean(positions)
    return positions


def axial_modes(number_of_ions: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return positions, normalized axial frequencies, and eigenvectors."""

    positions = equilibrium_positions(number_of_ions)
    if number_of_ions == 1:
        return positions, np.ones(1), np.ones((1, 1))
    delta = positions[:, None] - positions[None, :]
    hessian = np.zeros((number_of_ions, number_of_ions), dtype=float)
    for row in range(number_of_ions):
        for col in range(number_of_ions):
            if row == col:
                hessian[row, row] = 1.0 + sum(
                    2.0 / abs(positions[row] - positions[k]) ** 3
                    for k in range(number_of_ions)
                    if k != row
                )
            else:
                hessian[row, col] = -2.0 / abs(delta[row, col]) ** 3
    eigenvalues, eigenvectors = np.linalg.eigh(hessian)
    frequencies = np.sqrt(np.clip(eigenvalues, 0.0, None))
    return positions, frequencies, eigenvectors


def alternating_amplitudes(segment_count: int, negative_ratio: float = 0.84) -> np.ndarray:
    amplitudes = np.ones(segment_count, dtype=float)
    amplitudes[1::2] = -abs(float(negative_ratio))
    return amplitudes


def _durations_from_logits(logits: np.ndarray, segment_count: int, minimum_fraction: float) -> np.ndarray:
    full_logits = np.concatenate((np.asarray(logits, dtype=float), np.zeros(1)))
    shifted = full_logits - np.max(full_logits)
    weights = np.exp(shifted)
    weights /= np.sum(weights)
    return minimum_fraction + (1.0 - segment_count * minimum_fraction) * weights


def closure_residuals(
    boundaries: np.ndarray,
    amplitudes: np.ndarray,
    normalized_frequencies: np.ndarray,
) -> np.ndarray:
    start = boundaries[:-1]
    stop = boundaries[1:]
    residuals = []
    for frequency in normalized_frequencies:
        phase_step = np.exp(1j * 2.0 * np.pi * frequency * stop) - np.exp(
            1j * 2.0 * np.pi * frequency * start
        )
        residuals.append(np.sum(amplitudes * phase_step))
    return np.asarray(residuals)


def optimize_toggle_schedule(
    normalized_frequencies: np.ndarray,
    segment_count: int = 25,
    negative_ratio: float = 0.84,
    minimum_fraction: float = 0.004,
    seed: int = 260_715_597,
    restarts: int = 12,
) -> ToggleSchedule:
    """Optimize positive segment durations for simultaneous mode closure."""

    frequencies = np.asarray(normalized_frequencies, dtype=float)
    if segment_count * minimum_fraction >= 1.0:
        raise ValueError("minimum segment fractions leave no free duration")
    amplitudes = alternating_amplitudes(segment_count, negative_ratio)
    random = np.random.default_rng(seed)
    best: ToggleSchedule | None = None

    def objective(logits: np.ndarray) -> np.ndarray:
        durations = _durations_from_logits(logits, segment_count, minimum_fraction)
        boundaries = np.concatenate(([0.0], np.cumsum(durations)))
        residual = closure_residuals(boundaries, amplitudes, frequencies)
        return np.concatenate((residual.real, residual.imag))

    starts = [np.zeros(segment_count - 1)]
    starts.extend(random.normal(0.0, 0.8, segment_count - 1) for _ in range(restarts - 1))
    for initial in starts:
        result = least_squares(
            objective,
            initial,
            bounds=(-8.0, 8.0),
            xtol=1e-13,
            ftol=1e-13,
            gtol=1e-13,
            max_nfev=20_000,
        )
        durations = _durations_from_logits(result.x, segment_count, minimum_fraction)
        boundaries = np.concatenate(([0.0], np.cumsum(durations)))
        residual = closure_residuals(boundaries, amplitudes, frequencies)
        candidate = ToggleSchedule(
            boundaries=boundaries,
            amplitudes=amplitudes.copy(),
            residuals=residual,
            cost=float(np.sum(np.abs(residual) ** 2)),
        )
        if best is None or candidate.cost < best.cost:
            best = candidate
        if candidate.cost < 1e-16:
            break
    assert best is not None
    return best


def mode_trajectory(
    sample_fractions: np.ndarray,
    frequency: float,
    schedule: ToggleSchedule,
) -> np.ndarray:
    """Piecewise analytic integral of the toggle force, up to a scale."""

    samples = np.asarray(sample_fractions, dtype=float)
    result = np.zeros(samples.shape, dtype=complex)
    for index, time in np.ndenumerate(samples):
        if not 0.0 <= time <= 1.0:
            raise ValueError("sample fractions must lie in [0, 1]")
        accumulated = 0.0j
        for segment, amplitude in enumerate(schedule.amplitudes):
            start = schedule.boundaries[segment]
            stop = min(time, schedule.boundaries[segment + 1])
            if stop > start:
                accumulated += amplitude * (
                    np.exp(1j * 2.0 * np.pi * frequency * stop)
                    - np.exp(1j * 2.0 * np.pi * frequency * start)
                ) / frequency
            if time <= schedule.boundaries[segment + 1]:
                break
        result[index] = accumulated
    return result
