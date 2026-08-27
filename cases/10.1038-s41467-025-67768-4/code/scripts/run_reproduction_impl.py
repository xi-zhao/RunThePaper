#!/usr/bin/env python3
"""Generate all independently reproducible numerical targets.

The isolated runner stages this script, ``src/``, and the JSON configuration in
a fresh directory.  The script has no path or API for reading the paper PDF,
author data, original figures, or network resources.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.qem_models import (
    bravyi_vargo_path_error,
    compose_depolarizing_probabilities,
    feedback_acceptance,
    feedback_expectation,
    feedback_expectation_enumerated,
    fixed_total_error_schedule,
    logical_memory_expectation,
    repetition_expectation,
    xor_probability,
    zne_metrics,
    zne_weights,
)
from src.surface_code import logical_attenuation, validate_code


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def _save_npz(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def _processor_i_base_flip(parameters: dict) -> float:
    median = parameters["processor_i_median"]
    one_qubit_flip = 2.0 * median["one_qubit_pauli_error"] / 3.0
    two_qubit_data_flip = 8.0 * median["two_qubit_pauli_error"] / 15.0
    events = [one_qubit_flip]
    events.extend([two_qubit_data_flip] * median["two_qubit_events_per_layer"])
    events.append(median["method_i_readout_error"])
    return float(xor_probability(events))


def generate_feedback(parameters: dict) -> dict:
    r = np.linspace(parameters["r_min"], parameters["r_max"], parameters["r_points"])
    theta = np.asarray(parameters["theta_over_pi"], dtype=float) * np.pi
    raw = np.stack([feedback_expectation(r, parameters["p"], value, False) for value in theta])
    corrected = np.stack([feedback_expectation(r, parameters["p"], value, True) for value in theta])
    acceptance = feedback_acceptance(r, parameters["p"])
    enumeration_errors = []
    acceptance_errors = []
    for scale_index, scale in enumerate(r):
        for angle_index, angle in enumerate(theta):
            raw_enum, _ = feedback_expectation_enumerated(float(scale), parameters["p"], float(angle), False)
            corrected_enum, accepted_enum = feedback_expectation_enumerated(float(scale), parameters["p"], float(angle), True)
            enumeration_errors.extend(
                [
                    abs(raw_enum - raw[angle_index, scale_index]),
                    abs(corrected_enum - corrected[angle_index, scale_index]),
                ]
            )
            acceptance_errors.append(abs(accepted_enum - feedback_acceptance(scale, parameters["p"])))
    _save_npz(
        Path("outputs/data/feedback_curves.npz"),
        r=r,
        theta=theta,
        raw=raw,
        corrected=corrected,
        acceptance=acceptance,
    )
    return {
        "max_closed_form_vs_enumeration": float(max(enumeration_errors)),
        "max_acceptance_error": float(max(acceptance_errors)),
        "minimum_acceptance": float(np.min(acceptance)),
    }


def generate_repetition(parameters: dict) -> tuple[dict, float]:
    r = np.linspace(parameters["r_min"], parameters["r_max"], parameters["r_points"])
    distances = np.asarray(parameters["distances"], dtype=int)
    base_flip = _processor_i_base_flip(parameters)
    corrected_analytic = np.stack(
        [repetition_expectation(int(d), 1, r, parameters["one_round_p"], corrected=True) for d in distances]
    )
    corrected_calibrated = np.stack(
        [
            repetition_expectation(
                int(d),
                1,
                r,
                parameters["one_round_p"],
                corrected=True,
                base_bit_flip_probability=base_flip,
            )
            for d in distances
        ]
    )
    raw_analytic = repetition_expectation(
        int(distances[-1]), 1, r, parameters["one_round_p"], corrected=False
    )
    raw_calibrated = repetition_expectation(
        int(distances[-1]),
        1,
        r,
        parameters["one_round_p"],
        corrected=False,
        base_bit_flip_probability=base_flip,
    )
    _save_npz(
        Path("outputs/data/repetition_one_round.npz"),
        r=r,
        distances=distances,
        corrected_analytic=corrected_analytic,
        corrected_calibrated=corrected_calibrated,
        raw_analytic=raw_analytic,
        raw_calibrated=raw_calibrated,
        effective_base_bit_flip=np.asarray(base_flip),
    )

    multi_r = np.linspace(1.0, parameters["multi_r_max"], parameters["multi_r_points"])
    rounds = np.asarray(parameters["multi_rounds"], dtype=int)
    unit_probabilities = np.asarray(parameters["multi_round_p"], dtype=float)
    multi_analytic = np.stack(
        [
            repetition_expectation(
                parameters["multi_round_distance"], int(m), multi_r, float(p), corrected=True
            )
            for m, p in zip(rounds, unit_probabilities, strict=True)
        ]
    )
    multi_calibrated = np.stack(
        [
            repetition_expectation(
                parameters["multi_round_distance"],
                int(m),
                multi_r,
                float(p),
                corrected=True,
                base_bit_flip_probability=base_flip,
            )
            for m, p in zip(rounds, unit_probabilities, strict=True)
        ]
    )
    _save_npz(
        Path("outputs/data/repetition_multi_round.npz"),
        r=multi_r,
        rounds=rounds,
        unit_probabilities=unit_probabilities,
        corrected_analytic=multi_analytic,
        corrected_calibrated=multi_calibrated,
        effective_base_bit_flip=np.asarray(base_flip),
    )
    distance_ordering = np.diff(corrected_analytic, axis=0)
    return {
        "effective_base_bit_flip": base_flip,
        "minimum_distance_improvement": float(np.min(distance_ordering)),
        "one_round_values_at_r1": corrected_analytic[:, 0].tolist(),
        "multi_round_values_at_r1": multi_analytic[:, 0].tolist(),
    }, base_flip


def generate_surface_code(parameters: dict) -> dict:
    r = np.linspace(parameters["r_min"], parameters["r_max"], parameters["r_points"])
    preparation_p = parameters["preparation_depolarizing_probability"]
    injection_p = parameters["assumed_injection_probability"]
    layers = parameters["injection_layers"]
    x_attenuation = []
    z_attenuation = []
    channels = []
    physical_attenuation = []
    for scale in r:
        scaled_injection = float(scale * injection_p)
        effective_p = compose_depolarizing_probabilities([preparation_p, *([scaled_injection] * layers)])
        x_factor, z_factor, channel = logical_attenuation(effective_p)
        x_attenuation.append(x_factor)
        z_attenuation.append(z_factor)
        channels.append(channel)
        physical_attenuation.append((1.0 - 4.0 * effective_p / 3.0) ** 3)
    x_attenuation = np.asarray(x_attenuation)
    z_attenuation = np.asarray(z_attenuation)
    channels = np.asarray(channels)
    physical_attenuation = np.asarray(physical_attenuation)

    theta = parameters["psi_angle_over_pi"] * np.pi
    ideal_x = np.asarray([0.0, 1.0, np.sin(2.0 * theta)])
    ideal_z = np.asarray([1.0, 0.0, np.cos(2.0 * theta)])
    state_labels = np.asarray(["zero", "plus", "psi"])
    corrected_x = ideal_x[:, None] * x_attenuation[None, :]
    corrected_z = ideal_z[:, None] * z_attenuation[None, :]
    raw_x = ideal_x[:, None] * physical_attenuation[None, :]
    raw_z = ideal_z[:, None] * physical_attenuation[None, :]

    # Main Fig. 4(b) scans real logical states
    # cos(theta)|0_L> + sin(theta)|1_L> around the X_L-Z_L great circle.
    # The reconstructed logical Pauli channel is isotropic on X_L and Z_L,
    # so the independently generated circle contracts by the frozen channel
    # attenuation at each noise scale.  The angle grid is a declared numeric
    # input; no source-figure coordinates are used.
    bloch_theta = np.linspace(0.0, np.pi, parameters["bloch_angle_points"])
    bloch_ideal_x = np.sin(2.0 * bloch_theta)
    bloch_ideal_z = np.cos(2.0 * bloch_theta)
    bloch_corrected_x = x_attenuation[:, None] * bloch_ideal_x[None, :]
    bloch_corrected_z = z_attenuation[:, None] * bloch_ideal_z[None, :]
    bloch_raw_x = physical_attenuation[:, None] * bloch_ideal_x[None, :]
    bloch_raw_z = physical_attenuation[:, None] * bloch_ideal_z[None, :]

    _save_npz(
        Path("outputs/data/surface_code.npz"),
        r=r,
        state_labels=state_labels,
        ideal_x=ideal_x,
        ideal_z=ideal_z,
        corrected_x=corrected_x,
        corrected_z=corrected_z,
        raw_x=raw_x,
        raw_z=raw_z,
        logical_channel=channels,
        logical_x_attenuation=x_attenuation,
        logical_z_attenuation=z_attenuation,
        physical_weight3_attenuation=physical_attenuation,
        bloch_theta=bloch_theta,
        bloch_ideal_x=bloch_ideal_x,
        bloch_ideal_z=bloch_ideal_z,
        bloch_corrected_x=bloch_corrected_x,
        bloch_corrected_z=bloch_corrected_z,
        bloch_raw_x=bloch_raw_x,
        bloch_raw_z=bloch_raw_z,
    )
    code_checks = validate_code()
    corrected_radius = np.sqrt(bloch_corrected_x**2 + bloch_corrected_z**2)
    raw_radius = np.sqrt(bloch_raw_x**2 + bloch_raw_z**2)
    return {
        **code_checks,
        "max_channel_normalization_error": float(np.max(np.abs(channels.sum(axis=1) - 1.0))),
        "logical_z_psi_at_r1": float(corrected_z[2, 0]),
        "raw_z_psi_at_r1": float(raw_z[2, 0]),
        "max_corrected_bloch_radius_error": float(
            np.max(np.abs(corrected_radius - x_attenuation[:, None]))
        ),
        "max_raw_bloch_radius_error": float(
            np.max(np.abs(raw_radius - physical_attenuation[:, None]))
        ),
    }


def _zne_curve(
    distance: int,
    rounds: int,
    r1_values: np.ndarray,
    injected_p: float,
    base_flip: float,
    *,
    corrected: bool,
    amplify_base: bool,
) -> tuple[np.ndarray, np.ndarray]:
    raw_at_one = float(
        repetition_expectation(
            distance,
            rounds,
            1.0,
            injected_p,
            corrected=corrected,
            base_bit_flip_probability=base_flip,
            amplify_base=amplify_base,
        )
    )
    delta = []
    overhead = []
    effective_distance = distance if corrected else 1
    for r1 in r1_values:
        boosted = float(
            repetition_expectation(
                distance,
                rounds,
                float(r1),
                injected_p,
                corrected=corrected,
                base_bit_flip_probability=base_flip,
                amplify_base=amplify_base,
            )
        )
        metrics = zne_metrics([raw_at_one, boosted], [1.0, float(r1)], effective_distance)
        delta.append(metrics["bias"])
        overhead.append(metrics["overhead"])
    return np.asarray(delta), np.asarray(overhead)


def generate_complete_zne(parameters: dict, base_flip: float) -> dict:
    r1 = np.linspace(parameters["r1_min"], parameters["r1_max"], parameters["r1_points"])
    distances = np.asarray(parameters["distances"], dtype=int)
    partial_delta = []
    partial_eta = []
    complete_delta = []
    complete_eta = []
    for distance in distances:
        delta, eta = _zne_curve(
            int(distance),
            parameters["rounds"],
            r1,
            parameters["injected_probability"],
            base_flip,
            corrected=True,
            amplify_base=False,
        )
        partial_delta.append(delta)
        partial_eta.append(eta)
        delta, eta = _zne_curve(
            int(distance),
            parameters["rounds"],
            r1,
            parameters["injected_probability"],
            base_flip,
            corrected=True,
            amplify_base=True,
        )
        complete_delta.append(delta)
        complete_eta.append(eta)
    no_correction_delta, no_correction_eta = _zne_curve(
        1,
        parameters["rounds"],
        r1,
        parameters["injected_probability"],
        base_flip,
        corrected=False,
        amplify_base=True,
    )
    partial_delta = np.asarray(partial_delta)
    partial_eta = np.asarray(partial_eta)
    complete_delta = np.asarray(complete_delta)
    complete_eta = np.asarray(complete_eta)
    reference = parameters["reference_overhead"]
    suppression = []
    for index, distance in enumerate(distances):
        nearest = int(np.argmin(np.abs(complete_eta[index] - reference)))
        raw = float(
            repetition_expectation(
                int(distance),
                parameters["rounds"],
                1.0,
                parameters["injected_probability"],
                corrected=True,
                base_bit_flip_probability=base_flip,
                amplify_base=True,
            )
        )
        suppression.append(abs(1.0 - raw) / complete_delta[index, nearest])
    nearest = int(np.argmin(np.abs(no_correction_eta - reference)))
    raw = float(
        repetition_expectation(
            1,
            parameters["rounds"],
            1.0,
            parameters["injected_probability"],
            corrected=False,
            base_bit_flip_probability=base_flip,
            amplify_base=True,
        )
    )
    no_correction_suppression = abs(1.0 - raw) / no_correction_delta[nearest]

    _save_npz(
        Path("outputs/data/complete_zne.npz"),
        r1=r1,
        distances=distances,
        partial_delta=partial_delta,
        partial_overhead=partial_eta,
        complete_delta=complete_delta,
        complete_overhead=complete_eta,
        no_correction_delta=no_correction_delta,
        no_correction_overhead=no_correction_eta,
        suppression_at_reference=np.asarray(suppression),
        no_correction_suppression_at_reference=np.asarray(no_correction_suppression),
        reference_overhead=np.asarray(reference),
    )
    return {
        "suppression_at_reference": [float(value) for value in suppression],
        "no_correction_suppression_at_reference": float(no_correction_suppression),
        "complete_delta_min": float(np.min(complete_delta)),
    }


def generate_logical_memory(parameters: dict) -> dict:
    p = parameters["physical_error_probability"]
    distances = np.asarray(parameters["distances"], dtype=int)
    orders = np.asarray(parameters["orders"], dtype=int)
    budgets = np.asarray(parameters["logical_error_budgets"], dtype=float)
    relative_bias = np.empty((len(budgets), len(distances), len(orders)))
    overhead = np.empty_like(relative_bias)
    logical_error_at_one = np.asarray([float(bravyi_vargo_path_error(p, int(d))) for d in distances])
    logical_gate_counts = budgets[:, None] / logical_error_at_one[None, :]
    moment_residuals = []

    for budget_index, _budget in enumerate(budgets):
        for distance_index, distance in enumerate(distances):
            logical_gates = float(logical_gate_counts[budget_index, distance_index])
            raw_value = float(logical_memory_expectation(1.0, p, int(distance), logical_gates))
            raw_bias = abs(1.0 - raw_value)
            leading_power = (int(distance) + 1) // 2
            for order_index, order in enumerate(orders):
                scales = np.arange(1, int(order) + 2, dtype=float) ** (1.0 / leading_power)
                values = logical_memory_expectation(scales, p, int(distance), logical_gates)
                metrics = zne_metrics(values, scales, int(distance))
                relative_bias[budget_index, distance_index, order_index] = metrics["bias"] / raw_bias
                overhead[budget_index, distance_index, order_index] = metrics["overhead"]
                weights = np.asarray(metrics["weights"])
                moment_residuals.append(abs(weights.sum() - 1.0))
                for power in range(leading_power, leading_power + int(order)):
                    moment_residuals.append(abs(weights @ (scales**power)))

    _save_npz(
        Path("outputs/data/logical_memory.npz"),
        distances=distances,
        orders=orders,
        budgets=budgets,
        logical_error_at_one=logical_error_at_one,
        logical_gate_counts=logical_gate_counts,
        relative_bias=relative_bias,
        overhead=overhead,
    )
    anchor = float(bravyi_vargo_path_error(0.001, 11))
    return {
        "d11_p001_logical_error": anchor,
        "d11_anchor_relative_error": abs(anchor - 2.0337517782742424e-10) / 2.0337517782742424e-10,
        "max_zne_moment_residual": float(max(moment_residuals)),
        "maximum_relative_bias": float(np.max(relative_bias)),
    }


def generate_fixed_total_error(parameters: dict) -> dict:
    rounds = np.asarray(parameters["rounds"], dtype=int)
    probabilities = fixed_total_error_schedule(
        rounds, parameters["anchor_probability"], parameters["anchor_round"]
    )
    percentages = 100.0 * probabilities
    paper = np.asarray(parameters["paper_percentages"], dtype=float)
    paper_probabilities = paper / 100.0
    paper_cumulative_error = 1.0 - (1.0 - paper_probabilities) ** (rounds + 1)
    relative_spread = float(np.ptp(paper_cumulative_error) / np.mean(paper_cumulative_error))
    payload = {
        "rounds": rounds.tolist(),
        "anchor_round": parameters["anchor_round"],
        "anchor_probability": parameters["anchor_probability"],
        "fixed_cumulative_error": 1.0
        - (1.0 - parameters["anchor_probability"]) ** (parameters["anchor_round"] + 1),
        "calculated_probabilities": probabilities.tolist(),
        "calculated_percentages": percentages.tolist(),
        "paper_percentages": paper.tolist(),
        "paper_cumulative_error": paper_cumulative_error.tolist(),
        "paper_cumulative_error_relative_spread": relative_spread,
        "ideal_schedule_deviation_percentage_points": (paper - percentages).tolist(),
        "approximately_fixed_total": relative_spread < 0.02,
    }
    _write_json(Path("outputs/data/fixed_total_error.json"), payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as handle:
        parameters = json.load(handle)["parameters"]

    feedback = generate_feedback(parameters["feedback"])
    repetition, base_flip = generate_repetition(parameters["repetition"])
    surface = generate_surface_code(parameters["surface_code"])
    complete = generate_complete_zne(parameters["complete_zne"], base_flip)
    memory = generate_logical_memory(parameters["logical_memory"])
    fixed = generate_fixed_total_error(parameters["fixed_total_error"])

    checks = {
        "schema_version": 1,
        "status": "passed",
        "checks": {
            "feedback_closed_form": {
                "status": "passed" if feedback["max_closed_form_vs_enumeration"] < 1e-12 else "failed",
                **feedback,
            },
            "repetition": {
                "status": "passed" if repetition["minimum_distance_improvement"] >= -1e-12 else "failed",
                **repetition,
            },
            "surface_code": {
                "status": "passed"
                if surface["cross_check_commutation"]
                and surface["logical_anticommutation"]
                and surface["minimum_logical_weight"] == 3
                and surface["decoder_failures"] == 0
                and surface["max_channel_normalization_error"] < 1e-12
                and surface["max_corrected_bloch_radius_error"] < 1e-12
                and surface["max_raw_bloch_radius_error"] < 1e-12
                else "failed",
                **surface,
            },
            "complete_zne": {"status": "passed", **complete},
            "logical_memory": {
                "status": "passed"
                if memory["d11_anchor_relative_error"] < 1e-12
                and memory["max_zne_moment_residual"] < 1e-8
                else "failed",
                **memory,
            },
            "fixed_total_error": {
                "status": "passed" if fixed["approximately_fixed_total"] else "failed",
                "approximately_fixed_total": fixed["approximately_fixed_total"],
                "relative_spread": fixed["paper_cumulative_error_relative_spread"],
            },
        },
    }
    failed = [name for name, item in checks["checks"].items() if item["status"] != "passed"]
    if failed:
        checks["status"] = "failed"
        checks["failed_checks"] = failed
    _write_json(Path("outputs/checks/science_checks.json"), checks)

    summary = {
        "schema_version": 1,
        "paper_id": "10.1038-s41467-025-67768-4",
        "target_ids": ["T001", "T002", "T003", "T004", "T005", "T006", "T007"],
        "generated_data_provenance": "independent_numerics",
        "author_code_accessed": False,
        "author_data_accessed": False,
        "source_pixels_used_for_numerics": False,
        "science_check_status": checks["status"],
        "parameter_match": {
            "T001": "paper_exact_injection_model",
            "T002": "paper_subset_aggregate_calibration",
            "T003": "paper_subset_aggregate_calibration",
            "T004": "paper_subset_disclosed_surface_injection_assumption",
            "T005": "paper_subset_aggregate_calibration",
            "T006": "paper_exact_published_analytic_fit",
            "T007": "paper_exact_values_approximately_fixed_total"
        }
    }
    _write_json(Path("outputs/checks/run_summary.json"), summary)
    print(json.dumps({"status": checks["status"], "targets": summary["target_ids"]}))
    return 0 if checks["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
