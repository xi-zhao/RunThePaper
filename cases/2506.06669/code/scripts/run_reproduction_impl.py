#!/usr/bin/env python3
"""Generate all public-theory datasets for arXiv:2506.06669.

This entrypoint deliberately performs no plotting.  It is intended to run in
the harness's raw/reference-free isolated numerical channel and freezes one
NPZ plus one scientific check per target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.state_transfer import (  # noqa: E402
    endpoint_target,
    even_site_population,
    expected_zigzag_spectrum,
    four_corner_target,
    fst_hamiltonian,
    fst_hamiltonian_2d,
    lindblad_trajectory,
    mhz_to_angular,
    population_scan,
    pulsed_lindblad_final,
    reduced_endpoint_density,
    reduced_selected_density,
    sample_parameter_noise,
    state_fidelity,
    three_site_populations,
    unitary_amplitudes,
    zigzag_hamiltonian,
    zigzag_parameters,
)


TARGET_IDS = [f"T{index:03d}" for index in range(1, 11)]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def target_check(
    check_dir: Path,
    target_id: str,
    *,
    status: str,
    formula_dependencies: list[str],
    parameter_match: str,
    elapsed_seconds: float,
    checks: dict[str, Any],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "target_id": target_id,
        "status": status,
        "formula_gate": "verified" if all(item != "QS009" for item in formula_dependencies) else "reconstructed",
        "formula_dependencies": formula_dependencies,
        "parameter_match": parameter_match,
        "generated_data_provenance": "independent_numerics",
        "elapsed_seconds": round(elapsed_seconds, 6),
        "checks": checks,
        "notes": notes or [],
    }
    write_json(check_dir / f"{target_id}_science.json", payload)
    return payload


def run_eigensystem(parameters: dict[str, Any], data_dir: Path, check_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    j_scale = float(mhz_to_angular(parameters["j_fst_mhz"]))
    payload: dict[str, Any] = {}
    spectrum_errors: dict[str, float] = {}
    printed_zero_level_discrepancy: dict[str, float] = {}
    mirror_errors: dict[str, float] = {}
    low_sector_even_weight: dict[str, float] = {}
    eigenpair_residuals: dict[str, float] = {}
    for m in parameters["fig1_m_values"]:
        hamiltonian = zigzag_hamiltonian(parameters["n_1d"], m, j_scale)
        eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
        for column in range(eigenvectors.shape[1]):
            pivot = int(np.argmax(np.abs(eigenvectors[:, column])))
            if eigenvectors[pivot, column] < 0.0:
                eigenvectors[:, column] *= -1.0
        weights = np.abs(eigenvectors) ** 2
        key = f"m{m}"
        payload[f"eigenvalues_{key}"] = eigenvalues / j_scale
        payload[f"eigenvectors_{key}"] = eigenvectors
        payload[f"eigenvector_weights_{key}"] = weights
        spectrum_errors[key] = float(
            np.max(
                np.abs(
                    eigenvalues
                    - expected_zigzag_spectrum(parameters["n_1d"], m, j_scale)
                )
            )
            / j_scale
        )
        printed_zero_level_discrepancy[key] = float(abs(eigenvalues[(parameters["n_1d"] - 1) // 2] / j_scale))
        mirror_errors[key] = float(np.max(np.abs(hamiltonian - np.flip(hamiltonian))))
        eigenpair_residuals[key] = float(
            np.max(np.abs(hamiltonian @ eigenvectors - eigenvectors * eigenvalues)) / j_scale
        )
        low_modes = eigenvalues <= 1.0e-12
        low_sector_even_weight[key] = float(np.mean(np.sum(weights[1::2, :][:, low_modes], axis=0)))
    save_npz(data_dir / "fig1cd.npz", **payload)
    passed = (
        max(spectrum_errors.values()) < 1.0e-10
        and max(mirror_errors.values()) < 1.0e-12
        and max(eigenpair_residuals.values()) < 1.0e-10
    )
    return target_check(
        check_dir,
        "T001",
        status="passed" if passed else "failed",
        formula_dependencies=["QS001", "QS002"],
        parameter_match="unknown",
        elapsed_seconds=time.perf_counter() - started,
        checks={
            "spectrum_max_error_in_J_units": spectrum_errors,
            "printed_zero_level_discrepancy_in_J_units": printed_zero_level_discrepancy,
            "mirror_symmetry_max_error": mirror_errors,
            "eigenpair_residual_max_in_J_units": eigenpair_residuals,
            "low_sector_even_site_weight": low_sector_even_weight,
        },
        notes=[
            "Fig. 1 says only m>0; m=4 is a declared representative, not paper-exact.",
            "Main Eq. (8) has a parity inconsistency: using high onsite energy on even sites, as required by Fig. 1, the printed spectrum, and the Supplement's elimination, restores the fixed zero level."
        ],
    )


def run_three_site(parameters: dict[str, Any], data_dir: Path, check_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    solution = parameters["fig2_solution"]
    delta_mhz = np.linspace(solution["delta_mhz_min"], solution["delta_mhz_max"], solution["delta_points"])
    coupling_mhz = np.linspace(
        solution["coupling_mhz_min"],
        solution["coupling_mhz_max"],
        solution["coupling_points"],
    )
    delta_grid = mhz_to_angular(delta_mhz)[None, :]
    coupling_grid = mhz_to_angular(coupling_mhz)[:, None]
    p1, p2, p3 = three_site_populations(delta_grid, coupling_grid, solution["time_ns"])

    fine = parameters["fig2_fine"]
    offsets_mhz = np.linspace(fine["offset_mhz_min"], fine["offset_mhz_max"], fine["offset_points"])
    offsets = mhz_to_angular(offsets_mhz)
    fine_times = np.linspace(fine["time_ns_min"], fine["time_ns_max"], fine["time_points"])
    j_scale = float(mhz_to_angular(parameters["j_pst_mhz"]))
    payload: dict[str, Any] = {
        "delta_mhz": delta_mhz,
        "coupling_mhz": coupling_mhz,
        "solution_p1": p1,
        "solution_p2": p2,
        "solution_p3": p3,
        "offset_mhz": offsets_mhz,
        "fine_time_ns": fine_times,
    }
    transfer_errors: dict[str, float] = {}
    for m in fine["m_values"]:
        onsite, couplings = zigzag_parameters(3, m, j_scale)
        payload[f"q2_scan_m{m}"] = population_scan(onsite, couplings, 1, offsets, fine_times)
        payload[f"q1_scan_m{m}"] = population_scan(onsite, couplings, 0, offsets, fine_times)
        final = unitary_amplitudes(zigzag_hamiltonian(3, m, j_scale), [np.pi / j_scale])[0]
        transfer_errors[f"m{m}"] = float(abs(abs(final[-1]) ** 2 - 1.0))

    test_delta = float(mhz_to_angular(10.0))
    test_coupling = float(mhz_to_angular(6.0))
    test_time = 60.0
    analytic = three_site_populations(test_delta, test_coupling, test_time)[2]
    direct_hamiltonian = np.array(
        [[0.0, test_coupling, 0.0], [test_coupling, test_delta, test_coupling], [0.0, test_coupling, 0.0]]
    )
    direct = abs(unitary_amplitudes(direct_hamiltonian, [test_time])[0, -1]) ** 2
    analytic_direct_error = float(abs(analytic - direct))
    normalization_error = float(np.max(np.abs(p1 + p2 + p3 - 1.0)))
    save_npz(data_dir / "fig2_3site.npz", **payload)
    passed = normalization_error < 1.0e-12 and analytic_direct_error < 1.0e-12 and max(transfer_errors.values()) < 1.0e-12
    return target_check(
        check_dir,
        "T002",
        status="passed" if passed else "failed",
        formula_dependencies=["QS001", "QS002", "QS003"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - started,
        checks={
            "population_normalization_max_error": normalization_error,
            "analytic_vs_direct_exponentiation_error": analytic_direct_error,
            "published_solution_transfer_errors": transfer_errors,
        },
        notes=["The direct Delta/J lane is exact; the source does not publish the coupler-frequency transfer function used by Fig. S2."],
    )


def run_five_site_pst(parameters: dict[str, Any], data_dir: Path, check_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    section = parameters["fig2_pst"]
    times = np.linspace(section["time_ns_min"], section["time_ns_max"], section["time_points"])
    j_scale = float(mhz_to_angular(parameters["j_pst_mhz"]))
    payload: dict[str, Any] = {"time_ns": times}
    transfer_errors: dict[str, float] = {}
    even_means: dict[str, float] = {}
    for m in section["m_values"]:
        hamiltonian = zigzag_hamiltonian(parameters["n_1d"], m, j_scale)
        amplitudes = unitary_amplitudes(hamiltonian, times)
        payload[f"populations_m{m}"] = np.abs(amplitudes) ** 2
        exact = unitary_amplitudes(hamiltonian, [np.pi / j_scale])[0]
        transfer_errors[f"m{m}"] = float(abs(abs(exact[-1]) ** 2 - 1.0))
        even_means[f"m{m}"] = float(np.mean(even_site_population(amplitudes)))
    save_npz(data_dir / "fig2_5site.npz", **payload)
    suppression = even_means[f"m{section['m_values'][-1]}"] < even_means[f"m{section['m_values'][0]}"]
    passed = max(transfer_errors.values()) < 1.0e-12 and suppression
    return target_check(
        check_dir,
        "T003",
        status="passed" if passed else "failed",
        formula_dependencies=["QS001", "QS002", "QS008"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - started,
        checks={
            "perfect_transfer_errors": transfer_errors,
            "mean_even_site_population": even_means,
            "large_m_suppression_passed": bool(suppression),
        },
        notes=["Theory-only unitary maps use the printed m values and 300 ns axis; hardware decoherence is not fabricated."],
    )


def run_one_dimensional_fst(
    parameters: dict[str, Any],
    data_dir: Path,
    check_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    section = parameters["fig3_dynamics"]
    times = np.linspace(section["time_ns_min"], section["time_ns_max"], section["time_points"])
    j_scale = float(mhz_to_angular(parameters["j_fst_mhz"]))
    theta = parameters["theta"]
    tau = np.pi / j_scale
    trajectory_payload: dict[str, Any] = {"time_ns": times}
    density_payload: dict[str, Any] = {}
    trace_errors: dict[str, float] = {}
    fidelities: dict[str, float] = {}
    even_means: dict[str, float] = {}
    target = endpoint_target(parameters["n_1d"])
    ideal_density = reduced_endpoint_density(np.outer(target, target.conj()), parameters["n_1d"])
    density_payload["ideal_bell_density"] = ideal_density
    for m in section["m_values"]:
        hamiltonian = fst_hamiltonian(parameters["n_1d"], m, j_scale, theta)
        trajectory = lindblad_trajectory(
            hamiltonian,
            times,
            t1_ns=parameters["t1_ns"],
            t2_ns=parameters["t2_1d_ns"],
        )
        populations = np.real(np.diagonal(trajectory, axis1=1, axis2=2))[:, 1:]
        trajectory_payload[f"populations_m{m}"] = populations
        even_means[f"m{m}"] = float(np.mean(np.sum(populations[:, 1::2], axis=1)))
        at_tau = lindblad_trajectory(
            hamiltonian,
            [0.0, tau],
            t1_ns=parameters["t1_ns"],
            t2_ns=parameters["t2_1d_ns"],
        )[-1]
        reduced = reduced_endpoint_density(at_tau, parameters["n_1d"])
        density_payload[f"reduced_density_m{m}"] = reduced
        fidelities[f"m{m}"] = state_fidelity(at_tau, target)
        trace_errors[f"m{m}"] = float(abs(np.trace(at_tau) - 1.0))
    save_npz(data_dir / "fig3ab.npz", **trajectory_payload)
    save_npz(data_dir / "fig3cd.npz", **density_payload)
    elapsed = time.perf_counter() - started
    suppression = even_means[f"m{section['m_values'][-1]}"] < even_means[f"m{section['m_values'][0]}"]
    common_checks = {
        "trace_errors": trace_errors,
        "bell_fidelities": fidelities,
        "mean_even_site_population": even_means,
        "m4_even_site_suppression_passed": bool(suppression),
    }
    t004 = target_check(
        check_dir,
        "T004",
        status="passed" if max(trace_errors.values()) < 1.0e-10 and suppression else "failed",
        formula_dependencies=["QS001", "QS002", "QS004", "QS006"],
        parameter_match="paper_subset",
        elapsed_seconds=elapsed,
        checks=common_checks,
        notes=["Only master-equation lines are generated; experimental markers are absent by design."],
    )
    positivity = {
        key: float(np.min(np.linalg.eigvalsh(value)))
        for key, value in density_payload.items()
        if key.startswith("reduced_density")
    }
    t005 = target_check(
        check_dir,
        "T005",
        status="passed" if min(positivity.values()) > -1.0e-10 and min(fidelities.values()) > 0.85 else "failed",
        formula_dependencies=["QS004", "QS006"],
        parameter_match="paper_subset",
        elapsed_seconds=elapsed,
        checks={"reduced_density_min_eigenvalues": positivity, "bell_fidelities": fidelities},
        notes=["The printed FST deformation gives the Bell-plus gauge; the named singlet differs by a local endpoint Z phase."],
    )
    return t004, t005


def noise_payload(
    parameters: dict[str, Any],
    *,
    transfer_kind: str,
    coupling_sigma_mhz: list[float],
    samples: int,
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    noise = parameters["noise"]
    frequency_sigma_mhz = np.asarray(noise["frequency_sigma_mhz"], dtype=float)
    coupling_sigma_mhz_array = np.asarray(coupling_sigma_mhz, dtype=float)
    m_values = np.asarray(noise["m_values"], dtype=int)
    rng = np.random.default_rng(seed)
    j_scale = float(mhz_to_angular(parameters["j_pst_mhz"] if transfer_kind == "pst" else parameters["j_fst_mhz"]))
    theta = parameters["theta"]

    raw_even = np.empty((len(m_values), len(frequency_sigma_mhz), samples), dtype=float)
    raw_odd = np.empty_like(raw_even)
    raw_coupling = np.empty((len(m_values), len(coupling_sigma_mhz_array), samples), dtype=float)
    for m_index, m in enumerate(m_values):
        for sigma_index, sigma in enumerate(mhz_to_angular(frequency_sigma_mhz)):
            raw_even[m_index, sigma_index] = sample_parameter_noise(
                n_sites=parameters["n_1d"], m=int(m), j_scale=j_scale,
                transfer_kind=transfer_kind, noise_kind="even_frequency",
                sigma=float(sigma), samples=samples, rng=rng, theta=theta,
            )
            raw_odd[m_index, sigma_index] = sample_parameter_noise(
                n_sites=parameters["n_1d"], m=int(m), j_scale=j_scale,
                transfer_kind=transfer_kind, noise_kind="odd_frequency",
                sigma=float(sigma), samples=samples, rng=rng, theta=theta,
            )
        for sigma_index, sigma in enumerate(mhz_to_angular(coupling_sigma_mhz_array)):
            raw_coupling[m_index, sigma_index] = sample_parameter_noise(
                n_sites=parameters["n_1d"], m=int(m), j_scale=j_scale,
                transfer_kind=transfer_kind, noise_kind="coupling",
                sigma=float(sigma), samples=samples, rng=rng, theta=theta,
            )

    payload = {
        "m_values": m_values,
        "frequency_sigma_mhz": frequency_sigma_mhz,
        "coupling_sigma_mhz": coupling_sigma_mhz_array,
        "even_samples": raw_even,
        "odd_samples": raw_odd,
        "coupling_samples": raw_coupling,
        "even_mean": np.mean(raw_even, axis=2),
        "even_std": np.std(raw_even, axis=2),
        "odd_mean": np.mean(raw_odd, axis=2),
        "odd_std": np.std(raw_odd, axis=2),
        "coupling_mean": np.mean(raw_coupling, axis=2),
        "coupling_std": np.std(raw_coupling, axis=2),
    }
    zero_error = float(
        max(
            np.max(np.abs(payload["even_mean"][:, 0] - 1.0)),
            np.max(np.abs(payload["odd_mean"][:, 0] - 1.0)),
            np.max(np.abs(payload["coupling_mean"][:, 0] - 1.0)),
        )
    )
    trend_checks = {
        "zero_noise_normalization_error": zero_error,
        "large_m_even_noise_advantage": bool(payload["even_mean"][-1, -1] > payload["even_mean"][0, -1]),
        "large_m_coupling_noise_advantage": bool(payload["coupling_mean"][-1, -1] > payload["coupling_mean"][0, -1]),
        "samples_per_point": samples,
        "seed": seed,
    }
    return payload, trend_checks


def run_noise_targets(parameters: dict[str, Any], data_dir: Path, check_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    noise = parameters["noise"]
    seed = int(parameters["random_seed"])
    fst_payload, fst_checks = noise_payload(
        parameters,
        transfer_kind="fst",
        coupling_sigma_mhz=noise["fst_coupling_sigma_mhz"],
        samples=int(noise["fst_samples"]),
        seed=seed,
    )
    save_npz(data_dir / "figS8.npz", **fst_payload)
    t006 = target_check(
        check_dir,
        "T006",
        status="passed" if fst_checks["zero_noise_normalization_error"] < 1.0e-12 and fst_checks["large_m_even_noise_advantage"] and fst_checks["large_m_coupling_noise_advantage"] else "failed",
        formula_dependencies=["QS004", "QS007"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - started,
        checks=fst_checks,
        notes=["Paper sample count is preserved; exact scan array and seed are unreported and replaced declaratively."],
    )

    pst_started = time.perf_counter()
    pst_payload, pst_checks = noise_payload(
        parameters,
        transfer_kind="pst",
        coupling_sigma_mhz=noise["pst_coupling_sigma_mhz"],
        samples=int(noise["pst_samples"]),
        seed=seed + 1,
    )
    save_npz(data_dir / "figS7.npz", **pst_payload)
    t008 = target_check(
        check_dir,
        "T008",
        status="passed" if pst_checks["zero_noise_normalization_error"] < 1.0e-12 and pst_checks["large_m_even_noise_advantage"] and pst_checks["large_m_coupling_noise_advantage"] else "failed",
        formula_dependencies=["QS002", "QS007"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - pst_started,
        checks=pst_checks,
        notes=["Paper sample count is preserved; exact scan array and seed are unreported and replaced declaratively."],
    )
    return t006, t008


def run_main_2d(parameters: dict[str, Any], data_dir: Path, check_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    section = parameters["fig4_dynamics"]
    times = np.linspace(section["time_ns_min"], section["time_ns_max"], section["time_points"])
    j_scale = float(mhz_to_angular(parameters["j_fst_mhz"]))
    hamiltonian = fst_hamiltonian_2d(
        parameters["rows_2d"], parameters["columns_2d"], section["m"], j_scale, parameters["theta"]
    )
    trajectory = lindblad_trajectory(
        hamiltonian,
        times,
        t1_ns=parameters["t1_ns"],
        tphi_ns=parameters["tphi_2d_ns"],
    )
    populations = np.real(np.diagonal(trajectory, axis1=1, axis2=2))[:, 1:]
    selected_times = np.asarray([0.0, 56.0, 111.0])
    selected_indices = np.asarray([int(np.argmin(abs(times - value))) for value in selected_times])
    tau = np.pi / j_scale
    at_tau = lindblad_trajectory(
        hamiltonian,
        [0.0, tau],
        t1_ns=parameters["t1_ns"],
        tphi_ns=parameters["tphi_2d_ns"],
    )[-1]
    corner_sites = [1, parameters["columns_2d"], (parameters["rows_2d"] - 1) * parameters["columns_2d"] + 1, parameters["rows_2d"] * parameters["columns_2d"]]
    reduced = reduced_selected_density(at_tau, parameters["rows_2d"] * parameters["columns_2d"], corner_sites)
    ideal_w_vector = np.zeros(16, dtype=complex)
    ideal_w_vector[[8, 4, 2, 1]] = 0.5
    ideal_w_density = np.outer(ideal_w_vector, ideal_w_vector.conj())
    target = four_corner_target(parameters["rows_2d"], parameters["columns_2d"])
    fidelity = state_fidelity(at_tau, target)
    ideal_amplitudes = unitary_amplitudes(hamiltonian, [tau])[-1]
    ideal_corner_probabilities = np.abs(ideal_amplitudes[np.asarray(corner_sites) - 1]) ** 2
    ideal_corner_spread = float(np.ptp(ideal_corner_probabilities))
    save_npz(
        data_dir / "fig4_theory.npz",
        time_ns=times,
        populations=populations,
        selected_times_ns=times[selected_indices],
        selected_population_maps=populations[selected_indices].reshape((-1, parameters["rows_2d"], parameters["columns_2d"])),
        reduced_four_corner_density=reduced,
        ideal_w_density=ideal_w_density,
    )
    trace_error = float(abs(np.trace(at_tau) - 1.0))
    corner_probabilities = populations[int(np.argmin(abs(times - tau))), np.asarray(corner_sites) - 1]
    dissipative_corner_spread = float(np.ptp(corner_probabilities))
    return target_check(
        check_dir,
        "T007",
        status="passed" if trace_error < 1.0e-10 and fidelity > 0.8 and ideal_corner_spread < 1.0e-10 else "failed",
        formula_dependencies=["QS004", "QS005", "QS006"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - started,
        checks={
            "trace_error": trace_error,
            "w_state_fidelity": fidelity,
            "unitary_four_corner_probability_spread": ideal_corner_spread,
            "dissipative_four_corner_probability_spread": dissipative_corner_spread,
            "selected_times_ns": times[selected_indices].tolist(),
        },
        notes=[
            "Main Fig. 4 does not report m; m=0 is declared because its simulated fidelity matches the reported 0.85-scale result.",
            "Equal corner populations are a closed-system invariant. Under local loss/dephasing the initially occupied corner has a different path history, so dissipative corner spread is diagnostic rather than a pass condition.",
        ],
    )


def run_fidelity_sweeps(parameters: dict[str, Any], data_dir: Path, check_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    section = parameters["fidelity_sweep"]
    m_values = np.asarray(section["m_values"], dtype=int)
    theta = parameters["theta"]
    sigma = parameters["effective_pulse_sigma_ns"]
    buffer = parameters["pulse_buffer_ns"]
    rtol = parameters["ode"]["rtol"]
    atol = parameters["ode"]["atol"]

    one_started = time.perf_counter()
    j_1d = float(mhz_to_angular(parameters["j_fst_mhz"]))
    tau = np.pi / j_1d
    bell_target = endpoint_target(parameters["n_1d"])
    fidelity_1d = np.empty(len(m_values), dtype=float)
    nfev_1d = np.empty(len(m_values), dtype=int)
    trace_errors_1d = np.empty(len(m_values), dtype=float)
    cached_1d: dict[int, np.ndarray] = {}
    density_m_values = set(section["density_m_values"])
    for index, m in enumerate(m_values):
        result = pulsed_lindblad_final(
            fst_hamiltonian(parameters["n_1d"], int(m), j_1d, theta),
            tau,
            sigma_ns=sigma,
            buffer_ns=buffer,
            t1_ns=parameters["t1_ns"],
            t2_ns=parameters["t2_1d_ns"],
            rtol=rtol,
            atol=atol,
        )
        fidelity_1d[index] = state_fidelity(result.density_matrix, bell_target)
        nfev_1d[index] = result.nfev
        trace_errors_1d[index] = result.trace_error
        if int(m) in density_m_values:
            cached_1d[int(m)] = reduced_endpoint_density(result.density_matrix, parameters["n_1d"])
    anchor_reference = {0: 0.910, 4: 0.914, 50: 0.926}
    anchor_generated = {m: float(fidelity_1d[np.where(m_values == m)[0][0]]) for m in anchor_reference if m in m_values}
    anchor_errors = {f"m{m}": abs(anchor_generated[m] - value) for m, value in anchor_reference.items() if m in anchor_generated}
    save_payload_1d: dict[str, Any] = {
        "m_values": m_values,
        "fidelity": fidelity_1d,
        "ode_nfev": nfev_1d,
        "trace_errors": trace_errors_1d,
    }
    for m, density in cached_1d.items():
        save_payload_1d[f"reduced_density_m{m}"] = density
    save_npz(data_dir / "figS9.npz", **save_payload_1d)
    t009 = target_check(
        check_dir,
        "T009",
        status="passed" if max(trace_errors_1d) < 1.0e-8 and anchor_errors and max(anchor_errors.values()) < 0.015 else "failed",
        formula_dependencies=["QS004", "QS006", "QS009"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - one_started,
        checks={
            "reported_anchor_fidelities": anchor_reference,
            "generated_anchor_fidelities": anchor_generated,
            "anchor_absolute_errors": anchor_errors,
            "max_trace_error": float(max(trace_errors_1d)),
            "max_ode_evaluations": int(max(nfev_1d)),
        },
        notes=["The effective pulse is reconstructed because physical control transfer functions are absent."],
    )

    two_started = time.perf_counter()
    h_times = np.linspace(section["time_ns_min"], section["time_ns_max"], section["time_points"])
    w_target = four_corner_target(parameters["rows_2d"], parameters["columns_2d"])
    fidelity_2d = np.empty(len(m_values), dtype=float)
    nfev_2d = np.empty(len(m_values), dtype=int)
    trace_errors_2d = np.empty(len(m_values), dtype=float)
    for index, m in enumerate(m_values):
        result = pulsed_lindblad_final(
            fst_hamiltonian_2d(parameters["rows_2d"], parameters["columns_2d"], int(m), j_1d, theta),
            tau,
            sigma_ns=sigma,
            buffer_ns=buffer,
            t1_ns=parameters["t1_ns"],
            tphi_ns=parameters["tphi_2d_ns"],
            rtol=rtol,
            atol=atol,
        )
        fidelity_2d[index] = state_fidelity(result.density_matrix, w_target)
        nfev_2d[index] = result.nfev
        trace_errors_2d[index] = result.trace_error

    evolution_payload: dict[str, Any] = {
        "m_values": m_values,
        "fidelity": fidelity_2d,
        "ode_nfev": nfev_2d,
        "trace_errors": trace_errors_2d,
        "evolution_time_ns": h_times,
    }
    even_population_means: dict[str, float] = {}
    for m in section["evolution_2d_m_values"]:
        hamiltonian = fst_hamiltonian_2d(parameters["rows_2d"], parameters["columns_2d"], m, j_1d, theta)
        trajectory = lindblad_trajectory(
            hamiltonian,
            h_times,
            t1_ns=parameters["t1_ns"],
            tphi_ns=parameters["tphi_2d_ns"],
        )
        populations = np.real(np.diagonal(trajectory, axis1=1, axis2=2))[:, 1:]
        evolution_payload[f"populations_m{m}"] = populations
        even_population_means[f"m{m}"] = float(np.mean(np.sum(populations[:, 1::2], axis=1)))
    save_npz(data_dir / "figS10.npz", **evolution_payload)

    baseline = float(fidelity_2d[0])
    crossover_candidates = m_values[(m_values > 0) & (fidelity_2d >= baseline)]
    crossover = int(crossover_candidates[0]) if len(crossover_candidates) else None
    suppression = even_population_means[f"m{section['evolution_2d_m_values'][-1]}"] < even_population_means[f"m{section['evolution_2d_m_values'][0]}"]
    trend_passed = fidelity_2d[-1] > fidelity_2d[0] and suppression
    t010 = target_check(
        check_dir,
        "T010",
        status="passed" if max(trace_errors_2d) < 1.0e-8 and trend_passed else "failed",
        formula_dependencies=["QS004", "QS005", "QS006", "QS009"],
        parameter_match="paper_subset",
        elapsed_seconds=time.perf_counter() - two_started,
        checks={
            "generated_crossover_m": crossover,
            "paper_reported_crossover_m": 6,
            "fidelity_m0": float(fidelity_2d[0]),
            "fidelity_last_m": float(fidelity_2d[-1]),
            "mean_even_index_population": even_population_means,
            "large_m_trend_passed": bool(trend_passed),
            "max_trace_error": float(max(trace_errors_2d)),
            "max_ode_evaluations": int(max(nfev_2d)),
        },
        notes=["The crossover is a sensitive diagnostic of the unpublished physical-control transfer functions."],
    )
    return t009, t010


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    parameters = json.loads(Path(args.config).read_text(encoding="utf-8"))["parameters"]

    data_dir = Path("outputs/data")
    check_dir = Path("outputs/checks")
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)
    total_started = time.perf_counter()
    results: list[dict[str, Any]] = []
    results.append(run_eigensystem(parameters, data_dir, check_dir))
    results.append(run_three_site(parameters, data_dir, check_dir))
    results.append(run_five_site_pst(parameters, data_dir, check_dir))
    results.extend(run_one_dimensional_fst(parameters, data_dir, check_dir))
    t006, t008 = run_noise_targets(parameters, data_dir, check_dir)
    results.append(t006)
    results.append(run_main_2d(parameters, data_dir, check_dir))
    results.append(t008)
    results.extend(run_fidelity_sweeps(parameters, data_dir, check_dir))
    results.sort(key=lambda item: item["target_id"])

    summary = {
        "schema_version": 1,
        "paper_id": "2506.06669",
        "run_label": parameters["run_label"],
        "status": "passed" if all(item["status"] == "passed" for item in results) else "failed",
        "target_count": len(results),
        "targets": [
            {
                "target_id": item["target_id"],
                "status": item["status"],
                "elapsed_seconds": item["elapsed_seconds"],
                "parameter_match": item["parameter_match"],
            }
            for item in results
        ],
        "total_elapsed_seconds": round(time.perf_counter() - total_started, 6),
    }
    write_json(check_dir / "reproduction_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
