"""Render the two reproduced panels from independently generated CSV files."""

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


def _render(target_id: str) -> int:
    module = importlib.import_module("_render_reproduction")
    module.WORKSPACE = CASE_ROOT
    module.DATA_DIR = CASE_ROOT / "outputs" / "data"
    module.FIGURE_DIR = CASE_ROOT / "outputs" / "figures"
    os.environ["PRAGENT_GUARDED_TARGET_ID"] = target_id
    os.environ["PRAGENT_GUARDED_STAGE"] = "final_reproduction"
    original_argv = sys.argv
    try:
        sys.argv = [
            "_render_reproduction",
            "--target",
            target_id,
            "--stage",
            "final_reproduction",
        ]
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
    args = parser.parse_args()
    targets = {
        "fig2": ["T001"],
        "fig3": ["T002"],
        "all": ["T001", "T002"],
    }[args.target]
    for target_id in targets:
        status = _render(target_id)
        if status:
            return status
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
