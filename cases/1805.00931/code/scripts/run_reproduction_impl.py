#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kicked_ising.reproduction import run_reproduction  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run feature or resumable paper-scale kicked-Ising targets."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--targets",
        help="Comma-separated schema-v2 target ids (T001,T002,T003,T004).",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        help="Run one externally scheduled shard; combine with --targets for one family.",
    )
    parser.add_argument("--resume", action="store_true", help="Resume verified checkpoints.")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Validate parameters and memory estimates without starting numerics.",
    )
    arguments = parser.parse_args()
    targets = (
        {value.strip() for value in arguments.targets.split(",") if value.strip()}
        if arguments.targets
        else None
    )
    result = run_reproduction(
        arguments.config,
        targets=targets,
        shard_index=arguments.shard_index,
        resume=arguments.resume,
        preflight=arguments.preflight,
    )
    if isinstance(result, dict) and result.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
