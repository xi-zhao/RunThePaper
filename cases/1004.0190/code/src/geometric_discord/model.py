"""Two-qubit Bloch tensors, discord witnesses, and DQC1 states."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULI = (X, Y, Z)
HS_BASIS = tuple(matrix / np.sqrt(2.0) for matrix in (I2, X, Y, Z))


def hermitian_operator_basis(dimension: int) -> tuple[np.ndarray, ...]:
    """Return an orthonormal generalized Gell-Mann basis including identity."""

    if dimension < 2:
        raise ValueError("local dimension must be at least two")
    basis = [np.eye(dimension, dtype=complex) / np.sqrt(dimension)]
    for row in range(dimension):
        for column in range(row + 1, dimension):
            symmetric = np.zeros((dimension, dimension), dtype=complex)
            symmetric[row, column] = symmetric[column, row] = 1.0 / np.sqrt(2.0)
            antisymmetric = np.zeros((dimension, dimension), dtype=complex)
            antisymmetric[row, column] = -1.0j / np.sqrt(2.0)
            antisymmetric[column, row] = 1.0j / np.sqrt(2.0)
            basis.extend((symmetric, antisymmetric))
    for level in range(1, dimension):
        diagonal = np.zeros(dimension)
        diagonal[:level] = 1.0
        diagonal[level] = -float(level)
        diagonal /= np.sqrt(level * (level + 1.0))
        basis.append(np.diag(diagonal).astype(complex))
    return tuple(basis)


def random_density_matrix(rng: np.random.Generator, dimension: int = 4) -> np.ndarray:
    matrix = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    rho = matrix @ matrix.conj().T
    return rho / np.trace(rho)


def random_unitary(rng: np.random.Generator, dimension: int) -> np.ndarray:
    matrix = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    q, r = np.linalg.qr(matrix)
    diagonal = np.diag(r)
    phases = np.where(abs(diagonal) > 0.0, diagonal.conj() / abs(diagonal), 1.0)
    return q @ np.diag(phases)


def bloch_parameters(rho: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rho = np.asarray(rho, dtype=complex).reshape(4, 4)
    x = np.array([np.trace(rho @ np.kron(sigma, I2)).real for sigma in PAULI])
    y = np.array([np.trace(rho @ np.kron(I2, sigma)).real for sigma in PAULI])
    tensor = np.array(
        [
            [np.trace(rho @ np.kron(left, right)).real for right in PAULI]
            for left in PAULI
        ]
    )
    return x, y, tensor


def geometric_discord(rho: np.ndarray) -> float:
    x, _, tensor = bloch_parameters(rho)
    k_matrix = np.outer(x, x) + tensor @ tensor.T
    return float(
        (np.dot(x, x) + np.sum(tensor**2) - np.linalg.eigvalsh(k_matrix)[-1]) / 4.0
    )


def dephase_a(rho: np.ndarray, direction: np.ndarray) -> np.ndarray:
    direction = np.asarray(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    observable = sum(direction[index] * PAULI[index] for index in range(3))
    plus = (I2 + observable) / 2.0
    minus = (I2 - observable) / 2.0
    return sum(
        np.kron(projector, I2) @ rho @ np.kron(projector, I2)
        for projector in (plus, minus)
    )


def geometric_discord_direct(rho: np.ndarray) -> tuple[float, np.ndarray]:
    def objective(angles: np.ndarray) -> float:
        theta, phi = angles
        direction = np.array(
            [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
        )
        delta = rho - dephase_a(rho, direction)
        return float(np.trace(delta @ delta).real)

    best = None
    for start in ((0.2, 0.2), (np.pi / 2, 0.0), (np.pi / 2, np.pi / 2), (2.2, 4.0)):
        result = minimize(
            objective,
            np.array(start),
            method="Nelder-Mead",
            options={"xatol": 1e-12, "fatol": 1e-14, "maxiter": 2000},
        )
        if best is None or result.fun < best.fun:
            best = result
    theta, phi = best.x
    direction = np.array(
        [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)]
    )
    return float(best.fun), direction


def operator_schmidt_left_operators(
    rho: np.ndarray,
    subsystem_dimensions: tuple[int, ...] | list[int],
    measured_subsystem: int,
    schmidt_singular_tolerance: float = 1e-12,
) -> tuple[tuple[np.ndarray, ...], np.ndarray]:
    """Return the left Schmidt operators for one subsystem versus the rest."""

    dimensions = tuple(int(value) for value in subsystem_dimensions)
    if any(value < 2 for value in dimensions):
        raise ValueError("all subsystem dimensions must be at least two")
    if measured_subsystem < 0 or measured_subsystem >= len(dimensions):
        raise ValueError("measured subsystem index is out of range")
    rho = np.asarray(rho, dtype=complex)
    total_dimension = int(np.prod(dimensions))
    if rho.shape != (total_dimension, total_dimension):
        raise ValueError("rho shape does not match subsystem dimensions")
    others = [index for index in range(len(dimensions)) if index != measured_subsystem]
    axes = (
        [measured_subsystem]
        + others
        + [len(dimensions) + measured_subsystem]
        + [len(dimensions) + index for index in others]
    )
    dimension_a = dimensions[measured_subsystem]
    dimension_b = total_dimension // dimension_a
    tensor = rho.reshape(dimensions + dimensions).transpose(axes)
    tensor = tensor.reshape(dimension_a, dimension_b, dimension_a, dimension_b)
    local_basis = hermitian_operator_basis(dimension_a)
    right_operators = []
    for left in local_basis:
        right_operators.append(
            sum(
                left[column, row] * tensor[row, :, column, :]
                for row in range(dimension_a)
                for column in range(dimension_a)
            )
        )
    # Work with Schmidt singular values directly.  Diagonalizing the Gram
    # matrix squares the condition number and can discard a real O(delta)
    # Schmidt component as O(delta**2) roundoff.  That is fatal here because
    # the paper's zero-discord criterion is an exact rank/commutation test.
    coefficient_matrix = np.stack(
        [operator.reshape(-1) for operator in right_operators], axis=0
    )
    left_vectors, singular_values, _ = np.linalg.svd(
        coefficient_matrix, full_matrices=False
    )
    numeric_floor = (
        np.finfo(float).eps
        * max(coefficient_matrix.shape)
        * max(1.0, float(singular_values[0]))
        * 8.0
    )
    singular_threshold = max(schmidt_singular_tolerance, numeric_floor)
    rank = int(np.sum(singular_values > singular_threshold))
    operators = tuple(
        sum(left_vectors[mu, index] * local_basis[mu] for mu in range(dimension_a**2))
        for index in range(rank)
    )
    return operators, singular_values[:rank]


def multipartite_discord_criterion(
    rho: np.ndarray,
    subsystem_dimensions: tuple[int, ...] | list[int],
    schmidt_singular_tolerance: float = 1e-12,
    commutator_tolerance: float = 1e-10,
) -> list[dict[str, float | int | bool]]:
    """Apply the paper's commuting-operator criterion to every subsystem."""

    diagnostics = []
    for subsystem in range(len(subsystem_dimensions)):
        operators, _ = operator_schmidt_left_operators(
            rho, subsystem_dimensions, subsystem, schmidt_singular_tolerance
        )
        norm = 0.0
        for first in range(len(operators)):
            for second in range(first + 1, len(operators)):
                commutator = (
                    operators[first] @ operators[second]
                    - operators[second] @ operators[first]
                )
                norm = max(norm, float(np.linalg.norm(commutator)))
        local_dimension = int(subsystem_dimensions[subsystem])
        diagnostics.append(
            {
                "subsystem": subsystem,
                "local_dimension": local_dimension,
                "operator_schmidt_rank": len(operators),
                "commutator_pairs": len(operators) * (len(operators) - 1) // 2,
                "max_commutator_norm": norm,
                "zero_discord": norm <= commutator_tolerance,
                "rank_witness_nonzero": len(operators) > local_dimension,
            }
        )
    return diagnostics


def operator_schmidt_commutator_norm(
    rho: np.ndarray,
    schmidt_singular_tolerance: float = 1e-12,
    commutator_tolerance: float = 1e-10,
) -> tuple[float, int]:
    rho = np.asarray(rho, dtype=complex)
    if rho.shape[0] != rho.shape[1] or rho.shape[0] % 2:
        raise ValueError("rho must describe a 2 x d bipartite state")
    diagnostics = multipartite_discord_criterion(
        rho,
        (2, rho.shape[0] // 2),
        schmidt_singular_tolerance,
        commutator_tolerance,
    )[0]
    return (
        float(diagnostics["max_commutator_norm"]),
        int(diagnostics["operator_schmidt_rank"]),
    )


def local_basis_optimization_dimension(
    subsystem_dimensions: tuple[int, ...] | list[int],
    measured_subsystems: tuple[int, ...] | list[int] | None = None,
) -> int:
    """Dimension of the local projective-basis search manifold."""

    dimensions = tuple(int(value) for value in subsystem_dimensions)
    selected = (
        range(len(dimensions))
        if measured_subsystems is None
        else tuple(int(value) for value in measured_subsystems)
    )
    if any(index < 0 or index >= len(dimensions) for index in selected):
        raise ValueError("measured subsystem index is out of range")
    return int(sum(dimensions[index] ** 2 - dimensions[index] for index in selected))


def local_projective_basis(
    dimension: int, parameters: np.ndarray | tuple[float, ...] | list[float]
) -> np.ndarray:
    """Build a local basis from complex Givens rotations.

    The ``d(d-1)`` real parameters are exactly the dimension of
    ``U(d)/U(1)^d``: one mixing angle and one relative phase for every pair of
    basis vectors.  Column phases are omitted because projectors do not depend
    on them.
    """

    values = np.asarray(parameters, dtype=float)
    expected = dimension * (dimension - 1)
    if values.shape != (expected,):
        raise ValueError(f"expected {expected} local-basis parameters")
    basis = np.eye(dimension, dtype=complex)
    cursor = 0
    for first in range(dimension):
        for second in range(first + 1, dimension):
            theta, phase = values[cursor : cursor + 2]
            cursor += 2
            rotation = np.eye(dimension, dtype=complex)
            cosine = np.cos(theta)
            sine = np.sin(theta)
            phase_factor = np.exp(1.0j * phase)
            rotation[first, first] = cosine
            rotation[second, second] = cosine
            rotation[first, second] = -phase_factor.conjugate() * sine
            rotation[second, first] = phase_factor * sine
            basis = basis @ rotation
    return basis


def projective_dephasing_distance(
    rho: np.ndarray,
    subsystem_dimensions: tuple[int, ...] | list[int],
    local_bases: tuple[np.ndarray, ...] | list[np.ndarray],
    measured_subsystems: tuple[int, ...] | list[int] | None = None,
) -> float:
    """Hilbert--Schmidt distance to dephasing in fixed local bases.

    Measuring one subsystem recovers the paper's bipartite geometric-discord
    objective.  Measuring every subsystem gives the natural fully classical
    multipartite extension.  The closest state for fixed projectors is the
    orthogonal Hilbert--Schmidt projection, so no second state optimization is
    required.
    """

    dimensions = tuple(int(value) for value in subsystem_dimensions)
    if any(value < 2 for value in dimensions):
        raise ValueError("all subsystem dimensions must be at least two")
    total_dimension = int(np.prod(dimensions))
    matrix = np.asarray(rho, dtype=complex)
    if matrix.shape != (total_dimension, total_dimension):
        raise ValueError("rho shape does not match subsystem dimensions")
    if len(local_bases) != len(dimensions):
        raise ValueError("one local basis is required per subsystem")
    selected = (
        tuple(range(len(dimensions)))
        if measured_subsystems is None
        else tuple(int(value) for value in measured_subsystems)
    )
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("measured subsystems must be non-empty and unique")
    if any(index < 0 or index >= len(dimensions) for index in selected):
        raise ValueError("measured subsystem index is out of range")

    product_basis = np.array([[1.0 + 0.0j]])
    for dimension, basis in zip(dimensions, local_bases, strict=True):
        local = np.asarray(basis, dtype=complex)
        if local.shape != (dimension, dimension):
            raise ValueError("local basis shape does not match subsystem dimension")
        if np.linalg.norm(local.conj().T @ local - np.eye(dimension)) > 1e-9:
            raise ValueError("local basis must be unitary")
        product_basis = np.kron(product_basis, local)

    rotated = product_basis.conj().T @ matrix @ product_basis
    labels = np.stack(np.unravel_index(np.arange(total_dimension), dimensions), axis=1)
    kept = np.ones((total_dimension, total_dimension), dtype=bool)
    for subsystem in selected:
        kept &= labels[:, subsystem, None] == labels[None, :, subsystem]
    removed = np.where(kept, 0.0, rotated)
    return float(np.vdot(removed, removed).real)


def multipartite_geometric_discord(
    rho: np.ndarray,
    subsystem_dimensions: tuple[int, ...] | list[int],
    measured_subsystems: tuple[int, ...] | list[int] | None = None,
    *,
    multistarts: int = 8,
    random_seed: int = 0,
    maxiter: int = 2000,
) -> tuple[float, tuple[np.ndarray, ...], dict[str, float | int | bool]]:
    """Minimize projective Hilbert--Schmidt discord over local bases.

    This is a deterministic multistart optimizer over the minimal flag-manifold
    coordinates.  It works for arbitrary finite local dimensions; runtime, not
    the interface, carries the multipartite scaling cost emphasized by the
    paper.
    """

    dimensions = tuple(int(value) for value in subsystem_dimensions)
    selected = (
        tuple(range(len(dimensions)))
        if measured_subsystems is None
        else tuple(int(value) for value in measured_subsystems)
    )
    parameter_counts = [
        dimensions[index] * (dimensions[index] - 1) for index in selected
    ]
    parameter_count = sum(parameter_counts)
    if multistarts < 1:
        raise ValueError("multistarts must be positive")
    if parameter_count == 0:
        raise ValueError("at least one measured subsystem is required")

    def unpack(values: np.ndarray) -> tuple[np.ndarray, ...]:
        bases = [np.eye(dimension, dtype=complex) for dimension in dimensions]
        cursor = 0
        for subsystem, count in zip(selected, parameter_counts, strict=True):
            bases[subsystem] = local_projective_basis(
                dimensions[subsystem], values[cursor : cursor + count]
            )
            cursor += count
        return tuple(bases)

    def objective(values: np.ndarray) -> float:
        return projective_dephasing_distance(
            rho, dimensions, unpack(values), measured_subsystems=selected
        )

    bounds = []
    for count in parameter_counts:
        for _ in range(count // 2):
            bounds.extend(((-np.pi / 2.0, np.pi / 2.0), (-np.pi, np.pi)))
    rng = np.random.default_rng(random_seed)
    starts = [np.zeros(parameter_count)]
    for _ in range(multistarts - 1):
        starts.append(np.array([rng.uniform(lower, upper) for lower, upper in bounds]))

    best = None
    total_evaluations = 0
    for start in starts:
        result = minimize(
            objective,
            start,
            method="Powell",
            bounds=bounds,
            options={"xtol": 1e-10, "ftol": 1e-13, "maxiter": maxiter},
        )
        total_evaluations += int(result.nfev)
        if best is None or result.fun < best.fun:
            best = result
    value = max(0.0, float(best.fun))
    return (
        value,
        unpack(best.x),
        {
            "success": bool(best.success),
            "multistarts": multistarts,
            "parameter_count": parameter_count,
            "function_evaluations": total_evaluations,
            "best_iterations": int(best.nit),
        },
    )


def bell_diagonal_state(t: np.ndarray | tuple[float, float, float]) -> np.ndarray:
    vector = np.asarray(t, dtype=float)
    rho = np.eye(4, dtype=complex)
    for value, sigma in zip(vector, PAULI, strict=True):
        rho += value * np.kron(sigma, sigma)
    return rho / 4.0


def dqc1_state(alpha: float, unitary: np.ndarray) -> np.ndarray:
    dimension = unitary.shape[0]
    upper = alpha * unitary.conj().T
    lower = alpha * unitary
    return np.block([[np.eye(dimension), upper], [lower, np.eye(dimension)]]) / (
        2.0 * dimension
    )


def dqc1_separable_reconstruction(alpha: float, unitary: np.ndarray) -> np.ndarray:
    """Reconstruct the DQC1 output as a control/register separable mixture."""

    eigenvalues, eigenvectors = np.linalg.eig(np.asarray(unitary, dtype=complex))
    dimension = unitary.shape[0]
    reconstructed = np.zeros((2 * dimension, 2 * dimension), dtype=complex)
    for index, eigenvalue in enumerate(eigenvalues):
        vector = eigenvectors[:, index]
        vector /= np.linalg.norm(vector)
        control = (
            np.array(
                [[1.0, alpha * eigenvalue.conjugate()], [alpha * eigenvalue, 1.0]],
                dtype=complex,
            )
            / 2.0
        )
        reconstructed += np.kron(control, np.outer(vector, vector.conj())) / dimension
    return (reconstructed + reconstructed.conj().T) / 2.0


def apply_local_channel(
    rho: np.ndarray,
    kraus_operators: tuple[np.ndarray, ...] | list[np.ndarray],
    subsystem_dimensions: tuple[int, ...] | list[int],
    subsystem: int,
) -> np.ndarray:
    """Apply a trace-preserving local channel to one tensor factor."""

    dimensions = tuple(int(value) for value in subsystem_dimensions)
    if subsystem < 0 or subsystem >= len(dimensions):
        raise ValueError("subsystem index is out of range")
    local_dimension = dimensions[subsystem]
    identity = np.eye(local_dimension, dtype=complex)
    completeness = np.zeros_like(identity)
    result = np.zeros_like(np.asarray(rho, dtype=complex))
    for kraus in kraus_operators:
        kraus = np.asarray(kraus, dtype=complex)
        if kraus.shape != (local_dimension, local_dimension):
            raise ValueError("Kraus operator dimension mismatch")
        completeness += kraus.conj().T @ kraus
        embedded = np.array([[1.0 + 0.0j]])
        for index, dimension in enumerate(dimensions):
            embedded = np.kron(
                embedded,
                kraus if index == subsystem else np.eye(dimension, dtype=complex),
            )
        result += embedded @ rho @ embedded.conj().T
    if np.linalg.norm(completeness - identity) > 1e-10:
        raise ValueError("Kraus operators are not trace preserving")
    return (result + result.conj().T) / 2.0


def dqc1_left_operators(unitary: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    hermitian = (unitary + unitary.conj().T) / 2.0
    antihermitian = (unitary - unitary.conj().T) / (2.0j)
    return hermitian, antihermitian
