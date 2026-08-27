#!/usr/bin/env python3
"""Execute a blocked target once its explicit scientific input package exists."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from external_input_models import (  # noqa: E402
    ScientificInputError,
    css_monte_carlo,
    css_monte_carlo_campaign,
    dynamic_polarizability,
    dynamic_polarizability_sweep,
    toggled_hamiltonian_evolution,
)


TARGET_MODELS = {
    "T018": dynamic_polarizability,
    "T020": css_monte_carlo,
    "T021": css_monte_carlo,
    "T022": css_monte_carlo,
    "T023": css_monte_carlo,
    "T024": css_monte_carlo,
    "T027": toggled_hamiltonian_evolution,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(TARGET_MODELS))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        package = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(package, dict):
            raise ScientificInputError("input package must be a JSON object")
        declared_target = str(package.get("target_id") or "")
        if declared_target != args.target:
            raise ScientificInputError(
                f"input package target_id {declared_target!r} does not match {args.target}"
            )
        if args.target == "T018" and "states" in package:
            result = dynamic_polarizability_sweep(package)
        elif args.target in {"T020", "T021", "T022", "T023", "T024"} and "experiments" in package:
            result = css_monte_carlo_campaign(package)
        else:
            result = TARGET_MODELS[args.target](package)
    except (OSError, json.JSONDecodeError, ScientificInputError) as exc:
        print(f"scientific input rejected: {exc}", file=sys.stderr)
        return 2

    payload = {
        "schema_version": 1,
        "status": "passed",
        "target_id": args.target,
        "scientific_input_mode": "explicit_external_package",
        "result": result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
