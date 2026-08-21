#!/usr/bin/env python3
"""Whole-paper scientific reproduction for Datta--Shaji--Caves (2008)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dqc1_discord.model import (  # noqa: E402
    analytic_typical_discord,
    brickwork_pseudorandom_unitary,
    discord_at_phi,
    discord_from_eigenphases,
    dqc1_sampling_bound,
    dqc1_separable_reconstruction,
    dqc1_state,
    eigenphase_spacing_statistics,
    first_symmetric_extension_contract,
    foundational_information_audit,
    haar_unitary,
    negativity,
    negativity_control,
    realignment_trace_norm,
    separable_example_state,
    two_qubit_discord_second,
    unitary_power,
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unitary_evidence(
    generator: str,
    instance: int,
    unitary: np.ndarray,
) -> tuple[np.ndarray, dict[str, object], list[dict[str, object]]]:
    phases = np.sort(np.mod(np.angle(np.linalg.eigvals(unitary)), 2.0 * np.pi))
    tau = np.trace(unitary) / unitary.shape[0]
    spacing = eigenphase_spacing_statistics(phases)
    summary = {
        "generator": generator,
        "instance": instance,
        "tau_real": float(tau.real),
        "tau_imag": float(tau.imag),
        "tau_abs": float(abs(tau)),
        "unitarity_residual": float(
            np.linalg.norm(unitary.conj().T @ unitary - np.eye(unitary.shape[0]))
        ),
        **spacing,
    }
    rows = [
        {
            "generator": generator,
            "instance": instance,
            "phase_index": phase_index,
            "eigenphase": float(phase),
        }
        for phase_index, phase in enumerate(phases)
    ]
    return phases, summary, rows


def generate_ensemble(
    generator: str,
    qubits: int,
    instances: int,
    rng: np.random.Generator,
    circuit_depth: int,
) -> tuple[np.ndarray, list[dict[str, object]], list[dict[str, object]]]:
    dimension = 2**qubits
    phase_matrix = np.empty((instances, dimension), dtype=float)
    summary_rows: list[dict[str, object]] = []
    phase_rows: list[dict[str, object]] = []
    for instance in range(instances):
        if generator == "qr_haar":
            unitary = haar_unitary(dimension, rng)
        elif generator == "independent_brickwork":
            unitary = brickwork_pseudorandom_unitary(qubits, circuit_depth, rng)
        else:
            raise ValueError(f"unknown generator: {generator}")
        phases, summary, rows = unitary_evidence(generator, instance, unitary)
        phase_matrix[instance] = phases
        summary_rows.append(summary)
        phase_rows.extend(rows)
    return phase_matrix, summary_rows, phase_rows


def ensemble_discord_rows(
    generator: str,
    phase_matrix: np.ndarray,
    alpha_values: np.ndarray,
    phi_grid_points: int,
) -> tuple[np.ndarray, list[dict[str, object]]]:
    values = np.empty((phase_matrix.shape[0], len(alpha_values)), dtype=float)
    rows: list[dict[str, object]] = []
    for instance, phases in enumerate(phase_matrix):
        tau = np.mean(np.exp(1j * phases))
        for alpha_index, alpha in enumerate(alpha_values):
            discord, optimal_phi = discord_from_eigenphases(
                phases, float(alpha), phi_grid_points
            )
            values[instance, alpha_index] = discord
            rows.append(
                {
                    "generator": generator,
                    "instance": instance,
                    "alpha_index": alpha_index,
                    "alpha": float(alpha),
                    "discord": discord,
                    "optimal_phi": optimal_phi,
                    "tau_real": float(tau.real),
                    "tau_imag": float(tau.imag),
                    "tau_abs": float(abs(tau)),
                }
            )
    return values, rows


def curve_rows(
    ensembles: dict[str, np.ndarray],
    alpha_values: np.ndarray,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for alpha_index, alpha in enumerate(alpha_values):
        analytic = float(analytic_typical_discord(alpha))
        row: dict[str, object] = {
            "alpha_index": alpha_index,
            "alpha": float(alpha),
            "analytic_discord": analytic,
        }
        for generator, matrix in ensembles.items():
            values = matrix[:, alpha_index]
            mean = float(np.mean(values))
            std = float(np.std(values, ddof=1))
            sem = std / np.sqrt(len(values))
            row[f"{generator}_mean"] = mean
            row[f"{generator}_std"] = std
            row[f"{generator}_sem"] = sem
            row[f"{generator}_ci95_low"] = mean - 1.959963984540054 * sem
            row[f"{generator}_ci95_high"] = mean + 1.959963984540054 * sem
            row[f"{generator}_mean_minus_analytic"] = mean - analytic
        row["generator_mean_difference"] = float(
            row["independent_brickwork_mean"] - row["qr_haar_mean"]
        )
        rows.append(row)
    return rows


def separability_rows(
    parameters: dict[str, object],
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(parameters["seed_separability"]))
    rows: list[dict[str, object]] = []
    for qubits in parameters["separability_qubits"]:
        unitary = haar_unitary(2 ** int(qubits), rng)
        for alpha, exponent in itertools.product(
            parameters["separability_alphas"], parameters["separability_stages"]
        ):
            stage = unitary_power(unitary, float(exponent))
            reconstructed, residual, minimum_factor = dqc1_separable_reconstruction(
                stage, float(alpha)
            )
            state = dqc1_state(stage, float(alpha))
            rows.append(
                {
                    "qubits": int(qubits),
                    "dimension": 2 ** int(qubits),
                    "alpha": float(alpha),
                    "unitary_stage_exponent": float(exponent),
                    "reconstruction_frobenius_residual": residual,
                    "minimum_product_factor_eigenvalue": minimum_factor,
                    "control_register_negativity": negativity_control(state),
                    "reconstructed_trace_error": float(
                        abs(np.trace(reconstructed) - 1.0)
                    ),
                }
            )
    return rows


def grouped_partition_rows(
    parameters: dict[str, object],
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(parameters["seed_partitions"]))
    rows: list[dict[str, object]] = []
    for qubits in parameters["partition_qubits"]:
        qubits = int(qubits)
        dimensions = (2,) * (qubits + 1)
        register_subsystems = tuple(range(1, qubits + 1))
        groups = [
            (0,) + selected
            for count in range(qubits)
            for selected in itertools.combinations(register_subsystems, count)
        ]
        for instance in range(int(parameters["partition_instances"])):
            unitary = haar_unitary(2**qubits, rng)
            for alpha, group in itertools.product(
                parameters["partition_alphas"], groups
            ):
                state = dqc1_state(unitary, float(alpha))
                rows.append(
                    {
                        "qubits": qubits,
                        "instance": instance,
                        "alpha": float(alpha),
                        "first_group": "-".join(map(str, group)),
                        "first_group_dimension": 2 ** len(group),
                        "second_group_dimension": 2 ** (qubits + 1 - len(group)),
                        "negativity": negativity(state, dimensions, group),
                        "realignment_trace_norm": realignment_trace_norm(
                            state, dimensions, group
                        ),
                    }
                )
    return rows


def circuit_convergence_rows(
    parameters: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    qubits = int(parameters["mixed_qubits"])
    instances = int(parameters["convergence_instances"])
    alpha_values = [float(value) for value in parameters["convergence_alphas"]]
    for depth in parameters["circuit_convergence_depths"]:
        rng = np.random.default_rng(int(parameters["seed_convergence"]) + int(depth))
        phase_matrix, summaries, _ = generate_ensemble(
            "independent_brickwork", qubits, instances, rng, int(depth)
        )
        for alpha in alpha_values:
            discords = np.asarray(
                [
                    discord_from_eigenphases(
                        phases, alpha, int(parameters["phi_grid_points"])
                    )[0]
                    for phases in phase_matrix
                ]
            )
            rows.append(
                {
                    "depth": int(depth),
                    "instances": instances,
                    "alpha": alpha,
                    "mean_discord": float(np.mean(discords)),
                    "std_discord": float(np.std(discords, ddof=1)),
                    "sem_discord": float(np.std(discords, ddof=1) / np.sqrt(instances)),
                    "mean_tau_abs": float(
                        np.mean([float(row["tau_abs"]) for row in summaries])
                    ),
                    "mean_gap_relative_rms": float(
                        np.mean([float(row["gap_relative_rms"]) for row in summaries])
                    ),
                }
            )
    return rows


def root_phi_rows(parameters: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    points = int(parameters["root_phi_grid_points"])
    for dimension, alpha in itertools.product(
        parameters["root_dimensions"], parameters["root_alphas"]
    ):
        dimension = int(dimension)
        alpha = float(alpha)
        phases = 2.0 * np.pi * np.arange(dimension) / dimension
        phis = np.linspace(0.0, 2.0 * np.pi / dimension, points, endpoint=False)
        discord_values = []
        conditional_values = []
        for phi in phis:
            discord, conditional, _, _ = discord_at_phi(phases, alpha, float(phi))
            discord_values.append(discord)
            conditional_values.append(conditional)
        at_zero = discord_at_phi(phases, alpha, 0.0)
        at_half_cell = discord_at_phi(phases, alpha, np.pi / dimension)
        rows.append(
            {
                "dimension": dimension,
                "qubits": int(np.log2(dimension)),
                "alpha": alpha,
                "phi_period": 2.0 * np.pi / dimension,
                "discord_min": float(np.min(discord_values)),
                "discord_max": float(np.max(discord_values)),
                "discord_range": float(np.ptp(discord_values)),
                "conditional_entropy_range": float(np.ptp(conditional_values)),
                "half_cell_q_plus_max_difference": float(
                    np.max(np.abs(np.sort(at_zero[2]) - np.sort(at_half_cell[2])))
                ),
                "half_cell_q_minus_max_difference": float(
                    np.max(np.abs(np.sort(at_zero[3]) - np.sort(at_half_cell[3])))
                ),
                "minimum_discord_minus_continuum": float(
                    np.min(discord_values) - analytic_typical_discord(alpha)
                ),
            }
        )
    return rows


def sampling_complexity_rows(parameters: dict[str, object]) -> list[dict[str, object]]:
    """Freeze the paper's fixed-accuracy ``1/alpha^2`` trial overhead."""

    rows: list[dict[str, object]] = []
    rms_error = float(parameters["sampling_rms_error"])
    for qubits, alpha in itertools.product(
        parameters["sampling_qubits"], parameters["sampling_alphas"]
    ):
        bound = dqc1_sampling_bound(float(alpha), rms_error)
        rows.append(
            {
                "register_qubits": int(qubits),
                **bound,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    output = (WORKSPACE / args.output_root).resolve()
    data_dir = output / "data"
    checks_dir = output / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    qubits = int(parameters["mixed_qubits"])
    instances = int(parameters["ensemble_instances"])
    alpha_values = np.linspace(0.0, 1.0, int(parameters["alpha_grid_points"]))
    ensembles: dict[str, np.ndarray] = {}
    instance_rows: list[dict[str, object]] = []
    phase_rows: list[dict[str, object]] = []
    long_rows: list[dict[str, object]] = []
    for generator, seed in (
        ("qr_haar", int(parameters["seed_haar"])),
        ("independent_brickwork", int(parameters["seed_circuit"])),
    ):
        phase_matrix, summaries, phases = generate_ensemble(
            generator,
            qubits,
            instances,
            np.random.default_rng(seed),
            int(parameters["circuit_depth"]),
        )
        discord_values, discord_rows = ensemble_discord_rows(
            generator,
            phase_matrix,
            alpha_values,
            int(parameters["phi_grid_points"]),
        )
        ensembles[generator] = discord_values
        instance_rows.extend(summaries)
        phase_rows.extend(phases)
        long_rows.extend(discord_rows)

    figure_rows = curve_rows(ensembles, alpha_values)
    separation = separability_rows(parameters)
    partitions = grouped_partition_rows(parameters)
    convergence = circuit_convergence_rows(parameters)
    root_sweep = root_phi_rows(parameters)
    sampling = sampling_complexity_rows(parameters)

    eq1 = separable_example_state()
    eq1_discord, (theta, phi) = two_qubit_discord_second(eq1)
    validation_rng = np.random.default_rng(int(parameters["seed_validation"]))
    validation_u = haar_unitary(
        2 ** int(parameters["dense_validation_qubits"]), validation_rng
    )
    alpha_validation = float(parameters["dense_validation_alpha"])
    validation_rho = dqc1_state(validation_u, alpha_validation)
    dimension = validation_u.shape[0]
    expected_spectrum = np.sort(
        np.repeat(
            [
                (1.0 - alpha_validation) / (2 * dimension),
                (1.0 + alpha_validation) / (2 * dimension),
            ],
            dimension,
        )
    )
    actual_spectrum = np.sort(np.linalg.eigvalsh(validation_rho))
    trace_readout = np.trace(validation_rho[:dimension, dimension:])
    expected_readout = (
        alpha_validation * np.trace(validation_u.conj().T) / (2 * dimension)
    )

    largest_root_rows = [
        row
        for row in root_sweep
        if row["dimension"] == max(parameters["root_dimensions"])
    ]
    foundational = foundational_information_audit()
    formula_rows = [
        {
            "check": "eq1_trace",
            "value": float(np.trace(eq1).real),
            "error": float(abs(np.trace(eq1) - 1.0)),
        },
        {
            "check": "eq1_negativity",
            "value": negativity_control(eq1),
            "error": negativity_control(eq1),
        },
        {
            "check": "eq1_discord",
            "value": eq1_discord,
            "error": float(abs(eq1_discord - 0.75 * np.log2(4.0 / 3.0))),
        },
        {"check": "eq1_optimal_theta", "value": theta, "error": 0.0},
        {"check": "eq1_optimal_phi", "value": phi, "error": 0.0},
        {
            "check": "dqc1_trace",
            "value": float(np.trace(validation_rho).real),
            "error": float(abs(np.trace(validation_rho) - 1.0)),
        },
        {
            "check": "dqc1_spectrum",
            "value": float(actual_spectrum.max()),
            "error": float(np.max(abs(actual_spectrum - expected_spectrum))),
        },
        {
            "check": "dqc1_trace_readout",
            "value": float(abs(trace_readout)),
            "error": float(abs(trace_readout - expected_readout)),
        },
        {
            "check": "analytic_alpha_one",
            "value": float(analytic_typical_discord(1.0)),
            "error": float(abs(analytic_typical_discord(1.0) - (2.0 - np.log2(np.e)))),
        },
        {
            "check": "root_continuum_largest_dimension",
            "value": float(
                max(
                    abs(float(row["minimum_discord_minus_continuum"]))
                    for row in largest_root_rows
                )
            ),
            "error": float(
                max(
                    abs(float(row["minimum_discord_minus_continuum"]))
                    for row in largest_root_rows
                )
            ),
        },
    ]
    formula_rows.extend(
        {
            "check": f"foundation_{name}",
            "value": value,
            "error": (max(0.0, -value) if name.endswith("_margin") else abs(value)),
        }
        for name, value in foundational.items()
    )

    symmetric_extension = {
        "schema_version": 1,
        "paper_id": "0709.0548",
        "claim_boundary": (
            "The cited first-level Doherty test is not rerun: the paper gives "
            "no solver, tolerance, seed, or certificate and this environment "
            "has no PSD-cone solver. The SDP itself is specified exactly."
        ),
        "contracts": [
            first_symmetric_extension_contract(
                2**group_size, 2 ** (int(qubits) + 1 - group_size)
            )
            for qubits in parameters["partition_qubits"]
            for group_size in range(1, int(qubits) + 1)
        ],
    }

    tables = {
        "fig1_discord.csv": figure_rows,
        "ensemble_instances.csv": instance_rows,
        "ensemble_eigenphases.csv": phase_rows,
        "ensemble_discord_long.csv": long_rows,
        "circuit_depth_convergence.csv": convergence,
        "separability_certificates.csv": separation,
        "grouped_partition_witnesses.csv": partitions,
        "root_phi_convergence.csv": root_sweep,
        "formula_checks.csv": formula_rows,
        "sampling_complexity.csv": sampling,
    }
    for name, rows in tables.items():
        write_csv(data_dir / name, rows)
    (data_dir / "symmetric_extension_contracts.json").write_text(
        json.dumps(symmetric_extension, indent=2) + "\n", encoding="utf-8"
    )

    expected_long_rows = 2 * instances * len(alpha_values)
    expected_phase_rows = 2 * instances * 2**qubits
    largest_root_range = max(float(row["discord_range"]) for row in largest_root_rows)
    smallest_root_range = max(
        float(row["discord_range"])
        for row in root_sweep
        if row["dimension"] == min(parameters["root_dimensions"])
    )
    finite_n_32_range = max(
        float(row["discord_range"]) for row in root_sweep if row["dimension"] == 32
    )
    maximum_reconstruction_residual = max(
        float(row["reconstruction_frobenius_residual"]) for row in separation
    )
    minimum_factor = min(
        float(row["minimum_product_factor_eigenvalue"]) for row in separation
    )
    maximum_unitarity_residual = max(
        float(row["unitarity_residual"]) for row in instance_rows
    )
    minimum_random_gap_std = min(float(row["gap_std"]) for row in instance_rows)
    assertions = {
        "eq1_separable_discordant": (
            negativity_control(eq1) < tolerances["density_matrix"]
            and abs(eq1_discord - 0.75 * np.log2(4.0 / 3.0)) < tolerances["formula"]
        ),
        "dqc1_state_spectrum": float(np.max(abs(actual_spectrum - expected_spectrum)))
        < tolerances["density_matrix"],
        "dqc1_trace_readout": abs(trace_readout - expected_readout)
        < tolerances["density_matrix"],
        "explicit_all_stage_separability": (
            maximum_reconstruction_residual < tolerances["separable_reconstruction"]
            and minimum_factor > -tolerances["density_matrix"]
        ),
        "all_instance_values_frozen": (
            len(long_rows) == expected_long_rows
            and len(phase_rows) == expected_phase_rows
        ),
        "both_generators_unitary": maximum_unitarity_residual < tolerances["unitarity"],
        "finite_root_grid_is_not_continuously_phi_invariant": finite_n_32_range
        > tolerances["finite_grid_effect_floor"],
        "root_phi_dependence_converges": largest_root_range < smallest_root_range,
        "random_eigenphases_are_not_exact_roots": minimum_random_gap_std
        > tolerances["exact_spacing_floor"],
        "grouped_partition_campaign_complete": len(partitions)
        == sum(
            int(parameters["partition_instances"])
            * len(parameters["partition_alphas"])
            * (2 ** int(qubit_count) - 1)
            for qubit_count in parameters["partition_qubits"]
        ),
        "circuit_depth_campaign_complete": len(convergence)
        == len(parameters["circuit_convergence_depths"])
        * len(parameters["convergence_alphas"]),
        "endpoint_value": abs(analytic_typical_discord(1.0) - (2.0 - np.log2(np.e)))
        < tolerances["formula"],
        "foundational_entropy_and_measurement_identities": max(
            foundational["classical_mutual_information_identity_error"],
            foundational["shannon_von_neumann_entropy_error"],
            foundational["measurement_probability_sum_error"],
            foundational["conditional_state_trace_error"],
        )
        < tolerances["formula"],
        "measurement_removes_measured_side_discord": foundational[
            "post_measurement_discord"
        ]
        < 5.0e-8,
        "discord_nonnegative_and_bounded": (
            foundational["minimum_test_discord"] > -5.0e-8
            and foundational["maximum_discord_upper_bound_excess"] < 5.0e-8
            and foundational["conditional_entropy_nonnegative_margin"] > -5.0e-12
            and foundational["conditional_entropy_upper_bound_margin"] > -5.0e-12
        ),
        "pure_state_discord_reduces_to_entanglement": max(
            foundational["pure_joint_entropy_max"],
            foundational["pure_marginal_entropy_error"],
            foundational["pure_discord_entanglement_error"],
        )
        < 5.0e-8,
        "sampling_overhead_is_inverse_square": all(
            abs(float(row["overhead_vs_alpha_one"]) - 1.0 / float(row["alpha"]) ** 2)
            < tolerances["formula"]
            for row in sampling
        ),
        "fixed_accuracy_trials_are_register_size_independent": all(
            len(
                {
                    int(row["shots"])
                    for row in sampling
                    if float(row["alpha"]) == float(alpha)
                }
            )
            == 1
            for alpha in parameters["sampling_alphas"]
        ),
    }
    science = {
        "schema_version": 2,
        "status": "passed" if all(assertions.values()) else "failed",
        "paper_id": "0709.0548",
        "assertions": [
            {
                "assertion_id": key,
                "status": "passed" if value else "failed",
            }
            for key, value in assertions.items()
        ],
        "metrics": {
            "eq1_discord": eq1_discord,
            "maximum_separable_reconstruction_residual": maximum_reconstruction_residual,
            "minimum_product_factor_eigenvalue": minimum_factor,
            "maximum_grouped_partition_negativity_alpha_le_half": max(
                float(row["negativity"])
                for row in partitions
                if float(row["alpha"]) <= 0.5
            ),
            "maximum_grouped_realignment_norm_alpha_le_half": max(
                float(row["realignment_trace_norm"])
                for row in partitions
                if float(row["alpha"]) <= 0.5
            ),
            "finite_n32_root_phi_discord_range": finite_n_32_range,
            "largest_root_phi_discord_range": largest_root_range,
            "minimum_random_eigenphase_gap_std": minimum_random_gap_std,
            "long_table_rows": len(long_rows),
            "phase_table_rows": len(phase_rows),
            "paper_generator_status": "publication_underspecified",
            "doherty_level_one_status": "code_ready_solver_unavailable",
            "foundational_information_audit": foundational,
            "sampling_complexity_rows": len(sampling),
            "sampling_maximum_overhead": max(
                float(row["overhead_vs_alpha_one"]) for row in sampling
            ),
        },
        "scientific_boundaries": [
            "The independent brickwork circuit is a convergence probe, not the unpublished author ensemble.",
            "Zero PPT negativity or realignment norm <=1 is not interpreted as a separability proof.",
            "The first symmetric-extension SDP is specified but not solved without a PSD-cone solver or author certificate.",
            "Finite root grids are not continuously phi invariant; only their continuum limit is.",
            "The fixed-accuracy sampling bound follows from bounded control-readout variance and does not assert a classical lower bound.",
        ],
    }
    science_path = checks_dir / "science_checks.json"
    science_path.write_text(json.dumps(science, indent=2) + "\n", encoding="utf-8")

    manifest_paths = [data_dir / name for name in tables] + [
        data_dir / "symmetric_extension_contracts.json",
        science_path,
    ]
    manifest = {
        "schema_version": 1,
        "files": [
            {
                "path": str(path.relative_to(output)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in manifest_paths
        ],
    }
    (checks_dir / "generated_data_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "schema_version": 2,
        "status": science["status"],
        "paper_id": "0709.0548",
        "parameter_match": "mixed",
        "parameters": parameters,
        "config_sha256": sha256(config_path),
        "outputs_sha256": {
            str(path.relative_to(output)): sha256(path) for path in manifest_paths
        },
    }
    (checks_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if science["status"] != "passed":
        failed = [key for key, value in assertions.items() if not value]
        raise SystemExit(f"scientific assertions failed: {failed}")


if __name__ == "__main__":
    main()
