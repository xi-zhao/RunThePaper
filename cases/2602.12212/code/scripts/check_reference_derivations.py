#!/usr/bin/env python3
"""Numerically check the Toth-Petz and Yu identities used by the tutorial note."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT = WORKSPACE / "outputs" / "checks" / "reference_derivation_checks.json"
TOLERANCE = 1e-10


def hermitian_random(rng: np.random.Generator, dimension: int) -> np.ndarray:
    raw = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    return (raw + raw.conj().T) / 2


def density_random(rng: np.random.Generator, dimension: int) -> np.ndarray:
    raw = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    density = raw @ raw.conj().T + 0.2 * np.eye(dimension)
    return density / np.trace(density)


def variance(state: np.ndarray, observable: np.ndarray) -> float:
    mean = np.vdot(state, observable @ state)
    second = np.vdot(state, observable @ observable @ state)
    return float(np.real(second - mean * mean))


def yu_trial(
    rng: np.random.Generator, dimension: int
) -> dict[str, float | int]:
    density = density_random(rng, dimension)
    observable = hermitian_random(rng, dimension)
    eigenvalues, eigenvectors = np.linalg.eigh(density)
    observable_eigenbasis = eigenvectors.conj().T @ observable @ eigenvectors

    root_products = np.sqrt(eigenvalues[:, None] * eigenvalues[None, :])
    eigenvalue_sums = eigenvalues[:, None] + eigenvalues[None, :]
    y_matrix = 2 * root_products / eigenvalue_sums * observable_eigenbasis
    z_matrix = (
        np.sqrt(2 * eigenvalues[:, None] * eigenvalues[None, :] / eigenvalue_sums)
        * observable_eigenbasis
    )

    alpha, y_eigenvectors = np.linalg.eigh(y_matrix)
    # U[k, a] = <psi_a | y_k>; eigh stores |y_k> in column k.
    unitary = y_eigenvectors.T
    probabilities = np.sum(np.abs(unitary) ** 2 * eigenvalues[None, :], axis=1)
    states = np.empty((dimension, dimension), dtype=complex)
    for index in range(dimension):
        support_state = np.sqrt(eigenvalues) * unitary[index]
        states[:, index] = (
            eigenvectors @ support_state / np.sqrt(probabilities[index])
        )

    reconstructed = sum(
        probabilities[index]
        * np.outer(states[:, index], states[:, index].conj())
        for index in range(dimension)
    )
    representative_energies = np.asarray(
        [
            np.real(np.vdot(states[:, index], observable @ states[:, index]))
            for index in range(dimension)
        ]
    )
    averaged_variance = sum(
        probabilities[index] * variance(states[:, index], observable)
        for index in range(dimension)
    )

    differences = eigenvalues[:, None] - eigenvalues[None, :]
    qfi = float(
        np.real(
            2
            * np.sum(
                differences**2
                / eigenvalue_sums
                * np.abs(observable_eigenbasis) ** 2
            )
        )
    )
    density_second_moment = float(
        np.real(np.trace(density @ observable @ observable))
    )
    z_second_moment = float(np.real(np.trace(z_matrix @ z_matrix)))

    return {
        "dimension": dimension,
        "reconstruction_error": float(np.linalg.norm(reconstructed - density)),
        "probability_normalization_error": float(abs(np.sum(probabilities) - 1)),
        "representative_energy_error": float(
            np.max(np.abs(representative_energies - alpha))
        ),
        "convex_roof_error": float(abs(averaged_variance - qfi / 4)),
        "z_trace_identity_error": float(
            abs(density_second_moment - z_second_moment - qfi / 4)
        ),
        "y_hermiticity_error": float(np.linalg.norm(y_matrix - y_matrix.conj().T)),
        "z_hermiticity_error": float(np.linalg.norm(z_matrix - z_matrix.conj().T)),
    }


def qubit_roof_trial(q: float) -> dict[str, float]:
    density = np.diag([q, 1 - q]).astype(complex)
    sigma_x = np.asarray([[0, 1], [1, 0]], dtype=complex)
    minimum_states = (
        np.asarray([np.sqrt(q), np.sqrt(1 - q)], dtype=complex),
        np.asarray([np.sqrt(q), -np.sqrt(1 - q)], dtype=complex),
    )
    maximum_states = (
        np.asarray([np.sqrt(q), 1j * np.sqrt(1 - q)], dtype=complex),
        np.asarray([np.sqrt(q), -1j * np.sqrt(1 - q)], dtype=complex),
    )

    reconstructed_minimum = sum(
        0.5 * np.outer(state, state.conj()) for state in minimum_states
    )
    reconstructed_maximum = sum(
        0.5 * np.outer(state, state.conj()) for state in maximum_states
    )
    minimum_average = sum(
        0.5 * variance(state, sigma_x) for state in minimum_states
    )
    maximum_average = sum(
        0.5 * variance(state, sigma_x) for state in maximum_states
    )
    qfi_quarter = (2 * q - 1) ** 2
    mixed_variance = float(
        np.real(
            np.trace(density @ sigma_x @ sigma_x)
            - np.trace(density @ sigma_x) ** 2
        )
    )
    return {
        "q": q,
        "minimum_reconstruction_error": float(
            np.linalg.norm(reconstructed_minimum - density)
        ),
        "maximum_reconstruction_error": float(
            np.linalg.norm(reconstructed_maximum - density)
        ),
        "minimum_roof_error": float(abs(minimum_average - qfi_quarter)),
        "maximum_roof_error": float(abs(maximum_average - mixed_variance)),
    }


def main() -> None:
    rng = np.random.default_rng(260212)
    yu_trials = [yu_trial(rng, dimension) for dimension in (2, 3, 4, 5)]
    qubit_trials = [qubit_roof_trial(q) for q in (0.17, 0.5, 0.83)]
    errors = [
        float(value)
        for trial in (*yu_trials, *qubit_trials)
        for key, value in trial.items()
        if key.endswith("_error")
    ]
    maximum_error = max(errors, default=0.0)
    payload = {
        "schema_version": 1,
        "paper_id": "2602.12212",
        "status": "passed" if maximum_error <= TOLERANCE else "failed",
        "tolerance": TOLERANCE,
        "maximum_error": maximum_error,
        "yu_trials": yu_trials,
        "qubit_double_roof_trials": qubit_trials,
        "interpretation": (
            "Independent numerical checks of the equations transcribed from "
            "Toth-Petz and Yu; they validate algebraic identities, not the "
            "thermodynamic-limit typicality conjecture."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if payload["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
