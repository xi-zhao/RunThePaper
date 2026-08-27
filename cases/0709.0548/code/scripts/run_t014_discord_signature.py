#!/usr/bin/env python3
"""Finite-boundary audit for the DQC1 first-signature claim."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from dqc1_discord.claim_boundaries import discord_signature_boundary  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()

    config_path = (WORKSPACE / args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = (WORKSPACE / args.output_root).resolve()
    data_dir = output_root / "data"
    checks_dir = output_root / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    rows, summary = discord_signature_boundary(config["parameters"])
    extension_rows = summary.get("symmetric_extension_rows", [])
    if not extension_rows:
        raise RuntimeError("the declared symmetric-extension campaign did not run")
    data_path = data_dir / "t014_discord_signature_boundary.csv"
    extension_path = data_dir / "t014_symmetric_extension.csv"
    check_path = checks_dir / "t014_discord_signature_boundary.json"
    write_csv(data_path, rows)
    write_csv(extension_path, extension_rows)
    check_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "paper_id": "0709.0548",
        "config_sha256": sha256(config_path),
        "outputs": {
            "data": {"path": "outputs/data/t014_discord_signature_boundary.csv", "sha256": sha256(data_path)},
            "symmetric_extension_data": {
                "path": "outputs/data/t014_symmetric_extension.csv",
                "sha256": sha256(extension_path),
            },
            "check": {"path": "outputs/checks/t014_discord_signature_boundary.json", "sha256": sha256(check_path)},
        },
    }
    (checks_dir / "t014_run_summary.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
