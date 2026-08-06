#!/usr/bin/env python3
"""Regenerate the reduced one-photon-loss trajectory ensemble."""
from _public_runner import CODE_ROOT, run_core


if __name__ == "__main__":
    raise SystemExit(
        run_core(
            "_run_quantum_one_photon_core.py",
            ["--config", str(CODE_ROOT / "config" / "quantum_one_photon.json")],
        )
    )
