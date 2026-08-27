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


def as_numpy(values: Any) -> np.ndarray:
    if hasattr(values, "detach"):
        return values.detach().cpu().numpy()
    return np.asarray(values, dtype=np.float64)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=np.float64), q))


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "p10": None, "p90": None, "p95": None, "max": None}
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


def source_positive_rows(sample: Any, logits: np.ndarray) -> list[dict[str, Any]]:
    n_atoms = int(len(sample.atom_positions))
    by_source: dict[int, list[int]] = defaultdict(list)
    for edge_pos, edge_type in enumerate(sample.edge_types):
        if int(edge_type) == EDGE_ATOM_TO_TARGET:
            by_source[int(sample.edge_index[0, edge_pos])].append(int(edge_pos))

    rows: list[dict[str, Any]] = []
    for source, edge_positions in by_source.items():
        for positive_edge in edge_positions:
            if float(sample.edge_labels[positive_edge]) <= 0.5:
                continue
            positive_logit = float(logits[positive_edge])
            negative_gaps = [
                float(logits[edge_pos]) - positive_logit
                for edge_pos in edge_positions
                if float(sample.edge_labels[edge_pos]) <= 0.5 and float(logits[edge_pos]) > positive_logit
            ]
            rows.append(
                {
                    "source": int(source),
                    "target": int(sample.edge_index[1, positive_edge]) - n_atoms,
                    "positive_edge": int(positive_edge),
                    "rank": int(1 + len(negative_gaps)),
                    "positive_logit": positive_logit,
                    "closest_beating_negative_gap": min(negative_gaps) if negative_gaps else 0.0,
                    "beating_negative_count": int(len(negative_gaps)),
                }
            )
    return rows


def run_check(
    *,
    control_checkpoint: Path,
    margin_checkpoint: Path,
    manifest_path: Path,
    output_dir: Path,
    device: str,
    margin_value: float,
    max_samples: int | None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "margin_mechanism_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    control_model = load_edge_scoring_model(control_checkpoint, device=device)
    margin_model = load_edge_scoring_model(margin_checkpoint, device=device)
    started = time.monotonic()

    positive_count = 0
    control_rank1 = 0
    margin_rank1 = 0
    fixed_rows: list[dict[str, Any]] = []
    worsened_rows: list[dict[str, Any]] = []
    improved_rows: list[dict[str, Any]] = []
    degraded_rows: list[dict[str, Any]] = []
    fixed_gap_values: list[float] = []
    worsened_margin_gap_values: list[float] = []
    fixed_control_rank_hist = Counter()
    fixed_margin_active = 0
    fixed_within_half_margin = 0
    sample_count = 0

    for sample_index, sample in enumerate(iter_dataset_manifest_samples(manifest_path), start=1):
        if max_samples is not None and sample_index > max_samples:
            break
        control_logits = as_numpy(predict_edge_logits(control_model, sample))
        margin_logits = as_numpy(predict_edge_logits(margin_model, sample))
        control_rows = source_positive_rows(sample, control_logits)
        margin_rows = source_positive_rows(sample, margin_logits)
        margin_by_key = {(row["source"], row["target"]): row for row in margin_rows}
        for control_row in control_rows:
            key = (control_row["source"], control_row["target"])
            margin_row = margin_by_key[key]
            positive_count += 1
            control_rank = int(control_row["rank"])
            margin_rank = int(margin_row["rank"])
            control_rank1 += int(control_rank == 1)
            margin_rank1 += int(margin_rank == 1)
            delta_rank = margin_rank - control_rank
            record = {
                "sample_index": int(sample_index),
                "source": int(control_row["source"]),
                "target": int(control_row["target"]),
                "control_rank": control_rank,
                "margin_rank": margin_rank,
                "delta_rank": int(delta_rank),
                "control_gap": float(control_row["closest_beating_negative_gap"]),
                "margin_gap": float(margin_row["closest_beating_negative_gap"]),
            }
            if control_rank > 1 and margin_rank == 1:
                fixed_rows.append(record)
                fixed_gap_values.append(float(control_row["closest_beating_negative_gap"]))
                fixed_control_rank_hist[control_rank] += 1
                fixed_margin_active += int(float(control_row["closest_beating_negative_gap"]) <= float(margin_value))
                fixed_within_half_margin += int(float(control_row["closest_beating_negative_gap"]) <= 0.5 * float(margin_value))
            if control_rank == 1 and margin_rank > 1:
                worsened_rows.append(record)
                worsened_margin_gap_values.append(float(margin_row["closest_beating_negative_gap"]))
            if delta_rank < 0:
                improved_rows.append(record)
            elif delta_rank > 0:
                degraded_rows.append(record)
        sample_count += 1
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "event": "sample",
                        "sample_index": sample_index,
                        "positive_count": positive_count,
                        "fixed_count": len(fixed_rows),
                        "worsened_count": len(worsened_rows),
                        "elapsed_seconds": time.monotonic() - started,
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    summary = {
        "sample_count": int(sample_count),
        "positive_count": int(positive_count),
        "control_rank1": int(control_rank1),
        "margin_rank1": int(margin_rank1),
        "net_rank1_delta": int(margin_rank1 - control_rank1),
        "control_rank1_rate": float(control_rank1 / positive_count) if positive_count else None,
        "margin_rank1_rate": float(margin_rank1 / positive_count) if positive_count else None,
        "fixed_count": int(len(fixed_rows)),
        "worsened_count": int(len(worsened_rows)),
        "improved_any_rank_count": int(len(improved_rows)),
        "degraded_any_rank_count": int(len(degraded_rows)),
        "fixed_control_gap_summary": summarize(fixed_gap_values),
        "worsened_margin_gap_summary": summarize(worsened_margin_gap_values),
        "fixed_control_rank_histogram": {str(rank): int(count) for rank, count in sorted(fixed_control_rank_hist.items())},
        "fixed_margin_active_fraction": float(fixed_margin_active / len(fixed_rows)) if fixed_rows else None,
        "fixed_within_half_margin_fraction": float(fixed_within_half_margin / len(fixed_rows)) if fixed_rows else None,
        "margin_value": float(margin_value),
        "mechanism_supported": bool(fixed_rows and fixed_margin_active / len(fixed_rows) >= 0.9),
    }
    result = {
        "status": "completed",
        "control_checkpoint": str(control_checkpoint),
        "margin_checkpoint": str(margin_checkpoint),
        "manifest_path": str(manifest_path),
        "summary": summary,
        "fixed_examples": sorted(fixed_rows, key=lambda row: (row["control_rank"], -row["control_gap"]), reverse=True)[:50],
        "worsened_examples": sorted(worsened_rows, key=lambda row: (row["margin_rank"], -row["margin_gap"]), reverse=True)[:50],
    }
    (output_dir / "margin_mechanism_check.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare control and margin checkpoints to test margin mechanism.")
    parser.add_argument("--control-checkpoint", type=Path, required=True)
    parser.add_argument("--margin-checkpoint", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--margin-value", type=float, default=0.55)
    parser.add_argument("--max-samples", type=int)
    args = parser.parse_args()
    result = run_check(
        control_checkpoint=args.control_checkpoint,
        margin_checkpoint=args.margin_checkpoint,
        manifest_path=args.manifest_path,
        output_dir=args.output_dir,
        device=args.device,
        margin_value=args.margin_value,
        max_samples=args.max_samples,
    )
    print(json.dumps({"status": "completed", "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
