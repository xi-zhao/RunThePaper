"""Formula-derived dispersion models for clean-room scientific runs.

The Nature paper does not publish the measured fibre dispersion coefficients.
Consequently the exact curve in Fig. 2 cannot be regenerated from the paper.
This module implements a transparent *physical surrogate* from material and
geometry formulas only:

* the three-term fused-silica Sellmeier equation;
* a scalar capillary approximation for the fundamental PCF mode; and
* the co-moving transformation ``omega' = omega - u beta(omega)``.

No PDF path, figure coordinate, digitized curve, author array, or author code
is accepted by this module.  The surrogate is deliberately labelled
``reconstructed`` and must not be promoted to a paper-exact dispersion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import torch


C_NM_PER_FS = 299.792458
_SELLMEIER_B = (0.6961663, 0.4079426, 0.8974794)
_SELLMEIER_C_UM2 = (0.0684043**2, 0.1162414**2, 9.896161**2)
_LP01_ROOT = 2.404825557695773


@dataclass(frozen=True)
class PCFGeometry:
    """Published geometry plus one explicit scalar-mode approximation.

    The related dispersion paper reports ``pitch=1.079 um`` and
    ``hole_diameter=0.763 um``.  It does not report an analytic mapping from
    that microstructure to an effective core radius.  The default
    ``effective_core_radius=pitch`` is therefore an assumption, not a fitted
    paper parameter.  Paper-scale campaigns sweep this value.
    """

    pitch_um: float = 1.079
    hole_diameter_um: float = 0.763
    effective_core_radius_um: float = 1.079
    mode_root: float = _LP01_ROOT

    def validate(self) -> None:
        if self.pitch_um <= 0 or self.hole_diameter_um <= 0:
            raise ValueError("PCF geometry lengths must be positive")
        if self.hole_diameter_um >= self.pitch_um:
            raise ValueError("hole diameter must be smaller than pitch")
        if self.effective_core_radius_um <= 0:
            raise ValueError("effective core radius must be positive")
        if self.mode_root <= 0:
            raise ValueError("mode root must be positive")


def _sellmeier_index_scalar(wavelength_um: float) -> float:
    wavelength_squared = wavelength_um * wavelength_um
    index_squared = 1.0
    for coefficient, resonance_squared in zip(
        _SELLMEIER_B, _SELLMEIER_C_UM2, strict=True
    ):
        index_squared += (
            coefficient
            * wavelength_squared
            / (wavelength_squared - resonance_squared)
        )
    if index_squared <= 0:
        raise ValueError("Sellmeier index is not real at this wavelength")
    return math.sqrt(index_squared)


def _effective_index_scalar(wavelength_um: float, geometry: PCFGeometry) -> float:
    material_index = _sellmeier_index_scalar(wavelength_um)
    transverse = (
        geometry.mode_root
        * wavelength_um
        / (2.0 * math.pi * geometry.effective_core_radius_um)
    )
    value = material_index * material_index - transverse * transverse
    if value <= 0:
        raise ValueError("capillary effective index is not real")
    return math.sqrt(value)


def _group_index_scalar(wavelength_um: float, geometry: PCFGeometry) -> float:
    step = max(1.0e-7, wavelength_um * 1.0e-5)
    derivative = (
        _effective_index_scalar(wavelength_um + step, geometry)
        - _effective_index_scalar(wavelength_um - step, geometry)
    ) / (2.0 * step)
    return _effective_index_scalar(wavelength_um, geometry) - wavelength_um * derivative


def fused_silica_index(wavelength_um: torch.Tensor) -> torch.Tensor:
    """Return the Malitson fused-silica phase index.

    The formula is evaluated only on its declared campaign interval.  The
    caller is responsible for the explicit ultraviolet continuation used
    outside that interval.
    """

    wavelength_squared = wavelength_um.square()
    index_squared = torch.ones_like(wavelength_um)
    for coefficient, resonance_squared in zip(
        _SELLMEIER_B, _SELLMEIER_C_UM2, strict=True
    ):
        index_squared = index_squared + (
            coefficient
            * wavelength_squared
            / (wavelength_squared - resonance_squared)
        )
    return torch.sqrt(torch.clamp_min(index_squared, 1.0e-12))


class CleanRoomPCFDispersion:
    """Formula-only capillary-PCF surrogate for independent numerics.

    ``u/c`` defaults to the group velocity of the 800 nm incident pump in
    this same surrogate.  This enforces the physical moving-frame rule
    without reading the Fig. 2 curve.  An additive co-moving offset can be
    supplied for sensitivity studies, but defaults to zero because the paper's
    fitted ``delta beta_0`` is not published.
    """

    provenance = "formula_only_reconstructed"
    parameter_match = "related_geometry_plus_declared_approximation"
    source_pixels_used = False
    author_code_used = False
    author_numeric_arrays_used = False
    minimum_sellmeier_wavelength_um = 0.21

    def __init__(
        self,
        geometry: PCFGeometry | None = None,
        *,
        pump_wavelength_nm: float = 800.0,
        frame_velocity_over_c: float | None = None,
        omega_prime_offset_rad_fs: float = 0.0,
    ) -> None:
        self.geometry = geometry or PCFGeometry()
        self.geometry.validate()
        if pump_wavelength_nm <= 0:
            raise ValueError("pump wavelength must be positive")
        self.pump_wavelength_nm = float(pump_wavelength_nm)
        derived_velocity = 1.0 / _group_index_scalar(
            pump_wavelength_nm / 1000.0, self.geometry
        )
        self.frame_velocity_over_c = float(
            derived_velocity
            if frame_velocity_over_c is None
            else frame_velocity_over_c
        )
        if not 0.0 < self.frame_velocity_over_c < 1.0:
            raise ValueError("frame velocity over c must lie between zero and one")
        self.omega_prime_offset_rad_fs = float(omega_prime_offset_rad_fs)

    def _valid_omega_prime(self, omega_rad_fs: torch.Tensor) -> torch.Tensor:
        wavelength_um = (
            2.0 * torch.pi * C_NM_PER_FS / omega_rad_fs / 1000.0
        )
        material_index = fused_silica_index(wavelength_um)
        transverse = (
            self.geometry.mode_root
            * wavelength_um
            / (2.0 * torch.pi * self.geometry.effective_core_radius_um)
        )
        effective_index = torch.sqrt(
            torch.clamp_min(material_index.square() - transverse.square(), 1.0e-12)
        )
        return (
            omega_rad_fs
            * (1.0 - self.frame_velocity_over_c * effective_index)
            + self.omega_prime_offset_rad_fs
        )

    def omega_prime(self, omega_rad_fs: torch.Tensor) -> torch.Tensor:
        """Evaluate the co-moving frequency with an explicit UV continuation."""

        positive = torch.clamp_min(omega_rad_fs, 0.0)
        maximum_valid_omega = (
            2.0
            * torch.pi
            * C_NM_PER_FS
            / (1000.0 * self.minimum_sellmeier_wavelength_um)
        )
        inside = torch.clamp(positive, min=1.0e-12, max=maximum_valid_omega)
        value = self._valid_omega_prime(inside)

        # The FFT grid extends beyond the published/material-valid interval.
        # Continue the last valid point by its local tangent rather than
        # crossing the Sellmeier pole at 116 nm.
        boundary = torch.as_tensor(
            maximum_valid_omega, device=positive.device, dtype=positive.dtype
        )
        delta = torch.as_tensor(
            1.0e-4, device=positive.device, dtype=positive.dtype
        )
        boundary_value = self._valid_omega_prime(boundary)
        boundary_slope = (
            self._valid_omega_prime(boundary)
            - self._valid_omega_prime(boundary - delta)
        ) / delta
        continued = boundary_value + boundary_slope * (positive - boundary)
        value = torch.where(positive > boundary, continued, value)
        return torch.where(omega_rad_fs > 0, value, torch.zeros_like(value))

    def metadata(self) -> dict[str, Any]:
        return {
            "model": "sellmeier_plus_scalar_capillary",
            "provenance": self.provenance,
            "parameter_match": self.parameter_match,
            "geometry": asdict(self.geometry),
            "pump_wavelength_nm": self.pump_wavelength_nm,
            "frame_velocity_over_c": self.frame_velocity_over_c,
            "frame_velocity_rule": "inverse_group_index_at_incident_pump",
            "omega_prime_offset_rad_fs": self.omega_prime_offset_rad_fs,
            "minimum_sellmeier_wavelength_um": self.minimum_sellmeier_wavelength_um,
            "ultraviolet_continuation": "local_tangent",
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
        }
