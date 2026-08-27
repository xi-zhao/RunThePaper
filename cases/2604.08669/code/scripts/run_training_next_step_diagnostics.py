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

import numpy as np
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from atom_path_planner import (  # noqa: E402
    EDGE_ATOM_TO_TARGET,
    EdgeScoringGNN,
    assignment_log_sinkhorn_cross_entropy,
    assignment_sinkhorn_cross_entropy,
    assignment_structured_margin_loss,
    assignment_distances,
    assignment_metrics,
    atom_target_score_distribution,
    binary_atom_target_cross_entropy,
    centered_square_lattice,
    dataset_sample_paths,
    decode_assignment_from_edge_scores,
    decode_assignment_with_modified_auction,
    diagnose_assignment_sample,
    generate_ground_truth_dataset_shard,
    iter_dataset_manifest_samples,
    load_edge_scoring_model,
    load_graph_sample_npz,
    predict_edge_logits,
    predict_edge_scores,
    resolve_torch_device,
    run_model_training_reproduction,
    sample_loaded_atoms,
    sha256_file,
    source_hard_negative_margin_loss,
    source_assignment_cross_entropy,
    source_temperature_cross_entropy,
    source_topk_hard_negative_cross_entropy,
    source_wise_positive_rank_diagnostics,
    squared_distances,
    target_assignment_cross_entropy,
    target_hard_negative_margin_loss,
    target_temperature_cross_entropy,
    target_topk_hard_negative_cross_entropy,
    torch,
    transform_atom_target_scores,
)


def diagnostic_profiles() -> dict[str, dict[str, Any]]:
    paper_single_sample = {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 1,
            "sample_count": 1,
            "seed_start": 260428690,
            "shard_id": "stage13-next-step-paper-single-sample-probe",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_next_step_single_sample_probe",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_next_step_single_sample_probe",
            "train_samples": 1,
            "eval_samples": 0,
            "epochs": 500,
            "max_updates": 500,
            "hidden_dim": 64,
            "message_passes": 6,
            "learning_rate": 0.01,
            "device": "cuda",
            "checkpoint_every_updates": 0,
            "history_stride": 10,
            "progress_every_updates": 10,
            "batch_size": 1,
            "model_arch": "plain",
            "score_head": "shallow",
            "loss_mode": "bce_source_ce",
            "source_ce_weight": 0.25,
            "margin": 1.0,
            "temperature": 0.25,
            "hard_negative_k": 3,
            "sinkhorn_iterations": 30,
            "max_grad_norm": None,
            "oracle_margin": 20.0,
            "go_loss_ratio_lte": 0.5,
            "go_rank1_rate_gte": 0.8,
            "go_average_gap_lte": 0.05,
            "loss_target_modes": ["source_ce", "source_margin", "source_ce_margin", "source_target_topk_hard_negative_ce", "assignment_margin"],
            "loss_target_go_rank1_rate_gte": 0.8,
            "loss_target_go_mean_positive_rank_lte": 2.0,
            "loss_target_go_average_gap_lte": 1.5,
            "loss_target_score_method": "logits",
            "assignment_margin_max_targets": 256,
            "gradient_probe_updates": [0, 1, 10, 50, 100, 250, 500],
            "gradient_vanishing_ratio_lte": 1e-3,
            "logit_separation_gte": 0.1,
            "score_alignment_methods": ["sigmoid", "logits", "source_softmax", "source_rank"],
            "score_alignment_decoders": ["score_hungarian", "modified_auction"],
            "score_alignment_gap_go_lte": 1.5,
            "score_alignment_gap_no_go_gte": 2.0,
            "score_interpolation_alphas": [0.0, 0.25, 0.5, 0.75, 1.0],
            "score_interpolation_method": "sigmoid",
            "score_interpolation_oracle_gap_lte": 1e-6,
            "oracle_feature_scale": 2.0,
            "oracle_feature_go_loss_ratio_lte": 0.2,
            "oracle_feature_go_rank1_rate_gte": 0.95,
            "oracle_feature_go_average_gap_lte": 0.01,
            "assignment_audit_checkpoint_path": None,
            "assignment_audit_score_method": "sigmoid",
            "assignment_audit_decoders": ["score_hungarian", "modified_auction"],
            "assignment_audit_relative_gap_lte": 0.005,
            "assignment_audit_average_gap_lte": 0.05,
            "assignment_audit_forced_top1_limit": 64,
            "assignment_audit_forced_top1_relative_gap_lte": 0.005,
            "regret_audit_label_regret_median_no_go_gt": 0.005,
            "regret_audit_model_regret_median_go_lte": 0.01,
            "resume_checkpoint_path": None,
            "resume_optimizer_state": True,
            "seed": 260408690,
    }
    thin_k32_single_sample = {
        **paper_single_sample,
        "k_neighbors": 32,
        "shard_id": "stage13-next-step-paper-single-sample-thin-k32-probe",
        "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_next_step_single_sample_thin_k32_probe",
        "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_next_step_single_sample_thin_k32_probe",
        "epochs": 200,
        "max_updates": 200,
        "learning_rate": 0.001,
        "history_stride": 5,
        "progress_every_updates": 5,
        "model_arch": "residual_layernorm",
        "score_head": "deep_edge_mlp",
        "loss_mode": "source_target_topk_hard_negative_ce",
        "temperature": 0.25,
        "hard_negative_k": 3,
        "max_grad_norm": 1.0,
        "loss_target_modes": ["source_target_topk_hard_negative_ce"],
        "gradient_probe_updates": [0, 1, 5, 20, 100, 200],
    }
    medium_k32_single_sample = {
        **thin_k32_single_sample,
        "initial_side": 50,
        "target_side": 25,
        "target_lattice_spacing": (50 - 1) / (25 - 1),
        "shard_id": "stage13-next-step-medium-single-sample-k32-probe",
        "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_next_step_medium_single_sample_k32_probe",
        "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_next_step_medium_single_sample_k32_probe",
        "epochs": 300,
        "max_updates": 300,
        "gradient_probe_updates": [0, 1, 5, 20, 100, 300],
    }
    medium_k32_regret_audit = {
        **medium_k32_single_sample,
        "sample_count": 32,
        "shard_id": "stage13-medium-k32-regret-audit-pilot",
        "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_medium_k32_regret_audit_pilot",
        "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_medium_k32_regret_audit_pilot",
        "assignment_audit_forced_top1_limit": 8,
    }
    paper_metric_contract = {
        **paper_single_sample,
        "sample_count": 8,
        "shard_id": "stage13-paper-hungarian-metric-contract",
        "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_target_stage13_metric_contract_probe",
        "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_metric_contract_probe",
        "paper_hungarian_average_distance": 0.5112,
        "paper_hungarian_max_distance": 1.82,
        "paper_gnn_average_distance": 0.5120,
        "paper_gnn_max_distance": 1.93,
        "paper_sample_count": 1024,
        "metric_contract_min_decision_samples": 4,
        "metric_contract_average_ratio_lte": 1.005,
        "metric_contract_max_ratio_lte": 1.06,
    }
    return {
        "paper_single_sample": paper_single_sample,
        "paper_single_sample_thin_k32": thin_k32_single_sample,
        "paper_medium_single_sample_k32": medium_k32_single_sample,
        "paper_medium_regret_audit_k32": medium_k32_regret_audit,
        "paper_hungarian_metric_contract": paper_metric_contract,
        "canary": {
            "initial_side": 9,
            "target_side": 5,
            "k_neighbors": 16,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "workers": 1,
            "sample_count": 1,
            "seed_start": 260428690,
            "shard_id": "canary-single-sample-probe",
            "dataset_dir": ROOT / "outputs" / "datasets" / "paper_gnn_canary_single_sample_probe",
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_canary_single_sample_probe",
            "train_samples": 1,
            "eval_samples": 0,
            "epochs": 8,
            "max_updates": 8,
            "hidden_dim": 16,
            "message_passes": 2,
            "learning_rate": 0.01,
            "device": "cpu",
            "checkpoint_every_updates": 0,
            "history_stride": 1,
            "progress_every_updates": 1,
            "batch_size": 1,
            "model_arch": "plain",
            "score_head": "shallow",
            "loss_mode": "bce_source_ce",
            "source_ce_weight": 0.25,
            "margin": 1.0,
            "temperature": 0.25,
            "hard_negative_k": 3,
            "sinkhorn_iterations": 30,
            "max_grad_norm": None,
            "oracle_margin": 20.0,
            "go_loss_ratio_lte": 0.5,
            "go_rank1_rate_gte": 0.8,
            "go_average_gap_lte": 0.05,
            "loss_target_modes": ["source_ce", "source_margin", "source_ce_margin", "assignment_margin"],
            "loss_target_go_rank1_rate_gte": 0.8,
            "loss_target_go_mean_positive_rank_lte": 2.0,
            "loss_target_go_average_gap_lte": 1.5,
            "loss_target_score_method": "logits",
            "assignment_margin_max_targets": 256,
            "gradient_probe_updates": [0, 1, 2, 8],
            "gradient_vanishing_ratio_lte": 1e-3,
            "logit_separation_gte": 0.1,
            "score_alignment_methods": ["sigmoid", "logits", "source_softmax", "source_rank"],
            "score_alignment_decoders": ["score_hungarian", "modified_auction"],
            "score_alignment_gap_go_lte": 1.5,
            "score_alignment_gap_no_go_gte": 2.0,
            "score_interpolation_alphas": [0.0, 0.25, 0.5, 0.75, 1.0],
            "score_interpolation_method": "sigmoid",
            "score_interpolation_oracle_gap_lte": 1e-6,
            "oracle_feature_scale": 2.0,
            "oracle_feature_go_loss_ratio_lte": 0.2,
            "oracle_feature_go_rank1_rate_gte": 0.95,
            "oracle_feature_go_average_gap_lte": 0.01,
            "assignment_audit_checkpoint_path": None,
            "assignment_audit_score_method": "sigmoid",
            "assignment_audit_decoders": ["score_hungarian", "modified_auction"],
            "assignment_audit_relative_gap_lte": 0.005,
            "assignment_audit_average_gap_lte": 0.05,
            "assignment_audit_forced_top1_limit": 8,
            "assignment_audit_forced_top1_relative_gap_lte": 0.005,
            "regret_audit_label_regret_median_no_go_gt": 0.005,
            "regret_audit_model_regret_median_go_lte": 0.01,
            "target_lattice_spacing": None,
            "paper_hungarian_average_distance": 0.0,
            "paper_hungarian_max_distance": 0.0,
            "paper_gnn_average_distance": 0.0,
            "paper_gnn_max_distance": 0.0,
            "paper_sample_count": 1,
            "metric_contract_min_decision_samples": 1,
            "metric_contract_average_ratio_lte": 1.005,
            "metric_contract_max_ratio_lte": 1.06,
            "resume_checkpoint_path": None,
            "resume_optimizer_state": True,
            "seed": 260408690,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run next-step training diagnostics for the 2604.08669 GNN training lane."
    )
    parser.add_argument("--profile", choices=sorted(diagnostic_profiles()), default="paper_single_sample")
    parser.add_argument(
        "--mode",
        choices=[
            "oracle_loss",
            "single_sample_overfit",
            "gradient_flow",
            "score_alignment",
            "score_interpolation",
            "loss_target",
            "oracle_feature_topk",
            "assignment_cost_gap",
            "regret_audit",
            "metric_contract",
            "all",
        ],
        default="all",
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--sample-count", type=int)
    parser.add_argument("--target-lattice-spacing", type=float)
    parser.add_argument("--device")
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--max-updates", type=int)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--hidden-dim", type=int)
    parser.add_argument("--message-passes", type=int)
    parser.add_argument("--model-arch", choices=["plain", "residual_layernorm"])
    parser.add_argument("--score-head", choices=["shallow", "deep_edge_mlp"])
    parser.add_argument(
        "--loss-mode",
        choices=[
            "bce",
            "target_ce",
            "target_temperature_ce",
            "source_ce",
            "source_temperature_ce",
            "source_target_temperature_ce",
            "source_topk_hard_negative_ce",
            "target_topk_hard_negative_ce",
            "source_target_topk_hard_negative_ce",
            "assignment_sinkhorn_ce",
            "assignment_log_sinkhorn_ce",
            "bce_source_ce",
            "source_target_ce",
            "source_margin",
            "source_ce_margin",
            "target_margin",
            "source_target_margin",
            "assignment_margin",
        ],
    )
    parser.add_argument("--source-ce-weight", type=float)
    parser.add_argument("--margin", type=float)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--hard-negative-k", type=int)
    parser.add_argument("--sinkhorn-iterations", type=int)
    parser.add_argument("--max-grad-norm", type=float)
    parser.add_argument("--oracle-feature-scale", type=float)
    parser.add_argument("--assignment-audit-checkpoint-path", type=Path)
    parser.add_argument(
        "--assignment-audit-score-method",
        choices=["sigmoid", "logits", "source_softmax", "source_rank"],
    )
    parser.add_argument("--assignment-audit-forced-top1-limit", type=int)
    parser.add_argument("--resume-checkpoint-path", type=Path)
    parser.add_argument(
        "--no-resume-optimizer-state",
        dest="resume_optimizer_state",
        action="store_false",
        default=None,
    )
    parser.add_argument("--assignment-margin-max-targets", type=int)
    parser.add_argument(
        "--loss-target-score-method",
        choices=["sigmoid", "logits", "source_softmax", "source_rank"],
    )
    parser.add_argument(
        "--loss-target-modes",
        nargs="+",
        choices=[
            "source_ce",
            "source_temperature_ce",
            "source_margin",
            "source_ce_margin",
            "source_target_ce",
            "target_temperature_ce",
            "source_target_temperature_ce",
            "source_topk_hard_negative_ce",
            "target_topk_hard_negative_ce",
            "source_target_topk_hard_negative_ce",
            "assignment_sinkhorn_ce",
            "assignment_log_sinkhorn_ce",
            "target_margin",
            "source_target_margin",
            "assignment_margin",
        ],
    )
    parser.add_argument(
        "--score-alignment-decoders",
        nargs="+",
        choices=["score_hungarian", "modified_auction"],
    )
    parser.add_argument("--score-interpolation-alphas", nargs="+", type=float)
    parser.add_argument(
        "--score-interpolation-method",
        choices=["sigmoid", "logits", "source_softmax", "source_rank"],
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = dict(diagnostic_profiles()[args.profile])
    for key in [
        "output_dir",
        "dataset_dir",
        "sample_count",
        "target_lattice_spacing",
        "device",
        "epochs",
        "max_updates",
        "learning_rate",
        "hidden_dim",
        "message_passes",
        "model_arch",
        "score_head",
        "loss_mode",
        "source_ce_weight",
        "margin",
        "temperature",
        "hard_negative_k",
        "sinkhorn_iterations",
        "max_grad_norm",
        "oracle_feature_scale",
        "assignment_audit_checkpoint_path",
        "assignment_audit_score_method",
        "assignment_audit_forced_top1_limit",
        "resume_checkpoint_path",
        "resume_optimizer_state",
        "assignment_margin_max_targets",
        "loss_target_score_method",
        "score_interpolation_method",
    ]:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    if args.score_alignment_decoders is not None:
        config["score_alignment_decoders"] = list(args.score_alignment_decoders)
    if args.score_interpolation_alphas is not None:
        config["score_interpolation_alphas"] = list(args.score_interpolation_alphas)
    if args.loss_target_modes is not None:
        config["loss_target_modes"] = list(args.loss_target_modes)
    config["profile"] = args.profile
    config["mode"] = args.mode
    config["platform"] = platform_payload()

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    request_path = output_dir / "next_step_diagnostics_request.json"
    request_path.write_text(json.dumps(json_ready(config), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "run_request": str(request_path)}, indent=2, sort_keys=True))
        return 0

    started = time.time()
    result: dict[str, object] = {
        "status": "completed",
        "artifact_type": "next_step_training_diagnostics",
        "paper_id": "2604.08669",
        "config": json_ready(config),
        "artifacts": {"run_request_path": str(request_path)},
    }
    if args.mode in {"oracle_loss", "all"}:
        result["oracle_loss_sanity"] = run_oracle_loss_sanity(config)
    if args.mode in {"single_sample_overfit", "all"}:
        result["single_sample_overfit_probe"] = run_single_sample_overfit_probe(config)
    if args.mode == "gradient_flow":
        result["gradient_flow_probe"] = run_gradient_flow_probe(config)
    if args.mode == "score_alignment":
        result["score_alignment_probe"] = run_score_alignment_probe(config)
    if args.mode == "score_interpolation":
        result["score_interpolation_probe"] = run_score_interpolation_probe(config)
    if args.mode == "loss_target":
        result["loss_target_probe"] = run_loss_target_probe(config)
    if args.mode == "oracle_feature_topk":
        result["oracle_feature_topk_probe"] = run_oracle_feature_topk_probe(config)
    if args.mode == "assignment_cost_gap":
        result["assignment_cost_gap_probe"] = run_assignment_cost_gap_probe(config)
    if args.mode == "regret_audit":
        result["regret_audit_probe"] = run_regret_audit_probe(config)
    if args.mode == "metric_contract":
        result["paper_hungarian_metric_contract"] = run_paper_hungarian_metric_contract(config)
    result["runtime"] = {"wall_time_seconds": time.time() - started}

    result_path = output_dir / "next_step_diagnostics.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output_dir)}, indent=2, sort_keys=True))
    return 0


def run_oracle_loss_sanity(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    sample = next(iter_dataset_manifest_samples(Path(manifest["manifest_path"])))
    logits = oracle_edge_logits(sample, margin=float(config["oracle_margin"]))
    losses = loss_components(
        sample=sample,
        logits=logits,
        device=str(config["device"]),
        source_ce_weight=float(config["source_ce_weight"]),
    )
    diagnostics = diagnose_assignment_sample(sample, sigmoid_numpy(logits))
    result = {
        "status": "completed",
        "artifact_type": "oracle_loss_sanity",
        "manifest_path": str(manifest["manifest_path"]),
        "losses": losses,
        "assignment": diagnostics["assignment"],
        "source_rank": diagnostics["source_rank"],
    }
    (output_dir / "oracle_loss_sanity.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_oracle_feature_topk_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    sample_paths = dataset_sample_paths(manifest_path)
    if not sample_paths:
        raise ValueError("oracle feature top-k probe requires at least one manifest sample")

    sample_path = sample_paths[0]
    sample_sha_before = sha256_file(sample_path)
    base_sample = load_graph_sample_npz(sample_path)
    sample_sha_after_load = sha256_file(sample_path)
    sample = with_oracle_edge_feature(base_sample, feature_scale=float(config.get("oracle_feature_scale", 1.0)))

    torch_device = resolve_torch_device(str(config["device"]))
    torch.manual_seed(int(config["seed"]))
    model = EdgeScoringGNN(
        node_dim=int(sample.node_features.shape[1]),
        edge_dim=int(sample.edge_features.shape[1]),
        hidden_dim=int(config["hidden_dim"]),
        message_passes=int(config["message_passes"]),
        model_arch=str(config["model_arch"]),
        score_head=str(config["score_head"]),
    )
    model.to(torch_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))

    progress_path = output_dir / "oracle_feature_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    max_updates = int(config["max_updates"])
    started = time.monotonic()
    write_gradient_progress(progress_path, started=started, event="started", update=0, target_updates=max_updates)

    initial_snapshot = gradient_flow_snapshot(
        model=model,
        sample=sample,
        optimizer=optimizer,
        device=torch_device,
        update=0,
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
        margin=float(config["margin"]),
        temperature=float(config["temperature"]),
        hard_negative_k=int(config["hard_negative_k"]),
        sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        max_grad_norm=config.get("max_grad_norm"),
        apply_step=False,
    )
    loss_final = float(initial_snapshot["loss"])
    for update in range(1, max_updates + 1):
        loss_final = train_gradient_probe_step(
            model=model,
            sample=sample,
            optimizer=optimizer,
            device=torch_device,
            loss_mode=str(config["loss_mode"]),
            source_ce_weight=float(config["source_ce_weight"]),
            margin=float(config["margin"]),
            temperature=float(config["temperature"]),
            hard_negative_k=int(config["hard_negative_k"]),
            sinkhorn_iterations=int(config["sinkhorn_iterations"]),
            max_grad_norm=config.get("max_grad_norm"),
        )
        progress_every = int(config.get("progress_every_updates", 0))
        if progress_every > 0 and (update % progress_every == 0 or update == max_updates):
            write_gradient_progress(
                progress_path,
                started=started,
                event="update",
                update=update,
                target_updates=max_updates,
                loss=loss_final,
            )

    final_snapshot = gradient_flow_snapshot(
        model=model,
        sample=sample,
        optimizer=optimizer,
        device=torch_device,
        update=max_updates,
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
        margin=float(config["margin"]),
        temperature=float(config["temperature"]),
        hard_negative_k=int(config["hard_negative_k"]),
        sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        max_grad_norm=config.get("max_grad_norm"),
        apply_step=False,
    )
    loss_final = float(final_snapshot["loss"])
    write_gradient_progress(
        progress_path,
        started=started,
        event="completed",
        update=max_updates,
        target_updates=max_updates,
        loss=loss_final,
    )

    sample_sha_after_training = sha256_file(sample_path)
    scores = predict_edge_scores(model, sample)
    diagnostics = diagnose_assignment_sample(sample, scores)
    train_diagnostics = flat_training_diagnostics(diagnostics)
    training = {
        "updates": max_updates,
        "learning_rate": float(config["learning_rate"]),
        "hidden_dim": int(config["hidden_dim"]),
        "message_passes": int(config["message_passes"]),
        "loss_mode": str(config["loss_mode"]),
        "source_ce_weight": float(config["source_ce_weight"]),
        "runtime_seconds": time.monotonic() - started,
        "loss_initial": float(initial_snapshot["loss"]),
        "loss_final": loss_final,
    }
    result = {
        "status": "completed",
        "artifact_type": "oracle_feature_topk_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "sample_path": str(sample_path),
        "sample_stability": {
            "sample_sha256_before": sample_sha_before,
            "sample_sha256_after_load": sample_sha_after_load,
            "sample_sha256_after_training": sample_sha_after_training,
            "sample_hash_stable": sample_sha_before == sample_sha_after_load == sample_sha_after_training,
        },
        "oracle_feature": {
            "feature_scale": float(config.get("oracle_feature_scale", 1.0)),
            "base_edge_dim": int(base_sample.edge_features.shape[1]),
            "augmented_edge_dim": int(sample.edge_features.shape[1]),
        },
        "model": {
            "node_dim": int(sample.node_features.shape[1]),
            "edge_dim": int(sample.edge_features.shape[1]),
            "hidden_dim": int(config["hidden_dim"]),
            "message_passes": int(config["message_passes"]),
            "model_arch": str(config["model_arch"]),
            "score_head": str(config["score_head"]),
        },
        "training": training,
        "snapshots": {
            "initial": initial_snapshot,
            "final": final_snapshot,
        },
        "train_diagnostics": train_diagnostics,
        "decision": oracle_feature_decision(
            config=config,
            training=training,
            train_diagnostics=train_diagnostics,
        ),
        "artifacts": {"progress_path": str(progress_path)},
    }
    (output_dir / "oracle_feature_topk_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_assignment_cost_gap_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    sample = next(iter_dataset_manifest_samples(manifest_path))

    checkpoint_path = config.get("assignment_audit_checkpoint_path") or config.get("resume_checkpoint_path")
    if checkpoint_path:
        model = load_edge_scoring_model(Path(checkpoint_path), device=str(config["device"]))
        edge_values = predict_edge_logits(model, sample)
        score_source = {"type": "checkpoint", "path": str(checkpoint_path)}
    else:
        edge_values = oracle_edge_logits(sample, margin=float(config["oracle_margin"])).detach().cpu().numpy()
        score_source = {"type": "oracle_scores", "margin": float(config["oracle_margin"])}

    score_method = str(config.get("assignment_audit_score_method", "sigmoid"))
    edge_scores = transform_atom_target_scores(sample, np.asarray(edge_values, dtype=np.float64), method=score_method)
    cost_baselines = assignment_cost_baselines(sample)
    decoders: dict[str, object] = {}
    for decoder_name in config.get("assignment_audit_decoders", ["score_hungarian", "modified_auction"]):
        if decoder_name == "score_hungarian":
            assignment = decode_assignment_from_edge_scores(sample, edge_scores)
        elif decoder_name == "modified_auction":
            assignment = decode_assignment_with_modified_auction(sample, edge_scores)
        else:
            raise ValueError(f"unsupported assignment audit decoder: {decoder_name}")
        metrics = assignment_metrics(sample, assignment)
        decoders[str(decoder_name)] = assignment_cost_gap_summary(
            sample=sample,
            metrics=metrics,
            baselines=cost_baselines,
        )

    source_rank = source_wise_positive_rank_diagnostics(sample, edge_scores)
    score_distribution = diagnose_assignment_sample(sample, edge_scores)["score_distribution"]
    forced_top1 = forced_top1_degeneracy_audit(
        sample=sample,
        edge_scores=edge_scores,
        limit=int(config.get("assignment_audit_forced_top1_limit", 0)),
        relative_gap_lte=float(config.get("assignment_audit_forced_top1_relative_gap_lte", 0.005)),
        baselines=cost_baselines,
    )
    result = {
        "status": "completed",
        "artifact_type": "assignment_cost_gap_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "score_source": score_source,
        "score_method": score_method,
        "cost_baselines": cost_baselines,
        "decoders": decoders,
        "source_rank": source_rank,
        "score_distribution": score_distribution,
        "forced_top1_degeneracy": forced_top1,
        "decision": assignment_cost_gap_decision(config=config, decoders=decoders, forced_top1=forced_top1),
    }
    (output_dir / "assignment_cost_gap_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_regret_audit_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    progress_path = output_dir / "regret_audit_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    checkpoint_path = config.get("assignment_audit_checkpoint_path") or config.get("resume_checkpoint_path")
    model = None
    score_source: dict[str, object]
    if checkpoint_path:
        model = load_edge_scoring_model(Path(checkpoint_path), device=str(config["device"]))
        score_source = {"type": "checkpoint", "path": str(checkpoint_path)}
    else:
        score_source = {"type": "none_label_regret_only"}

    started = time.monotonic()
    rows: list[dict[str, object]] = []
    samples = list(iter_dataset_manifest_samples(manifest_path))
    total_samples = len(samples)
    for sample_index, sample in enumerate(samples):
        baselines = assignment_cost_baselines(sample)
        label = baselines["label_assignment"]  # type: ignore[index]
        candidate = baselines["candidate_optimum"]  # type: ignore[index]
        label_total = float(label["total_distance"])  # type: ignore[index]
        candidate_total = float(candidate["total_distance"])  # type: ignore[index]
        row: dict[str, object] = {
            "sample_index": sample_index,
            "atom_count": int(len(sample.atom_positions)),
            "target_count": int(sample.target_count),
            "edge_count": int(sample.edge_index.shape[1]),
            "label_total_distance": label_total,
            "candidate_optimal_total_distance": candidate_total,
            "label_total_gap_vs_candidate": label_total - candidate_total,
            "label_relative_regret": (label_total - candidate_total) / max(abs(candidate_total), 1e-12),
        }
        if model is not None:
            edge_values = predict_edge_logits(model, sample)
            score_method = str(config.get("assignment_audit_score_method", "sigmoid"))
            edge_scores = transform_atom_target_scores(sample, np.asarray(edge_values, dtype=np.float64), method=score_method)
            decoder_rows: dict[str, object] = {}
            for decoder_name in config.get("assignment_audit_decoders", ["score_hungarian", "modified_auction"]):
                if decoder_name == "score_hungarian":
                    assignment = decode_assignment_from_edge_scores(sample, edge_scores)
                elif decoder_name == "modified_auction":
                    assignment = decode_assignment_with_modified_auction(sample, edge_scores)
                else:
                    raise ValueError(f"unsupported regret audit decoder: {decoder_name}")
                metrics = assignment_metrics(sample, assignment)
                decoder_rows[str(decoder_name)] = assignment_cost_gap_summary(
                    sample=sample,
                    metrics=metrics,
                    baselines=baselines,
                )
            forced = forced_top1_degeneracy_audit(
                sample=sample,
                edge_scores=edge_scores,
                limit=int(config.get("assignment_audit_forced_top1_limit", 0)),
                relative_gap_lte=float(config.get("assignment_audit_forced_top1_relative_gap_lte", 0.005)),
                baselines=baselines,
            )
            source_rank = source_wise_positive_rank_diagnostics(sample, edge_scores)
            row["model"] = {
                "score_method": score_method,
                "decoders": decoder_rows,
                "source_rank": source_rank,
                "forced_top1_degeneracy": forced,
            }
        rows.append(row)
        write_regret_progress(
            progress_path,
            started=started,
            sample_index=sample_index + 1,
            total_samples=total_samples,
            label_relative_regret=float(row["label_relative_regret"]),
        )

    summary = regret_audit_summary(rows)
    result = {
        "status": "completed",
        "artifact_type": "regret_audit_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "score_source": score_source,
        "summary": summary,
        "decision": regret_audit_decision(config=config, summary=summary, has_model=model is not None),
        "samples": rows,
        "artifacts": {"progress_path": str(progress_path)},
    }
    (output_dir / "regret_audit_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_paper_hungarian_metric_contract(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "paper_hungarian_metric_contract_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    target_positions = metric_contract_target_positions(config)
    started = time.monotonic()
    rows: list[dict[str, object]] = []
    sample_count = int(config["sample_count"])
    for sample_index in range(sample_count):
        seed = int(config["seed_start"]) + sample_index
        atoms = sample_loaded_atoms(
            int(config["initial_side"]),
            float(config["loading_probability"]),
            len(target_positions),
            seed,
        )
        squared_cost = squared_distances(atoms, target_positions)
        euclidean_cost = np.sqrt(squared_cost)
        squared_assignment = solve_assignment_from_cost(squared_cost)
        euclidean_assignment = solve_assignment_from_cost(euclidean_cost)
        squared_metrics = assignment_distance_payload(atoms, target_positions, squared_assignment)
        euclidean_metrics = assignment_distance_payload(atoms, target_positions, euclidean_assignment)
        row = {
            "sample_index": sample_index,
            "seed": seed,
            "atom_count": int(len(atoms)),
            "target_count": int(len(target_positions)),
            "squared_label": squared_metrics,
            "euclidean_label": euclidean_metrics,
            "match_consistency": assignment_match_consistency(squared_assignment, euclidean_assignment),
            "A_vs_B_euclidean_average_regret": relative_gap(
                float(squared_metrics["euclidean_average"]),
                float(euclidean_metrics["euclidean_average"]),
            ),
            "A_vs_B_euclidean_max_regret": relative_gap(
                float(squared_metrics["euclidean_max"]),
                float(euclidean_metrics["euclidean_max"]),
            ),
            "B_vs_A_squared_total_regret": relative_gap(
                float(euclidean_metrics["squared_total"]),
                float(squared_metrics["squared_total"]),
            ),
        }
        rows.append(row)
        write_metric_contract_progress(progress_path, started=started, row=row, total_samples=sample_count)

    summary = paper_metric_contract_summary(config, rows)
    result = {
        "status": "completed",
        "artifact_type": "paper_hungarian_metric_contract",
        "paper_id": "2604.08669",
        "config": json_ready(config),
        "paper_fig3_reference": {
            "hungarian_average_distance": float(config["paper_hungarian_average_distance"]),
            "hungarian_max_distance": float(config["paper_hungarian_max_distance"]),
            "gnn_average_distance": float(config["paper_gnn_average_distance"]),
            "gnn_max_distance": float(config["paper_gnn_max_distance"]),
            "paper_sample_count": int(config["paper_sample_count"]),
        },
        "metric_contract": {
            "primary_metrics": ["euclidean_average_distance", "euclidean_max_distance"],
            "baseline_source": "selected_hungarian_cost_from_fig3_calibration",
            "average_distance_ratio_lte": float(config["metric_contract_average_ratio_lte"]),
            "max_distance_ratio_lte": float(config["metric_contract_max_ratio_lte"]),
            "training_label_cost_candidates": ["squared_distance", "euclidean_distance"],
        },
        "summary": summary,
        "decision": paper_metric_contract_decision(config, summary),
        "samples": rows,
        "artifacts": {"progress_path": str(progress_path)},
    }
    (output_dir / "paper_hungarian_metric_contract.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_single_sample_overfit_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    training = run_model_training_reproduction(
        output_dir=output_dir,
        train_samples=1,
        eval_samples=int(config["eval_samples"]),
        initial_side=int(config["initial_side"]),
        target_side=int(config["target_side"]),
        k_neighbors=int(config["k_neighbors"]),
        epochs=int(config["epochs"]),
        hidden_dim=int(config["hidden_dim"]),
        message_passes=int(config["message_passes"]),
        model_arch=str(config["model_arch"]),
        score_head=str(config["score_head"]),
        seed=int(config["seed"]),
        device=str(config["device"]),
        learning_rate=float(config["learning_rate"]),
        loading_probability=float(config["loading_probability"]),
        target="paper_scale_single_sample_overfit_probe",
        graph_backend=str(config["graph_backend"]),
        stream_samples=False,
        checkpoint_every_updates=int(config["checkpoint_every_updates"]),
        max_updates=int(config["max_updates"]),
        history_stride=int(config["history_stride"]),
        progress_every_updates=int(config["progress_every_updates"]),
        batch_size=int(config["batch_size"]),
        dataset_manifest_path=Path(manifest["manifest_path"]),
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
        margin=float(config["margin"]),
        temperature=float(config["temperature"]),
        hard_negative_k=int(config["hard_negative_k"]),
        sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        max_grad_norm=config.get("max_grad_norm"),
        resume_checkpoint_path=Path(config["resume_checkpoint_path"]) if config.get("resume_checkpoint_path") else None,
        resume_optimizer_state=bool(config.get("resume_optimizer_state", True)),
    )
    sample = next(iter_dataset_manifest_samples(Path(manifest["manifest_path"])))
    model = load_edge_scoring_model(Path(training["artifacts"]["checkpoint_path"]), device=str(config["device"]))  # type: ignore[index]
    scores = predict_edge_scores(model, sample)
    diagnostics = diagnose_assignment_sample(sample, scores)
    train_diagnostics = {
        "average_distance_gap": diagnostics["assignment"]["average_distance_gap"],  # type: ignore[index]
        "max_distance_gap": diagnostics["assignment"]["max_distance_gap"],  # type: ignore[index]
        "rank1_rate": diagnostics["source_rank"]["rank1_rate"],  # type: ignore[index]
        "mean_positive_rank": diagnostics["source_rank"]["mean_positive_rank"],  # type: ignore[index]
        "mean_positive_margin": diagnostics["source_rank"]["mean_positive_margin"],  # type: ignore[index]
        "score_distribution": diagnostics["score_distribution"],
    }
    decision = single_sample_decision(config=config, training=training, train_diagnostics=train_diagnostics)
    result = {
        "status": "completed",
        "artifact_type": "single_sample_overfit_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest["manifest_path"]),
        "training": training["training"],
        "train_diagnostics": train_diagnostics,
        "decision": decision,
        "artifacts": {
            "metrics_path": str(output_dir / "metrics.json"),
            "checkpoint_path": training["artifacts"]["checkpoint_path"],  # type: ignore[index]
        },
    }
    (output_dir / "single_sample_overfit_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_gradient_flow_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    sample_paths = dataset_sample_paths(manifest_path)
    if not sample_paths:
        raise ValueError("gradient flow probe requires at least one manifest sample")
    sample_path = sample_paths[0]
    sample_sha_before = sha256_file(sample_path)
    sample = load_graph_sample_npz(sample_path)
    sample_sha_after_load = sha256_file(sample_path)

    torch_device = resolve_torch_device(str(config["device"]))
    torch.manual_seed(int(config["seed"]))
    model = EdgeScoringGNN(
        node_dim=4,
        edge_dim=6,
        hidden_dim=int(config["hidden_dim"]),
        message_passes=int(config["message_passes"]),
        model_arch=str(config["model_arch"]),
        score_head=str(config["score_head"]),
    )
    model.to(torch_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    max_updates = int(config["max_updates"])
    probe_updates = sanitize_probe_updates(config.get("gradient_probe_updates"), max_updates=max_updates)
    progress_path = output_dir / "gradient_flow_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    snapshots: list[dict[str, object]] = []
    loss_records: list[dict[str, float | int]] = []
    started = time.monotonic()
    write_gradient_progress(progress_path, started=started, event="started", update=0, target_updates=max_updates)
    initial_snapshot = gradient_flow_snapshot(
        model=model,
        sample=sample,
        optimizer=optimizer,
        device=torch_device,
        update=0,
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
        margin=float(config["margin"]),
        temperature=float(config["temperature"]),
        hard_negative_k=int(config["hard_negative_k"]),
        sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        max_grad_norm=config.get("max_grad_norm"),
        apply_step=False,
    )
    snapshots.append(initial_snapshot)
    write_gradient_progress(
        progress_path,
        started=started,
        event="snapshot",
        update=0,
        target_updates=max_updates,
        loss=float(initial_snapshot["loss"]),
        extra={"snapshot_index": 0},
    )

    for update in range(1, max_updates + 1):
        should_record = update in probe_updates
        if should_record:
            snapshot = gradient_flow_snapshot(
                model=model,
                sample=sample,
                optimizer=optimizer,
                device=torch_device,
                update=update,
                loss_mode=str(config["loss_mode"]),
                source_ce_weight=float(config["source_ce_weight"]),
                margin=float(config["margin"]),
                temperature=float(config["temperature"]),
                hard_negative_k=int(config["hard_negative_k"]),
                sinkhorn_iterations=int(config["sinkhorn_iterations"]),
                max_grad_norm=config.get("max_grad_norm"),
                apply_step=True,
            )
            snapshots.append(snapshot)
            loss_records.append({"update": update, "loss": float(snapshot["loss"])})
            write_gradient_progress(
                progress_path,
                started=started,
                event="snapshot",
                update=update,
                target_updates=max_updates,
                loss=float(snapshot["loss"]),
                extra={"snapshot_index": len(snapshots) - 1},
            )
        else:
            loss_value = train_gradient_probe_step(
                model=model,
                sample=sample,
                optimizer=optimizer,
                device=torch_device,
                loss_mode=str(config["loss_mode"]),
                source_ce_weight=float(config["source_ce_weight"]),
                margin=float(config["margin"]),
                temperature=float(config["temperature"]),
                hard_negative_k=int(config["hard_negative_k"]),
                sinkhorn_iterations=int(config["sinkhorn_iterations"]),
                max_grad_norm=config.get("max_grad_norm"),
            )
            loss_records.append({"update": update, "loss": loss_value})
            progress_every = int(config.get("progress_every_updates", 0))
            if progress_every > 0 and (update % progress_every == 0 or update == max_updates):
                write_gradient_progress(
                    progress_path,
                    started=started,
                    event="update",
                    update=update,
                    target_updates=max_updates,
                    loss=loss_value,
                )

    sample_sha_after_training = sha256_file(sample_path)
    scores = predict_edge_scores(model, sample)
    diagnostics = diagnose_assignment_sample(sample, scores)
    decision = gradient_flow_decision(config=config, snapshots=snapshots)
    result = {
        "status": "completed",
        "artifact_type": "gradient_flow_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "sample_path": str(sample_path),
        "sample_stability": {
            "sample_sha256_before": sample_sha_before,
            "sample_sha256_after_load": sample_sha_after_load,
            "sample_sha256_after_training": sample_sha_after_training,
            "sample_hash_stable": sample_sha_before == sample_sha_after_load == sample_sha_after_training,
        },
        "training": {
            "updates": max_updates,
            "learning_rate": float(config["learning_rate"]),
            "hidden_dim": int(config["hidden_dim"]),
            "message_passes": int(config["message_passes"]),
            "loss_mode": str(config["loss_mode"]),
            "source_ce_weight": float(config["source_ce_weight"]),
            "runtime_seconds": time.monotonic() - started,
            "loss_initial": snapshots[0]["loss"],
            "loss_final": loss_records[-1]["loss"] if loss_records else snapshots[0]["loss"],
            "recorded_losses": len(loss_records),
        },
        "snapshots": snapshots,
        "train_diagnostics": {
            "assignment": diagnostics["assignment"],
            "source_rank": diagnostics["source_rank"],
            "score_distribution": diagnostics["score_distribution"],
        },
        "decision": decision,
        "artifacts": {"progress_path": str(progress_path)},
    }
    (output_dir / "gradient_flow_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_score_alignment_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    sample = next(iter_dataset_manifest_samples(manifest_path))

    torch_device = resolve_torch_device(str(config["device"]))
    torch.manual_seed(int(config["seed"]))
    model = EdgeScoringGNN(
        node_dim=4,
        edge_dim=6,
        hidden_dim=int(config["hidden_dim"]),
        message_passes=int(config["message_passes"]),
        model_arch=str(config["model_arch"]),
        score_head=str(config["score_head"]),
    )
    model.to(torch_device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    progress_path = output_dir / "score_alignment_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    started = time.monotonic()
    max_updates = int(config["max_updates"])

    initial_snapshot = gradient_flow_snapshot(
        model=model,
        sample=sample,
        optimizer=optimizer,
        device=torch_device,
        update=0,
        loss_mode=str(config["loss_mode"]),
        source_ce_weight=float(config["source_ce_weight"]),
        margin=float(config["margin"]),
        temperature=float(config["temperature"]),
        hard_negative_k=int(config["hard_negative_k"]),
        sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        max_grad_norm=config.get("max_grad_norm"),
        apply_step=False,
    )
    loss_initial = float(initial_snapshot["loss"])
    loss_final = loss_initial
    write_gradient_progress(progress_path, started=started, event="started", update=0, target_updates=max_updates)

    for update in range(1, max_updates + 1):
        loss_final = train_gradient_probe_step(
            model=model,
            sample=sample,
            optimizer=optimizer,
            device=torch_device,
            loss_mode=str(config["loss_mode"]),
            source_ce_weight=float(config["source_ce_weight"]),
            margin=float(config["margin"]),
            temperature=float(config["temperature"]),
            hard_negative_k=int(config["hard_negative_k"]),
            sinkhorn_iterations=int(config["sinkhorn_iterations"]),
            max_grad_norm=config.get("max_grad_norm"),
        )
        progress_every = int(config.get("progress_every_updates", 0))
        if progress_every > 0 and (update % progress_every == 0 or update == max_updates):
            write_gradient_progress(
                progress_path,
                started=started,
                event="update",
                update=update,
                target_updates=max_updates,
                loss=loss_final,
            )

    logits = predict_edge_logits(model, sample)
    methods = [str(item) for item in config.get("score_alignment_methods", ["sigmoid", "logits"])]
    decoders = [str(item) for item in config.get("score_alignment_decoders", ["score_hungarian"])]
    score_views: list[dict[str, object]] = []
    partial_path = output_dir / "score_alignment_partial.json"
    for method in methods:
        write_gradient_progress(
            progress_path,
            started=started,
            event="score_view_started",
            update=max_updates,
            target_updates=max_updates,
            loss=loss_final,
            extra={"method": method, "decoders": decoders},
        )
        view = score_alignment_view(sample=sample, logits=logits, method=method, decoders=decoders)
        score_views.append(view)
        partial_path.write_text(
            json.dumps(
                {
                    "status": "partial",
                    "artifact_type": "score_alignment_probe",
                    "completed_methods": [item["method"] for item in score_views],
                    "score_views": score_views,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        write_gradient_progress(
            progress_path,
            started=started,
            event="score_view_completed",
            update=max_updates,
            target_updates=max_updates,
            loss=loss_final,
            extra={"method": method, "decoders": decoders},
        )
    decision = score_alignment_decision(config=config, score_views=score_views)
    result = {
        "status": "completed",
        "artifact_type": "score_alignment_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "training": {
            "updates": max_updates,
            "learning_rate": float(config["learning_rate"]),
            "loss_initial": loss_initial,
            "loss_final": loss_final,
            "loss_mode": str(config["loss_mode"]),
            "source_ce_weight": float(config["source_ce_weight"]),
            "runtime_seconds": time.monotonic() - started,
        },
        "score_views": score_views,
        "decision": decision,
        "artifacts": {"progress_path": str(progress_path)},
    }
    (output_dir / "score_alignment_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_score_interpolation_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    sample = next(iter_dataset_manifest_samples(manifest_path))

    torch_device = resolve_torch_device(str(config["device"]))
    checkpoint_path = config.get("resume_checkpoint_path")
    if checkpoint_path is not None:
        model = load_edge_scoring_model(Path(checkpoint_path), device=str(config["device"]))
        model_source = {"type": "checkpoint", "path": str(checkpoint_path)}
    else:
        torch.manual_seed(int(config["seed"]))
        model = EdgeScoringGNN(
            node_dim=4,
            edge_dim=6,
            hidden_dim=int(config["hidden_dim"]),
            message_passes=int(config["message_passes"]),
            model_arch=str(config["model_arch"]),
            score_head=str(config["score_head"]),
        )
        model.to(torch_device)
        model.eval()
        model_source = {"type": "initialized", "seed": int(config["seed"])}

    method = str(config.get("score_interpolation_method", "sigmoid"))
    decoders = [str(item) for item in config.get("score_alignment_decoders", ["score_hungarian", "modified_auction"])]
    alphas = sorted({float(item) for item in config.get("score_interpolation_alphas", [0.0, 0.25, 0.5, 0.75, 1.0])})
    if not alphas:
        raise ValueError("score_interpolation requires at least one alpha")

    model_logits = predict_edge_logits(model, sample)
    oracle_logits = oracle_edge_logits(sample, margin=float(config["oracle_margin"])).detach().cpu().numpy()
    model_scores = transform_atom_target_scores(sample, np.asarray(model_logits, dtype=np.float64), method=method)
    oracle_scores = transform_atom_target_scores(sample, np.asarray(oracle_logits, dtype=np.float64), method=method)

    score_views: list[dict[str, object]] = []
    for alpha in alphas:
        blended_scores = ((1.0 - alpha) * model_scores) + (alpha * oracle_scores)
        score_views.append(
            score_interpolation_view(sample=sample, scores=blended_scores, alpha=alpha, decoders=decoders)
        )

    decision = score_interpolation_decision(config=config, score_views=score_views, decoders=decoders)
    result = {
        "status": "completed",
        "artifact_type": "score_interpolation_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "model_source": model_source,
        "method": method,
        "decoders": decoders,
        "score_views": score_views,
        "decision": decision,
    }
    (output_dir / "score_interpolation_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def run_loss_target_probe(config: dict[str, Any]) -> dict[str, object]:
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = ensure_single_sample_manifest(config)
    manifest_path = Path(manifest["manifest_path"])
    gate_sample = next(iter_dataset_manifest_samples(manifest_path))
    loss_modes, skipped_objectives = scalable_loss_target_modes(
        [str(item) for item in config.get("loss_target_modes", ["source_ce"])],
        target_count=int(gate_sample.target_count),
        assignment_margin_max_targets=int(config.get("assignment_margin_max_targets", 256)),
    )
    progress_path = output_dir / "loss_target_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    started = time.monotonic()

    objective_results: list[dict[str, object]] = []
    for loss_mode in loss_modes:
        write_gradient_progress(
            progress_path,
            started=started,
            event="started_objective",
            update=0,
            target_updates=int(config["max_updates"]),
            extra={"loss_mode": loss_mode},
        )
        objective_dir = output_dir / f"objective_{loss_mode}"
        training = run_model_training_reproduction(
            output_dir=objective_dir,
            train_samples=1,
            eval_samples=int(config["eval_samples"]),
            initial_side=int(config["initial_side"]),
            target_side=int(config["target_side"]),
            k_neighbors=int(config["k_neighbors"]),
            epochs=int(config["epochs"]),
            hidden_dim=int(config["hidden_dim"]),
            message_passes=int(config["message_passes"]),
            model_arch=str(config["model_arch"]),
            score_head=str(config["score_head"]),
            seed=int(config["seed"]),
            device=str(config["device"]),
            learning_rate=float(config["learning_rate"]),
            loading_probability=float(config["loading_probability"]),
            target=f"paper_scale_loss_target_probe_{loss_mode}",
            graph_backend=str(config["graph_backend"]),
            stream_samples=False,
            checkpoint_every_updates=int(config["checkpoint_every_updates"]),
            max_updates=int(config["max_updates"]),
            history_stride=int(config["history_stride"]),
            progress_every_updates=int(config["progress_every_updates"]),
            batch_size=int(config["batch_size"]),
            dataset_manifest_path=manifest_path,
            loss_mode=loss_mode,
            source_ce_weight=float(config["source_ce_weight"]),
            margin=float(config["margin"]),
            temperature=float(config["temperature"]),
            hard_negative_k=int(config["hard_negative_k"]),
            sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        )
        sample = next(iter_dataset_manifest_samples(manifest_path))
        model = load_edge_scoring_model(Path(training["artifacts"]["checkpoint_path"]), device=str(config["device"]))  # type: ignore[index]
        logits = predict_edge_logits(model, sample)
        score_views = loss_target_score_views(
            sample=sample,
            logits=logits,
            decision_method=str(config.get("loss_target_score_method", "logits")),
        )
        train_diagnostics = score_views[str(config.get("loss_target_score_method", "logits"))]
        objective_decision = loss_target_objective_decision(config=config, train_diagnostics=train_diagnostics)
        result = {
            "loss_mode": loss_mode,
            "training": training["training"],
            "train_diagnostics_method": str(config.get("loss_target_score_method", "logits")),
            "train_diagnostics": train_diagnostics,
            "score_views": score_views,
            "decision": objective_decision,
            "artifacts": {
                "metrics_path": str(objective_dir / "metrics.json"),
                "checkpoint_path": training["artifacts"]["checkpoint_path"],  # type: ignore[index]
            },
        }
        objective_results.append(result)
        write_gradient_progress(
            progress_path,
            started=started,
            event="completed_objective",
            update=int(config["max_updates"]),
            target_updates=int(config["max_updates"]),
            loss=float(training["training"]["loss_final"]),  # type: ignore[index]
            extra={
                "loss_mode": loss_mode,
                "rank1_rate": train_diagnostics["rank1_rate"],
                "mean_positive_rank": train_diagnostics["mean_positive_rank"],
                "average_distance_gap": train_diagnostics["average_distance_gap"],
            },
        )

    decision = loss_target_probe_decision(config=config, objective_results=objective_results)
    result = {
        "status": "completed",
        "artifact_type": "loss_target_probe",
        "paper_id": "2604.08669",
        "manifest_path": str(manifest_path),
        "objective_results": objective_results,
        "skipped_objectives": skipped_objectives,
        "decision": decision,
        "artifacts": {"progress_path": str(progress_path)},
    }
    (output_dir / "loss_target_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def loss_target_score_views(
    *,
    sample: Any,
    logits: Any,
    decision_method: str,
) -> dict[str, dict[str, object]]:
    methods = list(dict.fromkeys([decision_method, "sigmoid"]))
    views: dict[str, dict[str, object]] = {}
    for method in methods:
        scores = transform_atom_target_scores(sample, np.asarray(logits, dtype=np.float64), method=method)
        views[method] = flat_training_diagnostics(diagnose_assignment_sample(sample, scores))
    return views


def score_alignment_view(*, sample: Any, logits: Any, method: str, decoders: list[str]) -> dict[str, object]:
    scores = transform_atom_target_scores(sample, np.asarray(logits, dtype=np.float64), method=method)
    decoder_metrics: dict[str, object] = {}
    if "score_hungarian" in decoders:
        score_hungarian_assignment = decode_assignment_from_edge_scores(sample, scores)
        decoder_metrics["score_hungarian"] = assignment_metrics(sample, score_hungarian_assignment)
    if "modified_auction" in decoders:
        modified_auction_assignment = decode_assignment_with_modified_auction(sample, scores)
        decoder_metrics["modified_auction"] = assignment_metrics(sample, modified_auction_assignment)
    return {
        "method": method,
        "decoders": decoder_metrics,
        "source_rank": source_wise_positive_rank_diagnostics(sample, scores),
        "score_distribution": atom_target_score_distribution(sample, scores),
    }


def score_alignment_decision(*, config: dict[str, Any], score_views: list[dict[str, object]]) -> dict[str, object]:
    best_method = None
    best_gap = None
    for view in score_views:
        decoders = view["decoders"]  # type: ignore[index]
        metrics = decoders.get("score_hungarian") if isinstance(decoders, dict) else None
        if metrics is None and isinstance(decoders, dict) and decoders:
            metrics = next(iter(decoders.values()))
        if metrics is None:
            continue
        gap = float(metrics["average_distance_gap"])  # type: ignore[index]
        if best_gap is None or gap < best_gap:
            best_gap = gap
            best_method = str(view["method"])
    go_threshold = float(config.get("score_alignment_gap_go_lte", 1.5))
    no_go_threshold = float(config.get("score_alignment_gap_no_go_gte", 2.0))
    if best_gap is not None and best_gap < go_threshold:
        status = "score_alignment_go"
        recommendation = "redesign_loss_toward_assignment_compatible_scores"
    elif best_gap is not None and best_gap >= no_go_threshold:
        status = "score_alignment_no_go"
        recommendation = "inspect_index_alignment_and_conflict_cases_before_loss_redesign"
    else:
        status = "score_alignment_inconclusive"
        recommendation = "run_conflict_case_audit_before_training"
    return {
        "status": status,
        "recommendation": recommendation,
        "best_by_average_gap": {"method": best_method, "average_distance_gap": best_gap},
        "criteria": {
            "go_average_gap_lt": go_threshold,
            "no_go_average_gap_gte": no_go_threshold,
        },
    }


def score_interpolation_view(
    *,
    sample: Any,
    scores: Any,
    alpha: float,
    decoders: list[str],
) -> dict[str, object]:
    scores = np.asarray(scores, dtype=np.float64)
    decoder_metrics: dict[str, object] = {}
    if "score_hungarian" in decoders:
        score_hungarian_assignment = decode_assignment_from_edge_scores(sample, scores)
        decoder_metrics["score_hungarian"] = assignment_metrics(sample, score_hungarian_assignment)
    if "modified_auction" in decoders:
        modified_auction_assignment = decode_assignment_with_modified_auction(sample, scores)
        decoder_metrics["modified_auction"] = assignment_metrics(sample, modified_auction_assignment)
    return {
        "alpha": float(alpha),
        "decoders": decoder_metrics,
        "source_rank": source_wise_positive_rank_diagnostics(sample, scores),
        "score_distribution": atom_target_score_distribution(sample, scores),
    }


def score_interpolation_decision(
    *,
    config: dict[str, Any],
    score_views: list[dict[str, object]],
    decoders: list[str],
) -> dict[str, object]:
    if not score_views:
        return {
            "status": "score_interpolation_no_views",
            "recommendation": "check_score_interpolation_alphas",
            "primary_decoder": None,
        }
    primary_decoder = "score_hungarian" if "score_hungarian" in decoders else (decoders[0] if decoders else None)
    if primary_decoder is None:
        return {
            "status": "score_interpolation_no_decoder",
            "recommendation": "configure_at_least_one_decoder",
            "primary_decoder": None,
        }

    ordered = sorted(score_views, key=lambda item: float(item["alpha"]))
    gap_curve: list[dict[str, float]] = []
    for view in ordered:
        decoders_payload = view["decoders"]  # type: ignore[index]
        metrics = decoders_payload.get(primary_decoder) if isinstance(decoders_payload, dict) else None
        if metrics is None:
            continue
        gap_curve.append(
            {
                "alpha": float(view["alpha"]),
                "average_distance_gap": float(metrics["average_distance_gap"]),  # type: ignore[index]
                "max_distance_gap": float(metrics["max_distance_gap"]),  # type: ignore[index]
            }
        )
    if not gap_curve:
        return {
            "status": "score_interpolation_missing_decoder_metrics",
            "recommendation": "check_decoder_configuration",
            "primary_decoder": primary_decoder,
        }

    oracle_point = max(gap_curve, key=lambda item: item["alpha"])
    model_point = min(gap_curve, key=lambda item: item["alpha"])
    oracle_threshold = float(config.get("score_interpolation_oracle_gap_lte", 1e-6))
    oracle_gap = float(oracle_point["average_distance_gap"])
    oracle_ok = oracle_gap <= oracle_threshold
    nonincreasing = all(
        gap_curve[idx + 1]["average_distance_gap"] <= gap_curve[idx]["average_distance_gap"] + 1e-9
        for idx in range(len(gap_curve) - 1)
    )

    if not oracle_ok:
        status = "score_interpolation_pipeline_mismatch"
        recommendation = "debug_oracle_score_decoder_metric_path_before_training"
    elif oracle_gap <= float(model_point["average_distance_gap"]) + 1e-9:
        status = "score_interpolation_passed"
        recommendation = "decoder_responds_to_oracle_scores_continue_loss_metric_alignment"
    else:
        status = "score_interpolation_inconclusive"
        recommendation = "inspect_score_scaling_or_decoder_discontinuities"

    return {
        "status": status,
        "recommendation": recommendation,
        "primary_decoder": primary_decoder,
        "model_point": model_point,
        "oracle_point": oracle_point,
        "gap_curve": gap_curve,
        "monotonic_nonincreasing": bool(nonincreasing),
        "criteria": {"oracle_average_gap_lte": oracle_threshold},
    }


def ensure_single_sample_manifest(config: dict[str, Any]) -> dict[str, object]:
    return generate_ground_truth_dataset_shard(
        output_dir=Path(config["dataset_dir"]),
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


def oracle_edge_logits(sample: Any, *, margin: float) -> torch.Tensor:
    atom_to_target = sample.edge_types == EDGE_ATOM_TO_TARGET
    positive = atom_to_target & (sample.edge_labels > 0.5)
    negative = atom_to_target & (sample.edge_labels <= 0.5)
    logits = torch.zeros(int(sample.edge_index.shape[1]), dtype=torch.float32)
    logits[torch.as_tensor(positive)] = float(margin)
    logits[torch.as_tensor(negative)] = -float(margin)
    return logits


def with_oracle_edge_feature(sample: Any, *, feature_scale: float = 1.0) -> Any:
    edge_features = np.asarray(sample.edge_features, dtype=np.float32)
    edge_labels = np.asarray(sample.edge_labels, dtype=np.float32)
    if edge_features.shape[0] != edge_labels.shape[0]:
        raise ValueError("edge feature and label lengths must match")
    oracle_feature = (edge_labels * float(feature_scale)).reshape(-1, 1)
    return sample._replace(edge_features=np.concatenate([edge_features, oracle_feature], axis=1).astype(np.float32))


def sigmoid_numpy(logits: torch.Tensor) -> Any:
    return torch.sigmoid(logits).detach().cpu().numpy()


def loss_components(
    *,
    sample: Any,
    logits: torch.Tensor,
    device: str,
    source_ce_weight: float,
) -> dict[str, float]:
    torch_device = torch.device(device)
    logits = logits.to(torch_device)
    mask = torch.as_tensor(sample.edge_types == EDGE_ATOM_TO_TARGET, device=torch_device)
    labels = torch.as_tensor(sample.edge_labels, dtype=torch.float32, device=torch_device)
    bce_loss = binary_atom_target_cross_entropy(logits=logits, labels=labels, mask=mask, device=torch_device)
    source_loss = source_assignment_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=torch_device,
    )
    target_loss = target_assignment_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=torch_device,
    )
    return {
        "bce": float(bce_loss.detach().item()),
        "source_ce": float(source_loss.detach().item()),
        "target_ce": float(target_loss.detach().item()),
        "bce_source_ce": float((bce_loss + float(source_ce_weight) * source_loss).detach().item()),
    }


def write_gradient_progress(
    progress_path: Path,
    *,
    started: float,
    event: str,
    update: int,
    target_updates: int,
    loss: float | None = None,
    extra: dict[str, object] | None = None,
) -> None:
    elapsed = max(time.monotonic() - started, 1e-9)
    payload: dict[str, object] = {
        "event": event,
        "update": int(update),
        "target_updates": int(target_updates),
        "loss": loss,
        "elapsed_seconds": elapsed,
        "updates_per_second": float(update) / elapsed if update else None,
    }
    if extra:
        payload.update(extra)
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def train_gradient_probe_step(
    *,
    model: EdgeScoringGNN,
    sample: Any,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    loss_mode: str,
    source_ce_weight: float,
    margin: float,
    temperature: float,
    hard_negative_k: int,
    sinkhorn_iterations: int,
    max_grad_norm: float | None,
) -> float:
    optimizer.zero_grad(set_to_none=True)
    logits = model(sample)
    losses = loss_tensor_components(
        sample=sample,
        logits=logits,
        device=device,
        source_ce_weight=source_ce_weight,
        margin=margin,
        temperature=temperature,
        hard_negative_k=hard_negative_k,
        sinkhorn_iterations=sinkhorn_iterations,
    )
    loss = combined_loss_tensor(losses, loss_mode=loss_mode, source_ce_weight=source_ce_weight)
    if not bool(torch.isfinite(loss.detach()).item()):
        raise ValueError(f"{loss_mode} produced a non-finite loss")
    loss.backward()
    clip_gradients_if_requested(model=model, max_grad_norm=max_grad_norm, loss_mode=loss_mode)
    optimizer.step()
    return float(loss.detach().item())


def gradient_flow_snapshot(
    *,
    model: EdgeScoringGNN,
    sample: Any,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    update: int,
    loss_mode: str,
    source_ce_weight: float,
    margin: float,
    temperature: float,
    hard_negative_k: int,
    sinkhorn_iterations: int,
    max_grad_norm: float | None,
    apply_step: bool,
) -> dict[str, object]:
    optimizer.zero_grad(set_to_none=True)
    logits, activations = forward_with_activation_trace(model, sample)
    losses = loss_tensor_components(
        sample=sample,
        logits=logits,
        device=device,
        source_ce_weight=source_ce_weight,
        margin=margin,
        temperature=temperature,
        hard_negative_k=hard_negative_k,
        sinkhorn_iterations=sinkhorn_iterations,
    )
    loss = combined_loss_tensor(losses, loss_mode=loss_mode, source_ce_weight=source_ce_weight)
    named_parameters = list(model.named_parameters())
    component_grad_norms = loss_component_gradient_norms(losses, named_parameters)
    before_parameters = {
        name: parameter.detach().clone()
        for name, parameter in named_parameters
        if parameter.requires_grad
    }
    loss.backward()
    module_grad_norms = module_parameter_norms(named_parameters, use_grad=True)
    activation_gradient_norms = {
        name: tensor_norm(value.grad)
        for name, value in activations.items()
    }
    activation_norms = {
        name: tensor_norm(value.detach())
        for name, value in activations.items()
    }
    if apply_step:
        clip_gradients_if_requested(model=model, max_grad_norm=max_grad_norm, loss_mode=loss_mode)
        optimizer.step()
    parameter_update_norms = parameter_update_norms_by_module(model, before_parameters)
    with torch.no_grad():
        post_update_logits = model(sample)
        post_update_scores = torch.sigmoid(post_update_logits)
    return {
        "update": int(update),
        "loss": float(loss.detach().item()),
        "loss_components": {name: float(value.detach().item()) for name, value in losses.items()},
        "loss_component_gradient_norms": component_grad_norms,
        "module_grad_norms": module_grad_norms,
        "parameter_update_norms": parameter_update_norms,
        "activation_norms": activation_norms,
        "activation_gradient_norms": activation_gradient_norms,
        "activation_gradient_ratios": activation_gradient_ratios(activation_gradient_norms),
        "logit_distribution": edge_value_distribution(sample, post_update_logits.detach().cpu()),
        "score_distribution": edge_value_distribution(sample, post_update_scores.detach().cpu()),
    }


def clip_gradients_if_requested(
    *,
    model: EdgeScoringGNN,
    max_grad_norm: float | None,
    loss_mode: str,
) -> float | None:
    if max_grad_norm is None:
        return None
    grad_clip = float(max_grad_norm)
    if grad_clip <= 0.0:
        raise ValueError("max_grad_norm must be positive when provided")
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
    grad_norm_tensor = torch.as_tensor(grad_norm, device=next(model.parameters()).device)
    if not bool(torch.isfinite(grad_norm_tensor).item()):
        raise ValueError(f"{loss_mode} produced non-finite gradients")
    return float(grad_norm_tensor.detach().cpu().item())


def forward_with_activation_trace(model: EdgeScoringGNN, sample: Any) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    device = next(model.parameters()).device
    node_features = torch.as_tensor(sample.node_features, dtype=torch.float32, device=device)
    edge_features = torch.as_tensor(sample.edge_features, dtype=torch.float32, device=device)
    edge_index = torch.as_tensor(sample.edge_index, dtype=torch.long, device=device)
    src = edge_index[0]
    dst = edge_index[1]
    node_state = model.node_norm(model.node_encoder(node_features))
    node_state.retain_grad()
    activations = {"encoded": node_state}
    for pass_index in range(model.message_passes):
        messages = model.message(torch.cat([node_state[src], edge_features], dim=1))
        aggregate = torch.zeros_like(node_state)
        aggregate.index_add_(0, dst, messages)
        degree = torch.zeros((node_state.shape[0], 1), dtype=torch.float32, device=device)
        degree.index_add_(0, dst, torch.ones((len(dst), 1), dtype=torch.float32, device=device))
        aggregate = aggregate / degree.clamp_min(1.0)
        updated = model.update(torch.cat([node_state, aggregate], dim=1))
        if model.model_arch == "residual_layernorm":
            node_state = model.update_norm(node_state + updated)
        else:
            node_state = updated
        node_state.retain_grad()
        activations[f"pass_{pass_index + 1}"] = node_state
    logits = model.classifier(torch.cat([node_state[src], node_state[dst], edge_features], dim=1))
    return logits.squeeze(1), activations


def loss_tensor_components(
    *,
    sample: Any,
    logits: torch.Tensor,
    device: torch.device,
    source_ce_weight: float,
    margin: float,
    temperature: float,
    hard_negative_k: int,
    sinkhorn_iterations: int,
) -> dict[str, torch.Tensor]:
    mask = torch.as_tensor(sample.edge_types == EDGE_ATOM_TO_TARGET, device=device)
    labels = torch.as_tensor(sample.edge_labels, dtype=torch.float32, device=device)
    bce_loss = binary_atom_target_cross_entropy(logits=logits, labels=labels, mask=mask, device=device)
    source_loss = source_assignment_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
    )
    source_temperature_loss = source_temperature_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        temperature=float(temperature),
    )
    target_loss = target_assignment_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
    )
    target_temperature_loss = target_temperature_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        temperature=float(temperature),
    )
    source_topk_hard_negative_loss = source_topk_hard_negative_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        hard_negative_k=int(hard_negative_k),
        temperature=float(temperature),
    )
    target_topk_hard_negative_loss = target_topk_hard_negative_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        hard_negative_k=int(hard_negative_k),
        temperature=float(temperature),
    )
    assignment_sinkhorn_loss = assignment_sinkhorn_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        temperature=float(temperature),
        iterations=int(sinkhorn_iterations),
    )
    assignment_log_sinkhorn_loss = assignment_log_sinkhorn_cross_entropy(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        temperature=float(temperature),
        iterations=int(sinkhorn_iterations),
    )
    source_margin_loss = source_hard_negative_margin_loss(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        margin=float(margin),
    )
    target_margin_loss = target_hard_negative_margin_loss(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        margin=float(margin),
    )
    assignment_margin_loss = assignment_structured_margin_loss(
        logits=logits,
        labels=labels,
        sample=sample,
        mask=mask,
        device=device,
        margin=float(margin),
    )
    return {
        "bce": bce_loss,
        "source_ce": source_loss,
        "source_temperature_ce": source_temperature_loss,
        "target_ce": target_loss,
        "target_temperature_ce": target_temperature_loss,
        "source_topk_hard_negative_ce": source_topk_hard_negative_loss,
        "target_topk_hard_negative_ce": target_topk_hard_negative_loss,
        "source_target_topk_hard_negative_ce": source_topk_hard_negative_loss + target_topk_hard_negative_loss,
        "assignment_sinkhorn_ce": assignment_sinkhorn_loss,
        "assignment_log_sinkhorn_ce": assignment_log_sinkhorn_loss,
        "bce_source_ce": bce_loss + float(source_ce_weight) * source_loss,
        "source_target_ce": source_loss + target_loss,
        "source_target_temperature_ce": source_temperature_loss + target_temperature_loss,
        "source_margin": source_margin_loss,
        "source_ce_margin": source_loss + source_margin_loss,
        "target_margin": target_margin_loss,
        "source_target_margin": source_margin_loss + target_margin_loss,
        "assignment_margin": assignment_margin_loss,
    }


def combined_loss_tensor(
    losses: dict[str, torch.Tensor],
    *,
    loss_mode: str,
    source_ce_weight: float,
) -> torch.Tensor:
    if loss_mode == "bce":
        return losses["bce"]
    if loss_mode == "target_ce":
        return losses["target_ce"]
    if loss_mode == "target_temperature_ce":
        return losses["target_temperature_ce"]
    if loss_mode == "source_ce":
        return losses["source_ce"]
    if loss_mode == "source_temperature_ce":
        return losses["source_temperature_ce"]
    if loss_mode == "source_target_temperature_ce":
        return losses["source_target_temperature_ce"]
    if loss_mode == "source_topk_hard_negative_ce":
        return losses["source_topk_hard_negative_ce"]
    if loss_mode == "target_topk_hard_negative_ce":
        return losses["target_topk_hard_negative_ce"]
    if loss_mode == "source_target_topk_hard_negative_ce":
        return losses["source_target_topk_hard_negative_ce"]
    if loss_mode == "assignment_sinkhorn_ce":
        return losses["assignment_sinkhorn_ce"]
    if loss_mode == "assignment_log_sinkhorn_ce":
        return losses["assignment_log_sinkhorn_ce"]
    if loss_mode == "source_target_ce":
        return losses["source_target_ce"]
    if loss_mode == "bce_source_ce":
        return losses["bce"] + float(source_ce_weight) * losses["source_ce"]
    if loss_mode == "source_margin":
        return losses["source_margin"]
    if loss_mode == "source_ce_margin":
        return losses["source_ce_margin"]
    if loss_mode == "target_margin":
        return losses["target_margin"]
    if loss_mode == "source_target_margin":
        return losses["source_target_margin"]
    if loss_mode == "assignment_margin":
        return losses["assignment_margin"]
    raise ValueError(f"unsupported loss_mode: {loss_mode}")


def loss_component_gradient_norms(
    losses: dict[str, torch.Tensor],
    named_parameters: list[tuple[str, torch.nn.Parameter]],
) -> dict[str, float]:
    parameters = [parameter for _name, parameter in named_parameters if parameter.requires_grad]
    norms: dict[str, float] = {}
    for name, loss in losses.items():
        grads = torch.autograd.grad(loss, parameters, retain_graph=True, allow_unused=True)
        norms[name] = tensor_list_norm([grad for grad in grads if grad is not None])
    return norms


def module_parameter_norms(
    named_parameters: list[tuple[str, torch.nn.Parameter]],
    *,
    use_grad: bool,
) -> dict[str, float]:
    by_module: dict[str, list[torch.Tensor]] = {}
    for name, parameter in named_parameters:
        value = parameter.grad if use_grad else parameter
        if value is None:
            continue
        module = name.split(".", 1)[0]
        by_module.setdefault(module, []).append(value.detach())
    norms = {module: tensor_list_norm(values) for module, values in by_module.items()}
    norms["total"] = tensor_list_norm([value for values in by_module.values() for value in values])
    return norms


def parameter_update_norms_by_module(
    model: EdgeScoringGNN,
    before_parameters: dict[str, torch.Tensor],
) -> dict[str, float]:
    by_module: dict[str, list[torch.Tensor]] = {}
    for name, parameter in model.named_parameters():
        before = before_parameters.get(name)
        if before is None:
            continue
        module = name.split(".", 1)[0]
        by_module.setdefault(module, []).append((parameter.detach() - before).detach())
    norms = {module: tensor_list_norm(values) for module, values in by_module.items()}
    norms["total"] = tensor_list_norm([value for values in by_module.values() for value in values])
    return norms


def edge_value_distribution(sample: Any, values: torch.Tensor) -> dict[str, object]:
    array = values.detach().cpu().numpy()
    atom_target_mask = sample.edge_types == EDGE_ATOM_TO_TARGET
    positive_mask = atom_target_mask & (sample.edge_labels > 0.5)
    negative_mask = atom_target_mask & (sample.edge_labels <= 0.5)
    return {
        "positive": numeric_summary(array[positive_mask]),
        "negative": numeric_summary(array[negative_mask]),
        "positive_minus_negative_mean": mean_gap(array[positive_mask], array[negative_mask]),
    }


def numeric_summary(values: Any) -> dict[str, float | int | None]:
    array = torch.as_tensor(values, dtype=torch.float64).detach().cpu().numpy()
    if array.size == 0:
        return {"count": 0, "mean": None, "std": None, "min": None, "p50": None, "p90": None, "max": None}
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "std": float(array.std()),
        "min": float(array.min()),
        "p50": float(np.percentile(array, 50)),
        "p90": float(np.percentile(array, 90)),
        "max": float(array.max()),
    }


def mean_gap(positive_values: Any, negative_values: Any) -> float | None:
    positive = torch.as_tensor(positive_values, dtype=torch.float64).detach().cpu().numpy()
    negative = torch.as_tensor(negative_values, dtype=torch.float64).detach().cpu().numpy()
    if positive.size == 0 or negative.size == 0:
        return None
    return float(positive.mean() - negative.mean())


def tensor_norm(value: torch.Tensor | None) -> float:
    if value is None:
        return 0.0
    return float(torch.linalg.vector_norm(value.detach()).item())


def tensor_list_norm(values: list[torch.Tensor]) -> float:
    if not values:
        return 0.0
    squared = sum(float(torch.sum(value.detach() * value.detach()).item()) for value in values)
    return float(squared**0.5)


def activation_gradient_ratios(activation_gradient_norms: dict[str, float]) -> dict[str, float | None]:
    encoded = activation_gradient_norms.get("encoded", 0.0)
    pass_keys = sorted(
        [key for key in activation_gradient_norms if key.startswith("pass_")],
        key=lambda item: int(item.split("_", 1)[1]),
    )
    final = activation_gradient_norms[pass_keys[-1]] if pass_keys else 0.0
    return {
        "encoded_to_final": encoded / final if final > 0 else None,
        "encoded": encoded,
        "final": final,
    }


def sanitize_probe_updates(value: Any, *, max_updates: int) -> list[int]:
    if value is None:
        updates = {0, 1, max_updates}
    else:
        updates = {int(item) for item in value}
        updates.add(0)
        updates.add(max_updates)
    return sorted(item for item in updates if 0 <= item <= max_updates)


def gradient_flow_decision(
    *,
    config: dict[str, Any],
    snapshots: list[dict[str, object]],
) -> dict[str, object]:
    final = snapshots[-1] if snapshots else {}
    ratios = final.get("activation_gradient_ratios", {})
    ratio = ratios.get("encoded_to_final") if isinstance(ratios, dict) else None
    logit_distribution = final.get("logit_distribution", {})
    logit_gap = None
    if isinstance(logit_distribution, dict):
        logit_gap = logit_distribution.get("positive_minus_negative_mean")
    gradient_vanishing = bool(
        isinstance(ratio, (int, float))
        and ratio <= float(config.get("gradient_vanishing_ratio_lte", 1e-3))
    )
    weak_logit_separation = bool(
        not isinstance(logit_gap, (int, float))
        or logit_gap < float(config.get("logit_separation_gte", 0.1))
    )
    if gradient_vanishing:
        status = "gradient_vanishing_suspected"
        recommendation = "test residual_layernorm_before_lr_sweep"
    elif weak_logit_separation:
        status = "weak_logit_separation"
        recommendation = "inspect_loss_component_gradients_then_short_lr_sweep"
    else:
        status = "gradient_flow_not_obviously_blocked"
        recommendation = "run_short_lr_sweep"
    return {
        "status": status,
        "recommendation": recommendation,
        "encoded_to_final_gradient_ratio": ratio,
        "positive_minus_negative_logit_mean": logit_gap,
        "criteria": {
            "gradient_vanishing_ratio_lte": float(config.get("gradient_vanishing_ratio_lte", 1e-3)),
            "logit_separation_gte": float(config.get("logit_separation_gte", 0.1)),
        },
    }


def single_sample_decision(
    *,
    config: dict[str, Any],
    training: dict[str, object],
    train_diagnostics: dict[str, object],
) -> dict[str, object]:
    training_state = training["training"]  # type: ignore[index]
    loss_initial = training_state.get("loss_initial")  # type: ignore[union-attr]
    loss_final = training_state.get("loss_final")  # type: ignore[union-attr]
    loss_ratio = None
    if isinstance(loss_initial, (int, float)) and isinstance(loss_final, (int, float)) and loss_initial > 0:
        loss_ratio = float(loss_final) / float(loss_initial)
    rank1_rate = float(train_diagnostics["rank1_rate"])
    average_gap = float(train_diagnostics["average_distance_gap"])
    passed = bool(
        loss_ratio is not None
        and loss_ratio <= float(config["go_loss_ratio_lte"])
        and rank1_rate >= float(config["go_rank1_rate_gte"])
        and average_gap <= float(config["go_average_gap_lte"])
    )
    return {
        "status": "overfit_passed" if passed else "overfit_not_yet_passed",
        "loss_ratio": loss_ratio,
        "rank1_rate": rank1_rate,
        "average_distance_gap": average_gap,
        "go_criteria": {
            "loss_ratio_lte": float(config["go_loss_ratio_lte"]),
            "rank1_rate_gte": float(config["go_rank1_rate_gte"]),
            "average_gap_lte": float(config["go_average_gap_lte"]),
        },
    }


def oracle_feature_decision(
    *,
    config: dict[str, Any],
    training: dict[str, object],
    train_diagnostics: dict[str, object],
) -> dict[str, object]:
    loss_initial = training.get("loss_initial")
    loss_final = training.get("loss_final")
    loss_ratio = None
    if isinstance(loss_initial, (int, float)) and isinstance(loss_final, (int, float)) and loss_initial > 0:
        loss_ratio = float(loss_final) / float(loss_initial)
    rank1_rate = float(train_diagnostics["rank1_rate"])
    mean_positive_rank = float(train_diagnostics["mean_positive_rank"])
    average_gap = float(train_diagnostics["average_distance_gap"])
    passed = bool(
        loss_ratio is not None
        and loss_ratio <= float(config.get("oracle_feature_go_loss_ratio_lte", 0.2))
        and rank1_rate >= float(config.get("oracle_feature_go_rank1_rate_gte", 0.95))
        and average_gap <= float(config.get("oracle_feature_go_average_gap_lte", 0.01))
    )
    return {
        "status": "oracle_feature_passed" if passed else "oracle_feature_not_yet_passed",
        "recommendation": (
            "continue_to_warmup_mixed_negative_probe"
            if passed
            else "debug_oracle_feature_path_or_topk_objective_before_curriculum"
        ),
        "loss_ratio": loss_ratio,
        "rank1_rate": rank1_rate,
        "mean_positive_rank": mean_positive_rank,
        "average_distance_gap": average_gap,
        "go_criteria": {
            "loss_ratio_lte": float(config.get("oracle_feature_go_loss_ratio_lte", 0.2)),
            "rank1_rate_gte": float(config.get("oracle_feature_go_rank1_rate_gte", 0.95)),
            "average_gap_lte": float(config.get("oracle_feature_go_average_gap_lte", 0.01)),
        },
    }


def assignment_cost_gap_decision(
    *,
    config: dict[str, Any],
    decoders: dict[str, object],
    forced_top1: dict[str, object],
) -> dict[str, object]:
    primary_name = "score_hungarian" if "score_hungarian" in decoders else next(iter(decoders))
    primary = decoders[primary_name]
    relative_gap = float(primary["relative_total_distance_gap"])  # type: ignore[index]
    candidate_relative_gap = float(primary.get("relative_total_distance_gap_vs_candidate_optimum", relative_gap))  # type: ignore[union-attr]
    average_gap = float(primary["average_distance_gap"])  # type: ignore[index]
    relative_threshold = float(config.get("assignment_audit_relative_gap_lte", 0.005))
    average_threshold = float(config.get("assignment_audit_average_gap_lte", 0.05))
    cost_gap_passed = candidate_relative_gap <= relative_threshold
    near_rate = forced_top1.get("top1_near_optimal_rate")
    degeneracy_suspected = isinstance(near_rate, (int, float)) and float(near_rate) >= 0.8
    if cost_gap_passed:
        status = "assignment_cost_gap_passed"
        recommendation = "treat_rank1_as_secondary_and_continue_small_generalization_gate"
    elif degeneracy_suspected:
        status = "label_degeneracy_suspected"
        recommendation = "revise_metric_or_label_tie_policy_before_training_changes"
    else:
        status = "assignment_cost_gap_not_yet_passed"
        recommendation = "run_feature_sufficiency_probe_before_architecture_or_curriculum"
    return {
        "status": status,
        "recommendation": recommendation,
        "primary_decoder": primary_name,
        "relative_total_distance_gap": relative_gap,
        "relative_total_distance_gap_vs_candidate_optimum": candidate_relative_gap,
        "average_distance_gap": average_gap,
        "top1_near_optimal_rate": near_rate,
        "go_criteria": {
            "relative_total_distance_gap_lte": relative_threshold,
            "candidate_relative_total_distance_gap_lte": relative_threshold,
            "average_distance_gap_reference_only_lte": average_threshold,
            "top1_near_optimal_rate_for_degeneracy_gte": 0.8,
        },
    }


def regret_audit_decision(
    *,
    config: dict[str, Any],
    summary: dict[str, object],
    has_model: bool,
) -> dict[str, object]:
    label_regret = summary["label_relative_regret"]  # type: ignore[index]
    label_median = label_regret.get("p50") if isinstance(label_regret, dict) else None
    label_threshold = float(config.get("regret_audit_label_regret_median_no_go_gt", 0.005))
    model_threshold = float(config.get("regret_audit_model_regret_median_go_lte", 0.01))
    best_model = summary.get("best_model_decoder")
    model_median = None
    if isinstance(best_model, dict):
        model_median = best_model.get("p50_relative_regret")
    if isinstance(label_median, (int, float)) and float(label_median) > label_threshold:
        status = "label_regret_no_go"
        recommendation = "revise_label_or_cost_aware_metric_before_curriculum"
    elif has_model and isinstance(model_median, (int, float)) and float(model_median) <= model_threshold:
        status = "regret_audit_go"
        recommendation = "continue_small_generalization_gate_with_cost_aware_metric"
    else:
        status = "regret_audit_inconclusive"
        recommendation = "add_model_checkpoint_or_run_feature_sufficiency_probe_after_metric_fix"
    return {
        "status": status,
        "recommendation": recommendation,
        "label_regret_median": label_median,
        "best_model_relative_regret_median": model_median,
        "go_criteria": {
            "label_regret_median_no_go_gt": label_threshold,
            "model_regret_median_go_lte": model_threshold,
        },
    }


def solve_assignment_from_cost(cost: np.ndarray) -> np.ndarray:
    atom_indices, target_indices = linear_sum_assignment(np.asarray(cost, dtype=np.float64))
    order = np.argsort(target_indices)
    return np.column_stack([atom_indices[order], target_indices[order]]).astype(np.int64)


def metric_contract_target_positions(config: dict[str, Any]) -> np.ndarray:
    initial_side = int(config["initial_side"])
    target_side = int(config["target_side"])
    spacing = config.get("target_lattice_spacing")
    if spacing is None:
        return centered_square_lattice(initial_side, target_side)
    spacing_value = float(spacing)
    extent = (target_side - 1) * spacing_value
    offset = ((initial_side - 1) - extent) / 2.0
    coords = [
        (offset + row * spacing_value, offset + col * spacing_value)
        for row in range(target_side)
        for col in range(target_side)
    ]
    return np.asarray(coords, dtype=np.float32)


def assignment_distance_payload(
    atom_positions: np.ndarray,
    target_positions: np.ndarray,
    assignment: np.ndarray,
) -> dict[str, float]:
    distances = assignment_distances(atom_positions, target_positions, assignment)
    return {
        "euclidean_total": float(np.sum(distances)),
        "euclidean_average": float(np.mean(distances)),
        "euclidean_max": float(np.max(distances)) if distances.size else 0.0,
        "squared_total": float(np.sum(distances * distances)),
        "assignment_count": int(distances.size),
    }


def assignment_match_consistency(left: np.ndarray, right: np.ndarray) -> float:
    left_pairs = {(int(atom), int(target)) for atom, target in np.asarray(left, dtype=np.int64)}
    right_pairs = {(int(atom), int(target)) for atom, target in np.asarray(right, dtype=np.int64)}
    denominator = max(len(left_pairs), len(right_pairs), 1)
    return len(left_pairs & right_pairs) / denominator


def relative_gap(value: float, reference: float) -> float:
    return (float(value) - float(reference)) / max(abs(float(reference)), 1e-12)


def write_metric_contract_progress(
    progress_path: Path,
    *,
    started: float,
    row: dict[str, object],
    total_samples: int,
) -> None:
    elapsed = max(time.monotonic() - started, 1e-9)
    sample_index = int(row["sample_index"]) + 1
    payload = {
        "event": "sample",
        "sample_index": sample_index,
        "total_samples": int(total_samples),
        "seed": int(row["seed"]),
        "match_consistency": float(row["match_consistency"]),
        "A_vs_B_euclidean_average_regret": float(row["A_vs_B_euclidean_average_regret"]),
        "A_vs_B_euclidean_max_regret": float(row["A_vs_B_euclidean_max_regret"]),
        "B_vs_A_squared_total_regret": float(row["B_vs_A_squared_total_regret"]),
        "elapsed_seconds": elapsed,
        "samples_per_second": sample_index / elapsed,
    }
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def paper_metric_contract_summary(config: dict[str, Any], rows: list[dict[str, object]]) -> dict[str, object]:
    paper_average = float(config["paper_hungarian_average_distance"])
    paper_max = float(config["paper_hungarian_max_distance"])
    summary: dict[str, object] = {
        "sample_count": len(rows),
        "match_consistency": numeric_summary([float(row["match_consistency"]) for row in rows]),
        "A_vs_B_euclidean_average_regret": numeric_summary(
            [float(row["A_vs_B_euclidean_average_regret"]) for row in rows]
        ),
        "A_vs_B_euclidean_max_regret": numeric_summary([float(row["A_vs_B_euclidean_max_regret"]) for row in rows]),
        "B_vs_A_squared_total_regret": numeric_summary([float(row["B_vs_A_squared_total_regret"]) for row in rows]),
    }
    for label_key in ["squared_label", "euclidean_label"]:
        label_rows = [row[label_key] for row in rows]
        euclidean_average = [float(row["euclidean_average"]) for row in label_rows]  # type: ignore[index]
        euclidean_max = [float(row["euclidean_max"]) for row in label_rows]  # type: ignore[index]
        squared_total = [float(row["squared_total"]) for row in label_rows]  # type: ignore[index]
        mean_average = float(np.mean(euclidean_average)) if euclidean_average else 0.0
        mean_max = float(np.mean(euclidean_max)) if euclidean_max else 0.0
        average_relative_error = relative_gap(mean_average, paper_average) if paper_average > 0 else None
        max_relative_error = relative_gap(mean_max, paper_max) if paper_max > 0 else None
        if average_relative_error is not None and max_relative_error is not None:
            fig3_joint_error = abs(average_relative_error) + abs(max_relative_error)
        else:
            fig3_joint_error = None
        summary[label_key] = {
            "euclidean_average": numeric_summary(euclidean_average),
            "euclidean_max": numeric_summary(euclidean_max),
            "squared_total": numeric_summary(squared_total),
            "fig3_calibration": {
                "paper_average_distance": paper_average,
                "paper_max_distance": paper_max,
                "mean_average_distance": mean_average,
                "mean_max_distance": mean_max,
                "average_relative_error": average_relative_error,
                "max_relative_error": max_relative_error,
                "joint_abs_relative_error": fig3_joint_error,
            },
        }
    return summary


def paper_metric_contract_decision(config: dict[str, Any], summary: dict[str, object]) -> dict[str, object]:
    sample_count = int(summary["sample_count"])
    min_samples = int(config.get("metric_contract_min_decision_samples", 1))
    squared = summary["squared_label"]  # type: ignore[index]
    euclidean = summary["euclidean_label"]  # type: ignore[index]
    squared_error = squared["fig3_calibration"]["joint_abs_relative_error"]  # type: ignore[index]
    euclidean_error = euclidean["fig3_calibration"]["joint_abs_relative_error"]  # type: ignore[index]
    if not isinstance(squared_error, (int, float)) or not isinstance(euclidean_error, (int, float)):
        return {
            "status": "metric_contract_reference_missing",
            "recommendation": "set_paper_fig3_reference_before_freezing_label_cost",
            "selected_label_cost": None,
            "sample_count": sample_count,
            "min_decision_samples": min_samples,
        }
    if sample_count < min_samples:
        status = "metric_contract_needs_more_samples"
        selected = None
        recommendation = "increase_sample_count_before_freezing_label_cost"
    elif float(squared_error) < float(euclidean_error):
        status = "squared_distance_label_preferred"
        selected = "squared_distance"
        recommendation = "freeze_squared_distance_hungarian_labels_and_report_euclidean_avg_max"
    elif float(euclidean_error) < float(squared_error):
        status = "euclidean_distance_label_preferred"
        selected = "euclidean_distance"
        recommendation = "relabel_with_euclidean_hungarian_before_training"
    else:
        status = "metric_contract_tie"
        selected = None
        recommendation = "run_paired_ab_training_or_expand_oracle_sample_count"
    return {
        "status": status,
        "recommendation": recommendation,
        "selected_label_cost": selected,
        "squared_joint_abs_relative_error": float(squared_error),
        "euclidean_joint_abs_relative_error": float(euclidean_error),
        "sample_count": sample_count,
        "min_decision_samples": min_samples,
        "go_criteria": {
            "choose_label_with_lower_fig3_joint_abs_relative_error": True,
            "average_distance_ratio_lte_for_trained_model": float(config["metric_contract_average_ratio_lte"]),
            "max_distance_ratio_lte_for_trained_model": float(config["metric_contract_max_ratio_lte"]),
        },
    }


def regret_audit_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    summary: dict[str, object] = {
        "sample_count": len(rows),
        "label_relative_regret": numeric_summary([float(row["label_relative_regret"]) for row in rows]),
        "label_total_gap_vs_candidate": numeric_summary([float(row["label_total_gap_vs_candidate"]) for row in rows]),
    }
    decoder_names = sorted(
        {
            decoder_name
            for row in rows
            if isinstance(row.get("model"), dict)
            for decoder_name in row["model"].get("decoders", {})  # type: ignore[union-attr]
        }
    )
    decoder_summaries: dict[str, object] = {}
    for decoder_name in decoder_names:
        regrets = []
        label_regrets = []
        for row in rows:
            model = row.get("model")
            if not isinstance(model, dict):
                continue
            decoders = model.get("decoders", {})
            if not isinstance(decoders, dict) or decoder_name not in decoders:
                continue
            decoder = decoders[decoder_name]
            regrets.append(float(decoder["relative_total_distance_gap_vs_candidate_optimum"]))  # type: ignore[index]
            label_regrets.append(float(decoder["relative_total_distance_gap"]))  # type: ignore[index]
        decoder_summaries[decoder_name] = {
            "relative_regret_vs_candidate": numeric_summary(regrets),
            "relative_gap_vs_label": numeric_summary(label_regrets),
        }
    summary["model_decoders"] = decoder_summaries
    best_decoder = None
    for decoder_name, decoder_summary in decoder_summaries.items():
        regret_summary = decoder_summary["relative_regret_vs_candidate"]  # type: ignore[index]
        p50 = regret_summary.get("p50") if isinstance(regret_summary, dict) else None
        if not isinstance(p50, (int, float)):
            continue
        if best_decoder is None or float(p50) < float(best_decoder["p50_relative_regret"]):
            best_decoder = {"decoder": decoder_name, "p50_relative_regret": float(p50)}
    summary["best_model_decoder"] = best_decoder

    forced_rates = []
    rank1_rates = []
    for row in rows:
        model = row.get("model")
        if not isinstance(model, dict):
            continue
        forced = model.get("forced_top1_degeneracy")
        if isinstance(forced, dict) and isinstance(forced.get("top1_near_optimal_rate"), (int, float)):
            forced_rates.append(float(forced["top1_near_optimal_rate"]))
        source_rank = model.get("source_rank")
        if isinstance(source_rank, dict) and isinstance(source_rank.get("rank1_rate"), (int, float)):
            rank1_rates.append(float(source_rank["rank1_rate"]))
    if forced_rates:
        summary["forced_top1_near_optimal_rate"] = numeric_summary(forced_rates)
    if rank1_rates:
        summary["source_rank1_rate"] = numeric_summary(rank1_rates)
    return summary


def write_regret_progress(
    progress_path: Path,
    *,
    started: float,
    sample_index: int,
    total_samples: int,
    label_relative_regret: float,
) -> None:
    elapsed = max(time.monotonic() - started, 1e-9)
    payload = {
        "event": "sample",
        "sample_index": int(sample_index),
        "total_samples": int(total_samples),
        "label_relative_regret": float(label_relative_regret),
        "elapsed_seconds": elapsed,
        "samples_per_second": float(sample_index) / elapsed if sample_index else None,
    }
    with progress_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def assignment_cost_gap_summary(
    *,
    sample: Any,
    metrics: dict[str, float],
    baselines: dict[str, object],
) -> dict[str, float]:
    assignment_count = max(1, int(sample.optimal_assignment.shape[0]))
    predicted_total = float(metrics["predicted_average_distance"]) * assignment_count
    label_total = float(metrics["optimal_average_distance"]) * assignment_count
    total_gap = predicted_total - label_total
    relative_gap = total_gap / max(abs(label_total), 1e-12)
    candidate = baselines["candidate_optimum"]  # type: ignore[index]
    dense = baselines["dense_optimum"]  # type: ignore[index]
    candidate_total = float(candidate["total_distance"])  # type: ignore[index]
    dense_total = float(dense["total_distance"])  # type: ignore[index]
    candidate_gap = predicted_total - candidate_total
    dense_gap = predicted_total - dense_total
    return {
        **metrics,
        "predicted_total_distance": predicted_total,
        "optimal_total_distance": label_total,
        "total_distance_gap": total_gap,
        "relative_total_distance_gap": relative_gap,
        "candidate_optimal_total_distance": candidate_total,
        "candidate_optimal_average_distance": float(candidate["average_distance"]),  # type: ignore[index]
        "total_distance_gap_vs_candidate_optimum": candidate_gap,
        "relative_total_distance_gap_vs_candidate_optimum": candidate_gap / max(abs(candidate_total), 1e-12),
        "dense_optimal_total_distance": dense_total,
        "dense_optimal_average_distance": float(dense["average_distance"]),  # type: ignore[index]
        "total_distance_gap_vs_dense_optimum": dense_gap,
        "relative_total_distance_gap_vs_dense_optimum": dense_gap / max(abs(dense_total), 1e-12),
    }


def forced_top1_degeneracy_audit(
    *,
    sample: Any,
    edge_scores: np.ndarray,
    limit: int,
    relative_gap_lte: float,
    baselines: dict[str, object],
) -> dict[str, object]:
    if limit <= 0:
        return {"status": "skipped", "checked_sources": 0}
    top1_targets = top1_atom_target_candidates(sample, edge_scores)
    if not top1_targets:
        return {"status": "no_atom_target_candidates", "checked_sources": 0}

    distance_matrix = atom_target_candidate_distance_matrix(sample)
    optimal_assignment = sample.optimal_assignment.astype(np.int64)
    candidate = baselines["candidate_optimum"]  # type: ignore[index]
    optimal_total = float(candidate["total_distance"])  # type: ignore[index]
    assignment_count = max(1, int(optimal_assignment.shape[0]))

    rows: list[dict[str, object]] = []
    top1_equals_label = 0
    near_optimal = 0
    forced_gaps: list[float] = []
    forced_relative_gaps: list[float] = []
    for atom_idx, label_target_idx in optimal_assignment[: int(limit)]:
        atom_int = int(atom_idx)
        label_target_int = int(label_target_idx)
        top1 = top1_targets.get(atom_int)
        if top1 is None:
            continue
        top1_target_int = int(top1["target_idx"])
        if top1_target_int == label_target_int:
            top1_equals_label += 1
            forced = {
                "average_distance_gap": 0.0,
                "relative_total_distance_gap": 0.0,
                "total_distance_gap": 0.0,
            }
        else:
            forced = forced_assignment_cost_gap(
                distance_matrix=distance_matrix,
                atom_idx=atom_int,
                target_idx=top1_target_int,
                optimal_total=optimal_total,
                assignment_count=assignment_count,
            )
        forced_gap = float(forced["average_distance_gap"])
        forced_relative_gap = float(forced["relative_total_distance_gap"])
        is_near = forced_relative_gap <= float(relative_gap_lte)
        if is_near:
            near_optimal += 1
        forced_gaps.append(forced_gap)
        forced_relative_gaps.append(forced_relative_gap)
        if len(rows) < 10:
            rows.append(
                {
                    "atom_idx": atom_int,
                    "label_target_idx": label_target_int,
                    "top1_target_idx": top1_target_int,
                    "top1_score": float(top1["score"]),
                    "top1_equals_label": top1_target_int == label_target_int,
                    "top1_near_optimal": bool(is_near),
                    "forced_average_distance_gap": forced_gap,
                    "forced_relative_total_distance_gap": forced_relative_gap,
                }
            )

    checked = len(forced_gaps)
    return {
        "status": "completed",
        "checked_sources": checked,
        "top1_equals_label_count": int(top1_equals_label),
        "top1_equals_label_rate": top1_equals_label / checked if checked else 0.0,
        "top1_near_optimal_count": int(near_optimal),
        "top1_near_optimal_rate": near_optimal / checked if checked else 0.0,
        "mean_forced_average_distance_gap": float(np.mean(forced_gaps)) if forced_gaps else None,
        "mean_forced_relative_total_distance_gap": float(np.mean(forced_relative_gaps)) if forced_relative_gaps else None,
        "relative_gap_lte": float(relative_gap_lte),
        "examples": rows,
    }


def top1_atom_target_candidates(sample: Any, edge_scores: np.ndarray) -> dict[int, dict[str, float | int]]:
    n_atoms = int(len(sample.atom_positions))
    scores = np.asarray(edge_scores, dtype=np.float64)
    top1: dict[int, dict[str, float | int]] = {}
    for edge_pos, (src, dst) in enumerate(sample.edge_index.T):
        if int(sample.edge_types[edge_pos]) != EDGE_ATOM_TO_TARGET:
            continue
        atom_idx = int(src)
        target_idx = int(dst) - n_atoms
        if target_idx < 0 or target_idx >= len(sample.target_positions):
            continue
        score = float(scores[edge_pos])
        current = top1.get(atom_idx)
        if current is None or score > float(current["score"]):
            top1[atom_idx] = {"target_idx": target_idx, "score": score, "edge_pos": int(edge_pos)}
    return top1


def atom_target_distance_matrix(sample: Any) -> np.ndarray:
    atoms = np.asarray(sample.atom_positions, dtype=np.float64)
    targets = np.asarray(sample.target_positions, dtype=np.float64)
    deltas = atoms[:, None, :] - targets[None, :, :]
    return np.sqrt(np.sum(deltas * deltas, axis=2))


def atom_target_candidate_distance_matrix(sample: Any) -> np.ndarray:
    dense = atom_target_distance_matrix(sample)
    missing_penalty = float(np.max(dense) + 1_000_000.0)
    candidate = np.full_like(dense, missing_penalty)
    n_atoms = int(len(sample.atom_positions))
    for edge_pos, (src, dst) in enumerate(sample.edge_index.T):
        if int(sample.edge_types[edge_pos]) != EDGE_ATOM_TO_TARGET:
            continue
        atom_idx = int(src)
        target_idx = int(dst) - n_atoms
        if 0 <= atom_idx < candidate.shape[0] and 0 <= target_idx < candidate.shape[1]:
            candidate[atom_idx, target_idx] = min(candidate[atom_idx, target_idx], dense[atom_idx, target_idx])
    return candidate


def assignment_cost_baselines(sample: Any) -> dict[str, object]:
    assignment_count = max(1, int(sample.optimal_assignment.shape[0]))
    dense = atom_target_distance_matrix(sample)
    candidate = atom_target_candidate_distance_matrix(sample)
    label_assignment = sample.optimal_assignment.astype(np.int64)
    label_total = float(np.sum(dense[label_assignment[:, 0], label_assignment[:, 1]]))
    return {
        "label_assignment": {
            "total_distance": label_total,
            "average_distance": label_total / assignment_count,
        },
        "dense_optimum": solve_distance_baseline(dense, assignment_count=assignment_count),
        "candidate_optimum": solve_distance_baseline(candidate, assignment_count=assignment_count),
    }


def solve_distance_baseline(distance_matrix: np.ndarray, *, assignment_count: int) -> dict[str, float]:
    row_index, col_index = linear_sum_assignment(distance_matrix)
    selected = distance_matrix[row_index, col_index]
    total = float(np.sum(selected))
    return {
        "total_distance": total,
        "average_distance": total / max(1, int(assignment_count)),
        "max_distance": float(np.max(selected)) if selected.size else 0.0,
    }


def forced_assignment_cost_gap(
    *,
    distance_matrix: np.ndarray,
    atom_idx: int,
    target_idx: int,
    optimal_total: float,
    assignment_count: int,
) -> dict[str, float]:
    if atom_idx < 0 or atom_idx >= distance_matrix.shape[0]:
        raise ValueError("forced atom index out of range")
    if target_idx < 0 or target_idx >= distance_matrix.shape[1]:
        raise ValueError("forced target index out of range")
    atom_mask = np.ones(distance_matrix.shape[0], dtype=bool)
    target_mask = np.ones(distance_matrix.shape[1], dtype=bool)
    atom_mask[int(atom_idx)] = False
    target_mask[int(target_idx)] = False
    remaining = distance_matrix[atom_mask][:, target_mask]
    if remaining.size:
        row_index, col_index = linear_sum_assignment(remaining)
        remaining_total = float(np.sum(remaining[row_index, col_index]))
    else:
        remaining_total = 0.0
    predicted_total = float(distance_matrix[int(atom_idx), int(target_idx)]) + remaining_total
    total_gap = predicted_total - float(optimal_total)
    return {
        "predicted_total_distance": predicted_total,
        "optimal_total_distance": float(optimal_total),
        "total_distance_gap": total_gap,
        "average_distance_gap": total_gap / max(1, int(assignment_count)),
        "relative_total_distance_gap": total_gap / max(abs(float(optimal_total)), 1e-12),
    }


def flat_training_diagnostics(diagnostics: dict[str, object]) -> dict[str, object]:
    assignment = diagnostics["assignment"]  # type: ignore[index]
    source_rank = diagnostics["source_rank"]  # type: ignore[index]
    return {
        "average_distance_gap": assignment["average_distance_gap"],  # type: ignore[index]
        "max_distance_gap": assignment["max_distance_gap"],  # type: ignore[index]
        "rank1_rate": source_rank["rank1_rate"],  # type: ignore[index]
        "mean_positive_rank": source_rank["mean_positive_rank"],  # type: ignore[index]
        "mean_positive_margin": source_rank["mean_positive_margin"],  # type: ignore[index]
        "score_distribution": diagnostics["score_distribution"],
    }


def loss_target_objective_decision(
    *,
    config: dict[str, Any],
    train_diagnostics: dict[str, object],
) -> dict[str, object]:
    rank1_rate = float(train_diagnostics["rank1_rate"])
    mean_positive_rank = float(train_diagnostics["mean_positive_rank"])
    average_gap = float(train_diagnostics["average_distance_gap"])
    passed = bool(
        rank1_rate >= float(config["loss_target_go_rank1_rate_gte"])
        and mean_positive_rank <= float(config["loss_target_go_mean_positive_rank_lte"])
        and average_gap <= float(config["loss_target_go_average_gap_lte"])
    )
    return {
        "status": "loss_target_objective_passed" if passed else "loss_target_objective_not_yet_passed",
        "rank1_rate": rank1_rate,
        "mean_positive_rank": mean_positive_rank,
        "average_distance_gap": average_gap,
        "go_criteria": {
            "rank1_rate_gte": float(config["loss_target_go_rank1_rate_gte"]),
            "mean_positive_rank_lte": float(config["loss_target_go_mean_positive_rank_lte"]),
            "average_gap_lte": float(config["loss_target_go_average_gap_lte"]),
        },
    }


def loss_target_probe_decision(
    *,
    config: dict[str, Any],
    objective_results: list[dict[str, object]],
) -> dict[str, object]:
    if not objective_results:
        return {
            "status": "loss_target_not_yet_passed",
            "recommendation": "no_objective_results",
            "best_by_rank": None,
        }
    best = sorted(
        objective_results,
        key=lambda item: (
            -float(item["train_diagnostics"]["rank1_rate"]),  # type: ignore[index]
            float(item["train_diagnostics"]["mean_positive_rank"]),  # type: ignore[index]
            float(item["train_diagnostics"]["average_distance_gap"]),  # type: ignore[index]
        ),
    )[0]
    best_summary = {
        "loss_mode": best["loss_mode"],
        "rank1_rate": float(best["train_diagnostics"]["rank1_rate"]),  # type: ignore[index]
        "mean_positive_rank": float(best["train_diagnostics"]["mean_positive_rank"]),  # type: ignore[index]
        "average_distance_gap": float(best["train_diagnostics"]["average_distance_gap"]),  # type: ignore[index]
    }
    passed = any(
        item["decision"]["status"] == "loss_target_objective_passed"  # type: ignore[index]
        for item in objective_results
    )
    return {
        "status": "loss_target_go" if passed else "loss_target_not_yet_passed",
        "recommendation": "start_curriculum_from_passing_objective" if passed else "do_not_start_curriculum",
        "best_by_rank": best_summary,
        "criteria": {
            "rank1_rate_gte": float(config["loss_target_go_rank1_rate_gte"]),
            "mean_positive_rank_lte": float(config["loss_target_go_mean_positive_rank_lte"]),
            "average_gap_lte": float(config["loss_target_go_average_gap_lte"]),
        },
    }


def scalable_loss_target_modes(
    requested_modes: list[str],
    *,
    target_count: int,
    assignment_margin_max_targets: int,
) -> tuple[list[str], list[dict[str, str]]]:
    active: list[str] = []
    skipped: list[dict[str, str]] = []
    for mode in requested_modes:
        if mode == "assignment_margin" and int(target_count) > int(assignment_margin_max_targets):
            skipped.append(
                {
                    "loss_mode": mode,
                    "reason": "target_count_exceeds_assignment_margin_max_targets",
                }
            )
            continue
        active.append(mode)
    return active, skipped


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
