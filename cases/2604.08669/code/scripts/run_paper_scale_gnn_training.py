#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from atom_path_planner import run_model_training_reproduction  # noqa: E402


def training_profiles() -> dict[str, dict[str, Any]]:
    return {
        "canary": {
            "initial_side": 9,
            "target_side": 5,
            "k_neighbors": 16,
            "train_samples": 8,
            "eval_samples": 2,
            "epochs": 2,
            "hidden_dim": 32,
            "message_passes": 6,
            "learning_rate": 0.01,
            "loading_probability": 0.75,
            "device": "cpu",
            "graph_backend": "kdtree",
            "stream_samples": True,
            "checkpoint_every_updates": 4,
            "history_stride": 1,
            "prefetch_workers": 0,
            "prefetch_buffer": 0,
            "progress_every_updates": 1,
            "batch_size": 1,
            "loss_mode": "bce",
            "source_ce_weight": 0.1,
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_canary",
        },
        "a100_calibration": {
            "initial_side": 33,
            "target_side": 25,
            "k_neighbors": 64,
            "train_samples": 1024,
            "eval_samples": 128,
            "epochs": 20,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.01,
            "loading_probability": 0.75,
            "device": "cuda",
            "graph_backend": "kdtree",
            "stream_samples": True,
            "checkpoint_every_updates": 256,
            "history_stride": 10,
            "prefetch_workers": 4,
            "prefetch_buffer": 8,
            "progress_every_updates": 25,
            "batch_size": 8,
            "loss_mode": "bce",
            "source_ce_weight": 0.1,
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_a100_calibration",
        },
        "paper_target": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "train_samples": 1_000_000,
            "eval_samples": 1024,
            "epochs": 1,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.01,
            "loading_probability": 0.75,
            "device": "cuda",
            "graph_backend": "kdtree",
            "stream_samples": True,
            "checkpoint_every_updates": 1000,
            "history_stride": 100,
            "prefetch_workers": 8,
            "prefetch_buffer": 16,
            "progress_every_updates": 100,
            "batch_size": 2,
            "loss_mode": "bce",
            "source_ce_weight": 0.1,
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the 2604.08669 GNN path-planner model.")
    parser.add_argument("--config", type=Path, help="Workspace-relative JSON config under config/.")
    parser.add_argument("--profile", choices=sorted(training_profiles()), default="canary")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--device")
    parser.add_argument("--train-samples", type=int)
    parser.add_argument("--eval-samples", type=int)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--hidden-dim", type=int)
    parser.add_argument("--message-passes", type=int)
    parser.add_argument("--k-neighbors", type=int)
    parser.add_argument("--target-lattice-spacing", type=float)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--max-updates", type=int)
    parser.add_argument("--checkpoint-every-updates", type=int)
    parser.add_argument("--prefetch-workers", type=int)
    parser.add_argument("--prefetch-buffer", type=int)
    parser.add_argument("--progress-every-updates", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--dataset-manifest-path", type=Path)
    parser.add_argument("--eval-dataset-manifest-path", type=Path)
    parser.add_argument("--resume-checkpoint-path", type=Path)
    parser.add_argument("--loss-mode", choices=["bce", "target_ce", "source_ce", "bce_source_ce"])
    parser.add_argument("--source-ce-weight", type=float)
    parser.add_argument("--seed", type=int, default=260408690)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_payload: dict[str, Any] = {}
    if args.config is not None:
        config_path = args.config
        if config_path.is_absolute() or ".." in config_path.parts or config_path.parts[:1] != ("config",):
            raise ValueError("--config must be workspace-relative under config/")
        config_payload = json.loads((ROOT / config_path).read_text(encoding="utf-8"))

    profile = str(config_payload.get("profile", args.profile))
    config = dict(training_profiles()[profile])
    if config_payload:
        for key, value in config_payload.items():
            if key not in {"schema_version", "paper_id", "target_ids", "execution_status", "method_note"}:
                config[key] = value
    for key in [
        "output_dir",
        "device",
        "train_samples",
        "eval_samples",
        "epochs",
        "hidden_dim",
        "message_passes",
        "k_neighbors",
        "target_lattice_spacing",
        "learning_rate",
        "max_updates",
        "checkpoint_every_updates",
        "prefetch_workers",
        "prefetch_buffer",
        "progress_every_updates",
        "batch_size",
        "dataset_manifest_path",
        "eval_dataset_manifest_path",
        "resume_checkpoint_path",
        "loss_mode",
        "source_ce_weight",
    ]:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    config["seed"] = args.seed
    config["profile"] = profile
    config["platform"] = platform_payload()

    output_dir = Path(config.pop("output_dir"))
    output_dir.mkdir(parents=True, exist_ok=True)
    run_request_path = output_dir / "run_request.json"
    run_request_path.write_text(json.dumps(json_ready(config), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "run_request": str(run_request_path), "config": json_ready(config)}, indent=2))
        return 0

    started = time.time()
    metrics = run_model_training_reproduction(
        output_dir=output_dir,
        train_samples=int(config["train_samples"]),
        eval_samples=int(config["eval_samples"]),
        initial_side=int(config["initial_side"]),
        target_side=int(config["target_side"]),
        k_neighbors=int(config["k_neighbors"]),
        epochs=int(config["epochs"]),
        hidden_dim=int(config["hidden_dim"]),
        message_passes=int(config["message_passes"]),
        seed=int(config["seed"]),
        device=str(config["device"]),
        learning_rate=float(config["learning_rate"]),
        loading_probability=float(config["loading_probability"]),
        target=f"{args.profile}_gnn_path_planner",
        graph_backend=str(config["graph_backend"]),
        target_lattice_spacing=config.get("target_lattice_spacing"),
        stream_samples=bool(config["stream_samples"]),
        checkpoint_every_updates=int(config["checkpoint_every_updates"]),
        max_updates=config.get("max_updates"),
        history_stride=int(config["history_stride"]),
        prefetch_workers=int(config["prefetch_workers"]),
        prefetch_buffer=int(config["prefetch_buffer"]),
        progress_every_updates=int(config["progress_every_updates"]),
        batch_size=int(config["batch_size"]),
        dataset_manifest_path=config.get("dataset_manifest_path"),
        eval_dataset_manifest_path=config.get("eval_dataset_manifest_path"),
        resume_checkpoint_path=config.get("resume_checkpoint_path"),
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
    )
    wall_time = time.time() - started
    metrics["runtime"] = {
        "wall_time_seconds": wall_time,
        "updates_per_second": float(metrics["training"]["updates"]) / wall_time if wall_time > 0 else None,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output_dir), "summary": metrics["summary"]}, indent=2))
    return 0


def platform_payload() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "gpu": None,
    }
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return payload
    if result.returncode == 0:
        payload["gpu"] = result.stdout.strip()
    return payload


def json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
