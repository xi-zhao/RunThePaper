#!/usr/bin/env python3
"""Run formula-derived numerics without access to paper/reference images."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from moire_hubbard.reproduction import run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    result = run(config, WORKSPACE)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
