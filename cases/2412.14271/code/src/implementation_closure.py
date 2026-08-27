from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import numpy as np

from dicke import one_photon_branches, one_photon_steady_state_ed


ITEMS_BY_TARGET = {
    "T001": tuple(f"Main Fig. 2({panel})" for panel in "abcdefg"),
    "T006": (
        "Formal Fig. S3 (panel inventory unavailable)",
        "Formal Fig. S4 (panel inventory unavailable)",
    ),
}


def _finite_or_none(values: np.ndarray) -> list[float | None]:
    return [float(value) if np.isfinite(value) else None for value in np.asarray(values, dtype=float)]


def _run_fig2_attestation(config: dict[str, Any]) -> dict[str, Any]:
    lambdas = np.asarray(config["lambdas"], dtype=float)
    branches = one_photon_branches(
        lambdas,
        omega_c=float(config["omega_c"]),
        omega_a=float(config["omega_a"]),
        kappa1=float(config["kappa1"]),
    )
    started = time.monotonic()
    ed_rows = []
    for cutoff in config["cutoffs"]:
        for coupling in lambdas:
            row_started = time.monotonic()
            result = one_photon_steady_state_ed(
                int(config["system_size"]),
                int(cutoff),
                float(coupling),
                omega_c=float(config["omega_c"]),
                omega_a=float(config["omega_a"]),
                kappa1=float(config["kappa1"]),
            )
            ed_rows.append(
                {
                    key: value.tolist() if isinstance(value, np.ndarray) else value
                    for key, value in result.items()
                }
                | {"runtime_seconds": time.monotonic() - row_started}
            )
    tolerances = config["acceptance_tolerances"]
    passed = (
        np.isclose(branches["lambda_c"], np.sqrt(config["kappa1"] ** 2 + 4 * config["omega_c"] ** 2) / 4)
        and all(row["trace_error"] <= tolerances["trace_error"] for row in ed_rows)
        and all(row["hermiticity_error"] <= tolerances["hermiticity_error"] for row in ed_rows)
        and all(row["minimum_density_eigenvalue"] >= -tolerances["positivity"] for row in ed_rows)
        and all(row["liouvillian_residual"] <= tolerances["liouvillian_residual"] for row in ed_rows)
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "mean_field": {
            "lambda": lambdas.tolist(),
            "lambda_c": float(branches["lambda_c"]),
            "normal_photons": branches["normal_photons"].tolist(),
            "normal_jz": branches["normal_jz"].tolist(),
            "super_photons": _finite_or_none(branches["super_photons"]),
            "super_jx_positive": _finite_or_none(branches["super_jx_positive"]),
            "super_jx_negative": _finite_or_none(branches["super_jx_negative"]),
            "super_jz": _finite_or_none(branches["super_jz"]),
        },
        "steady_state_ed": ed_rows,
        "runtime_seconds": time.monotonic() - started,
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _blocked_formal_supplement(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("status") != "missing_indispensable_input":
        raise ValueError("formal supplement status must remain missing until a verified source is frozen")
    if config.get("supplement_sha256") is not None:
        raise ValueError("supplement_sha256 must be null while the supplement is unavailable")
    required_fields = tuple(config.get("required_fields", ()))
    if not required_fields:
        raise ValueError("required_fields must declare the unblock schema")
    figures = config.get("figures")
    if not isinstance(figures, dict) or set(figures) != {"S3", "S4"}:
        raise ValueError("figures must declare exactly S3 and S4")
    for figure_id, declaration in figures.items():
        if not isinstance(declaration, dict):
            raise ValueError(f"{figure_id} declaration must be an object")
        if any(declaration.get(field) is not None for field in required_fields):
            raise ValueError(f"{figure_id} fields must remain null until source acquisition")
    return {
        "status": "input_blocked",
        "paper_exact_status": "input_blocked",
        "reason": "The authorized formal supplement is absent; panel inventories, observables, parameters, and acceptance conditions are not guessed.",
        "required_input_schema": config,
        "scientific_coverage_changed": False,
    }


def run_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if config.get("paper_id") != "2412.14271":
        raise ValueError("paper_id must be 2412.14271")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if parameters.get("profile") != "reduced_implementation_attestation":
        raise ValueError("only the frozen reduced implementation-attestation profile is accepted")
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    fig2 = _run_fig2_attestation(parameters["fig2"])
    supplement = _blocked_formal_supplement(parameters["formal_supplement"])
    target_checks = {"T001": fig2, "T006": supplement}
    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": "attested" if target_id == "T001" else "input_contract_attested",
            "scientific_coverage_changed": False,
        }
        for target_id, items in ITEMS_BY_TARGET.items()
        for item_id in items
    }
    status = "passed" if fig2["status"] == "passed" and supplement["status"] == "input_blocked" else "failed"
    return {
        "schema_version": 1,
        "paper_id": "2412.14271",
        "status": status,
        "profile": parameters["profile"],
        "fixed_item_denominator": len(item_results),
        "item_results": item_results,
        "target_checks": target_checks,
        "scientific_coverage_changed": False,
        "numerical_input_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "reference_pixels_read": False,
        },
    }
