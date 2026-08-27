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

from atom_path_planner import (  # noqa: E402
    diagnose_assignment_sample,
    generate_ground_truth_dataset_shard,
    iter_dataset_manifest_samples,
    load_edge_scoring_model,
    predict_edge_logits,
    run_model_training_reproduction,
    summarize_assignment_diagnostics,
    transform_atom_target_scores,
)


def overfit_profiles() -> dict[str, dict[str, Any]]:
    return {
        "paper_target": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 8,
            "sample_count": 128,
            "seed_start": 260428690,
            "shard_id": "stage13-fixed-shard128",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_fixed_shard128",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_fixed_shard128_overfit",
            "resume_checkpoint_path": ROOT
            / "outputs"
            / "checks"
            / "paper_gnn_target_stage13_bce_source_ce_w025_u1024_eval64"
            / "model_state.pt",
            "resume_optimizer_state": True,
            "train_samples": 128,
            "eval_samples": 16,
            "epochs": 8,
            "max_updates": 1024,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.0005,
            "device": "cuda",
            "checkpoint_every_updates": 128,
            "history_stride": 16,
            "progress_every_updates": 16,
            "batch_size": 1,
            "loss_mode": "bce_source_ce",
            "source_ce_weight": 0.25,
            "train_diagnostics_samples": 128,
            "diagnostics_score_method": "logits",
            "diagnostics_saturation_threshold": 0.999,
            "seed": 260408690,
        },
        "source_ce_shard16": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 8,
            "sample_count": 16,
            "seed_start": 260428690,
            "shard_id": "stage13-source-ce-fixed-shard16",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_fixed_shard16",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_fixed_shard16_source_ce_overfit",
            "resume_checkpoint_path": ROOT
            / "outputs"
            / "checks"
            / "paper_gnn_target_stage13_bce_source_ce_w025_u1024_eval64"
            / "model_state.pt",
            "resume_optimizer_state": False,
            "train_samples": 16,
            "eval_samples": 4,
            "epochs": 64,
            "max_updates": 1024,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.0005,
            "device": "cuda",
            "checkpoint_every_updates": 128,
            "history_stride": 16,
            "progress_every_updates": 16,
            "batch_size": 1,
            "loss_mode": "source_ce",
            "source_ce_weight": 0.0,
            "train_diagnostics_samples": 16,
            "diagnostics_score_method": "logits",
            "diagnostics_saturation_threshold": 0.999,
            "seed": 260408690,
        },
        "source_ce_shard128": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 8,
            "sample_count": 128,
            "seed_start": 260428690,
            "shard_id": "stage13-fixed-shard128",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_fixed_shard128",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_fixed_shard128_source_ce_overfit",
            "resume_checkpoint_path": ROOT
            / "outputs"
            / "checks"
            / "paper_gnn_target_stage13_bce_source_ce_w025_u1024_eval64"
            / "model_state.pt",
            "resume_optimizer_state": False,
            "train_samples": 128,
            "eval_samples": 16,
            "epochs": 8,
            "max_updates": 1024,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.0005,
            "device": "cuda",
            "checkpoint_every_updates": 128,
            "history_stride": 16,
            "progress_every_updates": 16,
            "batch_size": 1,
            "loss_mode": "source_ce",
            "source_ce_weight": 0.0,
            "train_diagnostics_samples": 128,
            "diagnostics_score_method": "logits",
            "diagnostics_saturation_threshold": 0.999,
            "seed": 260408690,
        },
        "bce_source_ce_reset_shard16": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 8,
            "sample_count": 16,
            "seed_start": 260428690,
            "shard_id": "stage13-bce-source-ce-reset-fixed-shard16",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_fixed_shard16",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_fixed_shard16_bce_source_ce_reset_overfit",
            "resume_checkpoint_path": ROOT
            / "outputs"
            / "checks"
            / "paper_gnn_target_stage13_bce_source_ce_w025_u1024_eval64"
            / "model_state.pt",
            "resume_optimizer_state": False,
            "train_samples": 16,
            "eval_samples": 4,
            "epochs": 64,
            "max_updates": 1024,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.001,
            "device": "cuda",
            "checkpoint_every_updates": 128,
            "history_stride": 16,
            "progress_every_updates": 16,
            "batch_size": 1,
            "loss_mode": "bce_source_ce",
            "source_ce_weight": 0.25,
            "train_diagnostics_samples": 16,
            "diagnostics_score_method": "logits",
            "diagnostics_saturation_threshold": 0.999,
            "seed": 260408690,
        },
        "bce_source_ce_reset_shard128": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 8,
            "sample_count": 128,
            "seed_start": 260428690,
            "shard_id": "stage13-fixed-shard128",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_fixed_shard128",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_fixed_shard128_bce_source_ce_reset_overfit",
            "resume_checkpoint_path": ROOT
            / "outputs"
            / "checks"
            / "paper_gnn_target_stage13_bce_source_ce_w025_u1024_eval64"
            / "model_state.pt",
            "resume_optimizer_state": False,
            "train_samples": 128,
            "eval_samples": 16,
            "epochs": 8,
            "max_updates": 1024,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.001,
            "device": "cuda",
            "checkpoint_every_updates": 128,
            "history_stride": 16,
            "progress_every_updates": 16,
            "batch_size": 1,
            "loss_mode": "bce_source_ce",
            "source_ce_weight": 0.25,
            "train_diagnostics_samples": 128,
            "diagnostics_score_method": "logits",
            "diagnostics_saturation_threshold": 0.999,
            "seed": 260408690,
        },
        "canary": {
            "initial_side": 9,
            "target_side": 5,
            "k_neighbors": 16,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 1,
            "sample_count": 4,
            "seed_start": 260428690,
            "shard_id": "canary-fixed-shard4",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_canary_fixed_shard4",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_canary_fixed_shard_overfit",
            "resume_checkpoint_path": None,
            "resume_optimizer_state": True,
            "train_samples": 4,
            "eval_samples": 1,
            "epochs": 2,
            "max_updates": 8,
            "hidden_dim": 8,
            "message_passes": 2,
            "learning_rate": 0.01,
            "device": "cpu",
            "checkpoint_every_updates": 4,
            "history_stride": 1,
            "progress_every_updates": 1,
            "batch_size": 1,
            "loss_mode": "bce_source_ce",
            "source_ce_weight": 0.25,
            "train_diagnostics_samples": 4,
            "diagnostics_score_method": "logits",
            "diagnostics_saturation_threshold": 0.999,
            "seed": 260408690,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a fixed-shard overfit probe for 2604.08669 GNN training.")
    parser.add_argument("--profile", choices=sorted(overfit_profiles()), default="paper_target")
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume-checkpoint-path", type=Path)
    parser.add_argument("--reset-optimizer-state", dest="resume_optimizer_state", action="store_false", default=None)
    parser.add_argument("--sample-count", type=int)
    parser.add_argument("--target-lattice-spacing", type=float)
    parser.add_argument("--seed-start", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--train-samples", type=int)
    parser.add_argument("--eval-samples", type=int)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--max-updates", type=int)
    parser.add_argument("--hidden-dim", type=int)
    parser.add_argument("--message-passes", type=int)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--device")
    parser.add_argument("--checkpoint-every-updates", type=int)
    parser.add_argument("--history-stride", type=int)
    parser.add_argument("--progress-every-updates", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--loss-mode", choices=["bce", "target_ce", "source_ce", "bce_source_ce"])
    parser.add_argument("--source-ce-weight", type=float)
    parser.add_argument("--train-diagnostics-samples", type=int)
    parser.add_argument("--diagnostics-score-method", choices=["sigmoid", "logits", "source_softmax", "source_rank"])
    parser.add_argument("--diagnostics-saturation-threshold", type=float)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = dict(overfit_profiles()[args.profile])
    for key in [
        "dataset_dir",
        "output_dir",
        "resume_checkpoint_path",
        "resume_optimizer_state",
        "sample_count",
        "target_lattice_spacing",
        "seed_start",
        "workers",
        "train_samples",
        "eval_samples",
        "epochs",
        "max_updates",
        "hidden_dim",
        "message_passes",
        "learning_rate",
        "device",
        "checkpoint_every_updates",
        "history_stride",
        "progress_every_updates",
        "batch_size",
        "loss_mode",
        "source_ce_weight",
        "train_diagnostics_samples",
        "diagnostics_score_method",
        "diagnostics_saturation_threshold",
        "seed",
    ]:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    config["profile"] = args.profile
    config["platform"] = platform_payload()

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    request_path = output_dir / "fixed_shard_overfit_request.json"
    request_path.write_text(json.dumps(json_ready(config), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "request_path": str(request_path)}, indent=2, sort_keys=True))
        return 0

    started = time.time()
    result = run_fixed_shard_overfit(config)
    result["runtime"] = {"wall_time_seconds": time.time() - started}
    result_path = output_dir / "fixed_shard_overfit.json"
    result_path.write_text(json.dumps(json_ready(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output_dir), "decision": result["decision"]}, indent=2))
    return 0


def run_fixed_shard_overfit(config: dict[str, Any]) -> dict[str, object]:
    dataset_dir = Path(config["dataset_dir"])
    output_dir = Path(config["output_dir"])
    dataset_manifest = generate_ground_truth_dataset_shard(
        output_dir=dataset_dir,
        shard_id=str(config["shard_id"]),
        sample_count=int(config["sample_count"]),
        initial_side=int(config["initial_side"]),
        target_side=int(config["target_side"]),
        loading_probability=float(config["loading_probability"]),
        k_neighbors=int(config["k_neighbors"]),
        seed_start=int(config["seed_start"]),
        graph_backend=str(config["graph_backend"]),
        workers=int(config["workers"]),
        target_lattice_spacing=config.get("target_lattice_spacing"),
    )
    manifest_path = Path(dataset_manifest["manifest_path"])
    training = run_model_training_reproduction(
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
        target="fixed_shard_overfit_gnn_path_planner",
        graph_backend=str(config["graph_backend"]),
        target_lattice_spacing=config.get("target_lattice_spacing"),
        stream_samples=False,
        checkpoint_every_updates=int(config["checkpoint_every_updates"]),
        max_updates=int(config["max_updates"]) if config.get("max_updates") is not None else None,
        history_stride=int(config["history_stride"]),
        prefetch_workers=0,
        prefetch_buffer=0,
        progress_every_updates=int(config["progress_every_updates"]),
        batch_size=int(config["batch_size"]),
        dataset_manifest_path=manifest_path,
        resume_checkpoint_path=Path(config["resume_checkpoint_path"]) if config.get("resume_checkpoint_path") else None,
        resume_optimizer_state=bool(config["resume_optimizer_state"]),
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
    )
    train_diagnostics = diagnose_fixed_shard_training_set(
        checkpoint_path=Path(training["artifacts"]["checkpoint_path"]),  # type: ignore[index]
        manifest_path=manifest_path,
        output_dir=output_dir,
        device=str(config["device"]),
        max_samples=int(config["train_diagnostics_samples"]),
        score_method=str(config.get("diagnostics_score_method", "logits")),
        saturation_threshold=float(config.get("diagnostics_saturation_threshold", 0.999)),
    )
    decision = overfit_decision(training=training, train_diagnostics=train_diagnostics)
    return {
        "status": "completed",
        "paper_id": "2604.08669",
        "config": json_ready(config),
        "dataset": dataset_manifest,
        "training": training,
        "train_diagnostics": train_diagnostics,
        "decision": decision,
    }


def diagnose_fixed_shard_training_set(
    *,
    checkpoint_path: Path,
    manifest_path: Path,
    output_dir: Path,
    device: str,
    max_samples: int,
    score_method: str = "logits",
    saturation_threshold: float = 0.999,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "train_diagnostics_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    model = load_edge_scoring_model(checkpoint_path, device=device)
    rows: list[dict[str, object]] = []
    started = time.monotonic()
    for idx, sample in enumerate(iter_dataset_manifest_samples(manifest_path), start=1):
        if idx > max_samples:
            break
        sample_started = time.monotonic()
        logits = predict_edge_logits(model, sample)
        scores = transform_atom_target_scores(sample, logits, method=score_method)
        saturation = score_saturation_diagnostics(
            scores,
            threshold=saturation_threshold,
            applies=score_method == "sigmoid",
        )
        if score_method == "sigmoid" and saturation["upper_saturation_fraction"] > 0.95:
            raise ValueError(
                "sigmoid diagnostics saturated; use diagnostics_score_method=logits "
                f"(upper_saturation_fraction={saturation['upper_saturation_fraction']:.6f})"
            )
        row = diagnose_assignment_sample(sample, scores)
        row["sample_index"] = idx
        row["score_method"] = score_method
        row["score_saturation"] = saturation
        rows.append(row)
        write_progress(
            progress_path,
            {
                "event": "sample",
                "sample_index": idx,
                "max_samples": max_samples,
                "average_distance_gap": row["assignment"]["average_distance_gap"],  # type: ignore[index]
                "rank1_rate": row["source_rank"]["rank1_rate"],  # type: ignore[index]
                "score_method": score_method,
                "upper_saturation_fraction": saturation["upper_saturation_fraction"],
                "elapsed_seconds": time.monotonic() - started,
                "sample_seconds": time.monotonic() - sample_started,
            },
        )
    summary = summarize_assignment_diagnostics(rows)
    write_progress(progress_path, {"event": "completed", "samples": len(rows), "elapsed_seconds": time.monotonic() - started})
    rows_path = output_dir / "train_diagnostic_rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    result = {
        "status": "completed",
        "checkpoint_path": str(checkpoint_path),
        "manifest_path": str(manifest_path),
        "score_method": score_method,
        "summary": summary,
        "artifacts": {
            "progress_path": str(progress_path),
            "rows_path": str(rows_path),
        },
    }
    (output_dir / "train_diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def score_saturation_diagnostics(scores: Any, *, threshold: float, applies: bool) -> dict[str, object]:
    import numpy as np

    values = np.asarray(scores, dtype=np.float64)
    base: dict[str, object] = {"applies": bool(applies), "count": int(values.size)}
    if not applies:
        return {
            **base,
            "upper_saturation_fraction": 0.0,
            "lower_saturation_fraction": 0.0,
            "tie_unique_fraction": float(len(np.unique(values)) / values.size) if values.size else 0.0,
        }
    if values.size == 0:
        return {
            **base,
            "upper_saturation_fraction": 0.0,
            "lower_saturation_fraction": 0.0,
            "tie_unique_fraction": 0.0,
        }
    unique_values = len(np.unique(values))
    return {
        **base,
        "upper_saturation_fraction": float(np.mean(values >= float(threshold))),
        "lower_saturation_fraction": float(np.mean(values <= 1.0 - float(threshold))),
        "tie_unique_fraction": float(unique_values / values.size),
    }


def overfit_decision(*, training: dict[str, object], train_diagnostics: dict[str, object]) -> dict[str, object]:
    training_state = training["training"]  # type: ignore[index]
    loss_initial = training_state.get("loss_initial")  # type: ignore[union-attr]
    loss_final = training_state.get("loss_final")  # type: ignore[union-attr]
    loss_ratio = None
    if isinstance(loss_initial, (int, float)) and isinstance(loss_final, (int, float)) and loss_initial > 0:
        loss_ratio = float(loss_final) / float(loss_initial)
    summary = train_diagnostics["summary"]  # type: ignore[index]
    rank1 = float(summary["source_rank"]["mean_rank1_rate"])  # type: ignore[index]
    average_gap = float(summary["assignment_gap"]["mean_average_distance_gap"])  # type: ignore[index]
    passed = bool(loss_ratio is not None and loss_ratio <= 0.1 and rank1 >= 0.9 and average_gap <= 0.05)
    return {
        "status": "overfit_passed" if passed else "overfit_not_yet_passed",
        "loss_ratio": loss_ratio,
        "mean_train_rank1_rate": rank1,
        "mean_train_average_distance_gap": average_gap,
        "go_criteria": {
            "loss_ratio_lte": 0.1,
            "mean_train_rank1_rate_gte": 0.9,
            "mean_train_average_distance_gap_lte": 0.05,
        },
    }


def write_progress(path: Path, payload: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


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
