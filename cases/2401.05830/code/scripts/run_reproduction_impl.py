#!/usr/bin/env python3
"""Run the complete independent numerical reproduction from a frozen config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from inverse_mpemba.reproduction import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    summary = run(config_path.resolve(), WORKSPACE)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
