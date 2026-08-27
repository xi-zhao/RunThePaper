#!/usr/bin/env python3
"""Run the item-level DQC1 implementation-closure campaign."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dqc1_discord.implementation_closure import run_campaign  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()
    run_campaign(WORKSPACE / args.config, WORKSPACE / args.output_root)


if __name__ == "__main__":
    main()
