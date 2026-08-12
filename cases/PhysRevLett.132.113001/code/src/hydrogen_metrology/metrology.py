"""Decimal arithmetic and uncertainty propagation for the metrology claims."""

from __future__ import annotations

from decimal import Decimal, getcontext
from math import sqrt
from typing import Iterable

import numpy as np

getcontext().prec = 40


def quadrature(values: Iterable[float]) -> float:
    return sqrt(sum(float(value) ** 2 for value in values))


def table_i_rows() -> list[dict[str, float | str]]:
    """Printed correction and uncertainty entries from main Table I."""

    return [
        {
            "name": "first_order_doppler",
            "correction_khz": 0.0,
            "stat_khz": 2.4,
            "syst_khz": 0.0,
        },
        {
            "name": "second_order_doppler",
            "correction_khz": 4.5,
            "stat_khz": 0.0,
            "syst_khz": 0.12,
        },
        {
            "name": "quadratic_stark",
            "correction_khz": 0.0,
            "stat_khz": 1.6,
            "syst_khz": 0.0,
        },
        {
            "name": "thermal_ac_stark",
            "correction_khz": -2.2,
            "stat_khz": 0.0,
            "syst_khz": 1.1,
        },
        {"name": "zeeman", "correction_khz": 0.0, "stat_khz": 0.0, "syst_khz": 0.56},
        {"name": "pressure", "correction_khz": 0.0, "stat_khz": 0.0, "syst_khz": 0.05},
        {
            "name": "photon_recoil_n20",
            "correction_khz": -1458.8,
            "stat_khz": 0.0,
            "syst_khz": 0.0,
        },
        {
            "name": "photon_recoil_n24",
            "correction_khz": -1467.8,
            "stat_khz": 0.0,
            "syst_khz": 0.0,
        },
    ]


def uncertainty_closure(
    rows: list[dict[str, float | str]],
    *,
    reported_stat_khz: float,
    reported_syst_khz: float,
) -> dict[str, float]:
    listed_stat = quadrature(float(row["stat_khz"]) for row in rows)
    listed_syst = quadrature(float(row["syst_khz"]) for row in rows)
    residual_stat = sqrt(max(reported_stat_khz**2 - listed_stat**2, 0.0))
    residual_syst = sqrt(max(reported_syst_khz**2 - listed_syst**2, 0.0))
    return {
        "listed_stat_khz": listed_stat,
        "listed_syst_khz": listed_syst,
        "reported_stat_khz": reported_stat_khz,
        "reported_syst_khz": reported_syst_khz,
        "unlisted_statistical_component_khz": residual_stat,
        "unlisted_systematic_component_khz": residual_syst,
    }


def binding_frequency_from_printed_inputs() -> dict[str, str]:
    """Assemble the ground-state binding frequency without float rounding."""

    ionization_2s_khz = Decimal("822025399526.6")
    transition_2s_1s_khz = Decimal("2466061102474.796")
    hyperfine_1s_khz = Decimal("1420405.7517667")
    assembled = ionization_2s_khz + transition_2s_1s_khz + hyperfine_1s_khz
    paper_value = Decimal("3288087922407.2")
    return {
        "ionization_2s_khz": str(ionization_2s_khz),
        "transition_2s_1s_khz": str(transition_2s_1s_khz),
        "hyperfine_1s_khz": str(hyperfine_1s_khz),
        "assembled_khz": str(assembled),
        "paper_khz": str(paper_value),
        "paper_minus_assembled_hz": str((paper_value - assembled) * Decimal(1000)),
    }


def regression_curves(
    field_grid_v_per_cm: np.ndarray,
    doppler_grid_mhz: np.ndarray,
) -> dict[str, np.ndarray]:
    """Published Appendix A models and parameter-only uncertainty bands."""

    fields = np.asarray(field_grid_v_per_cm, dtype=float)
    doppler = np.asarray(doppler_grid_mhz, dtype=float)
    b_khz_per_field2 = -0.3
    sigma_b = 3.5
    a_khz_per_mhz = -0.9
    sigma_a = 1.8
    return {
        "field": fields,
        "field_trend_khz": b_khz_per_field2 * fields**2,
        "field_band_khz": sigma_b * fields**2,
        "doppler": doppler,
        "doppler_trend_khz": a_khz_per_mhz * doppler,
        "doppler_band_khz": sigma_a * doppler,
    }


def table_ii_rows() -> list[dict[str, float | str]]:
    """Published scalar inputs of main Table II."""

    return [
        {"method": "29c-30c", "frequency_khz": 3_289_841_960_306.0, "sigma_khz": 69.0},
        {
            "method": "2S-4P + 2S-2P",
            "frequency_khz": 3_289_841_960_226.0,
            "sigma_khz": 29.0,
        },
        {
            "method": "2S-8D + 2S-2P",
            "frequency_khz": 3_289_841_960_268.0,
            "sigma_khz": 22.0,
        },
        {
            "method": "2S-high-n",
            "frequency_khz": 3_289_841_960_204.0,
            "sigma_khz": 35.0,
        },
        {
            "method": "CODATA 2010",
            "frequency_khz": 3_289_841_960_365.0,
            "sigma_khz": 16.0,
        },
        {
            "method": "CODATA 2018",
            "frequency_khz": 3_289_841_960_250.8,
            "sigma_khz": 6.4,
        },
    ]


def sigma_separation(
    first_value: float,
    first_sigma: float,
    second_value: float,
    second_sigma: float,
    *,
    convention: str,
) -> float:
    delta = abs(first_value - second_value)
    if convention == "combined":
        denominator = quadrature((first_sigma, second_sigma))
    elif convention == "first_only":
        denominator = first_sigma
    else:
        raise ValueError("convention must be combined or first_only")
    return delta / denominator


def literature_points() -> list[dict[str, float | str]]:
    """Published scalar results used to rebuild the Fig. 4 science plane."""

    return [
        {
            "label": "2S-4P",
            "rp_fm": 0.8335,
            "rp_sigma_fm": 0.0095,
            "rydberg_m_inv": 10973731.568076,
            "rydberg_sigma_m_inv": 0.000096,
        },
        {
            "label": "1S-3S 2018",
            "rp_fm": 0.8770,
            "rp_sigma_fm": 0.0130,
            "rydberg_m_inv": 10973731.568530,
            "rydberg_sigma_m_inv": 0.000140,
        },
        {
            "label": "1S-3S 2020",
            "rp_fm": 0.8482,
            "rp_sigma_fm": 0.0038,
            "rydberg_m_inv": 10973731.568226,
            "rydberg_sigma_m_inv": 0.000038,
        },
        {
            "label": "2S-8D",
            "rp_fm": 0.8584,
            "rp_sigma_fm": 0.0051,
            "rydberg_m_inv": 10973731.568332,
            "rydberg_sigma_m_inv": 0.000052,
        },
        {
            "label": "this work + 1S-2S",
            "rp_fm": 0.8220,
            "rp_sigma_fm": 0.0130,
            "rydberg_frequency_khz": 3_289_841_960_194.0,
            "rydberg_frequency_sigma_khz": 40.0,
        },
        {
            "label": "this work + muH",
            "rp_fm": 0.84087,
            "rp_sigma_fm": 0.00039,
            "rydberg_frequency_khz": 3_289_841_960_214.0,
            "rydberg_frequency_sigma_khz": 22.0,
        },
    ]


def normalized_literature_points() -> list[dict[str, float | str]]:
    """Normalize published results to CODATA 2018, as in Fig. 4."""

    rp0 = 0.8414
    rp_sigma0 = 0.0019
    rydberg0_m_inv = 10973731.568160
    rydberg_sigma0_m_inv = 0.000021
    c_m_per_s = 299_792_458.0
    rows: list[dict[str, float | str]] = []
    for point in literature_points():
        if "rydberg_m_inv" in point:
            y_value = (
                float(point["rydberg_m_inv"]) - rydberg0_m_inv
            ) / rydberg_sigma0_m_inv
            y_sigma = float(point["rydberg_sigma_m_inv"]) / rydberg_sigma0_m_inv
        else:
            center_khz = rydberg0_m_inv * c_m_per_s / 1e3
            sigma_khz = rydberg_sigma0_m_inv * c_m_per_s / 1e3
            y_value = (float(point["rydberg_frequency_khz"]) - center_khz) / sigma_khz
            y_sigma = float(point["rydberg_frequency_sigma_khz"]) / sigma_khz
        rows.append(
            {
                "label": str(point["label"]),
                "x": (float(point["rp_fm"]) - rp0) / rp_sigma0,
                "x_sigma": float(point["rp_sigma_fm"]) / rp_sigma0,
                "y": y_value,
                "y_sigma": y_sigma,
            }
        )
    return rows
