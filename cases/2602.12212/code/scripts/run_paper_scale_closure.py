#!/usr/bin/env python3
"""Recompute every paper-scale target without source or author numerical inputs."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
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


def run_step(step: dict[str, Any]) -> dict[str, Any]:
    module_name = str(step["module"])
    argv = [str(value) for value in step.get("args", [])]
    module = importlib.import_module(module_name)
    previous_argv = sys.argv
    started = perf_counter()
    try:
        sys.argv = [module_name, *argv]
        status = int(module.main())
    finally:
        sys.argv = previous_argv
    if status != 0:
        raise RuntimeError(f"{module_name} failed with status {status}")
    return {
        "module": module_name,
        "target_ids": [str(value) for value in step["target_ids"]],
        "args": argv,
        "status": status,
        "duration_seconds": perf_counter() - started,
    }


def main() -> int:
    args = parse_args()
    payload = json.loads(args.config.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    results = [run_step(step) for step in parameters["steps"]]
    summary = {
        "schema_version": 1,
        "profile": parameters["profile"],
        "scientific_input_boundary": parameters["scientific_input_boundary"],
        "steps": results,
        "status": "passed",
    }
    destination = WORKSPACE / "outputs" / "checks" / "paper_scale_closure.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
