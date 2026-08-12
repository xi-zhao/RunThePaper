"""End-to-end paper-parameter reproduction and scientific checks."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from scipy.linalg import expm

from .bosons import trace_gram
from .model import (
    evolve_su4,
    generator_qfi,
    husimi_q,
    maximum_subgroup_qfi,
    normalized_time,
    oat_analytic_axis,
    oat_analytic_qfi,
    oat_state,
    qfim,
    qfim_eigensystem,
    spin_operator_basis,
    subgroup_coefficient_bases,
    su4_hamiltonian,
    su4_initial_state,
    tracked_optimal_generator,
)
from .rendering import (
    render_generator_path,
    render_husimi,
    render_oat_spectrum,
    render_su4_coefficients,
    render_su4_spectrum,
)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_csv(path: Path, columns: Mapping[str, np.ndarray]) -> None:
    names = list(columns)
    arrays = [np.asarray(columns[name]) for name in names]
    lengths = {array.size for array in arrays}
    if len(lengths) != 1:
        raise ValueError(
            f"columns have unequal lengths: {dict(zip(names, map(np.size, arrays), strict=True))}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    values = np.column_stack([array.reshape(-1) for array in arrays])
    np.savetxt(
        path, values, delimiter=",", header=",".join(names), comments="", fmt="%.17g"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assertion(name: str, value: float, limit: float, relation: str) -> dict[str, Any]:
    if relation == "le":
        passed = value <= limit
    elif relation == "ge":
        passed = value >= limit
    else:
        raise ValueError(relation)
    return {
        "name": name,
        "value": float(value),
        "relation": relation,
        "limit": float(limit),
        "status": "passed" if passed else "failed",
    }


def _oat_campaign(
    parameters: Mapping[str, Any], data_dir: Path, figure_dir: Path
) -> dict[str, Any]:
    particles = int(parameters["particles"])
    theta = np.linspace(0.0, np.pi, int(parameters["husimi_theta_points"]))
    phi = np.linspace(-np.pi, np.pi, int(parameters["husimi_phi_points"]))
    squeezed_tau = float(parameters["squeezed_tau"])

    initial_state = oat_state(particles, 0.0)
    squeezed_state = oat_state(particles, squeezed_tau)
    q_initial = husimi_q(initial_state, particles, theta, phi)
    q_squeezed = husimi_q(squeezed_state, particles, theta, phi)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")

    t001_path = data_dir / "T001_main_fig1a_husimi.csv"
    t002_path = data_dir / "T002_main_fig1b_husimi.csv"
    _write_csv(
        t001_path, {"theta": theta_grid, "phi": phi_grid, "probability": q_initial}
    )
    _write_csv(
        t002_path, {"theta": theta_grid, "phi": phi_grid, "probability": q_squeezed}
    )
    render_husimi(figure_dir / "T001_main_fig1a_husimi.png", theta, phi, q_initial)
    render_husimi(figure_dir / "T002_main_fig1b_husimi.png", theta, phi, q_squeezed)

    times = np.linspace(
        float(parameters["tau_min"]),
        float(parameters["tau_max"]),
        int(parameters["oat_time_points"]),
    )
    operator_basis = spin_operator_basis(particles)
    matrices = np.asarray(
        [qfim(oat_state(particles, tau), operator_basis.operators) for tau in times]
    )
    eigenvalues = np.asarray([qfim_eigensystem(matrix)[0] for matrix in matrices])
    coefficients, projectors, ranks, residuals = tracked_optimal_generator(
        matrices,
        seed=(0.0, 1.0, 0.0),
        relative_tolerance=float(parameters["leading_relative_tolerance"]),
    )
    analytic_qfi = oat_analytic_qfi(particles, times)

    spectrum = {
        "tau": times,
        "normalized_time": normalized_time(times),
        "lambda_1": eigenvalues[:, 0],
        "lambda_2": eigenvalues[:, 1],
        "lambda_3": eigenvalues[:, 2],
        "analytic_qfi": analytic_qfi,
    }
    generator = {
        "tau": times,
        "normalized_time": normalized_time(times),
        "coefficient_Jx": coefficients[:, 0],
        "coefficient_Jy": coefficients[:, 1],
        "coefficient_Jz": coefficients[:, 2],
        "lambda_max": eigenvalues[:, 0],
        "leading_rank": ranks,
        "eigen_residual": residuals,
    }
    _write_csv(data_dir / "T003_main_fig1c_qfim.csv", spectrum)
    _write_csv(data_dir / "T004_main_fig1d_generator.csv", generator)
    np.savez_compressed(
        data_dir / "T004_leading_projectors.npz", projectors=projectors, tau=times
    )
    render_oat_spectrum(figure_dir / "T003_main_fig1c_qfim.png", spectrum)
    render_generator_path(figure_dir / "T004_main_fig1d_generator.png", generator)

    early = times <= 1 / np.sqrt(particles)
    analytic_error = float(np.max(np.abs(eigenvalues[early, 0] - analytic_qfi[early])))
    analytic_axes = oat_analytic_axis(particles, times[early])
    analytic_projector_overlap = np.einsum(
        "ti,tij,tj->t", analytic_axes, projectors[early], analytic_axes
    )
    return {
        "matrices": matrices,
        "eigenvalues": eigenvalues,
        "projectors": projectors,
        "residuals": residuals,
        "analytic_error": analytic_error,
        "analytic_axis_min_projector_overlap": float(
            np.min(analytic_projector_overlap[1:])
        ),
        "initial_husimi_max": float(q_initial.max()),
        "squeezed_husimi_max": float(q_squeezed.max()),
    }


def _su4_campaign(
    parameters: Mapping[str, Any], data_dir: Path, figure_dir: Path
) -> dict[str, Any]:
    particles = int(parameters["particles"])
    times = np.linspace(
        float(parameters["tau_min"]),
        float(parameters["tau_max"]),
        int(parameters["su4_time_points"]),
    )
    hamiltonian, operator_basis = su4_hamiltonian(particles)
    initial = su4_initial_state(particles, operator_basis.space)
    states = evolve_su4(hamiltonian, initial, times)
    matrices = np.asarray([qfim(state, operator_basis.operators) for state in states])
    eigenvalues = np.asarray([qfim_eigensystem(matrix)[0] for matrix in matrices])
    subgroup = np.asarray([maximum_subgroup_qfi(matrix) for matrix in matrices])
    coefficients, projectors, ranks, residuals = tracked_optimal_generator(
        matrices,
        seed=(
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ),
        relative_tolerance=float(parameters["leading_relative_tolerance"]),
    )
    norm_drift = np.abs(np.sum(np.abs(states) ** 2, axis=1) - 1.0)

    spectrum: dict[str, np.ndarray] = {
        "tau": times,
        "normalized_time": normalized_time(times),
        "subgroup_max": subgroup,
        "state_norm_error": norm_drift,
    }
    for index in range(8):
        spectrum[f"lambda_{index + 1}"] = eigenvalues[:, index]

    coefficient_data: dict[str, np.ndarray] = {
        "tau": times,
        "normalized_time": normalized_time(times),
        "leading_rank": ranks,
        "eigen_residual": residuals,
    }
    for index, name in enumerate(operator_basis.names):
        coefficient_data[f"coefficient_{name}"] = coefficients[:, index]

    _write_csv(data_dir / "T005_main_fig2a_qfim.csv", spectrum)
    _write_csv(data_dir / "T006_main_fig2b_coefficients.csv", coefficient_data)
    np.savez_compressed(
        data_dir / "T006_leading_projectors.npz",
        projectors=projectors,
        eigenvalues=eigenvalues,
        tau=times,
        operator_names=np.asarray(operator_basis.names),
    )
    render_su4_spectrum(figure_dir / "T005_main_fig2a_qfim.png", spectrum)
    render_su4_coefficients(
        figure_dir / "T006_main_fig2b_coefficients.png",
        normalized_time(times),
        coefficients,
        operator_basis.names,
    )

    midpoint = int(np.argmin(np.abs(times - np.pi / 4)))
    if not np.isclose(times[midpoint], np.pi / 4, atol=1e-14, rtol=0.0):
        raise RuntimeError("the paper grid must contain tau=pi/4 exactly")
    return {
        "hamiltonian": hamiltonian,
        "operator_basis": operator_basis,
        "initial": initial,
        "states": states,
        "matrices": matrices,
        "eigenvalues": eigenvalues,
        "projectors": projectors,
        "coefficients": coefficients,
        "ranks": ranks,
        "residuals": residuals,
        "subgroup": subgroup,
        "norm_drift": norm_drift,
        "midpoint": midpoint,
    }


def _solver_parity(su4: Mapping[str, Any]) -> dict[str, Any]:
    particles = 4
    hamiltonian, basis = su4_hamiltonian(particles)
    initial = su4_initial_state(particles, basis.space)
    times = np.linspace(0.0, np.pi / 2, 9)
    sparse_states = evolve_su4(hamiltonian, initial, times)
    dense_hamiltonian = hamiltonian.toarray()
    dense_states = np.asarray(
        [expm(-1j * dense_hamiltonian * tau) @ initial for tau in times]
    )
    phase_aligned_errors = []
    for sparse_state, dense_state in zip(sparse_states, dense_states, strict=True):
        phase = np.vdot(dense_state, sparse_state)
        if abs(phase) > 0:
            sparse_state = sparse_state * np.exp(-1j * np.angle(phase))
        phase_aligned_errors.append(np.max(np.abs(sparse_state - dense_state)))

    gram = trace_gram(su4["operator_basis"].operators)
    diagonal = np.real(np.diag(gram))
    off_diagonal = gram - np.diag(np.diag(gram))

    test_state = su4["states"][su4["midpoint"]]
    test_matrix = su4["matrices"][su4["midpoint"]]
    coefficients = np.arange(1, 16, dtype=float)
    coefficients /= np.linalg.norm(coefficients)
    operators = su4["operator_basis"].operators
    generator_sparse = coefficients[0] * operators[0]
    for coefficient, operator in zip(coefficients[1:], operators[1:], strict=True):
        generator_sparse = generator_sparse + coefficient * operator
    generator = generator_sparse.toarray()
    epsilon = 1e-3
    overlap = np.vdot(test_state, expm(-1j * epsilon * generator) @ test_state)
    fidelity_qfi = 4 * (1 - abs(overlap) ** 2) / epsilon**2
    covariance_qfi = generator_qfi(test_matrix, coefficients)

    return {
        "status": "passed",
        "small_n_dense_sparse_max_error": float(max(phase_aligned_errors)),
        "operator_trace_gram_max_off_diagonal": float(np.max(np.abs(off_diagonal))),
        "operator_trace_gram_relative_diagonal_spread": float(
            np.ptp(diagonal) / np.mean(diagonal)
        ),
        "fidelity_qfi": float(fidelity_qfi),
        "covariance_qfi": float(covariance_qfi),
        "fidelity_covariance_relative_error": float(
            abs(fidelity_qfi - covariance_qfi) / covariance_qfi
        ),
    }


def _paper_consistency(su4: Mapping[str, Any]) -> dict[str, Any]:
    initial_qfim = su4["matrices"][0]
    j_basis, k_basis, _ = subgroup_coefficient_bases()
    qfi_jx = generator_qfi(initial_qfim, j_basis[:, 0])
    qfi_ky = generator_qfi(initial_qfim, k_basis[:, 1])
    qfi_kz = generator_qfi(initial_qfim, k_basis[:, 2])
    return {
        "status": "inconclusive",
        "paper_error_candidate_emitted": False,
        "source_statement": "Main text calls the explicit initial ket a simultaneous eigenstate of J_x and K_y.",
        "explicit_ket_check": {
            "qfi_Jx": float(qfi_jx),
            "qfi_Ky": float(qfi_ky),
            "qfi_Kz": float(qfi_kz),
            "interpretation": "Zero QFI is the variance-zero eigenstate condition. The printed ket is a J_x and K_z eigenstate, not a K_y eigenstate, under the supplement's operator definitions.",
        },
        "impact": "The numerical implementation follows the explicit ket. The adjacent axis label does not change the reproduced figures, but it is a falsifiable textual inconsistency.",
        "remaining_gates": [
            "fresh-context inventory-first review",
            "independent check of alternative phase or axis conventions",
            "erratum or author clarification search",
        ],
    }


def _science_checks(
    parameters: Mapping[str, Any], oat: Mapping[str, Any], su4: Mapping[str, Any]
) -> dict[str, Any]:
    particles = int(parameters["particles"])
    midpoint = int(su4["midpoint"])
    ratios = su4["eigenvalues"][midpoint, [0, 2, 7]] / particles**2
    printed = np.asarray([0.307, 0.189, 0.117])
    oat_initial = oat["eigenvalues"][0]
    oat_final = oat["eigenvalues"][-1]
    su4_initial = su4["eigenvalues"][0]
    qfim_minimum = min(
        min(float(np.min(np.linalg.eigvalsh(matrix))) for matrix in oat["matrices"]),
        min(float(np.min(np.linalg.eigvalsh(matrix))) for matrix in su4["matrices"]),
    )
    assertions = [
        _assertion(
            "T001 initial Husimi maximum equals one",
            abs(oat["initial_husimi_max"] - 1),
            2e-12,
            "le",
        ),
        _assertion(
            "T002 squeezed Husimi remains a probability",
            oat["squeezed_husimi_max"],
            1.0 + 2e-12,
            "le",
        ),
        _assertion(
            "T003 analytic OAT parity",
            oat["analytic_error"],
            float(parameters["analytic_early_time_tolerance"]),
            "le",
        ),
        _assertion(
            "T003 initial spectrum",
            float(np.max(np.abs(oat_initial - [particles, particles, 0]))),
            2e-10,
            "le",
        ),
        _assertion(
            "T003 final NOON spectrum",
            float(np.max(np.abs(oat_final - [particles**2, particles, particles]))),
            2e-8,
            "le",
        ),
        _assertion(
            "T004 eigen residual",
            float(np.max(oat["residuals"])),
            float(parameters["eigen_residual_tolerance"]),
            "le",
        ),
        _assertion(
            "T004 analytic-axis leading-space overlap",
            oat["analytic_axis_min_projector_overlap"],
            1 - 2e-8,
            "ge",
        ),
        _assertion(
            "T005 state norm drift",
            float(np.max(su4["norm_drift"])),
            float(parameters["norm_tolerance"]),
            "le",
        ),
        _assertion(
            "T005 six SQL eigenvalues at tau=0",
            float(np.max(np.abs(su4_initial[:6] - particles))),
            2e-9,
            "le",
        ),
        _assertion(
            "T005 remaining initial eigenvalues vanish",
            float(np.max(np.abs(su4_initial[6:]))),
            2e-9,
            "le",
        ),
        _assertion(
            "T005 leading peak near 146",
            abs(float(np.max(su4["eigenvalues"][:, 0])) - 146),
            1.0,
            "le",
        ),
        _assertion(
            "T005 printed pi/4 anchors",
            float(np.max(np.abs(ratios - printed))),
            float(parameters["printed_anchor_tolerance"]),
            "le",
        ),
        _assertion(
            "T005 subgroup QFI never exceeds global optimum",
            float(np.max(su4["subgroup"] - su4["eigenvalues"][:, 0])),
            2e-9,
            "le",
        ),
        _assertion(
            "T006 representative normalization",
            float(np.max(np.abs(np.sum(su4["coefficients"] ** 2, axis=1) - 1.0))),
            2e-12,
            "le",
        ),
        _assertion(
            "T006 projector rank trace",
            float(
                np.max(
                    np.abs(np.trace(su4["projectors"], axis1=1, axis2=2) - su4["ranks"])
                )
            ),
            2e-9,
            "le",
        ),
        _assertion(
            "T006 eigen residual",
            float(np.max(su4["residuals"])),
            float(parameters["eigen_residual_tolerance"]),
            "le",
        ),
        _assertion(
            "all QFIMs positive semidefinite",
            -qfim_minimum,
            float(parameters["qfim_negative_tolerance"]),
            "le",
        ),
    ]
    failed = [item["name"] for item in assertions if item["status"] != "passed"]
    return {
        "status": "passed" if not failed else "failed",
        "assertions": assertions,
        "failed": failed,
        "paper_anchors": {
            "su4_leading_peak": float(np.max(su4["eigenvalues"][:, 0])),
            "su4_leading_peak_tau": float(
                np.linspace(
                    float(parameters["tau_min"]),
                    float(parameters["tau_max"]),
                    int(parameters["su4_time_points"]),
                )[np.argmax(su4["eigenvalues"][:, 0])]
            ),
            "pi_over_4_ratios": ratios.tolist(),
            "oat_final_spectrum": oat_final.tolist(),
        },
    }


def run_reproduction(config_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    workspace = config_path.resolve().parents[1]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    data_dir = workspace / "outputs" / "data"
    figure_dir = workspace / "outputs" / "figures"
    checks_dir = workspace / "outputs" / "checks"
    for directory in (data_dir, figure_dir, checks_dir):
        directory.mkdir(parents=True, exist_ok=True)

    oat = _oat_campaign(parameters, data_dir, figure_dir)
    su4 = _su4_campaign(parameters, data_dir, figure_dir)
    target_checks = _science_checks(parameters, oat, su4)
    solver_parity = _solver_parity(su4)
    paper_consistency = _paper_consistency(su4)
    _write_json(checks_dir / "target_checks.json", target_checks)
    _write_json(checks_dir / "solver_parity.json", solver_parity)
    _write_json(checks_dir / "paper_consistency_checks.json", paper_consistency)

    if target_checks["status"] != "passed":
        raise RuntimeError(f"scientific checks failed: {target_checks['failed']}")
    if (
        solver_parity["small_n_dense_sparse_max_error"] > 2e-11
        or solver_parity["operator_trace_gram_relative_diagonal_spread"] > 2e-12
        or solver_parity["fidelity_covariance_relative_error"] > 2e-4
    ):
        raise RuntimeError(f"solver parity failed: {solver_parity}")

    artifact_paths = sorted(
        [
            *data_dir.glob("*"),
            *figure_dir.glob("*"),
            checks_dir / "target_checks.json",
            checks_dir / "solver_parity.json",
            checks_dir / "paper_consistency_checks.json",
        ]
    )
    manifest = {
        "status": "passed",
        "generated_data_provenance": "independent_numerics",
        "source_pixels_are_numerical_inputs": False,
        "author_code_used": False,
        "author_arrays_used": False,
        "config_sha256": _sha256(config_path),
        "artifacts": [
            {
                "path": str(path.relative_to(workspace)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in artifact_paths
        ],
    }
    _write_json(checks_dir / "generated_data_manifest.json", manifest)
    summary = {
        "status": "passed",
        "paper_id": "2305.15556",
        "artifact_stage": config["artifact_stage"],
        "parameter_match": config["parameter_match"],
        "target_ids": ["T001", "T002", "T003", "T004", "T005", "T006"],
        "duration_seconds": time.perf_counter() - started,
        "particles": int(parameters["particles"]),
        "su4_dimension": int(su4["operator_basis"].space.dimension),
        "science_assertions_passed": len(target_checks["assertions"]),
        "science_assertions_total": len(target_checks["assertions"]),
    }
    _write_json(checks_dir / "run_summary.json", summary)
    return summary
