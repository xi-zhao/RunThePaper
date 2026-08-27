"""Independent density-matrix numerics for the paper's theory curves.

This module intentionally has no reference-data or source-image loader.  It
implements only Eqs. (5), (7)-(10), (18), (20), and (21), plus the scan
geometry mapped from Figure 1 and Sections V.A-V.C.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Mapping

import numpy as np


SYMMETRIC_IDEAL_LIMIT = -1.0 / 8.0
ASYMMETRIC_IDEAL_LIMIT = (1.0 - sqrt(3.0)) / 4.0
NUMERIC_TOLERANCE = 1e-12


@dataclass(frozen=True)
class ScanResult:
    """All five visible theory sequences for one frozen target."""

    target_id: str
    angle_deg: np.ndarray
    p_ab: np.ndarray
    p_bc: np.ndarray
    p_ac: np.ndarray
    wigner: np.ndarray
    w_limit: np.ndarray
    rho: np.ndarray
    fidelity: float


def measurement_ket(angle_deg: float) -> np.ndarray:
    """Return Eq. (7) in the [H,V] basis."""

    angle_rad = np.deg2rad(angle_deg)
    return np.array(
        [np.sin(angle_rad), np.cos(angle_rad)],
        dtype=np.complex128,
    )


def source_state(w: float, xi_rad: float = pi) -> np.ndarray:
    """Return Eq. (18) in the [HH,HV,VH,VV] basis."""

    if not 0.0 <= w <= 1.0:
        raise ValueError(f"w must lie in [0,1], got {w}")
    state = np.array(
        [
            0.0,
            sqrt(w),
            np.exp(1j * xi_rad) * sqrt(1.0 - w),
            0.0,
        ],
        dtype=np.complex128,
    )
    if not np.isclose(np.vdot(state, state).real, 1.0, atol=NUMERIC_TOLERANCE):
        raise AssertionError("source state is not normalized")
    return state


def density_matrix(
    w: float,
    visibility_v: float,
    xi_rad: float = pi,
) -> np.ndarray:
    """Return the isotropic-noise density matrix in Eq. (20)."""

    if not 0.0 <= visibility_v <= 1.0:
        raise ValueError(
            f"visibility_v must lie in [0,1], got {visibility_v}"
        )
    state = source_state(w, xi_rad)
    return (
        visibility_v * np.outer(state, state.conjugate())
        + (1.0 - visibility_v) * np.eye(4, dtype=np.complex128) / 4.0
    )


def born_probability(
    rho: np.ndarray,
    alice_angle_deg: float,
    bob_angle_deg: float,
) -> float:
    """Evaluate the plus-plus Born probability for local projectors."""

    joint = np.kron(
        measurement_ket(alice_angle_deg),
        measurement_ket(bob_angle_deg),
    )
    value = np.vdot(joint, rho @ joint)
    if abs(value.imag) > NUMERIC_TOLERANCE:
        raise AssertionError(f"Born probability has imaginary part {value.imag}")
    return float(value.real)


def wigner_components(
    rho: np.ndarray,
    theta_alice_deg: float,
    theta_bob_deg: float,
    spacing_deg: float,
) -> tuple[float, float, float, float]:
    """Evaluate the three probability terms and Eq. (5)."""

    alice_a = theta_alice_deg
    alice_b = theta_alice_deg + spacing_deg
    bob_b_prime = theta_bob_deg + spacing_deg
    bob_c_prime = theta_bob_deg + 2.0 * spacing_deg

    p_ab = born_probability(rho, alice_a, bob_b_prime)
    p_bc = born_probability(rho, alice_b, bob_c_prime)
    p_ac = born_probability(rho, alice_a, bob_c_prime)
    wigner = p_ab + p_bc - p_ac
    return p_ab, p_bc, p_ac, wigner


def singlet_fidelity(w: float, visibility_v: float) -> float:
    """Evaluate the singlet fidelity derived from Eq. (21)."""

    pure_overlap = 0.5 + sqrt(w * (1.0 - w))
    return visibility_v * pure_overlap + (1.0 - visibility_v) / 4.0


def ideal_violation_limit(target_id: str) -> float:
    """Return the visible analytic line for the target panel."""

    if target_id in {"T-FIG003", "T-FIG004"}:
        return SYMMETRIC_IDEAL_LIMIT
    if target_id in {"T-FIG005A", "T-FIG005B"}:
        return ASYMMETRIC_IDEAL_LIMIT
    raise ValueError(f"unknown target_id {target_id}")


def _angle_grid(params: Mapping[str, object]) -> np.ndarray:
    step = float(params.get("grid_step_deg", 0.5))
    if step <= 0.0:
        raise ValueError("grid_step_deg must be positive")
    count = int(round(360.0 / step))
    if not np.isclose(count * step, 360.0, atol=NUMERIC_TOLERANCE):
        raise ValueError("grid_step_deg must divide 360 exactly")
    return np.linspace(0.0, 360.0, count + 1, dtype=np.float64)


def _scan_angles(
    target_id: str,
    coordinate_deg: float,
    params: Mapping[str, object],
) -> tuple[float, float, float]:
    if target_id == "T-FIG003":
        return (
            float(params["theta_alice_deg"]),
            float(params["theta_bob_deg"]),
            coordinate_deg,
        )
    spacing = float(params["basis_spacing_deg"])
    if target_id == "T-FIG004":
        origin_offset = float(params["common_absolute_origin_offset_deg"])
        basis_start = coordinate_deg + origin_offset
        return basis_start, basis_start, spacing
    if target_id == "T-FIG005A":
        return (
            float(params["theta_alice_fixed_deg"]),
            coordinate_deg,
            spacing,
        )
    if target_id == "T-FIG005B":
        return (
            coordinate_deg,
            float(params["theta_bob_fixed_deg"]),
            spacing,
        )
    raise ValueError(f"unknown target_id {target_id}")


def scan_target(
    target_id: str,
    params: Mapping[str, object],
) -> ScanResult:
    """Generate all paper-visible theory sequences for exactly one target."""

    w = float(params["w"])
    visibility_v = float(params["visibility_v"])
    phase = params.get("phase_xi")
    if phase != "pi":
        raise ValueError(f"the frozen paper fit requires phase_xi='pi', got {phase}")
    rho = density_matrix(w, visibility_v, pi)
    angles = _angle_grid(params)

    p_ab = np.empty_like(angles)
    p_bc = np.empty_like(angles)
    p_ac = np.empty_like(angles)
    wigner = np.empty_like(angles)
    for index, coordinate in enumerate(angles):
        theta_alice, theta_bob, spacing = _scan_angles(
            target_id,
            float(coordinate),
            params,
        )
        p_ab[index], p_bc[index], p_ac[index], wigner[index] = (
            wigner_components(
                rho,
                theta_alice,
                theta_bob,
                spacing,
            )
        )

    limit = ideal_violation_limit(target_id)
    return ScanResult(
        target_id=target_id,
        angle_deg=angles,
        p_ab=p_ab,
        p_bc=p_bc,
        p_ac=p_ac,
        wigner=wigner,
        w_limit=np.full_like(angles, limit),
        rho=rho,
        fidelity=singlet_fidelity(w, visibility_v),
    )


def ideal_scan(target_id: str, grid_step_deg: float = 0.5) -> ScanResult:
    """Return the ideal-singlet scan for independent limit checks."""

    common: dict[str, object] = {
        "w": 0.5,
        "visibility_v": 1.0,
        "phase_xi": "pi",
        "grid_step_deg": grid_step_deg,
    }
    if target_id == "T-FIG003":
        common.update(
            {
                "theta_alice_deg": 0.0,
                "theta_bob_deg": 0.0,
            }
        )
    elif target_id == "T-FIG004":
        common.update(
            {
                "basis_spacing_deg": 30.0,
                "common_absolute_origin_offset_deg": -30.0,
            }
        )
    elif target_id == "T-FIG005A":
        common.update(
            {
                "basis_spacing_deg": 30.0,
                "theta_alice_fixed_deg": 0.0,
            }
        )
    elif target_id == "T-FIG005B":
        common.update(
            {
                "basis_spacing_deg": 30.0,
                "theta_bob_fixed_deg": 0.0,
            }
        )
    else:
        raise ValueError(f"unknown target_id {target_id}")
    return scan_target(target_id, common)


def periodicity_error(result: ScanResult) -> float:
    """Return the largest 180-degree periodicity residual."""

    step = float(result.angle_deg[1] - result.angle_deg[0])
    offset = int(round(180.0 / step))
    fields = (
        result.p_ab,
        result.p_bc,
        result.p_ac,
        result.wigner,
        result.w_limit,
    )
    return max(
        float(np.max(np.abs(values[:-offset] - values[offset:])))
        for values in fields
    )


def physical_checks(result: ScanResult) -> dict[str, object]:
    """Build target-specific, machine-checkable scientific assertions."""

    hermiticity_error = float(
        np.max(np.abs(result.rho - result.rho.conjugate().T))
    )
    trace_error = float(abs(np.trace(result.rho).real - 1.0))
    min_eigenvalue = float(np.linalg.eigvalsh(result.rho).min())
    probability_min = float(
        min(result.p_ab.min(), result.p_bc.min(), result.p_ac.min())
    )
    probability_max = float(
        max(result.p_ab.max(), result.p_bc.max(), result.p_ac.max())
    )
    identity_error = float(
        np.max(
            np.abs(
                result.wigner - (result.p_ab + result.p_bc - result.p_ac)
            )
        )
    )
    periodic_error = periodicity_error(result)
    ideal = ideal_scan(result.target_id)
    ideal_minimum = float(ideal.wigner.min())
    expected_limit = ideal_violation_limit(result.target_id)
    ideal_limit_error = abs(ideal_minimum - expected_limit)

    assertions = {
        "density_matrix_hermitian": {
            "status": "passed"
            if hermiticity_error <= NUMERIC_TOLERANCE
            else "failed",
            "value": hermiticity_error,
            "tolerance": NUMERIC_TOLERANCE,
        },
        "density_matrix_trace_one": {
            "status": "passed"
            if trace_error <= NUMERIC_TOLERANCE
            else "failed",
            "value": trace_error,
            "tolerance": NUMERIC_TOLERANCE,
        },
        "density_matrix_positive_semidefinite": {
            "status": "passed"
            if min_eigenvalue >= -NUMERIC_TOLERANCE
            else "failed",
            "value": min_eigenvalue,
            "tolerance": NUMERIC_TOLERANCE,
        },
        "born_probabilities_bounded": {
            "status": "passed"
            if probability_min >= -NUMERIC_TOLERANCE
            and probability_max <= 1.0 + NUMERIC_TOLERANCE
            else "failed",
            "minimum": probability_min,
            "maximum": probability_max,
        },
        "wigner_identity": {
            "status": "passed"
            if identity_error <= NUMERIC_TOLERANCE
            else "failed",
            "value": identity_error,
            "tolerance": NUMERIC_TOLERANCE,
        },
        "projector_periodicity_180_deg": {
            "status": "passed"
            if periodic_error <= 5e-12
            else "failed",
            "value": periodic_error,
            "tolerance": 5e-12,
        },
        "ideal_analytic_minimum": {
            "status": "passed"
            if ideal_limit_error <= 5e-12
            else "failed",
            "value": ideal_minimum,
            "expected": expected_limit,
            "absolute_error": ideal_limit_error,
            "tolerance": 5e-12,
        },
        "all_visible_theory_series_generated": {
            "status": "passed",
            "series": [
                "W_MODEL",
                "P_AB",
                "P_BC",
                "P_AC",
                "W_LIMIT",
            ],
            "count": 5,
        },
    }
    return {
        "status": "passed"
        if all(
            item["status"] == "passed"
            for item in assertions.values()
        )
        else "failed",
        "assertions": assertions,
        "metrics": {
            "wigner_minimum": float(result.wigner.min()),
            "wigner_minimum_angle_deg": float(
                result.angle_deg[int(np.argmin(result.wigner))]
            ),
            "wigner_maximum": float(result.wigner.max()),
            "wigner_mean": float(result.wigner.mean()),
            "singlet_fidelity_from_rounded_parameters": result.fidelity,
        },
    }
