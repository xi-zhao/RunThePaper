#!/usr/bin/env python3
"""Plan, execute, resume, and aggregate the complete paper-scale campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
SOURCE = WORKSPACE / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from dtc_paper_scale import (  # noqa: E402
    aggregate_units,
    build_work_units,
    load_config,
    run_units,
    validate_config,
)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument(
        "--config",
        type=Path,
        default=Path("config/paper_scale_all.json"),
        help="Path relative to workspace unless absolute.",
    )
    subcommands = command.add_subparsers(dest="action", required=True)

    validate = subcommands.add_parser(
        "validate", help="Validate config and enumerate both profiles."
    )
    validate.set_defaults(action="validate")

    plan = subcommands.add_parser(
        "plan", help="Print deterministic work-unit metadata."
    )
    _add_profile(plan)

    run = subcommands.add_parser(
        "run", help="Execute all or a deterministic subset of work units."
    )
    _add_profile(run)
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--unit-index", type=int)
    run.add_argument("--shard-index", type=int)
    run.add_argument("--shard-count", type=int)
    run.add_argument("--resume", action="store_true")

    aggregate = subcommands.add_parser(
        "aggregate", help="Fail closed unless every expected shard is valid."
    )
    _add_profile(aggregate)
    _add_rendering_boundary(aggregate)

    run_all = subcommands.add_parser(
        "run-all", help="Execute a complete profile and aggregate it."
    )
    _add_profile(run_all)
    _add_rendering_boundary(run_all)
    run_all.add_argument("--workers", type=int, default=1)
    run_all.add_argument("--resume", action="store_true")
    return command


def _add_profile(command: argparse.ArgumentParser) -> None:
    command.add_argument("--profile", choices=("paper", "smoke"), default="paper")


def _add_rendering_boundary(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--skip-render",
        action="store_true",
        help="Freeze numerical data and checks without importing a renderer.",
    )


def resolve_config(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (WORKSPACE / path).resolve()


def main() -> int:
    args = parser().parse_args()
    config_path = resolve_config(args.config)
    if args.action == "validate":
        payload = validate_config(load_config(config_path))
    elif args.action == "plan":
        units = build_work_units(load_config(config_path), args.profile)
        payload = {
            "schema_version": 1,
            "status": "passed",
            "profile": args.profile,
            "work_units": len(units),
            "sample_realizations": sum(unit.sample_count for unit in units),
            "families": sorted({unit.family for unit in units}),
            "first_unit": units[0].as_dict(),
            "last_unit": units[-1].as_dict(),
        }
    elif args.action == "run":
        payload = run_units(
            WORKSPACE,
            config_path,
            profile=args.profile,
            workers=args.workers,
            unit_index=args.unit_index,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
            resume=args.resume,
        )
    elif args.action == "aggregate":
        payload = aggregate_units(
            WORKSPACE,
            config_path,
            profile=args.profile,
            render=not args.skip_render,
        )
    else:
        run_payload = run_units(
            WORKSPACE,
            config_path,
            profile=args.profile,
            workers=args.workers,
            resume=args.resume,
        )
        aggregate_payload = aggregate_units(
            WORKSPACE,
            config_path,
            profile=args.profile,
            render=not args.skip_render,
        )
        payload = {
            "schema_version": 1,
            "status": aggregate_payload["status"],
            "run": run_payload,
            "aggregate": aggregate_payload,
        }
        if args.profile == "smoke":
            evidence_path = (
                WORKSPACE
                / "outputs"
                / "checks"
                / "paper_scale_smoke"
                / "attested_evidence.json"
            )
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = evidence_path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            temporary.replace(evidence_path)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
