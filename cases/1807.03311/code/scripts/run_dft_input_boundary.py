#!/usr/bin/env python3
"""Run the strict input-boundary campaign for Supplement Fig. 5(a,b)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from twisted_tmd.dft_input_boundary import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    config = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output = (
        args.output_root
        if args.output_root.is_absolute()
        else WORKSPACE / args.output_root
    )
    manifest = run_campaign(config, output)
    return 0 if manifest["status"] == "input_blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
