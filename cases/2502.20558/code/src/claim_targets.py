from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Sequence


def _parse_z_string(term: str) -> list[int]:
    tokens = [token.strip() for token in term.replace("*", " ").split() if token.strip()]
    qubits: list[int] = []
    for token in tokens:
        if token == "I":
            continue
        if not token.startswith("Z"):
            raise ValueError(f"Only Z-Pauli strings are supported, got {term!r}")
        qubits.append(int(token[1:]))
    return qubits


def format_z_string(qubits: Iterable[int]) -> str:
    ordered = sorted(set(int(value) for value in qubits))
    return " ".join(f"Z{value}" for value in ordered) if ordered else "I"


def supercheck_product(stabilizer_left: str, stabilizer_right: str) -> dict[str, object]:
    counts: defaultdict[int, int] = defaultdict(int)
    for qubit in _parse_z_string(stabilizer_left):
        counts[qubit] += 1
    for qubit in _parse_z_string(stabilizer_right):
        counts[qubit] += 1
    surviving = sorted(qubit for qubit, count in counts.items() if count % 2 == 1)
    cancelled = sorted(qubit for qubit, count in counts.items() if count % 2 == 0)
    return {
        "stabilizer_left": stabilizer_left,
        "stabilizer_right": stabilizer_right,
        "supercheck": format_z_string(surviving),
        "cancelled_qubits": cancelled,
        "surviving_qubits": surviving,
    }


def exclusive_loss_weights(probabilities: Sequence[float]) -> list[float]:
    running_survival = 1.0
    weights: list[float] = []
    for probability in probabilities:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("loss probabilities must lie in [0, 1]")
        weight = probability * running_survival
        weights.append(weight)
        running_survival *= 1.0 - probability
    return weights


def posterior_loss_weights(probabilities: Sequence[float]) -> list[dict[str, float]]:
    raw = exclusive_loss_weights(probabilities)
    total = sum(raw)
    if total <= 0.0:
        raise ValueError("posterior normalization requires at least one positive location probability")
    rows: list[dict[str, float]] = []
    for index, (prior, exclusive) in enumerate(zip(probabilities, raw, strict=True), start=1):
        rows.append(
            {
                "location_index": float(index),
                "raw_probability": float(prior),
                "exclusive_weight": float(exclusive),
                "posterior_weight": float(exclusive / total),
            }
        )
    return rows


def merge_detector_error_models(
    weights: Sequence[float],
    lifecycle_dems: Sequence[Sequence[dict[str, object]]],
) -> list[dict[str, object]]:
    if len(weights) != len(lifecycle_dems):
        raise ValueError("weights and lifecycle_dems must have the same length")
    merged: defaultdict[tuple[str, ...], float] = defaultdict(float)
    for weight, dem in zip(weights, lifecycle_dems, strict=True):
        for row in dem:
            detectors = tuple(sorted(str(token) for token in row["detectors"]))
            merged[detectors] += float(weight) * float(row["probability"])
    return [
        {"detectors": list(detectors), "probability": probability}
        for detectors, probability in sorted(merged.items())
    ]


def final_detector_error_model(
    lifecycle_dems: Sequence[Sequence[dict[str, object]]],
    lifecycle_weights: Sequence[Sequence[float]],
    pauli_dem: Sequence[dict[str, object]],
    first_comb_dem: Sequence[dict[str, object]],
    omega: float,
) -> list[dict[str, object]]:
    if len(lifecycle_dems) != len(lifecycle_weights):
        raise ValueError("Each lifecycle DEM family requires matching weights")
    merged: defaultdict[tuple[str, ...], float] = defaultdict(float)
    for dem_rows, weights in zip(lifecycle_dems, lifecycle_weights, strict=True):
        if dem_rows and isinstance(dem_rows[0], dict):
            component = merge_detector_error_models(weights, [dem_rows])  # type: ignore[list-item]
        else:
            component = merge_detector_error_models(weights, dem_rows)
        for row in component:
            merged[tuple(row["detectors"])] += float(row["probability"])
    for row in pauli_dem:
        merged[tuple(sorted(str(token) for token in row["detectors"]))] += float(row["probability"])
    if float(omega) != 0.0:
        for row in first_comb_dem:
            merged[tuple(sorted(str(token) for token in row["detectors"]))] += float(omega) * float(row["probability"])
    return [
        {"detectors": list(detectors), "probability": probability}
        for detectors, probability in sorted(merged.items())
    ]


def exact_union_probability(event_probability: float, multiplicity: int) -> float:
    if multiplicity < 1:
        raise ValueError("multiplicity must be positive")
    return 1.0 - (1.0 - event_probability) ** multiplicity


def second_order_inclusion_exclusion(event_probability: float, multiplicity: int) -> float:
    if multiplicity < 1:
        raise ValueError("multiplicity must be positive")
    first = multiplicity * event_probability
    second = math.comb(multiplicity, 2) * (event_probability**2)
    return first - second


def third_order_residual_rows(
    q_values: Sequence[float],
    multiplicity: int,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for value in q_values:
        exact = exact_union_probability(value, multiplicity)
        second_order = second_order_inclusion_exclusion(value, multiplicity)
        residual = exact - second_order
        rows.append(
            {
                "event_probability": float(value),
                "exact_union_probability": float(exact),
                "second_order_approximation": float(second_order),
                "residual": float(residual),
                "residual_over_q_cubed": float(residual / (value**3)),
            }
        )
    return rows


def error_model_b_candidates(p_cz: float) -> dict[str, object]:
    if not 0.0 <= p_cz <= 1.0:
        raise ValueError("p_cz must lie in [0, 1]")
    per_qubit = 1.0 - math.sqrt(1.0 - p_cz)
    literal_caption = [
        ("L⊗Z", per_qubit / 2.0),
        ("Z⊗L", per_qubit / 2.0),
        ("L⊗I", per_qubit / 2.0),
        ("I⊗L", per_qubit / 2.0),
    ]
    normalized_four_branch = [
        ("L⊗Z", per_qubit / 4.0),
        ("Z⊗L", per_qubit / 4.0),
        ("L⊗I", per_qubit / 4.0),
        ("I⊗L", per_qubit / 4.0),
    ]
    return {
        "per_qubit_error": float(per_qubit),
        "literal_caption": {
            "branches": [{"event": event, "probability": float(probability)} for event, probability in literal_caption],
            "total_probability": float(sum(probability for _, probability in literal_caption)),
        },
        "normalized_four_branch": {
            "branches": [{"event": event, "probability": float(probability)} for event, probability in normalized_four_branch],
            "total_probability": float(sum(probability for _, probability in normalized_four_branch)),
        },
    }


def logical_error_max_rows(logical_qubits: Sequence[int]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for qubits in logical_qubits:
        if qubits < 1:
            raise ValueError("logical_qubits entries must be positive")
        rows.append(
            {
                "logical_qubits": float(qubits),
                "plogical_max": float(1.0 - 1.0 / (2**qubits)),
            }
        )
    return rows
