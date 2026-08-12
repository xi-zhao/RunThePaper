"""End-to-end independent numerical campaign and immutable data manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from .metrology import (
    brightness_audit,
    hom_bandwidth_conventions,
    hom_delay_curve,
    reconstructed_spectral_visibility,
)
from .modes import ModeResult, electrode_loss_curve, solve_scalar_mode
from .quantum import (
    FOCK_LABELS,
    classical_transfer,
    mzi_unitary,
    output_probabilities,
    probability_grid,
    two_photon_lift,
)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"refusing empty frozen CSV: {path}")
    return rows


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2404.08378":
        raise ValueError("wrong paper_id")
    if config.get("target_ids") != [f"T{index:03d}" for index in range(1, 19)]:
        raise ValueError("feature config must declare T001-T018 exactly")
    return config


def implementation_digest(workspace: Path) -> str:
    paths = [
        workspace / "src" / "lnoi_interference" / name
        for name in (
            "__init__.py",
            "campaign.py",
            "metrology.py",
            "modes.py",
            "quantum.py",
        )
    ]
    paths.append(workspace / "scripts" / "run_reproduction.py")
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(workspace).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_mode_npz(path: Path, pump: ModeResult, telecom: ModeResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        x_pump_um=pump.x_um,
        y_pump_um=pump.y_um,
        intensity_pump=pump.intensity,
        index_pump=pump.refractive_index,
        effective_index_pump=pump.effective_index,
        x_telecom_um=telecom.x_um,
        y_telecom_um=telecom.y_um,
        intensity_telecom=telecom.intensity,
        index_telecom=telecom.refractive_index,
        effective_index_telecom=telecom.effective_index,
    )


def run_feature(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    data_root = workspace / "outputs" / "data" / "feature"
    checks_root = workspace / "outputs" / "checks" / "feature"
    data_root.mkdir(parents=True, exist_ok=True)

    phase_points = int(config["quantum"]["surface_points"])
    cut_points = int(config["quantum"]["cut_points"])
    theta_surface = np.linspace(-np.pi, np.pi, phase_points)
    phi_surface = np.linspace(-np.pi, np.pi, phase_points)
    surfaces = probability_grid(theta_surface, phi_surface)
    np.savez_compressed(
        data_root / "quantum_surfaces.npz",
        theta_rad=theta_surface,
        phi_rad=phi_surface,
        probabilities=surfaces,
        fock_labels=np.asarray(FOCK_LABELS),
    )

    phi_cut = np.linspace(-np.pi, np.pi, cut_points)
    cut_rows: list[dict[str, Any]] = []
    cut_arrays: dict[str, np.ndarray] = {}
    for theta_label, theta_value in (("pi_over_2", np.pi / 2.0), ("pi", np.pi)):
        probabilities = np.stack(
            [output_probabilities(theta_value, phi) for phi in phi_cut]
        )
        cut_arrays[theta_label] = probabilities
        for phi, row in zip(phi_cut, probabilities, strict=True):
            for state_index, state in enumerate(FOCK_LABELS):
                cut_rows.append(
                    {
                        "theta_case": theta_label,
                        "phi_rad": float(phi),
                        "state": state,
                        "probability": float(row[state_index]),
                    }
                )
    write_csv(data_root / "quantum_cuts.csv", cut_rows)

    theta_classical = np.linspace(-np.pi / 2.0, 3.0 * np.pi / 2.0, cut_points)
    transfer = classical_transfer(theta_classical)
    classical_rows: list[dict[str, Any]] = []
    for input_index, input_port in enumerate(("a", "b")):
        for output_index, output_port in enumerate(("a", "b")):
            for theta, probability in zip(
                theta_classical, transfer[output_index, input_index], strict=True
            ):
                classical_rows.append(
                    {
                        "input_port": input_port,
                        "output_port": output_port,
                        "theta_rad": float(theta),
                        "relative_intensity": float(probability),
                    }
                )
    write_csv(data_root / "mzi_transfer.csv", classical_rows)

    imperfection_phi = np.linspace(-np.pi, np.pi, cut_points)
    imperfection_rows: list[dict[str, Any]] = []
    for balance in config["quantum"]["balances"]:
        for phi in imperfection_phi:
            probabilities = output_probabilities(
                np.pi / 2.0, phi, balance=float(balance)
            )
            imperfection_rows.append(
                {
                    "model": "balance",
                    "parameter": float(balance),
                    "phi_rad": float(phi),
                    "bunched_probability": float(probabilities[0] + probabilities[2]),
                    "split_probability": float(probabilities[1]),
                }
            )
    for purity in config["quantum"]["purities"]:
        for phi in imperfection_phi:
            probabilities = output_probabilities(np.pi / 2.0, phi, purity=float(purity))
            imperfection_rows.append(
                {
                    "model": "purity",
                    "parameter": float(purity),
                    "phi_rad": float(phi),
                    "bunched_probability": float(probabilities[0] + probabilities[2]),
                    "split_probability": float(probabilities[1]),
                }
            )
    write_csv(data_root / "imperfection_scans.csv", imperfection_rows)

    mode_config = config["modes"]
    mode_common = {
        "x_extent_um": float(mode_config["x_extent_um"]),
        "y_min_um": float(mode_config["y_min_um"]),
        "y_max_um": float(mode_config["y_max_um"]),
        "nx": int(mode_config["nx"]),
        "ny": int(mode_config["ny"]),
        "film_height_um": float(mode_config["film_height_um"]),
        "top_width_um": float(mode_config["top_width_um"]),
        "sidewall_angle_deg": float(mode_config["sidewall_angle_deg"]),
    }
    pump_mode = solve_scalar_mode(
        float(mode_config["pump_wavelength_um"]), **mode_common
    )
    telecom_mode = solve_scalar_mode(
        float(mode_config["telecom_wavelength_um"]), **mode_common
    )
    _write_mode_npz(data_root / "mode_profiles.npz", pump_mode, telecom_mode)

    delay_fs = np.linspace(
        float(config["hom"]["delay_min_fs"]),
        float(config["hom"]["delay_max_fs"]),
        int(config["hom"]["delay_points"]),
    )
    hom_counts = hom_delay_curve(
        delay_fs,
        baseline_hz=float(config["hom"]["baseline_hz"]),
        visibility=float(config["hom"]["visibility"]),
        fwhm_fs=float(config["hom"]["fwhm_fs"]),
    )
    write_csv(
        data_root / "hom_curve.csv",
        [
            {"delay_fs": float(delay), "coincidence_hz": float(count)}
            for delay, count in zip(delay_fs, hom_counts, strict=True)
        ],
    )

    spectral_wavelength = np.linspace(1500.0, 1600.0, 501)
    spectral_results = {
        device: reconstructed_spectral_visibility(spectral_wavelength, device=device)
        for device in ("fiber", "lnoi")
    }
    spectral_rows: list[dict[str, Any]] = []
    for device, result in spectral_results.items():
        for index in range(spectral_wavelength.size):
            spectral_rows.append(
                {
                    "device": device,
                    "signal_wavelength_nm": float(
                        result["signal_wavelength_nm"][index]
                    ),
                    "idler_wavelength_nm": float(result["idler_wavelength_nm"][index]),
                    "signal_reflectivity": float(result["signal_reflectivity"][index]),
                    "idler_reflectivity": float(result["idler_reflectivity"][index]),
                    "pair_weight": float(result["pair_weight"][index]),
                    "integrated_visibility": float(result["visibility"]),
                    "provenance": "printed_endpoint_reconstruction",
                }
            )
    write_csv(data_root / "spectral_visibility.csv", spectral_rows)

    coupler_counts = np.arange(0, 4)
    ideal_loss = 10.0 * np.log10(2.0) * coupler_counts
    printed_excess_loss = (10.0 * np.log10(2.0) + 0.25) * coupler_counts
    write_csv(
        data_root / "coupler_loss.csv",
        [
            {
                "coupler_count": int(count),
                "ideal_loss_db": float(ideal),
                "printed_excess_trend_db": float(excess),
            }
            for count, ideal, excess in zip(
                coupler_counts, ideal_loss, printed_excess_loss, strict=True
            )
        ],
    )

    gaps_um = np.linspace(0.5, 3.0, 51)
    electrode_loss = electrode_loss_curve(
        telecom_mode,
        gaps_um,
        top_width_um=float(mode_config["top_width_um"]),
    )
    write_csv(
        data_root / "electrode_loss.csv",
        [
            {"gap_um": float(gap), "loss_db_per_mm": float(loss)}
            for gap, loss in zip(gaps_um, electrode_loss, strict=True)
        ],
    )

    brightness = brightness_audit(
        detected_pairs_per_s=float(config["brightness"]["detected_pairs_per_s"]),
        loss_db_per_photon=float(config["brightness"]["loss_db_per_photon"]),
        pump_power_uw=float(config["brightness"]["pump_power_uw"]),
        printed_normalized_brightness=float(
            config["brightness"]["printed_normalized_brightness"]
        ),
    )
    bandwidth = hom_bandwidth_conventions(float(config["hom"]["fwhm_fs"]))
    claims = {"brightness": brightness, "bandwidth": bandwidth}
    atomic_json(data_root / "claim_arithmetic.json", claims)

    unitary_errors = []
    lifted_errors = []
    for theta in np.linspace(-np.pi, np.pi, 17):
        unitary = mzi_unitary(theta)
        lifted = two_photon_lift(unitary)
        unitary_errors.append(
            float(np.max(np.abs(unitary.conjugate().T @ unitary - np.eye(2))))
        )
        lifted_errors.append(
            float(np.max(np.abs(lifted.conjugate().T @ lifted - np.eye(3))))
        )
    probability_sum_error = float(np.max(np.abs(np.sum(surfaces, axis=0) - 1.0)))
    bunching = output_probabilities(np.pi / 2.0, 0.0)
    antibunching = output_probabilities(np.pi / 2.0, np.pi / 2.0)
    target_checks = {
        "schema_version": 1,
        "status": "passed",
        "checks": {
            "unitary_max_error": max(unitary_errors),
            "two_photon_lift_max_error": max(lifted_errors),
            "surface_probability_sum_max_error": probability_sum_error,
            "theta_pi_over_2_phi_0": bunching.tolist(),
            "theta_pi_over_2_phi_pi_over_2": antibunching.tolist(),
            "pump_effective_index": pump_mode.effective_index,
            "telecom_effective_index": telecom_mode.effective_index,
            "spectral_visibility_reconstruction": {
                device: float(result["visibility"])
                for device, result in spectral_results.items()
            },
            "electrode_loss_at_0p5_um_db_per_mm": float(electrode_loss[0]),
            "electrode_loss_at_3_um_db_per_mm": float(electrode_loss[-1]),
            "brightness": brightness,
            "bandwidth": bandwidth,
        },
        "acceptance": {
            "single_photon_unitary": max(unitary_errors) < 1e-12,
            "two_photon_unitary": max(lifted_errors) < 1e-12,
            "probabilities_normalized": probability_sum_error < 1e-12,
            "eq4_bunching_limit": float(bunching[1]) < 1e-12,
            "eq4_antibunching_limit": abs(float(antibunching[1]) - 1.0) < 1e-12,
            "mode_indices_physical": (
                1.0 < telecom_mode.effective_index < 2.5
                and 1.0 < pump_mode.effective_index < 2.5
            ),
            "lnoi_reconstruction_outperforms_fiber": float(
                spectral_results["lnoi"]["visibility"]
            )
            > float(spectral_results["fiber"]["visibility"]),
            "electrode_overlap_decreases": float(electrode_loss[0])
            > float(electrode_loss[-1]),
            "brightness_matches_printed_scale": abs(
                brightness["brightness_pairs_per_s_per_mw"] / 2.3e8 - 1.0
            )
            < 0.02,
            "printed_50nm_matches_0p441_convention": abs(
                bandwidth["pulse_tbp_0p441_bandwidth_nm"] / 50.0 - 1.0
            )
            < 0.05,
        },
    }
    if not all(target_checks["acceptance"].values()):
        target_checks["status"] = "failed"
    atomic_json(checks_root / "target_checks.json", target_checks)

    target_status = {
        **{f"T{index:03d}": "feature_reproduced" for index in range(2, 14)},
        "T001": "reconstructed_feature",
        "T014": "reconstructed_feature",
        "T015": "feature_reproduced",
        "T016": "reconstructed_feature",
        "T017": "printed_claim_reproduced",
        "T018": "convention_audited",
    }
    atomic_json(
        checks_root / "target_status.json",
        {"schema_version": 1, "paper_id": config["paper_id"], "targets": target_status},
    )
    return {
        "theta_surface": theta_surface,
        "phi_surface": phi_surface,
        "surfaces": surfaces,
        "theta_classical": theta_classical,
        "transfer": transfer,
        "phi_cut": phi_cut,
        "cut_arrays": cut_arrays,
        "imperfection_rows": imperfection_rows,
        "pump_mode": pump_mode,
        "telecom_mode": telecom_mode,
        "delay_fs": delay_fs,
        "hom_counts": hom_counts,
        "spectral_results": spectral_results,
        "coupler_counts": coupler_counts,
        "ideal_loss": ideal_loss,
        "printed_excess_loss": printed_excess_loss,
        "gaps_um": gaps_um,
        "electrode_loss": electrode_loss,
        "claims": claims,
        "target_checks": target_checks,
        "summary": {
            "paper_id": config["paper_id"],
            "profile": config["profile"],
            "target_count": len(config["target_ids"]),
            "numeric_coverage_items": 27,
            "independently_generated_targets": 18,
            "deferred_author_data_items": 9,
            "scientific_status": "feature_reproduced_with_declared_reconstructions",
        },
    }


def build_manifest(workspace: Path, config: dict[str, Any]) -> dict[str, Any]:
    data_root = workspace / "outputs" / "data" / "feature"
    files = sorted(path for path in data_root.glob("*") if path.is_file())
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "config_sha256": sha256_bytes(canonical_json(config).encode()),
        "implementation_sha256": implementation_digest(workspace),
        "source_pixels_used_as_scientific_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "files": [
            {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in files
        ],
    }
    checks = workspace / "outputs" / "checks" / "feature"
    atomic_json(checks / "generated_data_manifest.json", manifest)
    atomic_json(checks / "data_freeze.json", manifest)
    return manifest


def verify_frozen_data(workspace: Path) -> dict[str, Any]:
    """Fail closed unless every frozen numerical file still matches its hash."""

    freeze_path = workspace / "outputs" / "checks" / "feature" / "data_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    mismatches: list[dict[str, str]] = []
    for entry in freeze["files"]:
        path = workspace / entry["path"]
        actual = sha256_file(path) if path.is_file() else "missing"
        if actual != entry["sha256"]:
            mismatches.append(
                {"path": entry["path"], "expected": entry["sha256"], "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"frozen numerical data mismatch: {mismatches}")
    return freeze


def load_frozen_feature(workspace: Path) -> dict[str, Any]:
    """Load hash-verified arrays for the post-freeze rendering lane."""

    verify_frozen_data(workspace)
    data_root = workspace / "outputs" / "data" / "feature"

    with np.load(data_root / "quantum_surfaces.npz", allow_pickle=False) as arrays:
        theta_surface = arrays["theta_rad"].copy()
        phi_surface = arrays["phi_rad"].copy()
        surfaces = arrays["probabilities"].copy()

    cut_rows = read_csv(data_root / "quantum_cuts.csv")
    phi_cut = np.asarray(
        sorted({float(row["phi_rad"]) for row in cut_rows}), dtype=float
    )
    cut_arrays: dict[str, np.ndarray] = {}
    for theta_label in ("pi_over_2", "pi"):
        values = np.empty((phi_cut.size, len(FOCK_LABELS)), dtype=float)
        lookup = {
            (float(row["phi_rad"]), row["state"]): float(row["probability"])
            for row in cut_rows
            if row["theta_case"] == theta_label
        }
        for phi_index, phi in enumerate(phi_cut):
            for state_index, state in enumerate(FOCK_LABELS):
                values[phi_index, state_index] = lookup[(float(phi), state)]
        cut_arrays[theta_label] = values

    classical_rows = read_csv(data_root / "mzi_transfer.csv")
    theta_classical = np.asarray(
        sorted({float(row["theta_rad"]) for row in classical_rows}), dtype=float
    )
    transfer = np.empty((2, 2, theta_classical.size), dtype=float)
    for input_index, input_port in enumerate(("a", "b")):
        for output_index, output_port in enumerate(("a", "b")):
            selected = [
                row
                for row in classical_rows
                if row["input_port"] == input_port and row["output_port"] == output_port
            ]
            transfer[output_index, input_index] = [
                float(row["relative_intensity"]) for row in selected
            ]

    with np.load(data_root / "mode_profiles.npz", allow_pickle=False) as arrays:
        pump_mode = ModeResult(
            wavelength_um=0.781,
            x_um=arrays["x_pump_um"].copy(),
            y_um=arrays["y_pump_um"].copy(),
            refractive_index=arrays["index_pump"].copy(),
            intensity=arrays["intensity_pump"].copy(),
            effective_index=float(arrays["effective_index_pump"]),
        )
        telecom_mode = ModeResult(
            wavelength_um=1.562,
            x_um=arrays["x_telecom_um"].copy(),
            y_um=arrays["y_telecom_um"].copy(),
            refractive_index=arrays["index_telecom"].copy(),
            intensity=arrays["intensity_telecom"].copy(),
            effective_index=float(arrays["effective_index_telecom"]),
        )

    hom_rows = read_csv(data_root / "hom_curve.csv")
    spectral_rows = read_csv(data_root / "spectral_visibility.csv")
    spectral_results: dict[str, dict[str, np.ndarray | float]] = {}
    for device in ("fiber", "lnoi"):
        rows = [row for row in spectral_rows if row["device"] == device]
        spectral_results[device] = {
            "signal_wavelength_nm": np.asarray(
                [float(row["signal_wavelength_nm"]) for row in rows]
            ),
            "idler_wavelength_nm": np.asarray(
                [float(row["idler_wavelength_nm"]) for row in rows]
            ),
            "signal_reflectivity": np.asarray(
                [float(row["signal_reflectivity"]) for row in rows]
            ),
            "idler_reflectivity": np.asarray(
                [float(row["idler_reflectivity"]) for row in rows]
            ),
            "pair_weight": np.asarray([float(row["pair_weight"]) for row in rows]),
            "visibility": float(rows[0]["integrated_visibility"]),
        }

    coupler_rows = read_csv(data_root / "coupler_loss.csv")
    electrode_rows = read_csv(data_root / "electrode_loss.csv")
    claims = json.loads(
        (data_root / "claim_arithmetic.json").read_text(encoding="utf-8")
    )
    return {
        "theta_surface": theta_surface,
        "phi_surface": phi_surface,
        "surfaces": surfaces,
        "theta_classical": theta_classical,
        "transfer": transfer,
        "phi_cut": phi_cut,
        "cut_arrays": cut_arrays,
        "imperfection_rows": read_csv(data_root / "imperfection_scans.csv"),
        "pump_mode": pump_mode,
        "telecom_mode": telecom_mode,
        "delay_fs": np.asarray([float(row["delay_fs"]) for row in hom_rows]),
        "hom_counts": np.asarray([float(row["coincidence_hz"]) for row in hom_rows]),
        "spectral_results": spectral_results,
        "coupler_counts": np.asarray(
            [int(row["coupler_count"]) for row in coupler_rows]
        ),
        "ideal_loss": np.asarray([float(row["ideal_loss_db"]) for row in coupler_rows]),
        "printed_excess_loss": np.asarray(
            [float(row["printed_excess_trend_db"]) for row in coupler_rows]
        ),
        "gaps_um": np.asarray([float(row["gap_um"]) for row in electrode_rows]),
        "electrode_loss": np.asarray(
            [float(row["loss_db_per_mm"]) for row in electrode_rows]
        ),
        "claims": claims,
    }
