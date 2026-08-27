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
SCORE_SPACE_SENSITIVITY = 0.02
GEOMETRY_CEILING_FRACTION = 0.70
MODEL_GAP_FAR_LARGE_MARGIN_FRACTION = 0.15
MODEL_GAP_RANK_GT4_FRACTION = 0.25


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


def load_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def has_frozen_logits(row: dict[str, Any]) -> bool:
    return ("winner_logit" in row and "positive_logit" in row) or (
        "winner_score_logit" in row and "positive_score_logit" in row
    )


def raw_logit_gap(row: dict[str, Any]) -> float | None:
    if "winner_logit" in row and "positive_logit" in row:
        return float(row["winner_logit"]) - float(row["positive_logit"])
    if "winner_score_logit" in row and "positive_score_logit" in row:
        return float(row["winner_score_logit"]) - float(row["positive_score_logit"])
    return None


def score_gap(row: dict[str, Any], *, temperature: float, score_method: str) -> float | None:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if not has_frozen_logits(row):
        return None
    if "winner_logit" in row and "positive_logit" in row:
        winner_logit = float(row["winner_logit"])
        positive_logit = float(row["positive_logit"])
    else:
        winner_logit = float(row["winner_score_logit"])
        positive_logit = float(row["positive_score_logit"])
    if score_method == "scaled_logits":
        return (winner_logit - positive_logit) / float(temperature)
    if score_method == "sigmoid":
        return sigmoid(winner_logit / float(temperature)) - sigmoid(positive_logit / float(temperature))
    raise ValueError(f"unsupported score_method: {score_method}")


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


def winner_farther(row: dict[str, Any]) -> bool:
    return float(row.get("winner_distance_minus_positive", 0.0)) > 0.0


def geometry_or_near_tie(row: dict[str, Any], gap: float | None) -> bool:
    if bool(row.get("winner_closer_than_positive")) or bool(row.get("winner_same_distance_shell")):
        return True
    return gap is not None and gap <= SMALL_SCORE_GAP


def far_large_margin(row: dict[str, Any], gap: float | None) -> bool:
    return gap is not None and winner_farther(row) and gap > LARGE_SCORE_GAP and rank_bucket(row) == "rank_gt4"


def summarize_numbers(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "p10": None, "median": None, "mean": None, "p90": None, "max": None}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": ordered[0],
        "p10": percentile(ordered, 10),
        "median": percentile(ordered, 50),
        "mean": sum(ordered) / len(ordered),
        "p90": percentile(ordered, 90),
        "max": ordered[-1],
    }


def percentile(ordered_values: list[float], q: float) -> float:
    if not ordered_values:
        raise ValueError("percentile requires at least one value")
    if len(ordered_values) == 1:
        return ordered_values[0]
    position = (len(ordered_values) - 1) * (q / 100.0)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered_values[lower]
    weight = position - lower
    return ordered_values[lower] * (1.0 - weight) + ordered_values[upper] * weight


def fraction(count: int, denominator: int) -> float:
    return float(count) / float(max(1, denominator))


def summarize_raw_logits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    gaps: list[float] = []
    for row in rows:
        gap = raw_logit_gap(row)
        if gap is not None:
            gaps.append(gap)
        counts["rows"] += 1
        counts[f"rank:{rank_bucket(row)}"] += 1
        counts["has_frozen_logits"] += int(gap is not None)
        counts["geometry_or_near_tie"] += int(geometry_or_near_tie(row, gap))
        counts["far_large_margin"] += int(far_large_margin(row, gap))
        counts["winner_geometrically_closer"] += int(bool(row.get("winner_closer_than_positive")))
        counts["winner_same_distance_shell"] += int(bool(row.get("winner_same_distance_shell")))

    denominator = max(1, counts["rows"])
    return {
        "row_count": counts["rows"],
        "has_frozen_logits_count": counts["has_frozen_logits"],
        "geometry_or_near_tie_fraction": fraction(counts["geometry_or_near_tie"], denominator),
        "far_large_margin_fraction": fraction(counts["far_large_margin"], denominator),
        "rank2_to_4_fraction": fraction(counts["rank:rank2_to_4"], denominator),
        "rank_gt4_fraction": fraction(counts["rank:rank_gt4"], denominator),
        "winner_geometrically_closer_fraction": fraction(counts["winner_geometrically_closer"], denominator),
        "winner_same_distance_shell_fraction": fraction(counts["winner_same_distance_shell"], denominator),
        "logit_gap": summarize_numbers(gaps),
    }


def summarize_score_view(rows: list[dict[str, Any]], *, score_method: str, temperature: float) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    gaps: list[float] = []
    for row in rows:
        gap = score_gap(row, temperature=temperature, score_method=score_method)
        if gap is not None:
            gaps.append(gap)
        counts["rows"] += 1
        counts["geometry_or_near_tie"] += int(geometry_or_near_tie(row, gap))
        counts["far_large_margin"] += int(far_large_margin(row, gap))
    denominator = max(1, counts["rows"])
    return {
        "score_method": score_method,
        "temperature": temperature,
        "geometry_or_near_tie_fraction": fraction(counts["geometry_or_near_tie"], denominator),
        "far_large_margin_fraction": fraction(counts["far_large_margin"], denominator),
        "score_gap": summarize_numbers(gaps),
    }


def fraction_range(summaries: list[dict[str, Any]], key: str) -> float:
    if not summaries:
        return 0.0
    values = [float(summary[key]) for summary in summaries]
    return max(values) - min(values)


def build_decision(raw: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, Any]:
    has_logits = raw["has_frozen_logits_count"] > 0 and raw["has_frozen_logits_count"] == raw["row_count"]
    if raw["row_count"] == 0:
        return {
            "status": "blocked_missing_rows",
            "has_frozen_logits": False,
            "recommendation": "provide failure rows before calibration audit",
        }
    if not has_logits:
        return {
            "status": "blocked_missing_logits",
            "has_frozen_logits": False,
            "recommendation": "export winner_logit and positive_logit before temperature calibration",
        }
    if (
        raw["far_large_margin_fraction"] >= MODEL_GAP_FAR_LARGE_MARGIN_FRACTION
        or raw["rank_gt4_fraction"] >= MODEL_GAP_RANK_GT4_FRACTION
    ):
        return {
            "status": "model_extractable_gap_candidate",
            "has_frozen_logits": True,
            "recommendation": "do not scale data yet; inspect decoder-aligned or assignment-structured objective",
        }
    if artifacts["sigmoid_threshold_sensitive"] or artifacts["scaled_logit_fixed_threshold_sensitive"]:
        return {
            "status": "score_space_threshold_artifact",
            "has_frozen_logits": True,
            "recommendation": "keep go/no-go gates in raw logits or ranks; do not use sigmoid fixed-gap thresholds for scale approval",
        }
    if raw["geometry_or_near_tie_fraction"] >= GEOMETRY_CEILING_FRACTION:
        return {
            "status": "geometry_ceiling_confirmed",
            "has_frozen_logits": True,
            "recommendation": "train scale may be considered only after user approval and with Euclidean Fig.3 metrics as primary gates",
        }
    return {
        "status": "calibration_inconclusive",
        "has_frozen_logits": True,
        "recommendation": "collect more failure rows before approving scale training",
    }


def build_result(
    rows: list[dict[str, Any]],
    temperatures: list[float],
    *,
    plateau_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = summarize_raw_logits(rows)
    scaled_summaries = [
        summarize_score_view(rows, score_method="scaled_logits", temperature=temperature)
        for temperature in temperatures
    ]
    sigmoid_summaries = [
        summarize_score_view(rows, score_method="sigmoid", temperature=temperature)
        for temperature in temperatures
    ]
    scaled_range = fraction_range(scaled_summaries, "geometry_or_near_tie_fraction")
    sigmoid_range = fraction_range(sigmoid_summaries, "geometry_or_near_tie_fraction")
    artifacts = {
        "monotonic_rank_order_invariant": True,
        "scaled_logit_fixed_threshold_range": scaled_range,
        "sigmoid_threshold_range": sigmoid_range,
        "scaled_logit_fixed_threshold_sensitive": scaled_range > SCORE_SPACE_SENSITIVITY,
        "sigmoid_threshold_sensitive": sigmoid_range > SCORE_SPACE_SENSITIVITY,
        "sensitivity_threshold": SCORE_SPACE_SENSITIVITY,
    }
    result = {
        "artifact_type": "score_calibration_audit",
        "mode": "eval_only",
        "does_not_train": True,
        "thresholds": {
            "small_score_gap": SMALL_SCORE_GAP,
            "large_score_gap": LARGE_SCORE_GAP,
            "score_space_sensitivity": SCORE_SPACE_SENSITIVITY,
            "geometry_ceiling_fraction": GEOMETRY_CEILING_FRACTION,
            "model_gap_far_large_margin_fraction": MODEL_GAP_FAR_LARGE_MARGIN_FRACTION,
            "model_gap_rank_gt4_fraction": MODEL_GAP_RANK_GT4_FRACTION,
        },
        "temperatures": temperatures,
        "raw_logit_reference": raw,
        "scaled_logit_fixed_threshold_summaries": scaled_summaries,
        "sigmoid_threshold_summaries": sigmoid_summaries,
        "calibration_artifacts": artifacts,
        "decision": build_decision(raw, artifacts),
    }
    if plateau_result is not None:
        result["plateau_reference"] = {
            "status": plateau_result.get("status"),
            "decision": plateau_result.get("decision"),
            "combined": plateau_result.get("combined"),
        }
    return result


def dry_run_contract() -> dict[str, Any]:
    return {
        "status": "dry_run",
        "artifact_type": "score_calibration_audit",
        "mode": "eval_only",
        "does_not_train": True,
        "required_inputs": [
            "failure rows JSON/JSONL with winner_logit and positive_logit",
            "optional plateau_attribution_result.json for reference context",
        ],
        "decision_statuses": [
            "score_space_threshold_artifact",
            "geometry_ceiling_confirmed",
            "model_extractable_gap_candidate",
            "blocked_missing_logits",
            "blocked_missing_rows",
            "calibration_inconclusive",
        ],
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    decision = result["decision"]
    raw = result["raw_logit_reference"]
    artifacts = result["calibration_artifacts"]
    lines = [
        "# Stage13 Score Calibration Audit",
        "",
        "## Decision",
        f"- status: `{decision['status']}`",
        f"- recommendation: {decision['recommendation']}",
        "",
        "## Raw Logit Reference",
        f"- row_count: `{raw['row_count']}`",
        f"- geometry_or_near_tie_fraction: `{raw['geometry_or_near_tie_fraction']}`",
        f"- far_large_margin_fraction: `{raw['far_large_margin_fraction']}`",
        f"- rank_gt4_fraction: `{raw['rank_gt4_fraction']}`",
        "",
        "## Calibration Artifacts",
        f"- monotonic_rank_order_invariant: `{artifacts['monotonic_rank_order_invariant']}`",
        f"- scaled_logit_fixed_threshold_range: `{artifacts['scaled_logit_fixed_threshold_range']}`",
        f"- sigmoid_threshold_range: `{artifacts['sigmoid_threshold_range']}`",
        f"- scaled_logit_fixed_threshold_sensitive: `{artifacts['scaled_logit_fixed_threshold_sensitive']}`",
        f"- sigmoid_threshold_sensitive: `{artifacts['sigmoid_threshold_sensitive']}`",
        "",
        "## Boundary",
        "- This audit is eval-only and does not start or approve any training.",
        "- Training scale approval must still use paper Fig.3 Euclidean average/max distance as primary metrics.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--failure-rows", type=Path)
    parser.add_argument("--plateau-result", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--temperatures", nargs="*", type=float, default=DEFAULT_TEMPERATURES)
    args = parser.parse_args(argv)

    if args.dry_run or args.failure_rows is None:
        print(json.dumps(dry_run_contract(), indent=2, sort_keys=True))
        return 0

    rows = load_failure_rows(args.failure_rows)
    plateau_result = load_optional_json(args.plateau_result)
    result = build_result(rows, args.temperatures, plateau_result=plateau_result)
    result["input_path"] = str(args.failure_rows)
    if args.plateau_result is not None:
        result["plateau_result_path"] = str(args.plateau_result)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "score_calibration_audit.json"
        md_path = args.output_dir / "score_calibration_audit.md"
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(result, md_path)
        print(json.dumps({"status": "written", "json": str(json_path), "markdown": str(md_path)}, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
