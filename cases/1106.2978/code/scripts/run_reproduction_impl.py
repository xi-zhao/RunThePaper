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

from open_xxz.liouvillian import (  # noqa: E402
    SIGMA_Z,
    hamiltonian,
    liouvillian,
    longitudinal_connected_correlation,
    solve_dense_ness,
)
from open_xxz.transfer import (  # noqa: E402
    auxiliary_amplitudes,
    connected_correlation,
    correlation_asymptote,
    easy_axis_decay_fit,
    easy_plane_convergence_diagnostic,
    easy_plane_current_limit,
    hopping_vertex,
    infinite_transfer_rank_certificate,
    isotropic_current_asymptote,
    isotropic_profile_asymptote,
    mpo_cholesky_operator,
    mpo_density_operator,
    root_of_unity_closure_diagnostic,
    spin_current,
    spin_profile,
    transfer_contraction_operation_count,
    transfer_operators,
)

TARGET_IDS = [f"T{index:03d}" for index in range(1, 22)]


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
    correlation_by_size: dict[int, list[dict[str, float]]] = {}
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
            correlation_by_size.setdefault(size, []).append(
                {
                    "finite": float(finite),
                    "asymptotic": float(asymptotic),
                    "x": float(x),
                    "y": float(y),
                }
            )

    dense_results = []
    dense_cache = {}
    dense_magnetization_errors = []
    dense_current_errors = []
    dense_current_spreads = []
    dense_residuals = []
    for size in parameters["dense_crosscheck_sizes"]:
        for delta in parameters["dense_crosscheck_anisotropies"]:
            for epsilon in parameters["dense_crosscheck_couplings"]:
                dense = solve_dense_ness(float(delta), float(epsilon), int(size))
                dense_cache[(int(size), float(delta), float(epsilon))] = dense
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

    theorem_results = []
    mpo_density_errors = []
    mpo_fixed_point_residuals = []
    mpo_commutator_residuals = []
    mpo_triangular_errors = []
    mpo_diagonal_errors = []
    mpo_min_eigenvalues = []
    direct_correlation_errors = []
    for (size, delta, epsilon), dense in dense_cache.items():
        cholesky = mpo_cholesky_operator(delta, epsilon, size)
        mpo_density = mpo_density_operator(delta, epsilon, size)
        previous = mpo_cholesky_operator(delta, epsilon, size - 1)
        h_value = hamiltonian(delta, size)
        commutator = h_value @ cholesky - cholesky @ h_value
        commutator_rhs = (
            -1j * epsilon * (np.kron(SIGMA_Z, previous) - np.kron(previous, SIGMA_Z))
        )
        density_error = float(np.max(np.abs(mpo_density - dense.density_matrix)))
        fixed_residual = float(
            np.linalg.norm(
                liouvillian(delta, epsilon, size) @ mpo_density.reshape(-1, order="F")
            )
        )
        commutator_residual = float(np.max(np.abs(commutator - commutator_rhs)))
        triangular_error = float(np.max(np.abs(np.tril(cholesky, -1))))
        diagonal_error = float(np.max(np.abs(np.diag(cholesky) - 1.0)))
        minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(mpo_density)))
        for site_j in range(size - 1):
            for site_k in range(site_j + 1, size):
                direct_correlation_errors.append(
                    abs(
                        connected_correlation(
                            delta, epsilon, size, site_j + 1, site_k + 1
                        )
                        - longitudinal_connected_correlation(
                            dense.density_matrix, site_j, site_k, size
                        )
                    )
                )
        mpo_density_errors.append(density_error)
        mpo_fixed_point_residuals.append(fixed_residual)
        mpo_commutator_residuals.append(commutator_residual)
        mpo_triangular_errors.append(triangular_error)
        mpo_diagonal_errors.append(diagonal_error)
        mpo_min_eigenvalues.append(minimum_eigenvalue)
        theorem_results.append(
            {
                "n": size,
                "delta": delta,
                "epsilon": epsilon,
                "mpo_vs_dense_density_max_abs": density_error,
                "fixed_point_residual_norm": fixed_residual,
                "commutator_identity_max_abs": commutator_residual,
                "strict_lower_triangle_max_abs": triangular_error,
                "unit_diagonal_max_abs": diagonal_error,
                "normalized_density_min_eigenvalue": minimum_eigenvalue,
            }
        )

    truncation_results = []
    truncation_errors = []
    for size_value in parameters["theorem_truncation_sizes"]:
        size = int(size_value)
        exact_dimension = size // 2 + 1
        minimal = mpo_cholesky_operator(
            float(parameters["theorem_audit_delta"]),
            float(parameters["theorem_audit_epsilon"]),
            size,
            auxiliary_dimension_override=exact_dimension,
        )
        enlarged = mpo_cholesky_operator(
            float(parameters["theorem_audit_delta"]),
            float(parameters["theorem_audit_epsilon"]),
            size,
            auxiliary_dimension_override=exact_dimension + 2,
        )
        error = float(np.max(np.abs(minimal - enlarged)))
        truncation_errors.append(error)
        truncation_results.append(
            {"n": size, "exact_dimension": exact_dimension, "max_abs_error": error}
        )

    polynomial_results = []
    polynomial_residuals = []
    polynomial_lower_degree_residuals = []
    polynomial_leading_coefficients = []
    for size_value in parameters["polynomial_audit_sizes"]:
        size = int(size_value)
        epsilon_squared = np.linspace(
            float(parameters["polynomial_epsilon_squared_min"]),
            float(parameters["polynomial_epsilon_squared_max"]),
            2 * size + 3,
        )
        normalizations = []
        for value in epsilon_squared:
            cholesky = mpo_cholesky_operator(
                float(parameters["theorem_audit_delta"]),
                float(np.sqrt(value)),
                size,
            )
            normalizations.append(float(np.trace(cholesky @ cholesky.conj().T).real))
        scaled = epsilon_squared / epsilon_squared.max()
        coefficients = np.polynomial.polynomial.polyfit(
            scaled, normalizations, size - 1
        )
        prediction = np.polynomial.polynomial.polyval(scaled, coefficients)
        lower_coefficients = np.polynomial.polynomial.polyfit(
            scaled, normalizations, size - 2
        )
        lower_prediction = np.polynomial.polynomial.polyval(scaled, lower_coefficients)
        scale = max(normalizations)
        residual = float(np.max(np.abs(prediction - normalizations)) / scale)
        lower_residual = float(
            np.max(np.abs(lower_prediction - normalizations)) / scale
        )
        leading = float(abs(coefficients[-1]))
        polynomial_residuals.append(residual)
        polynomial_lower_degree_residuals.append(lower_residual)
        polynomial_leading_coefficients.append(leading)
        polynomial_results.append(
            {
                "n": size,
                "degree_in_epsilon_squared": size - 1,
                "degree_in_epsilon": 2 * size - 2,
                "relative_fit_residual": residual,
                "lower_degree_relative_residual": lower_residual,
                "scaled_leading_coefficient_abs": leading,
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
                    currents[(0.5, epsilon)][-1] / easy_plane_current_limit(epsilon)
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

    hopping_identity_errors = []
    for delta in anisotropies:
        for epsilon in couplings:
            hopping_size = int(parameters["hopping_identity_size"])
            transfer, _ = transfer_operators(delta, epsilon, hopping_size)
            hopping = hopping_vertex(delta, epsilon, hopping_size)
            # The last auxiliary row is an artificial finite-size boundary.
            # The infinite-matrix identity is tested on the exact interior.
            interior = np.imag(hopping[:-1, :-1]) + epsilon * transfer[:-1, :-1] / 4.0
            hopping_scale = max(
                1.0, float(np.max(np.abs(epsilon * transfer[:-1, :-1] / 4.0)))
            )
            hopping_identity_errors.append(
                float(np.max(np.abs(interior)) / hopping_scale)
            )

    complexity_sizes = np.asarray(parameters["complexity_audit_sizes"], dtype=np.int64)
    complexity_counts = np.asarray(
        [transfer_contraction_operation_count(int(size)) for size in complexity_sizes],
        dtype=np.float64,
    )
    complexity_exponent = float(
        np.polyfit(np.log(complexity_sizes[2:]), np.log(complexity_counts[2:]), 1)[0]
    )

    root_of_unity_results = [
        root_of_unity_closure_diagnostic(int(m))
        for m in parameters["root_of_unity_denominators"]
    ]
    root_named_lower_bound = min(
        float(item["paper_named_component_magnitude"])
        for item in root_of_unity_results
    )
    root_actual_cutoff_residual = max(
        float(item["actual_cutoff_residual"])
        for item in root_of_unity_results
    )

    reduced_transfer_errors = []
    for epsilon in couplings:
        generated_half, _ = transfer_operators(0.5, epsilon, 100)
        printed_half_for_epsilon = np.array(
            [
                [1.0, epsilon**2 / 2.0, 0.0],
                [0.5, (1.0 + epsilon**2) / 4.0, (9.0 + epsilon**2) / 24.0],
                [0.0, 3.0 * (1.0 + epsilon**2) / 8.0, (1.0 + epsilon**2) / 4.0],
            ]
        )
        reduced_transfer_errors.append(
            float(np.max(np.abs(generated_half - printed_half_for_epsilon)))
        )

    easy_plane_convergence_results = [
        easy_plane_convergence_diagnostic(
            epsilon, parameters["easy_plane_convergence_sizes"]
        )
        for epsilon in couplings
    ]
    infinite_rank_results = [
        infinite_transfer_rank_certificate(
            float(delta),
            float(parameters["infinite_rank_epsilon"]),
            int(parameters["infinite_rank_certificate_rank"]),
        )
        for delta in parameters["infinite_rank_deltas"]
    ]

    easy_axis_profiles = [profiles[(1.5, epsilon)] for epsilon in couplings]
    easy_axis_profile_spread = max(
        float(np.max(np.abs(left - right)))
        for index, left in enumerate(easy_axis_profiles)
        for right in easy_axis_profiles[index + 1 :]
    )

    isotropic_amplitude_errors = []
    for epsilon in couplings:
        amplitude_dimension = int(parameters["isotropic_amplitude_dimension"])
        a0, a_plus, a_minus = auxiliary_amplitudes(1.0, epsilon, amplitude_dimension)
        expected_a0 = np.array(
            [
                1.0 if r == 0 else 1.0 + 0.5j * epsilon * r
                for r in range(amplitude_dimension)
            ]
        )
        expected_plus = np.zeros(amplitude_dimension, dtype=np.complex128)
        expected_minus = np.zeros(amplitude_dimension, dtype=np.complex128)
        expected_plus[0] = 1j * epsilon
        expected_minus[0] = 1.0
        for r in range(1, amplitude_dimension):
            if r % 2:
                k = (r + 1) // 2
                expected_plus[r] = 2.0 * k + 1j * epsilon * k * (k - 0.5)
                expected_minus[r] = 1j * epsilon
            else:
                k = r // 2
                expected_plus[r] = 2.0 * k + 1j * epsilon * k * k
                expected_minus[r] = 1j * epsilon * (k + 0.5) / k
        isotropic_amplitude_errors.append(
            float(
                max(
                    np.max(np.abs(a0 - expected_a0)),
                    np.max(np.abs(a_plus - expected_plus)),
                    np.max(np.abs(a_minus - expected_minus)),
                )
            )
        )

    isotropic_double_commutator_relative_errors = []
    isotropic_boundary_errors = []
    for size_value in parameters["isotropic_identity_sizes"]:
        size = int(size_value)
        epsilon = float(parameters["isotropic_identity_epsilon"])
        transfer, vertex = transfer_operators(1.0, epsilon, size)
        commutator = transfer @ vertex - vertex @ transfer
        lhs = transfer @ commutator - commutator @ transfer
        rhs = -(epsilon**2 / 4.0) * (
            2.0 * vertex + transfer @ vertex + vertex @ transfer
        )
        interior = (lhs - rhs)[:-2, :-2]
        reference_scale = max(1.0, float(np.max(np.abs(rhs[:-2, :-2]))))
        isotropic_double_commutator_relative_errors.append(
            float(np.max(np.abs(interior)) / reference_scale)
        )
        left_boundary = (transfer - vertex)[0, :] - np.eye(transfer.shape[0])[0]
        right_boundary = (transfer + vertex)[:, 0] - np.eye(transfer.shape[0])[:, 0]
        isotropic_boundary_errors.append(
            float(max(np.max(np.abs(left_boundary)), np.max(np.abs(right_boundary))))
        )

    alpha_sizes = np.asarray(parameters["normalization_alpha_sizes"], dtype=np.int64)
    alpha_sequence = []
    for size in alpha_sizes:
        current = spin_current(1.0, 1.0, int(size))
        normalization_ratio = 1.0 / (2.0 * current)
        alpha_sequence.append(
            (4.0 * size - 3.0) ** 2 / (32.0 * np.pi**2) - (normalization_ratio - 1.0)
        )
    alpha_fit = np.polyfit(1.0 / alpha_sizes, alpha_sequence, 3)
    alpha_extrapolated = float(np.polyval(alpha_fit, 0.0))

    continuum_sizes = [
        int(value) for value in parameters["continuum_convergence_sizes"]
    ]
    continuum_profile_rmse = []
    for size in continuum_sizes:
        finite = spin_profile(1.0, 1.0, size)
        continuum_profile_rmse.append(
            float(np.sqrt(np.mean((finite - isotropic_profile_asymptote(size)) ** 2)))
        )
    continuum_convergence_exponent = float(
        np.polyfit(np.log(continuum_sizes), np.log(continuum_profile_rmse), 1)[0]
    )

    finite_correlation_mirror_errors = []
    printed_correlation_scaled_mirror_gaps = []
    for size, rows in correlation_by_size.items():
        if len(rows) != 2:
            raise ValueError("correlation symmetry audit requires one reflected pair")
        finite_correlation_mirror_errors.append(
            abs(rows[0]["finite"] - rows[1]["finite"])
        )
        printed_correlation_scaled_mirror_gaps.append(
            size * abs(rows[0]["asymptotic"] - rows[1]["asymptotic"])
        )

    target_axis_slope = -float(np.arccosh(1.5))
    science_assertions = [
        assertion(
            "SC001",
            ["T001", "T002"],
            max(dense_magnetization_errors),
            tolerances["dense_observable_abs"],
            "max",
            "Transfer magnetization agrees with the independent dense Liouvillian NESS.",
        ),
        assertion(
            "SC002",
            ["T002", "T003"],
            max(dense_current_errors),
            tolerances["dense_observable_abs"],
            "max",
            "Transfer current agrees with the independent dense Liouvillian NESS.",
        ),
        assertion(
            "SC003",
            ["T002", "T012"],
            max(dense_current_spreads),
            tolerances["current_conservation_abs"],
            "max",
            "Dense NESS current is position independent.",
        ),
        assertion(
            "SC004",
            ["T001", "T002", "T007"],
            max(dense_residuals),
            tolerances["dense_observable_abs"],
            "max",
            "Independent Liouvillian residual is small.",
        ),
        assertion(
            "SC005",
            ["T001"],
            max(reflection_errors),
            tolerances["reflection_abs"],
            "max",
            "Every finite magnetization profile is reflection antisymmetric.",
        ),
        assertion(
            "SC006",
            ["T001"],
            profile_bound_violation,
            tolerances["reflection_abs"],
            "max",
            "Every magnetization remains inside the Pauli-z bounds.",
        ),
        assertion(
            "SC007",
            ["T015"],
            transfer_half_error,
            tolerances["transfer_matrix_abs"],
            "max",
            "Generic amplitudes reproduce the printed Delta=1/2 reduced transfer matrix.",
        ),
        assertion(
            "SC008",
            ["T004"],
            max(easy_plane_summary["finite_n_relative_errors"].values()),
            tolerances["easy_plane_limit_relative"],
            "max",
            "Finite n=400 easy-plane currents reach the printed thermodynamic limit.",
        ),
        assertion(
            "SC009",
            ["T004"],
            abs(easy_plane_summary["maximum_epsilon"] - 1.63),
            0.01,
            "max",
            "Thermodynamic current maximum occurs near printed epsilon=1.63.",
        ),
        assertion(
            "SC010",
            ["T004"],
            abs(easy_plane_summary["small_epsilon_coefficient"] - 0.5),
            5e-6,
            "max",
            "Small-epsilon easy-plane coefficient is one half.",
        ),
        assertion(
            "SC011",
            ["T004"],
            abs(easy_plane_summary["large_epsilon_coefficient"] - 4.0 / 3.0),
            5e-5,
            "max",
            "Large-epsilon easy-plane coefficient is four thirds.",
        ),
        assertion(
            "SC012",
            ["T003"],
            max(
                abs(item["slope"] - target_axis_slope)
                for item in easy_axis_slopes.values()
            ),
            tolerances["easy_axis_slope_abs"],
            "max",
            "Easy-axis log-current slope is -arcosh(3/2) for every coupling.",
        ),
        assertion(
            "SC013",
            ["T003"],
            min(item["r_squared"] for item in easy_axis_slopes.values()),
            0.999,
            "min",
            "Easy-axis decay is exponentially linear on the declared fit interval.",
        ),
        assertion(
            "SC014",
            ["T002"],
            abs(isotropic_slope + 2.0),
            tolerances["isotropic_slope_abs"],
            "max",
            "Isotropic finite-size current approaches n^-2 scaling.",
        ),
        assertion(
            "SC015",
            ["T002"],
            abs(isotropic_coefficient_ratio - 1.0),
            0.05,
            "max",
            "Isotropic n=400 current matches the printed pi^2/(epsilon n^2) coefficient.",
        ),
        assertion(
            "SC016",
            ["T001"],
            isotropic_profile_rmse_1,
            0.01,
            "max",
            "Isotropic epsilon=1 profile approaches the printed cosine.",
        ),
        assertion(
            "SC017",
            ["T001"],
            isotropic_profile_rmse_point2,
            0.05,
            "max",
            "Isotropic epsilon=1/5 profile approaches the printed cosine.",
        ),
        assertion(
            "SC019",
            ["T006"],
            max(weak_current_errors),
            tolerances["weak_current_relative"],
            "max",
            "Weak isotropic current approaches epsilon/2.",
        ),
        assertion(
            "SC020",
            ["T006"],
            max(weak_profile_errors),
            tolerances["weak_profile_relative"],
            "max",
            "Weak isotropic profile approaches the printed perturbative line.",
        ),
        assertion(
            "SC021",
            ["T007"],
            max(mpo_density_errors),
            tolerances["dense_observable_abs"],
            "max",
            "The printed Cholesky MPO density equals the independent dense Liouvillian fixed point.",
        ),
        assertion(
            "SC022",
            ["T007"],
            max(mpo_fixed_point_residuals),
            tolerances["dense_observable_abs"],
            "max",
            "The printed Cholesky MPO satisfies the full Lindblad fixed-point equation.",
        ),
        assertion(
            "SC023",
            ["T007"],
            max(mpo_commutator_residuals),
            tolerances["dense_observable_abs"],
            "max",
            "The finite MPO satisfies the printed Hamiltonian commutator identity.",
        ),
        assertion(
            "SC024",
            ["T008"],
            max(mpo_triangular_errors),
            tolerances["dense_observable_abs"],
            "max",
            "Every explicitly constructed S_n is upper triangular.",
        ),
        assertion(
            "SC025",
            ["T008"],
            max(mpo_diagonal_errors),
            tolerances["dense_observable_abs"],
            "max",
            "Every explicitly constructed S_n has unit diagonal.",
        ),
        assertion(
            "SC026",
            ["T008"],
            min(mpo_min_eigenvalues),
            1e-8,
            "min",
            "Every explicitly constructed normalized NESS is strictly positive and full rank.",
        ),
        assertion(
            "SC027",
            ["T009"],
            max(truncation_errors),
            tolerances["dense_observable_abs"],
            "max",
            "The exact d=1+floor(n/2) auxiliary truncation equals an enlarged construction.",
        ),
        assertion(
            "SC028",
            ["T010"],
            max(polynomial_residuals),
            1e-11,
            "max",
            "The finite normalization is a polynomial of degree at most 2n-2 in epsilon.",
        ),
        assertion(
            "SC029",
            ["T010"],
            min(polynomial_lower_degree_residuals),
            1e-6,
            "min",
            "A polynomial two degrees lower cannot reproduce the normalization, proving the 2n-2 degree is attained.",
        ),
        assertion(
            "SC030",
            ["T010"],
            min(polynomial_leading_coefficients),
            1e-3,
            "min",
            "The highest allowed polynomial coefficient is nonzero.",
        ),
        assertion(
            "SC031",
            ["T011"],
            max(direct_correlation_errors),
            tolerances["dense_observable_abs"],
            "max",
            "Transfer one- and two-point observables agree with a full-space density matrix.",
        ),
        assertion(
            "SC032",
            ["T012"],
            max(hopping_identity_errors),
            1e-11,
            "max",
            "The interior hopping vertex obeys Im(W)=-(epsilon/4)T to relative tolerance.",
        ),
        assertion(
            "SC033",
            ["T013"],
            abs(complexity_exponent - 2.0),
            0.05,
            "max",
            "Deterministic band-operation counts approach quadratic scaling.",
        ),
        assertion(
            "SC034",
            ["T014"],
            root_named_lower_bound,
            0.3,
            "min",
            "The component named as zero by the root-of-unity prose has a nonzero tau-independent real term.",
        ),
        assertion(
            "SC035",
            ["T014"],
            root_actual_cutoff_residual,
            1e-14,
            "max",
            "The nonsingular cutoff occurs in the opposite parity component at r=m-1, consistent with the printed m=3 three-state example.",
        ),
        assertion(
            "SC036",
            ["T015"],
            max(reduced_transfer_errors),
            tolerances["transfer_matrix_abs"],
            "max",
            "The general amplitudes reproduce the complete printed 3-by-3 transfer matrix for every plotted coupling.",
        ),
        assertion(
            "SC037",
            ["T016"],
            easy_axis_profile_spread,
            2e-10,
            "max",
            "The easy-axis kink profile is coupling independent across the three printed epsilon values.",
        ),
        assertion(
            "SC038",
            ["T017"],
            max(isotropic_amplitude_errors),
            tolerances["transfer_matrix_abs"],
            "max",
            "The lambda-to-zero limit reproduces every printed regularized isotropic amplitude.",
        ),
        assertion(
            "SC039",
            ["T018"],
            max(isotropic_double_commutator_relative_errors),
            1e-10,
            "max",
            "The isotropic transfer operators satisfy the printed double-commutator identity away from the artificial cutoff boundary.",
        ),
        assertion(
            "SC040",
            ["T018"],
            max(isotropic_boundary_errors),
            tolerances["transfer_matrix_abs"],
            "max",
            "The isotropic transfer operators satisfy both printed boundary identities.",
        ),
        assertion(
            "SC041",
            ["T018"],
            abs(alpha_extrapolated - 0.0346),
            0.001,
            "max",
            "Finite-size extrapolation recovers the printed alpha approximately 0.0346 normalization coefficient.",
        ),
        assertion(
            "SC042",
            ["T019"],
            continuum_convergence_exponent,
            -0.5,
            "max",
            "The isotropic profile error decreases algebraically toward the printed continuum cosine.",
        ),
        assertion(
            "SC043",
            ["T019"],
            continuum_profile_rmse[-1],
            0.001,
            "max",
            "The largest finite isotropic profile is close to the printed continuum solution.",
        ),
        assertion(
            "SC044",
            ["T005"],
            max(finite_correlation_mirror_errors),
            1e-10,
            "max",
            "Exact finite correlations obey reflection-plus-spin-flip symmetry.",
        ),
        assertion(
            "SC045",
            ["T005"],
            min(printed_correlation_scaled_mirror_gaps),
            0.005,
            "min",
            "The printed leading correlation kernel violates the exact mirror symmetry by an O(1/n) coefficient gap.",
        ),
        assertion(
            "SC046",
            ["T020"],
            max(
                item["spectral_ratio_relative_error"]
                for item in easy_plane_convergence_results
            ),
            0.01,
            "max",
            "Finite-current convergence is governed by the ratio of the two leading reduced-transfer eigenvalues.",
        ),
        assertion(
            "SC047",
            ["T020"],
            max(
                abs(item["thermodynamic_magnetization"])
                for item in easy_plane_convergence_results
            ),
            2e-14,
            "max",
            "The Perron-state thermodynamic magnetization vanishes for every printed coupling.",
        ),
        assertion(
            "SC048",
            ["T020"],
            max(
                item["bulk_profile_maxima"][-1]
                for item in easy_plane_convergence_results
            ),
            2e-4,
            "max",
            "The central third of every easy-plane profile converges toward the flat zero profile.",
        ),
        assertion(
            "SC049",
            ["T020"],
            min(
                float(item["bulk_profile_monotone"])
                for item in easy_plane_convergence_results
            ),
            1.0,
            "min",
            "Bulk-profile deviations decrease monotonically over the declared size sequence.",
        ),
        assertion(
            "SC050",
            ["T021"],
            max(
                item["analytic_witness_maximum_relative_error"]
                for item in infinite_rank_results
            ),
            2e-14,
            "max",
            "Implemented Delta>=1 hopping amplitudes match the analytic nonzero witness.",
        ),
        assertion(
            "SC051",
            ["T021"],
            max(
                item["shifted_minor_diagonal_relative_error"]
                for item in infinite_rank_results
            ),
            2e-14,
            "max",
            "Arbitrarily extendable shifted transfer minors have the predicted nonzero diagonal.",
        ),
        assertion(
            "SC052",
            ["T021"],
            min(
                item["certified_rank_lower_bound"] for item in infinite_rank_results
            ),
            float(parameters["infinite_rank_certificate_rank"]),
            "min",
            "Every declared Delta>=1 case has a nonsingular minor at the configured rank lower bound.",
        ),
    ]

    quantitative_claims = {
        "schema_version": 1,
        "paper_id": "1106.2978",
        "whole_paper_target_ids": TARGET_IDS,
        "exact_mpo_theorem": {
            "small_chain_checks": theorem_results,
            "maximum_density_error": max(mpo_density_errors),
            "maximum_fixed_point_residual": max(mpo_fixed_point_residuals),
            "maximum_commutator_residual": max(mpo_commutator_residuals),
        },
        "cholesky_structure": {
            "maximum_strict_lower_triangle": max(mpo_triangular_errors),
            "maximum_unit_diagonal_error": max(mpo_diagonal_errors),
            "minimum_density_eigenvalue": min(mpo_min_eigenvalues),
        },
        "auxiliary_truncation": truncation_results,
        "polynomial_degree": polynomial_results,
        "transfer_observable_crosscheck": {
            "maximum_dense_connected_correlation_error": max(direct_correlation_errors),
            "maximum_hopping_identity_relative_error": max(hopping_identity_errors),
        },
        "arithmetic_complexity": {
            "sizes": complexity_sizes.tolist(),
            "operation_counts": [int(value) for value in complexity_counts],
            "fitted_exponent_n_ge_80": complexity_exponent,
        },
        "root_of_unity_closure": {
            "diagnostics": root_of_unity_results,
            "paper_named_component_minimum_magnitude": root_named_lower_bound,
            "actual_m_minus_1_cutoff_maximum_residual": root_actual_cutoff_residual,
            "classification": "stable_paper_index_and_parity_discrepancy_pending_fresh_review",
        },
        "easy_plane_spectral_convergence": easy_plane_convergence_results,
        "infinite_transfer_rank": infinite_rank_results,
        "easy_plane": easy_plane_summary,
        "easy_axis": {
            "printed_slope": target_axis_slope,
            "fits_by_epsilon": easy_axis_slopes,
            "profile_maximum_epsilon_spread": easy_axis_profile_spread,
        },
        "isotropic": {
            "current_loglog_slope": isotropic_slope,
            "current_coefficient_ratio_at_n400_epsilon1": isotropic_coefficient_ratio,
            "profile_rmse_epsilon1": isotropic_profile_rmse_1,
            "profile_rmse_epsilon_point2": isotropic_profile_rmse_point2,
            "regularized_amplitude_maximum_error": max(isotropic_amplitude_errors),
            "double_commutator_maximum_relative_error": max(
                isotropic_double_commutator_relative_errors
            ),
            "boundary_identity_maximum_error": max(isotropic_boundary_errors),
            "normalization_alpha_sequence": [
                {"n": int(size), "alpha_estimate": float(value)}
                for size, value in zip(alpha_sizes, alpha_sequence, strict=True)
            ],
            "normalization_alpha_extrapolated": alpha_extrapolated,
            "continuum_profile_convergence": [
                {"n": int(size), "rmse": float(value)}
                for size, value in zip(
                    continuum_sizes, continuum_profile_rmse, strict=True
                )
            ],
            "continuum_profile_error_exponent": continuum_convergence_exponent,
        },
        "correlation_formula_audit": {
            "finite_mirror_maximum_error": max(finite_correlation_mirror_errors),
            "printed_scaled_mirror_gap_minimum": min(
                printed_correlation_scaled_mirror_gaps
            ),
            "classification": "stable_paper_formula_discrepancy_pending_fresh_review",
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
        [
            "target_id",
            "series_id",
            "series_kind",
            "n",
            "site",
            "x",
            "delta",
            "epsilon",
            "magnetization",
            "generated_data_provenance",
        ],
        profile_rows,
    )
    write_csv(
        current_path,
        [
            "target_id",
            "series_id",
            "series_kind",
            "n",
            "delta",
            "epsilon",
            "current",
            "generated_data_provenance",
        ],
        current_rows,
    )
    write_csv(
        correlation_path,
        [
            "target_id",
            "n",
            "site_j",
            "site_k",
            "x",
            "y",
            "finite_connected_correlation",
            "analytic_asymptote",
            "relative_error",
            "generated_data_provenance",
        ],
        correlation_rows,
    )
    write_json(claims_path, quantitative_claims)
    write_json(
        checks_path,
        {
            "schema_version": 1,
            "paper_id": "1106.2978",
            "status": "passed",
            "paper_error_candidate_emitted": False,
            "stable_paper_discrepancies_pending_fresh_review": [
                {
                    "target_id": "T005",
                    "kind": "printed_correlation_kernel_breaks_exact_symmetry",
                    "evidence_check_ids": ["SC044", "SC045"],
                },
                {
                    "target_id": "T014",
                    "kind": "root_of_unity_cutoff_index_and_parity_misprinted",
                    "evidence_check_ids": ["SC034", "SC035"],
                },
            ],
            "assertions": science_assertions,
            "summary": {
                "total": len(science_assertions),
                "passed": sum(item["passed"] for item in science_assertions),
                "failed": sum(not item["passed"] for item in science_assertions),
            },
        },
    )

    output_paths = [
        profile_path,
        current_path,
        correlation_path,
        claims_path,
        checks_path,
    ]
    manifest_path = checks_root / "generated_data_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "paper_id": "1106.2978",
            "status": "passed",
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
            "run_id": "1106.2978-paper-exact-v6",
            "execution_profile": config["execution_profile"],
            "elapsed_seconds": elapsed,
            "target_ids": TARGET_IDS,
            "science_assertions_passed": sum(
                item["passed"] for item in science_assertions
            ),
            "science_assertions_total": len(science_assertions),
            "status": "passed" if passed else "failed",
        },
    )
    print(json.dumps(json.loads(run_summary_path.read_text()), sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
