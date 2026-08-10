#!/usr/bin/env python3
"""Run or resume the sharded T001-T031 paper-scale campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from backends import run_backend_benchmark  # noqa: E402
from paper_scale import FAMILY_ORDER, load_campaign  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("validate-config", "plan", "run-shard", "run-family", "run-all"),
    )
    parser.add_argument("--config", type=Path, default=Path("config/paper_scale.json"))
    parser.add_argument(
        "--acceptance",
        type=Path,
        default=Path("config/paper_scale_acceptance.json"),
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--backend", choices=("auto", "numpy", "cupy"))
    parser.add_argument("--family", choices=FAMILY_ORDER)
    parser.add_argument("--condition")
    parser.add_argument("--shard", type=int)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    return parser


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else WORKSPACE / path


def main() -> None:
    args = _parser().parse_args()
    config_path = _resolve(args.config)
    output_root = _resolve(args.output_root) if args.output_root else None
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    benchmark = None
    selected_backend = args.backend
    if args.action == "run-all":
        benchmark = run_backend_benchmark(
            config_payload["backend_benchmark"], smoke=args.smoke
        )
        if benchmark["status"] != "passed":
            raise SystemExit(
                "backend parity benchmark failed; campaign was not started"
            )
        if selected_backend == "auto":
            selected_backend = benchmark["selected_backend"]
        if selected_backend is not None:
            matching = [
                row
                for row in benchmark["results"]
                if row["backend"] == selected_backend
            ]
            if not matching or not all(row.get("passed") for row in matching):
                raise SystemExit(
                    f"requested backend {selected_backend} did not pass every parity probe"
                )
    campaign = load_campaign(
        config_path,
        output_root=output_root,
        smoke=args.smoke,
        backend=selected_backend,
    )
    if args.action == "validate-config":
        result = {
            "status": "passed",
            "mode": campaign.mode,
            "config_sha256": campaign.config_hash,
            "conditions": len(campaign.conditions),
            "target_count": len(campaign.config["target_map"]),
        }
    elif args.action == "plan":
        result = campaign.plan()
    elif args.action == "run-shard":
        if args.family is None or args.condition is None or args.shard is None:
            raise SystemExit("run-shard requires --family, --condition, and --shard")
        result = campaign.run_shard(
            args.family,
            args.condition,
            args.shard,
            resume=not args.no_resume,
        )
    elif args.action == "run-family":
        if args.family is None:
            raise SystemExit("run-family requires --family")
        result = {
            "run": campaign.run_family(args.family, resume=not args.no_resume),
            "aggregate": campaign.aggregate_family(args.family),
        }
    else:
        assert benchmark is not None
        benchmark_path = campaign.output_root / "checks" / "backend_benchmark.json"
        benchmark_path.parent.mkdir(parents=True, exist_ok=True)
        benchmark_path.write_text(
            json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        run = campaign.run_all(resume=not args.no_resume)
        aggregate = campaign.aggregate_all()
        acceptance = campaign.accept(_resolve(args.acceptance))
        result = {
            "status": acceptance["status"],
            "mode": campaign.mode,
            "backend_benchmark": benchmark,
            "run": run,
            "aggregate": aggregate,
            "acceptance": acceptance,
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
