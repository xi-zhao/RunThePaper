#!/usr/bin/env python3
"""Execute the 16-item analytic claim falsification suite."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_workspace = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_workspace))

from src.claim_audit import run_claim_audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    payload = run_claim_audit(config)
    output = Path(config["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload["items_total"] == 16 else 2


if __name__ == "__main__":
    raise SystemExit(main())
