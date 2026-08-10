#!/usr/bin/env python3
"""Validate or execute the isolated paper-scale theory campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from tbg_topology.paper_scale import (  # noqa: E402
    PaperScaleConfigError,
    execute_campaign,
    validate_config,
)


def _config_path(value: str) -> Path:
    candidate = Path(value)
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (WORKSPACE / candidate).resolve()
    )
    try:
        resolved.relative_to(WORKSPACE.resolve())
    except ValueError as error:
        raise PaperScaleConfigError(
            "config must remain inside the case workspace"
        ) from error
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    try:
        config = json.loads(_config_path(arguments.config).read_text(encoding="utf-8"))
        result = (
            validate_config(config)
            if arguments.validate_only
            else execute_campaign(config, WORKSPACE, resume=arguments.resume)
        )
    except (
        json.JSONDecodeError,
        OSError,
        PaperScaleConfigError,
        RuntimeError,
    ) as error:
        print(
            json.dumps({"status": "failed", "error": str(error)}, indent=2),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return (
        0
        if result.get("status")
        in {
            "ready",
            "paper_scale_complete_reconstructed",
        }
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
