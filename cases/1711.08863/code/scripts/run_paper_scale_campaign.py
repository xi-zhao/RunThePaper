#!/usr/bin/env python3
"""CLI adapter for the checkpointed Main-Figure-2 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from giant_atoms.campaign import (  # noqa: E402
    CampaignError,
    load_campaign_config,
    run_campaign,
)


def _config_path(value: Path) -> Path:
    return value if value.is_absolute() else WORKSPACE / value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run or resume the paper-scale analytic campaign for Main Fig. 2."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=WORKSPACE,
        help="Output root; defaults to the case workspace (tests may override it).",
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--shard-index",
        type=int,
        help="Run exactly one zero-based shard, suitable for a scheduler array job.",
    )
    selection.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Validate existing checkpoints and aggregate only when every shard exists.",
    )
    parser.add_argument(
        "--max-new-shards",
        type=int,
        help="Compute at most this many new shards, then leave a resumable partial state.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate and summarize the config without creating outputs.",
    )
    arguments = parser.parse_args()

    try:
        config = load_campaign_config(_config_path(arguments.config))
        if arguments.validate_only:
            print(
                json.dumps(
                    {
                        "status": "valid",
                        "run_id": config.run_id,
                        "target_ids": list(config.target_ids),
                        "parameters": config.parameters,
                        "shard_count": config.shard_count,
                        "config_sha256": config.sha256,
                    },
                    indent=2,
                )
            )
            return
        state = run_campaign(
            config,
            arguments.workspace_root,
            shard_index=arguments.shard_index,
            max_new_shards=arguments.max_new_shards,
            aggregate_only=arguments.aggregate_only,
        )
    except CampaignError as exc:
        parser.error(str(exc))
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
