#!/usr/bin/env python3
"""Config-driven entrypoint for every paper-scale numerical target."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("paper_id") != "2607.02157" or not payload.get("stages"):
        raise ValueError("invalid paper-exact campaign config")
    ids = [str(stage.get("stage_id") or "") for stage in payload["stages"]]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise ValueError("stage ids must be unique and non-empty")
    for stage in payload["stages"]:
        mode = str(stage.get("mode") or "")
        if mode in {"scan", "nmse"}:
            required = {"model", "sequences", "points", "realizations", "output"}
        elif mode == "spectral":
            required = {
                "sequences",
                "samples",
                "omega_points",
                "tfim_realizations",
                "j_points",
                "alpha_points",
                "output_dir",
                "check_output",
                "outputs",
            }
        else:
            raise ValueError(f"unsupported campaign mode: {mode}")
        missing = sorted(key for key in required if key not in stage)
        if missing:
            raise ValueError(f"{stage['stage_id']} missing fields: {missing}")
    return payload


def stage_command(stage: dict[str, Any], backend: str) -> list[str]:
    if stage["mode"] == "spectral":
        return [
            sys.executable,
            "scripts/run_figS1.py",
            "--n-seq",
            str(stage["sequences"]),
            "--n-samples",
            str(stage["samples"]),
            "--tfim-realizations",
            str(stage["tfim_realizations"]),
            "--n-j",
            str(stage["j_points"]),
            "--n-alpha",
            str(stage["alpha_points"]),
            "--omega-points",
            str(stage["omega_points"]),
            "--output-dir",
            str(stage["output_dir"]),
            "--check-path",
            str(stage["check_output"]),
        ]
    command = [sys.executable, "scripts/qrc_gpu.py"]
    if backend == "cupy_eig":
        command.append("--cupy-eig")
    command.extend(
        [
            str(stage["mode"]),
            "--model",
            str(stage["model"]),
            "--n-seq",
            str(stage["sequences"]),
            "--n-points",
            str(stage["points"]),
            "--realizations",
            str(stage["realizations"]),
        ]
    )
    if stage["mode"] == "scan":
        command.extend(["--pack", str(stage.get("pack", 1))])
    else:
        command.extend(["--chunk", str(stage.get("chunk", 50))])
    command.extend(["--out", str(stage["output"])])
    return command


def stage_outputs(stage: dict[str, Any]) -> list[str]:
    if stage["mode"] == "spectral":
        outputs = [str(value) for value in stage.get("outputs", [])]
        if not outputs:
            raise ValueError("spectral stage must declare its output set")
        return outputs
    return [str(stage["output"])]


def stage_workload(stage: dict[str, Any]) -> dict[str, int]:
    if stage["mode"] == "spectral":
        return {
            "sequence_evaluations": 0,
            "spectral_filter_updates": (
                int(stage["sequences"])
                * int(stage["samples"])
                * int(stage["omega_points"])
            ),
            "spectral_eigendecompositions": (
                int(stage["tfim_realizations"]) * int(stage["j_points"])
                + int(stage["alpha_points"])
            ),
        }
    return {
        "sequence_evaluations": (
            int(stage["sequences"])
            * int(stage["points"])
            * int(stage["realizations"])
        )
    }


def build_plan(config: dict[str, Any], selected: str = "all") -> dict[str, Any]:
    stages = [stage for stage in config["stages"] if selected == "all" or stage["stage_id"] == selected]
    if not stages:
        raise ValueError(f"unknown stage: {selected}")
    return {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "planned",
        "stages": [
            {
                "stage_id": stage["stage_id"],
                "mode": stage["mode"],
                **stage_workload(stage),
                "command": stage_command(stage, str(config.get("backend") or "")),
                "outputs": stage_outputs(stage),
            }
            for stage in stages
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", default="all")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    plan = build_plan(load_config(config_path), args.stage)
    if args.plan:
        print(json.dumps(plan, indent=2))
        return 0
    for stage in plan["stages"]:
        for value in stage["outputs"]:
            (WORKSPACE / value).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(stage["command"], cwd=WORKSPACE, check=True)
    plan["status"] = "completed"
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
