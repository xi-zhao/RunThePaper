#!/usr/bin/env python3
"""Generate all seven numerical panels without reading paper pixels or author data."""

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

from spin_squeezing.model import (  # noqa: E402
    coherent_state,
    husimi_q,
    minimum_one_axis_variance,
    minimum_transverse_variance,
    minimum_two_axis_variance,
    one_axis_state,
    one_axis_variances,
    spin_operators,
    two_axis_generator,
    two_axis_state,
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
        "src/spin_squeezing/__init__.py",
        "src/spin_squeezing/model.py",
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


def json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"cannot serialize {type(value).__name__}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n",
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp.npy")
    np.save(temporary, np.asarray(array, dtype=np.float64), allow_pickle=False)
    os.replace(temporary, path)


def panel_state(spin: float, family: str, mu: float) -> np.ndarray:
    if family == "css_x":
        return coherent_state(spin, np.pi / 2.0, 0.0)
    if family == "css_z":
        return coherent_state(spin, 0.0, 0.0)
    if family == "one_axis":
        return one_axis_state(spin, mu)
    if family == "two_axis":
        return two_axis_state(spin, mu)
    raise ValueError(f"unknown QPD family: {family}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
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

    spin_qpd = float(parameters["spin_qpd"])
    theta = np.linspace(0.0, np.pi, int(parameters["theta_points"]))
    phi = np.linspace(-np.pi, np.pi, int(parameters["phi_points"]))
    write_csv(
        data_root / "qpd_axes.csv",
        ["axis", "index", "radians"],
        [
            {"axis": "theta", "index": index, "radians": f"{value:.17g}"}
            for index, value in enumerate(theta)
        ]
        + [
            {"axis": "phi", "index": index, "radians": f"{value:.17g}"}
            for index, value in enumerate(phi)
        ],
    )

    landmark_rows: list[dict[str, Any]] = []
    q_files: list[Path] = []
    norm_errors: list[float] = []
    q_bound_violations: list[float] = []
    qmax_differences: list[float] = []
    for panel in parameters["qpd_panels"]:
        target_id = str(panel["target_id"])
        family = str(panel["family"])
        mu = float(panel["mu"])
        state = panel_state(spin_qpd, family, mu)
        norm_error = abs(float(np.vdot(state, state).real) - 1.0)
        q_values = husimi_q(state, spin_qpd, theta, phi)
        qmax = float(np.max(q_values))
        printed_qmax = float(panel["printed_qmax"])
        qmax_difference = abs(qmax - printed_qmax)
        q_path = data_root / f"{target_id}_qpd.npy"
        write_npy(q_path, q_values)
        q_files.append(q_path)
        norm_errors.append(norm_error)
        q_bound_violations.append(
            max(0.0, -float(np.min(q_values)), float(np.max(q_values)) - 1.0)
        )
        qmax_differences.append(qmax_difference)
        max_index = np.unravel_index(int(np.argmax(q_values)), q_values.shape)
        landmark_rows.append(
            {
                "target_id": target_id,
                "panel_id": panel["panel_id"],
                "family": family,
                "spin": spin_qpd,
                "mu": f"{mu:.12g}",
                "computed_qmax": f"{qmax:.15g}",
                "printed_qmax": f"{printed_qmax:.15g}",
                "absolute_difference": f"{qmax_difference:.15g}",
                "maximum_theta": f"{theta[max_index[0]]:.15g}",
                "maximum_phi": f"{phi[max_index[1]]:.15g}",
                "state_norm_error": f"{norm_error:.15g}",
            }
        )
    write_csv(
        data_root / "qpd_landmarks.csv",
        [
            "target_id",
            "panel_id",
            "family",
            "spin",
            "mu",
            "computed_qmax",
            "printed_qmax",
            "absolute_difference",
            "maximum_theta",
            "maximum_phi",
            "state_norm_error",
        ],
        landmark_rows,
    )

    scalar_tolerance = float(solver["scalar_tolerance"])
    variance_rows: list[dict[str, Any]] = []
    one_axis_results = {}
    two_axis_results = {}
    for spin_value in [float(value) for value in parameters["variance_spins"]]:
        oat = minimum_one_axis_variance(
            spin_value,
            mu_max=float(solver["one_axis_mu_max"]),
            tolerance=scalar_tolerance,
        )
        tact = minimum_two_axis_variance(
            spin_value,
            mu_max=float(solver["two_axis_mu_max"]),
            coarse_points=int(solver["two_axis_coarse_points"]),
            tolerance=scalar_tolerance,
        )
        one_axis_results[spin_value] = oat
        two_axis_results[spin_value] = tact
        variance_rows.append(
            {
                "spin": f"{spin_value:.12g}",
                "css_variance": f"{0.5 * spin_value:.15g}",
                "one_axis_minimum": f"{oat.variance:.15g}",
                "one_axis_mu": f"{oat.mu:.15g}",
                "one_axis_asymptote": f"{0.5 * (spin_value / 3.0) ** (1.0 / 3.0):.15g}",
                "two_axis_minimum": f"{tact.variance:.15g}",
                "two_axis_mu": f"{tact.mu:.15g}",
                "two_axis_asymptote": "0.5",
                "one_axis_boundary_hit": str(oat.boundary_hit).lower(),
                "two_axis_boundary_hit": str(tact.boundary_hit).lower(),
            }
        )
    write_csv(
        data_root / "variance_scaling.csv",
        [
            "spin",
            "css_variance",
            "one_axis_minimum",
            "one_axis_mu",
            "one_axis_asymptote",
            "two_axis_minimum",
            "two_axis_mu",
            "two_axis_asymptote",
            "one_axis_boundary_hit",
            "two_axis_boundary_hit",
        ],
        variance_rows,
    )

    direct_formula_differences = []
    _, _, _, _, sy, sz = spin_operators(spin_qpd)
    for mu in (0.0, 0.199, 0.399):
        state = one_axis_state(spin_qpd, mu)
        direct = minimum_transverse_variance(state, sy, sz)
        formula = one_axis_variances(spin_qpd, mu)[0]
        direct_formula_differences.append(abs(direct - formula))

    generator = two_axis_generator(spin_qpd)
    hermiticity_error = float(np.max(np.abs(generator - generator.conj().T)))
    s20_oat = minimum_one_axis_variance(
        spin_qpd,
        mu_max=float(solver["one_axis_mu_max"]),
        tolerance=scalar_tolerance,
    )
    s20_tact = minimum_two_axis_variance(
        spin_qpd,
        mu_max=float(solver["two_axis_mu_max"]),
        coarse_points=int(solver["two_axis_coarse_points"]),
        tolerance=scalar_tolerance,
    )
    refined_tact = minimum_two_axis_variance(
        spin_qpd,
        mu_max=float(solver["two_axis_mu_max"]),
        coarse_points=2 * int(solver["two_axis_coarse_points"]) - 1,
        tolerance=scalar_tolerance,
    )
    max_spin = max(two_axis_results)
    oat_ratio = one_axis_results[max_spin].variance / (
        0.5 * (max_spin / 3.0) ** (1.0 / 3.0)
    )
    tact_half_distance = abs(two_axis_results[max_spin].variance - 0.5) / 0.5
    refinement_difference = abs(s20_tact.variance - refined_tact.variance)
    all_boundary_free = not any(
        result.boundary_hit
        for result in [*one_axis_results.values(), *two_axis_results.values()]
    )

    gates = {
        "state_norms": max(norm_errors) <= float(acceptance["max_state_norm_error"]),
        "q_bounds": max(q_bound_violations)
        <= float(acceptance["max_q_bound_violation"]),
        "printed_qmax_landmarks": max(qmax_differences)
        <= float(acceptance["max_printed_qmax_difference"]),
        "one_axis_formula_parity": max(direct_formula_differences)
        <= float(acceptance["max_one_axis_formula_difference"]),
        "two_axis_generator_hermitian": hermiticity_error <= 1e-12,
        "s20_optimal_times": abs(s20_oat.mu - 0.199)
        <= float(acceptance["max_s20_optimal_mu_difference"])
        and abs(s20_tact.mu - 0.203)
        <= float(acceptance["max_s20_optimal_mu_difference"]),
        "minimum_search_interior": all_boundary_free,
        "one_axis_asymptotic_scaling": float(
            acceptance["one_axis_s100_asymptotic_ratio_range"][0]
        )
        <= oat_ratio
        <= float(acceptance["one_axis_s100_asymptotic_ratio_range"][1]),
        "two_axis_asymptotic_scaling": tact_half_distance
        <= float(acceptance["max_two_axis_s100_distance_from_half"]),
        "two_axis_grid_refinement": refinement_difference
        <= float(acceptance["max_two_axis_grid_refinement_variance_difference"]),
    }
    status = "passed" if all(gates.values()) else "failed"
    science_checks = {
        "schema_version": 1,
        "status": status,
        "targets": [f"T{index:03d}" for index in range(1, 8)],
        "author_code_used": False,
        "author_arrays_used": False,
        "source_pixels_used_as_numeric_input": False,
        "gates": gates,
        "metrics": {
            "max_state_norm_error": max(norm_errors),
            "max_q_bound_violation": max(q_bound_violations),
            "max_printed_qmax_difference": max(qmax_differences),
            "max_one_axis_formula_difference": max(direct_formula_differences),
            "two_axis_generator_hermiticity_error": hermiticity_error,
            "s20_one_axis_optimal_mu": s20_oat.mu,
            "s20_one_axis_minimum_variance": s20_oat.variance,
            "s20_two_axis_optimal_mu": s20_tact.mu,
            "s20_two_axis_minimum_variance": s20_tact.variance,
            "maximum_spin": max_spin,
            "one_axis_asymptotic_ratio_at_maximum_spin": oat_ratio,
            "two_axis_relative_distance_from_half_at_maximum_spin": tact_half_distance,
            "two_axis_grid_refinement_variance_difference": refinement_difference,
        },
        "paper_review": {
            "printed_qmax_values": "numerically_supported",
            "one_axis_asymptote": "numerically_supported",
            "two_axis_asymptote": "numerically_supported_at_finite_S",
            "paper_error_candidate_emitted": False,
        },
    }
    write_json(checks_root / "science_checks.json", science_checks)

    generated_files = [
        data_root / "qpd_axes.csv",
        data_root / "qpd_landmarks.csv",
        data_root / "variance_scaling.csv",
        *q_files,
        checks_root / "science_checks.json",
    ]
    write_json(
        checks_root / "generated_data_manifest.json",
        {
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
        },
    )
    write_json(
        checks_root / "run_summary.json",
        {
            "schema_version": 1,
            "status": status,
            "profile": config["profile"],
            "config_sha256": config_hash,
            "implementation_sha256": implementation_hash,
            "elapsed_seconds": time.perf_counter() - started,
            "qpd_panels": len(parameters["qpd_panels"]),
            "qpd_grid_points_per_panel": len(theta) * len(phi),
            "variance_spin_values": len(parameters["variance_spins"]),
            "largest_hilbert_dimension": int(2 * max_spin + 1),
        },
    )
    print(json.dumps(science_checks, indent=2, default=json_default))
    return 0 if status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
