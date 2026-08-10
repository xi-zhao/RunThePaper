#!/usr/bin/env python3
"""Write per-panel acceptance and protocol-v2 evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from qdrift_resources.panel_audit import audit_panel_targets  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=WORKSPACE / "config" / "panel_acceptance.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=WORKSPACE / "outputs" / "checks" / "panel_target_acceptance.json",
    )
    arguments = parser.parse_args()

    payload = audit_panel_targets(WORKSPACE, arguments.config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(arguments.output)
    if payload["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
