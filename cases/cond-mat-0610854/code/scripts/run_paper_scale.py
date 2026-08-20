#!/usr/bin/env python3
"""Stable paper-scale entrypoint for CPU clusters or an A100 host."""

from __future__ import annotations

import sys

from run_reproduction import main


if __name__ == "__main__":
    if "--config" not in sys.argv:
        sys.argv.extend(["--config", "config/paper_scale.json"])
    raise SystemExit(main())
