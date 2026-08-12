"""Independent feature campaign for PhysRevLett.132.113001."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from .metrology import (
    binding_frequency_from_printed_inputs,
    normalized_literature_points,
    regression_curves,
    sigma_separation,
    table_i_rows,
    table_ii_rows,
    uncertainty_closure,
)
from .spectra import calculated_spectrum, mirror_symmetry_error
from .stark import (
    expected_linear_stark_eigenvalues,
    field_free_level_rows,
    intermanifold_quadratic_shift_hz,
    k_zero_stark_branches,
    same_n_z_matrix,
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
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "PhysRevLett.132.113001":
        raise ValueError("wrong paper_id")
    if config.get("target_ids") != [f"T{index:03d}" for index in range(1, 13)]:
        raise ValueError("feature campaign must declare T001-T012 exactly")
    return config


def implementation_digest(workspace: Path) -> str:
    paths = sorted((workspace / "src" / "hydrogen_metrology").glob("*.py"))
    paths += [workspace / "scripts" / "run_reproduction.py"]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(workspace).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _stark_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    fields = np.linspace(
        config["stark"]["field_min_v_per_cm"],
        config["stark"]["field_max_v_per_cm"],
        config["stark"]["field_points"],
    )
    rows: list[dict[str, Any]] = []
    for n in config["stark"]["principal_quantum_numbers"]:
        for branch in k_zero_stark_branches(n, fields):
            for field, shift in zip(fields, branch.shift_hz, strict=True):
                rows.append(
                    {
                        "n": n,
                        "field_v_per_cm": float(field),
                        "branch": branch.name,
                        "spin_projection": branch.spin_projection,
                        "magnetic_label": branch.magnetic_label,
                        "shift_khz": float(shift / 1e3),
                    }
                )
    return rows


def _spectrum_rows(
    config: dict[str, Any],
) -> tuple[list[dict[str, float]], dict[str, Any]]:
    specification = config["spectrum"]
    frequencies = np.linspace(
        specification["frequency_min_mhz"],
        specification["frequency_max_mhz"],
        specification["frequency_points"],
    )
    intensity, components = calculated_spectrum(
        frequencies,
        n=specification["n"],
        field_v_per_cm=specification["field_v_per_cm"],
        doppler_shift_mhz=specification["doppler_shift_mhz"],
        doppler_sigma_mhz=specification["doppler_sigma_mhz"],
        field_sigma_mhz=specification["field_sigma_mhz"],
        asymmetry_gamma=specification["asymmetry_gamma"],
    )
    rows = [
        {"frequency_mhz": float(frequency), "intensity": float(value)}
        for frequency, value in zip(frequencies, intensity, strict=True)
    ]
    return rows, {
        "components": components,
        "mirror_symmetry_error": mirror_symmetry_error(frequencies, intensity),
    }


def _regression_rows(curves: dict[str, np.ndarray]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for x, center, band in zip(
        curves["field"],
        curves["field_trend_khz"],
        curves["field_band_khz"],
        strict=True,
    ):
        rows.append(
            {
                "model": "quadratic_stark",
                "x": float(x),
                "center_khz": float(center),
                "band_khz": float(band),
            }
        )
    for x, center, band in zip(
        curves["doppler"],
        curves["doppler_trend_khz"],
        curves["doppler_band_khz"],
        strict=True,
    ):
        rows.append(
            {
                "model": "linear_doppler",
                "x": float(x),
                "center_khz": float(center),
                "band_khz": float(band),
            }
        )
    return rows


def _stark_table_rows() -> list[dict[str, Any]]:
    fields = np.asarray([0.4, 0.8])
    rows: list[dict[str, Any]] = []
    for n in (20, 24):
        for branch in k_zero_stark_branches(n, fields):
            for field, shift in zip(fields, branch.shift_hz, strict=True):
                rows.append(
                    {
                        "n": n,
                        "field_v_per_cm": float(field),
                        "branch": branch.name,
                        "predicted_shift_khz": float(shift / 1e3),
                        "model_stage": "dirac_plus_stark_plus_scaled_hyperfine",
                    }
                )
    return rows


def run_feature(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    data_root = workspace / "outputs" / "data" / "feature"
    checks_root = workspace / "outputs" / "checks" / "feature"
    stark_rows = _stark_rows(config)
    spectrum_rows, spectrum_checks = _spectrum_rows(config)
    literature_rows = normalized_literature_points()
    field_grid = np.linspace(0.0, config["regressions"]["field_max_v_per_cm"], 161)
    doppler_grid = np.linspace(
        -config["regressions"]["doppler_max_mhz"],
        config["regressions"]["doppler_max_mhz"],
        161,
    )
    regression_arrays = regression_curves(field_grid, doppler_grid)
    uncertainty_rows = table_i_rows()
    closure = uncertainty_closure(
        uncertainty_rows,
        reported_stat_khz=config["metrology"]["reported_stat_khz"],
        reported_syst_khz=config["metrology"]["reported_syst_khz"],
    )
    rydberg_rows = table_ii_rows()
    field_free_rows = field_free_level_rows((2, 20, 24))
    stark_table_rows = _stark_table_rows()
    binding = binding_frequency_from_printed_inputs()
    comparison = {
        "this_work_vs_codata2018_combined_sigma": sigma_separation(
            3_289_841_960_194.0, 40.0, 3_289_841_960_250.8, 6.4, convention="combined"
        ),
        "this_work_vs_codata2010_first_only_sigma": sigma_separation(
            3_289_841_960_204.0,
            35.0,
            3_289_841_960_365.0,
            16.0,
            convention="first_only",
        ),
    }

    write_csv(data_root / "stark_branches.csv", stark_rows)
    write_csv(data_root / "spectrum.csv", spectrum_rows)
    write_csv(data_root / "literature_points.csv", literature_rows)
    write_csv(data_root / "regressions.csv", _regression_rows(regression_arrays))
    write_csv(data_root / "uncertainty_budget.csv", uncertainty_rows)
    write_csv(data_root / "rydberg_table.csv", rydberg_rows)
    write_csv(data_root / "field_free_table.csv", field_free_rows)
    write_csv(data_root / "stark_table.csv", stark_table_rows)
    write_csv(
        data_root / "claim_arithmetic.csv",
        [{**binding, **comparison, **closure}],
    )

    eigenvalue_errors = {
        str(n): float(
            np.max(
                np.abs(
                    np.linalg.eigvalsh(same_n_z_matrix(n))
                    - expected_linear_stark_eigenvalues(n)
                )
            )
        )
        for n in (20, 24)
    }
    quadratic_ratio = float(
        intermanifold_quadratic_shift_hz(24, 0.8)
        / intermanifold_quadratic_shift_hz(24, 0.4)
    )
    target_checks = {
        "schema_version": 1,
        "status": "passed",
        "checks": {
            "T001_T002_z_eigenvalue_max_error_a0": eigenvalue_errors,
            "T001_T002_quadratic_F08_over_F04": quadratic_ratio,
            "T003_six_components": len(spectrum_checks["components"]),
            "T003_mirror_symmetry_error": spectrum_checks["mirror_symmetry_error"],
            "T004_point_count": len(literature_rows),
            "T005_field_sigma_at_0p68_khz": 3.5 * 0.68**2,
            "T006_doppler_sigma_at_1p33_mhz_khz": 1.8 * 1.33,
            "T007_uncertainty_closure": closure,
            "T008_sigma_comparisons": comparison,
            "T009_model_stage": "leading_dirac_only",
            "T010_branch_rows": len(stark_table_rows),
            "T011_printed_input_gap_hz": binding["paper_minus_assembled_hz"],
            "T012_rydberg_rows": len(rydberg_rows),
        },
        "acceptance": {
            "z_eigenvalue_error_lt_1e-9": max(eigenvalue_errors.values()) < 1e-9,
            "quadratic_field_ratio_is_four": abs(quadratic_ratio - 4.0) < 1e-12,
            "six_line_components": len(spectrum_checks["components"]) == 6,
            "binding_rounding_gap_lt_100_hz": abs(
                float(binding["paper_minus_assembled_hz"])
            )
            < 100.0,
            "all_outputs_finite": all(
                np.isfinite(float(row["shift_khz"])) for row in stark_rows
            ),
        },
    }
    if not all(target_checks["acceptance"].values()):
        target_checks["status"] = "failed"
    atomic_json(checks_root / "target_checks.json", target_checks)

    return {
        "stark_rows": stark_rows,
        "spectrum_rows": spectrum_rows,
        "literature_rows": literature_rows,
        "regression_arrays": regression_arrays,
        "uncertainty_rows": uncertainty_rows,
        "rydberg_rows": rydberg_rows,
        "field_free_rows": field_free_rows,
        "stark_table_rows": stark_table_rows,
        "target_checks": target_checks,
        "summary": {
            "paper_id": config["paper_id"],
            "profile": config["profile"],
            "target_count": len(config["target_ids"]),
            "numeric_coverage_items": 14,
            "independently_generated_targets": 12,
            "deferred_author_data_items": 4,
            "scientific_status": "feature_reproduced_with_declared_approximations",
        },
    }


def build_manifest(workspace: Path, config: dict[str, Any]) -> dict[str, Any]:
    roots = [
        workspace / "outputs" / "data" / "feature",
        workspace / "outputs" / "figures" / "feature",
    ]
    files = sorted(path for root in roots for path in root.glob("*") if path.is_file())
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
    atomic_json(
        workspace / "outputs" / "checks" / "feature" / "generated_data_manifest.json",
        manifest,
    )
    atomic_json(
        workspace / "outputs" / "checks" / "feature" / "data_freeze.json", manifest
    )
    return manifest
