"""Run both paper-exact Casimir targets in one isolated process."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

import reproduce


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def _validate_config(parameters: dict) -> None:
    if tuple(float(value) for value in parameters["model"]["m0_values"]) != reproduce.MASSES:
        raise ValueError("paper mass grid does not match the implemented model grid")
    expected_axes = {
        "alpha0_left_axis": [0.0, 30.0, 301],
        "alpha0_right_axis": [0.1, 12.0, 240],
    }
    for key, expected in expected_axes.items():
        if parameters["T001"][key] != expected:
            raise ValueError(f"T001 {key} does not match the paper-exact implementation")
    if parameters["T002"]["alpha0_axis"] != [0.1, 25.0, 250]:
        raise ValueError("T002 alpha0 axis does not match the paper-exact implementation")


def _run_phase(target: str, phase: str) -> dict:
    os.environ["PRAGENT_GUARDED_TARGET_ID"] = target
    os.environ["PRAGENT_GUARDED_STAGE"] = "final_reproduction"
    reproduce.require_guarded_target(target, allowed_stages={"final_reproduction"})
    started = time.perf_counter()
    if phase == "data":
        payload = (
            reproduce._write_t001_data()
            if target == "T001"
            else reproduce._write_t002_data()
        )
        output = reproduce.CHECK_DIR / f"{target}_data_generation.json"
    elif phase == "check":
        payload = (
            reproduce._t001_checks()
            if target == "T001"
            else reproduce._t002_checks()
        )
        output = reproduce.CHECK_DIR / f"{target}_scientific_checks.json"
    else:
        raise ValueError(f"unsupported isolated phase: {phase}")
    payload["execution"] = {
        "schema_version": 1,
        "target_id": target,
        "phase": phase,
        "guarded_stage": os.environ["PRAGENT_GUARDED_STAGE"],
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "environment": {"python": sys.version.split()[0]},
    }
    reproduce._write_json(output, payload)
    if payload.get("status") != "passed":
        raise RuntimeError(f"{target} {phase} failed scientific validation")
    return {"target_id": target, "phase": phase, "status": payload["status"]}


def main() -> int:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    _validate_config(config["parameters"])
    results = [
        _run_phase(target, phase)
        for target in ("T001", "T002")
        for phase in ("data", "check")
    ]
    print(
        json.dumps(
            {
                "status": "passed",
                "paper_id": config["paper_id"],
                "profile": "paper_exact",
                "results": results,
                "generated_data_provenance": "independent_numerics",
                "paper_scale_outputs_replaced": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
