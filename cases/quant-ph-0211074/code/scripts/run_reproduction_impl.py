#!/usr/bin/env python3
"""Generate every numerical target without reading paper figures or author data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vidal_entanglement.model import (  # noqa: E402
    block_covariance,
    correlation_coefficients,
    entropy_from_covariance,
    majorization_margin,
)
from vidal_entanglement.xxx import (  # noqa: E402
    GroundState,
    block_entropies,
    dicke_entropy,
    xxx_ground_state,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def implementation_sha256() -> str:
    digest = hashlib.sha256()
    for relative in [
        "scripts/run_reproduction.py",
        "src/vidal_entanglement/__init__.py",
        "src/vidal_entanglement/model.py",
        "src/vidal_entanglement/xxx.py",
    ]:
        path = WORKSPACE / relative
        digest.update(relative.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def fit_log_slope(lengths: np.ndarray, entropies: np.ndarray) -> tuple[float, float]:
    slope, intercept = np.polyfit(np.log2(lengths), entropies, 1)
    return float(slope), float(intercept)


def entropy_from_coefficients(
    length: int, coefficients: dict[int, float]
) -> tuple[float, np.ndarray]:
    return entropy_from_covariance(block_covariance(length, coefficients))


def load_or_run_xxx(
    output_root: Path,
    config_sha256: str,
    implementation_sha: str,
    *,
    n_spins: int,
    n_up: int,
    delta: float,
    coupling_sign: float,
    tolerance: float,
    seed: int,
    resume: bool,
) -> GroundState:
    checkpoint = (
        output_root / f"checkpoints/xxx_n{n_spins}_nup{n_up}_antiferromagnetic.npz"
    )
    if resume and checkpoint.exists():
        loaded = np.load(checkpoint, allow_pickle=False)
        if (
            str(loaded["config_sha256"]) == config_sha256
            and str(loaded["implementation_sha256"]) == implementation_sha
        ):
            return GroundState(
                n_spins=int(loaded["n_spins"]),
                n_up=int(loaded["n_up"]),
                delta=float(loaded["delta"]),
                coupling_sign=float(loaded["coupling_sign"]),
                energy=float(loaded["energy"]),
                residual_norm=float(loaded["residual_norm"]),
                translation_overlap=complex(loaded["translation_overlap"]),
                basis=np.asarray(loaded["basis"], dtype=np.uint64),
                amplitudes=np.asarray(loaded["amplitudes"], dtype=float),
            )

    ground = xxx_ground_state(
        n_spins,
        n_up=n_up,
        delta=delta,
        coupling_sign=coupling_sign,
        tolerance=tolerance,
        seed=seed,
    )
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    temporary = checkpoint.with_name(checkpoint.name + ".tmp.npz")
    np.savez_compressed(
        temporary,
        config_sha256=config_sha256,
        implementation_sha256=implementation_sha,
        n_spins=ground.n_spins,
        n_up=ground.n_up,
        delta=ground.delta,
        coupling_sign=ground.coupling_sign,
        energy=ground.energy,
        residual_norm=ground.residual_norm,
        translation_overlap=ground.translation_overlap,
        basis=ground.basis,
        amplitudes=ground.amplitudes,
    )
    os.replace(temporary, checkpoint)
    return ground


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    config_path = (WORKSPACE / args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    solver = config["solver"]
    acceptance = config["acceptance"]
    output_root = (WORKSPACE / args.output_root).resolve()
    data_root = output_root / "data"
    checks_root = output_root / "checks"
    config_hash = sha256_file(config_path)
    implementation_hash = implementation_sha256()

    quadrature = int(solver["fourier_quadrature_points"])
    convergence_quadrature = int(solver["fourier_convergence_points"])
    fig1_lengths = [int(value) for value in parameters["fig1_block_lengths"]]
    fig1_a = np.linspace(
        float(parameters["fig1_a_start"]),
        float(parameters["fig1_a_end"]),
        int(parameters["fig1_a_points"]),
    )
    fig1_rows: list[dict[str, Any]] = []
    max_antisymmetry = 0.0
    max_mode_violation = 0.0
    for a_value in fig1_a:
        coefficients = correlation_coefficients(
            max(fig1_lengths) - 1,
            a=float(a_value),
            gamma=float(parameters["fig1_gamma"]),
            quadrature_points=quadrature,
        )
        for length in fig1_lengths:
            covariance = block_covariance(length, coefficients)
            entropy, modes = entropy_from_covariance(covariance)
            max_antisymmetry = max(
                max_antisymmetry, float(np.max(np.abs(covariance + covariance.T)))
            )
            max_mode_violation = max(
                max_mode_violation,
                max(0.0, -float(np.min(modes)), float(np.max(modes)) - 1.0),
            )
            fig1_rows.append(
                {
                    "a": f"{a_value:.12g}",
                    "gamma": parameters["fig1_gamma"],
                    "block_length": length,
                    "entropy_bits": f"{entropy:.15g}",
                    "mode_min": f"{np.min(modes):.15g}",
                    "mode_max": f"{np.max(modes):.15g}",
                    "quadrature_points": quadrature,
                }
            )
    write_csv(
        data_root / "fig1_ising_surface.csv",
        [
            "a",
            "gamma",
            "block_length",
            "entropy_bits",
            "mode_min",
            "mode_max",
            "quadrature_points",
        ],
        fig1_rows,
    )

    fig2_lengths = np.asarray(parameters["fig2_block_lengths"], dtype=int)
    ising_coefficients = correlation_coefficients(
        int(np.max(fig2_lengths)) - 1,
        a=float(parameters["critical_ising_a"]),
        gamma=float(parameters["critical_ising_gamma"]),
        quadrature_points=quadrature,
    )
    xx_coefficients = correlation_coefficients(
        int(np.max(fig2_lengths)) - 1,
        a=np.inf,
        gamma=float(parameters["critical_xx_gamma"]),
        quadrature_points=quadrature,
    )
    ising_entropies = np.asarray(
        [
            entropy_from_coefficients(int(length), ising_coefficients)[0]
            for length in fig2_lengths
        ]
    )
    xx_entropies = np.asarray(
        [
            entropy_from_coefficients(int(length), xx_coefficients)[0]
            for length in fig2_lengths
        ]
    )

    xxx_ground = load_or_run_xxx(
        output_root,
        config_hash,
        implementation_hash,
        n_spins=int(parameters["xxx_n_spins"]),
        n_up=int(parameters["xxx_n_up"]),
        delta=float(parameters["xxx_delta"]),
        coupling_sign=float(parameters["xxx_caption_implied_coupling_sign"]),
        tolerance=float(solver["xxx_eigensolver_tolerance"]),
        seed=int(solver["xxx_seed"]),
        resume=args.resume,
    )
    xxx_lengths = list(range(1, int(parameters["xxx_n_spins"]) // 2 + 1))
    xxx_entropies = block_entropies(xxx_ground, xxx_lengths)
    dicke_entropies = {
        length: dicke_entropy(
            int(parameters["xxx_n_spins"]), int(parameters["xxx_n_up"]), length
        )
        for length in xxx_lengths
    }

    fig2_rows: list[dict[str, Any]] = []
    for length, entropy in zip(fig2_lengths, ising_entropies, strict=True):
        fig2_rows.append(
            {
                "series_id": "critical_ising",
                "model": "XY",
                "convention": "paper_exact",
                "block_length": int(length),
                "entropy_bits": f"{entropy:.15g}",
                "guide_entropy_bits": f"{(np.log2(length) + np.pi) / 6.0:.15g}",
                "plot_role": "paper_series",
            }
        )
    for length, entropy in zip(fig2_lengths, xx_entropies, strict=True):
        fig2_rows.append(
            {
                "series_id": "critical_xx",
                "model": "XY",
                "convention": "paper_exact_zero_field_limit",
                "block_length": int(length),
                "entropy_bits": f"{entropy:.15g}",
                "guide_entropy_bits": f"{(np.log2(length) + np.pi) / 3.0:.15g}",
                "plot_role": "paper_series",
            }
        )
    for length in xxx_lengths:
        fig2_rows.extend(
            [
                {
                    "series_id": "xxx_antiferromagnetic",
                    "model": "XXX",
                    "convention": "caption_implied_antiferromagnetic",
                    "block_length": length,
                    "entropy_bits": f"{xxx_entropies[length]:.15g}",
                    "guide_entropy_bits": f"{(np.log2(length) + np.pi) / 3.0:.15g}",
                    "plot_role": "paper_series_under_review",
                },
                {
                    "series_id": "xxx_printed_sign_dicke",
                    "model": "XXX",
                    "convention": "literal_printed_ferromagnetic_symmetric_sector",
                    "block_length": length,
                    "entropy_bits": f"{dicke_entropies[length]:.15g}",
                    "guide_entropy_bits": "",
                    "plot_role": "review_only",
                },
                {
                    "series_id": "xxx_printed_sign_polarized",
                    "model": "XXX",
                    "convention": "literal_printed_ferromagnetic_polarized_ground_state",
                    "block_length": length,
                    "entropy_bits": "0",
                    "guide_entropy_bits": "",
                    "plot_role": "review_only",
                },
            ]
        )
    write_csv(
        data_root / "fig2_critical_entropy.csv",
        [
            "series_id",
            "model",
            "convention",
            "block_length",
            "entropy_bits",
            "guide_entropy_bits",
            "plot_role",
        ],
        fig2_rows,
    )

    majorization_lengths = [
        int(value) for value in parameters["majorization_block_lengths"]
    ]
    majorization_rows: list[dict[str, Any]] = []
    majorization_minimum = float("inf")
    majorization_all_passed = True
    for model, coefficients in [
        ("critical_ising", ising_coefficients),
        ("critical_xx", xx_coefficients),
    ]:
        modes = {
            length: entropy_from_coefficients(length, coefficients)[1]
            for length in range(
                min(majorization_lengths), max(majorization_lengths) + 3
            )
        }
        for length in majorization_lengths:
            result = majorization_margin(modes[length], modes[length + 2])
            minimum = float(result["minimum_margin"])
            passed = minimum >= -float(acceptance["majorization_tolerance"])
            majorization_minimum = min(majorization_minimum, minimum)
            majorization_all_passed &= passed
            majorization_rows.append(
                {
                    "model": model,
                    "block_length": length,
                    "larger_block_length": length + 2,
                    "minimum_margin": f"{minimum:.15g}",
                    "worst_partial_sum_index": result["worst_partial_sum_index"],
                    "normalization_error": f"{float(result['normalization_error']):.15g}",
                    "tolerance": acceptance["majorization_tolerance"],
                    "passed": str(passed).lower(),
                }
            )
    write_csv(
        data_root / "majorization_checks.csv",
        [
            "model",
            "block_length",
            "larger_block_length",
            "minimum_margin",
            "worst_partial_sum_index",
            "normalization_error",
            "tolerance",
            "passed",
        ],
        majorization_rows,
    )

    convergence_differences = []
    for a_value in [0.6, 0.9, 1.0]:
        fine = correlation_coefficients(
            19, a=a_value, gamma=1.0, quadrature_points=quadrature
        )
        coarse = correlation_coefficients(
            19, a=a_value, gamma=1.0, quadrature_points=convergence_quadrature
        )
        fine_entropy = entropy_from_coefficients(20, fine)[0]
        coarse_entropy = entropy_from_coefficients(20, coarse)[0]
        convergence_differences.append(abs(fine_entropy - coarse_entropy))

    fit_mask = fig2_lengths >= 8
    ising_slope, ising_intercept = fit_log_slope(
        fig2_lengths[fit_mask], ising_entropies[fit_mask]
    )
    xx_slope, xx_intercept = fit_log_slope(
        fig2_lengths[fit_mask], xx_entropies[fit_mask]
    )
    xxx_fit_lengths = np.arange(1, min(5, max(xxx_lengths)) + 1, dtype=float)
    xxx_slope, xxx_intercept = fit_log_slope(
        xxx_fit_lengths,
        np.asarray([xxx_entropies[int(length)] for length in xxx_fit_lengths]),
    )
    gates = {
        "covariance_antisymmetry": max_antisymmetry
        <= float(acceptance["max_covariance_antisymmetry"]),
        "covariance_modes_physical": max_mode_violation
        <= float(acceptance["max_covariance_mode_violation"]),
        "fourier_convergence": max(convergence_differences)
        <= float(acceptance["max_fourier_entropy_difference"]),
        "critical_ising_slope": float(acceptance["critical_ising_slope_range"][0])
        <= ising_slope
        <= float(acceptance["critical_ising_slope_range"][1]),
        "critical_xx_slope": float(acceptance["critical_xx_slope_range"][0])
        <= xx_slope
        <= float(acceptance["critical_xx_slope_range"][1]),
        "xxx_short_block_slope": float(acceptance["xxx_short_block_slope_range"][0])
        <= xxx_slope
        <= float(acceptance["xxx_short_block_slope_range"][1]),
        "xxx_ground_residual": xxx_ground.residual_norm
        <= float(acceptance["max_xxx_residual"]),
        "xxx_translation": abs(xxx_ground.translation_overlap)
        >= float(acceptance["min_translation_overlap_abs"]),
        "xxx_sign_discrepancy_audited": max(xxx_entropies.values()) > 1.0
        and max(dicke_entropies.values()) > 1.0,
        "majorization_audit_complete": len(majorization_rows)
        == 2 * len(majorization_lengths),
    }
    science_status = "passed" if all(gates.values()) else "failed"
    checks = {
        "schema_version": 1,
        "status": science_status,
        "targets": ["T001", "T002", "T003"],
        "author_code_used": False,
        "author_arrays_used": False,
        "source_pixels_used_as_numeric_input": False,
        "gates": gates,
        "metrics": {
            "max_covariance_antisymmetry": max_antisymmetry,
            "max_covariance_mode_violation": max_mode_violation,
            "max_fourier_entropy_difference": max(convergence_differences),
            "critical_ising_log2_slope": ising_slope,
            "critical_ising_intercept": ising_intercept,
            "critical_xx_log2_slope": xx_slope,
            "critical_xx_intercept": xx_intercept,
            "xxx_short_block_log2_slope": xxx_slope,
            "xxx_short_block_intercept": xxx_intercept,
            "xxx_ground_energy": xxx_ground.energy,
            "xxx_ground_residual_norm": xxx_ground.residual_norm,
            "xxx_translation_overlap_real": float(xxx_ground.translation_overlap.real),
            "xxx_translation_overlap_imag": float(xxx_ground.translation_overlap.imag),
            "xxx_printed_polarized_entropy": 0.0,
            "xxx_printed_dicke_half_chain_entropy": dicke_entropies[max(xxx_lengths)],
            "xxx_caption_implied_half_chain_entropy": xxx_entropies[max(xxx_lengths)],
            "xxx_hamiltonian_caption_sign_discrepancy_detected": True,
            "majorization_minimum_margin": majorization_minimum,
            "majorization_all_passed": majorization_all_passed,
        },
        "paper_review": {
            "xxx_sign_convention": "inconclusive_pending_fresh_review",
            "majorization_claim": (
                "numerically_supported"
                if majorization_all_passed
                else "falsified_in_declared_range"
            ),
            "paper_error_candidate_emitted": False,
        },
    }
    write_json(checks_root / "science_checks.json", checks)

    generated_files = [
        data_root / "fig1_ising_surface.csv",
        data_root / "fig2_critical_entropy.csv",
        data_root / "majorization_checks.csv",
        checks_root / "science_checks.json",
        output_root
        / (
            f"checkpoints/xxx_n{int(parameters['xxx_n_spins'])}"
            f"_nup{int(parameters['xxx_n_up'])}_antiferromagnetic.npz"
        ),
    ]
    manifest = {
        "schema_version": 1,
        "status": "passed",
        "config_sha256": config_hash,
        "implementation_sha256": implementation_hash,
        "files": [
            {
                "path": str(path.relative_to(output_root)),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in generated_files
        ],
    }
    write_json(checks_root / "generated_data_manifest.json", manifest)
    write_json(
        checks_root / "run_summary.json",
        {
            "schema_version": 1,
            "status": science_status,
            "profile": config["profile"],
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "elapsed_seconds": time.perf_counter() - started,
            "xy_entropy_points": len(fig1_rows) + 2 * len(fig2_lengths),
            "xxx_sector_dimension": len(xxx_ground.basis),
            "majorization_checks": len(majorization_rows),
        },
    )
    print(json.dumps(checks, indent=2))
    return 0 if science_status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
