#!/usr/bin/env python3
"""Generate all quantitative evidence for arXiv:cond-mat/0509490."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dziarmaga_ising.model import (  # noqa: E402
    asymptotic_defect_density,
    bdg_excitation_probability,
    dispersion,
    finite_chain_defect_density,
    ground_state_probability,
    landau_zener_probability,
    positive_momenta,
    reverse_bdg_excitation_probability,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _json_default(value: object) -> object:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()

    started = time.perf_counter()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    p = config["parameters"]
    a = config["acceptance"]
    output_root = Path(args.output_root)
    data_dir = output_root / "data"
    checks_dir = output_root / "checks"

    coupling_j = float(p["coupling_j"])
    hbar = float(p["hbar"])
    lattice_spacing = float(p["lattice_spacing"])

    dispersion_rows: list[dict[str, object]] = []
    dispersion_k = positive_momenta(int(p["dispersion_chain_length"]), lattice_spacing)
    for field in p["dispersion_fields"]:
        energies = dispersion(dispersion_k, float(field), coupling_j, lattice_spacing)
        for momentum, energy in zip(dispersion_k, energies, strict=True):
            dispersion_rows.append(
                {"field_g": field, "momentum_k": momentum, "energy": energy}
            )
    _write_csv(
        data_dir / "dispersion.csv",
        ["field_g", "momentum_k", "energy"],
        dispersion_rows,
    )

    bdg_rows: list[dict[str, object]] = []
    bdg_k = positive_momenta(int(p["bdg_chain_length"]), lattice_spacing)
    for tau in p["bdg_quench_times"]:
        for mode_index in p["bdg_mode_indices"]:
            momentum = float(bdg_k[int(mode_index)])
            probability, norm = bdg_excitation_probability(
                momentum,
                float(tau),
                field_initial=float(p["field_initial"]),
                coupling_j=coupling_j,
                hbar=hbar,
                lattice_spacing=lattice_spacing,
                rtol=float(p["solver_rtol"]),
                atol=float(p["solver_atol"]),
            )
            lz_full = float(
                landau_zener_probability(
                    momentum,
                    float(tau),
                    coupling_j,
                    hbar,
                    lattice_spacing,
                )
            )
            lz_gaussian = float(
                landau_zener_probability(
                    momentum,
                    float(tau),
                    coupling_j,
                    hbar,
                    lattice_spacing,
                    long_wavelength=True,
                )
            )
            bdg_rows.append(
                {
                    "quench_time": tau,
                    "mode_index": mode_index,
                    "momentum_k": momentum,
                    "p_bdg": probability,
                    "p_lz_sin2": lz_full,
                    "p_lz_gaussian": lz_gaussian,
                    "state_norm": norm,
                    "absolute_error_bdg_vs_lz": abs(probability - lz_full),
                }
            )
    _write_csv(
        data_dir / "excitation_probability.csv",
        [
            "quench_time",
            "mode_index",
            "momentum_k",
            "p_bdg",
            "p_lz_sin2",
            "p_lz_gaussian",
            "state_norm",
            "absolute_error_bdg_vs_lz",
        ],
        bdg_rows,
    )

    reverse_rows: list[dict[str, object]] = []
    reverse_chain_length = int(p["reverse_chain_length"])
    reverse_k = positive_momenta(reverse_chain_length, lattice_spacing)
    reverse_density_rows: list[dict[str, object]] = []
    for tau_value in p["reverse_quench_times"]:
        tau = float(tau_value)
        forward_probabilities: list[float] = []
        reverse_probabilities: list[float] = []
        for mode_index, momentum_value in enumerate(reverse_k):
            momentum = float(momentum_value)
            forward_probability, forward_norm = bdg_excitation_probability(
                momentum,
                tau,
                field_initial=float(p["field_initial"]),
                coupling_j=coupling_j,
                hbar=hbar,
                lattice_spacing=lattice_spacing,
                rtol=float(p["solver_rtol"]),
                atol=float(p["solver_atol"]),
            )
            reverse_probability, reverse_norm = reverse_bdg_excitation_probability(
                momentum,
                tau,
                field_final=float(p["field_initial"]),
                coupling_j=coupling_j,
                hbar=hbar,
                lattice_spacing=lattice_spacing,
                rtol=float(p["solver_rtol"]),
                atol=float(p["solver_atol"]),
            )
            forward_probabilities.append(forward_probability)
            reverse_probabilities.append(reverse_probability)
            reverse_rows.append(
                {
                    "quench_time": tau,
                    "mode_index": mode_index,
                    "momentum_k": momentum,
                    "forward_probability": forward_probability,
                    "reverse_probability": reverse_probability,
                    "absolute_probability_difference": abs(
                        forward_probability - reverse_probability
                    ),
                    "forward_state_norm": forward_norm,
                    "reverse_state_norm": reverse_norm,
                }
            )
        forward_density = 2.0 * sum(forward_probabilities) / reverse_chain_length
        reverse_density = 2.0 * sum(reverse_probabilities) / reverse_chain_length
        reverse_density_rows.append(
            {
                "quench_time": tau,
                "chain_length": reverse_chain_length,
                "forward_kink_density": forward_density,
                "reverse_flip_density": reverse_density,
                "absolute_density_difference": abs(forward_density - reverse_density),
                "finite_lz_density": finite_chain_defect_density(
                    reverse_chain_length,
                    tau,
                    coupling_j,
                    hbar,
                    lattice_spacing,
                ),
            }
        )
    _write_csv(
        data_dir / "reverse_quench_modes.csv",
        [
            "quench_time",
            "mode_index",
            "momentum_k",
            "forward_probability",
            "reverse_probability",
            "absolute_probability_difference",
            "forward_state_norm",
            "reverse_state_norm",
        ],
        reverse_rows,
    )
    _write_csv(
        data_dir / "reverse_quench_density.csv",
        [
            "quench_time",
            "chain_length",
            "forward_kink_density",
            "reverse_flip_density",
            "absolute_density_difference",
            "finite_lz_density",
        ],
        reverse_density_rows,
    )

    density_taus = np.geomspace(
        float(p["density_tau_min"]),
        float(p["density_tau_max"]),
        int(p["density_tau_points"]),
    )
    analytic_density = asymptotic_defect_density(density_taus, coupling_j, hbar)
    finite_density = np.array(
        [
            finite_chain_defect_density(
                int(p["density_chain_length"]),
                float(tau),
                coupling_j,
                hbar,
                lattice_spacing,
            )
            for tau in density_taus
        ]
    )
    density_rows = [
        {
            "quench_time": tau,
            "analytic_density": analytic,
            "finite_chain_density": finite,
            "relative_error": abs(finite - analytic) / analytic,
        }
        for tau, analytic, finite in zip(
            density_taus, analytic_density, finite_density, strict=True
        )
    ]
    _write_csv(
        data_dir / "defect_density.csv",
        [
            "quench_time",
            "analytic_density",
            "finite_chain_density",
            "relative_error",
        ],
        density_rows,
    )

    scaled_taus = np.geomspace(
        float(p["ground_state_scaled_tau_min"]),
        float(p["ground_state_scaled_tau_max"]),
        int(p["ground_state_scaled_tau_points"]),
    )
    ground_rows: list[dict[str, object]] = []
    collapse_values: dict[float, list[float]] = {float(x): [] for x in scaled_taus}
    for chain_length in p["ground_state_chain_lengths"]:
        n = int(chain_length)
        for scaled_tau in scaled_taus:
            tau = float(scaled_tau) * n**2
            probability = ground_state_probability(
                n, tau, coupling_j, hbar, lattice_spacing
            )
            one_mode = 1.0 - math.exp(
                -2.0 * math.pi**3 * coupling_j * tau / (hbar * n**2)
            )
            collapse_values[float(scaled_tau)].append(probability)
            ground_rows.append(
                {
                    "chain_length": n,
                    "scaled_quench_time_tau_over_n2": scaled_tau,
                    "quench_time": tau,
                    "ground_state_probability": probability,
                    "one_mode_approximation": one_mode,
                }
            )
    _write_csv(
        data_dir / "ground_state_probability.csv",
        [
            "chain_length",
            "scaled_quench_time_tau_over_n2",
            "quench_time",
            "ground_state_probability",
            "one_mode_approximation",
        ],
        ground_rows,
    )

    fit_mask = (density_taus >= float(p["density_fit_tau_min"])) & (
        density_taus <= float(p["density_fit_tau_max"])
    )
    slope, intercept = np.polyfit(
        np.log(density_taus[fit_mask]), np.log(finite_density[fit_mask]), 1
    )
    density_relative_error = float(
        np.max(np.abs(finite_density[fit_mask] - analytic_density[fit_mask]) / analytic_density[fit_mask])
    )
    max_bdg_norm_error = max(abs(float(row["state_norm"]) - 1.0) for row in bdg_rows)
    max_bdg_lz_error = max(float(row["absolute_error_bdg_vs_lz"]) for row in bdg_rows)
    collapse_spread = max(float(np.ptp(values)) for values in collapse_values.values())
    k_min = float(dispersion_k[0])
    critical_ratio = float(
        dispersion(k_min, 1.0, coupling_j, lattice_spacing)
        / (2.0 * coupling_j * k_min * lattice_spacing)
    )
    reverse_probability_error = max(
        float(row["absolute_probability_difference"]) for row in reverse_rows
    )
    reverse_density_error = max(
        float(row["absolute_density_difference"]) for row in reverse_density_rows
    )
    reverse_norm_error = max(
        max(
            abs(float(row["forward_state_norm"]) - 1.0),
            abs(float(row["reverse_state_norm"]) - 1.0),
        )
        for row in reverse_rows
    )

    checks = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "cond-mat-0509490",
        "target_results": {
            "T001": {
                "status": "passed",
                "critical_dispersion_ratio": critical_ratio,
                "critical_dispersion_ratio_error": abs(critical_ratio - 1.0),
            },
            "T002": {
                "status": "passed",
                "max_bdg_norm_error": max_bdg_norm_error,
                "max_bdg_lz_absolute_error": max_bdg_lz_error,
            },
            "T003": {
                "status": "passed",
                "fitted_density_exponent": slope,
                "density_exponent_error": abs(slope + 0.5),
                "max_density_relative_error": density_relative_error,
                "analytic_prefactor": 1.0 / (2.0 * math.pi * math.sqrt(2.0)),
            },
            "T004": {
                "status": "passed",
                "ground_state_collapse_spread": collapse_spread,
                "analytic_lz_coefficient": 2.0 * math.pi**3,
                "reported_reference_fit": 59.0,
                "relative_gap_to_reported_fit": abs(2.0 * math.pi**3 - 59.0) / (2.0 * math.pi**3),
            },
            "T005": {
                "status": "passed",
                "max_forward_reverse_probability_error": reverse_probability_error,
                "max_forward_reverse_density_error": reverse_density_error,
                "max_reverse_validation_norm_error": reverse_norm_error,
                "validation_chain_length": reverse_chain_length,
            },
        },
        "assertions": {
            "critical_dispersion_linear": abs(critical_ratio - 1.0)
            <= float(a["critical_dispersion_ratio_error_max"]),
            "bdg_norm_conserved": max_bdg_norm_error
            <= float(a["bdg_norm_error_max"]),
            "bdg_matches_lz": max_bdg_lz_error
            <= float(a["bdg_lz_absolute_error_max"]),
            "density_exponent_minus_half": abs(slope + 0.5)
            <= float(a["density_slope_error_max"]),
            "finite_density_matches_thermodynamic": density_relative_error
            <= float(a["density_relative_error_max"]),
            "ground_state_n2_collapse": collapse_spread
            <= float(a["ground_state_collapse_spread_max"]),
            "reverse_quench_same_mode_probabilities": reverse_probability_error
            <= float(a["reverse_quench_probability_error_max"]),
            "reverse_quench_same_density": reverse_density_error
            <= float(a["reverse_quench_density_error_max"]),
            "reverse_quench_norm_conserved": reverse_norm_error
            <= float(a["bdg_norm_error_max"]),
        },
    }
    if not all(checks["assertions"].values()):
        checks["status"] = "failed"
        for result in checks["target_results"].values():
            result["status"] = "failed"
    _write_json(checks_dir / "science_checks.json", checks)

    produced = sorted(
        [
            data_dir / "dispersion.csv",
            data_dir / "excitation_probability.csv",
            data_dir / "defect_density.csv",
            data_dir / "ground_state_probability.csv",
            data_dir / "reverse_quench_density.csv",
            data_dir / "reverse_quench_modes.csv",
            checks_dir / "science_checks.json",
        ],
        key=lambda item: item.as_posix(),
    )
    manifest = {
        "schema_version": 1,
        "paper_id": "cond-mat-0509490",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_used": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "files": [
            {
                "path": path.relative_to(output_root).as_posix(),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in produced
        ],
    }
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    summary = {
        "schema_version": 1,
        "paper_id": "cond-mat-0509490",
        "status": checks["status"],
        "runtime_seconds": time.perf_counter() - started,
        "targets": ["T001", "T002", "T003", "T004", "T005"],
        "paper_parameters_executed": True,
        "artifact_stage": "final_reproduction",
    }
    _write_json(checks_dir / "run_summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
