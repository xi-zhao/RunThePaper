"""Calculated Rydberg-Stark line shapes from the published equations."""

from __future__ import annotations

import numpy as np
from scipy.special import erf

from .constants import CODATA2018


def linear_stark_center_mhz(n: int, k: int, field_v_per_cm: float) -> float:
    """First-order parabolic-state displacement in MHz."""

    field_atomic = field_v_per_cm / CODATA2018.atomic_field_v_per_cm
    return 1.5 * n * k * field_atomic * CODATA2018.hartree_over_h_hz / 1e6


def asymmetric_component(
    frequencies_mhz: np.ndarray,
    center_mhz: float,
    sigma_mhz: float,
    gamma: float,
    orientation: int,
) -> np.ndarray:
    """One Gaussian-error-function component of method Eq. (4)."""

    delta = frequencies_mhz - center_mhz
    gaussian = np.exp(-0.5 * (delta / sigma_mhz) ** 2)
    asymmetry = 1.0 + erf(orientation * gamma * delta / (np.sqrt(2.0) * sigma_mhz))
    return gaussian * asymmetry


def calculated_spectrum(
    frequencies_mhz: np.ndarray,
    *,
    n: int,
    field_v_per_cm: float,
    doppler_shift_mhz: float,
    doppler_sigma_mhz: float,
    field_sigma_mhz: float,
    asymmetry_gamma: float,
) -> tuple[np.ndarray, list[dict[str, float | int]]]:
    """Evaluate the six-peak k=-2,0,+2 theoretical spectrum."""

    frequencies = np.asarray(frequencies_mhz, dtype=float)
    total = np.zeros_like(frequencies)
    component_rows: list[dict[str, float | int]] = []
    k_weights = {-2: 0.92, 0: 1.0, 2: 0.88}
    for k_value in (-2, 0, 2):
        stark_center = linear_stark_center_mhz(n, k_value, field_v_per_cm)
        sigma = np.sqrt(doppler_sigma_mhz**2 + (abs(k_value) * field_sigma_mhz) ** 2)
        for component_index, orientation in enumerate((-1, 1), start=1):
            doppler_center = (-1 if component_index == 1 else 1) * doppler_shift_mhz
            center = stark_center + doppler_center
            component = k_weights[k_value] * asymmetric_component(
                frequencies,
                center,
                sigma,
                asymmetry_gamma,
                orientation,
            )
            total += component
            component_rows.append(
                {
                    "k": k_value,
                    "component": component_index,
                    "center_mhz": center,
                    "sigma_mhz": sigma,
                    "orientation": orientation,
                }
            )
    maximum = float(np.max(total))
    if maximum <= 0:
        raise ValueError("calculated spectrum has no positive intensity")
    return total / maximum, component_rows


def mirror_symmetry_error(frequencies_mhz: np.ndarray, intensity: np.ndarray) -> float:
    """Relative RMS reflection error around zero frequency."""

    frequencies = np.asarray(frequencies_mhz, dtype=float)
    values = np.asarray(intensity, dtype=float)
    reflected = np.interp(-frequencies, frequencies, values)
    scale = max(float(np.sqrt(np.mean(values**2))), np.finfo(float).eps)
    return float(np.sqrt(np.mean((values - reflected) ** 2)) / scale)
