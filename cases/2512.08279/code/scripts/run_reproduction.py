"""Run the public reproduction entry points.

The full Fig. 3 campaign takes roughly 17 minutes on an Apple M4. Use
``--quick`` for a three-epsilon profile before starting the paper-scale run.
"""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import sys


CASE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = CASE_ROOT / "code"
sys.path.insert(0, str(CODE_ROOT))
sys.path.insert(0, str(CODE_ROOT / "scripts"))


def _configure_module(module: object) -> None:
    module.WORKSPACE = CASE_ROOT
    module.DATA_DIR = CASE_ROOT / "outputs" / "data"
    module.CHECK_DIR = CASE_ROOT / "outputs" / "checks"


def _call(module_name: str, target_id: str, argv: list[str]) -> int:
    module = importlib.import_module(module_name)
    _configure_module(module)
    os.environ["PRAGENT_GUARDED_TARGET_ID"] = target_id
    os.environ["PRAGENT_GUARDED_STAGE"] = argv[1]
    original_argv = sys.argv
    try:
        sys.argv = [module_name, *argv]
        return int(module.main())
    finally:
        sys.argv = original_argv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        choices=["fig2", "fig3", "all"],
        default="all",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a three-epsilon Fig. 3 profile instead of the 82-solve campaign.",
    )
    args = parser.parse_args()

    if args.target in {"fig2", "all"}:
        status = _call(
            "_run_swap_dephasing",
            "T001",
            ["--stage", "final_reproduction"],
        )
        if status:
            return status

    if args.target in {"fig3", "all"}:
        if args.quick:
            fig3_args = [
                "--stage",
                "exploratory",
                "--mode",
                "profile",
                "--branch",
                "both",
                "--time-points",
                "101",
                "--epsilons",
                "0,0.1,0.2",
                "--verify-full-grid",
            ]
        else:
            fig3_args = [
                "--stage",
                "final_reproduction",
                "--mode",
                "final",
            ]
        status = _call("_run_programming_cost", "T002", fig3_args)
        if status:
            return status

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
