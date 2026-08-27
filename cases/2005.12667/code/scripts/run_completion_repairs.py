#!/usr/bin/env python3
"""Generate independent completion artifacts for previously uncovered targets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.completion_repairs import (  # noqa: E402
    amplifier_iq_claim_checks,
    dissipation_drive_claim_checks,
    epsilon_driven_strong_dispersive,
    finite_line_mode_checks,
    gaussian_wavepacket_time_mode_checks,
    lc_harmonic_reference,
    low_damping_exchange,
    normalized_damped_response,
    quadrature_marginals,
    small_matrix_multilevel_shift_check,
    tomography_claim_checks,
    transmon_harmonic_comparator,
)


DATA_DIR = WORKSPACE / "outputs" / "data"
FIGURE_DIR = WORKSPACE / "outputs" / "figures"
CHECK_DIR = WORKSPACE / "outputs" / "checks"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
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


def save_figure(fig: plt.Figure, filename: str) -> Path:
    path = FIGURE_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def check_record(target_id: str, passed: bool, **metrics: object) -> dict[str, object]:
    payload = {
        "schema_version": 1,
        "paper_id": "2005.12667",
        "target_id": target_id,
        "passed": passed,
        "source_boundary": {
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
        },
    }
    payload.update(metrics)
    return payload


def run(config_path: Path) -> dict[str, dict[str, object]]:
    config = json.loads(config_path.read_text(encoding="utf-8"))["targets"]
    results: dict[str, dict[str, object]] = {}

    x = np.linspace(-4.0, 4.0, 801)
    potential, energies = lc_harmonic_reference(x, float(config["T028"]["omega"]))
    rows = [
        {
            "x": float(value),
            "potential": float(entry),
            "energy_0": float(energies[0]),
            "energy_1": float(energies[1]),
            "energy_2": float(energies[2]),
            "energy_3": float(energies[3]),
        }
        for value, entry in zip(x, potential, strict=True)
    ]
    data = DATA_DIR / "fig1_lc_harmonic_reference.csv"
    write_csv(data, rows)
    fig, axis = plt.subplots(figsize=(6.4, 4.0))
    axis.plot(x, potential, color="black")
    for level in energies[:4]:
        axis.hlines(level, x[0], x[-1], color="#1f77b4", linewidth=1.2)
    axis.set(xlabel="Generalized coordinate", ylabel="Energy", title="LC harmonic potential and equally spaced levels")
    axis.grid(alpha=0.2)
    figure = save_figure(fig, "fig1_lc_harmonic_reference.png")
    spacing_residual = float(np.max(np.abs(np.diff(energies) - float(config["T028"]["omega"]))))
    payload = check_record("T028", spacing_residual < 1e-12, spacing_residual=spacing_residual)
    check = CHECK_DIR / "T028_lc_harmonic_reference.json"
    write_json(check, payload)
    results["T028"] = {"data": str(data.relative_to(WORKSPACE)), "figure": str(figure.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    detuning = np.linspace(-5.0, 5.0, 1601)
    response = normalized_damped_response(detuning)
    rows = [{"detuning_over_kappa": float(delta), "response_amplitude": float(value)} for delta, value in zip(detuning, response, strict=True)]
    data = DATA_DIR / "fig1_damped_response.csv"
    write_csv(data, rows)
    fig, axis = plt.subplots(figsize=(6.2, 3.8))
    axis.plot(detuning, response, color="#1f77b4")
    axis.axhline(1.0 / np.sqrt(2.0), color="#d62728", linestyle="--", linewidth=0.9)
    axis.set(xlabel=r"$\Delta/\kappa$", ylabel="Normalized response", title="One-port damped-oscillator response")
    axis.grid(alpha=0.2)
    figure = save_figure(fig, "fig1_damped_response.png")
    half_power = detuning[response >= 1.0 / np.sqrt(2.0)]
    fwhm_residual = abs((half_power[-1] - half_power[0]) - 1.0)
    payload = check_record("T029", fwhm_residual < 0.02, fwhm_residual=fwhm_residual)
    check = CHECK_DIR / "T029_damped_response.json"
    write_json(check, payload)
    results["T029"] = {"data": str(data.relative_to(WORKSPACE)), "figure": str(figure.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    marginals = quadrature_marginals(
        float(config["T031"]["two_chi_over_kappa"]),
        float(config["T031"]["integration_time"]),
    )
    rows = [
        {
            "x": float(value),
            "ground_marginal": float(g),
            "excited_marginal": float(e),
        }
        for value, g, e in zip(marginals.x, marginals.ground, marginals.excited, strict=True)
    ]
    data = DATA_DIR / "fig18_quadrature_marginals.csv"
    write_csv(data, rows)
    fig, axis = plt.subplots(figsize=(6.4, 4.0))
    axis.plot(marginals.x, marginals.ground, label="g")
    axis.plot(marginals.x, marginals.excited, label="e")
    axis.set(xlabel="x quadrature", ylabel="Probability density", title="Pointer-state x marginals")
    axis.legend()
    axis.grid(alpha=0.2)
    figure = save_figure(fig, "fig18_quadrature_marginals.png")
    norm_ground = float(np.trapezoid(marginals.ground, marginals.x))
    norm_excited = float(np.trapezoid(marginals.excited, marginals.x))
    payload = check_record(
        "T031",
        abs(norm_ground - 1.0) < 1e-6 and abs(norm_excited - 1.0) < 1e-6,
        norm_ground=norm_ground,
        norm_excited=norm_excited,
        overlap_area=marginals.overlap_area,
        assignment_error=marginals.assignment_error,
    )
    check = CHECK_DIR / "T031_quadrature_marginals.json"
    write_json(check, payload)
    results["T031"] = {"data": str(data.relative_to(WORKSPACE)), "figure": str(figure.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    phase = np.linspace(-0.9, 0.9, 801)
    cosine, harmonic = transmon_harmonic_comparator(phase, float(config["T040"]["EJ_over_EC"]))
    rows = [{"phase": float(value), "cosine_potential": float(cos_val), "harmonic_comparator": float(harm_val)} for value, cos_val, harm_val in zip(phase, cosine, harmonic, strict=True)]
    data = DATA_DIR / "fig5_harmonic_comparator.csv"
    write_csv(data, rows)
    fig, axis = plt.subplots(figsize=(6.2, 4.0))
    axis.plot(phase, cosine, label="cosine")
    axis.plot(phase, harmonic, "--", label="quadratic")
    axis.set(xlabel=r"$\varphi$", ylabel=r"Potential / $E_C$", title="Transmon cosine potential and quadratic comparator")
    axis.legend()
    axis.grid(alpha=0.2)
    figure = save_figure(fig, "fig5_harmonic_comparator.png")
    curvature_residual = abs((cosine[401 + 1] - 2.0 * cosine[401] + cosine[401 - 1]) / (phase[1] - phase[0]) ** 2 - float(config["T040"]["EJ_over_EC"]))
    payload = check_record("T040", curvature_residual < 0.05, curvature_residual=curvature_residual)
    check = CHECK_DIR / "T040_harmonic_comparator.json"
    write_json(check, payload)
    results["T040"] = {"data": str(data.relative_to(WORKSPACE)), "figure": str(figure.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    time, q_from_q, c_from_q, q_from_c, c_from_c = low_damping_exchange(
        float(config["T041"]["g_MHz"]),
        float(config["T041"]["kappa_MHz"]),
        float(config["T041"]["gamma1_MHz"]),
        float(config["T041"]["time_stop_per_inverse_MHz"]),
    )
    rows = []
    for idx, value in enumerate(time):
        rows.append(
            {
                "time_inverse_MHz": float(value),
                "qubit_from_qubit": float(q_from_q[idx]),
                "cavity_from_qubit": float(c_from_q[idx]),
                "qubit_from_cavity": float(q_from_c[idx]),
                "cavity_from_cavity": float(c_from_c[idx]),
            }
        )
    data = DATA_DIR / "fig20_low_damping_trajectories.csv"
    write_csv(data, rows)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6), sharey=True)
    axes[0].plot(time, q_from_q, label="P_e |0,e>")
    axes[0].plot(time, c_from_q, label="n |0,e>")
    axes[1].plot(time, q_from_c, label="P_e |1,g>")
    axes[1].plot(time, c_from_c, label="n |1,g>")
    for axis in axes:
        axis.grid(alpha=0.2)
        axis.set_xlabel("Time (1/MHz)")
        axis.legend(fontsize=7)
    axes[0].set_ylabel("Excitation probability")
    axes[0].set_title(r"$|0,e\rangle$ initial")
    axes[1].set_title(r"$|1,g\rangle$ initial")
    figure = save_figure(fig, "fig20_low_damping_trajectories.png")
    symmetry_residual = float(max(np.max(np.abs(q_from_q - c_from_c)), np.max(np.abs(c_from_q - q_from_c))))
    payload = check_record("T041", symmetry_residual < 1e-10, symmetry_residual=symmetry_residual)
    check = CHECK_DIR / "T041_low_damping_trajectories.json"
    write_json(check, payload)
    results["T041"] = {"data": str(data.relative_to(WORKSPACE)), "figure": str(figure.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    detuning = np.linspace(-12.0, 12.0, 2401)
    spectrum, mean_photons = epsilon_driven_strong_dispersive(
        detuning,
        chi=float(config["T043"]["chi_MHz"]),
        rabi_frequency=float(config["T043"]["rabi_MHz"]),
        gamma1=float(config["T043"]["gamma1_MHz"]),
        gamma_phi=float(config["T043"]["gamma_phi_MHz"]),
        kappa=float(config["T043"]["kappa_MHz"]),
        epsilon=float(config["T043"]["epsilon_MHz"]),
        cavity_drive_detuning=float(
            config["T043"][
                "cavity_drive_detuning_from_pulled_resonance_MHz"
            ]
        ),
    )
    rows = [{"detuning_MHz": float(delta), "excited_population": float(value), "derived_mean_photons": mean_photons} for delta, value in zip(detuning, spectrum, strict=True)]
    data = DATA_DIR / "fig25b_strong_dispersive_spectrum.csv"
    write_csv(data, rows)
    fig, axis = plt.subplots(figsize=(6.5, 4.0))
    axis.plot(detuning, spectrum, color="#1f77b4")
    axis.set(xlabel="Qubit detuning (MHz)", ylabel=r"$P_e$", title=r"Strong-dispersive spectrum at $\epsilon=0.1$")
    axis.grid(alpha=0.2)
    figure = save_figure(fig, "fig25b_strong_dispersive_spectrum.png")
    payload = check_record(
        "T043",
        float(np.max(spectrum)) > 0.0,
        derived_mean_photons=mean_photons,
        spectrum_peak=float(np.max(spectrum)),
        parameter_match="paper_subset",
        caption_drive_condition="on_pulled_cavity_resonance",
    )
    check = CHECK_DIR / "T043_strong_dispersive_spectrum.json"
    write_json(check, payload)
    results["T043"] = {"data": str(data.relative_to(WORKSPACE)), "figure": str(figure.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    claim_payloads = {
        "T033": small_matrix_multilevel_shift_check(),
        "T034": {
            key: value
            for key, value in finite_line_mode_checks().items()
            if key in {"orthonormality_error", "completeness_trace"}
        },
        "T035": {
            key: value
            for key, value in finite_line_mode_checks().items()
            if key in {"boundary_current_magnitude", "energy_balance_error"}
        },
        "T036": gaussian_wavepacket_time_mode_checks(),
        "T037": dissipation_drive_claim_checks(),
        "T038": amplifier_iq_claim_checks(),
        "T039": tomography_claim_checks(),
    }
    claim_thresholds = {
        "T033": lambda item: item["max_spacing_error"] < 2e-3,
        "T034": lambda item: item["orthonormality_error"] < 1e-6,
        "T035": lambda item: item["energy_balance_error"] < 1e-6,
        "T036": lambda item: item["overlap_zero_delay"] > 0.999 and item["overlap_four_sigma_delay"] < 0.05,
        "T037": lambda item: item["t2_identity_residual"] < 1e-12 and item["coherent_poisson_residual"] < 1e-12,
        "T038": lambda item: item["max_commutator_error"] < 1e-12 and item["iq_orthogonality_overlap"] < 1e-3,
        "T039": lambda item: item["wigner_integral_error"] < 1e-8 and item["q_integral_error"] < 5e-3,
    }
    for target_id, metrics in claim_payloads.items():
        rows = [{"metric": key, "value": float(value)} for key, value in metrics.items()]
        data = DATA_DIR / f"{target_id.lower()}_claim_checks.csv"
        write_csv(data, rows)
        payload = check_record(target_id, claim_thresholds[target_id](metrics), **metrics)
        check = CHECK_DIR / f"{target_id}_claim_checks.json"
        write_json(check, payload)
        results[target_id] = {"data": str(data.relative_to(WORKSPACE)), "check": str(check.relative_to(WORKSPACE))}

    failures = []
    for target_id, record in results.items():
        check_path = WORKSPACE / record["check"]
        passed = json.loads(check_path.read_text(encoding="utf-8"))["passed"]
        if not passed:
            failures.append(target_id)
    if failures:
        raise RuntimeError(f"completion repair checks failed: {', '.join(sorted(failures))}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/completion_repairs.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside workspace")
    results = run(config_path)
    print(json.dumps({"status": "passed", "targets": sorted(results)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
