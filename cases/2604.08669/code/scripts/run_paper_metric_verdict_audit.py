#!/usr/bin/env python3
"""Eval-only paper metric verdict audit for stage13 checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from atom_path_planner import (  # noqa: E402
    dataset_sample_paths,
    diagnose_assignment_sample,
    load_edge_scoring_model,
    load_graph_sample_npz,
    predict_edge_scores,
    summarize_assignment_diagnostics,
)


PAPER_GNN_AVERAGE_DISTANCE = 0.512
PAPER_GNN_MAX_DISTANCE = 1.93


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[int(position)])
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    weight = position - lower
    return float(lower_value * (1.0 - weight) + upper_value * weight)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _assignment_value(row: dict[str, Any], key: str) -> float:
    return float(row.get("assignment", {}).get(key, 0.0))


def summarize_paper_metrics(
    rows: list[dict[str, Any]],
    *,
    paper_average: float | None = None,
    paper_max: float | None = None,
    paper_average_distance: float = PAPER_GNN_AVERAGE_DISTANCE,
    paper_max_distance: float = PAPER_GNN_MAX_DISTANCE,
    worst_tail_count: int = 10,
) -> dict[str, Any]:
    if paper_average is not None:
        paper_average_distance = paper_average
    if paper_max is not None:
        paper_max_distance = paper_max

    predicted_average = [_assignment_value(row, "predicted_average_distance") for row in rows]
    predicted_max = [_assignment_value(row, "predicted_max_distance") for row in rows]
    optimal_average = [_assignment_value(row, "optimal_average_distance") for row in rows]
    optimal_max = [_assignment_value(row, "optimal_max_distance") for row in rows]
    average_gap = [_assignment_value(row, "average_distance_gap") for row in rows]
    max_gap = [_assignment_value(row, "max_distance_gap") for row in rows]

    mean_predicted_average = _mean(predicted_average)
    mean_predicted_max = _mean(predicted_max)
    average_distance_passed = (
        mean_predicted_average is not None and mean_predicted_average < paper_average_distance
    )
    max_distance_passed = mean_predicted_max is not None and mean_predicted_max < paper_max_distance

    worst_rows = sorted(
        rows,
        key=lambda row: _assignment_value(row, "predicted_max_distance"),
        reverse=True,
    )[: max(0, worst_tail_count)]
    worst_predicted_max_rows = []
    for row in worst_rows:
        assignment = row.get("assignment", {})
        worst_predicted_max_rows.append(
            {
                "sample_index": row.get("sample_index"),
                "sample_path": row.get("sample_path"),
                "predicted_average_distance": assignment.get("predicted_average_distance"),
                "predicted_max_distance": assignment.get("predicted_max_distance"),
                "optimal_average_distance": assignment.get("optimal_average_distance"),
                "optimal_max_distance": assignment.get("optimal_max_distance"),
                "average_distance_gap": assignment.get("average_distance_gap"),
                "max_distance_gap": assignment.get("max_distance_gap"),
            }
        )

    return {
        "eval_samples": len(rows),
        "paper_gnn_reference": {
            "average_distance": paper_average_distance,
            "max_distance": paper_max_distance,
            "source": "paper_fig3_gnn",
        },
        "mean_predicted_average_distance": mean_predicted_average,
        "mean_predicted_max_distance": mean_predicted_max,
        "mean_optimal_average_distance": _mean(optimal_average),
        "mean_optimal_max_distance": _mean(optimal_max),
        "mean_average_distance_gap": _mean(average_gap),
        "mean_max_distance_gap": _mean(max_gap),
        "predicted_average_distance_tail": {
            "p50": percentile(predicted_average, 0.50),
            "p90": percentile(predicted_average, 0.90),
            "p99": percentile(predicted_average, 0.99),
            "max": max(predicted_average) if predicted_average else None,
            "count_over_paper_average": sum(
                1 for value in predicted_average if value > paper_average_distance
            ),
        },
        "predicted_max_distance_tail": {
            "p50": percentile(predicted_max, 0.50),
            "p90": percentile(predicted_max, 0.90),
            "p99": percentile(predicted_max, 0.99),
            "max": max(predicted_max) if predicted_max else None,
            "count_over_paper_max": sum(1 for value in predicted_max if value > paper_max_distance),
        },
        "surpass_paper_gnn": {
            "average_distance_passed": average_distance_passed,
            "max_distance_passed": max_distance_passed,
            "passed": bool(average_distance_passed and max_distance_passed),
            "rule": "mean_predicted_average_distance < paper_average_distance and "
            "mean_predicted_max_distance < paper_max_distance",
        },
        "worst_predicted_max_rows": worst_predicted_max_rows,
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def run_manifest_checkpoint_diagnostics(
    *,
    checkpoint_path: Path,
    output_dir: Path,
    dataset_manifest_path: Path,
    eval_samples: int,
    device: str,
    progress_every_samples: int,
) -> dict[str, Any]:
    if eval_samples <= 0:
        raise ValueError("eval_samples must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "diagnostics_progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    eval_paths = dataset_sample_paths(dataset_manifest_path)
    if not eval_paths:
        raise ValueError("dataset manifest does not contain samples")

    model = load_edge_scoring_model(checkpoint_path, device=device)
    rows: list[dict[str, Any]] = []
    started = time.monotonic()
    for idx in range(1, eval_samples + 1):
        sample_started = time.monotonic()
        sample_path = eval_paths[(idx - 1) % len(eval_paths)]
        sample = load_graph_sample_npz(sample_path)
        scores = predict_edge_scores(model, sample)
        row = diagnose_assignment_sample(sample, scores)
        row["sample_index"] = idx
        row["sample_path"] = str(sample_path)
        rows.append(row)
        if progress_every_samples > 0 and (idx % progress_every_samples == 0 or idx == eval_samples):
            append_progress(
                progress_path,
                {
                    "event": "sample",
                    "sample_index": idx,
                    "eval_samples": eval_samples,
                    "average_distance_gap": row["assignment"]["average_distance_gap"],
                    "max_distance_gap": row["assignment"]["max_distance_gap"],
                    "rank1_rate": row["source_rank"]["rank1_rate"],
                    "elapsed_seconds": time.monotonic() - started,
                    "sample_seconds": time.monotonic() - sample_started,
                },
            )

    summary = summarize_assignment_diagnostics(rows)
    append_progress(
        progress_path,
        {
            "event": "completed",
            "eval_samples": eval_samples,
            "elapsed_seconds": time.monotonic() - started,
        },
    )
    rows_path = output_dir / "diagnostic_rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(json_ready(row), sort_keys=True) + "\n")

    return {
        "status": "completed",
        "checkpoint_path": str(checkpoint_path),
        "config": {
            "dataset_manifest_path": str(dataset_manifest_path),
            "eval_samples": eval_samples,
            "device": device,
        },
        "summary": summary,
        "artifacts": {
            "diagnostic_rows_path": str(rows_path),
            "progress_path": str(progress_path),
        },
    }


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_candidates(root: Path) -> dict[str, Path]:
    return {
        "objective_pair_treatment_src_tgt_topk": root
        / "outputs/checks/paper_gnn_target_stage13_objective_pair_u0512/"
        "treatment_src_tgt_topk_u0512/model_state.pt",
        "objective_pair_treatment_freshopt_src_tgt_topk": root
        / "outputs/checks/paper_gnn_target_stage13_objective_pair_treatment_freshopt_u0512/"
        "treatment_src_tgt_topk_freshopt_u0512/model_state.pt",
    }


def default_splits(root: Path, shard32_samples: int, val64_samples: int) -> dict[str, dict[str, Any]]:
    return {
        "shard32": {
            "manifest": root / "outputs/datasets/paper_gnn_target_fig3_v1_shard32/manifest.json",
            "eval_samples": shard32_samples,
        },
        "val64": {
            "manifest": root / "outputs/datasets/paper_gnn_target_fig3_v1_val64/manifest.json",
            "eval_samples": val64_samples,
        },
    }


def parse_candidate_specs(specs: list[str] | None, root: Path) -> dict[str, Path]:
    if not specs:
        return default_candidates(root)
    parsed: dict[str, Path] = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"candidate spec must be name=path, got {spec!r}")
        name, path_text = spec.split("=", 1)
        path = Path(path_text)
        if not path.is_absolute():
            path = root / path
        parsed[name] = path
    return parsed


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_progress(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"time": time.time(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(json_ready(payload), sort_keys=True) + "\n")


def choose_decision(results: dict[str, Any]) -> dict[str, Any]:
    ready_candidates = []
    for candidate_name, candidate in results.get("candidates", {}).items():
        val64 = candidate.get("splits", {}).get("val64", {})
        summary = val64.get("paper_metric_summary")
        if not summary:
            continue
        ready_candidates.append((candidate_name, summary))

    if not ready_candidates:
        return {
            "status": "blocked_missing_val64_verdict",
            "next_action": "complete_eval_only_audit_before_training",
        }

    passed = [
        (name, summary)
        for name, summary in ready_candidates
        if summary.get("surpass_paper_gnn", {}).get("passed")
    ]
    if passed:
        best = min(
            passed,
            key=lambda item: (
                item[1].get("mean_predicted_average_distance", float("inf")),
                item[1].get("mean_predicted_max_distance", float("inf")),
            ),
        )
        return {
            "status": "surpass_paper_gnn_candidate",
            "best_candidate": best[0],
            "next_action": "promote_to_larger_validation_only_after_user_confirmation",
        }

    max_pass_avg_fail = []
    for name, summary in ready_candidates:
        verdict = summary.get("surpass_paper_gnn", {})
        if verdict.get("max_distance_passed") and not verdict.get("average_distance_passed"):
            max_pass_avg_fail.append((name, summary))
    if max_pass_avg_fail:
        best = min(
            max_pass_avg_fail,
            key=lambda item: item[1].get("mean_predicted_average_distance", float("inf")),
        )
        return {
            "status": "distance_tiebreak_objective_needed",
            "best_candidate": best[0],
            "next_action": "design_small_distance_tiebreak_objective_before_scaling_training",
        }

    return {
        "status": "paper_metric_verdict_stop",
        "next_action": "do_not_expand_training_until_avg_and_max_failure_modes_are_explained",
    }


def run_verdict_audit(
    *,
    output_dir: Path,
    candidates: dict[str, Path],
    splits: dict[str, dict[str, Any]],
    device: str,
    paper_average_distance: float,
    paper_max_distance: float,
    progress_every_samples: int,
    worst_tail_count: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "paper_metric_verdict_progress.jsonl"
    if progress_path.exists():
        progress_path.unlink()

    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "paper_metric_verdict_audit",
        "root": str(ROOT),
        "platform": platform.platform(),
        "paper_gnn_reference": {
            "average_distance": paper_average_distance,
            "max_distance": paper_max_distance,
        },
        "candidates": {},
    }

    for candidate_name, checkpoint_path in candidates.items():
        candidate_result: dict[str, Any] = {
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_ready": checkpoint_path.exists(),
            "splits": {},
        }
        result["candidates"][candidate_name] = candidate_result
        append_progress(
            progress_path,
            {
                "event": "candidate_start",
                "candidate": candidate_name,
                "checkpoint_ready": checkpoint_path.exists(),
            },
        )

        for split_name, split in splits.items():
            manifest_path = Path(split["manifest"])
            split_result: dict[str, Any] = {
                "manifest_path": str(manifest_path),
                "manifest_ready": manifest_path.exists(),
                "manifest_sha256": file_sha256(manifest_path),
                "eval_samples_requested": int(split["eval_samples"]),
            }
            candidate_result["splits"][split_name] = split_result
            if not checkpoint_path.exists() or not manifest_path.exists():
                split_result["status"] = "missing_checkpoint_or_manifest"
                append_progress(
                    progress_path,
                    {
                        "event": "split_skipped_missing_input",
                        "candidate": candidate_name,
                        "split": split_name,
                        "checkpoint_ready": checkpoint_path.exists(),
                        "manifest_ready": manifest_path.exists(),
                    },
                )
                continue

            split_output = output_dir / candidate_name / split_name
            append_progress(
                progress_path,
                {
                    "event": "split_eval_start",
                    "candidate": candidate_name,
                    "split": split_name,
                    "eval_samples": int(split["eval_samples"]),
                },
            )
            diagnostics = run_manifest_checkpoint_diagnostics(
                checkpoint_path=checkpoint_path,
                output_dir=split_output,
                dataset_manifest_path=manifest_path,
                device=device,
                eval_samples=int(split["eval_samples"]),
                progress_every_samples=progress_every_samples,
            )
            rows_path = Path(diagnostics["artifacts"]["diagnostic_rows_path"])
            rows = read_jsonl(rows_path)
            paper_metric_summary = summarize_paper_metrics(
                rows,
                paper_average_distance=paper_average_distance,
                paper_max_distance=paper_max_distance,
                worst_tail_count=worst_tail_count,
            )
            split_result.update(
                {
                    "status": "ready",
                    "diagnostics_artifacts": diagnostics.get("artifacts", {}),
                    "diagnostics_summary": diagnostics.get("summary", {}),
                    "paper_metric_summary": paper_metric_summary,
                }
            )
            write_json(split_output / "paper_metric_summary.json", paper_metric_summary)
            append_progress(
                progress_path,
                {
                    "event": "split_eval_ready",
                    "candidate": candidate_name,
                    "split": split_name,
                    "mean_predicted_average_distance": paper_metric_summary.get(
                        "mean_predicted_average_distance"
                    ),
                    "mean_predicted_max_distance": paper_metric_summary.get(
                        "mean_predicted_max_distance"
                    ),
                    "surpass_paper_gnn": paper_metric_summary.get("surpass_paper_gnn", {}).get(
                        "passed"
                    ),
                },
            )

    result["decision"] = choose_decision(result)
    write_json(output_dir / "paper_metric_verdict_audit.json", result)
    (output_dir / "paper_metric_verdict_audit.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    append_progress(progress_path, {"event": "audit_ready", "decision": result["decision"]})
    return result


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Paper Metric Verdict Audit",
        "",
        "This is eval-only. It does not start or resume training.",
        "",
        "## Decision",
        "",
        f"- status: `{result.get('decision', {}).get('status')}`",
        f"- next action: `{result.get('decision', {}).get('next_action')}`",
        "",
        "## Paper GNN Reference",
        "",
        f"- average distance: `{result.get('paper_gnn_reference', {}).get('average_distance')}`",
        f"- max distance: `{result.get('paper_gnn_reference', {}).get('max_distance')}`",
        "",
        "## Candidates",
        "",
    ]
    for candidate_name, candidate in result.get("candidates", {}).items():
        lines.append(f"### {candidate_name}")
        lines.append("")
        for split_name, split in candidate.get("splits", {}).items():
            summary = split.get("paper_metric_summary")
            if not summary:
                lines.append(f"- {split_name}: `{split.get('status')}`")
                continue
            verdict = summary.get("surpass_paper_gnn", {})
            lines.append(
                f"- {split_name}: avg `{summary.get('mean_predicted_average_distance')}`, "
                f"max `{summary.get('mean_predicted_max_distance')}`, "
                f"paper-pass `{verdict.get('passed')}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_dry_run_payload(
    *,
    output_dir: Path,
    candidates: dict[str, Path],
    splits: dict[str, dict[str, Any]],
    paper_average_distance: float,
    paper_max_distance: float,
) -> dict[str, Any]:
    return {
        "kind": "paper_metric_verdict_audit_dry_run",
        "root": str(ROOT),
        "output_dir": str(output_dir),
        "paper_gnn_reference": {
            "average_distance": paper_average_distance,
            "max_distance": paper_max_distance,
        },
        "candidates": {
            name: {"checkpoint_path": str(path), "checkpoint_ready": path.exists()}
            for name, path in candidates.items()
        },
        "splits": {
            name: {
                "manifest_path": str(Path(split["manifest"])),
                "manifest_ready": Path(split["manifest"]).exists(),
                "manifest_sha256": file_sha256(Path(split["manifest"])),
                "eval_samples": int(split["eval_samples"]),
            }
            for name, split in splits.items()
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs/checks/paper_gnn_target_stage13_paper_metric_verdict_audit",
    )
    parser.add_argument("--candidate", action="append", help="Candidate checkpoint as name=path.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--paper-average-distance", type=float, default=PAPER_GNN_AVERAGE_DISTANCE)
    parser.add_argument("--paper-max-distance", type=float, default=PAPER_GNN_MAX_DISTANCE)
    parser.add_argument("--shard32-samples", type=int, default=32)
    parser.add_argument("--val64-samples", type=int, default=64)
    parser.add_argument("--progress-every-samples", type=int, default=1)
    parser.add_argument("--worst-tail-count", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    candidates = parse_candidate_specs(args.candidate, ROOT)
    splits = default_splits(ROOT, args.shard32_samples, args.val64_samples)
    if args.dry_run:
        payload = build_dry_run_payload(
            output_dir=output_dir,
            candidates=candidates,
            splits=splits,
            paper_average_distance=args.paper_average_distance,
            paper_max_distance=args.paper_max_distance,
        )
        print(json.dumps(json_ready(payload), indent=2, sort_keys=True))
        return

    result = run_verdict_audit(
        output_dir=output_dir,
        candidates=candidates,
        splits=splits,
        device=args.device,
        paper_average_distance=args.paper_average_distance,
        paper_max_distance=args.paper_max_distance,
        progress_every_samples=args.progress_every_samples,
        worst_tail_count=args.worst_tail_count,
    )
    print(json.dumps(json_ready({"decision": result["decision"]}), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
