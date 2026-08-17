#!/usr/bin/env python3
"""Generate and scientifically validate every numerical target."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from open_xxz.liouvillian import solve_dense_ness  # noqa: E402
from open_xxz.transfer import (  # noqa: E402
    connected_correlation,
    correlation_asymptote,
    easy_axis_decay_fit,
    easy_plane_current_limit,
    isotropic_current_asymptote,
    isotropic_profile_asymptote,
    spin_current,
    spin_profile,
    transfer_operators,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def assertion(
    check_id: str,
    target_ids: list[str],
    value: float,
    threshold: float,
    comparator: str,
    description: str,
) -> dict[str, object]:
    if comparator == "max":
        passed = value <= threshold
    elif comparator == "min":
        passed = value >= threshold
    else:
        raise ValueError(f"unknown comparator {comparator}")
    return {
        "check_id": check_id,
        "target_ids": target_ids,
        "description": description,
        "value": float(value),
        "threshold": float(threshold),
        "comparator": comparator,
        "passed": bool(passed),
    }


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    config_path = Path(args.config).resolve()
    output_root = Path(args.output_root).resolve()
    config = json.loads(config_path.read_text())
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    data_root = output_root / "data"
    checks_root = output_root / "checks"
    data_root.mkdir(parents=True, exist_ok=True)
    checks_root.mkdir(parents=True, exist_ok=True)

    profile_size = int(parameters["profile_size"])
    anisotropies = [float(value) for value in parameters["anisotropies"]]
    couplings = [float(value) for value in parameters["couplings"]]
    current_sizes = np.arange(
        int(parameters["current_size_min"]),
        int(parameters["current_size_max"]) + 1,
        dtype=int,
    )

    profile_rows: list[dict[str, object]] = []
    profiles: dict[tuple[float, float], np.ndarray] = {}
    for delta in anisotropies:
        for epsilon in couplings:
            values = spin_profile(delta, epsilon, profile_size)
            profiles[(delta, epsilon)] = values
            for site, magnetization in enumerate(values, start=1):
                profile_rows.append(
                    {
                        "target_id": "T001",
                        "series_id": f"delta_{delta:g}_epsilon_{epsilon:g}",
                        "series_kind": "finite_transfer",
                        "n": profile_size,
                        "site": site,
                        "x": (site - 1) / (profile_size - 1),
                        "delta": delta,
                        "epsilon": epsilon,
                        "magnetization": float(magnetization),
                        "generated_data_provenance": "independent_numerics",
                    }
                )
    isotropic_profile = isotropic_profile_asymptote(profile_size)
    for site, magnetization in enumerate(isotropic_profile, start=1):
        profile_rows.append(
            {
                "target_id": "T001",
                "series_id": "delta_1_asymptotic_cosine",
                "series_kind": "printed_analytic_asymptote",
                "n": profile_size,
                "site": site,
                "x": (site - 1) / (profile_size - 1),
                "delta": 1.0,
                "epsilon": "",
                "magnetization": float(magnetization),
                "generated_data_provenance": "independent_numerics",
            }
        )

    currents: dict[tuple[float, float], np.ndarray] = {}
    current_rows: list[dict[str, object]] = []
    for delta in anisotropies:
        for epsilon in couplings:
            values = np.array(
                [spin_current(delta, epsilon, int(size)) for size in current_sizes],
                dtype=np.float64,
            )
            currents[(delta, epsilon)] = values
            for size, current in zip(current_sizes, values, strict=True):
                current_rows.append(
                    {
                        "target_id": "T002",
                        "series_id": f"delta_{delta:g}_epsilon_{epsilon:g}",
                        "series_kind": "finite_transfer",
                        "n": int(size),
                        "delta": delta,
                        "epsilon": epsilon,
                        "current": float(current),
                        "generated_data_provenance": "independent_numerics",
                    }
                )
    for epsilon in couplings:
        asymptotic = isotropic_current_asymptote(epsilon, current_sizes)
        for size, current in zip(current_sizes, asymptotic, strict=True):
            current_rows.append(
                {
                    "target_id": "T002",
                    "series_id": f"delta_1_epsilon_{epsilon:g}_asymptotic_n_minus_2",
                    "series_kind": "printed_analytic_asymptote",
                    "n": int(size),
                    "delta": 1.0,
                    "epsilon": epsilon,
                    "current": float(current),
                    "generated_data_provenance": "independent_numerics",
                }
            )

    correlation_rows: list[dict[str, object]] = []
    correlation_relative_errors: list[float] = []
    for size in parameters["correlation_sizes"]:
        size = int(size)
        for nominal_x, nominal_y in parameters["correlation_points"]:
            site_j = round(float(nominal_x) * (size - 1)) + 1
            site_k = round(float(nominal_y) * (size - 1)) + 1
            x = (site_j - 1) / (size - 1)
            y = (site_k - 1) / (size - 1)
            finite = connected_correlation(1.0, 1.0, size, site_j, site_k)
            asymptotic = correlation_asymptote(x, y, size)
            relative_error = abs(finite / asymptotic - 1.0)
            if size == max(parameters["correlation_sizes"]):
                correlation_relative_errors.append(float(relative_error))
            correlation_rows.append(
                {
                    "target_id": "T005",
                    "n": size,
                    "site_j": site_j,
                    "site_k": site_k,
                    "x": x,
                    "y": y,
                    "finite_connected_correlation": finite,
                    "analytic_asymptote": asymptotic,
                    "relative_error": relative_error,
                    "generated_data_provenance": "independent_numerics",
                }
            )

    dense_results = []
    dense_magnetization_errors = []
    dense_current_errors = []
    dense_current_spreads = []
    dense_residuals = []
    for size in parameters["dense_crosscheck_sizes"]:
        for delta in parameters["dense_crosscheck_anisotropies"]:
            for epsilon in parameters["dense_crosscheck_couplings"]:
                dense = solve_dense_ness(float(delta), float(epsilon), int(size))
                transfer_profile = spin_profile(float(delta), float(epsilon), int(size))
                transfer_current = spin_current(float(delta), float(epsilon), int(size))
                magnetization_error = float(
                    np.max(np.abs(dense.magnetization - transfer_profile))
                )
                current_error = float(
                    np.max(np.abs(dense.bond_currents - transfer_current))
                )
                current_spread = float(np.ptp(dense.bond_currents))
                dense_magnetization_errors.append(magnetization_error)
                dense_current_errors.append(current_error)
                dense_current_spreads.append(current_spread)
                dense_residuals.append(dense.residual_norm)
                dense_results.append(
                    {
                        "n": int(size),
                        "delta": float(delta),
                        "epsilon": float(epsilon),
                        "magnetization_max_abs_error": magnetization_error,
                        "current_max_abs_error": current_error,
                        "bond_current_spread": current_spread,
                        "liouvillian_residual_norm": dense.residual_norm,
                        "trace_error": dense.trace_error,
                        "hermiticity_error": dense.hermiticity_error,
                    }
                )

    easy_axis_slopes = {}
    fit_mask = (current_sizes >= int(parameters["easy_axis_fit_min"])) & (
        current_sizes <= int(parameters["easy_axis_fit_max"])
    )
    for epsilon in couplings:
        fit = easy_axis_decay_fit(
            current_sizes[fit_mask], currents[(1.5, epsilon)][fit_mask]
        )
        easy_axis_slopes[str(epsilon)] = fit

    isotropic_fit_mask = current_sizes >= 70
    isotropic_slope = float(
        np.polyfit(
            np.log(current_sizes[isotropic_fit_mask]),
            np.log(currents[(1.0, 1.0)][isotropic_fit_mask]),
            1,
        )[0]
    )
    isotropic_coefficient_ratio = float(
        currents[(1.0, 1.0)][-1]
        / isotropic_current_asymptote(1.0, int(current_sizes[-1]))
    )

    thermo_grid = np.linspace(
        float(parameters["thermodynamic_grid_min"]),
        float(parameters["thermodynamic_grid_max"]),
        int(parameters["thermodynamic_grid_points"]),
    )
    thermo_current = np.asarray(easy_plane_current_limit(thermo_grid))
    maximum_index = int(np.argmax(thermo_current))
    easy_plane_summary = {
        "maximum_epsilon": float(thermo_grid[maximum_index]),
        "maximum_current": float(thermo_current[maximum_index]),
        "small_epsilon_coefficient": float(easy_plane_current_limit(1e-5) / 1e-5),
        "large_epsilon_coefficient": float(easy_plane_current_limit(1e5) * 1e5),
        "finite_n_relative_errors": {
            str(epsilon): float(
                abs(
                    currents[(0.5, epsilon)][-1]
                    / easy_plane_current_limit(epsilon)
                    - 1.0
                )
            )
            for epsilon in couplings
        },
    }

    weak_results = []
    weak_current_errors = []
    weak_profile_errors = []
    for size in parameters["weak_coupling_sizes"]:
        for epsilon in parameters["weak_couplings"]:
            size = int(size)
            epsilon = float(epsilon)
            finite_profile = spin_profile(1.0, epsilon, size)
            sites = np.arange(1, size + 1, dtype=np.float64)
            perturbative_profile = epsilon**2 * (size + 1.0 - 2.0 * sites) / 4.0
            current_relative_error = float(
                abs(spin_current(1.0, epsilon, size) / (epsilon / 2.0) - 1.0)
            )
            profile_relative_error = float(
                np.max(np.abs(finite_profile - perturbative_profile))
                / np.max(np.abs(perturbative_profile))
            )
            weak_current_errors.append(current_relative_error)
            weak_profile_errors.append(profile_relative_error)
            weak_results.append(
                {
                    "n": size,
                    "epsilon": epsilon,
                    "epsilon_star": float(2.0 * np.pi / size),
                    "current_relative_error": current_relative_error,
                    "profile_relative_error": profile_relative_error,
                }
            )

    generated_half, _ = transfer_operators(0.5, 1.0, 100)
    printed_half = np.array(
        [[1.0, 0.5, 0.0], [0.5, 0.5, 10.0 / 24.0], [0.0, 0.75, 0.5]]
    )
    transfer_half_error = float(np.max(np.abs(generated_half - printed_half)))
    reflection_errors = [
        float(np.max(np.abs(values + values[::-1]))) for values in profiles.values()
    ]
    profile_bound_violation = max(
        float(max(0.0, np.max(np.abs(values)) - 1.0)) for values in profiles.values()
    )
    isotropic_profile_rmse_1 = float(
        np.sqrt(np.mean((profiles[(1.0, 1.0)] - isotropic_profile) ** 2))
    )
    isotropic_profile_rmse_point2 = float(
        np.sqrt(np.mean((profiles[(1.0, 0.2)] - isotropic_profile) ** 2))
    )

    target_axis_slope = -float(np.arccosh(1.5))
    science_assertions = [
        assertion("SC001", ["T001", "T002"], max(dense_magnetization_errors), tolerances["dense_observable_abs"], "max", "Transfer magnetization agrees with the independent dense Liouvillian NESS."),
        assertion("SC002", ["T002", "T003"], max(dense_current_errors), tolerances["dense_observable_abs"], "max", "Transfer current agrees with the independent dense Liouvillian NESS."),
        assertion("SC003", ["T002"], max(dense_current_spreads), tolerances["current_conservation_abs"], "max", "Dense NESS current is position independent."),
        assertion("SC004", ["T001", "T002"], max(dense_residuals), tolerances["dense_observable_abs"], "max", "Independent Liouvillian residual is small."),
        assertion("SC005", ["T001"], max(reflection_errors), tolerances["reflection_abs"], "max", "Every finite magnetization profile is reflection antisymmetric."),
        assertion("SC006", ["T001"], profile_bound_violation, tolerances["reflection_abs"], "max", "Every magnetization remains inside the Pauli-z bounds."),
        assertion("SC007", ["T004"], transfer_half_error, tolerances["transfer_matrix_abs"], "max", "Generic amplitudes reproduce the printed Delta=1/2 reduced transfer matrix."),
        assertion("SC008", ["T004"], max(easy_plane_summary["finite_n_relative_errors"].values()), tolerances["easy_plane_limit_relative"], "max", "Finite n=400 easy-plane currents reach the printed thermodynamic limit."),
        assertion("SC009", ["T004"], abs(easy_plane_summary["maximum_epsilon"] - 1.63), 0.01, "max", "Thermodynamic current maximum occurs near printed epsilon=1.63."),
        assertion("SC010", ["T004"], abs(easy_plane_summary["small_epsilon_coefficient"] - 0.5), 5e-6, "max", "Small-epsilon easy-plane coefficient is one half."),
        assertion("SC011", ["T004"], abs(easy_plane_summary["large_epsilon_coefficient"] - 4.0 / 3.0), 5e-5, "max", "Large-epsilon easy-plane coefficient is four thirds."),
        assertion("SC012", ["T003"], max(abs(item["slope"] - target_axis_slope) for item in easy_axis_slopes.values()), tolerances["easy_axis_slope_abs"], "max", "Easy-axis log-current slope is -arcosh(3/2) for every coupling."),
        assertion("SC013", ["T003"], min(item["r_squared"] for item in easy_axis_slopes.values()), 0.999, "min", "Easy-axis decay is exponentially linear on the declared fit interval."),
        assertion("SC014", ["T002"], abs(isotropic_slope + 2.0), tolerances["isotropic_slope_abs"], "max", "Isotropic finite-size current approaches n^-2 scaling."),
        assertion("SC015", ["T002"], abs(isotropic_coefficient_ratio - 1.0), 0.05, "max", "Isotropic n=400 current matches the printed pi^2/(epsilon n^2) coefficient."),
        assertion("SC016", ["T001"], isotropic_profile_rmse_1, 0.01, "max", "Isotropic epsilon=1 profile approaches the printed cosine."),
        assertion("SC017", ["T001"], isotropic_profile_rmse_point2, 0.05, "max", "Isotropic epsilon=1/5 profile approaches the printed cosine."),
        assertion("SC018", ["T005"], max(correlation_relative_errors), tolerances["correlation_scaled_relative"], "max", "Largest-size connected correlations approach the printed 1/n kernel."),
        assertion("SC019", ["T006"], max(weak_current_errors), tolerances["weak_current_relative"], "max", "Weak isotropic current approaches epsilon/2."),
        assertion("SC020", ["T006"], max(weak_profile_errors), tolerances["weak_profile_relative"], "max", "Weak isotropic profile approaches the printed perturbative line."),
    ]

    quantitative_claims = {
        "schema_version": 1,
        "paper_id": "1106.2978",
        "easy_plane": easy_plane_summary,
        "easy_axis": {
            "printed_slope": target_axis_slope,
            "fits_by_epsilon": easy_axis_slopes,
        },
        "isotropic": {
            "current_loglog_slope": isotropic_slope,
            "current_coefficient_ratio_at_n400_epsilon1": isotropic_coefficient_ratio,
            "profile_rmse_epsilon1": isotropic_profile_rmse_1,
            "profile_rmse_epsilon_point2": isotropic_profile_rmse_point2,
        },
        "weak_coupling": weak_results,
        "independent_dense_crosschecks": dense_results,
    }

    profile_path = data_root / "magnetization_profiles.csv"
    current_path = data_root / "current_scaling.csv"
    correlation_path = data_root / "correlation_checks.csv"
    claims_path = data_root / "quantitative_claims.json"
    checks_path = checks_root / "science_checks.json"
    write_csv(
        profile_path,
        ["target_id", "series_id", "series_kind", "n", "site", "x", "delta", "epsilon", "magnetization", "generated_data_provenance"],
        profile_rows,
    )
    write_csv(
        current_path,
        ["target_id", "series_id", "series_kind", "n", "delta", "epsilon", "current", "generated_data_provenance"],
        current_rows,
    )
    write_csv(
        correlation_path,
        ["target_id", "n", "site_j", "site_k", "x", "y", "finite_connected_correlation", "analytic_asymptote", "relative_error", "generated_data_provenance"],
        correlation_rows,
    )
    write_json(claims_path, quantitative_claims)
    write_json(
        checks_path,
        {
            "schema_version": 1,
            "paper_id": "1106.2978",
            "assertions": science_assertions,
            "summary": {
                "total": len(science_assertions),
                "passed": sum(item["passed"] for item in science_assertions),
                "failed": sum(not item["passed"] for item in science_assertions),
            },
        },
    )

    output_paths = [profile_path, current_path, correlation_path, claims_path, checks_path]
    manifest_path = checks_root / "generated_data_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "paper_id": "1106.2978",
            "config_path": str(config_path),
            "config_sha256": sha256(config_path),
            "source_pixels_used_as_scientific_inputs": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "artifacts": [
                {"path": str(path.relative_to(output_root)), "sha256": sha256(path)}
                for path in output_paths
            ],
        },
    )
    elapsed = time.perf_counter() - started
    run_summary_path = checks_root / "run_summary.json"
    passed = all(item["passed"] for item in science_assertions)
    write_json(
        run_summary_path,
        {
            "schema_version": 1,
            "paper_id": "1106.2978",
            "run_id": "1106.2978-paper-exact-v3",
            "execution_profile": config["execution_profile"],
            "elapsed_seconds": elapsed,
            "target_ids": ["T001", "T002", "T003", "T004", "T005", "T006"],
            "science_assertions_passed": sum(item["passed"] for item in science_assertions),
            "science_assertions_total": len(science_assertions),
            "status": "passed" if passed else "failed",
        },
    )
    print(json.dumps(json.loads(run_summary_path.read_text()), sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
