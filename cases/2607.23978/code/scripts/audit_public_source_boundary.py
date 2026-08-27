#!/usr/bin/env python3
"""Prove which indispensable definitions are absent from the public source."""

from __future__ import annotations

import json
import re
import tarfile
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
CASE = WORKSPACE.parent
SOURCE = CASE / "paper-source/non_Hermitian_sensing_main.tex"
ARCHIVE = CASE / "raw/2607.23978-source.tar"
OUTPUT = WORKSPACE / "outputs/checks/public_source_boundary_audit.json"


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    with tarfile.open(ARCHIVE) as bundle:
        members = sorted(member.name for member in bundle.getmembers() if member.isfile())

    supplement_files = [
        name
        for name in members
        if re.search(r"supp|appendix|sm\.", Path(name).name, flags=re.IGNORECASE)
    ]
    definition_patterns = {
        "A1": r"A_?1\s*(?:'|\\prime)?\s*(?:=|\\equiv)",
        "A2": r"A_?2\s*(?:'|\\prime)?\s*(?:=|\\equiv)",
    }
    definitions = {
        name: bool(re.search(pattern, source))
        for name, pattern in definition_patterns.items()
    }
    port_probability_definitions = re.findall(
        r"(?<![A-Za-z0-9_{])P(?:_[A-Za-z0-9]+|_\{[^}]+\})?\s*\([^)]*\)\s*=",
        source,
    )
    cfi_sum_present = "F_{\\rm POVM}" in source and "\\sum_j" in source
    supplement_delegations = [
        line.strip()
        for line in source.splitlines()
        if "Supplemental Material" in line
    ]

    passed = (
        not supplement_files
        and not any(definitions.values())
        and cfi_sum_present
        and not port_probability_definitions
        and len(supplement_delegations) >= 2
    )
    payload = {
        "schema_version": 1,
        "paper_id": "2607.23978",
        "status": "passed" if passed else "failed",
        "source_archive_files": members,
        "supplement_files": supplement_files,
        "nonoptimal_observable_definitions_present": definitions,
        "cfi_sum_present": cfi_sum_present,
        "port_probability_definitions": port_probability_definitions,
        "supplement_delegation_count": len(supplement_delegations),
        "conclusion": (
            "The public archive omits the Supplement, the A1/A2 matrix definitions, "
            "and the output-port probabilities required for the two blocked targets."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
