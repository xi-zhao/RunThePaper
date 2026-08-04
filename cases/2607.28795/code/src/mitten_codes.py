"""Independent construction and invariant checks for the eight mitten codes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .gf2 import hamming_weights, inverse, matmul_mod2, rank
from .group_algebra import FiniteGroupTable


@dataclass(frozen=True)
class MittenMatrices:
    hx: np.ndarray
    hz: np.ndarray
    left_a0: np.ndarray
    left_a1: np.ndarray
    right_b0: np.ndarray
    right_b1: np.ndarray


def build_checks(group: FiniteGroupTable, specification: dict[str, Any]) -> MittenMatrices:
    """Expand Eq. (2) into binary H_X and H_Z matrices."""

    a0 = tuple(specification["a0"])
    a1 = tuple(specification["a1"])
    b0 = tuple(specification["b0"])
    b1 = tuple(specification["b1"])
    left_a0 = group.left_regular(a0)
    left_a1 = group.left_regular(a1)
    right_b0 = group.right_regular(b0)
    right_b1 = group.right_regular(b1)
    left_a0_star = group.left_regular(group.star_support(a0))
    left_a1_star = group.left_regular(group.star_support(a1))
    right_b0_star = group.right_regular(group.star_support(b0))
    right_b1_star = group.right_regular(group.star_support(b1))
    zero = np.zeros_like(left_a0)

    hx = np.block(
        [
            [left_a0, zero, left_a1, zero, right_b0_star],
            [zero, left_a0, zero, left_a1, right_b1_star],
        ]
    )
    hz = np.block(
        [
            [right_b0, right_b1, zero, zero, left_a0_star],
            [zero, zero, right_b0, right_b1, left_a1_star],
        ]
    )
    return MittenMatrices(hx, hz, left_a0, left_a1, right_b0, right_b1)


def canonical_logicals(matrices: MittenMatrices) -> tuple[np.ndarray, np.ndarray]:
    """Construct the canonical logical basis of Eqs. (3)-(4)."""

    order = matrices.left_a0.shape[0]
    identity = np.eye(order, dtype=np.uint8)
    u_columns = matmul_mod2(inverse(matrices.right_b1), matrices.right_b0)
    v_columns = matmul_mod2(inverse(matrices.left_a1), matrices.left_a0)
    zero = np.zeros((order, order), dtype=np.uint8)
    logical_x = np.concatenate((identity, u_columns.T, zero, zero, zero), axis=1)
    logical_z = np.concatenate((identity, zero, v_columns.T, zero, zero), axis=1)
    return logical_x, logical_z


def analyze_code(
    group: FiniteGroupTable,
    specification: dict[str, Any],
    matrices: MittenMatrices,
) -> dict[str, Any]:
    """Recompute all algebraic Table-I/VI quantities and exact invariants."""

    order = group.order
    hx_rank = rank(matrices.hx)
    hz_rank = rank(matrices.hz)
    block_length = int(matrices.hx.shape[1])
    logical_qubits = block_length - hx_rank - hz_rank
    commutator = matmul_mod2(matrices.hx, matrices.hz.T)
    hx_weights = hamming_weights(matrices.hx)
    hz_weights = hamming_weights(matrices.hz)
    left_pivot_rank = rank(matrices.left_a1)
    right_pivot_rank = rank(matrices.right_b1)
    invariants = {
        "css_commutation": bool(not np.any(commutator)),
        "full_hx_rank": hx_rank == 2 * order,
        "full_hz_rank": hz_rank == 2 * order,
        "dimension_equals_group_order": logical_qubits == order,
        "rate_is_one_fifth": 5 * logical_qubits == block_length,
        "row_check_weight_is_nine": bool(np.all(hx_weights == 9) and np.all(hz_weights == 9)),
        "left_a1_invertible": left_pivot_rank == order,
        "right_b1_invertible": right_pivot_rank == order,
    }
    if left_pivot_rank == order and right_pivot_rank == order:
        logical_x, logical_z = canonical_logicals(matrices)
        x_kernel = matmul_mod2(matrices.hz, logical_x.T)
        z_kernel = matmul_mod2(matrices.hx, logical_z.T)
        pairing = matmul_mod2(logical_x, logical_z.T)
        x_weights = hamming_weights(logical_x)
        z_weights = hamming_weights(logical_z)
        canonical_basis = {
            "status": "constructed",
            "canonical_x_weight": int(x_weights[0]),
            "canonical_z_weight": int(z_weights[0]),
            "x_in_kernel": bool(not np.any(x_kernel)),
            "z_in_kernel": bool(not np.any(z_kernel)),
            "delta_pairing": bool(np.array_equal(pairing, np.eye(order, dtype=np.uint8))),
            "x_weight_uniform": bool(np.all(x_weights == x_weights[0])),
            "z_weight_uniform": bool(np.all(z_weights == z_weights[0])),
        }
        canonical_passed = all(
            value is True
            for key, value in canonical_basis.items()
            if key not in {"status", "canonical_x_weight", "canonical_z_weight"}
        )
    else:
        canonical_basis = {
            "status": "blocked_by_singular_pivot",
            "canonical_x_weight": None,
            "canonical_z_weight": None,
            "x_in_kernel": None,
            "z_in_kernel": None,
            "delta_pairing": None,
            "x_weight_uniform": None,
            "z_weight_uniform": None,
        }
        canonical_passed = False
    passed = all(invariants.values()) and canonical_passed
    return {
        "code_id": specification["code_id"],
        "small_group_id": list(group.small_group_id),
        "group_order": order,
        "n": block_length,
        "rank_hx": hx_rank,
        "rank_hz": hz_rank,
        "k": logical_qubits,
        "rate": logical_qubits / block_length,
        "check_weight_hx": sorted(set(int(value) for value in hx_weights)),
        "check_weight_hz": sorted(set(int(value) for value in hz_weights)),
        "canonical_x_weight": canonical_basis["canonical_x_weight"],
        "canonical_z_weight": canonical_basis["canonical_z_weight"],
        "invariants": invariants,
        "canonical_basis": canonical_basis,
        "status": "passed" if passed else "paper_claim_inconsistent",
    }
