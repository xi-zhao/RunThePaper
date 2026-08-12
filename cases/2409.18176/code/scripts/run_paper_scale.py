#!/usr/bin/env python3
"""Run or validate the checkpointed paper-scale convergence plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from bose_fermi_transport.paper_scale import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/paper_scale.json")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-units", type=int)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    config = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config.parents:
        raise ValueError("config must remain inside workspace")
    result = run_campaign(
        config,
        WORKSPACE,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        max_units=args.max_units,
        validate_only=args.validate_only,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
