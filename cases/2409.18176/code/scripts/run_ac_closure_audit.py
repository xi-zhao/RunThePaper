#!/usr/bin/env python3
"""Run the source-free AC density-closure adjudication."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.bose_fermi_transport.ac_adjudication import audit_ac_closures  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    result = audit_ac_closures(config["parameters"])
    output = WORKSPACE / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
