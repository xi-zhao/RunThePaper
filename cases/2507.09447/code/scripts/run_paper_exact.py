#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from paper_exact_reproduction import (  # noqa: E402
    recompute_paper_scaling,
    run_paper_ed,
    run_paper_profiles,
    run_paper_theory,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the resumable paper-matched Fig. 3–5 numerics.")
    parser.add_argument(
        "--stage",
        choices=("ed", "scaling", "profiles", "theory", "all"),
        default="all",
        help="Numerical stage to run. 'all' runs ED, profiles, and theory in that order.",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Limit ED work in this invocation; useful for checkpoint and scheduler smoke tests.",
    )
    parser.add_argument("--config", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results: dict[str, object] = {}
    if args.stage in {"ed", "all"}:
        results["ed"] = run_paper_ed(WORKSPACE, args.config, max_batches=args.max_batches)
        if args.stage == "all" and results["ed"]["status"] != "passed":  # type: ignore[index]
            print(json.dumps(results, indent=2), flush=True)
            raise SystemExit("ED stage is checkpointed but incomplete; rerun before downstream paper export")
    if args.stage == "scaling":
        results["scaling"] = recompute_paper_scaling(WORKSPACE, args.config)
    if args.stage in {"profiles", "all"}:
        results["profiles"] = run_paper_profiles(WORKSPACE, args.config)
    if args.stage in {"theory", "all"}:
        results["theory"] = run_paper_theory(WORKSPACE, args.config)
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()
