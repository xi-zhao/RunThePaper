#!/usr/bin/env python3
"""Run all paper-exact Hofstadter numerical targets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from hofstadter_reproduction.campaign import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_exact.json")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    config = (WORKSPACE / args.config).resolve()
    output = (WORKSPACE / args.output_dir).resolve()
    summary = run_campaign(config, output)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
