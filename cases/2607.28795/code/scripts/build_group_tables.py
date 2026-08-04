#!/usr/bin/env python3
"""Freeze GAP SmallGroup multiplication tables as source-blind numeric input."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gap_program(group_ids: list[list[int]]) -> str:
    ids = "[" + ",".join(f"[{order},{index}]" for order, index in group_ids) + "]"
    return rf"""
ids := {ids};;
SizeScreen([1000000, 1000000]);;
if LoadPackage("smallgrp") <> true then Error("smallgrp is required"); fi;
smallgrp_version := InstalledPackageVersion("smallgrp");;
Print("{{\"schema_version\":1,\"ordering\":\"GAP Elements(G), zero-based\",\"gap_version\":\"", GAPInfo.Version, "\",\"smallgrp_version\":\"", smallgrp_version, "\",\"groups\":[");
for position in [1..Length(ids)] do
  group := SmallGroup(ids[position][1], ids[position][2]);;
  elements := Elements(group);;
  products := List([1..Length(elements)], i -> List([1..Length(elements)], j -> Position(elements, elements[i] * elements[j]) - 1));;
  inverses := List([1..Length(elements)], i -> Position(elements, Inverse(elements[i])) - 1);;
  identity := Position(elements, One(group)) - 1;;
  if position > 1 then Print(","); fi;
  Print("{{\"small_group_id\":", ids[position], ",\"order\":", Length(elements), ",\"identity\":", identity, ",\"multiplication\":", products, ",\"inverse\":", inverses, "}}");
od;
Print("]}}\n");
QUIT;
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gap", required=True, help="Path to an independent GAP executable")
    parser.add_argument(
        "--gap-root",
        action="append",
        default=[],
        help="Optional GAP root; repeat to add a separate package root",
    )
    parser.add_argument("--paper-inputs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    args = parser.parse_args()

    paper_inputs = json.loads(args.paper_inputs.read_text(encoding="utf-8"))
    group_ids = [row["small_group_id"] for row in paper_inputs["mitten_codes"]]
    command = [args.gap, "-q"]
    if args.gap_root:
        command.extend(["-l", ";".join(args.gap_root)])
    completed = subprocess.run(
        command,
        input=gap_program(group_ids),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr or f"GAP exited with {completed.returncode}")
    payload = json.loads(completed.stdout)
    observed_ids = [row["small_group_id"] for row in payload["groups"]]
    if observed_ids != group_ids:
        raise SystemExit(f"GAP group order mismatch: {observed_ids} != {group_ids}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "generator": "scripts/build_group_tables.py",
        "mathematical_dependency": "GAP Small Groups Library",
        "gap_version": payload["gap_version"],
        "smallgrp_version": payload["smallgrp_version"],
        "paper_inputs_sha256": sha256(args.paper_inputs),
        "group_tables_sha256": sha256(args.output),
        "author_repository_accessed": False,
    }
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
