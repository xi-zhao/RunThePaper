#!/usr/bin/env python3
"""Checkpointed clean-room multi-seed campaign for Figures 8 and 9."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))
sys.path.insert(0, str(WORKSPACE / "scripts"))

from independent_tn import optimize_network  # noqa: E402
from implementation_closure import emit_paper_scale_table_outputs  # noqa: E402
from run_independent_reimplementation import load_networks  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _validated_clean_archive(path: Path, expected_sha256: str) -> None:
    if sha256_file(path) != expected_sha256:
        raise ValueError("Clean circuit input archive SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            raise ValueError("Clean circuit input archive is corrupt")
    if any("/results/" in name or "/experiments/networks/" in name for name in names):
        raise ValueError("Clean archive contains an author result or network plan")


def _profile(config: dict[str, Any], smoke: bool) -> dict[str, Any]:
    key = "smoke" if smoke else "paper_scale"
    profile = config.get(key)
    if not isinstance(profile, dict):
        raise ValueError(f"Missing {key} profile")
    return profile


def _law_residual(stats: dict[str, Any]) -> float:
    return abs(
        float(stats["overhead"]) - (1.0 + 2.0 * float(stats["m"]) + float(stats["r"]))
    )


def run_campaign(
    config_path: Path,
    output_dir: Path,
    *,
    smoke: bool,
    shard_index: int,
    shard_count: int,
    resume: bool,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = _profile(config, smoke)
    archive_path = (WORKSPACE / config["input_boundary"]["archive"]).resolve()
    _validated_clean_archive(archive_path, config["input_boundary"]["archive_sha256"])
    networks = load_networks(archive_path)
    all_networks = {network.name: network for network in networks}
    requested = profile.get("circuits", "all")
    if requested != "all":
        names = set(requested)
        networks = [network for network in networks if network.name in names]
        if {network.name for network in networks} != names:
            raise ValueError("Smoke profile names an unknown circuit")

    seeds = [int(seed) for seed in profile["seeds"]]
    units = [(seed, network) for seed in seeds for network in networks]
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("Require 0 <= shard_index < shard_count")
    selected = [
        unit for index, unit in enumerate(units) if index % shard_count == shard_index
    ]
    config_digest = canonical_hash(
        {
            "profile": profile,
            "archive_sha256": config["input_boundary"]["archive_sha256"],
            "implementation_sha256": sha256_file(Path(__file__)),
        }
    )
    started = time.perf_counter()
    completed = skipped = 0
    for seed, network in selected:
        record_path = output_dir / "records" / f"seed-{seed}" / f"{network.name}.json"
        if resume and record_path.is_file():
            prior = json.loads(record_path.read_text(encoding="utf-8"))
            if (
                prior.get("config_digest") == config_digest
                and prior.get("network", {}).get("topology_sha256")
                == network.topology_sha256
                and prior.get("status") == "completed"
            ):
                skipped += 1
                continue
        unit_started = time.perf_counter()
        result = optimize_network(
            network,
            greedy_trials=int(profile["greedy_trials"]),
            anneal_steps=int(profile["anneal_steps"]),
            polish_steps=int(profile["polish_steps"]),
            seed=seed,
        )
        convert = result["convert_only"]
        full = result["full_anneal"]
        result.update(
            {
                "schema_version": 1,
                "paper_id": "2608.03987",
                "status": "completed",
                "execution_profile": "smoke" if smoke else "paper_scale",
                "config_digest": config_digest,
                "runtime_seconds": time.perf_counter() - unit_started,
                "pipeline_gap": abs(
                    float(convert["overhead"]) - float(full["overhead"])
                )
                / float(full["overhead"]),
                "maximum_cost_law_residual": max(
                    _law_residual(result[name])
                    for name in ("convert_only", "polished", "full_anneal")
                ),
                "numerical_input_policy": (
                    "clean raw circuits only; no author code, plans, result arrays, "
                    "digitized curves, or source pixels"
                ),
            }
        )
        atomic_json(record_path, result)
        completed += 1

    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for seed, network in units:
        path = output_dir / "records" / f"seed-{seed}" / f"{network.name}.json"
        if not path.is_file():
            missing.append(f"{seed}:{network.name}")
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        if (
            row.get("config_digest") != config_digest
            or row.get("status") != "completed"
        ):
            missing.append(f"{seed}:{network.name}:stale")
            continue
        records.append(row)

    threshold = float(config["acceptance"]["pipeline_gap_threshold"])
    aggregate: dict[str, Any] = {
        "schema_version": 1,
        "paper_id": "2608.03987",
        "execution_profile": "smoke" if smoke else "paper_scale",
        "config_digest": config_digest,
        "expected_units": len(units),
        "records_present": len(records),
        "missing_units": missing,
        "completed_this_invocation": completed,
        "skipped_this_invocation": skipped,
        "runtime_seconds": time.perf_counter() - started,
        "complete": not missing,
        "source_policy": "inputs clean circuit archive only",
    }
    if not missing:
        per_seed: dict[str, Any] = {}
        for seed in seeds:
            rows = [row for row in records if int(row["search"]["seed"]) == seed]
            gaps = [float(row["pipeline_gap"]) for row in rows]
            per_seed[str(seed)] = {
                "circuits": len(rows),
                "below_threshold": sum(gap < threshold for gap in gaps),
                "maximum_gap": max(gaps),
                "mean_gap": sum(gaps) / len(gaps),
            }
        aggregate.update(
            {
                "per_seed": per_seed,
                "maximum_cost_law_residual": max(
                    float(row["maximum_cost_law_residual"]) for row in records
                ),
                "acceptance": {
                    "all_units_complete": True,
                    "cost_law_passed": max(
                        float(row["maximum_cost_law_residual"]) for row in records
                    )
                    <= float(config["acceptance"]["cost_law_tolerance"]),
                    "minimum_seed_count_passed": len(seeds)
                    >= int(config["acceptance"]["minimum_seed_count"]),
                    "paper_claim_is_robust": all(
                        int(row["below_threshold"])
                        >= int(config["acceptance"]["paper_below_threshold_count"])
                        for row in per_seed.values()
                    ),
                },
            }
        )
        if not smoke:
            aggregate["table_targets"] = emit_paper_scale_table_outputs(
                records,
                all_networks,
                output_dir,
            )
    atomic_json(output_dir / "aggregate.json", aggregate)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=WORKSPACE / "config" / "paper_scale.json"
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.output_dir or WORKSPACE / "outputs" / (
        "data/paper_scale_smoke" if args.smoke else "data/paper_scale"
    )
    result = run_campaign(
        args.config,
        output,
        smoke=args.smoke,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        resume=args.resume,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
