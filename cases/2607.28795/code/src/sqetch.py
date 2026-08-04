"""Source-blind implementation of Appendix-H sketch information-set decoding."""

from __future__ import annotations

from math import comb
from time import perf_counter
from typing import Any

import numpy as np

from .gf2 import hamming_weights, matmul_mod2, nullspace, rref


def sketch_inclusion_probability(nullity: int, required_rows: int, sketch_rows: int) -> float:
    """Eq. (H9): probability every required basis row appears in the sketch."""

    if not 0 <= required_rows <= nullity or sketch_rows < 0 or nullity <= 0:
        raise ValueError("invalid inclusion-probability parameters")
    return float(
        sum(
            (-1) ** missing
            * comb(required_rows, missing)
            * ((nullity - missing) / nullity) ** sketch_rows
            for missing in range(required_rows + 1)
        )
    )


def approximate_hit_probability(single_trial_probability: float, trials: int) -> float:
    """Independent-trial amplification used to sanity-check the H11-H13 model."""

    if not 0.0 <= single_trial_probability <= 1.0 or trials < 0:
        raise ValueError("invalid hit-probability parameters")
    return float(1.0 - (1.0 - single_trial_probability) ** trials)


def steane_check_matrix() -> np.ndarray:
    """A conventional parity-check matrix for the [[7,1,3]] Steane code."""

    return np.asarray(
        [
            [1, 0, 1, 0, 1, 0, 1],
            [0, 1, 1, 0, 0, 1, 1],
            [0, 0, 0, 1, 1, 1, 1],
        ],
        dtype=np.uint8,
    )


def _logical_candidate_weights(candidates: np.ndarray, opposite_nullspace: np.ndarray) -> list[int]:
    if candidates.size == 0:
        return []
    nonzero = candidates[np.any(candidates, axis=1)]
    if nonzero.size == 0:
        return []
    syndromes = matmul_mod2(opposite_nullspace, nonzero.T)
    logical_mask = np.any(syndromes, axis=0)
    return [int(value) for value in hamming_weights(nonzero[logical_mask])]


def sketch_trial(
    null_basis: np.ndarray,
    opposite_nullspace: np.ndarray,
    sketch_rows: int,
    rng: np.random.Generator,
) -> list[int]:
    """One Algorithm-1 trial: sampled rows, column permutation, RREF, logical test."""

    nullity, columns = null_basis.shape
    if nullity == 0 or sketch_rows <= 0:
        return []
    sampled_indices = rng.integers(0, nullity, size=sketch_rows)
    permutation = rng.permutation(columns)
    sampled = null_basis[sampled_indices][:, permutation]
    reduced, _ = rref(sampled)
    restored = np.zeros_like(reduced)
    restored[:, permutation] = reduced
    return _logical_candidate_weights(restored, opposite_nullspace)


def full_basis_trial(
    null_basis: np.ndarray,
    opposite_nullspace: np.ndarray,
    rng: np.random.Generator,
) -> list[int]:
    """A transparent full-nullspace RREF baseline, not the paper's QDistRnd code."""

    permutation = rng.permutation(null_basis.shape[1])
    reduced, _ = rref(null_basis[:, permutation])
    restored = np.zeros_like(reduced)
    restored[:, permutation] = reduced
    return _logical_candidate_weights(restored, opposite_nullspace)


def estimate_minimum_weight(
    check_for_kernel: np.ndarray,
    opposite_check: np.ndarray,
    *,
    sketch_rows: int,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    """Run bounded sketch trials and return the best logical weight found."""

    null_basis = nullspace(check_for_kernel)
    opposite_nullspace = nullspace(opposite_check)
    rng = np.random.default_rng(seed)
    best: int | None = None
    candidates_total = 0
    for _ in range(trials):
        weights = sketch_trial(null_basis, opposite_nullspace, sketch_rows, rng)
        candidates_total += len(weights)
        if weights:
            trial_best = min(weights)
            best = trial_best if best is None else min(best, trial_best)
    return {
        "nullity": int(null_basis.shape[0]),
        "sketch_rows": int(sketch_rows),
        "trials": int(trials),
        "logical_candidates": candidates_total,
        "best_weight": best,
    }


def benchmark_methods(
    check_for_kernel: np.ndarray,
    opposite_check: np.ndarray,
    *,
    sketch_rows: int,
    sketch_trials: int,
    baseline_trials: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Measure reduced-scale sketch and full-nullspace RREF costs."""

    null_basis = nullspace(check_for_kernel)
    opposite_nullspace = nullspace(opposite_check)
    rows: list[dict[str, Any]] = []
    for method, trials in (("sqetch", sketch_trials), ("full_nullspace_rref", baseline_trials)):
        rng = np.random.default_rng(seed + (0 if method == "sqetch" else 1))
        best: int | None = None
        candidate_count = 0
        started = perf_counter()
        for _ in range(trials):
            if method == "sqetch":
                weights = sketch_trial(null_basis, opposite_nullspace, sketch_rows, rng)
            else:
                weights = full_basis_trial(null_basis, opposite_nullspace, rng)
            candidate_count += len(weights)
            if weights:
                trial_best = min(weights)
                best = trial_best if best is None else min(best, trial_best)
        elapsed = perf_counter() - started
        rows.append(
            {
                "method": method,
                "trials": trials,
                "elapsed_seconds": elapsed,
                "seconds_per_trial": elapsed / trials,
                "logical_candidates": candidate_count,
                "best_weight": best,
                "nullity": int(null_basis.shape[0]),
                "sketch_rows": sketch_rows if method == "sqetch" else int(null_basis.shape[0]),
            }
        )
    return rows
