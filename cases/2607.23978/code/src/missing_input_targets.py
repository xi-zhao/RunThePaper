"""Formula-level runners for targets whose public definitions are missing.

The module accepts analytic matrix expressions, never sampled author curves or
source-image pixels.  It therefore makes the numerical path executable without
pretending that the absent Supplemental Material is known.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from src.sensing import (
    encoded_state,
    expectation,
    fisher_information_hermitian,
    normalized_fringe,
)


_FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "conj": np.conjugate,
    "real": np.real,
    "imag": np.imag,
}
_CONSTANTS = {"pi": np.pi, "j": 1j}


class ScientificInputError(ValueError):
    """Raised when formula-level scientific input violates the contract."""


def evaluate_expression(expression: str, variables: dict[str, float]) -> complex:
    """Evaluate a small arithmetic expression without Python ``eval``."""
    if not isinstance(expression, str) or not expression.strip():
        raise ScientificInputError("matrix entries must be non-empty expressions")
    try:
        node = ast.parse(expression, mode="eval").body
    except SyntaxError as exc:
        raise ScientificInputError(f"invalid expression: {expression!r}") from exc

    def visit(current: ast.AST) -> complex:
        if isinstance(current, ast.Constant) and isinstance(current.value, (int, float, complex)):
            return complex(current.value)
        if isinstance(current, ast.Name):
            if current.id in variables:
                return complex(variables[current.id])
            if current.id in _CONSTANTS:
                return complex(_CONSTANTS[current.id])
            raise ScientificInputError(f"unknown symbol {current.id!r}")
        if isinstance(current, ast.UnaryOp) and isinstance(current.op, (ast.UAdd, ast.USub)):
            value = visit(current.operand)
            return value if isinstance(current.op, ast.UAdd) else -value
        if isinstance(current, ast.BinOp) and isinstance(
            current.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
        ):
            left, right = visit(current.left), visit(current.right)
            if isinstance(current.op, ast.Add):
                return left + right
            if isinstance(current.op, ast.Sub):
                return left - right
            if isinstance(current.op, ast.Mult):
                return left * right
            if isinstance(current.op, ast.Div):
                return left / right
            return left**right
        if (
            isinstance(current, ast.Call)
            and isinstance(current.func, ast.Name)
            and current.func.id in _FUNCTIONS
            and len(current.args) == 1
            and not current.keywords
        ):
            return complex(_FUNCTIONS[current.func.id](visit(current.args[0])))
        raise ScientificInputError(f"unsupported expression element: {ast.dump(current)}")

    value = visit(node)
    if not np.isfinite(value.real) or not np.isfinite(value.imag):
        raise ScientificInputError(f"expression is non-finite: {expression!r}")
    return value


def matrix_from_expressions(spec: Any, variables: dict[str, float]) -> np.ndarray:
    """Build one 2x2 matrix from formula strings."""
    if (
        not isinstance(spec, list)
        or len(spec) != 2
        or any(not isinstance(row, list) or len(row) != 2 for row in spec)
    ):
        raise ScientificInputError("each observable or POVM element must be a 2x2 expression matrix")
    return np.asarray(
        [[evaluate_expression(entry, variables) for entry in row] for row in spec],
        dtype=complex,
    )


def validate_scientific_input(payload: dict[str, Any]) -> None:
    """Require formula provenance and reject array/pixel substitution."""
    if payload.get("schema_version") != 1:
        raise ScientificInputError("scientific input schema_version must be 1")
    provenance = payload.get("formula_provenance")
    if not isinstance(provenance, dict):
        raise ScientificInputError("formula_provenance is required")
    source_refs = provenance.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs or not all(
        isinstance(ref, str) and ref.strip() for ref in source_refs
    ):
        raise ScientificInputError("formula_provenance.source_refs must be non-empty")
    digest = provenance.get("transcription_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest.lower()
    ):
        raise ScientificInputError("formula_provenance.transcription_sha256 must be a SHA-256 digest")
    forbidden = {"sampled_curve", "author_array", "source_pixels", "digitized_points"}
    if forbidden.intersection(payload):
        raise ScientificInputError("sampled author data and source pixels are forbidden scientific inputs")


def reproduce_nonoptimal_series(
    payload: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Generate the missing Fig. 2 theory series from disclosed A1/A2 formulas."""
    formulas = payload.get("nonoptimal_observables")
    if not isinstance(formulas, dict) or set(formulas) != {"A1", "A2"}:
        raise ScientificInputError("nonoptimal_observables must define exactly A1 and A2")
    theta = float(parameters["theta_reference_over_pi"]) * np.pi
    phi_over_pi = np.linspace(
        float(parameters["phi_over_pi_min"]),
        float(parameters["phi_over_pi_max"]),
        int(parameters["phi_points"]),
    )
    phi = phi_over_pi * np.pi
    series: dict[str, Any] = {"phi_over_pi": phi_over_pi.tolist(), "by_p": {}}
    for raw_p in parameters["fringe_p_values"]:
        p = float(raw_p)
        variables = {"p": p, "theta": theta}
        rho = encoded_state(p, theta)
        a1 = matrix_from_expressions(formulas["A1"], variables)
        a2 = matrix_from_expressions(formulas["A2"], variables)
        entry: dict[str, Any] = {}
        for name, observable in {"A1": a1, "A2": a2, "A2_dagger": a2.conjugate().T}.items():
            mean = expectation(rho, observable)
            entry[name] = {
                "fringe": normalized_fringe(rho, observable, phi).tolist(),
                "expectation_real": float(mean.real),
                "expectation_imag": float(mean.imag),
            }
        series["by_p"][str(p)] = entry
    return series


def reproduce_complete_povm(
    payload: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Evaluate the complete-POVM CFI from formula-defined 2x2 effects."""
    contract = payload.get("complete_povm")
    if not isinstance(contract, dict):
        raise ScientificInputError("complete_povm formula contract is required")
    elements = contract.get("elements")
    if not isinstance(elements, list) or len(elements) < 2:
        raise ScientificInputError("complete_povm.elements must contain at least two effects")
    p = float(contract.get("p", parameters["fringe_p_values"][-1]))
    theta_center = float(parameters["theta_reference_over_pi"]) * np.pi
    step = float(parameters["theta_derivative_step"])

    def probabilities(theta: float) -> tuple[np.ndarray, dict[str, float]]:
        variables = {"p": p, "theta": theta}
        effects = [matrix_from_expressions(row["matrix"], variables) for row in elements]
        rho = encoded_state(p, theta)
        probs = np.asarray([expectation(rho, effect).real for effect in effects])
        completeness = np.linalg.norm(sum(effects, np.zeros((2, 2), dtype=complex)) - np.eye(2))
        hermiticity = max(np.linalg.norm(effect - effect.conjugate().T) for effect in effects)
        min_eigenvalue = min(float(np.linalg.eigvalsh(effect).min()) for effect in effects)
        checks = {
            "completeness_error": float(completeness),
            "hermiticity_error": float(hermiticity),
            "minimum_eigenvalue": min_eigenvalue,
            "normalization_error": float(abs(probs.sum() - 1.0)),
        }
        return probs, checks

    center, checks = probabilities(theta_center)
    plus, _ = probabilities(theta_center + step)
    minus, _ = probabilities(theta_center - step)
    derivative = (plus - minus) / (2.0 * step)
    if np.any(center <= 0.0):
        raise ScientificInputError("complete POVM probabilities must be strictly positive at the test point")
    cfi = float(np.sum(derivative**2 / center))
    bound = float(fisher_information_hermitian(p))
    tolerance = float(contract.get("bound_tolerance", 1e-9))
    physical = (
        checks["completeness_error"] <= 1e-9
        and checks["hermiticity_error"] <= 1e-9
        and checks["minimum_eigenvalue"] >= -1e-9
        and checks["normalization_error"] <= 1e-9
    )
    return {
        "p": p,
        "theta": theta_center,
        "probabilities": center.tolist(),
        "classical_fisher_information": cfi,
        "hermitian_optimum": bound,
        "bound_tolerance": tolerance,
        "bound_passed": bool(cfi <= bound + tolerance),
        "physical_povm_passed": bool(physical),
        "physical_checks": checks,
    }


def load_formula_input(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ScientificInputError("scientific input must be a JSON object")
    validate_scientific_input(payload)
    payload["_input_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload
