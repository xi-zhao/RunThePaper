#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from p2wgs_potential import run_software_assembly_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the software-only 2604.08669 path-planning -> P2WGS -> timing pipeline."
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "checks" / "software_assembly_pipeline")
    parser.add_argument("--grid-size", type=int, default=64)
    parser.add_argument("--initial-side", type=int, default=7)
    parser.add_argument("--target-side", type=int, default=4)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--p2wgs-iterations", type=int, default=5)
    parser.add_argument("--sigma", type=float, default=1.4)
    parser.add_argument("--seed", type=int, default=260408672)
    parser.add_argument("--loading-probability", type=float, default=0.75)
    parser.add_argument("--k-neighbors", type=int, default=16)
    parser.add_argument(
        "--checkpoint-path",
        default=str(ROOT / "outputs" / "checks" / "retrained_gnn_model" / "model_state.pt"),
        help="Use the local GNN checkpoint when it exists; pass none to force Hungarian labels.",
    )
    parser.add_argument(
        "--assignment-strategy",
        default="auto",
        choices=["auto", "hungarian_ground_truth", "gnn_score_hungarian", "modified_auction"],
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--path-planning-ms",
        type=float,
        default=None,
        help="Override measured local path-planning time with a paper/device timing assumption.",
    )
    parser.add_argument("--slm-refresh-ms", type=float, default=0.5)
    parser.add_argument("--transfer-delay-ms", type=float, default=3.0)
    parser.add_argument("--graph-backend", default="auto")
    args = parser.parse_args()

    checkpoint_path_arg = str(args.checkpoint_path).strip()
    checkpoint_path: Path | None
    if checkpoint_path_arg.lower() in {"", "none", "null"}:
        checkpoint_path = None
    else:
        checkpoint_path = Path(checkpoint_path_arg)
    if checkpoint_path is not None and not checkpoint_path.exists():
        checkpoint_path = None

    metrics = run_software_assembly_pipeline(
        output_dir=args.output_dir,
        grid_size=args.grid_size,
        initial_side=args.initial_side,
        target_side=args.target_side,
        frames=args.frames,
        p2wgs_iterations=args.p2wgs_iterations,
        sigma=args.sigma,
        seed=args.seed,
        loading_probability=args.loading_probability,
        k_neighbors=args.k_neighbors,
        checkpoint_path=checkpoint_path,
        assignment_strategy=args.assignment_strategy,
        device=args.device,
        path_planning_ms=args.path_planning_ms,
        slm_refresh_ms=args.slm_refresh_ms,
        transfer_delay_ms=args.transfer_delay_ms,
        graph_backend=args.graph_backend,
    )
    print(
        json.dumps(
            {
                "assignment_strategy": metrics["path_planning"]["assignment_strategy"],
                "assignment_source": metrics["path_planning"]["assignment_source"],
                "target_count": metrics["path_planning"]["target_count"],
                "mean_generation_ms": metrics["p2wgs"]["mean_generation_ms"],
                "total_assembly_time_ms": metrics["timing"]["total_assembly_time_ms"],
                "metrics_path": str(args.output_dir / "metrics.json"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
