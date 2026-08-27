#!/usr/bin/env python3
"""Run a source-blind implementation probe for every numerical target."""
from __future__ import annotations

import argparse
import importlib
import json
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
    return {
        "module": module_name,
        "target_ids": [str(value) for value in step["target_ids"]],
        "args": argv,
        "status": status,
        "duration_seconds": perf_counter() - started,
    }


def _namespace_outputs() -> None:
    for kind in ("data", "figures", "checks"):
        root = WORKSPACE / "outputs" / kind
        destination = root / "implementation_probe"
        destination.mkdir(parents=True, exist_ok=True)
        for source in sorted(root.iterdir()):
            if source == destination:
                continue
            target = destination / source.name
            if source.is_dir():
                shutil.move(str(source), str(target))
            else:
                source.replace(target)


def main() -> int:
    args = parse_args()
    payload = json.loads(args.config.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    results = [_run_step(step) for step in parameters["steps"]]
    _namespace_outputs()
    summary = {
        "schema_version": 1,
        "profile": parameters["profile"],
        "source_pixels_used_in_generation": False,
        "steps": results,
        "status": "passed" if all(row["status"] == 0 for row in results) else "failed",
    }
    destination = WORKSPACE / "outputs" / "checks" / "implementation_probe" / "implementation_probe_summary.json"
    destination.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
