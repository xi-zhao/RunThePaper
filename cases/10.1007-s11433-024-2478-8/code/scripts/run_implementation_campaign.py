#!/usr/bin/env python3
"""Validate every numerical target's clean-room executable path.

This command never reads ``raw/``, reference figures, digitized curves, author
arrays, or author code.  Published protocols exercise the case-local
Hamiltonian builders.  Targets whose indispensable inputs are absent emit a
machine-readable blocked artifact and an exact input schema; supplying that
schema activates the same numerical Hamiltonian path without changing code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

import coefficients as coeffs  # noqa: E402
import hamiltonians as h1  # noqa: E402
import hamiltonians_2p as h2  # noqa: E402
from waveforms import FourierWaveform, TWO_PI  # noqa: E402


TARGET_IDS = tuple(f"T{index:03d}" for index in range(1, 9))


def _scalar(function, time_us: float) -> float:
    return float(np.asarray(function(time_us)))


def _matrix_check(matrix: np.ndarray) -> dict[str, object]:
    return {
        "dimension": int(matrix.shape[0]),
        "hermitian_residual": float(np.max(np.abs(matrix - matrix.conj().T))),
        "finite": bool(np.isfinite(matrix).all()),
    }


def _single_photon_kernel(protocol_name: str, times: list[float]) -> dict[str, object]:
    protocol = coeffs.SINGLE_PHOTON_PROTOCOLS[protocol_name]
    checks: list[dict[str, object]] = []
    for time_us in times:
        omega1 = _scalar(protocol.omega1, time_us)
        omega2 = _scalar(protocol.omega2, time_us)
        delta1 = _scalar(protocol.delta1, time_us)
        delta2 = _scalar(protocol.delta2, time_us)
        blockade = TWO_PI * protocol.B_mhz
        penalty = TWO_PI * protocol.delta_q_mhz
        matrices = {
            "00": h1.h_sector00(omega1, delta1),
            "01": h1.h_sector01(omega1, omega2, delta1, delta2, blockade, penalty),
            "11": h1.h_sector11(omega1, omega2, delta1, delta2, blockade, penalty),
        }
        checks.append(
            {
                "time_us": time_us,
                "waveforms_rad_per_us": {
                    "omega1": omega1,
                    "omega2": omega2,
                    "delta1": delta1,
                    "delta2": delta2,
                },
                "sectors": {name: _matrix_check(matrix) for name, matrix in matrices.items()},
            }
        )
    return {
        "status": "passed",
        "protocol": protocol_name,
        "source": protocol.source,
        "kernel_checks": checks,
        "paper_scale_entrypoints": [
            "scripts/run_fig3.py",
            "scripts/run_fig5.py",
            "scripts/run_fig7.py",
        ],
    }


def _two_photon_kernel(protocol_name: str, times: list[float]) -> dict[str, object]:
    protocol = coeffs.TWO_PHOTON_PROTOCOLS[protocol_name]
    checks: list[dict[str, object]] = []
    for time_us in times:
        params = {
            "omega1p": _scalar(protocol.omega1p, time_us),
            "omega1s": protocol.omega1s,
            "omega2p": _scalar(protocol.omega2p, time_us),
            "omega2s": protocol.omega2s,
            "delta1": _scalar(protocol.delta1, time_us),
            "delta2": _scalar(protocol.delta2, time_us),
            "delta_0": TWO_PI * protocol.delta0_mhz,
            "B": TWO_PI * protocol.B_mhz,
            "delta_q": TWO_PI * protocol.delta_q_mhz,
        }
        sectors = {
            name: h2.build_sector(spec["n"], spec["roles"], spec["adjacency"], params)
            for name, spec in h2.SECTORS.items()
        }
        checks.append(
            {
                "time_us": time_us,
                "sectors": {name: _matrix_check(matrix) for name, matrix in sectors.items()},
            }
        )
    return {
        "status": "passed",
        "protocol": protocol_name,
        "source": protocol.source,
        "kernel_checks": checks,
        "paper_scale_entrypoints": ["scripts/run_fig4.py"],
    }


def _required_number(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _required_coefficients(payload: dict[str, object], key: str) -> tuple[float, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, (int, float)) for item in value):
        raise ValueError(f"{key} must be a non-empty numeric list")
    return tuple(float(item) for item in value)


def _four_atom_kernel(payload: dict[str, object], times: list[float]) -> dict[str, object]:
    roles = payload.get("roles")
    adjacency = payload.get("adjacency")
    if not isinstance(roles, list) or len(roles) != 4 or any(role not in {"buffer", "qubit"} for role in roles):
        raise ValueError("roles must contain four buffer/qubit entries")
    if not isinstance(adjacency, list) or not adjacency:
        raise ValueError("adjacency must be a non-empty pair list")
    pairs: list[tuple[int, int]] = []
    for pair in adjacency:
        if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(index, int) for index in pair):
            raise ValueError("each adjacency edge must contain two integer indices")
        if min(pair) < 0 or max(pair) >= 4 or pair[0] == pair[1]:
            raise ValueError("adjacency indices must name two distinct four-atom sites")
        pairs.append((pair[0], pair[1]))
    functions = {
        "omega1p": FourierWaveform(_required_coefficients(payload, "omega1p_coefficients_mhz")),
        "omega2p": FourierWaveform(_required_coefficients(payload, "omega2p_coefficients_mhz")),
        "delta1": FourierWaveform(_required_coefficients(payload, "delta1_coefficients_mhz")),
        "delta2": FourierWaveform(_required_coefficients(payload, "delta2_coefficients_mhz")),
    }
    checks = []
    for time_us in times:
        params = {
            "omega1p": _scalar(functions["omega1p"], time_us),
            "omega1s": TWO_PI * _required_number(payload, "omega1s_mhz"),
            "omega2p": _scalar(functions["omega2p"], time_us),
            "omega2s": TWO_PI * _required_number(payload, "omega2s_mhz"),
            "delta1": _scalar(functions["delta1"], time_us),
            "delta2": _scalar(functions["delta2"], time_us),
            "delta_0": TWO_PI * _required_number(payload, "delta0_mhz"),
            "B": TWO_PI * _required_number(payload, "B_mhz"),
            "delta_q": TWO_PI * _required_number(payload, "delta_q_mhz"),
        }
        checks.append({"time_us": time_us, **_matrix_check(h2.build_sector(4, roles, pairs, params))})
    return {"status": "passed", "kernel_checks": checks, "scientific_acceptance": "not_claimed"}


def _b100_kernel(payload: dict[str, object], times: list[float]) -> dict[str, object]:
    waveforms = {
        key: FourierWaveform(_required_coefficients(payload, key))
        for key in (
            "omega1_coefficients_mhz",
            "omega2_coefficients_mhz",
            "delta1_coefficients_mhz",
            "delta2_coefficients_mhz",
        )
    }
    checks = []
    for time_us in times:
        omega1 = _scalar(waveforms["omega1_coefficients_mhz"], time_us)
        omega2 = _scalar(waveforms["omega2_coefficients_mhz"], time_us)
        delta1 = _scalar(waveforms["delta1_coefficients_mhz"], time_us)
        delta2 = _scalar(waveforms["delta2_coefficients_mhz"], time_us)
        blockade = TWO_PI * _required_number(payload, "B_mhz")
        penalty = TWO_PI * _required_number(payload, "delta_q_mhz")
        checks.append(
            {
                "time_us": time_us,
                "sectors": {
                    "00": _matrix_check(h1.h_sector00(omega1, delta1)),
                    "01": _matrix_check(h1.h_sector01(omega1, omega2, delta1, delta2, blockade, penalty)),
                    "11": _matrix_check(h1.h_sector11(omega1, omega2, delta1, delta2, blockade, penalty)),
                },
            }
        )
    return {"status": "passed", "kernel_checks": checks, "scientific_acceptance": "not_claimed"}


def run(config_path: Path, output_root: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("paper_id") != "10.1007-s11433-024-2478-8":
        raise ValueError("configuration paper_id mismatch")
    times = config.get("sample_times_us")
    if not isinstance(times, list) or not times or not all(isinstance(value, (int, float)) for value in times):
        raise ValueError("sample_times_us must be a non-empty numeric list")
    sample_times = [float(value) for value in times]
    results: dict[str, dict[str, object]] = {}
    for target_id, protocol_name in config["single_photon_protocols"].items():
        results[target_id] = _single_photon_kernel(protocol_name, sample_times)
    for target_id, protocol_name in config["two_photon_protocols"].items():
        results[target_id] = _two_photon_kernel(protocol_name, sample_times)
    missing = config.get("missing_input_targets", {})
    for target_id in ("T007", "T008"):
        declaration = missing[target_id]
        payload = declaration.get("input")
        if payload is None:
            results[target_id] = {
                "status": "blocked_missing_input",
                "required_schema": declaration["required_schema"],
                "scientific_acceptance": "not_claimed",
            }
        elif not isinstance(payload, dict):
            raise ValueError(f"{target_id}.input must be an object or null")
        elif target_id == "T007":
            results[target_id] = _four_atom_kernel(payload, sample_times)
        else:
            results[target_id] = _b100_kernel(payload, sample_times)
    if set(results) != set(TARGET_IDS):
        raise ValueError("campaign must produce exactly T001--T008")

    data_dir = output_root / "data" / "implementation_validation"
    check_dir = output_root / "checks" / "implementation_validation"
    data_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)
    for target_id, payload in sorted(results.items()):
        document = {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "target_id": target_id,
            "artifact_stage": "implementation_validation",
            "generated_data_provenance": "independent_numerics",
            "scientific_acceptance": "not_claimed",
            **payload,
        }
        text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        (data_dir / f"{target_id.lower()}.json").write_text(text, encoding="utf-8")
        (check_dir / f"{target_id.lower()}.json").write_text(text, encoding="utf-8")
    summary = {
        "paper_id": config["paper_id"],
        "targets": len(results),
        "passed": sum(row["status"] == "passed" for row in results.values()),
        "blocked_missing_input": sum(row["status"] == "blocked_missing_input" for row in results.values()),
        "scientific_acceptance": "not_claimed",
    }
    (check_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", default=Path("outputs"), type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.output_root), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
