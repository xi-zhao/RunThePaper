from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from cdhm import CDHM, floquet_bands, initial_populations
from observables import band_populations, evolve_fast, x_expectation
from theory import delta_rho_theory, delta_x_theory


ITEMS_BY_TARGET = {
    "T101": ("Main Figure 1(a)", "Main Figure 1(b)"),
    "T201": ("Main Figure 2(a)", "Main Figure 2(b)"),
    "T301": ("Main Figure 3",),
    "T401": ("Main Figure 4",),
}


def _finite_tree(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    if isinstance(value, (int, float, np.number)):
        return bool(np.isfinite(value))
    return True


def _model(parameters: dict[str, Any], *, j: float, k: float) -> CDHM:
    return CDHM(
        J=j,
        K=k,
        N=int(parameters["N"]),
        tau=float(parameters["tau"]),
        n_sub=int(parameters["n_sub"]),
    )


def _attest_fig1(config: dict[str, Any], common: dict[str, Any]) -> dict[str, Any]:
    model = _model(common, j=float(config["J"]), k=float(config["K"]))
    k_grid = np.linspace(
        -np.pi / model.N,
        np.pi / model.N,
        int(config["Nk"]),
        endpoint=False,
    )
    beta_grid = np.linspace(0.0, 2.0 * np.pi, int(config["Nbeta"]), endpoint=False)
    phases = []
    maximum_unitarity_error = 0.0
    for beta in beta_grid:
        operator = model.floquet_operator(k_grid, float(beta))
        identity = np.eye(model.N)
        error = np.max(
            np.abs(np.swapaxes(operator.conj(), -1, -2) @ operator - identity)
        )
        maximum_unitarity_error = max(maximum_unitarity_error, float(error))
        omega, _ = floquet_bands(model, k_grid, float(beta))
        phases.append(omega)
    populations, *_ = initial_populations(model, k_grid, beta=0.0)
    maximum_population_error = float(
        np.max(np.abs(populations.sum(axis=-1) - 1.0))
    )
    phase_array = np.asarray(phases)
    passed = (
        phase_array.shape == (len(beta_grid), len(k_grid), model.N)
        and np.isfinite(phase_array).all()
        and maximum_unitarity_error < 1e-10
        and maximum_population_error < 1e-10
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "phase_grid_shape": list(phase_array.shape),
        "maximum_unitarity_error": maximum_unitarity_error,
        "maximum_population_normalization_error": maximum_population_error,
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _attest_fig2(config: dict[str, Any], common: dict[str, Any]) -> dict[str, Any]:
    model = _model(common, j=float(config["J"]), k=float(config["K"]))
    nk = int(config["Nk"])
    periods = int(config["T"])
    k_grid = np.linspace(-np.pi / model.N, np.pi / model.N, nk, endpoint=False)
    initial, *_ = initial_populations(model, k_grid, beta=0.0)
    _, final_state, _ = evolve_fast(
        model,
        T=periods,
        Nk=nk,
        n_sub=model.n_sub,
    )
    final = band_populations(model, k_grid, final_state, beta=0.0)
    actual_change = final - initial
    predicted_change, predicted_initial = delta_rho_theory(
        model,
        k_grid,
        T=periods,
        Nbeta_g=int(config["Nbeta_geometric"]),
    )
    conservation_error = float(np.max(np.abs(final.sum(axis=-1) - 1.0)))
    passed = (
        actual_change.shape == predicted_change.shape == predicted_initial.shape
        and np.isfinite(actual_change).all()
        and np.isfinite(predicted_change).all()
        and conservation_error < 1e-9
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "grid_shape": list(actual_change.shape),
        "maximum_population_conservation_error": conservation_error,
        "actual_change_l2": float(np.linalg.norm(actual_change)),
        "equation_8_change_l2": float(np.linalg.norm(predicted_change)),
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _attest_fig3(config: dict[str, Any], common: dict[str, Any]) -> dict[str, Any]:
    model = _model(common, j=float(config["J"]), k=float(config["K"]))
    displacements: dict[str, float] = {}
    for periods in config["T_values"]:
        _, final_state, _ = evolve_fast(
            model,
            T=int(periods),
            Nk=int(config["Nk_dynamics"]),
            n_sub=model.n_sub,
        )
        displacements[str(periods)] = x_expectation(model, final_state)
    theory = delta_x_theory(
        model,
        Nk=int(config["Nk_theory"]),
        Nbeta_F=int(config["Nbeta_berry"]),
        Nbeta_E=int(config["Nbeta_energy"]),
    )
    passed = len(displacements) == len(config["T_values"]) and _finite_tree(
        {"actual": displacements, "theory": theory}
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "actual_displacement_by_T": displacements,
        "equation_13": theory,
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _attest_fig4(config: dict[str, Any], common: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for coupling in config["J_values"]:
        model = _model(common, j=float(coupling), k=float(config["K"]))
        _, final_state, _ = evolve_fast(
            model,
            T=int(config["T"]),
            Nk=int(config["Nk_dynamics"]),
            n_sub=model.n_sub,
        )
        theory = delta_x_theory(
            model,
            Nk=int(config["Nk_theory"]),
            Nbeta_F=int(config["Nbeta_berry"]),
            Nbeta_E=int(config["Nbeta_energy"]),
        )
        rows.append(
            {
                "J": float(coupling),
                "actual_displacement": x_expectation(model, final_state),
                "equation_13_total": theory["total"],
                "berry_only": theory["berry"],
                "chern": theory["chern"],
            }
        )
    passed = len(rows) == len(config["J_values"]) and _finite_tree(rows)
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "scan": rows,
        "paper_target_boundary": config["paper_target_boundary"],
    }


def run_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if config.get("paper_id") != "10.1103-PhysRevB.91.085420":
        raise ValueError("paper_id must be 10.1103-PhysRevB.91.085420")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if parameters.get("profile") != "reduced_implementation_attestation":
        raise ValueError("only the frozen reduced implementation-attestation profile is accepted")
    common = parameters["common"]
    target_checks = {
        "T101": _attest_fig1(parameters["T101"], common),
        "T201": _attest_fig2(parameters["T201"], common),
        "T301": _attest_fig3(parameters["T301"], common),
        "T401": _attest_fig4(parameters["T401"], common),
    }
    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": (
                "attested" if target_checks[target_id]["status"] == "passed" else "failed"
            ),
            "scientific_coverage_changed": False,
        }
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    status = (
        "passed"
        if all(check["status"] == "passed" for check in target_checks.values())
        else "failed"
    )
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": status,
        "profile": parameters["profile"],
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
