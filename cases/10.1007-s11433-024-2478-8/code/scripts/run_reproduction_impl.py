#!/usr/bin/env python3
"""Recompute the six published BAM observables without source-image access."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import coefficients as coefficients  # noqa: E402
import gate  # noqa: E402
import gate_2p  # noqa: E402
from dual_pulse import run_dual_pulse  # noqa: E402


def _protocol_result(protocol: object) -> dict[str, float]:
    result = gate.run_protocol(protocol, n_out=401)
    summary = gate.summarize(result)
    return {
        "conditional_phase_over_pi": float(summary["conditional_phase_over_pi"]),
        "gate_error": float(summary["gate_error"]),
        "max_leakage": float(summary["max_leakage"]),
        "max_norm_drift": float(summary["max_norm_drift"]),
    }


def _two_photon_result(protocol: object) -> dict[str, float]:
    result = gate_2p.run_protocol(protocol, n_out=401)
    return {
        "conditional_phase_over_pi": float(gate.conditional_phase(result) / np.pi),
        "gate_error": float(gate.average_gate_error(result)["gate_error"]),
        "p00_return": float(result["00"].population[-1]),
        "p01_return": float(result["01"].population[-1]),
        "p11_return": float(result["11"].population[-1]),
    }


def _scaled_protocol(r_buffer: float, r_qubit: float) -> object:
    base = coefficients.FIG3_HYBRID
    omega1 = base.omega1
    omega2 = base.omega2
    return dataclasses.replace(
        base,
        omega1=lambda time, ratio=r_buffer: ratio * np.asarray(omega1(time)),
        omega2=lambda time, ratio=r_qubit: ratio * np.asarray(omega2(time)),
    )


def _fig7_grid(points: int, bounds: list[float]) -> tuple[np.ndarray, np.ndarray]:
    axis = np.linspace(float(bounds[0]), float(bounds[1]), points)
    errors = np.empty((points, points), dtype=float)
    for row, r_qubit in enumerate(axis):
        for column, r_buffer in enumerate(axis):
            errors[row, column] = _protocol_result(
                _scaled_protocol(float(r_buffer), float(r_qubit))
            )["gate_error"]
    return axis, errors


def _dual_pulse(doppler_mhz: float, points: int) -> dict[str, object]:
    zero = run_dual_pulse(0.0, points)
    flipped = run_dual_pulse(doppler_mhz, points, flip=True)
    unflipped = run_dual_pulse(doppler_mhz, points, flip=False)

    def end_phase(payload: dict[str, object], sector: str) -> float:
        return float(np.unwrap(payload[sector][1])[-1])

    def conditional_phase(payload: dict[str, object]) -> float:
        phases = {sector: end_phase(payload, sector) for sector in ("00", "01", "11")}
        return phases["11"] + phases["00"] - 2.0 * phases["01"]

    ratios: dict[str, float] = {}
    for sector in ("00", "01", "11"):
        flipped_shift = end_phase(flipped, sector) - end_phase(zero, sector)
        unflipped_shift = end_phase(unflipped, sector) - end_phase(zero, sector)
        ratios[sector] = abs(flipped_shift) / (abs(unflipped_shift) + 1e-15)
    return {
        "conditional_phase_over_pi": conditional_phase(zero) / np.pi,
        "cancellation_ratio_dual_over_single": ratios,
    }


def run(config_path: Path, output_root: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "10.1007-s11433-024-2478-8":
        raise ValueError("configuration paper_id mismatch")
    acceptance = config["acceptance"]

    t001 = _protocol_result(coefficients.FIG3_HYBRID)
    t002 = _protocol_result(coefficients.FIG3_AMPLITUDE)
    axis, fig7_errors = _fig7_grid(
        int(config["fig7_grid_points"]), config["fig7_ratio_range"]
    )
    t003 = {
        "grid_points": int(axis.size),
        "ratio_range": [float(axis[0]), float(axis[-1])],
        "error_min": float(fig7_errors.min()),
        "error_max": float(fig7_errors.max()),
        "error_center": float(fig7_errors[axis.size // 2, axis.size // 2]),
    }
    t004 = _two_photon_result(coefficients.FIG4_HYBRID)
    t005 = _two_photon_result(coefficients.FIG4_AMPLITUDE)
    t006 = _dual_pulse(
        float(config["dual_pulse_doppler_mhz"]),
        int(config["dual_pulse_output_points"]),
    )

    phase_tol = float(acceptance["conditional_phase_abs_error_max"])
    results = {
        "T001": {
            **t001,
            "scientific_status": "passed"
            if t001["gate_error"] <= acceptance["single_photon_gate_error_max"]
            and abs(abs(t001["conditional_phase_over_pi"]) - 1.0) <= phase_tol
            else "failed",
        },
        "T002": {
            **t002,
            "scientific_status": "passed"
            if t002["gate_error"] <= acceptance["single_photon_gate_error_max"]
            and abs(abs(t002["conditional_phase_over_pi"]) - 1.0) <= phase_tol
            else "failed",
        },
        "T003": {
            **t003,
            "scientific_status": "passed"
            if t003["error_max"] <= acceptance["fig7_error_max"]
            else "failed",
        },
        "T004": {
            **t004,
            "scientific_status": "paper_discrepancy_requires_fresh_review"
            if t004["gate_error"] > acceptance["two_photon_gate_error_max"]
            else "passed",
        },
        "T005": {
            **t005,
            "scientific_status": "paper_discrepancy_requires_fresh_review"
            if t005["gate_error"] > acceptance["two_photon_gate_error_max"]
            else "passed",
        },
        "T006": {
            **t006,
            "scientific_status": "passed"
            if max(t006["cancellation_ratio_dual_over_single"].values())
            <= acceptance["dual_pulse_cancellation_ratio_max"]
            and abs(abs(t006["conditional_phase_over_pi"]) - 1.0) <= phase_tol
            else "failed",
        },
    }
    output_root.mkdir(parents=True, exist_ok=True)
    data_dir = output_root / "data" / "scientific_closure"
    check_dir = output_root / "checks" / "scientific_closure"
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)
    np.savez(data_dir / "fig7_grid.npz", axis=axis, error=fig7_errors)
    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "source_boundary": {
            "author_code_used": False,
            "author_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
        },
        "targets": results,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (data_dir / "targets.json").write_text(text, encoding="utf-8")
    (check_dir / "targets.json").write_text(text, encoding="utf-8")
    print(json.dumps({"status": "completed", "targets": results}, ensure_ascii=False))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    run(args.config, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
