#!/usr/bin/env python3
"""Emit strict implementation artifacts for T008 and T009."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


WORKSPACE = Path(__file__).resolve().parents[1]
SRC = WORKSPACE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from missing_benchmark_campaign import build_blocked_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else WORKSPACE / args.config
    output_root = args.output_root if args.output_root.is_absolute() else WORKSPACE / args.output_root
    results = build_blocked_artifacts(json.loads(config_path.read_text(encoding="utf-8")))
    output_root.mkdir(parents=True, exist_ok=True)
    for target_id, payload in results.items():
        (output_root / f"{target_id}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    summary = {
        "schema_version": 1,
        "paper_id": "10.1038-s41467-025-67768-4",
        "profile": "strict_missing_benchmark_boundary",
        "scientific_promotion": False,
        "targets_total": len(results),
        "items_total": sum(len(payload["item_ids"]) for payload in results.values()),
        "blocked_on_paper_input": sorted(results),
        "failed_targets": sorted(
            target_id
            for target_id, payload in results.items()
            if not all(payload["checks"].values())
        ),
        "clean_room_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "source_or_reference_pixels_read": False,
            "legacy_generated_outputs_read": False,
        },
    }
    (output_root / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not summary["failed_targets"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
