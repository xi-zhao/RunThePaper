"""Code-fault checks for the formula-only Figure 2 dispersion surrogate.

These checks validate the implementation and its ultraviolet continuation.
They do not supply the unpublished fibre fit or turn the surrogate into a
paper-exact reproduction.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch

from .physical_dispersion import (
    C_NM_PER_FS,
    CleanRoomPCFDispersion,
    PCFGeometry,
    fused_silica_index,
)


_B = (0.6961663, 0.4079426, 0.8974794)
_C = (0.0684043**2, 0.1162414**2, 9.896161**2)


def _sellmeier_oracle(wavelength_um: float) -> float:
    squared = wavelength_um * wavelength_um
    value = 1.0 + sum(
        coefficient * squared / (squared - resonance)
        for coefficient, resonance in zip(_B, _C, strict=True)
    )
    return math.sqrt(value)


def _effective_index_oracle(wavelength_um: float, geometry: PCFGeometry) -> float:
    material = _sellmeier_oracle(wavelength_um)
    transverse = (
        geometry.mode_root
        * wavelength_um
        / (2.0 * math.pi * geometry.effective_core_radius_um)
    )
    return math.sqrt(material * material - transverse * transverse)


def _group_index_oracle(wavelength_um: float, geometry: PCFGeometry) -> float:
    step = max(1e-7, wavelength_um * 1e-5)
    derivative = (
        _effective_index_oracle(wavelength_um + step, geometry)
        - _effective_index_oracle(wavelength_um - step, geometry)
    ) / (2.0 * step)
    return _effective_index_oracle(wavelength_um, geometry) - wavelength_um * derivative


def _dispersion_backend_check(parameters: dict[str, Any]) -> dict[str, Any]:
    geometry = PCFGeometry(**parameters["geometry"])
    model = CleanRoomPCFDispersion(geometry)
    wavelengths = np.asarray(parameters["wavelengths_um"], dtype=float)
    torch_wavelengths = torch.as_tensor(wavelengths, dtype=torch.float64)
    torch_indices = fused_silica_index(torch_wavelengths).detach().cpu().numpy()
    oracle_indices = np.asarray([_sellmeier_oracle(value) for value in wavelengths])
    index_residual = float(np.max(np.abs(torch_indices - oracle_indices)))

    omega = 2.0 * np.pi * C_NM_PER_FS / (1000.0 * wavelengths)
    torch_omega = torch.as_tensor(omega, dtype=torch.float64)
    generated = model.omega_prime(torch_omega).detach().cpu().numpy()
    oracle = np.asarray(
        [
            value
            * (1.0 - model.frame_velocity_over_c * _effective_index_oracle(wavelength, geometry))
            for value, wavelength in zip(omega, wavelengths, strict=True)
        ]
    )
    dispersion_residual = float(np.max(np.abs(generated - oracle)))
    tolerance = float(parameters["backend_tolerance"])
    return {
        "target_id": "T_F2A",
        "checks": {
            "sellmeier_scalar_tensor_crosscheck": {
                "kind": "backend_crosscheck",
                "value": index_residual,
                "tolerance": tolerance,
                "passed": index_residual <= tolerance,
            },
            "co_moving_formula_rederivation": {
                "kind": "exact_rederivation",
                "value": dispersion_residual,
                "tolerance": tolerance,
                "passed": dispersion_residual <= tolerance,
            },
        },
        "wavelengths_um": wavelengths.tolist(),
        "scientific_boundary": "exact fibre modal dispersion coefficients are unpublished",
    }


def _frame_velocity_check(parameters: dict[str, Any]) -> dict[str, Any]:
    geometry = PCFGeometry(**parameters["geometry"])
    pump_nm = float(parameters["pump_wavelength_nm"])
    model = CleanRoomPCFDispersion(geometry, pump_wavelength_nm=pump_nm)
    oracle_velocity = 1.0 / _group_index_oracle(pump_nm / 1000.0, geometry)
    velocity_residual = abs(model.frame_velocity_over_c - oracle_velocity)

    pump_omega = 2.0 * np.pi * C_NM_PER_FS / pump_nm
    delta = float(parameters["omega_derivative_step"])
    points = torch.tensor(
        [pump_omega - delta, pump_omega + delta], dtype=torch.float64
    )
    values = model.omega_prime(points)
    derivative = abs(float((values[1] - values[0]) / (2.0 * delta)))
    return {
        "target_id": "T_F2B",
        "checks": {
            "group_velocity_oracle": {
                "kind": "exact_rederivation",
                "value": velocity_residual,
                "tolerance": float(parameters["velocity_tolerance"]),
                "passed": velocity_residual <= float(parameters["velocity_tolerance"]),
            },
            "pump_stationary_frame": {
                "kind": "invariant",
                "value": derivative,
                "tolerance": float(parameters["stationarity_tolerance"]),
                "passed": derivative <= float(parameters["stationarity_tolerance"]),
            },
        },
        "scientific_boundary": "dataset-specific fitted frame velocities and offset are unpublished",
    }


def _uv_continuation_check(parameters: dict[str, Any]) -> dict[str, Any]:
    geometry = PCFGeometry(**parameters["geometry"])
    delta = float(parameters["omega_step"])
    boundaries = [float(value) for value in parameters["minimum_wavelengths_um"]]
    rows = []
    maximum_value_jump = 0.0
    maximum_slope_jump = 0.0
    continuation_values = []
    for wavelength in boundaries:
        model = CleanRoomPCFDispersion(geometry)
        model.minimum_sellmeier_wavelength_um = wavelength
        boundary = 2.0 * np.pi * C_NM_PER_FS / (1000.0 * wavelength)
        points = torch.tensor(
            [boundary - 2 * delta, boundary - delta, boundary, boundary + delta, boundary + 2 * delta],
            dtype=torch.float64,
        )
        values = model.omega_prime(points).detach().cpu().numpy()
        left_slope = (values[2] - values[1]) / delta
        right_slope = (values[3] - values[2]) / delta
        value_jump = abs(values[3] - (values[2] + left_slope * delta))
        slope_jump = abs(right_slope - left_slope)
        maximum_value_jump = max(maximum_value_jump, float(value_jump))
        maximum_slope_jump = max(maximum_slope_jump, float(slope_jump))
        evaluation_omega = boundary + float(parameters["evaluation_offset_rad_fs"])
        continuation_value = float(
            model.omega_prime(torch.tensor(evaluation_omega, dtype=torch.float64))
        )
        continuation_values.append(continuation_value)
        rows.append(
            {
                "minimum_wavelength_um": wavelength,
                "boundary_omega_rad_fs": boundary,
                "value_jump": float(value_jump),
                "slope_jump": float(slope_jump),
                "continuation_value": continuation_value,
            }
        )
    sensitivity_span = float(np.ptp(continuation_values))
    return {
        "target_id": "T_F2C",
        "checks": {
            "tangent_continuation_continuity": {
                "kind": "invariant",
                "value": max(maximum_value_jump, maximum_slope_jump),
                "tolerance": float(parameters["continuity_tolerance"]),
                "passed": max(maximum_value_jump, maximum_slope_jump)
                <= float(parameters["continuity_tolerance"]),
            },
            "uv_boundary_sensitivity": {
                "kind": "convergence",
                "value": sensitivity_span,
                "tolerance": float(parameters["sensitivity_span_maximum"]),
                "passed": sensitivity_span
                <= float(parameters["sensitivity_span_maximum"]),
            },
        },
        "rows": rows,
        "scientific_boundary": "the surrogate UV continuation is numerically controlled but cannot replace the unpublished measured fibre dispersion",
    }


def run_campaign(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("paper_id") != "10.1038-s41586-026-10720-3":
        raise ValueError("unexpected paper_id")
    policy = config["source_policy"]
    if any(bool(policy.get(key, True)) for key in policy):
        raise ValueError("all forbidden input flags must be false")
    parameters = config["parameters"]
    results = {
        "T_F2A": _dispersion_backend_check(parameters["T_F2A"]),
        "T_F2B": _frame_velocity_check(parameters["T_F2B"]),
        "T_F2C": _uv_continuation_check(parameters["T_F2C"]),
    }
    for result in results.values():
        result["passed"] = bool(
            len({check["kind"] for check in result["checks"].values()}) >= 2
            and all(bool(check["passed"]) for check in result["checks"].values())
        )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "purpose": "code_fault_discrimination_only",
        "target_results": results,
        "status": "passed" if all(row["passed"] for row in results.values()) else "failed",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
    }
