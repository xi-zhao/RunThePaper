#!/usr/bin/env python3
"""Run independent small-model validation without reading paper artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from nio_dmft.dmft import (  # noqa: E402
    atomic_spin_correlation,
    fll_double_counting,
    hubbard_i_self_energy,
    run_hubbard_i_dmft,
)
from nio_dmft.lattice import build_layered_pd_model  # noqa: E402
from nio_dmft.observables import (  # noqa: E402
    imaginary_time_symmetry_error,
    integrated_spectral_weight,
    spectral_observables,
    surface_energy,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def assertion(
    assertion_id: str,
    value: float,
    tolerance: float,
    *,
    comparison: str = "less_equal",
) -> dict[str, object]:
    if comparison == "less_equal":
        passed = value <= tolerance
    elif comparison == "greater_equal":
        passed = value >= tolerance
    else:
        raise ValueError(f"unknown comparison {comparison}")
    return {
        "assertion_id": assertion_id,
        "essential": True,
        "comparison": comparison,
        "value": float(value),
        "tolerance": float(tolerance),
        "status": "passed" if passed else "failed",
    }


def build_model(parameters: dict[str, object], orientation: str):
    suffix = "001" if orientation == "001" else "110"
    return build_layered_pd_model(
        orientation=orientation,
        n_layers=int(parameters[f"n_layers_{suffix}"]),
        relaxed=True,
        nk=int(parameters["nk"]),
        epsilon_d=float(parameters["epsilon_d_ev"]),
        epsilon_p=float(parameters["epsilon_p_ev"]),
        inplane_d_hopping=float(parameters["inplane_d_hopping_ev"]),
        inplane_p_hopping=float(parameters["inplane_p_hopping_ev"]),
        interlayer_d_hopping=float(parameters["interlayer_d_hopping_ev"]),
        interlayer_p_hopping=float(parameters["interlayer_p_hopping_ev"]),
        pd_hybridization=float(parameters["pd_hybridization_ev"]),
        surface_coordination=float(parameters[f"surface_coordination_{suffix}"]),
        surface_crystal_field=float(parameters[f"surface_crystal_field_{suffix}_ev"]),
        relaxation_scale=float(parameters[f"relaxation_scale_{suffix}"]),
    )


def run(config_path: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("scope") != "independent_method_validation_only":
        raise ValueError("feature runner refuses a target-reproduction config")
    parameters = config["parameters"]
    omega = np.linspace(
        float(parameters["omega_min_ev"]),
        float(parameters["omega_max_ev"]),
        int(parameters["omega_points"]),
    )
    results: dict[str, object] = {}
    assertions: list[dict[str, object]] = []
    archive: dict[str, np.ndarray] = {"omega_ev": omega}
    for orientation in ("001", "110"):
        model = build_model(parameters, orientation)
        dmft = run_hubbard_i_dmft(
            model,
            beta=float(parameters["beta_ev_inverse"]),
            n_iw=int(parameters["n_iw"]),
            chemical_potential=float(parameters["chemical_potential_ev"]),
            epsilon_d=float(parameters["epsilon_d_ev"]),
            hubbard_u=float(parameters["hubbard_u_ev"]),
            hund_j=float(parameters["hund_j_ev"]),
            initial_occupancy=float(parameters["initial_occupancy"]),
            mixing=float(parameters["mixing"]),
            tolerance=float(parameters["tolerance"]),
            max_iterations=int(parameters["max_iterations"]),
        )
        dc = fll_double_counting(
            dmft.occupancies,
            hubbard_u=float(parameters["hubbard_u_ev"]),
            hund_j=float(parameters["hund_j_ev"]),
        )
        retarded_sigma = hubbard_i_self_energy(
            omega + 1j * float(parameters["broadening_ev"]),
            occupancy=dmft.occupancies,
            epsilon_d=float(parameters["epsilon_d_ev"]),
            chemical_potential=float(parameters["chemical_potential_ev"]),
            hubbard_u=float(parameters["hubbard_u_ev"]),
            double_counting=dc,
        )
        spectra = spectral_observables(
            model,
            omega,
            retarded_sigma,
            chemical_potential=float(parameters["chemical_potential_ev"]),
            broadening=float(parameters["broadening_ev"]),
        )
        weights = integrated_spectral_weight(omega, spectra["total_dos"])
        inversion_error = float(
            np.max(np.abs(dmft.occupancies - dmft.occupancies[::-1]))
        )
        surface_response = float(
            np.max(
                np.abs(
                    spectra["d_dos"][:, 0] - spectra["d_dos"][:, model.n_layers // 2]
                )
            )
        )
        suffix = orientation
        assertions.extend(
            [
                assertion(
                    f"{suffix}_fixed_point_residual",
                    float(dmft.residual_history[-1]),
                    float(parameters["tolerance"]),
                ),
                assertion(f"{suffix}_inversion_symmetry", inversion_error, 1e-10),
                assertion(
                    f"{suffix}_retarded_causality",
                    float(np.max(np.imag(retarded_sigma))),
                    1e-10,
                ),
                assertion(
                    f"{suffix}_spectral_nonnegativity",
                    float(-np.min(spectra["total_dos"])),
                    1e-10,
                ),
                assertion(
                    f"{suffix}_spectral_sum_rule",
                    abs(float(weights) / model.n_orbitals - 1.0),
                    0.12,
                ),
                assertion(
                    f"{suffix}_surface_layer_response",
                    surface_response,
                    1e-3,
                    comparison="greater_equal",
                ),
            ]
        )
        archive[f"dos_{suffix}"] = spectra["total_dos"]
        archive[f"d_dos_{suffix}"] = spectra["d_dos"]
        archive[f"p_dos_{suffix}"] = spectra["p_dos"]
        archive[f"a_k_{suffix}"] = spectra["a_k"]
        archive[f"occupancy_{suffix}"] = dmft.occupancies
        archive[f"sigma_iw_{suffix}"] = dmft.self_energy_iw
        archive[f"sigma_retarded_{suffix}"] = retarded_sigma
        archive[f"residual_{suffix}"] = dmft.residual_history
        results[orientation] = {
            "converged": dmft.converged,
            "iterations": dmft.iterations,
            "final_residual": float(dmft.residual_history[-1]),
            "inversion_error": inversion_error,
            "surface_response": surface_response,
            "spectral_weight_per_orbital": float(weights) / model.n_orbitals,
        }

    tau = np.linspace(0.0, float(parameters["beta_ev_inverse"]), 121)
    chi_tau = atomic_spin_correlation(
        tau,
        beta=float(parameters["beta_ev_inverse"]),
        epsilon_d=float(parameters["epsilon_d_ev"]),
        chemical_potential=float(parameters["chemical_potential_ev"]),
        hubbard_u=float(parameters["hubbard_u_ev"]),
    )
    assertions.append(
        assertion(
            "atomic_spin_correlation_tau_symmetry",
            imaginary_time_symmetry_error(chi_tau),
            1e-14,
        )
    )
    area = 17.0
    bulk_energy = -21.0
    gamma = surface_energy(
        7 * bulk_energy + 2.0 * area * 0.059,
        formula_units=7,
        bulk_energy_ev_per_formula=bulk_energy,
        surface_area_angstrom2=area,
    )
    assertions.append(
        assertion("surface_energy_formula_roundtrip", abs(gamma - 59.0), 1e-10)
    )
    archive["tau_ev_inverse"] = tau
    archive["atomic_chi_tau"] = chi_tau

    output_root = WORKSPACE / "outputs"
    data_path = output_root / "data" / "feature" / "method_validation.npz"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(data_path, **archive)
    check_path = output_root / "checks" / "feature" / "target_checks.json"
    check_payload = {
        "schema_version": 1,
        "paper_id": "2101.12558",
        "scope": "independent_method_validation_only",
        "paper_figure_targets_executed": False,
        "all_essential_passed": all(row["status"] == "passed" for row in assertions),
        "assertions": assertions,
        "orientations": results,
        "boundary": (
            "Passing checks validates the layered Dyson/FLL/Hubbard-I, spectral, "
            "spin-correlation, and surface-energy algebra only; it does not "
            "reproduce any NiO paper panel."
        ),
    }
    write_json(check_path, check_payload)
    manifest_path = output_root / "checks" / "feature" / "generated_data_manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "paper_id": "2101.12558",
            "generated_data_provenance": "independent_numerics",
            "config": {"path": "config/feature.json", "sha256": sha256(config_path)},
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
    return 0 if check_payload["all_essential_passed"] else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    arguments = parser.parse_args()
    config_path = (WORKSPACE / arguments.config).resolve()
    config_path.relative_to(WORKSPACE)
    return run(config_path)


if __name__ == "__main__":
    raise SystemExit(main())
