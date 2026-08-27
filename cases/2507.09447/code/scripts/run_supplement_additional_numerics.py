#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from supplement_additional_numerics import run_additional_numerics  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the clean-room unidirectional, Fig. S3, and Fig. S4 numerical closure."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=WORKSPACE / "config" / "supplement_additional_run.json",
    )
    parser.add_argument(
        "--science-only",
        action="store_true",
        help="Generate numerical data and checks without invoking the rendering stack.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_additional_numerics(WORKSPACE, config, render_figures=not args.science_only)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
