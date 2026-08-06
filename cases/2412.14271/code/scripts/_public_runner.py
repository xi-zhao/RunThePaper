"""Run a case script from the public package with stable output paths."""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys


CODE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = CODE_ROOT.parent


def run_core(script_name: str, arguments: list[str]) -> int:
    """Execute a preserved scientific runner from the public case root."""
    script = CODE_ROOT / "scripts" / script_name
    os.chdir(CASE_ROOT)
    sys.path.insert(0, str(CODE_ROOT))
    sys.argv = [str(script), *arguments]
    runpy.run_path(str(script), run_name="__main__")
    return 0
