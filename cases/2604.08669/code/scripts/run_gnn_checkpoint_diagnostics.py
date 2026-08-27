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
    dataset_sample_paths,
    diagnose_assignment_sample,
    iter_eval_samples,
    load_graph_sample_npz,
    load_edge_scoring_model,
    predict_edge_scores,
    summarize_assignment_diagnostics,
)


def diagnostic_profiles() -> dict[str, dict[str, Any]]:
    return {
        "paper_target": {
            "initial_side": 127,
            "target_side": 101,
            "target_lattice_spacing": (127 - 1) / (101 - 1),
            "k_neighbors": 128,
            "eval_samples": 256,
            "loading_probability": 0.75,
            "device": "cuda",
            "graph_backend": "kdtree",
            "stream_samples": True,
            "prefetch_workers": 8,
            "prefetch_buffer": 16,
            "progress_every_samples": 1,
            "seed": 260408690,
        },
        "canary": {
            "initial_side": 9,
            "target_side": 5,
            "k_neighbors": 16,
            "eval_samples": 2,
            "loading_probability": 0.75,
            "device": "cpu",
            "graph_backend": "kdtree",
            "stream_samples": False,
            "prefetch_workers": 0,
            "prefetch_buffer": 0,
            "progress_every_samples": 1,
            "seed": 260408690,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose a trained 2604.08669 edge-scoring checkpoint.")
    parser.add_argument("--profile", choices=sorted(diagnostic_profiles()), default="paper_target")
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dataset-manifest-path", type=Path)
    parser.add_argument("--eval-samples", type=int)
    parser.add_argument("--target-lattice-spacing", type=float)
    parser.add_argument("--device")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--prefetch-workers", type=int)
    parser.add_argument("--prefetch-buffer", type=int)
    parser.add_argument("--progress-every-samples", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = dict(diagnostic_profiles()[args.profile])
    for key in [
        "dataset_manifest_path",
        "eval_samples",
        "target_lattice_spacing",
        "device",
        "seed",
        "prefetch_workers",
        "prefetch_buffer",
        "progress_every_samples",
    ]:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    config["profile"] = args.profile
    config["checkpoint_path"] = args.checkpoint_path
    config["platform"] = platform_payload()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    run_request_path = output_dir / "diagnostics_request.json"
    run_request_path.write_text(json.dumps(json_ready(config), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "run_request": str(run_request_path)}, indent=2))
        return 0

    started = time.time()
    diagnostics = run_checkpoint_diagnostics(
        checkpoint_path=Path(config["checkpoint_path"]),
        output_dir=output_dir,
        dataset_manifest_path=config.get("dataset_manifest_path"),
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
        device=str(config["device"]),
    )
    diagnostics["runtime"] = {"wall_time_seconds": time.time() - started}
    diagnostics_path = output_dir / "diagnostics.json"
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "completed",
                "output_dir": str(output_dir),
                "summary": diagnostics["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def run_checkpoint_diagnostics(
    *,
    checkpoint_path: Path,
    output_dir: Path,
    dataset_manifest_path: Path | None = None,
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
    device: str,
) -> dict[str, object]:
    if eval_samples <= 0:
        raise ValueError("eval_samples must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "diagnostics_progress.jsonl"
    progress_path.write_text("", encoding="utf-8")

    model = load_edge_scoring_model(checkpoint_path, device=device)
    rows: list[dict[str, object]] = []
    if dataset_manifest_path is not None:
        eval_paths = dataset_sample_paths(dataset_manifest_path)
        if not eval_paths:
            raise ValueError("dataset manifest does not contain samples")
        eval_iter = (load_graph_sample_npz(eval_paths[idx % len(eval_paths)]) for idx in range(eval_samples))
    else:
        eval_iter = iter_eval_samples(
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
    started = time.monotonic()
    for idx, sample in enumerate(eval_iter, start=1):
        sample_started = time.monotonic()
        scores = predict_edge_scores(model, sample)
        row = diagnose_assignment_sample(sample, scores)
        row["sample_index"] = idx
        rows.append(row)
        if progress_every_samples > 0 and (idx % progress_every_samples == 0 or idx == eval_samples):
            write_progress(
                progress_path,
                {
                    "event": "sample",
                    "sample_index": idx,
                    "eval_samples": eval_samples,
                    "average_distance_gap": row["assignment"]["average_distance_gap"],  # type: ignore[index]
                    "rank1_rate": row["source_rank"]["rank1_rate"],  # type: ignore[index]
                    "elapsed_seconds": time.monotonic() - started,
                    "sample_seconds": time.monotonic() - sample_started,
                },
            )

    summary = summarize_assignment_diagnostics(rows)
    write_progress(
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
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "status": "completed",
        "paper_id": "2604.08669",
        "checkpoint_path": str(checkpoint_path),
        "config": {
            "dataset_manifest_path": str(dataset_manifest_path) if dataset_manifest_path else None,
            "eval_samples": eval_samples,
            "initial_side": initial_side,
            "target_side": target_side,
            "loading_probability": loading_probability,
            "k_neighbors": k_neighbors,
            "seed": seed,
            "graph_backend": graph_backend,
            "target_lattice_spacing": target_lattice_spacing,
            "stream_samples": stream_samples,
            "prefetch_workers": prefetch_workers,
            "prefetch_buffer": prefetch_buffer,
            "device": device,
        },
        "summary": summary,
        "artifacts": {
            "diagnostic_rows_path": str(rows_path),
            "progress_path": str(progress_path),
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
