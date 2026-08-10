#!/usr/bin/env python3
"""Run all formula-derived numeric targets without reading paper figures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from exact_scars.campaign import ScarCampaign  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output = args.output if args.output.is_absolute() else WORKSPACE / args.output
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest = ScarCampaign(WORKSPACE, config, output).run()
    print(
        json.dumps(
            {
                "targets_total": manifest["targets_total"],
                "all_numeric_items_have_outputs": manifest[
                    "all_numeric_items_have_outputs"
                ],
                "paper_error_candidates": len(manifest["paper_error_candidates"]),
                "elapsed_seconds": manifest["elapsed_seconds"],
            },
            indent=2,
        )
    )
    return 0 if manifest["all_numeric_items_have_outputs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
