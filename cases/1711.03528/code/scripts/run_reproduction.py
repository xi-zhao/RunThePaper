#!/usr/bin/env python3
"""Portable public entrypoint for the independently implemented reproduction."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

CASE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = CASE_ROOT / "code"
IMPLEMENTATION = CODE_ROOT / "scripts" / "run_reproduction_impl.py"


def sync_generated_outputs() -> None:
    for group in ("data", "figures", "checks"):
        source = CODE_ROOT / "outputs" / group
        destination = CASE_ROOT / "outputs" / group
        if not source.is_dir():
            continue
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def main() -> int:
    environment = os.environ.copy()
    python_path = [str(CODE_ROOT), str(CODE_ROOT / "src")]
    if environment.get("PYTHONPATH"):
        python_path.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(python_path)
    completed = subprocess.run(
        [sys.executable, str(IMPLEMENTATION), *sys.argv[1:]],
        cwd=CODE_ROOT,
        env=environment,
        check=False,
    )
    if completed.returncode == 0:
        sync_generated_outputs()
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
