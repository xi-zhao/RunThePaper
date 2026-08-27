#!/usr/bin/env python3
"""Verify that the frozen public artifacts still match their recorded hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = CASE_ROOT / "outputs" / "checks" / "public_artifact_verification.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []
    for relative, expected in payload["files"].items():
        path = CASE_ROOT / relative
        if not path.is_file() or digest(path) != expected:
            failures.append(relative)
    print(json.dumps({"status": "passed" if not failures else "failed", "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
