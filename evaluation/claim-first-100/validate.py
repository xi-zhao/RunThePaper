#!/usr/bin/env python3
"""Validate the frozen Claim-first public tables and recorded hashes."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    summary = json.loads((DATA / "summary.json").read_text(encoding="utf-8"))
    checks = rows("checks.csv")
    claims = rows("claims.csv")
    papers = rows("papers.csv")
    non_numeric = rows("non_numeric_claims.csv")
    blocked = rows("externally_blocked_checks.csv")
    attempted = rows("attempted_not_reproduced_checks.csv")

    population = summary["population"]
    assert len(checks) == population["claim_checks"] == 3933
    assert len(claims) == population["authored_claims"] == 1427
    assert len(papers) == population["papers"] == 100
    assert len(non_numeric) == population["non_numeric_claims"] == 15

    observed = Counter(row["disposition"] for row in checks)
    expected = summary["check_metrics"]["disposition_counts"]
    assert observed == Counter(expected)
    assert len(blocked) == expected["externally_blocked"] == 1134
    assert len(attempted) == expected["attempted_not_reproduced"] == 731
    assert summary["check_metrics"]["finalized_checks"] == len(checks)

    for name, expected_hash in summary["provenance"]["output_sha256"].items():
        path = DATA / name
        assert path.is_file(), f"missing hashed output: {name}"
        assert sha256(path) == expected_hash, f"hash mismatch: {name}"

    print(
        json.dumps(
            {
                "status": "passed",
                "papers": len(papers),
                "claims": len(claims),
                "checks": len(checks),
                "dispositions": dict(observed),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
