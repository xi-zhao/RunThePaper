#!/usr/bin/env python3
"""Run all formula-derived numerical targets in the isolated channel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from scientific_closure import run_scientific_closure  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    manifest = run_scientific_closure(args.config, args.output_root)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if manifest["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
