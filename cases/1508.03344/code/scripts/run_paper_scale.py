#!/usr/bin/env python3
"""Paper-scale convenience entrypoint; forwards to run_reproduction.py."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
if "--config" not in sys.argv:
    sys.argv[1:1] = ["--config", "config/paper_scale.json"]
runpy.run_path(str(WORKSPACE / "scripts" / "run_reproduction.py"), run_name="__main__")
