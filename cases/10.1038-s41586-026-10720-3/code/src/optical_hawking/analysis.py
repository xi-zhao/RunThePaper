"""Observable extraction and paper phase-matching checks."""

from __future__ import annotations

from typing import Any, Protocol

import torch

from .physical_dispersion import CleanRoomPCFDispersion
from .model import (
    PulseSpec,
    wavelength_nm_from_angular_frequency,
)


class DispersionLike(Protocol):
    def omega_prime(self, omega_rad_fs: torch.Tensor) -> torch.Tensor: ...


def _bisect_root(
    dispersion: DispersionLike,
    target: float,
    lower: float,
    upper: float,
    iterations: int = 80,
) -> float:
    dtype = torch.float64

    def value(x: float) -> float:
        tensor = torch.tensor(x, dtype=dtype)
        return float(dispersion.omega_prime(tensor)) - target

    left_value = value(lower)
    right_value = value(upper)
    if left_value * right_value > 0:
        raise ValueError(f"root target {target} is not bracketed by [{lower}, {upper}]")
    for _ in range(iterations):
        middle = 0.5 * (lower + upper)
        middle_value = value(middle)
        if left_value * middle_value <= 0:
            upper = middle
            right_value = middle_value
        else:
            lower = middle
            left_value = middle_value
    return 0.5 * (lower + upper)


def _golden_section_extremum(
    dispersion: DispersionLike,
    lower: float,
    upper: float,
    *,
    maximize: bool,
    iterations: int = 80,
) -> float:
    """Locate one bracketed stationary point without differentiating the trace."""

    ratio = (5.0**0.5 - 1.0) / 2.0

    def objective(value: float) -> float:
        omega = torch.tensor(value, dtype=torch.float64)
        result = float(dispersion.omega_prime(omega))
        return -result if maximize else result

    left = upper - ratio * (upper - lower)
    right = lower + ratio * (upper - lower)
    left_value = objective(left)
    right_value = objective(right)
    for _ in range(iterations):
        if left_value < right_value:
            upper = right
            right = left
            right_value = left_value
            left = upper - ratio * (upper - lower)
            left_value = objective(left)
        else:
            lower = left
            left = right
            left_value = right_value
            right = lower + ratio * (upper - lower)
            right_value = objective(right)
    return 0.5 * (lower + upper)


def phase_matching_from_angular_frequencies(
    pump_omega_rad_fs: float,
    probe_omega_rad_fs: float,
    dispersion: DispersionLike | None = None,
) -> dict[str, Any]:
    """Evaluate the paper's three UV roots from the carrier frequencies."""

    dispersion = dispersion or CleanRoomPCFDispersion()

    def wp(value: float) -> float:
        return float(dispersion.omega_prime(torch.tensor(value, dtype=torch.float64)))

    pump_prime = wp(pump_omega_rad_fs)
    probe_prime = wp(probe_omega_rad_fs)
    targets = {
        "nrr": -pump_prime,
        "hawking_partner": -probe_prime,
        "backreaction": pump_prime - 2.0 * probe_prime,
    }
    markers: dict[str, Any] = {
        "pump_omega_rad_fs": pump_omega_rad_fs,
        "probe_omega_rad_fs": probe_omega_rad_fs,
        "pump_omega_prime_rad_fs": pump_prime,
        "probe_omega_prime_rad_fs": probe_prime,
    }
    for name, target in targets.items():
        # The exact measured fibre coefficients are unavailable, so a clean
        # physical surrogate may move the UV roots by several percent.  Scan
        # a broad physical UV interval rather than encoding Fig. 2 pixels.
        grid = torch.linspace(7.0, 10.0, 1501, dtype=torch.float64)
        residual = dispersion.omega_prime(grid) - target
        sign_change = residual[:-1] * residual[1:] <= 0
        candidates = torch.nonzero(sign_change, as_tuple=False).flatten()
        if candidates.numel() == 0:
            markers[name] = {
                "omega_prime_rad_fs": target,
                "status": "no_root_in_188_to_269_nm_surrogate_window",
            }
            continue
        index = int(candidates[-1])
        omega = _bisect_root(
            dispersion,
            target,
            float(grid[index]),
            float(grid[index + 1]),
        )
        markers[name] = {
            "omega_prime_rad_fs": target,
            "omega_rad_fs": omega,
            "wavelength_nm": wavelength_nm_from_angular_frequency(omega),
        }
    if all(
        "wavelength_nm" in markers[name]
        for name in ("hawking_partner", "backreaction")
    ):
        markers["backreaction_shift_nm"] = (
            markers["hawking_partner"]["wavelength_nm"]
            - markers["backreaction"]["wavelength_nm"]
        )
    else:
        markers["backreaction_shift_nm"] = None
    return markers


def figure2_landmarks(
    probe: PulseSpec,
    dispersion: DispersionLike | None = None,
) -> dict[str, Any]:
    """Return the IR and UV landmarks drawn in the paper's Fig. 2.

    The pump marker in Fig. 2 is the Raman-shifted carrier at the local
    dispersion minimum, not the incident 800 nm laser carrier used by the
    propagation preset.  Keeping those two physical states separate is
    necessary to reproduce all three UV phase-matching levels at once.
    """

    dispersion = dispersion or CleanRoomPCFDispersion()
    horizon_lower = 1.0
    horizon_upper = 1.4
    horizon_omega = _golden_section_extremum(
        dispersion, horizon_lower, horizon_upper, maximize=True
    )
    pump_omega = _golden_section_extremum(
        dispersion, 1.7, 2.2, maximize=False
    )
    probe_prime = float(
        dispersion.omega_prime(
            torch.tensor(probe.omega_rad_fs, dtype=torch.float64)
        )
    )
    horizon_is_interior = (
        horizon_lower + 1.0e-4
        < horizon_omega
        < horizon_upper - 1.0e-4
    )
    redshifted_omega: float | None = None
    if horizon_is_interior:
        try:
            redshifted_omega = _bisect_root(
                dispersion, probe_prime, 0.75, horizon_omega
            )
        except ValueError:
            redshifted_omega = None
    phase_matching = phase_matching_from_angular_frequencies(
        pump_omega,
        probe.omega_rad_fs,
        dispersion,
    )
    return {
        **phase_matching,
        "horizon": {
            "omega_rad_fs": horizon_omega,
            "omega_prime_rad_fs": float(
                dispersion.omega_prime(
                    torch.tensor(horizon_omega, dtype=torch.float64)
                )
            ),
            "status": (
                "stationary_point"
                if horizon_is_interior
                else "not_resolved_by_formula_only_surrogate"
            ),
        },
        "redshifted_probe": {
            "omega_rad_fs": redshifted_omega,
            "omega_prime_rad_fs": probe_prime,
            "status": (
                "root_found"
                if redshifted_omega is not None
                else "not_resolved_by_formula_only_surrogate"
            ),
        },
    }


def phase_matching_markers(
    pump: PulseSpec,
    probe: PulseSpec,
    dispersion: DispersionLike | None = None,
) -> dict[str, Any]:
    """Return NRR, Hawking-partner, and backreaction marker positions.

    The identities are Eqs. (1), (B.1), and (B.3) of the paper:
    omega'_NRR=-omega'_pump, omega'_-=-omega'_probe, and
    omega'_B=omega'_pump-2 omega'_probe.
    """

    return phase_matching_from_angular_frequencies(
        pump.omega_rad_fs,
        probe.omega_rad_fs,
        dispersion,
    )


def spectral_power(state_omega: torch.Tensor) -> torch.Tensor:
    """FFT-normalized spectral power for comparisons on the same grid."""

    return state_omega.abs().square() / state_omega.shape[-1] ** 2


def stimulated_signal(spectral_power_batch: torch.Tensor) -> torch.Tensor:
    """Pump-subtracted stimulated spectra, with and without conjugated SPM.

    The scenario order is the domain contract defined in ``solver.py``:
    pump+probe, pump only, then the same pair with conjugated SPM disabled.
    """

    if spectral_power_batch.ndim != 2 or spectral_power_batch.shape[0] != 4:
        raise ValueError("spectral_power_batch must have shape [4, frequency]")
    return torch.stack(
        (
            spectral_power_batch[0] - spectral_power_batch[1],
            spectral_power_batch[2] - spectral_power_batch[3],
        )
    )


def conjugated_spm_contribution(spectral_power_batch: torch.Tensor) -> torch.Tensor:
    """Return the stimulated spectrum attributable to conjugated SPM."""

    signals = stimulated_signal(spectral_power_batch)
    return signals[0] - signals[1]
