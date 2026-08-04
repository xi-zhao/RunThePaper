"""Independent numerics for arXiv:1904.10246v2.

The source panels are never read here.  This module implements only the
paper-derived probability model, likelihood, schedules, analytic bounds, and
resource formulas.  Plotting and target-scoped file writes live in the guarded
runner.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np


PAPER_AMPLITUDES = (2 / 3, 1 / 3, 1 / 6, 1 / 12, 1 / 24, 1 / 48)
PAPER_FIG2_REPETITIONS = 1000
PAPER_FIG2_SHOTS = 100
PAPER_PERCENTILE = 100.0 * 8.0 / math.pi**2


def amplified_probability(a: float, m: int | np.ndarray) -> np.ndarray:
    """Return sin^2((2m+1) asin(sqrt(a)))."""
    if not 0.0 <= float(a) <= 1.0:
        raise ValueError("a must lie in [0, 1]")
    depths = np.asarray(m, dtype=np.int64)
    if np.any(depths < 0):
        raise ValueError("amplification depths must be non-negative")
    theta = math.asin(math.sqrt(float(a)))
    return np.sin((2 * depths + 1) * theta) ** 2


def lis_schedule(maximum_m: int) -> np.ndarray:
    if maximum_m < 0:
        raise ValueError("maximum_m must be non-negative")
    return np.arange(maximum_m + 1, dtype=np.int64)


def eis_schedule(maximum_stage: int) -> np.ndarray:
    if maximum_stage < 0:
        raise ValueError("maximum_stage must be non-negative")
    if maximum_stage == 0:
        return np.array([0], dtype=np.int64)
    return np.array([0, *(2 ** np.arange(maximum_stage, dtype=np.int64))], dtype=np.int64)


def query_count(schedule: Iterable[int], shots: int | Iterable[int]) -> int:
    depths = np.asarray(list(schedule), dtype=np.int64)
    shot_values = _shot_array(shots, len(depths))
    return int(np.sum(shot_values * (2 * depths + 1)))


def fisher_information(a: float, schedule: Iterable[int], shots: int | Iterable[int]) -> float:
    if not 0.0 < float(a) < 1.0:
        raise ValueError("Fisher information requires 0 < a < 1")
    depths = np.asarray(list(schedule), dtype=np.int64)
    shot_values = _shot_array(shots, len(depths))
    weights = 2 * depths + 1
    return float(np.sum(shot_values * weights**2) / (float(a) * (1.0 - float(a))))


def cramer_rao_error(a: float, schedule: Iterable[int], shots: int | Iterable[int]) -> float:
    return 1.0 / math.sqrt(fisher_information(a, schedule, shots))


def _shot_array(shots: int | Iterable[int], size: int) -> np.ndarray:
    if np.isscalar(shots):
        values = np.full(size, int(shots), dtype=np.int64)
    else:
        values = np.asarray(list(shots), dtype=np.int64)
    if values.shape != (size,) or np.any(values <= 0):
        raise ValueError("shots must be positive and match the schedule length")
    return values


def cumulative_mle_amplitudes(
    counts: np.ndarray,
    schedule: Iterable[int],
    shots: int | Iterable[int],
    *,
    grid_size: int,
    batch_size: int = 32,
) -> np.ndarray:
    """Global-grid MLE for every cumulative schedule prefix.

    A fine full-domain grid avoids using the known target amplitude as an
    initializer.  Quadratic interpolation of the winning grid point and its
    neighbors removes visible grid quantization without changing which global
    basin wins.
    """
    count_values = np.asarray(counts, dtype=np.int64)
    depths = np.asarray(list(schedule), dtype=np.int64)
    shot_values = _shot_array(shots, len(depths))
    if count_values.ndim != 2 or count_values.shape[1] != len(depths):
        raise ValueError("counts must have shape (repetitions, schedule_length)")
    if np.any(count_values < 0) or np.any(count_values > shot_values[None, :]):
        raise ValueError("counts must lie between zero and their shot counts")
    if grid_size < 1025 or grid_size % 2 == 0:
        raise ValueError("grid_size must be an odd integer >= 1025")

    endpoint = 1e-10
    theta_grid = np.linspace(endpoint, math.pi / 2 - endpoint, grid_size, dtype=np.float64)
    step = float(theta_grid[1] - theta_grid[0])
    query_weights = 2 * depths + 1
    probabilities = np.sin(query_weights[:, None] * theta_grid[None, :]) ** 2
    probabilities = np.clip(probabilities, 1e-15, 1.0 - 1e-15)
    log_p = np.log(probabilities)
    log_one_minus_p = np.log1p(-probabilities)

    estimates = np.empty(count_values.shape, dtype=np.float64)
    for start in range(0, count_values.shape[0], batch_size):
        stop = min(start + batch_size, count_values.shape[0])
        batch = count_values[start:stop]
        log_likelihood = np.zeros((stop - start, grid_size), dtype=np.float64)
        row_indices = np.arange(stop - start)

        for column in range(len(depths)):
            hits = batch[:, column].astype(np.float64)
            misses = shot_values[column] - hits
            log_likelihood += (
                hits[:, None] * log_p[column][None, :]
                + misses[:, None] * log_one_minus_p[column][None, :]
            )
            winner = np.argmax(log_likelihood, axis=1)
            refined_theta = theta_grid[winner].copy()
            interior = (winner > 0) & (winner < grid_size - 1)
            if np.any(interior):
                rows = row_indices[interior]
                centers = winner[interior]
                left = log_likelihood[rows, centers - 1]
                middle = log_likelihood[rows, centers]
                right = log_likelihood[rows, centers + 1]
                denominator = left - 2.0 * middle + right
                offsets = np.zeros_like(middle)
                usable = np.abs(denominator) > 1e-14
                offsets[usable] = 0.5 * (left[usable] - right[usable]) / denominator[usable]
                offsets = np.clip(offsets, -1.0, 1.0)
                refined_theta[interior] += offsets * step
            estimates[start:stop, column] = np.sin(refined_theta) ** 2
    return estimates


@dataclass(frozen=True)
class SchedulePoint:
    stage: int
    n_query: int
    error: float
    cramer_rao: float


def simulate_schedule_curve(
    *,
    a: float,
    schedule: np.ndarray,
    shots: int,
    repetitions: int,
    rng: np.random.Generator,
    grid_size: int,
    statistic: str,
    percentile: float = PAPER_PERCENTILE,
) -> list[SchedulePoint]:
    probabilities = amplified_probability(a, schedule)
    counts = rng.binomial(shots, probabilities, size=(repetitions, len(schedule)))
    estimates = cumulative_mle_amplitudes(
        counts,
        schedule,
        shots,
        grid_size=grid_size,
    )
    points: list[SchedulePoint] = []
    for stage in range(len(schedule)):
        prefix = schedule[: stage + 1]
        absolute_errors = np.abs(estimates[:, stage] - a)
        if statistic == "rmse":
            error = float(np.sqrt(np.mean(absolute_errors**2)))
        elif statistic == "percentile":
            error = float(np.percentile(absolute_errors, percentile))
        else:
            raise ValueError(f"unsupported statistic: {statistic}")
        points.append(
            SchedulePoint(
                stage=stage,
                n_query=query_count(prefix, shots),
                error=error,
                cramer_rao=cramer_rao_error(a, prefix, shots),
            )
        )
    return points


def classical_curve(
    *,
    a: float,
    query_counts: Iterable[int],
    repetitions: int,
    rng: np.random.Generator,
    statistic: str,
    percentile: float = PAPER_PERCENTILE,
) -> list[SchedulePoint]:
    points: list[SchedulePoint] = []
    for stage, n_query in enumerate(query_counts):
        n_query = int(n_query)
        counts = rng.binomial(n_query, a, size=repetitions)
        errors = np.abs(counts / n_query - a)
        if statistic == "rmse":
            error = float(np.sqrt(np.mean(errors**2)))
        elif statistic == "percentile":
            error = float(np.percentile(errors, percentile))
        else:
            raise ValueError(f"unsupported statistic: {statistic}")
        points.append(
            SchedulePoint(
                stage=stage,
                n_query=n_query,
                error=error,
                cramer_rao=math.sqrt(a * (1.0 - a) / n_query),
            )
        )
    return points


def fitted_log_slope(points: Iterable[SchedulePoint], minimum: float, maximum: float) -> float:
    selected = [point for point in points if minimum <= point.n_query <= maximum and point.error > 0]
    if len(selected) < 2:
        raise ValueError("at least two points are needed for a log slope")
    x = np.log10([point.n_query for point in selected])
    y = np.log10([point.error for point in selected])
    return float(np.polyfit(x, y, 1)[0])


def complexity_rows() -> list[dict[str, str]]:
    return [
        {
            "method": "Classical",
            "schedule": "m_k=0 for all k",
            "query_complexity": "O(epsilon^-2)",
            "postprocessing_complexity": "O(epsilon^-2)",
        },
        {
            "method": "Linearly incremental sequence (LIS)",
            "schedule": "m_k=k",
            "query_complexity": "O(epsilon^-4/3)",
            "postprocessing_complexity": "O(epsilon^-5/3)",
        },
        {
            "method": "Exponentially incremental sequence (EIS)",
            "schedule": "m_0=0; m_k=2^(k-1)",
            "query_complexity": "O(epsilon^-1)",
            "postprocessing_complexity": "O(epsilon^-1 log(epsilon^-1))",
        },
    ]


PAPER_RESOURCE_REFERENCE = (
    (0, None, None, 4, 3),
    (1, 135, 7, 18, 3),
    (2, 399, 8, 32, 3),
    (4, 927, 9, 60, 3),
    (8, 1981, 10, 116, 3),
    (16, 4085, 11, 228, 3),
    (32, 8287, 12, 452, 3),
    (64, 16683, 13, 900, 3),
    (128, 33465, 14, 1796, 3),
    (256, 67017, 15, 3588, 3),
)


def resource_rows() -> list[dict[str, int | None]]:
    rows: list[dict[str, int | None]] = [
        {
            "q_operators": 0,
            "conventional_cnot": None,
            "conventional_qubits": None,
            "proposed_cnot": 4,
            "proposed_qubits": 3,
        }
    ]
    for exponent in range(9):
        q_operators = 2**exponent
        rows.append(
            {
                "q_operators": q_operators,
                "conventional_cnot": 262 * q_operators - 127 + exponent * (exponent + 1),
                "conventional_qubits": 7 + exponent,
                "proposed_cnot": 14 * q_operators + 4,
                "proposed_qubits": 3,
            }
        )
    return rows


def conventional_qae_error(a: float, phase_bits: int) -> tuple[int, float]:
    if phase_bits < 2:
        raise ValueError("phase_bits must be at least 2")
    theta = math.asin(math.sqrt(a))
    maximum_q = 2**phase_bits - 1
    location = theta * maximum_q / math.pi
    candidates: set[int] = set()
    for center in (location, maximum_q - location):
        candidates.add(max(0, min(maximum_q, math.floor(center))))
        candidates.add(max(0, min(maximum_q, math.ceil(center))))
    candidate_errors = [
        abs(math.sin(math.pi * candidate / maximum_q) ** 2 - a)
        for candidate in candidates
    ]
    return maximum_q, max(candidate_errors)


def assert_resource_reference() -> None:
    generated = resource_rows()
    tuples = tuple(
        (
            int(row["q_operators"]),
            row["conventional_cnot"],
            row["conventional_qubits"],
            int(row["proposed_cnot"]),
            int(row["proposed_qubits"]),
        )
        for row in generated
    )
    if tuples != PAPER_RESOURCE_REFERENCE:
        raise AssertionError(f"resource rows differ from the frozen table: {tuples!r}")
