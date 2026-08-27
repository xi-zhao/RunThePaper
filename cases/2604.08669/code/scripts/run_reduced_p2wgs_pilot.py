#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from p2wgs_potential import run_reduced_p2wgs_pilot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the reduced-scale 2604.08669 P2WGS continuity pilot.")
    parser.add_argument("--config", type=Path, help="Workspace-relative JSON config under config/.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "checks" / "reduced_p2wgs_pilot")
    parser.add_argument("--grid-size", type=int, default=64)
    parser.add_argument("--initial-side", type=int, default=7)
    parser.add_argument("--target-side", type=int, default=4)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--iterations", type=int, nargs="+", default=[3, 5, 8, 10])
    parser.add_argument("--sigma", type=float, default=1.4)
    parser.add_argument("--seed", type=int, default=260408670)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_payload: dict[str, Any] = {}
    if args.config is not None:
        config_path = args.config
        if config_path.is_absolute() or ".." in config_path.parts or config_path.parts[:1] != ("config",):
            raise ValueError("--config must be workspace-relative under config/")
        config_payload = json.loads((ROOT / config_path).read_text(encoding="utf-8"))

    output_dir_value = config_payload.get("output_dir")
    if output_dir_value is None:
        output_dir = args.output_dir
    else:
        output_ref = Path(str(output_dir_value))
        if output_ref.is_absolute() or ".." in output_ref.parts or output_ref.parts[:1] != ("outputs",):
            raise ValueError("config output_dir must be workspace-relative under outputs/")
        output_dir = ROOT / output_ref
    grid_size = int(config_payload.get("grid_size", args.grid_size))
    initial_side = int(config_payload.get("initial_side", args.initial_side))
    target_side = int(config_payload.get("target_side", args.target_side))
    samples = int(config_payload.get("samples", args.samples))
    frames = int(config_payload.get("frames", args.frames))
    iterations = [int(value) for value in config_payload.get("iterations", args.iterations)]
    sigma = float(config_payload.get("sigma", args.sigma))
    seed = int(config_payload.get("seed", args.seed))
    resolved = {
        "output_dir": str(output_dir),
        "grid_size": grid_size,
        "initial_side": initial_side,
        "target_side": target_side,
        "samples": samples,
        "frames": frames,
        "iterations": iterations,
        "sigma": sigma,
        "seed": seed,
    }
    if args.dry_run:
        print(json.dumps({"status": "ready", "resolved_run": resolved}, indent=2, sort_keys=True))
        return 0

    metrics = run_reduced_p2wgs_pilot(
        output_dir=output_dir,
        grid_size=grid_size,
        initial_side=initial_side,
        target_side=target_side,
        samples=samples,
        frames=frames,
        iterations=iterations,
        sigma=sigma,
        seed=seed,
    )
    print(json.dumps(metrics["summary"], indent=2, sort_keys=True))
    print(f"metrics: {output_dir / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
