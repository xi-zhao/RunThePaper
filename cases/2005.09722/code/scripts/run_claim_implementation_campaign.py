#!/usr/bin/env python3
"""Execute the uncovered-claim implementation campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from claim_implementation_campaign import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    manifest = run_campaign(args.config, args.output_root)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if manifest["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
