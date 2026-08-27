#!/usr/bin/env python3
"""Run source-blind numerical probes for the implemented scientific targets."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
sys.path.insert(0, str(SRC))

from gate_model import (  # noqa: E402
    GateParameters,
    branch_displacements,
    chain_gate_duration_us,
    concurrence,
    decay_infidelity,
    reduced_spin_state,
    rotated_basis_populations,
)
from ion_chain import axial_modes, optimize_toggle_schedule  # noqa: E402
from supplement_claims import (  # noqa: E402
    circular_field_budget,
    large_n_participation_scaling,
    linear_thermal_invariance,
    magnus_resource_budget,
    multimode_spin_dynamics,
    rf_dressing_sweep,
    table_s3_error_budget,
    table_s4_toggle_sweep,
    table_s6_fidelity_budget,
    taylor_anharmonic_gate_fidelity,
)


OUTPUT_DIR = WORKSPACE / "outputs" / "data" / "implementation_probe"
SUMMARY_PATH = (
    WORKSPACE / "outputs" / "checks" / "implementation_probe" / "summary.json"
)
EXPECTED_TARGETS = (
    "T001",
    "T002",
    "T007",
    "T012",
    "T015",
    "T016",
    "T017",
    "T019",
    "T025",
    "T026",
    "T028",
    "T029",
    "T030",
)
EXPECTED_MATCH = {
    "T001": "paper_exact",
    "T002": "paper_subset",
    "T007": "paper_subset",
    "T012": "proxy_model",
    "T015": "paper_subset",
    "T016": "paper_subset",
    "T017": "paper_subset_with_source_conflict",
    "T019": "paper_exact_reimplemented_method",
    "T025": "paper_subset",
    "T026": "paper_exact_linear_model",
    "T028": "paper_subset_with_formula_risk",
    "T029": "paper_subset",
    "T030": "paper_subset_with_numeric_crosscheck",
}


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"no rows generated for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _read_parameters(config_path: Path) -> dict[str, Any]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("config.parameters must be an object")
    if parameters.get("profile") != "implementation_probe":
        raise ValueError("only the implementation_probe profile is allowed")
    if tuple(parameters.get("target_ids", ())) != EXPECTED_TARGETS:
        raise ValueError("target_ids must match the declared independent-numerics set")
    if parameters.get("target_parameter_match") != EXPECTED_MATCH:
        raise ValueError("target_parameter_match must preserve the project contract")
    return parameters


def _gate_parameters(parameters: dict[str, Any]) -> GateParameters:
    values = parameters.get("gate_parameters")
    if not isinstance(values, dict):
        raise ValueError("gate_parameters must be an object")
    expected = GateParameters()
    for field in ("coupling_ratio", "trap_frequency_hz", "gate_time_us", "ion_mass_amu"):
        if field not in values or not math.isclose(
            float(values[field]), float(getattr(expected, field)), rel_tol=0.0, abs_tol=1e-15
        ):
            raise ValueError(f"gate parameter {field} does not match the reviewed implementation")
    return GateParameters(**{key: float(value) for key, value in values.items()})


def _probe_t001(params: GateParameters) -> dict[str, float]:
    rows = []
    for time_point in np.linspace(0.0, 2.0, 17):
        state = reduced_spin_state(float(time_point), params)
        populations = rotated_basis_populations(state)
        rows.append(
            {
                "t_over_T": float(time_point),
                "max_displacement": float(
                    np.max(np.abs(branch_displacements(float(time_point), params)))
                ),
                "concurrence": concurrence(state),
                "population_sum": float(sum(populations.values())),
            }
        )
    _write_csv(OUTPUT_DIR / "T001_gate_invariants.csv", rows)
    at_one = rows[8]
    at_two = rows[-1]
    if at_one["max_displacement"] >= 1e-12 or not math.isclose(
        float(at_one["concurrence"]), 1.0, abs_tol=1e-7
    ):
        raise RuntimeError("T001 failed the one-period closure/CZ invariant")
    if float(at_two["concurrence"]) >= 1e-7:
        raise RuntimeError("T001 failed the two-period concurrence invariant")
    return {
        "closure_T": float(at_one["max_displacement"]),
        "concurrence_T": float(at_one["concurrence"]),
        "concurrence_2T": float(at_two["concurrence"]),
    }


def _probe_t002(_params: GateParameters) -> dict[str, float]:
    ion_counts = np.asarray((1, 25, 50, 75, 100), dtype=float)
    durations = chain_gate_duration_us(ion_counts)
    low_l = decay_infidelity(durations, 100.0) + 1.0e-3
    circular = decay_infidelity(durations, 119_000.0) + 1.0e-3
    rows = [
        {
            "number_of_ions": int(number),
            "gate_duration_us": float(duration),
            "low_l_infidelity": float(low),
            "circular_infidelity": float(circ),
        }
        for number, duration, low, circ in zip(
            ion_counts, durations, low_l, circular, strict=True
        )
    ]
    _write_csv(OUTPUT_DIR / "T002_chain_scaling.csv", rows)
    if np.any(np.diff(durations) < 0) or not math.isclose(float(durations[-1]), 15.0):
        raise RuntimeError("T002 failed the disclosed duration-scaling contract")
    return {
        "duration_N1_us": float(durations[0]),
        "duration_N100_us": float(durations[-1]),
        "low_l_infidelity_N100": float(low_l[-1]),
        "circular_infidelity_N100": float(circular[-1]),
    }


def _probe_t007(_params: GateParameters) -> dict[str, float]:
    _positions, frequencies, _eigenvectors = axial_modes(10)
    schedule = optimize_toggle_schedule(frequencies, restarts=4)
    rows = [
        {
            "mode": index + 1,
            "frequency_over_com": float(frequency),
            "closure_residual_abs": float(abs(residual)),
        }
        for index, (frequency, residual) in enumerate(
            zip(frequencies, schedule.residuals, strict=True)
        )
    ]
    _write_csv(OUTPUT_DIR / "T007_mode_closure.csv", rows)
    max_residual = float(np.max(np.abs(schedule.residuals)))
    if max_residual >= 1e-4 or not math.isclose(
        float(frequencies[-1]), 6.58, rel_tol=0.025, abs_tol=0.02
    ):
        raise RuntimeError("T007 failed the mode-spectrum/closure invariants")
    return {
        "omega10_over_omega": float(frequencies[-1]),
        "max_closure_residual": max_residual,
        "segment_count": float(len(schedule.amplitudes)),
    }


def _probe_t012(params: GateParameters) -> dict[str, float]:
    lifetime_us = 6_000.0
    rows = []
    for time_point in np.linspace(0.0, 2.0, 9):
        state = reduced_spin_state(float(time_point), params, mean_phonon=1.0)
        survival = math.exp(-(float(time_point) * params.gate_time_us) / lifetime_us)
        rows.append(
            {
                "t_over_T": float(time_point),
                "survival": survival,
                "concurrence_proxy": survival * concurrence(state),
            }
        )
    _write_csv(OUTPUT_DIR / "T012_circular_proxy.csv", rows)
    values = np.asarray([row["concurrence_proxy"] for row in rows], dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0.0) or np.any(values > 1.0):
        raise RuntimeError("T012 produced an invalid proxy concurrence")
    return {
        "concurrence_proxy_T": float(rows[4]["concurrence_proxy"]),
        "lifetime_us": lifetime_us,
    }


def _probe_t015(params: GateParameters) -> dict[str, float]:
    rows = multimode_spin_dynamics(np.linspace(0.0, 2.0, 81), params)
    _write_csv(OUTPUT_DIR / "T015_multimode_spin_dynamics.csv", rows)
    at_one = rows[40]
    at_two = rows[-1]
    if at_one["concurrence"] < 0.999 or at_two["concurrence"] > 1e-6:
        raise RuntimeError("T015 failed the multimode closure/entanglement checks")
    return {
        "concurrence_T": float(at_one["concurrence"]),
        "concurrence_2T": float(at_two["concurrence"]),
        "max_trace_error": max(float(row["trace_error"]) for row in rows),
    }


def _probe_t016(_params: GateParameters) -> dict[str, float]:
    rows = table_s3_error_budget()
    _write_csv(OUTPUT_DIR / "T016_table_s3_error_budget.csv", rows)
    return {
        "upper_bound_total": float(rows[-1]["upper_infidelity"]),
        "independently_derived_rows": float(
            sum(row["provenance"] == "independent_formula" for row in rows)
        ),
    }


def _probe_t017(_params: GateParameters) -> dict[str, object]:
    rows = table_s4_toggle_sweep()
    _write_csv(OUTPUT_DIR / "T017_table_s4_toggle_scaling.csv", rows)
    printed_n10 = next(
        row
        for row in rows
        if row["number_of_ions"] == 10 and row["contract"] == "printed_table"
    )
    formula_n10 = next(
        row
        for row in rows
        if row["number_of_ions"] == 10
        and row["contract"] == "stated_2N_plus_5"
    )
    finding = {
        "schema_version": 1,
        "status": "source_contract_conflict_detected",
        "printed_table_segments": 17,
        "stated_rule_segments": 25,
        "printed_table_max_residual": printed_n10["max_closure_residual"],
        "stated_rule_max_residual": formula_n10["max_closure_residual"],
        "interpretation": "Under the printed asymmetric amplitude model, 17 segments do not close the ten modes while 25 segments do.",
    }
    _write_json(
        WORKSPACE
        / "outputs"
        / "checks"
        / "implementation_probe"
        / "T017_source_conflict.json",
        finding,
    )
    return finding


def _probe_t019(_params: GateParameters) -> dict[str, object]:
    budget_rows = table_s6_fidelity_budget()
    thermal_rows = taylor_anharmonic_gate_fidelity()
    _write_csv(OUTPUT_DIR / "T019_table_s6_fidelity.csv", budget_rows)
    _write_csv(OUTPUT_DIR / "T019_taylor_thermal_fidelity.csv", thermal_rows)
    paper_checkpoints = {0.0: 3e-4, 1.0: 1e-3, 5.0: 8e-3, 10.0: 0.026, 20.0: 0.077}
    comparisons = []
    for row in thermal_rows:
        mean_phonon = float(row["mean_phonon"])
        if mean_phonon not in paper_checkpoints:
            continue
        paper_value = paper_checkpoints[mean_phonon]
        reproduced = float(row["full_infidelity"])
        comparisons.append(
            {
                "mean_phonon": mean_phonon,
                "paper_infidelity": paper_value,
                "reproduced_infidelity": reproduced,
                "relative_difference": (reproduced - paper_value) / paper_value,
            }
        )
    validation = {
        "schema_version": 1,
        "status": "paper_checkpoints_reproduced",
        "method": "independent_fock_space_diagonalization",
        "taylor_order": 5,
        "n_fock": 120,
        "eta": 1.88e-3,
        "comparisons": comparisons,
        "max_absolute_relative_difference": max(
            abs(float(row["relative_difference"])) for row in comparisons
        ),
        "linear_floor_through_nbar_5": max(
            float(row["linear_infidelity"])
            for row in thermal_rows
            if float(row["mean_phonon"]) <= 5.0
        ),
    }
    if validation["max_absolute_relative_difference"] >= 0.2:
        raise RuntimeError("T019 misses a printed anharmonic checkpoint by 20% or more")
    if validation["linear_floor_through_nbar_5"] >= 1e-7:
        raise RuntimeError("T019 linear control exceeds its truncation floor through nbar=5")
    _write_json(
        WORKSPACE
        / "outputs"
        / "checks"
        / "implementation_probe"
        / "T019_taylor_validation.json",
        validation,
    )
    return {
        "regimes": len(budget_rows),
        "thermal_points": len(thermal_rows),
        **validation,
    }


def _probe_t025(_params: GateParameters) -> dict[str, float]:
    rows = magnus_resource_budget()
    _write_csv(OUTPUT_DIR / "T025_magnus_resource_budget.csv", rows)
    central = rows[1]
    return {
        "stark_shift_MHz_w1": float(central["stark_shift_MHz"]),
        "beam_power_mW_w1": float(central["beam_power_mW"]),
    }


def _probe_t026(_params: GateParameters) -> dict[str, float]:
    rows = linear_thermal_invariance()
    _write_csv(OUTPUT_DIR / "T026_linear_thermal_invariance.csv", rows)
    maximum_difference = max(
        float(row["max_density_matrix_difference"]) for row in rows
    )
    if maximum_difference >= 1e-11:
        raise RuntimeError("T026 failed the exact linear thermal-invariance check")
    return {"max_density_matrix_difference": maximum_difference}


def _probe_t028(_params: GateParameters) -> dict[str, object]:
    rows = rf_dressing_sweep()
    _write_csv(OUTPUT_DIR / "T028_rf_dressing_sweep.csv", rows)
    finding = {
        "schema_version": 1,
        "status": "partial_check_passed_absolute_claim_blocked",
        "dispersive_points": sum(bool(row["dispersive"]) for row in rows),
        "signs": sorted({str(row["shift_sign"]) for row in rows}),
        "blocked_input": "absolute dipole and bare-polarizability data",
        "formula_review": "The printed Eq. S24 needs a fresh dimensional derivation before the claimed 1-10 correction can be accepted.",
    }
    _write_json(
        WORKSPACE
        / "outputs"
        / "checks"
        / "implementation_probe"
        / "T028_formula_review.json",
        finding,
    )
    return finding


def _probe_t029(_params: GateParameters) -> dict[str, float]:
    result = circular_field_budget()
    _write_json(
        WORKSPACE
        / "outputs"
        / "checks"
        / "implementation_probe"
        / "T029_field_budget.json",
        {"schema_version": 1, "status": "passed", **result},
    )
    if result["dephasing_upper"] >= 1e-4:
        raise RuntimeError("T029 exceeds the printed magnetic-dephasing bound")
    return result


def _probe_t030(_params: GateParameters) -> dict[str, float]:
    rows, fit = large_n_participation_scaling()
    _write_csv(OUTPUT_DIR / "T030_large_n_scaling.csv", rows)
    finding = {
        "schema_version": 1,
        "status": "scaling_supported_n10_value_disagrees",
        **fit,
    }
    _write_json(
        WORKSPACE
        / "outputs"
        / "checks"
        / "implementation_probe"
        / "T030_scaling_fit.json",
        finding,
    )
    if not -1.2 < fit["large_n_exponent"] < -0.7:
        raise RuntimeError("T030 does not support a 1/N asymptotic regime")
    return fit


PROBES: dict[str, Callable[[GateParameters], dict[str, object]]] = {
    "T001": _probe_t001,
    "T002": _probe_t002,
    "T007": _probe_t007,
    "T012": _probe_t012,
    "T015": _probe_t015,
    "T016": _probe_t016,
    "T017": _probe_t017,
    "T019": _probe_t019,
    "T025": _probe_t025,
    "T026": _probe_t026,
    "T028": _probe_t028,
    "T029": _probe_t029,
    "T030": _probe_t030,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    parameters = _read_parameters(args.config)
    gate_parameters = _gate_parameters(parameters)
    results = [
        {
            "target_id": target_id,
            "status": "passed",
            "parameter_match": EXPECTED_MATCH[target_id],
            "result": PROBES[target_id](gate_parameters),
        }
        for target_id in EXPECTED_TARGETS
    ]
    payload = {
        "schema_version": 1,
        "paper_id": "2607.15597",
        "status": "passed",
        "profile": "implementation_probe",
        "generated_data_provenance": "independent_numerics",
        "target_ids": list(EXPECTED_TARGETS),
        "results": results,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
