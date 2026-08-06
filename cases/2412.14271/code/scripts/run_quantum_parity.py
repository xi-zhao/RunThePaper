#!/usr/bin/env python3
"""Regenerate the parity-resolved two-photon-loss calculation."""
from _public_runner import CODE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_run_quantum_parity_core.py",
            ["--config", str(CODE_ROOT / "config" / "quantum_parity.json")],
        )
    )
