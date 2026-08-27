#!/usr/bin/env python3
"""Execute one blocked target from a complete reviewed benchmark contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from missing_benchmark_campaign import HANDLERS  # noqa: E402
from missing_benchmark_models import ScientificInputError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(HANDLERS))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        package = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(package, dict):
            raise ScientificInputError("input package must be a JSON object")
        if package.get("target_id") != args.target:
            raise ScientificInputError("input package target_id does not match --target")
        result = HANDLERS[args.target](package)
    except (OSError, json.JSONDecodeError, ScientificInputError, ValueError) as exc:
        print(f"scientific input rejected: {exc}", file=sys.stderr)
        return 2
    payload = {
        "schema_version": 1,
        "target_id": args.target,
        "scientific_input_mode": "explicit_external_package",
        "result": result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
