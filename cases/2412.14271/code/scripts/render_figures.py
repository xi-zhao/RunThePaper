#!/usr/bin/env python3
"""Render all declared numerical figures from generated arrays."""
from _public_runner import CASE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_render_figures_core.py",
            [
                "--data-dir",
                str(CASE_ROOT / "outputs" / "data"),
                "--output-dir",
                str(CASE_ROOT / "outputs" / "figures"),
            ],
        )
    )
