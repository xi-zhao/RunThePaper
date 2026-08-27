"""Independent unit and normalization checks for the supplement UPPE scans."""

from __future__ import annotations

from typing import Any

import torch

from .model import PropagationConfig, PulseSpec, SimulationGrid
from .solver import AnalyticSignalUPPE


def _pulse(values: dict[str, Any], *, average_power_w: float | None = None) -> PulseSpec:
    return PulseSpec(
        wavelength_nm=float(values["wavelength_nm"]),
        intensity_fwhm_fs=float(values["intensity_fwhm_fs"]),
        average_power_w=float(
            values["average_power_w"] if average_power_w is None else average_power_w
        ),
        repetition_rate_hz=float(values["repetition_rate_hz"]),
    )


def check_supplement_normalization(config: dict[str, Any]) -> dict[str, Any]:
    """Verify field, FFT, chirp, power and frequency-dependent-gamma units.

    These checks close the clean-room method question only.  They cannot supply
    the paper's unpublished fibre dispersion, pulse state, delay, chirp
    convention or sampling grid, so scientific coverage is not promoted.
    """

    if config.get("paper_id") != "10.1038-s41586-026-10720-3":
        raise ValueError("paper_id does not match this case")
    if config.get("profile") != "method_closure_attestation":
        raise ValueError("only the frozen method-closure profile is accepted")
    points = [int(value) for value in config["grid_points"]]
    if len(points) < 2 or any(value < 64 or value & (value - 1) for value in points):
        raise ValueError("grid_points must contain increasing powers of two")
    if points != sorted(set(points)):
        raise ValueError("grid_points must be unique and increasing")

    pump = _pulse(config["pump"])
    omega_max = float(config["omega_max_rad_fs"])
    energy_rows: list[dict[str, float | int]] = []
    for grid_points in points:
        grid = SimulationGrid(points=grid_points, omega_max_rad_fs=omega_max)
        time, _omega, _positive = grid.tensors(torch.device("cpu"), torch.float64)
        field = pump.field(time, torch.complex128)
        numeric_energy = float(torch.sum(field.abs().square()) * grid.dt_fs)
        expected_energy = float(pump.pulse_energy_w_fs)
        spectrum = torch.fft.fft(field)
        parseval_time = float(torch.sum(field.abs().square()))
        parseval_frequency = float(torch.sum(spectrum.abs().square()) / grid_points)
        energy_rows.append(
            {
                "grid_points": grid_points,
                "time_window_fs": grid.time_window_fs,
                "numeric_energy_w_fs": numeric_energy,
                "expected_energy_w_fs": expected_energy,
                "energy_relative_error": abs(numeric_energy - expected_energy)
                / expected_energy,
                "parseval_relative_error": abs(parseval_time - parseval_frequency)
                / parseval_time,
            }
        )

    fine_grid = SimulationGrid(points=points[-1], omega_max_rad_fs=omega_max)
    time, omega, _positive = fine_grid.tensors(torch.device("cpu"), torch.float64)
    field = pump.field(time, torch.complex128)
    spectrum = torch.fft.fft(field)
    detuning = omega - pump.omega_rad_fs
    chirped_spectrum = spectrum * torch.exp(
        0.5j * float(config["chirp_gdd_fs2"]) * detuning.square()
    )
    chirped = torch.fft.ifft(chirped_spectrum)
    chirp_energy_relative = float(
        torch.abs(torch.sum(chirped.abs().square()) - torch.sum(field.abs().square()))
        / torch.sum(field.abs().square())
    )

    probe_values = config["probe"]
    probe_powers = [float(value) for value in config["power_probe_w"]]
    probe_energies = [
        _pulse(probe_values, average_power_w=power).pulse_energy_w_fs
        for power in probe_powers
    ]
    power_ratio = probe_powers[-1] / probe_powers[0]
    energy_ratio = probe_energies[-1] / probe_energies[0]

    propagation = PropagationConfig(
        length_mm=0.002,
        step_mm=0.001,
        gamma_spm_w_inv_mm=float(config["gamma_spm_w_inv_mm"]),
        precision="complex128",
        record_snapshots=0,
    )
    solver = AnalyticSignalUPPE(
        fine_grid, propagation, device=torch.device("cpu")
    )
    positive_indices = torch.nonzero(solver.omega_rad_fs > 0.0).flatten()
    first = int(positive_indices[len(positive_indices) // 4])
    second = int(positive_indices[len(positive_indices) // 2])
    effective_gamma = 3.0 * solver.nonlinear_gamma.real
    expected_first = (
        propagation.gamma_spm_w_inv_mm
        * float(solver.omega_rad_fs[first])
        / pump.omega_rad_fs
    )
    gamma_relative = abs(float(effective_gamma[first]) - expected_first) / abs(
        expected_first
    )
    frequency_ratio_relative = abs(
        float(effective_gamma[second] / effective_gamma[first])
        - float(solver.omega_rad_fs[second] / solver.omega_rad_fs[first])
    ) / abs(float(solver.omega_rad_fs[second] / solver.omega_rad_fs[first]))

    tolerances = config["tolerances"]
    checks = {
        "sech_field_integrates_to_pulse_energy": max(
            float(row["energy_relative_error"]) for row in energy_rows
        )
        <= float(tolerances["pulse_energy_relative"]),
        "energy_is_grid_converged": abs(
            float(energy_rows[-1]["numeric_energy_w_fs"])
            - float(energy_rows[-2]["numeric_energy_w_fs"])
        )
        / float(energy_rows[-1]["numeric_energy_w_fs"])
        <= float(tolerances["grid_convergence_relative"]),
        "fft_obeys_parseval": max(
            float(row["parseval_relative_error"]) for row in energy_rows
        )
        <= float(tolerances["parseval_relative"]),
        "spectral_chirp_preserves_energy": chirp_energy_relative
        <= float(tolerances["chirp_energy_relative"]),
        "average_power_maps_linearly_to_pulse_energy": abs(
            energy_ratio - power_ratio
        )
        / power_ratio
        <= float(tolerances["power_scaling_relative"]),
        "frequency_dependent_gamma_matches_printed_uppe_scaling": max(
            gamma_relative, frequency_ratio_relative
        )
        <= float(tolerances["gamma_frequency_relative"]),
    }
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "status": "passed" if all(checks.values()) else "failed",
        "scientific_promotion": False,
        "target_ids": ["T_S1A", "T_S1B", "T_S1C"],
        "checks": checks,
        "metrics": {
            "pulse_energy": energy_rows,
            "chirp_energy_relative_error": chirp_energy_relative,
            "power_ratio": power_ratio,
            "pulse_energy_ratio": energy_ratio,
            "gamma_value_relative_error": gamma_relative,
            "gamma_frequency_ratio_relative_error": frequency_ratio_relative,
        },
        "remaining_boundary": {
            "category": "publication_underspecified",
            "missing_inputs": [
                "experiment-specific fibre dispersion",
                "measured pulse shapes and relative delay",
                "paper chirp convention and initial chirp state",
                "paper scan sampling and raw signal extraction protocol",
            ],
        },
        "clean_room_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "reference_pixels_read": False,
            "legacy_generated_outputs_read": False,
        },
    }
