#!/usr/bin/env python3
"""Run the full non-diagonal spectral diffusion equation for Main Fig. 1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from xxz_diffusion import RootOfUnityXXZ  # noqa: E402
from xxz_diffusion.full_ghd import evolve_linearized_full_ghd  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _interpolate_profiles(
    source_x: np.ndarray, source_profiles: np.ndarray, target_x: np.ndarray
) -> np.ndarray:
    return np.stack(
        [np.interp(target_x, source_x, profile) for profile in source_profiles]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", default="final")
    parser.add_argument("--variant", action="append", dest="variants")
    parser.add_argument("--backend", choices=["numpy", "cupy"])
    args = parser.parse_args()

    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must be inside the case workspace")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paper = config["paper_parameters"]
    profile = config["profiles"][args.profile]
    variants = profile["variants"]
    if args.variants:
        selected = set(args.variants)
        variants = [row for row in variants if row.get("id") in selected]
        missing = sorted(selected - {str(row.get("id")) for row in variants})
        if missing:
            raise ValueError(f"unknown variants: {missing}")
    if not variants:
        raise ValueError("no variants selected")
    ell = int(paper["ell"])
    if abs(float(paper["delta"]) - float(np.cos(np.pi / ell))) > 1.0e-14:
        raise ValueError("paper delta must equal cos(pi/ell)")

    output_data = WORKSPACE / "outputs" / "data"
    output_checks = WORKSPACE / "outputs" / "checks"
    output_data.mkdir(parents=True, exist_ok=True)
    output_checks.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    results: dict[str, dict[str, Any]] = {}
    output_paths: list[Path] = []
    for variant in variants:
        variant_id = str(variant["id"])
        x_edges = np.linspace(
            float(variant["x_min"]),
            float(variant["x_max"]),
            int(variant["x_points"]),
            endpoint=False,
        )
        x = x_edges + 0.5 * (x_edges[1] - x_edges[0])
        state = RootOfUnityXXZ(
            ell=ell,
            rapidity_cutoff=float(variant["rapidity_cutoff"]),
            rapidity_points=int(variant["rapidity_points"]),
        ).solve_stationary_state()
        backend = args.backend or str(variant["backend"])
        result = evolve_linearized_full_ghd(
            state,
            x=x,
            times=[float(value) for value in paper["times"]],
            time_step=float(variant["time_step"]),
            backend=backend,
        )
        profiles = result["magnetization_over_mu"]
        data_path = output_data / f"T001_full_ghd_{args.profile}_{variant_id}.npz"
        np.savez_compressed(
            data_path,
            x=x,
            times=result["times"],
            magnetization_over_mu=profiles,
            susceptibility_plateau=np.asarray(result["susceptibility_plateau"]),
            diffusion_eigenvalue_real_min=np.asarray(
                result["diffusion_eigenvalue_real_min"]
            ),
            diffusion_eigenvalue_imag_max=np.asarray(
                result["diffusion_eigenvalue_imag_max"]
            ),
            maximum_profile_imaginary_residual=np.asarray(
                result["maximum_profile_imaginary_residual"]
            ),
            numerical_input_provenance=np.asarray(
                "paper_full_spectral_diffusion_operator_and_parameters_only"
            ),
        )
        output_paths.append(data_path)
        plateau = float(result["susceptibility_plateau"])
        period = float(variant["x_max"]) - float(variant["x_min"])
        plateau_half_width = period / 16.0
        left_plateau_mask = np.abs(x + period / 4.0) <= plateau_half_width
        right_plateau_mask = np.abs(x - period / 4.0) <= plateau_half_width
        plateau_error = max(
            float(np.max(np.abs(profiles[:, left_plateau_mask] - plateau))),
            float(np.max(np.abs(profiles[:, right_plateau_mask] + plateau))),
        )
        oddness = float(np.max(np.abs(profiles + profiles[:, ::-1])))
        results[variant_id] = {
            "variant": variant,
            "backend_used": backend,
            "x": x,
            "profiles": profiles,
            "data_path": str(data_path.relative_to(WORKSPACE)),
            "susceptibility_plateau": plateau,
            "plateau_error": plateau_error,
            "oddness_residual": oddness,
            "diffusion_eigenvalue_real_min": result["diffusion_eigenvalue_real_min"],
            "diffusion_eigenvalue_imag_max": result["diffusion_eigenvalue_imag_max"],
            "maximum_profile_imaginary_residual": result[
                "maximum_profile_imaginary_residual"
            ],
        }

    acceptance = config["acceptance"]
    checks: dict[str, dict[str, Any]] = {}
    for variant_id, result in results.items():
        metrics = {
            "oddness_residual": (
                result["oddness_residual"],
                float(acceptance["maximum_oddness_residual"]),
                "maximum",
            ),
            "plateau_error": (
                result["plateau_error"],
                float(acceptance["maximum_plateau_error"]),
                "maximum",
            ),
            "profile_imaginary_residual": (
                result["maximum_profile_imaginary_residual"],
                float(acceptance["maximum_profile_imaginary_residual"]),
                "maximum",
            ),
            "diffusion_eigenvalue_imag": (
                result["diffusion_eigenvalue_imag_max"],
                float(acceptance["maximum_diffusion_eigenvalue_imag"]),
                "maximum",
            ),
            "diffusion_eigenvalue_real_min": (
                result["diffusion_eigenvalue_real_min"],
                float(acceptance["minimum_diffusion_eigenvalue_real"]),
                "minimum",
            ),
        }
        for name, (value, threshold, direction) in metrics.items():
            checks[f"{variant_id}_{name}"] = {
                "value": value,
                "threshold": threshold,
                "direction": direction,
                "passed": value <= threshold if direction == "maximum" else value >= threshold,
            }

    comparisons: dict[str, dict[str, Any]] = {}
    for contract in profile.get("comparisons", []):
        left_id = str(contract["left"])
        right_id = str(contract["right"])
        if left_id not in results or right_id not in results:
            continue
        left = results[left_id]
        right = results[right_id]
        right_on_left = _interpolate_profiles(right["x"], right["profiles"], left["x"])
        residual = left["profiles"] - right_on_left
        rms = float(np.sqrt(np.mean(np.square(residual))))
        threshold = float(contract["threshold"])
        comparisons[str(contract["id"])] = {
            "left": left_id,
            "right": right_id,
            "rms": rms,
            "threshold": threshold,
            "passed": rms <= threshold,
        }

    all_passed = all(row["passed"] for row in checks.values()) and all(
        row["passed"] for row in comparisons.values()
    )
    full_profile_selected = len(results) == len(profile["variants"])
    comparisons_complete = len(comparisons) == len(profile.get("comparisons", []))
    status = (
        "passed_code_ready_validation"
        if all_passed and full_profile_selected and comparisons_complete
        else "passed_selected_variants"
        if all_passed
        else "failed"
    )
    check_path = output_checks / f"T001_full_ghd_{args.profile}_checks.json"
    serializable_results = {
        key: {name: value for name, value in row.items() if name not in {"x", "profiles"}}
        for key, row in results.items()
    }
    write_json(
        check_path,
        {
            "schema_version": 1,
            "status": status,
            "paper_id": config["paper_id"],
            "target_id": "T001_FULL_OPERATOR",
            "profile": args.profile,
            "paper_parameters": paper,
            "variant_results": serializable_results,
            "checks": checks,
            "comparisons": comparisons,
            "full_profile_selected": full_profile_selected,
            "comparisons_complete": comparisons_complete,
            "author_code_used": False,
            "author_numerical_arrays_used": False,
            "source_pixels_used_as_numerical_input": False,
            "runtime_seconds": time.perf_counter() - started,
        },
    )
    output_paths.append(check_path)
    manifest_path = output_checks / f"T001_full_ghd_{args.profile}_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "status": "passed" if status != "failed" else "failed",
            "config": str(config_path.relative_to(WORKSPACE)),
            "config_sha256": sha256(config_path),
            "outputs": [
                {
                    "path": str(path.relative_to(WORKSPACE)),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
                for path in output_paths
            ],
        },
    )
    print(json.dumps({"status": status, "checks": str(check_path)}, indent=2))
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
