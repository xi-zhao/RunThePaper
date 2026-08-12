#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/src"))

from atom_path_planner import run_reduced_training_pilot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the reduced-scale 2604.08669 GNN path-planner retraining.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "checks" / "retrained_gnn_model")
    parser.add_argument("--train-samples", type=int, default=32)
    parser.add_argument("--eval-samples", type=int, default=8)
    parser.add_argument("--initial-side", type=int, default=9)
    parser.add_argument("--target-side", type=int, default=5)
    parser.add_argument("--k-neighbors", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--message-passes", type=int, default=2)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=260408669)
    args = parser.parse_args()

    metrics = run_reduced_training_pilot(
        output_dir=args.output_dir,
        train_samples=args.train_samples,
        eval_samples=args.eval_samples,
        initial_side=args.initial_side,
        target_side=args.target_side,
        k_neighbors=args.k_neighbors,
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
        message_passes=args.message_passes,
        device=args.device,
        seed=args.seed,
    )
    print(json.dumps(metrics["summary"], indent=2, sort_keys=True))
    print("metrics: outputs/checks/retrained_gnn_model/metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
