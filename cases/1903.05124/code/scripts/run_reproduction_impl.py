#!/usr/bin/env python3
"""Run every implemented numerical target through one isolated entrypoint.

The target modules already contain the paper-derived algorithms and scientific
checks.  This file only supplies a deterministic, subprocess-free orchestration
boundary so the Harness can attest the existing implementation as one minimal
input bundle.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
from time import perf_counter
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
SCRIPTS = WORKSPACE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def _run_step(step: dict[str, Any]) -> dict[str, Any]:
    target_id = str(step["target_id"])
    module_name = str(step["module"])
    argv = [str(value) for value in step.get("args", [])]
    os.environ["PRAGENT_GUARDED_TARGET_ID"] = target_id
    module = importlib.import_module(module_name)
    previous_argv = sys.argv
    started = perf_counter()
    try:
        sys.argv = [module_name, *argv]
        status = int(module.main())
    finally:
        sys.argv = previous_argv
    return {
        "target_id": target_id,
        "module": module_name,
        "args": argv,
        "status": status,
        "duration_seconds": perf_counter() - started,
    }


def _freeze_current_upstream() -> None:
    """Freeze the T001 data produced earlier in this same clean-room run."""

    source = WORKSPACE / "outputs" / "data" / "main_fig2_numerical_data.csv"
    destination = WORKSPACE / "outputs" / "data" / "frozen_main_fig2_numerical_data.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _namespace_outputs() -> None:
    for kind in ("data", "figures", "checks"):
        root = WORKSPACE / "outputs" / kind
        destination = root / "implementation_probe"
        destination.mkdir(parents=True, exist_ok=True)
        for source in sorted(root.iterdir()):
            if not source.is_file() or source.name.startswith("frozen_"):
                continue
            source.replace(destination / source.name)


def main() -> int:
    args = parse_args()
    payload = json.loads(args.config.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    results = []
    for step in parameters["steps"]:
        result = _run_step(step)
        results.append(result)
        if result["target_id"] == "T001" and result["status"] == 0:
            _freeze_current_upstream()
    summary = {
        "schema_version": 1,
        "profile": parameters["profile"],
        "source_pixels_used_in_generation": False,
        "steps": results,
        "status": "passed" if all(row["status"] == 0 for row in results) else "failed",
    }
    _namespace_outputs()
    destination = WORKSPACE / "outputs" / "checks" / "implementation_probe" / "implementation_probe_summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
