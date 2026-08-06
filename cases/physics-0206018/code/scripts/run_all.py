#!/usr/bin/env python3
"""Regenerate the three numerical BEM targets and science checks."""
from _public_runner import CODE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_run_all_core.py",
            ["--config", str(CODE_ROOT / "config" / "feature.json")],
        )
    )
