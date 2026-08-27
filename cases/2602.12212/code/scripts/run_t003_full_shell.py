#!/usr/bin/env python3
"""Generate the full 214-state T003 shell without touching shared outputs."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SCRIPTS = WORKSPACE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def move_output(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.replace(destination)


def main() -> int:
    args = parse_args()
    parameters = json.loads(args.config.read_text(encoding="utf-8"))["parameters"]
    module = importlib.import_module("run_dynamics")
    argv = [
        "run_dynamics",
        "--backend",
        str(parameters["backend"]),
        "--length",
        str(parameters["length"]),
        "--beta",
        str(parameters["beta"]),
        "--time-max",
        str(parameters["time_max"]),
        "--time-points",
        str(parameters["time_points"]),
        "--boundary",
        str(parameters["boundary"]),
        "--max-band-representatives",
        str(parameters["max_band_representatives"]),
        "--no-reference-comparison",
    ]
    previous_argv = sys.argv
    try:
        sys.argv = argv
        status = int(module.main())
    finally:
        sys.argv = previous_argv
    if status != 0:
        return status

    destinations = {
        "data": "outputs/data/paper_scale_full_shell/t003_dynamics.csv",
        "figure": "outputs/figures/paper_scale_full_shell/t003_dynamics.png",
        "check": "outputs/checks/paper_scale_full_shell/t003_dynamics.json",
    }
    check_source = WORKSPACE / "outputs" / "checks" / "t003_dynamics.json"
    check = json.loads(check_source.read_text(encoding="utf-8"))
    check["paths"] = {
        "data": destinations["data"],
        "figure": destinations["figure"],
    }
    check_source.write_text(
        json.dumps(check, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    move_output(
        WORKSPACE / "outputs" / "data" / "t003_dynamics.csv",
        WORKSPACE / destinations["data"],
    )
    move_output(
        WORKSPACE / "outputs" / "figures" / "t003_dynamics.png",
        WORKSPACE / destinations["figure"],
    )
    move_output(check_source, WORKSPACE / destinations["check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
