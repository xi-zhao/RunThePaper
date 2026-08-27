#!/usr/bin/env python3
"""Run every numerical target from a frozen, source-free configuration."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
TARGET_MODULES = {
    "T001": "run_main_fig1.py",
    "T002": "run_main_fig2.py",
    "T003": "run_main_fig3.py",
    "T004": "run_supp_fig2.py",
    "T005": "run_supp_fig3.py",
    "T006": "run_supp_fig4.py",
}


def _load_module(target_id: str, filename: str):
    path = WORKSPACE / "scripts" / filename
    spec = importlib.util.spec_from_file_location(f"campaign_{target_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load target module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_close(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"frozen parameter mismatch for {label}: {actual!r} != {expected!r}")


def _validate_bound_parameters(target_id: str, module, params: dict[str, object]) -> None:
    """Fail closed if a hard-coded target drifts from the frozen config."""

    _assert_close(module.TARGET_ID, target_id, f"{target_id}.target_id")
    if target_id == "T001":
        _assert_close(module.BULK.__dict__, params["bulk"], "T001.bulk")
        _assert_close(module.VACUUM.__dict__, params["vacuum"], "T001.vacuum")
        _assert_close(module.BULK_RADIAL_MAX, params["bulk_radial_max"], "T001.bulk_radial_max")
        _assert_close(module.BULK_RADIAL_SAMPLES, params["bulk_radial_samples"], "T001.bulk_radial_samples")
        _assert_close(module.BULK_ANGULAR_SAMPLES, params["bulk_angular_samples"], "T001.bulk_angular_samples")
        _assert_close(module.EDGE_KY_SAMPLES, params["edge_ky_samples"], "T001.edge_ky_samples")
    elif target_id == "T003":
        _assert_close(module.DELTA, params["delta"], "T003.delta")
        _assert_close(module.KAPPA_X, params["kappa_x"], "T003.kappa_x")
        _assert_close(module.KAPPA_Y, params["kappa_y"], "T003.kappa_y")
    elif target_id == "T004":
        _assert_close(module.MASS_SCALE, params["mass_scale"], "T004.mass_scale")
        _assert_close(module.KAPPA_SAMPLES, params["kappa_samples"], "T004.kappa_samples")
    elif target_id == "T006":
        _assert_close(module.MASS, params["mass"], "T006.mass")
        _assert_close(module.DELTA, params["delta"], "T006.delta")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.config.read_text(encoding="utf-8"))
    if payload.get("paper_id") != "1706.07435":
        raise RuntimeError("campaign config belongs to another paper")
    parameters = payload["parameters"]
    if set(parameters) != {*TARGET_MODULES, "scientific_boundary"}:
        raise RuntimeError("campaign config must bind exactly T001-T006 plus scientific_boundary")
    boundary = parameters["scientific_boundary"]
    expected_boundary = {
        "paper_equations_only": True,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "source_pixels_used_as_numerical_inputs": False,
        "reference_artifacts_read_by_runner": False,
    }
    _assert_close(boundary, expected_boundary, "scientific_boundary")

    results: list[dict[str, object]] = []
    original_argv = sys.argv[:]
    try:
        for target_id, filename in TARGET_MODULES.items():
            module = _load_module(target_id, filename)
            _validate_bound_parameters(target_id, module, parameters[target_id])
            os.environ["PRAGENT_GUARDED_TARGET_ID"] = target_id
            if target_id == "T005":
                expected = parameters[target_id]
                supp_config = json.loads(
                    (WORKSPACE / "config" / "supp_fig3.json").read_text(encoding="utf-8")
                )["parameters"]
                _assert_close(supp_config, expected, "T005.config")
                sys.argv = [filename, "--config", "config/supp_fig3.json"]
            else:
                sys.argv = [filename]
            return_code = int(module.main())
            results.append({"target_id": target_id, "return_code": return_code})
            if return_code != 0:
                raise RuntimeError(f"{target_id} scientific runner failed")
    finally:
        sys.argv = original_argv
        os.environ.pop("PRAGENT_GUARDED_TARGET_ID", None)

    print(json.dumps({"status": "passed", "targets": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
