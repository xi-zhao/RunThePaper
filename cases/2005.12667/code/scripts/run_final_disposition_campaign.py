#!/usr/bin/env python3
"""Run one clean-room scientific campaign for every scored RMP target."""

from __future__ import annotations

import argparse
import copy
from math import sqrt
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
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
    rectangular_te_mode_features,
    small_matrix_multilevel_shift_check,
    tomography_claim_checks,
    transmon_harmonic_comparator,
)
from src.implementation_campaign import run_campaign  # noqa: E402


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _result(
    target_id: str,
    item_ids: list[str],
    *,
    scale: str,
    data: dict[str, Any],
    checks: dict[str, bool],
) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "status": "passed" if all(checks.values()) else "failed",
        "scientific_scale": scale,
        "item_ids": item_ids,
        "data": data,
        "checks": checks,
        "checks_passed": all(checks.values()),
    }


def _repair_results(
    parameters: dict[str, Any],
    item_map: dict[str, list[str]],
    *,
    ideal_mode_points: int,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}

    x = np.linspace(-4.0, 4.0, 801)
    potential, energies = lc_harmonic_reference(
        x, float(parameters["T028"]["omega"])
    )
    spacing_residual = float(
        np.max(np.abs(np.diff(energies) - float(parameters["T028"]["omega"])))
    )
    results["T028"] = _result(
        "T028",
        item_map["T028"],
        scale="normalized_analytic_reference",
        data={"x": x, "potential": potential, "energies": energies},
        checks={"equal_spacing": spacing_residual < 1e-12},
    )

    detuning = np.linspace(-5.0, 5.0, 1601)
    response = normalized_damped_response(detuning)
    half_power = detuning[response >= 1.0 / sqrt(2.0)]
    fwhm_residual = abs(float(half_power[-1] - half_power[0]) - 1.0)
    results["T029"] = _result(
        "T029",
        item_map["T029"],
        scale="normalized_analytic_reference",
        data={"detuning_over_kappa": detuning, "response": response},
        checks={
            "unit_peak": abs(float(np.max(response)) - 1.0) < 1e-12,
            "unit_fwhm": fwhm_residual < 0.02,
        },
    )

    marginals = quadrature_marginals(
        float(parameters["T031"]["two_chi_over_kappa"]),
        float(parameters["T031"]["integration_time"]),
    )
    ground_norm = float(np.trapezoid(marginals.ground, marginals.x))
    excited_norm = float(np.trapezoid(marginals.excited, marginals.x))
    results["T031"] = _result(
        "T031",
        item_map["T031"],
        scale="paper_parameters",
        data={
            "x": marginals.x,
            "ground": marginals.ground,
            "excited": marginals.excited,
            "overlap_area": marginals.overlap_area,
            "assignment_error": marginals.assignment_error,
        },
        checks={
            "ground_normalized": abs(ground_norm - 1.0) < 1e-8,
            "excited_normalized": abs(excited_norm - 1.0) < 1e-8,
            "physical_overlap": 0.0 <= marginals.overlap_area <= 1.0,
        },
    )

    line_modes = finite_line_mode_checks()
    claim_metrics = {
        "T033": small_matrix_multilevel_shift_check(),
        "T034": {
            key: line_modes[key]
            for key in ("orthonormality_error", "completeness_trace")
        },
        "T035": {
            key: line_modes[key]
            for key in ("boundary_current_magnitude", "energy_balance_error")
        },
        "T036": gaussian_wavepacket_time_mode_checks(),
        "T037": dissipation_drive_claim_checks(),
        "T038": amplifier_iq_claim_checks(),
        "T039": tomography_claim_checks(),
    }
    claim_checks = {
        "T033": claim_metrics["T033"]["max_spacing_error"] < 2e-3,
        "T034": claim_metrics["T034"]["orthonormality_error"] < 1e-6,
        "T035": claim_metrics["T035"]["energy_balance_error"] < 1e-6,
        "T036": (
            claim_metrics["T036"]["overlap_zero_delay"] > 0.999
            and claim_metrics["T036"]["overlap_four_sigma_delay"] < 0.05
        ),
        "T037": (
            claim_metrics["T037"]["t2_identity_residual"] < 1e-12
            and claim_metrics["T037"]["coherent_poisson_residual"] < 1e-12
        ),
        "T038": (
            claim_metrics["T038"]["max_commutator_error"] < 1e-12
            and claim_metrics["T038"]["iq_orthogonality_overlap"] < 1e-3
        ),
        "T039": (
            claim_metrics["T039"]["wigner_integral_error"] < 1e-8
            and claim_metrics["T039"]["q_integral_error"] < 5e-3
        ),
    }
    for target_id, metrics in claim_metrics.items():
        results[target_id] = _result(
            target_id,
            item_map[target_id],
            scale="equation_claim",
            data=metrics,
            checks={"claim_invariant": claim_checks[target_id]},
        )

    phase = np.linspace(-0.9, 0.9, 801)
    cosine, harmonic = transmon_harmonic_comparator(
        phase, float(parameters["T040"]["EJ_over_EC"])
    )
    center = len(phase) // 2
    curvature = (
        cosine[center + 1] - 2.0 * cosine[center] + cosine[center - 1]
    ) / float(phase[1] - phase[0]) ** 2
    curvature_residual = abs(
        float(curvature) - float(parameters["T040"]["EJ_over_EC"])
    )
    results["T040"] = _result(
        "T040",
        item_map["T040"],
        scale="paper_parameters",
        data={"phase": phase, "cosine": cosine, "harmonic": harmonic},
        checks={"matched_origin_curvature": curvature_residual < 0.05},
    )

    time, q_from_q, c_from_q, q_from_c, c_from_c = low_damping_exchange(
        float(parameters["T041"]["g_MHz"]),
        float(parameters["T041"]["kappa_MHz"]),
        float(parameters["T041"]["gamma1_MHz"]),
        float(parameters["T041"]["time_stop_per_inverse_MHz"]),
    )
    symmetry_residual = float(
        max(
            np.max(np.abs(q_from_q - c_from_c)),
            np.max(np.abs(c_from_q - q_from_c)),
        )
    )
    results["T041"] = _result(
        "T041",
        item_map["T041"],
        scale="paper_parameters",
        data={
            "time_inverse_MHz": time,
            "qubit_from_qubit": q_from_q,
            "cavity_from_qubit": c_from_q,
            "qubit_from_cavity": q_from_c,
            "cavity_from_cavity": c_from_c,
        },
        checks={
            "exchange_symmetry": symmetry_residual < 1e-10,
            "population_bounds": bool(
                min(
                    np.min(q_from_q),
                    np.min(c_from_q),
                    np.min(q_from_c),
                    np.min(c_from_c),
                )
                >= -1e-12
            ),
        },
    )

    strong = parameters["T043"]
    qubit_detuning = np.linspace(-12.0, 72.0, 4201)
    spectrum, mean_photons = epsilon_driven_strong_dispersive(
        qubit_detuning,
        chi=float(strong["chi_MHz"]),
        rabi_frequency=float(strong["rabi_MHz"]),
        gamma1=float(strong["gamma1_MHz"]),
        gamma_phi=float(strong["gamma_phi_MHz"]),
        kappa=float(strong["kappa_MHz"]),
        epsilon=float(strong["epsilon_MHz"]),
        cavity_drive_detuning=float(
            strong["cavity_drive_detuning_from_pulled_resonance_MHz"]
        ),
    )
    results["T043"] = _result(
        "T043",
        item_map["T043"],
        scale="paper_subset",
        data={
            "qubit_detuning_MHz": qubit_detuning,
            "excited_population": spectrum,
            "derived_mean_photons": mean_photons,
        },
        checks={
            "caption_resonant_occupation": abs(mean_photons - 4.0) < 1e-12,
            "finite_nonnegative_spectrum": bool(
                np.all(np.isfinite(spectrum)) and np.min(spectrum) >= 0.0
            ),
            "number_split_support": int(np.count_nonzero(spectrum > 0.01 * np.max(spectrum))) > 20,
        },
    )

    ideal_modes = rectangular_te_mode_features(points=ideal_mode_points)
    results["T030"] = _result(
        "T030",
        ["M-F04-b", "M-F04-c", "M-F04-d", "M-F04-e"],
        scale="normalized_ideal_rectangular_cavity_proxy",
        data=ideal_modes,
        checks={
            "four_declared_modes": ideal_modes["mode_labels"]
            == ["TE110", "TE210", "TE120", "TE220"],
            "mode_orthonormality": ideal_modes["max_orthonormality_error"] < 1e-10,
            "helmholtz_equation": ideal_modes["max_helmholtz_residual"] < 0.12,
        },
    )
    return results


def _basis_convergence_error(
    full: dict[str, Any],
    reduced: dict[str, Any],
) -> float:
    errors: list[float] = []
    full_rows = full["data"]["spectra"]
    reduced_rows = reduced["data"]["spectra"]
    if len(full_rows) != len(reduced_rows):
        raise ValueError("T032 convergence sweeps do not share a grid")
    for full_row, reduced_row in zip(full_rows, reduced_rows, strict=True):
        for key in ("one_excitation", "two_excitation"):
            left = np.asarray(full_row[key], dtype=float)
            right = np.asarray(reduced_row[key], dtype=float)
            if left.shape != right.shape:
                raise ValueError(f"T032 {key} manifold shape drifted")
            errors.append(float(np.max(np.abs(left - right))))
    return max(errors)


def run(config_path: Path, output_root: Path) -> dict[str, Any]:
    final_config = _read_json(config_path)
    if final_config.get("paper_id") != "2005.12667":
        raise ValueError("final campaign configuration targets the wrong paper")
    profile = final_config["profiles"]["paper"]
    implementation_path = WORKSPACE / profile["implementation_config"]
    repair_path = WORKSPACE / profile["repair_config"]
    implementation = _read_json(implementation_path)
    repair = _read_json(repair_path)

    results = run_campaign(implementation, profile["implementation_profile"])
    results.update(
        _repair_results(
            repair["targets"],
            final_config["repair_target_items"],
            ideal_mode_points=int(profile["ideal_rectangular_cavity_grid_points"]),
        )
    )

    convergence_config = copy.deepcopy(implementation)
    convergence_config["target_items"] = {
        "T032": implementation["target_items"]["T032"]
    }
    convergence_config["profiles"][profile["implementation_profile"]][
        "fig30_dimensions"
    ] = profile["basis_convergence_dimensions"]
    convergence = run_campaign(
        convergence_config, profile["implementation_profile"]
    )["T032"]
    basis_error = _basis_convergence_error(results["T032"], convergence)
    results["T032"]["data"]["basis_convergence_max_abs_error"] = basis_error
    results["T032"]["checks"]["basis_converged"] = basis_error <= float(
        profile["basis_convergence_tolerance"]
    )
    results["T032"]["checks_passed"] = all(results["T032"]["checks"].values())

    expected = set(final_config["target_ids"])
    if set(results) != expected:
        raise RuntimeError(
            f"target surface mismatch: missing={sorted(expected - set(results))}, "
            f"extra={sorted(set(results) - expected)}"
        )
    failures = sorted(
        target_id
        for target_id, payload in results.items()
        if not payload.get("checks_passed")
    )
    external = set(final_config["externally_blocked_candidates"])
    for target_id, payload in results.items():
        payload["scientific_disposition_candidate"] = (
            "externally_blocked" if target_id in external else "reproduced"
        )
        _write_json(output_root / f"{target_id}.json", payload)

    summary = {
        "schema_version": 1,
        "paper_id": "2005.12667",
        "status": "passed" if not failures else "failed",
        "profile": "paper",
        "targets_total": len(results),
        "reproduced_candidates": sorted(expected - external),
        "externally_blocked_candidates": sorted(external),
        "failed_checks": failures,
        "clean_room_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "source_or_reference_pixels_read": False,
            "legacy_generated_outputs_read": False,
        },
    }
    _write_json(output_root / "campaign_summary.json", summary)
    check_path = WORKSPACE / "outputs/checks/final_disposition/discriminating_checks.json"
    _write_json(
        check_path,
        {
            "schema_version": 1,
            "paper_id": "2005.12667",
            "status": summary["status"],
            "profile": "paper",
            "targets": {
                target_id: {
                    "status": "passed" if payload.get("checks_passed") else "failed",
                    "scientific_scale": payload.get("scientific_scale"),
                    "checks": payload.get("checks"),
                    "disposition_candidate": payload[
                        "scientific_disposition_candidate"
                    ],
                    "evidence": f"outputs/data/final_disposition/{target_id}.json",
                }
                for target_id, payload in sorted(results.items())
            },
            "clean_room_boundary": summary["clean_room_boundary"],
        },
    )
    if failures:
        raise RuntimeError(f"final scientific checks failed: {', '.join(failures)}")
    return summary


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        if np.iscomplexobj(value):
            return {"real": value.real.tolist(), "imag": value.imag.tolist()}
        return value.tolist()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, np.generic):
        return value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs/data/final_disposition"),
    )
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output_root = (
        args.output_root
        if args.output_root.is_absolute()
        else WORKSPACE / args.output_root
    )
    summary = run(config_path.resolve(), output_root.resolve())
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
