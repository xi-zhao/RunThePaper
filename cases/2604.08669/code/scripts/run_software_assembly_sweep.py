#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from p2wgs_potential import run_software_assembly_sweep  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a 2604.08669 software assembly reproduction sweep across scales and P2WGS iterations."
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "checks" / "software_assembly_sweep")
    parser.add_argument(
        "--scale",
        nargs="+",
        default=["7:4", "9:5"],
        help="One or more initial_side:target_side pairs.",
    )
    parser.add_argument("--grid-size", type=int, default=64)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--p2wgs-iterations", type=int, nargs="+", default=[3, 5])
    parser.add_argument("--sigma", type=float, default=1.4)
    parser.add_argument("--seed", type=int, default=260408690)
    parser.add_argument("--loading-probability", type=float, default=0.75)
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
    parser.add_argument("--path-planning-ms", type=float, default=None)
    parser.add_argument("--slm-refresh-ms", type=float, default=0.5)
    parser.add_argument("--transfer-delay-ms", type=float, default=3.0)
    parser.add_argument("--graph-backend", default="auto")
    args = parser.parse_args()

    checkpoint_path = normalize_checkpoint_path(args.checkpoint_path)
    configs = build_sweep_configs(
        scale_specs=args.scale,
        grid_size=args.grid_size,
        frames=args.frames,
        p2wgs_iterations=args.p2wgs_iterations,
        sigma=args.sigma,
        seed=args.seed,
        loading_probability=args.loading_probability,
        checkpoint_path=checkpoint_path,
        assignment_strategy=args.assignment_strategy,
        device=args.device,
        path_planning_ms=args.path_planning_ms,
        slm_refresh_ms=args.slm_refresh_ms,
        transfer_delay_ms=args.transfer_delay_ms,
        graph_backend=args.graph_backend,
    )
    metrics = run_software_assembly_sweep(output_dir=args.output_dir, configs=configs)
    print(
        json.dumps(
            {
                "config_count": metrics["summary"]["config_count"],
                "completed_count": metrics["summary"]["completed_count"],
                "assignment_strategies": metrics["summary"]["assignment_strategies"],
                "assignment_sources": metrics["summary"]["assignment_sources"],
                "best_total_assembly_config_id": metrics["summary"]["best_total_assembly_config_id"],
                "metrics_path": str(args.output_dir / "metrics.json"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def normalize_checkpoint_path(value: str) -> Path | None:
    text = str(value).strip()
    if text.lower() in {"", "none", "null"}:
        return None
    path = Path(text)
    return path if path.exists() else None


def build_sweep_configs(
    *,
    scale_specs: list[str],
    grid_size: int,
    frames: int,
    p2wgs_iterations: list[int],
    sigma: float,
    seed: int,
    loading_probability: float,
    checkpoint_path: Path | None,
    assignment_strategy: str,
    device: str,
    path_planning_ms: float | None,
    slm_refresh_ms: float,
    transfer_delay_ms: float,
    graph_backend: str,
) -> list[dict[str, object]]:
    configs: list[dict[str, object]] = []
    for scale_index, scale_spec in enumerate(scale_specs):
        initial_side, target_side = parse_scale_spec(scale_spec)
        for iteration_index, iteration_count in enumerate(p2wgs_iterations):
            configs.append(
                {
                    "config_id": f"i{initial_side}_t{target_side}_iter{iteration_count}",
                    "grid_size": grid_size,
                    "initial_side": initial_side,
                    "target_side": target_side,
                    "frames": frames,
                    "p2wgs_iterations": int(iteration_count),
                    "sigma": sigma,
                    "seed": seed + scale_index * 100 + iteration_index,
                    "loading_probability": loading_probability,
                    "k_neighbors": min(16, target_side * target_side),
                    "checkpoint_path": str(checkpoint_path) if checkpoint_path is not None else None,
                    "assignment_strategy": assignment_strategy,
                    "device": device,
                    "path_planning_ms": path_planning_ms,
                    "slm_refresh_ms": slm_refresh_ms,
                    "transfer_delay_ms": transfer_delay_ms,
                    "graph_backend": graph_backend,
                }
            )
    return configs


def parse_scale_spec(scale_spec: str) -> tuple[int, int]:
    parts = str(scale_spec).split(":")
    if len(parts) != 2:
        raise ValueError(f"scale must be initial_side:target_side, got {scale_spec!r}")
    initial_side = int(parts[0])
    target_side = int(parts[1])
    if initial_side < target_side:
        raise ValueError(f"initial_side must be at least target_side, got {scale_spec!r}")
    return initial_side, target_side


if __name__ == "__main__":
    raise SystemExit(main())
