from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scar_tdvp.paper_scale import load_config, run_campaign, work_units  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run checkpointed paper-scale main-figure campaigns"
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--list-units", action="store_true")
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--shard-count", type=int)
    parser.add_argument("--unit-id", action="append")
    parser.add_argument("--stop-after-checkpoints", type=int)
    arguments = parser.parse_args()

    config, digest = load_config(Path(arguments.config), smoke=arguments.smoke)
    if arguments.validate_only:
        print(
            json.dumps(
                {
                    "status": "passed",
                    "paper_id": config["paper_id"],
                    "scope": config["scope"],
                    "config_digest": digest,
                    "work_units": len(work_units(config)),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.list_units:
        print(json.dumps(list(work_units(config)), indent=2, sort_keys=True))
        return 0

    result = run_campaign(
        config,
        WORKSPACE,
        digest=digest,
        resume=arguments.resume,
        aggregate=arguments.aggregate or arguments.aggregate_only,
        aggregate_only=arguments.aggregate_only,
        shard_index=arguments.shard_index,
        shard_count=arguments.shard_count,
        unit_ids=arguments.unit_id,
        stop_after_checkpoints=arguments.stop_after_checkpoints,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"passed", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
