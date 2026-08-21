"""Formula-level and independent ensemble checks for two-qubit entanglement."""

from __future__ import annotations

import numpy as np
from scipy.linalg import schur
from scipy.special import gammaln, logsumexp
from scipy.optimize import brentq

SIGMA_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
SPIN_FLIP = np.kron(SIGMA_Y, SIGMA_Y)


def binary_entropy(probability: float) -> float:
    """Binary entropy in bits, including its continuous endpoints."""

    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0, 1]")
    if probability in (0.0, 1.0):
        return 0.0
    return float(
        -probability * np.log2(probability)
        - (1.0 - probability) * np.log2(1.0 - probability)
    )


def typical_subspace_record(
    schmidt_probability: float,
    copies: int,
    *,
    information_tolerance: float,
) -> dict[str, float | int]:
    """Evaluate the finite-copy Schmidt typical set for a pure qubit pair.

    The paper's operational paragraph relies on an external asymptotic
    protocol theorem.  This calculation does not replace that proof; it makes
    its numerical core explicit by enumerating the binomial Schmidt types and
    checking concentration and typical-set dimension without sampling.
    """

    if not 0.0 < schmidt_probability < 1.0:
        raise ValueError("schmidt_probability must lie strictly between 0 and 1")
    if copies < 1:
        raise ValueError("copies must be positive")
    if information_tolerance <= 0.0:
        raise ValueError("information_tolerance must be positive")

    counts = np.arange(copies + 1, dtype=float)
    log_multiplicity = (
        gammaln(copies + 1.0)
        - gammaln(counts + 1.0)
        - gammaln(copies - counts + 1.0)
    )
    log_sequence_probability = (
        counts * np.log(schmidt_probability)
        + (copies - counts) * np.log(1.0 - schmidt_probability)
    )
    entropy = binary_entropy(schmidt_probability)
    information_per_copy = -log_sequence_probability / (copies * np.log(2.0))
    selected = np.abs(information_per_copy - entropy) <= information_tolerance
    if not np.any(selected):
        raise RuntimeError("the configured typical set is empty")
    log_type_probability = log_multiplicity + log_sequence_probability
    mass = float(np.exp(logsumexp(log_type_probability[selected])))
    dimension_rate = float(
        logsumexp(log_multiplicity[selected]) / (copies * np.log(2.0))
    )
    return {
        "schmidt_probability": schmidt_probability,
        "copies": copies,
        "information_tolerance": information_tolerance,
        "entanglement_entropy": entropy,
        "typical_probability_mass": mass,
        "typical_dimension_rate": dimension_rate,
        "rate_minus_entropy": dimension_rate - entropy,
        "selected_binomial_types": int(np.sum(selected)),
    }


def caratheodory_ensemble_bound(hilbert_dimension: int) -> int:
    """Return the d^2 pure-state bound for a d-dimensional density matrix."""

    if hilbert_dimension < 1:
        raise ValueError("hilbert_dimension must be positive")
    return hilbert_dimension * hilbert_dimension


def _hermitian_sqrt(matrix: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh((matrix + matrix.conj().T) / 2.0)
    return (vectors * np.sqrt(np.clip(values, 0.0, None))) @ vectors.conj().T


def spin_flip_state(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=complex).reshape(4)
    return SPIN_FLIP @ state.conj()


def spin_flip_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex).reshape(4, 4)
    return SPIN_FLIP @ rho.conj() @ SPIN_FLIP


def magic_basis() -> np.ndarray:
    """Return a magic basis in which spin flip is coefficient conjugation.

    The common printed magic basis is an eigenbasis of spin flip with a common
    eigenvalue ``-1`` for our computational-basis convention.  Multiplying the
    four vectors by the same phase ``i`` removes that irrelevant common sign
    and makes the anti-linear action exactly coefficient conjugation.
    """

    conventional = np.column_stack(
        [
            np.array([1.0, 0.0, 0.0, 1.0]) / np.sqrt(2.0),
            1.0j * np.array([1.0, 0.0, 0.0, -1.0]) / np.sqrt(2.0),
            1.0j * np.array([0.0, 1.0, 1.0, 0.0]) / np.sqrt(2.0),
            np.array([0.0, 1.0, -1.0, 0.0]) / np.sqrt(2.0),
        ]
    ).astype(complex)
    return 1.0j * conventional


def magic_basis_coordinates(state: np.ndarray) -> np.ndarray:
    return magic_basis().conj().T @ np.asarray(state, dtype=complex).reshape(4)


def partial_trace_b(state: np.ndarray) -> np.ndarray:
    matrix = np.asarray(state, dtype=complex).reshape(2, 2)
    return matrix @ matrix.conj().T


def von_neumann_entropy(rho: np.ndarray) -> float:
    values = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    values = np.clip(values.real, 0.0, 1.0)
    positive = values > 1e-15
    return float(-np.sum(values[positive] * np.log2(values[positive])))


def pure_concurrence(state: np.ndarray) -> float:
    state = np.asarray(state, dtype=complex).reshape(4)
    norm = np.linalg.norm(state)
    if norm == 0.0:
        return 0.0
    state = state / norm
    return float(abs(np.vdot(state, spin_flip_state(state))))


def pure_entanglement(state: np.ndarray) -> float:
    state = np.asarray(state, dtype=complex).reshape(4)
    state = state / np.linalg.norm(state)
    return von_neumann_entropy(partial_trace_b(state))


def entanglement_from_concurrence(value: float | np.ndarray) -> float | np.ndarray:
    concurrence_value = np.clip(np.asarray(value, dtype=float), 0.0, 1.0)
    probability = (1.0 + np.sqrt(np.maximum(0.0, 1.0 - concurrence_value**2))) / 2.0
    complement = 1.0 - probability
    result = np.zeros_like(probability)
    mask = (probability > 0.0) & (probability < 1.0)
    result[mask] = -probability[mask] * np.log2(probability[mask])
    mask = (complement > 0.0) & (complement < 1.0)
    result[mask] -= complement[mask] * np.log2(complement[mask])
    if result.ndim == 0:
        return float(result)
    return result


def concurrence_spectrum(rho: np.ndarray) -> np.ndarray:
    """Return the four ``lambda_i`` using the proof's symmetric tau matrix.

    This is algebraically equivalent to diagonalizing Wootters's Hermitian
    ``R`` but is substantially more stable for rank-deficient states: it avoids
    taking two nested matrix square roots near exact zero eigenvalues.
    """

    rho = np.asarray(rho, dtype=complex).reshape(4, 4)
    values, vectors = np.linalg.eigh((rho + rho.conj().T) / 2.0)
    keep = values > 1e-13
    eigenensemble = vectors[:, keep] * np.sqrt(values[keep])
    tau = eigenensemble.conj().T @ SPIN_FLIP @ eigenensemble.conj()
    singular_values = np.linalg.svd(tau, compute_uv=False)
    return np.pad(
        np.sort(np.clip(singular_values.real, 0.0, None))[::-1],
        (0, 4 - len(singular_values)),
    )


def concurrence(rho: np.ndarray) -> float:
    values = concurrence_spectrum(rho)
    return float(max(0.0, values[0] - np.sum(values[1:])))


def _subnormalized_eigenensemble(
    rho: np.ndarray, tolerance: float = 1e-13
) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex).reshape(4, 4)
    values, vectors = np.linalg.eigh((rho + rho.conj().T) / 2.0)
    keep = values > tolerance
    return vectors[:, keep] * np.sqrt(values[keep])


def takagi_factorization_symmetric(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``U, s`` with ``U @ matrix @ U.T == diag(s)``.

    Start from a complex SVD ``A=L S R^H``.  Symmetry implies that
    ``C=R^H conj(L)`` is a symmetric unitary inside each degenerate singular
    subspace.  A unitary square root ``Q`` of each such block gives Takagi
    vectors ``W=LQ``.  This phase-refinement route keeps exact and near-zero
    modes in the same complex inner product; the real-augmented eigenproblem
    does not and becomes non-orthogonal when O(1) and O(1e-12) modes coexist.
    """

    matrix = np.asarray(matrix, dtype=complex)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Takagi factorization requires a square matrix")
    if np.linalg.norm(matrix - matrix.T) > 1e-9:
        raise ValueError("Takagi factorization requires a complex-symmetric matrix")
    size = matrix.shape[0]
    left, singular_values, right_h = np.linalg.svd(matrix)
    scale = max(1.0, float(singular_values[0]) if size else 0.0)
    degeneracy_tolerance = 1024.0 * np.finfo(float).eps * size * scale
    near_null_tolerance = 1e-10 * scale
    phase_relation = right_h @ left.conj()
    refinement = np.zeros((size, size), dtype=complex)

    start = 0
    while start < size:
        if singular_values[start] <= near_null_tolerance:
            stop = size
        else:
            stop = start + 1
            while (
                stop < size
                and abs(singular_values[stop] - singular_values[start])
                <= degeneracy_tolerance
            ):
                stop += 1
        indices = np.arange(start, stop)
        block = phase_relation[np.ix_(indices, indices)]

        # The exact phase relation is symmetric unitary.  Remove only its
        # antisymmetric roundoff *before* the Schur solve; polarizing an SVD of
        # a degenerate -I block can otherwise choose an arbitrary real
        # rotation whose transpose square has the wrong sign.
        symmetric_block = 0.5 * (block + block.T)
        triangular, schur_vectors = schur(symmetric_block, output="complex")
        phases = np.diag(triangular)
        phases = np.divide(
            phases,
            np.abs(phases),
            out=np.ones_like(phases),
            where=np.abs(phases) > 0.0,
        )
        root = (
            schur_vectors
            @ np.diag(np.sqrt(phases))
            @ schur_vectors.conj().T
        )
        refinement[np.ix_(indices, indices)] = root
        start = stop

    vectors = left @ refinement
    if np.linalg.norm(vectors.conj().T @ vectors - np.eye(size)) > 1e-10:
        raise RuntimeError("Takagi vectors are not unitary")
    unitary = vectors.conj().T
    diagonal = unitary @ matrix @ unitary.T
    residual = np.linalg.norm(diagonal - np.diag(np.diag(diagonal)))
    if residual > 1e-10 * scale:
        raise RuntimeError("Takagi off-diagonal residual exceeds tolerance")
    values = np.clip(np.real(np.diag(diagonal)), 0.0, None)
    if np.max(np.abs(np.imag(np.diag(diagonal))), initial=0.0) > 1e-10 * scale:
        raise RuntimeError("Takagi diagonal is not real")
    return unitary, values


def tilde_orthogonal_decomposition(rho: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Construct Wootters's tilde-orthogonal subnormalized states ``x_i``."""

    eigenensemble = _subnormalized_eigenensemble(rho)
    tau = eigenensemble.conj().T @ SPIN_FLIP @ eigenensemble.conj()
    unitary, lambdas = takagi_factorization_symmetric(tau)
    states = eigenensemble @ unitary.conj().T
    overlaps = states.conj().T @ SPIN_FLIP @ states.conj()
    if np.linalg.norm(overlaps - np.diag(lambdas)) > 2e-9:
        raise RuntimeError("tilde-orthogonal construction did not diagonalize overlaps")
    return states, lambdas


def subnormalized_preconcurrence(state: np.ndarray) -> float:
    state = np.asarray(state, dtype=complex).reshape(4)
    weight = float(np.vdot(state, state).real)
    if weight <= 1e-15:
        return 0.0
    return float(np.vdot(state, spin_flip_state(state)).real / weight)


def signed_preconcurrence_decomposition(
    rho: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the printed ``x_1, i x_2, i x_3, i x_4`` sign convention."""

    states, lambdas = tilde_orthogonal_decomposition(rho)
    signed = states.copy()
    if signed.shape[1] > 1:
        signed[:, 1:] *= 1.0j
    signs = np.ones(len(lambdas))
    signs[1:] = -1.0
    return signed, signs * lambdas


def equal_preconcurrence_decomposition(
    rho: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Construct the positive-branch optimal ensemble by real rotations.

    At every step, the largest and smallest remaining preconcurrences bracket
    ``C(rho)``.  A real two-state rotation is chosen by a one-dimensional root
    solve so that one state lands exactly at ``C``; the final state follows
    from conservation of the weighted average.
    """

    target = concurrence(rho)
    if target <= 1e-13:
        raise ValueError("equal-preconcurrence construction is for C(rho) > 0")
    states, _ = signed_preconcurrence_decomposition(rho)
    active = list(range(states.shape[1]))
    for _ in range(max(0, len(active) - 1)):
        values = {
            index: subnormalized_preconcurrence(states[:, index]) for index in active
        }
        high = max(active, key=values.get)
        low = min(active, key=values.get)
        if values[high] < target - 1e-10 or values[low] > target + 1e-10:
            raise RuntimeError("remaining preconcurrences do not bracket the target")
        first, second = states[:, high].copy(), states[:, low].copy()

        def residual(angle: float) -> float:
            candidate = np.cos(angle) * first + np.sin(angle) * second
            numerator = np.vdot(candidate, spin_flip_state(candidate)).real
            return float(numerator - target * np.vdot(candidate, candidate).real)

        if abs(residual(0.0)) <= 1e-13:
            angle = 0.0
        elif abs(residual(np.pi / 2.0)) <= 1e-13:
            angle = np.pi / 2.0
        else:
            angle = float(brentq(residual, 0.0, np.pi / 2.0, xtol=1e-14))
        states[:, high] = np.cos(angle) * first + np.sin(angle) * second
        states[:, low] = -np.sin(angle) * first + np.cos(angle) * second
        active.remove(high)

    preconcurrences = np.array(
        [
            subnormalized_preconcurrence(states[:, index])
            for index in range(states.shape[1])
        ]
    )
    return states, {
        "target_concurrence": target,
        "max_preconcurrence_error": float(np.max(np.abs(preconcurrences - target))),
    }


def _pair_phases_for_resultant(
    first: float, second: float, resultant: float, base_angle: float
) -> tuple[float, float]:
    tolerance = 1e-14
    if first + second <= tolerance:
        return base_angle, base_angle
    if resultant <= tolerance:
        if abs(first - second) > 1e-10:
            raise RuntimeError("two unequal vectors cannot have zero resultant")
        return base_angle + np.pi / 2.0, base_angle - np.pi / 2.0
    if first <= tolerance or second <= tolerance:
        return base_angle, base_angle
    cosine_first = np.clip(
        (first**2 + resultant**2 - second**2) / (2.0 * first * resultant), -1.0, 1.0
    )
    cosine_second = np.clip(
        (second**2 + resultant**2 - first**2) / (2.0 * second * resultant), -1.0, 1.0
    )
    return (
        base_angle + float(np.arccos(cosine_first)),
        base_angle - float(np.arccos(cosine_second)),
    )


def zero_concurrence_decomposition(
    rho: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Construct the Eq. (23)-(24) four-state ensemble for ``C(rho)=0``."""

    states, lambdas = tilde_orthogonal_decomposition(rho)
    if lambdas[0] > np.sum(lambdas[1:]) + 1e-10:
        raise ValueError("the four-vector phase closure requires C(rho)=0")
    padded_states = np.zeros((4, 4), dtype=complex)
    padded_states[:, : states.shape[1]] = states
    padded_lambdas = np.zeros(4)
    padded_lambdas[: len(lambdas)] = lambdas
    total = float(np.sum(padded_lambdas))
    boundary_tolerance = 256.0 * np.finfo(float).eps * max(1.0, total)
    if total <= boundary_tolerance:
        phase_angles = np.zeros(4)
    elif abs(padded_lambdas[0] - np.sum(padded_lambdas[1:])) <= boundary_tolerance:
        # On the separability boundary the polygon is collinear.  Evaluating
        # arccos at +/-1 amplifies round-off into O(sqrt(eps)) concurrence, so
        # use the exact phase assignment instead.
        phase_angles = np.array([0.0, np.pi, np.pi, np.pi])
    else:
        lower = max(
            abs(padded_lambdas[0] - padded_lambdas[1]),
            abs(padded_lambdas[2] - padded_lambdas[3]),
        )
        upper = min(
            padded_lambdas[0] + padded_lambdas[1],
            padded_lambdas[2] + padded_lambdas[3],
        )
        if lower > upper + 1e-10:
            raise RuntimeError("lambda polygon does not close")
        resultant = (lower + upper) / 2.0
        phase_angles = np.array(
            [
                *_pair_phases_for_resultant(
                    padded_lambdas[0], padded_lambdas[1], resultant, 0.0
                ),
                *_pair_phases_for_resultant(
                    padded_lambdas[2], padded_lambdas[3], resultant, np.pi
                ),
            ]
        )
    closure = np.sum(padded_lambdas * np.exp(1.0j * phase_angles))
    state_phases = np.exp(0.5j * phase_angles)
    hadamard = (
        np.array(
            [
                [1.0, 1.0, 1.0, 1.0],
                [1.0, 1.0, -1.0, -1.0],
                [1.0, -1.0, 1.0, -1.0],
                [1.0, -1.0, -1.0, 1.0],
            ]
        )
        / 2.0
    )
    result = (padded_states * state_phases) @ hadamard.T
    return result, {
        "phase_closure_error": float(abs(closure)),
        "max_state_concurrence": float(
            max(pure_concurrence(result[:, index]) for index in range(4))
        ),
    }


def optimal_decomposition(rho: np.ndarray) -> tuple[np.ndarray, dict[str, float | str]]:
    """Construct an ensemble that attains Wootters's convex-roof formula."""

    target = concurrence(rho)
    if target > 1e-12:
        states, diagnostics = equal_preconcurrence_decomposition(rho)
        branch = "positive_concurrence"
    else:
        states, diagnostics = zero_concurrence_decomposition(rho)
        branch = "zero_concurrence"
    reconstruction = float(np.linalg.norm(states @ states.conj().T - rho))
    average_c = average_concurrence(states)
    average_e = average_entanglement(states)
    diagnostics.update(
        {
            "branch": branch,
            "reconstruction_error": reconstruction,
            "average_concurrence": average_c,
            "average_entanglement": average_e,
            "concurrence_gap": float(abs(average_c - target)),
            "entanglement_gap": float(
                abs(average_e - entanglement_from_concurrence(target))
            ),
        }
    )
    return states, diagnostics


def random_density_matrix(rng: np.random.Generator, rank: int = 4) -> np.ndarray:
    matrix = rng.normal(size=(4, rank)) + 1.0j * rng.normal(size=(4, rank))
    rho = matrix @ matrix.conj().T
    return rho / np.trace(rho)


def random_isometry(rng: np.random.Generator, rows: int, columns: int) -> np.ndarray:
    if rows < columns:
        raise ValueError("rows must be at least columns")
    matrix = rng.normal(size=(rows, columns)) + 1.0j * rng.normal(size=(rows, columns))
    q, _ = np.linalg.qr(matrix)
    return q[:, :columns]


def hjw_decomposition(rho: np.ndarray, isometry: np.ndarray) -> np.ndarray:
    weighted = _subnormalized_eigenensemble(rho)
    isometry = np.asarray(isometry, dtype=complex)
    if isometry.shape[1] != weighted.shape[1]:
        raise ValueError("isometry columns must equal density-matrix rank")
    return weighted @ isometry.conj().T


def hjw_isometry_from_decomposition(rho: np.ndarray, states: np.ndarray) -> np.ndarray:
    """Recover the HJW isometry for a supplied subnormalized ensemble."""

    weighted = _subnormalized_eigenensemble(rho)
    coefficients = np.linalg.pinv(weighted) @ np.asarray(states, dtype=complex)
    isometry = coefficients.conj().T
    if np.linalg.norm(isometry.conj().T @ isometry - np.eye(weighted.shape[1])) > 2e-9:
        raise RuntimeError("supplied states are not an HJW ensemble of rho")
    return isometry


def average_concurrence(subnormalized_states: np.ndarray) -> float:
    total = 0.0
    for index in range(subnormalized_states.shape[1]):
        state = subnormalized_states[:, index]
        total += abs(np.vdot(state, spin_flip_state(state)))
    return float(total)


def average_entanglement(subnormalized_states: np.ndarray) -> float:
    total = 0.0
    for index in range(subnormalized_states.shape[1]):
        state = subnormalized_states[:, index]
        weight = float(np.vdot(state, state).real)
        if weight > 1e-15:
            total += weight * pure_entanglement(state)
    return float(total)


def bell_state(label: str = "psi_minus") -> np.ndarray:
    states = {
        "phi_plus": np.array([1, 0, 0, 1], dtype=complex),
        "phi_minus": np.array([1, 0, 0, -1], dtype=complex),
        "psi_plus": np.array([0, 1, 1, 0], dtype=complex),
        "psi_minus": np.array([0, 1, -1, 0], dtype=complex),
    }
    return states[label] / np.sqrt(2.0)


def bell_diagonal_state(probabilities: np.ndarray | list[float]) -> np.ndarray:
    """Return a Bell-diagonal density matrix in a fixed four-state order."""

    probabilities = np.asarray(probabilities, dtype=float)
    if probabilities.shape != (4,) or np.any(probabilities < 0.0):
        raise ValueError("Bell probabilities must be four nonnegative numbers")
    if abs(float(np.sum(probabilities)) - 1.0) > 1e-12:
        raise ValueError("Bell probabilities must sum to one")
    labels = ("phi_plus", "phi_minus", "psi_plus", "psi_minus")
    rho = np.zeros((4, 4), dtype=complex)
    for probability, label in zip(probabilities, labels, strict=True):
        state = bell_state(label)
        rho += probability * np.outer(state, state.conj())
    return rho


def werner_state(p: float) -> np.ndarray:
    singlet = bell_state("psi_minus")
    return p * np.outer(singlet, singlet.conj()) + (1.0 - p) * np.eye(4) / 4.0


def partial_transpose_b(rho: np.ndarray) -> np.ndarray:
    return np.asarray(rho).reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
