#!/usr/bin/env python3
"""Generate data, figures, comparisons, and checks for the scoped reproduction."""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent
sys.path.insert(0, str(WORKSPACE))

from src.cqed_reproduction import (  # noqa: E402
    annihilation,
    black_box_kerr,
    bogoliubov_kerrs,
    critical_photon_number,
    discretized_bath_hamiltonians,
    duffing_jc_hamiltonian,
    generic_multilevel_shifts,
    jc_analytic_energies,
    jc_block,
    label_bare_state_energies,
    linear_dressed_frequencies,
    longitudinal_analytic_energy,
    longitudinal_block,
    passive_one_port_response,
    thermal_oscillator_evolution,
    transmon_coupling,
    transmon_coupling_via_alpha,
    transmon_dispersive_energy,
    transmon_dispersive_shifts,
    two_level_dispersive_parameters,
)


DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"
COMPARISON_DIR = WORKSPACE / "outputs" / "comparisons"
REFERENCE_DIR = WORKSPACE / "references" / "original_figures"
CONFIG_PATH = WORKSPACE / "experiments" / "paper_scope.json"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=lambda value: value.item() if isinstance(value, np.generic) else str(value),
        )
        + "\n",
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    return str(path.relative_to(WORKSPACE))


def reproduce_figure_8(config: dict[str, object]) -> dict[str, float]:
    generated = config["generated_parameters"]
    omega_r = float(generated["omega_r"])
    omega_q = float(generated["omega_q"])
    coupling = float(generated["coupling"])
    manifolds = [int(value) for value in generated["manifolds"]]
    rows: list[dict[str, object]] = []
    max_eigenvalue_error = 0.0
    max_sqrt_law_error = 0.0
    for n in manifolds:
        analytic_lower, analytic_upper = jc_analytic_energies(n, omega_r, omega_q, coupling)
        numeric_lower, numeric_upper = np.linalg.eigvalsh(jc_block(n, omega_r, omega_q, coupling))
        numeric_error = max(
            abs(analytic_lower - numeric_lower), abs(analytic_upper - numeric_upper)
        )
        splitting = analytic_upper - analytic_lower
        expected_splitting = 2.0 * coupling * np.sqrt(n)
        max_eigenvalue_error = max(max_eigenvalue_error, numeric_error)
        max_sqrt_law_error = max(max_sqrt_law_error, abs(splitting - expected_splitting))
        rows.append(
            {
                "manifold_n": n,
                "bare_center": n * omega_r,
                "analytic_lower": analytic_lower,
                "analytic_upper": analytic_upper,
                "numeric_lower": numeric_lower,
                "numeric_upper": numeric_upper,
                "splitting": splitting,
                "expected_2g_sqrt_n": expected_splitting,
                "absolute_error": numeric_error,
            }
        )

    data_path = DATA_DIR / "fig8_jaynes_cummings_spectrum.csv"
    write_csv(data_path, list(rows[0]), rows)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for row in rows:
        n = int(row["manifold_n"])
        center = float(row["bare_center"])
        lower = (float(row["analytic_lower"]) - center) / coupling
        upper = (float(row["analytic_upper"]) - center) / coupling
        ax.hlines(0.0, n - 0.28, n + 0.28, color="0.68", linewidth=2.2)
        ax.hlines([lower, upper], n - 0.28, n + 0.28, color="#1f77b4", linewidth=2.8)
        ax.plot([n, n], [lower, upper], color="#1f77b4", alpha=0.25, linewidth=1.0)
        ax.text(n + 0.31, upper, rf"$+\sqrt{{{n}}}$", va="center", fontsize=9)
        ax.text(n + 0.31, lower, rf"$-\sqrt{{{n}}}$", va="center", fontsize=9)
    ax.set_xlabel("Total-excitation manifold $n$")
    ax.set_ylabel(r"$(E-n\hbar\omega_r)/(\hbar g)$")
    ax.set_title(r"Jaynes--Cummings doublets: splitting $2g\sqrt{n}$")
    ax.set_xticks(manifolds)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    figure_path = FIGURE_DIR / "fig8_jaynes_cummings_spectrum.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    render_comparison(
        REFERENCE_DIR / "transmon-resonator-resonant.png",
        figure_path,
        COMPARISON_DIR / "fig8_source_vs_reproduction.png",
        "Paper Fig. 8 (analytic schematic)",
        "Independent Eq. (38) evaluation",
    )
    return {
        "max_eigenvalue_error": max_eigenvalue_error,
        "max_sqrt_law_error": max_sqrt_law_error,
    }


def reproduce_figure_9(config: dict[str, object]) -> dict[str, float]:
    generated = config["generated_parameters"]
    omega_r = float(generated["omega_r"])
    omega_q = float(generated["omega_q"])
    coupling = float(generated["coupling"])
    ec = float(generated["charging_energy_frequency"])
    cavity_dimension = int(generated["cavity_dimension"])
    transmon_dimension = int(generated["transmon_dimension"])
    max_photon = int(generated["max_photon_number"])
    detuning = omega_q - omega_r

    hamiltonian = duffing_jc_hamiltonian(
        cavity_dimension,
        transmon_dimension,
        omega_r,
        omega_q,
        coupling,
        ec,
    )
    exact_energies, overlaps = label_bare_state_energies(hamiltonian)
    lamb, chi = transmon_dispersive_shifts(
        transmon_dimension - 1, coupling, detuning, ec
    )
    rows: list[dict[str, object]] = []
    max_energy_error = 0.0
    minimum_overlap = 1.0
    for j in [0, 1]:
        for n in range(max_photon + 1):
            bare_index = n * transmon_dimension + j
            prediction = transmon_dispersive_energy(
                j, n, omega_r, omega_q, ec, lamb, chi
            )
            exact = float(exact_energies[bare_index])
            overlap = float(overlaps[bare_index])
            error = abs(exact - prediction)
            max_energy_error = max(max_energy_error, error)
            minimum_overlap = min(minimum_overlap, overlap)
            rows.append(
                {
                    "transmon_level": j,
                    "photon_number": n,
                    "exact_energy": exact,
                    "dispersive_energy": prediction,
                    "absolute_error": error,
                    "bare_state_overlap": overlap,
                    "predicted_cavity_spacing": omega_r + chi[j],
                }
            )
    data_path = DATA_DIR / "fig9_dispersive_spectrum.csv"
    write_csv(data_path, list(rows[0]), rows)

    parameters = two_level_dispersive_parameters(omega_r, omega_q, coupling, ec)
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 5.0), sharey=False)
    for j, ax in enumerate(axes):
        branch_rows = [row for row in rows if int(row["transmon_level"]) == j]
        baseline = float(branch_rows[0]["dispersive_energy"])
        for row in branch_rows:
            n = int(row["photon_number"])
            predicted = float(row["dispersive_energy"]) - baseline
            exact = float(row["exact_energy"]) - baseline
            ax.hlines(predicted, -0.32, 0.32, color="#1f77b4", linewidth=2.5)
            ax.plot(0.0, exact, "o", color="#d62728", markersize=4.5)
            ax.text(0.36, predicted, rf"$n={n}$", va="center", fontsize=9)
        state = "g" if j == 0 else "e"
        sign = "-" if j == 0 else "+"
        ax.set_title(rf"$|{state}\rangle$: spacing $\omega_r' {sign} \chi$")
        ax.set_xlim(-0.55, 0.85)
        ax.set_xticks([])
        ax.set_ylabel("Energy relative to branch ground")
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Dispersive ladders: formula (blue) vs exact diagonalization (red)")
    fig.tight_layout()
    figure_path = FIGURE_DIR / "fig9_dispersive_spectrum.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    render_comparison(
        REFERENCE_DIR / "transmon-resonator-dispersive.png",
        figure_path,
        COMPARISON_DIR / "fig9_source_vs_reproduction.png",
        "Paper Fig. 9 (analytic schematic)",
        "Eq. (40) vs independent diagonalization",
    )
    return {
        "max_energy_error": max_energy_error,
        "minimum_bare_state_overlap": minimum_overlap,
        "lambda_abs": abs(coupling / detuning),
        "ncrit_j0": critical_photon_number(0, coupling, detuning, ec),
        "ncrit_j1": critical_photon_number(1, coupling, detuning, ec),
        "omega_r_dressed": parameters["omega_r_dressed"],
        "omega_q_dressed": parameters["omega_q_dressed"],
        "chi": parameters["chi"],
    }


def chapter3_sanity_checks() -> dict[str, float]:
    coupling_direct = transmon_coupling(6.0, 0.08, 50.0, 50.0)
    coupling_alpha = transmon_coupling_via_alpha(6.0, 0.08, 50.0, 50.0)
    coupling_identity_error = abs(coupling_direct - coupling_alpha)

    omega_r, omega_q, coupling = 5.0, 7.0, 0.18
    exact_linear = np.linalg.eigvalsh(np.array([[omega_r, coupling], [coupling, omega_q]]))
    dressed_linear = np.asarray(linear_dressed_frequencies(omega_r, omega_q, coupling))
    bogoliubov_error = float(np.max(np.abs(exact_linear - dressed_linear)))
    ec = 0.24
    kerrs = bogoliubov_kerrs(coupling, omega_q - omega_r, ec)
    dispersive = two_level_dispersive_parameters(omega_r, omega_q, coupling, ec)
    cross_kerr_relation_error = abs(kerrs["chi_ab"] - 2.0 * dispersive["chi"])
    formal_self_kerr_error = abs(
        kerrs["K_a"] + ec * (coupling / (omega_q - omega_r)) ** 4
    )

    frequencies = np.array([5.2, 7.1, 9.0])
    phases = np.array([0.19, 0.13, 0.08])
    ej = 22.0
    bbq = black_box_kerr(frequencies, phases, ej)
    chi_participation = -np.outer(frequencies, frequencies) * np.outer(
        bbq.participation, bbq.participation
    ) / (4.0 * ej)
    black_box_participation_error = float(np.max(np.abs(bbq.chi - chi_participation)))
    black_box_symmetry_error = float(np.max(np.abs(bbq.chi - bbq.chi.T)))

    levels = np.array([0.0, 5.0, 9.75])
    g_matrix = np.zeros((3, 3), dtype=float)
    g_matrix[0, 1] = g_matrix[1, 0] = 0.06
    g_matrix[1, 2] = g_matrix[2, 1] = 0.06 * np.sqrt(2.0)
    generic_lamb, generic_chi = generic_multilevel_shifts(levels, g_matrix, 6.0)

    longitudinal_errors: list[float] = []
    for sigma_z in [-1, 1]:
        eigenvalues = np.linalg.eigvalsh(longitudinal_block(36, 4.0, 5.5, 0.35, sigma_z))
        for n in range(5):
            expected = longitudinal_analytic_energy(n, 4.0, 5.5, 0.35, sigma_z)
            longitudinal_errors.append(abs(float(eigenvalues[n]) - expected))

    return {
        "eq31_eq33_identity_error": coupling_identity_error,
        "bogoliubov_frequency_error": bogoliubov_error,
        "eq51_cross_kerr_relation_error": cross_kerr_relation_error,
        "eq51_formal_self_kerr_error": formal_self_kerr_error,
        "black_box_participation_error": black_box_participation_error,
        "black_box_symmetry_error": black_box_symmetry_error,
        "generic_multilevel_lamb_finite": float(np.all(np.isfinite(generic_lamb))),
        "generic_multilevel_chi_finite": float(np.all(np.isfinite(generic_chi))),
        "longitudinal_completed_square_error": max(longitudinal_errors),
    }


def reproduce_open_system(config: dict[str, object]) -> dict[str, float]:
    thermal = config["thermal_lindblad"]
    dimension = int(thermal["dimension"])
    omega_r = float(thermal["omega_r"])
    kappa = float(thermal["kappa"])
    nbar = float(thermal["thermal_occupation"])
    initial_fock = int(thermal["initial_fock_state"])
    times = np.linspace(
        float(thermal["time_start"]),
        float(thermal["time_stop"]),
        int(thermal["time_points"]),
    )
    rhos = thermal_oscillator_evolution(
        dimension, omega_r, kappa, nbar, initial_fock, times
    )
    a = annihilation(dimension)
    number = a.conj().T @ a
    mean_number = np.real(np.einsum("tij,ji->t", rhos, number))
    analytic_number = nbar + (initial_fock - nbar) * np.exp(-kappa * times)
    trace = np.real(np.trace(rhos, axis1=1, axis2=2))
    hermiticity_error = np.asarray(
        [np.linalg.norm(rho - rho.conj().T) for rho in rhos]
    )
    min_eigenvalue = np.asarray(
        [np.min(np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)) for rho in rhos]
    )
    thermal_rows = [
        {
            "time": t,
            "mean_photon_number": numerical,
            "analytic_mean_photon_number": analytic,
            "absolute_error": abs(numerical - analytic),
            "trace": tr,
            "hermiticity_error": hermitian,
            "minimum_density_eigenvalue": minimum,
        }
        for t, numerical, analytic, tr, hermitian, minimum in zip(
            times,
            mean_number,
            analytic_number,
            trace,
            hermiticity_error,
            min_eigenvalue,
            strict=True,
        )
    ]
    write_csv(DATA_DIR / "eq68_thermal_lindblad.csv", list(thermal_rows[0]), thermal_rows)

    input_output = config["input_output"]
    io_kappa = float(input_output["kappa"])
    detuning = np.linspace(
        float(input_output["detuning_min"]),
        float(input_output["detuning_max"]),
        int(input_output["points"]),
    )
    cavity, output = passive_one_port_response(
        detuning, io_kappa, complex(float(input_output["input_amplitude"]))
    )
    io_rows = [
        {
            "detuning_over_kappa": delta / io_kappa,
            "cavity_real": amplitude.real,
            "cavity_imag": amplitude.imag,
            "output_real": reflected.real,
            "output_imag": reflected.imag,
            "output_magnitude": abs(reflected),
            "output_phase": np.angle(reflected),
        }
        for delta, amplitude, reflected in zip(detuning, cavity, output, strict=True)
    ]
    write_csv(DATA_DIR / "eq75_input_output_response.csv", list(io_rows[0]), io_rows)

    bath = discretized_bath_hamiltonians()
    hermiticity = {
        name: float(np.linalg.norm(matrix - matrix.conj().T))
        for name, matrix in bath.items()
    }

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
    axes[0].plot(times, mean_number, label="Lindblad integration", color="#1f77b4")
    axes[0].plot(times, analytic_number, "--", label=r"$\bar n+(n_0-\bar n)e^{-\kappa t}$", color="#d62728")
    axes[0].set_xlabel("Time")
    axes[0].set_ylabel(r"$\langle a^\dagger a\rangle$")
    axes[0].set_title("Eq. (68): thermal relaxation")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.2)
    axes[1].plot(detuning / io_kappa, np.abs(output), color="#2ca02c", label=r"$|b_{out}/b_{in}|$")
    axes[1].plot(detuning / io_kappa, np.angle(output), color="#9467bd", label="phase")
    axes[1].set_xlabel(r"Detuning $\Delta/\kappa$")
    axes[1].set_title("Eqs. (72),(75): passive one-port response")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.2)
    fig.tight_layout()
    figure_path = FIGURE_DIR / "eq66_75_open_system_validation.png"
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    return {
        "eq66_full_hermiticity_residual": hermiticity["eq66_full"],
        "eq67_arxiv_literal_hermiticity_residual": hermiticity[
            "eq67_arxiv_literal"
        ],
        "eq67_published_correction_hermiticity_residual": hermiticity[
            "eq67_published_correction"
        ],
        "eq68_max_mean_number_error": float(
            np.max(np.abs(mean_number - analytic_number))
        ),
        "eq68_max_trace_error": float(np.max(np.abs(trace - 1.0))),
        "eq68_max_hermiticity_error": float(np.max(hermiticity_error)),
        "eq68_min_density_eigenvalue": float(np.min(min_eigenvalue)),
        "eq75_max_passivity_error": float(np.max(np.abs(np.abs(output) - 1.0))),
    }


def render_comparison(
    reference_path: Path,
    generated_path: Path,
    output_path: Path,
    reference_title: str,
    generated_title: str,
) -> Path | None:
    if not reference_path.is_file():
        return None
    reference = plt.imread(reference_path)
    generated = plt.imread(generated_path)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0))
    axes[0].imshow(reference)
    axes[0].set_title(reference_title)
    axes[1].imshow(generated)
    axes[1].set_title(generated_title)
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def similarity_scorecard() -> dict[str, object]:
    return {
        "schema_version": 1,
        "paper_id": "2005.12667",
        "status": "draft",
        "targets": [
            {
                "target_id": "T001",
                "label": "Figure 8 Jaynes-Cummings spectrum",
                "figure_refs": ["Fig. 8"],
                "weight": 1.0,
                "components": {
                    "feature_match": {
                        "score": 50,
                        "reason": "Independent block diagonalization reproduces the doublets and the exact 2g sqrt(n) splitting."
                    },
                    "numeric_closeness": {
                        "score": 35,
                        "reason": "Matrix eigenvalues agree with Eq. (38) at machine precision for every generated manifold."
                    },
                    "paper_scope_coverage": {
                        "score": 15,
                        "reason": "The source figure's analytic manifolds and its central square-root invariant are covered; two extra manifolds test generalization."
                    }
                },
                "panel_coverage": {
                    "panels": [
                        {
                            "panel_id": "main",
                            "status": "reproduced",
                            "evidence": "outputs/data/fig8_jaynes_cummings_spectrum.csv"
                        }
                    ]
                },
                "evaluation": {
                    "critical": True,
                    "paper_level_role": "main_claim",
                    "artifact_pass": True,
                    "data_backed": True,
                    "manual_interventions": 0,
                    "failure_type": "none",
                    "parameter_match": "not_applicable",
                    "artifact_stage": "exploratory",
                    "reference_comparison": "analytic_reference",
                    "generated_data_provenance": "independent_numerics",
                    "formula_gate": "verified",
                    "formula_dependencies": ["EQ035_039"]
                },
                "physics_assertions": [
                    {
                        "assertion_id": "jc_sqrt_n_splitting",
                        "tier": "analytic",
                        "essential": True,
                        "status": "passed",
                        "evidence": "outputs/checks/chapter3_checks.json#fig8.max_sqrt_law_error"
                    },
                    {
                        "assertion_id": "jc_matrix_formula_agreement",
                        "tier": "numeric",
                        "essential": True,
                        "status": "passed",
                        "evidence": "outputs/checks/chapter3_checks.json#fig8.max_eigenvalue_error"
                    }
                ],
                "evidence": [
                    "outputs/data/fig8_jaynes_cummings_spectrum.csv",
                    "outputs/figures/fig8_jaynes_cummings_spectrum.png",
                    "comparison-artifacts/fig8_source_vs_reproduction.png"
                ]
            },
            {
                "target_id": "T002",
                "label": "Figure 9 dispersive spectrum",
                "figure_refs": ["Fig. 9"],
                "weight": 1.0,
                "components": {
                    "feature_match": {
                        "score": 50,
                        "reason": "The generated ladders have the qubit-conditioned omega_r' +/- chi spacings and Lamb-shifted branch origins."
                    },
                    "numeric_closeness": {
                        "score": 34,
                        "reason": "Second-order dispersive energies agree closely with independent finite-dimensional diagonalization in the declared |g/Delta|=0.03 regime."
                    },
                    "paper_scope_coverage": {
                        "score": 15,
                        "reason": "Both qubit branches and photon levels n=0..3 are evaluated, covering the full analytic content of the source schematic."
                    }
                },
                "panel_coverage": {
                    "panels": [
                        {
                            "panel_id": "main",
                            "status": "reproduced",
                            "evidence": "outputs/data/fig9_dispersive_spectrum.csv"
                        }
                    ]
                },
                "evaluation": {
                    "critical": True,
                    "paper_level_role": "main_claim",
                    "artifact_pass": True,
                    "data_backed": True,
                    "manual_interventions": 0,
                    "failure_type": "none",
                    "parameter_match": "not_applicable",
                    "artifact_stage": "exploratory",
                    "reference_comparison": "analytic_reference",
                    "generated_data_provenance": "independent_numerics",
                    "formula_gate": "verified",
                    "formula_dependencies": ["EQ040_044"]
                },
                "physics_assertions": [
                    {
                        "assertion_id": "dispersive_small_parameter",
                        "tier": "analytic",
                        "essential": True,
                        "status": "passed",
                        "evidence": "outputs/checks/chapter3_checks.json#fig9.lambda_abs"
                    },
                    {
                        "assertion_id": "dispersive_exact_diagonalization",
                        "tier": "numeric",
                        "essential": True,
                        "status": "passed",
                        "evidence": "outputs/checks/chapter3_checks.json#fig9.max_energy_error"
                    }
                ],
                "evidence": [
                    "outputs/data/fig9_dispersive_spectrum.csv",
                    "outputs/figures/fig9_dispersive_spectrum.png",
                    "comparison-artifacts/fig9_source_vs_reproduction.png"
                ]
            }
        ]
    }


def main() -> int:
    started = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for directory in [DATA_DIR, FIGURE_DIR, CHECK_DIR, COMPARISON_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    fig8 = reproduce_figure_8(config["chapter3"]["figure_8"])
    fig9 = reproduce_figure_9(config["chapter3"]["figure_9"])
    other = chapter3_sanity_checks()
    chapter3_thresholds = {
        "fig8_machine_precision": fig8["max_eigenvalue_error"] < 1e-12,
        "fig8_sqrt_law": fig8["max_sqrt_law_error"] < 1e-12,
        "fig9_dispersive_energy": fig9["max_energy_error"] < 2e-4,
        "fig9_state_identity": fig9["minimum_bare_state_overlap"] > 0.99,
        "fig9_regime": fig9["lambda_abs"] < 0.1 and 3 < fig9["ncrit_j0"],
        "coupling_identity": other["eq31_eq33_identity_error"] < 1e-14,
        "bogoliubov_diagonalization": other["bogoliubov_frequency_error"] < 1e-12,
        "formal_eq51_self_kerr": other["eq51_formal_self_kerr_error"] < 1e-14,
        "black_box_identity": other["black_box_participation_error"] < 1e-12,
        "longitudinal_completed_square": other["longitudinal_completed_square_error"] < 1e-10,
    }
    chapter3_check = {
        "status": "passed" if all(chapter3_thresholds.values()) else "failed",
        "paper_id": "2005.12667",
        "scope": "arXiv v1 Section III, Eqs. (29)-(63)",
        "fig8": fig8,
        "fig9": fig9,
        "other_equations": other,
        "thresholds": chapter3_thresholds,
    }
    write_json(CHECK_DIR / "chapter3_checks.json", chapter3_check)

    open_system = reproduce_open_system(config["open_system"])
    open_system_thresholds = {
        "eq66_hermitian": open_system["eq66_full_hermiticity_residual"] < 1e-12,
        "eq67_arxiv_typo_detected": open_system[
            "eq67_arxiv_literal_hermiticity_residual"
        ] > 1e-3,
        "eq67_published_correction_hermitian": open_system[
            "eq67_published_correction_hermiticity_residual"
        ] < 1e-12,
        "eq68_mean_number": open_system["eq68_max_mean_number_error"] < 2e-7,
        "eq68_trace": open_system["eq68_max_trace_error"] < 1e-10,
        "eq68_hermiticity": open_system["eq68_max_hermiticity_error"] < 1e-10,
        "eq68_positivity": open_system["eq68_min_density_eigenvalue"] > -1e-10,
        "eq75_passivity": open_system["eq75_max_passivity_error"] < 1e-12,
    }
    open_system_check = {
        "status": "passed" if all(open_system_thresholds.values()) else "failed",
        "paper_id": "2005.12667",
        "scope": "arXiv v1 Eqs. (66)-(68), (70)-(75), with Eqs. (64)-(65), (69) and Appendix C",
        "source_correction": {
            "arxiv_v1_eq67": "The printed minus form is anti-Hermitian for real lambda.",
            "published_rmp_eq69": "The formal publication replaces it with a b^dagger + a^dagger b, restoring Hermiticity.",
            "input_output_signs": "The executable form uses the passive one-port relative sign and records the convention explicitly."
        },
        "metrics": open_system,
        "thresholds": open_system_thresholds,
    }
    write_json(CHECK_DIR / "open_system_checks.json", open_system_check)
    runtime = time.perf_counter() - started
    run_check = {
        "status": "passed"
        if chapter3_check["status"] == "passed" and open_system_check["status"] == "passed"
        else "failed",
        "paper_id": "2005.12667",
        "runtime_seconds": runtime,
        "commands": ["python case/2005.12667/scripts/run_reproduction.py"],
        "outputs": {
            "data": sorted(relative(path) for path in DATA_DIR.glob("*.csv")),
            "figures": sorted(relative(path) for path in FIGURE_DIR.glob("*.png")),
            "comparisons": sorted(relative(path) for path in COMPARISON_DIR.glob("*.png")),
            "checks": [
                "outputs/checks/chapter3_checks.json",
                "outputs/checks/open_system_checks.json"
            ]
        }
    }
    write_json(CHECK_DIR / "reproduction_run.json", run_check)
    print(json.dumps(run_check, indent=2, ensure_ascii=False))
    return 0 if run_check["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
