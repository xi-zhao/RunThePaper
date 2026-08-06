#!/usr/bin/env python3
"""Regenerate the reduced finite-size two-photon trajectory ensemble."""
from _public_runner import CODE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_run_quantum_main_core.py",
            ["--config", str(CODE_ROOT / "config" / "quantum_main.json")],
        )
    )
