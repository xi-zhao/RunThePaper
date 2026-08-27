#!/usr/bin/env python3
"""Run the independent S4--S9 numerical campaign without reading source art."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from supplemental_campaign import (  # noqa: E402
    exact_cylinder_phase_rows,
    exact_cylinder_spectrum_arrays,
    exact_model_phase_rows,
    s4_finite_size_scan,
    s4_parameter_rows,
    similarity_transform_residual,
    skin_profile_arrays,
)


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _atomic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", choices=("smoke", "paper"), default="paper")
    parser.add_argument("--output-root")
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()

    config_path = (ROOT / arguments.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = config["profiles"][arguments.profile]
    output_root = (
        Path(arguments.output_root).resolve()
        if arguments.output_root
        else ROOT / "outputs" / "supplemental_campaign" / arguments.profile
    )
    manifest_path = output_root / "manifest.json"
    config_digest = _sha256(config_path)
    if arguments.resume and manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prior.get("config_sha256") == config_digest and prior.get("profile") == arguments.profile:
            print(json.dumps({"status": "resumed", "manifest": str(manifest_path)}))
            return 0

    gamma_values = profile["gamma_values"]
    phase_payload = {
        "s4_formula_rows": s4_parameter_rows(gamma_values),
        "s4_finite_size_rows": s4_finite_size_scan(
            ("gamma_x_only", "anisotropic_velocity"),
            profile["s4_scan_gamma_values"],
            profile["s4_sizes"],
            profile["s4_m_offsets"],
        ),
        "s8_phase_rows": exact_model_phase_rows(gamma_values),
        "s9_phase_rows": exact_cylinder_phase_rows(gamma_values),
    }
    phase_path = output_root / "data" / "phase_diagrams.json"
    _atomic_json(phase_path, phase_payload)

    shifts = [complex(value[0], value[1]) for value in profile["skin_state_shifts"]]
    skin_arrays, skin_summary = skin_profile_arrays(
        square_size=int(profile["skin_square_size"]),
        disk_radius=int(profile["skin_disk_radius"]),
        shifts=shifts,
    )
    skin_path = output_root / "data" / "skin_profiles.npz"
    _atomic_npz(skin_path, skin_arrays)
    skin_summary_path = output_root / "data" / "skin_profiles_summary.json"
    _atomic_json(skin_summary_path, skin_summary)

    exact = config["exact_cylinder"]
    exact_arrays = exact_cylinder_spectrum_arrays(
        gamma=float(exact["gamma"]),
        m=float(exact["m"]),
        t=float(exact["t"]),
        length_y=int(profile["exact_cylinder_length_y"]),
        kx_points=int(profile["exact_cylinder_kx_points"]),
    )
    exact_path = output_root / "data" / "exact_cylinder_spectrum.npz"
    _atomic_npz(exact_path, exact_arrays)

    checks = {
        "status": "passed",
        "profile": arguments.profile,
        "paper_parameters_executed": arguments.profile == "paper",
        "source_pixels_used_as_numerical_input": False,
        "author_code_or_arrays_used": False,
        "targets": ["T007", "T008", "T009", "T010", "T011"],
        "skin_parameter_status": "reconstructed_missing_size_and_state_selection",
        "exact_similarity_transform_residual": similarity_transform_residual(6, 0.2),
        "s4_scan_rows": len(phase_payload["s4_finite_size_rows"]),
        "s8_open_boundary_is_gamma_independent": all(
            row["m"] == 2.0
            for row in phase_payload["s8_phase_rows"]
            if row["series"] == "open_boundary_non_bloch"
        ),
    }
    checks["status"] = "passed" if (
        checks["exact_similarity_transform_residual"] < 1e-12
        and checks["s8_open_boundary_is_gamma_independent"]
    ) else "failed"
    checks_path = output_root / "checks" / "science.json"
    _atomic_json(checks_path, checks)

    output_paths = [phase_path, skin_path, skin_summary_path, exact_path, checks_path]
    manifest = {
        "schema_version": 1,
        "profile": arguments.profile,
        "config_sha256": config_digest,
        "implementation_sha256": _sha256(ROOT / "src" / "supplemental_campaign.py"),
        "paper_parameters_executed": arguments.profile == "paper",
        "numerical_input_policy": {
            "paper_pixels": "forbidden",
            "digitized_curves": "forbidden",
            "author_code": "forbidden",
            "author_arrays": "forbidden",
        },
        "outputs": {
            str(path.relative_to(ROOT)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in output_paths
        },
    }
    _atomic_json(manifest_path, manifest)
    print(json.dumps({"status": checks["status"], "manifest": str(manifest_path)}, indent=2))
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
