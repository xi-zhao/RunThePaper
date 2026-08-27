#!/usr/bin/env python3
"""Audit the publication text for an explicit Fig. S20 time-origin rule.

This is a source-audit lane, not a numerical runner.  It may read the frozen
publication text, but its output is never consumed by the scientific solver.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
CASE = WORKSPACE.parent
PRINTED_TIMES = [10.5, 19.5, 28.5, 37.5, 46.5, 55.5]


def main() -> int:
    source_path = CASE / "raw" / "supplement.txt"
    text = source_path.read_text(encoding="utf-8")
    lower = text.lower()
    printed_times_found = {str(value): f"t = {value:g} ns" in lower for value in PRINTED_TIMES}
    delay_contract_found = "after a delay time t" in lower
    movie_range_found = "from 2.5 ns to 55.5 ns" in lower
    offset_patterns = [
        r"time[- ]origin",
        r"(?:offset|shift)\s+(?:of\s+)?(?:exactly\s+)?5(?:\.0)?\s*ns",
        r"t\s*(?:=|->|→)\s*t\s*[-+]\s*5(?:\.0)?\s*ns",
        r"subtract(?:ed|ing)?\s+5(?:\.0)?\s*ns",
    ]
    offset_hits = [pattern for pattern in offset_patterns if re.search(pattern, lower)]
    passed = (
        all(printed_times_found.values())
        and delay_contract_found
        and movie_range_found
        and not offset_hits
    )
    payload = {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "scope": "publication_source_audit_only",
        "source": "raw/supplement.txt",
        "scientific_runner_consumes_this_artifact": False,
        "printed_times_found": printed_times_found,
        "published_delay_contract_found": delay_contract_found,
        "published_movie_range_found": movie_range_found,
        "explicit_five_ns_time_origin_rule_found": bool(offset_hits),
        "matched_offset_patterns": offset_hits,
        "conclusion": (
            "The supplement prints all six S20 times and defines evolution after a delay t, "
            "but does not publish the common five-nanosecond time-origin mapping required "
            "to reconcile the twelve matrices."
        ),
        "boundary": (
            "This audit establishes publication underspecification; it does not authorize "
            "feeding a fitted offset into the clean-room numerical runner."
        ),
    }
    output = WORKSPACE / "outputs" / "checks" / "S20_time_origin_source_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
