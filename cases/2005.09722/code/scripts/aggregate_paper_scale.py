#!/usr/bin/env python3
"""Aggregate complete paper-scale scalar checkpoints without loading states."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from paper_scale import FAMILY_ORDER, load_campaign  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--family", choices=FAMILY_ORDER)
    parser.add_argument("--backend", choices=("numpy", "cupy"))
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    config = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output = (
        args.output_root
        if args.output_root is None or args.output_root.is_absolute()
        else WORKSPACE / args.output_root
    )
    campaign = load_campaign(
        config,
        output_root=output,
        smoke=args.smoke,
        backend=args.backend,
    )
    result = (
        campaign.aggregate_family(args.family)
        if args.family
        else campaign.aggregate_all()
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
