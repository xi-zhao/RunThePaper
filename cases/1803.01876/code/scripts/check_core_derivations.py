#!/usr/bin/env python3
"""Symbolic checks for the first derivation pass."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "outputs/checks/core_derivations.json"


def main() -> int:
    t1, t2, t3, gamma, k, beta, E = sp.symbols("t1 t2 t3 gamma k beta E", nonzero=True)
    i = sp.I

    dx = t1 + t2 * sp.cos(k)
    dy = t2 * sp.sin(k)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])

    h = dx * sx + (dy + i * gamma / 2) * sy
    h_expected = sp.Matrix(
        [
            [0, t1 + gamma / 2 + t2 * sp.exp(-i * k)],
            [t1 - gamma / 2 + t2 * sp.exp(i * k), 0],
        ]
    )

    checks: list[dict[str, object]] = []
    checks.append(
        check_matrix(
            "EQC001_matrix_form",
            h.subs({sp.cos(k): (sp.exp(i * k) + sp.exp(-i * k)) / 2, sp.sin(k): (sp.exp(i * k) - sp.exp(-i * k)) / (2 * i)}),
            h_expected,
        )
    )

    checks.append(
        check_matrix(
            "EQC001_chiral_symmetry",
            sz * h_expected * sz,
            -h_expected,
        )
    )

    e_squared_from_matrix = sp.simplify(h_expected[0, 1] * h_expected[1, 0])
    e_squared_from_paper = sp.simplify(dx**2 + (dy + i * gamma / 2) ** 2)
    e_squared_from_paper_exp = e_squared_from_paper.subs(
        {
            sp.cos(k): (sp.exp(i * k) + sp.exp(-i * k)) / 2,
            sp.sin(k): (sp.exp(i * k) - sp.exp(-i * k)) / (2 * i),
        }
    )
    checks.append(
        check_expr(
            "EQC002_eigenvalue_square",
            e_squared_from_matrix,
            e_squared_from_paper_exp,
        )
    )
    checks.append(check_open_chain_matrix_entries())

    a = t1 - gamma / 2
    b = t1 + gamma / 2
    beta_equation = sp.expand((a + t2 * beta) * (b + t2 / beta) - E**2)
    quadratic = sp.expand(beta * beta_equation)
    expected_quadratic = sp.expand(t2 * b * beta**2 + (t1**2 - gamma**2 / 4 + t2**2 - E**2) * beta + t2 * a)
    checks.append(check_expr("EQC006_beta_quadratic", quadratic, expected_quadratic))

    numerator = E**2 + gamma**2 / 4 - t1**2 - t2**2
    discriminant = numerator**2 - 4 * t2**2 * (t1**2 - gamma**2 / 4)
    beta_plus = (numerator + sp.sqrt(discriminant)) / (2 * t2 * b)
    beta_minus = (numerator - sp.sqrt(discriminant)) / (2 * t2 * b)
    checks.append(
        check_expr(
            "EQC006_beta_root_sum",
            sp.simplify(beta_plus + beta_minus),
            sp.simplify(-(t1**2 - gamma**2 / 4 + t2**2 - E**2) / (t2 * b)),
        )
    )
    checks.append(
        check_expr(
            "EQC006_beta_root_product",
            sp.simplify(beta_plus * beta_minus),
            sp.simplify(a / b),
        )
    )
    checks.append(check_open_boundary_bulk_spectrum_formula())

    transition_expr = sp.solve(sp.Eq((t1 - gamma / 2) * (t1 + gamma / 2), t2**2), t1)
    transition_expected = {-sp.sqrt(gamma**2 / 4 + t2**2), sp.sqrt(gamma**2 / 4 + t2**2)}
    root_residuals = sorted(
        [sp.simplify(lhs - rhs) for lhs, rhs in zip(sorted(transition_expr, key=str), sorted(transition_expected, key=str))],
        key=str,
    )
    checks.append(
        {
            "name": "EQC005_transition_roots",
            "passed": all(item == 0 for item in root_residuals),
            "lhs": [str(item) for item in sorted(transition_expr, key=str)],
            "rhs": [str(item) for item in sorted(transition_expected, key=str)],
            "residuals": [str(item) for item in root_residuals],
        }
    )

    a_beta = t1 - gamma / 2 + t2 * beta
    b_beta = t1 + gamma / 2 + t2 / beta
    energy = sp.sqrt(a_beta * b_beta)
    q = -b_beta / energy
    q_inv = -a_beta / energy
    h_beta = sp.Matrix([[0, b_beta], [a_beta, 0]])
    q_matrix = sp.Matrix([[0, q], [q_inv, 0]])
    checks.append(check_matrix("EQC009_Q_flattening", q_matrix, -h_beta / energy))
    checks.append(check_expr("EQC009_q_inverse", sp.simplify(q * q_inv), sp.Integer(1)))
    checks.append(check_matrix("EQC009_Q_squared", q_matrix * q_matrix, sp.eye(2)))
    checks.append(check_numeric_winding_sanity())

    a_t3 = t3 / beta + (t1 - gamma / 2) + t2 * beta
    b_t3 = t2 / beta + (t1 + gamma / 2) + t3 * beta
    t3_equation = sp.expand(beta**2 * (a_t3 * b_t3 - E**2))
    expected_t3_quartic = sp.expand(
        t2 * t3 * beta**4
        + ((t1 - gamma / 2) * t3 + (t1 + gamma / 2) * t2) * beta**3
        + (t2**2 + (t1 - gamma / 2) * (t1 + gamma / 2) + t3**2 - E**2) * beta**2
        + ((t1 + gamma / 2) * t3 + (t1 - gamma / 2) * t2) * beta
        + t2 * t3
    )
    checks.append(check_expr("EQC010_t3_quartic", t3_equation, expected_t3_quartic))

    passed = all(item["passed"] for item in checks)
    result = {
        "status": "passed" if passed else "failed",
        "checks": checks,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


def check_matrix(name: str, lhs: sp.Matrix, rhs: sp.Matrix) -> dict[str, object]:
    diff = sp.simplify(lhs - rhs)
    passed = all(sp.simplify(value) == 0 for value in diff)
    return {
        "name": name,
        "passed": passed,
        "max_symbolic_residual": "0" if passed else str(diff),
    }


def check_expr(name: str, lhs: sp.Expr, rhs: sp.Expr) -> dict[str, object]:
    residual = sp.simplify(lhs - rhs)
    return {
        "name": name,
        "passed": residual == 0,
        "residual": str(residual),
    }


def check_open_chain_matrix_entries() -> dict[str, object]:
    import sys

    src_path = str(ROOT / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from nonhermitian_ssh import open_chain_hamiltonian

    L = 3
    t1 = 0.4
    t2 = 1.2
    gamma = 0.6
    actual = open_chain_hamiltonian(L=L, t1=t1, t2=t2, gamma=gamma, t3=0.0)
    expected = np.zeros((2 * L, 2 * L), dtype=np.complex128)

    for n in range(L):
        a = 2 * n
        b = a + 1
        expected[a, b] = t1 + gamma / 2.0
        expected[b, a] = t1 - gamma / 2.0
        if n > 0:
            expected[a, 2 * (n - 1) + 1] = t2
        if n < L - 1:
            expected[b, 2 * (n + 1)] = t2

    residual = actual - expected
    max_abs_residual = float(np.max(np.abs(residual)))
    return {
        "name": "EQC003_open_chain_matrix_entries",
        "passed": bool(max_abs_residual < 1e-12),
        "matrix_size": int(actual.shape[0]),
        "basis_order": "(A1, B1, A2, B2, ...)",
        "checked_entries": [
            "H[A_n,B_n]=t1+gamma/2",
            "H[B_n,A_n]=t1-gamma/2",
            "H[A_n,B_{n-1}]=t2",
            "H[B_n,A_{n+1}]=t2",
        ],
        "max_abs_residual": max_abs_residual,
    }


def check_open_boundary_bulk_spectrum_formula() -> dict[str, object]:
    import sys

    src_path = str(ROOT / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from nonhermitian_ssh import generalized_brillouin_radius, non_bloch_ab

    t2 = 1.0
    gamma = 4.0 / 3.0
    t1_values = [-1.4, -0.4, 0.4, 1.4]
    k_values = np.linspace(0.0, 2.0 * np.pi, 17, endpoint=False)
    max_abs_residual = 0.0
    sector_results = []

    for t1_value in t1_values:
        radius = generalized_brillouin_radius(t1=t1_value, gamma=gamma)
        beta_values = radius * np.exp(1j * k_values)
        a_beta, b_beta = non_bloch_ab(beta=beta_values, t1=t1_value, t2=t2, gamma=gamma)
        from_code = a_beta * b_beta
        paper_formula = (
            t1_value**2
            + t2**2
            - gamma**2 / 4.0
            + t2
            * np.sqrt(abs(t1_value**2 - gamma**2 / 4.0))
            * (
                np.sign(t1_value + gamma / 2.0) * np.exp(1j * k_values)
                + np.sign(t1_value - gamma / 2.0) * np.exp(-1j * k_values)
            )
        )
        residual = float(np.max(np.abs(from_code - paper_formula)))
        max_abs_residual = max(max_abs_residual, residual)
        sector_results.append(
            {
                "t1": t1_value,
                "radius": float(radius),
                "sign_t1_plus_gamma_over_2": int(np.sign(t1_value + gamma / 2.0)),
                "sign_t1_minus_gamma_over_2": int(np.sign(t1_value - gamma / 2.0)),
                "max_abs_residual": residual,
            }
        )

    return {
        "name": "EQC008_open_boundary_spectrum_formula",
        "passed": bool(max_abs_residual < 1e-12),
        "checked_identity": "non_bloch_ab(beta=r exp(ik)) product equals paper Eq. spectra",
        "sampled_t1_sectors": sector_results,
        "k_samples": int(len(k_values)),
        "max_abs_residual": max_abs_residual,
    }


def check_numeric_winding_sanity() -> dict[str, object]:
    probes = {
        "-1.4": 0,
        "-1.0": 1,
        "0.0": 1,
        "1.0": 1,
        "1.4": 0,
    }
    observed = {
        key: winding_number_t3_zero(t1=float(key), t2=1.0, gamma=4.0 / 3.0)
        for key in probes
    }
    return {
        "name": "EQC009_winding_sanity",
        "passed": observed == probes,
        "observed": observed,
        "expected": probes,
    }


def winding_number_t3_zero(t1: float, t2: float, gamma: float, samples: int = 4096) -> int:
    denominator = t1 + gamma / 2.0
    if abs(denominator) < 1e-12:
        raise ValueError("C_beta radius is singular at t1 = -gamma/2")
    radius = np.sqrt(abs((t1 - gamma / 2.0) / denominator))
    angles = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    beta_values = radius * np.exp(1j * angles)
    a_values = t1 - gamma / 2.0 + t2 * beta_values
    b_values = t1 + gamma / 2.0 + t2 / beta_values
    wind_a = phase_winding(a_values)
    wind_b = phase_winding(b_values)
    return int(round((wind_a - wind_b) / 2.0))


def phase_winding(values: np.ndarray) -> float:
    phase = np.unwrap(np.angle(values))
    closed_phase = np.unwrap(np.angle(np.concatenate([values, values[:1]])))
    return float((closed_phase[-1] - closed_phase[0]) / (2.0 * np.pi))


if __name__ == "__main__":
    raise SystemExit(main())
