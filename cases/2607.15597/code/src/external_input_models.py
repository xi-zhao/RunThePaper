"""Numerical engines for targets blocked only by unpublished scientific inputs.

The functions in this module never substitute guessed paper parameters.  They
accept complete, explicit input packages and either compute the requested
observable or fail with a field-level input error.
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Iterable

import numpy as np


class ScientificInputError(ValueError):
    """A required scientific definition or parameter is absent or malformed."""


def dynamic_polarizability(input_package: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a sum-over-states dynamic polarizability in atomic units.

    The angular factor is deliberately supplied per transition because the
    publication does not freeze enough state-coupling metadata to infer it.
    Energies and the drive energy are expressed in Hartree, so no hidden unit
    convention enters the calculation.
    """

    drive_energy = _positive_float(input_package, "drive_energy_hartree", allow_zero=True)
    transitions = input_package.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        raise ScientificInputError("transitions must be a non-empty list")

    rows: list[dict[str, float | str]] = []
    total = 0.0
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            raise ScientificInputError(f"transitions[{index}] must be an object")
        label = str(transition.get("label") or f"transition_{index}")
        delta = _nonzero_float(transition, "delta_energy_hartree")
        dipole = _positive_float(transition, "reduced_dipole_au", allow_zero=True)
        angular_factor = _finite_float(transition, "angular_factor")
        denominator = delta * delta - drive_energy * drive_energy
        if math.isclose(denominator, 0.0, rel_tol=0.0, abs_tol=1e-18):
            raise ScientificInputError(f"{label}: drive is resonant with the transition")
        contribution = angular_factor * 2.0 * delta * dipole * dipole / denominator
        rows.append(
            {
                "label": label,
                "delta_energy_hartree": delta,
                "reduced_dipole_au": dipole,
                "angular_factor": angular_factor,
                "contribution_au": contribution,
            }
        )
        total += contribution

    return {
        "model": "sum_over_states_dynamic_polarizability",
        "drive_energy_hartree": drive_energy,
        "transition_count": len(rows),
        "contributions": rows,
        "polarizability_au": total,
    }


def dynamic_polarizability_sweep(
    input_package: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate every explicitly supplied Stark-map state and field sample.

    The paper does not publish the MQDT basis or tracked-state arrays.  This
    function therefore accepts only a fully enumerated external package and
    delegates every sample to :func:`dynamic_polarizability`; it never fills
    missing states, fields, or transitions by interpolation.
    """

    states = input_package.get("states")
    if not isinstance(states, list) or not states:
        raise ScientificInputError("states must be a non-empty list")
    output_states = []
    labels: set[str] = set()
    for state in states:
        if not isinstance(state, dict):
            raise ScientificInputError("each states entry must be an object")
        state_id = str(state.get("state_id") or "").strip()
        if not state_id or state_id in labels:
            raise ScientificInputError("state_id values must be unique and non-empty")
        labels.add(state_id)
        samples = state.get("samples")
        if not isinstance(samples, list) or not samples:
            raise ScientificInputError(f"state {state_id!r} requires non-empty samples")
        rows = []
        for sample in samples:
            if not isinstance(sample, dict) or "field_v_m" not in sample:
                raise ScientificInputError(
                    f"state {state_id!r} samples require field_v_m"
                )
            result = dynamic_polarizability(sample)
            rows.append(
                {
                    "field_v_m": _finite_float(sample, "field_v_m"),
                    **result,
                }
            )
        output_states.append({"state_id": state_id, "samples": rows})
    return {"states": output_states, "state_count": len(output_states)}


def css_monte_carlo(input_package: dict[str, Any]) -> dict[str, Any]:
    """Run a reproducible binary CSS error-correction Monte Carlo experiment.

    A publication-specific parity check, logical operator and decoder are
    mandatory inputs.  Exact minimum-weight decoding is included for small
    independent checks; paper-scale runs can supply an explicit syndrome
    lookup generated from a separately reviewed decoder implementation.
    """

    parity_check = _binary_matrix(input_package, "parity_check_z")
    logical_z = _binary_matrix(input_package, "logical_z")
    if parity_check.shape[1] != logical_z.shape[1]:
        raise ScientificInputError("parity_check_z and logical_z widths must match")
    qubits = parity_check.shape[1]
    shots = _positive_int(input_package, "shots")
    seed = _nonnegative_int(input_package, "seed")
    probabilities = _probability_vector(input_package, qubits)
    decoder = _decoder(input_package.get("decoder"), parity_check)

    rng = np.random.default_rng(seed)
    failures = 0
    syndrome_histogram: dict[str, int] = {}
    for _ in range(shots):
        error = (rng.random(qubits) < probabilities).astype(np.uint8)
        syndrome = parity_check @ error % 2
        syndrome_key = "".join(str(int(bit)) for bit in syndrome)
        syndrome_histogram[syndrome_key] = syndrome_histogram.get(syndrome_key, 0) + 1
        correction = decoder(syndrome)
        residual = error ^ correction
        if np.any(logical_z @ residual % 2):
            failures += 1

    rate = failures / shots
    standard_error = math.sqrt(rate * (1.0 - rate) / shots)
    return {
        "model": "binary_css_monte_carlo",
        "qubits": qubits,
        "checks": int(parity_check.shape[0]),
        "logical_operators": int(logical_z.shape[0]),
        "shots": shots,
        "seed": seed,
        "failures": failures,
        "logical_failure_rate": rate,
        "binomial_standard_error": standard_error,
        "syndrome_histogram": syndrome_histogram,
    }


def css_monte_carlo_campaign(input_package: dict[str, Any]) -> dict[str, Any]:
    """Run a frozen set of explicitly named CSS Monte Carlo experiments."""

    experiments = input_package.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        raise ScientificInputError("experiments must be a non-empty list")
    results = []
    labels: set[str] = set()
    for experiment in experiments:
        if not isinstance(experiment, dict):
            raise ScientificInputError("each experiments entry must be an object")
        label = str(experiment.get("label") or "").strip()
        if not label or label in labels:
            raise ScientificInputError("experiment labels must be unique and non-empty")
        labels.add(label)
        results.append({"label": label, **css_monte_carlo(experiment)})
    return {"experiments": results, "experiment_count": len(results)}


def toggled_hamiltonian_evolution(input_package: dict[str, Any]) -> dict[str, Any]:
    """Integrate a piecewise-constant Hamiltonian from explicit matrices."""

    base = _hermitian_matrix(input_package, "base_hamiltonian_rad_s")
    toggle = _hermitian_matrix(input_package, "toggle_hamiltonian_rad_s")
    if base.shape != toggle.shape:
        raise ScientificInputError("base and toggle Hamiltonians must have the same shape")
    schedule = input_package.get("schedule")
    if not isinstance(schedule, list) or not schedule:
        raise ScientificInputError("schedule must be a non-empty list")

    unitary = np.eye(base.shape[0], dtype=complex)
    total_duration = 0.0
    for index, segment in enumerate(schedule):
        if not isinstance(segment, dict):
            raise ScientificInputError(f"schedule[{index}] must be an object")
        duration = _positive_float(segment, "duration_s")
        multiplier = _finite_float(segment, "toggle_multiplier")
        hamiltonian = base + multiplier * toggle
        values, vectors = np.linalg.eigh(hamiltonian)
        step = (vectors * np.exp(-1j * values * duration)) @ vectors.conj().T
        unitary = step @ unitary
        total_duration += duration

    identity = np.eye(base.shape[0], dtype=complex)
    unitarity_error = float(np.max(np.abs(unitary.conj().T @ unitary - identity)))
    result: dict[str, Any] = {
        "model": "piecewise_constant_toggled_hamiltonian",
        "dimension": int(base.shape[0]),
        "segments": len(schedule),
        "total_duration_s": total_duration,
        "unitarity_error": unitarity_error,
        "unitary": _encode_complex_matrix(unitary),
    }
    if "target_unitary" in input_package:
        target = _complex_matrix(input_package, "target_unitary")
        if target.shape != unitary.shape:
            raise ScientificInputError("target_unitary has the wrong shape")
        overlap = abs(np.trace(target.conj().T @ unitary)) / unitary.shape[0]
        result["process_infidelity_proxy"] = float(max(0.0, 1.0 - overlap * overlap))
    return result


def _decoder(payload: Any, parity_check: np.ndarray):
    if not isinstance(payload, dict):
        raise ScientificInputError("decoder must be an object")
    kind = str(payload.get("kind") or "")
    if kind == "syndrome_lookup":
        corrections = payload.get("corrections")
        if not isinstance(corrections, dict):
            raise ScientificInputError("decoder.corrections must be an object")
        width = parity_check.shape[1]

        def lookup(syndrome: np.ndarray) -> np.ndarray:
            key = "".join(str(int(bit)) for bit in syndrome)
            raw = corrections.get(key)
            if not isinstance(raw, list) or len(raw) != width:
                raise ScientificInputError(f"decoder has no {width}-bit correction for syndrome {key}")
            return _binary_vector(raw, f"decoder.corrections[{key}]")

        return lookup
    if kind == "exact_min_weight":
        max_qubits = int(payload.get("max_qubits", 20))
        width = parity_check.shape[1]
        if width > max_qubits:
            raise ScientificInputError(
                f"exact_min_weight is limited to {max_qubits} qubits; provide a reviewed decoder lookup"
            )
        lookup = _minimum_weight_lookup(parity_check)
        return lambda syndrome: lookup["".join(str(int(bit)) for bit in syndrome)].copy()
    raise ScientificInputError("decoder.kind must be syndrome_lookup or exact_min_weight")


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


def _binary_matrix(payload: dict[str, Any], key: str) -> np.ndarray:
    raw = payload.get(key)
    if not isinstance(raw, list) or not raw or not all(isinstance(row, list) for row in raw):
        raise ScientificInputError(f"{key} must be a non-empty matrix")
    widths = {len(row) for row in raw}
    if len(widths) != 1 or 0 in widths:
        raise ScientificInputError(f"{key} rows must have one non-zero width")
    matrix = np.asarray(raw, dtype=int)
    if np.any((matrix != 0) & (matrix != 1)):
        raise ScientificInputError(f"{key} must contain only 0 and 1")
    return matrix.astype(np.uint8)


def _binary_vector(raw: Iterable[Any], label: str) -> np.ndarray:
    vector = np.asarray(list(raw), dtype=int)
    if vector.ndim != 1 or np.any((vector != 0) & (vector != 1)):
        raise ScientificInputError(f"{label} must be a binary vector")
    return vector.astype(np.uint8)


def _probability_vector(payload: dict[str, Any], width: int) -> np.ndarray:
    raw = payload.get("error_probability")
    values = [raw] * width if isinstance(raw, (int, float)) else raw
    if not isinstance(values, list) or len(values) != width:
        raise ScientificInputError("error_probability must be a scalar or one value per qubit")
    probabilities = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(probabilities)) or np.any(probabilities < 0) or np.any(probabilities > 1):
        raise ScientificInputError("error probabilities must lie in [0, 1]")
    return probabilities


def _hermitian_matrix(payload: dict[str, Any], key: str) -> np.ndarray:
    matrix = _complex_matrix(payload, key)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ScientificInputError(f"{key} must be square")
    if not np.allclose(matrix, matrix.conj().T, atol=1e-12, rtol=1e-12):
        raise ScientificInputError(f"{key} must be Hermitian")
    return matrix


def _complex_matrix(payload: dict[str, Any], key: str) -> np.ndarray:
    raw = payload.get(key)
    if not isinstance(raw, list) or not raw or not all(isinstance(row, list) for row in raw):
        raise ScientificInputError(f"{key} must be a non-empty matrix")
    widths = {len(row) for row in raw}
    if len(widths) != 1 or 0 in widths:
        raise ScientificInputError(f"{key} rows must have one non-zero width")
    matrix = np.asarray([[_complex_value(value, key) for value in row] for row in raw])
    if not np.all(np.isfinite(matrix.real)) or not np.all(np.isfinite(matrix.imag)):
        raise ScientificInputError(f"{key} values must be finite")
    return matrix


def _complex_value(value: Any, label: str) -> complex:
    if isinstance(value, (int, float)):
        return complex(float(value), 0.0)
    if isinstance(value, list) and len(value) == 2 and all(isinstance(part, (int, float)) for part in value):
        return complex(float(value[0]), float(value[1]))
    raise ScientificInputError(f"{label} entries must be numbers or [real, imaginary]")


def _encode_complex_matrix(matrix: np.ndarray) -> list[list[list[float]]]:
    return [[[float(value.real), float(value.imag)] for value in row] for row in matrix]


def _finite_float(payload: dict[str, Any], key: str) -> float:
    raw = payload.get(key)
    if not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
        raise ScientificInputError(f"{key} must be a finite number")
    return float(raw)


def _positive_float(payload: dict[str, Any], key: str, *, allow_zero: bool = False) -> float:
    value = _finite_float(payload, key)
    if value < 0.0 or (value == 0.0 and not allow_zero):
        comparator = "nonnegative" if allow_zero else "positive"
        raise ScientificInputError(f"{key} must be {comparator}")
    return value


def _nonzero_float(payload: dict[str, Any], key: str) -> float:
    value = _finite_float(payload, key)
    if value == 0.0:
        raise ScientificInputError(f"{key} must be nonzero")
    return value


def _positive_int(payload: dict[str, Any], key: str) -> int:
    raw = payload.get(key)
    if not isinstance(raw, int) or isinstance(raw, bool) or raw <= 0:
        raise ScientificInputError(f"{key} must be a positive integer")
    return raw


def _nonnegative_int(payload: dict[str, Any], key: str) -> int:
    raw = payload.get(key)
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise ScientificInputError(f"{key} must be a nonnegative integer")
    return raw
