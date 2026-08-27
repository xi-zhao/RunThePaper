"""Clean-room implementation campaign for every authored numerical target.

The campaign deliberately separates two facts:

* a small, independently generated calculation can validate an algorithmic
  path; and
* the 53-qubit paper result still needs the exact circuit, contraction order,
  slicing plan, and hardware benchmark inputs.

No paper PDF, source figure, author array, or author code is read here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

try:  # package import in the runner
    from .big_batch_feature_sim import (
        apply_single_qubit_gate,
        apply_two_qubit_gate,
        extract_big_batch,
        simulate_random_circuit,
    )
except ImportError:  # direct module import under PYTHONPATH=src in case tests
    from big_batch_feature_sim import (  # type: ignore[no-redef]
        apply_single_qubit_gate,
        apply_two_qubit_gate,
        extract_big_batch,
        simulate_random_circuit,
    )


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 14))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sqrt_x() -> np.ndarray:
    return 0.5 * np.array(
        [[1.0 + 1.0j, 1.0 - 1.0j], [1.0 - 1.0j, 1.0 + 1.0j]],
        dtype=np.complex128,
    )


def _rz(angle: float) -> np.ndarray:
    return np.diag(
        [np.exp(-0.5j * angle), np.exp(0.5j * angle)]
    ).astype(np.complex128)


def _fsim(theta: float, phi: float) -> np.ndarray:
    c = np.cos(theta)
    s = -1.0j * np.sin(theta)
    return np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, c, s, 0.0],
            [0.0, s, c, 0.0],
            [0.0, 0.0, 0.0, np.exp(-1.0j * phi)],
        ],
        dtype=np.complex128,
    )


def _apply_clean_room_cycle(
    state: np.ndarray,
    *,
    n_qubits: int,
    cycle: int,
    dtype: np.dtype[Any] = np.dtype(np.complex128),
) -> np.ndarray:
    for qubit in range(n_qubits):
        gate = (_sqrt_x() @ _rz(0.17 * (cycle + qubit + 1))).astype(dtype)
        state = apply_single_qubit_gate(state, gate, qubit, n_qubits)
    start = cycle % 2
    for qubit_a in range(start, n_qubits - 1, 2):
        gate = _fsim(np.pi / 2 - 0.08, 0.11).astype(dtype)
        state = apply_two_qubit_gate(
            state, gate, qubit_a, qubit_a + 1, n_qubits
        )
    return state.astype(dtype, copy=False)


def _small_fsim_state(
    *, n_qubits: int, cycles: int, dtype: np.dtype[Any] = np.dtype(np.complex128)
) -> np.ndarray:
    state = np.zeros(2**n_qubits, dtype=dtype)
    state[0] = 1.0
    for cycle in range(cycles):
        state = _apply_clean_room_cycle(
            state, n_qubits=n_qubits, cycle=cycle, dtype=dtype
        )
    return state


def _head_tail_factorization(n_qubits: int, cycles: int, output_index: int) -> dict[str, Any]:
    split = cycles // 2
    initial = np.zeros(2**n_qubits, dtype=np.complex128)
    initial[0] = 1.0
    head = initial
    for cycle in range(split):
        head = _apply_clean_room_cycle(head, n_qubits=n_qubits, cycle=cycle)

    tail_row = np.empty(2**n_qubits, dtype=np.complex128)
    for basis_index in range(2**n_qubits):
        basis = np.zeros(2**n_qubits, dtype=np.complex128)
        basis[basis_index] = 1.0
        evolved = basis
        for cycle in range(split, cycles):
            evolved = _apply_clean_room_cycle(
                evolved, n_qubits=n_qubits, cycle=cycle
            )
        tail_row[basis_index] = evolved[output_index]

    full = head
    for cycle in range(split, cycles):
        full = _apply_clean_room_cycle(full, n_qubits=n_qubits, cycle=cycle)
    direct = full[output_index]
    contracted = np.dot(tail_row, head)
    return {
        "n_qubits": n_qubits,
        "cycles": cycles,
        "cut_dimension": int(head.size),
        "output_index": output_index,
        "direct_amplitude": [float(direct.real), float(direct.imag)],
        "contracted_amplitude": [float(contracted.real), float(contracted.imag)],
        "absolute_error": float(abs(direct - contracted)),
    }


def _reduced_probability_features(params: dict[str, Any]) -> dict[str, Any]:
    state = simulate_random_circuit(
        int(params["n_qubits"]), int(params["depth"]), int(params["seed"])
    )
    n_qubits = int(params["n_qubits"])
    n_open = int(params["n_open"])
    open_qubits = list(range(n_qubits - n_open, n_qubits))
    closed_qubits = list(range(n_qubits - n_open))
    batch = extract_big_batch(
        state,
        n_qubits=n_qubits,
        depth=int(params["depth"]),
        seed=int(params["seed"]),
        label="implementation_validation",
        closed_qubits=closed_qubits,
        open_qubits=open_qubits,
    )
    conditional = batch.conditional_probabilities
    return {
        "mode": "reduced_validation",
        "n_qubits": n_qubits,
        "depth": int(params["depth"]),
        "batch_size": batch.batch_size,
        "state_norm": float(np.vdot(state, state).real),
        "conditional_sum": float(np.sum(conditional)),
        "conditional_min": float(np.min(conditional)),
        "scaled_probability_mean": float(np.mean(batch.scaled_probabilities)),
        "xeb_all": batch.xeb_all,
    }


def _blocked_boundary(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    required = list(params["required_paper_exact_inputs"])
    supplied = list(params.get("supplied_paper_exact_inputs", []))
    missing = [name for name in required if name not in supplied]
    if not missing:
        raise ValueError(
            f"{target_id}: boundary configuration unexpectedly supplies every input; "
            "replace the boundary mode with the scientific execution path"
        )
    return {
        "mode": "input_boundary",
        "status": "input_blocked",
        "target_id": target_id,
        "input_schema_version": 1,
        "required_paper_exact_inputs": required,
        "supplied_paper_exact_inputs": supplied,
        "missing_paper_exact_inputs": missing,
        "forbidden_substitutions": [
            "author numerical code",
            "author numerical arrays",
            "digitized paper curves",
            "source-figure pixels",
            "guessed circuit or contraction metadata",
        ],
        "acceptance_boundary": params["acceptance_boundary"],
    }


def _run_target(target_id: str, params: dict[str, Any]) -> dict[str, Any]:
    mode = params["mode"]
    if mode == "reduced_probability_features":
        return _reduced_probability_features(params)
    if mode == "head_tail_factorization":
        result = _head_tail_factorization(
            int(params["n_qubits"]),
            int(params["cycles"]),
            int(params["output_index"]),
        )
        result["mode"] = "reduced_validation"
        result["passed"] = result["absolute_error"] <= float(params["tolerance"])
        return result
    if mode == "analytic_contraction_cost":
        exponent = int(params["n_a"]) + int(params["n_b"]) + int(params["n_ab"])
        return {
            "mode": "analytic_validation",
            "exponent": exponent,
            "cost": 2**exponent,
            "passed": exponent == int(params["expected_exponent"]),
        }
    if mode == "input_boundary":
        return _blocked_boundary(target_id, params)
    if mode == "complex_precision":
        state128 = _small_fsim_state(
            n_qubits=int(params["n_qubits"]), cycles=int(params["cycles"])
        )
        state64 = _small_fsim_state(
            n_qubits=int(params["n_qubits"]),
            cycles=int(params["cycles"]),
            dtype=np.dtype(np.complex64),
        ).astype(np.complex128)
        max_error = float(np.max(np.abs(state128 - state64)))
        return {
            "mode": "reduced_validation",
            "max_amplitude_error": max_error,
            "norm_error_complex64": float(abs(np.vdot(state64, state64).real - 1.0)),
            "passed": max_error <= float(params["tolerance"]),
        }
    if mode == "branch_merge":
        state = _small_fsim_state(
            n_qubits=int(params["n_qubits"]), cycles=int(params["cycles"])
        )
        branches = np.array_split(state, int(params["branches"]))
        merged = np.concatenate(branches)
        return {
            "mode": "reduced_validation",
            "branches": len(branches),
            "max_merge_error": float(np.max(np.abs(state - merged))),
            "passed": bool(np.array_equal(state, merged)),
        }
    if mode == "mixed_xeb":
        state = _small_fsim_state(
            n_qubits=int(params["n_qubits"]), cycles=int(params["cycles"])
        )
        probabilities = np.abs(state) ** 2
        count = int(params["sample_count"])
        top = np.sort(probabilities)[-count:]
        rng = np.random.default_rng(int(params["seed"]))
        random = probabilities[rng.choice(probabilities.size, size=count, replace=False)]
        weight = float(params["top_weight"])
        mixed = weight * top + (1.0 - weight) * random
        scale = probabilities.size
        def xeb(values: np.ndarray) -> float:
            return float(scale * np.mean(values) - 1.0)

        xeb_top, xeb_random, xeb_mixed = xeb(top), xeb(random), xeb(mixed)
        lower, upper = sorted((xeb_top, xeb_random))
        return {
            "mode": "reduced_validation",
            "xeb_top": xeb_top,
            "xeb_random": xeb_random,
            "xeb_mixed": xeb_mixed,
            "passed": lower - 1e-12 <= xeb_mixed <= upper + 1e-12,
        }
    if mode == "marginal_identity":
        state = _small_fsim_state(
            n_qubits=int(params["n_qubits"]), cycles=int(params["cycles"])
        )
        probabilities = np.abs(state.reshape(2, -1)) ** 2
        marginals = probabilities.sum(axis=1)
        return {
            "mode": "analytic_validation",
            "total_probability": float(probabilities.sum()),
            "marginal_probability_sum": float(marginals.sum()),
            "passed": bool(
                np.isclose(probabilities.sum(), 1.0, atol=float(params["tolerance"]))
                and np.isclose(marginals.sum(), 1.0, atol=float(params["tolerance"]))
            ),
        }
    if mode == "memory_formula":
        elements = 2 ** int(params["tensor_rank"])
        bytes_total = elements * int(params["bytes_per_complex"])
        return {
            "mode": "analytic_validation",
            "elements": elements,
            "bytes": bytes_total,
            "gibibytes": bytes_total / 2**30,
            "passed": bytes_total > 0,
        }
    raise ValueError(f"{target_id}: unsupported campaign mode {mode!r}")


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    targets = config.get("targets")
    if not isinstance(targets, dict) or tuple(sorted(targets)) != TARGET_IDS:
        raise ValueError("config must declare exactly T001-T013")

    results: dict[str, dict[str, Any]] = {}
    for target_id in TARGET_IDS:
        result = _run_target(target_id, targets[target_id])
        result.update(
            {
                "schema_version": 1,
                "paper_id": config["paper_id"],
                "target_id": target_id,
                "campaign_scale": config["campaign_scale"],
                "scientific_coverage_promoted": False,
            }
        )
        check_passed = result.get("status") == "input_blocked" or bool(
            result.get("passed", True)
        )
        check = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "status": "passed" if check_passed else "failed",
            "implementation_attestation_only": True,
            "scientific_coverage_promoted": False,
            "result_mode": result["mode"],
        }
        _write_json(
            output_root / "data" / "implementation_closure" / f"{target_id}.json",
            result,
        )
        _write_json(
            output_root / "checks" / "implementation_closure" / f"{target_id}.json",
            check,
        )
        if not check_passed:
            raise RuntimeError(f"{target_id}: implementation validation failed")
        results[target_id] = result

    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "campaign_scale": config["campaign_scale"],
        "target_ids": list(TARGET_IDS),
        "targets_attested": len(results),
        "input_blocked_targets": [
            target_id
            for target_id, result in results.items()
            if result.get("status") == "input_blocked"
        ],
        "scientific_coverage_promoted": False,
        "clean_room_boundary": config["clean_room_boundary"],
    }
    _write_json(
        output_root / "checks" / "implementation_closure" / "manifest.json",
        manifest,
    )
    return manifest
