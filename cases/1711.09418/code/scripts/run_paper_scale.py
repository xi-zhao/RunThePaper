#!/usr/bin/env python3
"""CLI for the checkpointed paper-scale Fig. 2/Fig. 3 calculation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from symmetry_entanglement.paper_scale import (  # noqa: E402
    acceptance_report,
    aggregate_analytic,
    aggregate_spectrum,
    backend_benchmark,
    effective_config,
    load_config,
    prepare_eigenvalues,
    run_all,
    run_analytic_shard,
    run_fig2,
    run_spectrum_shard,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Paper-scale, resumable reproduction of arXiv:1711.09418 Figs. 2 and 3"
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--profile", choices=("paper", "smoke"), default="paper")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--resume", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-config", help="load and validate the JSON contract")
    subparsers.add_parser(
        "prepare", help="compute/checkpoint the shared correlation spectrum"
    )
    subparsers.add_parser("fig2", help="run the checkpointed T001 charge recurrence")

    numeric = subparsers.add_parser(
        "fig3-shard", help="run one exact many-body state shard"
    )
    numeric.add_argument("--shard-index", required=True, type=int)
    numeric.add_argument("--num-shards", required=True, type=int)

    analytic = subparsers.add_parser(
        "analytic-shard", help="run one Eq. (11) x-grid shard"
    )
    analytic.add_argument("--shard-index", required=True, type=int)
    analytic.add_argument("--num-shards", required=True, type=int)

    aggregate = subparsers.add_parser(
        "aggregate", help="merge all configured T002 shards"
    )
    aggregate.add_argument("--spectrum-shards", type=int)
    aggregate.add_argument("--analytic-shards", type=int)

    subparsers.add_parser(
        "benchmark", help="run independent backend and streaming parity checks"
    )
    subparsers.add_parser(
        "accept", help="evaluate per-target acceptance after aggregation"
    )
    subparsers.add_parser(
        "run-all", help="run every configured shard, aggregate, benchmark, and accept"
    )
    return parser


def _resolve_from_workspace(path: Path) -> Path:
    return path if path.is_absolute() else WORKSPACE / path


def main() -> None:
    args = build_parser().parse_args()
    config_path = _resolve_from_workspace(args.config)
    base_config = load_config(config_path)
    config = effective_config(base_config, args.profile)
    output_root = (
        _resolve_from_workspace(args.output_root)
        if args.output_root is not None
        else _resolve_from_workspace(Path(config["execution"]["output_root"]))
    )
    os.chdir(WORKSPACE)

    if args.command == "validate-config":
        result = {
            "status": "passed",
            "paper_id": config["paper_id"],
            "profile": config["active_profile"],
            "output_root": str(output_root.relative_to(WORKSPACE)),
            "target_ids": sorted(config["targets"]),
        }
    elif args.command == "prepare":
        eigenvalues, stage = prepare_eigenvalues(
            config, output_root, resume=args.resume
        )
        result = {**stage, "active_modes": int(eigenvalues.size)}
    elif args.command == "fig2":
        eigenvalues, _ = prepare_eigenvalues(config, output_root, resume=True)
        result = run_fig2(config, output_root, eigenvalues, resume=args.resume)
    elif args.command == "fig3-shard":
        eigenvalues, _ = prepare_eigenvalues(config, output_root, resume=True)
        result = run_spectrum_shard(
            config,
            output_root,
            eigenvalues,
            shard_index=args.shard_index,
            num_shards=args.num_shards,
            resume=args.resume,
        )
    elif args.command == "analytic-shard":
        result = run_analytic_shard(
            config,
            output_root,
            shard_index=args.shard_index,
            num_shards=args.num_shards,
            resume=args.resume,
        )
    elif args.command == "aggregate":
        spectrum_shards = args.spectrum_shards or int(
            config["execution"]["spectrum_shards"]
        )
        analytic_shards = args.analytic_shards or int(
            config["execution"]["analytic_shards"]
        )
        eigenvalues, _ = prepare_eigenvalues(config, output_root, resume=True)
        result = {
            "numeric": aggregate_spectrum(
                config, output_root, eigenvalues, num_shards=spectrum_shards
            ),
            "analytic": aggregate_analytic(
                config, output_root, num_shards=analytic_shards
            ),
        }
    elif args.command == "benchmark":
        result = backend_benchmark(config, output_root)
    elif args.command == "accept":
        eigenvalues, _ = prepare_eigenvalues(config, output_root, resume=True)
        result = acceptance_report(
            config,
            output_root,
            eigenvalues,
            spectrum_shards=int(config["execution"]["spectrum_shards"]),
        )
    else:
        result = run_all(config, output_root, resume=args.resume)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
