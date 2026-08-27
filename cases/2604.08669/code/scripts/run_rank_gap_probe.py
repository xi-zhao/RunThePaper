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


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float64), q))


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "p10": None,
            "p90": None,
            "p95": None,
            "max": None,
        }
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "median": percentile(values, 50),
        "p10": percentile(values, 10),
        "p90": percentile(values, 90),
        "p95": percentile(values, 95),
        "max": float(array.max()),
    }


def edge_kind(sample: Any, edge_pos: int, n_atoms: int) -> str:
    src = int(sample.edge_index[0, edge_pos])
    dst = int(sample.edge_index[1, edge_pos])
    if src < n_atoms and dst >= n_atoms:
        return "atom_to_target"
    if src < n_atoms and dst < n_atoms:
        return "atom_to_atom"
    if src >= n_atoms and dst < n_atoms:
        return "target_to_atom"
    return "target_to_target"


def probe_sample(sample: Any, logits: np.ndarray, *, tie_epsilon: float) -> dict[str, Any]:
    n_atoms = int(len(sample.atom_positions))
    rows: list[dict[str, Any]] = []
    by_source: dict[int, list[int]] = defaultdict(list)
    for edge_pos, edge_type in enumerate(sample.edge_types):
        if int(edge_type) != EDGE_ATOM_TO_TARGET:
            continue
        src = int(sample.edge_index[0, edge_pos])
        by_source[src].append(int(edge_pos))

    for source, edge_positions in by_source.items():
        positive_edges = [edge_pos for edge_pos in edge_positions if float(sample.edge_labels[edge_pos]) > 0.5]
        if not positive_edges:
            continue
        edge_positions_sorted = sorted(edge_positions, key=lambda edge_pos: float(logits[edge_pos]), reverse=True)
        for positive_edge in positive_edges:
            positive_logit = float(logits[positive_edge])
            rank = 1 + sum(1 for edge_pos in edge_positions if float(logits[edge_pos]) > positive_logit)
            winner = edge_positions_sorted[0]
            winner_logit = float(logits[winner])
            winner_is_positive = float(sample.edge_labels[winner]) > 0.5
            beating_negatives = [
                edge_pos
                for edge_pos in edge_positions
                if float(sample.edge_labels[edge_pos]) <= 0.5 and float(logits[edge_pos]) > positive_logit
            ]
            near_ties = [
                edge_pos
                for edge_pos in edge_positions
                if edge_pos != positive_edge and abs(float(logits[edge_pos]) - positive_logit) <= tie_epsilon
            ]
            if beating_negatives:
                closest_gap = min(float(logits[edge_pos]) - positive_logit for edge_pos in beating_negatives)
                winner_gap = winner_logit - positive_logit
                max_negative = max(beating_negatives, key=lambda edge_pos: float(logits[edge_pos]))
                negative_kind = edge_kind(sample, max_negative, n_atoms)
            else:
                closest_gap = 0.0
                winner_gap = 0.0 if winner_is_positive else winner_logit - positive_logit
                negative_kind = "none"
            rows.append(
                {
                    "source": int(source),
                    "positive_edge": int(positive_edge),
                    "positive_target": int(sample.edge_index[1, positive_edge]) - n_atoms,
                    "rank": int(rank),
                    "positive_logit": positive_logit,
                    "winner_logit": winner_logit,
                    "winner_is_positive": bool(winner_is_positive),
                    "winner_gap": float(winner_gap),
                    "closest_beating_negative_gap": float(closest_gap),
                    "beating_negative_count": int(len(beating_negatives)),
                    "near_tie_count": int(len(near_ties)),
                    "top_beating_negative_kind": negative_kind,
                }
            )
    return {"positive_rows": rows}


def run_probe(
    *,
    checkpoint_path: Path,
    manifest_path: Path,
    output_dir: Path,
    device: str,
    max_samples: int | None,
    tie_epsilon: float,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "rank_gap_probe_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")
    model = load_edge_scoring_model(checkpoint_path, device=device)
    started = time.monotonic()

    all_rows: list[dict[str, Any]] = []
    rank_hist = Counter()
    fail_kind_hist = Counter()
    fail_gaps: list[float] = []
    rank2_to_4_gaps: list[float] = []
    near_tie_failures = 0
    sample_count = 0
    for sample_index, sample in enumerate(iter_dataset_manifest_samples(manifest_path), start=1):
        if max_samples is not None and sample_index > max_samples:
            break
        raw_logits = predict_edge_logits(model, sample)
        if hasattr(raw_logits, "detach"):
            logits = raw_logits.detach().cpu().numpy()
        else:
            logits = np.asarray(raw_logits, dtype=np.float64)
        sample_result = probe_sample(sample, logits, tie_epsilon=tie_epsilon)
        rows = sample_result["positive_rows"]
        for row in rows:
            row["sample_index"] = sample_index
            rank_hist[int(row["rank"])] += 1
            if int(row["rank"]) > 1:
                fail_gaps.append(float(row["closest_beating_negative_gap"]))
                fail_kind_hist[str(row["top_beating_negative_kind"])] += 1
                near_tie_failures += int(row["near_tie_count"] > 0)
                if 2 <= int(row["rank"]) <= 4:
                    rank2_to_4_gaps.append(float(row["closest_beating_negative_gap"]))
        all_rows.extend(rows)
        sample_count += 1
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "event": "sample",
                        "sample_index": sample_index,
                        "positive_rows": len(rows),
                        "elapsed_seconds": time.monotonic() - started,
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    positive_count = len(all_rows)
    failure_count = sum(count for rank, count in rank_hist.items() if rank > 1)
    rank2_to_4_count = sum(count for rank, count in rank_hist.items() if 2 <= rank <= 4)
    rank1_count = rank_hist.get(1, 0)
    summary = {
        "sample_count": sample_count,
        "positive_count": positive_count,
        "rank1_count": int(rank1_count),
        "rank1_rate": float(rank1_count / positive_count) if positive_count else None,
        "failure_count": int(failure_count),
        "rank2_to_4_count": int(rank2_to_4_count),
        "rank_histogram": {str(rank): int(count) for rank, count in sorted(rank_hist.items())},
        "failure_gap_to_closest_winning_negative": summarize(fail_gaps),
        "rank2_to_4_gap_to_closest_winning_negative": summarize(rank2_to_4_gaps),
        "near_tie_failure_count": int(near_tie_failures),
        "near_tie_failure_fraction": float(near_tie_failures / failure_count) if failure_count else None,
        "top_beating_negative_kind_histogram": dict(sorted(fail_kind_hist.items())),
        "suggested_margin_from_rank2_to_4_median_gap_x2": (
            float(2.0 * np.median(np.asarray(rank2_to_4_gaps, dtype=np.float64))) if rank2_to_4_gaps else None
        ),
        "suggested_margin_from_rank2_to_4_p90_gap": percentile(rank2_to_4_gaps, 90),
        "interpretation": (
            "small_gap_near_miss"
            if rank2_to_4_gaps and float(np.percentile(np.asarray(rank2_to_4_gaps), 90)) < 2.0
            else "large_or_mixed_gap"
        ),
    }
    result = {
        "status": "completed",
        "checkpoint_path": str(checkpoint_path),
        "manifest_path": str(manifest_path),
        "device": device,
        "tie_epsilon": tie_epsilon,
        "summary": summary,
        "top_failures": sorted(
            [row for row in all_rows if int(row["rank"]) > 1],
            key=lambda row: (int(row["rank"]), float(row["closest_beating_negative_gap"])),
            reverse=True,
        )[:50],
    }
    (output_dir / "rank_gap_probe.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe rank failure logit gaps for a fixed checkpoint and dataset.")
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--tie-epsilon", type=float, default=1e-6)
    args = parser.parse_args()
    result = run_probe(
        checkpoint_path=args.checkpoint_path,
        manifest_path=args.manifest_path,
        output_dir=args.output_dir,
        device=args.device,
        max_samples=args.max_samples,
        tie_epsilon=args.tie_epsilon,
    )
    print(json.dumps({"status": result["status"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
