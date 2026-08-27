#!/usr/bin/env python3
"""Replay committed paper-scale numerical state in the isolated runner.

The legacy paper-scale calculation originally left its resumable checkpoints in
an ignored cache directory.  This runner deliberately ignores that cache.  It
accepts only the hash-bound, Git-tracked snapshot under ``frozen_inputs`` and
copies that snapshot into a disposable workspace before invoking the scientific
code.  A clean checkout therefore sees exactly the same numerical inputs as the
isolated run.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from paper_exact_reproduction import (  # noqa: E402
    run_paper_ed,
    run_paper_profiles,
    run_paper_theory,
)


FROZEN_ROOT = WORKSPACE / "frozen_inputs"
FROZEN_STATE = FROZEN_ROOT / "paper_exact_checkpoint_state"
FROZEN_MANIFEST = FROZEN_ROOT / "paper_exact_checkpoint_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_frozen_evidence() -> dict:
    manifest = json.loads(FROZEN_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen":
        raise RuntimeError("frozen numerical manifest is not in the frozen state")
    if manifest.get("paper_id") != "2507.09447":
        raise RuntimeError("frozen numerical manifest belongs to another paper")

    declared = {
        str(row["path"]): row
        for row in manifest.get("files", [])
        if isinstance(row, dict) and row.get("path")
    }
    actual = {
        path.relative_to(FROZEN_ROOT).as_posix()
        for path in FROZEN_STATE.rglob("*")
        if path.is_file()
    }
    if set(declared) != actual:
        missing = sorted(set(declared) - actual)
        extra = sorted(actual - set(declared))
        raise RuntimeError(f"frozen numerical inventory mismatch: missing={missing}, extra={extra}")

    for relative, row in sorted(declared.items()):
        path = FROZEN_ROOT / relative
        if path.stat().st_size != int(row["bytes"]):
            raise RuntimeError(f"frozen numerical size mismatch: {relative}")
        if _sha256(path) != row["sha256"]:
            raise RuntimeError(f"frozen numerical hash mismatch: {relative}")

    for row in manifest.get("implementation_bindings", []):
        path = WORKSPACE / str(row["path"])
        if not path.is_file():
            raise RuntimeError(f"bound implementation file is missing: {row['path']}")
        if path.stat().st_size != int(row["bytes"]) or _sha256(path) != row["sha256"]:
            raise RuntimeError(f"bound implementation changed: {row['path']}")
    return manifest


def main() -> int:
    manifest = _verify_frozen_evidence()
    config = WORKSPACE / "config" / "paper_exact_run.json"
    outputs_root = WORKSPACE / "outputs"
    outputs_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="paper-replay-", dir=outputs_root) as temp_dir:
        replay_workspace = Path(temp_dir)
        replay_checkpoints = replay_workspace / "outputs" / "paper_exact" / "checkpoints"
        shutil.copytree(FROZEN_STATE, replay_checkpoints)

        results = {
            "ed": run_paper_ed(replay_workspace, config),
            "profiles": run_paper_profiles(replay_workspace, config),
            "theory": run_paper_theory(replay_workspace, config),
        }
        if any(result.get("status") != "passed" for result in results.values()):
            raise RuntimeError(f"paper replay did not pass: {results}")

        source_dir = replay_workspace / "outputs" / "paper_exact" / "data"
        output_dir = WORKSPACE / "outputs" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        data_files = [
            "paper_ed_histograms.npz",
            "paper_scaling.csv",
            "paper_profiles.npz",
            "paper_fig34_theory.npz",
            "paper_fig5_contours.npz",
            "paper_alpha.csv",
        ]
        for name in data_files:
            shutil.copy2(source_dir / name, output_dir / name)

    summary = {
        "schema_version": 1,
        "status": "passed",
        "paper_id": "2507.09447",
        "target_ids": ["T001", "T002", "T003"],
        "mode": "committed_frozen_state_replay",
        "frozen_evidence": {
            "manifest": "frozen_inputs/paper_exact_checkpoint_manifest.json",
            "manifest_sha256": _sha256(FROZEN_MANIFEST),
            "files": len(manifest["files"]),
            "bytes": sum(int(row["bytes"]) for row in manifest["files"]),
            "legacy_generation_attestation": manifest["origin"][
                "legacy_generation_attestation"
            ],
        },
        "scientific_boundary": {
            "author_code_used": False,
            "author_arrays_used": False,
            "source_pixels_used_as_numerical_inputs": False,
            "paper_or_reference_artifacts_read_by_runner": False,
            "frozen_state_origin": "case-local independently generated numerics",
            "ignored_runtime_cache_used": False,
        },
        "stages": results,
        "outputs": [f"outputs/data/{name}" for name in data_files],
    }
    check = WORKSPACE / "outputs" / "checks" / "paper_replay_attested.json"
    check.parent.mkdir(parents=True, exist_ok=True)
    check.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "outputs": summary["outputs"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
