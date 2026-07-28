from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Iterable, Sequence

import cvxpy as cp
import numpy as np
import scipy.sparse as sp
from scipy.linalg import expm


Array = np.ndarray


def _as_complex_matrix(value: Array, *, name: str) -> Array:
    matrix = np.asarray(value, dtype=np.complex128)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"{name} must be a square matrix, got {matrix.shape}")
    return matrix


def hermitian_part(matrix: Array) -> Array:
    matrix = np.asarray(matrix, dtype=np.complex128)
    return 0.5 * (matrix + matrix.conj().T)


def hermitian_residual(matrix: Array) -> float:
    matrix = np.asarray(matrix, dtype=np.complex128)
    return float(np.linalg.norm(matrix - matrix.conj().T, ord="fro"))


def minimum_eigenvalue(matrix: Array) -> float:
    return float(np.min(np.linalg.eigvalsh(hermitian_part(matrix))).real)


def liouvillian(hamiltonian: Array, jump_operators: Iterable[Array]) -> Array:
    """Return the row-vectorized GKSL generator from EQC001.

    The convention is vec(|i><j|)=|i>|j>, equivalently NumPy C-order
    flattening. Therefore vec(A X B)=(A tensor B.T) vec(X).
    """

    hamiltonian = _as_complex_matrix(hamiltonian, name="hamiltonian")
    dimension = hamiltonian.shape[0]
    identity = np.eye(dimension, dtype=np.complex128)
    generator = -1j * (
        np.kron(hamiltonian, identity)
        - np.kron(identity, hamiltonian.T)
    )
    for raw_jump in jump_operators:
        jump = _as_complex_matrix(raw_jump, name="jump operator")
        if jump.shape != hamiltonian.shape:
            raise ValueError("jump operators and Hamiltonian must have the same dimension")
        loss = jump.conj().T @ jump
        generator += np.kron(jump, jump.conj())
        generator -= 0.5 * np.kron(loss, identity)
        generator -= 0.5 * np.kron(identity, loss.T)
    return generator


def channel_superoperator(generator: Array, time_value: float) -> Array:
    generator = _as_complex_matrix(generator, name="generator")
    return expm(float(time_value) * generator)


def apply_superoperator(superoperator: Array, operator: Array) -> Array:
    operator = _as_complex_matrix(operator, name="operator")
    dimension = operator.shape[0]
    superoperator = np.asarray(superoperator, dtype=np.complex128)
    if superoperator.shape != (dimension * dimension, dimension * dimension):
        raise ValueError("superoperator shape does not match operator dimension")
    output = superoperator @ operator.reshape(-1, order="C")
    return output.reshape((dimension, dimension), order="C")


def superoperator_to_choi(superoperator: Array, dimension: int) -> Array:
    """Reshuffle K_(ab,ij) into J_(ia,jb), using input-before-output order."""

    superoperator = np.asarray(superoperator, dtype=np.complex128)
    expected = (dimension * dimension, dimension * dimension)
    if superoperator.shape != expected:
        raise ValueError(f"expected a {expected} superoperator, got {superoperator.shape}")
    tensor = superoperator.reshape(
        (dimension, dimension, dimension, dimension),
        order="C",
    )
    choi = tensor.transpose(2, 0, 3, 1).reshape(expected, order="C")
    return hermitian_part(choi)


def channel_choi(
    hamiltonian: Array,
    jump_operators: Iterable[Array],
    time_value: float,
) -> Array:
    dimension = np.asarray(hamiltonian).shape[0]
    generator = liouvillian(hamiltonian, jump_operators)
    return superoperator_to_choi(
        channel_superoperator(generator, time_value),
        dimension,
    )


def map_to_choi(map_function, input_dimension: int, output_dimension: int) -> Array:
    choi = np.zeros(
        (input_dimension * output_dimension, input_dimension * output_dimension),
        dtype=np.complex128,
    )
    for row in range(input_dimension):
        for column in range(input_dimension):
            matrix_unit = np.zeros((input_dimension, input_dimension), dtype=np.complex128)
            matrix_unit[row, column] = 1.0
            output = np.asarray(map_function(matrix_unit), dtype=np.complex128)
            if output.shape != (output_dimension, output_dimension):
                raise ValueError("map output has the wrong dimension")
            row_slice = slice(row * output_dimension, (row + 1) * output_dimension)
            column_slice = slice(
                column * output_dimension,
                (column + 1) * output_dimension,
            )
            choi[row_slice, column_slice] = output
    return hermitian_part(choi)


def partial_trace_output(matrix: Array, input_dimension: int, output_dimension: int) -> Array:
    matrix = np.asarray(matrix, dtype=np.complex128)
    total_dimension = input_dimension * output_dimension
    if matrix.shape != (total_dimension, total_dimension):
        raise ValueError("matrix shape does not match partial-trace dimensions")
    tensor = matrix.reshape(
        (input_dimension, output_dimension, input_dimension, output_dimension),
        order="C",
    )
    return np.einsum("iaja->ij", tensor, optimize=True)


def apply_choi(choi: Array, input_operator: Array, output_dimension: int) -> Array:
    input_operator = _as_complex_matrix(input_operator, name="input_operator")
    input_dimension = input_operator.shape[0]
    choi = np.asarray(choi, dtype=np.complex128)
    expected = input_dimension * output_dimension
    if choi.shape != (expected, expected):
        raise ValueError("Choi shape does not match input/output dimensions")
    tensor = choi.reshape(
        (input_dimension, output_dimension, input_dimension, output_dimension),
        order="C",
    )
    return np.einsum("ij,iajb->ab", input_operator, tensor, optimize=True)


def partial_trace_output_linear_map(
    input_dimension: int,
    output_dimension: int,
) -> sp.csr_matrix:
    """Sparse map vec_C(J) -> vec_C(Tr_out J)."""

    total_dimension = input_dimension * output_dimension
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    for input_row in range(input_dimension):
        for input_column in range(input_dimension):
            output_row = input_row * input_dimension + input_column
            for traced_index in range(output_dimension):
                total_row = input_row * output_dimension + traced_index
                total_column = input_column * output_dimension + traced_index
                matrix_index = total_row * total_dimension + total_column
                rows.append(output_row)
                columns.append(matrix_index)
                values.append(1.0)
    return sp.coo_matrix(
        (values, (rows, columns)),
        shape=(input_dimension * input_dimension, total_dimension * total_dimension),
        dtype=np.float64,
    ).tocsr()


def partial_trace_output_expression(
    matrix_expression,
    input_dimension: int,
    output_dimension: int,
):
    linear_map = partial_trace_output_linear_map(input_dimension, output_dimension)
    vector = cp.reshape(
        matrix_expression,
        (input_dimension * output_dimension) ** 2,
        order="C",
    )
    return cp.reshape(
        linear_map @ vector,
        (input_dimension, input_dimension),
        order="C",
    )


def program_contraction_linear_map(
    program_state: Array,
    system_dimension: int,
    program_dimension: int,
    output_dimension: int,
) -> sp.csr_matrix:
    """Sparse map vec_C(J^P) -> vec_C(J[P(.-program)])."""

    program_state = np.asarray(program_state, dtype=np.complex128)
    if program_state.shape != (program_dimension, program_dimension):
        raise ValueError("program state has the wrong dimension")
    total_dimension = system_dimension * program_dimension * output_dimension
    effective_dimension = system_dimension * output_dimension
    rows: list[int] = []
    columns: list[int] = []
    values: list[complex] = []
    for system_row in range(system_dimension):
        for output_row in range(output_dimension):
            effective_row = system_row * output_dimension + output_row
            for system_column in range(system_dimension):
                for output_column in range(output_dimension):
                    effective_column = system_column * output_dimension + output_column
                    result_index = (
                        effective_row * effective_dimension + effective_column
                    )
                    for program_row in range(program_dimension):
                        for program_column in range(program_dimension):
                            coefficient = program_state[program_row, program_column]
                            if coefficient == 0:
                                continue
                            total_row = (
                                (system_row * program_dimension + program_row)
                                * output_dimension
                                + output_row
                            )
                            total_column = (
                                (system_column * program_dimension + program_column)
                                * output_dimension
                                + output_column
                            )
                            matrix_index = total_row * total_dimension + total_column
                            rows.append(result_index)
                            columns.append(matrix_index)
                            values.append(coefficient)
    return sp.coo_matrix(
        (values, (rows, columns)),
        shape=(effective_dimension**2, total_dimension**2),
        dtype=np.complex128,
    ).tocsr()


def contract_program_choi(
    retrieval_choi: Array,
    program_state: Array,
    system_dimension: int,
    program_dimension: int,
    output_dimension: int,
) -> Array:
    retrieval_choi = np.asarray(retrieval_choi, dtype=np.complex128)
    linear_map = program_contraction_linear_map(
        program_state,
        system_dimension,
        program_dimension,
        output_dimension,
    )
    vector = linear_map @ retrieval_choi.reshape(-1, order="C")
    effective_dimension = system_dimension * output_dimension
    return hermitian_part(
        vector.reshape(
            (effective_dimension, effective_dimension),
            order="C",
        )
    )


def contract_program_choi_expression(
    retrieval_choi_expression,
    program_state: Array,
    system_dimension: int,
    program_dimension: int,
    output_dimension: int,
):
    linear_map = program_contraction_linear_map(
        program_state,
        system_dimension,
        program_dimension,
        output_dimension,
    )
    total_dimension = system_dimension * program_dimension * output_dimension
    effective_dimension = system_dimension * output_dimension
    vector = cp.reshape(
        retrieval_choi_expression,
        total_dimension**2,
        order="C",
    )
    return cp.reshape(
        linear_map @ vector,
        (effective_dimension, effective_dimension),
        order="C",
    )


def computational_basis(dimension: int, index: int) -> Array:
    vector = np.zeros(dimension, dtype=np.complex128)
    vector[index] = 1.0
    return vector


def swap_operator() -> Array:
    swap = np.zeros((4, 4), dtype=np.complex128)
    for first in range(2):
        for second in range(2):
            source = 2 * first + second
            target = 2 * second + first
            swap[target, source] = 1.0
    return swap


def bell_states() -> tuple[Array, Array, Array, Array]:
    zero = computational_basis(2, 0)
    one = computational_basis(2, 1)
    state_00 = np.kron(zero, zero)
    state_01 = np.kron(zero, one)
    state_10 = np.kron(one, zero)
    state_11 = np.kron(one, one)
    return (
        (state_00 + state_11) / math.sqrt(2.0),
        (state_00 - state_11) / math.sqrt(2.0),
        (state_01 + state_10) / math.sqrt(2.0),
        (state_01 - state_10) / math.sqrt(2.0),
    )


def bell_projectors() -> tuple[Array, Array, Array, Array]:
    return tuple(np.outer(state, state.conj()) for state in bell_states())


def bell_dephase(operator: Array) -> Array:
    operator = _as_complex_matrix(operator, name="operator")
    output = np.zeros_like(operator)
    for projector in bell_projectors():
        output += projector @ operator @ projector
    return output


def swap_program_state(time_value: float) -> Array:
    vector = np.array(
        [np.exp(1j * time_value), np.exp(-1j * time_value)],
        dtype=np.complex128,
    ) / math.sqrt(2.0)
    return np.outer(vector, vector.conj())


def swap_program_processor(operator: Array) -> Array:
    """Minimal two-level HPTP processor from Supplemental Eq. programmable_swap."""

    operator = _as_complex_matrix(operator, name="operator")
    system_dimension = 4
    program_dimension = 2
    expected = system_dimension * program_dimension
    if operator.shape != (expected, expected):
        raise ValueError("SWAP processor expects a 4x2-dimensional input")
    tensor = operator.reshape(
        (system_dimension, program_dimension, system_dimension, program_dimension),
        order="C",
    )
    reduced = np.einsum("ipjp->ij", tensor, optimize=True)
    swap = swap_operator()
    projectors = ((np.eye(4) + swap) / 2.0, (np.eye(4) - swap) / 2.0)
    output = np.zeros((system_dimension, system_dimension), dtype=np.complex128)
    for index, projector in enumerate(projectors):
        output += projector @ reduced @ projector
        for other_index, other_projector in enumerate(projectors):
            if index == other_index:
                continue
            block = tensor[:, index, :, other_index]
            output += 2.0 * projector @ block @ other_projector
    return output


def swap_program_processor_choi() -> Array:
    return map_to_choi(
        swap_program_processor,
        input_dimension=8,
        output_dimension=4,
    )


def swap_dephasing_liouvillian(lambda_value: float) -> Array:
    swap = swap_operator()
    jumps = [math.sqrt(lambda_value) * projector for projector in bell_projectors()]
    # liouvillian(H, ...) implements -i[H,.]; H=-S produces +i[S,.].
    return liouvillian(-swap, jumps)


def swap_dephasing_channel(operator: Array, time_value: float, lambda_value: float) -> Array:
    operator = _as_complex_matrix(operator, name="operator")
    unitary = expm(1j * time_value * swap_operator())
    coherent = unitary @ operator @ unitary.conj().T
    damping_weight = math.exp(-lambda_value * time_value)
    return damping_weight * coherent + (1.0 - damping_weight) * bell_dephase(operator)


def swap_overlap_exact(time_value: float | Array, lambda_value: float = 0.5):
    time_array = np.asarray(time_value, dtype=float)
    values = 0.5 * (
        1.0 + np.exp(-lambda_value * time_array) * np.cos(2.0 * time_array)
    )
    return float(values) if values.ndim == 0 else values


@dataclass
class SignedChannelDecomposition:
    p_plus: float
    p_minus: float
    choi_plus_subnormalized: Array
    choi_minus_subnormalized: Array
    choi_plus_channel: Array
    choi_minus_channel: Array
    objective: float
    status: str
    solver: str
    solve_time_seconds: float
    iterations: int | None
    primal_trace_residual: float
    decomposition_residual: float
    minimum_eigenvalue_plus: float
    minimum_eigenvalue_minus: float


def decompose_hptp_processor(
    processor_choi: Array,
    *,
    input_dimension: int,
    output_dimension: int,
    solver: str = "SCS",
    solver_epsilon: float = 1e-7,
    max_iterations: int = 100_000,
) -> SignedChannelDecomposition:
    processor_choi = hermitian_part(processor_choi)
    total_dimension = input_dimension * output_dimension
    if processor_choi.shape != (total_dimension, total_dimension):
        raise ValueError("processor Choi dimension mismatch")
    plus = cp.Variable((total_dimension, total_dimension), hermitian=True)
    minus = cp.Variable((total_dimension, total_dimension), hermitian=True)
    p_plus = cp.Variable(nonneg=True)
    p_minus = cp.Variable(nonneg=True)
    identity = np.eye(input_dimension)
    constraints = [
        plus >> 0,
        minus >> 0,
        plus - minus == processor_choi,
        partial_trace_output_expression(
            plus,
            input_dimension,
            output_dimension,
        )
        == p_plus * identity,
        partial_trace_output_expression(
            minus,
            input_dimension,
            output_dimension,
        )
        == p_minus * identity,
    ]
    problem = cp.Problem(cp.Minimize(p_plus + p_minus), constraints)
    start = time.perf_counter()
    if solver.upper() == "SCS":
        problem.solve(
            solver=cp.SCS,
            eps=solver_epsilon,
            max_iters=max_iterations,
            verbose=False,
        )
    else:
        problem.solve(solver=solver, verbose=False)
    elapsed = time.perf_counter() - start
    if plus.value is None or minus.value is None:
        raise RuntimeError(f"decomposition SDP did not return a solution: {problem.status}")
    plus_value = hermitian_part(plus.value)
    minus_value = hermitian_part(minus.value)
    p_plus_value = float(p_plus.value)
    p_minus_value = float(p_minus.value)
    if p_plus_value <= 0 or p_minus_value <= 0:
        raise RuntimeError("signed decomposition returned a nonpositive branch weight")
    trace_plus = partial_trace_output(
        plus_value,
        input_dimension,
        output_dimension,
    )
    trace_minus = partial_trace_output(
        minus_value,
        input_dimension,
        output_dimension,
    )
    trace_residual = max(
        np.linalg.norm(trace_plus - p_plus_value * identity, ord="fro"),
        np.linalg.norm(trace_minus - p_minus_value * identity, ord="fro"),
    )
    solver_stats = problem.solver_stats
    return SignedChannelDecomposition(
        p_plus=p_plus_value,
        p_minus=p_minus_value,
        choi_plus_subnormalized=plus_value,
        choi_minus_subnormalized=minus_value,
        choi_plus_channel=plus_value / p_plus_value,
        choi_minus_channel=minus_value / p_minus_value,
        objective=float(problem.value),
        status=str(problem.status),
        solver=str(solver_stats.solver_name),
        solve_time_seconds=float(elapsed),
        iterations=(
            int(solver_stats.num_iters)
            if solver_stats.num_iters is not None
            else None
        ),
        primal_trace_residual=float(trace_residual),
        decomposition_residual=float(
            np.linalg.norm(
                plus_value - minus_value - processor_choi,
                ord="fro",
            )
        ),
        minimum_eigenvalue_plus=minimum_eigenvalue(plus_value),
        minimum_eigenvalue_minus=minimum_eigenvalue(minus_value),
    )


def quasi_sample_swap_dephasing(
    times: Sequence[float],
    decomposition: SignedChannelDecomposition,
    *,
    lambda_value: float = 0.5,
    outer_cycles: int = 1000,
    inner_samples: int = 200,
    seed: int = 251208279,
) -> dict[str, Array]:
    times_array = np.asarray(times, dtype=float)
    random = np.random.default_rng(seed)
    initial_vector = computational_basis(4, 1)
    initial_state = np.outer(initial_vector, initial_vector.conj())
    observable = initial_state
    q_plus = decomposition.p_plus / decomposition.objective
    kappa = decomposition.objective
    exact_values: list[float] = []
    direct_values: list[float] = []
    sampled_values: list[float] = []
    standard_errors: list[float] = []
    coherent_branch_counts: list[int] = []
    plus_inner_counts: list[int] = []
    generator = swap_dephasing_liouvillian(lambda_value)
    for time_value in times_array:
        exact = swap_overlap_exact(time_value, lambda_value)
        evolved = apply_superoperator(
            channel_superoperator(generator, time_value),
            initial_state,
        )
        direct = float(np.trace(observable @ evolved).real)
        program = swap_program_state(time_value)
        processor_input = np.kron(initial_state, program)
        plus_output = apply_choi(
            decomposition.choi_plus_channel,
            processor_input,
            output_dimension=4,
        )
        minus_output = apply_choi(
            decomposition.choi_minus_channel,
            processor_input,
            output_dimension=4,
        )
        plus_observable = float(np.trace(observable @ plus_output).real)
        minus_observable = float(np.trace(observable @ minus_output).real)
        coherent_probability = math.exp(-lambda_value * float(time_value))
        coherent_mask = random.random(outer_cycles) < coherent_probability
        cycle_values = np.full(outer_cycles, 0.5, dtype=float)
        coherent_count = int(np.sum(coherent_mask))
        total_plus = 0
        if coherent_count:
            plus_counts = random.binomial(
                inner_samples,
                q_plus,
                size=coherent_count,
            )
            total_plus = int(np.sum(plus_counts))
            inner_estimates = kappa * (
                plus_counts * plus_observable
                - (inner_samples - plus_counts) * minus_observable
            ) / inner_samples
            cycle_values[coherent_mask] = inner_estimates
        exact_values.append(exact)
        direct_values.append(direct)
        sampled_values.append(float(np.mean(cycle_values)))
        standard_errors.append(
            float(np.std(cycle_values, ddof=1) / math.sqrt(outer_cycles))
            if outer_cycles > 1
            else 0.0
        )
        coherent_branch_counts.append(coherent_count)
        plus_inner_counts.append(total_plus)
    return {
        "time": times_array,
        "exact_overlap": np.asarray(exact_values),
        "direct_liouvillian_overlap": np.asarray(direct_values),
        "quasi_sampled_overlap": np.asarray(sampled_values),
        "standard_error": np.asarray(standard_errors),
        "coherent_branch_count": np.asarray(coherent_branch_counts, dtype=int),
        "plus_inner_count": np.asarray(plus_inner_counts, dtype=int),
    }


@dataclass
class DiamondNormResult:
    value: float
    status: str
    solver: str
    solve_time_seconds: float
    iterations: int | None
    minimum_eigenvalue_plus: float
    minimum_eigenvalue_minus: float
    partial_trace_slack: float


@dataclass
class BatchDiamondNormResult:
    values: Array
    status: str
    solver: str
    solve_time_seconds: float
    iterations: int | None
    worst_psd_violation: float
    worst_partial_trace_violation: float


def diamond_norm_hp(
    choi_difference: Array,
    *,
    input_dimension: int,
    output_dimension: int,
    solver: str = "SCS",
    solver_epsilon: float = 1e-7,
    max_iterations: int = 100_000,
) -> DiamondNormResult:
    choi_difference = hermitian_part(choi_difference)
    total_dimension = input_dimension * output_dimension
    if choi_difference.shape != (total_dimension, total_dimension):
        raise ValueError("diamond-norm Choi dimension mismatch")
    certificate = cp.Variable((total_dimension, total_dimension), hermitian=True)
    upper_bound = cp.Variable(nonneg=True)
    partial_trace = partial_trace_output_expression(
        certificate,
        input_dimension,
        output_dimension,
    )
    constraints = [
        certificate >> 0,
        certificate + choi_difference >> 0,
        certificate - choi_difference >> 0,
        partial_trace << upper_bound * np.eye(input_dimension),
    ]
    problem = cp.Problem(cp.Minimize(upper_bound), constraints)
    start = time.perf_counter()
    if solver.upper() == "SCS":
        problem.solve(
            solver=cp.SCS,
            eps=solver_epsilon,
            max_iters=max_iterations,
            verbose=False,
        )
    else:
        problem.solve(solver=solver, verbose=False)
    elapsed = time.perf_counter() - start
    if certificate.value is None or upper_bound.value is None:
        raise RuntimeError(f"diamond norm SDP did not return a solution: {problem.status}")
    certificate_value = hermitian_part(certificate.value)
    bound_value = float(upper_bound.value)
    trace_value = partial_trace_output(
        certificate_value,
        input_dimension,
        output_dimension,
    )
    return DiamondNormResult(
        value=bound_value,
        status=str(problem.status),
        solver=str(problem.solver_stats.solver_name),
        solve_time_seconds=float(elapsed),
        iterations=(
            int(problem.solver_stats.num_iters)
            if problem.solver_stats.num_iters is not None
            else None
        ),
        minimum_eigenvalue_plus=minimum_eigenvalue(
            certificate_value + choi_difference
        ),
        minimum_eigenvalue_minus=minimum_eigenvalue(
            certificate_value - choi_difference
        ),
        partial_trace_slack=float(
            bound_value - np.max(np.linalg.eigvalsh(hermitian_part(trace_value))).real
        ),
    )


def diamond_norms_hp_batch(
    choi_differences: Sequence[Array],
    *,
    input_dimension: int,
    output_dimension: int,
    solver: str = "SCS",
    solver_epsilon: float = 1e-5,
    max_iterations: int = 100_000,
) -> BatchDiamondNormResult:
    """Solve independent HP diamond-norm SDPs in one separable cone program."""

    if not choi_differences:
        return BatchDiamondNormResult(
            values=np.asarray([], dtype=float),
            status="not_needed",
            solver=solver,
            solve_time_seconds=0.0,
            iterations=0,
            worst_psd_violation=0.0,
            worst_partial_trace_violation=0.0,
        )
    differences = [hermitian_part(value) for value in choi_differences]
    total_dimension = input_dimension * output_dimension
    for difference in differences:
        if difference.shape != (total_dimension, total_dimension):
            raise ValueError("batch diamond-norm Choi dimension mismatch")
    bounds = cp.Variable(len(differences), nonneg=True)
    certificates: list[cp.Variable] = []
    constraints = []
    identity = np.eye(input_dimension)
    for index, difference in enumerate(differences):
        certificate = cp.Variable((total_dimension, total_dimension), hermitian=True)
        certificates.append(certificate)
        constraints.extend(
            [
                certificate >> 0,
                certificate + difference >> 0,
                certificate - difference >> 0,
                partial_trace_output_expression(
                    certificate,
                    input_dimension,
                    output_dimension,
                )
                << bounds[index] * identity,
            ]
        )
    problem = cp.Problem(cp.Minimize(cp.sum(bounds)), constraints)
    start = time.perf_counter()
    if solver.upper() == "SCS":
        problem.solve(
            solver=cp.SCS,
            eps=solver_epsilon,
            max_iters=max_iterations,
            verbose=False,
        )
    else:
        problem.solve(solver=solver, verbose=False)
    elapsed = time.perf_counter() - start
    if bounds.value is None:
        raise RuntimeError(f"batch diamond norm SDP returned no solution: {problem.status}")
    values = np.maximum(np.asarray(bounds.value, dtype=float), 0.0)
    worst_psd_violation = 0.0
    worst_trace_violation = 0.0
    for index, (certificate_variable, difference) in enumerate(
        zip(certificates, differences, strict=True)
    ):
        if certificate_variable.value is None:
            raise RuntimeError("batch diamond certificate missing")
        certificate = hermitian_part(certificate_variable.value)
        worst_psd_violation = max(
            worst_psd_violation,
            -minimum_eigenvalue(certificate),
            -minimum_eigenvalue(certificate + difference),
            -minimum_eigenvalue(certificate - difference),
        )
        trace_value = partial_trace_output(
            certificate,
            input_dimension,
            output_dimension,
        )
        worst_trace_violation = max(
            worst_trace_violation,
            float(
                np.max(
                    np.linalg.eigvalsh(
                        hermitian_part(trace_value - values[index] * identity)
                    )
                ).real
            ),
        )
    return BatchDiamondNormResult(
        values=values,
        status=str(problem.status),
        solver=str(problem.solver_stats.solver_name),
        solve_time_seconds=float(elapsed),
        iterations=(
            int(problem.solver_stats.num_iters)
            if problem.solver_stats.num_iters is not None
            else None
        ),
        worst_psd_violation=float(max(0.0, worst_psd_violation)),
        worst_partial_trace_violation=float(max(0.0, worst_trace_violation)),
    )


def choi_absolute_diamond_upper_bound(
    choi_difference: Array,
    *,
    input_dimension: int,
    output_dimension: int,
) -> float:
    """Certified diamond-norm upper bound from Z=|J|.

    For Hermitian J, |J|+J and |J|-J are both positive semidefinite. The
    Watrous primal is therefore feasible with Z=|J|, giving
    ||Phi||_diamond <= ||Tr_out |J(Phi)||||_infinity.
    """

    choi_difference = hermitian_part(choi_difference)
    eigenvalues, eigenvectors = np.linalg.eigh(choi_difference)
    absolute_choi = (eigenvectors * np.abs(eigenvalues)) @ eigenvectors.conj().T
    partial = partial_trace_output(
        absolute_choi,
        input_dimension,
        output_dimension,
    )
    return float(np.max(np.linalg.eigvalsh(hermitian_part(partial))).real)


def amplitude_damping_choi(
    time_value: float,
    *,
    gamma: float = 0.1,
    with_z_hamiltonian: bool = False,
) -> Array:
    eta = math.exp(-gamma * time_value)
    # A global phase turns exp(-i Z t) into diag(1, exp(2 i t)); the
    # off-diagonal density-matrix element then acquires exp(-2 i t).
    phase = np.exp(2j * time_value) if with_z_hamiltonian else 1.0 + 0.0j
    kraus_zero = np.array(
        [[1.0, 0.0], [0.0, math.sqrt(eta) * phase]],
        dtype=np.complex128,
    )
    kraus_one = np.array(
        [[0.0, math.sqrt(1.0 - eta)], [0.0, 0.0]],
        dtype=np.complex128,
    )
    identity_vector = np.eye(2, dtype=np.complex128).reshape(-1, order="C")
    choi = np.zeros((4, 4), dtype=np.complex128)
    for kraus in (kraus_zero, kraus_one):
        vector = np.kron(np.eye(2), kraus) @ identity_vector
        choi += np.outer(vector, vector.conj())
    return hermitian_part(choi)


def fig3_model(
    times: Sequence[float],
    *,
    gamma: float = 0.1,
    with_z_hamiltonian: bool = False,
) -> tuple[list[Array], list[Array]]:
    hamiltonian = (
        np.diag([1.0, -1.0]).astype(np.complex128)
        if with_z_hamiltonian
        else np.zeros((2, 2), dtype=np.complex128)
    )
    jump = math.sqrt(gamma) * np.array(
        [[0.0, 1.0], [0.0, 0.0]],
        dtype=np.complex128,
    )
    generator = liouvillian(hamiltonian, [jump])
    target_choi: list[Array] = []
    program_states: list[Array] = []
    for time_value in times:
        choi = superoperator_to_choi(
            channel_superoperator(generator, float(time_value)),
            2,
        )
        target_choi.append(choi)
        program_states.append(choi / 2.0)
    return target_choi, program_states


@dataclass
class ProgrammingCostSolution:
    epsilon: float
    kappa: float
    gamma_log2: float
    p_plus: float
    p_minus: float
    status: str
    solver: str
    solve_time_seconds: float
    setup_time_seconds: float | None
    solver_time_seconds: float | None
    iterations: int | None
    trace_residual: float
    signed_weight_residual: float
    minimum_eigenvalue_plus: float
    minimum_eigenvalue_minus: float
    worst_diamond_psd_violation: float
    worst_diamond_trace_violation: float
    retrieval_choi: Array


class ProgrammingCostProblem:
    """One compiled finite-grid SDP whose epsilon bound can be updated."""

    def __init__(
        self,
        target_choi: Sequence[Array],
        program_states: Sequence[Array],
        *,
        system_dimension: int = 2,
        program_dimension: int = 4,
        output_dimension: int = 2,
    ) -> None:
        if len(target_choi) != len(program_states) or not target_choi:
            raise ValueError("target Choi and program-state lists must have equal nonzero length")
        self.target_choi = [hermitian_part(value) for value in target_choi]
        self.program_states = [hermitian_part(value) for value in program_states]
        self.system_dimension = system_dimension
        self.program_dimension = program_dimension
        self.output_dimension = output_dimension
        input_dimension = system_dimension * program_dimension
        total_dimension = input_dimension * output_dimension
        self.input_dimension = input_dimension
        self.total_dimension = total_dimension
        self.j_plus = cp.Variable((total_dimension, total_dimension), hermitian=True)
        self.j_minus = cp.Variable((total_dimension, total_dimension), hermitian=True)
        self.p_plus = cp.Variable(nonneg=True)
        self.p_minus = cp.Variable(nonneg=True)
        self.epsilon = cp.Parameter(nonneg=True)
        self.certificates: list[cp.Variable] = []
        retrieval = self.j_plus - self.j_minus
        identity_input = np.eye(input_dimension)
        constraints = [
            self.j_plus >> 0,
            self.j_minus >> 0,
            partial_trace_output_expression(
                self.j_plus,
                input_dimension,
                output_dimension,
            )
            == self.p_plus * identity_input,
            partial_trace_output_expression(
                self.j_minus,
                input_dimension,
                output_dimension,
            )
            == self.p_minus * identity_input,
            partial_trace_output_expression(
                retrieval,
                input_dimension,
                output_dimension,
            )
            == identity_input,
        ]
        for target, program in zip(self.target_choi, self.program_states, strict=True):
            effective = contract_program_choi_expression(
                retrieval,
                program,
                system_dimension,
                program_dimension,
                output_dimension,
            )
            difference = effective - target
            certificate = cp.Variable(
                (
                    system_dimension * output_dimension,
                    system_dimension * output_dimension,
                ),
                hermitian=True,
            )
            self.certificates.append(certificate)
            trace_certificate = partial_trace_output_expression(
                certificate,
                system_dimension,
                output_dimension,
            )
            constraints.extend(
                [
                    certificate >> 0,
                    certificate + difference >> 0,
                    certificate - difference >> 0,
                    trace_certificate
                    << 2.0 * self.epsilon * np.eye(system_dimension),
                ]
            )
        self.problem = cp.Problem(
            cp.Minimize(self.p_plus + self.p_minus),
            constraints,
        )

    @property
    def time_points(self) -> int:
        return len(self.target_choi)

    def solve(
        self,
        epsilon: float,
        *,
        solver: str = "SCS",
        solver_epsilon: float = 2e-5,
        max_iterations: int = 100_000,
        warm_start: bool = True,
        verbose: bool = False,
    ) -> ProgrammingCostSolution:
        self.epsilon.value = float(epsilon)
        start = time.perf_counter()
        if solver.upper() == "SCS":
            self.problem.solve(
                solver=cp.SCS,
                eps=solver_epsilon,
                max_iters=max_iterations,
                warm_start=warm_start,
                verbose=verbose,
            )
        else:
            self.problem.solve(
                solver=solver,
                warm_start=warm_start,
                verbose=verbose,
            )
        elapsed = time.perf_counter() - start
        if self.j_plus.value is None or self.j_minus.value is None:
            raise RuntimeError(
                f"programming-cost SDP returned no solution: {self.problem.status}"
            )
        plus = hermitian_part(self.j_plus.value)
        minus = hermitian_part(self.j_minus.value)
        retrieval = plus - minus
        p_plus = float(self.p_plus.value)
        p_minus = float(self.p_minus.value)
        kappa = float(self.problem.value)
        identity_input = np.eye(self.input_dimension)
        trace_residual = max(
            np.linalg.norm(
                partial_trace_output(
                    plus,
                    self.input_dimension,
                    self.output_dimension,
                )
                - p_plus * identity_input,
                ord="fro",
            ),
            np.linalg.norm(
                partial_trace_output(
                    minus,
                    self.input_dimension,
                    self.output_dimension,
                )
                - p_minus * identity_input,
                ord="fro",
            ),
            np.linalg.norm(
                partial_trace_output(
                    retrieval,
                    self.input_dimension,
                    self.output_dimension,
                )
                - identity_input,
                ord="fro",
            ),
        )
        worst_psd_violation = 0.0
        worst_trace_violation = 0.0
        for target, program, raw_certificate in zip(
            self.target_choi,
            self.program_states,
            self.certificates,
            strict=True,
        ):
            if raw_certificate.value is None:
                raise RuntimeError("diamond certificate missing from solved problem")
            certificate = hermitian_part(raw_certificate.value)
            effective = contract_program_choi(
                retrieval,
                program,
                self.system_dimension,
                self.program_dimension,
                self.output_dimension,
            )
            difference = effective - target
            worst_psd_violation = max(
                worst_psd_violation,
                -minimum_eigenvalue(certificate),
                -minimum_eigenvalue(certificate + difference),
                -minimum_eigenvalue(certificate - difference),
            )
            trace_certificate = partial_trace_output(
                certificate,
                self.system_dimension,
                self.output_dimension,
            )
            worst_trace_violation = max(
                worst_trace_violation,
                float(
                    np.max(
                        np.linalg.eigvalsh(
                            hermitian_part(
                                trace_certificate
                                - 2.0 * float(epsilon) * np.eye(self.system_dimension)
                            )
                        )
                    ).real
                ),
            )
        stats = self.problem.solver_stats
        return ProgrammingCostSolution(
            epsilon=float(epsilon),
            kappa=kappa,
            gamma_log2=float(math.log2(max(kappa, np.finfo(float).tiny))),
            p_plus=p_plus,
            p_minus=p_minus,
            status=str(self.problem.status),
            solver=str(stats.solver_name),
            solve_time_seconds=float(elapsed),
            setup_time_seconds=(
                float(stats.setup_time) if stats.setup_time is not None else None
            ),
            solver_time_seconds=(
                float(stats.solve_time) if stats.solve_time is not None else None
            ),
            iterations=int(stats.num_iters) if stats.num_iters is not None else None,
            trace_residual=float(trace_residual),
            signed_weight_residual=float(abs((p_plus - p_minus) - 1.0)),
            minimum_eigenvalue_plus=minimum_eigenvalue(plus),
            minimum_eigenvalue_minus=minimum_eigenvalue(minus),
            worst_diamond_psd_violation=float(max(0.0, worst_psd_violation)),
            worst_diamond_trace_violation=float(max(0.0, worst_trace_violation)),
            retrieval_choi=retrieval,
        )
