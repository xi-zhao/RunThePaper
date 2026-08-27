#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_TEMPERATURES = [0.1, 0.25, 0.5, 1.0, 2.0]
SMALL_SCORE_GAP = 0.0081
LARGE_SCORE_GAP = 0.05


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def load_failure_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        raise ValueError(f"unsupported failure JSON root: {type(payload).__name__}")
    for key in ("failures", "example_failures", "rows"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    raise ValueError("failure JSON must contain a failures, example_failures, or rows list")


def load_failure_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return load_jsonl(path)
    return load_failure_json(path)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def score_from_logit(logit: float, temperature: float, score_method: str) -> float:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    scaled = float(logit) / float(temperature)
    if score_method == "logits":
        return scaled
    if score_method == "sigmoid":
        return sigmoid(scaled)
    raise ValueError(f"unsupported score_method: {score_method}")


def score_gap(row: dict[str, Any], temperature: float, score_method: str) -> tuple[float | None, str]:
    if "winner_logit" in row and "positive_logit" in row:
        winner = score_from_logit(float(row["winner_logit"]), temperature, score_method)
        positive = score_from_logit(float(row["positive_logit"]), temperature, score_method)
        return winner - positive, "recomputed_from_logits"
    if "winner_score_logit" in row and "positive_score_logit" in row:
        winner = score_from_logit(float(row["winner_score_logit"]), temperature, score_method)
        positive = score_from_logit(float(row["positive_score_logit"]), temperature, score_method)
        return winner - positive, "recomputed_from_logits"
    if "score_gap_to_winner" in row:
        return float(row["score_gap_to_winner"]), "precomputed_gap_only"
    return None, "missing_score_gap"


def geometry_bucket(row: dict[str, Any]) -> str:
    if bool(row.get("winner_closer_than_positive")):
        return "winner_geometrically_closer"
    if bool(row.get("winner_same_distance_shell")):
        return "winner_same_distance_shell"
    if "winner_distance_minus_positive" in row and float(row["winner_distance_minus_positive"]) > 0.0:
        return "winner_farther_than_positive"
    return "geometry_unknown"


def rank_bucket(row: dict[str, Any]) -> str:
    rank = row.get("rank", row.get("positive_rank"))
    if rank is None:
        return "rank_missing"
    rank_int = int(rank)
    if rank_int == 1:
        return "rank1"
    if 2 <= rank_int <= 4:
        return "rank2_to_4"
    return "rank_gt4"


def is_geometry_or_near_tie(row: dict[str, Any], gap: float | None) -> bool:
    if bool(row.get("winner_closer_than_positive")) or bool(row.get("winner_same_distance_shell")):
        return True
    return gap is not None and gap <= SMALL_SCORE_GAP


def is_far_large_margin(row: dict[str, Any], gap: float | None) -> bool:
    if gap is None:
        return False
    return (
        float(row.get("winner_distance_minus_positive", 0.0)) > 0.0
        and gap > LARGE_SCORE_GAP
        and rank_bucket(row) == "rank_gt4"
    )


def summarize_rows(
    rows: list[dict[str, Any]],
    *,
    temperature: float,
    score_method: str,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    gap_sources: Counter[str] = Counter()
    score_gaps: list[float] = []
    for row in rows:
        gap, source = score_gap(row, temperature, score_method)
        gap_sources[source] += 1
        if gap is not None:
            score_gaps.append(gap)
        counts["rows"] += 1
        counts[f"geometry:{geometry_bucket(row)}"] += 1
        counts[f"rank:{rank_bucket(row)}"] += 1
        if is_geometry_or_near_tie(row, gap):
            counts["geometry_or_near_tie"] += 1
        if is_far_large_margin(row, gap):
            counts["far_large_margin"] += 1

    denominator = max(1, counts["rows"])
    return {
        "temperature": temperature,
        "score_method": score_method,
        "row_count": counts["rows"],
        "gap_sources": dict(gap_sources),
        "geometry_or_near_tie_fraction": counts["geometry_or_near_tie"] / denominator,
        "far_large_margin_fraction": counts["far_large_margin"] / denominator,
        "rank2_to_4_fraction": counts["rank:rank2_to_4"] / denominator,
        "rank_gt4_fraction": counts["rank:rank_gt4"] / denominator,
        "winner_geometrically_closer_fraction": counts["geometry:winner_geometrically_closer"] / denominator,
        "winner_same_distance_shell_fraction": counts["geometry:winner_same_distance_shell"] / denominator,
        "score_gap": summarize_numbers(score_gaps),
    }


def summarize_numbers(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "mean": None, "max": None}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": ordered[0],
        "mean": sum(ordered) / len(ordered),
        "max": ordered[-1],
    }


def stress_decision(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not summaries:
        return {"status": "blocked_missing_rows", "reason": "no failure rows were provided"}
    any_logits = any(summary["gap_sources"].get("recomputed_from_logits", 0) > 0 for summary in summaries)
    fractions = [float(summary["geometry_or_near_tie_fraction"]) for summary in summaries]
    fraction_range = max(fractions) - min(fractions)
    if not any_logits:
        status = "blocked_missing_frozen_logits"
        recommendation = "collect frozen logits or accept only the baseline margin-bin re-slice"
    elif fraction_range <= 0.02:
        status = "geometry_ceiling_stable_under_temperature"
        recommendation = "do not expect train128 to lift rank1 by more than +0.001"
    else:
        status = "score_calibration_sensitive"
        recommendation = "inspect score calibration before spending A100 on scale"
    return {
        "status": status,
        "geometry_or_near_tie_fraction_range": fraction_range,
        "has_frozen_logits": any_logits,
        "recommendation": recommendation,
    }


def build_result(rows: list[dict[str, Any]], temperatures: list[float], score_method: str) -> dict[str, Any]:
    summaries = [
        summarize_rows(rows, temperature=temperature, score_method=score_method)
        for temperature in temperatures
    ]
    return {
        "artifact_type": "geometry_ceiling_stress_test",
        "mode": "eval_only",
        "does_not_train": True,
        "score_method": score_method,
        "temperatures": temperatures,
        "summaries": summaries,
        "decision": stress_decision(summaries),
    }


def dry_run_contract() -> dict[str, Any]:
    return {
        "status": "dry_run",
        "artifact_type": "geometry_ceiling_stress_test",
        "mode": "eval_only",
        "does_not_train": True,
        "required_inputs": [
            "failure rows JSON/JSONL with rank/geometry fields",
            "optional winner_logit and positive_logit fields for true temperature sweep",
        ],
        "fallback_without_logits": "margin-bin re-slice only; decision becomes blocked_missing_frozen_logits",
        "default_temperatures": DEFAULT_TEMPERATURES,
        "decision_statuses": [
            "geometry_ceiling_stable_under_temperature",
            "score_calibration_sensitive",
            "blocked_missing_frozen_logits",
            "blocked_missing_rows",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--failure-rows", type=Path, help="Path to JSONL rows or JSON with failures/example_failures/rows.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--score-method", choices=["sigmoid", "logits"], default="sigmoid")
    parser.add_argument("--temperatures", nargs="*", type=float, default=DEFAULT_TEMPERATURES)
    args = parser.parse_args(argv)

    if args.dry_run or args.failure_rows is None:
        print(json.dumps(dry_run_contract(), indent=2, sort_keys=True))
        return 0

    rows = load_failure_rows(args.failure_rows)
    result = build_result(rows, args.temperatures, args.score_method)
    result["input_path"] = str(args.failure_rows)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "written", "output": str(args.output)}, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
