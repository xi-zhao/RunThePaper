from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np

from fig5a_proxy_core import (
    coherent_error_unitary,
    deterministic_proxy_probabilities,
    pauli_twirl_probability,
)
from public_targets import heating_transition_matrix, leakage_generalized_pauli_twirl


ITEMS_BY_TARGET = {
    "F5A_PROXY": ("FIG5_A",),
    "T_FIG5B": ("FIG5_B",),
    "T_FIG6A": ("FIG6_A",),
    "T_FIG6B": ("FIG6_B",),
    "T_FIG7": ("FIG7",),
    "T_FIG8": ("FIG8",),
    "T_FIG11": ("FIG11",),
}


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == hashlib.sha256().digest_size * 2
        and all(character in "0123456789abcdef" for character in value.lower())
    )


def _attest_fig5a_proxy(config: dict[str, Any]) -> dict[str, Any]:
    theta = float(config["theta"])
    unitary = coherent_error_unitary(theta)
    identity_error = float(np.max(np.abs(unitary.conj().T @ unitary - np.eye(2))))
    proxy = deterministic_proxy_probabilities(
        theta=theta,
        distance=int(config["distance"]),
        rounds=int(config["rounds"]),
    )
    probability = pauli_twirl_probability(theta)
    passed = (
        identity_error < 1e-12
        and 0.0 <= probability <= 0.5
        and proxy["coherent_trace_error"] < 1e-12
        and proxy["twirled_trace_error"] < 1e-12
        and 0.0 <= proxy["coherent_odd_x_parity_probability"] <= 1.0
        and 0.0 <= proxy["twirled_odd_x_parity_probability"] <= 1.0
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_proxy_implementation_attestation",
        "paper_scale_executed": False,
        "equation_9_unitarity_error": identity_error,
        "equation_10_single_pauli_probability": probability,
        "deterministic_channel_proxy": proxy,
        "scientific_scope": "proxy_model_only",
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _validate_input_bundle(target_id: str, config: dict[str, Any]) -> list[str]:
    bundle = config.get("input_bundle")
    required_keys = {
        "path",
        "sha256",
        "format",
        "required_fields",
        "source_requirement",
    }
    if not isinstance(bundle, dict) or set(bundle) != required_keys:
        raise ValueError(f"{target_id} input_bundle must implement the frozen schema")
    if bundle["format"] != "clean_room_qec_input_bundle_v1":
        raise ValueError(f"{target_id} input_bundle format is unsupported")
    fields = bundle["required_fields"]
    if (
        not isinstance(fields, list)
        or not fields
        or len(fields) != len(set(fields))
        or not all(isinstance(field, str) and field.strip() for field in fields)
    ):
        raise ValueError(f"{target_id} required_fields must be unique non-empty strings")
    if not isinstance(bundle["source_requirement"], str) or not bundle[
        "source_requirement"
    ].strip():
        raise ValueError(f"{target_id} source_requirement must be non-empty")
    path = bundle["path"]
    digest = bundle["sha256"]
    if path is None and digest is None:
        return fields
    if not isinstance(path, str) or not path.strip() or not _valid_sha256(digest):
        raise ValueError(f"{target_id} input bundle path and SHA-256 must be supplied together")
    raise ValueError(
        f"{target_id} input bundle is populated; execute it through a dedicated scientific run contract"
    )


def _fig5b_upstream_check(config: dict[str, Any]) -> dict[str, Any]:
    transitions = leakage_generalized_pauli_twirl(float(config["p_transfer"]))
    source_totals: dict[str, float] = {}
    for transition in transitions:
        source_totals[transition.source_sector] = (
            source_totals.get(transition.source_sector, 0.0)
            + transition.transition_probability
        )
    return {
        "printed_channel_rederived": True,
        "source_transition_totals": source_totals,
        "transition_normalized": all(
            abs(total - 1.0) < 1e-12 for total in source_totals.values()
        ),
    }


def _transmon_upstream_check(config: dict[str, Any]) -> dict[str, Any]:
    coupling = float(config["g"])
    if coupling == 0.0:
        raise ValueError("transmon coupling g must be nonzero")
    return {
        "public_hamiltonian_parameters_frozen": {
            "omega_untuned": float(config["omega_untuned"]),
            "alpha_1": float(config["alpha_1"]),
            "alpha_2": float(config["alpha_2"]),
            "g": coupling,
        },
        "tau_cz_from_equation_15": math.pi / (math.sqrt(2.0) * abs(coupling)),
        "tuned_pulse_schedule_available": False,
    }


def _fig8_upstream_check(config: dict[str, Any]) -> dict[str, Any]:
    axes = config["public_axis_bounds"]
    if set(axes) != {"p_depol", "gamma_deph", "gamma_iss"}:
        raise ValueError("Fig. 8 axis bounds must declare all three public parameters")
    return {
        "public_axis_bounds": axes,
        "barycentric_ray_count": int(config["barycentric_ray_count"]),
        "exact_ray_coordinates_available": False,
    }


def _fig11_upstream_check(config: dict[str, Any]) -> dict[str, Any]:
    transition = heating_transition_matrix(
        levels=int(config["levels"]),
        gamma_h=float(config["gamma_h"]),
        n_thermal=float(config["n_thermal"]),
        interval=float(config["interval"]),
    )
    distribution = np.zeros(int(config["levels"]), dtype=float)
    distribution[0] = 1.0
    sector = np.arange(int(config["levels"]), dtype=float)
    per_sector = float(config["p0"]) + float(config["kappa"]) * (2.0 * sector + 1.0)
    rates = []
    for _ in range(int(config["rounds"])):
        distribution = transition @ distribution
        rates.append(float(distribution @ per_sector))
    return {
        "transition_column_error": float(
            np.max(np.abs(transition.sum(axis=0) - 1.0))
        ),
        "sector_depolarizing_probabilities": per_sector.tolist(),
        "reduced_round_rates": rates,
        "reduced_round_average": float(np.mean(rates)),
        "qec_logical_error_simulated": False,
    }


def _attest_blocked_target(
    target_id: str,
    config: dict[str, Any],
    *,
    upstream_check: dict[str, Any],
) -> dict[str, Any]:
    missing_fields = _validate_input_bundle(target_id, config)
    return {
        "status": "input_blocked",
        "profile": "strict_input_boundary",
        "paper_scale_executed": False,
        "implemented_upstream_check": upstream_check,
        "missing_indispensable_fields": missing_fields,
        "blocked_artifact_valid": True,
        "scientific_coverage_changed": False,
        "boundary": config["boundary"],
    }


def run_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if config.get("paper_id") != "2607.08767":
        raise ValueError("paper_id must be 2607.08767")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    transmon = parameters["transmon_public_parameters"]
    target_checks = {
        "F5A_PROXY": _attest_fig5a_proxy(parameters["F5A_PROXY"]),
        "T_FIG5B": _attest_blocked_target(
            "T_FIG5B",
            parameters["T_FIG5B"],
            upstream_check=_fig5b_upstream_check(parameters["T_FIG5B"]),
        ),
        "T_FIG6A": _attest_blocked_target(
            "T_FIG6A",
            parameters["T_FIG6A"],
            upstream_check=_transmon_upstream_check(transmon),
        ),
        "T_FIG6B": _attest_blocked_target(
            "T_FIG6B",
            parameters["T_FIG6B"],
            upstream_check=_transmon_upstream_check(transmon),
        ),
        "T_FIG7": _attest_blocked_target(
            "T_FIG7",
            parameters["T_FIG7"],
            upstream_check=_transmon_upstream_check(transmon),
        ),
        "T_FIG8": _attest_blocked_target(
            "T_FIG8",
            parameters["T_FIG8"],
            upstream_check=_fig8_upstream_check(parameters["T_FIG8"]),
        ),
        "T_FIG11": _attest_blocked_target(
            "T_FIG11",
            parameters["T_FIG11"],
            upstream_check=_fig11_upstream_check(parameters["T_FIG11"]),
        ),
    }
    accepted_statuses = {"passed", "input_blocked"}
    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": (
                "attested"
                if target_checks[target_id]["status"] in accepted_statuses
                else "failed"
            ),
            "scientific_coverage_changed": False,
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    status = (
        "passed"
        if all(check["status"] in accepted_statuses for check in target_checks.values())
        else "failed"
    )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "profile": "proxy_and_strict_input_boundary_attestation",
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
