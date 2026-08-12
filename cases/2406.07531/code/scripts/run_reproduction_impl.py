#!/usr/bin/env python3
"""Run independent small-system checks without reading paper artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from ibdet_reproduction.baths import (  # noqa: E402
    combine_embedding_basis,
    density_matrix_bath,
    green_function_bath,
    natural_orbital_bath,
)
from ibdet_reproduction.ed import (  # noqa: E402
    one_body_matrix,
    solve_lehmann_green_function,
)
from ibdet_reproduction.embedding import (  # noqa: E402
    combine_gw_ibdet,
    hf_self_energy,
    local_only_correction,
    project_hamiltonian,
)
from ibdet_reproduction.spectra import (  # noqa: E402
    dyson_green_function,
    occupied_bandwidth,
    spectral_function,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def mean_field_density(one_body: np.ndarray, n_electrons: int) -> np.ndarray:
    _, orbitals = np.linalg.eigh(one_body)
    occupied = orbitals[:, :n_electrons]
    return occupied @ occupied.conj().T


def synthetic_eri(dimension: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    metric = rng.normal(size=(dimension, dimension))
    metric = 0.5 * (metric + metric.T) / dimension
    return np.einsum("pq,rs->pqrs", metric, metric, optimize=True)


def assertion(
    assertion_id: str,
    value: float,
    tolerance: float,
    *,
    comparison: str = "less_equal",
    essential: bool = True,
) -> dict[str, object]:
    if comparison == "less_equal":
        passed = value <= tolerance
    elif comparison == "greater_equal":
        passed = value >= tolerance
    else:
        raise ValueError(f"unknown comparison {comparison}")
    return {
        "assertion_id": assertion_id,
        "essential": essential,
        "comparison": comparison,
        "value": float(value),
        "tolerance": float(tolerance),
        "status": "passed" if passed else "failed",
    }


def run(config_path: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    n_sites = int(parameters["n_sites"])
    n_electrons = int(parameters["n_electrons"])
    frequency = np.linspace(
        float(parameters["frequency_min_ev"]),
        float(parameters["frequency_max_ev"]),
        int(parameters["frequency_points"]),
    )
    broadening = float(parameters["broadening_ev"])
    result = solve_lehmann_green_function(
        n_sites,
        n_electrons,
        frequency,
        hopping=float(parameters["hopping_ev"]),
        onsite_u=float(parameters["onsite_u_ev"]),
        nearest_v=float(parameters["nearest_v_ev"]),
        broadening=broadening,
        periodic=bool(parameters["periodic"]),
    )
    one_body = one_body_matrix(
        n_sites,
        float(parameters["hopping_ev"]),
        periodic=bool(parameters["periodic"]),
    )
    mean_density = mean_field_density(one_body, n_electrons)
    impurity = [int(value) for value in parameters["impurity_spin_orbitals"]]
    impurity_basis = np.zeros((2 * n_sites, len(impurity)), dtype=np.complex128)
    impurity_basis[impurity, np.arange(len(impurity))] = 1.0
    density_bath = density_matrix_bath(
        mean_density,
        impurity,
        singular_value_threshold=float(parameters["density_bath_threshold"]),
    )
    fixed = np.concatenate([impurity_basis, density_bath.orbitals], axis=1)
    green_frequency = np.linspace(
        float(parameters["frequency_min_ev"]),
        float(parameters["frequency_max_ev"]),
        int(parameters["green_bath_frequency_points"]),
    )
    green_bath = green_function_bath(
        one_body,
        impurity,
        green_frequency,
        chemical_potential=result.chemical_potential,
        broadening=broadening,
        singular_value_threshold=float(parameters["green_bath_threshold"]),
        against=fixed,
    )
    fixed_with_green = np.concatenate([fixed, green_bath.orbitals], axis=1)
    natural_bath = natural_orbital_bath(
        result.density,
        impurity,
        occupation_threshold=float(parameters["natural_occupation_threshold"]),
        against=fixed_with_green,
    )
    rotation = combine_embedding_basis(
        2 * n_sites,
        impurity,
        [density_bath, green_bath, natural_bath],
    )

    reconstructed_mean_density = (
        rotation @ (rotation.conj().T @ mean_density @ rotation) @ rotation.conj().T
    )
    impurity_density_error = np.max(
        np.abs(
            reconstructed_mean_density[np.ix_(impurity, impurity)]
            - mean_density[np.ix_(impurity, impurity)]
        )
    )
    eri = synthetic_eri(2 * n_sites, int(parameters["random_seed"]))
    projected = project_hamiltonian(one_body, mean_density, eri, rotation)
    hf_reconstruction_error = np.max(
        np.abs(
            projected["one_body"]
            + hf_self_energy(projected["density"], projected["eri"])
            - projected["fock"]
        )
    )
    zero = np.zeros_like(result.self_energy)
    gw_limit_error = np.max(
        np.abs(combine_gw_ibdet(result.self_energy, zero, zero) - result.self_energy)
    )
    labels = np.repeat(np.arange(n_sites), 2)
    local_sigma = local_only_correction(result.self_energy, labels)
    full_green = dyson_green_function(
        one_body,
        result.self_energy,
        frequency,
        chemical_potential=result.chemical_potential,
        broadening=broadening,
    )
    local_green = dyson_green_function(
        one_body,
        local_sigma,
        frequency,
        chemical_potential=result.chemical_potential,
        broadening=broadening,
    )
    full_dos = spectral_function(full_green)
    local_dos = spectral_function(local_green)
    lehmann_dos = spectral_function(result.green)
    spectral_weight = float(np.trapezoid(lehmann_dos, frequency))
    particle_trace_error = abs(float(np.trace(result.density).real) - n_electrons)
    embedding_orthogonality = np.max(
        np.abs(rotation.conj().T @ rotation - np.eye(rotation.shape[1]))
    )
    nonlocal_effect = float(np.max(np.abs(full_dos - local_dos)))
    diagonal_causality = float(
        np.max(np.imag(np.diagonal(result.self_energy, axis1=1, axis2=2)))
    )
    full_bandwidth = occupied_bandwidth(
        frequency,
        full_dos,
        chemical_potential=0.0,
        relative_threshold=0.02,
    )
    local_bandwidth = occupied_bandwidth(
        frequency,
        local_dos,
        chemical_potential=0.0,
        relative_threshold=0.02,
    )

    shell_distance = np.asarray(
        [min(site, n_sites - site) for site in range(n_sites) for _ in (0, 1)],
        dtype=int,
    )
    selected_indices = [
        int(np.argmin(np.abs(frequency - value))) for value in (-3.0, 0.0)
    ]
    shell_values = np.zeros((2, int(np.max(shell_distance)) + 1), dtype=np.complex128)
    for frequency_index, data_index in enumerate(selected_indices):
        for shell in range(shell_values.shape[1]):
            columns = np.flatnonzero(shell_distance == shell)
            shell_values[frequency_index, shell] = np.mean(
                result.self_energy[data_index, impurity[0], columns]
            )

    assertions = [
        assertion("embedding_orthonormality", embedding_orthogonality, 1e-10),
        assertion("bdm_impurity_density_reproduction", impurity_density_error, 1e-10),
        assertion("hf_subtraction_roundtrip", hf_reconstruction_error, 1e-10),
        assertion("gw_replacement_limit", gw_limit_error, 1e-12),
        assertion("particle_number_trace", particle_trace_error, 1e-10),
        assertion(
            "spectral_sum_rule_relative",
            abs(spectral_weight / (2 * n_sites) - 1.0),
            0.08,
        ),
        assertion("retarded_self_energy_causality", diagonal_causality, 5e-8),
        assertion(
            "nonlocal_self_energy_changes_dos",
            nonlocal_effect,
            1e-3,
            comparison="greater_equal",
        ),
    ]
    output_root = WORKSPACE / "outputs"
    data_path = output_root / "data" / "feature" / "method_validation.npz"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        data_path,
        frequency_ev=frequency,
        exact_lehmann_dos=lehmann_dos,
        full_dyson_dos=full_dos,
        local_only_dos=local_dos,
        self_energy=result.self_energy,
        local_self_energy=local_sigma,
        shell_distance=np.arange(shell_values.shape[1]),
        shell_frequency_ev=np.asarray([-3.0, 0.0]),
        shell_values=shell_values,
        embedding_rotation=rotation,
        density_bath_strengths=density_bath.strengths,
        green_bath_strengths=green_bath.strengths,
        natural_bath_strengths=natural_bath.strengths,
    )
    check_path = output_root / "checks" / "feature" / "target_checks.json"
    payload = {
        "schema_version": 1,
        "paper_id": "2406.07531",
        "scope": "independent_method_validation_only",
        "paper_figure_targets_executed": False,
        "all_essential_passed": all(
            row["status"] == "passed" for row in assertions if row["essential"]
        ),
        "assertions": assertions,
        "bath_sizes": {
            "B_DM": density_bath.size,
            "B_GF": green_bath.size,
            "B_NO": natural_bath.size,
            "embedding_total": int(rotation.shape[1]),
        },
        "energetics_ev": {
            "ground_energy": result.ground_energy,
            "chemical_potential": result.chemical_potential,
            "addition_threshold": result.addition_threshold,
            "removal_threshold": result.removal_threshold,
            "full_occupied_bandwidth": full_bandwidth,
            "local_occupied_bandwidth": local_bandwidth,
        },
        "boundary": "Passing these checks validates the independent algebra and toy-model physics. It does not reproduce material-specific Figs. 2-4.",
    }
    json_write(check_path, payload)
    manifest_path = output_root / "checks" / "feature" / "generated_data_manifest.json"
    json_write(
        manifest_path,
        {
            "schema_version": 1,
            "paper_id": "2406.07531",
            "generated_data_provenance": "independent_numerics",
            "config": {
                "path": "config/feature.json",
                "sha256": sha256(config_path),
            },
            "files": [
                {
                    "path": "outputs/data/feature/method_validation.npz",
                    "sha256": sha256(data_path),
                    "source_pixels_used": False,
                    "author_arrays_used": False,
                },
                {
                    "path": "outputs/checks/feature/target_checks.json",
                    "sha256": sha256(check_path),
                    "source_pixels_used": False,
                    "author_arrays_used": False,
                },
            ],
        },
    )
    return 0 if payload["all_essential_passed"] else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    arguments = parser.parse_args()
    config_path = (WORKSPACE / arguments.config).resolve()
    config_path.relative_to(WORKSPACE)
    return run(config_path)


if __name__ == "__main__":
    raise SystemExit(main())
