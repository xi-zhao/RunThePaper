#!/usr/bin/env python3
"""Render base and RenderContract figures from frozen BEM arrays."""
from _public_runner import CASE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_render_figures_core.py",
            [
                "--data",
                str(CASE_ROOT / "outputs" / "data" / "bem_reproduction.npz"),
                "--output-dir",
                str(CASE_ROOT / "outputs" / "figures"),
            ],
        )
    )
