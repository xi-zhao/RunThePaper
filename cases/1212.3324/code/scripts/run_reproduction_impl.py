#!/usr/bin/env python3
"""Execute all declared Rudner numerical targets without reference access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from floquet_winding.campaign import load_config, run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    output_root = (WORKSPACE / args.output_root).resolve()
    config = load_config(config_path)
    summary = run_campaign(config, config_path=config_path, output_root=output_root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
