r"""Small, self-contained MPO/DMRG backend for Supplementary Figure S1.

The paper uses DMRG at ``N=60`` with an MPO whose bond dimension grows only
linearly with deformation range.  This module implements the same scalable
object independently from the printed Hamiltonian: a prefix-automaton MPO for
the translated Pauli strings and a checkpointable two-site DMRG solver.

It intentionally has no reader for paper figures, author arrays, or external
DMRG output.  The reduced exact solver is used in tests as an oracle only at
small ``N``.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh


IDENTITY = np.eye(2, dtype=np.complex128)
SIGMA_X = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
SIGMA_Z = np.asarray([[-1.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
PROJECTOR_DOWN = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
OPERATORS = {"I": IDENTITY, "X": SIGMA_X, "Z": SIGMA_Z, "P": PROJECTOR_DOWN}

MPO = list[np.ndarray]
MPS = list[np.ndarray]


def _translated_string_mpo(
    n_sites: int,
    patterns: Sequence[tuple[complex, tuple[str, ...]]],
) -> MPO:
    """Return the sum of every in-bounds translation of each operator string."""

    prefixes = sorted(
        {tokens[:length] for _, tokens in patterns for length in range(1, len(tokens))},
        key=lambda value: (len(value), value),
    )
    prefix_state = {prefix: index + 1 for index, prefix in enumerate(prefixes)}
    terminal = len(prefixes) + 1
    dimension = terminal + 1
    bulk = np.zeros((dimension, dimension, 2, 2), dtype=np.complex128)
    bulk[0, 0] = IDENTITY
    bulk[terminal, terminal] = IDENTITY

    unique_edges: set[tuple[int, int, str]] = set()
    terminal_edges: dict[tuple[int, int, str], complex] = {}
    for coefficient, tokens in patterns:
        if not tokens:
            raise ValueError("operator strings must be non-empty")
        for position, token in enumerate(tokens):
            source = 0 if position == 0 else prefix_state[tokens[:position]]
            target = terminal if position == len(tokens) - 1 else prefix_state[tokens[: position + 1]]
            key = (source, target, token)
            if target == terminal:
                terminal_edges[key] = terminal_edges.get(key, 0.0) + coefficient
            else:
                unique_edges.add(key)
    for source, target, token in unique_edges:
        bulk[source, target] += OPERATORS[token]
    for (source, target, token), coefficient in terminal_edges.items():
        bulk[source, target] += coefficient * OPERATORS[token]

    tensors: MPO = []
    for site in range(n_sites):
        tensor = bulk
        if site == 0:
            tensor = tensor[0:1, :, :, :]
        if site == n_sites - 1:
            tensor = tensor[:, terminal : terminal + 1, :, :]
        tensors.append(np.array(tensor, copy=True))
    return tensors


def _product_mpo(
    n_sites: int,
    site_operators: Mapping[int, str],
    coefficient: complex,
) -> MPO:
    tensors: MPO = []
    for site in range(n_sites):
        operator = OPERATORS[site_operators.get(site, "I")]
        if site == 0:
            operator = coefficient * operator
        tensors.append(operator.reshape(1, 1, 2, 2).copy())
    return tensors


def add_mpo(left: MPO, right: MPO) -> MPO:
    """Exact block-sum of two open-boundary MPOs."""

    if len(left) != len(right):
        raise ValueError("MPO lengths differ")
    result: MPO = []
    last = len(left) - 1
    for site, (a, b) in enumerate(zip(left, right)):
        if a.shape[2:] != b.shape[2:]:
            raise ValueError("MPO physical dimensions differ")
        if site == 0:
            tensor = np.concatenate((a, b), axis=1)
        elif site == last:
            tensor = np.concatenate((a, b), axis=0)
        else:
            tensor = np.zeros(
                (a.shape[0] + b.shape[0], a.shape[1] + b.shape[1], 2, 2),
                dtype=np.complex128,
            )
            tensor[: a.shape[0], : a.shape[1]] = a
            tensor[a.shape[0] :, a.shape[1] :] = b
        result.append(tensor)
    return result


def compress_mpo(mpo: MPO, cutoff: float = 1e-14) -> MPO:
    """Remove exact/redundant automaton channels by left-to-right SVD."""

    result = [np.array(tensor, copy=True) for tensor in mpo]
    for site in range(len(result) - 1):
        tensor = result[site]
        left, right, out_dim, in_dim = tensor.shape
        matrix = tensor.transpose(0, 2, 3, 1).reshape(left * out_dim * in_dim, right)
        u_matrix, singular, vh_matrix = np.linalg.svd(matrix, full_matrices=False)
        if singular.size == 0:
            raise RuntimeError("zero-rank MPO bond")
        keep = max(1, int(np.sum(singular > cutoff * singular[0])))
        u_matrix = u_matrix[:, :keep]
        transfer = singular[:keep, None] * vh_matrix[:keep, :]
        result[site] = u_matrix.reshape(left, out_dim, in_dim, keep).transpose(0, 3, 1, 2)
        result[site + 1] = np.einsum("ka,abst->kbst", transfer, result[site + 1])
    return result


def open_pxp_mpo(
    n_sites: int,
    couplings: Mapping[int, float],
    *,
    compress_cutoff: float = 1e-14,
) -> MPO:
    """Build the open deformed-PXP MPO from Main Eqs. (1)--(4).

    Missing boundary neighbours are omitted, as prescribed in Supplementary
    Sec. "Low lying special states".  The sign follows the main-text
    deformation ``H = H0 - sum h_d PXP(Z_left+Z_right)``.
    """

    if n_sites < 3:
        raise ValueError("the open PXP MPO requires at least three sites")
    patterns: list[tuple[complex, tuple[str, ...]]] = [(1.0, ("P", "X", "P"))]
    for distance, value in sorted(couplings.items()):
        if distance < 2:
            raise ValueError("deformation distances start at two")
        gap = ("I",) * (distance - 2)
        patterns.append((-float(value), ("P", "X", "P") + gap + ("Z",)))
        patterns.append((-float(value), ("Z",) + gap + ("P", "X", "P")))
    mpo = _translated_string_mpo(n_sites, patterns)

    boundary_terms: list[tuple[complex, dict[int, str]]] = [
        (1.0, {0: "X", 1: "P"}),
        (1.0, {n_sites - 2: "P", n_sites - 1: "X"}),
    ]
    for distance, value in sorted(couplings.items()):
        if distance < n_sites:
            boundary_terms.append((-float(value), {0: "X", 1: "P", distance: "Z"}))
            boundary_terms.append(
                (-float(value), {n_sites - 1 - distance: "Z", n_sites - 2: "P", n_sites - 1: "X"})
            )
    for coefficient, operators in boundary_terms:
        mpo = add_mpo(mpo, _product_mpo(n_sites, operators, coefficient))
    return compress_mpo(mpo, cutoff=compress_cutoff)


def mpo_to_dense(mpo: MPO) -> np.ndarray:
    """Contract a small MPO exactly; intended for tests, never paper scale."""

    blocks: dict[int, np.ndarray] = {0: np.ones((1, 1), dtype=np.complex128)}
    for tensor in mpo:
        next_blocks: dict[int, np.ndarray] = {}
        for left_state, prefix in blocks.items():
            for right_state in range(tensor.shape[1]):
                local = tensor[left_state, right_state]
                if np.max(np.abs(local), initial=0.0) == 0.0:
                    continue
                value = np.kron(prefix, local)
                next_blocks[right_state] = next_blocks.get(right_state, 0.0) + value
        blocks = next_blocks
    if set(blocks) != {0}:
        raise RuntimeError("invalid open MPO boundary")
    return np.asarray(blocks[0])


def random_mps(n_sites: int, max_bond: int, seed: int) -> MPS:
    """Create a reproducible random open MPS and left-canonicalize it."""

    rng = np.random.default_rng(seed)
    bonds = [1]
    for cut in range(1, n_sites):
        bonds.append(min(max_bond, 2**min(cut, n_sites - cut)))
    bonds.append(1)
    mps = [
        rng.normal(size=(bonds[site], 2, bonds[site + 1])).astype(np.complex128)
        for site in range(n_sites)
    ]
    for site in range(n_sites - 1):
        left, physical, right = mps[site].shape
        q_matrix, r_matrix = np.linalg.qr(mps[site].reshape(left * physical, right))
        rank = q_matrix.shape[1]
        mps[site] = q_matrix.reshape(left, physical, rank)
        mps[site + 1] = np.einsum("ab,bsd->asd", r_matrix, mps[site + 1])
    normalize_mps(mps)
    return mps


def _advance_left(environment: np.ndarray, state: np.ndarray, operator: np.ndarray) -> np.ndarray:
    return np.einsum(
        "awb,asc,wxst,btd->cxd",
        environment,
        state.conjugate(),
        operator,
        state,
        optimize=True,
    )


def _advance_right(environment: np.ndarray, state: np.ndarray, operator: np.ndarray) -> np.ndarray:
    return np.einsum(
        "asc,wyst,btd,cyd->awb",
        state.conjugate(),
        operator,
        state,
        environment,
        optimize=True,
    )


def mps_inner(left: MPS, right: MPS) -> complex:
    environment = np.ones((1, 1), dtype=np.complex128)
    for a, b in zip(left, right):
        environment = np.einsum(
            "ab,asc,bsd->cd", environment, a.conjugate(), b, optimize=True
        )
    return complex(environment[0, 0])


def normalize_mps(mps: MPS) -> float:
    norm = float(np.sqrt(max(mps_inner(mps, mps).real, 0.0)))
    if norm <= 1e-15:
        raise RuntimeError("zero-norm MPS")
    mps[0] = mps[0] / norm
    return norm


def mpo_expectation(mps: MPS, mpo: MPO) -> float:
    environment = np.ones((1, 1, 1), dtype=np.complex128)
    for state, operator in zip(mps, mpo):
        environment = _advance_left(environment, state, operator)
    return float(environment[0, 0, 0].real)


def _mixed_left(prior: MPS, current: MPS, stop: int) -> np.ndarray:
    environment = np.ones((1, 1), dtype=np.complex128)
    for site in range(stop):
        environment = np.einsum(
            "ab,asc,bsd->cd",
            environment,
            prior[site].conjugate(),
            current[site],
            optimize=True,
        )
    return environment


def _mixed_right(prior: MPS, current: MPS, start: int) -> np.ndarray:
    environment = np.ones((1, 1), dtype=np.complex128)
    for site in range(len(current) - 1, start - 1, -1):
        environment = np.einsum(
            "asc,bsd,cd->ab",
            prior[site].conjugate(),
            current[site],
            environment,
            optimize=True,
        )
    return environment


def _local_projector_vector(prior: MPS, current: MPS, site: int) -> np.ndarray:
    left = _mixed_left(prior, current, site)
    right = _mixed_right(prior, current, site + 2)
    q_vector = np.einsum(
        "ab,ase,euc,cd->bsud",
        left,
        prior[site].conjugate(),
        prior[site + 1].conjugate(),
        right,
        optimize=True,
    )
    return q_vector.conjugate()


def _two_site_operator(
    left: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    right: np.ndarray,
    shape: tuple[int, int, int, int],
    projector: np.ndarray | None,
    penalty_weight: float,
) -> LinearOperator:
    dimension = int(np.prod(shape))

    def matvec(raw_vector: np.ndarray) -> np.ndarray:
        vector = raw_vector.reshape(shape)
        result = np.einsum(
            "awb,wxst,xyuv,cyd,btvd->asuc",
            left,
            first,
            second,
            right,
            vector,
            optimize=True,
        )
        if projector is not None:
            result = result + penalty_weight * projector * np.vdot(projector, vector)
        return np.asarray(result).reshape(-1)

    return LinearOperator((dimension, dimension), matvec=matvec, dtype=np.complex128)


def _smallest_local_eigenpair(
    operator: LinearOperator,
    initial: np.ndarray,
    tolerance: float,
    max_iterations: int,
) -> tuple[float, np.ndarray, float]:
    dimension = operator.shape[0]
    initial = np.asarray(initial, dtype=np.complex128).reshape(-1)
    if dimension <= 48:
        identity = np.eye(dimension, dtype=np.complex128)
        dense = np.column_stack([operator @ identity[:, column] for column in range(dimension)])
        values, vectors = np.linalg.eigh((dense + dense.conjugate().T) / 2.0)
        value = float(values[0].real)
        vector = vectors[:, 0]
    else:
        values, vectors = eigsh(
            operator,
            k=1,
            which="SA",
            v0=initial,
            tol=tolerance,
            maxiter=max_iterations,
        )
        value = float(values[0].real)
        vector = vectors[:, 0]
    residual = float(np.linalg.norm(operator @ vector - value * vector))
    return value, vector, residual


def _split_two_site(
    vector: np.ndarray,
    shape: tuple[int, int, int, int],
    *,
    max_bond: int,
    cutoff: float,
    direction: str,
) -> tuple[np.ndarray, np.ndarray, float]:
    left, first_physical, second_physical, right = shape
    matrix = vector.reshape(left * first_physical, second_physical * right)
    u_matrix, singular, vh_matrix = np.linalg.svd(matrix, full_matrices=False)
    threshold = cutoff * singular[0] if singular.size else cutoff
    keep = min(max_bond, max(1, int(np.sum(singular > threshold))))
    discarded = float(np.sum(np.abs(singular[keep:]) ** 2))
    u_matrix = u_matrix[:, :keep]
    singular = singular[:keep]
    vh_matrix = vh_matrix[:keep]
    if direction == "right":
        first = u_matrix.reshape(left, first_physical, keep)
        second = (singular[:, None] * vh_matrix).reshape(keep, second_physical, right)
    elif direction == "left":
        first = (u_matrix * singular[None, :]).reshape(left, first_physical, keep)
        second = vh_matrix.reshape(keep, second_physical, right)
    else:
        raise ValueError("direction must be right or left")
    return first, second, discarded


def schmidt_values(mps: MPS, cut: int) -> np.ndarray:
    """Return normalized Schmidt values across ``cut`` without densifying."""

    if not 0 < cut < len(mps):
        raise ValueError("cut must lie inside the chain")
    state = [np.array(tensor, copy=True) for tensor in mps]
    for site in range(cut - 1):
        left, physical, right = state[site].shape
        q_matrix, r_matrix = np.linalg.qr(state[site].reshape(left * physical, right))
        rank = q_matrix.shape[1]
        state[site] = q_matrix.reshape(left, physical, rank)
        state[site + 1] = np.einsum("ab,bsd->asd", r_matrix, state[site + 1])
    for site in range(len(state) - 1, cut, -1):
        left, physical, right = state[site].shape
        q_matrix, r_matrix = np.linalg.qr(state[site].reshape(left, physical * right).T)
        rank = q_matrix.shape[1]
        state[site] = q_matrix.T.reshape(rank, physical, right)
        state[site - 1] = np.einsum("asb,bc->asc", state[site - 1], r_matrix.T)
    theta = np.einsum("asb,btc->astc", state[cut - 1], state[cut], optimize=True)
    matrix = theta.reshape(theta.shape[0] * 2, 2 * theta.shape[-1])
    singular = np.linalg.svd(matrix, compute_uv=False)
    norm = np.linalg.norm(singular)
    return singular / norm


def save_mps(path: Path, mps: MPS, metadata: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {f"tensor_{index:03d}": tensor for index, tensor in enumerate(mps)}
    arrays["metadata_json"] = np.asarray(json.dumps(dict(metadata), sort_keys=True))
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary.replace(path)


def load_mps(path: Path) -> tuple[MPS, dict[str, object]]:
    with np.load(path, allow_pickle=False) as payload:
        tensor_names = sorted(name for name in payload.files if name.startswith("tensor_"))
        mps = [np.asarray(payload[name]) for name in tensor_names]
        metadata = json.loads(str(payload["metadata_json"]))
    return mps, metadata


@dataclass(frozen=True)
class DMRGSettings:
    max_bond: int
    singular_value_cutoff: float
    energy_tolerance: float
    local_tolerance: float
    local_max_iterations: int
    minimum_sweeps: int
    maximum_sweeps: int
    excited_state_penalty: float
    seed: int


@dataclass
class DMRGResult:
    energy: float
    mps: MPS
    sweeps: int
    energy_change: float
    maximum_local_residual: float
    maximum_discarded_weight: float
    overlap_with_penalized_state: float
    converged: bool


def two_site_dmrg(
    mpo: MPO,
    settings: DMRGSettings,
    *,
    checkpoint_path: Path,
    resume: bool,
    prior_state: MPS | None = None,
) -> DMRGResult:
    """Minimize an MPO, optionally penalizing overlap with one prior MPS."""

    if resume and checkpoint_path.exists():
        state, metadata = load_mps(checkpoint_path)
        start_sweep = int(metadata.get("sweep", 0))
        previous_energy = float(metadata.get("energy", np.inf))
    else:
        state = random_mps(len(mpo), min(settings.max_bond, 4), settings.seed)
        start_sweep = 0
        previous_energy = np.inf

    maximum_local_residual = np.inf
    maximum_discarded = np.inf
    energy_change = np.inf
    converged = False
    completed_sweeps = start_sweep
    for sweep in range(start_sweep, settings.maximum_sweeps):
        sweep_residual = 0.0
        sweep_discarded = 0.0
        for direction, sites in (
            ("right", range(len(state) - 1)),
            ("left", range(len(state) - 2, -1, -1)),
        ):
            if direction == "right":
                right_environments: list[np.ndarray | None] = [None] * (len(state) + 1)
                right_environments[len(state)] = np.ones((1, 1, 1), dtype=np.complex128)
                for cursor in range(len(state) - 1, -1, -1):
                    right_environments[cursor] = _advance_right(
                        right_environments[cursor + 1], state[cursor], mpo[cursor]
                    )
                left_environment = np.ones((1, 1, 1), dtype=np.complex128)
            else:
                left_environments: list[np.ndarray | None] = [None] * (len(state) + 1)
                left_environments[0] = np.ones((1, 1, 1), dtype=np.complex128)
                for cursor in range(len(state)):
                    left_environments[cursor + 1] = _advance_left(
                        left_environments[cursor], state[cursor], mpo[cursor]
                    )
                right_environment = np.ones((1, 1, 1), dtype=np.complex128)

            for site in sites:
                if direction == "right":
                    left = left_environment
                    right = right_environments[site + 2]
                else:
                    left = left_environments[site]
                    right = right_environment
                theta = np.einsum("asb,btc->astc", state[site], state[site + 1], optimize=True)
                projector = (
                    _local_projector_vector(prior_state, state, site)
                    if prior_state is not None
                    else None
                )
                operator = _two_site_operator(
                    left,
                    mpo[site],
                    mpo[site + 1],
                    right,
                    theta.shape,
                    projector,
                    settings.excited_state_penalty,
                )
                _, vector, residual = _smallest_local_eigenpair(
                    operator,
                    theta,
                    settings.local_tolerance,
                    settings.local_max_iterations,
                )
                first, second, discarded = _split_two_site(
                    vector,
                    theta.shape,
                    max_bond=settings.max_bond,
                    cutoff=settings.singular_value_cutoff,
                    direction=direction,
                )
                state[site], state[site + 1] = first, second
                sweep_residual = max(sweep_residual, residual)
                sweep_discarded = max(sweep_discarded, discarded)
                if direction == "right":
                    left_environment = _advance_left(left_environment, state[site], mpo[site])
                else:
                    right_environment = _advance_right(
                        right_environment, state[site + 1], mpo[site + 1]
                    )

        normalize_mps(state)
        energy = mpo_expectation(state, mpo)
        energy_change = abs(energy - previous_energy)
        previous_energy = energy
        completed_sweeps = sweep + 1
        maximum_local_residual = sweep_residual
        maximum_discarded = sweep_discarded
        overlap = abs(mps_inner(prior_state, state)) if prior_state is not None else 0.0
        save_mps(
            checkpoint_path,
            state,
            {
                "sweep": completed_sweeps,
                "energy": energy,
                "energy_change": energy_change,
                "maximum_local_residual": maximum_local_residual,
                "maximum_discarded_weight": maximum_discarded,
                "overlap_with_penalized_state": overlap,
            },
        )
        if (
            completed_sweeps >= settings.minimum_sweeps
            and energy_change <= settings.energy_tolerance
            and maximum_local_residual <= max(10.0 * settings.local_tolerance, 1e-12)
        ):
            converged = True
            break

    return DMRGResult(
        energy=float(previous_energy),
        mps=state,
        sweeps=completed_sweeps,
        energy_change=float(energy_change),
        maximum_local_residual=float(maximum_local_residual),
        maximum_discarded_weight=float(maximum_discarded),
        overlap_with_penalized_state=float(
            abs(mps_inner(prior_state, state)) if prior_state is not None else 0.0
        ),
        converged=converged,
    )


def dmrg_ground_and_first_excited(
    mpo: MPO,
    settings: DMRGSettings,
    *,
    checkpoint_directory: Path,
    resume: bool,
) -> tuple[DMRGResult, DMRGResult]:
    checkpoint_directory.mkdir(parents=True, exist_ok=True)
    ground = two_site_dmrg(
        mpo,
        settings,
        checkpoint_path=checkpoint_directory / "ground.npz",
        resume=resume,
    )
    excited_settings = DMRGSettings(**{**settings.__dict__, "seed": settings.seed + 1})
    excited = two_site_dmrg(
        mpo,
        excited_settings,
        checkpoint_path=checkpoint_directory / "first_excited.npz",
        resume=resume,
        prior_state=ground.mps,
    )
    return ground, excited
