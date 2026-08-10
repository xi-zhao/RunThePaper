"""Independent level-1 QAOA and RQAOA numerics for arXiv:1910.08980.

The implementation follows Eq. (C9) and the recursive elimination algorithm in
Appendix C of the paper.  It deliberately contains no parser for paper figures
or author-produced numerical data.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from time import perf_counter

import networkx as nx
import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp, minimize_scalar
from scipy.sparse import coo_matrix


FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True)
class QAOA1Result:
    beta: float
    gamma: float
    expected_energy: float
    correlations: FloatArray


@dataclass(frozen=True)
class ExactIsingResult:
    energy: float
    spins: IntArray
    runtime_seconds: float
    mip_gap: float


@dataclass(frozen=True)
class RQAOAResult:
    energy: float
    spins: IntArray
    eliminations: tuple[dict[str, float | int], ...]
    cutoff_exact_energy: float
    runtime_seconds: float


def edge_pairs(couplings: FloatArray, *, atol: float = 1e-12) -> IntArray:
    """Return the nonzero upper-triangular interaction pairs."""

    rows, cols = np.nonzero(np.triu(np.abs(couplings) > atol, k=1))
    return np.column_stack((rows, cols)).astype(np.int64, copy=False)


def ising_energy(couplings: FloatArray, spins: IntArray) -> float:
    """Evaluate sum_{u<v} J_uv z_u z_v."""

    return float(0.5 * spins @ couplings @ spins)


def qaoa1_coefficients(
    couplings: FloatArray,
    gamma: float,
    pairs: IntArray | None = None,
) -> tuple[FloatArray, FloatArray, IntArray]:
    """Return the beta-independent coefficients in the paper's Eq. (C9).

    For every active edge ``e=(u,v)``, the correlation is

        M_e = A_e sin^2(2 beta) + B_e cos(2 beta) sin(2 beta).

    The products include every remaining qubit except ``u`` and ``v``.  Zero
    couplings therefore contribute a factor one, exactly as in the equation.
    """

    matrix = np.asarray(couplings, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("couplings must be a square matrix")
    if not np.allclose(matrix, matrix.T, atol=1e-12):
        raise ValueError("couplings must be symmetric")

    active_pairs = edge_pairs(matrix) if pairs is None else np.asarray(pairs, dtype=np.int64)
    a_values = np.empty(len(active_pairs), dtype=np.float64)
    b_values = np.empty(len(active_pairs), dtype=np.float64)
    all_indices = np.arange(matrix.shape[0])

    for index, (u, v) in enumerate(active_pairs):
        keep = (all_indices != u) & (all_indices != v)
        row_u = matrix[u, keep]
        row_v = matrix[v, keep]
        product_minus = np.prod(np.cos(2.0 * gamma * (row_u - row_v)))
        product_plus = np.prod(np.cos(2.0 * gamma * (row_u + row_v)))
        product_u = np.prod(np.cos(2.0 * gamma * row_u))
        product_v = np.prod(np.cos(2.0 * gamma * row_v))
        a_values[index] = 0.5 * (product_minus - product_plus)
        b_values[index] = np.sin(2.0 * gamma * matrix[u, v]) * (product_u + product_v)

    return a_values, b_values, active_pairs


def _optimal_beta(a_total: float, b_total: float) -> tuple[float, float]:
    """Maximize A sin^2(2 beta)+B cos(2 beta)sin(2 beta) analytically."""

    angle = float(np.mod(np.arctan2(b_total, -a_total), 2.0 * np.pi))
    beta = 0.25 * angle
    maximum = 0.5 * (a_total + np.hypot(a_total, b_total))
    return beta, float(maximum)


def qaoa1_at_gamma(couplings: FloatArray, gamma: float) -> QAOA1Result:
    """Optimize beta exactly for a fixed gamma."""

    a_values, b_values, pairs = qaoa1_coefficients(couplings, gamma)
    weights = couplings[pairs[:, 0], pairs[:, 1]] if len(pairs) else np.empty(0)
    a_total = float(weights @ a_values)
    b_total = float(weights @ b_values)
    beta, expected_energy = _optimal_beta(a_total, b_total)
    sine = np.sin(2.0 * beta)
    cosine = np.cos(2.0 * beta)
    correlations = a_values * sine**2 + b_values * cosine * sine
    return QAOA1Result(beta, float(gamma), expected_energy, correlations)


def optimize_qaoa1(
    couplings: FloatArray,
    *,
    gamma_grid_points: int = 257,
    local_candidates: int = 8,
) -> QAOA1Result:
    """Globally search one gamma period, then polish the best grid basins.

    All couplings created by the paper's signed-Ising protocol and recursive
    contractions are integers, so ``gamma in [0, pi]`` is a complete period.
    Beta is optimized analytically at every gamma.
    """

    if gamma_grid_points < 17:
        raise ValueError("gamma_grid_points must be at least 17")
    matrix = np.asarray(couplings, dtype=np.float64)
    if len(edge_pairs(matrix)) == 0:
        return QAOA1Result(0.0, 0.0, 0.0, np.empty(0, dtype=np.float64))

    grid = np.linspace(0.0, pi, gamma_grid_points, endpoint=False)
    energies = np.array([qaoa1_at_gamma(matrix, gamma).expected_energy for gamma in grid])
    candidate_indices = np.argsort(energies)[-min(local_candidates, len(grid)) :]
    spacing = pi / gamma_grid_points
    candidate_gammas = [float(grid[int(np.argmax(energies))])]

    for index in candidate_indices:
        center = float(grid[index])
        lower = max(0.0, center - spacing)
        upper = min(pi, center + spacing)
        if upper <= lower:
            continue
        result = minimize_scalar(
            lambda gamma: -qaoa1_at_gamma(matrix, float(gamma)).expected_energy,
            bounds=(lower, upper),
            method="bounded",
            options={"xatol": 1e-11, "maxiter": 100},
        )
        candidate_gammas.append(float(result.x))

    candidate_gammas.extend((0.0, pi))
    results = [qaoa1_at_gamma(matrix, gamma) for gamma in candidate_gammas]
    return max(results, key=lambda item: item.expected_energy)


def exact_ising_max(
    couplings: FloatArray,
    *,
    time_limit_seconds: float | None = None,
) -> ExactIsingResult:
    """Solve the signed Ising maximum exactly through a binary MILP.

    A binary variable ``d_e`` represents whether the endpoint spins differ.
    Four linear inequalities impose ``d_e = b_u XOR b_v``.  The global spin
    flip is removed by fixing ``b_0=0``.
    """

    matrix = np.asarray(couplings, dtype=np.float64)
    pairs = edge_pairs(matrix)
    n = matrix.shape[0]
    m = len(pairs)
    if n == 0:
        raise ValueError("empty Ising model")
    if m == 0:
        return ExactIsingResult(0.0, np.ones(n, dtype=np.int64), 0.0, 0.0)

    objective = np.zeros(n + m, dtype=np.float64)
    weights = matrix[pairs[:, 0], pairs[:, 1]]
    objective[n:] = 2.0 * weights

    row_indices: list[int] = []
    col_indices: list[int] = []
    values: list[float] = []
    upper_bounds = np.empty(4 * m, dtype=np.float64)

    def add(row: int, column: int, value: float) -> None:
        row_indices.append(row)
        col_indices.append(column)
        values.append(value)

    for edge_index, (u, v) in enumerate(pairs):
        d = n + edge_index
        base = 4 * edge_index
        # b_u - b_v - d <= 0
        add(base, int(u), 1.0)
        add(base, int(v), -1.0)
        add(base, d, -1.0)
        upper_bounds[base] = 0.0
        # -b_u + b_v - d <= 0
        add(base + 1, int(u), -1.0)
        add(base + 1, int(v), 1.0)
        add(base + 1, d, -1.0)
        upper_bounds[base + 1] = 0.0
        # d - b_u - b_v <= 0
        add(base + 2, int(u), -1.0)
        add(base + 2, int(v), -1.0)
        add(base + 2, d, 1.0)
        upper_bounds[base + 2] = 0.0
        # d + b_u + b_v <= 2
        add(base + 3, int(u), 1.0)
        add(base + 3, int(v), 1.0)
        add(base + 3, d, 1.0)
        upper_bounds[base + 3] = 2.0

    constraints_matrix = coo_matrix(
        (values, (row_indices, col_indices)), shape=(4 * m, n + m)
    ).tocsr()
    lower = np.zeros(n + m, dtype=np.float64)
    upper = np.ones(n + m, dtype=np.float64)
    upper[0] = 0.0
    bounds = Bounds(lower, upper)
    options: dict[str, float | bool] = {"mip_rel_gap": 0.0, "presolve": True}
    if time_limit_seconds is not None:
        options["time_limit"] = float(time_limit_seconds)

    started = perf_counter()
    result = milp(
        objective,
        integrality=np.ones(n + m, dtype=np.int8),
        bounds=bounds,
        constraints=LinearConstraint(constraints_matrix, -np.inf, upper_bounds),
        options=options,
    )
    runtime = perf_counter() - started
    if not result.success or result.x is None:
        raise RuntimeError(
            f"exact Ising MILP did not prove an optimum: status={result.status}, "
            f"message={result.message!s}"
        )
    spins = np.where(result.x[:n] >= 0.5, -1, 1).astype(np.int64)
    energy = ising_energy(matrix, spins)
    gap = float(getattr(result, "mip_gap", 0.0) or 0.0)
    if gap > 1e-10:
        raise RuntimeError(f"MILP returned a nonzero optimality gap: {gap}")
    return ExactIsingResult(energy, spins, runtime, gap)


def brute_force_ising_max(couplings: FloatArray) -> ExactIsingResult:
    """Small-system oracle used only by tests and formula checks."""

    matrix = np.asarray(couplings, dtype=np.float64)
    n = matrix.shape[0]
    if n > 24:
        raise ValueError("brute-force oracle is limited to 24 spins")
    started = perf_counter()
    best_energy = -np.inf
    best_spins = np.ones(n, dtype=np.int64)
    # Fix the first spin because the Hamiltonian has global Z2 symmetry.
    for state in range(1 << max(0, n - 1)):
        spins = np.ones(n, dtype=np.int64)
        for bit in range(1, n):
            if state & (1 << (bit - 1)):
                spins[bit] = -1
        energy = ising_energy(matrix, spins)
        if energy > best_energy:
            best_energy = energy
            best_spins = spins.copy()
    return ExactIsingResult(float(best_energy), best_spins, perf_counter() - started, 0.0)


def random_signed_regular_instance(
    n: int,
    *,
    degree: int,
    graph_seed: int,
    coupling_seed: int,
) -> FloatArray:
    """Generate the random signed regular-graph ensemble stated in Fig. 1."""

    graph = nx.random_regular_graph(degree, n, seed=int(graph_seed))
    pairs = sorted((min(u, v), max(u, v)) for u, v in graph.edges())
    generator = np.random.default_rng(int(coupling_seed))
    weights = generator.choice(np.array([-1.0, 1.0]), size=len(pairs))
    matrix = np.zeros((n, n), dtype=np.float64)
    for (u, v), weight in zip(pairs, weights, strict=True):
        matrix[u, v] = matrix[v, u] = weight
    return matrix


def run_rqaoa1(
    couplings: FloatArray,
    *,
    cutoff: int,
    gamma_grid_points: int = 257,
    local_candidates: int = 8,
    exact_time_limit_seconds: float | None = None,
) -> RQAOAResult:
    """Run the paper's recursive level-1 QAOA until ``cutoff`` variables."""

    original = np.asarray(couplings, dtype=np.float64)
    if cutoff < 1 or cutoff > original.shape[0]:
        raise ValueError("cutoff must lie between one and the model size")
    active_matrix = original.copy()
    active_nodes = list(range(original.shape[0]))
    constraints: list[tuple[int, int, int]] = []
    trace: list[dict[str, float | int]] = []
    constant_shift = 0.0
    started = perf_counter()

    while len(active_nodes) > cutoff:
        optimum = optimize_qaoa1(
            active_matrix,
            gamma_grid_points=gamma_grid_points,
            local_candidates=local_candidates,
        )
        pairs = edge_pairs(active_matrix)
        if len(pairs) == 0:
            # Isolated variables do not affect the energy.  Eliminate the last
            # one with a harmless +1 constraint so the declared cutoff is met.
            parent_index, removed_index, sigma = 0, len(active_nodes) - 1, 1
            correlation = 0.0
        else:
            best = int(np.argmax(np.abs(optimum.correlations)))
            parent_index, removed_index = map(int, pairs[best])
            correlation = float(optimum.correlations[best])
            sigma = 1 if correlation >= 0.0 else -1

        parent_node = active_nodes[parent_index]
        removed_node = active_nodes[removed_index]
        edge_weight = float(active_matrix[parent_index, removed_index])
        constant_shift += edge_weight * sigma

        for neighbor in range(len(active_nodes)):
            if neighbor in (parent_index, removed_index):
                continue
            merged = (
                active_matrix[parent_index, neighbor]
                + sigma * active_matrix[removed_index, neighbor]
            )
            if abs(merged) < 1e-12:
                merged = 0.0
            active_matrix[parent_index, neighbor] = merged
            active_matrix[neighbor, parent_index] = merged

        constraints.append((removed_node, parent_node, sigma))
        trace.append(
            {
                "step": len(trace) + 1,
                "active_size": len(active_nodes),
                "removed_node": removed_node,
                "parent_node": parent_node,
                "sigma": sigma,
                "correlation": correlation,
                "beta": optimum.beta,
                "gamma": optimum.gamma,
                "qaoa_expected_energy": optimum.expected_energy,
                "edge_weight": edge_weight,
                "constant_shift": constant_shift,
            }
        )

        active_matrix = np.delete(np.delete(active_matrix, removed_index, axis=0), removed_index, axis=1)
        active_nodes.pop(removed_index)

    cutoff_solution = exact_ising_max(
        active_matrix, time_limit_seconds=exact_time_limit_seconds
    )
    assignments = {
        node: int(spin) for node, spin in zip(active_nodes, cutoff_solution.spins, strict=True)
    }
    for removed_node, parent_node, sigma in reversed(constraints):
        assignments[removed_node] = sigma * assignments[parent_node]
    spins = np.array([assignments[node] for node in range(original.shape[0])], dtype=np.int64)
    energy = ising_energy(original, spins)
    reduced_identity_energy = cutoff_solution.energy + constant_shift
    if not np.isclose(energy, reduced_identity_energy, atol=1e-8):
        raise RuntimeError(
            "RQAOA reconstruction violated the elimination energy identity: "
            f"original={energy}, reduced={reduced_identity_energy}"
        )
    return RQAOAResult(
        energy=energy,
        spins=spins,
        eliminations=tuple(trace),
        cutoff_exact_energy=cutoff_solution.energy,
        runtime_seconds=perf_counter() - started,
    )
