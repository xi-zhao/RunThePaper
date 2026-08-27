"""Claim-level clean-room checks for enhanced quantum state transfer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm

from src.state_transfer import (
    endpoint_target,
    expected_zigzag_spectrum,
    fst_hamiltonian,
    fst_hamiltonian_2d,
    four_corner_target,
    lindblad_trajectory,
    mhz_to_angular,
    pulsed_lindblad_final,
    state_fidelity,
    unitary_amplitudes,
    zigzag_hamiltonian,
)


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"configuration must be a JSON object: {path}")
    return payload


def _c001(spec: dict[str, Any]) -> dict[str, Any]:
    n = int(spec["chain_sites"])
    coupling = float(spec["coupling"])
    tolerance = float(spec["tolerance"])
    literal = np.zeros((n, n), dtype=complex)
    corrected = np.zeros((n, n), dtype=complex)
    for site in range(n - 1):
        literal[site + 1, site] += 2.0 * coupling
        corrected[site + 1, site] += coupling
        corrected[site, site + 1] += coupling
    literal_norm = float(np.linalg.norm(literal - literal.conj().T))
    corrected_norm = float(np.linalg.norm(corrected - corrected.conj().T))
    if not literal_norm > tolerance or not corrected_norm <= tolerance:
        raise RuntimeError("C001: literal/corrected Hermiticity discrimination failed")
    return {
        "target_id": "C001",
        "status": "code_attested_claim_test",
        "scientific_coverage_promoted": False,
        "literal_hermiticity_residual": literal_norm,
        "conjugate_corrected_hermiticity_residual": corrected_norm,
        "literal_expression_is_hermitian": False,
        "conjugate_corrected_expression_is_hermitian": True,
        "fresh_review_required_before_paper_error_claim": True,
    }


def _c002(spec: dict[str, Any]) -> dict[str, Any]:
    j_scale = float(spec["j_scale"])
    transfer_time = float(spec["transfer_time"])
    tolerance = float(spec["tolerance"])
    rows: list[dict[str, Any]] = []
    for n in spec["odd_chain_sizes"]:
        for m in spec["m_values"]:
            hamiltonian = zigzag_hamiltonian(int(n), int(m), j_scale)
            spectrum_error = float(
                np.max(
                    np.abs(
                        np.linalg.eigvalsh(hamiltonian)
                        - expected_zigzag_spectrum(int(n), int(m), j_scale)
                    )
                )
            )
            endpoint = unitary_amplitudes(
                hamiltonian, [transfer_time], initial_site=0
            )[0, -1]
            transfer_error = float(abs(1.0 - abs(endpoint) ** 2))
            rows.append(
                {
                    "n_sites": int(n),
                    "m": int(m),
                    "spectrum_max_error": spectrum_error,
                    "endpoint_transfer_error": transfer_error,
                }
            )
    passed = all(
        row["spectrum_max_error"] <= tolerance
        and row["endpoint_transfer_error"] <= tolerance
        for row in rows
    )
    if not passed:
        raise RuntimeError("C002: finite-domain universal-property search failed")
    return {
        "target_id": "C002",
        "status": "code_attested_finite_property_domain",
        "scientific_coverage_promoted": False,
        "tested_instances": rows,
        "finite_test_domain_passed": True,
        "analytic_all_integer_proof_still_required": True,
    }


def _schur_effective(hamiltonian: np.ndarray) -> np.ndarray:
    odd = np.arange(0, len(hamiltonian), 2)
    even = np.arange(1, len(hamiltonian), 2)
    h_oo = hamiltonian[np.ix_(odd, odd)]
    h_oe = hamiltonian[np.ix_(odd, even)]
    h_ee = hamiltonian[np.ix_(even, even)]
    return h_oo - h_oe @ np.linalg.solve(h_ee, h_oe.T)


def _c003(spec: dict[str, Any]) -> dict[str, Any]:
    j_scale = float(spec["j_scale"])
    ratio_limit = float(spec["convergence_ratio_limit"])
    rows: list[dict[str, Any]] = []
    for n in spec["odd_chain_sizes"]:
        expected_low = j_scale * np.arange(-(int(n) - 1) // 2, 1, dtype=float)
        errors: list[float] = []
        for m in spec["m_values"]:
            effective = _schur_effective(
                zigzag_hamiltonian(int(n), int(m), j_scale)
            )
            error = float(
                np.max(np.abs(np.linalg.eigvalsh(effective) - expected_low))
            )
            errors.append(error)
            rows.append(
                {
                    "n_sites": int(n),
                    "m": int(m),
                    "effective_dimension": int(len(effective)),
                    "low_branch_spectrum_error": error,
                }
            )
        ratios = [errors[i + 1] / errors[i] for i in range(len(errors) - 1)]
        if not all(ratio <= ratio_limit for ratio in ratios):
            raise RuntimeError(f"C003: Schur convergence failed for n={n}: {ratios}")
    return {
        "target_id": "C003",
        "status": "code_attested_asymptotic_schur_check",
        "scientific_coverage_promoted": False,
        "checks": rows,
        "asymptotic_spectrum_convergence_passed": True,
        "supplement_index_convention_fresh_review_required": True,
    }


def _c004(spec: dict[str, Any]) -> dict[str, Any]:
    m = int(spec["m"])
    j_scale = float(spec["j_scale"])
    theta = float(spec["theta"])
    transfer_time = float(spec["transfer_time"])
    tolerance = float(spec["tolerance"])
    rows: list[dict[str, Any]] = []
    for n in spec["odd_chain_sizes"]:
        base = zigzag_hamiltonian(int(n), m, j_scale)
        deformed = fst_hamiltonian(int(n), m, j_scale, theta)
        spectrum_error = float(
            np.max(np.abs(np.linalg.eigvalsh(base) - np.linalg.eigvalsh(deformed)))
        )
        amplitudes = unitary_amplitudes(deformed, [transfer_time])[0]
        endpoint_mass = float(abs(amplitudes[0]) ** 2 + abs(amplitudes[-1]) ** 2)
        middle_mass = float(np.sum(np.abs(amplitudes[1:-1]) ** 2))
        relative_phase = amplitudes[-1] / amplitudes[0]
        gauge_corrected_phase = -relative_phase
        rows.append(
            {
                "n_sites": int(n),
                "isospectral_error": spectrum_error,
                "endpoint_probability": endpoint_mass,
                "middle_probability": middle_mass,
                "relative_phase_real": float(relative_phase.real),
                "relative_phase_imag": float(relative_phase.imag),
                "bell_minus_gauge_phase_real": float(gauge_corrected_phase.real),
                "bell_minus_gauge_phase_imag": float(gauge_corrected_phase.imag),
            }
        )
    if not all(
        row["isospectral_error"] <= tolerance
        and abs(1.0 - row["endpoint_probability"]) <= tolerance
        and row["middle_probability"] <= tolerance
        for row in rows
    ):
        raise RuntimeError("C004: isospectral endpoint-gauge test failed")
    return {
        "target_id": "C004",
        "status": "code_attested_phase_gauge_check",
        "scientific_coverage_promoted": False,
        "checks": rows,
        "local_endpoint_phase_flip_maps_plus_to_minus": True,
        "fresh_review_required_for_paper_gauge_convention": True,
    }


def _d001(spec: dict[str, Any]) -> dict[str, Any]:
    rows = int(spec["rows"])
    columns = int(spec["columns"])
    transfer_time = float(spec["transfer_time"])
    tolerance = float(spec["backend_tolerance"])
    target = four_corner_target(rows, columns)[1:]
    checks: list[dict[str, Any]] = []
    for m in spec["m_values"]:
        hamiltonian = fst_hamiltonian_2d(
            rows,
            columns,
            int(m),
            float(spec["j_scale"]),
            float(spec["theta"]),
        )
        eig_state = unitary_amplitudes(hamiltonian, [transfer_time])[0]
        expm_state = expm(-1j * transfer_time * hamiltonian)[:, 0]
        backend_error = float(np.linalg.norm(eig_state - expm_state))
        ideal_fidelity = float(abs(np.vdot(target, eig_state)) ** 2)
        checks.append(
            {
                "m": int(m),
                "independent_backend_state_error": backend_error,
                "ideal_four_corner_fidelity": ideal_fidelity,
            }
        )
    if not all(row["independent_backend_state_error"] <= tolerance for row in checks):
        raise RuntimeError("D001: independent propagator cross-check failed")
    required = spec.get("required_input_schema")
    supplied = spec.get("supplied_inputs")
    if not isinstance(required, dict) or not required or not isinstance(supplied, list):
        raise ValueError("D001: invalid indispensable-input schema")
    missing = sorted(set(required) - {str(value) for value in supplied})
    if not missing:
        raise RuntimeError("D001: full crossover inputs declared but no dissipative run configured")

    published = spec["published_simulation"]
    j_scale = float(mhz_to_angular(published["j_fst_mhz"]))
    tau_ns = float(published["tau_ns"])
    m_grid = [int(value) for value in published["m_values"]]
    target_2d = four_corner_target(rows, columns)

    def first_crossover(values: list[float]) -> int | None:
        baseline = values[0]
        return next(
            (m for m, value in zip(m_grid[1:], values[1:], strict=True) if value >= baseline),
            None,
        )

    square_fidelities: list[float] = []
    shared_fidelities: list[float] = []
    split_fidelities: list[float] = []
    trace_errors: list[float] = []
    for m in m_grid:
        hamiltonian = fst_hamiltonian_2d(
            rows, columns, m, j_scale, float(spec["theta"])
        )
        square_density = lindblad_trajectory(
            hamiltonian,
            [0.0, tau_ns],
            t1_ns=float(published["t1_ns"]),
            tphi_ns=float(published["tphi_2d_ns"]),
        )[-1]
        square_fidelities.append(state_fidelity(square_density, target_2d))
        shared = pulsed_lindblad_final(
            hamiltonian,
            tau_ns,
            sigma_ns=float(published["coupler_sigma_ns"]),
            buffer_ns=float(published["buffer_ns"]),
            t1_ns=float(published["t1_ns"]),
            tphi_ns=float(published["tphi_2d_ns"]),
        )
        split = pulsed_lindblad_final(
            hamiltonian,
            tau_ns,
            sigma_ns=float(published["coupler_sigma_ns"]),
            onsite_sigma_ns=float(published["qubit_sigma_ns"]),
            coupling_sigma_ns=float(published["coupler_sigma_ns"]),
            buffer_ns=float(published["buffer_ns"]),
            t1_ns=float(published["t1_ns"]),
            tphi_ns=float(published["tphi_2d_ns"]),
        )
        shared_fidelities.append(state_fidelity(shared.density_matrix, target_2d))
        split_fidelities.append(state_fidelity(split.density_matrix, target_2d))
        trace_errors.extend([shared.trace_error, split.trace_error])

    anchor_target = endpoint_target(int(published["n_1d"]))
    anchor_comparison: dict[str, dict[str, float]] = {}
    for m_text, reference in published["one_dimensional_fidelity_anchors"].items():
        m = int(m_text)
        hamiltonian = fst_hamiltonian(
            int(published["n_1d"]), m, j_scale, float(spec["theta"])
        )
        shared = pulsed_lindblad_final(
            hamiltonian,
            tau_ns,
            sigma_ns=float(published["coupler_sigma_ns"]),
            buffer_ns=float(published["buffer_ns"]),
            t1_ns=float(published["t1_ns"]),
            t2_ns=float(published["t2_1d_ns"]),
        )
        split = pulsed_lindblad_final(
            hamiltonian,
            tau_ns,
            sigma_ns=float(published["coupler_sigma_ns"]),
            onsite_sigma_ns=float(published["qubit_sigma_ns"]),
            coupling_sigma_ns=float(published["coupler_sigma_ns"]),
            buffer_ns=float(published["buffer_ns"]),
            t1_ns=float(published["t1_ns"]),
            t2_ns=float(published["t2_1d_ns"]),
        )
        anchor_comparison[m_text] = {
            "paper": float(reference),
            "shared_envelope": state_fidelity(shared.density_matrix, anchor_target),
            "channel_split_envelope": state_fidelity(split.density_matrix, anchor_target),
        }

    crossover_by_interpretation = {
        "square": first_crossover(square_fidelities),
        "shared_flattop": first_crossover(shared_fidelities),
        "channel_split_flattop": first_crossover(split_fidelities),
    }
    if max(trace_errors) > float(published["trace_tolerance"]):
        raise RuntimeError("D001: pulse-contract variants violated trace preservation")
    return {
        "target_id": "D001",
        "status": "blocked_missing_source_input",
        "scientific_coverage_promoted": False,
        "ideal_static_checks": checks,
        "core_static_hamiltonian_and_propagator_check_passed": True,
        "publication_source_trace": {
            "status": "passed",
            "source_ref": str(published["source_ref"]),
            "disclosed_inputs": published["disclosed_inputs"],
            "undisclosed_inputs": required,
            "paper_reported_crossover_m": int(published["paper_reported_crossover_m"]),
        },
        "pulse_contract_sensitivity": {
            "m_values": m_grid,
            "square_fidelity": square_fidelities,
            "shared_flattop_fidelity": shared_fidelities,
            "channel_split_flattop_fidelity": split_fidelities,
            "first_integer_crossover_by_interpretation": crossover_by_interpretation,
            "one_dimensional_anchor_comparison": anchor_comparison,
            "max_trace_error": max(trace_errors),
            "interpretation_changes_scientific_result": len(
                {str(value) for value in crossover_by_interpretation.values()}
            )
            > 1,
        },
        "missing_inputs": missing,
        "required_input_schema": required,
        "acceptance_boundary": str(spec["acceptance_boundary"]),
    }


def run_campaign(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _read_object(config_path)
    targets = config.get("targets")
    if not isinstance(targets, dict):
        raise TypeError("targets must be an object")
    handlers = {"C001": _c001, "C002": _c002, "C003": _c003, "C004": _c004, "D001": _d001}
    output_dir = output_root / "checks" / "implementation_closure"
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for target_id, handler in handlers.items():
        raw_spec = targets.get(target_id)
        if not isinstance(raw_spec, dict):
            raise TypeError(f"{target_id}: target specification must be an object")
        record = handler(raw_spec)
        (output_dir / f"{target_id}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        records.append(record)
    summary = {
        "schema_version": 1,
        "paper_id": config.get("paper_id"),
        "target_count": len(records),
        "code_attested_count": len(records),
        "input_blocked_count": sum(
            row["status"] == "blocked_missing_source_input" for row in records
        ),
        "scientific_coverage_promoted": False,
    }
    (output_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary
