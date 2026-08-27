#!/usr/bin/env python3
"""Recompute Fig. 6 and Appendix Figs. a6-a8 from printed formulas.

This scientific runner reads only case-local code and a frozen configuration.
It does not read the paper PDF, source images, digitized curves, author code or
author numerical arrays.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import coefficients as coeffs  # noqa: E402
import gate  # noqa: E402
import gate_2p  # noqa: E402


def _cz_summary(results: dict[str, object]) -> dict[str, object]:
    phase = gate.conditional_phase(results)
    metric = gate.average_gate_error(results)
    return {
        "conditional_phase_over_pi": phase / np.pi,
        "max_leakage": max(
            float(1.0 - results[key].population[-1])
            for key in ("00", "01", "11")
        ),
        **metric,
    }


def _ccz_summary(results: dict[str, object]) -> dict[str, object]:
    labels = [f"{value:03b}" for value in range(8)]
    amps = np.asarray([results[label].amp_final for label in labels])
    phases = np.asarray([np.angle(value) for value in amps])
    conditional = (
        phases[7]
        - phases[6]
        - phases[5]
        - phases[3]
        + phases[4]
        + phases[2]
        + phases[1]
        - phases[0]
    )
    conditional = float((conditional + np.pi) % (2.0 * np.pi) - np.pi)

    bits = np.asarray([[int(bit) for bit in label] for label in labels])
    ccz = np.ones(8, dtype=complex)
    ccz[-1] = -1.0

    def negative_overlap(angles: np.ndarray) -> float:
        local = np.exp(1j * (bits @ angles))
        return -float(abs(np.vdot(local * ccz, amps)))

    grid = np.linspace(-np.pi, np.pi, 9)
    best = min(
        (negative_overlap(np.asarray([a, b, c])), a, b, c)
        for a in grid
        for b in grid
        for c in grid
    )
    fit = minimize(
        negative_overlap,
        np.asarray(best[1:]),
        method="Nelder-Mead",
        options={"xatol": 1e-9, "fatol": 1e-13},
    )
    overlap = -float(fit.fun)
    trace_uu = float(np.sum(np.abs(amps) ** 2))
    fidelity = (overlap**2 + trace_uu) / (8.0 * 9.0)
    return {
        "conditional_phase_over_pi": conditional / np.pi,
        "max_leakage": max(
            float(1.0 - results[label].population[-1]) for label in labels
        ),
        "f_avg": fidelity,
        "gate_error": 1.0 - fidelity,
        "final_populations": {
            label: float(results[label].population[-1]) for label in labels
        },
    }


def _store_standard(
    arrays: dict[str, np.ndarray],
    name: str,
    results: dict[str, object],
) -> None:
    for sector, result in results.items():
        arrays[f"{name}_{sector}_population"] = result.population
        arrays[f"{name}_{sector}_phase"] = result.phase


def run(config_path: Path, output_root: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "10.1007-s11433-024-2478-8":
        raise ValueError("configuration paper_id mismatch")
    n_out = int(config["time_points"])
    if n_out < 3:
        raise ValueError("time_points must be at least 3")

    arrays: dict[str, np.ndarray] = {}
    time, fig6 = gate_2p.run_three_qubit_active_patterns(
        coeffs.FIG6_TOFFOLI,
        n_out=n_out,
    )
    arrays["time_us"] = time
    for label, result in fig6.items():
        arrays[f"fig6_{label}_population"] = result.population
        arrays[f"fig6_{label}_phase"] = result.phase
    fig6_summary = _ccz_summary(fig6)
    fig6_limits = config["toffoli_acceptance"]
    fig6_summary["scientific_status"] = (
        "passed"
        if abs(abs(fig6_summary["conditional_phase_over_pi"]) - 1.0)
        <= float(fig6_limits["conditional_phase_abs_error_max"])
        and fig6_summary["max_leakage"] <= float(fig6_limits["max_leakage"])
        else "paper_discrepancy_requires_fresh_review"
    )

    protocols: dict[str, dict[str, object]] = {}
    for name in ("a6_hybrid", "a6_amplitude"):
        results = gate.run_protocol(coeffs.SINGLE_PHOTON_PROTOCOLS[name], n_out=n_out)
        _store_standard(arrays, name, results)
        protocols[name] = _cz_summary(results)
    for name in ("a7_hybrid", "a7_amplitude"):
        results = gate_2p.run_protocol(coeffs.TWO_PHOTON_PROTOCOLS[name], n_out=n_out)
        _store_standard(arrays, name, results)
        protocols[name] = _cz_summary(results)
    for name in ("a8_hybrid", "a8_amplitude"):
        results = gate_2p.run_protocol_with_end_coupling(
            coeffs.TWO_PHOTON_PROTOCOLS[name],
            end_coupling_ratio=float(config["a8_end_coupling_ratio"]),
            n_out=n_out,
        )
        _store_standard(arrays, name, results)
        protocols[name] = _cz_summary(results)

    error_limit = float(config["appendix_gate_error_max"])
    for summary in protocols.values():
        summary["scientific_status"] = (
            "passed"
            if summary["gate_error"] <= error_limit
            else "paper_discrepancy_requires_fresh_review"
        )

    target8_status = (
        "passed"
        if all(row["scientific_status"] == "passed" for row in protocols.values())
        else "mixed_requires_fresh_review"
    )
    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "source_boundary": {
            "author_code_used": False,
            "author_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
        },
        "targets": {
            "T007": {"figure": "Main Figure 6", **fig6_summary},
            "T008": {
                "figure": "Appendix Figures a6-a8",
                "scientific_status": target8_status,
                "protocols": protocols,
            },
        },
    }

    data_dir = output_root / "data" / "remaining_targets"
    check_dir = output_root / "checks" / "remaining_targets"
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(data_dir / "trajectories.npz", **arrays)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (data_dir / "targets.json").write_text(text, encoding="utf-8")
    (check_dir / "targets.json").write_text(text, encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", default=Path("outputs"), type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.output_root), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
