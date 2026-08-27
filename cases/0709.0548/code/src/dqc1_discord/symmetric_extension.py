"""Independent first-level PPT symmetric-extension checks for DQC1 states.

The paper cites the first Doherty--Parrilo--Spedalieri hierarchy level as an
entanglement test that does not detect entanglement for ``alpha <= 1/2``.  A
feasible extension is therefore the scientifically relevant outcome: it says
that this particular test is non-detecting, not that the state is separable.
"""

from __future__ import annotations

import time
from typing import Any

import cvxpy as cp
import numpy as np


def bipartite_reorder(
    matrix: np.ndarray,
    dimensions: tuple[int, ...],
    first_group: tuple[int, ...],
) -> tuple[np.ndarray, int, int, tuple[int, ...], tuple[int, ...]]:
    """Return ``matrix`` in ``A tensor B`` order for a declared partition."""

    subsystem_count = len(dimensions)
    first = tuple(dict.fromkeys(first_group))
    if not first or len(first) == subsystem_count:
        raise ValueError("the bipartition must have two non-empty groups")
    if any(index < 0 or index >= subsystem_count for index in first):
        raise ValueError("bipartition subsystem index out of range")
    second = tuple(index for index in range(subsystem_count) if index not in first)
    total = int(np.prod(dimensions))
    if matrix.shape != (total, total):
        raise ValueError("matrix shape does not match subsystem dimensions")

    order = first + second
    tensor = matrix.reshape(*dimensions, *dimensions)
    axes = order + tuple(subsystem_count + index for index in order)
    first_dimension = int(np.prod([dimensions[index] for index in first]))
    second_dimension = total // first_dimension
    reordered = tensor.transpose(axes).reshape(total, total)
    return reordered, first_dimension, second_dimension, first, second


def _swap_operator(duplicate_dimension: int, other_dimension: int) -> np.ndarray:
    """Return the operator swapping the two duplicated subsystems."""

    size = duplicate_dimension**2 * other_dimension
    swap = np.zeros((size, size), dtype=float)
    for first in range(duplicate_dimension):
        for second in range(duplicate_dimension):
            for other in range(other_dimension):
                source = (first * duplicate_dimension + second) * other_dimension + other
                target = (second * duplicate_dimension + first) * other_dimension + other
                swap[target, source] = 1.0
    return swap


def _partial_trace_duplicate(
    extension: np.ndarray,
    duplicate_dimension: int,
    other_dimension: int,
) -> np.ndarray:
    tensor = extension.reshape(
        duplicate_dimension,
        duplicate_dimension,
        other_dimension,
        duplicate_dimension,
        duplicate_dimension,
        other_dimension,
    )
    return np.einsum("aibcid->abcd", tensor).reshape(
        duplicate_dimension * other_dimension,
        duplicate_dimension * other_dimension,
    )


def _partial_transpose_numeric(
    matrix: np.ndarray,
    dimensions: tuple[int, ...],
    axis: int,
) -> np.ndarray:
    subsystem_count = len(dimensions)
    tensor = matrix.reshape(*dimensions, *dimensions)
    axes = list(range(2 * subsystem_count))
    axes[axis], axes[subsystem_count + axis] = (
        axes[subsystem_count + axis],
        axes[axis],
    )
    return tensor.transpose(axes).reshape(matrix.shape)


def first_ppt_symmetric_extension(
    matrix: np.ndarray,
    dimensions: tuple[int, ...],
    first_group: tuple[int, ...],
    *,
    solver: str = "SCS",
    tolerance: float = 5.0e-5,
    solver_epsilon: float = 1.0e-6,
    max_iterations: int = 20_000,
) -> dict[str, Any]:
    """Solve one first-level PPT symmetric-extension feasibility problem.

    The smaller side of the bipartition is duplicated.  This changes only the
    computational orientation: separability implies an extension on either
    side.  The constraints are positivity, exchange symmetry, the correct
    marginal, and positivity under the independent partial-transpose cuts.
    """

    reordered, first_dimension, second_dimension, first, second = bipartite_reorder(
        matrix, dimensions, first_group
    )
    if first_dimension <= second_dimension:
        duplicate_group = first
        other_group = second
        duplicate_dimension = first_dimension
        other_dimension = second_dimension
        marginal = reordered
    else:
        duplicate_group = second
        other_group = first
        duplicate_dimension = second_dimension
        other_dimension = first_dimension
        marginal = reordered.reshape(
            first_dimension,
            second_dimension,
            first_dimension,
            second_dimension,
        ).transpose(1, 0, 3, 2).reshape(reordered.shape)

    installed_solvers = tuple(cp.installed_solvers())
    if solver not in installed_solvers:
        raise RuntimeError(
            f"requested PSD-cone solver {solver!r} is unavailable; installed={installed_solvers}"
        )

    extension_dimension = duplicate_dimension**2 * other_dimension
    extension = cp.Variable(
        (extension_dimension, extension_dimension), hermitian=True
    )
    swap = _swap_operator(duplicate_dimension, other_dimension)
    implicit_dimensions = (
        duplicate_dimension,
        duplicate_dimension,
        other_dimension,
    )
    constraints = [
        extension >> 0,
        extension == swap @ extension @ swap.T,
        cp.partial_trace(extension, implicit_dimensions, axis=1) == marginal,
        cp.partial_transpose(extension, implicit_dimensions, axis=0) >> 0,
        cp.partial_transpose(extension, implicit_dimensions, axis=2) >> 0,
    ]
    problem = cp.Problem(cp.Minimize(0.0), constraints)
    started = time.perf_counter()
    problem.solve(
        solver=solver,
        eps=solver_epsilon,
        max_iters=max_iterations,
        verbose=False,
    )
    elapsed = time.perf_counter() - started

    solver_status = str(problem.status)
    feasible = solver_status in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}
    result: dict[str, Any] = {
        "solver": solver,
        "cvxpy_version": cp.__version__,
        "solver_status": solver_status,
        "feasible": feasible,
        "duplicate_group": list(duplicate_group),
        "other_group": list(other_group),
        "duplicate_dimension": duplicate_dimension,
        "other_dimension": other_dimension,
        "extension_dimension": extension_dimension,
        "runtime_seconds": elapsed,
        "solver_iterations": int(problem.solver_stats.num_iters or 0),
        "solver_epsilon": solver_epsilon,
        "acceptance_tolerance": tolerance,
    }
    if not feasible or extension.value is None:
        result.update(
            {
                "certificate_passed": False,
                "minimum_extension_eigenvalue": None,
                "marginal_residual_fro": None,
                "swap_residual_fro": None,
                "minimum_ppt_duplicate_eigenvalue": None,
                "minimum_ppt_other_eigenvalue": None,
            }
        )
        return result

    value = np.asarray(extension.value)
    value = (value + value.conj().T) / 2.0
    traced = _partial_trace_duplicate(
        value, duplicate_dimension, other_dimension
    )
    ppt_duplicate = _partial_transpose_numeric(value, implicit_dimensions, 0)
    ppt_other = _partial_transpose_numeric(value, implicit_dimensions, 2)
    minimum_extension = float(np.linalg.eigvalsh(value).min())
    marginal_residual = float(np.linalg.norm(traced - marginal, ord="fro"))
    swap_residual = float(np.linalg.norm(value - swap @ value @ swap.T, ord="fro"))
    minimum_ppt_duplicate = float(
        np.linalg.eigvalsh((ppt_duplicate + ppt_duplicate.conj().T) / 2.0).min()
    )
    minimum_ppt_other = float(
        np.linalg.eigvalsh((ppt_other + ppt_other.conj().T) / 2.0).min()
    )
    certificate_passed = bool(
        minimum_extension >= -tolerance
        and marginal_residual <= tolerance
        and swap_residual <= tolerance
        and minimum_ppt_duplicate >= -tolerance
        and minimum_ppt_other >= -tolerance
    )
    result.update(
        {
            "certificate_passed": certificate_passed,
            "minimum_extension_eigenvalue": minimum_extension,
            "marginal_residual_fro": marginal_residual,
            "swap_residual_fro": swap_residual,
            "minimum_ppt_duplicate_eigenvalue": minimum_ppt_duplicate,
            "minimum_ppt_other_eigenvalue": minimum_ppt_other,
        }
    )
    return result
