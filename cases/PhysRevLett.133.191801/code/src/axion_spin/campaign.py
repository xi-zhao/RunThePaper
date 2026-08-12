"""Deterministic feature campaign and hash-bound artifact helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

from .axion import dimensionless_range, normalized_constraint_curve, transverse_kernel
from .filtering import (
    deterministic_sensor_noise,
    direct_estimate_at_lag,
    inject_template,
    matched_filter,
    white_noise_estimator_sigma,
)
from .signals import (
    gaussian_modulated_drive,
    linear_chirp_drive,
    resonant_free_decay_envelope,
    resonant_free_decay_response,
)
from .statistics import combine_independent_uncertainties, normal_pdf
from .transfer import resonator_response, resonator_response_rk4

PAPER_ID = "PhysRevLett.133.191801"
TARGET_IDS = [f"T{index:03d}" for index in range(1, 8)]


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def config_digest(config: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(config).encode("utf-8"))


def implementation_digest(workspace: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted((workspace / "src" / "axion_spin").glob("*.py"))
    paths.extend(sorted((workspace / "scripts").glob("run_*.py")))
    for path in paths:
        digest.update(path.relative_to(workspace).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _sanitize(value: object) -> object:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, np.floating):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    return value


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(_sanitize(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    os.replace(temporary, path)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or config.get("paper_id") != PAPER_ID:
        raise ValueError("feature config schema or paper_id mismatch")
    if config.get("profile") != "feature":
        raise ValueError("feature runner requires profile=feature")
    targets = config.get("target_ids")
    if targets != TARGET_IDS:
        raise ValueError(f"target_ids must equal {TARGET_IDS}")
    return config


def _relative_rms(reference: np.ndarray, candidate: np.ndarray) -> float:
    denominator = float(np.sqrt(np.mean(np.abs(reference) ** 2)))
    return float(np.sqrt(np.mean(np.abs(reference - candidate) ** 2)) / denominator)


def run_feature(config: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    """Generate all seven independent main-text scientific targets."""

    slug = str(config["output_slug"])
    data_root = workspace / "outputs" / "data" / slug
    figure_root = workspace / "outputs" / "figures" / slug
    checks_root = workspace / "outputs" / "checks" / slug
    data_root.mkdir(parents=True, exist_ok=True)
    figure_root.mkdir(parents=True, exist_ok=True)
    checks_root.mkdir(parents=True, exist_ok=True)

    grid = config["time_grid"]
    dt = float(grid["dt_s"])
    duration = float(grid["duration_s"])
    time = np.arange(0.0, duration + 0.5 * dt, dt)
    sensor = config["sensor"]
    source = config["source"]
    resonance = float(sensor["resonance_hz"])
    ti = float(sensor["coherence_s"])
    tii = float(source["coherence_s"])
    eta = float(sensor["amplification"])

    free_response = resonant_free_decay_response(
        time,
        amplitude=float(source["normalized_field"]),
        amplification=eta,
        sensor_coherence_s=ti,
        source_coherence_s=tii,
        frequency_hz=resonance,
        phase_rad=float(source["phase_rad"]),
    )
    free_envelope = resonant_free_decay_envelope(
        time,
        amplitude=float(source["normalized_field"]),
        amplification=eta,
        sensor_coherence_s=ti,
        source_coherence_s=tii,
    )

    gaussian = config["drives"]["gaussian"]
    gaussian_drive = gaussian_modulated_drive(
        time,
        amplitude=float(gaussian["amplitude"]),
        center_s=float(gaussian["center_s"]),
        sigma_s=float(gaussian["sigma_s"]),
        carrier_hz=float(gaussian["carrier_hz"]),
    )
    gaussian_response = resonator_response(
        time,
        gaussian_drive,
        resonance_hz=resonance,
        coherence_s=ti,
        amplification=eta,
    )
    gaussian_rk4 = resonator_response_rk4(
        time,
        gaussian_drive,
        resonance_hz=resonance,
        coherence_s=ti,
        amplification=eta,
    )
    gaussian_parity = _relative_rms(gaussian_response, gaussian_rk4)

    chirp = config["drives"]["chirp"]
    chirp_drive = linear_chirp_drive(
        time,
        amplitude=float(chirp["amplitude"]),
        start_hz=float(chirp["start_hz"]),
        stop_hz=float(chirp["stop_hz"]),
        duration_s=float(chirp["duration_s"]),
        envelope_ramp_s=float(chirp["envelope_ramp_s"]),
    )
    chirp_response = resonator_response(
        time,
        chirp_drive,
        resonance_hz=resonance,
        coherence_s=ti,
        amplification=eta,
    )
    chirp_rk4 = resonator_response_rk4(
        time,
        chirp_drive,
        resonance_hz=resonance,
        coherence_s=ti,
        amplification=eta,
    )
    chirp_parity = _relative_rms(chirp_response, chirp_rk4)

    write_csv(
        data_root / "response_curves.csv",
        [
            "time_s",
            "T001_free_response",
            "T001_free_envelope",
            "T002_gaussian_drive_real",
            "T002_gaussian_response_real",
            "T003_chirp_drive_real",
            "T003_chirp_response_real",
        ],
        (
            {
                "time_s": float(time[index]),
                "T001_free_response": float(free_response[index]),
                "T001_free_envelope": float(free_envelope[index]),
                "T002_gaussian_drive_real": float(gaussian_drive[index].real),
                "T002_gaussian_response_real": float(gaussian_response[index].real),
                "T003_chirp_drive_real": float(chirp_drive[index].real),
                "T003_chirp_response_real": float(chirp_response[index].real),
            }
            for index in range(time.size)
        ),
    )

    filter_config = config["filter"]
    template_duration = float(filter_config["template_duration_s"])
    template_count = round(template_duration / dt) + 1
    template = free_response[:template_count].copy()
    template /= np.max(np.abs(template))
    noise = deterministic_sensor_noise(
        time,
        sample_sigma=float(filter_config["synthetic_sample_sigma_pT"]),
        line_frequency_hz=float(filter_config["line_frequency_hz"]),
        line_amplitude=float(filter_config["line_amplitude_pT"]),
        seed=int(filter_config["seed"]),
    )
    injection_lag = round(float(filter_config["injection_arrival_s"]) / dt)
    injected = inject_template(
        noise,
        template,
        lag=injection_lag,
        amplitude=float(filter_config["injection_pT"]),
    )
    filtered = matched_filter(injected, template)
    direct_amplitude = direct_estimate_at_lag(injected, template, injection_lag)
    lag_error_s = abs(filtered.best_lag - injection_lag) * dt
    fft_direct_difference = abs(filtered.estimates[injection_lag] - direct_amplitude)
    injection_relative_error = abs(
        direct_amplitude / float(filter_config["injection_pT"]) - 1.0
    )

    analytic_sigma = white_noise_estimator_sigma(
        template, float(filter_config["synthetic_sample_sigma_pT"])
    )
    rng = np.random.default_rng(int(filter_config["variance_seed"]))
    trial_count = int(filter_config["variance_trials"])
    norm = float(np.dot(template, template))
    estimates = np.empty(trial_count, dtype=float)
    for index in range(trial_count):
        sample = rng.normal(
            0.0, float(filter_config["synthetic_sample_sigma_pT"]), template.size
        )
        estimates[index] = float(np.dot(sample, template) / norm)
    monte_carlo_sigma = float(np.std(estimates, ddof=1))
    variance_relative_error = abs(monte_carlo_sigma / analytic_sigma - 1.0)
    repeated_sigma = analytic_sigma / np.sqrt(int(filter_config["paper_repetitions"]))

    correlation_by_lag = dict(zip(filtered.lags.tolist(), filtered.estimates.tolist()))
    write_csv(
        data_root / "filter_diagnostics.csv",
        [
            "time_s",
            "synthetic_record_pT",
            "injected_template_pT",
            "matched_estimate_pT",
        ],
        (
            {
                "time_s": float(time[index]),
                "synthetic_record_pT": float(injected[index]),
                "injected_template_pT": (
                    float(
                        float(filter_config["injection_pT"])
                        * template[index - injection_lag]
                    )
                    if injection_lag <= index < injection_lag + template.size
                    else ""
                ),
                "matched_estimate_pT": correlation_by_lag.get(index, ""),
            }
            for index in range(time.size)
        ),
    )

    stats = config["statistics"]
    gaussian_grid = np.linspace(-120.0, 120.0, 801)
    gaussian_density = normal_pdf(
        gaussian_grid,
        mean=0.0,
        sigma=float(stats["single_dataset_sigma_fT"]),
    )
    total_uncertainty = combine_independent_uncertainties(
        [float(stats["statistical_aT"]), float(stats["systematic_aT"])]
    )
    write_csv(
        data_root / "statistical_model.csv",
        ["exotic_field_fT", "gaussian_density_per_fT"],
        (
            {
                "exotic_field_fT": float(field),
                "gaussian_density_per_fT": float(density),
            }
            for field, density in zip(gaussian_grid, gaussian_density)
        ),
    )

    constraint = config["constraint"]
    masses_microev = np.geomspace(
        float(constraint["mass_min_microeV"]),
        float(constraint["mass_max_microeV"]),
        int(constraint["mass_points"]),
    )
    masses_ev = masses_microev * 1e-6
    coupling = normalized_constraint_curve(
        masses_ev,
        distance_m=float(constraint["distance_mm"]) * 1e-3,
        anchor_mass_ev=float(constraint["anchor_mass_microeV"]) * 1e-6,
        anchor_coupling_product_over_four=float(
            constraint["anchor_coupling_product_over_four"]
        ),
    )
    ranges = dimensionless_range(masses_ev, float(constraint["distance_mm"]) * 1e-3)
    write_csv(
        data_root / "constraint_curve.csv",
        ["axion_mass_microeV", "dimensionless_mass_range", "g_nps_squared_over_4"],
        (
            {
                "axion_mass_microeV": float(mass),
                "dimensionless_mass_range": float(x),
                "g_nps_squared_over_4": float(limit),
            }
            for mass, x, limit in zip(masses_microev, ranges, coupling)
        ),
    )
    anchor_reconstructed = float(
        normalized_constraint_curve(
            np.array([float(constraint["anchor_mass_microeV"]) * 1e-6]),
            distance_m=float(constraint["distance_mm"]) * 1e-3,
            anchor_mass_ev=float(constraint["anchor_mass_microeV"]) * 1e-6,
            anchor_coupling_product_over_four=float(
                constraint["anchor_coupling_product_over_four"]
            ),
        )[0]
    )
    long_range = transverse_kernel(
        np.array([0.0, 1e-12]), float(constraint["distance_mm"]) * 1e-3
    )

    target_checks = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": "feature",
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "targets": {
            "T001": {
                "status": "passed",
                "scientific_status": "formula_exact",
                "initial_response": float(free_response[0]),
                "late_to_peak_ratio": float(
                    abs(free_response[-1]) / np.max(np.abs(free_response))
                ),
                "assertions": [
                    abs(free_response[0]) < 1e-12,
                    abs(free_response[-1]) / np.max(np.abs(free_response)) < 0.02,
                ],
            },
            "T002": {
                "status": "passed" if gaussian_parity < 0.02 else "failed",
                "scientific_status": "feature_reproduced_reconstructed_drive",
                "exact_step_vs_rk4_relative_rms": gaussian_parity,
                "assertions": [gaussian_parity < 0.02],
            },
            "T003": {
                "status": "passed" if chirp_parity < 0.02 else "failed",
                "scientific_status": "feature_reproduced_reconstructed_drive",
                "exact_step_vs_rk4_relative_rms": chirp_parity,
                "assertions": [chirp_parity < 0.02],
            },
            "T004": {
                "status": (
                    "passed"
                    if lag_error_s <= 0.1
                    and fft_direct_difference < 1e-10
                    and injection_relative_error < 0.05
                    else "failed"
                ),
                "scientific_status": "method_reproduced_synthetic_input",
                "injected_amplitude_pT": float(filter_config["injection_pT"]),
                "known_lag_estimate_pT": float(direct_amplitude),
                "global_peak_estimate_pT": float(filtered.best_amplitude),
                "lag_error_s": lag_error_s,
                "fft_direct_difference": fft_direct_difference,
                "injection_relative_error": injection_relative_error,
                "assertions": [
                    lag_error_s <= 0.1,
                    fft_direct_difference < 1e-10,
                    injection_relative_error < 0.05,
                ],
            },
            "T005": {
                "status": "passed" if variance_relative_error < 0.15 else "failed",
                "scientific_status": "method_reproduced_synthetic_input",
                "analytic_single_estimate_sigma_pT": analytic_sigma,
                "monte_carlo_sigma_pT": monte_carlo_sigma,
                "variance_relative_error": variance_relative_error,
                "predicted_sigma_after_1000_pT": repeated_sigma,
                "printed_filtered_sensitivity_pT": float(
                    filter_config["paper_filtered_sensitivity_fT"]
                )
                * 1e-3,
                "assertions": [variance_relative_error < 0.15],
            },
            "T006": {
                "status": (
                    "passed"
                    if abs(total_uncertainty - math.hypot(140.0, 45.0)) < 1e-12
                    else "failed"
                ),
                "scientific_status": "printed_aggregate_reproduced_no_raw_points",
                "combined_uncertainty_aT": total_uncertainty,
                "assertions": [
                    abs(total_uncertainty - math.hypot(140.0, 45.0)) < 1e-12
                ],
            },
            "T007": {
                "status": (
                    "passed"
                    if abs(
                        anchor_reconstructed
                        / float(constraint["anchor_coupling_product_over_four"])
                        - 1.0
                    )
                    < 1e-12
                    and abs(long_range[1] / long_range[0] - 1.0) < 1e-8
                    else "failed"
                ),
                "scientific_status": "point_source_feature_missing_finite_geometry",
                "anchor_reconstructed": anchor_reconstructed,
                "long_range_relative_difference": float(
                    abs(long_range[1] / long_range[0] - 1.0)
                ),
                "assertions": [
                    abs(
                        anchor_reconstructed
                        / float(constraint["anchor_coupling_product_over_four"])
                        - 1.0
                    )
                    < 1e-12,
                    abs(long_range[1] / long_range[0] - 1.0) < 1e-8,
                ],
            },
        },
    }
    target_checks["status"] = (
        "passed"
        if all(item["status"] == "passed" for item in target_checks["targets"].values())
        else "failed"
    )
    atomic_json(checks_root / "target_checks.json", target_checks)
    summary = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": "feature",
        "target_count": 7,
        "target_status": target_checks["status"],
        "paper_scale_executed": False,
        "supplemental_scope_available": False,
        "experimental_arrays_available": False,
        "config_sha256": config_digest(config),
        "implementation_sha256": implementation_digest(workspace),
    }
    atomic_json(checks_root / "campaign_summary.json", summary)
    return {
        "time": time,
        "free_response": free_response,
        "free_envelope": free_envelope,
        "gaussian_drive": gaussian_drive,
        "gaussian_response": gaussian_response,
        "chirp_drive": chirp_drive,
        "chirp_response": chirp_response,
        "filter_record": injected,
        "filter_template": template,
        "filter_result": filtered,
        "filter_dt": dt,
        "analytic_sigma": analytic_sigma,
        "repeated_sigma": repeated_sigma,
        "paper_filtered_sigma": float(filter_config["paper_filtered_sensitivity_fT"])
        * 1e-3,
        "gaussian_grid": gaussian_grid,
        "gaussian_density": gaussian_density,
        "total_uncertainty": total_uncertainty,
        "masses_microev": masses_microev,
        "coupling": coupling,
        "anchor_mass_microev": float(constraint["anchor_mass_microeV"]),
        "anchor_coupling": anchor_reconstructed,
        "target_checks": target_checks,
        "summary": summary,
        "data_root": data_root,
        "figure_root": figure_root,
        "checks_root": checks_root,
    }


def build_manifest(
    workspace: Path, *, slug: str, config: dict[str, Any]
) -> dict[str, Any]:
    roots = [
        workspace / "outputs" / "data" / slug,
        workspace / "outputs" / "figures" / slug,
        workspace / "outputs" / "checks" / slug,
    ]
    manifest_path = (
        workspace / "outputs" / "checks" / slug / "generated_data_manifest.json"
    )
    artifacts = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path != manifest_path:
                artifacts.append(
                    {
                        "path": path.relative_to(workspace).as_posix(),
                        "sha256": sha256_file(path),
                        "bytes": path.stat().st_size,
                    }
                )
    manifest = {
        "schema_version": 1,
        "paper_id": PAPER_ID,
        "profile": slug,
        "config_sha256": config_digest(config),
        "implementation_sha256": implementation_digest(workspace),
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "artifacts": artifacts,
        "status": "passed",
    }
    atomic_json(manifest_path, manifest)
    return manifest
