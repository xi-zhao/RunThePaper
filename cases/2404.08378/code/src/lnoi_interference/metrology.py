"""Independent calculations behind the HOM and brightness claims."""

from __future__ import annotations

import numpy as np

from .quantum import spectrum_weighted_hom_visibility

SPEED_OF_LIGHT_M_PER_S = 299_792_458.0


def hom_delay_curve(
    delay_fs: np.ndarray,
    *,
    baseline_hz: float,
    visibility: float,
    fwhm_fs: float,
) -> np.ndarray:
    """Gaussian HOM dip parameterized by its full width at half minimum."""

    delay_fs = np.asarray(delay_fs, dtype=float)
    if baseline_hz <= 0.0 or fwhm_fs <= 0.0 or not 0.0 <= visibility <= 1.0:
        raise ValueError("invalid HOM parameters")
    envelope = np.exp(-4.0 * np.log(2.0) * (delay_fs / fwhm_fs) ** 2)
    return baseline_hz * (1.0 - visibility * envelope)


def wavelength_from_frequency_bandwidth(
    frequency_hz: float, central_wavelength_nm: float
) -> float:
    wavelength_m = central_wavelength_nm * 1e-9
    return float(frequency_hz * wavelength_m**2 / SPEED_OF_LIGHT_M_PER_S * 1e9)


def hom_bandwidth_conventions(
    width_fs: float, central_wavelength_nm: float = 1562.0
) -> dict[str, float]:
    """Expose the width-convention ambiguity instead of hiding it."""

    width_seconds = float(width_fs) * 1e-15
    conventional_frequency = 0.441 / width_seconds
    hom_autocorrelation_frequency = (
        2.0 * np.sqrt(2.0) * np.log(2.0) / np.pi
    ) / width_seconds
    return {
        "width_fs": float(width_fs),
        "central_wavelength_nm": float(central_wavelength_nm),
        "pulse_tbp_0p441_bandwidth_thz": float(conventional_frequency / 1e12),
        "pulse_tbp_0p441_bandwidth_nm": wavelength_from_frequency_bandwidth(
            conventional_frequency, central_wavelength_nm
        ),
        "hom_autocorrelation_bandwidth_thz": float(
            hom_autocorrelation_frequency / 1e12
        ),
        "hom_autocorrelation_bandwidth_nm": wavelength_from_frequency_bandwidth(
            hom_autocorrelation_frequency, central_wavelength_nm
        ),
    }


def brightness_audit(
    detected_pairs_per_s: float,
    loss_db_per_photon: float,
    pump_power_uw: float,
    printed_normalized_brightness: float,
) -> dict[str, float]:
    """Undo per-photon loss for a two-photon coincidence and normalize by pump."""

    source_pairs_per_s = float(detected_pairs_per_s) * 10.0 ** (
        2.0 * float(loss_db_per_photon) / 10.0
    )
    brightness = source_pairs_per_s / (float(pump_power_uw) / 1000.0)
    implied_bandwidth_nm = brightness / float(printed_normalized_brightness)
    return {
        "detected_pairs_per_s": float(detected_pairs_per_s),
        "loss_db_per_photon": float(loss_db_per_photon),
        "pump_power_uw": float(pump_power_uw),
        "source_pairs_per_s": source_pairs_per_s,
        "brightness_pairs_per_s_per_mw": brightness,
        "printed_normalized_brightness_pairs_per_s_per_nm_per_mw": float(
            printed_normalized_brightness
        ),
        "bandwidth_implied_by_two_printed_brightness_values_nm": implied_bandwidth_nm,
    }


def conjugate_wavelength_nm(
    signal_nm: np.ndarray, pump_nm: float = 781.0
) -> np.ndarray:
    signal_nm = np.asarray(signal_nm, dtype=float)
    denominator = 1.0 / float(pump_nm) - 1.0 / signal_nm
    if np.any(denominator <= 0.0):
        raise ValueError("signal wavelengths must exceed the pump wavelength")
    return 1.0 / denominator


def printed_endpoint_reflectivity(
    wavelength_nm: np.ndarray, *, device: str
) -> np.ndarray:
    """Linear reconstruction from the only printed S5(a) endpoint values."""

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    endpoints = {
        "fiber": (0.532, 0.365),
        "lnoi": (0.535, 0.481),
    }
    if device not in endpoints:
        raise ValueError(f"unknown device: {device}")
    low, high = endpoints[device]
    reflectivity = low + (high - low) * (wavelength_nm - 1540.0) / 40.0
    return np.clip(reflectivity, 1e-6, 1.0 - 1e-6)


def reconstructed_grating_transmission(wavelength_nm: np.ndarray) -> np.ndarray:
    """Declared Gaussian reconstruction of the printed -7/-10 dB anchors."""

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    center_nm = 1530.0
    sigma_nm = 32.0 / np.sqrt(2.0 * np.log(2.0))
    relative = np.exp(-0.5 * ((wavelength_nm - center_nm) / sigma_nm) ** 2)
    return 10.0 ** (-7.0 / 10.0) * relative


def reconstructed_spectral_visibility(
    wavelength_nm: np.ndarray, *, device: str
) -> dict[str, np.ndarray | float]:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    idler_nm = conjugate_wavelength_nm(wavelength_nm)
    signal_reflectivity = printed_endpoint_reflectivity(wavelength_nm, device=device)
    idler_reflectivity = printed_endpoint_reflectivity(idler_nm, device=device)
    weights = reconstructed_grating_transmission(
        wavelength_nm
    ) * reconstructed_grating_transmission(idler_nm)
    visibility = spectrum_weighted_hom_visibility(
        signal_reflectivity, idler_reflectivity, weights
    )
    return {
        "signal_wavelength_nm": wavelength_nm,
        "idler_wavelength_nm": idler_nm,
        "signal_reflectivity": signal_reflectivity,
        "idler_reflectivity": idler_reflectivity,
        "pair_weight": weights,
        "visibility": visibility,
    }
