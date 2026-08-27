#!/usr/bin/env python3
"""Evaluate the paper's three-level inactive-side Doob realization."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantum_jumps.doob import (  # noqa: E402
    doob_similarity_superoperator,
    mapped_lindblad_model,
    rank_one_jump_basis,
)
from quantum_jumps.liouvillian import (  # noqa: E402
    dominant_eigenpair,
    lindblad_superoperator,
    trace_preservation_residual,
)
from quantum_jumps.models import QuantumJumpModel, three_level_model  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    return parser.parse_args()


def mapped_observables(model: QuantumJumpModel, bias: float) -> dict[str, float]:
    mapped = mapped_lindblad_model(model, bias)
    generator = lindblad_superoperator(mapped.hamiltonian, mapped.jumps)
    expected, theta, _ = doob_similarity_superoperator(model, bias)
    basis = rank_one_jump_basis(mapped.jumps[mapped.counted_jump])
    hamiltonian = basis.conj().T @ mapped.hamiltonian @ basis
    steady_state = dominant_eigenpair(generator).right_matrix
    jump = mapped.jumps[mapped.counted_jump]
    emission_rate = float(np.trace(jump.conj().T @ jump @ steady_state).real)

    extra_drive = float(abs(hamiltonian[1, 2]))
    return {
        "s": float(bias),
        "theta": float(theta.real),
        "generator_reconstruction_residual": float(np.linalg.norm(generator - expected)),
        "trace_preservation_residual": trace_preservation_residual(generator),
        "primary_drive_01": float(abs(hamiltonian[0, 1])),
        "weak_drive_02": float(abs(hamiltonian[0, 2])),
        "additional_drive_12": extra_drive,
        # The |1~>-|2~> coupling dresses |1~> into a doublet displaced by
        # +/-|H12|.  This is the paper's effective detuning mechanism; it is
        # not represented as an invented diagonal energy shift.
        "nearest_dressed_detuning_01": extra_drive,
        "emission_rate": emission_rate,
    }


def check(name: str, value: float, threshold: float, relation: str) -> dict[str, object]:
    if relation == "max":
        passed = value <= threshold
    elif relation == "min":
        passed = value >= threshold
    else:
        raise ValueError(f"unsupported relation: {relation}")
    return {
        "name": name,
        "value": value,
        "relation": relation,
        "threshold": threshold,
        "passed": bool(passed),
    }


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text())
    parameters = config["parameters"]
    tolerances = config["tolerances"]
    model = three_level_model(
        omega_1=float(parameters["omega_1"]),
        omega_2=float(parameters["omega_2"]),
        kappa_1=float(parameters["kappa_1"]),
    )
    rows = [mapped_observables(model, float(s)) for s in parameters["biases"]]
    by_bias = {row["s"]: row for row in rows}
    zero = by_bias[0.0]
    acceptance = by_bias[float(parameters["acceptance_bias"])]
    drive_ratio = acceptance["additional_drive_12"] / float(parameters["omega_2"])
    emission_ratio = acceptance["emission_rate"] / zero["emission_rate"]

    checks = [
        check(
            "explicit operators reconstruct Doob generator",
            max(row["generator_reconstruction_residual"] for row in rows),
            float(tolerances["generator_reconstruction_absolute"]),
            "max",
        ),
        check(
            "mapped generators preserve trace",
            max(row["trace_preservation_residual"] for row in rows),
            float(tolerances["trace_preservation_absolute"]),
            "max",
        ),
        check(
            "unbiased model has no |1~>-|2~> drive",
            zero["additional_drive_12"],
            float(tolerances["zero_bias_extra_drive_absolute"]),
            "max",
        ),
        check(
            "inactive mapping adds a drive stronger than original Omega_2",
            drive_ratio,
            float(tolerances["extra_drive_over_omega_2_minimum"]),
            "min",
        ),
        check(
            "inactive mapping suppresses steady photon emission",
            emission_ratio,
            float(tolerances["emission_rate_ratio_maximum"]),
            "max",
        ),
    ]

    data_path = args.output_root / "data" / "T012_three_level_doob_mapping.csv"
    check_path = args.output_root / "checks" / "T012_three_level_doob_mapping.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "schema_version": 1,
        "target_id": "T012",
        "claim": "The inactive three-level Doob realization adds a |1~>-|2~> drive whose dressed-state splitting suppresses photon emission.",
        "method": {
            "formula": "paper Eqs. (10)-(11)",
            "basis": "SVD canonical basis of the independently derived rank-one mapped jump",
            "source_code_policy": "No author numerical code or arrays used",
        },
        "parameters": parameters,
        "derived_ratios_at_acceptance_bias": {
            "additional_drive_over_original_omega_2": drive_ratio,
            "emission_rate_over_unbiased": emission_ratio,
        },
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
        "rows": rows,
    }
    check_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["derived_ratios_at_acceptance_bias"], indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
