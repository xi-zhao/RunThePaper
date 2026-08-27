#!/usr/bin/env python3
"""Run claim-level clean-room state-transfer checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.implementation_closure import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    print(json.dumps(run_campaign(args.config, args.output_root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
