#!/usr/bin/env python3
"""Isolated numerical entrypoint for arXiv:1811.08017."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from qdrift_resources.reproduction import run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    arguments = parser.parse_args()
    run(arguments.config)


if __name__ == "__main__":
    main()
