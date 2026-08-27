#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from atom_path_planner import (  # noqa: E402
    EDGE_ATOM_TO_TARGET,
    iter_dataset_manifest_samples,
    load_edge_scoring_model,
    predict_edge_logits,
)


def percentile(values: list[float] | list[int], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float64), q))


def summarize(values: list[float] | list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "p10": None, "p90": None, "max": None}
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "median": percentile(values, 50),
        "p10": percentile(values, 10),
        "p90": percentile(values, 90),
        "max": float(array.max()),
    }


def target_grid_offset(winner_target: int, positive_target: int, target_count: int) -> str:
    side = int(round(float(target_count) ** 0.5))
    if side * side != int(target_count):
        return "non_square_target_grid"
    winner_row, winner_col = divmod(int(winner_target), side)
    positive_row, positive_col = divmod(int(positive_target), side)
    return f"dr={winner_row - positive_row},dc={winner_col - positive_col}"


def candidate_distance_rank(candidates: list[dict[str, Any]], target_idx: int) -> int | None:
    ordered = sorted(candidates, key=lambda row: (float(row["distance"]), int(row["target"])))
    for rank, row in enumerate(ordered, start=1):
        if int(row["target"]) == int(target_idx):
            return rank
    return None


def primary_structure_label(row: dict[str, Any]) -> str:
    if bool(row.get("winner_closer_than_positive")):
        return "winner_geometrically_closer"
    if bool(row.get("winner_same_distance_shell")):
        return "winner_same_distance_shell"
    offset = str(row.get("target_grid_offset", "unknown"))
    if offset.startswith("dr="):
        parts = offset.replace("dr=", "").replace("dc=", "").split(",")
        try:
            l1 = abs(int(parts[0])) + abs(int(parts[1]))
            if l1 <= 2:
                return "local_target_offset_l1_le_2"
        except Exception:
            pass
    if int(row.get("rank", 0)) <= 4:
        return "rank2_to_4_no_simple_geometry"
    return "unclassified"


def classify_failure(
    row: dict[str, Any],
    *,
    near_miss_rank_lte: int,
    near_miss_score_gap_lte: float,
) -> tuple[str, str]:
    if bool(row.get("contract_anomaly")):
        return "contract_anomaly", str(row.get("contract_anomaly_reason", "unknown"))
    if int(row["rank"]) <= int(near_miss_rank_lte) and float(row["score_gap_to_winner"]) <= float(
        near_miss_score_gap_lte
    ):
        return "near_miss", "top_rank_small_score_gap"
    structure = primary_structure_label(row)
    if structure != "unclassified":
        return "structured_confusion", structure
    return "unclassified", "no_dominant_structure"


def mine_sample_failures(
    sample: Any,
    logits: np.ndarray,
    *,
    sample_index: int,
    tie_epsilon: float,
    near_miss_rank_lte: int,
    near_miss_score_gap_lte: float,
) -> dict[str, Any]:
    n_atoms = int(len(sample.atom_positions))
    n_targets = int(len(sample.target_positions))
    candidates_by_source: dict[int, list[dict[str, Any]]] = defaultdict(list)
    positive_label_count_by_source: Counter[int] = Counter()

    for edge_pos, edge_type in enumerate(sample.edge_types):
        if int(edge_type) != EDGE_ATOM_TO_TARGET:
            continue
        src = int(sample.edge_index[0, edge_pos])
        target = int(sample.edge_index[1, edge_pos]) - n_atoms
        if not (0 <= src < n_atoms and 0 <= target < n_targets):
            continue
        distance = float(np.linalg.norm(sample.atom_positions[src] - sample.target_positions[target]))
        label = float(sample.edge_labels[edge_pos])
        if label > 0.5:
            positive_label_count_by_source[src] += 1
        candidates_by_source[src].append(
            {
                "edge_pos": int(edge_pos),
                "source": src,
                "target": target,
                "logit": float(logits[edge_pos]),
                "label": label,
                "distance": distance,
            }
        )

    failures: list[dict[str, Any]] = []
    rank_hist = Counter()
    missing_optimal_edges = 0
    duplicate_positive_sources = 0
    success_count = 0
    positive_count = 0
    score_gaps: list[float] = []
    ranks: list[int] = []

    for atom_idx_raw, target_idx_raw in sample.optimal_assignment.astype(np.int64):
        atom_idx = int(atom_idx_raw)
        target_idx = int(target_idx_raw)
        candidates = candidates_by_source.get(atom_idx, [])
        positive_candidates = [row for row in candidates if int(row["target"]) == target_idx and float(row["label"]) > 0.5]
        source_positive_count = int(positive_label_count_by_source.get(atom_idx, 0))
        if source_positive_count > 1:
            duplicate_positive_sources += 1
        if not positive_candidates:
            missing_optimal_edges += 1
            positive_count += 1
            rank_hist["missing"] += 1
            failures.append(
                {
                    "sample_index": int(sample_index),
                    "source": atom_idx,
                    "positive_target": target_idx,
                    "bucket": "contract_anomaly",
                    "bucket_reason": "missing_positive_atom_to_target_edge",
                    "contract_anomaly": True,
                    "contract_anomaly_reason": "missing_positive_atom_to_target_edge",
                }
            )
            continue

        positive = max(positive_candidates, key=lambda row: float(row["logit"]))
        positive_logit = float(positive["logit"])
        ordered = sorted(candidates, key=lambda row: float(row["logit"]), reverse=True)
        rank = 1 + sum(1 for row in candidates if float(row["logit"]) > positive_logit + tie_epsilon)
        rank_hist[rank] += 1
        ranks.append(int(rank))
        positive_count += 1
        if rank == 1:
            success_count += 1
            continue

        winner = ordered[0]
        winner_logit = float(winner["logit"])
        score_gap = winner_logit - positive_logit
        positive_distance = float(positive["distance"])
        winner_distance = float(winner["distance"])
        positive_distance_rank = candidate_distance_rank(candidates, target_idx)
        winner_distance_rank = candidate_distance_rank(candidates, int(winner["target"]))
        row = {
            "sample_index": int(sample_index),
            "source": atom_idx,
            "positive_target": target_idx,
            "winner_target": int(winner["target"]),
            "rank": int(rank),
            "positive_logit": positive_logit,
            "winner_logit": winner_logit,
            "score_gap_to_winner": float(score_gap),
            "positive_distance": positive_distance,
            "winner_distance": winner_distance,
            "winner_distance_minus_positive": float(winner_distance - positive_distance),
            "positive_distance_rank_in_candidates": positive_distance_rank,
            "winner_distance_rank_in_candidates": winner_distance_rank,
            "winner_closer_than_positive": bool(winner_distance + 1e-9 < positive_distance),
            "winner_same_distance_shell": bool(abs(winner_distance - positive_distance) <= 1e-6),
            "target_grid_offset": target_grid_offset(int(winner["target"]), target_idx, n_targets),
            "source_positive_label_count": source_positive_count,
            "contract_anomaly": bool(source_positive_count != 1),
            "contract_anomaly_reason": "source_positive_label_count_not_one" if source_positive_count != 1 else None,
            "top3": [
                {
                    "target": int(top["target"]),
                    "logit": float(top["logit"]),
                    "distance": float(top["distance"]),
                    "is_positive": bool(float(top["label"]) > 0.5),
                }
                for top in ordered[:3]
            ],
        }
        bucket, reason = classify_failure(
            row,
            near_miss_rank_lte=near_miss_rank_lte,
            near_miss_score_gap_lte=near_miss_score_gap_lte,
        )
        row["bucket"] = bucket
        row["bucket_reason"] = reason
        failures.append(row)
        score_gaps.append(float(score_gap))

    return {
        "positive_count": int(positive_count),
        "success_count": int(success_count),
        "missing_optimal_edges": int(missing_optimal_edges),
        "duplicate_positive_sources": int(duplicate_positive_sources),
        "rank_hist": rank_hist,
        "ranks": ranks,
        "score_gaps": score_gaps,
        "failures": failures,
    }


def routing_decision(
    *,
    failure_count: int,
    bucket_counts: Counter[str],
    bucket_reason_counts: Counter[str],
    expected_rank1_status: str,
) -> dict[str, Any]:
    denominator = max(int(failure_count), 1)
    near_miss_fraction = float(bucket_counts.get("near_miss", 0) / denominator)
    structured_fraction = float(bucket_counts.get("structured_confusion", 0) / denominator)
    contract_fraction = float(bucket_counts.get("contract_anomaly", 0) / denominator)
    dominant_reason, dominant_reason_count = ("none", 0)
    if bucket_reason_counts:
        dominant_reason, dominant_reason_count = bucket_reason_counts.most_common(1)[0]
    dominant_reason_fraction = float(dominant_reason_count / denominator)

    if expected_rank1_status == "mismatch" or contract_fraction > 0.10:
        route = "stop_training_audit_eval_or_label_contract"
    elif structured_fraction >= 0.40 and dominant_reason_fraction >= 0.40:
        route = "data_side_hard_negative_mining"
    elif near_miss_fraction >= 0.60:
        route = "topk_scale_control_short_paired_probe"
    else:
        route = "inconclusive_report_before_training"

    return {
        "route": route,
        "thresholds": {
            "near_miss_fraction_gte_for_scale_control": 0.60,
            "structured_dominant_fraction_gte_for_data_mining": 0.40,
            "contract_anomaly_fraction_gt_for_contract_audit": 0.10,
        },
        "observed": {
            "near_miss_fraction": near_miss_fraction,
            "structured_confusion_fraction": structured_fraction,
            "contract_anomaly_fraction": contract_fraction,
            "dominant_bucket_reason": dominant_reason,
            "dominant_bucket_reason_fraction": dominant_reason_fraction,
        },
    }


def run_probe(
    *,
    checkpoint_path: Path,
    manifest_path: Path,
    output_dir: Path,
    device: str,
    max_samples: int | None,
    max_failures_dump: int,
    tie_epsilon: float,
    near_miss_rank_lte: int,
    near_miss_score_gap_lte: float,
    expected_rank1: float | None,
    rank1_tolerance: float,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "failure_mining_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    model = load_edge_scoring_model(checkpoint_path, device=device)
    started = time.monotonic()

    sample_count = 0
    positive_count = 0
    success_count = 0
    missing_optimal_edges = 0
    duplicate_positive_sources = 0
    rank_hist: Counter[Any] = Counter()
    bucket_counts: Counter[str] = Counter()
    bucket_reason_counts: Counter[str] = Counter()
    structure_counts: Counter[str] = Counter()
    target_offset_counts: Counter[str] = Counter()
    score_gaps: list[float] = []
    ranks: list[int] = []
    failures_dump: list[dict[str, Any]] = []

    for sample_index, sample in enumerate(iter_dataset_manifest_samples(manifest_path), start=1):
        if max_samples is not None and sample_index > max_samples:
            break
        raw_logits = predict_edge_logits(model, sample)
        logits = raw_logits.detach().cpu().numpy() if hasattr(raw_logits, "detach") else np.asarray(raw_logits)
        sample_result = mine_sample_failures(
            sample,
            logits,
            sample_index=sample_index,
            tie_epsilon=tie_epsilon,
            near_miss_rank_lte=near_miss_rank_lte,
            near_miss_score_gap_lte=near_miss_score_gap_lte,
        )
        sample_count += 1
        positive_count += int(sample_result["positive_count"])
        success_count += int(sample_result["success_count"])
        missing_optimal_edges += int(sample_result["missing_optimal_edges"])
        duplicate_positive_sources += int(sample_result["duplicate_positive_sources"])
        rank_hist.update(sample_result["rank_hist"])
        ranks.extend(sample_result["ranks"])
        score_gaps.extend(sample_result["score_gaps"])
        failures = list(sample_result["failures"])
        for row in failures:
            bucket = str(row.get("bucket", "unclassified"))
            reason = str(row.get("bucket_reason", "unknown"))
            bucket_counts[bucket] += 1
            bucket_reason_counts[reason] += 1
            if bucket == "structured_confusion":
                structure_counts[reason] += 1
                target_offset_counts[str(row.get("target_grid_offset", "unknown"))] += 1
        if len(failures_dump) < max_failures_dump:
            failures_dump.extend(failures[: max(0, max_failures_dump - len(failures_dump))])

        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "event": "sample",
                        "sample_index": sample_index,
                        "positive_count": int(sample_result["positive_count"]),
                        "failure_count": int(len(failures)),
                        "elapsed_seconds": time.monotonic() - started,
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    failure_count = int(sum(bucket_counts.values()))
    rank1_rate = float(success_count / positive_count) if positive_count else 0.0
    expected_rank1_status = "not_checked"
    expected_rank1_delta = None
    if expected_rank1 is not None:
        expected_rank1_delta = float(rank1_rate - float(expected_rank1))
        expected_rank1_status = "ok" if abs(expected_rank1_delta) <= float(rank1_tolerance) else "mismatch"
    decision = routing_decision(
        failure_count=failure_count,
        bucket_counts=bucket_counts,
        bucket_reason_counts=bucket_reason_counts,
        expected_rank1_status=expected_rank1_status,
    )

    summary = {
        "sample_count": int(sample_count),
        "positive_count": int(positive_count),
        "success_count": int(success_count),
        "failure_count": failure_count,
        "rank1_rate": rank1_rate,
        "mean_positive_rank": float(np.mean(np.asarray(ranks, dtype=np.float64))) if ranks else None,
        "rank_histogram": {str(key): int(value) for key, value in sorted(rank_hist.items(), key=lambda kv: str(kv[0]))},
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "bucket_fractions": {
            key: float(value / max(failure_count, 1)) for key, value in sorted(bucket_counts.items())
        },
        "bucket_reason_counts": dict(bucket_reason_counts.most_common()),
        "structured_reason_counts": dict(structure_counts.most_common()),
        "target_grid_offset_counts": dict(target_offset_counts.most_common(20)),
        "score_gap_to_winner": summarize(score_gaps),
        "missing_optimal_edges": int(missing_optimal_edges),
        "duplicate_positive_sources": int(duplicate_positive_sources),
        "expected_rank1_check": {
            "expected_rank1": expected_rank1,
            "observed_rank1": rank1_rate,
            "delta": expected_rank1_delta,
            "tolerance": float(rank1_tolerance),
            "status": expected_rank1_status,
        },
        "routing_decision": decision,
    }
    result = {
        "status": "completed",
        "checkpoint_path": str(checkpoint_path),
        "manifest_path": str(manifest_path),
        "device": device,
        "config": {
            "tie_epsilon": tie_epsilon,
            "near_miss_rank_lte": near_miss_rank_lte,
            "near_miss_score_gap_lte": near_miss_score_gap_lte,
            "max_failures_dump": max_failures_dump,
        },
        "summary": summary,
        "failures": failures_dump,
    }
    (output_dir / "failure_mining_probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bucket source-rank failures for a fixed checkpoint and dataset.")
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--max-failures-dump", type=int, default=200)
    parser.add_argument("--tie-epsilon", type=float, default=1e-6)
    parser.add_argument("--near-miss-rank-lte", type=int, default=3)
    parser.add_argument("--near-miss-score-gap-lte", type=float, default=0.0081)
    parser.add_argument("--expected-rank1", type=float)
    parser.add_argument("--rank1-tolerance", type=float, default=0.002)
    args = parser.parse_args()
    result = run_probe(
        checkpoint_path=args.checkpoint_path,
        manifest_path=args.manifest_path,
        output_dir=args.output_dir,
        device=args.device,
        max_samples=args.max_samples,
        max_failures_dump=args.max_failures_dump,
        tie_epsilon=args.tie_epsilon,
        near_miss_rank_lte=args.near_miss_rank_lte,
        near_miss_score_gap_lte=args.near_miss_score_gap_lte,
        expected_rank1=args.expected_rank1,
        rank1_tolerance=args.rank1_tolerance,
    )
    print(json.dumps({"status": result["status"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
