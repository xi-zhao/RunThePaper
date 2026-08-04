#!/usr/bin/env python3
"""Render the final Figure 1 artifact from the A100-produced binned CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))

from run_afhm_figure1 import write_figure  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=WORKSPACE / "outputs" / "data" / "afhm_figure1_binned.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=WORKSPACE / "outputs" / "figures" / "afhm_figure1_reproduction.png",
    )
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"no binned rows in {args.input}")
    write_figure(rows, args.output)
    print(f"rendered {len(rows)} bins to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
