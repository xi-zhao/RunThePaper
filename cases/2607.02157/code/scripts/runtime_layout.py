"""Resolve paths for both the master workspace and the public case layout."""
from __future__ import annotations

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

if SCRIPT_DIR.parent.name == "code":
    CASE_ROOT = SCRIPT_DIR.parents[1]
    SOURCE_DIR = SCRIPT_DIR.parent / "src"
else:
    CASE_ROOT = SCRIPT_DIR.parent
    SOURCE_DIR = SCRIPT_DIR
