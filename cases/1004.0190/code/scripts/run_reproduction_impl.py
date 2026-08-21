#!/usr/bin/env python3
"""Generate all numerical evidence for Dakić-Vedral-Brukner geometric discord."""

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

from geometric_discord.model import (  # noqa: E402
    X,
    Y,
    apply_local_channel,
    bell_diagonal_state,
    dqc1_left_operators,
    dqc1_separable_reconstruction,
    dqc1_state,
    geometric_discord,
    geometric_discord_direct,
    hermitian_operator_basis,
    local_projective_basis,
    local_basis_optimization_dimension,
    multipartite_geometric_discord,
    multipartite_discord_criterion,
    operator_schmidt_commutator_norm,
    random_density_matrix,
    random_unitary,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=json_default) + "\n",
        encoding="utf-8",
    )


def json_default(value: object) -> object:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def random_qubit_density(rng: np.random.Generator) -> np.ndarray:
    return random_density_matrix(rng, 2)


def random_cq_state(rng: np.random.Generator) -> np.ndarray:
    basis = random_unitary(rng, 2)
    probabilities = rng.dirichlet(np.ones(2))
    rho = np.zeros((4, 4), dtype=complex)
    for index in range(2):
        vector = basis[:, index]
        rho += probabilities[index] * np.kron(
            np.outer(vector, vector.conj()), random_qubit_density(rng)
        )
    return rho


def involution(rng: np.random.Generator, dimension: int) -> np.ndarray:
    basis = random_unitary(rng, dimension)
    signs = np.ones(dimension)
    signs[dimension // 2 :] = -1.0
    return basis @ np.diag(signs) @ basis.conj().T


def cat_density(dimension: int, weight: float = 0.4) -> np.ndarray:
    rho = np.zeros((dimension, dimension), dtype=complex)
    rho[0, 0] = weight
    rho[-1, -1] = 1.0 - weight
    return rho


def maximally_entangled_density(dimension: int) -> np.ndarray:
    state = np.zeros(dimension**2, dtype=complex)
    state[:: dimension + 1] = 1.0 / np.sqrt(dimension)
    return np.outer(state, state.conj())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()
    started = time.perf_counter()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    p, limits = config["parameters"], config["acceptance"]
    schmidt_tolerance = float(p["operator_schmidt_singular_tolerance"])
    commutator_tolerance = float(p["zero_discord_commutator_tolerance"])
    rng = np.random.default_rng(int(p["random_seed"]))
    root = Path(args.output_root)
    data = root / "data"
    checks = root / "checks"
    data.mkdir(parents=True, exist_ok=True)

    random_rows = []
    formula_error = 0.0
    for index in range(int(p["random_two_qubit_states"])):
        rho = random_density_matrix(rng)
        closed = geometric_discord(rho)
        direct, _ = geometric_discord_direct(rho)
        error = abs(closed - direct)
        formula_error = max(formula_error, error)
        commutator, rank = operator_schmidt_commutator_norm(
            rho, schmidt_tolerance, commutator_tolerance
        )
        random_rows.append(
            {
                "sample": index,
                "closed_form_discord": closed,
                "direct_dephasing_distance": direct,
                "absolute_error": error,
                "operator_schmidt_rank": rank,
                "max_left_commutator_norm": commutator,
            }
        )

    cq_commutator = 0.0
    cq_discord = 0.0
    cq_rank = 0
    cq_boolean = True
    for _ in range(int(p["classical_quantum_states"])):
        rho = random_cq_state(rng)
        diagnostics = multipartite_discord_criterion(
            rho, (2, 2), schmidt_tolerance, commutator_tolerance
        )[0]
        commutator = float(diagnostics["max_commutator_norm"])
        rank = int(diagnostics["operator_schmidt_rank"])
        cq_boolean = cq_boolean and bool(diagnostics["zero_discord"])
        cq_commutator = max(cq_commutator, commutator)
        cq_discord = max(cq_discord, geometric_discord(rho))
        cq_rank = max(cq_rank, rank)

    regression_delta = float(p["schmidt_regression_delta"])
    identity = np.eye(2)
    z = np.diag([1.0, -1.0])
    small_component_state = (
        np.kron(identity, identity)
        + regression_delta * np.kron(X, X)
        + regression_delta * np.kron(z, z)
    ) / 4.0
    small_component_norm, small_component_rank = operator_schmidt_commutator_norm(
        small_component_state, schmidt_tolerance, commutator_tolerance
    )

    near_unitary_dimension = int(p["dqc1_unitary_dimension"])
    near_unitary_phases = float(p["near_unitary_global_phase"]) + (
        regression_delta * np.linspace(-2.0, 2.0, near_unitary_dimension)
    )
    near_unitary = np.diag(np.exp(1j * near_unitary_phases))
    near_unitary_norm, near_unitary_rank = operator_schmidt_commutator_norm(
        dqc1_state(float(p["dqc1_alpha"]), near_unitary),
        schmidt_tolerance,
        commutator_tolerance,
    )
    schmidt_regression_rows = [
        {
            "family": "bell_diagonal_small_components",
            "perturbation": regression_delta,
            "expected_rank": 3,
            "observed_rank": small_component_rank,
            "max_left_commutator_norm": small_component_norm,
            "zero_discord": small_component_norm <= commutator_tolerance,
        },
        {
            "family": "near_global_phase_dqc1",
            "perturbation": regression_delta,
            "expected_rank_min": 2,
            "observed_rank": near_unitary_rank,
            "max_left_commutator_norm": near_unitary_norm,
            "zero_discord": near_unitary_norm <= commutator_tolerance,
        },
    ]

    tetrahedron = [(-1, -1, -1), (-1, 1, 1), (1, -1, 1), (1, 1, -1)]
    octahedron = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    facet_centers = [
        (first / 3.0, second / 3.0, third / 3.0)
        for first in (-1.0, 1.0)
        for second in (-1.0, 1.0)
        for third in (-1.0, 1.0)
    ]
    true_separable_maxima = []
    for zero_axis in range(3):
        active = [index for index in range(3) if index != zero_axis]
        for first_sign in (-1.0, 1.0):
            for second_sign in (-1.0, 1.0):
                point = [0.0, 0.0, 0.0]
                point[active[0]] = first_sign / 2.0
                point[active[1]] = second_sign / 2.0
                true_separable_maxima.append(tuple(point))
    geometry_rows = []
    for kind, points in (
        ("bell_vertex", tetrahedron),
        ("separable_vertex", octahedron),
        ("separable_facet_center", facet_centers),
        ("separable_true_maximum", true_separable_maxima),
    ):
        for point in points:
            rho = bell_diagonal_state(point)
            geometry_rows.append(
                {
                    "kind": kind,
                    "t1": point[0],
                    "t2": point[1],
                    "t3": point[2],
                    "geometric_discord": geometric_discord(rho),
                    "minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(rho)).real),
                }
            )
    for axis in range(3):
        for value in np.linspace(-1.0, 1.0, int(p["geometry_edge_points"])):
            point = [0.0, 0.0, 0.0]
            point[axis] = float(value)
            geometry_rows.append(
                {
                    "kind": f"zero_discord_axis_{axis + 1}",
                    "t1": point[0],
                    "t2": point[1],
                    "t3": point[2],
                    "geometric_discord": geometric_discord(bell_diagonal_state(point)),
                    "minimum_eigenvalue": float(
                        np.min(np.linalg.eigvalsh(bell_diagonal_state(point))).real
                    ),
                }
            )

    ket0 = np.array([1.0, 0.0])
    ket1 = np.array([0.0, 1.0])
    ketp = (ket0 + ket1) / np.sqrt(2.0)
    ketm = (ket0 - ket1) / np.sqrt(2.0)

    def project(vector: np.ndarray) -> np.ndarray:
        return np.outer(vector, vector.conj())

    example = (
        sum(
            np.kron(project(left), project(right))
            for left, right in ((ket0, ketp), (ket1, ketm), (ketp, ket1), (ketm, ket0))
        )
        / 4.0
    )
    example_discord = geometric_discord(example)

    initial_local = 0.5 * np.kron(project(ket0), project(ket0)) + 0.5 * np.kron(
        project(ket1), project(ket1)
    )
    prepared_local = apply_local_channel(
        initial_local,
        (np.outer(ket0, ket0), np.outer(ketp, ket1)),
        (2, 2),
        0,
    )
    reset_local = apply_local_channel(
        prepared_local,
        (np.outer(ket0, ket0), np.outer(ket0, ket1)),
        (2, 2),
        0,
    )
    local_operation_rows = [
        {
            "stage": "initial_classical",
            "geometric_discord": geometric_discord(initial_local),
        },
        {
            "stage": "nonorthogonal_prepare",
            "geometric_discord": geometric_discord(prepared_local),
        },
        {"stage": "reset", "geometric_discord": geometric_discord(reset_local)},
    ]

    dqc1_rows = []
    random_nonzero = 0
    dimension = int(p["dqc1_unitary_dimension"])
    alpha = float(p["dqc1_alpha"])
    trace_error = 0.0
    dqc1_separable_error = 0.0
    involution_commutator = 0.0
    for index in range(int(p["dqc1_random_unitaries"])):
        unitary = random_unitary(rng, dimension)
        rho = dqc1_state(alpha, unitary)
        dqc1_separable_error = max(
            dqc1_separable_error,
            float(np.linalg.norm(rho - dqc1_separable_reconstruction(alpha, unitary))),
        )
        commutator, rank = operator_schmidt_commutator_norm(
            rho, schmidt_tolerance, commutator_tolerance
        )
        random_nonzero += int(commutator > 1e-8)
        measured_x = float(np.trace(rho @ np.kron(X, np.eye(dimension))).real)
        measured_y = float(np.trace(rho @ np.kron(Y, np.eye(dimension))).real)
        trace_value = np.trace(unitary) / dimension
        trace_error = max(
            trace_error,
            abs(measured_x - alpha * trace_value.real),
            abs(measured_y - alpha * trace_value.imag),
        )
        dqc1_rows.append(
            {
                "sample": index,
                "kind": "haar",
                "operator_schmidt_rank": rank,
                "left_commutator_norm": commutator,
                "measured_x": measured_x,
                "measured_y": measured_y,
                "expected_x": alpha * trace_value.real,
                "expected_y": alpha * trace_value.imag,
            }
        )
        observable = involution(rng, dimension)
        phase = rng.uniform(-np.pi, np.pi)
        classical_unitary = np.exp(1j * phase) * observable
        classical_rho = dqc1_state(alpha, classical_unitary)
        classical_commutator, classical_rank = operator_schmidt_commutator_norm(
            classical_rho, schmidt_tolerance, commutator_tolerance
        )
        involution_commutator = max(involution_commutator, classical_commutator)
        hermitian, antihermitian = dqc1_left_operators(classical_unitary)
        gram = np.array(
            [
                [
                    np.vdot(hermitian, hermitian).real,
                    np.vdot(hermitian, antihermitian).real,
                ],
                [
                    np.vdot(antihermitian, hermitian).real,
                    np.vdot(antihermitian, antihermitian).real,
                ],
            ]
        )
        dqc1_rows.append(
            {
                "sample": index,
                "kind": "phase_times_involution",
                "operator_schmidt_rank": classical_rank,
                "left_commutator_norm": classical_commutator,
                "measured_x": "",
                "measured_y": "",
                "expected_x": "",
                "expected_y": "",
                "operator_pair_gram_determinant": float(np.linalg.det(gram)),
            }
        )

    multipartite_rows = []
    multipartite_classical_commutator = 0.0
    multipartite_classical_boolean = True
    multipartite_ghz_commutator = np.inf
    multipartite_ghz_rank = np.inf
    qubit_search_dimensions = []
    for parties in range(2, int(p["multipartite_max_qubits"]) + 1):
        dimensions = (2,) * parties
        total_dimension = 2**parties
        fully_classical = cat_density(total_dimension)
        ghz = np.zeros(total_dimension, dtype=complex)
        ghz[0] = ghz[-1] = 1.0 / np.sqrt(2.0)
        ghz_density = np.outer(ghz, ghz.conj())
        search_dimension = local_basis_optimization_dimension(dimensions)
        qubit_search_dimensions.append(search_dimension)
        for state_kind, rho in (
            ("fully_classical_cat_mixture", fully_classical),
            ("ghz", ghz_density),
        ):
            criterion_started = time.perf_counter()
            diagnostics = multipartite_discord_criterion(
                rho, dimensions, schmidt_tolerance, commutator_tolerance
            )
            runtime = time.perf_counter() - criterion_started
            for row in diagnostics:
                multipartite_rows.append(
                    {
                        "family": "party_scaling",
                        "state_kind": state_kind,
                        "parties": parties,
                        "local_dimension": 2,
                        "hilbert_dimension": total_dimension,
                        "measured_subsystem": row["subsystem"],
                        "operator_schmidt_rank": row["operator_schmidt_rank"],
                        "commutator_pairs": row["commutator_pairs"],
                        "max_commutator_norm": row["max_commutator_norm"],
                        "zero_discord": row["zero_discord"],
                        "rank_witness_nonzero": row["rank_witness_nonzero"],
                        "all_local_basis_optimization_dimension": search_dimension,
                        "criterion_runtime_seconds": runtime,
                    }
                )
                if state_kind == "fully_classical_cat_mixture":
                    multipartite_classical_commutator = max(
                        multipartite_classical_commutator,
                        float(row["max_commutator_norm"]),
                    )
                    multipartite_classical_boolean = (
                        multipartite_classical_boolean and bool(row["zero_discord"])
                    )
                else:
                    multipartite_ghz_commutator = min(
                        multipartite_ghz_commutator,
                        float(row["max_commutator_norm"]),
                    )
                    multipartite_ghz_rank = min(
                        multipartite_ghz_rank,
                        int(row["operator_schmidt_rank"]),
                    )

    operator_basis_error = 0.0
    qudit_nonzero_commutator = np.inf
    qudit_ranks = []
    qudit_search_dimensions = []
    for local_dimension in range(2, int(p["multipartite_max_local_dimension"]) + 1):
        basis = hermitian_operator_basis(local_dimension)
        gram = np.array([[np.vdot(left, right) for right in basis] for left in basis])
        operator_basis_error = max(
            operator_basis_error,
            float(np.linalg.norm(gram - np.eye(local_dimension**2))),
        )
        dimensions = (local_dimension, local_dimension)
        search_dimension = local_basis_optimization_dimension(dimensions)
        qudit_search_dimensions.append(search_dimension)
        criterion_started = time.perf_counter()
        diagnostics = multipartite_discord_criterion(
            maximally_entangled_density(local_dimension),
            dimensions,
            schmidt_tolerance,
            commutator_tolerance,
        )
        runtime = time.perf_counter() - criterion_started
        for row in diagnostics:
            qudit_nonzero_commutator = min(
                qudit_nonzero_commutator, float(row["max_commutator_norm"])
            )
            qudit_ranks.append(int(row["operator_schmidt_rank"]))
            multipartite_rows.append(
                {
                    "family": "local_dimension_scaling",
                    "state_kind": "maximally_entangled",
                    "parties": 2,
                    "local_dimension": local_dimension,
                    "hilbert_dimension": local_dimension**2,
                    "measured_subsystem": row["subsystem"],
                    "operator_schmidt_rank": row["operator_schmidt_rank"],
                    "commutator_pairs": row["commutator_pairs"],
                    "max_commutator_norm": row["max_commutator_norm"],
                    "zero_discord": row["zero_discord"],
                    "rank_witness_nonzero": row["rank_witness_nonzero"],
                    "all_local_basis_optimization_dimension": search_dimension,
                    "criterion_runtime_seconds": runtime,
                }
            )

    optimizer_rows = []
    optimizer_classical_error = 0.0
    optimizer_ghz_error = 0.0
    optimizer_qudit_error = 0.0
    optimizer_all_converged = True
    optimizer_multistarts = int(p["multipartite_optimizer_multistarts"])
    optimizer_maxiter = int(p["multipartite_optimizer_maxiter"])
    for parties in range(2, int(p["multipartite_optimizer_max_qubits"]) + 1):
        dimensions = (2,) * parties
        total_dimension = 2**parties
        planted_bases = tuple(
            local_projective_basis(
                2, (0.18 + 0.07 * subsystem, -0.31 + 0.09 * subsystem)
            )
            for subsystem in range(parties)
        )
        product_basis = np.array([[1.0 + 0.0j]])
        for basis in planted_bases:
            product_basis = np.kron(product_basis, basis)
        rotated_classical = (
            product_basis @ cat_density(total_dimension) @ product_basis.conj().T
        )
        classical_value, _, classical_diagnostics = multipartite_geometric_discord(
            rotated_classical,
            dimensions,
            multistarts=optimizer_multistarts,
            random_seed=int(p["random_seed"]) + parties,
            maxiter=optimizer_maxiter,
        )
        optimizer_classical_error = max(optimizer_classical_error, classical_value)
        optimizer_all_converged &= bool(classical_diagnostics["success"])
        optimizer_rows.append(
            {
                "family": "rotated_fully_classical",
                "parties": parties,
                "local_dimension": 2,
                "hilbert_dimension": total_dimension,
                "optimized_discord": classical_value,
                "analytic_value": 0.0,
                **classical_diagnostics,
            }
        )

        ghz = np.zeros(total_dimension, dtype=complex)
        ghz[0] = ghz[-1] = 1.0 / np.sqrt(2.0)
        ghz_value, _, ghz_diagnostics = multipartite_geometric_discord(
            np.outer(ghz, ghz.conj()),
            dimensions,
            multistarts=optimizer_multistarts,
            random_seed=int(p["random_seed"]) + 100 + parties,
            maxiter=optimizer_maxiter,
        )
        optimizer_ghz_error = max(optimizer_ghz_error, abs(ghz_value - 0.5))
        optimizer_all_converged &= bool(ghz_diagnostics["success"])
        optimizer_rows.append(
            {
                "family": "ghz",
                "parties": parties,
                "local_dimension": 2,
                "hilbert_dimension": total_dimension,
                "optimized_discord": ghz_value,
                "analytic_value": 0.5,
                **ghz_diagnostics,
            }
        )

    for local_dimension in range(
        2, int(p["multipartite_optimizer_max_local_dimension"]) + 1
    ):
        expected = 1.0 - 1.0 / local_dimension
        optimized, _, diagnostics = multipartite_geometric_discord(
            maximally_entangled_density(local_dimension),
            (local_dimension, local_dimension),
            multistarts=optimizer_multistarts,
            random_seed=int(p["random_seed"]) + 200 + local_dimension,
            maxiter=optimizer_maxiter,
        )
        optimizer_qudit_error = max(optimizer_qudit_error, abs(optimized - expected))
        optimizer_all_converged &= bool(diagnostics["success"])
        optimizer_rows.append(
            {
                "family": "maximally_entangled_qudit",
                "parties": 2,
                "local_dimension": local_dimension,
                "hilbert_dimension": local_dimension**2,
                "optimized_discord": optimized,
                "analytic_value": expected,
                **diagnostics,
            }
        )
    bell_error = max(
        abs(geometric_discord(bell_diagonal_state(point)) - 0.5)
        for point in tetrahedron
    )
    facet_formula_error = max(
        abs(geometric_discord(bell_diagonal_state(point)) - 1.0 / 18.0)
        for point in facet_centers
    )
    separable_max_error = max(
        abs(geometric_discord(bell_diagonal_state(point)) - 1.0 / 16.0)
        for point in true_separable_maxima
    )
    printed_separable_gap = min(
        abs(geometric_discord(bell_diagonal_state(point)) - 1.0 / 6.0)
        for point in facet_centers
    )
    zero_axis_error = max(
        row["geometric_discord"]
        for row in geometry_rows
        if row["kind"].startswith("zero_discord_axis")
    )
    assertions = {
        "closed_form_matches_direct_minimization": formula_error
        <= limits["geometric_formula_error_max"],
        "cq_schmidt_operators_commute": cq_commutator
        <= limits["classical_commutator_norm_max"],
        "cq_geometric_discord_zero": cq_discord
        <= limits["classical_geometric_discord_max"],
        "cq_operator_schmidt_rank_bound": cq_rank <= 2,
        "cq_zero_discord_boolean": cq_boolean,
        "small_schmidt_component_retained": small_component_rank == 3
        and small_component_norm >= limits["multipartite_nonzero_commutator_min"],
        "near_unitary_dqc1_not_false_zero": near_unitary_rank >= 2
        and near_unitary_norm >= limits["multipartite_nonzero_commutator_min"],
        "bell_vertices_have_half": bell_error <= limits["bell_max_error_max"],
        "separable_facet_centers_follow_closed_formula": facet_formula_error
        <= limits["separable_max_error_max"],
        "all_eight_separable_facet_centers_enumerated": len(facet_centers) == 8,
        "separable_global_maximum_one_sixteenth": separable_max_error
        <= limits["separable_max_error_max"],
        "printed_one_sixth_is_inconsistent": printed_separable_gap > 0.1,
        "zero_discord_axes": zero_axis_error
        <= limits["classical_geometric_discord_max"],
        "printed_nonorthogonal_separable_example_nonzero": example_discord > 1e-6,
        "dqc1_trace_readout": trace_error <= limits["dqc1_trace_readout_error_max"],
        "dqc1_involution_condition": involution_commutator
        <= limits["dqc1_involution_commutator_max"],
        "dqc1_control_register_separable_reconstruction": dqc1_separable_error
        <= limits["dqc1_separable_reconstruction_error_max"],
        "generic_dqc1_nonzero_discord_witness": random_nonzero
        == int(p["dqc1_random_unitaries"]),
        "multipartite_classical_states_commute": multipartite_classical_commutator
        <= limits["multipartite_classical_commutator_max"],
        "multipartite_classical_zero_discord_boolean": multipartite_classical_boolean,
        "multipartite_ghz_detected": multipartite_ghz_commutator
        >= limits["multipartite_nonzero_commutator_min"],
        "multipartite_rank_witness_detects_ghz": multipartite_ghz_rank > 2,
        "general_local_operator_basis_orthonormal": operator_basis_error
        <= limits["operator_basis_orthonormality_error_max"],
        "maximally_entangled_qudits_detected": qudit_nonzero_commutator
        >= limits["multipartite_nonzero_commutator_min"]
        and all(
            rank == dimension**2
            for dimension, rank in zip(
                range(2, int(p["multipartite_max_local_dimension"]) + 1),
                qudit_ranks[::2],
                strict=True,
            )
        ),
        "basis_search_dimension_scales": qubit_search_dimensions
        == [2 * parties for parties in range(2, int(p["multipartite_max_qubits"]) + 1)]
        and qudit_search_dimensions
        == [
            2 * (dimension**2 - dimension)
            for dimension in range(2, int(p["multipartite_max_local_dimension"]) + 1)
        ],
        "multipartite_optimizer_converged": optimizer_all_converged,
        "multipartite_optimizer_finds_rotated_classical_zero": optimizer_classical_error
        <= limits["multipartite_optimizer_classical_max"],
        "multipartite_optimizer_recovers_ghz_half": optimizer_ghz_error
        <= limits["multipartite_optimizer_analytic_error_max"],
        "multipartite_optimizer_recovers_qudit_formula": optimizer_qudit_error
        <= limits["multipartite_optimizer_analytic_error_max"],
        "local_prepare_channel_creates_discord": local_operation_rows[1][
            "geometric_discord"
        ]
        >= limits["local_operation_discord_min"],
        "local_reset_channel_removes_discord": local_operation_rows[2][
            "geometric_discord"
        ]
        <= limits["classical_geometric_discord_max"],
    }
    metrics = {
        "max_geometric_formula_error": formula_error,
        "max_cq_commutator_norm": cq_commutator,
        "max_cq_geometric_discord": cq_discord,
        "max_cq_operator_schmidt_rank": cq_rank,
        "all_cq_zero_discord_boolean": cq_boolean,
        "small_component_operator_schmidt_rank": small_component_rank,
        "small_component_commutator_norm": small_component_norm,
        "near_unitary_operator_schmidt_rank": near_unitary_rank,
        "near_unitary_commutator_norm": near_unitary_norm,
        "bell_vertex_error": bell_error,
        "separable_facet_centers_count": len(facet_centers),
        "separable_facet_center_formula_error": facet_formula_error,
        "separable_true_maximum_error": separable_max_error,
        "printed_one_sixth_absolute_gap": printed_separable_gap,
        "zero_axis_error": zero_axis_error,
        "separable_nonorthogonal_example_discord": example_discord,
        "dqc1_trace_readout_error": trace_error,
        "dqc1_involution_commutator_norm": involution_commutator,
        "dqc1_separable_reconstruction_error": dqc1_separable_error,
        "generic_dqc1_nonzero_count": random_nonzero,
        "multipartite_max_classical_commutator_norm": multipartite_classical_commutator,
        "multipartite_all_classical_zero_discord_boolean": multipartite_classical_boolean,
        "multipartite_min_ghz_commutator_norm": multipartite_ghz_commutator,
        "multipartite_min_ghz_operator_schmidt_rank": multipartite_ghz_rank,
        "max_operator_basis_orthonormality_error": operator_basis_error,
        "minimum_qudit_entangled_commutator_norm": qudit_nonzero_commutator,
        "qubit_party_search_dimensions": qubit_search_dimensions,
        "qudit_search_dimensions": qudit_search_dimensions,
        "multipartite_optimizer_max_classical_discord": optimizer_classical_error,
        "multipartite_optimizer_max_ghz_error": optimizer_ghz_error,
        "multipartite_optimizer_max_qudit_error": optimizer_qudit_error,
        "local_prepare_discord": local_operation_rows[1]["geometric_discord"],
        "local_reset_discord": local_operation_rows[2]["geometric_discord"],
    }
    status = "passed" if all(assertions.values()) else "failed"

    for path, rows in (
        (data / "random_state_checks.csv", random_rows),
        (data / "discord_geometry.csv", geometry_rows),
        (data / "dqc1_checks.csv", dqc1_rows),
        (data / "multipartite_scaling.csv", multipartite_rows),
        (data / "multipartite_discord.csv", optimizer_rows),
        (data / "local_operation_checks.csv", local_operation_rows),
        (data / "schmidt_tolerance_regression.csv", schmidt_regression_rows),
    ):
        fields = sorted({key for row in rows for key in row})
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    science = {
        "schema_version": 1,
        "paper_id": "1004.0190",
        "status": status,
        "assertions": assertions,
        "metrics": metrics,
        "paper_discrepancies": [
            {
                "source_ref": "paragraph after Fig. 1 and Eq. for D_A^(2)(t)",
                "printed_claim": "separable maximum 1/6 at octahedron facet centers",
                "formula_value_at_facet_center": 1.0 / 18.0,
                "independent_global_maximum": 1.0 / 16.0,
                "independent_maximizers": "permutations of (+/-1/2,+/-1/2,0)",
            },
            {
                "source_ref": "Eq. (17)",
                "printed_claim": "i_k=+/-1 generates eight facet-center sign combinations through (-1)^(i_k)",
                "literal_index_result": "all exponents give -1, so the eight index tuples collapse to one state",
                "likely_repair": "replace i_k=+/-1 by i_k in {0,1}",
            },
            {
                "source_ref": "final local-operation example",
                "printed_claim": "rho=|00><00|+|11><11| is a density operator",
                "literal_trace": 2.0,
                "likely_repair": "multiply the two-term mixture by 1/2",
            },
        ],
        "target_results": {
            f"T{i:03d}": {"status": "passed" if status == "passed" else "failed"}
            for i in range(1, 9)
        },
    }
    write_json(checks / "science_checks.json", science)
    produced = [
        data / "random_state_checks.csv",
        data / "discord_geometry.csv",
        data / "dqc1_checks.csv",
        data / "multipartite_scaling.csv",
        data / "multipartite_discord.csv",
        data / "local_operation_checks.csv",
        data / "schmidt_tolerance_regression.csv",
        checks / "science_checks.json",
    ]
    write_json(
        checks / "generated_data_manifest.json",
        {
            "schema_version": 1,
            "paper_id": "1004.0190",
            "generated_data_provenance": "independent_numerics",
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "files": [
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
                for path in produced
            ],
        },
    )
    write_json(
        checks / "run_summary.json",
        {
            "schema_version": 1,
            "paper_id": "1004.0190",
            "status": status,
            "runtime_seconds": time.perf_counter() - started,
            "targets": [f"T{i:03d}" for i in range(1, 9)],
            "paper_parameters_executed": True,
            "artifact_stage": "final_reproduction",
        },
    )
    print(json.dumps({"status": status, **metrics}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
