#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WS / "scripts"))

import gen_fig2  # noqa: E402
import run_ed_validation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the paper-exact reproduction bundle for T1/T2.")
    parser.add_argument(
        "--config",
        type=Path,
        default=WS / "config" / "paper_exact.json",
        help="Paper-exact configuration used for the attested scientific run.",
    )
    return parser.parse_args()


def validate_config(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("config.parameters must be an object")
    for key in ["fig2", "ed_validation"]:
        if not isinstance(parameters.get(key), dict):
            raise ValueError(f"config.parameters.{key} must be an object")
    return payload


def main() -> int:
    args = parse_args()
    validate_config(args.config)
    original_argv = sys.argv[:]
    try:
        sys.argv = ["gen_fig2.py", "--config", str(args.config), "--skip-figure"]
        code1 = gen_fig2.main()
        sys.argv = ["run_ed_validation.py", "--config", str(args.config)]
        code2 = run_ed_validation.main()
    finally:
        sys.argv = original_argv
    return 0 if code1 == 0 and code2 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
