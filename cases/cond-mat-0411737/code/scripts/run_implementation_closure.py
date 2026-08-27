#!/usr/bin/env python3
"""Run the fixed-denominator implementation-closure campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from implementation_closure import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output_root = args.output_root if args.output_root.is_absolute() else WORKSPACE / args.output_root
    config = json.loads(config_path.read_text(encoding="utf-8"))
    results = run_campaign(config)
    output_root.mkdir(parents=True, exist_ok=True)
    for target_id, result in results.items():
        (output_root / f"{target_id}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    failed = sorted(target_id for target_id, row in results.items() if not row["checks_passed"])
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "profile": config["profile"],
        "scientific_promotion": False,
        "targets_total": len(results),
        "items_total": sum(len(row["item_ids"]) for row in results.values()),
        "computed_targets": sorted(target_id for target_id, row in results.items() if row["status"] == "passed"),
        "blocked_on_paper_input": sorted(target_id for target_id, row in results.items() if row["status"] == "blocked_on_paper_input"),
        "failed_targets": failed,
        "clean_room_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "source_or_reference_pixels_read": False,
            "legacy_generated_outputs_read": False
        }
    }
    (output_root / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
