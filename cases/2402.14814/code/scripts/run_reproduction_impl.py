#!/usr/bin/env python3
"""CLI entry point for the independent paper reproduction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from laughlin_reproduction.reproduction import run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=WORKSPACE / "config" / "paper_exact.json"
    )
    parser.add_argument("--output-root", type=Path, default=WORKSPACE / "outputs")
    args = parser.parse_args()
    result = run(args.config.resolve(), args.output_root.resolve())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
