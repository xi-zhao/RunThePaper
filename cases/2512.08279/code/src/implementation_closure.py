"""Small, source-independent witnesses for the paper's seven target families.

These checks close implementation readiness only.  A finite-dimensional
numeric witness is not a proof of a theorem and must not change scientific
coverage or the target score.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.linalg import expm


Array = np.ndarray
MapFunction = Callable[[Array], Array]


@dataclass(frozen=True)
class ProductBranch:
    """One signed product-map branch in the paper's CNOT decomposition."""

    branch_id: str
    coefficient: float
    left_map: MapFunction
    right_map: MapFunction

ITEMS_BY_TARGET = {
    "T001": ["C17-SWAP-DEPHASING-SEMIGROUP", "C18-SWAP-DEPHASING-HPTP", "F2-EXACT", "F2-QUASI"],
    "T002": ["F3-AD", "F3-ADZ"],
    "T003": [
        "C01-PAULI-PROGRAMMABLE", "C02-COVARIANT-PROGRAMMABLE", "C07-QMATRIX-POLYTOPE",
        "C08-UNITARY-CONJUGATED-SEMIGROUP", "C09-COVARIANCE-GENERATOR-IFF",
        "C10-COVARIANT-QDS-CHOI", "C11-COVARIANT-IRREP-UNITAL", "C12-COVARIANT-FINITE-MIXTURE",
    ],
    "T004": [
        "C03-COHERENT-NO-GO", "C04-AD-NO-GO", "C13-GENERATOR-CHANNEL-CONDITION",
        "C14-COMMUTATOR-CP-IFF", "C15-COMMUTATOR-EXP-IFF", "C16-UNITARY-FAMILY-PROGRAMMABILITY",
    ],
    "T005": ["C05-H-HPTP-DIM-K", "C06-AD-HPTP-DIM-12", "C30-COHERENT-PROTOCOL-COST-2", "C31-AD-CIRCUIT-KAPPA-5"],
    "T006": [
        "C19-INITIAL-COST-ZERO", "C20-COST-MONOTONE-T", "C21-ANALYTIC-CONTINUATION",
        "C22-COST-FAITHFULNESS", "C23-NOISY-PROGRAM-BOUND", "C24-SCALING-INVARIANCE",
        "C25-COMMUTING-SUM-SUBADDITIVITY", "C26-TENSOR-SUBADDITIVITY", "C27-TROTTER-APPROXIMATE-SUM",
    ],
    "T007": ["C28-CHOI-BLOCK-RETRIEVAL", "C29-STEADY-STATE-POSITIVE-COST"],
    "T008": ["C32-PROGRAMMABILITY-DEFINITIONS"],
    "T009": ["C33-CHOI-LINK-PRELIMINARIES"],
    "T010": ["C34-GKSL-LIOUVILLE-PRELIMINARIES"],
    "T011": ["C35-HPTP-IMPLEMENTABILITY-COST"],
}


def _paulis() -> tuple[Array, Array, Array, Array]:
    identity = np.eye(2, dtype=np.complex128)
    x = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    z = np.diag([1, -1]).astype(np.complex128)
    return identity, x, y, z


def _matrix_unit(dimension: int, row: int, column: int) -> Array:
    value = np.zeros((dimension, dimension), dtype=np.complex128)
    value[row, column] = 1.0
    return value


def _choi(map_function: Callable[[Array], Array], dimension: int = 2) -> Array:
    blocks = [[map_function(_matrix_unit(dimension, i, j)) for j in range(dimension)] for i in range(dimension)]
    return np.block(blocks)


def _partial_trace_output(choi: Array, dimension: int = 2) -> Array:
    tensor = choi.reshape(dimension, dimension, dimension, dimension)
    return np.einsum("iaja->ij", tensor)


def _choi_rectangular(
    map_function: Callable[[Array], Array],
    input_dimension: int,
    output_dimension: int,
) -> Array:
    """Return an unnormalized Choi matrix for a possibly rectangular channel."""

    blocks = [
        [map_function(_matrix_unit(input_dimension, i, j)) for j in range(input_dimension)]
        for i in range(input_dimension)
    ]
    choi = np.block(blocks)
    expected = (input_dimension * output_dimension,) * 2
    if choi.shape != expected:
        raise ValueError(f"rectangular Choi shape {choi.shape} does not match {expected}")
    return choi


def _partial_trace_rectangular_output(
    choi: Array,
    input_dimension: int,
    output_dimension: int,
) -> Array:
    tensor = choi.reshape(input_dimension, output_dimension, input_dimension, output_dimension)
    return np.einsum("iaja->ij", tensor)


def _superoperator(map_function: MapFunction, dimension: int = 2) -> Array:
    """Build the row-vectorized matrix of a linear map from matrix units."""

    columns = [
        map_function(_matrix_unit(dimension, i, j)).reshape(-1)
        for i in range(dimension)
        for j in range(dimension)
    ]
    return np.column_stack(columns)


def _map_from_superoperator(superoperator: Array, dimension: int = 2) -> MapFunction:
    return lambda operator: (superoperator @ operator.reshape(-1)).reshape(dimension, dimension)


def _link_product(first_choi: Array, second_choi: Array, dimension: int = 2) -> Array:
    """Contract compatible Choi matrices to represent second composed with first."""

    first = first_choi.reshape(dimension, dimension, dimension, dimension)
    second = second_choi.reshape(dimension, dimension, dimension, dimension)
    return np.einsum("iajb,acbd->icjd", first, second).reshape(dimension**2, dimension**2)


def _apply_on_second_subsystem(
    operator: Array,
    map_function: MapFunction,
    dimension: int = 2,
) -> Array:
    """Apply I tensor map to a bipartite operator in A tensor B order."""

    tensor = operator.reshape(dimension, dimension, dimension, dimension)
    output = np.zeros_like(operator, dtype=np.complex128)
    for row in range(dimension):
        for column in range(dimension):
            output += np.kron(
                _matrix_unit(dimension, row, column),
                map_function(tensor[row, :, column, :]),
            )
    return output


def _unitary(theta: float, generator: Array) -> Array:
    values, vectors = np.linalg.eigh(generator)
    return (vectors * np.exp(-1j * theta * values)) @ vectors.conj().T


def _amplitude_damping(probability: float) -> list[Array]:
    p = float(probability)
    return [
        np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - p)]], dtype=np.complex128),
        np.array([[0.0, np.sqrt(p)], [0.0, 0.0]], dtype=np.complex128),
    ]


def _apply_kraus(operator: Array, kraus: list[Array]) -> Array:
    return sum(k @ operator @ k.conj().T for k in kraus)


def _unitary_map(unitary: Array) -> MapFunction:
    return lambda operator: unitary @ operator @ unitary.conj().T


def _projection_map(projector: Array) -> MapFunction:
    return lambda operator: projector @ operator @ projector


def _apply_product_map(operator: Array, left_map: MapFunction, right_map: MapFunction) -> Array:
    """Apply a product superoperator to a two-qubit operator in S tensor P order."""

    output = np.zeros_like(operator, dtype=np.complex128)
    for left_row in range(2):
        for left_column in range(2):
            left_unit = _matrix_unit(2, left_row, left_column)
            left_output = left_map(left_unit)
            for right_row in range(2):
                for right_column in range(2):
                    right_unit = _matrix_unit(2, right_row, right_column)
                    coefficient = operator[2 * left_row + right_row, 2 * left_column + right_column]
                    output += coefficient * np.kron(left_output, right_map(right_unit))
    return output


def _paper_cnot_branches(coefficients: Array) -> list[ProductBranch]:
    """Construct the six product maps printed in the supplement."""

    if coefficients.shape != (6,):
        raise ValueError("the paper CNOT decomposition requires exactly six coefficients")
    identity, x, _, z = _paulis()
    hadamard = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)
    phase = np.diag([1.0, 1.0j]).astype(np.complex128)
    zero = np.diag([1.0, 0.0]).astype(np.complex128)
    one = np.diag([0.0, 1.0]).astype(np.complex128)
    plus = np.outer(np.array([1.0, 1.0]), np.array([1.0, 1.0])) / 2.0
    minus = np.outer(np.array([1.0, -1.0]), np.array([1.0, -1.0])) / 2.0
    definitions = [
        ("pi0_tensor_identity", _projection_map(zero), _unitary_map(identity)),
        ("pi1_tensor_x", _projection_map(one), _unitary_map(x)),
        ("identity_tensor_pi_plus", _unitary_map(identity), _projection_map(plus)),
        ("z_tensor_pi_minus", _unitary_map(z), _projection_map(minus)),
        (
            "s_tensor_h_sdag_h",
            _unitary_map(phase),
            _unitary_map(hadamard @ phase.conj().T @ hadamard),
        ),
        (
            "sdag_tensor_h_s_h",
            _unitary_map(phase.conj().T),
            _unitary_map(hadamard @ phase @ hadamard),
        ),
    ]
    return [
        ProductBranch(branch_id, float(coefficient), left_map, right_map)
        for coefficient, (branch_id, left_map, right_map) in zip(coefficients, definitions, strict=True)
    ]


def _apply_branch(operator: Array, branch: ProductBranch) -> Array:
    return _apply_product_map(operator, branch.left_map, branch.right_map)


def _cnot(control: int, target: int) -> Array:
    if {control, target} != {0, 1}:
        raise ValueError("control and target must be the two distinct qubit indices")
    unitary = np.zeros((4, 4), dtype=np.complex128)
    for first in range(2):
        for second in range(2):
            input_bits = [first, second]
            output_bits = input_bits.copy()
            output_bits[target] ^= input_bits[control]
            unitary[2 * output_bits[0] + output_bits[1], 2 * first + second] = 1.0
    return unitary


def _rotation_y(theta: float) -> Array:
    cosine = np.cos(theta / 2.0)
    sine = np.sin(theta / 2.0)
    return np.array([[cosine, -sine], [sine, cosine]], dtype=np.complex128)


def _partial_trace_second_qubit(operator: Array) -> Array:
    return np.einsum("iaja->ij", operator.reshape(2, 2, 2, 2))


def _paper_program_states(theta: float) -> list[Array]:
    """Return the six normalized qubit components of the dimension-12 program."""

    sine = float(np.sin(theta / 2.0))
    cosine = float(np.cos(theta / 2.0))
    # The square-root form is algebraically equivalent to the printed ratios
    # and keeps sigma_4 well defined at the removable gamma=1 endpoint.
    return [
        np.array([1.0, 0.0], dtype=np.complex128),
        np.array([sine, cosine], dtype=np.complex128),
        np.array([np.sqrt((1.0 + sine) / 2.0), np.sqrt((1.0 - sine) / 2.0)], dtype=np.complex128),
        np.array([np.sqrt((1.0 - sine) / 2.0), -np.sqrt((1.0 + sine) / 2.0)], dtype=np.complex128),
        np.array([(1.0 - 1.0j) + sine * (1.0 + 1.0j), (1.0 + 1.0j) * cosine]) / 2.0,
        np.array([(1.0 + 1.0j) + sine * (1.0 - 1.0j), (1.0 - 1.0j) * cosine]) / 2.0,
    ]


def _program_state_preparation_checks(
    theta: float,
    branches: list[ProductBranch],
    program_states: list[Array],
) -> tuple[float, int]:
    """Match printed program states to the six right-side CNOT maps.

    The two projection branches are normalized after successful projection, as
    in the supplement.  At the removable gamma=1 endpoint the ``Pi_-`` outcome
    has zero probability, so its normalized state is checked by continuity in
    the interior probability points instead of dividing by zero.
    """

    zero_state = np.diag([1.0, 0.0]).astype(np.complex128)
    rotate_forward = _rotation_y(theta / 2.0)
    rotate_backward = _rotation_y(-theta / 2.0)
    rotated_zero = rotate_forward @ zero_state @ rotate_forward.conj().T
    residuals: list[float] = []
    for branch, program_state in zip(branches, program_states, strict=True):
        prepared = branch.right_map(rotated_zero)
        prepared = rotate_backward @ prepared @ rotate_backward.conj().T
        preparation_probability = float(np.trace(prepared).real)
        if preparation_probability <= np.finfo(float).eps:
            continue
        prepared /= preparation_probability
        printed_state = np.outer(program_state, program_state.conj())
        residuals.append(float(np.linalg.norm(prepared - printed_state)))
    return (max(residuals, default=0.0), len(residuals))


def _amplitude_damping_branch_output(operator: Array, probability: float, branch: ProductBranch) -> Array:
    """Apply one affine CNOT branch inside the paper's amplitude-damping dilation."""

    identity = np.eye(2, dtype=np.complex128)
    environment_zero = np.diag([1.0, 0.0]).astype(np.complex128)
    theta = 2.0 * np.arcsin(np.sqrt(probability))
    cnot_system_to_environment = _cnot(0, 1)
    cnot_environment_to_system = _cnot(1, 0)
    rotate_forward = np.kron(identity, _rotation_y(theta / 2.0))
    rotate_backward = np.kron(identity, _rotation_y(-theta / 2.0))

    joint = np.kron(operator, environment_zero)
    joint = rotate_forward @ joint @ rotate_forward.conj().T
    joint = cnot_system_to_environment @ joint @ cnot_system_to_environment.conj().T
    joint = rotate_backward @ joint @ rotate_backward.conj().T
    joint = _apply_branch(joint, branch)
    joint = cnot_environment_to_system @ joint @ cnot_environment_to_system.conj().T
    return _partial_trace_second_qubit(joint)


def _amplitude_damping_protocol_checks(config: dict[str, Any], tolerance: float) -> dict[str, Any]:
    coefficients = np.asarray(config["amplitude_damping_protocol_coefficients"], dtype=float)
    paper_coefficients = np.array([1.0, 1.0, 1.0, 1.0, -0.5, -0.5], dtype=float)
    probabilities = np.asarray(config["amplitude_damping_protocol_probabilities"], dtype=float)
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("amplitude-damping probabilities must lie in [0, 1]")
    branches = _paper_cnot_branches(coefficients)
    cnot = _cnot(0, 1)

    def reconstructed_cnot(operator: Array) -> Array:
        return sum(branch.coefficient * _apply_branch(operator, branch) for branch in branches)

    def exact_cnot(operator: Array) -> Array:
        return cnot @ operator @ cnot.conj().T

    cnot_residuals = [
        np.linalg.norm(reconstructed_cnot(_matrix_unit(4, row, column)) - exact_cnot(_matrix_unit(4, row, column)))
        for row in range(4)
        for column in range(4)
    ]
    reconstructed_cnot_choi = _choi(reconstructed_cnot, dimension=4)
    exact_cnot_choi = _choi(exact_cnot, dimension=4)

    probability_checks = []
    maximum_amplitude_damping_residual = 0.0
    maximum_amplitude_damping_choi_residual = 0.0
    maximum_program_state_norm_residual = 0.0
    maximum_program_state_preparation_residual = 0.0
    for probability in probabilities:
        probability = float(probability)
        theta = float(2.0 * np.arcsin(np.sqrt(probability)))
        program_states = _paper_program_states(theta)
        state_norm_residual = max(abs(float(np.vdot(state, state).real) - 1.0) for state in program_states)
        state_preparation_residual, checked_state_preparations = _program_state_preparation_checks(
            theta, branches, program_states
        )
        target_kraus = _amplitude_damping(probability)

        def reconstructed_amplitude_damping(operator: Array) -> Array:
            return sum(
                branch.coefficient * _amplitude_damping_branch_output(operator, probability, branch)
                for branch in branches
            )

        def exact_amplitude_damping(operator: Array) -> Array:
            return _apply_kraus(operator, target_kraus)

        residuals = [
            np.linalg.norm(
                reconstructed_amplitude_damping(_matrix_unit(2, row, column))
                - exact_amplitude_damping(_matrix_unit(2, row, column))
            )
            for row in range(2)
            for column in range(2)
        ]
        choi_residual = float(
            np.linalg.norm(_choi(reconstructed_amplitude_damping) - _choi(exact_amplitude_damping))
        )
        probability_checks.append(
            {
                "probability": probability,
                "theta": theta,
                "max_matrix_unit_residual": float(max(residuals)),
                "choi_residual": choi_residual,
                "max_program_state_norm_residual": float(state_norm_residual),
                "max_program_state_preparation_residual": state_preparation_residual,
                "checked_program_state_preparations": checked_state_preparations,
            }
        )
        maximum_amplitude_damping_residual = max(maximum_amplitude_damping_residual, float(max(residuals)))
        maximum_amplitude_damping_choi_residual = max(maximum_amplitude_damping_choi_residual, choi_residual)
        maximum_program_state_norm_residual = max(maximum_program_state_norm_residual, float(state_norm_residual))
        maximum_program_state_preparation_residual = max(
            maximum_program_state_preparation_residual, state_preparation_residual
        )

    representative_probability = float(config["amplitude_damping_probability"])
    branch_checks = []
    for branch in branches:
        cnot_branch_choi = branch.coefficient * _choi(lambda operator, row=branch: _apply_branch(operator, row), 4)
        damping_branch_choi = branch.coefficient * _choi(
            lambda operator, row=branch: _amplitude_damping_branch_output(
                operator, representative_probability, row
            )
        )
        branch_checks.append(
            {
                "branch_id": branch.branch_id,
                "coefficient": branch.coefficient,
                "weighted_cnot_choi_norm": float(np.linalg.norm(cnot_branch_choi)),
                "weighted_amplitude_damping_choi_norm": float(np.linalg.norm(damping_branch_choi)),
            }
        )

    result = {
        "configured_coefficients": coefficients.tolist(),
        "paper_coefficients": paper_coefficients.tolist(),
        "paper_coefficient_match": bool(np.array_equal(coefficients, paper_coefficients)),
        "coefficient_sum": float(np.sum(coefficients)),
        "term_count": int(len(coefficients)),
        "sampling_overhead": float(np.sum(np.abs(coefficients))),
        "program_dimension": 12,
        "cnot_max_matrix_unit_residual": float(max(cnot_residuals)),
        "cnot_choi_residual": float(np.linalg.norm(reconstructed_cnot_choi - exact_cnot_choi)),
        "cnot_trace_preservation_residual": float(
            np.linalg.norm(_partial_trace_output(reconstructed_cnot_choi, dimension=4) - np.eye(4))
        ),
        "amplitude_damping_probabilities": probabilities.tolist(),
        "amplitude_damping_max_matrix_unit_residual": maximum_amplitude_damping_residual,
        "amplitude_damping_max_choi_residual": maximum_amplitude_damping_choi_residual,
        "max_program_state_norm_residual": maximum_program_state_norm_residual,
        "max_program_state_preparation_residual": maximum_program_state_preparation_residual,
        "probability_checks": probability_checks,
        "branch_checks": branch_checks,
    }
    result["passed"] = bool(
        result["paper_coefficient_match"]
        and result["term_count"] == 6
        and abs(result["sampling_overhead"] - 5.0) <= tolerance
        and result["program_dimension"] == 12
        and result["cnot_max_matrix_unit_residual"] <= tolerance
        and result["cnot_choi_residual"] <= tolerance
        and result["cnot_trace_preservation_residual"] <= tolerance
        and result["amplitude_damping_max_matrix_unit_residual"] <= tolerance
        and result["amplitude_damping_max_choi_residual"] <= tolerance
        and result["max_program_state_norm_residual"] <= tolerance
        and result["max_program_state_preparation_residual"] <= tolerance
        and all(row["weighted_amplitude_damping_choi_norm"] > tolerance for row in branch_checks)
    )
    return result


def _programmability_definition_checks(config: dict[str, Any], tolerance: float) -> dict[str, Any]:
    """Instantiate the fixed-processor definition with two qubit channels.

    This is a finite witness for the definitions and measure-and-prepare
    construction.  It is deliberately not presented as a proof of a general
    diamond-norm statement.
    """

    identity, x, _, _ = _paulis()
    channels = (_unitary_map(identity), _unitary_map(x))

    def processor(operator: Array) -> Array:
        tensor = operator.reshape(2, 2, 2, 2)
        return sum(channel(tensor[:, index, :, index]) for index, channel in enumerate(channels))

    processor_choi = _choi_rectangular(processor, input_dimension=4, output_dimension=2)
    probabilities = np.asarray(config["definition_program_probabilities"], dtype=float)
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("definition program probabilities must lie in [0, 1]")
    retrieval_residuals: list[float] = []
    program_minimum_eigenvalues: list[float] = []
    program_trace_residuals: list[float] = []
    for probability in probabilities:
        program = np.diag([float(probability), float(1.0 - probability)]).astype(np.complex128)
        program_minimum_eigenvalues.append(float(np.min(np.linalg.eigvalsh(program)).real))
        program_trace_residuals.append(abs(float(np.trace(program).real) - 1.0))
        for row in range(2):
            for column in range(2):
                basis = _matrix_unit(2, row, column)
                retrieved = processor(np.kron(basis, program))
                target = probability * channels[0](basis) + (1.0 - probability) * channels[1](basis)
                retrieval_residuals.append(float(np.linalg.norm(retrieved - target)))

    signed_weights = np.asarray(config["definition_quasi_weights"], dtype=float)
    if signed_weights.shape != (2,):
        raise ValueError("definition quasi weights must contain two entries")
    signed_residual = max(
        np.linalg.norm(
            sum(weight * channel(_matrix_unit(2, row, column)) for weight, channel in zip(signed_weights, channels, strict=True))
            - (
                signed_weights[0] * _matrix_unit(2, row, column)
                + signed_weights[1] * x @ _matrix_unit(2, row, column) @ x
            )
        )
        for row in range(2)
        for column in range(2)
    )
    result = {
        "program_probabilities": probabilities.tolist(),
        "program_minimum_eigenvalue": min(program_minimum_eigenvalues),
        "program_trace_residual": max(program_trace_residuals),
        "processor_choi_minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(processor_choi)).real),
        "processor_trace_preservation_residual": float(
            np.linalg.norm(_partial_trace_rectangular_output(processor_choi, 4, 2) - np.eye(4))
        ),
        "exact_measure_prepare_max_residual": max(retrieval_residuals),
        "quasi_signed_weight_sum": float(np.sum(signed_weights)),
        "quasi_sampling_overhead": float(np.sum(np.abs(signed_weights))),
        "quasi_retrieval_max_residual": float(signed_residual),
        "general_claim_proved": False,
    }
    result["passed"] = bool(
        result["program_minimum_eigenvalue"] >= -tolerance
        and result["program_trace_residual"] <= tolerance
        and result["processor_choi_minimum_eigenvalue"] >= -tolerance
        and result["processor_trace_preservation_residual"] <= tolerance
        and result["exact_measure_prepare_max_residual"] <= tolerance
        and abs(result["quasi_signed_weight_sum"] - 1.0) <= tolerance
        and result["quasi_retrieval_max_residual"] <= tolerance
    )
    return result


def _choi_link_checks(config: dict[str, Any], tolerance: float) -> dict[str, Any]:
    """Check Choi normalization and compatible link contractions on qubits."""

    identity, x, _, _ = _paulis()
    probabilities = np.asarray(config["choi_link_flip_probabilities"], dtype=float)
    if probabilities.shape != (3,) or np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("three Choi-link probabilities in [0,1] are required")

    def flip_map(probability: float) -> MapFunction:
        return lambda operator: (1.0 - probability) * operator + probability * x @ operator @ x

    maps = tuple(flip_map(float(probability)) for probability in probabilities)
    chois = tuple(_choi(map_function) for map_function in maps)
    maximally_entangled_vector = identity.reshape(-1) / np.sqrt(2.0)
    maximally_entangled_state = np.outer(maximally_entangled_vector, maximally_entangled_vector.conj())
    choi_from_state = 2.0 * _apply_on_second_subsystem(maximally_entangled_state, maps[0])
    direct_composition = _choi(lambda operator: maps[1](maps[0](operator)))
    linked_composition = _link_product(chois[0], chois[1])
    forward_link = _link_product(chois[0], chois[1])
    reverse_link = _link_product(chois[1], chois[0])
    left_association = _link_product(_link_product(chois[0], chois[1]), chois[2])
    right_association = _link_product(chois[0], _link_product(chois[1], chois[2]))
    result = {
        "maximally_entangled_state_trace_residual": abs(float(np.trace(maximally_entangled_state).real) - 1.0),
        "choi_from_state_residual": float(np.linalg.norm(choi_from_state - chois[0])),
        "link_composition_residual": float(np.linalg.norm(linked_composition - direct_composition)),
        "compatible_commutativity_residual": float(np.linalg.norm(forward_link - reverse_link)),
        "compatible_associativity_residual": float(np.linalg.norm(left_association - right_association)),
        "linked_choi_trace_preservation_residual": float(np.linalg.norm(_partial_trace_output(linked_composition) - identity)),
        "general_claim_proved": False,
    }
    result["passed"] = bool(max(value for key, value in result.items() if key.endswith("residual")) <= tolerance)
    return result


def _gksl_liouville_checks(config: dict[str, Any], tolerance: float) -> dict[str, Any]:
    """Exercise GKSL, vectorization, semigroup, spectrum and reshuffling claims."""

    identity, x, _, z = _paulis()
    rate = float(config["gksl_rate"])
    times = np.asarray(config["gksl_times"], dtype=float)
    lowering = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    hamiltonian = 0.37 * z
    jump = np.sqrt(rate) * lowering
    jump_norm = jump.conj().T @ jump

    def direct_generator(operator: Array) -> Array:
        return (
            -1j * (hamiltonian @ operator - operator @ hamiltonian)
            + jump @ operator @ jump.conj().T
            - 0.5 * (jump_norm @ operator + operator @ jump_norm)
        )

    liouville = (
        -1j * (np.kron(hamiltonian, identity) - np.kron(identity, hamiltonian.T))
        + np.kron(jump, jump.conj())
        - 0.5 * np.kron(jump_norm, identity)
        - 0.5 * np.kron(identity, jump_norm.T)
    )
    action_residual = max(
        np.linalg.norm(
            (liouville @ _matrix_unit(2, row, column).reshape(-1)).reshape(2, 2)
            - direct_generator(_matrix_unit(2, row, column))
        )
        for row in range(2)
        for column in range(2)
    )
    channels = [expm(float(time) * liouville) for time in times]
    channel_maps = [_map_from_superoperator(channel) for channel in channels]
    channel_chois = [_choi(channel_map) for channel_map in channel_maps]
    semigroup_residual = max(
        np.linalg.norm(expm((float(a) + float(b)) * liouville) - expm(float(a) * liouville) @ expm(float(b) * liouville))
        for a in times
        for b in times
    )
    stationary_state = np.diag([1.0, 0.0]).astype(np.complex128)

    coherent_liouville = -1j * (np.kron(z, identity) - np.kron(identity, z.T))
    coherent_spectrum = np.linalg.eigvals(coherent_liouville)

    def depolarizing_generator(operator: Array) -> Array:
        return rate * (np.trace(operator) * identity / 2.0 - operator)

    depolarizing_liouville = _superoperator(depolarizing_generator)
    depolarizing_spectrum = np.linalg.eigvals(depolarizing_liouville)
    depolarizing_channel = _map_from_superoperator(expm(float(times[-1]) * depolarizing_liouville))
    probe_state = np.diag([1.0, 0.0]).astype(np.complex128)
    expected_probe = np.exp(-rate * float(times[-1])) * probe_state + (
        1.0 - np.exp(-rate * float(times[-1]))
    ) * identity / 2.0
    reshuffled_choi = _choi(channel_maps[-1])
    explicit_choi = np.block(
        [
            [channel_maps[-1](_matrix_unit(2, row, column)) for column in range(2)]
            for row in range(2)
        ]
    )
    result = {
        "vectorized_gksl_action_residual": float(action_residual),
        "semigroup_identity_residual": float(np.linalg.norm(channels[0] - np.eye(4))),
        "semigroup_composition_residual": float(semigroup_residual),
        "minimum_channel_choi_eigenvalue": float(min(np.min(np.linalg.eigvalsh(choi)).real for choi in channel_chois)),
        "maximum_channel_trace_residual": float(max(np.linalg.norm(_partial_trace_output(choi) - identity) for choi in channel_chois)),
        "maximum_liouville_real_eigenvalue": float(np.max(np.real(np.linalg.eigvals(liouville)))),
        "stationary_kernel_residual": float(np.linalg.norm(direct_generator(stationary_state))),
        "coherent_spectrum_real_part_residual": float(np.max(np.abs(np.real(coherent_spectrum)))),
        "depolarizing_stationary_residual": float(np.linalg.norm(depolarizing_generator(identity / 2.0))),
        "depolarizing_nonzero_real_part_max": float(np.max(np.real(depolarizing_spectrum[np.abs(depolarizing_spectrum) > tolerance]))),
        "depolarizing_exponential_solution_residual": float(np.linalg.norm(depolarizing_channel(probe_state) - expected_probe)),
        "choi_reshuffling_residual": float(np.linalg.norm(reshuffled_choi - explicit_choi)),
        "general_claim_proved": False,
    }
    residual_keys = [key for key in result if key.endswith("residual")]
    result["passed"] = bool(
        max(float(result[key]) for key in residual_keys) <= tolerance
        and result["minimum_channel_choi_eigenvalue"] >= -tolerance
        and result["maximum_liouville_real_eigenvalue"] <= tolerance
        and result["depolarizing_nonzero_real_part_max"] < -tolerance
    )
    return result


def _hptp_cost_checks(config: dict[str, Any], tolerance: float) -> dict[str, Any]:
    """Check finite signed-channel cost identities and seek a composition counterexample."""

    identity, x, _, z = _paulis()
    signed_weights = np.asarray(config["implementability_signed_weights"], dtype=float)
    cptp_weights = np.asarray(config["implementability_cptp_weights"], dtype=float)
    if signed_weights.shape != (2,) or cptp_weights.shape != (2,):
        raise ValueError("implementability witnesses require two coefficients")

    def signed_map(weights: Array, operators: tuple[Array, Array] = (identity, x)) -> MapFunction:
        return lambda operator: sum(
            float(weight) * unitary @ operator @ unitary.conj().T
            for weight, unitary in zip(weights, operators, strict=True)
        )

    nonphysical_map = signed_map(signed_weights)
    nonphysical_choi = _choi(nonphysical_map)
    overhead = float(np.sum(np.abs(signed_weights)))
    positive_weight = float(np.sum(np.maximum(signed_weights, 0.0)))
    negative_weight = float(np.sum(np.maximum(-signed_weights, 0.0)))
    positive_channel_weights = np.maximum(signed_weights, 0.0) / positive_weight
    negative_channel_weights = np.maximum(-signed_weights, 0.0) / negative_weight
    positive_channel = signed_map(positive_channel_weights)
    negative_channel = signed_map(negative_channel_weights)
    decomposition_residual = max(
        np.linalg.norm(
            nonphysical_map(_matrix_unit(2, row, column))
            - positive_weight * positive_channel(_matrix_unit(2, row, column))
            + negative_weight * negative_channel(_matrix_unit(2, row, column))
        )
        for row in range(2)
        for column in range(2)
    )
    choi_trace_norm_over_dimension = float(np.sum(np.abs(np.linalg.eigvalsh(nonphysical_choi))) / 2.0)

    tensor_weights = np.outer(signed_weights, signed_weights).reshape(-1)
    tensor_overhead = float(np.sum(np.abs(tensor_weights)))
    composed_weights = np.array(
        [
            signed_weights[0] * cptp_weights[0] + signed_weights[1] * cptp_weights[1],
            signed_weights[0] * cptp_weights[1] + signed_weights[1] * cptp_weights[0],
        ]
    )
    composed_overhead = float(np.sum(np.abs(composed_weights)))
    product_overhead = overhead * float(np.sum(np.abs(cptp_weights)))

    hadamard = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)
    conjugated_map = lambda operator: hadamard @ nonphysical_map(hadamard @ operator @ hadamard) @ hadamard
    conjugated_choi = _choi(conjugated_map)

    noise_probability = float(config["invertible_flip_noise_probability"])
    inverse_weights = np.array(
        [
            (1.0 - noise_probability) / (1.0 - 2.0 * noise_probability),
            -noise_probability / (1.0 - 2.0 * noise_probability),
        ]
    )
    inverse_map = signed_map(inverse_weights)
    noise_map = signed_map(np.array([1.0 - noise_probability, noise_probability]))
    inverse_residual = max(
        np.linalg.norm(
            inverse_map(noise_map(_matrix_unit(2, row, column))) - _matrix_unit(2, row, column)
        )
        for row in range(2)
        for column in range(2)
    )
    result = {
        "signed_trace_weight": float(np.sum(signed_weights)),
        "two_channel_decomposition_residual": float(decomposition_residual),
        "positive_channel_choi_minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(_choi(positive_channel))).real),
        "negative_channel_choi_minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(_choi(negative_channel))).real),
        "nonphysical_choi_minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(nonphysical_choi)).real),
        "implementability_overhead": overhead,
        "implementability_cost_log2": float(np.log2(overhead)),
        "choi_trace_norm_over_dimension": choi_trace_norm_over_dimension,
        "tensor_overhead": tensor_overhead,
        "tensor_additivity_residual": abs(float(np.log2(tensor_overhead)) - 2.0 * float(np.log2(overhead))),
        "composition_overhead": composed_overhead,
        "composition_product_bound": product_overhead,
        "composition_equality_counterexample_gap": product_overhead - composed_overhead,
        "unitary_invariance_residual": abs(
            float(np.sum(np.abs(np.linalg.eigvalsh(conjugated_choi))) / 2.0) - choi_trace_norm_over_dimension
        ),
        "inverse_noise_residual": float(inverse_residual),
        "inverse_noise_overhead": float(np.sum(np.abs(inverse_weights))),
        "general_claim_proved": False,
    }
    result["passed"] = bool(
        abs(result["signed_trace_weight"] - 1.0) <= tolerance
        and result["two_channel_decomposition_residual"] <= tolerance
        and min(result["positive_channel_choi_minimum_eigenvalue"], result["negative_channel_choi_minimum_eigenvalue"]) >= -tolerance
        and result["nonphysical_choi_minimum_eigenvalue"] < -tolerance
        and abs(result["implementability_overhead"] - result["choi_trace_norm_over_dimension"]) <= tolerance
        and result["tensor_additivity_residual"] <= tolerance
        and result["composition_overhead"] <= result["composition_product_bound"] + tolerance
        and result["composition_equality_counterexample_gap"] > tolerance
        and result["unitary_invariance_residual"] <= tolerance
        and result["inverse_noise_residual"] <= tolerance
    )
    return result


def run_campaign(config: dict[str, Any]) -> dict[str, Any]:
    profile = str(config["profile"])
    config = config["parameters"]
    tolerance = float(config["tolerance"])
    identity, x, y, z = _paulis()
    target_checks: dict[str, dict[str, Any]] = {}

    # T001: the printed SWAP-dephasing family has a closed semigroup factor and
    # a fixed signed two-branch HPTP representation.  We attest these algebraic
    # paths without invoking the unavailable SDP dependency.
    times = np.asarray(config["times"], dtype=float)
    rate = float(config["swap_dephasing_rate"])
    coherence = np.exp(-2.0 * rate * times)
    semigroup_error = max(
        abs(np.exp(-2.0 * rate * (a + b)) - np.exp(-2.0 * rate * a) * np.exp(-2.0 * rate * b))
        for a in times for b in times
    )
    signed_weights = np.asarray(config["hptp_signed_weights"], dtype=float)
    t001 = {
        "semigroup_max_error": float(semigroup_error),
        "initial_coherence": float(coherence[0]),
        "signed_trace_weight": float(np.sum(signed_weights)),
        "quasi_overhead": float(np.sum(np.abs(signed_weights))),
    }
    t001["passed"] = bool(
        semigroup_error <= tolerance
        and abs(t001["initial_coherence"] - 1.0) <= tolerance
        and abs(t001["signed_trace_weight"] - 1.0) <= tolerance
        and abs(t001["quasi_overhead"] - 2.0) <= tolerance
    )
    target_checks["T001"] = t001

    # T002: both amplitude-damping variants are independently constructed from
    # Kraus operators; positivity and trace preservation are implementation
    # invariants for the cost-curve inputs.
    ad = _amplitude_damping(float(config["amplitude_damping_probability"]))
    ad_choi = _choi(lambda op: _apply_kraus(op, ad))
    rotation = _unitary(float(config["z_rotation_angle"]), z)
    adz_choi = _choi(lambda op: rotation @ _apply_kraus(op, ad) @ rotation.conj().T)
    t002 = {
        "ad_min_choi_eigenvalue": float(np.min(np.linalg.eigvalsh(ad_choi)).real),
        "adz_min_choi_eigenvalue": float(np.min(np.linalg.eigvalsh(adz_choi)).real),
        "ad_trace_residual": float(np.linalg.norm(_partial_trace_output(ad_choi) - identity)),
        "adz_trace_residual": float(np.linalg.norm(_partial_trace_output(adz_choi) - identity)),
    }
    t002["passed"] = bool(
        min(t002["ad_min_choi_eigenvalue"], t002["adz_min_choi_eigenvalue"]) >= -tolerance
        and max(t002["ad_trace_residual"], t002["adz_trace_residual"]) <= tolerance
    )
    target_checks["T002"] = t002

    # T003: a Pauli semigroup witness is a finite channel polytope, is unital,
    # and commutes with Pauli covariance.  This is a numerical witness, not a
    # general proof of C01/C02/C07-C12.
    weights = np.asarray(config["pauli_mixture_weights"], dtype=float)
    paulis = (identity, x, y, z)

    def pauli_map(op: np.ndarray) -> np.ndarray:
        return sum(w * p @ op @ p for w, p in zip(weights, paulis, strict=True))

    pauli_choi = _choi(pauli_map)
    covariance_residual = max(
        np.linalg.norm(pauli_map(p @ x @ p) - p @ pauli_map(x) @ p)
        for p in paulis
    )
    t003 = {
        "mixture_weight_sum": float(np.sum(weights)),
        "minimum_weight": float(np.min(weights)),
        "choi_min_eigenvalue": float(np.min(np.linalg.eigvalsh(pauli_choi)).real),
        "trace_residual": float(np.linalg.norm(_partial_trace_output(pauli_choi) - identity)),
        "unital_residual": float(np.linalg.norm(pauli_map(identity) - identity)),
        "covariance_residual": float(covariance_residual),
        "finite_channel_count": len(weights),
    }
    t003["passed"] = bool(
        abs(t003["mixture_weight_sum"] - 1.0) <= tolerance
        and t003["minimum_weight"] >= 0.0
        and t003["choi_min_eigenvalue"] >= -tolerance
        and max(t003["trace_residual"], t003["unital_residual"], t003["covariance_residual"]) <= tolerance
    )
    target_checks["T003"] = t003

    # T004: explicit small-dimensional counter-witnesses exercise the no-go
    # code path.  A non-scalar commutator map is not CP, nontrivial unitary
    # families do not differ by phase, and amplitude damping is non-unital.
    commutator_choi = _choi(lambda op: -1j * (z @ op - op @ z))
    scalar_commutator_choi = _choi(lambda op: -1j * (identity @ op - op @ identity))
    u0 = _unitary(0.0, z)
    u1 = _unitary(float(config["z_rotation_angle"]), z)
    phase_fit = np.trace(u0.conj().T @ u1) / 2.0
    phase_residual = np.linalg.norm(u1 - phase_fit * u0)
    t004 = {
        "nonscalar_commutator_min_choi_eigenvalue": float(np.min(np.linalg.eigvalsh(commutator_choi)).real),
        "scalar_commutator_norm": float(np.linalg.norm(scalar_commutator_choi)),
        "amplitude_damping_unital_residual": float(np.linalg.norm(_apply_kraus(identity, ad) - identity)),
        "non_global_phase_residual": float(phase_residual),
        "commuting_exponential_residual": float(np.linalg.norm(u1 @ z - z @ u1)),
    }
    t004["passed"] = bool(
        t004["nonscalar_commutator_min_choi_eigenvalue"] < -tolerance
        and t004["scalar_commutator_norm"] <= tolerance
        and t004["amplitude_damping_unital_residual"] > tolerance
        and t004["non_global_phase_residual"] > tolerance
        and t004["commuting_exponential_residual"] <= tolerance
    )
    target_checks["T004"] = t004

    # T005: construct all six product maps in the printed CNOT decomposition,
    # insert them into the controlled-Ry amplitude-damping dilation, and compare
    # the weighted result against both exact CNOT and Kraus channels.
    coherent = np.asarray(config["coherent_protocol_coefficients"], dtype=float)
    eigenvalues = np.asarray(config["hamiltonian_eigenvalues"], dtype=float)
    amplitude_damping_protocol = _amplitude_damping_protocol_checks(config, tolerance)
    t005 = {
        "distinct_hamiltonian_eigenvalues": int(len(np.unique(eigenvalues))),
        "coherent_signed_sum": float(np.sum(coherent)),
        "coherent_overhead": float(np.sum(np.abs(coherent))),
        "amplitude_damping_protocol": amplitude_damping_protocol,
    }
    t005["passed"] = bool(
        t005["distinct_hamiltonian_eigenvalues"] == len(eigenvalues)
        and abs(t005["coherent_signed_sum"] - 1.0) <= tolerance
        and abs(t005["coherent_overhead"] - 2.0) <= tolerance
        and amplitude_damping_protocol["passed"]
    )
    target_checks["T005"] = t005

    # T006: exercise the structural-cost API on a transparent scalar witness
    # and test scaling, monotonicity, subadditivity and first-order Trotter
    # convergence.  This does not adjudicate the full diamond-norm theorems.
    def cost(rate_value: float, time_value: float) -> float:
        return abs(rate_value) * max(0.0, time_value)

    time_grid = np.asarray(config["cost_time_grid"], dtype=float)
    costs = np.asarray([cost(0.4, value) for value in time_grid])
    scale = float(config["positive_rate_scale"])
    a = np.array([[0.0, 1.0], [-1.0, 0.0]])
    b = np.array([[0.0, 0.0], [1.0, 0.0]])
    dt = float(config["trotter_step"])
    exact_second_order = np.eye(2) + dt * (a + b) + 0.5 * dt**2 * (a + b) @ (a + b)
    split_second_order = (np.eye(2) + dt * a + 0.5 * dt**2 * a @ a) @ (
        np.eye(2) + dt * b + 0.5 * dt**2 * b @ b
    )
    t006 = {
        "initial_cost": float(costs[0]),
        "minimum_cost_increment": float(np.min(np.diff(costs))),
        "faithfulness_zero_rate": float(cost(0.0, time_grid[-1])),
        "scaling_residual": float(abs(cost(scale * 0.4, time_grid[-1] / scale) - cost(0.4, time_grid[-1]))),
        "commuting_sum_subadditivity_residual": float(cost(0.2 + 0.3, 1.0) - cost(0.2, 1.0) - cost(0.3, 1.0)),
        "tensor_sum_subadditivity_residual": float(cost(0.1 + 0.25, 1.0) - cost(0.1, 1.0) - cost(0.25, 1.0)),
        "trotter_error": float(np.linalg.norm(split_second_order - exact_second_order)),
        "trotter_error_over_dt2": float(np.linalg.norm(split_second_order - exact_second_order) / dt**2),
    }
    t006["passed"] = bool(
        abs(t006["initial_cost"]) <= tolerance
        and t006["minimum_cost_increment"] >= -tolerance
        and abs(t006["faithfulness_zero_rate"]) <= tolerance
        and t006["scaling_residual"] <= tolerance
        and max(t006["commuting_sum_subadditivity_residual"], t006["tensor_sum_subadditivity_residual"]) <= tolerance
        and t006["trotter_error_over_dt2"] < float(config["trotter_error_constant_limit"])
    )
    target_checks["T006"] = t006

    # T007: verify Choi block retrieval on the identity channel and a
    # unique-steady-state spectral witness for amplitude damping.
    identity_choi = _choi(lambda op: op)
    block_residual = max(
        np.linalg.norm(identity_choi[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2] - _matrix_unit(2, i, j))
        for i in range(2) for j in range(2)
    )
    damping_probability = float(config["steady_state_damping_probability"])
    contraction_eigenvalue = np.sqrt(1.0 - damping_probability)
    t007 = {
        "choi_block_retrieval_residual": float(block_residual),
        "steady_state_contraction_eigenvalue": float(contraction_eigenvalue),
        "unique_steady_state_gap": float(1.0 - contraction_eigenvalue),
    }
    t007["passed"] = bool(block_residual <= tolerance and 0.0 < contraction_eigenvalue < 1.0)
    target_checks["T007"] = t007

    # T008-T011 close the fresh review's four genuine authored-scope gaps.
    # Each campaign executes finite examples or counterexamples.  The output
    # explicitly refuses to promote those examples into general proofs.
    target_checks["T008"] = _programmability_definition_checks(config, tolerance)
    target_checks["T009"] = _choi_link_checks(config, tolerance)
    target_checks["T010"] = _gksl_liouville_checks(config, tolerance)
    target_checks["T011"] = _hptp_cost_checks(config, tolerance)

    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": "attested" if target_checks[target_id]["passed"] else "failed",
            "scientific_status": "unchanged",
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    for item_id in ("C06-AD-HPTP-DIM-12", "C31-AD-CIRCUIT-KAPPA-5"):
        item_results[item_id]["scientific_status"] = "awaiting_fresh_review"
        item_results[item_id]["author_evidence_status"] = "paper_exact_protocol_executed"
    return {
        "schema_version": 1,
        "paper_id": "2512.08279",
        "profile": profile,
        "purpose": "implementation_attestation_only",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
        "target_checks": target_checks,
        "item_results": item_results,
        "status": "passed" if all(row["passed"] for row in target_checks.values()) else "failed",
    }
