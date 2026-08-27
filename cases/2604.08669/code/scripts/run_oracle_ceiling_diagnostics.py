#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from atom_path_planner import (  # noqa: E402
    GraphSample,
    diagnose_assignment_sample,
    iter_dataset_manifest_samples,
    iter_eval_samples,
    oracle_decoder_audit,
    summarize_assignment_diagnostics,
    summarize_eval_rows,
)


def oracle_profiles() -> dict[str, dict[str, Any]]:
    return {
        "paper_target": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "eval_samples": 64,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "stream_samples": True,
            "prefetch_workers": 8,
            "prefetch_buffer": 16,
            "progress_every_samples": 1,
            "seed": 260408690,
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_target_stage13_oracle_ceiling_eval64",
        },
        "canary": {
            "initial_side": 9,
            "target_side": 5,
            "k_neighbors": 16,
            "eval_samples": 2,
            "loading_probability": 0.75,
            "graph_backend": "kdtree",
            "stream_samples": False,
            "prefetch_workers": 0,
            "prefetch_buffer": 0,
            "progress_every_samples": 1,
            "seed": 260408690,
            "output_dir": ROOT / "outputs" / "checks" / "paper_gnn_oracle_canary",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run oracle ceiling diagnostics for 2604.08669 assignment decoding.")
    parser.add_argument("--profile", choices=sorted(oracle_profiles()), default="paper_target")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dataset-manifest-path", type=Path)
    parser.add_argument("--eval-samples", type=int)
    parser.add_argument("--target-lattice-spacing", type=float)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--prefetch-workers", type=int)
    parser.add_argument("--prefetch-buffer", type=int)
    parser.add_argument("--progress-every-samples", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = dict(oracle_profiles()[args.profile])
    for key in [
        "output_dir",
        "dataset_manifest_path",
        "eval_samples",
        "target_lattice_spacing",
        "seed",
        "prefetch_workers",
        "prefetch_buffer",
        "progress_every_samples",
    ]:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    config["profile"] = args.profile
    config["platform"] = platform_payload()

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    request_path = output_dir / "oracle_ceiling_request.json"
    request_path.write_text(json.dumps(json_ready(config), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "request_path": str(request_path)}, indent=2, sort_keys=True))
        return 0

    started = time.time()
    result = run_oracle_ceiling_diagnostics(
        output_dir=output_dir,
        eval_samples=int(config["eval_samples"]),
        initial_side=int(config["initial_side"]),
        target_side=int(config["target_side"]),
        loading_probability=float(config["loading_probability"]),
        k_neighbors=int(config["k_neighbors"]),
        seed=int(config["seed"]),
        graph_backend=str(config["graph_backend"]),
        target_lattice_spacing=config.get("target_lattice_spacing"),
        stream_samples=bool(config["stream_samples"]),
        prefetch_workers=int(config["prefetch_workers"]),
        prefetch_buffer=int(config["prefetch_buffer"]),
        progress_every_samples=int(config["progress_every_samples"]),
        dataset_manifest_path=config.get("dataset_manifest_path"),
    )
    result["runtime"] = {"wall_time_seconds": time.time() - started}
    result_path = output_dir / "oracle_ceiling.json"
    result_path.write_text(json.dumps(json_ready(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "output_dir": str(output_dir), "summary": result["summary"]}, indent=2))
    return 0


def run_oracle_ceiling_diagnostics(
    *,
    output_dir: Path,
    eval_samples: int,
    initial_side: int,
    target_side: int,
    loading_probability: float,
    k_neighbors: int,
    seed: int,
    graph_backend: str,
    target_lattice_spacing: float | None,
    stream_samples: bool,
    prefetch_workers: int,
    prefetch_buffer: int,
    progress_every_samples: int,
    dataset_manifest_path: Path | str | None = None,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "oracle_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    if dataset_manifest_path is not None:
        samples_iter = iter_dataset_manifest_samples(Path(dataset_manifest_path))
    else:
        samples_iter = iter_eval_samples(
            eval_samples=eval_samples,
            initial_side=initial_side,
            target_side=target_side,
            loading_probability=loading_probability,
            k_neighbors=k_neighbors,
            seed=seed + 1000,
            graph_backend=graph_backend,
            target_lattice_spacing=target_lattice_spacing,
            stream_samples=stream_samples,
            prefetch_workers=prefetch_workers,
            prefetch_buffer=prefetch_buffer,
        )

    rows: list[dict[str, object]] = []
    score_hungarian_rows: list[dict[str, float]] = []
    modified_auction_rows: list[dict[str, float]] = []
    started = time.monotonic()
    for idx, sample in enumerate(limit_samples(samples_iter, eval_samples), start=1):
        sample_started = time.monotonic()
        scores = sample.edge_labels.astype(float)
        row = diagnose_assignment_sample(sample, scores)
        audit = oracle_decoder_audit(sample)
        rows.append(row)
        score_hungarian_rows.append(audit["decoders"]["score_hungarian"])  # type: ignore[index]
        modified_auction_rows.append(audit["decoders"]["modified_auction"])  # type: ignore[index]
        if progress_every_samples > 0 and (idx % progress_every_samples == 0 or idx == eval_samples):
            write_progress(
                progress_path,
                {
                    "event": "sample",
                    "sample_index": idx,
                    "eval_samples": eval_samples,
                    "score_hungarian_average_gap": score_hungarian_rows[-1]["average_distance_gap"],
                    "modified_auction_average_gap": modified_auction_rows[-1]["average_distance_gap"],
                    "elapsed_seconds": time.monotonic() - started,
                    "sample_seconds": time.monotonic() - sample_started,
                },
            )

    write_progress(progress_path, {"event": "completed", "eval_samples": len(rows), "elapsed_seconds": time.monotonic() - started})
    rows_path = output_dir / "oracle_rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    return {
        "status": "completed",
        "paper_id": "2604.08669",
        "config": {
            "dataset_manifest_path": str(dataset_manifest_path) if dataset_manifest_path else None,
            "eval_samples": eval_samples,
            "initial_side": initial_side,
            "target_side": target_side,
            "loading_probability": loading_probability,
            "k_neighbors": k_neighbors,
            "seed": seed,
            "graph_backend": graph_backend,
            "stream_samples": stream_samples,
            "prefetch_workers": prefetch_workers,
            "prefetch_buffer": prefetch_buffer,
        },
        "summary": {
            "oracle_scores": summarize_assignment_diagnostics(rows),
            "score_hungarian_decoder": summarize_eval_rows(score_hungarian_rows),
            "modified_auction_decoder": summarize_eval_rows(modified_auction_rows),
        },
        "artifacts": {
            "progress_path": str(progress_path),
            "rows_path": str(rows_path),
        },
    }


def limit_samples(samples: Iterable[GraphSample], limit: int) -> Iterable[GraphSample]:
    for idx, sample in enumerate(samples):
        if idx >= limit:
            break
        yield sample


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
