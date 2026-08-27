#!/usr/bin/env python3
"""Run the focused T005 stability implementation campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.stability_implementation_campaign import run_campaign


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    manifest = run_campaign(args.config, args.output_root)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if manifest["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
