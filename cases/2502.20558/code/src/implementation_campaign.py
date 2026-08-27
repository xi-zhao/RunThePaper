"""Clean-room reduced-scale implementations for targets T001--T020.

This module provides a deterministic scientific mechanism model for every
enumerated figure/table item while the paper-exact circuit-level surface-code
and correlated-MLE implementations remain unfinished.  It uses independently
written probability, lifecycle, error-channel, and repetition-decoder formulas.
It does not read paper pixels, author arrays, author code, or reference data.

The generated artifacts prove that every target has an executable scientific
path.  They are explicitly code-readiness evidence, not scientific acceptance
of the paper figures.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .analytic_targets import (
    algorithm_lifecycles,
    effective_distance_endpoints,
    lifecycle_curves,
    lifecycle_threshold_percent,
    table_i_analytic_rows,
    threshold_interpolation,
)
from .error_models import error_model_a, movement_error


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 21))

METHOD_FACTORS = {
    "loss_no_ssr": 1.35,
    "loss_ssr": 0.82,
    "loss_exact_time": 0.70,
    "erasure": 0.68,
    "conventional": 1.00,
    "swap1": 0.84,
    "swap2": 0.88,
    "teleportation": 0.91,
    "dc025": 0.66,
    "dc1_lmi": 0.70,
    "dc1": 0.76,
    "dc2": 0.80,
    "dc3": 0.84,
    "dc4": 0.88,
    "unspecified": 1.00,
}

METHOD_TOKENS = (
    ("LOSS-EXACTTIME", "loss_exact_time"),
    ("LOSS-NOSSR", "loss_no_ssr"),
    ("LOSS-SSR", "loss_ssr"),
    ("DC1-LMI", "dc1_lmi"),
    ("DC025", "dc025"),
    ("SWAP1", "swap1"),
    ("SWAP2", "swap2"),
    ("TELE", "teleportation"),
    ("CONV", "conventional"),
    ("DC1", "dc1"),
    ("DC2", "dc2"),
    ("DC3", "dc3"),
    ("DC4", "dc4"),
    ("ERASURE", "erasure"),
)


def _method(item_id: str) -> str:
    for token, method in METHOD_TOKENS:
        if token in item_id:
            return method
    return "unspecified"


def _distance(item_id: str, default: int) -> int:
    match = re.search(r"(?:^|-)D(\d{2})(?:-|$)", item_id)
    return int(match.group(1)) if match else default


def _loss_fraction(item_id: str, default: float) -> float:
    match = re.search(r"(?:^|-)L(\d{3})(?:-|$)", item_id)
    return int(match.group(1)) / 100.0 if match else default


def _decimal_token(item_id: str, prefix: str, default: float) -> float:
    match = re.search(rf"(?:^|-){prefix}(\d+(?:P\d+)?)(?:-|$)", item_id)
    if not match:
        return default
    return float(match.group(1).replace("P", "."))


def _bias(item_id: str, default: float) -> float:
    eta = _decimal_token(item_id, "ETA", -1.0)
    if eta >= 0.0:
        return eta
    match = re.search(r"(?:^|-)B(\d{3})(?:-|$)", item_id)
    return float(int(match.group(1))) if match else default


def _quantity(item: dict[str, Any]) -> str:
    item_id = str(item["item_id"])
    scientific_object = str(item.get("scientific_object") or "").lower()
    if "physical-qubit" in scientific_object:
        return "physical_qubits"
    if "beta-fit" in item_id.lower() or "effective distance" in scientific_object:
        return "effective_distance"
    if "threshold" in item_id.lower() or "threshold" in scientific_object:
        return "threshold"
    if "reduction" in scientific_object:
        return "reduction"
    if "combination-weight" in scientific_object:
        return "combination_weight"
    if "movement" in scientific_object:
        return "movement_error"
    if "lifecycle" in scientific_object:
        return "lifecycle"
    if str(item.get("item_type")) == "table":
        return "table_value"
    return "logical_error"


def binomial_tail(distance: int, probability: float) -> float:
    """Odd-distance majority-decoder failure probability."""

    if distance < 1 or distance % 2 == 0:
        raise ValueError("distance must be a positive odd integer")
    probability = min(max(float(probability), 0.0), 1.0)
    start = (distance + 1) // 2
    return sum(
        math.comb(distance, errors)
        * probability**errors
        * (1.0 - probability) ** (distance - errors)
        for errors in range(start, distance + 1)
    )


def _model_b_effective_rate(
    physical_error: float,
    loss_fraction: float,
    bias: float,
) -> tuple[float, dict[str, float]]:
    """Return both published-caption and normalized candidate weights.

    The case already records that the paper's Error Model B description is
    internally inconsistent.  The implementation therefore preserves both
    candidates instead of choosing one from visual agreement.
    """

    model_a = error_model_a(physical_error, loss_fraction, bias)
    loss = model_a["loss"]
    pauli = model_a["x"] + model_a["y"] + model_a["z"]
    literal_caption_total = 2.0 * loss + pauli
    normalized_four_branch_total = loss + pauli
    return normalized_four_branch_total, {
        "literal_caption_total": literal_caption_total,
        "normalized_four_branch_total": normalized_four_branch_total,
    }


def logical_error_proxy(
    *,
    distance: int,
    physical_error: float,
    loss_fraction: float,
    bias: float,
    method: str,
    rounds: int,
    error_model: str,
    movement_rate: float = 0.0,
) -> tuple[float, dict[str, Any]]:
    """Evaluate a transparent clean-room decoder-mechanism approximation."""

    if error_model == "B":
        base_rate, model_details = _model_b_effective_rate(
            physical_error,
            loss_fraction,
            bias,
        )
    else:
        probabilities = error_model_a(physical_error, loss_fraction, bias)
        loss = probabilities["loss"]
        pauli = probabilities["x"] + probabilities["y"] + probabilities["z"]
        information_penalty = {
            "loss_no_ssr": 0.50,
            "loss_ssr": 0.20,
            "loss_exact_time": 0.10,
            "erasure": 0.08,
        }.get(method, 0.25)
        base_rate = pauli + information_penalty * loss
        model_details = probabilities
    method_factor = METHOD_FACTORS[method]
    effective_rate = min(0.499999, method_factor * base_rate + movement_rate)
    per_round = binomial_tail(distance, effective_rate)
    logical_error = 1.0 - (1.0 - per_round) ** max(1, rounds)
    return logical_error, {
        "effective_rate": effective_rate,
        "per_round_logical_error": per_round,
        "method_factor": method_factor,
        "error_model_details": model_details,
    }


def _algorithm_lifecycle(item_id: str) -> float:
    rows = algorithm_lifecycles(ghz_qubits=16)
    if "GHZ16" in item_id:
        row = rows[0]
    elif "DIST15TO1" in item_id:
        row = rows[1]
    elif "SYNTH" in item_id:
        row = rows[2]
    else:
        row = rows[3]
    return float(row["maximum"] if item_id.endswith("-MAX") else row["average"])


def _lifecycle_value(item_id: str, distance: int, rounds: int) -> float:
    if item_id.startswith("F6B-"):
        return _algorithm_lifecycle(item_id)
    row = lifecycle_curves(distance, [max(2, rounds)])[0]
    if "DATA" in item_id:
        return float(row["conventional_data_lifecycle"])
    if "MEASURE" in item_id:
        return float(row["conventional_measure_lifecycle"])
    return float(row["conventional_all_lifecycle"])


def _table_value(item_id: str, distance: int) -> float:
    rows = table_i_analytic_rows(distance)
    row = rows[0]
    if "MEASURE" in item_id:
        return float(row["measure_lifecycle"])
    if "SPACETIME" in item_id:
        return float(row["space_time_overhead"])
    return float(row["data_lifecycle"])


def evaluate_item(
    target_id: str,
    item: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one atomic item without consulting any reference artifact."""

    item_id = str(item["item_id"])
    quantity = _quantity(item)
    method = _method(item_id)
    distance = _distance(item_id, int(parameters["default_distance"]))
    loss_fraction = _loss_fraction(item_id, float(parameters["default_loss_fraction"]))
    bias = _bias(item_id, float(parameters["default_bias"]))
    rounds = int(parameters["rounds"])
    physical_error = float(parameters["physical_error"])
    error_model = "B" if target_id == "T020" else "A"
    movement_rate = 0.0
    if target_id == "T015":
        movement_percent = (
            _decimal_token(item_id, "PERR", 0.1)
            if "PERR" in item_id
            else _decimal_token(item_id, "P", 0.1)
        )
        movement_rate = movement_error(
            movement_percent / 100.0,
            float(parameters["movement_duration"]),
            float(parameters["movement_slot_duration"]),
        )

    logical_error, details = logical_error_proxy(
        distance=distance,
        physical_error=physical_error,
        loss_fraction=loss_fraction,
        bias=bias,
        method=method,
        rounds=rounds,
        error_model=error_model,
        movement_rate=movement_rate,
    )

    if quantity == "threshold":
        loss_only = lifecycle_threshold_percent(max(1.0, details["method_factor"] * rounds)) / 100.0
        pauli_only = float(parameters["pauli_only_threshold"]) / details["method_factor"]
        value = threshold_interpolation(loss_fraction, loss_only, pauli_only)
        units = "physical_error_probability"
    elif quantity == "effective_distance":
        lower, upper = effective_distance_endpoints(distance)
        value = lower + (upper - lower) * (1.0 - loss_fraction) / details["method_factor"]
        value = min(float(distance), value)
        units = "effective_distance"
    elif quantity == "physical_qubits":
        value = (2 * distance**2 - 1) * details["method_factor"]
        units = "proxy_qubit_count"
    elif quantity == "lifecycle":
        value = _lifecycle_value(item_id, distance, rounds)
        units = "entangling_gate_opportunities"
    elif quantity == "table_value":
        value = _table_value(item_id, distance)
        units = "paper_formula_value"
    elif quantity == "movement_error":
        value = movement_rate
        units = "probability"
    elif quantity == "combination_weight":
        value = _decimal_token(item_id, "P", 0.01)
        units = "decoder_weight"
    elif quantity == "reduction":
        baseline, _ = logical_error_proxy(
            distance=distance,
            physical_error=physical_error,
            loss_fraction=loss_fraction,
            bias=bias,
            method="loss_no_ssr",
            rounds=rounds,
            error_model=error_model,
        )
        value = baseline / max(logical_error, 1e-15)
        units = "improvement_factor"
    else:
        value = logical_error
        units = "logical_error_probability"

    return {
        "item_id": item_id,
        "source_ref": item.get("source_ref"),
        "scientific_object": item.get("scientific_object"),
        "quantity": quantity,
        "value": float(value),
        "units": units,
        "parameters": {
            "distance": distance,
            "rounds": rounds,
            "physical_error": physical_error,
            "loss_fraction": loss_fraction,
            "bias": bias,
            "method": method,
            "error_model": error_model,
            "movement_rate": movement_rate,
        },
        "mechanism_details": details,
        "artifact_stage": "exploratory",
        "parameter_match": "proxy_model",
        "generated_data_provenance": "independent_numerics",
        "scientific_acceptance": "not_claimed",
    }


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    """Execute every configured target and write target-level data/check files."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "2502.20558":
        raise ValueError("configuration paper_id must be 2502.20558")
    parameters = config.get("parameters")
    targets = config.get("targets")
    if not isinstance(parameters, dict) or not isinstance(targets, dict):
        raise ValueError("configuration requires parameters and targets objects")
    if set(targets) != set(TARGET_IDS):
        raise ValueError("configuration must declare exactly T001--T020")

    summaries: dict[str, Any] = {}
    for target_id in TARGET_IDS:
        target = targets[target_id]
        items = target.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{target_id} must declare at least one atomic item")
        rows = [evaluate_item(target_id, item, parameters) for item in items]
        item_ids = [row["item_id"] for row in rows]
        finite = all(math.isfinite(row["value"]) for row in rows)
        unique = len(item_ids) == len(set(item_ids))
        probability_rows_valid = all(
            0.0 <= row["value"] <= 1.0
            for row in rows
            if row["units"] in {"probability", "logical_error_probability", "physical_error_probability"}
        )
        status = "passed" if finite and unique and probability_rows_valid else "failed"

        stem = target_id.lower()
        data_path = output_root / "data" / "implementation_validation" / f"{stem}.json"
        check_path = output_root / "checks" / "implementation_validation" / f"{stem}.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        check_path.parent.mkdir(parents=True, exist_ok=True)
        data_payload = {
            "schema_version": 1,
            "paper_id": "2502.20558",
            "target_id": target_id,
            "status": "generated",
            "scientific_scope": "cleanroom_reduced_scale_mechanism_model",
            "scientific_acceptance": "not_claimed",
            "rows": rows,
        }
        data_path.write_text(
            json.dumps(data_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        check_payload = {
            "schema_version": 1,
            "paper_id": "2502.20558",
            "target_id": target_id,
            "status": status,
            "artifact_stage": "exploratory",
            "parameter_match": "proxy_model",
            "generated_data_provenance": "independent_numerics",
            "scientific_acceptance": "not_claimed",
            "assertions": {
                "all_values_finite": finite,
                "atomic_item_ids_unique": unique,
                "probabilities_bounded": probability_rows_valid,
                "all_configured_items_emitted": len(rows) == len(items),
            },
            "item_count": len(rows),
            "forbidden_scientific_inputs": [],
            "remaining_boundary": (
                "Paper-exact circuit builders, delayed-erasure hypergraphs, correlated MLE/MWPM, "
                "published grids, shot counts, and fit windows are not established by this validation run."
            ),
            "data": data_path.as_posix(),
        }
        check_path.write_text(
            json.dumps(check_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if status != "passed":
            raise AssertionError(f"implementation validation failed for {target_id}")
        summaries[target_id] = {"status": status, "item_count": len(rows)}

    return {
        "schema_version": 1,
        "paper_id": "2502.20558",
        "status": "passed",
        "mode": config.get("mode"),
        "targets": summaries,
        "scientific_acceptance": "not_claimed",
    }
