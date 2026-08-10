#!/usr/bin/env python3
"""Evaluate T001-T031 machine contracts while preserving science blockers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from paper_scale import load_campaign  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument(
        "--acceptance", type=Path, default=Path("config/paper_scale_acceptance.json")
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--backend", choices=("numpy", "cupy"))
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else WORKSPACE / path

    campaign = load_campaign(
        resolve(args.config),
        output_root=resolve(args.output_root) if args.output_root else None,
        smoke=args.smoke,
        backend=args.backend,
    )
    print(
        json.dumps(campaign.accept(resolve(args.acceptance)), indent=2, sort_keys=True)
    )


if __name__ == "__main__":
    main()
