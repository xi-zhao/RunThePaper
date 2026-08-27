"""Sharded formula-only campaign for every reproducible numerical paper item.

The campaign is intentionally independent of ``raw/``, ``paper_reference``
and all source-figure extraction code.  Missing measured dispersion, spectra,
and fitted tables remain explicit blockers; they are never replaced by pixels.
"""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

import numpy as np
import torch

from .analysis import (
    conjugated_spm_contribution,
    figure2_landmarks,
    phase_matching_markers,
    stimulated_signal,
)
from .model import PropagationConfig, PulseSpec, SimulationGrid
from .physical_dispersion import CleanRoomPCFDispersion, PCFGeometry
from .solver import AnalyticSignalUPPE, build_counterfactual_batch
from .theory import SidebandParameters, sideband_spectrum


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def implementation_digest(workspace: Path) -> str:
    paths = (
        "src/optical_hawking/model.py",
        "src/optical_hawking/physical_dispersion.py",
        "src/optical_hawking/analysis.py",
        "src/optical_hawking/solver.py",
        "src/optical_hawking/theory.py",
        "src/optical_hawking/paper_scale_campaign.py",
        "scripts/run_paper_scale.py",
    )
    digest = hashlib.sha256()
    for relative in paths:
        path = workspace / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _unit(
    unit_id: str,
    target_ids: tuple[str, ...],
    family: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    if not target_ids:
        raise ValueError("a campaign unit must bind at least one target")
    return {
        "unit_id": unit_id,
        "target_id": target_ids[0],
        "target_ids": list(target_ids),
        "family": family,
        "parameters": parameters,
    }


def _paper_pump(config: dict[str, Any]) -> PulseSpec:
    values = config["paper_parameters"]["pump"]
    return PulseSpec(
        wavelength_nm=float(values["wavelength_nm"]),
        intensity_fwhm_fs=float(values["fwhm_fs"]),
        average_power_w=float(values["average_power_mw"]) * 1.0e-3,
        repetition_rate_hz=float(values["repetition_rate_mhz"]) * 1.0e6,
    )


def _paper_probe(
    config: dict[str, Any], wavelength_nm: float | None = None
) -> PulseSpec:
    values = config["paper_parameters"]["probe"]
    return PulseSpec(
        wavelength_nm=float(wavelength_nm or values["wavelength_nm"]),
        intensity_fwhm_fs=float(values["fwhm_fs"]),
        average_power_w=float(values["average_power_mw"]) * 1.0e-3,
        repetition_rate_hz=float(
            config["paper_parameters"]["pump"]["repetition_rate_mhz"]
        )
        * 1.0e6,
    )


def _probe_wavelengths(config: dict[str, Any]) -> tuple[float, ...]:
    return tuple(
        float(value)
        for value in config["paper_parameters"]["probe_wavelengths_nm"]
    )


def build_plan(config: dict[str, Any], profile_name: str) -> list[dict[str, Any]]:
    profile = config["profiles"][profile_name]
    fig4_probe_wavelengths = _probe_wavelengths(config)
    supplement_probe_wavelengths = tuple(
        float(value)
        for value in profile["supplement_scans"]["probe_wavelength_nm"]
    )
    fig4_mu = tuple(float(value) for value in config["paper_parameters"]["fig4_mu"])
    if len(fig4_probe_wavelengths) != len(fig4_mu):
        raise ValueError("probe_wavelengths_nm and fig4_mu must have equal length")
    units: list[dict[str, Any]] = []
    for radius in profile["dispersion"]["effective_core_radius_um"]:
        units.append(
            _unit(
                f"T_F2-dispersion-a{radius:.4f}",
                ("T_F2A", "T_F2B", "T_F2C"),
                "dispersion",
                {"effective_core_radius_um": radius},
            )
        )
    for wavelength in supplement_probe_wavelengths:
        units.append(
            _unit(
                f"T_S1A-probe-{wavelength:.0f}nm",
                ("T_S1A",),
                "uppe_probe",
                {"probe_wavelength_nm": wavelength},
            )
        )
    for power_mw in profile["supplement_scans"]["pump_power_mw"]:
        units.append(
            _unit(
                f"T_S1B-power-{power_mw:.1f}mW",
                ("T_S1B",),
                "uppe_power",
                {"pump_power_mw": power_mw},
            )
        )
    for prechirp_cm in profile["supplement_scans"]["prechirp_cm"]:
        units.append(
            _unit(
                f"T_S1C-chirp-{prechirp_cm:+.2f}cm",
                ("T_S1C",),
                "uppe_chirp",
                {"prechirp_cm": prechirp_cm},
            )
        )
    for index, (probe, mu) in enumerate(
        zip(fig4_probe_wavelengths, fig4_mu, strict=True)
    ):
        panel = chr(ord("A") + index)
        units.append(
            _unit(
                f"T_F4{panel}-{probe:.0f}nm",
                (f"T_F4{panel}",),
                "sideband_family",
                {
                    "panel": panel.lower(),
                    "probe_wavelength_nm": probe,
                    "mu": mu,
                },
            )
        )
    units.append(
        _unit("T_F5C-equal-slope", ("T_F5C",), "thermal_family", {})
    )
    return units


def smoke_plan(full_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # The smoke profile is already reduced in grid size and propagation length.
    # Keep all of its independently declared scan points so each numerical
    # panel has a real multi-point artifact instead of a one-point placeholder.
    return list(full_plan)


def shard_for(unit: dict[str, Any], shard_count: int) -> int:
    return int(sha256_bytes(canonical_json(unit))[:16], 16) % shard_count


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    temporary.replace(path)


def _atomic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def _geometry(config: dict[str, Any], radius: float | None = None) -> PCFGeometry:
    geometry = config["paper_parameters"]["related_pcf_geometry"]
    return PCFGeometry(
        pitch_um=float(geometry["pitch_um"]),
        hole_diameter_um=float(geometry["hole_diameter_um"]),
        effective_core_radius_um=float(radius or geometry["effective_core_radius_um"]),
    )


def _dispersion_unit(
    config: dict[str, Any], profile: dict[str, Any], unit: dict[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    radius = float(unit["parameters"]["effective_core_radius_um"])
    dispersion = CleanRoomPCFDispersion(_geometry(config, radius))
    omega = torch.linspace(
        float(profile["dispersion"]["omega_rad_fs"][0]),
        float(profile["dispersion"]["omega_rad_fs"][1]),
        int(profile["dispersion"]["points"]),
        dtype=torch.float64,
    )
    omega_prime = dispersion.omega_prime(omega)
    pump = _paper_pump(config)
    probe = _paper_probe(config)
    markers = phase_matching_markers(pump, probe, dispersion)
    landmarks = figure2_landmarks(probe, dispersion)
    paper_horizon_nm = float(config["paper_parameters"]["printed_landmarks"]["horizon_nm"])
    horizon_status = landmarks["horizon"]["status"]
    horizon_nm = (
        2.0 * np.pi * 299.792458 / landmarks["horizon"]["omega_rad_fs"]
        if horizon_status == "stationary_point"
        else None
    )
    metrics = {
        "dispersion": dispersion.metadata(),
        "phase_matching": markers,
        "landmarks": landmarks,
        "paper_horizon_nm": paper_horizon_nm,
        "horizon_nm": horizon_nm,
        "horizon_feature_passed": bool(
            horizon_nm is not None and abs(horizon_nm - paper_horizon_nm) <= 20.0
        ),
        "paper_exact": False,
        "blocker": "measured_fibre_dispersion_coefficients_not_published",
    }
    return {
        "omega_rad_fs": omega.numpy(),
        "omega_prime_rad_fs": omega_prime.numpy(),
    }, metrics


def _prechirp_pump(
    solver: AnalyticSignalUPPE,
    pump: PulseSpec,
    gdd_fs2: float,
    complex_dtype: torch.dtype,
) -> torch.Tensor:
    field = pump.field(solver.time_fs, complex_dtype)
    if gdd_fs2 == 0.0:
        return field
    spectrum = torch.fft.fft(field)
    detuning = solver.omega_rad_fs - pump.omega_rad_fs
    phase = torch.exp(0.5j * gdd_fs2 * detuning.square()).to(complex_dtype)
    return torch.fft.ifft(spectrum * phase)


def _build_batch_with_prechirp(
    solver: AnalyticSignalUPPE,
    pump: PulseSpec,
    probe: PulseSpec,
    gdd_fs2: float,
    complex_dtype: torch.dtype,
) -> tuple[torch.Tensor, torch.Tensor]:
    if gdd_fs2 == 0.0:
        return build_counterfactual_batch(
            solver.time_fs, pump, probe, complex_dtype
        )
    pump_field = _prechirp_pump(solver, pump, gdd_fs2, complex_dtype)
    probe_field = probe.field(solver.time_fs, complex_dtype)
    initial = torch.stack(
        (
            pump_field + probe_field,
            pump_field,
            pump_field + probe_field,
            pump_field,
        )
    )
    weights = torch.tensor(
        ((1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 0.0), (1.0, 1.0, 0.0)),
        device=solver.time_fs.device,
        dtype=solver.time_fs.dtype,
    )
    return initial, weights


def _nearest_power(
    wavelength_nm: np.ndarray,
    power: np.ndarray,
    centre_nm: float | None,
) -> float | None:
    if centre_nm is None:
        return None
    valid = np.isfinite(wavelength_nm)
    if not np.any(valid):
        return None
    indices = np.flatnonzero(valid)
    selected = indices[int(np.argmin(np.abs(wavelength_nm[valid] - centre_nm)))]
    return float(power[selected])


def _propagation_unit(
    workspace: Path,
    config: dict[str, Any],
    profile: dict[str, Any],
    unit: dict[str, Any],
    device: str | None,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    scale = profile["propagation"]
    dispersion = CleanRoomPCFDispersion(_geometry(config))
    propagation = PropagationConfig(
        length_mm=float(scale["length_mm"]),
        step_mm=float(scale["step_mm"]),
        integrator=str(scale["integrator"]),
        gamma_spm_w_inv_mm=float(scale["gamma_spm_w_inv_mm"]),
        frame_velocity_over_c=dispersion.frame_velocity_over_c,
        precision=str(scale["precision"]),
        compile_step=bool(scale["compile_step"]),
        record_snapshots=0,
    )
    grid = SimulationGrid(
        points=int(scale["grid_points"]),
        omega_max_rad_fs=float(scale["omega_max_rad_fs"]),
    )
    pump = _paper_pump(config)
    probe = _paper_probe(config)
    gdd_fs2 = 0.0
    family = unit["family"]
    if family == "uppe_probe":
        probe = replace(
            probe,
            wavelength_nm=float(unit["parameters"]["probe_wavelength_nm"]),
        )
    elif family == "uppe_power":
        pump = replace(
            pump,
            average_power_w=float(unit["parameters"]["pump_power_mw"]) * 1.0e-3,
        )
    elif family == "uppe_chirp":
        prechirp_cm = float(unit["parameters"]["prechirp_cm"])
        gdd_fs2 = prechirp_cm * float(
            config["reconstructed_parameters"]["silica_gdd_fs2_per_cm_at_800nm"]
        )
    elif family == "convergence":
        if unit["parameters"]["variant"] == "grid_refinement":
            grid = SimulationGrid(
                points=2 * grid.points,
                omega_max_rad_fs=grid.omega_max_rad_fs,
            )
        else:
            propagation = replace(propagation, step_mm=0.5 * propagation.step_mm)

    solver = AnalyticSignalUPPE(grid, propagation, dispersion, device)
    initial, weights = _build_batch_with_prechirp(
        solver, pump, probe, gdd_fs2, propagation.complex_dtype
    )
    result = solver.propagate(initial, weights)
    spectra = result.final_spectral_power.numpy()
    signal = stimulated_signal(result.final_spectral_power).numpy()
    conjugated = conjugated_spm_contribution(result.final_spectral_power).numpy()
    omega = result.omega_rad_fs.numpy()
    wavelength = np.full_like(omega, np.nan, dtype=float)
    positive = omega > 0
    wavelength[positive] = 2.0 * np.pi * 299.792458 / omega[positive]
    markers = phase_matching_markers(pump, probe, dispersion)
    metrics = {
        "family": family,
        "grid": asdict(grid),
        "propagation": propagation.as_dict(),
        "pump": asdict(pump),
        "probe": asdict(probe),
        "prechirp_gdd_fs2": gdd_fs2,
        "phase_matching": markers,
        "runtime_seconds": result.runtime_seconds,
        "device": result.device,
        "maximum_embedded_relative_error": result.maximum_embedded_relative_error,
        "signal_samples": {
            name: {
                "wavelength_nm": marker.get("wavelength_nm"),
                "stimulated_power": _nearest_power(
                    wavelength,
                    signal[0],
                    marker.get("wavelength_nm"),
                ),
                "conjugated_spm_power": _nearest_power(
                    wavelength,
                    conjugated,
                    marker.get("wavelength_nm"),
                ),
            }
            for name, marker in markers.items()
            if isinstance(marker, dict)
        },
        "paper_exact": False,
        "blockers": [
            "measured_fibre_dispersion_coefficients_not_published",
            "measured_pulse_shape_delay_and_chirp_not_published",
        ],
    }
    return {
        "omega_rad_fs": omega,
        "wavelength_nm": wavelength,
        "final_spectral_power": spectra,
        "stimulated_signal": signal,
        "conjugated_spm_contribution": conjugated,
    }, metrics


def _sideband_unit(
    config: dict[str, Any], profile: dict[str, Any], unit: dict[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    probe = replace(
        _paper_probe(config),
        wavelength_nm=float(unit["parameters"]["probe_wavelength_nm"]),
    )
    dispersion = CleanRoomPCFDispersion(_geometry(config))
    markers = phase_matching_markers(_paper_pump(config), probe, dispersion)
    hawking = markers["hawking_partner"].get("wavelength_nm")
    shift = markers.get("backreaction_shift_nm")
    if hawking is None or shift is None:
        raise RuntimeError("formula-only surrogate did not resolve sideband centres")
    wavelength = np.linspace(
        float(profile["fig4_formula_family"]["wavelength_nm"][0]),
        float(profile["fig4_formula_family"]["wavelength_nm"][1]),
        int(profile["fig4_formula_family"]["points"]),
    )
    curves: list[np.ndarray] = []
    contracts: list[dict[str, float]] = []
    for width in profile["fig4_formula_family"]["spectral_width_rad_fs"]:
        for modulation in profile["fig4_formula_family"]["modulation_x"]:
            for ratio in profile["fig4_formula_family"]["backreaction_to_hawking"]:
                parameters = SidebandParameters(
                    hawking_wavelength_nm=float(hawking),
                    backreaction_shift_nm=float(shift),
                    spectral_width_rad_fs=float(width),
                    modulation_x=float(modulation),
                    hawking_intensity=1.0,
                    backreaction_intensity=float(ratio),
                )
                curve = sideband_spectrum(
                    wavelength,
                    parameters,
                    mu=float(unit["parameters"]["mu"]),
                )
                curves.append(curve / max(float(np.max(curve)), 1.0e-30))
                contracts.append(parameters.as_dict())
    metrics = {
        "panel": unit["parameters"]["panel"],
        "probe_wavelength_nm": probe.wavelength_nm,
        "mu": unit["parameters"]["mu"],
        "phase_matching": markers,
        "family_members": len(curves),
        "parameter_contracts": contracts,
        "paper_exact": False,
        "blocker": "six_fitted_D1_parameter_tables_and_raw_spectra_not_published",
        "scientific_meaning": "formula sensitivity family, not a fit to Fig. 4 pixels",
    }
    return {
        "wavelength_nm": wavelength,
        "normalized_formula_curves": np.asarray(curves),
    }, metrics


def _thermal_unit(
    profile: dict[str, Any], unit: dict[str, Any]
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    settings = profile["fig5_formula_family"]
    ratio = np.linspace(
        float(settings["frequency_ratio"][0]),
        float(settings["frequency_ratio"][1]),
        int(settings["points"]),
    )
    slope = float(settings["dimensionless_slope_gauge"])
    hawking = float(settings["hawking_intercept_gauge"]) + slope * ratio
    backreaction = float(settings["backreaction_intercept_gauge"]) + slope * ratio
    metrics = {
        "slope_hawking": slope,
        "slope_backreaction": slope,
        "relative_slope_difference": 0.0,
        "paper_exact": False,
        "blocker": "raw_NRR_Hawking_backreaction_counts_and_fitted_frequencies_not_published",
        "scientific_meaning": "dimensionless equal-slope consequence of Eqs. D2-D3",
    }
    return {
        "frequency_ratio": ratio,
        "log_p_hawking": hawking,
        "log_p_backreaction": backreaction,
    }, metrics


def run_unit(
    workspace: Path,
    config: dict[str, Any],
    profile_name: str,
    unit: dict[str, Any],
    output_root: Path,
    config_digest: str,
    code_digest: str,
    device: str | None,
    resume: bool,
) -> dict[str, Any]:
    json_path = output_root / "units" / f"{unit['unit_id']}.json"
    npz_path = output_root / "units" / f"{unit['unit_id']}.npz"
    unit_digest = sha256_bytes(canonical_json(unit))
    if resume and json_path.exists() and npz_path.exists():
        existing = json.loads(json_path.read_text())
        if (
            existing.get("config_sha256") == config_digest
            and existing.get("implementation_sha256") == code_digest
            and existing.get("unit_sha256") == unit_digest
            and existing.get("npz_sha256") == sha256_file(npz_path)
        ):
            return {"unit_id": unit["unit_id"], "status": "resumed"}

    profile = config["profiles"][profile_name]
    if unit["family"] == "dispersion":
        arrays, metrics = _dispersion_unit(config, profile, unit)
    elif unit["family"].startswith("uppe_") or unit["family"] == "convergence":
        arrays, metrics = _propagation_unit(
            workspace, config, profile, unit, device
        )
    elif unit["family"] == "sideband_family":
        arrays, metrics = _sideband_unit(config, profile, unit)
    elif unit["family"] == "thermal_family":
        arrays, metrics = _thermal_unit(profile, unit)
    else:  # pragma: no cover - plan construction owns this invariant
        raise ValueError(f"unknown unit family: {unit['family']}")

    for name, array in arrays.items():
        if not np.all(np.isfinite(array) | np.isnan(array)):
            raise RuntimeError(f"non-finite array outside declared NaN mask: {name}")
    _atomic_npz(npz_path, arrays)
    payload = {
        "schema_version": 1,
        "status": "completed",
        "profile": profile_name,
        "unit": unit,
        "unit_sha256": unit_digest,
        "config_sha256": config_digest,
        "implementation_sha256": code_digest,
        "npz_path": str(npz_path.relative_to(workspace)),
        "npz_sha256": sha256_file(npz_path),
        "metrics": metrics,
        "scientific_input_boundary": {
            "paper_equations_and_scalar_parameters_only": True,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "digitized_curves_used": False,
            "source_pixels_used": False,
        },
    }
    _atomic_json(json_path, payload)
    return {"unit_id": unit["unit_id"], "status": "completed"}


def _load_records(output_root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted((output_root / "units").glob("*.json")):
        payload = json.loads(path.read_text())
        records[payload["unit"]["unit_id"]] = payload
    return records


def aggregate(
    workspace: Path,
    config: dict[str, Any],
    profile_name: str,
    plan: list[dict[str, Any]],
    output_root: Path,
    config_digest: str,
    code_digest: str,
) -> dict[str, Any]:
    records = _load_records(output_root)
    expected_ids = {unit["unit_id"] for unit in plan}
    valid: dict[str, dict[str, Any]] = {}
    stale: list[str] = []
    for unit_id in sorted(expected_ids & records.keys()):
        record = records[unit_id]
        npz_path = workspace / record["npz_path"]
        if (
            record.get("config_sha256") != config_digest
            or record.get("implementation_sha256") != code_digest
            or not npz_path.exists()
            or record.get("npz_sha256") != sha256_file(npz_path)
        ):
            stale.append(unit_id)
        else:
            valid[unit_id] = record
    missing = sorted(expected_ids - valid.keys())
    forbidden = [
        unit_id
        for unit_id, record in valid.items()
        if any(
            record["scientific_input_boundary"][name]
            for name in (
                "author_code_used",
                "author_numeric_arrays_used",
                "digitized_curves_used",
                "source_pixels_used",
            )
        )
    ]
    horizon_passes = [
        bool(record["metrics"].get("horizon_feature_passed"))
        for record in valid.values()
        if record["unit"]["family"] == "dispersion"
    ]
    acceptance = {
        "schema_version": 1,
        "profile": profile_name,
        "expected_units": len(plan),
        "completed_units": len(valid),
        "complete": not missing and not stale,
        "missing_units": missing,
        "stale_units": stale,
        "forbidden_scientific_inputs": forbidden,
        "static_clean_input_boundary_passed": not forbidden,
        "runtime_file_access_attested": False,
        "paper_parameters_executed": profile_name == "paper" and not missing and not stale,
        "paper_exact": False,
        "dispersion_horizon_feature_passed_by_any_declared_surrogate": any(horizon_passes),
        "science_status": (
            "blocked_missing_paper_parameters"
            if not any(horizon_passes)
            else "reconstructed_feature_only"
        ),
        "blocking_missing_inputs": config["missing_indispensable_inputs"],
    }
    _atomic_json(output_root / "acceptance.json", acceptance)
    manifest = {
        "schema_version": 1,
        "profile": profile_name,
        "config_sha256": config_digest,
        "implementation_sha256": code_digest,
        "unit_output_hashes": {
            unit_id: record["npz_sha256"] for unit_id, record in sorted(valid.items())
        },
        "acceptance_sha256": sha256_file(output_root / "acceptance.json"),
    }
    _atomic_json(output_root / "manifest.json", manifest)
    return acceptance
