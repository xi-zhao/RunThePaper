from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.paper_scale_campaign import (  # noqa: E402 - bootstrap workspace package
    aggregate_campaign,
    load_campaign_config,
    make_smoke_payload,
    prepare_campaign,
    run_campaign,
    run_crosschecks,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Checkpointed paper-scale theory campaign for arXiv:1709.03478"
    )
    parser.add_argument(
        "--config", required=True, help="Workspace-relative paper-scale JSON deck"
    )
    parser.add_argument(
        "--action",
        choices=("prepare", "run", "finalize", "smoke"),
        default="prepare",
        help="prepare is the safe default; run performs configured numerical blocks",
    )
    parser.add_argument(
        "--profile",
        action="append",
        dest="profiles",
        help="Limit execution to one or more named profiles",
    )
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Bound newly executed blocks for controlled probes",
    )
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="After a complete unsharded run, execute cross-checks and aggregate",
    )
    parser.add_argument(
        "--output-root", default=None, help="Test-only/scratch output override"
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    workspace = Path.cwd()
    payload = load_campaign_config(Path(args.config))
    if args.output_root is not None:
        base = Path(args.output_root)
        payload["campaign"]["output_roots"] = {
            "state": str(base / "state"),
            "data": str(base / "data"),
            "figures": str(base / "figures"),
        }

    if args.action == "prepare":
        result = prepare_campaign(payload, workspace, args.profiles)
    elif args.action == "smoke":
        smoke = make_smoke_payload(payload, args.output_root)
        run_result = run_campaign(
            smoke, workspace, profile_names=args.profiles, resume=args.resume
        )
        crosschecks = run_crosschecks(smoke, workspace)
        aggregate = aggregate_campaign(smoke, workspace)
        result = {
            "status": "smoke_completed",
            "run": run_result,
            "crosschecks": crosschecks["status"],
            "assessment": aggregate,
        }
    elif args.action == "finalize":
        crosschecks = run_crosschecks(payload, workspace)
        aggregate = aggregate_campaign(payload, workspace)
        result = {
            "status": "finalized",
            "crosschecks": crosschecks["status"],
            "assessment": aggregate,
        }
    else:
        result = run_campaign(
            payload,
            workspace,
            profile_names=args.profiles,
            resume=args.resume,
            max_tasks=args.max_tasks,
            shard_index=args.shard_index,
            shard_count=args.shard_count,
        )
        if args.finalize:
            if args.shard_count != 1:
                raise SystemExit(
                    "--finalize requires --shard-count 1; finalize shared sharded runs separately"
                )
            crosschecks = run_crosschecks(payload, workspace)
            aggregate = aggregate_campaign(payload, workspace)
            result = {
                "run": result,
                "crosschecks": crosschecks["status"],
                "assessment": aggregate,
            }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
