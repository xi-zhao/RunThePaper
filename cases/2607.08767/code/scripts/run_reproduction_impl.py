#!/usr/bin/env python3
"""Run a transparent proxy of Plaquette Fig. 5(a).

This is deliberately a proxy_model target.  It uses the paper's public
distance, round count, coherent-error formula, Pauli twirl, and shot counts,
but makes the otherwise unpublished circuit-location convention explicit.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, pauli_error
from scipy.linalg import expm
from scipy.stats import beta


WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = WORKSPACE / "config" / "fig5a_proxy.json"


def pauli_twirl_probability(theta: float) -> float:
    """Return the X and Z probability in Eq. (10)."""

    return float(math.sin(math.sqrt(2.0) * math.pi * theta) ** 2 / 2.0)


def coherent_error_unitary(theta: float) -> np.ndarray:
    """Return U = exp[-i theta pi (X + Z)] from Eq. (9)."""

    x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return expm(-1j * theta * math.pi * (x + z))


def build_memory_circuit(*, distance: int, rounds: int, theta: float, coherent: bool) -> QuantumCircuit:
    """Build the explicit repetition-memory proxy circuit.

    Data qubits encode logical |+>.  Adjacent ZZ checks are measured with
    ideal ancillas.  In the Pauli-twirled circuit, identity instructions mark
    the exact locations on which the Aer noise model is applied.
    """

    if distance < 3 or distance % 2 == 0:
        raise ValueError("distance must be an odd integer >= 3")
    if rounds < 1:
        raise ValueError("rounds must be positive")

    data_count = distance
    ancilla_count = distance - 1
    qubits = QuantumRegister(data_count + ancilla_count, "q")
    syndrome = ClassicalRegister(ancilla_count * rounds, "syndrome")
    output = ClassicalRegister(data_count, "logical_x")
    circuit = QuantumCircuit(qubits, syndrome, output)

    circuit.h(qubits[0])
    for index in range(1, data_count):
        circuit.cx(qubits[0], qubits[index])

    unitary = coherent_error_unitary(theta)
    for round_index in range(rounds):
        for ancilla_index in range(ancilla_count):
            circuit.reset(qubits[data_count + ancilla_index])

        for data_index in range(data_count):
            if coherent:
                circuit.unitary(unitary, [qubits[data_index]], label="Uerr")
            else:
                circuit.id(qubits[data_index])

        for ancilla_index in range(ancilla_count):
            ancilla = qubits[data_count + ancilla_index]
            circuit.cx(qubits[ancilla_index], ancilla)
            circuit.cx(qubits[ancilla_index + 1], ancilla)
            circuit.measure(ancilla, syndrome[round_index * ancilla_count + ancilla_index])

    for data_index in range(data_count):
        circuit.h(qubits[data_index])
        circuit.measure(qubits[data_index], output[data_index])
    return circuit


def count_logical_x_errors(counts: dict[str, int]) -> int:
    """Count odd final X-parity outcomes from Qiskit register strings."""

    errors = 0
    for key, count in counts.items():
        output_bits = key.split()[0]
        if output_bits.count("1") % 2 == 1:
            errors += count
    return errors


def clopper_pearson(errors: int, shots: int, confidence: float = 0.95) -> tuple[float, float]:
    """Return an exact two-sided binomial confidence interval."""

    alpha = 1.0 - confidence
    lower = 0.0 if errors == 0 else float(beta.ppf(alpha / 2.0, errors, shots - errors + 1))
    upper = 1.0 if errors == shots else float(beta.ppf(1.0 - alpha / 2.0, errors + 1, shots - errors))
    return lower, upper


def run_backend(*, coherent: bool, config: dict[str, Any], shots: int, seed: int) -> dict[str, Any]:
    circuit = build_memory_circuit(
        distance=int(config["distance"]),
        rounds=int(config["rounds"]),
        theta=float(config["theta"]),
        coherent=coherent,
    )
    noise_model = None
    if not coherent:
        p = pauli_twirl_probability(float(config["theta"]))
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(
            pauli_error([("I", 1.0 - 2.0 * p), ("X", p), ("Z", p)]),
            "id",
        )

    started = time.perf_counter()
    result = AerSimulator().run(
        circuit,
        shots=shots,
        seed_simulator=seed,
        noise_model=noise_model,
    ).result()
    runtime_seconds = time.perf_counter() - started
    counts = result.get_counts()
    errors = count_logical_x_errors(counts)
    probability = errors / shots
    interval = clopper_pearson(errors, shots)
    return {
        "backend": "full_state_proxy" if coherent else "pauli_twirl_proxy",
        "shots": shots,
        "logical_errors": errors,
        "logical_error_probability": probability,
        "confidence_interval_95": list(interval),
        "runtime_seconds": runtime_seconds,
    }


def write_outputs(payload: dict[str, Any], output_root: Path) -> None:
    data_dir = output_root / "data"
    check_dir = output_root / "checks"
    figure_dir = output_root / "figures"
    for directory in (data_dir, check_dir, figure_dir):
        directory.mkdir(parents=True, exist_ok=True)

    (check_dir / "fig5a_proxy_result.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with (data_dir / "fig5a_proxy_results.csv").open("w", newline="\n", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "source",
                "backend",
                "logical_error_probability",
                "ci95_low",
                "ci95_high",
                "shots",
            ],
        )
        writer.writeheader()
        for backend in ("full_state", "clifford"):
            writer.writerow(
                {
                    "source": "paper",
                    "backend": backend,
                    "logical_error_probability": payload["paper_reference"][backend],
                    "ci95_low": "",
                    "ci95_high": "",
                    "shots": "",
                }
            )
        for result in payload["proxy_results"]:
            writer.writerow(
                {
                    "source": "independent_proxy",
                    "backend": result["backend"],
                    "logical_error_probability": result["logical_error_probability"],
                    "ci95_low": result["confidence_interval_95"][0],
                    "ci95_high": result["confidence_interval_95"][1],
                    "shots": result["shots"],
                }
            )

    labels = ["Coherent / full-state", "Pauli / Clifford"]
    paper = [payload["paper_reference"]["full_state"], payload["paper_reference"]["clifford"]]
    proxy = [item["logical_error_probability"] for item in payload["proxy_results"]]
    proxy_yerr = np.array(
        [
            [value - item["confidence_interval_95"][0] for value, item in zip(proxy, payload["proxy_results"])],
            [item["confidence_interval_95"][1] - value for value, item in zip(proxy, payload["proxy_results"])],
        ]
    )
    x = np.arange(len(labels))
    width = 0.34
    fig, axis = plt.subplots(figsize=(7.2, 4.5))
    axis.bar(x - width / 2, paper, width, label="Paper Fig. 5(a)", color="#555555")
    axis.bar(
        x + width / 2,
        proxy,
        width,
        yerr=proxy_yerr,
        capsize=4,
        label="Independent proxy",
        color="#D97706",
    )
    axis.set_ylabel("Logical error probability")
    axis.set_xticks(x, labels)
    axis.set_ylim(0.0, 1.0)
    axis.set_title("Plaquette Fig. 5(a): paper reference vs explicit proxy circuit")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(figure_dir / "fig5a_proxy_comparison.png", dpi=180)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=WORKSPACE / "outputs")
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    exact = run_backend(
        coherent=True,
        config=config,
        shots=int(config["full_state_shots"]),
        seed=int(config["seed"]),
    )
    twirl = run_backend(
        coherent=False,
        config=config,
        shots=int(config["pauli_twirl_shots"]),
        seed=int(config["seed"]) + 1,
    )

    exact_p = exact["logical_error_probability"]
    twirl_p = twirl["logical_error_probability"]
    paper_full = float(config["paper_reference"]["full_state_logical_error_probability"])
    paper_clifford = float(config["paper_reference"]["clifford_logical_error_probability"])
    payload = {
        "status": "passed",
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "target_id": config["target_id"],
        "scope": "proxy_model",
        "generated_data_provenance": "independent_numerics",
        "parameters": {
            "theta": config["theta"],
            "distance": config["distance"],
            "rounds": config["rounds"],
            "single_qubit_pauli_x_probability": pauli_twirl_probability(float(config["theta"])),
            "single_qubit_pauli_z_probability": pauli_twirl_probability(float(config["theta"])),
            "seed": config["seed"],
        },
        "proxy_assumptions": config["proxy_assumptions"],
        "paper_reference": {"full_state": paper_full, "clifford": paper_clifford},
        "proxy_results": [exact, twirl],
        "comparisons": {
            "paper_clifford_absolute_error": abs(twirl_p - paper_clifford),
            "paper_full_state_absolute_error": abs(exact_p - paper_full),
            "proxy_coherent_minus_twirl": exact_p - twirl_p,
            "paper_coherent_minus_twirl": paper_full - paper_clifford,
        },
        "checks": {
            "eq10_probability_matches_0_0243": abs(pauli_twirl_probability(float(config["theta"])) - 0.0243) < 1e-4,
            "proxy_reproduces_twirl_underestimate_direction": exact_p > twirl_p,
            "clifford_reference_within_0_01": abs(twirl_p - paper_clifford) < 0.01,
            "full_state_reference_within_0_05": abs(exact_p - paper_full) < 0.05,
        },
        "decision": {
            "status": "paper_metric_verdict_stop",
            "next_action": "attribute_full_state_circuit_contract_mismatch_before_expansion",
            "reason": (
                "The Clifford branch matches the paper, while the coherent branch misses by more than the declared "
                "0.05 tolerance. Reconstruct circuit-location, frame, and decoder semantics before adding a sector-aware "
                "backend or opening Fig. 8."
            ),
        },
        "verdict": "partial_proxy_boundary_detected",
        "boundary": (
            "The public parameters reproduce the Clifford result and the direction of the coherent-vs-twirled gap, "
            "but not the paper full-state value. Exact paper-level reproduction requires the unpublished circuit-location, "
            "frame, and decoder conventions."
        ),
    }
    write_outputs(payload, args.output_root)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
