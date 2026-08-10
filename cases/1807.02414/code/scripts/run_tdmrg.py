#!/usr/bin/env python3
"""Run the independent paper-scale purification-TEBD campaign for T003."""

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

from xxz_diffusion.tdmrg import evolve_domain_wall  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _common_center(left: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    common = min(left.shape[-1], right.shape[-1])
    left_start = (left.shape[-1] - common) // 2
    right_start = (right.shape[-1] - common) // 2
    return (
        left[..., left_start : left_start + common],
        right[..., right_start : right_start + common],
    )


def _comparison_metrics(left: np.ndarray, right: np.ndarray, mu: float) -> dict[str, float]:
    left_common, right_common = _common_center(left, right)
    residual = (left_common - right_common) / float(mu)
    return {
        "normalized_rms": float(np.sqrt(np.mean(np.square(residual)))),
        "normalized_max_abs": float(np.max(np.abs(residual))),
    }


def _validate_variant(variant: dict[str, Any]) -> None:
    required = {
        "id",
        "chain_length",
        "max_bond",
        "time_step",
        "relative_cutoff",
        "backend",
    }
    missing = sorted(required - set(variant))
    if missing:
        raise ValueError(f"variant is missing required fields: {missing}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", default="final")
    parser.add_argument("--variant", action="append", dest="variants")
    parser.add_argument("--backend", choices=["numpy", "cupy"])
    parser.add_argument("--resume", action="store_true")
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
        variants = [variant for variant in variants if variant.get("id") in selected]
        missing = sorted(selected - {str(variant.get("id")) for variant in variants})
        if missing:
            raise ValueError(f"unknown variants for profile {args.profile!r}: {missing}")
    if not variants:
        raise ValueError("the selected profile has no variants")

    delta = float(paper["delta"])
    expected_delta = float(np.cos(np.pi / int(paper["ell"])))
    if abs(delta - expected_delta) > 1.0e-14:
        raise ValueError("paper delta must equal cos(pi/ell)")
    mu = float(paper["domain_wall_mu"])
    times = [float(value) for value in paper["times"]]
    output_data = WORKSPACE / "outputs" / "data"
    output_checks = WORKSPACE / "outputs" / "checks"
    checkpoint_root = WORKSPACE / "outputs" / "checkpoints" / "T003_tdmrg"
    output_data.mkdir(parents=True, exist_ok=True)
    output_checks.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    results: dict[str, dict[str, Any]] = {}
    output_files: list[Path] = []
    for variant in variants:
        _validate_variant(variant)
        variant_id = str(variant["id"])
        backend = args.backend or str(variant["backend"])
        checkpoint_path = checkpoint_root / args.profile / f"{variant_id}.npz"
        result = evolve_domain_wall(
            chain_length=int(variant["chain_length"]),
            delta=delta,
            mu=mu,
            time_step=float(variant["time_step"]),
            times=times,
            max_bond=int(variant["max_bond"]),
            relative_cutoff=float(variant["relative_cutoff"]),
            backend=backend,
            checkpoint_path=checkpoint_path,
            checkpoint_every_steps=int(variant.get("checkpoint_every_steps", 0)),
            resume=args.resume,
            checkpoint_metadata={
                "paper_id": config["paper_id"],
                "target_id": "T003",
                "profile": args.profile,
                "variant": variant_id,
                "config_sha256": sha256(config_path),
            },
        )
        chain_length = int(variant["chain_length"])
        positions = np.arange(chain_length, dtype=float) - 0.5 * (chain_length - 1)
        data_path = output_data / f"T003_tdmrg_{args.profile}_{variant_id}.npz"
        np.savez_compressed(
            data_path,
            x=positions,
            times=result["times"],
            magnetization=result["magnetization"],
            magnetization_over_mu=result["magnetization"] / mu,
            norms=result["norms"],
            delta=np.asarray(delta),
            mu=np.asarray(mu),
            chain_length=np.asarray(chain_length),
            time_step=np.asarray(float(variant["time_step"])),
            max_bond=np.asarray(int(variant["max_bond"])),
            relative_cutoff=np.asarray(float(variant["relative_cutoff"])),
            numerical_input_provenance=np.asarray(
                "paper_hamiltonian_and_product_density_matrix_only"
            ),
        )
        output_files.extend([data_path, checkpoint_path])
        initial_plateau = 0.5 * np.tanh(0.5 * mu)
        edge_sites = int(config["acceptance"]["edge_sites"])
        magnetization = result["magnetization"]
        left_boundary_error = float(
            np.max(np.abs(magnetization[:, :edge_sites] - initial_plateau))
        )
        right_boundary_error = float(
            np.max(np.abs(magnetization[:, -edge_sites:] + initial_plateau))
        )
        diagnostics = dict(result["diagnostics"])
        results[variant_id] = {
            "variant": variant,
            "backend_used": backend,
            "data_path": str(data_path.relative_to(WORKSPACE)),
            "checkpoint_path": str(checkpoint_path.relative_to(WORKSPACE)),
            "magnetization": magnetization,
            "norm_drift": float(np.max(np.abs(result["norms"] - 1.0))),
            "boundary_plateau_error": max(left_boundary_error, right_boundary_error),
            "diagnostics": diagnostics,
        }

    acceptance = config["acceptance"]
    checks: dict[str, dict[str, Any]] = {}
    for variant_id, result in results.items():
        checks[f"{variant_id}_norm"] = {
            "value": result["norm_drift"],
            "threshold": float(acceptance["maximum_norm_drift"]),
            "passed": result["norm_drift"] <= float(acceptance["maximum_norm_drift"]),
        }
        checks[f"{variant_id}_boundary"] = {
            "value": result["boundary_plateau_error"],
            "threshold": float(acceptance["maximum_boundary_plateau_error"]),
            "passed": result["boundary_plateau_error"]
            <= float(acceptance["maximum_boundary_plateau_error"]),
        }
        maximum_discarded = float(result["diagnostics"]["maximum_discarded_weight"])
        checks[f"{variant_id}_truncation"] = {
            "value": maximum_discarded,
            "threshold": float(acceptance["maximum_single_update_discarded_weight"]),
            "passed": maximum_discarded
            <= float(acceptance["maximum_single_update_discarded_weight"]),
        }

    comparison_results: dict[str, dict[str, Any]] = {}
    selected_ids = set(results)
    for comparison in profile.get("comparisons", []):
        left_id = str(comparison["left"])
        right_id = str(comparison["right"])
        if left_id not in selected_ids or right_id not in selected_ids:
            continue
        metrics = _comparison_metrics(
            results[left_id]["magnetization"],
            results[right_id]["magnetization"],
            mu,
        )
        metric = str(comparison["metric"])
        threshold = float(comparison["threshold"])
        comparison_results[str(comparison["id"])] = {
            **metrics,
            "metric": metric,
            "threshold": threshold,
            "passed": metrics[metric] <= threshold,
            "left": left_id,
            "right": right_id,
        }

    all_passed = all(check["passed"] for check in checks.values()) and all(
        check["passed"] for check in comparison_results.values()
    )
    full_profile_selected = len(results) == len(profile["variants"])
    required_comparisons = len(profile.get("comparisons", []))
    comparisons_complete = len(comparison_results) == required_comparisons
    status = (
        "passed_code_ready_validation"
        if all_passed and full_profile_selected and comparisons_complete
        else "passed_selected_variants"
        if all_passed
        else "failed"
    )
    checks_path = output_checks / f"T003_tdmrg_{args.profile}_checks.json"
    serializable_results = {
        variant_id: {key: value for key, value in result.items() if key != "magnetization"}
        for variant_id, result in results.items()
    }
    write_json(
        checks_path,
        {
            "schema_version": 1,
            "status": status,
            "paper_id": config["paper_id"],
            "target_id": "T003",
            "profile": args.profile,
            "formula": "purification TEBD of the printed XXZ Hamiltonian and rho_0",
            "paper_parameters": paper,
            "variant_results": serializable_results,
            "checks": checks,
            "comparisons": comparison_results,
            "full_profile_selected": full_profile_selected,
            "comparisons_complete": comparisons_complete,
            "author_code_used": False,
            "author_numerical_arrays_used": False,
            "source_pixels_used_as_numerical_input": False,
            "runtime_seconds": time.perf_counter() - started,
        },
    )
    output_files.append(checks_path)
    manifest_path = output_checks / f"T003_tdmrg_{args.profile}_manifest.json"
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
                for path in output_files
            ],
        },
    )
    print(json.dumps({"status": status, "checks": str(checks_path)}, indent=2))
    return 0 if status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
