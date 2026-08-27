#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.implementation_campaign import run_campaign  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    run_campaign(args.config, args.profile, args.output_root)


if __name__ == "__main__":
    main()
