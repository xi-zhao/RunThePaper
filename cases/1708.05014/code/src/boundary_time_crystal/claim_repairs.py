"""Independent implementations for atomic claims omitted by the legacy case."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

import numpy as np
from scipy.optimize import least_squares

from .model import magnetization_dynamics, semiclassical_rhs


@dataclass(frozen=True)
class DampedOscillationFit:
    offset: float
    cosine_amplitude: float
    sine_amplitude: float
    eta: float
    angular_frequency: float
    r_squared: float
    root_mean_square_residual: float
    fit_minimum_time: float
    fit_points: int


def fit_damped_oscillation(
    times: np.ndarray,
    values: np.ndarray,
    *,
    fit_minimum_time: float,
    maximum_function_evaluations: int = 4000,
) -> tuple[DampedOscillationFit, np.ndarray]:
    """Fit ``c + exp(-eta t) [a cos(wt) + b sin(wt)]`` to a frozen window.

    The frequency seed comes only from the generated time series.  No
    Liouvillian eigenvalue or paper curve is used to choose ``eta``.
    """

    times = np.asarray(times, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    if times.ndim != 1 or values.shape != times.shape or times.size < 20:
        raise ValueError("times and values must be matching one-dimensional arrays")
    if np.any(~np.isfinite(times)) or np.any(~np.isfinite(values)):
        raise ValueError("fit inputs must be finite")
    if np.any(np.diff(times) <= 0.0):
        raise ValueError("times must be strictly increasing")

    mask = times >= float(fit_minimum_time)
    if int(np.count_nonzero(mask)) < 20:
        raise ValueError("fit window must contain at least 20 samples")
    fit_times = times[mask]
    fit_values = values[mask]
    local_times = fit_times - fit_times[0]
    time_step = float(np.median(np.diff(local_times)))
    span = float(local_times[-1])

    late_points = max(5, fit_values.size // 10)
    offset_seed = float(np.mean(fit_values[-late_points:]))
    centered = fit_values - offset_seed
    spectrum = np.abs(np.fft.rfft(centered - np.mean(centered)))
    frequencies = np.fft.rfftfreq(fit_values.size, time_step)
    peak_index = int(np.argmax(spectrum[1:]) + 1)
    omega_seed = max(2.0 * np.pi * float(frequencies[peak_index]), 1e-4)
    eta_seed = max(1.0 / max(span, 1.0), 1e-4)

    minimum_omega = max(0.25 * 2.0 * np.pi / span, 1e-5)
    maximum_omega = np.pi / time_step
    initial = np.asarray(
        [
            offset_seed,
            float(centered[0]),
            0.0,
            np.log(eta_seed),
            np.log(omega_seed),
        ]
    )
    lower = np.asarray([-1.5, -2.0, -2.0, np.log(1e-8), np.log(minimum_omega)])
    upper = np.asarray([1.5, 2.0, 2.0, np.log(10.0), np.log(maximum_omega)])
    initial = np.clip(initial, lower + 1e-12, upper - 1e-12)

    def model(parameters: np.ndarray, sample_times: np.ndarray) -> np.ndarray:
        offset, cosine, sine, log_eta, log_omega = parameters
        eta = np.exp(log_eta)
        omega = np.exp(log_omega)
        envelope = np.exp(-eta * sample_times)
        return offset + envelope * (
            cosine * np.cos(omega * sample_times)
            + sine * np.sin(omega * sample_times)
        )

    result = least_squares(
        lambda parameters: model(parameters, local_times) - fit_values,
        initial,
        bounds=(lower, upper),
        max_nfev=int(maximum_function_evaluations),
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
    )
    prediction = model(result.x, local_times)
    residual = prediction - fit_values
    residual_sum = float(np.sum(residual**2))
    total_sum = float(np.sum((fit_values - np.mean(fit_values)) ** 2))
    r_squared = 1.0 - residual_sum / total_sum if total_sum > 0.0 else 1.0
    fit = DampedOscillationFit(
        offset=float(result.x[0]),
        cosine_amplitude=float(result.x[1]),
        sine_amplitude=float(result.x[2]),
        eta=float(np.exp(result.x[3])),
        angular_frequency=float(np.exp(result.x[4])),
        r_squared=r_squared,
        root_mean_square_residual=float(np.sqrt(np.mean(residual**2))),
        fit_minimum_time=float(fit_minimum_time),
        fit_points=int(fit_values.size),
    )
    full_prediction = np.full_like(values, np.nan)
    full_prediction[mask] = prediction
    return fit, full_prediction


def estimate_eta_profile(
    profile: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate dynamics and fit eta independently for every declared N."""

    kappa = float(profile["kappa"])
    omega_0 = float(profile["omega0_over_kappa"]) * kappa
    time_contract = profile["time"]
    times = np.linspace(
        float(time_contract["minimum"]),
        float(time_contract["maximum"]),
        int(time_contract["points"]),
    )
    summary_rows: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    for number_spins in profile["N"]:
        number_spins = int(number_spins)
        values = magnetization_dynamics(number_spins, omega_0, times, kappa)
        fit, prediction = fit_damped_oscillation(
            times,
            values,
            fit_minimum_time=float(profile["fit_minimum_time"]),
            maximum_function_evaluations=int(profile["maximum_function_evaluations"]),
        )
        summary_rows.append(
            {
                "N": number_spins,
                "inverse_N": 1.0 / number_spins,
                "eta_from_magnetization_fit": fit.eta / kappa,
                "angular_frequency_over_kappa": fit.angular_frequency / kappa,
                "fit_r_squared": fit.r_squared,
                "fit_rms_residual": fit.root_mean_square_residual,
                "fit_minimum_time": fit.fit_minimum_time,
                "fit_points": fit.fit_points,
                "observable": "magnetization_dynamics",
            }
        )
        for time_value, magnetization, fitted in zip(times, values, prediction, strict=True):
            trace_rows.append(
                {
                    "N": number_spins,
                    "time": float(time_value),
                    "magnetization_z_over_N": float(magnetization),
                    "fit_prediction": None if np.isnan(fitted) else float(fitted),
                    "in_fit_window": bool(time_value >= fit.fit_minimum_time),
                }
            )
    return summary_rows, trace_rows


def _fixed_point_rows(
    *,
    omega_0: float,
    kappa: float,
    omega_z: float,
    formula: str,
) -> list[dict[str, Any]]:
    denominator_squared = kappa**2 + 4.0 * omega_z**2
    if formula == "rederived":
        denominator = denominator_squared
        mz_squared = 1.0 - omega_0**2 / denominator_squared
    elif formula == "printed_s17":
        denominator = np.sqrt(denominator_squared)
        mz_squared = 1.0 - omega_0**2 / np.sqrt(denominator_squared)
    else:
        raise ValueError(formula)
    if mz_squared < 0.0:
        raise ValueError("declared point lies below the non-trivial fixed-point threshold")
    mx = 2.0 * omega_z * omega_0 / denominator
    my = kappa * omega_0 / denominator
    rows: list[dict[str, Any]] = []
    for branch in (-1.0, 1.0):
        point = np.asarray([mx, my, branch * np.sqrt(mz_squared)], dtype=np.float64)
        rhs = semiclassical_rhs(
            0.0,
            point,
            omega_0=omega_0,
            kappa=kappa,
            omega_x=0.0,
            omega_z=omega_z,
        )
        rows.append(
            {
                "formula": formula,
                "branch": "minus" if branch < 0.0 else "plus",
                "m_x": float(point[0]),
                "m_y": float(point[1]),
                "m_z": float(point[2]),
                "unit_norm_residual": float(abs(np.dot(point, point) - 1.0)),
                "rhs_max_abs_residual": float(np.max(np.abs(rhs))),
            }
        )
    return rows


def analyze_s17_fixed_points(parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Substitute printed and independently rederived S17 points into S13."""

    omega_0 = float(parameters["omega_0"])
    kappa = float(parameters["kappa"])
    omega_z = float(parameters["omega_z"])
    tolerance = float(parameters["residual_tolerance"])
    rows = [
        *_fixed_point_rows(
            omega_0=omega_0,
            kappa=kappa,
            omega_z=omega_z,
            formula="rederived",
        ),
        *_fixed_point_rows(
            omega_0=omega_0,
            kappa=kappa,
            omega_z=omega_z,
            formula="printed_s17",
        ),
    ]
    rederived = [row for row in rows if row["formula"] == "rederived"]
    printed = [row for row in rows if row["formula"] == "printed_s17"]
    threshold = 0.5 * np.sqrt(max(0.0, omega_0**2 - kappa**2))
    expected_threshold = float(parameters["expected_transition_omega_z"])
    checks = {
        "rederived_rhs_passes": bool(
            max(row["rhs_max_abs_residual"] for row in rederived) <= tolerance
        ),
        "rederived_unit_norm_passes": bool(
            max(row["unit_norm_residual"] for row in rederived) <= tolerance
        ),
        "printed_formula_is_inconsistent": bool(
            max(
                max(row["rhs_max_abs_residual"], row["unit_norm_residual"])
                for row in printed
            )
            > 100.0 * tolerance
        ),
        "transition_value_matches_following_text": bool(
            abs(threshold - expected_threshold) <= tolerance
        ),
    }
    return {
        "schema_version": 1,
        "target_id": "T026",
        "status": "passed" if all(checks.values()) else "failed",
        "paper_formula_consistency": "discrepancy_observed",
        "paper_error_candidate_emitted": False,
        "fresh_review_required": True,
        "source_pixels_used_in_generation": False,
        "author_arrays_used_in_generation": False,
        "parameters": dict(parameters),
        "correct_transition_omega_z": float(threshold),
        "checks": checks,
        "rows": rows,
    }


def fit_as_dict(fit: DampedOscillationFit) -> dict[str, float | int]:
    return asdict(fit)
