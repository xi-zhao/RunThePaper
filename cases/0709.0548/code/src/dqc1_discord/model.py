"""Scientific core for Datta--Shaji--Caves, PRL 100, 050502 (2008)."""

from __future__ import annotations

import numpy as np
from scipy.linalg import schur


def binary_entropy(probability: float | np.ndarray) -> float | np.ndarray:
    p = np.asarray(probability, dtype=float)
    safe = np.clip(p, 1e-300, 1.0 - 1e-16)
    value = -safe * np.log2(safe) - (1.0 - safe) * np.log2(1.0 - safe)
    value = np.where((p <= 0.0) | (p >= 1.0), 0.0, value)
    return float(value) if value.ndim == 0 else value


def entropy_probabilities(probabilities: np.ndarray, axis: int = -1) -> np.ndarray:
    p = np.asarray(probabilities, dtype=float)
    terms = np.where(p > 0.0, -p * np.log2(np.clip(p, 1e-300, None)), 0.0)
    return np.sum(terms, axis=axis)


def entropy_density(matrix: np.ndarray) -> float:
    eigenvalues = np.linalg.eigvalsh((matrix + matrix.conj().T) / 2.0)
    return float(entropy_probabilities(np.clip(eigenvalues, 0.0, None)))


def haar_unitary(dimension: int, rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    q, r = np.linalg.qr(matrix)
    phases = np.diag(r)
    phases = np.where(np.abs(phases) > 0.0, phases / np.abs(phases), 1.0)
    return q @ np.diag(phases.conj())


def haar_su2(rng: np.random.Generator) -> np.ndarray:
    """Draw one Haar SU(2) gate from a normalized real quaternion."""

    quaternion = rng.normal(size=4)
    quaternion /= np.linalg.norm(quaternion)
    a, b, c, d = quaternion
    return np.asarray(
        [[a + 1j * b, c + 1j * d], [-c + 1j * d, a - 1j * b]],
        dtype=complex,
    )


def brickwork_pseudorandom_unitary(
    qubits: int,
    depth: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Transparent local random-circuit proxy for the unpublished generator.

    Each layer applies independent Haar SU(2) gates followed by alternating
    nearest-neighbour controlled-Z gates.  The paper does not publish its
    finite pseudo-random circuit, so this implementation is intentionally
    labeled as an independent convergence probe rather than author code.
    """

    if qubits < 1 or depth < 1:
        raise ValueError("qubits and depth must be positive")
    dimension = 2**qubits
    unitary = np.eye(dimension, dtype=complex)
    basis = np.arange(dimension, dtype=np.uint64)
    for layer in range(depth):
        local = np.asarray([[1.0 + 0.0j]])
        for _ in range(qubits):
            local = np.kron(local, haar_su2(rng))
        unitary = local @ unitary
        phase = np.ones(dimension, dtype=complex)
        for first in range(layer % 2, qubits - 1, 2):
            left = qubits - 1 - first
            right = qubits - 2 - first
            both_one = ((basis >> left) & 1) & ((basis >> right) & 1)
            phase[both_one.astype(bool)] *= -1.0
        unitary = phase[:, None] * unitary
    return unitary


def dqc1_state(unitary: np.ndarray, alpha: float) -> np.ndarray:
    dimension = unitary.shape[0]
    identity = np.eye(dimension, dtype=complex)
    return np.block(
        [[identity, alpha * unitary.conj().T], [alpha * unitary, identity]]
    ) / (2.0 * dimension)


def unitary_power(unitary: np.ndarray, exponent: float) -> np.ndarray:
    """Return a continuous spectral power of a unitary matrix."""

    triangular, vectors = schur(unitary, output="complex")
    off_diagonal = triangular - np.diag(np.diag(triangular))
    if np.linalg.norm(off_diagonal) > 1.0e-9:
        raise ValueError("input is not numerically normal/unitary")
    phases = np.angle(np.diag(triangular))
    return vectors @ np.diag(np.exp(1j * exponent * phases)) @ vectors.conj().T


def dqc1_separable_reconstruction(
    unitary: np.ndarray,
    alpha: float,
) -> tuple[np.ndarray, float, float]:
    """Construct the control-register product mixture in the U eigenbasis.

    For ``U|u_k>=exp(i theta_k)|u_k>`` the DQC1 state is exactly the uniform
    mixture of ``rho_control(theta_k) tensor |u_k><u_k|``.  The returned
    residual and smallest factor eigenvalue certify separability directly;
    no PPT-sufficiency assumption is used.
    """

    triangular, vectors = schur(unitary, output="complex")
    off_diagonal = triangular - np.diag(np.diag(triangular))
    if np.linalg.norm(off_diagonal) > 1.0e-9:
        raise ValueError("input is not numerically normal/unitary")
    phases = np.angle(np.diag(triangular))
    dimension = unitary.shape[0]
    reconstructed = np.zeros((2 * dimension, 2 * dimension), dtype=complex)
    minimum_factor_eigenvalue = np.inf
    for index, phase in enumerate(phases):
        control = 0.5 * np.asarray(
            [
                [1.0, alpha * np.exp(-1j * phase)],
                [alpha * np.exp(1j * phase), 1.0],
            ],
            dtype=complex,
        )
        register_vector = vectors[:, index]
        register = np.outer(register_vector, register_vector.conj())
        reconstructed += np.kron(control, register) / dimension
        minimum_factor_eigenvalue = min(
            minimum_factor_eigenvalue,
            float(np.linalg.eigvalsh(control).min()),
            float(np.linalg.eigvalsh(register).min()),
        )
    target = dqc1_state(unitary, alpha)
    residual = float(np.linalg.norm(reconstructed - target, ord="fro"))
    return reconstructed, residual, float(minimum_factor_eigenvalue)


def partial_transpose_control(matrix: np.ndarray) -> np.ndarray:
    dimension = matrix.shape[0] // 2
    tensor = matrix.reshape(2, dimension, 2, dimension)
    return tensor.transpose(2, 1, 0, 3).reshape(2 * dimension, 2 * dimension)


def partial_transpose(
    matrix: np.ndarray,
    dimensions: tuple[int, ...],
    subsystems: tuple[int, ...],
) -> np.ndarray:
    """Partial transpose arbitrary subsystems of a multipartite state."""

    total = int(np.prod(dimensions))
    if matrix.shape != (total, total):
        raise ValueError("matrix shape does not match subsystem dimensions")
    if any(index < 0 or index >= len(dimensions) for index in subsystems):
        raise ValueError("partial-transpose subsystem index out of range")
    tensor = matrix.reshape(*dimensions, *dimensions)
    axes = list(range(2 * len(dimensions)))
    for index in set(subsystems):
        axes[index], axes[len(dimensions) + index] = (
            axes[len(dimensions) + index],
            axes[index],
        )
    return tensor.transpose(axes).reshape(total, total)


def negativity(
    matrix: np.ndarray,
    dimensions: tuple[int, ...],
    subsystems: tuple[int, ...],
) -> float:
    """Return the trace-norm negativity for an arbitrary bipartition."""

    transposed = partial_transpose(matrix, dimensions, subsystems)
    eigenvalues = np.linalg.eigvalsh((transposed + transposed.conj().T) / 2.0)
    return float(np.sum(np.maximum(-eigenvalues, 0.0)))


def realignment_trace_norm(
    matrix: np.ndarray,
    dimensions: tuple[int, ...],
    first_group: tuple[int, ...],
) -> float:
    """Return the computable cross-norm for a declared bipartition.

    A separable state has realignment trace norm at most one.  The criterion is
    only a one-sided entanglement witness; a value below one must never be
    reported as a separability proof.
    """

    subsystem_count = len(dimensions)
    first = tuple(dict.fromkeys(first_group))
    if not first or len(first) == subsystem_count:
        raise ValueError("the bipartition must have two non-empty groups")
    if any(index < 0 or index >= subsystem_count for index in first):
        raise ValueError("realignment subsystem index out of range")
    second = tuple(index for index in range(subsystem_count) if index not in first)
    total = int(np.prod(dimensions))
    if matrix.shape != (total, total):
        raise ValueError("matrix shape does not match subsystem dimensions")

    tensor = matrix.reshape(*dimensions, *dimensions)
    row_axes = list(first) + list(second)
    column_axes = [subsystem_count + index for index in first] + [
        subsystem_count + index for index in second
    ]
    reordered = tensor.transpose(row_axes + column_axes)
    first_dimension = int(np.prod([dimensions[index] for index in first]))
    second_dimension = total // first_dimension
    bipartite = reordered.reshape(
        first_dimension,
        second_dimension,
        first_dimension,
        second_dimension,
    )
    realigned = bipartite.transpose(0, 2, 1, 3).reshape(
        first_dimension**2,
        second_dimension**2,
    )
    return float(np.linalg.svd(realigned, compute_uv=False).sum())


def first_symmetric_extension_contract(
    first_dimension: int,
    second_dimension: int,
) -> dict[str, int | str]:
    """Describe the first Doherty symmetric-extension SDP without solving it.

    The paper cites an external unpublished calculation but supplies neither a
    solver nor certificates.  This contract fixes the exact matrix dimensions
    and constraints needed by an independent SDP implementation, while keeping
    the current evidence honest when no PSD-cone solver is installed.
    """

    if first_dimension < 2 or second_dimension < 2:
        raise ValueError("both bipartite dimensions must be at least two")
    extension_dimension = first_dimension * second_dimension**2
    return {
        "first_dimension": first_dimension,
        "second_dimension": second_dimension,
        "extension_dimension": extension_dimension,
        "hermitian_variable_real_parameters": extension_dimension**2,
        "constraint": (
            "find X>=0 on A tensor B tensor B' with swap_BB'(X)=X "
            "and Tr_B'(X)=rho_AB"
        ),
        "status": "code_ready_solver_unavailable",
    }


def negativity_control(matrix: np.ndarray) -> float:
    eigenvalues = np.linalg.eigvalsh(partial_transpose_control(matrix))
    return float(np.sum(np.maximum(-eigenvalues, 0.0)))


def analytic_typical_discord(alpha: float | np.ndarray) -> float | np.ndarray:
    a = np.asarray(alpha, dtype=float)
    root = np.sqrt(np.maximum(0.0, 1.0 - a * a))
    value = (
        2.0
        - binary_entropy((1.0 - a) / 2.0)
        - np.log2(1.0 + root)
        - (1.0 - root) * np.log2(np.e)
    )
    return float(value) if value.ndim == 0 else value


def discord_from_eigenphases(
    eigenphases: np.ndarray, alpha: float, phi_grid_points: int = 257
) -> tuple[float, float]:
    phases = np.asarray(eigenphases, dtype=float)
    dimension = phases.size
    tau = np.mean(np.exp(1j * phases))
    phis = np.linspace(0.0, np.pi, phi_grid_points, endpoint=False)
    cosine = np.cos(phases[:, None] - phis[None, :])
    projection = tau.real * np.cos(phis) + tau.imag * np.sin(phis)
    p_plus = 0.5 * (1.0 + alpha * projection)
    p_minus = 1.0 - p_plus
    q_plus = (1.0 + alpha * cosine) / (dimension * (1.0 + alpha * projection)[None, :])
    q_minus = (1.0 - alpha * cosine) / (dimension * (1.0 - alpha * projection)[None, :])
    conditional = p_plus * entropy_probabilities(
        q_plus, axis=0
    ) + p_minus * entropy_probabilities(q_minus, axis=0)
    index = int(np.argmin(conditional))
    joint = np.log2(dimension) + binary_entropy((1.0 - alpha) / 2.0)
    control = binary_entropy((1.0 - alpha * abs(tau)) / 2.0)
    return float(control - joint + conditional[index]), float(phis[index])


def discord_at_phi(
    eigenphases: np.ndarray,
    alpha: float,
    phi: float,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Evaluate the DQC1 discord functional at one declared measurement angle."""

    phases = np.asarray(eigenphases, dtype=float)
    dimension = phases.size
    tau = np.mean(np.exp(1j * phases))
    cosine = np.cos(phases - phi)
    projection = tau.real * np.cos(phi) + tau.imag * np.sin(phi)
    p_plus = 0.5 * (1.0 + alpha * projection)
    p_minus = 1.0 - p_plus
    q_plus = (1.0 + alpha * cosine) / (dimension * (1.0 + alpha * projection))
    q_minus = (1.0 - alpha * cosine) / (dimension * (1.0 - alpha * projection))
    conditional = float(
        p_plus * entropy_probabilities(q_plus)
        + p_minus * entropy_probabilities(q_minus)
    )
    joint = np.log2(dimension) + binary_entropy((1.0 - alpha) / 2.0)
    control = binary_entropy((1.0 - alpha * abs(tau)) / 2.0)
    return float(control - joint + conditional), conditional, q_plus, q_minus


def eigenphase_spacing_statistics(eigenphases: np.ndarray) -> dict[str, float]:
    """Measure departure from an exactly equally spaced root grid."""

    phases = np.sort(np.mod(np.asarray(eigenphases, dtype=float), 2.0 * np.pi))
    gaps = np.diff(np.concatenate([phases, phases[:1] + 2.0 * np.pi]))
    ideal = 2.0 * np.pi / len(phases)
    return {
        "gap_mean": float(np.mean(gaps)),
        "gap_std": float(np.std(gaps)),
        "gap_max_absolute_deviation": float(np.max(np.abs(gaps - ideal))),
        "gap_relative_rms": float(np.sqrt(np.mean((gaps / ideal - 1.0) ** 2))),
    }


def separable_example_state() -> np.ndarray:
    zero = np.array([1.0, 0.0], dtype=complex)
    one = np.array([0.0, 1.0], dtype=complex)
    plus = (zero + one) / np.sqrt(2.0)
    minus = (zero - one) / np.sqrt(2.0)

    def projector(vector: np.ndarray) -> np.ndarray:
        return np.outer(vector, vector.conj())

    terms = [
        np.kron(projector(plus), projector(zero)),
        np.kron(projector(minus), projector(one)),
        np.kron(projector(zero), projector(minus)),
        np.kron(projector(one), projector(plus)),
    ]
    return sum(terms) / 4.0


def _partial_trace_second(matrix: np.ndarray) -> np.ndarray:
    return np.trace(matrix.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def _partial_trace_first(matrix: np.ndarray) -> np.ndarray:
    return np.trace(matrix.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def two_qubit_discord_second(
    matrix: np.ndarray, theta_points: int = 61, phi_points: int = 121
) -> tuple[float, tuple[float, float]]:
    joint_entropy = entropy_density(matrix)
    first_entropy = entropy_density(_partial_trace_second(matrix))
    second_entropy = entropy_density(_partial_trace_first(matrix))
    mutual = first_entropy + second_entropy - joint_entropy
    identity = np.eye(2, dtype=complex)
    pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
    pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)
    best = (np.inf, 0.0, 0.0)
    for theta in np.linspace(0.0, np.pi, theta_points):
        for phi in np.linspace(0.0, 2.0 * np.pi, phi_points, endpoint=False):
            direction = (
                np.sin(theta) * np.cos(phi) * pauli_x
                + np.sin(theta) * np.sin(phi) * pauli_y
                + np.cos(theta) * pauli_z
            )
            conditional = 0.0
            for sign in (-1.0, 1.0):
                projector = (identity + sign * direction) / 2.0
                measurement = np.kron(identity, projector)
                post = measurement @ matrix @ measurement
                probability = float(np.trace(post).real)
                if probability > 1e-15:
                    conditional += probability * entropy_density(
                        _partial_trace_second(post) / probability
                    )
            if conditional < best[0]:
                best = (conditional, theta, phi)
    classical = first_entropy - best[0]
    return float(mutual - classical), (best[1], best[2])


def foundational_information_audit() -> dict[str, float]:
    """Independently exercise the paper's information-theory foundation.

    The paper uses these identities before specializing to DQC1.  Keeping one
    compact audit here prevents broad prose claims from being silently covered
    by a single Eq. (1) example.
    """

    joint_probabilities = np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=float)
    row_probabilities = joint_probabilities.sum(axis=1)
    column_probabilities = joint_probabilities.sum(axis=0)
    mutual_direct = float(
        entropy_probabilities(row_probabilities)
        + entropy_probabilities(column_probabilities)
        - entropy_probabilities(joint_probabilities.ravel())
    )
    conditional_classical = float(
        sum(
            column_probabilities[index]
            * entropy_probabilities(
                joint_probabilities[:, index] / column_probabilities[index]
            )
            for index in range(2)
        )
    )
    mutual_conditional = float(
        entropy_probabilities(row_probabilities) - conditional_classical
    )

    probability_vector = np.asarray([0.2, 0.3, 0.5])
    probability_matrix = np.diag(probability_vector.astype(complex))
    shannon_von_neumann_error = abs(
        float(entropy_probabilities(probability_vector))
        - entropy_density(probability_matrix)
    )

    identity = np.eye(2, dtype=complex)
    projectors = (
        np.diag([1.0, 0.0]).astype(complex),
        np.diag([0.0, 1.0]).astype(complex),
    )
    example = separable_example_state()
    probabilities: list[float] = []
    conditional_states: list[np.ndarray] = []
    nonselective = np.zeros_like(example)
    for projector in projectors:
        measurement = np.kron(identity, projector)
        post = measurement @ example @ measurement
        probability = float(np.trace(post).real)
        probabilities.append(probability)
        conditional_states.append(_partial_trace_second(post) / probability)
        nonselective += post
    conditional_entropy = float(
        sum(
            probability * entropy_density(state)
            for probability, state in zip(
                probabilities, conditional_states, strict=True
            )
        )
    )
    first_entropy = entropy_density(_partial_trace_second(example))
    projected_discord, _ = two_qubit_discord_second(
        nonselective, theta_points=31, phi_points=61
    )

    zero = np.asarray([1.0, 0.0], dtype=complex)
    one = np.asarray([0.0, 1.0], dtype=complex)
    bell = (np.kron(zero, zero) + np.kron(one, one)) / np.sqrt(2.0)
    bell_state = np.outer(bell, bell.conj())
    classical_state = np.diag([0.1, 0.2, 0.3, 0.4]).astype(complex)
    test_states = (classical_state, example, bell_state)
    discords = [
        two_qubit_discord_second(state, theta_points=31, phi_points=61)[0]
        for state in test_states
    ]
    marginal_entropies = [
        entropy_density(_partial_trace_first(state)) for state in test_states
    ]

    pure_joint_error = 0.0
    pure_marginal_error = 0.0
    pure_discord_error = 0.0
    for schmidt_probability in (0.13, 0.37, 0.71):
        vector = np.asarray(
            [
                np.sqrt(schmidt_probability),
                0.0,
                0.0,
                np.sqrt(1.0 - schmidt_probability),
            ],
            dtype=complex,
        )
        state = np.outer(vector, vector.conj())
        first = entropy_density(_partial_trace_second(state))
        second = entropy_density(_partial_trace_first(state))
        discord, _ = two_qubit_discord_second(state, theta_points=31, phi_points=61)
        pure_joint_error = max(pure_joint_error, entropy_density(state))
        pure_marginal_error = max(pure_marginal_error, abs(first - second))
        pure_discord_error = max(pure_discord_error, abs(discord - second))

    return {
        "classical_mutual_information_identity_error": abs(
            mutual_direct - mutual_conditional
        ),
        "shannon_von_neumann_entropy_error": shannon_von_neumann_error,
        "measurement_probability_sum_error": abs(sum(probabilities) - 1.0),
        "conditional_state_trace_error": max(
            abs(float(np.trace(state).real) - 1.0) for state in conditional_states
        ),
        "conditional_entropy_nonnegative_margin": conditional_entropy,
        "conditional_entropy_upper_bound_margin": first_entropy - conditional_entropy,
        "post_measurement_discord": projected_discord,
        "minimum_test_discord": min(discords),
        "maximum_discord_upper_bound_excess": max(
            discord - marginal
            for discord, marginal in zip(discords, marginal_entropies, strict=True)
        ),
        "pure_joint_entropy_max": pure_joint_error,
        "pure_marginal_entropy_error": pure_marginal_error,
        "pure_discord_entanglement_error": pure_discord_error,
    }


def dqc1_sampling_bound(alpha: float, rms_error: float) -> dict[str, float | int]:
    """Return the fixed-accuracy DQC1 shot bound from control readout noise.

    A Pauli control measurement has variance at most one.  Because the
    normalized trace is obtained by dividing its expectation value by the
    control polarization ``alpha``, the estimator variance is bounded by
    ``1 / (shots * alpha**2)``.  Requiring RMS error ``epsilon`` therefore
    needs ``ceil(1 / (alpha**2 * epsilon**2))`` shots.  The bound contains no
    register-size dependence and makes the paper's ``1/alpha**2`` overhead
    explicit without importing an external complexity implementation.
    """

    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must lie in (0, 1]")
    if rms_error <= 0.0:
        raise ValueError("rms_error must be positive")
    shots = int(np.ceil(1.0 / (alpha**2 * rms_error**2)))
    return {
        "alpha": float(alpha),
        "rms_error": float(rms_error),
        "shots": shots,
        "variance_bound": float(1.0 / (shots * alpha**2)),
        "overhead_vs_alpha_one": float(1.0 / alpha**2),
    }
