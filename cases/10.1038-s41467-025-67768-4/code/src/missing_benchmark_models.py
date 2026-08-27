"""Parameterized clean-room models for two underspecified supplement targets.

The publication does not provide the complete qLDPC or lattice-surgery
benchmark contracts.  These functions define the executable boundary: a
reviewed package must supply the circuit schedule, binary fault locations,
decoder, sampling contract, and code observables.  Missing values are rejected
rather than inferred from source pixels, author arrays, or author code.
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Callable, Iterable

import numpy as np

from qem_models import zne_metrics


class ScientificInputError(ValueError):
    """Raised when a scientific benchmark package is incomplete."""


def _binary_matrix(payload: dict[str, Any], key: str, *, width: int | None = None) -> np.ndarray:
    raw = payload.get(key)
    if not isinstance(raw, list) or not raw or not all(isinstance(row, list) for row in raw):
        raise ScientificInputError(f"{key} must be a non-empty binary matrix")
    widths = {len(row) for row in raw}
    if len(widths) != 1 or 0 in widths or (width is not None and widths != {width}):
        raise ScientificInputError(f"{key} rows must have the declared non-zero width")
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and value in {0, 1}
        for row in raw
        for value in row
    ):
        raise ScientificInputError(f"{key} must contain only 0 and 1")
    return np.asarray(raw, dtype=np.uint8)


def _binary_vector(raw: Iterable[Any], width: int, label: str) -> np.ndarray:
    if not isinstance(raw, list) or len(raw) != width or not all(
        isinstance(value, int) and not isinstance(value, bool) and value in {0, 1}
        for value in raw
    ):
        raise ScientificInputError(f"{label} must be a {width}-bit vector")
    return np.asarray(raw, dtype=np.uint8)


def _minimum_weight_lookup(parity_check: np.ndarray) -> dict[str, np.ndarray]:
    width = parity_check.shape[1]
    lookup: dict[str, np.ndarray] = {}
    for weight in range(width + 1):
        for positions in itertools.combinations(range(width), weight):
            error = np.zeros(width, dtype=np.uint8)
            error[list(positions)] = 1
            syndrome = parity_check @ error % 2
            key = "".join(str(int(bit)) for bit in syndrome)
            lookup.setdefault(key, error)
        if len(lookup) == 2 ** parity_check.shape[0]:
            break
    return lookup


def _decoder(spec: Any, parity_check: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    if not isinstance(spec, dict):
        raise ScientificInputError("decoder must be an object")
    width = parity_check.shape[1]
    kind = str(spec.get("kind") or "")
    if kind == "exact_min_weight":
        max_qubits = spec.get("max_qubits")
        if not isinstance(max_qubits, int) or isinstance(max_qubits, bool) or max_qubits < 1:
            raise ScientificInputError("decoder.max_qubits must be a positive integer")
        if width > max_qubits:
            raise ScientificInputError(
                f"exact_min_weight is limited to {max_qubits} qubits; provide the reviewed paper decoder lookup"
            )
        lookup = _minimum_weight_lookup(parity_check)
    elif kind == "syndrome_lookup":
        raw = spec.get("corrections")
        if not isinstance(raw, dict) or not raw:
            raise ScientificInputError("decoder.corrections must be a non-empty object")
        syndrome_width = parity_check.shape[0]
        lookup = {}
        for key, value in raw.items():
            key = str(key)
            if len(key) != syndrome_width or set(key) - {"0", "1"}:
                raise ScientificInputError(
                    f"decoder syndrome {key!r} must be a {syndrome_width}-bit string"
                )
            lookup[key] = _binary_vector(value, width, f"decoder.corrections[{key}]")
    else:
        raise ScientificInputError("decoder.kind must be exact_min_weight or syndrome_lookup")

    def decode(syndrome: np.ndarray) -> np.ndarray:
        key = "".join(str(int(bit)) for bit in syndrome)
        correction = lookup.get(key)
        if correction is None:
            raise ScientificInputError(f"decoder has no correction for syndrome {key}")
        return correction.copy()

    return decode


def _schedule(payload: dict[str, Any], width: int) -> list[dict[str, Any]]:
    raw = payload.get("circuit_schedule")
    if not isinstance(raw, list) or not raw:
        raise ScientificInputError("circuit_schedule must be a non-empty list")
    schedule = []
    for index, step in enumerate(raw):
        if not isinstance(step, dict):
            raise ScientificInputError(f"circuit_schedule[{index}] must be an object")
        operation = str(step.get("operation") or "")
        if operation not in {"idle", "cx"}:
            raise ScientificInputError(f"unsupported binary operation: {operation}")
        qubits = step.get("qubits")
        expected_arity = 2 if operation == "cx" else 0
        if (
            not isinstance(qubits, list)
            or len(qubits) != expected_arity
            or not all(isinstance(value, int) and not isinstance(value, bool) for value in qubits)
            or len(set(qubits)) != len(qubits)
            or any(value < 0 or value >= width for value in qubits)
        ):
            raise ScientificInputError(
                f"circuit_schedule[{index}].qubits has the wrong arity or range"
            )
        faults = step.get("faults")
        if not isinstance(faults, list):
            raise ScientificInputError(f"circuit_schedule[{index}].faults must be a list")
        normalized_faults = []
        for fault_index, fault in enumerate(faults):
            if not isinstance(fault, dict):
                raise ScientificInputError(
                    f"circuit_schedule[{index}].faults[{fault_index}] must be an object"
                )
            support = fault.get("support")
            probability = fault.get("probability")
            if (
                not isinstance(support, list)
                or not support
                or not all(isinstance(value, int) and not isinstance(value, bool) for value in support)
                or len(set(support)) != len(support)
                or any(value < 0 or value >= width for value in support)
            ):
                raise ScientificInputError("fault support must contain unique in-range qubits")
            if (
                not isinstance(probability, (int, float))
                or isinstance(probability, bool)
                or not math.isfinite(float(probability))
                or not 0.0 <= float(probability) <= 1.0
            ):
                raise ScientificInputError("fault probability must lie in [0, 1]")
            normalized_faults.append(
                {"support": tuple(support), "probability": float(probability)}
            )
        schedule.append({"operation": operation, "qubits": qubits, "faults": normalized_faults})
    return schedule


def binary_circuit_monte_carlo(payload: dict[str, Any], *, noise_scale: float = 1.0) -> dict[str, Any]:
    """Simulate a declared binary Clifford/fault schedule and final decoder."""

    width = payload.get("n_data_qubits")
    shots = payload.get("shots")
    seed = payload.get("seed")
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ScientificInputError("n_data_qubits must be a positive integer")
    if not isinstance(shots, int) or isinstance(shots, bool) or shots < 1:
        raise ScientificInputError("shots must be a positive integer")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ScientificInputError("seed must be a nonnegative integer")
    if not math.isfinite(noise_scale) or noise_scale <= 0.0:
        raise ScientificInputError("noise_scale must be finite and positive")
    if payload.get("error_channel") != "binary_x":
        raise ScientificInputError("error_channel must explicitly be binary_x")
    checks = _binary_matrix(payload, "parity_check", width=width)
    logical = _binary_matrix(payload, "logical_observables", width=width)
    decoder = _decoder(payload.get("decoder"), checks)
    schedule = _schedule(payload, width)
    observable_indices = payload.get("observable_logical_indices")
    if (
        not isinstance(observable_indices, list)
        or not observable_indices
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in observable_indices)
        or len(set(observable_indices)) != len(observable_indices)
        or any(value < 0 or value >= logical.shape[0] for value in observable_indices)
    ):
        raise ScientificInputError("observable_logical_indices must select valid logical rows")

    rng = np.random.default_rng(seed)
    multiplicity = np.zeros(logical.shape[0] + 1, dtype=np.int64)
    signed_sum = 0
    decoder_failures = 0
    for _ in range(shots):
        error = np.zeros(width, dtype=np.uint8)
        for step in schedule:
            if step["operation"] == "cx":
                control, target = step["qubits"]
                error[target] ^= error[control]
            for fault in step["faults"]:
                probability = noise_scale * fault["probability"]
                if probability > 1.0:
                    raise ScientificInputError("scaled fault probability exceeds one")
                if rng.random() < probability:
                    error[list(fault["support"])] ^= 1
        syndrome = checks @ error % 2
        correction = decoder(syndrome)
        residual = error ^ correction
        decoder_failures += int(np.any(checks @ residual % 2))
        flips = logical @ residual % 2
        multiplicity[int(flips.sum())] += 1
        signed_sum += -1 if int(flips[observable_indices].sum()) & 1 else 1
    if decoder_failures:
        raise ScientificInputError("decoder returned a correction with nonzero residual syndrome")
    return {
        "model": "binary_circuit_monte_carlo",
        "n_data_qubits": width,
        "logical_qubits": int(logical.shape[0]),
        "shots": shots,
        "seed": seed,
        "noise_scale": noise_scale,
        "logical_multiplicity_counts": multiplicity.tolist(),
        "logical_multiplicity_probabilities": (multiplicity / shots).tolist(),
        "observable_expectation": signed_sum / shots,
    }


def qldpc_logical_multiplicity(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the declared qLDPC circuit and count affected logical qubits."""

    code = payload.get("code_parameters")
    if not isinstance(code, dict) or not all(
        isinstance(code.get(key), int) and not isinstance(code.get(key), bool)
        for key in ("n", "k", "d")
    ):
        raise ScientificInputError("code_parameters must define integer n, k, and d")
    if code["n"] < 1 or code["k"] < 1 or code["k"] > code["n"] or code["d"] < 1:
        raise ScientificInputError("code_parameters must satisfy n >= k >= 1 and d >= 1")
    if code["n"] != payload.get("n_data_qubits"):
        raise ScientificInputError("code_parameters.n must match n_data_qubits")
    result = binary_circuit_monte_carlo(payload)
    if result["logical_qubits"] != code["k"]:
        raise ScientificInputError("logical_observables row count must equal code_parameters.k")
    result.update({"model": "qldpc_logical_multiplicity", "code_parameters": code})
    return result


def lattice_surgery_zne(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate expectation, bias, and overhead from one complete circuit contract."""

    distance = payload.get("distance")
    scales = payload.get("noise_scales")
    orders = payload.get("zne_orders")
    experiment = payload.get("experiment")
    if not isinstance(distance, int) or isinstance(distance, bool) or distance < 1:
        raise ScientificInputError("distance must be a positive integer")
    if (
        not isinstance(scales, list)
        or len(scales) < 3
        or not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            and float(value) > 0.0
            for value in scales
        )
        or len(set(float(value) for value in scales)) != len(scales)
    ):
        raise ScientificInputError("noise_scales must contain at least three distinct positive values")
    if (
        not isinstance(orders, list)
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in orders)
        or sorted(set(orders)) != [1, 2]
    ):
        raise ScientificInputError("zne_orders must declare first and second order")
    if not isinstance(experiment, dict):
        raise ScientificInputError("experiment must be an object")
    base_seed = experiment.get("seed")
    if not isinstance(base_seed, int) or isinstance(base_seed, bool) or base_seed < 0:
        raise ScientificInputError("experiment.seed must be a nonnegative integer")
    expectations = []
    runs = []
    for index, scale in enumerate(scales):
        instance = dict(experiment)
        instance["seed"] = base_seed + index
        result = binary_circuit_monte_carlo(instance, noise_scale=float(scale))
        expectations.append(float(result["observable_expectation"]))
        runs.append(result)
    metrics = {}
    for order in orders:
        count = order + 1
        metrics[f"order_{order}"] = zne_metrics(
            expectations[:count], scales[:count], distance
        )
    return {
        "model": "lattice_surgery_binary_circuit_zne",
        "distance": distance,
        "noise_scales": [float(value) for value in scales],
        "expectations": expectations,
        "zne_metrics": metrics,
        "runs": runs,
    }


def required_schema(target_id: str) -> list[str]:
    circuit = [
        "n_data_qubits",
        "error_channel",
        "circuit_schedule[].operation",
        "circuit_schedule[].qubits",
        "circuit_schedule[].faults[].support",
        "circuit_schedule[].faults[].probability",
        "parity_check",
        "logical_observables",
        "observable_logical_indices",
        "decoder",
        "shots",
        "seed",
    ]
    if target_id == "T008":
        return ["code_parameters.n", "code_parameters.k", "code_parameters.d", *circuit]
    if target_id == "T009":
        return ["distance", "noise_scales", "zne_orders", *[f"experiment.{key}" for key in circuit]]
    raise ScientificInputError(f"unsupported target_id: {target_id}")
