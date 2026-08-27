#!/usr/bin/env python3
"""Run the clean-room final-resolution campaign."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.final_resolution import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    summary = run_campaign(args.config, args.profile, args.output_root)
    return 0 if summary["all_reproduction_acceptance_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
