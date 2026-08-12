#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))

from p2wgs_potential import run_reduced_p2wgs_pilot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the reduced-scale 2604.08669 P2WGS continuity pilot.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "checks" / "reduced_p2wgs_pilot")
    parser.add_argument("--grid-size", type=int, default=64)
    parser.add_argument("--initial-side", type=int, default=7)
    parser.add_argument("--target-side", type=int, default=4)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--iterations", type=int, nargs="+", default=[3, 5, 8, 10])
    parser.add_argument("--sigma", type=float, default=1.4)
    parser.add_argument("--seed", type=int, default=260408670)
    args = parser.parse_args()

    metrics = run_reduced_p2wgs_pilot(
        output_dir=args.output_dir,
        grid_size=args.grid_size,
        initial_side=args.initial_side,
        target_side=args.target_side,
        samples=args.samples,
        frames=args.frames,
        iterations=args.iterations,
        sigma=args.sigma,
        seed=args.seed,
    )
    print(json.dumps(metrics["summary"], indent=2, sort_keys=True))
    print("metrics: outputs/checks/reduced_p2wgs_pilot/metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
