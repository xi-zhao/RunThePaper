#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from scientific_closure import run_closure  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run clean-room Sycamore closure")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    run_closure(Path(args.config), Path(args.output_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
