#!/usr/bin/env python3
"""Guarded target-local audit of the paper's lambda construction."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))

from src.local_norms import model_lambda  # noqa: E402
from src.trotter_bounds import TARGET_SPECS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(TARGET_SPECS))
    args = parser.parse_args()
    if os.environ.get("PRAGENT_GUARDED_TARGET_ID") != args.target:
        raise RuntimeError("lambda audit target does not match the guarded target")
    spec = TARGET_SPECS[args.target]
    value, terms = model_lambda(spec.model)
    precision = 3 if spec.model == "xx_spin_chain" else 2
    matches_reported = round(value, precision) == round(spec.lam, precision)
    is_conservative = spec.lam + 1e-12 >= value
    output = WORKSPACE / "outputs" / "checks" / f"{spec.model}_lambda_method.json"
    payload = {
        "schema_version": 1,
        "status": "passed" if is_conservative else "failed",
        "target_id": args.target,
        "model": spec.model,
        "method": "independent_local_choi_bound",
        "paper_reported_lambda": spec.lam,
        "computed_lambda_full_precision": value,
        "reported_precision_digits": precision,
        "rounded_value_matches_paper": matches_reported,
        "paper_lambda_is_conservative": is_conservative,
        "terms": terms,
        "source_pixels_used": False,
        "author_modules_imported": False,
        "finding": (
            None
            if matches_reported
            else {
                "severity": "warning",
                "code": "paper_lambda_uses_looser_bound",
                "message": "The paper-reported lambda is larger than the independently evaluated local Choi bound; it remains a conservative input to the published resource-bound figure."
            }
        ),
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if is_conservative else 1


if __name__ == "__main__":
    raise SystemExit(main())
