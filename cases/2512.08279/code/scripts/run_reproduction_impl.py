from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC_DIR = WORKSPACE / "src"
SCRIPT_DIR = WORKSPACE / "scripts"
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _configure_module(module: object) -> None:
    module.WORKSPACE = WORKSPACE
    if hasattr(module, "DATA_DIR"):
        module.DATA_DIR = WORKSPACE / "outputs" / "data"
    if hasattr(module, "CHECK_DIR"):
        module.CHECK_DIR = WORKSPACE / "outputs" / "checks"
    if hasattr(module, "FIGURE_DIR"):
        module.FIGURE_DIR = WORKSPACE / "outputs" / "figures"


def _option_value(argv: list[str], option: str) -> str:
    try:
        return argv[argv.index(option) + 1]
    except (ValueError, IndexError) as error:
        raise ValueError(f"missing value for {option}") from error


def _call(module_name: str, target_id: str, argv: list[str]) -> int:
    module = importlib.import_module(module_name)
    _configure_module(module)
    os.environ["PRAGENT_GUARDED_TARGET_ID"] = target_id
    os.environ["PRAGENT_GUARDED_STAGE"] = _option_value(argv, "--stage")
    original_argv = sys.argv
    try:
        sys.argv = [module_name, *argv]
        return int(module.main())
    finally:
        sys.argv = original_argv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the source-free paper-scale reproduction for arXiv:2512.08279."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    parameters = config["parameters"]
    fig2 = parameters["fig2"]
    fig3 = parameters["fig3"]

    steps = [
        (
            "run_swap_dephasing",
            "T001",
            [
                "--stage",
                "final_reproduction",
                "--solver-epsilon",
                str(fig2["solver_epsilon"]),
            ],
        ),
        (
            "run_programming_cost",
            "T002",
            [
                "--stage",
                "final_reproduction",
                "--mode",
                "final",
                "--solver-epsilon",
                str(fig3["solver_epsilon"]),
                "--max-iterations",
                str(fig3["max_iterations"]),
            ],
        ),
    ]
    for module_name, target_id, argv in steps:
        status = _call(module_name, target_id, argv)
        if status:
            return status
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
