#!/usr/bin/env python3
"""Validate the frozen public artifacts without reading any paper image."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


CASE_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = CASE_ROOT / "outputs"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    records = []
    for group in ("data", "figures"):
        for path in sorted((OUTPUT_ROOT / group).rglob("*")):
            if not path.is_file():
                continue
            record = {
                "path": str(path.relative_to(CASE_ROOT)),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
            if path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8"))
                record["format_check"] = "valid_json"
            elif path.suffix.lower() == ".csv":
                with path.open(newline="", encoding="utf-8") as handle:
                    record["data_rows"] = max(sum(1 for _ in csv.reader(handle)) - 1, 0)
                record["format_check"] = "readable_csv"
            else:
                record["format_check"] = "nonempty" if path.stat().st_size else "empty"
            records.append(record)
    if not records or any(item["bytes"] == 0 for item in records):
        raise SystemExit("public artifact verification failed")
    payload = {
        "schema_version": 1,
        "policy": "artifact-integrity-only; no paper image or source-derived points are read",
        "status": "passed",
        "artifacts": records,
    }
    destination = OUTPUT_ROOT / "checks" / "public_artifact_verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"verified {len(records)} generated public artifacts")


if __name__ == "__main__":
    main()
