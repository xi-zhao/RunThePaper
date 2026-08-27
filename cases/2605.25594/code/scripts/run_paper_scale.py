#!/usr/bin/env python3
"""Plan, execute, resume, and aggregate all Anderson-model figure numerics.

The scientific runner is raw/reference-free by construction.  It reads only
the frozen case-local configuration and implementation modules.  The original
PDF/TeX and source figures are allowed only in later review/rendering stages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from paper_scale_campaign import (  # noqa: E402
    aggregate_target_index,
    anderson_hamiltonian_sparse,
    build_work_units,
    canonical_digest,
    describe_campaign,
    run_unit_numerics,
    work_unit_seed,
)

DEFAULT_CONFIG = WORKSPACE / "config" / "paper_scale.json"


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else WORKSPACE / path


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def implementation_digest() -> str:
    digest = hashlib.sha256()
    for path in [
        WORKSPACE / "src" / "anderson_sensitivity.py",
        WORKSPACE / "src" / "paper_scale_campaign.py",
        Path(__file__),
    ]:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def diagonalize(matrix: np.ndarray, backend: str) -> tuple[np.ndarray, np.ndarray, str]:
    if backend in {"auto", "torch_cuda"}:
        try:
            import torch

            if torch.cuda.is_available():
                try:
                    device_matrix = torch.from_numpy(matrix).to("cuda", torch.float64)
                    values, vectors = torch.linalg.eigh(device_matrix)
                    return (
                        values.cpu().numpy(),
                        vectors.cpu().numpy(),
                        "torch_cuda_float64",
                    )
                except RuntimeError:
                    if backend == "torch_cuda":
                        raise
                    # The known cuSOLVER workspace limit near L=32 must not
                    # corrupt a checkpoint.  Auto mode retries on the declared
                    # high-memory CPU/LAPACK path.
                    try:
                        del device_matrix
                    except UnboundLocalError:
                        pass
                    torch.cuda.empty_cache()
            if backend == "torch_cuda":
                raise RuntimeError("torch_cuda requested but CUDA is unavailable")
        except ImportError:
            if backend == "torch_cuda":
                raise
    values, vectors = np.linalg.eigh(matrix)
    return values, vectors, "numpy_lapack_float64"


def load_checkpoint(
    path: Path, config_sha256: str, implementation_sha256: str
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("config_sha256") != config_sha256:
        raise RuntimeError(f"checkpoint config hash mismatch: {path}")
    if payload.get("implementation_sha256") != implementation_sha256:
        raise RuntimeError(f"checkpoint implementation hash mismatch: {path}")
    return payload


def run_shard(
    config: dict[str, Any],
    *,
    worker_index: int,
    worker_count: int,
    max_units: int | None,
) -> int:
    if worker_count <= 0 or not 0 <= worker_index < worker_count:
        raise ValueError("worker_index must be in [0, worker_count)")
    config_sha256 = canonical_digest(config)
    implementation_sha256 = implementation_digest()
    root = resolve(str(config["checkpoint_root"]))
    selected = [
        unit
        for unit in build_work_units(config)
        if unit.index % worker_count == worker_index
    ]
    if max_units is not None:
        selected = selected[:max_units]
    completed = 0
    for unit in selected:
        output = root / f"{unit.key}.json"
        if load_checkpoint(output, config_sha256, implementation_sha256) is not None:
            continue
        started = time.time()
        seed = work_unit_seed(int(config["seed_base"]), unit)
        rng = np.random.default_rng(seed)
        hamiltonian = anderson_hamiltonian_sparse(
            unit.L,
            unit.W,
            rng,
            boundary_disorder=unit.boundary_disorder,
            boundary_disorder_halfwidth=float(config["boundary_disorder_halfwidth"]),
        )
        eigenvalues, eigenvectors, backend = diagonalize(
            hamiltonian.toarray(), str(config["diagonalization_backend"])
        )
        numerics = run_unit_numerics(unit, config, eigenvalues, eigenvectors)
        atomic_json(
            output,
            {
                "schema_version": 1,
                "paper_id": config["paper_id"],
                "work_unit_key": unit.key,
                "work_unit_index": unit.index,
                "family": unit.family,
                "target_ids": list(unit.target_ids),
                "parameters": {
                    "L": unit.L,
                    "W": unit.W,
                    "sample": unit.sample,
                    "operators": list(unit.operators),
                    "boundary_disorder": unit.boundary_disorder,
                    "seed": seed,
                },
                "backend": backend,
                "config_sha256": config_sha256,
                "implementation_sha256": implementation_sha256,
                "generated_data_provenance": "independent_numerics",
                "numerical_input_boundary": config["numerical_input_boundary"],
                "elapsed_seconds": time.time() - started,
                "numerics": numerics,
            },
        )
        completed += 1
    return completed


def aggregate(config: dict[str, Any]) -> int:
    config_sha256 = canonical_digest(config)
    implementation_sha256 = implementation_digest()
    root = resolve(str(config["checkpoint_root"]))
    records: list[dict[str, Any]] = []
    for unit in build_work_units(config):
        checkpoint = load_checkpoint(
            root / f"{unit.key}.json", config_sha256, implementation_sha256
        )
        if checkpoint is not None:
            records.append(checkpoint)
    index = aggregate_target_index(records, config)
    index.update(
        {
            "schema_version": 1,
            "paper_id": config["paper_id"],
            "config_sha256": config_sha256,
            "implementation_sha256": implementation_sha256,
            "generated_data_provenance": "independent_numerics",
            "numerical_input_boundary": config["numerical_input_boundary"],
            "acceptance_criteria": config["acceptance"],
        }
    )
    atomic_json(resolve(str(config["target_index_output"])), index)
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": index["status"],
        "checkpoint_count": len(records),
        "checkpoint_sha256": {
            row["work_unit_key"]: canonical_digest(row) for row in records
        },
        "target_index": config["target_index_output"],
    }
    atomic_json(resolve(str(config["manifest_output"])), manifest)
    return 0 if index["status"] == "passed" and index["all_targets_have_data"] else 3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plan")
    run_parser = subparsers.add_parser("run-shard")
    run_parser.add_argument("--worker-index", type=int, required=True)
    run_parser.add_argument("--worker-count", type=int, required=True)
    run_parser.add_argument("--max-units", type=int)
    subparsers.add_parser("aggregate")
    subparsers.add_parser("run-all")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.command == "plan":
        print(json.dumps(describe_campaign(config), indent=2))
        return 0
    if args.command == "run-shard":
        completed = run_shard(
            config,
            worker_index=args.worker_index,
            worker_count=args.worker_count,
            max_units=args.max_units,
        )
        print(json.dumps({"new_work_units": completed}, indent=2))
        return 0
    if args.command == "run-all":
        run_shard(config, worker_index=0, worker_count=1, max_units=None)
    return aggregate(config)


if __name__ == "__main__":
    raise SystemExit(main())
