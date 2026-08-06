#!/usr/bin/env python3
"""Regenerate analytic branches and equation-level science checks."""
from _public_runner import CODE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_run_analytic_core.py",
            ["--config", str(CODE_ROOT / "config" / "analytic.json")],
        )
    )
